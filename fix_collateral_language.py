"""
fix_collateral_language.py
Finds and replaces incorrect "overcollateralized" language across all HTML files
in the btcadp website folder.

Run from anywhere:
    python fix_collateral_language.py

Update WEBSITE_FOLDER below to match your local path if needed.
"""

import os
import glob

WEBSITE_FOLDER = r"C:\Users\mrjun\OneDrive\Documents\BTCC (Bitcoin Currency)\Website"

# Each tuple is (old text, new text)
REPLACEMENTS = [
    (
        "the system is heavily over-collateralized and every redemption generates profit",
        "Ledger 1 holds more Bitcoin value than the BTCC liability it backs \u2014 every redemption generates profit, and the surplus grows as spot rises"
    ),
    (
        "the system is heavily overcollateralized and every redemption generates profit",
        "Ledger 1 holds more Bitcoin value than the BTCC liability it backs \u2014 every redemption generates profit, and the surplus grows as spot rises"
    ),
    (
        "the system is heavily over-collateralized and every fiat redemption generates profit",
        "Ledger 1 holds more Bitcoin value than the BTCC liability it backs \u2014 every fiat redemption generates profit, and the surplus grows as spot rises"
    ),
    (
        "the system is heavily overcollateralized and every fiat redemption generates profit",
        "Ledger 1 holds more Bitcoin value than the BTCC liability it backs \u2014 every fiat redemption generates profit, and the surplus grows as spot rises"
    ),
    (
        "becomes increasingly over-collateralized, reducing Ledger 2 risk toward zero",
        "accumulates growing surplus, reducing Ledger 2 risk toward zero"
    ),
    (
        "becomes increasingly overcollateralized, reducing Ledger 2 risk toward zero",
        "accumulates growing surplus, reducing Ledger 2 risk toward zero"
    ),
    (
        "Ledger 1 becomes increasingly over-collateralized",
        "Ledger 1 accumulates growing surplus"
    ),
    (
        "Ledger 1 becomes increasingly overcollateralized",
        "Ledger 1 accumulates growing surplus"
    ),
    (
        "so far below BTC spot",
        # This is the worst conflation - the gap between BTCC price and spot is NOT coverage
        # Replace the full misleading sentence pattern
        "PLACEHOLDER_NOT_MATCHED_ALONE"  # handled separately below
    ),
]

# Handle the multi-line conflation sentence separately
MULTILINE_REPLACEMENTS = [
    (
        # The sentence that falsely implies the spot/BTCC price gap = coverage
        "is so far below BTC spot",
        "requires a sustained decline in spot below individual tokens\u2019 issuance prices to create Ledger 1 shortfalls"
    ),
]

def fix_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        original = f.read()

    content = original
    changes = []

    for old, new in REPLACEMENTS:
        if old == "PLACEHOLDER_NOT_MATCHED_ALONE":
            continue
        if old in content:
            content = content.replace(old, new)
            changes.append(f"  FIXED: ...{old[:60]}...")

    for old, new in MULTILINE_REPLACEMENTS:
        if old in content:
            content = content.replace(old, new)
            changes.append(f"  FIXED: ...{old[:60]}...")

    if content != original:
        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"\n[CHANGED] {os.path.basename(filepath)}")
        for c in changes:
            print(c)
    else:
        print(f"[  OK   ] {os.path.basename(filepath)} — no changes needed")

def main():
    if not os.path.isdir(WEBSITE_FOLDER):
        print(f"ERROR: Folder not found:\n  {WEBSITE_FOLDER}")
        print("\nUpdate WEBSITE_FOLDER at the top of this script to match your path.")
        return

    html_files = glob.glob(os.path.join(WEBSITE_FOLDER, "**", "*.html"), recursive=True)

    if not html_files:
        print(f"No HTML files found in:\n  {WEBSITE_FOLDER}")
        return

    print(f"Scanning {len(html_files)} HTML file(s) in:\n  {WEBSITE_FOLDER}\n")

    for filepath in sorted(html_files):
        fix_file(filepath)

    print("\nDone.")

if __name__ == "__main__":
    main()
