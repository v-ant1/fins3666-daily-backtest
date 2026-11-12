# FINRA equity short-interest data QA

Prepared 2026-11-11. This package is data-only; no prices, returns, signals, or backtests were accessed.

## Development data

`finra_si_dev.parquet` is a point-in-time panel of securities present in the S&P 500 roster or the Dow roster on each settlement date, covering 2020-06 through 2026-10. It retains FINRA's `symbolCode` as `symbol`/`ticker`, `settlementDate`, `currentShortPositionQuantity` as `short_interest`, `averageDailyVolumeQuantity` as `average_daily_volume`, and `daysToCoverQuantity` as `days_to_cover`; `market_class_code`, `issue_name`, universe-membership flags, source filename and URL are also retained. Values are reported by FINRA and are not recomputed or imputed. The full source settlement files are stored in `raw/`.

| Year | Matched panel rows | Settlement files |
|---:|---:|---:|
| 2020 | 6912 | 14 |
| 2021 | 11866 | 24 |
| 2022 | 11872 | 24 |
| 2023 | 11926 | 24 |
| 2024 | 11984 | 24 |
| 2025 | 12004 | 24 |
| 2026 | 9532 | 19 |

`dev_ticker_coverage.csv` gives row coverage by matched ticker. `dev_download_gaps.csv` and `dev_parse_errors.csv` report any missing source file or parse issue. Empty/nonreported securities are absent from FINRA files and are not zero-filled.

One planned month-end request is unavailable: no consolidated file was returned for the 2026-10-30/31 settlement search as of 2026-11-11, so the latest included file is dated 2026-10-15. The panel therefore has 19 files for 2026 rather than the 20 expected through October; this is reported as a source gap, not imputed.

## Sealed holdout

Raw files for the available portion of 2009-11 to 2020-10 are under `sealed_holdout_dow/finra_si/raw/`. The row-count and ticker-presence-only manifest is at `sealed_holdout_dow/finra_si/MANIFEST.md` and `.csv`; its fields are settlement date from the source URL, filename, row count, Dow ticker, and presence. It covers 69 files from 2017-12-29 to 2020-10-30 (2,070 file/ticker rows), with every active roster ticker present in its corresponding file. Files from 2009-11 through 2017-11 are not available through the public consolidated full-market file path: FINRA's linked older static archives are OTC-only. Therefore holdout coverage is partial; do not interpret the unavailable years as zero short interest. The manifest scan reads only a line count and the symbol column, and does not access short-interest, average daily volume, or days-to-cover values.

## Availability and timing

FINRA settlement files are semi-monthly, typically the 15th (or prior settlement day) and the final settlement day of a month. A settlement is a snapshot, not a daily series. The files were retrieved from FINRA's public file path `https://cdn.finra.org/equity/otcmarket/biweekly/shrtYYYYMMDD.csv`. The source directory is labelled `otcmarket` despite the portal's **current** file feed describing consolidated exchange-listed and OTC equity short interest; FINRA's static archive files are explicitly OTC-only. Field quoting changed in the latest years, so parsing uses the pipe delimiter and CSV quoting rules.

## Rebuild

Run from `A2/pivot_research`:

```powershell
python r6_data/finra_si/build_finra_si.py
```

The script downloads development files and available holdout raw files, writes the parsed development panel, and creates the holdout manifest using presence-only scanning.
