"""
EDA Pipeline — Retail Inventory Intelligence
Pandas-powered analysis that feeds both the Excel report and dashboard.
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings("ignore")

def run_eda(df_txn, df_products, df_stores, df_inventory):
    print("🔍 Running advanced EDA pipeline...")
    results = {}

    # ── 1. REVENUE OVERVIEW ───────────────────────────────────────────────────
    results["kpis"] = {
        "total_revenue":        round(df_txn["revenue"].sum(), 2),
        "total_lost_revenue":   round(df_txn["lost_revenue"].sum(), 2),
        "total_gross_profit":   round(df_txn["gross_profit"].sum(), 2),
        "avg_daily_revenue":    round(df_txn.groupby("date")["revenue"].sum().mean(), 2),
        "total_transactions":   len(df_txn[df_txn["qty_sold"] > 0]),
        "stockout_rate":        round(df_txn["is_stockout"].mean() * 100, 2),
        "lost_revenue_pct":     round(df_txn["lost_revenue"].sum() / (df_txn["revenue"].sum() + df_txn["lost_revenue"].sum()) * 100, 2),
        "avg_discount":         round(df_txn[df_txn["discount_pct"] > 0]["discount_pct"].mean() * 100, 2),
        "total_units_sold":     int(df_txn["qty_sold"].sum()),
        "total_units_lost":     int(df_txn["lost_units"].sum()),
    }

    # ── 2. MONTHLY REVENUE TREND ──────────────────────────────────────────────
    df_txn = df_txn.copy()
    df_txn["month"] = pd.to_datetime(df_txn["date"]).dt.to_period("M")
    monthly = df_txn.groupby("month").agg(
        revenue=("revenue","sum"),
        lost_revenue=("lost_revenue","sum"),
        gross_profit=("gross_profit","sum"),
        transactions=("txn_id","count"),
        stockout_events=("is_stockout","sum"),
    ).reset_index()
    monthly["month"] = monthly["month"].astype(str)
    monthly["stockout_rate"] = (monthly["stockout_events"] / monthly["transactions"] * 100).round(2)
    monthly["mom_growth"] = monthly["revenue"].pct_change() * 100
    results["monthly_trend"] = monthly

    # ── 3. CATEGORY PERFORMANCE ───────────────────────────────────────────────
    cat_perf = df_txn.groupby("category").agg(
        revenue=("revenue","sum"),
        lost_revenue=("lost_revenue","sum"),
        gross_profit=("gross_profit","sum"),
        units_sold=("qty_sold","sum"),
        units_lost=("lost_units","sum"),
        stockout_events=("is_stockout","sum"),
        total_events=("txn_id","count"),
    ).reset_index()
    cat_perf["stockout_rate"]    = (cat_perf["stockout_events"] / cat_perf["total_events"] * 100).round(2)
    cat_perf["lost_rev_pct"]     = (cat_perf["lost_revenue"] / (cat_perf["revenue"] + cat_perf["lost_revenue"]) * 100).round(2)
    cat_perf["avg_margin"]       = cat_perf["gross_profit"] / cat_perf["revenue"].replace(0, np.nan)
    cat_perf = cat_perf.sort_values("revenue", ascending=False)
    results["category_performance"] = cat_perf

    # ── 4. TOP LOSS-CAUSING SKUs ──────────────────────────────────────────────
    sku_loss = df_txn.groupby("sku_id").agg(
        total_lost_revenue=("lost_revenue","sum"),
        stockout_count=("is_stockout","sum"),
        total_events=("txn_id","count"),
        revenue=("revenue","sum"),
    ).reset_index()
    sku_loss = sku_loss.merge(df_products[["sku_id","product_name","category","abc_class","unit_price"]], on="sku_id")
    sku_loss["stockout_rate"] = (sku_loss["stockout_count"] / sku_loss["total_events"] * 100).round(1)
    sku_loss = sku_loss.sort_values("total_lost_revenue", ascending=False)
    results["top_loss_skus"] = sku_loss.head(50)

    # ── 5. STORE PERFORMANCE ──────────────────────────────────────────────────
    store_perf = df_txn.groupby("store_id").agg(
        revenue=("revenue","sum"),
        lost_revenue=("lost_revenue","sum"),
        gross_profit=("gross_profit","sum"),
        stockout_events=("is_stockout","sum"),
        total_events=("txn_id","count"),
    ).reset_index()
    store_perf = store_perf.merge(df_stores[["store_id","store_name","city","region","tier","target_monthly_revenue"]], on="store_id")
    store_perf["stockout_rate"]    = (store_perf["stockout_events"] / store_perf["total_events"] * 100).round(2)
    store_perf["monthly_revenue"]  = store_perf["revenue"] / 18
    store_perf["target_attainment"] = (store_perf["monthly_revenue"] / store_perf["target_monthly_revenue"] * 100).round(1)
    store_perf["revenue_rank"]     = store_perf["revenue"].rank(ascending=False).astype(int)
    results["store_performance"] = store_perf.sort_values("revenue", ascending=False)

    # ── 6. REGIONAL BREAKDOWN ─────────────────────────────────────────────────
    regional = store_perf.groupby("region").agg(
        revenue=("revenue","sum"),
        lost_revenue=("lost_revenue","sum"),
        store_count=("store_id","count"),
        avg_stockout_rate=("stockout_rate","mean"),
    ).reset_index()
    results["regional"] = regional

    # ── 7. WEEKDAY ANALYSIS ───────────────────────────────────────────────────
    df_txn["weekday"] = pd.to_datetime(df_txn["date"]).dt.day_name()
    weekday_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    weekday = df_txn.groupby("weekday").agg(
        revenue=("revenue","sum"),
        stockout_events=("is_stockout","sum"),
        transactions=("txn_id","count"),
    ).reindex(weekday_order).reset_index()
    weekday["avg_daily_revenue"] = weekday["revenue"] / 18  # ~18 of each weekday
    results["weekday_analysis"] = weekday

    # ── 8. INVENTORY RISK MATRIX ──────────────────────────────────────────────
    latest_inv = df_inventory.sort_values("snapshot_date").groupby(["store_id","sku_id"]).last().reset_index()
    risk_matrix = latest_inv.groupby("sku_id").agg(
        avg_stock=("stock_level","mean"),
        stores_at_risk=("is_stockout_risk","sum"),
        stores_overstocked=("overstock_flag","sum"),
        total_stores=("store_id","count"),
        total_inv_value=("inventory_value","sum"),
    ).reset_index()
    risk_matrix = risk_matrix.merge(df_products[["sku_id","product_name","category","abc_class"]], on="sku_id")
    risk_matrix["risk_coverage_pct"] = (risk_matrix["stores_at_risk"] / risk_matrix["total_stores"] * 100).round(1)
    # Priority score: A-class items at risk get highest score
    abc_weight = {"A": 3, "B": 2, "C": 1}
    risk_matrix["abc_weight"]  = risk_matrix["abc_class"].map(abc_weight)
    risk_matrix["priority_score"] = (risk_matrix["risk_coverage_pct"] * risk_matrix["abc_weight"]).round(1)
    results["inventory_risk"] = risk_matrix.sort_values("priority_score", ascending=False).head(50)

    # ── 9. DEMAND FORECASTING (simple trend + seasonality) ───────────────────
    monthly_demand = df_txn.groupby("month")["qty_demanded"].sum().reset_index()
    monthly_demand["month_num"] = range(len(monthly_demand))
    # Linear trend
    slope, intercept, r, p, se = stats.linregress(monthly_demand["month_num"], monthly_demand["qty_demanded"])
    # Forecast next 3 months
    future_months = [len(monthly_demand), len(monthly_demand)+1, len(monthly_demand)+2]
    forecasts = [intercept + slope * m for m in future_months]
    results["demand_forecast"] = {
        "slope":    round(slope, 2),
        "r_squared": round(r**2, 3),
        "forecast_next_3": [round(f) for f in forecasts],
        "trend": "increasing" if slope > 0 else "decreasing",
    }

    print("  ✓ KPIs computed")
    print("  ✓ Monthly trends, category/store/regional analysis done")
    print("  ✓ Inventory risk matrix built")
    print("  ✓ Demand forecast generated")
    print(f"\n  💀 PROBLEM QUANTIFIED: ₹{results['kpis']['total_lost_revenue']:,.0f} lost to stockouts")
    print(f"  📉 That's {results['kpis']['lost_revenue_pct']}% of potential revenue GONE.")
    return results
