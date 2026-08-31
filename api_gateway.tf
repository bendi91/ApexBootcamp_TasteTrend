# =============================================================================
# TasteTrend TERRAFORM configurations - API GATEWAY
# =============================================================================
#
# 1. Create the Core REST API Gateway Instance
resource "aws_api_gateway_rest_api" "tastetrend_api" {
  name        = "tastetrend-analytics-api"
  description = "REST API Gateway for TasteTrend Gen AI PoC query interface"
  
  endpoint_configuration {
    types = ["REGIONAL"] # Deploys directly within your mandated eu-central-1 region
  }
}

# 2. Define the URL Resource Route Path (creates the /query endpoint)
resource "aws_api_gateway_resource" "query_resource" {
  rest_api_id = aws_api_gateway_rest_api.tastetrend_api.id
  parent_id   = aws_api_gateway_rest_api.tastetrend_api.root_resource_id
  path_part   = "query" # Resolves the URL structure to end with /query
}

# 3. Create an HTTP POST Method on the /query Route
resource "aws_api_gateway_method" "query_post_method" {
  rest_api_id   = aws_api_gateway_rest_api.tastetrend_api.id
  resource_id   = aws_api_gateway_resource.query_resource.id
  http_method   = "POST" # Accept incoming JSON bodies containing user questions
  authorization = "NONE" # Kept open/unauthenticated per SOW out-of-scope criteria
}

# 4. Connect the POST Method Directly to Your Proxy Lambda Trigger
resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.tastetrend_api.id
  resource_id             = aws_api_gateway_resource.query_resource.id
  http_method             = aws_api_gateway_method.query_post_method.http_method
  integration_http_method = "POST"
  
  # AWS_PROXY passes the raw HTTP payload directly to your Python code environment
  type                    = "AWS_PROXY" 
  uri                     = aws_lambda_function.proxy_lambda.invoke_arn 
}

# 5. Grant API Gateway Explicit Permission to Execute Your Proxy Lambda Function
resource "aws_lambda_permission" "allow_api_gateway_invoke" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.proxy_lambda.function_name 
  principal     = "apigateway.amazonaws.com"
  
  # Restricts execution access to this API Gateway instance's "poc" stage,
  # POST method, and /query resource specifically — not any stage/method/
  # resource under this API. A new route added later needs its own
  # aws_lambda_permission resource; it won't inherit this one.
  source_arn = format(
  "%s/%s/%s%s",
  aws_api_gateway_rest_api.tastetrend_api.execution_arn,
  aws_api_gateway_stage.poc_stage.stage_name,
  aws_api_gateway_method.query_post_method.http_method,
  aws_api_gateway_resource.query_resource.path
)
}

# 6. Deploy the API Configurations to a Live, Public-Facing Staging Level
resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.tastetrend_api.id

  # Forces a fresh deployment if any routing methods or inner integrations shift
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.query_resource.id,
      aws_api_gateway_method.query_post_method.id,
      aws_api_gateway_integration.lambda_integration.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "poc_stage" {
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.tastetrend_api.id
  stage_name    = "poc" # Sets your stage name path mapping environment variable
}