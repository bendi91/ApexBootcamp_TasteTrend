# TasteTrend Gen AI POC

> **Note:** This is a mock Proof of Concept built as part of the Apex Lab MLOps Bootcamp program. The Statement of Work, client (TasteTrend LLC), and underlying review data are simulated for educational purposes.

An AWS-native serverless RAG (Retrieval-Augmented Generation) pipeline that transforms inconsistent, multi-source restaurant review data into a queryable natural-language knowledge base — demonstrating end-to-end ETL, vector embedding, and semantic search on AWS.

## What this does

TasteTrend ingests review data from four restaurant locations (each with different schemas, rating scales, and data quality issues), cleans and standardizes it, embeds review text into a vector database, and answers natural-language questions about ratings, sentiment, and customer feedback through a REST API.

## Architecture

`S3 → ETL Lambda → Embedding Lambda → OpenSearch → Proxy Lambda (RAG orchestration) → API Gateway`

Full architecture diagram and component breakdown: [`docs/Technical_documentation.md`](../docs/Technical_documentation.md#architecture-overview)

## Repo structure

```
├── api_gateway.tf      # API Gateway configuration
├── iam.tf              # IAM roles & permissions
├── lambda.tf           # Lambda function definitions & Cloudwatch configurations
├── main.tf             # Core configuration (Providers, S3, OpenSearch, Encryption, Environment Qutputs)
├── config/             # Schema mapping and rating divisor config (mapping_config.csv)
├── data/               # Raw source datasets
├── docs/               # Full project documentation (Technical Documentation, RAG Pipeline Validation, MVP Plan, User Guide)
├── src/                # Lambda source codes (ETL, embedding, proxy)
├── tests/              # Validation scripts, test queries and validation results
└── builds/             # Packaged Lambda deployment artifacts
```

## Quickstart

1. Provision infrastructure with Terraform (`main.tf`, `iam.tf`, `lambda.tf`, `api_gateway.tf`)
2. Run the ETL Lambda to ingest and clean the raw datasets
3. Run the Embedding Lambda to generates vector representations using LLM embeddings, then indexes the resulting metadata into an OpenSearch cluster
4. Run the validation script to simulate API queries — see [`docs/User_guide.md`](../docs/User_guide.md) for full setup and usage instructions

## Known limitations

This is a cost-optimized PoC, not a production system — quantitative queries (e.g. "average rating") are refused by design rather than calculated, retrieved review text is not sanitized against prompt injection, and there's no authentication on the API endpoint. Full list: [`docs/Technical_documentation.md § 5.2`](docs/Technical_documentation.md#52-known-limitation) and [`docs/User_guide.md § 5`](docs/User_guide.md#5-known-architectural-limitations).

## Estimated cost

~$31/month (eu-central-1)
Full breakdown: [`docs/Technical_documentation.md § Price calculation`](../docs/Technical_documentation.md#price-calculation)
