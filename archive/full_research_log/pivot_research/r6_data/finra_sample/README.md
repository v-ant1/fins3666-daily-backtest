# FINRA sample files and coverage checks

This folder contains a limited, recent-date feasibility pull for the R6 FINRA flow proposals. No price, return, or investment outcome data were downloaded or inspected.

## Reg SHO daily short-sale volume

- Raw source: FINRA's public daily files at `https://cdn.finra.org/equity/regsho/daily/CNMSshvolYYYYMMDD.txt`.
- Raw samples: 43 daily files from 2026-09-01 through 2026-10-30 (21 September dates and 22 October dates; weekdays with files available).
- `regsho_manifest.csv` records each sample date, source filename, row count, and coverage of the project's pinned 30-stock Dow roster. All 30 roster names appear in each sample.
- `regsho_rowcounts.csv` records row counts only.
- Historical availability check: the 2010-01-04 file exists and has 738 data rows after excluding its header/trailer. This was a row-count-only check: no historical symbols, volumes, prices, or returns were read or saved.

## OTC non-ATS weekly summary

- Raw source: FINRA's weekly OTC non-ATS summary API, filtered to the project's 30-stock Dow roster.
- Raw samples: week starts 2026-08-24 and 2026-08-31, saved under `otc_weekly/`.
- `otc_weekly_manifest.csv` records 459 and 461 rows respectively; both files include all 30 roster names.
- The sampled reports provide symbol, firm, share quantity, and trade count. They do not identify buy/sell direction or whether the activity is retail.
- FINRA weekly OTC summary reporting began in 2016, so it has no 2010 sample availability.

The raw data are unmodified apart from selecting the two OTC sample weeks and project-roster symbols. The manifest files document scope and coverage; they are not outcome analyses.
