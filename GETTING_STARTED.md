# 🚀 Getting Started — Bank Transaction Descriptive Analytics

A step-by-step guide to set up, run, and explore the project.

---

## 📋 Prerequisites

Before you begin, make sure you have the following installed:

| Software | Minimum Version | Check Command |
|---|---|---|
| **Python** | 3.11+ | `python --version` |
| **pip** | 24.0+ | `pip --version` |
| **Git** | 2.x | `git --version` |
| **Docker** *(optional)* | 24.x | `docker --version` |

---

## 🔧 Step 1 — Clone & Navigate to the Project

```bash
# If the repo is on GitHub/GitLab
git clone <your-repo-url>
cd bank-transaction-analytics

# If you already have the folder locally
cd D:\saswati-data\bank-transaction-analytics
```

---

## 🐍 Step 2 — Create a Python Virtual Environment

Creating a virtual environment keeps project dependencies isolated from your system Python.

### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Windows (Command Prompt)

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

> ✅ You should see `(venv)` at the beginning of your terminal prompt after activation.

---

## 📦 Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all required packages:

| Package | Purpose |
|---|---|
| `pandas`, `numpy` | Data processing |
| `scipy` | Statistical calculations |
| `plotly`, `matplotlib`, `seaborn` | Visualization |
| `streamlit` | Interactive dashboard |
| `fastapi`, `uvicorn` | REST API |
| `pydantic`, `pandera` | Schema validation |
| `pytest` | Testing |
| `jinja2` | Report templates |
| `openpyxl` | Excel file support |

---

## 📊 Step 4 — Generate the Sample Dataset

The project comes with a synthetic data generator that creates 50,000 realistic bank transactions:

```bash
python src/generate_dataset.py
```

**Expected output:**

```
Generating synthetic transaction dataset...
==================================================
Dataset saved to: data/sample/transactions.csv
Total records: 50,000
Unique customers: 2,000
Date range: 2023-01-01 to 2024-12-31
Amount range: -500,000.00 to 500,000.00
```

The generated file will be at: `data/sample/transactions.csv`

> 💡 **Using your own data?** Place your CSV or Excel file in `data/raw/` and upload it through the dashboard sidebar, or update the path in the code.

---

## ✅ Step 5 — Run the Tests

Verify everything is working correctly:

```bash
python -m pytest tests/ -v
```

**Expected output:**

```
tests/test_all.py::TestSchemaValidation::test_valid_schema PASSED
tests/test_all.py::TestSchemaValidation::test_missing_required_column PASSED
tests/test_all.py::TestSchemaValidation::test_empty_dataset PASSED
...
============================= 23 passed ==============================
```

All 23 tests should pass ✅

---

## 🖥️ Step 6 — Launch the Dashboard

This is the main way to interact with the project:

```bash
streamlit run dashboard/app.py
```

**Expected output:**

```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Open **http://localhost:8501** in your browser.

### Dashboard Pages

| Page | What You'll See |
|---|---|
| **🏦 Home** | KPI summary cards, navigation guide |
| **📊 Executive Overview** | Monthly trends, top categories, channel/status charts |
| **💰 Transaction Analysis** | Amount histogram, descriptive stats, box plots, outlier table |
| **👥 Customer Activity** | Customer distributions, top 20 table, concentration analysis |
| **🕐 Time & Behavior** | Day×hour heatmap, weekday vs weekend, hourly patterns |

### Using Filters

The **sidebar** on the left contains global filters that affect all pages:

- **Date Range** — Filter by transaction date window
- **Transaction Type** — Deposit, Withdrawal, Transfer, Payment, Refund
- **Category** — Food & Dining, Shopping, Salary, etc.
- **Status** — Completed, Failed, Reversed, Pending
- **Channel** — ATM, Branch, Mobile, Web, POS
- **Payment Method** — Card, UPI, Bank Transfer, Cash

> All charts and KPI cards update automatically when you change any filter.

---

## 🔌 Step 7 — Launch the API *(Optional)*

If you want to access the metrics programmatically via REST API:

```bash
uvicorn api.main:app --reload --port 8000
```

Then open **http://localhost:8000/docs** for the interactive Swagger UI.

### Available Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/kpis` | GET | Executive KPI summary |
| `/api/v1/amount-stats` | GET | Full descriptive statistics |
| `/api/v1/frequency?dimension=category` | GET | Frequency by any dimension |
| `/api/v1/customers?page=1&page_size=20` | GET | Paginated customer metrics |
| `/api/v1/time-patterns` | GET | Hourly/daily/weekly patterns |
| `/api/v1/categories` | GET | Category/channel breakdown |
| `/api/v1/outliers` | GET | IQR-flagged outlier records |
| `/api/v1/data-quality` | GET | Data quality summary |
| `/health` | GET | Health check |

### Example API Calls

```bash
# Get KPI summary
curl http://localhost:8000/api/v1/kpis

# Get amount statistics
curl http://localhost:8000/api/v1/amount-stats

# Get frequency by category
curl "http://localhost:8000/api/v1/frequency?dimension=category"

# Get top customers (page 1, 10 per page)
curl "http://localhost:8000/api/v1/customers?page=1&page_size=10&sort_by=total_value&sort_order=desc"

# Get outliers grouped by transaction type
curl "http://localhost:8000/api/v1/outliers?group_by=transaction_type"

# Filter KPIs by date range and status
curl "http://localhost:8000/api/v1/kpis?start_date=2024-01-01&end_date=2024-06-30&status=Completed"
```

---

## 🐳 Step 8 — Docker Deployment *(Optional)*

To run the full stack (Dashboard + API + PostgreSQL + Redis + Nginx) via Docker:

```bash
docker-compose up --build
```

| Service | Access URL |
|---|---|
| Dashboard | http://localhost (port 80) |
| API | http://localhost/api/v1/kpis |
| API Docs | http://localhost/docs |

To stop all containers:

```bash
docker-compose down
```

---

## 🔄 Step 9 — Run the Data Pipeline Manually *(Optional)*

If you want to run the pipeline on a specific file from the command line:

```bash
python -c "
from src.pipeline import run_pipeline
result = run_pipeline('data/sample/transactions.csv')
print('Success:', result.success)
print('Clean rows:', len(result.data))
print('Quarantined:', len(result.quarantined))
print('Summary:', result.pipeline_summary)
"
```

---

## 📂 Project Structure Quick Reference

```
bank-transaction-analytics/
│
├── data/sample/transactions.csv     ← Generated dataset (Step 4)
│
├── src/
│   ├── ingestion/                   ← Data loading & validation
│   ├── cleaning/                    ← Dedup, nulls, normalization
│   ├── analytics/                   ← Derived fields & aggregates
│   ├── metrics/metrics.py           ← ⭐ Single source of truth for KPIs
│   ├── visualization/charts.py      ← Plotly chart builders
│   ├── pipeline.py                  ← End-to-end pipeline orchestrator
│   └── generate_dataset.py          ← Synthetic data generator
│
├── dashboard/
│   ├── app.py                       ← Main Streamlit app (start here)
│   └── pages/                       ← 4 analysis pages
│
├── api/main.py                      ← FastAPI with 9 endpoints
├── tests/test_all.py                ← 23 comprehensive tests
├── docs/                            ← Data dictionary & methodology
└── docker-compose.yml               ← Full Docker deployment
```

---

## ❓ Troubleshooting

### "Module not found" errors

Make sure you're running commands from the project root directory:

```bash
cd D:\saswati-data\bank-transaction-analytics
```

And that your virtual environment is activated:

```powershell
.\venv\Scripts\Activate.ps1
```

### "No data file found" on the dashboard

Generate the sample dataset first:

```bash
python src/generate_dataset.py
```

### Port already in use

If port 8501 is already in use, specify a different port:

```bash
streamlit run dashboard/app.py --server.port 8502
```

### Dashboard shows "Please navigate to the main dashboard first"

When navigating to sub-pages directly, the data isn't loaded yet. Always start from the **main app page** first (http://localhost:8501), then navigate to sub-pages from the sidebar.

### Tests failing

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

---

## 📝 Quick Commands Cheat Sheet

| Action | Command |
|---|---|
| Install dependencies | `pip install -r requirements.txt` |
| Generate sample data | `python src/generate_dataset.py` |
| Run tests | `python -m pytest tests/ -v` |
| Start dashboard | `streamlit run dashboard/app.py` |
| Start API | `uvicorn api.main:app --reload --port 8000` |
| Docker (full stack) | `docker-compose up --build` |
| Stop Docker | `docker-compose down` |

---

> 🎓 **For detailed documentation**, see:
> - [Data Dictionary](docs/data_dictionary.md) — All field definitions
> - [Methodology](docs/methodology.md) — Statistical methods used
> - [README](README.md) — Full project overview
