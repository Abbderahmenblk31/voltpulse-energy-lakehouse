"""
VoltPulse - Power Grid Pipeline & Data Quality Tests
=====================================================
Automated regression tests to verify time-series integrity,
negative price validation, and battery storage arbitrage formulas.
"""

import os
import duckdb
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "lakehouse", "energy_lakehouse.duckdb")

@pytest.fixture
def db_conn():
    con = duckdb.connect(DB_PATH, read_only=True)
    yield con
    con.close()

def test_bronze_tables_contain_real_data(db_conn):
    """Verifies that spot prices and generation mix are populated with real observations."""
    prices_count = db_conn.execute("SELECT COUNT(*) FROM raw_spot_prices").fetchone()[0]
    gen_count = db_conn.execute("SELECT COUNT(*) FROM raw_generation_mix").fetchone()[0]
    assert prices_count > 100, f"Insufficient price records: {prices_count}"
    assert gen_count > 100, f"Insufficient generation records: {gen_count}"

def test_silver_timestamp_reconciliation(db_conn):
    """Ensures timestamps are reconciled without null dates and correctly categorized."""
    null_dates = db_conn.execute("SELECT COUNT(*) FROM silver_hourly_market WHERE market_date IS NULL").fetchone()[0]
    assert null_dates == 0, "Found null market dates in silver layer!"

def test_negative_price_flag_integrity(db_conn):
    """Ensures negative price flag strictly matches mathematical sign of spot price."""
    mismatched = db_conn.execute("""
        SELECT COUNT(*) 
        FROM silver_hourly_market 
        WHERE (spot_price_eur_mwh < 0 AND is_negative_price != 1)
           OR (spot_price_eur_mwh >= 0 AND is_negative_price != 0)
    """).fetchone()[0]
    assert mismatched == 0, f"Found {mismatched} negative price flag discrepancies!"

def test_battery_arbitrage_spread_logic(db_conn):
    """Ensures daily discharge price is always >= daily charge price (spread is non-negative)."""
    invalid_spreads = db_conn.execute("""
        SELECT COUNT(*) 
        FROM fct_daily_bess_arbitrage 
        WHERE daily_spread_eur_mwh < 0
    """).fetchone()[0]
    assert invalid_spreads == 0, f"Found {invalid_spreads} negative daily arbitrage spreads!"

def test_executive_summary_integrity(db_conn):
    """Verifies executive summary mart contains valid positive ROI."""
    row = db_conn.execute("SELECT * FROM mart_energy_executive_summary").fetchone()
    total_days = row[0]
    total_revenue = row[1]
    assert total_days > 0, "No market days analyzed in summary!"
    assert total_revenue > 0, f"Expected positive BESS revenue, got: {total_revenue}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
