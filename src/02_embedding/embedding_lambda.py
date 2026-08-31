# =============================================================================
# TasteTrend Embedding Lambda - PHASE 4
#
# Triggered by S3 "object created" events under processed/
#   1. Reads every review row in that file
#   2. Sends the review texts to the FM, which converts it into a "vector embedding"
#   3. Saves that vector, plus the review's other columns into OpenSearch
# This makes "RAG" possible later. Once every review is stored as a vector, 
# a natural-language question like "which restaurant has the best vegetarian options?" 
# becomes possible.
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
from urllib.parse import unquote_plus

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
bedrock_client = boto3.client('bedrock-runtime')
http = urllib3.PoolManager()

# ---------------------------------------------------------------------------
# Module-level Configuration Parameters
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

# The  reference table has nothing to embed. Filenames check early avoiding a
# pointless S3 download and a flood of "row missing review_id" warnings.
REFERENCE_FILE_MARKERS = ('restaurant_info', 'reference')

# Truncating review texts that are loger than 2000 characters
MAX_CHARS = 2000

# Credentials for signing OpenSearch requests — reuses the Lambda's own
# execution role, no separate secret needed.
credentials = boto3.Session().get_credentials()

# ---------------------------------------------------------------------------
# Function Definitions
# ---------------------------------------------------------------------------
# OpenSearch requires every request to be "signed" using AWS's SigV4 signing scheme.
# This proves to OpenSearch "this request really came from an AWS identity that's 
# allowed to call me," without needing a separate username/password.
def _signed_opensearch_request(method, path, body=None):
    url = f"https://{OPENSEARCH_ENDPOINT}{path}"
    # Convert the Python dict body into a JSON string, then into bytes —
    # HTTP requests send raw bytes, not Python objects.
    data = json.dumps(body).encode('utf-8') if body is not None else None
    headers = {'Content-Type': 'application/json'}

    # AWSRequest is a lightweight "unsent request" object
    # SigV4Auth now has something to attach a cryptographic signature to.
    request = AWSRequest(method=method, url=url, data=data, headers=headers)

    # 'es' here means "this signature is for the OpenSearch service"
    # SigV4 signatures are scoped per-AWS-service, so this tells AWS 
    # which service's permissions to check against.
    SigV4Auth(credentials, 'es', OPENSEARCH_REGION).add_auth(request)

    # Now actually send the signed request over the network and return OpenSearch's response
    return http.request(method, url, body=data, headers=dict(request.headers))

# A well-structured index needs to exist in OpenSearch before saving any data.
# Terraform cannot create this for us so this has to happen at runtime via 
# a normal HTTP API call, the first time this Lambda runs. This function checks 
# "does the index already exist?" first. If it already exists, do nothing and 
# return immediately. If not, define its structure and create it.
def ensure_index_exists():
    check = _signed_opensearch_request('HEAD', f'/{INDEX_NAME}')
    if check.status == 200:
        # 200 = "found it, already exists" — nothing to do.
        return

    logger.info(f"Index '{INDEX_NAME}' not found — creating it now.")

    # This dictionary defines the SHAPE of every document we'll store
    mapping = {
        # Turns on OpenSearch's KNN search feature for this index
        # Required for meaning-based vector search
        "settings": {"index.knn": True},
        "mappings": {
            "properties": {
                "review_id": {"type": "keyword"},
                "restaurant_id": {"type": "keyword"},
                "rating": {"type": "float"},
                "review_date": {"type": "date", "ignore_malformed": True},
                    # if a date string doesn't parse
                    # cleanly, don't fail the whole document
                "review_text": {"type": "text"},
                "embedding": {
                    # This makes vector search possible
                    "type": "knn_vector",
                    "dimension": EMBEDDING_DIMENSIONS,
                    "method": {
                        "name": "hnsw",
                        "space_type": "innerproduct",
                        "engine": "faiss"
                    }
                }
            }
        }
    }

    # Actually create the index with this structure.
    resp = _signed_opensearch_request('PUT', f'/{INDEX_NAME}', body=mapping)
    if resp.status not in (200, 201):
        raise RuntimeError(f"Failed to create index: {resp.status} {resp.data}")
    logger.info(f"Index '{INDEX_NAME}' created successfully.")

# COST SAVING STEP: Checks whether a review_id is already indexed BEFORE calling Bedrock.
# This is what prevents a Lambda retry from re-paying for embeddings that were already 
# successfully generated and indexed on a prior (timed-out or partially-failed) attempt.
# Uses a HEAD request (checks existence only, doesn't download the full document) 
# since a yes/no answer is needed here, not the actual data.
def document_already_indexed(review_id):
    resp = _signed_opensearch_request('HEAD', f'/{INDEX_NAME}/_doc/{review_id}')
    return resp.status == 200

# Splits text into chunks of maximum limit characters.
def chunk_text(text, limit=MAX_CHARS):
    return [text[i:i + limit] for i in range(0, len(text), limit)]

# CORE STEP: Calls Bedrock's FM to convert text into a vector.
def get_embedding(text):

    # Slices text to 2000 chars so Cohere never receives > 2048 chars
    safe_text = chunk_text(text, MAX_CHARS)[0] if text else ""

    # Main
    body = json.dumps({
        "texts": [safe_text],
        "input_type": "search_document"  # Required for indexing documents
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
    return result['embeddings'][0]  # Cohere returns a list of embeddings

# Writes one document into OpenSearch, using review_id as the document_id 
# so re-running this Lambda on the same file overwrites rather than creates a duplicate entry.
def index_document(review_id, doc):
    resp = _signed_opensearch_request('PUT', f'/{INDEX_NAME}/_doc/{review_id}', body=doc)
    if resp.status not in (200, 201):
        raise RuntimeError(f"Failed to index review_id={review_id}: {resp.status} {resp.data}")

# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------
# Invoked by AWS Lambda on every S3 "object created" event under processed/. 
# A single invocation may carry multiple file events, so every record is processed 
# individually in the loop below. Nothing here assumes exactly one file per invocation.
def lambda_handler(event, context):
    logger.info(f"Received event with {len(event.get('Records', []))} record(s).")

    # Check for the Opensearch index
    ensure_index_exists()

    # Useful for a quick sanity check in CloudWatch logs
    indexed_count = 0
    skipped_count = 0

    for record in event['Records']:
        # Pull out which S3 bucket and which file (key) triggered this event.
        s3_info = record['s3']
        bucket_name = s3_info['bucket']['name']

        # S3 keys can be URL-encoded. This decodes them back to the real filename
        file_key = unquote_plus(s3_info['object']['key'])

        # Safety check for processing the correct files
        if not file_key.startswith('processed/'):
            logger.info(f"Skipping non-processed file: {file_key}")
            continue

        # Skip the reference table before wasting an S3 download on it.
        if any(marker in file_key.lower() for marker in REFERENCE_FILE_MARKERS):
            logger.info(f"Skipping reference/dimension file (nothing to embed): {file_key}")
            continue

        logger.info(f"Processing file for embedding: {file_key}")

        # Download the whole CSV file's content into memory as text.
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        raw_text = response['Body'].read().decode('utf-8')

        # Turn each row into a dictionary keyed for easier data handling
        reader = csv.DictReader(io.StringIO(raw_text))

        for row in reader:
            review_id = row.get('review_id')
            review_text = row.get('review_text')

            # A row with no review_id can't be indexed and must be skipped.s
            if not review_id:
                logger.warning(f"[{file_key}] Row missing review_id — skipping.")
                continue

            # Cost-saving check: skip Bedrock entirely if this row was
            # already embedded and indexed on a previous invocation.
            if document_already_indexed(review_id):
                skipped_count += 1
                continue

            # Skip reviews with no text rather than sending an empty string to Bedrock.
            if not review_text or not review_text.strip():
                logger.info(f"[{review_id}] Blank review_text — nothing to embed, skipping.")
                continue

            # Call Bedrock to turn this review's text into a vector.
            try:
                embedding = get_embedding(review_text)
            except Exception as e:
                logger.error(f"[{review_id}] Bedrock embedding call failed: {str(e)}")
                continue  # one bad row shouldn't abort the whole file

            # Safely pull the rating value out of the row to avoid using Null or NaN values.
            raw_rating = row.get('rating')
            doc = {
                "review_id": review_id,
                "restaurant_id": row.get('restaurant_id'),
                "rating": float(raw_rating) if raw_rating not in (None, '', 'nan') else None,
                "review_date": row.get('review_date') or None,
                "review_text": review_text,
                "embedding": embedding,
            }

            # Save this review + its embedding into OpenSearch.
            try:
                index_document(review_id, doc)
                indexed_count += 1
            except Exception as e:
                logger.error(f"[{review_id}] OpenSearch indexing failed: {str(e)}")
                continue  # one bad row shouldn't abort the whole file

    # Final summary in the logs and also gets returned to whatever invoked this Lambda
    logger.info(f"Done. Indexed {indexed_count} new document(s), skipped {skipped_count} already-indexed.")
    return {'statusCode': 200, 'body': json.dumps({'indexed': indexed_count, 'skipped': skipped_count})}