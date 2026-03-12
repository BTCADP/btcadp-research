#!/usr/bin/env python3
"""
BTCADP Daily Incremental Updater
==================================
Appends new days to an existing btcadp_historical.csv and generates
only the missing day pages. Designed to run in CI (GitHub Actions)
on a daily schedule.

Unlike btcadp_generate.py which rebuilds the entire dataset (15-30 min),
this script only fetches the days that are missing from the CSV (typically
just yesterday), taking a few seconds per day.

Usage:
  python btcadp_update_daily.py                              # Append yesterday
  python btcadp_update_daily.py --backfill-from 2025-03-01   # Fill gaps from date
  python btcadp_update_daily.py --csv data.csv --days-dir pages/

Requirements:
  pip install requests
"""

import argparse
import csv
import io
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
#  CONSTANTS (must match btcadp_generate.py)
# ===========================================================================

GENESIS_DATE = datetime(2009, 1, 3, tzinfo=timezone.utc)

ERA_BOUNDARIES = [
    # (start, end, era_num, confidence, source_label)
    (datetime(2009, 1, 3,  tzinfo=timezone.utc), datetime(2010, 7, 17, tzinfo=timezone.utc), 0, "Defined",       "Specification-defined (no market existed)"),
    (datetime(2010, 7, 18, tzinfo=timezone.utc), datetime(2014, 2, 24, tzinfo=timezone.utc), 1, "Single-source", "CoinGecko aggregated daily (provisional)"),
    (datetime(2014, 2, 25, tzinfo=timezone.utc), datetime(2017, 12, 31, tzinfo=timezone.utc), 2, "Reduced",      "CoinGecko aggregated daily (provisional)"),
    (datetime(2018, 1, 1,  tzinfo=timezone.utc), None,                                       3, "Provisional",  "CoinGecko aggregated daily (provisional)"),
]

CSV_HEADERS = [
    "day", "date", "btcadp_usd", "confidence",
    "era", "data_source", "status", "spec_version",
]

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_MARKET_CHART_RANGE = f"{COINGECKO_BASE}/coins/bitcoin/market_chart/range"
API_DELAY = 6  # seconds between CoinGecko requests


# ===========================================================================
#  HELPERS
# ===========================================================================

def get_era_info(dt):
    """Return (era_num, confidence, source_label, status) for a given date."""
    for start, end, era_num, confidence, source_label in ERA_BOUNDARIES:
        end_check = end or datetime(9999, 12, 31, tzinfo=timezone.utc)
        if start <= dt <= end_check:
            status = "definitive" if era_num == 0 else "provisional"
            return era_num, confidence, source_label, status
    raise ValueError(f"No era defined for {dt.strftime('%Y-%m-%d')}")


def read_existing_csv(csv_path):
    """Read existing CSV, return list of rows and set of dates present."""
    rows = []
    dates = set()
    if not os.path.exists(csv_path):
        return rows, dates

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Strip any \r from values (handles CRLF source files)
            cleaned = {k.strip(): v.strip() for k, v in row.items()}
            rows.append(cleaned)
            dates.add(cleaned["date"])
    return rows, dates


def fetch_coingecko_prices(start_dt, end_dt):
    """
    Fetch daily prices from CoinGecko for a date range.
    Returns dict: { "YYYY-MM-DD": price_float, ... }
    """
    prices = {}
    from_ts = int(start_dt.timestamp())
    to_ts = int(end_dt.timestamp()) + 86400  # include end date

    # Fetch in 365-day chunks
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
        print(f"  Fetching CoinGecko {start_str} to {end_str}...")

        retries = 0
        while retries < 3:
            try:
                resp = requests.get(COINGECKO_MARKET_CHART_RANGE, params=params, timeout=30)
                if resp.status_code == 429:
                    wait = 60 * (retries + 1)
                    print(f"  Rate limited. Waiting {wait}s (attempt {retries + 1}/3)...")
                    time.sleep(wait)
                    retries += 1
                    continue
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.exceptions.RequestException as e:
                retries += 1
                if retries >= 3:
                    print(f"  ERROR: Failed after 3 attempts: {e}")
                    chunk_start = chunk_end
                    break
                print(f"  Retry {retries}/3 after error: {e}")
                time.sleep(10)
        else:
            chunk_start = chunk_end
            continue

        if "prices" in data:
            for timestamp_ms, price in data["prices"]:
                dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                date_str = dt.strftime("%Y-%m-%d")
                prices[date_str] = round(price, 2)
            print(f"    Got {len(data['prices'])} data points.")
        else:
            print(f"    WARNING: No price data in response.")

        chunk_start = chunk_end
        if chunk_start < to_ts:
            time.sleep(API_DELAY)

    return prices


def write_csv(csv_path, rows):
    """Write the full CSV with Unix line endings (LF)."""
    with open(csv_path, "w", newline="\n", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


# ===========================================================================
#  DAY PAGE GENERATOR (imported logic from generate_day_pages.py)
# ===========================================================================

# We import the page generator if available, otherwise define a minimal version
def generate_day_pages(csv_path, days_dir, only_dates=None):
    """
    Generate HTML day pages. If only_dates is provided, only those dates
    (plus their neighbors for nav links) are regenerated.
    """
    # Import the full generator
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, tools_dir)

    try:
        import generate_day_pages as gen
    except ImportError:
        print("  WARNING: generate_day_pages.py not found. Skipping page generation.")
        return

    # Read CSV
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    rows.sort(key=lambda r: r["date"])

    os.makedirs(days_dir, exist_ok=True)

    genesis = datetime(2009, 1, 3)

    # Determine which pages to generate
    if only_dates:
        # Also regenerate neighbors (they need updated nav links)
        dates_to_gen = set(only_dates)
        date_to_idx = {r["date"]: i for i, r in enumerate(rows)}
        for d in list(only_dates):
            idx = date_to_idx.get(d)
            if idx is not None:
                if idx > 0:
                    dates_to_gen.add(rows[idx - 1]["date"])
                if idx < len(rows) - 1:
                    dates_to_gen.add(rows[idx + 1]["date"])
        indices = [date_to_idx[d] for d in dates_to_gen if d in date_to_idx]
    else:
        indices = range(len(rows))

    count = 0
    for i in indices:
        row = rows[i]
        prev_date = rows[i - 1]["date"] if i > 0 else None
        next_date = rows[i + 1]["date"] if i < len(rows) - 1 else None
        prev_price = float(rows[i - 1]["btcadp_usd"]) if i > 0 else None

        dt = datetime.strptime(row["date"], "%Y-%m-%d")
        day_number = (dt - genesis).days + 1

        html = gen.generate_page(row, prev_date, next_date, prev_price, day_number)
        filepath = os.path.join(days_dir, f"{row['date']}.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        count += 1

    print(f"  Generated {count} day page(s).")

    # Regenerate the year index
    years = {}
    for row in rows:
        yr = row["date"][:4]
        if yr not in years:
            years[yr] = {"count": 0, "first": row["date"], "last": row["date"]}
        years[yr]["count"] += 1
        years[yr]["last"] = row["date"]

    # Build index (reuse the template from generate_day_pages.py)
    year_links = []
    for yr in sorted(years.keys()):
        info = years[yr]
        year_links.append(
            f'<a href="{info["first"]}.html" class="year-link">'
            f'<span class="yr">{yr}</span>'
            f'<span class="count">{info["count"]} days</span></a>'
        )

    days_index = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BTCADP — Daily Records Index</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg-primary: #0a0a0b;
    --bg-secondary: #111114;
    --bg-tertiary: #19191e;
    --border: #2a2a32;
    --text-primary: #e8e6e3;
    --text-secondary: #8a8a95;
    --text-muted: #555560;
    --orange: #f7931a;
    --font-display: 'Source Serif 4', Georgia, serif;
    --font-mono: 'JetBrains Mono', 'Courier New', monospace;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: var(--bg-primary);
    color: var(--text-primary);
    font-family: var(--font-mono);
    font-size: 14px;
    line-height: 1.6;
    min-height: 100vh;
  }}
  body::before {{
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(rgba(247,147,26,0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(247,147,26,0.02) 1px, transparent 1px);
    background-size: 60px 60px;
    pointer-events: none;
  }}
  .container {{
    max-width: 860px;
    margin: 0 auto;
    padding: 60px 24px;
    position: relative;
    z-index: 1;
  }}
  .back {{ font-size: 12px; color: var(--text-secondary); text-decoration: none; letter-spacing: 1px; }}
  .back:hover {{ color: var(--orange); }}
  h1 {{
    font-family: var(--font-display);
    font-size: 36px;
    font-weight: 700;
    margin: 24px 0;
  }}
  h1 .accent {{ color: var(--orange); }}
  .subtitle {{ font-size: 14px; color: var(--text-secondary); margin-bottom: 40px; }}
  .year-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
  }}
  .year-link {{
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 24px 16px;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    text-decoration: none;
    transition: all 0.2s;
  }}
  .year-link:hover {{ border-color: var(--orange); background: var(--bg-tertiary); }}
  .yr {{ font-family: var(--font-display); font-size: 24px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }}
  .year-link:hover .yr {{ color: var(--orange); }}
  .count {{ font-size: 12px; color: var(--text-muted); }}
</style>
</head>
<body>
<div class="container">
  <a href="../index.html" class="back">&larr; BTCADP Data Explorer</a>
  <h1><span class="accent">BTCADP</span> Daily Records</h1>
  <p class="subtitle">Every day in Bitcoin's history. Select a year to browse individual daily records.</p>
  <div class="year-grid">
    {"".join(year_links)}
  </div>
</div>
</body>
</html>'''

    index_path = os.path.join(days_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(days_index)
    print(f"  Updated {index_path}")


# ===========================================================================
#  MAIN
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Incrementally update BTCADP data and day pages."
    )
    parser.add_argument(
        "--csv", default="btcadp_historical.csv",
        help="Path to existing BTCADP CSV (default: btcadp_historical.csv)"
    )
    parser.add_argument(
        "--days-dir", default="days",
        help="Output directory for day pages (default: days/)"
    )
    parser.add_argument(
        "--backfill-from", default=None,
        help="Backfill from this date (YYYY-MM-DD) to yesterday"
    )
    parser.add_argument(
        "--skip-pages", action="store_true",
        help="Skip HTML page generation (CSV update only)"
    )
    args = parser.parse_args()

    # -----------------------------------------------------------------------
    #  Determine what needs fetching
    # -----------------------------------------------------------------------
    yesterday = (
        datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        - timedelta(days=1)
    )

    existing_rows, existing_dates = read_existing_csv(args.csv)

    if args.backfill_from:
        start_dt = datetime.strptime(args.backfill_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    elif existing_rows:
        last_date_str = max(existing_dates)
        last_dt = datetime.strptime(last_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        start_dt = last_dt + timedelta(days=1)
    else:
        print("ERROR: CSV is empty and no --backfill-from specified.")
        sys.exit(1)

    if start_dt > yesterday:
        print(f"Already up to date (last entry: {start_dt - timedelta(days=1):%Y-%m-%d}, "
              f"yesterday: {yesterday:%Y-%m-%d}).")
        return

    # Find missing dates in the range
    missing_dates = []
    current = start_dt
    while current <= yesterday:
        date_str = current.strftime("%Y-%m-%d")
        if date_str not in existing_dates:
            missing_dates.append(current)
        current += timedelta(days=1)

    if not missing_dates:
        print("No missing dates. Already up to date.")
        return

    print("=" * 60)
    print("BTCADP Incremental Update")
    print(f"Missing dates: {len(missing_dates)}")
    print(f"Range: {missing_dates[0]:%Y-%m-%d} to {missing_dates[-1]:%Y-%m-%d}")
    print("=" * 60)

    # -----------------------------------------------------------------------
    #  Fetch prices for missing dates
    # -----------------------------------------------------------------------
    # All missing dates are in Era 3 (post-2018) for any practical run
    fetch_start = missing_dates[0]
    fetch_end = missing_dates[-1]

    prices = fetch_coingecko_prices(fetch_start, fetch_end)

    # -----------------------------------------------------------------------
    #  Build new rows
    # -----------------------------------------------------------------------
    new_rows = []
    new_date_strs = []

    for dt in missing_dates:
        date_str = dt.strftime("%Y-%m-%d")
        day_number = (dt - GENESIS_DATE).days + 1
        era_num, confidence, source_label, status = get_era_info(dt)

        if era_num == 0:
            price_str = "0.00"
            status = "definitive"
        elif date_str in prices:
            price_str = f"{prices[date_str]:.2f}"
        else:
            # Interpolate from previous day
            if new_rows:
                price_str = new_rows[-1]["btcadp_usd"]
            elif existing_rows:
                price_str = existing_rows[-1]["btcadp_usd"]
            else:
                print(f"  WARNING: No price for {date_str} and no previous day. Skipping.")
                continue
            source_label = f"{source_label} (interpolated from previous day)"
            print(f"  WARNING: {date_str} interpolated (no CoinGecko data).")

        row = {
            "day": str(day_number),
            "date": date_str,
            "btcadp_usd": price_str,
            "confidence": confidence,
            "era": str(era_num),
            "data_source": source_label,
            "status": status,
            "spec_version": "1.0",
        }
        new_rows.append(row)
        new_date_strs.append(date_str)

    if not new_rows:
        print("No new data retrieved. Nothing to update.")
        return

    print(f"\n  New rows to append: {len(new_rows)}")
    for r in new_rows[:5]:
        print(f"    {r['date']}: ${r['btcadp_usd']}")
    if len(new_rows) > 5:
        print(f"    ... and {len(new_rows) - 5} more")

    # -----------------------------------------------------------------------
    #  Merge and write CSV
    # -----------------------------------------------------------------------
    all_rows = existing_rows + new_rows
    all_rows.sort(key=lambda r: r["date"])

    write_csv(args.csv, all_rows)
    print(f"\n  CSV updated: {args.csv} ({len(all_rows)} total rows)")

    # -----------------------------------------------------------------------
    #  Generate day pages (incremental)
    # -----------------------------------------------------------------------
    if not args.skip_pages:
        print("\nGenerating day pages...")
        generate_day_pages(args.csv, args.days_dir, only_dates=new_date_strs)

    # -----------------------------------------------------------------------
    #  Summary
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("UPDATE COMPLETE")
    print("=" * 60)
    print(f"  Added {len(new_rows)} day(s): {new_date_strs[0]} to {new_date_strs[-1]}")
    print(f"  CSV total: {len(all_rows)} rows")
    last_price = new_rows[-1]['btcadp_usd']
    print(f"  Latest price: ${float(last_price):,.2f}")


if __name__ == "__main__":
    main()
