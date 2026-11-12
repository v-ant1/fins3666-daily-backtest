# SEC earnings clock QA

## Scope and source universe

Collected SEC Form 8-K and 8-K/A filings explicitly tagged with Item 2.02, from acceptance dates 2020-06-01 through 2026-10-31. The requested `r5_D7/LINKS.csv` did not exist in this workspace, so the fallback set is the first 50 S&P 500 companies ranked by market capitalization on 2026-11-06 (the latest published list available when built); ranking and component source: [S&P 500 companies by market value](https://www.sectoralpha.in/sp-500-stocks). SEC CIK and filing metadata came from [company_tickers_exchange.json](https://www.sec.gov/files/company_tickers_exchange.json) and [EDGAR submissions API](https://www.sec.gov/edgar/sec-api-documentation).

Dow membership is point-in-time: 30 components at the window start, with S&P DJI changes applied effective 2020-08-31, 2024-02-26, and 2024-11-08. The 2020 release replaced XOM/PFE/RTX with CRM/AMGN/HON ([S&P DJI](https://press.spglobal.com/2020-08-24-Salesforce-com-Amgen-and-Honeywell-International-Set-to-Join-Dow-Jones-Industrial-Average)); Amazon replaced WBA from 2024-02-26 ([S&P DJI PDF](https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20240220-1470711/1470711_djiadjtawbajblu-feb2024.pdf)); NVDA and SHW replaced INTC and DOW from 2024-11-08 ([S&P DJI](https://press.spglobal.com/2024-11-01-NVIDIA-and-Sherwin-Williams-Set-to-Join-Dow-Jones-Industrial-Average-Vistra-to-Join-Dow-Jones-Utility-Average?asPDF=1)). RTX is the active issuer/ticker during this window, including the predecessor Dow constituent's final months. WBA was already delisted by the market-cap snapshot, so its historical Dow observations use CIK 0001618921 from the [SEC submissions index](https://data.sec.gov/submissions/CIK0001618921.json). Exxon appears under predecessor CIK 0000034088 and current CIK 0002115436; both are retained as XOM because the SEC ticker directory reflects the newer reporting CIK, while historical filings remain under the predecessor ([predecessor](https://data.sec.gov/submissions/CIK0000034088.json), [current](https://data.sec.gov/submissions/CIK0002115436.json)).

The combined universe has 64 unique CIKs (50 fallback tickers plus the Dow identities, with overlap collapsed by CIK). For firms selected only as Dow members, filings are included only while that CIK is in the Dow; fallback top-50 firms are retained throughout the full requested window. `dow_member_on_acceptance_date` in the event CSV distinguishes those cases. The extraction reads filing-index metadata only; it does not download or inspect prices or returns.

## Classification and schema

`earnings_clock.csv` contains 1649 qualifying event filings: 897 BMO, 20 intraday, and 732 AMC. `acceptance_timestamp_utc` is SEC's timestamp; `acceptance_timestamp_et` is converted with Python `America/New_York` timezone rules, including daylight saving. Classification uses local acceptance time: before 09:30 = BMO; 09:30 to before 16:00 = intraday; 16:00 or later = AMC. This is a mechanical timestamp classification, not a claim about the scheduled earnings-release time.

Columns are `ticker`, `cik`, `company_name`, `acceptance_timestamp_et`, `acceptance_timestamp_utc`, `classification`, `form`, `items`, `filing_date`, `report_date`, `accession_number`, `universe_source`, `dow_member_on_acceptance_date`, and `source_url`. The source URL resolves to the primary EDGAR filing document (or the filing text when the index lacks a primary-document name). Items are taken from the SEC submissions `items` field, split on commas and matched exactly to `2.02`; no document text keyword matching was used. The source for every event is linked in its CSV row.

## Coverage by firm and year

Counts are qualifying Item 2.02 filings. Years 2020 and 2026 are partial (2020 starts June 1; 2026 ends October 31). A dash means the firm was outside the point-in-time Dow membership and outside the fallback top-50 universe that year; zero means in-scope but no qualifying filing was indexed.

| Ticker | CIK | Inclusion source | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| AAPL | 0000320193 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 3 |
| ABBV | 0001551152 | S&P500_top50_market_cap_2026-11-06 | 3 | 4 | 8 | 8 | 8 | 8 | 8 |
| AMAT | 0000006951 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 3 | 4 | 3 |
| AMD | 0000002488 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 5 | 4 | 4 | 4 | 3 |
| AMGN | 0000318154 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 3 |
| AMZN | 0001018724 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| ANET | 0001596532 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 3 |
| AVGO | 0001730168 | S&P500_top50_market_cap_2026-11-06 | 3 | 4 | 4 | 4 | 4 | 4 | 3 |
| AXP | 0000004962 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| BA | 0000012927 | Dow_PIT | 2 | 4 | 4 | 4 | 5 | 4 | 4 |
| BAC | 0000070858 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 5 | 4 | 4 |
| BRK-B | 0001067983 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 3 | 4 | 4 | 4 | 3 |
| CAT | 0000018230 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 5 | 4 | 4 |
| COST | 0000909832 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 3 |
| CRM | 0001108524 | Dow_PIT | 1 | 4 | 4 | 4 | 4 | 4 | 3 |
| CRWD | 0001535527 | S&P500_top50_market_cap_2026-11-06 | 3 | 4 | 4 | 4 | 4 | 5 | 3 |
| CSCO | 0000858877 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 3 |
| CVX | 0000093410 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 5 | 5 | 4 | 5 |
| DIS | 0001744489 | Dow_PIT | 2 | 4 | 4 | 4 | 4 | 4 | 3 |
| DOW | 0001751788 | Dow_PIT | 2 | 4 | 4 | 5 | 4 | - | - |
| GE | 0000040545 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 5 | 4 | 4 | 4 |
| GOOGL | 0001652044 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 5 | 4 | 4 | 4 |
| GS | 0000886982 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 4 | 4 | 4 | 4 | 4 | 4 | 5 |
| HD | 0000354950 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 3 |
| HON | 0000773840 | Dow_PIT | 2 | 4 | 4 | 6 | 6 | 5 | 5 |
| IBM | 0000051143 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 3 | 5 | 4 | 4 | 4 | 4 | 5 |
| INTC | 0000050863 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 5 | 4 | 4 | 4 | 4 | 4 |
| JNJ | 0000200406 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 5 | 5 | 4 | 4 |
| JPM | 0000019617 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| KO | 0000021344 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| LIN | 0001707925 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| LLY | 0000059478 | S&P500_top50_market_cap_2026-11-06 | 3 | 5 | 6 | 4 | 4 | 5 | 4 |
| LRCX | 0000707549 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| MA | 0001141391 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| MCD | 0000063908 | Dow_PIT | 3 | 4 | 4 | 4 | 4 | 4 | 3 |
| META | 0001326801 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| MMM | 0000066740 | Dow_PIT | 2 | 5 | 6 | 5 | 4 | 4 | 4 |
| MRK | 0000310158 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 5 | 4 | 4 | 4 | 4 |
| MS | 0000895421 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| MSFT | 0000789019 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| MU | 0000723125 | S&P500_top50_market_cap_2026-11-06 | 2 | 5 | 4 | 4 | 4 | 4 | 3 |
| NFLX | 0001065280 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| NKE | 0000320187 | Dow_PIT | 3 | 4 | 4 | 4 | 4 | 4 | 4 |
| NVDA | 0001045810 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 5 | 4 | 4 | 4 | 3 |
| ORCL | 0001341439 | S&P500_top50_market_cap_2026-11-06 | 3 | 4 | 5 | 4 | 4 | 4 | 3 |
| PANW | 0001327567 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 3 |
| PFE | 0000078003 | Dow_PIT | 1 | - | - | - | - | - | - |
| PG | 0000080424 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| PLTR | 0001321655 | S&P500_top50_market_cap_2026-11-06 | 1 | 5 | 4 | 4 | 4 | 4 | 3 |
| PM | 0001413329 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| RTX | 0000101829 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| SHW | 0000089800 | Dow_PIT | - | - | - | - | 0 | 4 | 4 |
| TMO | 0000097745 | S&P500_top50_market_cap_2026-11-06 | 3 | 5 | 4 | 4 | 4 | 4 | 4 |
| TRV | 0000086312 | Dow_PIT | 3 | 4 | 4 | 5 | 4 | 4 | 4 |
| TSLA | 0001318605 | S&P500_top50_market_cap_2026-11-06 | 4 | 8 | 8 | 8 | 8 | 8 | 8 |
| TXN | 0000097476 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| UNH | 0000731766 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| V | 0001403161 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| VZ | 0000732712 | Dow_PIT | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| WBA | 0001618921 | Dow_PIT | 2 | 5 | 4 | 4 | 1 | - | - |
| WFC | 0000072971 | S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 4 |
| WMT | 0000104169 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 3 |
| XOM | 0000034088 | Dow_PIT+S&P500_top50_market_cap_2026-11-06 | 2 | 4 | 4 | 4 | 4 | 4 | 2 |
| XOM | 0002115436 | S&P500_top50_market_cap_2026-11-06 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |

## Rebuild

Run from the workspace root: `python A2/pivot_research/r4_L4/data/build_earnings_clock.py`. Requests use a generic project User-Agent and a 0.20-second minimum interval (at most five SEC requests per second). The script reads only SEC ticker/submission metadata and writes the event CSV and this report; no price files are accessed.
