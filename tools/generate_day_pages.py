#!/usr/bin/env python3
"""
BTCADP Per-Day Page Generator
==============================
Reads btcadp_historical.csv and generates a static HTML page for each day.
Each page shows the BTCADP value, provenance, research contributions,
and a structured submission format.

Usage:
  python3 generate_day_pages.py
  python3 generate_day_pages.py --csv btcadp_historical.csv --output-dir days/

The generated pages go into a 'days/' folder alongside index.html.
"""

import argparse
import csv
import os
import html as html_mod
from datetime import datetime, timedelta

# ===========================================================================
#  ERA METADATA
# ===========================================================================

ERA_INFO = {
    "0": {
        "name": "Genesis",
        "range": "January 3, 2009 – July 17, 2010",
        "color": "#555560",
        "method": "$0.00 — No market existed. Defined by specification.",
        "description": "Bitcoin existed but no organized exchange operated. The BTCADP is defined as $0.00 for all days in this era."
    },
    "1": {
        "name": "Single-Exchange Market",
        "range": "July 18, 2010 – February 24, 2014",
        "color": "#e74c3c",
        "method": "Mt. Gox daily VWAP (single-source)",
        "description": "Mt. Gox dominated global Bitcoin trading. Values are derived from Mt. Gox BTC/USD trade data."
    },
    "2": {
        "name": "Transition",
        "range": "February 25, 2014 – December 31, 2017",
        "color": "#f1c40f",
        "method": "Trimmed mean of exchange VWAPs (reduced confidence)",
        "description": "Post-Mt. Gox fragmentation across multiple exchanges. The full BTCADP methodology applies with a smaller exchange set."
    },
    "3": {
        "name": "Maturity",
        "range": "January 1, 2018 – Present",
        "color": "#2ecc71",
        "method": "Trimmed mean of exchange VWAPs (full methodology)",
        "description": "Abundant high-quality data from regulated exchanges. The full BTCADP methodology applies with 15–40 qualifying venues."
    }
}

# ===========================================================================
#  HTML TEMPLATE
# ===========================================================================

def generate_page(row, prev_date, next_date, prev_price, day_number):
    date = row["date"]
    price = float(row["btcadp_usd"])
    confidence = row["confidence"]
    era = row["era"]
    source = row["data_source"]
    status = row["status"]
    spec_version = row["spec_version"]
    era_info = ERA_INFO.get(era, ERA_INFO["3"])

    # Format date nicely
    dt = datetime.strptime(date, "%Y-%m-%d")
    date_display = dt.strftime("%B %d, %Y")
    day_of_week = dt.strftime("%A")

    # Price change from previous day
    change_html = ""
    if prev_price is not None and prev_price > 0 and price > 0:
        change = price - prev_price
        pct = (change / prev_price) * 100
        sign = "+" if change >= 0 else ""
        color = "#2ecc71" if change >= 0 else "#e74c3c"
        arrow = "&#x25B2;" if change >= 0 else "&#x25BC;"
        change_html = f'<span class="price-change" style="color:{color}">{arrow} {sign}${abs(change):,.2f} ({sign}{pct:.2f}%)</span>'

    # Format price
    if price == 0:
        price_display = "$0.00"
    elif price < 1:
        price_display = f"${price:.4f}"
    else:
        price_display = f"${price:,.2f}"

    # Prev/next links
    prev_link = f'<a href="/days/{prev_date}.html" class="nav-link">&larr; {prev_date}</a>' if prev_date else '<span class="nav-link disabled">&larr; Start of record</span>'
    next_link = f'<a href="/days/{next_date}.html" class="nav-link">{next_date} &rarr;</a>' if next_date else '<span class="nav-link disabled">Latest &rarr;</span>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BTCADP — {date} — Bitcoin Average Daily Price</title>
<meta name="description" content="BTCADP for {date_display}: {price_display}. Bitcoin Average Daily Price, Era {era} ({era_info['name']}). {confidence} confidence, {status}.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg-primary: #0a0a0b;
    --bg-secondary: #111114;
    --bg-tertiary: #19191e;
    --bg-hover: #222228;
    --border: #2a2a32;
    --text-primary: #e8e6e3;
    --text-secondary: #8a8a95;
    --text-muted: #555560;
    --orange: #f7931a;
    --orange-dim: rgba(247, 147, 26, 0.15);
    --green: #2ecc71;
    --yellow: #f1c40f;
    --red: #e74c3c;
    --era-color: {era_info['color']};
    --font-display: 'Source Serif 4', Georgia, serif;
    --font-mono: 'JetBrains Mono', 'Courier New', monospace;
    --font-body: 'Source Serif 4', Georgia, serif;
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
    z-index: 0;
  }}

  .container {{
    max-width: 860px;
    margin: 0 auto;
    padding: 0 24px;
    position: relative;
    z-index: 1;
  }}

  /* Toolbar */
  .toolbar {{
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(10,10,11,0.92);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: 12px 0;
  }}

  .toolbar-inner {{
    max-width: 860px;
    margin: 0 auto;
    padding: 0 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}

  .toolbar a {{
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-secondary);
    text-decoration: none;
    letter-spacing: 1px;
    transition: color 0.2s;
  }}

  .toolbar a:hover {{ color: var(--orange); }}

  .day-nav {{
    display: flex;
    gap: 16px;
    align-items: center;
  }}

  .nav-link {{
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-secondary);
    text-decoration: none;
    transition: color 0.2s;
  }}

  .nav-link:hover {{ color: var(--orange); }}
  .nav-link.disabled {{ color: var(--text-muted); cursor: default; }}

  .nav-divider {{ color: var(--border); }}

  /* Header */
  .day-header {{
    padding: 48px 0 32px;
    border-bottom: 1px solid var(--border);
  }}

  .day-label {{
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--orange);
    margin-bottom: 8px;
  }}

  .day-date {{
    font-family: var(--font-display);
    font-size: 40px;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
  }}

  .day-weekday {{
    font-size: 14px;
    color: var(--text-secondary);
    margin-bottom: 16px;
  }}

  .day-number {{
    font-size: 12px;
    color: var(--text-muted);
  }}

  /* Price display */
  .price-section {{
    padding: 32px 0;
    border-bottom: 1px solid var(--border);
  }}

  .price-main {{
    font-family: var(--font-display);
    font-size: 56px;
    font-weight: 700;
    color: var(--orange);
    margin-bottom: 8px;
  }}

  .price-change {{
    font-family: var(--font-mono);
    font-size: 16px;
    display: block;
    margin-bottom: 24px;
  }}

  .meta-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin-top: 24px;
  }}

  .meta-item {{
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 16px;
  }}

  .meta-label {{
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 6px;
  }}

  .meta-value {{
    font-size: 14px;
    color: var(--text-primary);
    font-weight: 500;
  }}

  .era-badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 3px;
    font-size: 12px;
    background: rgba(247,147,26,0.1);
    border: 1px solid var(--era-color);
    color: var(--era-color);
  }}

  .status-badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 3px;
    font-size: 12px;
  }}

  .status-provisional {{ background: rgba(241,196,15,0.1); color: var(--yellow); border: 1px solid var(--yellow); }}
  .status-definitive {{ background: rgba(46,204,113,0.1); color: var(--green); border: 1px solid var(--green); }}

  /* Provenance */
  .provenance {{
    padding: 32px 0;
    border-bottom: 1px solid var(--border);
  }}

  .section-title {{
    font-family: var(--font-display);
    font-size: 22px;
    font-weight: 600;
    margin-bottom: 16px;
  }}

  .provenance-text {{
    font-family: var(--font-body);
    font-size: 16px;
    color: var(--text-secondary);
    line-height: 1.8;
    max-width: 640px;
  }}

  /* Research section */
  .research {{
    padding: 32px 0;
    border-bottom: 1px solid var(--border);
  }}

  .research-empty {{
    background: var(--bg-secondary);
    border: 1px dashed var(--border);
    border-radius: 8px;
    padding: 40px;
    text-align: center;
  }}

  .research-empty p {{
    color: var(--text-muted);
    font-size: 14px;
    margin-bottom: 8px;
  }}

  .research-empty .cta {{
    color: var(--orange);
    font-size: 13px;
  }}

  /* Contribution format */
  .contrib-format {{
    padding: 32px 0;
    border-bottom: 1px solid var(--border);
  }}

  .format-block {{
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 24px;
    margin-top: 16px;
  }}

  .format-block pre {{
    font-family: var(--font-mono);
    font-size: 12px;
    line-height: 1.8;
    color: var(--text-secondary);
    white-space: pre-wrap;
    word-wrap: break-word;
  }}

  .format-block .field {{
    color: var(--orange);
  }}

  .format-block .comment {{
    color: var(--text-muted);
  }}

  .copy-btn {{
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    padding: 6px 16px;
    font-family: var(--font-mono);
    font-size: 11px;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.2s;
    float: right;
    margin-bottom: 12px;
  }}

  .copy-btn:hover {{ border-color: var(--orange); color: var(--orange); }}

  /* Contribution entries */
  .contribution {{
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 16px;
  }}

  .contrib-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
    flex-wrap: wrap;
    gap: 8px;
  }}

  .contrib-author {{
    font-weight: 600;
    color: var(--text-primary);
    font-size: 15px;
  }}

  .contrib-date {{
    font-size: 12px;
    color: var(--text-muted);
  }}

  .contrib-proposed {{
    font-family: var(--font-display);
    font-size: 24px;
    font-weight: 700;
    color: var(--orange);
    margin-bottom: 12px;
  }}

  .contrib-body {{
    font-family: var(--font-body);
    font-size: 15px;
    color: var(--text-secondary);
    line-height: 1.7;
  }}

  .contrib-body h4 {{
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-top: 16px;
    margin-bottom: 8px;
  }}

  .contrib-data {{
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 12px 16px;
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-secondary);
    margin: 8px 0;
    overflow-x: auto;
    white-space: pre;
  }}

  /* Footer */
  footer {{
    padding: 32px 0;
    text-align: center;
  }}

  footer p {{
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.8;
  }}

  footer a {{ color: var(--orange); text-decoration: none; }}
  footer a:hover {{ text-decoration: underline; }}

  @media (max-width: 768px) {{
    .day-date {{ font-size: 28px; }}
    .price-main {{ font-size: 36px; }}
    .meta-grid {{ grid-template-columns: 1fr 1fr; }}
  }}
</style>
</head>
<body>

<div class="toolbar">
  <div class="toolbar-inner">
    <a href="/index.html">&larr; BTCADP Data Explorer</a>
    <div class="day-nav">
      {prev_link}
      <span class="nav-divider">|</span>
      <a href="/index.html" style="color:var(--orange);text-decoration:none;">Home</a>
      <span class="nav-divider">|</span>
      {next_link}
    </div>
  </div>
</div>

<div class="container">

  <div class="day-header">
    <div class="day-label">BTCADP &bull; Daily Record</div>
    <div class="day-date">{date_display}</div>
    <div class="day-weekday">{day_of_week}</div>
    <div class="day-number">Day {day_number:,} of Bitcoin &bull; <a href="/specification.html" style="color:var(--orange);text-decoration:none;">Specification v{spec_version}</a></div>
  </div>

  <div class="price-section">
    <div class="price-main">{price_display}</div>
    {change_html}
    <div class="meta-grid">
      <div class="meta-item">
        <div class="meta-label">Era</div>
        <div class="meta-value"><span class="era-badge">Era {era}: {era_info['name']}</span></div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Confidence</div>
        <div class="meta-value">{confidence}</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Status</div>
        <div class="meta-value"><span class="status-badge status-{status}">{status}</span></div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Data Source</div>
        <div class="meta-value" style="font-size:12px;">{html_mod.escape(source)}</div>
      </div>
    </div>
  </div>

  <div class="provenance">
    <h2 class="section-title">Provenance</h2>
    <p class="provenance-text">{era_info['description']}</p>
    <p class="provenance-text" style="margin-top:12px;">
      {"This value is <strong>definitive</strong> — defined by the BTCADP specification." if status == "definitive" else "This value is <strong>provisional</strong> — derived from aggregated public data, not from trade-level exchange data per the full BTCADP methodology. It will be updated when independent research produces a verified value for this date."}
    </p>
  </div>

  <div class="research">
    <h2 class="section-title">Research Contributions</h2>
    <div id="contributions">
      <div class="research-empty">
        <p>No research contributions have been submitted for this date.</p>
        <p class="cta">Researchers: see the submission format below to contribute a verified BTCADP value for {date_display}.</p>
      </div>
    </div>
  </div>

  <div class="contrib-format">
    <h2 class="section-title">Submission Format</h2>
    <p style="color:var(--text-secondary);font-size:14px;margin-bottom:16px;max-width:640px;">
      To propose a refined BTCADP value for this date, submit the following information to
      <a href="mailto:spec@btcadp.org" style="color:var(--orange);">spec@btcadp.org</a>.
      All submissions must be reproducible per <a href="/specification.html#s7" style="color:var(--orange);">Section 7</a> of the specification.
    </p>
    <div class="format-block">
      <button class="copy-btn" onclick="copyTemplate()">Copy template</button>
      <pre id="template"><span class="comment"># BTCADP Research Submission</span>
<span class="comment"># Date: {date}</span>

<span class="field">researcher:</span>        <span class="comment"># Name or pseudonym, institutional affiliation</span>
<span class="field">date_submitted:</span>    <span class="comment"># YYYY-MM-DD</span>
<span class="field">proposed_btcadp:</span>   <span class="comment"># Your computed value, e.g. 13.45</span>

<span class="field">data_sources:</span>      <span class="comment"># Complete list of data used</span>
  <span class="comment"># - Source name, URL or archive location</span>
  <span class="comment"># - Date range covered</span>
  <span class="comment"># - Known limitations or gaps</span>

<span class="field">exchanges_evaluated:</span>
  <span class="comment"># For each exchange:</span>
  <span class="comment"># - Exchange name</span>
  <span class="comment"># - Trade count</span>
  <span class="comment"># - Hours active (UTC)</span>
  <span class="comment"># - Computed VWAP</span>
  <span class="comment"># - Qualified? (yes/no, reason if no)</span>

<span class="field">methodology:</span>
  <span class="comment"># Step-by-step description of calculation</span>
  <span class="comment"># Note any deviations from standard BTCADP spec</span>
  <span class="comment"># Justify each deviation</span>

<span class="field">computation:</span>
  <span class="comment"># Show the math:</span>
  <span class="comment"># - Individual exchange VWAPs</span>
  <span class="comment"># - Trimming applied</span>
  <span class="comment"># - Final mean calculation</span>
  <span class="comment"># - Rounding</span>

<span class="field">reproducibility:</span>
  <span class="comment"># Link to code, scripts, or detailed procedure</span>
  <span class="comment"># sufficient for independent verification</span>

<span class="field">notes:</span>
  <span class="comment"># Any additional context, caveats, or observations</span></pre>
    </div>
  </div>

  <footer>
    <p><a href="/index.html">Home</a> &bull; <a href="/specification.html">Specification</a> &bull; <a href="/live.html">Live</a> &bull; <a href="/days/index.html">Daily Records</a></p>
    <p style="margin-top:8px;">The BTCADP belongs to no one and benefits everyone.</p>
  </footer>

</div>

<script>
function copyTemplate() {{
  const el = document.getElementById('template');
  const text = el.innerText;
  navigator.clipboard.writeText(text).then(() => {{
    const btn = document.querySelector('.copy-btn');
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = 'Copy template', 2000);
  }});
}}
</script>
</body>
</html>'''


# ===========================================================================
#  MAIN GENERATOR
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate BTCADP per-day HTML pages.")
    parser.add_argument("--csv", default="btcadp_historical.csv", help="Input CSV path")
    parser.add_argument("--output-dir", default="days", help="Output directory for day pages")
    args = parser.parse_args()

    # Read CSV
    print(f"Reading {args.csv}...")
    rows = []
    with open(args.csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    # Sort by date ascending
    rows.sort(key=lambda r: r["date"])
    print(f"  {len(rows)} days loaded.")

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Genesis date for day numbering
    genesis = datetime(2009, 1, 3)

    # Generate pages
    print(f"Generating pages in {args.output_dir}/...")
    for i, row in enumerate(rows):
        prev_date = rows[i - 1]["date"] if i > 0 else None
        next_date = rows[i + 1]["date"] if i < len(rows) - 1 else None
        prev_price = float(rows[i - 1]["btcadp_usd"]) if i > 0 else None

        dt = datetime.strptime(row["date"], "%Y-%m-%d")
        day_number = (dt - genesis).days + 1

        html = generate_page(row, prev_date, next_date, prev_price, day_number)

        filepath = os.path.join(args.output_dir, f"{row['date']}.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

    print(f"  {len(rows)} pages generated.")

    # Generate index for the days directory
    print("Generating days/index.html (year index)...")
    years = {}
    for row in rows:
        yr = row["date"][:4]
        if yr not in years:
            years[yr] = {"count": 0, "first": row["date"], "last": row["date"]}
        years[yr]["count"] += 1
        years[yr]["last"] = row["date"]

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
  <a href="/index.html" class="back">&larr; BTCADP Data Explorer</a>
  <h1><span class="accent">BTCADP</span> Daily Records</h1>
  <p class="subtitle">Every day in Bitcoin's history. Select a year to browse individual daily records.</p>
  <div class="year-grid">
    {"".join(year_links)}
  </div>
</div>
</body>
</html>'''

    with open(os.path.join(args.output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(days_index)

    print()
    print("=" * 50)
    print("DONE")
    print("=" * 50)
    print(f"  {len(rows)} day pages generated in {args.output_dir}/")
    print(f"  Year index generated at {args.output_dir}/index.html")
    print()
    print("Directory structure:")
    print(f"  {args.output_dir}/")
    print(f"  ├── index.html          (year index)")
    print(f"  ├── 2009-01-03.html     (first day)")
    print(f"  ├── 2009-01-04.html")
    print(f"  ├── ...")
    print(f"  └── {rows[-1]['date']}.html  (latest day)")


if __name__ == "__main__":
    main()
