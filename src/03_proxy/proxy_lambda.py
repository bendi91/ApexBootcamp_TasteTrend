# =============================================================================
# TasteTrend Proxy Lambda (RAG Orchestration) — Phase 5
#
# Triggered by an API call
#   1. It receives a natural-language question via an API call
#   2. Searches the already-indexed reviews for relevant ones
#   3. And asks a language model to answer using only that retrieved evidence.
# =============================================================================

import json
import os
import csv
import io
import logging
import urllib3
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Talks to Bedrock's managed API (embedding + text generation)
bedrock_client = boto3.client('bedrock-runtime')
# Reads the processed reference table so restaurant names (not just location
# tags) can be matched in question text — see _load_restaurant_name_map().
s3_client = boto3.client('s3')
# A connection-pooling HTTP client, used for OpenSearch requests, which
# Bedrock's SDK has no built-in support for
http = urllib3.PoolManager()

# ---------------------------------------------------------------------------
# Module-level Configuration
# ---------------------------------------------------------------------------
# Set via Terraform environment variables — OPENSEARCH_ENDPOINT is only
# known after the domain is created, so it can't be hardcoded ahead of time.
OPENSEARCH_ENDPOINT = os.environ['OPENSEARCH_ENDPOINT']

# AWS_REGION is automatically provided by the Lambda runtime itself for every function
OPENSEARCH_REGION = os.environ.get('AWS_REGION', 'eu-central-1')

# The name of the index in OpenSearch where all review documents will be stored.
INDEX_NAME = 'tastetrend-reviews'

# Bedrock model config
EMBEDDING_MODEL_ID = 'cohere.embed-english-v3'
EMBEDDING_DIMENSIONS = 1024  # Cohere v3 defaults to 1024 dimensions

# Text-generation model for answering questions using retrieved reviews.
GENERATION_MODEL_ID = 'eu.amazon.nova-micro-v1:0'

# Search similar reviews
TOP_K = 5  # number of most-relevant reviews to retrieve as context
RELATIVE_RELEVANCE_THRESHOLD = 0.7  # keep hits scoring >= 70% of the top hit

# Known restaurant IDs/tags for rule-based filter extraction
KNOWN_RESTAURANTS = ["eastside", "uptown", "midtown", "downtown"]

# Bucket holding the processed reference table, used to resolve actual
# restaurant names (e.g. "Village Whiskey") to their internal location tag
# (e.g. "downtown"), since restaurant_id in the reviews index is the tag,
# not the business name. Same bucket etl_lambda.py/embedding_lambda.py read from.
DATA_BUCKET = os.environ['DATA_BUCKET']

# Same marker convention used in etl_lambda.py/embedding_lambda.py to
# identify the reference file among everything under processed/.
REFERENCE_FILE_MARKERS = ('restaurant_info', 'reference')

# Populated on first use by _load_restaurant_name_map() and reused for the
# lifetime of this execution environment (a warm Lambda container), so the
# reference table is fetched from S3 at most once per container, not once
# per invocation.
_RESTAURANT_NAME_MAP = None

# ---------------------------------------------------------------------------
# Function Definitions
# ---------------------------------------------------------------------------
# Same SigV4 signing pattern as embedding_lambda.py — duplicated here rather than 
# shared via a layer, since it's ~15 lines and keeping each Lambda's deployment package 
# independent is simpler for a PoC of this size.
def _signed_opensearch_request(method, path, body=None):
    url = f"https://{OPENSEARCH_ENDPOINT}{path}"
    # Convert the Python dict body into a JSON string, then into bytes —
    # HTTP requests send raw bytes, not Python objects.
    data = json.dumps(body).encode('utf-8') if body is not None else None
    headers = {'Content-Type': 'application/json'}

    # Credentials for signing OpenSearch requests — reuses the Lambda's own
    # execution role, no separate secret needed.
    credentials = boto3.Session().get_credentials()

    # AWSRequest is a lightweight "unsent request" object
    # SigV4Auth now has something to attach a cryptographic signature to.
    request = AWSRequest(method=method, url=url, data=data, headers=headers)

    # 'es' here means "this signature is for the OpenSearch service"
    # SigV4 signatures are scoped per-AWS-service, so this tells AWS 
    # which service's permissions to check against.
    SigV4Auth(credentials, 'es', OPENSEARCH_REGION).add_auth(request)

    # Now actually send the signed request over the network and return OpenSearch's response
    return http.request(method, url, body=data, headers=dict(request.headers))

# Same embedding call as embedding_lambda.py's get_embedding function.
# The question needs to land in the exact same vector space as the indexed reviews.
def embed_question(text):
    body = json.dumps({
        "texts": [text],
        "input_type": "search_query"  # Required for query/retrieval search
    })
    response = bedrock_client.invoke_model(
        modelId=EMBEDDING_MODEL_ID,
        body=body,
        contentType='application/json',
        accept='application/json'
    )
    # Bedrock's response body comes back as a stream of JSON bytes — parse
    # it, then pull out just the "embedding" field (the actual vector).
    result = json.loads(response['body'].read())
    return result['embeddings'][0]

# Finds and parses the processed reference table, returning a
# {restaurant_name (lowercase): restaurant_id (location tag)} map.
# Cached at module level so this only hits S3 once per warm container.
def _load_restaurant_name_map():
    global _RESTAURANT_NAME_MAP
    if _RESTAURANT_NAME_MAP is not None:
        return _RESTAURANT_NAME_MAP

    name_map = {}
    try:
        listing = s3_client.list_objects_v2(Bucket=DATA_BUCKET, Prefix='processed/')
        ref_key = next(
            (obj['Key'] for obj in listing.get('Contents', [])
             if any(marker in obj['Key'].lower() for marker in REFERENCE_FILE_MARKERS)),
            None
        )
        if not ref_key:
            logger.warning("No reference file found under processed/ — restaurant name matching will be limited to location tags.")
        else:
            response = s3_client.get_object(Bucket=DATA_BUCKET, Key=ref_key)
            raw_text = response['Body'].read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(raw_text))
            for row in reader:
                name = row.get('restaurant_name')
                rest_id = row.get('restaurant_id')
                if name and rest_id:
                    name_map[name.strip().lower()] = rest_id.strip().lower()
            logger.info(f"Loaded {len(name_map)} restaurant name(s) from reference file '{ref_key}'.")
    except Exception as e:
        # A broken lookup shouldn't take down question-answering entirely —
        # fall back to location-tag-only matching (KNOWN_RESTAURANTS) below.
        logger.error(f"Failed to load restaurant name map from S3: {str(e)}")

    _RESTAURANT_NAME_MAP = name_map
    return _RESTAURANT_NAME_MAP

# Extracts target restaurant_id(s) from the query text if present.
# Matches both internal location tags (e.g. "downtown") and real restaurant
# names from the reference table (e.g. "Village Whiskey"), since restaurant_id
# in the reviews index is the location tag either way.
def extract_restaurant_ids(question):
    q_lower = question.lower()
    matched = set(rest_id for rest_id in KNOWN_RESTAURANTS if rest_id in q_lower)

    name_map = _load_restaurant_name_map()
    for name, rest_id in name_map.items():
        if name in q_lower:
            matched.add(rest_id)

    return list(matched)

# Runs a KNN vector search against the reviews index, returning the
# k most semantically similar reviews to the question.
def search_similar_reviews(question_embedding, k=TOP_K, target_restaurants=None, apply_score_cutoff=True):
    # Initialize empty filter container to prevent unbound variable scope errors
    restaurant_filters = []

    # Runs k-NN search with an optional strict boolean filter on restaurant_id.
    knn_clause = {
        "knn": {
            "embedding": {
                "vector": question_embedding,
                "k": k
            }
        }
    }

    # If target restaurant is identified, strictly isolate context via OpenSearch boolean filter
    if target_restaurants:
        if isinstance(target_restaurants, str):
            target_restaurants = [target_restaurants.lower()]
        else:
            target_restaurants = [r.lower() for r in target_restaurants]

        # Use match inside filter
        restaurant_filters = [{"match": {"restaurant_id": r}} for r in target_restaurants]
        
        query = {
            "size": k,
            "query": {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "embedding": {
                                    "vector": question_embedding,
                                    "k": k
                                }
                            }
                        }
                    ],
                    "filter": [
                        {
                            "bool": {
                                "should": restaurant_filters,
                                "minimum_should_match": 1
                            }
                        }
                    ]
                }
            }
        }
    else:
        query = {
            "size": k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": question_embedding,
                        "k": k
                    }
                }
            }
        }
    resp = _signed_opensearch_request('POST', f'/{INDEX_NAME}/_search', body=query)
    if resp.status != 200:
        # A non-200 here means something structural is wrong --> worth failing loudly rather
        # than silently returning no results, which would look like "no relevant reviews exist" 
        # when the real problem is a broken search.
        raise RuntimeError(f"OpenSearch k-NN search failed: {resp.status} {resp.data}")

    result = json.loads(resp.data)
    hits = result['hits']['hits']

    used_fallback = False
    if not hits and target_restaurants:
        # FALLBACK: If vector distance drops hits to 0, execute standard text search
        logger.warning(f"k-NN filter returned 0 hits for {target_restaurants}. Executing term fallback search.")
        fallback_query = {
            "size": k,
            "query": {
                "bool": {
                    "should": restaurant_filters,
                    "minimum_should_match": 1
                }
            }
        }
        resp = _signed_opensearch_request('POST', f'/{INDEX_NAME}/_search', body=fallback_query)
        result = json.loads(resp.data)
        hits = result['hits']['hits']
        used_fallback = True


    if not hits:
        return []

    # Keyword-match _score (BM25-style) and k-NN vector-similarity _score are
    # different metrics on different scales. RELATIVE_RELEVANCE_THRESHOLD was
    # tuned for semantic similarity, so it isn't meaningful against fallback
    # keyword scores — skip the cutoff whenever the fallback path was used.
    # The fallback only fires when semantic search found zero hits, so any
    # keyword matches at all are already the best available evidence.
    if apply_score_cutoff and not used_fallback:

    # Filter out weak matches: KNN search always returns up to k results 
    # even if the index only has 1-2 relevant results. Without filtering, 
    # those weak ones would still get fed into the generation prompt as if 
    # they were solid supporting evidence.
    #
    # OpenSearch already sorts hits from best to worst, so hits[0] is 
    # guaranteed to be the single best match for this question.
    # Every hit (including hits[0] itself) must score at least the 
    # RELATIVE_RELEVANCE_THRESHOLD of that top score to survive.
        top_score = hits[0].get('_score', 0)
        score_cutoff = top_score * RELATIVE_RELEVANCE_THRESHOLD
        relevant_hits = [h for h in hits if h.get('_score', 0) >= score_cutoff]

    else:
        relevant_hits = hits


    # Each OpenSearch "hit" wraps the actual document under "_source".
    # This unwraps that so callers just get plain review dicts.
    return [hit['_source'] for hit in relevant_hits]

 # Assembles the retrieved reviews into context, then asks the model to answer 
 # using only that context — this is the core RAG mechanism:
 # grounding the answer in retrieved data rather than the model's own unguided knowledge.
def build_prompt(question, reviews):
    context_blocks = []
    for r in reviews:
        # A retrieved review might be blank/nulled or the columns might be missing
        # that shouldn't crash prompt construction.

        # Security vulnerability: Indirect Prompt Injection - must be resolved 
        # before production use. Out of scope for now
        context_blocks.append(
            f"- Restaurant: {r.get('restaurant_id', 'unknown')} | "
            f"Rating: {r.get('rating', 'n/a')} | "
            f"Review: {r.get('review_text', '')}"
        )
    context = "\n".join(context_blocks)
    # SECURITY: indirect prompt injection mitigation, NOT a complete fix.
    # A review could contain text crafted to look like an instruction aimed at the model
    # No prompt-level defense can guarantee a model will never follow
    # embedded text as a command.
    return (
        f"Reviews:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

# Calls the Bedrock FM with the RAG-augmented prompt.
def generate_answer(prompt):
    body = json.dumps({
        "system": [
            {
                "text": (
                    "You are a helpful and professional restaurant assistant designed to answer qualitative questions. "
                    "Answer questions directly using only the provided reviews, relying strictly on the retrieved evidence. "
                    "Maintain flawless grammar, correct mechanics, and an engaging tone. "
                    "Synthesize information in your own words. "
                    "Keep responses brief, limited to 2-3 natural sentences maximum without markdown bullets.\n\n"
                    "GUARDRAIL RULES:\n"
                    "1. If the user explicitly asks for exact mathematical calculations, numerical averages, or database-wide totals "
                    "(e.g., 'average rating', 'calculate mean', 'exact count'), refuse by returning EXACTLY:\n"
                    "\"Answering quantitative questions is not authorized for this assistant, but I can share what guests typically say about their experience!\"\n"
                    "2. If the user asks general, qualitative questions about ratings (e.g., 'typical ratings', 'how are the ratings'), "
                    "DO NOT REFUSE. Summarize the retrieved feedback qualitatively in 2-3 natural sentences without bullet points."
                )
            }
        ],
        "inferenceConfig": {
            "maxTokens": 150,
            "temperature": 0.2,
            "topP": 0.9
        },
        "messages": [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ]
    })
    
    response = bedrock_client.invoke_model(
        modelId=GENERATION_MODEL_ID,
        body=body,
        contentType='application/json',
        accept='application/json'
    )
    
    result = json.loads(response['body'].read())
    return result['output']['message']['content'][0]['text'].strip()

# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------
# Expects an API-Gateway-Lambda-proxy-style event.
# Returns an API-Gateway-proxy-shaped response
def lambda_handler(event, context):
    try:
        # API Gateway sends the request body as a JSON string, not a parsed dict, 
        # so we json.loads() it ourselves — the or '{}' fallback handles a request 
        # with no body at all, so this never crashes on None.
        body = json.loads(event.get('body') or '{}')
        question = body.get('question', '').strip()

        if not question:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing "question" in request body.'})
            }

        # Step 1: Extract restaurant targets
        extracted_from_text = extract_restaurant_ids(question)
        
        # If the text itself asks about multiple spots (e.g., comparison query), prioritize text extraction
        if len(extracted_from_text) > 1:
            target_restaurants = extracted_from_text
        else:
            payload_target = body.get('restaurant_id') or body.get('restaurant_ids')
            if isinstance(payload_target, str):
                target_restaurants = [payload_target]
            elif isinstance(payload_target, list):
                target_restaurants = payload_target
            else:
                target_restaurants = extracted_from_text

        logger.info(f"Received question: '{question}' | Target Restaurants: {target_restaurants}")

        # Step 2: Embed question
        question_embedding = embed_question(question)

        # Step 3: Retrieve reviews with entity-balanced retrieval
        reviews = []
        if len(target_restaurants) > 1:
            # Multi-entity query: fetch top hits per restaurant to guarantee balanced representation
            per_rest_k = max(2, TOP_K // len(target_restaurants))
            for rest_id in target_restaurants:
                hits = search_similar_reviews(
                    question_embedding,
                    k=per_rest_k,
                    target_restaurants=[rest_id],
                    apply_score_cutoff=False
                )
                # Log exact hit counts per entity
                logger.info(f"Retrieved {len(hits)} hits for target '{rest_id}'")
                reviews.extend(hits)
        elif len(target_restaurants) == 1:
            reviews = search_similar_reviews(
                question_embedding,
                k=TOP_K,
                target_restaurants=target_restaurants,
                apply_score_cutoff=True
            )
        else:
            reviews = search_similar_reviews(
                question_embedding,
                k=TOP_K,
                target_restaurants=None,
                apply_score_cutoff=True
            )


        if not reviews:
            # No matches isn't an error — it's a legitimate, honest answer
            # when the index genuinely has nothing relevant. Returning this
            # explicitly avoids hallucinations.
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'answer': "I couldn't find any relevant reviews to answer that question.",
                    'sources': []
                })
            }

        # Step 4: Build prompt & generate answer
        prompt = build_prompt(question, reviews)
        answer = generate_answer(prompt)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'answer': answer,
                'sources': reviews      # included to show which reviews 
                                        # the answer was grounded in
            })
        }

    except Exception as e:
        # This Lambda processes ONE question per invocation — there's no
        # "continue to the next item" concept to preserve, unlike a
        # multi-row file. Any failure at any step means this one request
        # simply failed, which is the entire scope of this invocation.
        logger.error(f"Error processing question: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal error processing your question.'})
        }

# DIAGNOSTIC MODE: Temporary handler to log index aggregation metrics to CloudWatch.
# Comment out primary lambda_handler during testing.
# def lambda_handler(event, context):
#     # Aggregation query: Counts exact document totals per restaurant_id
#     query = {
#         "size": 0,
#         "aggs": {
#             "restaurant_counts_keyword": {
#                 "terms": {
#                     "field": "restaurant_id.keyword",
#                     "size": 10
#                 }
#             },
#             "restaurant_counts_raw": {
#                 "terms": {
#                     "field": "restaurant_id",
#                     "size": 10
#                 }
#             }
#         }
#     }
    
#     resp = _signed_opensearch_request('POST', f'/{INDEX_NAME}/_search', body=query)
#     result = json.loads(resp.data)
    
#     buckets_kw = result.get('aggregations', {}).get('restaurant_counts_keyword', {}).get('buckets', [])
#     buckets_raw = result.get('aggregations', {}).get('restaurant_counts_raw', {}).get('buckets', [])
    
#     summary = {
#         "total_documents": result['hits']['total']['value'],
#         "counts_by_keyword_field": buckets_kw,
#         "counts_by_raw_field": buckets_raw
#     }
    
#     logger.info(f"OpenSearch Aggregation Inspection: {json.dumps(summary, indent=2)}")
    
#     return {
#         'statusCode': 200,
#         'body': json.dumps(summary)
#     }