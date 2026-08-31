import json
import os
import time
import requests
import boto3

# ---------------------------------------------------------------------------
# Dynamic API Endpoint Resolution
# ---------------------------------------------------------------------------
def get_api_gateway_url(api_name="TasteTrend", stage="poc", region="eu-central-1"):
    # 1. Check Environment Variable
    env_url = os.environ.get("TASTETREND_API_URL")
    if env_url:
        print(f"[CONFIG] Using API URL from environment variable: {env_url}")
        return env_url

    # 2. Try HTTP API Gateway (apigatewayv2)
    try:
        client_v2 = boto3.client("apigatewayv2", region_name=region)
        apis_v2 = client_v2.get_apis().get("Items", [])
        for api in apis_v2:
            if api_name.lower() in api.get("Name", "").lower():
                api_id = api["ApiId"]
                resolved_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/{stage}/query"
                print(f"[CONFIG] Resolved HTTP API URL: {resolved_url}")
                return resolved_url
    except Exception as e:
        print(f"[DEBUG] apigatewayv2 lookup failed: {e}")

    # 3. Try REST API Gateway (apigateway v1)
    try:
        client_v1 = boto3.client("apigateway", region_name=region)
        apis_v1 = client_v1.get_rest_apis().get("items", [])
        for api in apis_v1:
            if api_name.lower() in api.get("name", "").lower():
                api_id = api["id"]
                resolved_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/{stage}/query"
                print(f"[CONFIG] Resolved REST API URL: {resolved_url}")
                return resolved_url
    except Exception as e:
        print(f"[DEBUG] apigateway lookup failed: {e}")

    # 4. If dynamic resolution fails completely, throw an explicit error rather than attempting a dead default
    raise ValueError(
        "\n[ERROR] Could not dynamically resolve API Gateway URL from AWS.\n"
        "Please check your AWS CLI credentials or pass your active URL via environment variable:\n"
        "  $env:TASTETREND_API_URL='https://<NEW_API_ID>.execute-api.eu-central-1.amazonaws.com/poc/query'\n"
    )

# Initialize dynamic target API URL
API_URL = get_api_gateway_url(api_name="TasteTrend", stage="poc", region="eu-central-1")

# Resolve local directory paths for test query dataset and Markdown log output
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "test_queries.json")

# Generate timestamped filename (e.g., rag_evaluation_results_20260826_011554.md)
TIMESTAMP = time.strftime("%Y%m%d_%H%M%S")
LOG_FILE_NAME = f"rag_evaluation_results_{TIMESTAMP}.md"
LOG_FILE_PATH = os.path.join(BASE_DIR, LOG_FILE_NAME)

def run_evaluation():
    # Load the test suite containing benchmark queries and expected keyword assertions
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    passed_tests = 0
    total_tests = len(test_cases)
    
    # Initialize or overwrite the Markdown log file
    with open(LOG_FILE_PATH, "w", encoding="utf-8") as md_file:
        
        # -------------------------------------------------------------------
        # Write Report Header
        # -------------------------------------------------------------------
        md_file.write("# 🧪 RAG Pipeline Evaluation Report\n\n")
        md_file.write(f"**Target API:** `{API_URL}`  \n")
        md_file.write(f"**Timestamp:** `{time.strftime('%Y-%m-%d %H:%M:%S')}`\n\n")
        md_file.write("---\n\n")

        print("============================================================")
        print("RUNNING RAG EVALUATION")
        print("============================================================")

        # -------------------------------------------------------------------
        # Iterate Through Test Cases
        # -------------------------------------------------------------------
        for test in test_cases:
            print(f"\n[Test ID: {test['id']}] Category: {test['category'].upper()}")
            print(f"Query: \"{test['query']}\"")

            payload = {"question": test["query"]}
            start_time = time.time()

            try:
                # Dispatch POST request to API Gateway
                response = requests.post(
                    API_URL, 
                    json=payload, 
                    headers={"Content-Type": "application/json"}, 
                    timeout=30
                )
                elapsed_time = round(time.time() - start_time, 2)

                if response.status_code == 200:
                    res_data = response.json()
                    
                    # Unpack payload if returned as stringified JSON from Lambda proxy integration
                    if isinstance(res_data.get("body"), str):
                        res_data = json.loads(res_data["body"])

                    answer_text = res_data.get("answer", "")
                    sources = res_data.get("sources", [])

                    # Guardrail refusal phrases indicating authorized system behavior for math/aggregations
                    GUARDRAIL_PHRASES = [
                        "not authorized", 
                        "cannot calculate", 
                        "quantitative questions", 
                        "typically say"
                    ]
                    # Check if standard keywords match
                    keywords_found = [
                        kw for kw in test["expected_keywords"] 
                        if kw.lower() in str(answer_text).lower()
                    ]
                    # Check if a quantitative guardrail was correctly triggered
                    is_guardrail_triggered = (
                        test.get("category", "").upper() in ["RATINGS", "CALCULATIONS"] 
                        and any(phrase in str(answer_text).lower() for phrase in GUARDRAIL_PHRASES)
                    )
                    # Test passes if keywords match OR if the quantitative guardrail intercepted the request
                    is_passed = len(answer_text) > 0 and (len(keywords_found) > 0 or is_guardrail_triggered)

                    if is_guardrail_triggered:
                        keywords_found.append("GUARDRAIL_INTERCEPTED")

                    if is_passed:
                        passed_tests += 1
                        result_badge = "🟢 **PASSED**"
                        print(f"Status: 200 OK | Latency: {elapsed_time}s | RESULT: PASSED")
                    else:
                        result_badge = "🔴 **FAILED**"
                        print(f"Status: 200 OK | Latency: {elapsed_time}s | RESULT: FAILED")

                    # -------------------------------------------------------
                    # Append Test Result Entry to Markdown Log
                    # -------------------------------------------------------
                    md_file.write(f"### Test `{test['id']}`: {test['category'].upper()}\n\n")
                    md_file.write(f"* **Query:** \"{test['query']}\"\n")
                    md_file.write(f"* **Result:** {result_badge}\n")
                    md_file.write(f"* **Latency:** `{elapsed_time}s` | **Status Code:** `200`  \n")
                    md_file.write(f"* **Matched Keywords:** `{keywords_found}`\n\n")
                    md_file.write(f"**Generated Answer:**\n> {answer_text}\n\n")

                    # -------------------------------------------------------
                    # Render Collapsible Context Section (with Review IDs)
                    # -------------------------------------------------------
                    md_file.write(f"<details>\n<summary><b>View Retrieved Context ({len(sources)} chunks)</b></summary>\n\n")
                    if sources:
                        for idx, src in enumerate(sources, 1):
                            # Extract review ID with fallbacks to handle potential field variations
                            rev_id = src.get('review_id') or src.get('id') or 'N/A'
                            r_id = src.get('restaurant_id', 'unknown')
                            rating = src.get('rating', 'N/A')
                            
                            # Clean up line breaks for single-line log formatting
                            text = src.get('review_text', '').replace('\n', ' ')
                            
                            md_file.write(f"{idx}. **[ID: {rev_id} | {r_id} | Rating: {rating}]**: {text}\n")
                    else:
                        md_file.write("*No context chunks returned.*\n")
                    md_file.write("\n</details>\n\n---\n\n")

                else:
                    # Handle non-200 HTTP response statuses
                    err_msg = f"HTTP {response.status_code}: {response.text}"
                    print(f"RESULT: FAILED - {err_msg}")
                    md_file.write(f"### Test `{test['id']}`: {test['category'].upper()}\n\n")
                    md_file.write(f"* **Query:** \"{test['query']}\"\n")
                    md_file.write(f"* **Result:** 🔴 **FAILED** (`{err_msg}`)\n\n---\n\n")

            except Exception as e:
                # Handle connection/timeout failures
                err_msg = f"Connection Error: {str(e)}"
                print(f"RESULT: ERROR - {err_msg}")
                md_file.write(f"### Test `{test['id']}`: {test['category'].upper()}\n\n")
                md_file.write(f"* **Query:** \"{test['query']}\"\n")
                md_file.write(f"* **Result:** 🔴 **ERROR** (`{err_msg}`)\n\n---\n\n")

        # -------------------------------------------------------------------
        # Write Report Evaluation Summary
        # -------------------------------------------------------------------
        pass_percentage = round((passed_tests / total_tests) * 100, 1)
        summary_md = "## 📊 Evaluation Summary\n\n"
        summary_md += f"* **Pass Rate:** `{passed_tests}/{total_tests}` (`{pass_percentage}%`)\n"
        summary_md += f"* **Status:** {'✅ ALL TESTS PASSED' if passed_tests == total_tests else '⚠️ SOME TESTS FAILED'}\n"
        
        md_file.write(summary_md)

        summary_print = f"\n============================================================\n"
        summary_print += f"EVALUATION SUMMARY: {passed_tests}/{total_tests} Tests Passed\n"
        summary_print += f"============================================================\n"
        print(summary_print)

    print(f"\nMarkdown evaluation report saved to: {LOG_FILE_PATH}")

if __name__ == "__main__":
    run_evaluation()