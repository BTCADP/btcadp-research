# Tools

## Automated Daily Updates (GitHub Actions)

The repository includes a GitHub Actions workflow that runs daily at 01:30 UTC. It fetches the previous day's price, appends it to the CSV, generates the new day page, and commits the result automatically.

**Setup:** No configuration needed — the workflow runs automatically once the `.github/workflows/daily-update.yml` file is in your repository. GitHub Actions is enabled by default on new repositories.

**Manual trigger:** Go to Actions → "Daily BTCADP Update" → "Run workflow". You can optionally specify a `backfill_from` date to fill in any gaps.

## btcadp_update_daily.py

Incremental updater for daily automation. Reads the existing CSV, identifies missing dates, fetches only what's needed from CoinGecko, appends new rows, and generates only the new day pages.

```
pip install requests
python3 btcadp_update_daily.py                              # Append yesterday
python3 btcadp_update_daily.py --backfill-from 2025-03-10   # Fill gaps from a date
python3 btcadp_update_daily.py --skip-pages                 # CSV only, no HTML
```

Typically completes in under 30 seconds for a single day.

## btcadp_generate.py

Full historical rebuild. Fetches the entire Bitcoin price history from CoinGecko and generates the complete CSV from scratch. Use this for initial setup or to rebuild after a specification change.

```
pip install requests
python3 btcadp_generate.py --output btcadp_historical.csv
```

Takes 15–30 minutes due to API rate limits. Generates provisional values for all eras.

## generate_day_pages.py

Generates per-day HTML pages for the BTCADP website from the CSV. Called automatically by `btcadp_update_daily.py` for incremental updates, or run standalone for a full rebuild.

```
python3 generate_day_pages.py --csv btcadp_historical.csv --output-dir days/
```

Takes about 10–30 seconds to generate all 5,900+ pages.

## Notes

**Line endings:** All scripts output Unix-style line endings (LF). If the CSV was previously generated on Windows with CRLF endings, running `btcadp_generate.py` or `btcadp_update_daily.py` will normalize to LF.

**Confidence labels:** The `confidence` column currently uses "Provisional" for Era 3 data sourced from CoinGecko. Per Section 4.5 of the BTCADP specification, the valid confidence flags are: Full, Reduced, Low, Single-source, Defined, and No data — which require knowing how many exchanges qualified each day. Since CoinGecko provides aggregated data without exchange-level breakdowns, the true confidence tier cannot be determined for provisional values. This will resolve naturally as researchers produce definitive values from trade-level data.
