# Data Dictionary — Bank Transaction Analytics

## Core Transaction Fields

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| `transaction_id` | String | ✅ Yes | Unique transaction identifier. Deduplicated on ingest. | `TXN-000001` |
| `customer_id` | String | ✅ Yes | Pseudonymous customer/account reference. No real PII. | `CUST-0042` |
| `transaction_date` | Datetime | ✅ Yes | Timestamp of the transaction. Drives all time-based analysis. | `2024-06-15 14:32:00` |
| `amount` | Decimal | ✅ Yes | Monetary transaction value. Positive for credits, negative for debits (documented convention). | `2450.75` or `-150.00` |
| `transaction_type` | Categorical | Recommended | Type of transaction. | `Deposit`, `Withdrawal`, `Transfer`, `Payment`, `Refund` |
| `status` | Categorical | Recommended | Transaction status. | `Completed`, `Failed`, `Reversed`, `Pending` |
| `currency` | String | Recommended | ISO currency code. | `INR` |
| `category` | Categorical | Optional | Spending/activity category. Normalized via controlled vocabulary. | `Food & Dining`, `Shopping`, `Salary` |
| `channel` | Categorical | Optional | Banking channel used. | `ATM`, `Branch`, `Mobile`, `Web`, `POS` |
| `payment_method` | Categorical | Optional | Payment instrument used. | `Card`, `UPI`, `Bank Transfer`, `Cash` |
| `merchant` | String | Optional | Merchant or counterparty label. | `Amazon`, `Zomato` |
| `location` | String | Optional | City/region only. No precise personal location. | `Mumbai`, `Delhi` |

## Derived Analytical Fields

These fields are computed by the processing pipeline (`src/analytics/derived_fields.py`):

| Field | Derivation | Purpose |
|---|---|---|
| `transaction_year` | Extracted from `transaction_date` | Year-level grouping |
| `transaction_quarter` | Extracted from `transaction_date` | Quarterly analysis |
| `transaction_month` | Extracted from `transaction_date` | Monthly trends |
| `transaction_month_name` | Extracted from `transaction_date` | Display labels |
| `transaction_week` | ISO week from `transaction_date` | Weekly patterns |
| `day_of_week` | Day name from `transaction_date` | Weekday analysis |
| `day_of_week_num` | 0=Monday to 6=Sunday | Sorting |
| `hour` | Hour from `transaction_date` | Hourly patterns |
| `is_weekend` | 1 if Saturday/Sunday, else 0 | Weekday vs weekend |
| `transaction_date_only` | Date portion only | Daily aggregation |
| `absolute_amount` | `abs(amount)` | When sign convention requires it |
| `amount_band` | Binned ranges: 0-100, 100-500, ..., 100K+ | Distribution charts |

## Pre-Aggregated Tables

| Table | Grain | Key Metrics |
|---|---|---|
| `customer_metrics` | One row per customer | txn_count, total_value, avg_value, median_value, active_days |
| `daily_metrics` | One row per date | txn_count, txn_value, distinct_active_customers |
| `category_metrics` | One row per category×channel×type | txn_count, total_amount, avg_amount, pct_of_total |
| `time_pattern_metrics` | One row per day_of_week×hour | txn_count, txn_value |
| `outlier_review` | One row per flagged transaction | amount, group, Q1, Q3, IQR, threshold |

## Data Privacy

- Customer IDs are **pseudonymous** — no real names, emails, or phone numbers
- No card numbers, CVV, PINs, passwords, or authentication secrets
- Location limited to **city/region** granularity only
- Dashboard shows **aggregated** customer behavior, never raw personal data
