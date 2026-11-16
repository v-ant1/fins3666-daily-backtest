# ETF data and sector mapping QA

Prepared 2026-11-11. This is a data inventory and coverage check; no returns or other performance statistics were computed.

## Daily ETF bars

`etf_ohlcv_dev.parquet` contains Yahoo Finance daily bars for the requested 19 symbols, 2020-06-01 through 2026-10-30. The parquet has 30,666 ticker-date rows (1,614 per ETF), with `date`, `ticker`, `open`, `high`, `low`, `close`, `adj_close`, and `volume`. Prices and volume are vendor-reported daily fields; no adjustment or imputation was applied by this build.

| ETF | Development rows | First date | Last date | Holdout timestamp rows* | Holdout first | Holdout last |
|---|---:|---|---|---:|---|---|
| XLB | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| XLC | 1,614 | 2020-06-01 | 2026-10-30 | 598 | 2018-06-19 | 2020-10-30 |
| XLE | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| XLF | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| XLI | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| XLK | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| XLP | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| XLRE | 1,614 | 2020-06-01 | 2026-10-30 | 1,276 | 2015-10-08 | 2020-10-30 |
| XLU | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| XLV | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| XLY | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| SPY | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| DIA | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| QQQ | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| IWM | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| TLT | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| IEF | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| HYG | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |
| GLD | 1,614 | 2020-06-01 | 2026-10-30 | 2,769 | 2009-11-02 | 2020-10-30 |

\* Holdout coverage was checked for 2009-11-01 through 2020-10-31 using timestamp arrays only. The builder did not read or save any holdout OHLC, adjusted close, or volume fields. XLC and XLRE began trading within the holdout window, so their available date ranges are partial. The row-count/date summary is in `holdout_availability.csv`.

Source and retrieval: Yahoo Finance's public chart endpoint, `https://query1.finance.yahoo.com/v8/finance/chart/{ticker}`. `build_etf_data.py` records the exact request windows. This endpoint is an unofficial public interface and can change; it does not promise an immutable historical data snapshot. Development values alone are retained in the parquet.

## Sector and SIC mapping

- `sector_to_spdr_reference.csv` maps the 11 GICS sector names to their Select Sector SPDR symbols. The sector names follow [S&P Dow Jones Indices' GICS sector index page](https://www.spglobal.com/spdji/en/index-family/equity/us-equity/sp-sectors/); the matching Select Sector fund family is documented by [State Street](https://www.ssga.com/us/en/individual/capabilities/equities/sector-investing/select-sector-etfs).
- `stock_sector_sic_mapping.csv` contains dated S&P 500 membership intervals from `r6_data/sp500_pit_roster.csv` and dated Dow SIC membership intervals from `r6_C1/dow_sic_membership.csv`, joined to the available GICS sector label and its SPDR ETF. Its GICS labels are the current public constituent-list snapshot as of 2026-11-11 from [Wikipedia's S&P 500 constituents table](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies), which displays company GICS Sector. The S&P membership interval and SIC source dates are retained; the GICS label itself is not historical.
- `sector_sic_mapping.csv` joins the available dated SEC SIC observations to the same latest GICS labels, with the SIC filing/effective date and original SEC source URL. SIC and GICS are different taxonomies, so this is an issuer-level association table, not a universal SIC-code-to-GICS conversion.
- The membership interval coverage is 623 S&P 500 rows (622 tickers) and 265 Dow rows (33 tickers). Current-page sector labels match 504 S&P rows (503 tickers) and 261 Dow rows (32 tickers); one Dow name (WBA) and 119 S&P historical ticker identities have no exact current-ticker match in the current constituent table. They remain present with blank GICS/SPDR cells; no sector is imputed. These blanks primarily reflect historical constituents, ticker changes, and acquisitions. Consult the output CSV for each row and source interval.

Free public sector lists do not provide a complete historical GICS reclassification history for each security. Thus historical membership is dated where the project roster has an interval, while GICS/SPDR sector labels are a latest-available snapshot, not a point-in-time sector series. Do not treat those snapshot labels as information known at earlier dates.

## Rebuild

From `A2/pivot_research`, run:

```powershell
python r6_data/etf/build_etf_data.py
python r6_data/etf/build_sector_mapping.py
```

The first script downloads development bars and performs the holdout availability check, writing the holdout timestamps' count/date summary only. The second rebuilds the sector CSVs from the project SIC and point-in-time membership tables plus the public S&P constituent GICS list; source links and snapshot date are included in the files and above.
