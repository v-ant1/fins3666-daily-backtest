# Dividend input coverage QA (development panel)

Dividend event metadata was queried for all unique symbols in `r6_data/sp500_pit_roster.csv`. **Fixed schedule definition: use the ex-dividend date as the schedule proxy**, consistent with the prior-ex-date dividend-month signal design; Nasdaq declaration, record and payment dates are supplementary metadata only, not the formation schedule. Yahoo Finance dividend events provide ex-dates and per-share cash amounts; matching Nasdaq issuer-history rows add those supplementary dates where available. Only dividend action fields were selected and saved; no price or return observations were used.

- PIT roster symbols queried: 622
- Dividend rows with ex-dates 2020-06-01 through 2026-10-31: 10772
- Symbols with at least one returned dividend event: 449
- Rows whose ticker is PIT S&P 500 member on ex-date: 9786
- Nasdaq matched dividend rows: 2513; associated payment dates inside the development window: 2504
- Yahoo history errors/empty responses: 40; explicit no-dividend-event responses: 133
- SHA-256 `dividends_dev.parquet`: `9b64ee81b5f000bab09eadbc2a95a3f5fa3fac503ebc8721d8ed179682c5eda8`

## Rows by ex-date year

| Year | Dividend rows |
|---:|---:|
| 2020 | 928 |
| 2021 | 1609 |
| 2022 | 1676 |
| 2023 | 1695 |
| 2024 | 1715 |
| 2025 | 1740 |
| 2026 | 1409 |

## Sealed-era boundary and limitations

The requested 2019-06 through 2020-05 history is HOLDOUT-ERA and was not included in the development panel. It predates the permitted pre-2020-06 Dow boundary and overlaps the sealed holdout era for this study; do not use it absent a coordinator ruling. Thus this panel begins 2020-06-01 and does not provide a full prior-12-month calendar at the first formation date. A full 12-month lookback from this safe input boundary is available only from 2021-06-01 onward; earlier formation dates must be marked insufficient-history, not treated as having no payouts. Separate Dow 2009-2020 dividend-only records were staged under `sealed_holdout_dow/dividends/` after coordinator authorization and remain sealed; they were not used to fill this development panel.

Nasdaq payment-date coverage is partial; empty/null Nasdaq responses in `manifest.csv` mean unavailable through that endpoint, not zero dividends. The roster begins 2020-06-01, so the file is not proof of a complete all-market S&P payout calendar. Per-share amounts are not aggregate cash-flow amounts without share counts. Ticker membership on ex-date and pay date is tagged from the staged right-open PIT roster intervals. No prices, returns, forward outcomes or holdout records were joined.
