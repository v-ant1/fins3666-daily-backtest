# D1 — Reg SHO daily short-volume coverage

## Scope and pull

The pull covers every NYSE-session date from **2020-06-01 through 2026-10-30**. The calendar contains 1,614 sessions; the FINRA daily endpoint returned a file for all 1,614, with zero missing sessions and zero failed downloads. The raw files total 569,204,908 bytes (about 543 MiB); the full-session manifest is `r6_data/finra_regsho/download_manifest.csv`, and raw files are in `r6_data/finra_regsho/raw/`.

Each file has `Date`, `Symbol`, `ShortVolume`, `ShortExemptVolume`, `TotalVolume`, and `Market` fields. Across dates there are 8,193–12,462 issue rows per file. `daily_coverage.csv` reports roster counts, matched counts, file status, and the unmatched symbols for every date and universe. The signal panel is `signal_panel.csv.gz`; descriptive statistics are in `signal_statistics.csv`.

## Point-in-time roster matches

The supplied S&P membership intervals in `r6_data/sp500_pit_roster.csv` were applied date by date. A separate alias table maps the roster's modern ticker to the symbol FINRA actually reported at that date, including historical names such as FB/META, FLT/CPAY, and MMC/MRSH. `VTRS` to its predecessor symbol `MYL` is explicitly flagged as a predecessor mapping; it is not a simple symbol change. Share-class symbols such as BF-B and BRK-B are normalized to FINRA's slash form. These mappings are recorded in `ticker_aliases.csv` and the pull script.

| Universe | NYSE sessions | Expected roster names/date | Mean matched/date | Median daily coverage | Lowest daily coverage | Full-coverage dates |
|---|---:|---:|---:|---:|---:|---:|
| S&P 500 | 1,614 | 503–506 | 503.16 | 100.0% | 501/503 = 99.60% | 892 |
| Dow 30 | 1,614 | 30 | 30.00 | 100.0% | 100.0% | 1,614 |

S&P coverage is 99.91% on average. Its 722 incomplete sessions each have at least one roster name with no matching FINRA row; the worst coverage is still 501 of 503 names. Unmatched names and dates are retained in `daily_coverage.csv`, rather than imputed to zero. Examples include SBNY/SIVB during the March 2023 bank failures and isolated names such as BIIB/FISV on dates with no FINRA row. This is a roster-to-facility-data match, not a claim that those securities had no exchange trading.

The Dow roster in `dow_pit_roster.csv` applies the published 2020-08-31, 2024-02-26, 2024-11-08, and 2026-06-29 constituent changes. The 2020-06 start is obtained by reversing the August 2020 replacements from the later baseline; those changes and the more recent adds/removals are supported by [S&P DJI's August 2020 announcement](https://press.spglobal.com/2020-08-24-Salesforce-com-Amgen-and-Honeywell-International-Set-to-Join-Dow-Jones-Industrial-Average), [February 2024 announcement](https://press.spglobal.com/2024-02-20-Amazon-com-Set-to-Join-Dow-Jones-Industrial-Average-Uber-to-Join-Dow-Jones-Transportation-Average), [November 2024 announcement](https://press.spglobal.com/2024-11-01-NVIDIA-and-Sherwin-Williams-Set-to-Join-Dow-Jones-Industrial-Average-Vistra-to-Join-Dow-Jones-Utility-Average), and [June 2026 announcement](https://press.spglobal.com/2026-06-23-Alphabet-Set-to-Join-and-Honeywell-International-to-Remain-in-Dow-Jones-Industrial-Average).

## What the ratio means—and does not mean

The descriptive signal is `ShortVolume / TotalVolume` as printed in the FINRA file; `ShortExemptVolume` remains a separate field. FINRA's [daily data guide](https://www.finra.org/sites/default/files/2020-12/short-sale-volume-user-guide.pdf) defines these as volumes reported to FINRA facilities. FINRA also says its short-sale volume files include publicly disseminated trades and are **not consolidated with exchange data** in its [May 2019 notice](https://www.finra.org/sites/default/files/2019-07/information-notice-051019.pdf). Therefore, this ratio is short volume divided by total volume observed in the FINRA reporting facilities represented in that file; it is not a national consolidated-market short-volume ratio. It excludes exchange activity and non-publicly disseminated activity and should not be called short interest or net short positioning. FINRA explains the distinction between daily volume and open positions [here](https://www.finra.org/investors/insights/short-interest).

Because some reported short sales may be dealer/intermediary activity and may be offset by purchases not represented in the same daily file, neither the ratio nor the daily file alone proves directional investor selling pressure. An unmatched symbol is missing facility coverage, not a zero signal.

## Data boundary

The pull and its summaries use only FINRA flow files from 2020-06-01 onward, roster metadata, the NYSE calendar, and SIC classification metadata for the separate power calculation. No pre-2020-06 files were downloaded or queried, and no returns, prices, or strategy outcomes were calculated. During roster discovery, a terminal preview accidentally exposed three existing non-holdout development component rows; those values were not analyzed or used, the coordinator was informed, and the coordinator authorized continuing with isolated FINRA and roster inputs.

## Reproduction

From the project root:

```powershell
python r6_D1/build_dow_roster.py
python r6_D1/pull_and_summarize.py
```

`pull_and_summarize.py` uses the NYSE calendar and downloads from FINRA's official daily file path `https://cdn.finra.org/equity/regsho/daily/CNMSshvolYYYYMMDD.txt`. It keeps the downloaded full files, emits per-date coverage and ratio-only summaries, and never opens price or return files.
