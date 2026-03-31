# Power BI — Retail Intelligence Data Model

## Architecture

```
Azure SQL Database (source)
        │
        ├── fact_sales          ← 428K rows, denormalized transaction fact table
        ├── dim_products        ← 70 SKUs with category, margin, ABC class
        ├── dim_stores          ← 12 stores with region, tier, targets
        ├── dim_date            ← Full date dimension with fiscal/calendar fields
        ├── dim_inventory       ← Weekly inventory snapshots
        └── kpi_summary         ← Pre-aggregated KPI table
```

## Star Schema (Power BI Relationships)

```
                 dim_date
                    │
                    │ date → date
                    │
dim_products ── fact_sales ── dim_stores
  sku_id → sku_id     store_id → store_id
                    │
                    │ sku_id → sku_id
                    │
              dim_inventory
```

All relationships are **Many-to-One**, **Single Direction** (fact → dim).

---

## Connecting Power BI to Azure SQL

### Option A: Direct Query (live, always fresh)
1. Power BI Desktop → **Get Data → Azure → Azure SQL Database**
2. Server: `retail-intel-sql.database.windows.net`
3. Database: `retaildb`
4. Data Connectivity mode: **DirectQuery**
5. Authentication: **Database** (use credentials from Key Vault)

### Option B: Import Mode (faster, scheduled refresh)
- Same as above but select **Import**
- Set up scheduled refresh (daily) in Power BI Service
- Recommended for report performance

### Option C: Azure Blob CSV (local Power BI, no SQL)
1. Power BI Desktop → **Get Data → Azure → Azure Blob Storage**
2. Container: `powerbi-data`
3. Load all CSV files: fact_sales, dim_products, dim_stores, dim_date, dim_inventory
4. Create relationships manually in Model view

---

## DAX Measures Setup

1. In Power BI Desktop, go to **Modeling → New Table**
2. Create: `_Measures = DATATABLE("Placeholder", STRING, {{""}})`
3. Right-click `_Measures` → **New Measure**
4. Paste each measure from `powerbi/dax_measures.dax`

---

## Recommended Report Pages

### Page 1 — Executive Overview
| Visual | Type | Fields |
|--------|------|--------|
| Total Revenue | KPI Card | `[Total Revenue]` |
| Lost Revenue | KPI Card | `[Lost Revenue]` |
| Stockout Rate | KPI Card | `[Stockout Rate %]` |
| Revenue Trend | Line Chart | dim_date[month_name] → `[Total Revenue]`, `[Lost Revenue]` |
| Revenue by Region | Donut | dim_stores[region] → `[Total Revenue]` |
| MoM Growth | Bar | dim_date[month_name] → `[Revenue MoM Growth %]` |

### Page 2 — Stockout Risk
| Visual | Type | Fields |
|--------|------|--------|
| Category × Tier Matrix | Matrix | category, tier → `[Stockout Rate %]` |
| Revenue vs Loss Scatter | Scatter | `[Total Revenue]` × `[Lost Revenue %]`, size=`[Units Lost]` |
| Top Loss SKUs | Table | product_name, category, abc_class, `[Lost Revenue]`, `[Stockout Rate %]` |
| Weekday Heatmap | Matrix | weekday → category → `[Stockout Rate %]` |

### Page 3 — Store Leaderboard  
| Visual | Type | Fields |
|--------|------|--------|
| Revenue Rank | Bar (H) | store_name → `[Total Revenue]` |
| Target Attainment | Gauge | `[Target Attainment %]` |
| Revenue Map | Azure Map | city → `[Total Revenue]` |
| Store Scorecard | Table | All store KPIs with conditional formatting |

### Page 4 — Inventory Risk
| Visual | Type | Fields |
|--------|------|--------|
| Risk Count | KPI Card | `[Stores at Stockout Risk]` |
| Overstock Count | KPI Card | `[Stores Overstocked]` |
| Inventory Value | KPI Card | `[Total Inventory Value]` |
| Risk Matrix | Matrix | sku_id → store_id → `is_stockout_risk` |

### Page 5 — Revenue Recovery Roadmap
| Visual | Type | Fields |
|--------|------|--------|
| Annualized Lost Revenue | KPI Card | `[Implied Annual Lost Revenue]` |
| Recovery if Fixed | KPI Card | `[ROI of Fixing Stockouts]` |
| Loss by Category | Funnel | category → `[Lost Revenue]` |
| ABC Table | Table | abc_class, `[Total Revenue]`, `[ABC Revenue Share %]`, `[ABC Category]` |

---

## Power BI Service — Publishing & Sharing

```bash
# After building report in Desktop:
1. File → Publish → Publish to Power BI
2. Select workspace: "Retail Intelligence"
3. In Power BI Service → Settings → Scheduled Refresh → Daily at 6 AM
4. Share with stakeholders via workspace access
5. Embed in Streamlit using Power BI Embedded (see below)
```

## Power BI Embedded in Streamlit

```python
# In app.py — embed Power BI report
POWER_BI_EMBED_URL = "https://app.powerbi.com/reportEmbed?reportId={report_id}&groupId={workspace_id}"

st.components.v1.iframe(
    src=POWER_BI_EMBED_URL,
    height=600,
    scrolling=False
)
```

Add to GitHub Secrets:
- `POWER_BI_WORKSPACE_ID`
- `POWER_BI_REPORT_ID`
- `POWER_BI_ACCESS_TOKEN` (service principal)
