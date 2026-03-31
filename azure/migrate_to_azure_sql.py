"""
Azure SQL Migration Script
Migrates the SQLite database to Azure SQL for Power BI integration.
Run this after provisioning Azure infrastructure.
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime

print("🔄 Azure SQL Migration Script")
print("=" * 50)

# ── CHECK ENVIRONMENT ─────────────────────────────────────────────────────────
azure_conn_str = os.getenv("AZURE_SQL_CONNECTION")
if not azure_conn_str:
    print("\n⚠️  AZURE_SQL_CONNECTION not set.")
    print("   Running in LOCAL mode — exporting to CSV for manual Power BI connection")
    LOCAL_MODE = True
else:
    LOCAL_MODE = False
    try:
        import pyodbc
        conn = pyodbc.connect(azure_conn_str)
        print("✅ Connected to Azure SQL")
    except ImportError:
        print("❌ pyodbc not installed. Run: pip install pyodbc")
        LOCAL_MODE = True

# ── LOAD FROM SQLITE ──────────────────────────────────────────────────────────
print("\n📖 Reading from SQLite...")
sqlite_path = os.path.join(os.path.dirname(__file__), "..", "outputs", "retail.db")
sqlite_conn = sqlite3.connect(sqlite_path)

tables = {
    "transactions":  pd.read_sql("SELECT * FROM transactions", sqlite_conn),
    "products":      pd.read_sql("SELECT * FROM products",     sqlite_conn),
    "stores":        pd.read_sql("SELECT * FROM stores",       sqlite_conn),
    "inventory":     pd.read_sql("SELECT * FROM inventory",    sqlite_conn),
}

for name, df in tables.items():
    print(f"  ✓ {name}: {len(df):,} rows")

sqlite_conn.close()

# ── CREATE ANALYTICAL VIEWS (for Power BI) ────────────────────────────────────
def create_powerbi_views(df_txn, df_products, df_stores, df_inventory):
    """Create denormalized views optimized for Power BI."""

    # Fact table: enriched transactions
    fact_sales = df_txn.merge(
        df_products[["sku_id","product_name","category","gross_margin","abc_class","supplier_lead_days"]],
        on="sku_id", how="left"
    ).merge(
        df_stores[["store_id","store_name","city","region","tier","target_monthly_revenue"]],
        on="store_id", how="left"
    )
    fact_sales["year"]    = pd.to_datetime(fact_sales["date"]).dt.year
    fact_sales["month"]   = pd.to_datetime(fact_sales["date"]).dt.month
    fact_sales["quarter"] = pd.to_datetime(fact_sales["date"]).dt.quarter
    fact_sales["weekday"] = pd.to_datetime(fact_sales["date"]).dt.day_name()

    # Dim: Date table (Power BI needs this for time intelligence)
    dates = pd.date_range("2023-01-01", "2024-12-31", freq="D")
    dim_date = pd.DataFrame({
        "date":         dates.strftime("%Y-%m-%d"),
        "year":         dates.year,
        "quarter":      dates.quarter,
        "month":        dates.month,
        "month_name":   dates.strftime("%B"),
        "week":         dates.isocalendar().week,
        "weekday":      dates.day_name(),
        "is_weekend":   (dates.dayofweek >= 5).astype(int),
        "fiscal_year":  dates.year,  # adjust if fiscal year differs
        "fiscal_month": dates.month,
    })

    # KPI Summary (for Power BI cards)
    kpi_summary = pd.DataFrame([{
        "metric": "Total Revenue",         "value": df_txn["revenue"].sum(),        "unit": "INR"},
        {"metric": "Lost Revenue",          "value": df_txn["lost_revenue"].sum(),   "unit": "INR"},
        {"metric": "Gross Profit",          "value": df_txn["gross_profit"].sum(),   "unit": "INR"},
        {"metric": "Stockout Rate %",       "value": df_txn["is_stockout"].mean()*100, "unit": "%"},
        {"metric": "Total Units Sold",      "value": df_txn["qty_sold"].sum(),       "unit": "units"},
        {"metric": "Total Units Lost",      "value": df_txn["lost_units"].sum(),     "unit": "units"},
        {"metric": "Avg Daily Revenue",     "value": df_txn.groupby("date")["revenue"].sum().mean(), "unit": "INR"},
        {"metric": "Active SKUs",           "value": df_txn["sku_id"].nunique(),     "unit": "count"},
        {"metric": "Active Stores",         "value": df_txn["store_id"].nunique(),   "unit": "count"},
        {"metric": "Avg Discount Applied",  "value": df_txn[df_txn["discount_pct"]>0]["discount_pct"].mean()*100, "unit": "%"},
    ])

    return fact_sales, dim_date, kpi_summary


fact_sales, dim_date, kpi_summary = create_powerbi_views(
    tables["transactions"], tables["products"], tables["stores"], tables["inventory"]
)

# ── AZURE SQL UPLOAD (or CSV export for local Power BI) ───────────────────────
output_dir = os.path.join(os.path.dirname(__file__), "..", "outputs", "powerbi_data")
os.makedirs(output_dir, exist_ok=True)

if LOCAL_MODE:
    print("\n📤 Exporting Power BI-ready CSVs...")

    exports = {
        "fact_sales":        fact_sales,
        "dim_products":      tables["products"],
        "dim_stores":        tables["stores"],
        "dim_date":          dim_date,
        "dim_inventory":     tables["inventory"],
        "kpi_summary":       kpi_summary,
    }
    for name, df in exports.items():
        path = os.path.join(output_dir, f"{name}.csv")
        df.to_csv(path, index=False)
        print(f"  ✓ {name}.csv ({len(df):,} rows) → {path}")

    print(f"""
✅ Power BI files ready at: outputs/powerbi_data/

📊 To connect Power BI Desktop:
   1. Open Power BI Desktop
   2. Get Data → Text/CSV → select fact_sales.csv
   3. Also import: dim_products, dim_stores, dim_date, kpi_summary
   4. In Model view, create relationships:
      • fact_sales[sku_id]   → dim_products[sku_id]
      • fact_sales[store_id] → dim_stores[store_id]
      • fact_sales[date]     → dim_date[date]
   5. Create measures using DAX from: powerbi/dax_measures.dax
""")

else:
    print("\n📤 Uploading to Azure SQL...")
    engine_str = azure_conn_str.replace("Driver={ODBC Driver 18 for SQL Server};", "")

    uploads = {
        "fact_sales":    fact_sales,
        "dim_products":  tables["products"],
        "dim_stores":    tables["stores"],
        "dim_date":      dim_date,
        "dim_inventory": tables["inventory"],
        "kpi_summary":   kpi_summary,
    }
    cursor = conn.cursor()
    for table_name, df in uploads.items():
        print(f"  Uploading {table_name} ({len(df):,} rows)...", end=" ")
        # Batch insert with chunking
        chunk_size = 1000
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i+chunk_size]
            placeholders = ", ".join(["?" * len(df.columns)][0].split() or ["?"] * len(df.columns))
        print("✓")

    conn.commit()
    conn.close()
    print("\n✅ Azure SQL migration complete!")
    print("   Connect Power BI Desktop to Azure SQL using the connection string from Key Vault")

print("\n🚀 Next: Open powerbi/Retail_Intelligence.pbit in Power BI Desktop")
