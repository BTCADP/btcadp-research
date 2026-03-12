# Contributing to the BTCADP

The BTCADP belongs to no one and benefits everyone. This repository is the canonical home for BTCADP historical data and the research contributions that refine it.

## How It Works

1. **You do the research.** Pick a date (or range of dates), gather trade-level data, and compute the BTCADP using the methodology in the [specification](https://btcadp.org/specification.html).
2. **You submit a pull request.** Your findings, data sources, methodology, and code go into this repository where anyone can review them.
3. **The community reviews.** Other researchers can comment, verify, challenge, or corroborate your work — all in public.
4. **The value is updated.** Once a submission is reviewed and accepted, the canonical CSV is updated and the website reflects the new value.

Every step is public, timestamped, and auditable. No step requires trust in any individual or institution.

---

## What Can Be Contributed

### Refined daily BTCADP values
The primary contribution. If you have trade-level data for dates currently marked as "provisional" in the CSV, you can compute and submit a more accurate value.

### New exchange data for existing dates
If you have data from an exchange that wasn't included in a previous calculation, submit it. Even if it doesn't change the final value, it strengthens the transparency record.

### Methodology improvements
If you find that a filter or threshold in the specification doesn't work well for a particular era or dataset, document your findings. This informs future versions of the spec.

### Bug reports or ambiguities
If two independent implementations of the spec produce different results for the same input data, that's a spec bug. Report it.

---

## Submission Requirements

Every submission must include the following, per [Section 7.3](https://btcadp.org/specification.html#s7) of the specification:

### 1. Data Sources
A complete description of the trade-level data used:
- Source name and location (URL, archive, API endpoint)
- Date range covered
- Format (CSV, JSON, database dump, etc.)
- Known limitations, gaps, or quality issues
- For archived or leaked data: provenance and why you trust it

### 2. Methodology
A precise description of the calculation:
- Which filters from the spec were applied and in what order
- Any deviations from the standard methodology, with justification
- Detailed enough that someone else can replicate your work without contacting you

### 3. Transparency Records
For each date in your submission:
- Every exchange evaluated
- Each exchange's trade count, hours active, and computed VWAP
- Which exchanges qualified and which were excluded (with the specific filter they failed)
- The aggregation method used (trimmed mean, median, or simple mean) and the final computation

### 4. Reproducible Results
- The computed BTCADP value(s)
- Code or scripts sufficient for independent verification
- Instructions to run the code, including dependencies

If any of these four elements are missing, the submission is incomplete and will not be merged.

---

## How to Submit

### Step 1: Fork this repository

Click the "Fork" button at the top of this page.

### Step 2: Create your contribution folder

```
contributions/
└── YYYY-MM-DD/                    # The date you're submitting for
    ├── submission.md              # Your write-up (see template below)
    ├── transparency_record.csv    # Exchange-level data
    ├── code/                      # Scripts to reproduce your calculation
    │   ├── compute_btcadp.py      # (or whatever language)
    │   └── README.md              # How to run it
    └── data/                      # Raw data or references to it
        └── README.md              # Where the data came from
```

For date ranges, name the folder with the range: `2011-06-01_to_2011-06-30/`

### Step 3: Write your submission

Use this template for `submission.md`:

```markdown
# BTCADP Research Submission

## Date(s)
[The date or date range this submission covers]

## Researcher
[Name or pseudonym. Institutional affiliation if applicable.]

## Proposed BTCADP Value(s)
[Your computed value(s), e.g., "2011-06-15: $17.63"]

## Current Value
[The current provisional value in the CSV for comparison]

## Data Sources
[Complete description per the requirements above]

## Methodology
[Step-by-step description of your calculation]
[Note any deviations from the standard spec and why]

## Computation
[Show the math]
[Individual exchange VWAPs, trimming applied, final mean, rounding]

## Transparency Record
[Summary here; full data in transparency_record.csv]

## Reproducibility
[How to run your code to verify these results]

## Notes
[Any additional context, caveats, or observations]
```

### Step 4: Open a pull request

Push your changes to your fork and open a pull request against this repository. In the PR description, briefly summarize what you're submitting and for which date(s).

### Step 5: Respond to review

Other contributors and maintainers may ask questions, request clarification, or attempt to reproduce your results. Respond to feedback in the PR discussion. This is the peer review process.

---

## Review Criteria

Submissions are evaluated on:

- **Completeness.** Are all four required elements present?
- **Reproducibility.** Can an independent party follow your methodology and arrive at the same result?
- **Data quality.** Are the data sources credible and well-documented?
- **Methodological soundness.** Does the calculation follow the spec (or clearly justify deviations)?
- **Transparency.** Is the full exchange-level data available for audit?

Submissions are NOT evaluated on:
- Who the researcher is
- What institution they're affiliated with
- Whether the proposed value is higher or lower than the current one

The data and methodology speak for themselves.

---

## When Multiple Submissions Disagree

It is possible — even expected — that two researchers will compute different values for the same date using different data sources or methodological adaptations. When this happens:

1. Both submissions remain visible in the repository
2. The community discusses the differences in the PR threads
3. The stronger submission (better data, more complete methodology, independently verified) is accepted
4. The other submission remains as a documented alternative

If the disagreement cannot be resolved, both values may be noted in the transparency record with an explanation of the discrepancy. This is intellectual honesty, not failure.

---

## Repository Structure

```
btcadp-research/
├── README.md                       # Project overview
├── CONTRIBUTING.md                 # This file
├── LICENSE                         # Public domain / CC0
├── btcadp_historical.csv           # The canonical BTCADP dataset
├── specification/
│   └── BTCADP_Specification_v1_0.md  # The specification
├── contributions/
│   ├── 2011-06-15/                 # Example: single date
│   │   ├── submission.md
│   │   ├── transparency_record.csv
│   │   ├── code/
│   │   └── data/
│   └── 2013-01-01_to_2013-12-31/  # Example: date range
│       ├── submission.md
│       ├── transparency_record.csv
│       ├── code/
│       └── data/
└── tools/
    ├── btcadp_generate.py          # Data generation script
    └── generate_day_pages.py       # Website page generator
```

---

## Becoming a Maintainer

This repository starts with a single maintainer. Over time, researchers who demonstrate consistent, high-quality contributions may be invited to become co-maintainers with the ability to review and merge pull requests.

Maintainers are expected to:
- Review submissions objectively based on the criteria above
- Never merge their own submissions without independent review
- Prioritize the integrity of the data over any other consideration

The goal is a self-sustaining community of maintainers so that the BTCADP does not depend on any single person.

---

## Code of Conduct

- Evaluate contributions on their merits, not on who submitted them
- Be constructive in reviews — the goal is better data, not winning arguments
- Assume good faith unless evidence suggests otherwise
- Document everything — if it's not in the PR, it didn't happen

---

## License

All contributions to this repository are released into the public domain under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). By submitting a pull request, you agree that your contribution may be freely used, modified, and distributed by anyone for any purpose.

The BTCADP belongs to no one and benefits everyone.
