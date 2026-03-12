# Repository Setup Guide

This guide walks through setting up the BTCADP GitHub repository from scratch, including automated daily updates.

## 1. Initial Repository Setup

If you've just created an empty repository on GitHub:

```bash
# Clone your new empty repo
git clone https://github.com/YOUR_USERNAME/btcadp-research-repo.git
cd btcadp-research-repo

# Copy all repository files into it (from the provided zip or download)
# The structure should look like:
#
#   .github/
#     workflows/
#       daily-update.yml        ← automated daily pipeline
#   .gitattributes              ← enforces LF line endings
#   btcadp_historical.csv       ← the dataset
#   contributions/
#   days/                       ← generated day pages (created by scripts)
#   specification/
#   tools/
#     btcadp_generate.py        ← full rebuild script
#     btcadp_update_daily.py    ← incremental daily updater
#     generate_day_pages.py     ← HTML page generator
#   CONTRIBUTING.md
#   LICENSE
#   README.md
#   SETUP.md                    ← this file

# Initial commit
git add -A
git commit -m "initial: BTCADP repository with automated daily updates"
git push origin main
```

## 2. Generate the Day Pages (First Time)

Before automation starts, generate the full set of day pages from the CSV:

```bash
pip install requests
cd tools
python3 generate_day_pages.py --csv ../btcadp_historical.csv --output-dir ../days/
cd ..
git add days/
git commit -m "data: generate initial day pages"
git push
```

This creates ~5,900 HTML files in the `days/` directory.

## 3. Backfill Any Missing Dates

If the CSV doesn't cover through yesterday:

```bash
cd tools
python3 btcadp_update_daily.py --csv ../btcadp_historical.csv --days-dir ../days/
cd ..
git add btcadp_historical.csv days/
git commit -m "data: backfill to present"
git push
```

## 4. Verify Automation

The GitHub Actions workflow (`.github/workflows/daily-update.yml`) runs automatically every day at 01:30 UTC. To verify it's working:

1. Go to your repository on GitHub
2. Click the **Actions** tab
3. You should see "Daily BTCADP Update" in the list
4. Click **Run workflow** → **Run workflow** to trigger a manual test run
5. Watch the run complete — it should either add new data or report "Already up to date"

## 5. Hosting on btcadp.org

To serve the repository as a website on btcadp.org, you have two options:

### Option A: GitHub Pages

1. Go to **Settings** → **Pages**
2. Under "Source", select **Deploy from a branch**
3. Select `main` branch and `/ (root)` folder
4. Click **Save**
5. Configure your custom domain (btcadp.org) under "Custom domain"
6. Add a CNAME record in your DNS pointing btcadp.org to `YOUR_USERNAME.github.io`

This serves the repository directly as a static site. The `index.html`, `days/` folder, and `specification.html` at the root will be served as-is.

### Option B: External hosting (Netlify, Cloudflare Pages, etc.)

Connect your GitHub repository as the source. These platforms deploy automatically on every push, so the daily workflow commit will trigger a rebuild.

## Troubleshooting

**Workflow not running:** Check that GitHub Actions is enabled in your repository settings (Settings → Actions → General → "Allow all actions").

**Rate limiting from CoinGecko:** The free API allows ~10-12 requests/minute. The daily updater only needs 1-2 requests, so this shouldn't be an issue. For a full rebuild, the script handles 429 responses with automatic backoff.

**Manual backfill:** Use the workflow_dispatch trigger with a `backfill_from` date, or run locally:
```bash
python3 tools/btcadp_update_daily.py --backfill-from 2025-03-10
```

**Stale data after errors:** If the workflow fails (CoinGecko downtime, etc.), missing days will be picked up automatically on the next successful run — the script always checks for gaps.
