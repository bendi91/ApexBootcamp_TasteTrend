# =============================================================================
# TasteTrend TERRAFORM configurations - MAIN
# Core Environment Baseline
# =============================================================================
#
# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------
# Configure required providers and restrict versions to prevent breaking changes
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "eu-central-1"
}

# ---------------------------------------------------------------------------
# S3 Buckets
# ---------------------------------------------------------------------------
# Configures the data lake & uses the default AWS-managed KMS key (aws/s3) 
# to ensure zero-dollar overhead security compliance
resource "aws_s3_bucket" "data_lake" {
  bucket        = "tastetrend-data-lake-260810"
  force_destroy = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake_encryption" {
  bucket = aws_s3_bucket.data_lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms" # AWS-managed key
    }
  }
}

# Configures the config bucket & uses the default AWS-managed KMS key (aws/s3) 
# to ensure zero-dollar overhead security compliance
resource "aws_s3_bucket" "config_bucket" {
  bucket        = "tastetrend-configs-260810"
  force_destroy = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "config_bucket_encryption" {
  bucket = aws_s3_bucket.config_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms" # AWS-managed key
    }
  }
}

# Upload mapping_config.csv into the config bucket
resource "aws_s3_object" "mapping_config" {
  bucket = aws_s3_bucket.config_bucket.id
  key    = "mapping_config.csv"
  source = "${path.module}/config/mapping_config.csv"          # local file, relative to this .tf file
  etag   = filemd5("${path.module}/config/mapping_config.csv") # forces re-upload if the file content changes
}

# ---------------------------------------------------------------------------
# OpenSearch
# ---------------------------------------------------------------------------
# Mirrors the free-tier console configuration:
#   - Standard create,
#   - Dev/test template,
#   - Domain without standby,
#   - single-AZ,
#   - t3.small.search,
#   - 1 node
data "aws_caller_identity" "current" {}

resource "aws_opensearch_domain" "review_vectors" {
  domain_name    = "tastetrend-review-vectors"
  engine_version = "OpenSearch_2.11"
  cluster_config {
    instance_type             = "t3.small.search"  # Free-tier eligible instance
    instance_count             = 1                 # "Number of nodes: 1"
    dedicated_master_enabled  = false              # "Dev/test" template — no dedicated master nodes
    zone_awareness_enabled    = false              # "1-AZ (Single AZ)" — multi-AZ would force r7g/m7g instances
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = 10 # GB — stays within the 10GB/month free-tier EBS allowance
  }

  encrypt_at_rest {
    enabled = true # AWS-managed key — same zero-cost pattern as your S3 buckets
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  # Domain-level gate scoped to the embedding and proxy Lambda roles, the
  # only two that call OpenSearch. If a future Lambda needs OpenSearch access, 
  # add its role ARN here to avoid a 403 error.
  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = [
            aws_iam_role.embedding_lambda_role.arn,
            aws_iam_role.proxy_lambda_role.arn,
          ]
        }
        Action = [
          "es:ESHttpGet",
          "es:ESHttpPost",
          "es:ESHttpPut",
          "es:ESHttpHead",
        ]
        Resource  = "arn:aws:es:eu-central-1:${data.aws_caller_identity.current.account_id}:domain/tastetrend-review-vectors/*"
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# Environment Outputs
# ---------------------------------------------------------------------------
# 1. S3 bucket names
# A) The globally unique name of your raw input data lake storage bucket
output "data_lake_bucket_name" {
  value = aws_s3_bucket.data_lake.bucket
}

# B) The name of the background configuration storage bucket
output "config_bucket_name" {
  value = aws_s3_bucket.config_bucket.bucket
}

# 2. Lambda function names and their unique security ARN
# A) ETL Lambda
output "etl_lambda_function_name" {
  value = aws_lambda_function.etl_lambda.function_name
}

output "etl_lambda_function_arn" {
  value = aws_lambda_function.etl_lambda.arn
}

# B) Embedding Lambda
output "embedding_lambda_function_name" {
  value       = aws_lambda_function.embedding_lambda.function_name
}

output "embedding_lambda_function_arn" {
  value       = aws_lambda_function.embedding_lambda.arn
}

# C) Proxy Lambda
output "proxy_lambda_function_name" {
  value       = aws_lambda_function.proxy_lambda.function_name
}

output "proxy_lambda_function_arn" {
  value       = aws_lambda_function.proxy_lambda.arn
}

# 3. DATABASE VECTOR STORAGE:
# The active database web address the code uses to upload embeddings 
# and its unique security ARN
output "opensearch_domain_endpoint" {
  value = aws_opensearch_domain.review_vectors.endpoint
}

output "opensearch_domain_arn" {
  value = aws_opensearch_domain.review_vectors.arn
}

# PUBLIC API GATEWAY INTERFACE OUTPUT
output "tastetrend_query_api_url" {
  value       = "${aws_api_gateway_stage.poc_stage.invoke_url}/query"
}