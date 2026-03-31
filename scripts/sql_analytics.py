"""
SQL Analytics Engine
Advanced SQL queries on SQLite — portfolio-worthy complexity.
"""

import sqlite3
import pandas as pd
import os

def build_database(df_txn, df_products, df_stores, df_inventory, db_path="../outputs/retail.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    print("🗄️  Building SQLite database...")
    df_txn.to_sql("transactions",  conn, if_exists="replace", index=False)
    df_products.to_sql("products",   conn, if_exists="replace", index=False)
    df_stores.to_sql("stores",     conn, if_exists="replace", index=False)
    df_inventory.to_sql("inventory", conn, if_exists="replace", index=False)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_txn_sku   ON transactions(sku_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_txn_store ON transactions(store_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_txn_date  ON transactions(date)")
    conn.commit()
    print("  ✓ 4 tables, 3 indexes created")
    return conn


def run_sql_analytics(conn):
    print("\n📊 Running SQL analytics queries...")
    results = {}

    # ── Q1: Revenue Recovery Opportunity (Window Function + CTE) ─────────────
    results["revenue_recovery"] = pd.read_sql("""
        WITH category_totals AS (
            SELECT
                category,
                SUM(revenue)       AS actual_revenue,
                SUM(lost_revenue)  AS lost_revenue,
                SUM(revenue) + SUM(lost_revenue) AS potential_revenue,
                COUNT(*)           AS total_events,
                SUM(is_stockout)   AS stockout_events
            FROM transactions
            GROUP BY category
        )
        SELECT
            category,
            ROUND(actual_revenue, 0)    AS actual_revenue,
            ROUND(lost_revenue, 0)      AS lost_revenue,
            ROUND(potential_revenue, 0) AS potential_revenue,
            ROUND(lost_revenue * 100.0 / potential_revenue, 2) AS loss_pct,
            ROUND(stockout_events * 100.0 / total_events, 2)   AS stockout_rate,
            RANK() OVER (ORDER BY lost_revenue DESC)            AS loss_rank
        FROM category_totals
        ORDER BY lost_revenue DESC
    """, conn)

    # ── Q2: Store ABC Analysis with Running Total ─────────────────────────────
    results["store_abc"] = pd.read_sql("""
        WITH store_rev AS (
            SELECT
                t.store_id,
                s.store_name,
                s.city,
                s.region,
                s.tier,
                SUM(t.revenue)      AS revenue,
                SUM(t.lost_revenue) AS lost_revenue,
                SUM(t.gross_profit) AS gross_profit
            FROM transactions t
            JOIN stores s ON t.store_id = s.store_id
            GROUP BY t.store_id, s.store_name, s.city, s.region, s.tier
        ),
        totals AS (SELECT SUM(revenue) AS grand_total FROM store_rev),
        ranked AS (
            SELECT *,
                   ROUND(revenue * 100.0 / (SELECT grand_total FROM totals), 2) AS rev_share_pct,
                   SUM(revenue) OVER (ORDER BY revenue DESC) AS running_total,
                   ROUND(SUM(revenue) OVER (ORDER BY revenue DESC) * 100.0 /
                         (SELECT grand_total FROM totals), 2)                   AS cumulative_pct
            FROM store_rev
        )
        SELECT *,
               CASE
                   WHEN cumulative_pct <= 80 THEN 'A — Top 80%'
                   WHEN cumulative_pct <= 95 THEN 'B — Next 15%'
                   ELSE                           'C — Bottom 5%'
               END AS store_class
        FROM ranked
        ORDER BY revenue DESC
    """, conn)

    # ── Q3: 30-Day Rolling Stockout Trend (self-join simulation) ──────────────
    results["monthly_stockout"] = pd.read_sql("""
        SELECT
            SUBSTR(date, 1, 7)                              AS month,
            SUM(is_stockout)                                AS stockout_count,
            COUNT(*)                                        AS total_events,
            ROUND(SUM(is_stockout)*100.0/COUNT(*), 2)       AS stockout_rate,
            ROUND(SUM(lost_revenue), 0)                     AS monthly_lost_revenue,
            ROUND(SUM(revenue), 0)                          AS monthly_revenue
        FROM transactions
        GROUP BY SUBSTR(date, 1, 7)
        ORDER BY month
    """, conn)

    # ── Q4: Cross-category Basket Intelligence ────────────────────────────────
    results["category_day_heatmap"] = pd.read_sql("""
        SELECT
            category,
            CASE CAST(strftime('%w', date) AS INTEGER)
                WHEN 0 THEN 'Sunday'    WHEN 1 THEN 'Monday'
                WHEN 2 THEN 'Tuesday'   WHEN 3 THEN 'Wednesday'
                WHEN 4 THEN 'Thursday'  WHEN 5 THEN 'Friday'
                WHEN 6 THEN 'Saturday'
            END AS weekday,
            ROUND(AVG(revenue), 2)    AS avg_daily_revenue,
            ROUND(AVG(is_stockout)*100, 2) AS stockout_rate
        FROM transactions
        GROUP BY category, strftime('%w', date)
        ORDER BY category, CAST(strftime('%w', date) AS INTEGER)
    """, conn)

    # ── Q5: High-Value SKUs with Chronic Stockout Problem ────────────────────
    results["chronic_stockouts"] = pd.read_sql("""
        WITH sku_stats AS (
            SELECT
                t.sku_id,
                p.product_name,
                p.category,
                p.abc_class,
                p.unit_price,
                ROUND(SUM(t.revenue), 0)       AS revenue,
                ROUND(SUM(t.lost_revenue), 0)  AS lost_revenue,
                ROUND(SUM(t.is_stockout)*100.0/COUNT(*), 2) AS stockout_rate,
                COUNT(DISTINCT t.store_id)     AS stores_affected
            FROM transactions t
            JOIN products p ON t.sku_id = p.sku_id
            GROUP BY t.sku_id, p.product_name, p.category, p.abc_class, p.unit_price
            HAVING stockout_rate > 8
        )
        SELECT *,
               ROUND(lost_revenue * 100.0 / (revenue + lost_revenue), 2) AS loss_pct,
               RANK() OVER (ORDER BY lost_revenue DESC)                   AS priority_rank
        FROM sku_stats
        WHERE abc_class IN ('A','B')
        ORDER BY lost_revenue DESC
        LIMIT 25
    """, conn)

    # ── Q6: Region × Tier Revenue Matrix ─────────────────────────────────────
    results["region_tier_matrix"] = pd.read_sql("""
        SELECT
            s.region,
            s.tier,
            COUNT(DISTINCT s.store_id)          AS store_count,
            ROUND(SUM(t.revenue), 0)            AS total_revenue,
            ROUND(AVG(t.revenue), 2)            AS avg_txn_revenue,
            ROUND(SUM(t.lost_revenue), 0)       AS total_lost,
            ROUND(SUM(t.is_stockout)*100.0/COUNT(*), 2) AS stockout_rate
        FROM transactions t
        JOIN stores s ON t.store_id = s.store_id
        GROUP BY s.region, s.tier
        ORDER BY s.region, total_revenue DESC
    """, conn)

    for key, df in results.items():
        print(f"  ✓ {key}: {len(df)} rows")

    return results
