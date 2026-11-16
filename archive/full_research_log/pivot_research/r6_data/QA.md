# S&P 500 point-in-time data QA

## Deliverables and coverage

`sp500_pit_roster.csv` contains **623 dated membership intervals for 622 distinct tickers**, covering 2020-06-01 through 2026-10-30. The reconstructed roster has 505 listed securities on 2020-06-01 and 503 on 2026-10-30. Dates use half-open intervals (`effective_from` included, `effective_to_exclusive` excluded); a member is effective on the S&P change date, before that day's trading session.

`sp500_ohlcv_dev.parquet` preserves the original pull: **774,939 daily rows for 568 of 622 member tickers**. The gap-fill produced `sp500_ohlcv_gapfill.parquet` with **723 rows for three recovered tickers**, and `sp500_ohlcv_dev_gapfilled.parquet` combines both files with **775,662 rows for 571 tickers**. All observed rows span 2020-06-01 through 2026-10-30; a boundary check found no rows outside this development window. Columns are `date`, PIT `ticker`, raw `open`, `high`, `low`, `close`, `adj_close`, and `volume`. Each row is retained only inside that ticker's point-in-time membership interval. No returns, signals or other outcome measures were computed.

The recovered ticker coverage is:

| PIT ticker | Yahoo source symbol | Rows | First date | Last date | Lineage reason |
|---|---|---:|---|---|---|
| ADS | BFH | 15 | 2020-06-01 | 2020-06-19 | Alliance Data Systems changed its name and ticker to Bread Financial/BFH on 2022-04-04; same issuer and share line. |
| FBHS | FBIN | 644 | 2020-06-01 | 2022-12-16 | Fortune Brands Home & Security changed its name and ticker to FBIN on 2022-12-15; same share line. |
| SATS | ECHO | 64 | 2026-03-23 | 2026-06-23 | EchoStar changed its ticker from SATS to ECHO on 2026-06-24; same issuer and share line. |

The point-in-time roster bounds, rather than all rows in the alias symbol history, determine which dates are retained. `gapfill_manifest.csv` records source ticker, URL, row count, coverage and lineage note; `gapfill_errors.csv` records attempts without usable rows. Rebuild with `python r6_data\\build_gapfill.py` from `A2\\pivot_research`.

Lineage dates were checked against issuer or SEC sources: [Alliance Data's SEC filing](https://www.sec.gov/Archives/edgar/data/1101215/000110121524000041/R11.htm) states its ticker changed from ADS to BFH on April 4, 2022; [Fortune Brands' investor FAQ](https://ir.fbin.com/investor-faqs) gives December 15, 2022 for FBHS to FBIN; and [EchoStar's issuer announcement](https://ir.echostar.com/news-releases/news-release-details/echostar-changing-stocker-ticker-sats-echo-marking-companys-next) gives June 24, 2026 for SATS to ECHO.

Yahoo Finance returned no usable bars for 54 symbols; the rebuild log is in `download_errors.csv`. The missing tickers are:

`ABMD, ADS, ALXN, ANSS, ATVI, AVB, CDAY, CERN, CMA, CTLT, CTRA, CTXS, CXO, DAY, DFS, DISCA, DISCK, DISH, DRE, EA, ETFC, FBHS, FLIR, FRC, GPS, HBI, HES, HFC, HOLX, INFO, IPG, JNPR, JWN, K, KSU, KVUE, LEG, MRO, MXIM, NBL, NLSN, PBCT, PXD, QRVO, SATS, SBNY, SEE, SIVB, TIF, TWTR, VAR, WBA, WBD, XLNX`.

The remaining gaps in the combined file are **51 tickers**: `ABMD, ALXN, ANSS, ATVI, AVB, CDAY, CERN, CMA, CTLT, CTRA, CTXS, CXO, DAY, DFS, DISCA, DISCK, DISH, DRE, EA, ETFC, FLIR, FRC, GPS, HBI, HES, HFC, HOLX, INFO, IPG, JNPR, JWN, K, KSU, KVUE, LEG, MRO, MXIM, NBL, NLSN, PBCT, PXD, QRVO, SBNY, SEE, SIVB, TIF, TWTR, VAR, WBA, WBD, XLNX`.

These gaps include acquired, merged, renamed or otherwise delisted tickers (for example ABMD, ATVI, EA, SIVB, TWTR and WBA), and Yahoo symbols that returned an empty chart response. Yahoo 404/empty responses are recorded as provider coverage failures; this does not establish that every missing symbol was legally delisted. Rows for unavailable tickers are not imputed or replaced with acquirer prices. The point-in-time roster preserves all constituent names, but the combined parquet still has **51 historical symbols without price rows**, leaving survivorship and coverage gaps.

StockAnalysis was evaluated but not used for automated extraction: its help page says it offers no programmatic interface and that its displayed licensed data cannot be redistributed programmatically ([StockAnalysis API access FAQ](https://stockanalysis.com/help/faq/api-access/)). Stooq's CSV URL returned a browser JavaScript verification page, so the run did not attempt to circumvent it. The Yahoo endpoint returned data for three issuer-confirmed same-share-line ticker aliases; Yahoo responses remained empty/unusable for the other 51 missing names.

## Membership sources and cross-checks

The baseline is the current component table on [Wikipedia's S&P 500 company list](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies), reversed through the dated entries in [Wikipedia's historical components table](https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500) to the June 2020 boundary and then replayed forward. For changes during this window, the change table has 132 effective-date rows; 130 cite a direct S&P Dow Jones Indices release. Examples include the [June 2020 changes](https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20200612-1164959/1164959_correctedjune2020migrshuf.pdf), [September 2024 rebalance](https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20240906-1474143/1474143_septembershuffle546.pdf), [March 2025 rebalance](https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20250307-1477251/1477251_march2025rebalance1500.pdf), [March 2026 rebalance](https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20260306-1482263/1482263_march2026rebalance1546.pdf), and [October 30, 2026 change](https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20261030-1485650/1485650_kvue-ramp546.pdf). These release URLs are attached to affected membership intervals in the roster.

Two history-table entries are symbol changes, not constituent substitutions: WLTW→WTW on 2022-01-10 and CDAY→DAY on 2024-02-01. The current component list had later issuer symbols that the change table did not fully carry through, so two issuer-confirmed ticker transitions were added to preserve point-in-time labels: SATS→ECHO on 2026-06-24 ([EchoStar release](https://ir.echostar.com/news-releases/news-release-details/echostar-changing-stocker-ticker-sats-echo-marking-companys-next)) and EQR→VMRK on 2026-08-18 ([Vivmark Residential release](https://investors.vivmarkresidential.com/news-events/press-releases/detail/113/vivmark-residential-launches-as-one-of-the-countrys-leading-real-estate-companies)). These are ticker lineage changes, not extra index seats. Yahoo's current-symbol history was used for EQR/VMRK and WLTW/WTW where it returned continuous bars; the bars are labeled with the member ticker effective on each date.

The `sp100_member_at_2026_10_30` field flags membership in the S&P 100 snapshot at the end of this project window. The source page lists 101 securities because Alphabet has two share classes; the field is an endpoint classification, not a historical S&P 100 membership series. See the [S&P 100 constituent page](https://en.wikipedia.org/wiki/S%26P_100) and the [S&P DJI index overview](https://www.spglobal.com/spdji/en/indices/equity/sp-100/).

## Price source and boundaries

Bars are from Yahoo Finance's public daily chart endpoint, the source used by yfinance. The builder requests only `period1=2020-06-01` through an exclusive `period2=2026-10-31` boundary, at no more than four requests per second, and retries transient failures. It does not request any pre-2020-06 price data. OHLC are unadjusted vendor fields; adjusted close is retained as a separate raw field. Splits and corporate actions were not used to calculate any derived series.

## Rebuild command

From `A2\pivot_research` (Python packages: `requests`, `beautifulsoup4`, `pandas`, `lxml`, `pyarrow`):

```powershell
python r6_data\build_sp500_pit.py
```

The original roster command recreates `sp500_pit_roster.csv`, `sp500_ohlcv_dev.parquet`, and `download_errors.csv`. The original OHLCV file remains an incomplete provider pull with 54 missing tickers; use the separate gap-fill overlay and current 51-symbol residual list above when checking coverage.

The gap-fill command is `python r6_data\\build_gapfill.py`; it recreates `sp500_ohlcv_gapfill.parquet`, `sp500_ohlcv_dev_gapfilled.parquet`, `gapfill_manifest.csv`, and `gapfill_errors.csv`. It requests only the development date range and only mapped aliases for symbols absent from the original file. The original parquet is not overwritten.


## Dow early-window OHLCV gap fill (development only)

`r6_C1/INPUT_QA.md` records a Dow component-bar gap from the start of its development window through December 2020: for the point-in-time Dow roster effective 2020-11-27, only WBA had existing component rows before the other constituents' bars began on 2021-01-04. The missing members below were recovered for the 2020-11-27 through 2020-12-31 window. WBA is not duplicated because its early-window rows already existed.

The gap fill is `dow_dev_gapfill.parquet`. It contains raw daily `open`, `high`, `low`, `close`, `adj_close`, and `volume` fields, keyed by `date` and point-in-time `ticker`; it contains no imputed rows. Each recovered ticker has 24 rows spanning 2020-11-27 through 2020-12-31, matching the early-window session coverage described in the C1 input audit.

| PIT ticker | Rows | First date | Last date |
|---|---:|---|---|
| AAPL | 24 | 2020-11-27 | 2020-12-31 |
| AMGN | 24 | 2020-11-27 | 2020-12-31 |
| AXP | 24 | 2020-11-27 | 2020-12-31 |
| BA | 24 | 2020-11-27 | 2020-12-31 |
| CAT | 24 | 2020-11-27 | 2020-12-31 |
| CRM | 24 | 2020-11-27 | 2020-12-31 |
| CSCO | 24 | 2020-11-27 | 2020-12-31 |
| CVX | 24 | 2020-11-27 | 2020-12-31 |
| DIS | 24 | 2020-11-27 | 2020-12-31 |
| DOW | 24 | 2020-11-27 | 2020-12-31 |
| GS | 24 | 2020-11-27 | 2020-12-31 |
| HD | 24 | 2020-11-27 | 2020-12-31 |
| HON | 24 | 2020-11-27 | 2020-12-31 |
| IBM | 24 | 2020-11-27 | 2020-12-31 |
| INTC | 24 | 2020-11-27 | 2020-12-31 |
| JNJ | 24 | 2020-11-27 | 2020-12-31 |
| JPM | 24 | 2020-11-27 | 2020-12-31 |
| KO | 24 | 2020-11-27 | 2020-12-31 |
| MCD | 24 | 2020-11-27 | 2020-12-31 |
| MMM | 24 | 2020-11-27 | 2020-12-31 |
| MRK | 24 | 2020-11-27 | 2020-12-31 |
| MSFT | 24 | 2020-11-27 | 2020-12-31 |
| NKE | 24 | 2020-11-27 | 2020-12-31 |
| PG | 24 | 2020-11-27 | 2020-12-31 |
| TRV | 24 | 2020-11-27 | 2020-12-31 |
| UNH | 24 | 2020-11-27 | 2020-12-31 |
| V | 24 | 2020-11-27 | 2020-12-31 |
| VZ | 24 | 2020-11-27 | 2020-12-31 |
| WMT | 24 | 2020-11-27 | 2020-12-31 |

**Source and request boundary:** Yahoo Finance public chart endpoint, the source used by yfinance: `https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?period1=1606453200&period2=1609477200&interval=1d&events=div%2Csplits`. The request covered 2020-11-27 00:00 through 2021-01-01 00:00 America/New_York (exclusive end) and no earlier dates. The ticker set was determined from the C1 point-in-time Dow SIC-membership intervals active on 2020-11-27, less the already-present WBA rows in the development component panel. The resulting 29 tickers all returned rows; missing data were not imputed.

**Scope:** this parquet is an overlay for the initial 2020-11-27 to 2020-12-31 gap; it does not replace or rewrite the later Dow component panel. It is development data only, and contains no observations before 2020-06-01.

## S&P 500 earnings clock (2020-06 to 2026-10)

The point-in-time S&P 500 EDGAR Item 2.02 panel is in `earnings_clock_sp500.csv`; detailed source, timestamp rules, and year totals are in `earnings_clock_sp500_QA.md`. It contains 13,443 filing events across 603 issuers with observed events, from 613 mapped CIK identities and 622 ticker identities; all 613 submission metadata queries succeeded. `earnings_clock_sp500_coverage.csv` reports event counts per issuer and year, active membership tickers, and membership calendar days; filing rows retain SEC acceptance time in ET and the linked EDGAR document URL. The builder observes SEC fair access at five requests per second. No prices or returns were read.
