#!/usr/bin/env python3
"""
BTCADP Data Generator
=====================
Fetches historical Bitcoin daily price data from free public sources
and generates the BTCADP CSV file per the BTCADP Specification v1.0.

IMPORTANT: This script uses aggregated public data as PROVISIONAL values.
These are not true BTCADP values computed from trade-level exchange data.
All values are flagged accordingly. The research community is invited to
produce definitive values per Section 7 of the specification.

Data Sources:
  - Era 0 (Jan 3, 2009 - Jul 17, 2010): $0.00 (no market existed)
  - Era 1 (Jul 18, 2010 - Feb 24, 2014): CoinGecko aggregated daily data
  - Era 2 (Feb 25, 2014 - Dec 31, 2017): CoinGecko aggregated daily data
  - Era 3 (Jan 1, 2018 - Present):       CoinGecko aggregated daily data

Usage:
  python btcadp_generate.py                 # Generate full CSV
  python btcadp_generate.py --output data.csv  # Custom output path
  python btcadp_generate.py --end-date 2025-12-31  # Custom end date

Requirements:
  pip install requests
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library required. Install with: pip install requests")
    sys.exit(1)


# ===========================================================================
#  CONSTANTS
# ===========================================================================

# Era boundaries (inclusive)
ERA_0_START = datetime(2009, 1, 3, tzinfo=timezone.utc)
ERA_0_END   = datetime(2010, 7, 17, tzinfo=timezone.utc)
ERA_1_START = datetime(2010, 7, 18, tzinfo=timezone.utc)
ERA_1_END   = datetime(2014, 2, 24, tzinfo=timezone.utc)
ERA_2_START = datetime(2014, 2, 25, tzinfo=timezone.utc)
ERA_2_END   = datetime(2017, 12, 31, tzinfo=timezone.utc)
ERA_3_START = datetime(2018, 1, 1, tzinfo=timezone.utc)

# CoinGecko free API (no key required, rate limited to ~10-30 req/min)
COINGECKO_API_KEY = "CG-J3JAeCZyNhrfWTUqpW1PDuPX"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_MARKET_CHART_RANGE = f"{COINGECKO_BASE}/coins/bitcoin/market_chart/range"
COINGECKO_HEADERS = {"x-cg-demo-api-key": COINGECKO_API_KEY}

# CSV columns
CSV_HEADERS = [
    "day",            # Day number (1 = January 3, 2009)
    "date",           # YYYY-MM-DD (UTC)
    "btcadp_usd",     # Price in USD, 2 decimal places
    "confidence",     # Full, Reduced, Low, Single-source, Defined, Provisional
    "era",            # 0, 1, 2, or 3
    "data_source",    # Description of data origin
    "status",         # provisional or definitive
    "spec_version",   # 1.0
]

# Genesis date for day numbering
GENESIS_DATE = datetime(2009, 1, 3, tzinfo=timezone.utc)

# Polite delay between API requests (seconds)
API_DELAY = 6  # CoinGecko free tier: ~10-12 calls/min


# ===========================================================================
#  ERA 0: Genesis — $0.00 for all days
# ===========================================================================

def generate_era_0():
    """Generate Era 0 data: $0.00 for every day from Jan 3, 2009 to Jul 17, 2010."""
    print("Generating Era 0 (Genesis: Jan 3, 2009 - Jul 17, 2010)...")
    rows = []
    current = ERA_0_START
    while current <= ERA_0_END:
        day_number = (current - GENESIS_DATE).days + 1
        rows.append({
            "day": str(day_number),
            "date": current.strftime("%Y-%m-%d"),
            "btcadp_usd": "0.00",
            "confidence": "Defined",
            "era": "0",
            "data_source": "Specification-defined (no market existed)",
            "status": "definitive",
            "spec_version": "1.0",
        })
        current += timedelta(days=1)
    print(f"  Era 0: {len(rows)} days generated.")
    return rows


# ===========================================================================
#  COINGECKO DATA FETCHER
# ===========================================================================

def fetch_coingecko_range(start_dt, end_dt):
    """
    Fetch daily prices from CoinGecko for a date range.
    Returns a dict: { "YYYY-MM-DD": price_float, ... }
    
    CoinGecko's market_chart/range endpoint returns daily data points
    when the range exceeds 90 days.
    """
    prices = {}
    
    # CoinGecko uses UNIX timestamps
    from_ts = int(start_dt.timestamp())
    to_ts = int(end_dt.timestamp()) + 86400  # Include end date
    
    # Fetch in ~365-day chunks to avoid timeouts
    chunk_start = from_ts
    chunk_size = 365 * 86400
    
    while chunk_start < to_ts:
        chunk_end = min(chunk_start + chunk_size, to_ts)
        
        params = {
            "vs_currency": "usd",
            "from": chunk_start,
            "to": chunk_end,
        }
        
        start_str = datetime.fromtimestamp(chunk_start, tz=timezone.utc).strftime("%Y-%m-%d")
        end_str = datetime.fromtimestamp(chunk_end, tz=timezone.utc).strftime("%Y-%m-%d")
        print(f"  Fetching {start_str} to {end_str}...")
        
        try:
            resp = requests.get(COINGECKO_MARKET_CHART_RANGE, params=params, headers=COINGECKO_HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 429:
                print(f"  Rate limited. Waiting 60 seconds...")
                time.sleep(60)
                continue  # Retry this chunk
            else:
                print(f"  ERROR: HTTP {resp.status_code}: {e}")
                chunk_start = chunk_end
                continue
        except requests.exceptions.RequestException as e:
            print(f"  ERROR: {e}")
            chunk_start = chunk_end
            continue
        
        if "prices" in data:
            for timestamp_ms, price in data["prices"]:
                dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                date_str = dt.strftime("%Y-%m-%d")
                # CoinGecko may return multiple points per day; keep the last one
                prices[date_str] = round(price, 2)
            print(f"    Got {len(data['prices'])} data points.")
        else:
            print(f"    WARNING: No price data in response.")
        
        chunk_start = chunk_end
        time.sleep(API_DELAY)  # Be polite to the API
    
    return prices


def generate_era_data(era_num, start_dt, end_dt, confidence, source_label):
    """Generate rows for an era using CoinGecko data."""
    era_label = {1: "Single-Exchange", 2: "Transition", 3: "Maturity"}
    print(f"Fetching Era {era_num} ({era_label.get(era_num, '')}: "
          f"{start_dt.strftime('%Y-%m-%d')} - {end_dt.strftime('%Y-%m-%d')})...")
    
    prices = fetch_coingecko_range(start_dt, end_dt)
    
    rows = []
    missing_days = []
    current = start_dt
    while current <= end_dt:
        date_str = current.strftime("%Y-%m-%d")
        day_number = (current - GENESIS_DATE).days + 1
        if date_str in prices:
            rows.append({
                "day": str(day_number),
                "date": date_str,
                "btcadp_usd": f"{prices[date_str]:.2f}",
                "confidence": confidence,
                "era": str(era_num),
                "data_source": source_label,
                "status": "provisional",
                "spec_version": "1.0",
            })
        else:
            missing_days.append(date_str)
            # Fill missing days with previous day's price if available
            if rows:
                prev_price = rows[-1]["btcadp_usd"]
                rows.append({
                    "day": str(day_number),
                    "date": date_str,
                    "btcadp_usd": prev_price,
                    "confidence": confidence,
                    "era": str(era_num),
                    "data_source": f"{source_label} (interpolated from previous day)",
                    "status": "provisional",
                    "spec_version": "1.0",
                })
        current += timedelta(days=1)
    
    if missing_days:
        print(f"  WARNING: {len(missing_days)} days had no data and were interpolated.")
        if len(missing_days) <= 10:
            for d in missing_days:
                print(f"    - {d}")
    
    print(f"  Era {era_num}: {len(rows)} days generated.")
    return rows


# ===========================================================================
#  MAIN
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate the BTCADP historical CSV using free public data."
    )
    parser.add_argument(
        "--output", "-o",
        default="btcadp_historical.csv",
        help="Output CSV file path (default: btcadp_historical.csv)"
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help="End date in YYYY-MM-DD format (default: yesterday)"
    )
    args = parser.parse_args()
    
    # Determine end date
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        end_date = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=1)
    
    print("=" * 60)
    print("BTCADP Historical Data Generator")
    print("Specification Version: 1.0")
    print(f"Date Range: {ERA_0_START.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Output: {args.output}")
    print()
    print("NOTE: All values for Eras 1-3 are PROVISIONAL.")
    print("They are derived from aggregated public data, not from")
    print("trade-level exchange data per the BTCADP specification.")
    print("=" * 60)
    print()
    
    all_rows = []
    
    # Era 0: Generated locally (no API needed)
    all_rows.extend(generate_era_0())
    print()
    
    # Era 1: CoinGecko data
    era1_end = min(ERA_1_END, end_date)
    if end_date >= ERA_1_START:
        era1_rows = generate_era_data(
            era_num=1,
            start_dt=ERA_1_START,
            end_dt=era1_end,
            confidence="Single-source",
            source_label="CoinGecko aggregated daily (provisional)"
        )
        all_rows.extend(era1_rows)
        print()
    
    # Era 2: CoinGecko data
    if end_date >= ERA_2_START:
        era2_end = min(ERA_2_END, end_date)
        era2_rows = generate_era_data(
            era_num=2,
            start_dt=ERA_2_START,
            end_dt=era2_end,
            confidence="Reduced",
            source_label="CoinGecko aggregated daily (provisional)"
        )
        all_rows.extend(era2_rows)
        print()
    
    # Era 3: CoinGecko data
    if end_date >= ERA_3_START:
        era3_rows = generate_era_data(
            era_num=3,
            start_dt=ERA_3_START,
            end_dt=end_date,
            confidence="Provisional",
            source_label="CoinGecko aggregated daily (provisional)"
        )
        all_rows.extend(era3_rows)
        print()
    
    # Write CSV
    print(f"Writing {len(all_rows)} rows to {args.output}...")
    with open(args.output, "w", newline="\n", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(all_rows)
    
    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    era_counts = {}
    for row in all_rows:
        era = row["era"]
        era_counts[era] = era_counts.get(era, 0) + 1
    for era in sorted(era_counts.keys()):
        print(f"  Era {era}: {era_counts[era]} days")
    print(f"  TOTAL: {len(all_rows)} days")
    print()
    print(f"Output saved to: {os.path.abspath(args.output)}")
    print()
    print("Next steps:")
    print("  1. Review the CSV for completeness")
    print("  2. Place the CSV alongside the BTCADP website")
    print("  3. As research refines historical values, update the CSV")
    print("     and change 'status' from 'provisional' to 'definitive'")


if __name__ == "__main__":
    main()
