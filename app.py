"""
Retail Inventory Intelligence Platform
Azure-deployed Streamlit dashboard
Solving the $1.75T global stockout crisis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json, os

st.set_page_config(
    page_title="Retail Intelligence Platform",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
  .main { background: #0A0E1A; }
  .stApp { background: linear-gradient(135deg, #0A0E1A 0%, #0D1525 50%, #0A1020 100%); }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1B2A 0%, #0A1520 100%);
    border-right: 1px solid rgba(0,180,255,0.15);
  }
  [data-testid="stSidebar"] * { color: #CBD5E1 !important; }

  /* KPI Cards */
  .kpi-card {
    background: linear-gradient(135deg, #0F2137 0%, #142740 100%);
    border: 1px solid rgba(0,180,255,0.2);
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 12px 12px 0 0;
  }
  .kpi-card.blue::before  { background: linear-gradient(90deg,#00B4FF,#0062FF); }
  .kpi-card.red::before   { background: linear-gradient(90deg,#FF4444,#FF0080); }
  .kpi-card.amber::before { background: linear-gradient(90deg,#FFB020,#FF6B00); }
  .kpi-card.teal::before  { background: linear-gradient(90deg,#00D4AA,#00B4FF); }

  .kpi-label { font-size:12px; font-weight:600; letter-spacing:1.5px; text-transform:uppercase; color:#64748B; margin-bottom:8px; }
  .kpi-value { font-size:28px; font-weight:700; color:#F1F5F9; line-height:1; margin-bottom:4px; }
  .kpi-sub   { font-size:12px; color:#475569; }

  /* Section headers */
  .section-header {
    font-size: 11px; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: #00B4FF;
    border-bottom: 1px solid rgba(0,180,255,0.2);
    padding-bottom: 8px; margin: 24px 0 16px;
  }

  /* Alert banner */
  .alert-banner {
    background: linear-gradient(135deg,rgba(255,68,68,0.12),rgba(255,68,68,0.06));
    border: 1px solid rgba(255,68,68,0.3);
    border-left: 4px solid #FF4444;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 16px;
    color: #FCA5A5;
    font-size: 13px;
  }
  .alert-banner strong { color: #FF4444; }

  /* Tag badges */
  .badge { display:inline-block; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:600; }
  .badge-A { background:rgba(255,68,68,0.15); color:#FF8080; border:1px solid rgba(255,68,68,0.3); }
  .badge-B { background:rgba(255,176,32,0.15); color:#FFB020; border:1px solid rgba(255,176,32,0.3); }
  .badge-C { background:rgba(100,116,139,0.15); color:#94A3B8; border:1px solid rgba(100,116,139,0.3); }

  /* Hide Streamlit default elements */
  #MainMenu {visibility: hidden;}
  footer {visibility: hidden;}
  header {visibility: hidden;}

  div[data-testid="metric-container"] {
    background: #0F2137;
    border: 1px solid rgba(0,180,255,0.15);
    border-radius: 10px;
    padding: 12px;
  }

  /* Plotly bg override */
  .js-plotly-plot .plotly .modebar { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,33,55,0.5)",
    font=dict(family="DM Sans", color="#CBD5E1", size=12),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)"),
    margin=dict(l=10, r=10, t=30, b=10),
)

BASE_LEGEND = dict(
    bgcolor="rgba(0,0,0,0)",
    bordercolor="rgba(255,255,255,0.1)"
)
COLORS = {
    "blue":   "#00B4FF", "teal": "#00D4AA", "amber": "#FFB020",
    "red":    "#FF4444", "purple": "#A855F7", "green": "#22C55E",
    "slate":  "#475569",
}
CAT_PALETTE = ["#00B4FF","#00D4AA","#FFB020","#FF4444","#A855F7","#22C55E","#FB923C"]

@st.cache_data(ttl=3600)
def load_data():
    base = os.path.dirname(os.path.abspath(__file__))
    cache_path = os.path.join(base, "outputs", "analytics_cache.json")
    if not os.path.exists(cache_path):
        cache_path = os.path.join(base, "analytics_cache.json")
    with open(cache_path) as f:
        return json.load(f)

data = load_data()
kpis   = data["kpis"]
monthly = pd.DataFrame(data["monthly_trend"])
cat_df  = pd.DataFrame(data["category_performance"])
store_df = pd.DataFrame(data["store_performance"])
regional = pd.DataFrame(data["regional"])
weekday  = pd.DataFrame(data["weekday_analysis"])
inv_risk = pd.DataFrame(data["inventory_risk"])
recovery = pd.DataFrame(data["revenue_recovery"])
stockout_df = pd.DataFrame(data["monthly_stockout"])
chronic  = pd.DataFrame(data["chronic_stockouts"])
forecast = data["demand_forecast"]

with st.sidebar:
    st.markdown("## Retail Intel")
    st.markdown("---")

    page = st.radio("Navigation", [
        "Executive Overview",
        "Category Deep Dive",
        "Store Performance",
        "Stockout Risk",
        "Revenue Recovery",
        "Demand Forecast",
    ])

    st.markdown("---")
    st.markdown("**Dataset**")
    st.caption(f"Jan 2023 – Jun 2024")
    st.caption(f"12 stores · 70 SKUs")
    st.caption(f"{kpis['total_transactions']:,} transactions")

    st.markdown("---")
    st.markdown(f"""
    <div style="background:rgba(255,68,68,0.1);border:1px solid rgba(255,68,68,0.3);
         border-radius:8px;padding:12px;margin-top:8px;">
      <div style="font-size:11px;color:#FF4444;font-weight:700;letter-spacing:1px;
           text-transform:uppercase;margin-bottom:6px;">⚠ LIVE ALERT</div>
      <div style="font-size:12px;color:#FCA5A5;line-height:1.5;">
        9.1% of potential revenue lost to stockouts this period
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:10px;color:#334155;text-align:center;line-height:1.8;">
      Powered by <b style="color:#00B4FF;">Azure App Service</b><br>
      Data: SQLite → Azure SQL<br>
      BI: Power BI Embedded<br>
      CI/CD: GitHub Actions
    </div>
    """, unsafe_allow_html=True)

if page == "Executive Overview":
    st.markdown("""
    <h1 style="color:#F1F5F9;font-weight:700;font-size:32px;margin-bottom:4px;">
      Retail Inventory Intelligence
    </h1>
    <p style="color:#64748B;font-size:14px;margin-bottom:24px;">
      Solving the $1.75T global stockout crisis — real-time inventory analytics platform
    </p>
    """, unsafe_allow_html=True)

    lost_pct = kpis['lost_revenue_pct']
    st.markdown(f"""
    <div class="alert-banner">
      <strong>CRITICAL:</strong> ₹{kpis['total_lost_revenue']/1e6:.1f}M in revenue was lost to stockouts
      ({lost_pct}% of total demand). Fixing the top 10 SKUs could recover ₹{kpis['total_lost_revenue']*0.4/1e6:.0f}M+ annually.
    </div>
    """, unsafe_allow_html=True)

    
    c1, c2, c3, c4 = st.columns(4)
    def kpi_card(col, label, value, sub, color):
        col.markdown(f"""
        <div class="kpi-card {color}">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

    kpi_card(c1, "Total Revenue",    f"₹{kpis['total_revenue']/1e9:.2f}B", "Jan 2023 – Jun 2024", "blue")
    kpi_card(c2, "Revenue Lost",     f"₹{kpis['total_lost_revenue']/1e6:.0f}M", "Due to stockouts", "red")
    kpi_card(c3, "Gross Profit",     f"₹{kpis['total_gross_profit']/1e9:.2f}B", f"Avg {kpis['avg_discount']}% discount applied", "teal")
    kpi_card(c4, "Stockout Rate",    f"{kpis['stockout_rate']}%", f"{kpis['total_units_lost']:,} units never sold", "amber")

    st.markdown("<br>", unsafe_allow_html=True)

   
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown('<div class="section-header">Monthly Revenue vs Lost Revenue</div>', unsafe_allow_html=True)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(
            x=monthly["month"], y=monthly["revenue"]/1e6,
            name="Revenue (₹M)", marker_color=COLORS["blue"], opacity=0.9,
        ), secondary_y=False)
        fig.add_trace(go.Bar(
            x=monthly["month"], y=monthly["lost_revenue"]/1e6,
            name="Lost Revenue (₹M)", marker_color=COLORS["red"], opacity=0.85,
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            x=monthly["month"], y=monthly["stockout_rate"],
            name="Stockout %", line=dict(color=COLORS["amber"], width=2.5, dash="dot"),
            mode="lines+markers", marker=dict(size=5),
        ), secondary_y=True)
        fig.update_layout(**PLOTLY_THEME, barmode="group", height=340,
                          legend=dict(orientation="h", y=1.1))
        fig.update_yaxes(title_text="₹ Million", secondary_y=False, gridcolor="rgba(255,255,255,0.05)")
        fig.update_yaxes(title_text="Stockout %", secondary_y=True, gridcolor="rgba(255,255,255,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-header">Revenue by Region</div>', unsafe_allow_html=True)
        fig2 = go.Figure(go.Pie(
            labels=regional["region"],
            values=regional["revenue"],
            hole=0.6,
            marker=dict(colors=CAT_PALETTE, line=dict(color="#0A0E1A", width=2)),
            textinfo="label+percent",
            textfont=dict(size=11, color="#CBD5E1"),
        ))
        fig2.update_layout(**PLOTLY_THEME, height=290,
                           annotations=[dict(text=f"₹{sum(regional['revenue'])/1e9:.1f}B",
                                             showarrow=False, font=dict(size=18, color="#F1F5F9"))])
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<div class="section-header">Key Ratios</div>', unsafe_allow_html=True)
        ratios = [
            ("Recovery Opportunity", f"₹{kpis['total_lost_revenue']/1e6:.0f}M"),
            ("Avg Daily Revenue",    f"₹{kpis['avg_daily_revenue']/1e6:.1f}M"),
            ("Units Lost",           f"{kpis['total_units_lost']:,}"),
            ("Avg Discount",         f"{kpis['avg_discount']}%"),
        ]
        for label, val in ratios:
            c_l, c_r = st.columns([2,1])
            c_l.caption(label)
            c_r.markdown(f"**{val}**")

    
    st.markdown('<div class="section-header">Month-over-Month Revenue Growth</div>', unsafe_allow_html=True)
    monthly_clean = monthly.dropna(subset=["mom_growth"])
    colors_mom = [COLORS["teal"] if v >= 0 else COLORS["red"] for v in monthly_clean["mom_growth"]]
    fig3 = go.Figure(go.Bar(
        x=monthly_clean["month"], y=monthly_clean["mom_growth"].round(1),
        marker_color=colors_mom,
        text=monthly_clean["mom_growth"].round(1).astype(str) + "%",
        textposition="outside", textfont=dict(size=10, color="#CBD5E1"),
    ))
    fig3.update_layout(**PLOTLY_THEME, height=220,
                       yaxis_title="MoM Growth %",
                       shapes=[dict(type="line", y0=0, y1=0, x0=0, x1=1,
                                    xref="paper", yref="y",
                                    line=dict(color="#475569", width=1, dash="dash"))])
    st.plotly_chart(fig3, use_container_width=True)


elif page == "Category Deep Dive":
    st.markdown('<h2 style="color:#F1F5F9;font-weight:700;">Category Performance Analysis</h2>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Revenue vs Loss by Category</div>', unsafe_allow_html=True)
        fig = px.scatter(cat_df,
            x="revenue", y="lost_revenue",
            size="units_sold", color="category",
            text="category", color_discrete_sequence=CAT_PALETTE,
            hover_data={"stockout_rate": True, "avg_margin": ":.2f"},
            size_max=45,
        )
        fig.update_traces(textposition="top center", textfont=dict(size=9, color="#CBD5E1"))
        fig.update_layout(**PLOTLY_THEME, height=360,
                          xaxis_title="Revenue (₹)", yaxis_title="Lost Revenue (₹)",
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Gross Margin by Category</div>', unsafe_allow_html=True)
        cat_sorted = cat_df.sort_values("avg_margin", ascending=True)
        fig2 = go.Figure(go.Bar(
            x=cat_sorted["avg_margin"] * 100,
            y=cat_sorted["category"],
            orientation="h",
            marker=dict(
                color=cat_sorted["avg_margin"] * 100,
                colorscale=[[0,"#FF4444"],[0.5,"#FFB020"],[1,"#00D4AA"]],
                showscale=True,
                colorbar=dict(title="Margin %", tickfont=dict(color="#64748B")),
            ),
            text=(cat_sorted["avg_margin"]*100).round(1).astype(str)+"%",
            textposition="inside", textfont=dict(color="white", size=11),
        ))
        fig2.update_layout(**PLOTLY_THEME, height=360, xaxis_title="Gross Margin %")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-header">Category Scorecard</div>', unsafe_allow_html=True)
    display = cat_df[["category","revenue","lost_revenue","gross_profit","stockout_rate","lost_rev_pct","avg_margin"]].copy()
    display["revenue"]       = display["revenue"].apply(lambda x: f"₹{x/1e6:.1f}M")
    display["lost_revenue"]  = display["lost_revenue"].apply(lambda x: f"₹{x/1e6:.1f}M")
    display["gross_profit"]  = display["gross_profit"].apply(lambda x: f"₹{x/1e6:.1f}M")
    display["avg_margin"]    = (display["avg_margin"]*100).round(1).astype(str) + "%"
    display["stockout_rate"] = display["stockout_rate"].astype(str) + "%"
    display["lost_rev_pct"]  = display["lost_rev_pct"].astype(str) + "%"
    display.columns = ["Category","Revenue","Lost Revenue","Gross Profit","Stockout %","Loss %","Margin %"]
    st.dataframe(display.set_index("Category"), use_container_width=True)

    # Weekday heatmap
    st.markdown('<div class="section-header">Sales by Day of Week</div>', unsafe_allow_html=True)
    fig3 = px.bar(weekday, x="weekday", y="avg_daily_revenue",
                  color="avg_daily_revenue",
                  color_continuous_scale=[[0,"#0F2137"],[0.5,"#00B4FF"],[1,"#00D4AA"]],
                  text=weekday["avg_daily_revenue"].apply(lambda x: f"₹{x/1e6:.1f}M"))
    fig3.update_traces(textposition="outside", textfont=dict(color="#CBD5E1", size=10))
    fig3.update_layout(**PLOTLY_THEME, height=260,
                       yaxis_title="Avg Daily Revenue (₹)",
                       coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — STORE PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Store Performance":
    st.markdown('<h2 style="color:#F1F5F9;font-weight:700;">Store Performance Leaderboard</h2>', unsafe_allow_html=True)

    tier_filter = st.multiselect("Filter by Tier", ["Premium","Standard","Discount"],
                                 default=["Premium","Standard","Discount"])
    store_filtered = store_df[store_df["tier"].isin(tier_filter)]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Revenue by Store</div>', unsafe_allow_html=True)
        fig = px.bar(store_filtered.sort_values("revenue"),
                     x="revenue", y="store_name", orientation="h",
                     color="tier",
                     color_discrete_map={"Premium":COLORS["blue"],"Standard":COLORS["teal"],"Discount":COLORS["amber"]},
                     text=store_filtered.sort_values("revenue")["revenue"].apply(lambda x: f"₹{x/1e6:.0f}M"))
        fig.update_traces(textposition="outside", textfont=dict(color="#CBD5E1", size=9))
        fig.update_layout(**PLOTLY_THEME, height=420, xaxis_title="Revenue (₹)",
                          legend={**BASE_LEGEND, "orientation": "h", "y": 1.1})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Stockout Rate by Store</div>', unsafe_allow_html=True)
        fig2 = px.scatter(store_filtered,
                          x="revenue", y="stockout_rate",
                          size="lost_revenue", color="tier",
                          text="city",
                          color_discrete_map={"Premium":COLORS["blue"],"Standard":COLORS["teal"],"Discount":COLORS["amber"]},
                          size_max=40, hover_data=["store_name","target_attainment"])
        fig2.update_traces(textposition="top center", textfont=dict(size=9, color="#CBD5E1"))
        fig2.update_layout(**PLOTLY_THEME, height=420,
                           xaxis_title="Revenue (₹)", yaxis_title="Stockout %")
        st.plotly_chart(fig2, use_container_width=True)

    # Target attainment
    st.markdown('<div class="section-header">Target Attainment vs Revenue</div>', unsafe_allow_html=True)
    cols = st.columns(len(store_filtered))
    for i, (_, row) in enumerate(store_filtered.iterrows()):
        att = row["target_attainment"]
        color = "🟢" if att >= 100 else "🟡" if att >= 80 else "🔴"
        cols[i % len(cols)].metric(
            label=row["city"],
            value=f"{att:.0f}%",
            delta=f"{att-100:.0f}% vs target"
        )


elif page == "Stockout Risk":
    st.markdown('<h2 style="color:#F1F5F9;font-weight:700;"> Stockout Risk Intelligence</h2>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.markdown(f"""<div class="kpi-card red">
      <div class="kpi-label">Total Lost (Period)</div>
      <div class="kpi-value">₹{kpis['total_lost_revenue']/1e6:.0f}M</div>
      <div class="kpi-sub">623M units of demand unmet</div></div>""", unsafe_allow_html=True)
    col2.markdown(f"""<div class="kpi-card amber">
      <div class="kpi-label">Stockout Rate</div>
      <div class="kpi-value">{kpis['stockout_rate']}%</div>
      <div class="kpi-sub">of all demand events</div></div>""", unsafe_allow_html=True)
    col3.markdown(f"""<div class="kpi-card blue">
      <div class="kpi-label">Recovery Potential</div>
      <div class="kpi-value">₹{kpis['total_lost_revenue']*0.6/1e6:.0f}M</div>
      <div class="kpi-sub">with optimal reorder logic</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Stockout Rate Trend</div>', unsafe_allow_html=True)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(
            x=stockout_df["month"], y=stockout_df["stockout_rate"],
            name="Stockout %", fill="tozeroy",
            fillcolor="rgba(255,68,68,0.1)", line=dict(color=COLORS["red"], width=2),
        ), secondary_y=False)
        fig.add_trace(go.Bar(
            x=stockout_df["month"], y=stockout_df["monthly_lost_revenue"]/1e6,
            name="Lost ₹M", marker_color=COLORS["amber"], opacity=0.6,
        ), secondary_y=True)
        fig.update_layout(**PLOTLY_THEME, height=300, legend={**BASE_LEGEND, "orientation": "h", "y": 1.1})
        fig.update_yaxes(title_text="Stockout %", secondary_y=False)
        fig.update_yaxes(title_text="Lost Revenue ₹M", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Loss % by Category</div>', unsafe_allow_html=True)
        fig2 = px.funnel(
            recovery.sort_values("lost_revenue", ascending=False),
            x="lost_revenue", y="category",
            color_discrete_sequence=[COLORS["red"]]
        )
        fig2.update_layout(**PLOTLY_THEME, height=300)
        st.plotly_chart(fig2, use_container_width=True)

    # Chronic stockouts table
    st.markdown('<div class="section-header">Chronic Stockout SKUs (Priority Action Required)</div>', unsafe_allow_html=True)
    if not chronic.empty:
        display_cols = ["priority_rank","product_name","category","abc_class",
                        "unit_price","revenue","lost_revenue","stockout_rate","stores_affected"]
        avail = [c for c in display_cols if c in chronic.columns]
        tbl = chronic[avail].head(20).copy()
        if "revenue" in tbl.columns: tbl["revenue"] = tbl["revenue"].apply(lambda x: f"₹{x/1e6:.1f}M")
        if "lost_revenue" in tbl.columns: tbl["lost_revenue"] = tbl["lost_revenue"].apply(lambda x: f"₹{x/1e6:.1f}M")
        if "unit_price" in tbl.columns: tbl["unit_price"] = tbl["unit_price"].apply(lambda x: f"₹{x:,.0f}")
        if "stockout_rate" in tbl.columns: tbl["stockout_rate"] = tbl["stockout_rate"].astype(str) + "%"
        tbl.columns = [c.replace("_"," ").title() for c in tbl.columns]
        st.dataframe(tbl, use_container_width=True)
    else:
        st.info("No chronic stockouts detected above threshold.")


elif page == "💡 Revenue Recovery":
    st.markdown('<h2 style="color:#F1F5F9;font-weight:700;">💡 Revenue Recovery Playbook</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748B;">SQL-powered opportunity analysis: where to fix inventory first to maximise recovery.</p>', unsafe_allow_html=True)

    # Waterfall
    st.markdown('<div class="section-header">Revenue Recovery Waterfall by Category</div>', unsafe_allow_html=True)
    rec_sorted = recovery.sort_values("lost_revenue", ascending=False)
    cumulative = [0]
    for v in rec_sorted["lost_revenue"][:-1]:
        cumulative.append(cumulative[-1] + v)

    fig = go.Figure(go.Waterfall(
        x=rec_sorted["category"],
        y=rec_sorted["lost_revenue"]/1e6,
        measure=["relative"]*len(rec_sorted),
        text=(rec_sorted["lost_revenue"]/1e6).round(1).astype(str)+"M",
        textposition="outside",
        connector=dict(line=dict(color="rgba(255,255,255,0.2)", width=1, dash="dot")),
        increasing=dict(marker=dict(color=COLORS["red"])),
        decreasing=dict(marker=dict(color=COLORS["teal"])),
    ))
    fig.update_layout(**PLOTLY_THEME, height=360, yaxis_title="Lost Revenue (₹M)")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Stockout Rate vs Loss %</div>', unsafe_allow_html=True)
        fig2 = px.scatter(recovery,
            x="stockout_rate", y="loss_pct",
            size="lost_revenue", text="category",
            color="loss_rank", color_continuous_scale="Reds_r",
            size_max=50)
        fig2.update_traces(textposition="top center", textfont=dict(size=10, color="#CBD5E1"))
        fig2.update_layout(**PLOTLY_THEME, height=340,
                           xaxis_title="Stockout Rate %", yaxis_title="Revenue Loss %",
                           coloraxis_showscale=False)
        # Add quadrant lines
        fig2.add_hline(y=recovery["loss_pct"].mean(), line_dash="dot",
                       line_color="rgba(255,255,255,0.2)", annotation_text="Avg Loss %")
        fig2.add_vline(x=recovery["stockout_rate"].mean(), line_dash="dot",
                       line_color="rgba(255,255,255,0.2)", annotation_text="Avg Stockout %")
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Recovery Priority Matrix</div>', unsafe_allow_html=True)
        # Priority score = lost_revenue / potential_revenue * loss_rank
        recovery["priority"] = (recovery["lost_revenue"] / recovery["potential_revenue"] * 100).round(1)
        fig3 = px.bar(recovery.sort_values("priority", ascending=True),
                      x="priority", y="category", orientation="h",
                      color="priority",
                      color_continuous_scale=[[0,"#00D4AA"],[0.5,"#FFB020"],[1,"#FF4444"]],
                      text=recovery.sort_values("priority", ascending=True)["priority"].astype(str)+"%")
        fig3.update_traces(textposition="outside", textfont=dict(color="#CBD5E1", size=10))
        fig3.update_layout(**PLOTLY_THEME, height=340,
                           xaxis_title="Revenue at Risk %", coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    # Action table
    st.markdown('<div class="section-header">Recommended Actions</div>', unsafe_allow_html=True)
    action_tbl = recovery[["category","potential_revenue","actual_revenue","lost_revenue","loss_pct","stockout_rate"]].copy()
    action_tbl["potential_revenue"] = action_tbl["potential_revenue"].apply(lambda x: f"₹{x/1e6:.1f}M")
    action_tbl["actual_revenue"]    = action_tbl["actual_revenue"].apply(lambda x: f"₹{x/1e6:.1f}M")
    action_tbl["lost_revenue"]      = action_tbl["lost_revenue"].apply(lambda x: f"₹{x/1e6:.1f}M")
    action_tbl["loss_pct"]          = action_tbl["loss_pct"].astype(str) + "%"
    action_tbl["stockout_rate"]     = action_tbl["stockout_rate"].astype(str) + "%"
    action_tbl.columns = ["Category","Potential Revenue","Actual Revenue","Lost Revenue","Loss %","Stockout %"]
    st.dataframe(action_tbl.set_index("Category"), use_container_width=True)

elif page == "Demand Forecast":
    st.markdown('<h2 style="color:#F1F5F9;font-weight:700;"> Demand Forecast Engine</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748B;">Linear trend + seasonality decomposition. Feeds automated reorder system.</p>', unsafe_allow_html=True)

    fc = forecast
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"""<div class="kpi-card blue">
      <div class="kpi-label">Trend Direction</div>
      <div class="kpi-value" style="font-size:22px;">{fc['trend'].title()}</div>
      <div class="kpi-sub">Slope: +{fc['slope']:,.0f} units/month</div></div>""", unsafe_allow_html=True)
    col2.markdown(f"""<div class="kpi-card teal">
      <div class="kpi-label">Model R²</div>
      <div class="kpi-value">{fc['r_squared']:.3f}</div>
      <div class="kpi-sub">Linear fit quality</div></div>""", unsafe_allow_html=True)
    col3.markdown(f"""<div class="kpi-card amber">
      <div class="kpi-label">Next 3 Months Forecast</div>
      <div class="kpi-value" style="font-size:18px;">{fc['forecast_next_3'][0]:,}</div>
      <div class="kpi-sub">{fc['forecast_next_3'][1]:,} · {fc['forecast_next_3'][2]:,} units</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Historical + forecast
    st.markdown('<div class="section-header">Historical Demand + 3-Month Forecast</div>', unsafe_allow_html=True)
    hist_demand = pd.DataFrame(data["monthly_stockout"])[["month","stockout_count","monthly_revenue"]]

    # Forecast months
    last_month = hist_demand["month"].iloc[-1]
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    try:
        last_dt = datetime.strptime(last_month, "%Y-%m")
        future_months = [(last_dt + relativedelta(months=i)).strftime("%Y-%m") for i in range(1,4)]
    except:
        future_months = ["2024-07","2024-08","2024-09"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist_demand["month"], y=hist_demand["monthly_revenue"]/1e6,
        name="Actual Revenue ₹M",
        line=dict(color=COLORS["blue"], width=2.5),
        fill="tozeroy", fillcolor="rgba(0,180,255,0.08)",
    ))
    # Forecast
    forecast_revs = [m * 280 / 1e6 for m in fc["forecast_next_3"]]  # rough proxy
    last_actual = hist_demand["monthly_revenue"].iloc[-1] / 1e6
    fig.add_trace(go.Scatter(
        x=[hist_demand["month"].iloc[-1]] + future_months,
        y=[last_actual] + forecast_revs,
        name="Forecast",
        line=dict(color=COLORS["amber"], width=2.5, dash="dash"),
        mode="lines+markers",
        marker=dict(size=8, symbol="diamond"),
    ))
    fig.add_vrect(x0=hist_demand["month"].iloc[-1], x1=future_months[-1],
                  fillcolor="rgba(255,176,32,0.06)",
                  line=dict(color="rgba(255,176,32,0.3)", dash="dot"),
                  annotation_text="Forecast Zone", annotation_position="top left",
                  annotation_font=dict(color=COLORS["amber"], size=11))
    fig.update_layout(**PLOTLY_THEME, height=380,
                      yaxis_title="Revenue (₹M)",
                      legend={**BASE_LEGEND, "orientation": "h", "y": 1.1})
    st.plotly_chart(fig, use_container_width=True)

    # Inventory risk
    st.markdown('<div class="section-header">Inventory Risk Matrix (Latest Snapshot)</div>', unsafe_allow_html=True)
    risk_display = inv_risk[["product_name","category","abc_class","avg_stock","stores_at_risk","priority_score"]].head(20).copy()
    risk_display["avg_stock"] = risk_display["avg_stock"].round(0).astype(int)
    risk_display["priority_score"] = risk_display["priority_score"].round(1)
    risk_display.columns = ["Product","Category","ABC Class","Avg Stock","Stores at Risk","Priority Score"]
    st.dataframe(risk_display.set_index("Product"), use_container_width=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;">
  <span style="color:#334155;font-size:11px;">
    Retail Inventory Intelligence Platform · Built with Python, Pandas, SQL, Azure, Power BI
  </span>
  <span style="color:#334155;font-size:11px;">
    Data: Jan 2023–Jun 2024 · 428K transactions · SQLite → Azure SQL
  </span>
</div>
""", unsafe_allow_html=True)
