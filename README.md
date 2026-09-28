# 🏦 Bank Transaction Descriptive Analytics

> **Transform raw banking transaction records into statistically grounded, visual, and decision-ready insights.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/dashboard-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/api-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)

---

## 📋 Overview

This project analyzes historical bank transaction data across **six analytical dimensions**:

| Dimension | What It Answers |
|---|---|
| **Amount** | How are transaction values distributed? What are mean, median, percentiles? |
| **Frequency** | How often do transactions occur by day, week, month, category? |
| **Customer** | How active are customers? What's the concentration of value? |
| **Time** | When do transactions peak — by hour, day, month? |
| **Category** | Which categories/channels drive the most volume and value? |
| **Outliers** | Which transactions are statistical outliers (IQR method)? |

### What This Is
✅ Descriptive analytics — what happened, how much, how often, when
✅ Statistical analysis with visualizations and interactive dashboard
✅ Reproducible, auditable pipeline with centralized KPI definitions

### What This Is NOT
❌ Fraud detection or scoring
❌ Predictive ML models (churn, credit risk)
❌ Anti-money-laundering case decisions
❌ Connected to live bank accounts

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <repo-url>
cd bank-transaction-analytics

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Sample Data

```bash
python src/generate_dataset.py
```

This creates `data/sample/transactions.csv` with 50,000 synthetic transactions.

### 3. Run the Dashboard

```bash
streamlit run dashboard/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### 4. Run the API (Optional)

```bash
uvicorn api.main:app --reload --port 8000
```

API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

### 5. Run Tests

```bash
pytest tests/ -v
```

---

## 🏗️ Architecture

```
Data Source → Ingestion → Cleaning → Analytics → Metrics → Dashboard/API/Report
  (CSV)      (loader)    (dedupe,    (derived    (SINGLE     (Streamlit,
              schema)     nulls,     fields,    SOURCE OF    FastAPI,
                          normalize)  aggs)     TRUTH)       Jinja2)
```

### Key Design Principle

> **Centralized Metrics Library** (`src/metrics/metrics.py`): Every KPI is computed **exactly once**. The dashboard, API, and report all import from this single module — never recalculated inline.

---

## 📊 Dashboard Pages

| Page | Content |
|---|---|
| **📊 Executive Overview** | 6 KPI cards, monthly trend, top categories, channel/status distribution |
| **💰 Transaction Analysis** | Amount histogram, descriptive statistics, box plots, outlier review |
| **👥 Customer Activity** | Customer distributions, top 20 table, concentration analysis |
| **🕐 Time & Behavior** | Day×hour heatmap, weekday vs weekend, hourly/daily trends |

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/kpis` | GET | Executive KPI summary |
| `/api/v1/amount-stats` | GET | Full descriptive statistics |
| `/api/v1/frequency` | GET | Transaction frequency by dimension |
| `/api/v1/customers` | GET | Paginated customer metrics |
| `/api/v1/time-patterns` | GET | Time pattern distributions |
| `/api/v1/categories` | GET | Category/channel breakdowns |
| `/api/v1/outliers` | GET | IQR-flagged outliers |
| `/api/v1/data-quality` | GET | Data quality summary |

All endpoints accept filter query parameters: `start_date`, `end_date`, `transaction_type`, `category`, `status`, `channel`, `payment_method`.

---

## 🐳 Docker Deployment

```bash
docker-compose up --build
```

| Service | Port | Technology |
|---|---|---|
| Dashboard | 80 (via nginx) | Streamlit |
| API | 80/api/ (via nginx) | FastAPI |
| Database | 5432 (internal) | PostgreSQL 16 |
| Cache | 6379 (internal) | Redis 7 |

---

## 📁 Project Structure

```
bank-transaction-analytics/
├── data/               # Raw, processed, and sample datasets
├── src/
│   ├── ingestion/      # loader.py, schema_validator.py
│   ├── cleaning/       # dedupe.py, null_handler.py, normalizer.py
│   ├── analytics/      # derived_fields, customer/time/category aggregates
│   ├── metrics/        # metrics.py — SINGLE SOURCE OF TRUTH
│   └── visualization/  # Plotly chart builders
├── api/                # FastAPI application
├── dashboard/          # Streamlit multi-page dashboard
├── reports/            # Report templates and generator
├── tests/              # Comprehensive test suite
├── docs/               # Data dictionary and methodology
├── docker-compose.yml
└── Dockerfile
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html
```

Tests cover: schema validation, data quality rules, metrics accuracy, KPI reconciliation, and edge cases.

---

## 📖 Methodology

See [docs/methodology.md](docs/methodology.md) for statistical methods and [docs/data_dictionary.md](docs/data_dictionary.md) for field definitions.

---

## 📄 License

This project is for educational and analytical purposes.
