# Methodology — Bank Transaction Analytics

## Statistical Methods

All statistical methods are implemented in `src/metrics/metrics.py` as the single source of truth.
Each method maps to a specific, well-known implementation (Architecture §7).

### Central Tendency

| Measure | Implementation | Notes |
|---|---|---|
| **Mean** | `pandas .mean()` | Never shown alone — always paired with median due to skew |
| **Median** | `pandas .median()` | More robust to outliers than mean |
| **Mode** | `pandas .mode()` | Used for categorical fields |

### Dispersion

| Measure | Implementation | Notes |
|---|---|---|
| **Standard Deviation** | `pandas .std()` | Sample standard deviation (ddof=1) |
| **Variance** | `pandas .var()` | Sample variance |
| **Range** | `max - min` | Sensitive to outliers |
| **IQR** | `Q3 - Q1` | Robust measure of spread |
| **Coefficient of Variation** | `std / mean × 100` | Relative dispersion |

### Distribution Shape

| Measure | Implementation | Notes |
|---|---|---|
| **Skewness** | `pandas .skew()` | Positive = right-skewed (typical for banking) |
| **Kurtosis** | `pandas .kurtosis()` | Excess kurtosis (relative to normal) |

### Quantiles

| Measure | Implementation |
|---|---|
| **Quartiles** | `pandas .quantile([0.25, 0.50, 0.75])` |
| **Percentiles** | `pandas .quantile([0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99])` |

### Correlation

| Measure | Implementation | Notes |
|---|---|---|
| **Pearson correlation** | `pandas .corr()` | Reported as association only, never causation |

## Outlier Detection Method

**IQR-based outlier rule** (PRD §22):

```
Upper outlier:  amount > Q3 + 1.5 × IQR
Lower outlier:  amount < Q1 - 1.5 × IQR
```

Where:
- Q1 = 25th percentile
- Q3 = 75th percentile
- IQR = Q3 - Q1

**Important**: Outlier flags are for **descriptive analytical review only**.
They should NOT be described as evidence of fraud or suspicious behavior.

## Data Pipeline Stages

1. **Ingest** — Load raw CSV/Excel/DB records
2. **Validate** — Check required columns, data types, generate validation report
3. **Clean** — Handle nulls, invalid values, quarantine bad records with reason codes
4. **Normalize** — Standardize categories via controlled vocabulary maps
5. **Deduplicate** — Remove duplicate IDs and exact duplicate rows with audit
6. **Derive** — Add date parts, amount bands, absolute amounts
7. **Aggregate** — Compute customer, time, and category metrics
8. **Statistics** — Run descriptive statistics and outlier analysis
9. **Visualize** — Build chart-ready datasets
10. **Publish** — Refresh dashboard and generate reports

## KPI Definitions

| KPI | Formula | Source |
|---|---|---|
| Total Transactions | `COUNT(valid transaction_id)` | PRD §19 |
| Total Transaction Value | `SUM(amount)` under documented sign convention | PRD §19 |
| Average Transaction Value | `SUM(amount) / COUNT(transactions)` | PRD §19 |
| Median Transaction Value | `MEDIAN(valid amounts)` | PRD §19 |
| Active Customers | `COUNT(DISTINCT customer_id)` with valid activity | PRD §19 |
| Transactions per Customer | Total transactions / active customers | PRD §19 |
| Average Customer Value | Total value / active customers | PRD §19 |
| Active Days | `COUNT(DISTINCT transaction_date per customer)` | PRD §19 |
| 95th Percentile Amount | 95th percentile of valid amounts | PRD §19 |

## Key Analytical Principle

> The mean is never shown without its robust counterparts (median, percentiles)
> because banking amounts are typically right-skewed. This is enforced structurally
> by having `kpi_summary()` and `amount_statistics()` always return both together.
