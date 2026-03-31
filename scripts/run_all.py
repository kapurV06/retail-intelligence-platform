"""
🚀 RETAIL INTELLIGENCE PLATFORM — MAIN ORCHESTRATOR
Run this to generate all data, analysis, and reports.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from generate_data import df_products, df_stores, df_txn, df_inventory
from eda_analysis   import run_eda
from sql_analytics  import build_database, run_sql_analytics
from excel_report   import build_excel_report
import json, pickle

os.chdir(os.path.dirname(__file__))

print("="*60)
print("  RETAIL INVENTORY INTELLIGENCE PLATFORM")
print("  Solving the $1.75T Stockout Crisis")
print("="*60)

# Step 1: EDA
eda_results = run_eda(df_txn, df_products, df_stores, df_inventory)

# Step 2: SQL
conn = build_database(df_txn, df_products, df_stores, df_inventory)
sql_results = run_sql_analytics(conn)

# Step 3: Excel
build_excel_report(eda_results, sql_results)

# Step 4: Save analysis cache for dashboard
os.makedirs("../outputs", exist_ok=True)

# Convert DataFrames to JSON-serializable dicts for the dashboard
cache = {
    "kpis":                 eda_results["kpis"],
    "monthly_trend":        eda_results["monthly_trend"].to_dict("records"),
    "category_performance": eda_results["category_performance"].to_dict("records"),
    "store_performance":    eda_results["store_performance"].to_dict("records"),
    "regional":             eda_results["regional"].to_dict("records"),
    "weekday_analysis":     eda_results["weekday_analysis"].to_dict("records"),
    "inventory_risk":       eda_results["inventory_risk"].to_dict("records"),
    "demand_forecast":      eda_results["demand_forecast"],
    "revenue_recovery":     sql_results["revenue_recovery"].to_dict("records"),
    "store_abc":            sql_results["store_abc"].to_dict("records"),
    "monthly_stockout":     sql_results["monthly_stockout"].to_dict("records"),
    "chronic_stockouts":    sql_results["chronic_stockouts"].to_dict("records"),
    "region_tier_matrix":   sql_results["region_tier_matrix"].to_dict("records"),
}

with open("../outputs/analytics_cache.json", "w") as f:
    json.dump(cache, f, default=str)

print("\n✅ Analytics cache saved for dashboard.")
print("\n🚀 Now run: streamlit run dashboard.py")
