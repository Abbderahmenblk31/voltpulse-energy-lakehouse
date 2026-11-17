# ⚡ VoltPulse: National Power Grid Telemetry & Battery Energy Arbitrage Lakehouse

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit%20Cloud-FF4B4B.svg?style=for-the-badge&logo=streamlit)](https://abbderahmenblk31-voltpulse-energy-lakehouse-dashboardapp-nklezb.streamlit.app/)
[![Energy Lakehouse CI](https://github.com/Abbderahmenblk31/voltpulse-energy-lakehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/Abbderahmenblk31/voltpulse-energy-lakehouse/actions)
[![Engine: DuckDB](https://img.shields.io/badge/Engine-DuckDB%20Time--Series-yellow.svg)](https://duckdb.org/)
[![Data: 100% Real Fraunhofer ISE](https://img.shields.io/badge/Data-Official%20Fraunhofer%20ISE%20API-blue.svg)](https://api.energy-charts.info/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 🔗 **Interactive Cloud Application:** [Launch VoltPulse Live Dashboard](https://abbderahmenblk31-voltpulse-energy-lakehouse-dashboardapp-nklezb.streamlit.app/)

An enterprise-grade **Energy Data Engineering, Quantitative Market Analytics & Prescriptive Decision Lakehouse**. VoltPulse ingests **100% genuine wholesale electricity Day-Ahead spot prices** and **realized multi-fuel generation telemetry (21 fuel types)** from the official **Fraunhofer ISE / German Federal Grid Open Data API**.

The platform models high-frequency price volatility, captures **Negative Electricity Pricing events**, and executes a **Physics-Constrained Prescriptive 24-Hour BESS Dispatch Engine** that optimizes charge/discharge cycles for an industrial **10 MW / 20 MWh Battery Storage System** to maximize net revenue while protecting cell health.

---

## 📌 Executive Summary & Grid Economics

With the rapid expansion of renewable energy across Europe, power grids experience extreme structural volatility:
1. **Negative Price Spikes:** During midday solar surges and North Sea windstorms, electricity supply outstrips industrial demand. Spot prices plunge into **Negative Territory (e.g. -€20 to -€100/MWh)**. In this scenario, power generators must pay grid operators to absorb excess power.
2. **Evening Peak Spikes:** When solar generation drops at dusk and residential/industrial demand peaks, spot prices spike to **+€300 to +€600/MWh**.

This volatility underpins the multi-billion dollar clean energy asset class: **Utility-Scale Battery Energy Storage Systems (BESS)**.

**VoltPulse** operates as an automated quantitative trading and dispatch engine:
* Ingests real-time prices and 21 generation types (Solar, Wind Onshore/Offshore, Gas, Hard Coal, Lignite, Nuclear, Hydro, Biomass).
* Reconciles time-series records across 15-minute and 1-hour resolution boundaries in a local DuckDB Lakehouse.
* Simulates daily arbitrage across historical market periods.
* **Prescriptive Decision Intelligence:** Formulates an optimal hour-by-hour dispatch schedule for the upcoming 24-hour cycle, directing grid operators when to charge, hold, or discharge.

---

## 🏛️ Medallion Architecture & System Design

```text
       [Official National Power Grid API (Fraunhofer ISE / SMARD)]
         (Wholesale Day-Ahead Spot Prices & Realized Generation Mix)
                                      │
                                      ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                 BRONZE LAYER (RAW INGESTION)                │
  │  • fetch_spot_prices(): Wholesale market prices (EUR/MWh)   │
  │  • fetch_generation_mix(): 21 generation & fuel categories  │
  │  • Automated retry, backoff, and UTC timestamp alignment    │
  └─────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                 SILVER LAYER (RECONCILIATION)               │
  │  • Reconciles prices with fuel generation by UTC timestamp  │
  │  • Classifies peak (08:00-20:00 CET) vs off-peak blocks     │
  │  • Enforces negative price flag integrity (is_negative)     │
  └─────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │              GOLD LAYER (BESS FINANCIAL MARTS)              │
  │  • fct_daily_bess_arbitrage: Historical charge/discharge PnL│
  │  • mart_energy_executive_summary: Portfolio ROI & spreads   │
  └─────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │    PRESCRIPTIVE DECISION INTELLIGENCE (DISPATCH ENGINE)     │
  │  • mart_prescriptive_dispatch_plan:                         │
  │    - 24-hour hour-by-hour optimal dispatch vector           │
  │    - Physics constraints: 0 ≤ SOC ≤ 20 MWh, 10 MW max power │
  │    - Round-Trip Efficiency: 85% thermal loss modeled        │
  │    - Action: CHARGE / DISCHARGE / IDLE                      │
  └─────────────────────────────┬───────────────────────────────┘
                                │
              ┌─────────────────┴─────────────────┐
              ▼                                   ▼
 ┌──────────────────────────────┐    ┌──────────────────────────────┐
 │  AUTOMATED PYTEST CONTRACTS  │    │  INTERACTIVE ENERGY BI APP   │
 │  • Time-series continuity    │    │  • Streamlit + Plotly Dark   │
 │  • Negative price sign test  │    │  • PnL Ledger & Price Curves │
 │  • Spread positivity bounds  │    │  • Interactive Sizing Tool   │
 │  • Prescriptive SOC bounds   │    │  • 24h Prescriptive Dispatch │
 └──────────────────────────────┘    └──────────────────────────────┘
```

---

## 🧮 Prescriptive BESS Mathematical Dispatch Model

The prescriptive engine optimizes the daily economic objective function subject to physical battery state-of-charge constraints:

$$\max \sum_{t=0}^{23} \Pi_t$$

Where:
$$\Pi_t = \begin{cases} 
- \left(P_{\text{chg}, t} \times S_t\right) & \text{if Charging} \\
+ \left(P_{\text{dis}, t} \times \eta_{\text{rte}} \times S_t\right) & \text{if Discharging} \\
0 & \text{if Idle}
\end{cases}$$

Subject to:
1. **Power Rating Constraint:** $0 \le P_{\text{chg}, t} \le 10\text{ MW}$, $0 \le P_{\text{dis}, t} \le 10\text{ MW}$.
2. **State of Charge (SOC) Bounds:** $0 \le SOC_t \le 20\text{ MWh}$.
3. **SOC Continuity:** $SOC_{t+1} = SOC_t + \left(P_{\text{chg}, t} \cdot \Delta t\right) - \left(\frac{P_{\text{dis}, t}}{\eta_{\text{rte}}} \cdot \Delta t\right)$.
4. **Round-Trip Efficiency ($\eta_{\text{rte}}$):** $85.0\%$ (accounting for AC-DC conversion and lithium thermal losses).

### Prescriptive Dispatch Actions:
* **`🟢 CHARGE (10 MW)`:** Scheduled during lowest off-peak tariff hours (02:00-05:00 UTC) or negative pricing blocks.
* **`🔴 DISCHARGE (10 MW)`:** Dispatches stored electricity into evening peak hours (17:00-19:00 UTC) capturing maximum spread.
* **`⚪ IDLE / HOLD`:** Preserves battery state of charge during mid-tier price corridors to avoid degradation.

---

## 📊 Live Financial Results & Prescriptive Schedule

### 1. Historical BESS Arbitrage Scorecard (32 Market Days)
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

### 2. 24-Hour Prescriptive Dispatch Plan (Live 24h Schedule Sample)
```text
Hour (UTC)  Price (€/MWh)  Prescriptive Action   Power (MW)  SOC (MWh)   Hourly Flow (€)  Cum PnL (€)   Automated Decision Rationale
------------------------------------------------------------------------------------------------------------------------------------------------------
00:00-02:00     €225-€235  ⚪ IDLE / HOLD               0.0        0.0             €0.00        €0.00   Market price in neutral corridor. Maintain SOC.
03:00             €222.38  🟢 CHARGE (10 MW)          +10.0       10.0        -€2,223.80   -€2,223.80   Lowest off-peak tariff window. Charge 10 MW.
04:00             €224.70  🟢 CHARGE (10 MW)          +10.0       20.0        -€2,247.00   -€4,470.80   Second lowest off-peak window. Battery reaches 100% SOC.
05:00-16:00     €226-€330  ⚪ IDLE / HOLD               0.0       20.0             €0.00   -€4,470.80   Preserve full capacity for evening price peak.
17:00             €355.17  🔴 DISCHARGE (10 MW)       -10.0       10.0        +€3,018.95   -€1,451.85   Peak evening spike. Dispatch 10 MW into high-demand block.
18:00             €357.12  🔴 DISCHARGE (10 MW)       -10.0        0.0        +€3,035.52   +€1,583.67   Maximum market price spike. Complete cycle with profit.
19:00-23:00     €252-€347  ⚪ IDLE / HOLD               0.0        0.0             €0.00   +€1,583.67   Cycle complete. Hold battery ready for next trading day.
------------------------------------------------------------------------------------------------------------------------------------------------------
💡 PROJECTED SINGLE-DAY NET RETURN: +€1,583.67 EUR
```

---

## 🛠️ Tech Stack & Engineering Decisions

| Layer | Technology | Architectural Justification |
| :--- | :--- | :--- |
| **Engine / OLAP** | **DuckDB 1.0+ Columnar** | Ultra-fast local analytical SQL engine. Eliminates heavy Spark or Snowflake costs while executing complex window functions and time-series joins in sub-seconds. |
| **Data Ingestion** | **Python 3 / Requests / PyArrow** | Automated ingestion pipeline connecting directly to the official Fraunhofer ISE / SMARD German power grid API. |
| **Analytical Modeling** | **DuckDB SQL + Pandas** | Medallion time-series reconciliation, peak/off-peak classification, and daily battery arbitrage calculations. |
| **Visualization & BI** | **Streamlit + Plotly Dark** | Dual-axis price vs. renewable generation charts, financial ledgers, and interactive battery capacity sizing sliders. |
| **Quality Testing** | **Pytest** | Regression test suite enforcing non-negative spreads, timestamp reconciliation, and SOC boundary adherence. |
| **CI/CD** | **GitHub Actions** | Automated end-to-end integration pipeline executing on every push. |

---

## 🧪 Automated Regression & Data Quality Test Suite

Run the automated test suite with:
```bash
pytest tests/ -v
```

Execution output:
```text
tests/test_grid_pipeline.py::test_bronze_tables_contain_real_data PASSED [ 16%]
tests/test_grid_pipeline.py::test_silver_timestamp_reconciliation PASSED [ 33%]
tests/test_grid_pipeline.py::test_negative_price_flag_integrity PASSED   [ 50%]
tests/test_grid_pipeline.py::test_battery_arbitrage_spread_logic PASSED  [ 66%]
tests/test_grid_pipeline.py::test_executive_summary_integrity PASSED     [ 83%]
tests/test_grid_pipeline.py::test_prescriptive_dispatch_plan PASSED      [100%]
============================== 6 passed in 2.42s ==============================
```

---

## 🚀 Quickstart: Run Locally in 60 Seconds

### 1. Clone the repository
```bash
git clone https://github.com/Abbderahmenblk31/voltpulse-energy-lakehouse.git
cd voltpulse-energy-lakehouse
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the complete pipeline & launch dashboard
```bash
python run_pipeline.py
```
*This command fetches the latest spot prices, models the BESS arbitrage in DuckDB, passes all quality tests, and launches the dashboard at `http://localhost:8501`.*

---

## 📂 Repository Structure

```text
voltpulse-energy-lakehouse/
├── .github/
│   └── workflows/
│       └── ci.yml                    # Automated GitHub Actions CI workflow
├── data/
│   └── lakehouse/
│       └── energy_lakehouse.duckdb   # Embedded DuckDB database with time-series marts
├── ingest_engine/
│   └── ingest_grid_data.py           # Real-time wholesale prices & generation mix ingestion
├── models/
│   └── arbitrage_analysis.py         # Analytical SQL, BESS arbitrage simulation & prescriptive dispatch
├── dashboard/
│   └── app.py                        # Streamlit + Plotly dark interactive intelligence dashboard
├── tests/
│   └── test_grid_pipeline.py         # Automated data quality & mathematical consistency tests
├── requirements.txt                  # Python dependencies
├── run_pipeline.py                   # Master single-command pipeline orchestrator
└── README.md                         # Project documentation and quantitative case study
```

---

## 📜 License
MIT License. Open source research and engineering.
