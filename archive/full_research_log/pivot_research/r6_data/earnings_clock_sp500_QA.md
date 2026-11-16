# S&P 500 earnings clock QA

Prepared 2026-11-11. The event file contains EDGAR filing metadata only; no prices, returns, or price-derived fields were accessed.

## Scope and method

`earnings_clock_sp500.csv` covers point-in-time S&P 500 membership from 2020-06-01 through 2026-10-30. It includes Form 8-K and 8-K/A filings whose SEC submissions metadata lists Item 2.02 and whose EDGAR acceptance date falls inside the issuer's S&P membership interval. The roster is `r6_data/sp500_pit_roster.csv` (623 membership intervals, 622 unique ticker identities); CIKs come from `r6_data/sp500_sic_panel.csv`, which has one CIK mapping for each roster ticker. Issuer identity is deduplicated by CIK; the CSV retains the active ticker on each acceptance date. Filings outside membership intervals are excluded.

Acceptance times are SEC submission timestamps converted to `America/New_York` with daylight-saving rules. Classification is mechanical: before 09:30 ET = BMO; 09:30 to before 16:00 ET = intraday; 16:00 ET or later = AMC. This labels filing acceptance time, not scheduled earnings-release time. SEC's submissions `items` index field is split into comma-separated codes and matched to `2.02`; filing bodies were not downloaded or searched. Each event links to the SEC primary filing document, or the filing text if the primary document is absent.

## Coverage

The output contains 13,443 qualifying filings across 603 filing issuers and 613 point-in-time issuer CIKs, covering 622 ticker identities. Classifications: 7,185 BMO, 415 intraday, and 5,843 AMC. SEC submission metadata queries succeeded for 613 of 613 CIKs; failed queries are enumerated in `earnings_clock_sp500_fetch_status.csv`. `earnings_clock_sp500_coverage.csv` gives per-issuer/per-year event counts, active ticker(s), membership calendar days, and query status. Years 2020 and 2026 are partial (2020 begins June 1; the latest S&P roster interval ends October 31 exclusive).

| Year | Item 2.02 filings | BMO | Intraday | AMC |
|---:|---:|---:|---:|---:|
| 2020 | 1074 | 577 | 46 | 451 |
| 2021 | 2083 | 1123 | 78 | 882 |
| 2022 | 2086 | 1114 | 71 | 901 |
| 2023 | 2089 | 1125 | 60 | 904 |
| 2024 | 2113 | 1118 | 66 | 929 |
| 2025 | 2107 | 1129 | 51 | 927 |
| 2026 | 1891 | 999 | 43 | 849 |

A zero means the SEC submissions query succeeded and no qualifying Item 2.02 filing was indexed during membership days; it does not mean the company made no earnings announcement. The counts describe EDGAR filing-index metadata, not all issuer earnings announcements.

## Sources and fair access

The point-in-time roster and SEC SIC-derived CIK mappings are project inputs. Filing timestamps and Item 2.02 codes are from the [SEC EDGAR submissions API](https://www.sec.gov/edgar/sec-api-documentation); issuer index URLs use `https://data.sec.gov/submissions/CIK{cik}.json`. The builder identifies as `FINS3666 SEC metadata research project contact research@example.edu` and spaces SEC requests at least 0.20 seconds apart (five requests per second, below the 10 requests/second limit).

## Rebuild

From `A2/pivot_research`, run:

```powershell
python r6_data/build_earnings_clock_sp500.py
```

The builder writes the event CSV, per-issuer/year coverage, fetch status, and this report. No price data is opened.
