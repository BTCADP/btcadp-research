import csv
import time
import requests
from datetime import datetime, timezone

API_KEY = "CG-J3JAeCZyNhrfWTUqpW1PDuPX"
HEADERS = {"x-cg-demo-api-key": API_KEY}
BASE = "https://api.coingecko.com/api/v3"

def fetch_price(date_str):
    # CoinGecko history endpoint uses DD-MM-YYYY format
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    cg_date = dt.strftime("%d-%m-%Y")
    url = f"{BASE}/coins/bitcoin/history"
    params = {"date": cg_date, "localization": "false"}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            price = data["market_data"]["current_price"]["usd"]
            return round(price, 2)
        else:
            print(f"    HTTP {resp.status_code}")
            return None
    except Exception as e:
        print(f"    ERROR: {e}")
        return None

with open("btcadp_historical.csv", "r") as f:
    rows = list(csv.DictReader(f))

fieldnames = list(rows[0].keys())
to_fix = [r for r in rows if "interpolated" in r.get("data_source", "")]
print(f"Found {len(to_fix)} rows to fix.")

fixed = 0
for row in to_fix:
    d = row["date"]
    print(f"  {d}...", end=" ", flush=True)
    price = fetch_price(d)
    if price:
        row["btcadp_usd"] = f"{price:.2f}"
        row["data_source"] = "CoinGecko aggregated daily (provisional)"
        print(f"${price:,.2f}")
        fixed += 1
    else:
        print("skipped")
    time.sleep(6)

with open("btcadp_historical.csv", "w", newline="\n", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

print(f"\nDone. Fixed {fixed} of {len(to_fix)} rows.")
