# S2 pooled S&P index flow — source gate

**Tag:** L-IDX3. **Step 1: not passed; stop here.** No price data were requested, no event-return trial was registered, and no existing file was changed.

## Free source coverage checked

The Wikipedia historical-components page for the S&P 400 has dated change rows through the requested periods. The S&P 600 historical-components page has dated rows from late 2019 onward, but no 2016–2018 rows. The S&P Global press-release archive is free and contains dated releases with stated effective dates and index changes (including 2016 examples), but the archive is a collection of individual releases; this check did not establish an exhaustive row-level 2016–2018 S&P 600 census with announcement date, effective date, ticker, and from/to index. Consequently, full-window free-list coverage is not confirmed to the required standard.

Sources: [Historical components of the S&P 400](https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_400), [Historical components of the S&P 600](https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_600), [S&P Global press-release archive](https://press.spglobal.com/index.php?category=784), and a dated [2016 S&P release example](https://press.spglobal.com/2016-09-30-Dave-Busters-Entertainment-Set-to-Join-the-S-P-SmallCap-600).

## Observed annual Wikipedia change-row counts

Counts are dated rows in each historical-components table, filtered by effective date through 2026-10-30. They are source-table rows, not a reconciled count of unique pooled trade events. A dash means the S&P 600 table does not cover that year, not zero changes.

| Effective year | S&P 400 rows | S&P 600 rows |
|---:|---:|---:|
| 2016 | 53 | — |
| 2017 | 54 | — |
| 2018 | 50 | — |
| 2019 | 51 | 4 |
| 2020 | 46 | 51 |
| 2021 | 52 | 58 |
| 2022 | 45 | 60 |
| 2023 | 60 | 94 |
| 2024 | 41 | 77 |
| 2025 | 33 | 73 |
| 2026 through Oct. 30 | 28 | 74 |

The 2020 counts are whole-calendar-year table rows and are not split at the requested Nov. 27 development boundary. The missing earlier S&P 600 table coverage and unverified reconciliation from release archive to a complete, row-level list prevent defensible counts for both requested windows. Steps 2–4 were not run; no development prices or 2016–2020 price coverage were accessed.
