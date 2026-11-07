"""
VoltPulse - Master Pipeline Orchestrator
========================================
Runs full end-to-end power grid data pipeline:
1. Ingests wholesale spot prices and fuel generation mix from Fraunhofer ISE
2. Executes BESS battery storage arbitrage modeling in DuckDB
3. Runs automated data quality and time-series tests
4. Launches the interactive Streamlit Energy Trading Dashboard
"""

import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_step(title, command):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)
    result = subprocess.run(command, cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"❌ Error encountered in: {title}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    print("""
    ========================================================
       ⚡ VOLTPULSE: POWER GRID & BATTERY ARBITRAGE LAKEHOUSE ⚡
    ========================================================
    """)
    run_step("STEP 1: INGESTING POWER GRID & SPOT MARKET TELEMETRY", [sys.executable, "ingest_engine/ingest_grid_data.py"])
    run_step("STEP 2: RUNNING BESS ARBITRAGE & ENERGY MODELS", [sys.executable, "models/arbitrage_analysis.py"])
    run_step("STEP 3: EXECUTING AUTOMATED DATA TESTS", [sys.executable, "-m", "pytest", "tests/", "-v"])
    
    print("\n" + "="*70)
    print("  STEP 4: LAUNCHING INTERACTIVE ENERGY BI DASHBOARD")
    print("="*70)
    print("Opening Streamlit on http://localhost:8501 ...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard/app.py"], cwd=BASE_DIR)
