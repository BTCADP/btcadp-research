# BTCADP — Bitcoin Average Daily Price

A universal, reproducible, and institution-independent standard for daily Bitcoin valuation.

## What Is the BTCADP?

The BTCADP (Bitcoin Average Daily Price) establishes a universal reference point for Bitcoin's daily value.

It does this by computing Volume-Weighted Average Prices (VWAP) independently for each qualifying exchange, then aggregating them using a 25% trimmed mean. The result is a single daily price that is resistant to manipulation by any individual exchange and reproducible by anyone with access to the same trade data.

The full methodology is defined in the [BTCADP Specification v1.0](https://btcadp.org/specification.html).

## What Is This Repository?

This is the canonical home for:

- **`btcadp_historical.csv`** — The official BTCADP dataset, covering every day from January 3, 2009 (the Bitcoin genesis block) to the present
- **Research contributions** — Verified refinements to historical BTCADP values, submitted by independent researchers
- **Tools** — Scripts to generate data, build the website, and reproduce calculations

## Current Status

The dataset contains two types of values:

| Status | Meaning |
|--------|---------|
| **Definitive** | Defined by the specification (Era 0: $0.00) |
| **Provisional** | Derived from aggregated public data, not yet verified from trade-level exchange data |

All values for Eras 1, 2, and 3 are currently provisional. The research community is invited to produce definitive values — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Historical Eras

| Era | Dates | Method | Status |
|-----|-------|--------|--------|
| 0 | Jan 3, 2009 – Jul 17, 2010 | $0.00 (no market existed) | Definitive |
| 1 | Jul 18, 2010 – Feb 24, 2014 | Mt. Gox VWAP (single-source) | Provisional — researchers needed |
| 2 | Feb 25, 2014 – Dec 31, 2017 | Trimmed mean of exchange VWAPs | Provisional — researchers needed |
| 3 | Jan 1, 2018 – Present | Trimmed mean of exchange VWAPs | Provisional — researchers needed |

Eras 1 and 2 are where research contributions will have the greatest impact. The data challenges are genuinely interesting: reconstructing trade records from defunct exchanges, detecting bot activity in Mt. Gox data, and validating prices across a fragmented early market.

## How to Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full process. The short version:

1. Fork this repository
2. Do the research (gather data, compute BTCADP values, document everything)
3. Add your work to the `contributions/` folder
4. Open a pull request
5. Respond to community review

Every contribution must include: data sources, methodology, transparency records, and reproducible results.

## Website

The BTCADP is published at [btcadp.org](https://btcadp.org), which provides:

- An interactive price history chart
- A searchable daily data table
- The full specification
- A per-day research page for every day in Bitcoin's history
- Live indicative pricing from exchange WebSocket feeds

## Contact

spec@btcadp.org

## License

This repository and all contributions are released into the public domain under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).

The BTCADP belongs to no one and benefits everyone.
