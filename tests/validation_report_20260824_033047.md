# 🧪 TasteTrend ETL — Transformation Accuracy Validation Report

**Report Generated:** `2026-08-24 03:30:47`  
**Data Bucket:** `tastetrend-data-lake-260810`  
**Config Bucket:** `tastetrend-configs-260810`

> **Note:** Checks aligning raw to processed rows assume the Lambda coalesces priority fields across all raw rows sharing a `review_id`.

---

## 📁 File-Level Validation Results

### `raw/tastetrend_downtown_reviews.csv`
* **Target Path:** `processed/tastetrend_downtown_reviews.csv`
* **Result:** 🟢 **PASSED**

---

### `raw/tastetrend_eastside_reviews.csv`
* **Target Path:** `processed/tastetrend_eastside_reviews.csv`
* **Result:** 🟢 **PASSED**

---

### `raw/tastetrend_midtown_reviews.txt`
* **Target Path:** `processed/tastetrend_midtown_reviews.csv`
* **Result:** 🟢 **PASSED**

---

### `raw/tastetrend_restaurant_info.csv`
* **Target Path:** `processed/tastetrend_restaurant_info.csv`
* **Result:** 🟢 **PASSED**

---

### `raw/tastetrend_uptown_reviews.csv`
* **Target Path:** `processed/tastetrend_uptown_reviews.csv`
* **Result:** 🟢 **PASSED**

---

## 🔗 Cross-File Integrity Checks

* **Result:** 🟢 **PASSED** — `restaurant_id` values are consistent across all fact/reference tables.

---

## 📊 Evaluation Summary

* **Total Dataset Pairs Evaluated:** `5`
* **Total Discovered Issues:** `0`

> 🟢 **STATUS: PASSED** — All transformation rules successfully validated.

| Dataset Key | Status | Total Issues |
|---|---|---|
| `raw/tastetrend_downtown_reviews.csv` | 🟢 PASSED | `0` |
| `raw/tastetrend_eastside_reviews.csv` | 🟢 PASSED | `0` |
| `raw/tastetrend_midtown_reviews.txt` | 🟢 PASSED | `0` |
| `raw/tastetrend_restaurant_info.csv` | 🟢 PASSED | `0` |
| `raw/tastetrend_uptown_reviews.csv` | 🟢 PASSED | `0` |
