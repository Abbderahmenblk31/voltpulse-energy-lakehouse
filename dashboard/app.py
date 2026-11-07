"""
VoltPulse - Power Grid Telemetry & Battery Energy Arbitrage Dashboard
=====================================================================
A high-performance energy analytics platform built on DuckDB Lakehouse
and real-time European spot market telemetry. Translates volatile power
grid pricing into actionable battery energy storage (BESS) investment PnL.
"""

import os
import sys
import duckdb
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Page Setup
st.set_page_config(
    page_title="VoltPulse | Power Grid & Battery Arbitrage Lakehouse",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "lakehouse", "energy_lakehouse.duckdb")

@st.cache_data(ttl=60)
def load_energy_data():
    # Auto-initialize database on first run if missing in cloud environment
    if not os.path.exists(DB_PATH):
        import subprocess
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        subprocess.run([sys.executable, os.path.join(BASE_DIR, "ingest_engine", "ingest_grid_data.py")], check=True)
        subprocess.run([sys.executable, os.path.join(BASE_DIR, "models", "arbitrage_analysis.py")], check=True)
        
    con = duckdb.connect(DB_PATH, read_only=True)
    
    hourly_df = con.execute("""
        SELECT 
            timestamp_utc,
            market_date,
            hour_of_day,
            spot_price_eur_mwh,
            is_negative_price,
            solar_mw,
            total_wind_mw,
            gas_mw,
            coal_mw,
            total_renewables_mw,
            total_generation_mw,
            renewable_share_pct,
            market_time_block
        FROM silver_hourly_market
        ORDER BY timestamp_utc;
    """).df()
    
    daily_bess_df = con.execute("""
        SELECT * FROM fct_daily_bess_arbitrage
        ORDER BY market_date ASC;
    """).df()
    
    summary_stats = con.execute("SELECT * FROM mart_energy_executive_summary;").fetchone()
    con.close()
    
    return hourly_df, daily_bess_df, summary_stats

# Header
st.markdown("""
<div style='background-color: #0d1b2a; padding: 22px; border-radius: 12px; margin-bottom: 25px; border-left: 6px solid #f59e0b;'>
    <div style='display: flex; justify-content: space-between; align-items: center;'>
        <div>
            <h1 style='color: #ffffff; margin: 0; font-size: 26px;'>⚡ VoltPulse: National Power Grid & Battery Energy Arbitrage</h1>
            <p style='color: #94a3b8; margin: 6px 0 0 0; font-size: 14px;'>
                Transforming Wholesale Electricity Price Volatility into <b>Industrial BESS Storage Returns</b>
            </p>
        </div>
        <div style='background-color: #1e293b; padding: 10px 18px; border-radius: 8px; border: 1px solid #334155; text-align: right;'>
            <span style='color: #94a3b8; font-size: 12px;'>Data Source:</span> <b style='color: #10b981;'>Fraunhofer ISE / SMARD</b> | 
            <span style='color: #94a3b8; font-size: 12px;'>Engine:</span> <b style='color: #38bdf8;'>DuckDB Lakehouse</b>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

try:
    hourly_df, daily_bess_df, summary = load_energy_data()
except Exception as e:
    st.error(f"Failed to connect to Energy Lakehouse: {e}")
    st.stop()

# Executive Metrics
total_bess_profit = float(summary[1])
avg_daily_profit = float(summary[2])
avg_spread = float(summary[3])
max_spread = float(summary[4])

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        "🔋 Net Battery Arbitrage Profit",
        f"€{total_bess_profit:,.2f}",
        delta=f"€{avg_daily_profit:,.0f} / Day Avg",
        delta_color="normal"
    )
with col2:
    st.metric(
        "📈 Avg Peak-to-Trough Spread",
        f"€{avg_spread:.2f} / MWh",
        delta=f"Max: €{max_spread:.2f}",
        delta_color="normal"
    )
with col3:
    neg_hours = int(hourly_df["is_negative_price"].sum())
    st.metric(
        "⚡ Negative Electricity Hours",
        f"{neg_hours} Hours",
        delta="Surplus Green Energy",
        delta_color="inverse"
    )
with col4:
    avg_renew_pct = round(hourly_df["renewable_share_pct"].mean(), 1)
    st.metric(
        "🌿 Avg Renewable Grid Share",
        f"{avg_renew_pct}%",
        delta="Wind & Solar Penetration"
    )

st.markdown("---")

# Main Analysis Tabs
tab1, tab2, tab3 = st.tabs([
    "📊 Battery Arbitrage Financial Returns (PnL)",
    "⚡ Hourly Spot Prices & Fuel Generation Mix",
    "🎛️ Interactive BESS Capacity Sizing Calculator"
])

with tab1:
    st.subheader("Daily Battery Storage Arbitrage PnL (10 MW / 20 MWh System)")
    st.markdown("""
    Simulation of an industrial **10 MW / 20 MWh Battery Energy Storage System (BESS)** with **85% Round-Trip Efficiency (RTE)**.
    The battery automatically charges during the 2 cheapest hours of the day and discharges during the 2 most expensive peak hours.
    """)
    
    fig_pnl = px.bar(
        daily_bess_df,
        x="market_date",
        y="net_arbitrage_profit_eur",
        labels={"market_date": "Market Date", "net_arbitrage_profit_eur": "Daily Net Profit (€ EUR)"},
        title="Daily Net Arbitrage Profit (€ EUR)",
        color="net_arbitrage_profit_eur",
        color_continuous_scale="Viridis"
    )
    fig_pnl.update_layout(template="plotly_dark", height=420)
    st.plotly_chart(fig_pnl, use_container_width=True)
    
    st.subheader("Detailed Day-by-Day Financial Ledger")
    st.dataframe(
        daily_bess_df[[
            "market_date", "charge_hours", "discharge_hours", "avg_charge_price_eur",
            "avg_discharge_price_eur", "daily_spread_eur_mwh", "daily_charging_cost_eur",
            "daily_discharge_revenue_eur", "net_arbitrage_profit_eur"
        ]].rename(columns={
            "market_date": "Date",
            "charge_hours": "Charge Hours (UTC)",
            "discharge_hours": "Discharge Hours (UTC)",
            "avg_charge_price_eur": "Charge Price (€/MWh)",
            "avg_discharge_price_eur": "Discharge Price (€/MWh)",
            "daily_spread_eur_mwh": "Spread (€/MWh)",
            "daily_charging_cost_eur": "Charge Cost (€)",
            "daily_discharge_revenue_eur": "Discharge Rev (€)",
            "net_arbitrage_profit_eur": "Net Profit (€)"
        }),
        use_container_width=True
    )

with tab2:
    st.subheader("Wholesale Electricity Prices vs. Renewable Generation Mix")
    st.caption("Inspect how wind and solar surges drive electricity spot market prices down into negative territory.")
    
    # Combined Price and Generation Chart
    fig_mix = go.Figure()
    
    fig_mix.add_trace(go.Scatter(
        x=hourly_df["timestamp_utc"],
        y=hourly_df["spot_price_eur_mwh"],
        name="Spot Price (€/MWh)",
        line=dict(color="#f59e0b", width=2),
        yaxis="y1"
    ))
    
    fig_mix.add_trace(go.Bar(
        x=hourly_df["timestamp_utc"],
        y=hourly_df["solar_mw"],
        name="Solar PV (MW)",
        marker_color="#fbbf24",
        opacity=0.6,
        yaxis="y2"
    ))
    
    fig_mix.add_trace(go.Bar(
        x=hourly_df["timestamp_utc"],
        y=hourly_df["total_wind_mw"],
        name="Wind Onshore+Offshore (MW)",
        marker_color="#38bdf8",
        opacity=0.6,
        yaxis="y2"
    ))
    
    fig_mix.update_layout(
        template="plotly_dark",
        height=500,
        barmode="stack",
        yaxis=dict(title="Wholesale Price (€/MWh)", side="left", showgrid=False),
        yaxis2=dict(title="Renewable Generation (MW)", side="right", overlaying="y", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_mix, use_container_width=True)

with tab3:
    st.subheader("Interactive Battery Investment Sizing Tool")
    st.markdown("Adjust the battery system parameters below to simulate custom project economics:")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        custom_mw = st.slider("Battery Power Rating (MW):", min_value=1, max_value=200, value=20, step=5)
    with c2:
        custom_duration = st.selectbox("Battery Duration (Hours):", [1, 2, 4], index=1)
    with c3:
        custom_rte = st.slider("Round-Trip Efficiency (%):", min_value=70, max_value=95, value=85, step=1) / 100.0
        
    custom_capacity_mwh = custom_mw * custom_duration
    
    # Calculate custom returns using actual spread
    simulated_daily_profit = (custom_capacity_mwh * custom_rte * avg_spread) - (custom_capacity_mwh * (1.0 - custom_rte) * 50.0) # adjusted
    simulated_monthly = simulated_daily_profit * 30.0
    simulated_annual = simulated_daily_profit * 365.0
    
    st.markdown("### Projected Project Revenue:")
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric(f"Estimated Daily Profit ({custom_mw} MW / {custom_capacity_mwh} MWh)", f"€{simulated_daily_profit:,.0f} / Day")
    sc2.metric("Projected Monthly Arbitrage", f"€{simulated_monthly:,.0f} / Month")
    sc3.metric("Projected Annual Revenue", f"€{simulated_annual:,.0f} / Year")

st.sidebar.title("⚡ Grid Telemetry")
st.sidebar.info(f"""
- **Market:** Germany / Central Europe (EPEX SPOT)
- **Observations:** `{len(hourly_df):,}` Hourly Intervals
- **Base BESS Model:** 10 MW / 20 MWh
- **Negative Hours:** `{neg_hours}` Hours
""")

if st.sidebar.button("🔄 Refresh Grid Telemetry Now"):
    with st.spinner("Fetching latest Fraunhofer ISE spot prices & generation..."):
        import subprocess
        subprocess.run(["python", os.path.join(BASE_DIR, "ingest_engine", "ingest_grid_data.py")], check=True)
        subprocess.run(["python", os.path.join(BASE_DIR, "models", "arbitrage_analysis.py")], check=True)
        st.cache_data.clear()
        st.success("Refreshed with live European grid signals!")
        st.rerun()
