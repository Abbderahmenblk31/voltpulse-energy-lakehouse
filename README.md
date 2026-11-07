# ⚡ VoltPulse: National Power Grid Telemetry & Battery Energy Arbitrage Lakehouse

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit%20Cloud-FF4B4B.svg?style=for-the-badge&logo=streamlit)](https://abbderahmenblk31-voltpulse-energy-lakehouse-dashboardapp-nklezb.streamlit.app/)
[![Energy Lakehouse CI](https://github.com/Abbderahmenblk31/voltpulse-energy-lakehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/Abbderahmenblk31/voltpulse-energy-lakehouse/actions)
[![Engine: DuckDB](https://img.shields.io/badge/Engine-DuckDB%20Time--Series-yellow.svg)](https://duckdb.org/)
[![Data: 100% Real Fraunhofer ISE](https://img.shields.io/badge/Data-Official%20Fraunhofer%20ISE%20API-blue.svg)](https://api.energy-charts.info/)

> 🔗 **Interactive Cloud Application:** [Launch VoltPulse Live Dashboard](https://abbderahmenblk31-voltpulse-energy-lakehouse-dashboardapp-nklezb.streamlit.app/)

An enterprise-grade **Energy Data Engineering & Quantitative Analytics Lakehouse** that ingests **100% genuine wholesale electricity spot prices (Day-Ahead)** and **realized multi-fuel generation telemetry** from the official **Fraunhofer ISE / German Federal Grid Open Data API**. 

The platform models high-frequency price volatility, captures **Negative Electricity Pricing events**, and simulates daily financial returns for industrial **Battery Energy Storage Systems (BESS Arbitrage)**.

---

## 📌 Executive Summary & Financial Problem

As solar and wind penetration surges across Europe, power grids experience extreme structural volatility. When wind storms hit the North Sea during low-demand periods, power generation exceeds transmission limits, driving wholesale electricity spot prices into **Negative Territory (e.g. -€20/MWh to -€50/MWh)**—meaning producers must pay grid operators to absorb excess power. Conversely, during evening peak hours, prices spike to **+€300/MWh to +€500/MWh**.

This volatility drives the multi-billion dollar clean energy asset class: **Utility-Scale Battery Energy Storage (BESS)**.

**VoltPulse** operates as an automated financial decision engine:
1. Ingests hourly wholesale spot prices and 21 generation types (Solar, Wind Onshore/Offshore, Gas, Coal, Nuclear, Biomass, Hydro).
2. Cleans and reconciles time-series records across market boundaries.
3. Simulates a standard **10 MW / 20 MWh industrial BESS system (85% Round-Trip Efficiency)** that automatically charges during lowest/negative price hours and discharges at evening peak.
4. Generates executive investment metrics: **Daily Net PnL**, **Peak-to-Trough Arbitrage Spread**, and **Surplus Green Energy Waste**.

---

## 🏛️ System Architecture

```text
       [Official National Power Grid API (Fraunhofer ISE / SMARD)]
         (Wholesale Day-Ahead Spot Prices & Realized Generation Mix)
                                      │
                                      ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                 INGESTION & BRONZE LAYER                    │
  │  • fetch_spot_prices(): Wholesale market prices (EUR/MWh)   │
  │  • fetch_generation_mix(): 21 generation & fuel categories  │
  │  • Automated retry, backoff, and UTC timestamp alignment    │
  └─────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                 SILVER LAYER (RECONCILIATION)               │
  │  • Reconciles prices with fuel generation by UTC timestamp  │
  │  • Classifies peak vs off-peak European trading blocks      │
  │  • Enforces data contract: Negative price flag integrity    │
  └─────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │              GOLD LAYER (BESS FINANCIAL MARTS)              │
  │  • fct_daily_bess_arbitrage: Dynamic 2-hour charge/discharge│
  │    algorithm with 85% Round-Trip Efficiency (RTE) loss model│
  │  • mart_energy_executive_summary: Portfolio ROI & spreads   │
  └─────────────────────────────┬───────────────────────────────┘
                                │
             ┌──────────────────┴──────────────────┐
             ▼                                     ▼
┌──────────────────────────────┐     ┌──────────────────────────────┐
│  AUTOMATED PYTEST CONTRACTS  │     │ INTERACTIVE ENERGY BI APP    │
│  • Time-series continuity    │     │ • Streamlit + Plotly Dark    │
│  • Negative price logic      │     │ • PnL Ledger & Price Curves  │
│  • Positive spread integrity │     │ • Custom BESS Sizing Tool    │
└──────────────────────────────┘     └──────────────────────────────┘
```

---

## 📊 Live Financial Results (Sample from Actual 32-Day Run)

Running the analytical model against real European market data yielded these live returns:

```text
================================================================================
🔋 BESS BATTERY ARBITRAGE FINANCIAL SCORECARD (10 MW / 20 MWh SYSTEM)
================================================================================
   * Total Market Days Analyzed:        32 Days
   * Total Net Battery Arbitrage Profit: €69,167.85 EUR
   * Average Daily Profit per Battery:   €2,161.50 EUR / Day
   * Average Peak-to-Trough Spread:     €149.07 EUR / MWh
   * Maximum Single-Day Spread:          €344.13 EUR / MWh
================================================================================

[+] Top 5 Most Profitable Arbitrage Days Captured:
Date          Avg Charge (€)    Avg Discharge (€)    Daily Spread (€)    Net Daily Profit (€)
2026-10-29        €229.87            €574.00             €344.13              €5,160.60
2026-10-26         €15.80            €248.93             €233.13              €3,915.81
2026-10-11         €14.17            €240.76             €226.59              €3,809.52
2026-10-27         €39.46            €270.03             €230.57              €3,801.31
2026-10-22         €70.01            €285.23             €215.22              €3,448.71
```

---

## 🛠️ Tech Stack & Engineering Decisions

| Component | Technology | Engineering Justification |
| :--- | :--- | :--- |
| **Engine / OLAP** | **DuckDB 2.0 (Embedded)** | Unrivaled analytical performance on local time-series data. Computes daily window functions across thousands of hours in milliseconds. |
| **Data Source** | **Fraunhofer ISE Open API** | Direct scientific source for European power markets. 100% open, verified, and free of authentication keys. |
| **Data Quality** | **Pytest + SQL Assertions** | Automated unit tests validating time continuity, negative price signs, and non-negative daily spreads. |
| **Serving & BI** | **Streamlit + Plotly Dark** | Interactive energy trading dashboard featuring dual-axis price-generation charts and dynamic capacity sizing tools. |
| **CI/CD** | **GitHub Actions** | Automated end-to-end continuous integration running ingestion, modeling, and tests on every push. |

---

## 🚀 Quickstart: Run in 60 Seconds

### 1. Clone the repository:
```bash
git clone https://github.com/Abbderahmenblk31/voltpulse-energy-lakehouse.git
cd voltpulse-energy-lakehouse
```

### 2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run complete pipeline & launch dashboard:
```bash
python run_pipeline.py
```
*This command pulls live spot market data, executes BESS arbitrage models in DuckDB, passes all quality tests, and launches the interactive energy dashboard in your browser at `http://localhost:8501`!*

---

## 🧪 Running Automated Tests

To run the data quality regression tests:
```bash
pytest tests/ -v
```

Output:
```text
tests/test_grid_pipeline.py::test_bronze_tables_contain_real_data PASSED       [ 20%]
tests/test_grid_pipeline.py::test_silver_timestamp_reconciliation PASSED      [ 40%]
tests/test_grid_pipeline.py::test_negative_price_flag_integrity PASSED        [ 60%]
tests/test_grid_pipeline.py::test_battery_arbitrage_spread_logic PASSED        [ 80%]
tests/test_grid_pipeline.py::test_executive_summary_integrity PASSED          [100%]
============================== 5 passed in 0.82s ==============================
```

---

## 📂 Repository Structure

```text
voltpulse-energy-lakehouse/
├── .github/
│   └── workflows/
│       └── ci.yml                    # Automated GitHub Actions CI workflow
├── data/
│   └── lakehouse/
│       └── energy_lakehouse.duckdb   # Embedded DuckDB database
├── ingest_engine/
│   └── ingest_grid_data.py           # Ingestion of wholesale prices & 21 fuel types
├── models/
│   └── arbitrage_analysis.py         # Time-series reconciliation & BESS PnL models
├── dashboard/
│   └── app.py                        # Streamlit + Plotly interactive energy app
├── tests/
│   └── test_grid_pipeline.py         # Automated data quality & contract tests
├── requirements.txt                  # Python dependencies
├── run_pipeline.py                   # Master single-command pipeline orchestrator
└── README.md                         # Project documentation and engineering case study
```

---

## 📜 License
MIT License. Open source energy research and quantitative engineering.
