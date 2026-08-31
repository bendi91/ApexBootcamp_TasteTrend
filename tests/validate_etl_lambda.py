# ====================================================
# TasteTrend ETL — Transformation Accuracy Validator
# ====================================================
# Validates the processed/ output in S3 against the raw/ input, mirroring
# the same logic as lambda_function.py

import base64
import io
import re
import sys
from datetime import datetime
from pathlib import Path
import boto3
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# S3 Bucket names and metadata configuration path
DATA_BUCKET = "tastetrend-data-lake-260810"
CONFIG_BUCKET = "tastetrend-configs-260810"
CONFIG_KEY = "mapping_config.csv"

# Keyword markers used to distinguish reference files from standard fact tables
REFERENCE_FILE_MARKERS = ("restaurant_info", "reference")

# Regex pattern to identify near-duplicate suffix records (_copy or _dup)
NEAR_DUP_SUFFIX_RE = re.compile(r"(_copy|_dup)$", re.IGNORECASE)

# Exact required order for fact tables (CHECK 9). Kept as the single source
# of truth; REQUIRED_FACT_COLUMNS (the set used for CHECK 3) is derived from it
# so the two can never drift out of sync with each other.
REQUIRED_FACT_COLUMN_ORDER = [
    "review_id", "customer_id", "review_date", "rating", "review_text",
    "total_spent", "tip_amount", "party_size", "age_range", "gender",
    "ethnicity", "transaction_count", "restaurant_id",
]
REQUIRED_FACT_COLUMNS = set(REQUIRED_FACT_COLUMN_ORDER)

# Define required structure and column ordering for the reference dataset
REQUIRED_REFERENCE_COLUMN_ORDER = [
    "source_file_tag", "restaurant_name", "original_city", "address",
    "categories", "restaurant_id",
]

REQUIRED_REFERENCE_COLUMNS = set(REQUIRED_REFERENCE_COLUMN_ORDER)

# Mirrors FIELDS_TO_NULL_ON_DUPLICATE in lambda_function.py — the fields that
# must be NULL on every duplicate-collapsed row (transaction_count > 1).
FIELDS_TO_NULL_ON_DUPLICATE = [
    "customer_id", "total_spent", "tip_amount", "tip_percentage",
    "party_size", "age_range", "gender", "ethnicity",
]

# Acceptable numeric domain for user ratings
VALID_RATINGS = {1, 2, 3, 4, 5}

# Limit printed review IDs in output messages to avoid terminal output bloat
MAX_IDS_PRINTED = 25  # cap noisy output; total count is always shown

# Initialize Boto3 S3 Client instance
s3 = boto3.client("s3")

# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------
# Custom stream interceptor that duplicates standard output writes (sys.stdout)
# simultaneously to both the terminal screen and a local text log file.
class TeeStream:

    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log_file = open(filename, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

    def close(self):
        self.log_file.close()

# Formats a list or set of failing IDs into a readable string list.
# Truncates output if the count exceeds MAX_IDS_PRINTED to avoid output clutter
def format_id_list(ids):
    ids = list(ids)
    if not ids:
        return ""
    shown = ids[:MAX_IDS_PRINTED]
    text = ", ".join(str(i) for i in shown)
    if len(ids) > MAX_IDS_PRINTED:
        text += f"  ...and {len(ids) - MAX_IDS_PRINTED} more"
    return text

# Evaluates whether a target value represents an empty/missing cell.
# Returns True for pandas NaN values, None, or whitespace-only strings
def is_blank(value):
    if pd.isna(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False

# Validates if a string strictly conforms to Base64URL encoding standards.
# Handles padding requirements dynamically
def is_valid_b64url(value):
    if not isinstance(value, str) or value == "":
        return False
    try:
        base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        return True
    except Exception:
        return False

# ---------------------------------------------------------------------------
# Config / header map helpers
# ---------------------------------------------------------------------------
# Reads mapping configuration file directly from S3 using semicolon delimiter
def load_config_df():
    obj = s3.get_object(Bucket=CONFIG_BUCKET, Key=CONFIG_KEY)
    text = obj["Body"].read().decode("utf-8")
    return pd.read_csv(io.StringIO(text), sep=";")

# Extracts unique lowercase dataset source identifiers defined in config
def load_sources(config_df):
    return sorted(config_df["source_dataset"].str.lower().unique().tolist())

# Constructs per-source column translation dictionaries to normalize input names
# to target schema column names
def load_header_maps(config_df):
    header_maps = {}
    for source, group in config_df.groupby("source_dataset"):
        header_maps[source.lower()] = dict(zip(group["input_column"], group["target_column"]))
    return header_maps

# ---------------------------------------------------------------------------
# S3 helpers
# ---------------------------------------------------------------------------
# Lists all raw objects in S3 and derives their expected processed/ paths.
# Handles multi-page object listings cleanly via S3 Paginator
def list_raw_processed_pairs():
    raw_keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=DATA_BUCKET, Prefix="raw/"):
        for obj in page.get("Contents", []):
            raw_keys.append(obj["Key"])
    return [(k, re.sub(r"\.\w+$", ".csv", k.replace("raw/", "processed/"))) for k in raw_keys]

# Downloads an S3 object key and parses it into a Pandas DataFrame
def read_csv_from_s3(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    text = obj["Body"].read().decode("utf-8")
    return pd.read_csv(io.StringIO(text))

# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
# 1. Rating values: only 1-5 allowed; blank/null in processed is only
# legitimate if EVERY raw row sharing that review_id was blank too
def check_rating_values_and_nulls(raw_all, processed_df):
    if "rating" not in processed_df.columns or "review_id" not in processed_df.columns:
        return ["'rating' or 'review_id' column missing in processed file"]

    issues = []

    # a) Allowed value set check (non-null values only)
    non_null = processed_df[~processed_df["rating"].apply(is_blank)]
    invalid_values = non_null[~non_null["rating"].isin(VALID_RATINGS)]
    if not invalid_values.empty:
        issues.append(
            f"{len(invalid_values)} row(s) with rating not in {{1,2,3,4,5}}. "
            f"review_id(s): {format_id_list(invalid_values['review_id'])}"
        )

    # b) Bidirectional blank/null consistency, matched by review_id
    if "rating" not in raw_all.columns or "review_id" not in raw_all.columns:
        issues.append("Cannot check raw/processed null consistency — raw file missing rating/review_id")
        return issues

    # A review_id is "blank in raw" only if NONE of its raw rows had a valid
    # rating — a review_id with any valid rating among its raw rows is
    # expected to surface a value in processed after coalescing.
    raw_valid_ids = set(raw_all.loc[~raw_all["rating"].apply(is_blank), "review_id"])
    raw_null_ids = set(raw_all["review_id"]) - raw_valid_ids
    processed_null_ids = set(processed_df.loc[processed_df["rating"].apply(is_blank), "review_id"])

    # Only flag the direction that indicates a real bug: processed has a blank
    # rating where raw had a valid rating available (on any duplicate row).
    # The reverse (raw entirely blank, processed not blank) can't happen —
    # there'd be nothing to coalesce a value from.
    only_processed_null = processed_null_ids - raw_null_ids

    if only_processed_null:
        issues.append(
            f"{len(only_processed_null)} row(s) blank/null in processed but a valid rating "
            f"existed somewhere in raw (possibly on a sibling duplicate row). "
            f"review_id(s): {format_id_list(only_processed_null)}"
        )

    return issues

# 2. review_date strictly matches YYYY-MM-DD format
def check_date_format(df):
    if "review_date" not in df.columns or "review_id" not in df.columns:
        return ["'review_date' or 'review_id' column missing"]

    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    def is_valid(v):
        if pd.isna(v):
            return False
        s = str(v)
        if not date_re.match(s):
            return False
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    bad_mask = ~df["review_date"].apply(is_valid)
    bad = df[bad_mask]
    if not bad.empty:
        return [f"{len(bad)} row(s) with invalid review_date format. "
                f"review_id(s): {format_id_list(bad['review_id'])}"]
    return []

# 3. Fact table / reference table schema matches the exact required column set
# and for fact tables the exact required column order
# a) fact tables
def check_fact_schema(df):
    actual = set(df.columns)
    missing = REQUIRED_FACT_COLUMNS - actual
    extra = actual - REQUIRED_FACT_COLUMNS
    issues = []
    if missing:
        issues.append(f"Missing required column(s): {sorted(missing)}")
    if extra:
        issues.append(f"Unexpected extra column(s): {sorted(extra)}")
    return issues

def check_fact_column_order(df):
    actual = list(df.columns)
    if set(actual) != REQUIRED_FACT_COLUMNS:
        return []
    if actual != REQUIRED_FACT_COLUMN_ORDER:
        return [
            f"Fact table columns are present but out of order. "
            f"Expected: {REQUIRED_FACT_COLUMN_ORDER}. Found: {actual}"
        ]
    return []

# b) reference tables
def check_reference_schema(df):
    actual = set(df.columns)
    missing = REQUIRED_REFERENCE_COLUMNS - actual
    extra = actual - REQUIRED_REFERENCE_COLUMNS
    issues = []
    if missing:
        issues.append(f"Missing required column(s): {sorted(missing)}")
    if extra:
        issues.append(f"Unexpected extra column(s): {sorted(extra)}")
    return issues

def check_reference_column_order(df):
    actual = list(df.columns)
    if set(actual) != REQUIRED_REFERENCE_COLUMNS:
        return []
    if actual != REQUIRED_REFERENCE_COLUMN_ORDER:
        return [
            f"Reference table columns are present but out of order. "
            f"Expected: {REQUIRED_REFERENCE_COLUMN_ORDER}. Found: {actual}"
        ]
    return []

# 4. Near-duplicate (_copy/_dup suffix) rows are fully removed from processed
def check_near_duplicates_removed(df):
    if "review_id" not in df.columns:
        return ["'review_id' column missing — cannot check near-duplicates"]
    matches = df["review_id"].astype(str).str.contains(NEAR_DUP_SUFFIX_RE, regex=True, na=False)
    if matches.any():
        return [f"{matches.sum()} row(s) with _copy/_dup suffix still present. "
                f"review_id(s): {format_id_list(df.loc[matches, 'review_id'])}"]
    return []

# 5. restaurant_id values are consistent between fact tables and reference table
# a) cross check between fact and reference tables
def check_restaurant_id_cross_consistency(all_fact_dfs, reference_df):
    issues = []
    if reference_df is None or "restaurant_id" not in reference_df.columns:
        return ["Reference file not found or missing restaurant_id column"]

    ref_ids = set(reference_df["restaurant_id"].str.lower())
    fact_ids = set(all_fact_dfs.keys())

    missing_in_ref = fact_ids - ref_ids
    missing_in_fact = ref_ids - fact_ids

    if missing_in_ref:
        issues.append(f"Fact table restaurant_id(s) not found in reference file: {sorted(missing_in_ref)}")
    if missing_in_fact:
        issues.append(f"Reference file restaurant_id(s) with no matching fact table: {sorted(missing_in_fact)}")

    # Also check every row's restaurant_id within each fact table matches the expected source
    for source, df in all_fact_dfs.items():
        if "restaurant_id" not in df.columns:
            continue
        bad = df[df["restaurant_id"].str.lower() != source]
        if not bad.empty:
            issues.append(
                f"[{source}] {len(bad)} row(s) with restaurant_id inconsistent with source. "
                f"review_id(s): {format_id_list(bad['review_id']) if 'review_id' in bad.columns else 'n/a'}"
            )

    return issues

# b) double check for null values in reference table's restaurant id
def check_reference_row(df):
    issues = []
    if "restaurant_id" in df.columns and df["restaurant_id"].isna().any():
        issues.append("Some restaurant_id values are null in reference file")
    return issues

# 6. review_id values are valid Base64URL across all datasets
def check_base64url_encoding(df):
    if "review_id" not in df.columns:
        return ["'review_id' column missing"]
    invalid_mask = ~df["review_id"].apply(is_valid_b64url)
    if invalid_mask.any():
        return [f"{invalid_mask.sum()} row(s) with review_id failing Base64URL validation. "
                f"review_id(s): {format_id_list(df.loc[invalid_mask, 'review_id'])}"]
    return []

# 7. collects review_ids from raw where total_spent is NULL but
# tip_amount AND tip_percentage are both present and > 0, then verifies
# the processed row for that review_id has a NOT-NULL, > 0 total_spent.
def check_total_spent_derivation(raw_dedup, processed_df):
    issues = []
    required_raw = {"review_id", "total_spent", "tip_amount", "tip_percentage"}
    if not required_raw.issubset(raw_dedup.columns):
        missing = required_raw - set(raw_dedup.columns)
        return [f"Cannot validate total_spent derivation — raw file missing columns: {sorted(missing)}"]
    if not {"review_id", "total_spent", "transaction_count"}.issubset(processed_df.columns):
        return ["Cannot validate total_spent derivation — processed file missing review_id/total_spent/transaction_count"]

    # Exception 1: exclude near-duplicate rows — these are deleted entirely
    # regardless of their total_spent/tip values, so they'd never appear in
    # processed and shouldn't be treated as a derivation failure.
    non_near_dup_mask = ~raw_dedup["review_id"].astype(str).str.contains(NEAR_DUP_SUFFIX_RE, regex=True, na=False)
    raw_candidates = raw_dedup[non_near_dup_mask]

    should_derive_mask = (
        raw_candidates["total_spent"].apply(is_blank)
        & ~raw_candidates["tip_amount"].apply(is_blank)
        & ~raw_candidates["tip_percentage"].apply(is_blank)
        & (raw_candidates["tip_amount"] > 0)
        & (raw_candidates["tip_percentage"] > 0)
    )
    target_ids = set(raw_candidates.loc[should_derive_mask, "review_id"])
    if not target_ids:
        return issues  # nothing to check for this file

    processed_indexed = processed_df.set_index("review_id")

    failed_ids = []
    for rid in target_ids:
        if rid not in processed_indexed.index:
            failed_ids.append(rid)  # row vanished entirely — also a failure
            continue
        row = processed_indexed.loc[rid]
        if isinstance(row, pd.DataFrame):  # duplicate index safety
            row = row.iloc[0]

        # Exception 2: duplicate-collapsed rows are correctly nulled
        # regardless of the raw tip fields — skip rather than flag.
        if row.get("transaction_count", 1) > 1:
            continue

        val = row["total_spent"]
        if is_blank(val) or not (val > 0):
            failed_ids.append(rid)

    if failed_ids:
        issues.append(
            f"{len(failed_ids)} of {len(target_ids)} row(s) expected to have a derived total_spent "
            f"(raw total_spent NULL, tip_amount>0, tip_percentage>0) do NOT have a valid total_spent "
            f"in processed. review_id(s): {format_id_list(failed_ids)}"
        )
    return issues

# 8. review_id uniqueness in processed/, and row-count reconciliation using
# transaction_count as a multiplier (processed weighted count should equal raw row count)
def check_uniqueness_and_row_count(raw_df, processed_df):
    issues = []

    if "review_id" in processed_df.columns:
        dup_mask = processed_df.duplicated(subset="review_id", keep=False)
        if dup_mask.any():
            issues.append(
                f"{processed_df.loc[dup_mask, 'review_id'].nunique()} review_id value(s) appear more "
                f"than once in processed (should be unique). "
                f"review_id(s): {format_id_list(processed_df.loc[dup_mask, 'review_id'].unique())}"
            )
    else:
        issues.append("'review_id' column missing — cannot check uniqueness")

    if "transaction_count" in processed_df.columns:
        weighted_total = processed_df["transaction_count"].fillna(1).sum()
    else:
        weighted_total = None
        issues.append("'transaction_count' column missing — cannot reconcile row counts")

    raw_total = len(raw_df)
    if weighted_total is not None:
        print(f"  Row-count reconciliation: raw={raw_total}, "
              f"processed weighted by transaction_count={int(weighted_total)}")
        if int(weighted_total) != raw_total:
            issues.append(
                f"Weighted processed row count ({int(weighted_total)}) does NOT match raw row count "
                f"({raw_total}) — diff={raw_total - int(weighted_total)}. Check deduplication logic "
                f"and transaction_count values."
            )

    return issues

# 9. customer_id/total_spent/tip_amount/party_size/age_range/gender/ethnicity 
# are NULL on every duplicate-collapsed row (transaction_count > 1)
def check_duplicate_fields_nullified(df):
    issues = []
    if "transaction_count" not in df.columns:
        return ["'transaction_count' column missing — cannot check duplicate-field nullification"]
    if "review_id" not in df.columns:
        return ["'review_id' column missing — cannot check duplicate-field nullification"]

    dup_rows = df[df["transaction_count"] > 1]
    if dup_rows.empty:
        return issues

    present_fields = [f for f in FIELDS_TO_NULL_ON_DUPLICATE if f in df.columns]
    for col in present_fields:
        bad_mask = ~dup_rows[col].apply(is_blank)
        if bad_mask.any():
            issues.append(
                f"{bad_mask.sum()} duplicate-collapsed row(s) have a non-null '{col}' "
                f"(should be nulled). review_id(s): {format_id_list(dup_rows.loc[bad_mask, 'review_id'])}"
            )
    return issues

# 10. Verify pass-through fields (text, demographics & financials) didn't suffer data loss on unique rows
def check_passthrough_field_integrity(raw_renamed, processed_df):
    issues = []
    
    if "transaction_count" not in processed_df.columns or "review_id" not in processed_df.columns:
        return issues

    # Target unique, non-collapsed rows only
    unique_rids = set(processed_df.loc[processed_df["transaction_count"] == 1, "review_id"])
    if not unique_rids:
        return issues

    raw_unique = raw_renamed[raw_renamed["review_id"].isin(unique_rids)]
    processed_unique = processed_df[processed_df["review_id"].isin(unique_rids)]

    # Fields that should pass through 1:1 on unique rows without being lost
    passthrough_cols = [
        "review_text", "customer_id", "party_size", 
        "age_range", "gender", "ethnicity", 
        "total_spent", "tip_amount"
    ]

    # Index both frames by review_id so each row can be compared against
    # its own prior value, not just folded into a column-wide total.
    raw_indexed = raw_unique.set_index("review_id")
    processed_indexed = processed_unique.set_index("review_id")

    for col in passthrough_cols:
        if col not in raw_indexed.columns or col not in processed_indexed.columns:
            continue

        lost_ids = []
        for rid in raw_indexed.index:
            if rid not in processed_indexed.index:
                continue  # row-existence is covered by check_uniqueness_and_row_count

            raw_val = raw_indexed.at[rid, col]
            proc_val = processed_indexed.at[rid, col]

            # A row only counts as data loss if it HAD a real value in raw
            # but that exact same row is now blank in processed.
            if not is_blank(raw_val) and is_blank(proc_val):
                lost_ids.append(rid)

        if lost_ids:
            issues.append(
                f"Data loss in '{col}': {len(lost_ids)} unique row(s) had a non-null raw value "
                f"but are blank in processed. Affected review_id(s): {format_id_list(lost_ids)}."
        
                )

    return issues

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    script_dir = Path(__file__).resolve().parent
    filename = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    output_filepath = script_dir / filename

    total_issues = 0
    total_files_evaluated = 0
    file_results = []

    print("=" * 70)
    print("TasteTrend ETL — Transformation Accuracy Validation Report")
    print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    with open(output_filepath, "w", encoding="utf-8") as md:
        # Header block
        md.write("# 🧪 TasteTrend ETL — Transformation Accuracy Validation Report\n\n")
        md.write(f"**Report Generated:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`  \n")
        md.write(f"**Data Bucket:** `{DATA_BUCKET}`  \n")
        md.write(f"**Config Bucket:** `{CONFIG_BUCKET}`\n\n")
        md.write("> **Note:** Checks aligning raw to processed rows assume the Lambda coalesces priority ")
        md.write("fields across all raw rows sharing a `review_id`.\n\n")
        md.write("---\n\n")

        # Load S3 transformation mapping configuration
        try:
            config_df = load_config_df()
            sources = load_sources(config_df)
            header_maps = load_header_maps(config_df)
            print(f"\nSources loaded from mapping_config.csv: {sources}")
        except Exception as e:
            print(f"\n[FATAL] Could not load mapping_config.csv: {e}")
            md.write(f"## 🔴 Fatal System Error\n\nCould not load mapping configuration: `{e}`\n")
            sys.exit(1)

        # Discover dataset pairs under S3 raw/ prefix
        try:
            pairs = list_raw_processed_pairs()
        except Exception as e:
            print(f"\n[FATAL] Could not list S3 objects: {e}")
            md.write(f"## 🔴 Fatal System Error\n\nCould not list S3 objects: `{e}`\n")
            sys.exit(1)

        if not pairs:
            print("\n[WARNING] No files found under raw/. Nothing to validate.")
            md.write("## ⚠️ Validation Warning\n\nNo files detected under `raw/` prefix.\n")
            sys.exit(0)

        all_fact_dfs = {}
        reference_df = None

        md.write("## 📁 File-Level Validation Results\n\n")

        # Iterate through every detected raw/processed file pair
        for raw_key, processed_key in pairs:
            total_files_evaluated += 1
            print(f"\n{'-' * 70}")
            print(f"File: {raw_key}  ->  {processed_key}")

            md.write(f"### `{raw_key}`\n")
            md.write(f"* **Target Path:** `{processed_key}`\n")

            # Read Raw input dataset
            try:
                raw_df = read_csv_from_s3(DATA_BUCKET, raw_key)
            except Exception as e:
                print(f"  [ERROR] Could not read raw file: {e}")
                md.write(f"* **Result:** 🔴 **ERROR** (`Could not read raw file: {e}`)\n\n---\n\n")
                total_issues += 1
                continue

            # Read Processed target dataset
            try:
                processed_df = read_csv_from_s3(DATA_BUCKET, processed_key)
            except Exception as e:
                print(f"  [FAIL] Processed file missing or unreadable: {e}")
                md.write(f"* **Result:** 🔴 **FAILED** (`Processed file missing or unreadable: {e}`)\n\n---\n\n")
                total_issues += 1
                continue

            is_reference = any(marker in raw_key.lower() for marker in REFERENCE_FILE_MARKERS)
            issues = []

            if is_reference:
                # Reference file validations
                issues += check_reference_schema(processed_df)
                issues += check_reference_column_order(processed_df)
                issues += check_reference_row(processed_df)
                reference_df = processed_df
            else:
                # Fact table validations
                source = next((s for s in sources if s in raw_key.lower()), None)
                if source is None:
                    issues.append(f"Could not determine source dataset from key: `{raw_key}`")
                else:
                    header_map = header_maps.get(source, {})
                    raw_renamed = raw_df.rename(columns=header_map)

                    if "review_id" not in raw_renamed.columns:
                        issues.append("Could not identify review_id column in raw file via header map")
                    else:
                        raw_dedup = raw_renamed.drop_duplicates(subset="review_id", keep="first")

                        issues += check_fact_schema(processed_df)
                        issues += check_fact_column_order(processed_df)
                        issues += check_rating_values_and_nulls(raw_renamed, processed_df)
                        issues += check_date_format(processed_df)
                        issues += check_near_duplicates_removed(processed_df)
                        issues += check_base64url_encoding(processed_df)
                        issues += check_total_spent_derivation(raw_dedup, processed_df)
                        issues += check_uniqueness_and_row_count(raw_renamed, processed_df)
                        issues += check_duplicate_fields_nullified(processed_df)
                        issues += check_passthrough_field_integrity(raw_renamed, processed_df)

                    all_fact_dfs[source] = processed_df

            # Print file issue summary to console and write to markdown file
            if issues:
                print(f"  [FAIL] {len(issues)} issue(s) found:")
                for issue in issues:
                    print(f"    - {issue}")
                total_issues += len(issues)
                
                md.write(f"* **Result:** 🔴 **FAILED** (`{len(issues)} issue(s) found`)\n\n")
                md.write("**Detected Issues:**\n")
                for issue in issues:
                    md.write(f"* {issue}\n")
                file_results.append((raw_key, "🔴 FAILED", len(issues)))
            else:
                print("  [PASS] No issues found.")
                md.write("* **Result:** 🟢 **PASSED**\n")
                file_results.append((raw_key, "🟢 PASSED", 0))

            md.write("\n---\n\n")

        # Execute final cross-table referential integrity check
        print(f"\n{'-' * 70}")
        print("Cross-file restaurant_id consistency (fact tables vs reference)")
        
        md.write("## 🔗 Cross-File Integrity Checks\n\n")
        cross_issues = check_restaurant_id_cross_consistency(all_fact_dfs, reference_df)
        
        if cross_issues:
            print(f"  [FAIL] {len(cross_issues)} issue(s) found:")
            for issue in cross_issues:
                print(f"    - {issue}")
            total_issues += len(cross_issues)

            md.write(f"* **Result:** 🔴 **FAILED** (`{len(cross_issues)} issue(s) found`)\n\n")
            md.write("**Detected Issues:**\n")
            for issue in cross_issues:
                md.write(f"* {issue}\n")
        else:
            print("  [PASS] restaurant_id values are consistent across all files.")
            md.write("* **Result:** 🟢 **PASSED** — `restaurant_id` values are consistent across all fact/reference tables.\n")

        md.write("\n---\n\n")

        # Step 3: Markdown Evaluation Summary Table
        md.write("## 📊 Evaluation Summary\n\n")
        md.write(f"* **Total Dataset Pairs Evaluated:** `{total_files_evaluated}`\n")
        md.write(f"* **Total Discovered Issues:** `{total_issues}`\n\n")

        if total_issues == 0:
            md.write("> 🟢 **STATUS: PASSED** — All transformation rules successfully validated.\n\n")
        else:
            md.write(f"> 🔴 **STATUS: FAILED** — Discovered {total_issues} issue(s) across datasets.\n\n")

        md.write("| Dataset Key | Status | Total Issues |\n")
        md.write("|---|---|---|\n")
        for fkey, fstat, fcount in file_results:
            md.write(f"| `{fkey}` | {fstat} | `{fcount}` |\n")

    # Final Terminal Output
    print(f"\n{'=' * 70}")
    if total_issues == 0:
        print("SUMMARY: ALL CHECKS PASSED. Transformation accuracy validated.")
    else:
        print(f"SUMMARY: {total_issues} issue(s) found across all files. Review above.")
    print("=" * 70)
    print(f"\n[INFO] Validation report output successfully saved to: {output_filepath}")

if __name__ == "__main__":
    main()