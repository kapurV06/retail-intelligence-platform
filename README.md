# Retail Inventory Intelligence Platform

End-to-end retail analytics pipeline — from synthetic data generation to an interactive dashboard and Power BI reports.

The core question: which SKUs are heading toward stockouts, and what's the revenue cost? Built the full stack to answer it: data generation, SQL analytics, an Excel workbook, a Streamlit dashboard, and Power BI on top.

---

## What's inside

**Data layer** — synthetic retail dataset (18 months, multiple stores and SKUs) generated with realistic demand patterns and seasonal variation.

**Analytics** — Pandas + SciPy for EDA, SQLite with window functions and CTEs for inventory and ABC analysis, `openpyxl` for a 7-sheet executive Excel report.

**Dashboard** — 6-page Streamlit app covering executive overview, category breakdown, store performance, stockout risk, revenue recovery waterfall, and a 3-month demand forecast.

**BI layer** — Power BI reports with DAX measures and a star schema data model.

**Infra** — Dockerized, CI/CD via GitHub Actions for automated testing and builds.

---

## Stack

`Python` · `Pandas` · `SciPy` · `SQLite` · `Plotly` · `Streamlit` · `Power BI` · `openpyxl` · `Docker` · `GitHub Actions`

---

## Run it

```bash
git clone https://github.com/kapurV06/retail-intelligence-platform
cd retail-intelligence-platform
pip install -r requirements.txt

# Generate data and run the full pipeline
python scripts/run_all.py

# Launch dashboard
streamlit run app.py
```

Or with Docker:

```bash
docker build -t retail-intel .
docker run -p 8000:8000 retail-intel
```

---

## Structure

```
retail-intelligence-platform/
├── app.py                        # Streamlit dashboard
├── Dockerfile
├── requirements.txt
├── scripts/
│   ├── generate_data.py
│   ├── eda_analysis.py
│   ├── sql_analytics.py
│   ├── excel_report.py
│   └── run_all.py
├── powerbi/
│   ├── dax_measures.dax
│   └── DATA_MODEL.md
├── .github/workflows/              # CI/CD pipeline
├── data/
└── outputs/
    ├── retail.db
    ├── analytics_cache.json
    └── Retail_Intelligence_Report.xlsx
```
