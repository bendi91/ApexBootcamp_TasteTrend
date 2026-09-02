# TasteTrend Gen AI POC - Technical documentation

# Table of Contents

- [Architecture overview](#architecture-overview)
- [Phase 1: Data Discovery & Analysis](#phase-1-data-discovery-analysis)
  - [1.1 High-Level Data Profile](#11-high-level-data-profile)
      - [1.1.1 Review & transactional event datasets](#111-review-transactional-event-datasets)
      - [1.1.2 Restaurant info reference dataset](#112-restaurant-info-reference-dataset)
  - [1.2 Critical issue: Duplicate Unique Review Identifiers](#12-critical-issue-duplicate-unique-review-identifiers)
      - [1.2.1 Short description of the data corruption](#121-short-description-of-the-data-corruption)
      - [1.2.2 Potential origin and root cause](#122-potential-origin-and-root-cause)
      - [1.2.3 Downstream Impact Assessment](#123-downstream-impact-assessment)
      - [1.2.4 Conclusions](#124-conclusions)
      - [1.2.5 Resolving the duplication issue](#125-resolving-the-duplication-issue)
  - [1.3 Data Quality Registry & Standardization Requirements](#13-data-quality-registry-standardization-requirements)
- [Phase 2: Infrastructure Setup](#phase-2-infrastructure-setup)
- [Phase 3: ETL Pipeline Development](#phase-3-etl-pipeline-development)
  - [3.1 Mapping config](#31-mapping-config)
  - [3.2 ETL Lambda](#32-etl-lambda)
  - [3.3 Transformation Accuracy Validation](#33-transformation-accuracy-validation)
      - [3.3.1 Validation rules](#331-validation-rules)
      - [3.3.2 Validation results](#332-validation-results)
- [Phase 4: RAG Implementation](#phase-4-rag-implementation)
  - [4.1 Implementation details](#41-implementation-details)
  - [4.2 Validation results](#42-validation-results)
- [Phase 5: Bedrock Development](#phase-5-bedrock-development)
  - [5.1 Implementation details](#51-implementation-details)
  - [5.2 Known Limitation](#52-known-limitation)
- [Phase 6: API Gateway Setup](#phase-6-api-gateway-setup)
  - [6.1 Validating Phases 5 and 6](#61-validating-phases-5-and-6)
- [Price calculation](#price-calculation)

# Architecture overview

[Architecture overview](../docs/architecture-overview.png)

# Phase 1: Data Discovery & Analysis

The audit of TasteTrend datasets found substantial schema drift, missing values, near-duplicates and column format inconsistencies that must be standardized before any model building. A deeper investigation revealed serious Review ID duplication patterns and detected high risk dimensions assuming upstream join or data-generation fault. As a result, these dimensions are treated as unreliable and excluded from analysis and model building. However, one dataset shows no evidence of this corruption, offering promising prospects for future data expansion.

## 1.1 High-Level Data Profile

The incoming data package consists of five distinct datasets: one reference dataset providing core restaurant attributes, and four review & transactional event datasets (fact tables) capturing user reviews, financial metrics, and demographic dimensions.

### 1.1.1 Review & transactional event datasets

* Three of the four source fact tables are natively stored in a structured CSV format. However, the remaining dataset was delivered with a malformed file extension. Resolving this mismatch requires a simple file type conversion from TXT to CSV.  
* Each of the datasets is isolated to a single restaurant entity and maintains a uniform schema of 14 columns however the schema validation check reveals inconsistent column headers across the datasets which will require a header-normalization transformation step during ingestion.

### 1.1.2 Restaurant info reference dataset

* The `avg_stars` column contains static, duplicate values (`4.0`) across multiple restaurant entities, while the `total_reviews` column shows artificial data that does not align with the fact tables. Because these columns lack data integrity, they must be dropped from the source layer and dynamically aggregated from the fact tables as needed.  
* The `categories` column is worth splitting into a list/array if we want it usable for structured filtering or as RAG metadata rather than one long string.  
* The `location` column does not track actual neighborhoods, instead it is just a label unique to each source file. Since the `original_city` column proves that these restaurants are actually located in entirely different cities across the US, keeping the column name as `location` will cause confusion. Renaming it to `source_file_tag` will reflect its true purpose.

## 1.2 Critical issue: Duplicate Unique Review Identifiers

### 1.2.1 Short description of the data corruption

* Multiple rows share the same Review ID as well as the same review text, date and rating but have different records in customer name, party size, demographics and different values in the measure columns as well.   
* The review data and financial metrics likely originate from different sources.  
* While there are no exact row-level duplicates, the presence of duplicate review records introduces significant data quality risks.  
* Midtown is an exception — its IDs are 100% unique indicating an alternative upstream generation process than the rest of the input data.

### 1.2.2 Potential origin and root cause

* **Early assumption:** Each table visit generates a single review but there can be multiple financial records due to split checks → This logic is not supported by the current data structure:  
  * Identical Review ID rows contain conflicting information regarding customer IDs, party sizes and demographic data. These dimensions should theoretically share the exact same values if one feedback is being submitted per table.  
  * Even if multiple feedback entries are submitted for a single table, the recorded `party_size` should remain consistent, but the data reveals conflicting values.  
  * Identical Review ID rows show no internal consistency expected from real-world events. Total spent amounts and party sizes vary independently rather than forming a coherent split-check pattern.  
* These patterns suggest a systemic upstream failure rather than a localized edge case.  
* **Probable  root causes**:  
  * Theory 1: Many-to-many join fan-out: a join performed on a non-unique or improperly derived key, mechanically attaching unrelated financial/demographic rows to a review.  
  * Theory 2: ID collision at data-generation time: a script or a system accidentally produced the same `review_id` value multiple times for unrelated real-world events.

### 1.2.3 Downstream Impact Assessment

* As a consequence of these upstream anomalies, the integrity and reliability of the **financial metrics** require further auditing:  
  * `tip_amount` / `total_spent` × 100 closely matches the stored `tip_percentage`, typically under 0.1 percentage points, consistent with rounding across all four datasets including the ones with the ID problem. That's the opposite of what corrupted-by-join data looks like → there are no mismatched `tip_amount` - `total_spent` pairs.  
  * The `total_spent` values demonstrates reasonable median distributions and consistent per-person metrics across the datasets.  
  * Roughly 37% of the reviews across all datasets reflect a tipping rate exceeding 20%. Although this indicates a potential data anomaly, market research confirms that the variance aligns with US dining trends.  
  * While these findings serve as positive indicators of dataset health, the real-world origin or ground-truth accuracy of these data is still unclear → no source system, transaction log or audit trail exists to verify against.  
  * `total_spent` values get built from menu item prices (which often end in `.99`, `.95`, `.50`, `.00`) plus tax (a fixed percentage calculation) and a tip. It means some cent-endings should show up more often than others (so evenly spread values across 00–99 are suspicious). Chi-square goodness-of-fit test detects no clustering pattern → it doesn't rule out some other synthetic method that might have been used nor logically guarantee the data is real.

* **Party size** inconsistencies:  
  * The row count for identical Review IDs frequently surpasses the number specified in the party sizes.  
  * The value 7 is missing across all datasets despite a range of 1 to 8. This strongly indicates that the data was sampled from a fixed list [1,2,3,4,5,6,8] rather than a true real-world distribution.  
  * Dividing `total_spent` by `party_size` reveals minor anomalies, dropping as low as $1.00–$1.33. While the low volume of these records suggests no systemic data quality issues, it further highlights the structural unreliability of the `party_size` column.   

* **Customer ID** inconsistencies:  
  * Each customer identifier follows a `Prefix_####` pattern with a 4-digit numeric suffix (max 10,000 combinations per prefix). Three of the four datasets (downtown, uptown, and midtown) use the prefix `"Customer_"` and overlapping numeric values do occur between them.  
  * Given the small 10,000-value space, this is statistically consistent with random chance rather than any actual shared customer identity across restaurants.  
  * Eastside dataset uses `"Guest_"` as the prefix so it shares zero direct overlap with any other dataset's IDs, even where numeric suffixes coincidentally match. Uptown dataset also contains a second minor prefix variant `"Client_"` instead of `"Customer_"`. 

### 1.2.4 Conclusions

* The Midtown data profile demonstrates that these data quality issues are not systemic across all source dataset. As we expand and integrate new datasets, our goal is to ensure they follow the more reliable backend processes used by Midtown to maintain overall data consistency.  
* Completely removing all out-of-scope columns would eliminate high-value insights for future analysis or model development, even if those data present low data confidence in their current state. Instead, a more balanced approach is to flag and nullify high-risk data so our teams know exactly which parts of the dataset require careful handling or extra verification.  
* Leaving the door open for future remediation or onboarding new datasets with no such quality issues ensures to unlock significant analytical and modeling potential if the project scope expands.

| Tier | Columns | Status | Action |
| ----- | ----- | ----- | ----- |
| High confidence  | `review_id, rating, review_text, review_date` | Consistent | Use directly |
| Medium confidence  | `customer_id, total_spent, tip_amount, tip_percentage`  | Internally consistent but no audit trail to trace its origin | Use but don’t present as ground truth for restaurant economics |
| Low confidence  | `party_size, age_range, gender, ethnicity`  | Might contain valid records, but they are indistinguishable from the corrupted ones | Do not use, flagged as high risk for analysis & model building |

### 1.2.5 Resolving the duplication issue

1. Since financial metrics and individual payment splits do not serve current project goals, the duplicate entries must be removed by aggregating the transactions at the review level.   
2. Given that the origin of the financial metrics remains unverified, all financial metrics (`total_spent`, `tip_amount`, `tip_percentage`) must be nullified for duplicated entries to prevent the utilization of corrupted data.   
3. Regarding duplicated entries, it is impossible to verify which `customer_id`,  `party_size` and demographic values are accurate → these fields must be set to null as well.   
4. Although these dimensions and financial metrics are currently out of scope for model building, they should be kept due to their potential strategic value in the future.  
5. Keep the Customer IDs for unique entries and treat it as only meaningful in combination with `restaurant_name`, never `customer_id` alone because recurring IDs are likely a byproduct of random chance.  
6. Identical Review ID rows will be flagged via a new `transaction_count` column to track the exact volume of duplicate entries in the source table.   
   `transaction_count > 1` indicates that the Review ID isn’t unique and contains duplicate entries in the source table.

## 1.3 Data Quality Registry & Standardization Requirements

Listing all structural anomalies, data inconsistencies, and quality defects identified in the source datasets during the data profiling phase.

1. **Inconsistent column headers**

**Columns requiring standardization**

| downtown | eastside | uptown | midtown | schema mismatch correction |
| :--- | :--- | :--- | :--- | :--- |
| review_id | review_number | id | review_id | review_id |
| customer_name | guest_name | name | customer_name | customer_id |
| date | visit_date | review_date | date | review_date |
| rating | satisfaction_score | star_rating | rating_out_of_10 | rating |
| review_text | feedback_comments | comments | review_text | review_text |
| location | venue_location | venue | location | location |
| business_name | restaurant_name | establishment | restaurant_name | restaurant_name |

**Columns already consistent across all four datasets** (no renaming needed): `total_spent`, `tip_amount`, `tip_percentage`, `party_size`, `age_range`, `gender`, `ethnicity`

2. **Near-duplicates in Review IDs**

   * The Eastside and Uptown datasets contain records with systematic identifier mutations carrying “**_copy**” and **“_dup**” suffixes. Even though they look like copies, minor variance is detected across column values.

   * **Issue fix:** These records lack any verifiable operational origin  so that they must be dropped entirely.

3. **Mixed date formats**

   * The Eastside dataset contains three date formats in the same column. Other datasets utilize a standard timestamp format.

   * **Issue fix:** All dates must be normalized into a standardized `YYYY-MM-DD` format.

4. **Duplicated entries in Review IDs** ([discussed in a previous section](#1.2.5-resolving-the-duplication-issue))

5. **Review ID encoding format** might vary across datasets: Initial profiling confirms that `review_id` utilizes Base64URL encoding uniformly across all four datasets. However an encoding validation audit is required to ensure there are no parsing issues in the columns.

6. **Inconsistent rating encodings**

   * Downtown & Eastside: numeric 1–5

   * Midtown: numeric but on a 0–10 scale, and only even numbers (2,4,6,8,10) → needs to be converted to 1-5 numeric range 
   
   * Uptown: stored as literal star emoji strings (⭐⭐⭐) → needs numeric  conversion  
   
7. **Missing values** in `total_spent` column. **Issue fix:** Derives conditionally whenever valid `tip_amount` and `tip_percentage` values are present.

8. **Dropping tip_percentage column**: After the imputation of missing `total_spent` values, this source column becomes functionally redundant and should be dropped. It can be derived from `tip_amount` and `total_spent` as needed.

9. **Dimensionality reduction**

   * Extracting the unique identifier from the source file name and appending it as a new `restaurant_id` column. Because each dataset is strictly isolated to a single restaurant entity, the newly injected ID column can replace `restaurant_name` and `location` dimensions.

   * To establish relational integrity, the new `restaurant_id` must be injected into the reference table as well. In this case, the ID has to be derived from the `location` column because file-name detection can't work there.

10. Data inconsistencies in the **reference dataset** ([discussed in a previous section](#1.1.2-restaurant-info-reference-dataset))

11. Missing review and demographic records

    * Demographic data is classified as a high-risk analytical asset → No imputation is required.

    * Attempting to impute missing review attributes such as review texts and ratings would introduce unacceptable statistical noise → No imputation is required.

12. Potential missingness in tip amounts

    * We cannot automatically assume that a zero tip amount is accurate data. It is possible that the system logs an empty or missing value as zero.

    * However the `tip_amount = 0` is a small, consistent minority across all four files (2.9–3.8%) → No change is required.

# Phase 2: Infrastructure Setup

The entire AWS infrastructure is provisioned using Terraform and organized into four modular configuration files:

* [API Gateway terraform config](../api_gateway.tf): Provisions a regional REST API Gateway with a public /query POST endpoint, routing incoming HTTP requests directly to the Proxy Lambda function and granting the necessary execution permissions to deploy the interface to a poc stage.

* [IAM terraform config](../iam.tf): Defines IAM roles and fine-grained permission policies that grant each of the three Lambda functions (ETL, Embedding, Proxy) least-privilege access to exactly the services and resources they individually need — including CloudWatch, S3, Amazon Bedrock, KMS encryption, and OpenSearch — with permissions scoped per-function to specific buckets, models, and endpoints rather than granted broadly.

* [Lambda terraform config](../lambda.tf): Packages Python source code into ZIP archives, deploys three AWS Lambda functions (ETL, Embedding and Proxy) with supporting dependencies and CloudWatch logging, and configures S3 event triggers to automatically execute the ETL and embedding pipelines when files are added to the data lake.

* [Main terraform config](../main.tf): Provisions the baseline infrastructure for the environment, including provider settings, encrypted S3 buckets for data lake storage and configuration files, a single-node OpenSearch vector database domain and key environment deployment outputs. Encryption at rest is implemented using AWS-managed keys (SSE-KMS), guaranteeing standard compliance and zero-cost setup.

# Phase 3: ETL Pipeline Development

## 3.1 Mapping config

Schema mapping and rating range normalizations are driven entirely by an external CSV configuration file [Mapping config](../config/mapping_config.csv) created during data discovery. By parameterizing header mappings and rating scale divisors (converting 1–10 or 1–100 scales to the standard 1–5 baseline range), the ETL pipeline achieves full dynamic adaptability without requiring code changes or maintaining hardcoded dataset rules. 

## 3.2 ETL Lambda

The [ETL Lambda](../src/01_etl/etl_lambda.py) lambda function acts as an automated ETL pipeline that ingests raw dataset and reference CSV files from an S3 bucket, executes several data transformation steps and writes normalized output files back to a processed path.

The sequence of ETL transformation steps directly mirrors  the data inconsistencies listed in the [Data Quality Registry & Standardization Requirements](#1.3-data-quality-registry-&-standardization-requirements).

### Step 1 — Validate incoming file & normalize column headers
**Functions:** `detect_source`, `normalize_headers`, `transform_fact_table`

- **`detect_source`:** Identifies the dataset's origin by matching keywords in the S3 file path against the configured source names (sorted by length to avoid partial-match collisions).
- **`normalize_headers`:** Standardizes heterogenous column names by looking up the source's mapping rules and renaming the DataFrame's columns to fit the unified schema, logging a warning if any expected headers are missing.
- **`transform_fact_table`:** The main orchestrator, which contains a final step to reindex columns and guarantee deterministic positional order.

### Step 2 — Near-duplicates in Review IDs
**Function:** `drop_near_duplicates`

Identifies and removes rows with `_copy` or `_dup` suffixes in their `review_id`. Before dropping them, it counts how many near-duplicates exist for each base ID and maps that count back to the surviving row in a temporary `_near_dup_count` column, so Step 4 can accurately preserve total transaction counts.

### Step 3 — Mixed date formats
**Function:** `normalize_dates`

Parses the `review_date` column and standardizes valid values into a uniform ISO `YYYY-MM-DD` format. Any dates that cannot be parsed are coerced to missing values, and the function logs the count of successfully formatted versus failed dates for tracking.

### Step 4 — Resolve duplicate review IDs
**Function:** `resolve_duplicate_review_ids`

Collapses duplicate review submissions into a single consolidated record. It performs per-field coalescing across sibling rows to preserve critical review data (`review_date`, `rating`, `review_text`), explicitly nullifies financial and demographic fields to prevent data conflicts, and calculates the `transaction_count` metric per `review_id` to preserve raw entry volume.

### Step 5 — Review ID encoding may vary across datasets
**Function:** `validate_review_id_encoding`

Validates whether values in the `review_id` column adhere to valid Base64URL encoding standards. Logs a warning with sample invalid entries if any fail the check — an operational audit that doesn't alter the underlying data.

### Step 6 — Normalize rating values
**Function:** `normalize_rating`

Scans the `rating_divisor` column in **[Mapping config](../config/mapping_config.csv)**; a divisor value greater than 1 triggers scale normalization down to the 1–5 baseline range. Standardizes emoji-only ratings by removing Unicode variation selectors/ZWJ markers and counting remaining visual glyphs. Coerces mixed strings (combining numbers, letters, or emojis) to `NULL` while logging CloudWatch warnings, to surface raw data defects without crashing the pipeline.

### Step 7 — Missing values in `total_spent`
**Function:** `derive_missing_total_spent`

Dynamically calculates missing `total_spent` values using available tip metrics. Where `total_spent` is missing but both `tip_amount` and a positive `tip_percentage` exist, it derives the total and rounds to two decimal places, logging the number of recovered entries. If `total_spent`, `tip_amount`, or `tip_percentage` is entirely absent from the dataset's columns, the function returns the DataFrame unchanged rather than deriving anything.

### Step 8 — Dropping `tip_percentage`
**Function:** `drop_tip_percentage`

Cleans up the dataset by dropping the `tip_percentage` column once downstream calculations are complete, eliminating redundant data and keeping the schema lean.

### Step 9 — Dimensionality reduction
**Function:** `apply_restaurant_id`

Assigns the source dataset name as a standardized `restaurant_id` column and removes redundant text-based location and restaurant-name columns, logging the dropped fields for tracking.

### Step 10 — Fix reference table's anomalies
**Function:** `process_reference_dataset`

Normalizes the reference table by deriving a primary `restaurant_id` from the location string, formatting category lists as valid JSON arrays, dropping unreliable aggregate fields (`avg_stars`, `total_reviews`), and renaming the `location` column to `source_file_tag` to support downstream joins. Raises a `ValueError` and aborts if `location` is missing.

## 3.3 Transformation Accuracy Validation

This validation is designed for local execution, directly testing the ETL transformation to eliminate the operational and cost overhead of a cloud-hosted test infrastructure. It does not replace CloudWatch monitoring, both methods must be used for detecting errors and warnings in the transformation process. 

The validation script simplifies debugging by logging the Review IDs of the affected rows whenever an error is detected.

Related files:

* [ETL Lambda Validation](../tests/validate_etl_lambda.py): Validates data accuracy against the standardized CSV output produced by the ETL Lambda function.

* [ETL Lambda Validation Report](../tests/validation_report_20260824_033047.md): Upon completion, the script captures and writes all validation logs directly to a Markdown file for debugging.

### 3.3.1 Validation rules

1. Ensures ratings are within {1, 2, 3, 4, 5} and the processed ratings are validated against raw inputs across duplicate rows. A processed rating may only be NULL if every raw record sharing that `review_id` was also NULL. If a valid rating existed on any duplicate raw row, it must survive transformation into the final output.  
2. Confirms all dates strictly match `YYYY-MM-DD` format.  
3. Enforces required schema compliance across all tables including strict positional column ordering for both fact tables and the reference table.  
4. Verifies that suffix patterns like **_copy** or **_dup** were completely removed during transformation.  
5. Checks Restaurant ID cross consistency: Confirms `restaurant_id` values exist in the reference file and match across datasets.  
6. Verifies `review_id` values pass Base64URL decoding checks.  
7. Ensures `total_spent` was correctly recalculated whenever raw data had `total_spent` as null but contained valid `tip_amount` and `tip_percentage` values. Excludes near-duplicate rows and duplicate-collapsed rows because these entries were correctly nullified during the ETL transformation.  
8. Verifies each `review_id` is unique in the processed outputs and reconciles source dataset’s row counts against the `transaction_count` multiplier (if transaction_count = 3, the row must be counted 3 times ensuring an exact row-count match with raw inputs).
9. Confirms specific columns were nulled out on duplicate entries such as `customer_id`, `total_spent`, `tip_amount`, `party_size`, `age_range`, `gender`, `ethnicity`.
10. Performs a row-level integrity check on direct pass-through text, demographic, and financial fields (`review_text`, `customer_id`, `party_size`, `age_range`, `gender`, `ethnicity`, `total_spent`, `tip_amount`) for unique records (`transaction_count = 1`). For each such row, the value in the processed output is compared against that *same* ReviewID’s raw value. A value that has real data in the raw source but is blank in the processed output is flagged individually with the specific ReviewID reported for debugging. This guarantees no silent data loss occurs on a per-record basis.

### 3.3.2 Validation results

✅ All datasets passed the validation process with no error or warning messages. 

# Phase 4: RAG Implementation

The [Embedding Lambda](../src/02_embedding/embedding_lambda.py) lambda function processes standardized CSVs stored in S3 and generates vector representations using LLM embeddings, then indexes the resulting metadata into an OpenSearch cluster.

## 4.1 Implementation details

* **Vectorization**: Converts raw review text into 1024-dimensional dense vector embeddings using the **Cohere Embed English V3** model via Amazon Bedrock for cost optimization.  
* The following technologies align directly with the project's core business requirements:  
  * Using **k-NN Vector Search** enables natural language queries based on semantic meaning rather than exact keyword matching.  
  * **HNSW graph algorithm** optimizes vector navigation to deliver low-latency similarity search results, ensuring the RAG pipeline comfortably meets the under 3 seconds success criteria.  
  * Deploying the **FAISS engine** helps to minimize operational overhead and leverage low-cost options.  
* **Fault Optimization**: Uses a SigV4-signed HEAD check in OpenSearch. If a ReviewID is already indexed, it skips the Bedrock call entirely, protecting against redundant charges during pipeline retries.   
* **Text Preprocessing**:   
  * The embedding model has a 2,048 character threshold. Review texts exceeding 2,000 characters are truncated before vectorization.  
  * Character distribution analysis shows 4% of dataset records exceed this limit, resulting in minimal data loss.  
  * Implementing a multi-segment chunking strategy would add unnecessary pipeline complexity, directly opposing our design goal to minimize operational overhead. Truncation provides a practical baseline, but this approach should be audited before moving to production.

## 4.2 Validation results

The successful deployment and state of the RAG implementation can be validated directly through the AWS Management Console by inspecting the health metrics, index mappings and document ingestion statistics within the Amazon OpenSearch Service cluster. 

The Cluster configuration perfectly mirrors the free-tier settings defined in the terraform configuration:

* Standard create ✅  
* Dev/test template ✅  
* Domain without standby ✅
* **Availability Zone(s)**: `Single-AZ`
* **Instance type**: `t3.small.search`
* **Number of data nodes**: `1`
* **Storage type**: `EBS`
* **EBS volume type**: `gp3`
* **EBS volume size (GiB)**: `10`

The AWS Management Console shows **1,242** document count for the **tastetrend-reviews** index, perfectly matching the total row count of non-null `review_text` records across all standardized CSV files.

**Cluster health: Yellow →** The cluster runs as a Single-Node cluster with unassigned replica shards. OpenSearch requires primary shards and replica shards to be placed on different physical nodes for data redundancy. Because this cluster only has 1 data node provisioned to stay cost-optimized for the PoC, OpenSearch cannot place the replica shards anywhere. 

# Phase 5: Bedrock Development

This phase implements RAG orchestration as a custom-built Lambda function [Proxy Lambda](../src/03_proxy/proxy_lambda.py) rather than provisioning an Amazon Bedrock Agent. This was a deliberate engineering decision because utilizing Bedrock Agents would introduce serious per-invocation costs directly violating our core low-budget architectural strategy. The current lambda implementation provides an optimal balance between low execution complexity and precise retrieval control, offering far greater flexibility over query construction, dynamic filtering and score thresholding than a managed Amazon Bedrock Knowledge Base configuration.

## 5.1 Implementation details

As a proof-of-concept designed to minimize operational overhead and maximize scalability, the architecture prioritizes cost-optimized models accepting a slight trade-off in response sophistication compared to enterprise-tier models.

* **Query Vectorization**: Embeds incoming user queries using Bedrock's **Cohere Embed English** model to map natural-language questions into the exact 1024-dimensional vector space as the indexed reviews.  
* **Restaurant Targeting**: Before retrieval the lambda function determines which restaurant(s) to scope the search to. Matching question text against both known location tags like "downtown" and real restaurant names pulled from the reference table like "Village Whiskey". If the text names more than one restaurant, those take priority, enabling comparison queries. Otherwise, an explicit `restaurant_id` field in the request body is used if provided, falling back to whatever single restaurant the text extraction found.   
* **Semantic Retrieval & Filtering**: Retrieves the top candidate reviews (`TOP_K = 5`) via k-NN vector search. For single-restaurant queries, it applies a dynamic score cutoff threshold (`RELATIVE_RELEVANCE_THRESHOLD = 0.7`) relative to the top match, discarding weak semantic matches to reduce noise in the retrieved context. For multi-restaurant comparison queries, this score cutoff is intentionally disabled since retrieval is split across `N` restaurants (capped at `K=2` per entity), applying the same relative threshold per-restaurant would risk discarding a restaurant's only relevant reviews if its best match scored lower than another restaurant's best match.  
* **Keyword Fallback**: If the restaurant-filtered k-NN search returns no semantically similar reviews, the system falls back to a standard OpenSearch keyword (text-match) search against the same restaurant filter ensuring a query for real but under-represented content isn't met with an empty result. The relative relevance threshold score is not applied to fallback results, since keyword-match scores aren't comparable to the vector-similarity scores the relevance threshold is calibrated for.   
* **Grounded Text Generation**: Constructs a structured context block from retrieved reviews and passes it to **AWS Nova Micro** via Amazon Bedrock. Low inference temperature and strict system prompt constraints instruct the model to generate answers using only retrieved evidence.  
* **Prompt Engineering Strategies**:  
  * Configured a customer-friendly assistant persona delivering professional, approachable responses suited for a restaurant recommendation system.  
  * Enforces strict length control (2–3 sentences) and excludes markdown bullet lists or long structural intros for cleaner output.  
  * Writes in clear and grammatically correct sentences explicitly answering questions with its own words rather than copying the review texts.  
* **API Gateway Integration**: Designed around the standard API Gateway proxy request/response format → handling stringified JSON bodies and returning explicit status codes alongside source metadata for front-end transparency.

## 5.2 Known Limitation 

These vulnerabilities must be thoroughly audited before moving to production:

* **Guardrail rules in prompt engineering** to prevent hallucinations:   
  * Rule 1: If the user explicitly asks for exact mathematical calculations, the model refuses with the following phrase: “*Answering quantitative questions is not authorized for this assistant, but I can share what guests typically say about their experience!*”  
  * Rule 2: Upon triggering the quantitative guardrail, the system executes a graceful fallback mechanism: Rather than terminating the interaction with a cold error message, the model declines the calculation and offers a relevant qualitative insight for the user.  
  * LLMs do not strictly execute hard rules. Relying purely on prompt instructions creates deterministic failures where slight phrasing variations in qualitative queries can accidentally trigger the guardrail refusal, or vice versa.  
  * Integrating structured tools (SQL / Pandas execution layers) would systematically resolve quantitative calculations but this exceeds the current scope of this baseline PoC.   
* **Polarization compression** in sentiment related questions: when retrieved reviews contain extremely polar opposites (5-star reviews saying "amazing service" and low star reviews saying "terrible service"), standard generative summarization tends to flatten the conflict into a neutral statement. Resolving this issue requires specialized prompt tuning and sentiment pre-classification which falls outside the scope of this baseline PoC.  
* Comparison questions need a **balanced retrieval strategy** ensuring every entity gets equal representation in the results. This approach neutralizes single-source context dominations but introduces certain limitations:   
  * Applying a static `TOP K = 5` retrieval depth to multi-entity comparative queries causes linear context expansion, triggering prompt bloat and 'lost-in-the-middle' attention degradation. Capping retrieval at `K = 2` per entity reduces token overhead but introduces a **context-depth trade-off**, where complex multi-attribute queries may lack sufficient evidence due to constrained sample sizes per entity.   
  * Running multi-entity retrievals might increase **API latency**.  
  * When comparing data-rich and data-sparse target entities, retrieving fixed K units per entity leads to **noise injection** from lower-confidence vector matches. 

  Implementing dynamic, entity-adaptive context allocations and latency optimizations requires complex retrieval routing that exceeds the scope of this baseline PoC.

* While **metadata filtering** on restaurant names effectively prevents cross-restaurant hallucination, it relies on exact case-insensitive substring matching against known location tags and the restaurant names stored in the reference table. Non-standard phrasing still bypasses extraction: a nickname, a misspelling or a partial name not present in the reference table won't be recognized, and the query falls through to unfiltered search across all restaurants. Remediating this fully would require fuzzy matching or NER which increases code complexity beyond the scope of this proof-of-concept.   
* Applying a **static relative relevance threshold** (`0.7`) creates a rigid context-trimming boundary. No single static threshold universally aligns across all retrieval scenarios and it risks over-pruning valid context and prematurely triggering 'no information found' fallbacks. Replacing this fixed threshold with dynamic Top-K retrieval and secondary semantic reranking exceeds the scope of this baseline PoC.  
* **Temporal hallucinations** in trend related questions: the current vector search retrieves documents based on semantic similarity, not chronological distribution. LLMs lack native capabilities for aggregated time-series computation. Enabling such an analysis exceeds the scope of this baseline PoC.  
* **Indirect Prompt Injection**: passing unfiltered user review text directly into the generation prompt without sanitization introduces serious risks. Malicious instructions embedded in retrieved documents can manipulate LLM output logic. Fixing this requires adding dedicated security layers such as AWS Bedrock Guardrails, regex input filters or separate pre-processing Lambda functions for scanning and sanitizing retrieved review text before feeding it to the model. This implementation exceeds the scope of this baseline PoC.

# Phase 6: API Gateway Setup

This final phase completes the serverless inference architecture by provisioning a public REST API interface via Terraform to expose the RAG pipeline to end users.

## 6.1 Infrastructure Summary

* **Regional REST Interface:** Provisions a regional **aws_api_gateway_rest_api** instance deployed in `eu-central-1` region to act as the primary entry point for natural language analytics queries.  
* **Resource Routing & Integration:** Exposes a public /query endpoint accepting POST requests, wired directly to the Proxy Lambda via AWS_PROXY integration to stream raw JSON payloads straight to the inference function.  
* **Resource-Based Access Control:** Configures explicit aws_lambda_permission resources allowing API Gateway to trigger the Proxy Lambda, scoped strictly to the execution ARN of the API Gateway instance.  
* **Stage Deployment Automation:** Deploys the REST API to a live poc environment stage, utilizing hash-based redeployment triggers (`sha1`) to automatically capture routing and method schema updates during infrastructure updates.  
* **Alignment with SOW Boundaries:** Configures NONE authentication on the endpoint, keeping access open to fulfill the PoC scope requirements while deliberately excluding complex authentication controls.

## 6.2 Validating Phase 5 and Phase 6

The  [RAG pipeline validation](docs/RAG_pipeline_validation.md) document details the end-to-end validation methodology, demonstrating real-world pipeline execution by simulating user API requests and evaluating generated responses. 

# Price calculation

The TasteTrend architecture is engineered to minimize operational expenditure in the `eu-central-1` region by leveraging a hybrid serverless and low-cost deployment strategy:

* **Free Tier**: Lambda (256MB–512MB execution profiles), S3 storage, and Amazon CloudWatch log groups (configured with a 14-day retention policy) are sized to operate entirely within the AWS Free Tier allowances generating near-zero runtime costs.  
* **Cost-Minimized Infrastructure** (OpenSearch, Bedrock, API Gateway): For services outside the Free Tier, operational expenses are strictly controlled by using low-cost configurations and near-zero per-query inference overhead.

| AWS Service | Provisioned Resources | Estimated Monthly Usage  | Estimated Monthly Cost (USD) |
| ----- | ----- | ----- | ----- |
| **S3** | 2 buckets (Data Lake & Config)  | Uses less than 5 GB storage + AWS-managed SSE key  | **$0.00** |
| **Lambda** | 3 lambda functions (ETL, Embedding, Proxy)  | Doesn’t exceed the limit of 1 million requests per month | **$0.00** |
| **CloudWatch** | 3 log groups with 14-day retention | Stay within the 5 GB free storage | **$0.00** |
| **OpenSearch** | T3.small.search instance (Single AZ, 1 node) + EBS (gp3, 10GB) | $0.042 per hour → roughly $30.66 per month  + $0.1452 per GB / month | **$30.81** |
| **Bedrock** | Cohere Embed 3 English + Amazon Nova Micro  | $0.10 per 1M input tokens + $0.046 per 1M input tokens, $0.184 per 1M output tokens | ~ **$0.13** |
| **Amazon API Gateway** | Rest API | $3.70 per million request | ~ **$0.04** |
| **Estimated total monthly cost** | | | ~ **$31.00** |
