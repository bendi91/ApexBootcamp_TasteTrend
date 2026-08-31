# =============================================================================
# TasteTrend TERRAFORM configurations - LAMBDA
# =============================================================================
#
# ---------------------------------------------------------------------------
# 1. Compresses python scripts into a ZIP file so it can be uploaded to AWS
# ---------------------------------------------------------------------------
# A) ETL Lambda
data "archive_file" "etl_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/src/01_etl/etl_lambda.py"
  output_path = "${path.module}/builds/etl_lambda.zip"
}

# B) Embedding Lambda
data "archive_file" "embedding_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/src/02_embedding/embedding_lambda.py"
  output_path = "${path.module}/builds/embedding_lambda.zip"
}

# C) Proxy Lambda
data "archive_file" "proxy_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/src/03_proxy/proxy_lambda.py"
  output_path = "${path.module}/builds/proxy_lambda.zip"
}

# ---------------------------------------------------------------------------
# 2. Configures a 3rd-party Pandas library layer
# ---------------------------------------------------------------------------

locals {
  # Public pandas layer for Python 3.11 / eu-central-1 (Klayers).
  # Verify latest ARN: https://api.klayers.cloud/api/v2/p3.11/layers/latest/eu-central-1/html
  pandas_layer_arn = "arn:aws:lambda:eu-central-1:770693421928:layer:Klayers-p311-pandas:22"
}

# ---------------------------------------------------------------------------
# 3. Deploys lambda functions to AWS using the local ZIP file package
# ---------------------------------------------------------------------------
# A) ETL Lambda --------------------------------
resource "aws_lambda_function" "etl_lambda" {
  function_name = "tastetrend-etl-lambda"
  role          = aws_iam_role.etl_lambda_role.arn
  handler       = "etl_lambda.lambda_handler"
  runtime       = "python3.11"

  # Uses the ZIP package created by the archive_file data source
  filename         = data.archive_file.etl_lambda_zip.output_path
  # Triggers a redeployment ONLY when the contents of the python file actually change
  source_code_hash = data.archive_file.etl_lambda_zip.output_base64sha256

  memory_size = 512
  timeout     = 60

  layers = [local.pandas_layer_arn]

  # Explicitly wait for logging permissions and log groups to exist before creating the function
  depends_on = [
    aws_cloudwatch_log_group.etl_lambda_logs,
    aws_iam_role_policy_attachment.attach_etl,
  ]
}

# B) Embedding Lambda --------------------------------
resource "aws_lambda_function" "embedding_lambda" {
  function_name = "tastetrend-embedding-lambda"
  role          = aws_iam_role.embedding_lambda_role.arn
  handler       = "embedding_lambda.lambda_handler"
  runtime       = "python3.11"

  # Uses the ZIP package created by the archive_file data source
  filename         = data.archive_file.embedding_lambda_zip.output_path
  # Triggers a redeployment ONLY when the contents of the python file actually change
  source_code_hash = data.archive_file.embedding_lambda_zip.output_base64sha256

  memory_size = 512
  timeout     = 60

  # OPENSEARCH_ENDPOINT is only known once the domain finishes creating —
  # referencing it here also gives Terraform an implicit dependency on
  # aws_opensearch_domain.review_vectors, so this function won't be created
  # with a blank/missing endpoint.
  environment {
    variables = {
      OPENSEARCH_ENDPOINT = aws_opensearch_domain.review_vectors.endpoint
    }
  }

  # Explicitly wait for logging permissions and log groups to exist before creating the function
  depends_on = [
    aws_cloudwatch_log_group.embedding_lambda_logs,
    aws_iam_role_policy_attachment.attach_embedding,
  ]
}

# C) Proxy Lambda --------------------------------
resource "aws_lambda_function" "proxy_lambda" {
  function_name = "tastetrend-proxy-lambda"
  role          = aws_iam_role.proxy_lambda_role.arn
  handler       = "proxy_lambda.lambda_handler"
  runtime       = "python3.11"

  filename         = data.archive_file.proxy_lambda_zip.output_path
  source_code_hash = data.archive_file.proxy_lambda_zip.output_base64sha256

  memory_size = 256
  timeout     = 30 # lightweighted processing, less resources are sufficient here

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = aws_opensearch_domain.review_vectors.endpoint
	  DATA_BUCKET         = aws_s3_bucket.data_lake.id
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.proxy_lambda_logs,
    aws_iam_role_policy_attachment.attach_proxy,
  ]
}

# ---------------------------------------------------------------------------
# 4. Grants permission to S3 to trigger the Lambda and sets up an 
# automation loop to process files dropped into the data lake
# ---------------------------------------------------------------------------
# A) ETL Lambda
resource "aws_lambda_permission" "allow_s3_invoke_etl" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.etl_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.data_lake.arn
}

# B) Embedding Lambda
resource "aws_lambda_permission" "allow_s3_invoke_embedding" {
  statement_id  = "AllowExecutionFromS3Processed"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.embedding_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.data_lake.arn
}

# Proxy Lambda config is not needed here, it's invoked by the API gateway.

# ---------------------------------------------------------------------------
# 5. Configures the event trigger on the S3 bucket 
# to automatically execute the ETL process
# ---------------------------------------------------------------------------
resource "aws_s3_bucket_notification" "data_lake_etl_trigger" {
  bucket = aws_s3_bucket.data_lake.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.etl_lambda.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw/"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.embedding_lambda.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "processed/"
  }

  # S3 throws an Access Denied error during deployment if the notification is set up
  # before the Lambda function permissions are fully applied.
  depends_on = [
    aws_lambda_permission.allow_s3_invoke_etl,
    aws_lambda_permission.allow_s3_invoke_embedding,
  ]
}

# ---------------------------------------------------------------------------
# CloudWatch Log Group configs
# Short retention keeps volume well under the CloudWatch Logs free tier (5GB/mo)
# ---------------------------------------------------------------------------
# A) ETL Lambda
resource "aws_cloudwatch_log_group" "etl_lambda_logs" {
  name              = "/aws/lambda/tastetrend-etl-lambda"
  retention_in_days = 14
}

# B) Embedding Lambda
resource "aws_cloudwatch_log_group" "embedding_lambda_logs" {
  name              = "/aws/lambda/tastetrend-embedding-lambda"
  retention_in_days = 14
}

# C) Proxy Lambda
resource "aws_cloudwatch_log_group" "proxy_lambda_logs" {
  name              = "/aws/lambda/tastetrend-proxy-lambda"
  retention_in_days = 14
}