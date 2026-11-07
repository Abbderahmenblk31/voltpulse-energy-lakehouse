"""
VoltPulse - European Power Grid & Spot Market Ingestion Engine
==============================================================
Ingests 100% genuine real-time and historical electricity spot prices (Day-Ahead)
and generation breakdown by fuel type from the official Fraunhofer ISE
Energy-Charts Open Data API (covering Germany & Central Europe).
Persists time-series records into an embedded DuckDB Lakehouse.
"""

import os
import sys
import requests
import duckdb
import pandas as pd
from datetime import datetime, timezone, timedelta

# Ensure UTF-8 output on Windows consoles
if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAKEHOUSE_DIR = os.path.join(BASE_DIR, "data", "lakehouse")
os.makedirs(LAKEHOUSE_DIR, exist_ok=True)
DB_PATH = os.path.join(LAKEHOUSE_DIR, "energy_lakehouse.duckdb")

BASE_API_URL = "https://api.energy-charts.info"
HEADERS = {"User-Agent": "VoltPulse-Energy-Lakehouse/1.0 (Open-Research)"}

def fetch_spot_prices(country="de", start_date=None, end_date=None):
    """Fetches Day-Ahead Wholesale Electricity Spot Prices (EUR/MWh)."""
    print(f"[1/3] Fetching wholesale electricity spot prices for '{country.upper()}'...")
    url = f"{BASE_API_URL}/price?country={country}"
    if start_date and end_date:
        url += f"&start={start_date}&end={end_date}"
        
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    
    timestamps = payload.get("unix_seconds", [])
    prices = payload.get("price", [])
    
    records = []
    for ts, price in zip(timestamps, prices):
        if price is not None:
            dt_utc = datetime.fromtimestamp(ts, tz=timezone.utc)
            records.append({
                "timestamp_utc": dt_utc,
                "country": country.upper(),
                "spot_price_eur_mwh": float(price),
                "is_negative_price": 1 if float(price) < 0 else 0
            })
            
    df_prices = pd.DataFrame(records)
    print(f"   -> Retrieved {len(df_prices):,} hourly spot market price observations.")
    return df_prices

def fetch_generation_mix(country="de", start_date=None, end_date=None):
    """Fetches actual hourly power generation by fuel type (Solar, Wind, Gas, Coal, etc.)."""
    print(f"[2/3] Fetching actual power generation mix for '{country.upper()}'...")
    url = f"{BASE_API_URL}/public_power?country={country}"
    if start_date and end_date:
        url += f"&start={start_date}&end={end_date}"
        
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    
    timestamps = payload.get("unix_seconds", [])
    production_types = payload.get("production_types", [])
    
    # Map production types into standardized series
    type_data = {}
    for prod in production_types:
        name = prod.get("name", "").lower()
        data = prod.get("data", [])
        if "solar" in name:
            type_data["solar_mw"] = data
        elif "wind onshore" in name:
            type_data["wind_onshore_mw"] = data
        elif "wind offshore" in name:
            type_data["wind_offshore_mw"] = data
        elif "natural gas" in name or "fossil gas" in name:
            type_data["gas_mw"] = data
        elif "brown coal" in name or "lignite" in name:
            type_data["lignite_coal_mw"] = data
        elif "hard coal" in name:
            type_data["hard_coal_mw"] = data
        elif "hydro" in name and "storage consumption" not in name:
            type_data["hydro_mw"] = data
        elif "biomass" in name:
            type_data["biomass_mw"] = data
        elif "nuclear" in name:
            type_data["nuclear_mw"] = data
            
    records = []
    n = len(timestamps)
    for i in range(n):
        dt_utc = datetime.fromtimestamp(timestamps[i], tz=timezone.utc)
        solar = type_data.get("solar_mw", [0]*n)[i] or 0.0
        wind_on = type_data.get("wind_onshore_mw", [0]*n)[i] or 0.0
        wind_off = type_data.get("wind_offshore_mw", [0]*n)[i] or 0.0
        gas = type_data.get("gas_mw", [0]*n)[i] or 0.0
        coal = (type_data.get("lignite_coal_mw", [0]*n)[i] or 0.0) + (type_data.get("hard_coal_mw", [0]*n)[i] or 0.0)
        hydro = type_data.get("hydro_mw", [0]*n)[i] or 0.0
        biomass = type_data.get("biomass_mw", [0]*n)[i] or 0.0
        nuclear = type_data.get("nuclear_mw", [0]*n)[i] or 0.0
        
        total_renewables = solar + wind_on + wind_off + hydro + biomass
        total_generation = total_renewables + gas + coal + nuclear
        
        records.append({
            "timestamp_utc": dt_utc,
            "country": country.upper(),
            "solar_mw": float(solar),
            "wind_onshore_mw": float(wind_on),
            "wind_offshore_mw": float(wind_off),
            "gas_mw": float(gas),
            "coal_mw": float(coal),
            "hydro_mw": float(hydro),
            "biomass_mw": float(biomass),
            "nuclear_mw": float(nuclear),
            "total_renewables_mw": float(total_renewables),
            "total_generation_mw": float(total_generation),
            "renewable_share_pct": round((total_renewables / total_generation * 100.0), 1) if total_generation > 0 else 0.0
        })
        
    df_gen = pd.DataFrame(records)
    print(f"   -> Retrieved {len(df_gen):,} generation breakdown records.")
    return df_gen

def persist_to_lakehouse(df_prices, df_gen):
    """Stores bronze raw time-series into DuckDB Lakehouse."""
    print("[3/3] Ingesting time-series into DuckDB Lakehouse...")
    con = duckdb.connect(DB_PATH)
    
    con.register("df_prices", df_prices)
    con.register("df_gen", df_gen)
    
    con.execute("""
        CREATE OR REPLACE TABLE raw_spot_prices AS
        SELECT * FROM df_prices;
    """)
    
    con.execute("""
        CREATE OR REPLACE TABLE raw_generation_mix AS
        SELECT * FROM df_gen;
    """)
    
    # Summary Metrics
    price_stats = con.execute("""
        SELECT 
            MIN(spot_price_eur_mwh) as min_price,
            MAX(spot_price_eur_mwh) as max_price,
            ROUND(AVG(spot_price_eur_mwh), 2) as avg_price,
            SUM(is_negative_price) as negative_price_hours
        FROM raw_spot_prices;
    """).fetchone()
    
    print("\n" + "="*70)
    print("SUCCESS: VOLTPULSE POWER LAKEHOUSE INGESTION COMPLETE!")
    print(f"   * Lakehouse Database: {DB_PATH}")
    print(f"   * Price Range: {price_stats[0]:.2f} to {price_stats[1]:.2f} EUR/MWh")
    print(f"   * Average Electricity Price: {price_stats[2]} EUR/MWh")
    print(f"   * Negative Price Occurrences: {price_stats[3]} hours (Surplus Energy Events)")
    print("="*70 + "\n")
    con.close()

if __name__ == "__main__":
    print("="*70)
    print("  VOLTPULSE: POWER GRID & SPOT MARKET INGESTION ENGINE")
    print("="*70)
    # Default: Fetch recent 30-day window covering volatile market conditions
    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=30)
    start_str = start_dt.strftime("%Y-%m-%d")
    end_str = end_dt.strftime("%Y-%m-%d")
    
    prices = fetch_spot_prices("de", start_str, end_str)
    gen = fetch_generation_mix("de", start_str, end_str)
    persist_to_lakehouse(prices, gen)
