# =============================================================================
# TasteTrend ETL Lambda - PHASE 3
#
# Triggered by S3 "object created" events under raw/ 
# and writes the result to the same key path under processed/.
#
# Handles two categories of input file:
#   1. Fact tables
#   2. The single restaurant reference/dimension file
#
# To use the 5 row sample data for testing Phase 4, uncomment the "Phase 4 test mode" code blocks
# =============================================================================
import json
import boto3
import logging
import pandas as pd
from io import StringIO
import re
import base64
from urllib.parse import unquote_plus

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logger = logging.getLogger()
logger.setLevel(logging.INFO)       # INFO captures normal operational milestones without DEBUG-level noise
s3_client = boto3.client('s3')      # Reused across invocations on a warm container — cheaper than re-creating per call

# ---------------------------------------------------------------------------
# Module-level Constants
# ---------------------------------------------------------------------------
# CSV config file path
CONFIG_BUCKET = "tastetrend-configs-260810"
CONFIG_FILE_KEY = "mapping_config.csv"

# Fixed keywords for reference routing
REFERENCE_FILE_MARKERS = ('restaurant_info', 'reference')

# Handling near-duplicates: review_id ending in "_copy" or "_dup"
NEAR_DUP_SUFFIX_RE = re.compile(r'(_copy|_dup)$', re.IGNORECASE)

# Nullifying columns for duplicated Review ID rows
FIELDS_TO_NULL_ON_DUPLICATE = ['customer_id', 'total_spent', 'tip_amount', 'tip_percentage',
'party_size', 'age_range', 'gender', 'ethnicity']

# Invisible Unicode modifier characters stripped before counting emoji/symbol
# ratings (e.g. Uptown's star-emoji column).
VARIATION_SELECTORS = dict.fromkeys(range(0xFE00, 0xFE0F + 1))
ZERO_WIDTH_JOINER = '\u200D'

# Fixed list defining exact required fact table column sequence
REQUIRED_FACT_COLUMN_ORDER = [
    "review_id", "customer_id", "review_date", "rating", "review_text",
    "total_spent", "tip_amount", "party_size", "age_range", "gender",
    "ethnicity", "transaction_count", "restaurant_id",
]

# --- Phase 4 test mode: uncomment the line below to limit Eastside output
# to 5 rows, to avoid Bedrock/OpenSearch costs while testing embeddings.
# Comment it back out for normal full processing.
# For proper usage, dont forget to uncomment the following code blocks as well:
# lines 454-456 and lines 491-493
# TEST_MODE = True

# ---------------------------------------------------------------------------
# Runtime configuration
# ---------------------------------------------------------------------------
# Populated on first use per container via load_configurations_on_demand().
# Stay None until then — Lambda reuses this module's global state across
# warm invocations, so a cold-start container fetches the config CSV once
# and every subsequent invocation on that same container reuses it in memory.
HEADER_MAPS = None
DATASET_CONFIG = None

# Single S3 GET, shared by both config parsers below.
def _fetch_config_csv(bucket_name, file_key):
    try:
        # Download the CSV file from S3 into memory
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        csv_content = response['Body'].read().decode('utf-8')
        # Read it into a Pandas DataFrame table
        return pd.read_csv(StringIO(csv_content), sep=';')
    except Exception as e:
        logger.error(f"Failed to download or parse config CSV from S3: {str(e)}")
        raise e # Aborts the remaining files in this batch on any single-file failure

# The two loaders below stay separate rather than combined into one S3 fetch (Easier to read)
# 1. Validate if the incoming file is an allowed dataset & Apply schema correction
def load_header_maps_from_csv(config_df):
    try:
        # Build a nested dictionary structure
        header_maps = {}
        for source, group in config_df.groupby('source_dataset'):
            header_maps[source.lower()] = dict(zip(group['input_column'], group['target_column']))
            
        logger.info(f"Successfully loaded mappings for sources: {list(header_maps.keys())}")
        return header_maps
    # Helps to debug error messages if the script couldn't read the mapping config
    except Exception as e:
        logger.error(f"Failed to load mapping configuration: {str(e)}")
        raise e # Aborts the remaining files in this batch on any single-file failure

# 2. Implement a dynamic rating scale divisor to support range normalization 
# for non-standard scales exceeding the baseline 1–5 range
def load_rating_divisors_from_csv(config_df):
    try:
        rating_configs = {}
        for source, group in config_df.groupby('source_dataset'):
            # Filters out missing or blank cells from the config column to isolate valid numeric divisors
            non_null_divisors = group['rating_divisor'].dropna()

            if non_null_divisors.empty:
                logger.warning(f"[{source}] No rating_divisor value found in config; defaulting to 1.")
                divisor = 1
            else:
                divisor = int(non_null_divisors.iloc[0])
                # Sanity check: if the config accidentally specifies conflicting divisors for the same source
                if non_null_divisors.nunique() > 1:
                    logger.warning(
                        f"[{source}] Multiple distinct rating_divisor values found "
                        f"{sorted(non_null_divisors.unique().tolist())}; using {divisor}."
                    )

            rating_configs[source.lower()] = divisor

        logger.info(f"Successfully loaded rating divisors for: {list(rating_configs.keys())}")
        return rating_configs
    # Helps to debug error messages if the script couldn't read the mapping config
    except Exception as e:
        logger.error(f"Failed to load rating divisor configuration: {str(e)}")
        raise e # Aborts the remaining files in this batch on any single-file failure

# On-Demand configuration orchestrator that leverages native Lambda global container memory
def load_configurations_on_demand():
    global HEADER_MAPS, DATASET_CONFIG
    
    # Check global cache to reuse configuration data in memory and prevent redundant S3 network costs
    if HEADER_MAPS is not None and DATASET_CONFIG is not None:
        return HEADER_MAPS, DATASET_CONFIG

    logger.info("Configuration memory empty. Ingesting fresh config file from S3...")
    
    # Execute the single S3 network fetch
    _config_df = _fetch_config_csv(CONFIG_BUCKET, CONFIG_FILE_KEY)
    
    # Parse out both mappings from the same in-memory dataframe table without talking to S3 again
    HEADER_MAPS = load_header_maps_from_csv(_config_df)
    DATASET_CONFIG = load_rating_divisors_from_csv(_config_df)
    
    return HEADER_MAPS, DATASET_CONFIG
# ---------------------------------------------------------------------------
# Core Transformation Modules
# ---------------------------------------------------------------------------
# Step 1: Validate if the incoming file is an allowed dataset & 
# Header normalization: Renames raw column names to the unified schema
def detect_source(file_key, header_maps):
    key_lower = file_key.lower()
    for source in sorted(header_maps, key=len, reverse=True):
        if source in key_lower:
            return source
    raise ValueError(f"Could not determine source dataset from key: {file_key}")

def normalize_headers(df, source, header_maps):
    mapping = header_maps[source]
    missing = set(mapping.keys()) - set(df.columns)
    if missing:
        logger.warning(f"[{source}] Expected source columns not found: {missing}")
    return df.rename(columns=mapping)

# Step 2: Drop near-duplicates with _copy/_dup suffixes
def drop_near_duplicates(df, source):
    if 'review_id' not in df.columns:
        logger.warning(f"[{source}] review_id column missing; skipping near-duplicate drop.")
        return df
    mask = df['review_id'].astype(str).str.contains(NEAR_DUP_SUFFIX_RE, regex=True, na=False)
    
    if mask.any():
        # Before dropping, record how many near-duplicate rows existed per BASE
        # review_id (suffix stripped) — this count would otherwise be lost
        # entirely once the rows below are dropped, causing transaction_count
        # to silently under-report the true number of raw rows for that review.
        base_ids_of_dropped = df.loc[mask, 'review_id'].astype(str).str.replace(NEAR_DUP_SUFFIX_RE, '', regex=True)
        near_dup_counts = base_ids_of_dropped.value_counts()
 
        logger.info(f"[{source}] Automatically detected and dropping {mask.sum()} near-duplicate _copy/_dup rows")
        df = df.loc[~mask].copy()
 
        # Attach the dropped count onto whichever surviving row shares that base
        # review_id, so resolve_duplicate_review_ids() can fold it into transaction_count.
        df['_near_dup_count'] = df['review_id'].map(near_dup_counts).fillna(0).astype(int)
        return df
 
    df['_near_dup_count'] = 0
    return df

# Step 3: date normalization to YYYY-MM-DD
def normalize_dates(df, source):
    if 'review_date' not in df.columns:
        logger.warning(f"[{source}] review_date column missing; skipping date normalization.")
        return df
    
    parsed = pd.to_datetime(df['review_date'], errors='coerce')
    failed = parsed.isna().sum()
    df['review_date'] = parsed.dt.strftime('%Y-%m-%d')
    logger.info(
        f"[{source}] Standardized {len(df) - failed}/{len(df)} dates to ISO YYYY-MM-DD format."
    )
    if failed:
        logger.warning(f"[{source}] {failed} review_date values could not be parsed.")
    return df

# Step 4: Duplicate review_id resolution
def resolve_duplicate_review_ids(df, source):
    # Near-duplicate rows (dropped in Step 3) still count toward the total
    # number of raw submissions for a review_id, even though the rows
    # themselves are gone — carry that count forward rather than losing it.
    near_dup_counts = df.pop('_near_dup_count') if '_near_dup_count' in df.columns else 0

    # If 'review_id' is missing or completely unique
    # set transaction_count to 1 and exit immediately without hardcoding dataset names.
    if 'review_id' not in df.columns:
        df['transaction_count'] = 1
        return df

    # Count total original raw submissions per review_id
    df['transaction_count'] = df.groupby('review_id')['review_id'].transform('count') + near_dup_counts
    
    # 3. transaction_count = 1
    unique_df = df[df['transaction_count'] == 1].copy()
    
    # 4. transaction_count > 1
    duplicate_df = df[df['transaction_count'] > 1].copy()
    
    if not duplicate_df.empty:
        rows_before = len(duplicate_df)

        # Per-field coalescing: merge first non-null value per column across sibling rows
        coalesce_cols = [c for c in ('review_date', 'rating', 'review_text') if c in duplicate_df.columns]
        if coalesce_cols:
            duplicate_df[coalesce_cols] = (
                duplicate_df.groupby('review_id')[coalesce_cols]
                .transform(lambda g: g.bfill().ffill())
                )

        
        # Null out columns that actually exist in this dataset
        # A missing column shouldn't block deduplication from happening.
        present_fields = [f for f in FIELDS_TO_NULL_ON_DUPLICATE if f in duplicate_df.columns]
        missing_fields = set(FIELDS_TO_NULL_ON_DUPLICATE) - set(present_fields)
        if missing_fields:
            logger.warning(
                f"[{source}] Some duplicate-nullification fields are missing from "
                f"this dataset and will be skipped: {sorted(missing_fields)}"
            ) 
        
        duplicate_df[present_fields] = None
        duplicate_df = duplicate_df.drop_duplicates(subset='review_id', keep='first').copy()
        logger.info(
            f"[{source}] Coalesced review metadata and nulled financial/demographic fields "
            f"across {rows_before} duplicate rows, collapsing to {len(duplicate_df)} unique review_ids."

        )

    # Recombine unique and collapsed duplicate datasets
    final_df = pd.concat([unique_df, duplicate_df], ignore_index=True)
    return final_df

# Step 5: review_id Base64URL encoding validation (audit only) - logging any that fail 
# so encoding issues are visible in CloudWatch rather than silently propagating downstream.
def validate_review_id_encoding(df, source):
    def is_valid_b64url(value):
        if not isinstance(value, str):
            return False
        try:
            base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))
            return True
        except Exception:
            return False

    if 'review_id' not in df.columns:
        logger.warning(f"[{source}] review_id column missing; skipping Base64URL validation.")
        return df
    invalid_mask = ~df['review_id'].apply(is_valid_b64url)
    if invalid_mask.any():
        logger.warning(
            f"[{source}] {invalid_mask.sum()} review_id values failed Base64URL "
            f"validation: {df.loc[invalid_mask, 'review_id'].tolist()[:10]}"
        )
    return df

# Step 6: Rating scale normalization to uniform 1-5 range
# - Numeric values: divided by configured divisor if range exceeds 1-5 (e.g. 1-10 scale).
# - Pure symbol strings (e.g. "⭐⭐⭐"): evaluated by counting symbol characters (divisor is ignored).
# - String routing: numeric strings (e.g. "4", "8.0") are processed via the numeric path first.
# - Mixed/invalid strings: entries containing a mix of digits, text, or emojis (e.g. "4 ⭐", "4 stars") 
#   are explicitly rejected, logged as CloudWatch warnings, and coerced to NULL to prevent data corruption.
def normalize_rating(df, source, dataset_config):
    divisor = dataset_config.get(source, 1)
    
    if 'rating' not in df.columns:
        logger.warning(f"[{source}] rating column missing; skipping rating normalization.")
        return df

    numeric_count = 0
    symbol_count = 0
    unparseable_count = 0
    detected_symbols = set()

    def convert_value(v):
        nonlocal numeric_count, symbol_count, unparseable_count

        if pd.isna(v):
            return None

        # 1. Pure Numeric Path (handles floats, ints, or clean numeric strings like "4")
        numeric_val = pd.to_numeric(v, errors='coerce')
        if pd.notna(numeric_val):
            numeric_count += 1
            if divisor > 1:
                return round(float(numeric_val) / divisor, 1)
            return float(numeric_val)

        # 2. String Evaluation Path
        if isinstance(v, str):
            cleaned_str = v.strip()
            
            # Clean variation selectors and ZWJ
            symbols_cleaned = cleaned_str.translate(VARIATION_SELECTORS).replace(ZERO_WIDTH_JOINER, '')
            non_alphanumeric_symbols = "".join(re.findall(r'[^\w\s]', symbols_cleaned))

            # Strictly evaluate if string is pure symbols (NO digits or letters allowed)
            has_digits_or_letters = bool(re.search(r'[a-zA-Z0-9]', cleaned_str))

            if non_alphanumeric_symbols and not has_digits_or_letters:
                detected_symbols.update(non_alphanumeric_symbols)
                count = len(non_alphanumeric_symbols)
                symbol_count += 1
                if not (1 <= count <= 5):
                    logger.warning(f"[{source}] Symbol rating out of expected 1-5 domain: {v!r} -> {count}")
                return count

        # 3. Reject mixed/complex strings (e.g., "4 ⭐", "4 stars", "Rating: 5/5") or unparseable text
        unparseable_count += 1
        logger.warning(f"[{source}] Rejected mixed or invalid rating value, coercing to NULL: {v!r}")
        return None

    df['rating'] = df['rating'].apply(convert_value)

    logger.info(
        f"[{source}] Rating normalization complete: {numeric_count} numeric, "
        f"{symbol_count} pure symbol, {unparseable_count} unparseable/mixed (nulled)."
    )

    return df

# Step 7: Missing total_spent from tip columns
# No source restriction here by design: missing mask already scopes this to
# exactly the rows where the derivation is mathematically valid, regardless
# of which source file they came from. Duplicate-collapsed rows are
# automatically excluded, since resolve_duplicate_review_ids nulls all
def derive_missing_total_spent(df, source):
    # Safety Check: If any of the 3 required columns are completely missing,
    # skip the function immediately to prevent errors.
    required_columns = ['total_spent', 'tip_amount', 'tip_percentage']
    if not all(col in df.columns for col in required_columns):
        return df

    # IF total_spent IS NULL
    # AND tip_amount IS NOT NULL AND tip_amount > 0
    # AND tip_percentage IS NOT NULL AND tip_percentage > 0
    missing_mask = (
        df['total_spent'].isna() & 
        df['tip_amount'].notna() & 
            (df['tip_amount'] > 0) & 
        df['tip_percentage'].notna() & 
        (df['tip_percentage'] > 0)  # Prevents division by zero!
    )
    
    # Execute math only on the matching rows
    if missing_mask.any():
        df.loc[missing_mask, 'total_spent'] = (
            df.loc[missing_mask, 'tip_amount'] / (df.loc[missing_mask, 'tip_percentage'] / 100)
        ).round(2)
        
        logger.info(f"[{source}] Dynamically derived total_spent for {missing_mask.sum()} records from tip metrics.")
        
    return df

# Step 8: drop tip_percentage (redundant after total_spent is complete)
def drop_tip_percentage(df, source):
    if 'tip_percentage' in df.columns:
        df = df.drop(columns=['tip_percentage'], errors='ignore')
        logger.info(f"[{source}] Successfully dropped redundant tip_percentage column from table.")
    return df

# Step 9: dimensionality reduction — inject restaurant_id, drop location and restaurant_name
def apply_restaurant_id(df, source):
    df['restaurant_id'] = source
    
    # Tracks which columns are actually dropped so it shows up in CloudWatch
    dropped_cols = [col for col in ['location', 'restaurant_name'] if col in df.columns]
    df = df.drop(columns=['location', 'restaurant_name'], errors='ignore')

    # Documents your success criteria requirement for handling data quality issues!
    logger.info(f"Injected uniform restaurant_id '{source}' and dropped string columns: {dropped_cols}.")
    return df

# Step 10: Reference dataset
# Drops unreliable aggregate columns
# JSON-encodes the categories list so it survives a CSV round-trip cleanly 
# Derives restaurant_id per-row from location. Location is treated as 
# a required identity column: a missing location column fails loudly here
# rather than silently producing reference rows with no usable identity.
def process_reference_dataset(df, file_key):
    if 'location' not in df.columns:
        raise ValueError(
            f"[reference] 'location' column missing from '{file_key}' — "
            f"cannot derive restaurant_id, which every downstream join depends on."
        )
    
    df = df.drop(columns=['avg_stars', 'total_reviews'], errors='ignore')
    if 'categories' in df.columns:
        df['categories'] = df['categories'].apply(
            lambda v: json.dumps([c.strip() for c in v.split(',')]) if isinstance(v, str) else json.dumps([])
        )
    df['restaurant_id'] = df['location'].str.lower()
    df = df.rename(columns={'location': 'source_file_tag'})
    logger.info(f"[reference] Successfully processed reference file '{file_key}' containing {len(df)} standardized rows.")
    return df

# ---------------------------------------------------------------------------
# Pipeline controller
# ---------------------------------------------------------------------------
# Runs the full fact-table cleaning pipeline in a fixed, dependency-aware order.
# This order matters and should not be reshuffled casually
def transform_fact_table(df, source, header_maps, dataset_config):
    df = normalize_headers(df, source, header_maps)
    df = drop_near_duplicates(df, source)
    df = normalize_dates(df, source)
    df = resolve_duplicate_review_ids(df, source)
    df = validate_review_id_encoding(df, source)
    df = normalize_rating(df, source, dataset_config)
    df = derive_missing_total_spent(df, source)
    df = drop_tip_percentage(df, source)
    df = apply_restaurant_id(df, source)

    # Reindex columns to guarantee deterministic positional order for validation checks
    df = df.reindex(columns=REQUIRED_FACT_COLUMN_ORDER)
    logger.info(f"[{source}] Applied final column ordering reindex.")
    # --- Phase 4 test mode: uncomment to limit Eastside output to 5 rows,
    # to test embedding/indexing without processing the full dataset.
    # if TEST_MODE and source == 'eastside':
    #      df = df.head(5)
    #      logger.warning(f"[{source}] TEST MODE — output truncated to 5 rows.")

    return df

# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------
# Invoked by AWS Lambda on every S3 "object created" event under raw/. 
# A single invocation may carry multiple file events, so every record is processed 
# individually in the loop below. Nothing here assumes exactly one file per invocation.
def lambda_handler(event, context):
    logger.debug(f"Received event: {json.dumps(event)}")
    results = []
    
    # Populate (or reuse, if warm) the cached config on every invocation.
    # Costs one S3 GET on a cold start, nothing on a warm container.
    header_maps, dataset_config = load_configurations_on_demand()

    for record in event['Records']:
        # Parse incoming S3 file coordinates from the bucket notification trigger
        s3_info = record['s3']
        bucket_name = s3_info['bucket']['name']
        
        # URL-Decode the key path so spaces, plus signs (+), and %20 tokens don't cause 404 crashes
        file_key = unquote_plus(s3_info['object']['key'])

        if not file_key.startswith('raw/'):
            logger.info(f"Skipping non-raw file: {file_key}")
            continue

        # --- Phase 4 test mode: uncomment to process ONLY the Eastside file —
        # every other file in raw/ (other sources, the reference file) is
        # skipped entirely, before even being downloaded, so nothing but the
        # Eastside sample ever appears in processed/.
        # if TEST_MODE and 'eastside' not in file_key.lower():
        #     logger.info(f"TEST MODE — skipping non-Eastside file: {file_key}")
        #     continue
        
        try:
            logger.info(f"Processing file: {file_key} from bucket: {bucket_name}")
            response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
            raw_text = response['Body'].read().decode('utf-8')

            # One dataset arrives with a malformed .txt extension but is
            # CSV-structured internally — parsing is extension-agnostic here,
            # so no separate conversion branch is needed.
            df = pd.read_csv(StringIO(raw_text))

            # Check if the incoming object is the reference table or a fact table
            if any(marker in file_key.lower() for marker in REFERENCE_FILE_MARKERS):
                logger.info(f"Identified dimensional reference file asset path context: {file_key}")
                df = process_reference_dataset(df, file_key)
            
            # Proceed with the fact-file pipeline
            else:
                source = detect_source(file_key, header_maps)
                df = transform_fact_table(df, source, header_maps, dataset_config)

            out_buffer = StringIO()
            df.to_csv(out_buffer, index=False)

            new_key = re.sub(r'\.\w+$', '.csv', file_key.replace('raw/', 'processed/'))

            s3_client.put_object(
                Bucket=bucket_name,
                Key=new_key,
                Body=out_buffer.getvalue(),
                ContentType='text/csv'
            )
            logger.info(f"Successfully processed and saved to: {new_key}")
            results.append(new_key)

        except Exception as e:
            logger.error(f"Error processing {file_key}: {str(e)}")
            raise e # Aborts the remaining files in this batch on any single-file failure

    return {'statusCode': 200, 'body': json.dumps({'processed_files': results})}