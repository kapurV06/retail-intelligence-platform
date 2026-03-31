"""
Real-World Problem: Retail Stockout & Overstock Crisis
$1.75 TRILLION is lost annually by retailers due to inventory mismanagement.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime
import os

np.random.seed(42)
random.seed(42)

print("🔧 Generating retail supply chain data...")

CATEGORIES = {
    "Electronics":   {"margin": 0.28, "lead_days": 14, "seasonality": [1.0,0.9,0.9,1.0,1.1,1.0,1.0,1.1,1.2,1.3,1.6,2.0]},
    "Clothing":      {"margin": 0.55, "lead_days": 21, "seasonality": [0.8,0.7,1.1,1.2,1.1,1.3,1.4,1.2,1.1,0.9,1.2,1.4]},
    "Grocery":       {"margin": 0.18, "lead_days": 3,  "seasonality": [1.0,1.0,1.0,1.0,1.1,1.2,1.2,1.2,1.1,1.0,1.1,1.3]},
    "Home & Garden": {"margin": 0.42, "lead_days": 10, "seasonality": [0.6,0.7,1.1,1.5,1.8,1.9,1.8,1.6,1.2,0.9,0.8,0.7]},
    "Sports":        {"margin": 0.38, "lead_days": 7,  "seasonality": [0.9,0.9,1.1,1.3,1.5,1.7,1.7,1.5,1.2,1.0,0.9,0.8]},
    "Beauty":        {"margin": 0.62, "lead_days": 5,  "seasonality": [1.0,1.2,1.1,1.1,1.2,1.1,1.0,1.0,1.1,1.1,1.3,1.5]},
    "Toys & Games":  {"margin": 0.45, "lead_days": 12, "seasonality": [0.7,0.6,0.7,0.8,0.9,1.0,1.0,0.9,1.0,1.1,1.7,2.5]},
}

product_names = {
    "Electronics":   ["Smart TV 55in","Bluetooth Speaker","Laptop Stand","Wireless Earbuds","USB-C Hub","Webcam HD","Gaming Mouse","Mechanical Keyboard","Monitor 27in","Power Bank"],
    "Clothing":      ["Denim Jacket","Cotton Kurta","Sports Leggings","Formal Shirt","Winter Hoodie","Silk Saree","Running Shoes","Casual Sneakers","Formal Trousers","Summer Dress"],
    "Grocery":       ["Basmati Rice 5kg","Toor Dal 1kg","Cold-Pressed Oil","Organic Tea","Multigrain Atta","Ghee 500ml","Almond Pack","Honey 250ml","Masala Kit","Protein Oats"],
    "Home & Garden": ["Indoor Planter","Bedsheet Set","Kitchen Organizer","Wall Clock","Curtain Pair","Pressure Cooker","Air Purifier","LED Bulb Pack","Bath Towels","Sofa Cover"],
    "Sports":        ["Yoga Mat","Resistance Bands","Cricket Bat","Football","Badminton Set","Jump Rope","Dumbbell Pair","Gym Bag","Protein Shaker","Cycling Gloves"],
    "Beauty":        ["Face Serum","Sunscreen SPF50","Hair Mask","Body Lotion","Kajal","Lipstick Set","Beard Oil","Vitamin C Cream","Under-Eye Gel","Shampoo 400ml"],
    "Toys & Games":  ["LEGO Set","Board Game","Remote Car","Stuffed Bear","Puzzle 1000pc","Chess Set","Dart Board","Frisbee","Kite Set","Card Game"],
}

# ── PRODUCTS ──────────────────────────────────────────────────────────────────
products = []
sku_id = 1000
for cat, meta in CATEGORIES.items():
    for name in product_names[cat]:
        base_price = round(random.uniform(50, 5000), 2)
        cost = round(base_price * (1 - meta["margin"]), 2)
        products.append({
            "sku_id": f"SKU-{sku_id}", "product_name": name, "category": cat,
            "unit_price": base_price, "unit_cost": cost, "gross_margin": meta["margin"],
            "supplier_lead_days": meta["lead_days"] + random.randint(-2, 5),
            "reorder_point": random.randint(20, 100), "reorder_qty": random.randint(100, 500),
            "max_shelf_qty": random.randint(500, 2000),
            "abc_class": random.choices(["A","B","C"], weights=[20,30,50])[0],
        })
        sku_id += 1

df_products = pd.DataFrame(products)
print(f"  ✓ {len(df_products)} products")

# ── STORES ────────────────────────────────────────────────────────────────────
store_data = [
    ("STR-001","Mumbai Premium #1","Mumbai","West","Premium"),
    ("STR-002","Delhi Standard #2","Delhi","North","Standard"),
    ("STR-003","Bangalore Premium #3","Bangalore","South","Premium"),
    ("STR-004","Hyderabad Standard #4","Hyderabad","South","Standard"),
    ("STR-005","Chennai Discount #5","Chennai","South","Discount"),
    ("STR-006","Pune Standard #6","Pune","West","Standard"),
    ("STR-007","Kolkata Discount #7","Kolkata","East","Discount"),
    ("STR-008","Delhi Premium #8","Delhi","North","Premium"),
    ("STR-009","Jaipur Standard #9","Jaipur","North","Standard"),
    ("STR-010","Chandigarh Standard #10","Chandigarh","North","Standard"),
    ("STR-011","Ahmedabad Discount #11","Ahmedabad","West","Discount"),
    ("STR-012","Lucknow Standard #12","Lucknow","Central","Standard"),
]
TIER_MUL = {"Premium":1.3,"Standard":1.0,"Discount":0.75}
stores = []
for sid, sname, city, region, tier in store_data:
    stores.append({
        "store_id": sid, "store_name": sname, "city": city, "region": region, "tier": tier,
        "size_sqft": random.randint(8000, 50000), "opened_year": random.randint(2010, 2022),
        "target_monthly_revenue": random.randint(800_000, 5_000_000),
    })
df_stores = pd.DataFrame(stores)
print(f"  ✓ {len(df_stores)} stores")

# ── TRANSACTIONS (vectorized) ─────────────────────────────────────────────────
print("  ⏳ Simulating transactions (vectorized)...")
dates = pd.date_range("2023-01-01", "2024-06-30", freq="D")

all_txn = []
txn_counter = 100000

for store_row in df_stores.itertuples():
    store_mul = TIER_MUL[store_row.tier]
    for sku_row in df_products.itertuples():
        seas = np.array(CATEGORIES[sku_row.category]["seasonality"])
        months = dates.month.values - 1
        seasonal_factors = seas[months]
        weekday_factors = np.where(dates.dayofweek >= 5, 1.3, 1.0)
        spikes = np.where(np.random.random(len(dates)) < 0.015, 3.0, 1.0)
        base = random.uniform(0.5, 8) * store_mul
        lambdas = base * seasonal_factors * weekday_factors * spikes
        demands = np.random.poisson(lambdas).astype(int)
        mask = demands > 0
        if mask.sum() == 0:
            continue
        active_dates = dates[mask]
        active_demands = demands[mask]
        n = len(active_dates)
        stockouts = np.random.random(n) < 0.09
        discs = np.random.choice([0,0,0,0.05,0.10,0.15,0.20], size=n)
        discs_applied = np.where(np.random.random(n) < 0.12, discs, 0.0)
        sale_prices = np.round(sku_row.unit_price * (1 - discs_applied), 2)
        qty_sold = np.where(stockouts, 0, active_demands)
        revenues = np.round(qty_sold * sale_prices, 2)
        cogs = np.round(qty_sold * sku_row.unit_cost, 2)
        lost_rev = np.round(np.where(stockouts, active_demands * sku_row.unit_price, 0), 2)
        gp = np.round(qty_sold * (sale_prices - sku_row.unit_cost), 2)

        chunk = pd.DataFrame({
            "txn_id": range(txn_counter, txn_counter + n),
            "date": active_dates.strftime("%Y-%m-%d"),
            "store_id": store_row.store_id,
            "sku_id": sku_row.sku_id,
            "category": sku_row.category,
            "qty_demanded": active_demands,
            "qty_sold": qty_sold,
            "is_stockout": stockouts.astype(int),
            "lost_units": np.where(stockouts, active_demands, 0),
            "unit_price": sku_row.unit_price,
            "sale_price": sale_prices,
            "discount_pct": discs_applied,
            "revenue": revenues,
            "cogs": cogs,
            "lost_revenue": lost_rev,
            "gross_profit": gp,
        })
        all_txn.append(chunk)
        txn_counter += n

df_txn = pd.concat(all_txn, ignore_index=True)
print(f"  ✓ {len(df_txn):,} transaction records")

# ── INVENTORY SNAPSHOTS ───────────────────────────────────────────────────────
print("  ⏳ Building inventory snapshots...")
weeks = pd.date_range("2023-01-01", "2024-06-30", freq="2W")
inv_rows = []
for store_row in df_stores.itertuples():
    for sku_row in df_products.itertuples():
        stocks = np.random.randint(0, int(sku_row.max_shelf_qty), size=len(weeks))
        dos = np.round(stocks / np.random.uniform(1, 12, size=len(weeks)), 1)
        for i, wk in enumerate(weeks):
            s = int(stocks[i])
            inv_rows.append({
                "snapshot_date": wk.strftime("%Y-%m-%d"),
                "store_id": store_row.store_id, "sku_id": sku_row.sku_id,
                "stock_level": s, "reorder_point": sku_row.reorder_point,
                "days_of_supply": float(dos[i]),
                "is_below_reorder": int(s < sku_row.reorder_point),
                "is_stockout_risk": int(s < sku_row.reorder_point * 0.5),
                "overstock_flag": int(s > sku_row.max_shelf_qty * 0.9),
                "inventory_value": round(s * sku_row.unit_cost, 2),
            })

df_inventory = pd.DataFrame(inv_rows)
print(f"  ✓ {len(df_inventory):,} inventory snapshots")

os.makedirs("../data", exist_ok=True)
df_products.to_csv("../data/products.csv",   index=False)
df_stores.to_csv("../data/stores.csv",       index=False)
df_txn.to_csv("../data/transactions.csv",    index=False)
df_inventory.to_csv("../data/inventory.csv", index=False)

print(f"\n  💀 Lost revenue: ₹{df_txn['lost_revenue'].sum():,.0f}")
print(f"  📈 Actual revenue: ₹{df_txn['revenue'].sum():,.0f}")
print(f"  📦 Stockout rate: {df_txn['is_stockout'].mean()*100:.1f}%")
print("✅ Data generation complete")
