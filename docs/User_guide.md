# TasteTrend Gen AI POC - User Guide

Welcome to the **TasteTrend Analytics Gen AI Platform**. This guide provides practical instructions for interacting with the TasteTrend REST API, sending natural-language queries, formatting payload parameters, handling system responses, and understanding system guardrails and failure modes.

# 1. System Overview

The current iteration of the TasteTrend platform is engineered as a Proof-of-Concept (PoC) to demonstrate core retrieval-augmented generation capabilities prioritizing low inference costs and minimal operational overhead.

Rather than deploying an end-to-end mobile or web application, the system utilizes a locally executed python script to simulate user API requests and RAG pipeline’s responses in the following order: (1) Ingests natural-language queries from a structured JSON file (2) Transmits requests through AWS API Gateway to invoke the RAG pipeline (3) Outputs the RAG pipeline’s response into a MD file.

The TasteTrend PoC deploys lightweight foundation models such as **Cohere Embed English V3** and **AWS Nova Micro**. While this design choice drastically reduces per-query compute costs, it introduces acceptable trade-offs in model accuracy, complex reasoning and response generalization. Associated architectural limitations are cataloged in [5. Known Architectural Limitations](#5.-known-architectural-limitations).

With the TasteTrend AWS infrastructure fully provisioned and operational, execute the following sequential workflow to simulate client API requests and evaluate pipeline performance:

1. **Input Payload Configuration [Test Queries](../tests/test_queries.json):** Prepare a structured JSON file containing test queries and optional metadata parameters to define incoming user requests.  
2. **Local Script Execution [Validation Script](../tests/validate_RAG_pipeline.py):** Run the local Python simulation script to stream test payloads through Amazon API Gateway directly to the live AWS RAG infrastructure.  
3. **Output Evaluation [RAG Evaluation Results](../tests/rag_evaluation_results_20260826_014239.md):** Audit the generated Markdown report to evaluate responses, verify evidence grounding, and inspect retrieved source context returned by the API.

# 2. Input Payload Configuration

To feed test questions into the RAG simulation script, format your queries inside the **[Test Queries](../tests/test_queries.json)** file using the JSON schema required by the API Gateway endpoint. 

Query sample:

```json
{
    "id": "Q-02",
    "category": "sentiment",
    "query": "how customers feel about the happy hour at midtown?",
    "expected_keywords": ["midtown", "happy hour", "discount", "service"]
  },
  {
    "id": "Q-03",
    "category": "comparisons",
    "query": "which spot is better if i want good vegetarian options, eastside or downtown?",
    "expected_keywords": ["vegetarian", "veggie", "eastside", "downtown"]
  }
```

JSON schema:

* query: The primary natural-language question forwarded to the AWS RAG pipeline (Required API Payload ).
* id: Unique identifier used by the simulation script to index results in the output Markdown file (Informative metadata - optional).
* category: Query labels used by the simulation script to categorize results in the output Markdown file (Informative metadata - optional).
* expected_keywords: Keywords used by the local audit script to evaluate context retrieval quality (Validation markers - optional).

# 3. Local Script Execution

## 3.1 Environment Setup

To execute the local API simulation, set up your local execution environment and run the validation script using the steps below.

1. **Python Runtime:** Ensure **Python 3.12** or higher is installed on your local machine. You can download the installer matching your operating system from the official [Python Release Page](https://www.python.org/downloads/release/python-3120/).  
2. **Verify Installation:** Open Windows Command Prompt or PowerShell and check your installed Python version:

```bash
python --version
```

3. **Install Dependencies:** Install the required third-party library to enable HTTP transport over the API Gateway endpoint:

```bash
pip install requests boto3
```

## 3.2 Executing the simulation script

1. **Navigate to Root Directory:** Open PowerShell and navigate to the project root folder:

```bash
cd Replace this with your directory path
```

2. **Run the script:** Execute the [Validation Script](../tests/validate_RAG_pipeline.py) simulation script to stream test queries from the JSON file through API Gateway to the live AWS RAG pipeline:

```bash
python tests/validate_RAG_pipeline.py
```

3. **Review Output:** Upon execution, the script generates a timestamped Markdown audit report in the output directory detailing response text and verified source metadata.

## 3.3 Error handling

This section details common operational faults and technical strategies to resolve them while running the RAG pipeline validation script.

### 3.3.1 NameResolutionError / Connection Error HTTPSConnectionPool: Failed to resolve host

Root Cause: The API Gateway endpoint URL is outdated or non-existent

Remediation Step: Verify your active API endpoint in AWS/Terraform and pass it via environment variable

```powershell
$env:TASTETREND_API_URL="https://<api-id>.execute-api.eu-central-1.amazonaws.com/poc/query"
```

### 3.3.2 AWS Authentication Failure - [ERROR] Could not dynamically resolve API Gateway URL

Root Cause: Local AWS CLI credentials are missing, expired, or lack apigateway:GET permissions to auto-detect the URL.

Remediation Step: Run aws configure to update your access keys, or manually set the TASTETREND_API_URL environment variable to bypass AWS lookup.

### 3.3.3 HTTP 504 / Gateway Timeout - Status Code: 504

Root Cause: AWS Lambda container cold start or initial OpenSearch vector index initialization exceeded the gateway timeout threshold.

Remediation Step: Re-run RAG pipeline validation script. Subsequent invocations will use warm containers and fast database connection pool.

### 3.3.4 JSONDecodeError — invalid JSON in test_queries.json

Root Cause: Malformed JSON syntax in `tests/test_queries.json` — commonly a trailing comma or a missing/mismatched bracket.

Remediation Step: Validate the file before running the script:

```bash
python -m json.tool tests/test_queries.json
```

### 3.3.5 HTTP 400 / Bad Request

Root Cause: A query entry in `test_queries.json` is missing the required `query` field, or the payload does not match the schema defined in [Section 2](#2-input-payload-configuration).

Remediation Step: Check the offending entry against the JSON schema in Section 2 and ensure `query` is present and non-empty.

### HTTP 500 / Internal Server Error

Root Cause: An unhandled exception occurred in the Proxy Lambda function.

Remediation Step: Inspect the latest CloudWatch log stream for the Proxy Lambda to locate the stack trace.

# 4. Output Evaluation

## 4.1 Evaluation report

The simulation script exports test execution results into a formatted Markdown evaluation report [RAG Evaluation Results](../tests/rag_evaluation_results_20260826_014239.md), which functions as the primary audit record for pipeline validation.

Each query entry contains three core components:

* **Execution Telemetry:** Logs execution metadata including the input question, latency, HTTP status code, target keyword hits, and overall test status.

* **Synthesized Answer:** Displays the final qualitative response generated by AWS Nova Micro.

* **Retrieved Context Chunks:** Exposes the source review entities retrieved from the OpenSearch vector database. Each retrieved record includes the review_id, restaurant_id, rating, and original review_text. Review creation dates are omitted from source metadata, as the RAG pipeline is scoped strictly for qualitative semantic search and lacks time-series calculation capabilities.

Sample from the Markdown evaluation report:

```markdown
---

### Test `Q-01`: RATINGS

* **Query:** "typical ratings at eastside res?"
* **Result:** 🟢 **PASSED**
* **Latency:** `1.66s` | **Status Code:** `200`  
* **Matched Keywords:** `['rating', 'star', 'eastside', 'review']`

**Generated Answer:**
> Guests typically give eastside restaurant ratings around 3 to 4 stars, appreciating the atmosphere and service but noting mixed reviews about the food quality.

<details>
<summary><b>View Retrieved Context (3 chunks)</b></summary>

1. **[ID: dDKRtNXR8JJAz4x_ZCGo3g | eastside | Rating: 4.0]**: Great location, cool atmosphere! The food was a fairly priced for the quality, which was good. I had the pulled pork tacos and they were not skimpy, fully stuffed and filling for $6. Great draft beer selection but it was a buck or two overpriced compared to other craft beer places. The two waitresses were very nice and pleasant. It was slow when we got there and them boom it was packed, they didn't forget about us but we did have to track her down for our last beer. I will be back for sure!
2. **[ID: ADodUkepU3OyY-G5zZk7yA | eastside | Rating: 3.0]**: This place is fun! I like the staff and the vibe. Food is okay. Beer selection is okay. Great happy hour on wine once a week. 3.5 stars is more appropriate for this place.
3. **[ID: BCLvpd08Ci4Tcq-fIRhZdA | eastside | Rating: 2.0]**: Leaving this 2-star review in response to the food, not the place as a drinking/hangout spot...although the wine was crap, too. 2-Stars awarded for the Nintendo 64 and all of the nostalgia-worthy games, the decent choice of drafts (even if they were out of the draft I ordered), and the great service from the staff. The food, on the other hand, will make you wish you had eaten at home. My wife and I went out as a treat because we didn't feel like cooking, but the majority of our food was sub-par. I got the shrimp po-boy which was not a po-boy by definition (it was just shrimp on a crappy sandwich...no French bread, no Cajun sauce or even enough Cajun seasoning, and the shrimp was obviously frozen-thawed not fresh). One of the shrimps was even gray when I bit into it, and the sandwich itself smelled more like old fish than fresh shrimp. My wife got the Athena chicken sandwich and that was just so-so, with the overwhelming taste of feta disguising the low-quality factory chicken they use for the sandwich. The best part of our collective meals was the mixed greens we ordered as a side, so I wouldn't exactly recommend ordering food here unless you're completely hammered and taste is not a priority.

</details>

---
```

## 4.2 Manual validation

Audit each query entry manually against the following key criterias to verify end-to-end RAG performance:

1. **Query Accuracy** - Natural language queries return relevant results with >80% accuracy based on manual validation.

Mark the query result as accurate when:
* **Contextual Alignment**: The answer correctly summarizes the core sentiment and details of the retrieved source reviews.
* **Accuracy**: The response contains zero hallucinations or ungrounded claims outside the provided evidence.
* **Keyword Verification**: The review texts contain the expected validation keywords.

2. **Response Time** - API queries return results within 3 seconds for 95% of requests.        

Mark the query result as accurate when:
* **Latency**: Must remain under 3 seconds per query
* **Cold Start Behavior (Known issue)**: If the first query reports a latency significantly higher than 3 seconds, this is expected behavior caused by AWS Lambda container cold starts and OpenSearch connection pooling. Remediate this by executing the script again.

3. **Query Variety** - System successfully handles at least 5 different query types (ratings, sentiment, comparisons, trends, specific feedback). 

Mark the query result as accurate when:
* **Category coverage**: At least one query per each query types (ratings, sentiment, comparisons, trends, specific feedback)

4. **Guardrail rules** - The PoC architecture relies exclusively on semantic retrieval logic and does not integrate a calculation or statistical processing engine. When a user asks quantitative questions, the pipeline executes a hybrid refusal protocol.

Mark the query result as accurate when:
* **The system returns the mandatory policy message**: "Answering quantitative questions is not authorized for this assistant, but I can share what guests typically say about their experience!"
* **Qualitative Context Fallback**: To avoid presenting a cold error message, the pipeline immediately follows the refusal statement with a short, relevant qualitative summary grounded in retrieved review context.

5. **Query Generalization Rules** - the generated answers must meet specific generalization rules 

Mark the query result as accurate when:
* **Answer length & structure**: Brief responses limited to 2-3 sentences without markdown bullets.
* **Tone & Grammar**: Response contains flawless grammar and an engaging tone.
* **No copy&paste**: Rephrase and summarize retrieved evidence rather than copying or quoting raw review text directly.

# 5. Known Architectural Limitations

The TasteTrend Proof of Concept (PoC) prioritizes lightweight, rapid qualitative retrieval over complex retrieval routing and high-accuracy model architectures. While this design minimizes infrastructure complexity and cost for baseline testing, it introduces certain limitations. 

The following section supports manual validation and testing by helping to distinguish between unexpected system bugs and intentional architectural constraints:

* While **guardrail instructions** are written directly into the system prompt, LLMs don’t follow hard rules. Slight variations in how a query is phrased may occasionally trigger a refusal response on a valid qualitative query, or allow a quantitative question to pass through. Manual Verification: During evaluation, auditors should test diverse query phrasings to verify that guardrails trigger reliably.

* **Polarized Feedback:** When retrieved reviews contain extreme opposites (such as 5-star praise mixed with 1-star complaints), the model tends to smooth out the conflict into a neutral overall statement rather than explicitly contrasting both sides.

* **Multi-Location Comparisons:** To ensure fairness when comparing two or more locations the system fetches a balanced, fixed number of reviews for each entity. While this prevents one popular location from dominating the answer, it introduces a few trade-offs:  
  * **Less Depth per Location:** Capping review counts per entity keeps responses fast and focused, but complex queries asking about multiple specific details may lack full coverage.  
  * **Slightly Higher Latency:** Retrieving data for multiple locations requires additional processing time, which can modestly increase response latency.  
  * **Uneven Review Volume:** Comparing a well-reviewed location against a newer location with sparse reviews may cause lower-confidence matches to be included for the newer entity.

* **Location Name Phrasing:** The system filters reviews using exact location and restaurant names stored in the database. Using nicknames, abbreviations, or typos may bypass context filters, leading to incomplete or missing results.  

* **Search Relevance Cutoff:** The system uses a fixed relevance score threshold (0.7) to filter out off-topic reviews. For highly specific or uniquely phrased queries, this strict cutoff may occasionally discard relevant reviews, causing the assistant to respond with a *"No relevant information found"* fallback or less retrievals than 5.  

* **Time-Trend Analysis:** Search results are selected purely by topic similarity rather than date order. The system cannot analyze trends over time as it lacks chronological calculation capabilities.   

* **Unsanitized Review Context:** In this PoC, retrieved review text is passed directly into the AI model without security filtering. If a review contains hidden instructions or malicious text (Prompt Injection), it could trick the model into altering its standard response format. 
