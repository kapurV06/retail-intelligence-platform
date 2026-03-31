# Retail Inventory Intelligence Platform

> **Solving the $1.75 trillion global stockout crisis with end-to-end data analytics**

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template)
[![Azure App Service](https://img.shields.io/badge/Azure-App%20Service-0078D4?logo=microsoftazure)](https://azure.microsoft.com)
[![Power BI](https://img.shields.io/badge/Power%20BI-Connected-F2C811?logo=powerbi)](https://powerbi.microsoft.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Deployed-FF4B4B?logo=streamlit)](https://streamlit.io)

---

## The Problem

Retailers globally lose **$1.75 trillion/year** to inventory mismanagement — stockouts that lose sales, and overstocks that tie up capital. Most companies have the data. They just can't act on it fast enough.

This platform answers: **Which SKUs, in which stores, will stock out next — and what does it cost us?**

**Quantified in this dataset:**
- **₹623M lost** to stockouts across 18 months
- **9.1% of all demand** goes unmet
- Top 10 SKUs account for **40% of all lost revenue**

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Data Generation** | Python, Faker, NumPy | Realistic synthetic retail dataset |
| **EDA** | Pandas, SciPy | KPIs, trends, risk matrix, forecasting |
| **SQL Analytics** | SQLite → Azure SQL | Window functions, CTEs, ABC analysis |
| **Excel Reporting** | openpyxl, xlsxwriter | 7-sheet executive workbook |
| **Dashboard** | Streamlit + Plotly | 6-page interactive dashboard |
| **BI** | Power BI Desktop + Service | DAX measures, star schema, embedded reports |
| **Cloud** | Azure App Service | Containerized deployment |
| **CI/CD** | GitHub Actions | Automated test → build → deploy |
| **Container** | Docker | Reproducible, portable deployment |
| **Secrets** | Azure Key Vault | Connection strings, API keys |
| **Storage** | Azure Blob Storage | Power BI data source, report cache |
| **Database** | Azure SQL | Production data store for Power BI DirectQuery |

---

## Quick Start

### Local Development
```bash
git clone https://github.com/yourname/retail-intelligence-platform
cd retail-intelligence-platform
pip install -r requirements.txt

# Generate data + run full pipeline
python scripts/run_all.py

# Launch dashboard
streamlit run app.py
```

### Docker
```bash
docker build -t retail-intel .
docker run -p 8000:8000 retail-intel
# Open http://localhost:8000
```

### Azure Deployment
```bash
# 1. Provision infrastructure (one-time)
bash azure/provision.sh

# 2. Set GitHub Secrets:
#    AZURE_CREDENTIALS, AZURE_SQL_CONNECTION,
#    AZURE_STORAGE_CONNECTION, POWER_BI_WORKSPACE_ID

# 3. Push to main → GitHub Actions auto-deploys
git push origin main
```

---

## Project Structure

```
retail-intelligence-platform/
│
├── app.py                          
├── Dockerfile                      
├── requirements.txt
│
├── scripts/
│   ├── generate_data.py            
│   ├── eda_analysis.py             
│   ├── sql_analytics.py            
│   ├── excel_report.py             
│   └── run_all.py                  
│
├── azure/
│   ├── provision.sh               
│   └── migrate_to_azure_sql.py     
│
├── powerbi/
│   ├── dax_measures.dax            
│   └── DATA_MODEL.md               
│
├── .github/
│   └── workflows/
│       └── azure-deploy.yml        
│
├── data/                           
└── outputs/
    ├── retail.db                   
    ├── analytics_cache.json        
    └── Retail_Intelligence_Report.xlsx  
```

---

## Dashboard Pages

1. **Executive Overview** — Revenue trend, MoM growth, regional breakdown
2. **Category Deep Dive** — Margin analysis, revenue vs loss scatter, weekday heatmap
3. **Store Performance** — Leaderboard, target attainment, tier comparison
4. **Stockout Risk** — Chronic SKUs, loss funnel, trend analysis
5. **Revenue Recovery** — Waterfall chart, priority matrix, action table
6. **Demand Forecast** — Historical trend + 3-month projection, inventory risk

---

## 💡 Business Impact

If stockout rate is reduced from **9.1% → 4.5%** :
- **Annual revenue recovery: ~₹415M**
- **Top 10 SKU fix: ~₹250M alone**
- **ROI timeline: 3–6 months** (technology cost vs revenue gain)
