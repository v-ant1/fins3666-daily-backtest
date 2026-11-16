# SEC insider transactions: development data QA

## Scope and source

This folder contains the SEC quarterly Insider Transactions data sets for **2020Q2 through 2026Q3** and a filtered non-derivative transaction panel for S&P 500 issuers. The SEC describes these as quarterly, as-filed extracts of the XML-based Forms 3, 4 and 5; its documentation defines the `SUBMISSION`, `REPORTINGOWNER`, and `NONDERIV_TRANS` tables and the transaction fields used here ([SEC data-set page](https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets), [SEC data dictionary](https://www.sec.gov/files/insider_transactions_readme.pdf)). SEC code `P` means open-market or private purchase and `S` means open-market or private sale; the source does not distinguish private from open-market within those codes.

Raw official SEC ZIPs are in [`raw/`](raw/). `form4_dev.parquet` contains **141,195** unique as-filed non-derivative P/S transaction rows, matched to **595 issuer CIKs** and PIT S&P ticker intervals by CIK on the reported transaction date. The transaction-date range is **2020-06-01 to 2026-09-30**; filing dates in this extracted set run from **2020-06-01 to 2026-09-30**. The roster is `../sp500_pit_roster.csv`; ticker-to-CIK mapping uses the SEC-sourced `../sp500_sic_panel.csv`, which assigns one CIK per roster ticker. Transactions without an active PIT S&P membership interval for that issuer CIK on `transaction_date` are excluded (45,520 candidate P/S rows); this handles pre-entry and post-exit filings without look-ahead.

**2020Q2 boundary:** the SEC archive is both the first requested development archive and the final quarter named in the older availability-only range. It is retained and parsed only for records whose filing date and transaction date are both on/after **2020-06-01**; no earlier transaction or filing rows appear in the output. Archives from 2009Q1 through 2020Q1 were checked by HTTP `HEAD` for status and content length only, and their response bodies were not read. The requested 2009Q1-2020Q2 archive availability check is in [`archive_availability.csv`](archive_availability.csv), including the 2020Q2 size check.

## Output schema

`form4_dev.parquet` columns: `transaction_id, accession_number, archive_quarter, document_type, issuer_cik, ticker, issuer_trading_symbol, issuer_name, reporting_owners_json, owner_roles, is_officer, is_director, is_ten_percent_owner, transaction_date, filing_date, filing_lag_days, transaction_code, transaction_form_type, security_title, acquired_disposed_code, shares, price_usd, value_usd`. Reporting-owner identities and roles are kept as JSON in `reporting_owners_json`; `owner_roles` and the officer, director, and ten-percent-owner flags are convenience fields. Shares, price, and value come from the SEC's transaction table; missing values remain null, with no fill. `price_usd` is the reported insider transaction price, not a downloaded market price. Filing lag is calendar days (`filing_date - transaction_date`); no returns or price histories were accessed.

Counts treat each unique SEC accession plus non-derivative transaction surrogate key as one transaction row. SEC amendments are retained as filed; if an amendment repeats a transaction, original and amended filing rows can both occur. Owner rows are combined into one JSON field per transaction, so joint filers do not multiply transaction counts. The per-issuer output lists the full counts; the year-by-issuer output disaggregates it by transaction year.

## Purchase and sale counts by transaction year

| Transaction year | P purchases | S sales | P/S rows |
|---:|---:|---:|---:|
| 2020 | 510 | 12,214 | 12,724 |
| 2021 | 856 | 28,163 | 29,019 |
| 2022 | 1,204 | 17,993 | 19,197 |
| 2023 | 915 | 13,963 | 14,878 |
| 2024 | 774 | 21,900 | 22,674 |
| 2025 | 1,450 | 20,532 | 21,982 |
| 2026 | 912 | 19,809 | 20,721 |

Counts by year are assigned using `transaction_date`; 2020 begins on June 1. 2026 is partial through the latest available archive (2026Q3). The complete counts by issuer and issuer-year are in [`counts_by_issuer.csv`](counts_by_issuer.csv) and [`counts_by_issuer_year.csv`](counts_by_issuer_year.csv); annual totals are in [`counts_by_year.csv`](counts_by_year.csv).

## Filing lag distribution

| Calendar-day lag | P/S transaction rows |
|---:|---:|
| negative | 5 |
| 0 | 14,535 |
| 1 | 48,399 |
| 2 | 41,279 |
| 3 | 11,335 |
| 4-5 | 23,831 |
| 6-10 | 532 |
| 11-30 | 232 |
| 31-90 | 262 |
| 91-365 | 488 |
| >365 | 297 |

The lag distribution uses the same transaction rows and calendar-day definition. Negative lags are retained and identified rather than corrected. Exact lag values are in [`filing_lag_distribution.csv`](filing_lag_distribution.csv).

## Archive availability and reproducibility

All **26** requested development archives from 2020Q2 through 2026Q3 are stored as raw ZIPs; individual download sizes and the number of issuer submissions selected before transaction parsing are in [`dev_archive_manifest.csv`](dev_archive_manifest.csv). All **46** HEAD checks for 2009Q1-2020Q2 returned HTTP 200 with a `Content-Length`; per-quarter URLs and byte sizes are in `archive_availability.csv`. SEC paths have changed over time, so the recorded official-page links are preserved in that manifest. The SEC page says the archive is quarterly and notes that documents accepted after 5:30 p.m. Eastern on quarter-end's last business day roll into the next posting.

Rebuild the panel and count tables from this directory with:

```powershell
python r6_data\insider\build_form4_dev.py
```

The script parses the 2020Q2 development archive only after filtering the filing and transaction dates to 2020-06-01 or later, then parses the remaining development-quarter ZIPs through 2026Q3. It never opens the older 2009Q1-2020Q1 availability-check ZIPs. The SEC cautions that the data sets are as-filed extracts, can contain inaccuracies or extraction errors, and are not substitutes for reviewing individual filings.
