# TasteTrend Gen AI POC - MVP Plan

# Executive Summary

TasteTrend LLC is deploying an AWS-native Generative AI and RAG solution to automate the processing of unstructured, multi-source restaurant review data and eliminate manual feedback analysis delays. This Proof of Concept demonstrates how inconsistent review datasets can be standardized into a queryable knowledge base, enabling restaurant partners to instantly retrieve contextual insights.

# Scope Matrix Table

**Data Ingestion & Coverage**
* Current POC Baseline: Static batch processing of  source datasets via manual S3 upload.
* MVP Release Scope: Automated ingestion pipelines scaling coverage to 20+ restaurant locations.
* Future Roadmap: Multi-tenant SaaS architecture handling live feeds for hundreds of restaurant chains.

**ETL & Data Transformation Pipeline**
* Current POC Baseline: Single lightweight Lambda function executing Pandas-based batch cleaning and schema normalization.
* MVP Release Scope: Expanding the lambda architecture to host 20+restaurant dataset conversions.
* Future Roadmap: Switching to SageMaker or Glue for more robust processing.

**Vector Database & Search Infrastructure**
* Current POC Baseline: Single-node OpenSearch cluster (t3.small.search, 1 AZ, Yellow health status) using FAISS & HNSW graph indexing.
* MVP Release Scope: Multi-AZ OpenSearch domain with active replica shards for Green cluster health, automated snapshot backups, and high availability.
* Future Roadmap: Managed Amazon OpenSearch Serverless for auto-scaling vector storage and multi-tenant data isolation across large customer bases.

**LLM architecture**
* Current POC Baseline: Simple models for cost saving RAG pipeline.
* MVP Release Scope: Increasing model complexity but keeping an eye on budget-friendly solutions.
* Future Roadmap: Enterprise LLMs with fine-tuned domain models to increase accuracy and response quality.

**Search & Retrieval Engine**
* Current POC Baseline: Single-pass k-NN search (K=5 and static relative relevance threshold of 0.7).
* MVP Release Scope: Hybrid semantic search with dynamic thresholding and entity-adaptive retrieval.
* Future Roadmap: Multi-pass semantic reranking and competitor benchmarking capabilities.

**Quantitative Guardrails**
* Current POC Baseline: Static prompt-based refusal.
* MVP Release Scope: Automated SQL/Pandas execution fallback layer for exact math/rating calculations.
* Future Roadmap: Machine learning recommendation engine and predictive sentiment modeling.

**Security & Input Filtering**
* Current POC Baseline: Unsanitized review text passed directly into the generation prompt.
* MVP Release Scope: Regex pre-processing input sanitization to block indirect prompt injection.
* Future Roadmap: Dedicated AWS Bedrock Guardrails and full IAM user authentication/authorization.

**Infrastructure & Transport**
* Current POC Baseline: Public API Gateway endpoint (NONE auth) with shifting deployment URLs.
* MVP Release Scope: Static AWS Route 53 Custom Domain Name with automated Terraform CI/CD.
* Future Roadmap:Production-grade monitoring, automated alerting, and partner UI web dashboard.

# Target Success Metrics

* **Data Processing Integrity:** Complete ingestion and schema normalization across 100% of provided review datasets, with full documentation of data quality fixes (deduplication, rating scaling, and missing value handling).

* **Vector Embedding Generation:** Successfully vectorize and index 100% of processed review texts into OpenSearch vector storage.

* **Query Accuracy & Grounding:** Achieve >80% context accuracy on natural-language qualitative queries based on manual validation.

* **API Response Latency:** Ensure 95% of API query requests return results within 3 seconds (excluding initial Lambda cold starts).

* **Query Variety Coverage:** Demonstrate reliable execution across at least 5 distinct query categories (ratings, sentiment, comparisons, trends, specific feedback) plus verifying the guardrail rules against quantitative questions.

# Technical Debt 

* **Prompt Guardrails & Input Security Vulnerabilities:** Relying purely on prompt-level refusal rules creates deterministic failures on quantitative queries, while passing unparsed review text into the generation prompt exposes the system to indirect prompt injection. Production deployment requires dedicated security scanning (such as AWS Bedrock Guardrails) and a structured analytics execution layer (SQL/Pandas) for calculations.

* **Static Retrieval & Relevance Rigidities:** Static K=2 multi-entity retrieval caps and fixed 0.7 relevance threshold creates context bloat, sentiment flattening on polar reviews, and risks over-pruning valid context. Releasing the MVP requires implementing adaptive context allocation, dynamic thresholding, and secondary semantic reranking.

* **Entity Extraction & Temporal Query Limitations:** Non-standard user phrasing bypasses basic name-filtering rules, and semantic vector search lacks native time-series capabilities for chronological trend queries. Addressing these constraints requires integrating Named Entity Recognition (NER) for venue alias mapping and building time-series aggregation capabilities.

# Out-of-Scope Implementations

* **Real-Time Ingestion & External Integrations:** Live data feeds, real-time ingestion pipelines, and direct integrations with third-party restaurant management systems are excluded.

* **User Interface & Authentication:** Web-based dashboards, native mobile UIs, and user authentication/authorization mechanisms are out of scope (API transport remains the primary interface).

* **Advanced Analytics & Multi-Tenancy:** Predictive modeling, machine learning recommendation engines, multi-tenant architectures, and historical time-series analytics are deferred to post-MVP phases.

* **Production Operations:** Production-grade monitoring, automated alerting frameworks, and enterprise CI/CD deployment pipelines will not be implemented during this phase.