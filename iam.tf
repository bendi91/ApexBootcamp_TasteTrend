# =============================================================================
# TasteTrend TERRAFORM configurations - IAM
# =============================================================================
#
# ---------------------------------------------------------------------------
# 1. Configures the identity and security permissions required for the
# Lambda functions to safely interact with other AWS services
# ---------------------------------------------------------------------------
# A) ETL Lambda --------------------------------
resource "aws_iam_role" "etl_lambda_role" {
  name = "tastetrend-etl-lambda-role"
  # "Assume Role" policy: Gives the AWS Lambda service explicit permission to adopt this identity 
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# B) Embedding Lambda --------------------------------
resource "aws_iam_role" "embedding_lambda_role" {
  name = "tastetrend-embedding-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# C) Proxy Lambda --------------------------------
resource "aws_iam_role" "proxy_lambda_role" {
  name = "tastetrend-proxy-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# 2. IAM Policy for the Lambda functions that defines the exact resources 
# and API actions the functions are allowed to execute
# ---------------------------------------------------------------------------
# A) ETL Lambda --------------------------------
resource "aws_iam_policy" "etl_lambda_policy" {
  name        = "tastetrend-etl-lambda-policy"
  description = "Permissions for ETL Lambda to read/write S3 and write CloudWatch logs"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # CloudWatch: Allows to write print statements and runtime errors into monitoring logs
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.etl_lambda_logs.arn}:*"
      },
      {
        # Data Lake: Read/Write access to fetch raw files and save processed files
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      },
      {
        # Config Bucket: Read-only access to download setup CSVs
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.config_bucket.arn,
          "${aws_s3_bucket.config_bucket.arn}/*"
        ]
      },
      {
        # Encryption: Allows the code to decrypt bucket data on-the-fly using AWS KMS keys
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach Policy to ETL Lambda Role
resource "aws_iam_role_policy_attachment" "attach_etl" {
  role       = aws_iam_role.etl_lambda_role.name
  policy_arn = aws_iam_policy.etl_lambda_policy.arn
}

# B) Embedding Lambda --------------------------------
resource "aws_iam_policy" "embedding_lambda_policy" {
  name        = "tastetrend-embedding-lambda-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # CloudWatch: Allows to write print statements and runtime errors into monitoring logs
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.embedding_lambda_logs.arn}:*"
      },
      {
        # Read-only on the data lake — this Lambda only ever reads
        # processed/ files, it never writes back to S3.
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      },
      {
        # Bedrock's FM
        Effect   = "Allow"
        Action   = "bedrock:InvokeModel"
        Resource = "arn:aws:bedrock:eu-central-1::foundation-model/cohere.embed-english-v3"
      },
      {
        # Write access to the OpenSearch domain for indexing documents
        Effect = "Allow"
        Action = [
          "es:ESHttpPost",
          "es:ESHttpPut",
          "es:ESHttpGet",
          "es:ESHttpHead"
        ]
        Resource = "${aws_opensearch_domain.review_vectors.arn}/*"
      },
      {
        # Encryption: Allows the code to decrypt bucket data on-the-fly using AWS KMS keys
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      },
      {
      # Allow Marketplace Subscription
      Effect = "Allow"
      Action = [
        "aws-marketplace:ViewSubscriptions",
        "aws-marketplace:Subscribe"
      ]
      Resource = "*"
      }
    ]
  })
}

# Attach Policy to Embedding Lambda Role
resource "aws_iam_role_policy_attachment" "attach_embedding" {
  role       = aws_iam_role.embedding_lambda_role.name
  policy_arn = aws_iam_policy.embedding_lambda_policy.arn
}

# C) Proxy Lambda --------------------------------
resource "aws_iam_policy" "proxy_lambda_policy" {
  name        = "tastetrend-proxy-lambda-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # CloudWatch: Allows to write print statements and runtime errors into monitoring logs
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.proxy_lambda_logs.arn}:*"
      },
      {
        # Embedding the incoming question — same model as the embedding Lambda
        Effect   = "Allow"
        Action   = "bedrock:InvokeModel"
        Resource = "arn:aws:bedrock:eu-central-1::foundation-model/cohere.embed-english-v3"
      },
      {
        # Generating the final answer - AWS Nova Micro
        Effect   = "Allow"
        Action   = "bedrock:InvokeModel"
        Resource = [
          "arn:aws:bedrock:*::foundation-model/amazon.nova-micro-v1:0",
          "arn:aws:bedrock:eu-central-1:${data.aws_caller_identity.current.account_id}:inference-profile/eu.amazon.nova-micro-v1:0"
          ]
      },
	  {
        # Read-only access to the reference file under processed/, used to
        # resolve real restaurant names (e.g. "Village Whiskey") to their
        # internal location tag for question-text targeting. This Lambda
        # never writes to S3.
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      },
	  {
        # Allows the code to decrypt the KMS-encrypted S3 bucket
        # (for the reference-file read above) and the KMS-encrypted
        # OpenSearch domain — same AWS-managed key, zero additional cost,
        # as used by etl_lambda_policy/embedding_lambda_policy.
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      },
      {
        # Read-only search access to OpenSearch — this Lambda only queries,
        # it never writes/indexes documents
        Effect = "Allow"
        Action = [
          "es:ESHttpGet",
          "es:ESHttpPost"
        ]
        Resource = "${aws_opensearch_domain.review_vectors.arn}/*"
      },
      {
      # Allow Marketplace Subscription
      Effect = "Allow"
      Action = [
        "aws-marketplace:ViewSubscriptions",
        "aws-marketplace:Subscribe"
      ]
      Resource = "*"
      }
    ]
  })
}

# Attach Policy to Proxy Lambda Role
resource "aws_iam_role_policy_attachment" "attach_proxy" {
  role       = aws_iam_role.proxy_lambda_role.name
  policy_arn = aws_iam_policy.proxy_lambda_policy.arn
}