# 13F and SIC correction QA

**Scope.** Data-only verification of the corrected 13F position panel and SIC issuer lineage. No price data, returns, signals, or backtests were opened or computed.

## 13F crosswalk and earlier omissions

The earlier 13F mapping omitted Apple because CUSIP `037833100` was absent from the security-to-ticker crosswalk. Travelers was missed because its prior crosswalk entry used the wrong CUSIP (`86312V105`); EDGAR reports the sampled Travelers holdings under `89417E109`. The current bulk and pre-2013 parsers map `037833100` to AAPL and `89417E109` to TRV. Both tickers now appear in the corrected development and holdout position panels for quarters in which they are in the Dow roster.

### Value-unit correction

SEC 13F instructions changed the required rounding from nearest thousand dollars to nearest dollar for filings on/after 2023-01-03. The downloaded values in later SEC information tables are therefore dollars, even though the existing column is named `value_usd_thousands`; leaving them unscaled would create a 1,000-fold unit break. I converted rows with `availability_filing_date >= 2023-01-03` in `13f_development_pit_positions.csv` and its duplicate `13f_holder_by_dow_stock.csv` to USD thousands (dollars divided by 1,000, retaining three decimals), and applied the same conversion to post-cutoff manager totals in `13f_top50_pit_roster.csv`. The conversion uses filing availability date, not report quarter, and is implemented in `fix_13f_value_units.py`; SEC's official [Form 13F FAQ](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f) describes the nearest-dollar convention (updated 2023-01-03).

## Positive-position ticker counts by quarter

Each cell is the number of distinct tickers with at least one row whose `value_usd_thousands` is positive. The holdout panel covers 2010 Q1-2020 Q3; development covers 2020 Q2-2026 Q2. The shared 2020 Q2 and Q3 periods are shown in both columns.

| Quarter | Development | Holdout |
|---|---:|---:|
| 2010 Q1 (2010-03-31) | - | 30 |
| 2010 Q2 (2010-06-30) | - | 30 |
| 2010 Q3 (2010-09-30) | - | 30 |
| 2010 Q4 (2010-12-31) | - | 30 |
| 2011 Q1 (2011-03-31) | - | 30 |
| 2011 Q2 (2011-06-30) | - | 30 |
| 2011 Q3 (2011-09-30) | - | 30 |
| 2011 Q4 (2011-12-31) | - | 30 |
| 2012 Q1 (2012-03-31) | - | 30 |
| 2012 Q2 (2012-06-30) | - | 30 |
| 2012 Q3 (2012-09-30) | - | 30 |
| 2012 Q4 (2012-12-31) | - | 30 |
| 2013 Q1 (2013-03-31) | - | 30 |
| 2013 Q2 (2013-06-30) | - | 30 |
| 2013 Q3 (2013-09-30) | - | 30 |
| 2013 Q4 (2013-12-31) | - | 30 |
| 2014 Q1 (2014-03-31) | - | 30 |
| 2014 Q2 (2014-06-30) | - | 30 |
| 2014 Q3 (2014-09-30) | - | 30 |
| 2014 Q4 (2014-12-31) | - | 30 |
| 2015 Q1 (2015-03-31) | - | 30 |
| 2015 Q2 (2015-06-30) | - | 30 |
| 2015 Q3 (2015-09-30) | - | 30 |
| 2015 Q4 (2015-12-31) | - | 30 |
| 2016 Q1 (2016-03-31) | - | 30 |
| 2016 Q2 (2016-06-30) | - | 30 |
| 2016 Q3 (2016-09-30) | - | 30 |
| 2016 Q4 (2016-12-31) | - | 30 |
| 2017 Q1 (2017-03-31) | - | 30 |
| 2017 Q2 (2017-06-30) | - | 30 |
| 2017 Q3 (2017-09-30) | - | 30 |
| 2017 Q4 (2017-12-31) | - | 30 |
| 2018 Q1 (2018-03-31) | - | 30 |
| 2018 Q2 (2018-06-30) | - | 30 |
| 2018 Q3 (2018-09-30) | - | 30 |
| 2018 Q4 (2018-12-31) | - | 30 |
| 2019 Q1 (2019-03-31) | - | 30 |
| 2019 Q2 (2019-06-30) | - | 30 |
| 2019 Q3 (2019-09-30) | - | 30 |
| 2019 Q4 (2019-12-31) | - | 30 |
| 2020 Q1 (2020-03-31) | - | 30 |
| 2020 Q2 (2020-06-30) | 30 | 30 |
| 2020 Q3 (2020-09-30) | 30 | 30 |
| 2020 Q4 (2020-12-31) | 30 | - |
| 2021 Q1 (2021-03-31) | 30 | - |
| 2021 Q2 (2021-06-30) | 30 | - |
| 2021 Q3 (2021-09-30) | 30 | - |
| 2021 Q4 (2021-12-31) | 30 | - |
| 2022 Q1 (2022-03-31) | 30 | - |
| 2022 Q2 (2022-06-30) | 30 | - |
| 2022 Q3 (2022-09-30) | 30 | - |
| 2022 Q4 (2022-12-31) | 30 | - |
| 2023 Q1 (2023-03-31) | 30 | - |
| 2023 Q2 (2023-06-30) | 30 | - |
| 2023 Q3 (2023-09-30) | 30 | - |
| 2023 Q4 (2023-12-31) | 30 | - |
| 2024 Q1 (2024-03-31) | 30 | - |
| 2024 Q2 (2024-06-30) | 30 | - |
| 2024 Q3 (2024-09-30) | 30 | - |
| 2024 Q4 (2024-12-31) | 30 | - |
| 2025 Q1 (2025-03-31) | 30 | - |
| 2025 Q2 (2025-06-30) | 30 | - |
| 2025 Q3 (2025-09-30) | 30 | - |
| 2025 Q4 (2025-12-31) | 30 | - |
| 2026 Q1 (2026-03-31) | 30 | - |
| 2026 Q2 (2026-06-30) | 30 | - |

## EDGAR value spot checks

I summed each selected CUSIP's reported `value` across all matching information-table rows in the filing, then compared that total divided by 1,000 with the panel's `value_usd_thousands`. Multiple rows for a CUSIP are expected in some filings because positions may be split by class or investment discretion. All 12 comparisons matched EDGAR to three decimal places.

| Report quarter | Manager | Ticker | Panel value (USD thousands) | EDGAR matching rows | Filing source |
|---|---|---|---:|---:|---|
| 2025 Q2 | State Street Corp (CIK 0000093751) | AAPL | 123358461.474 | 1 | [EDGAR information table](https://www.sec.gov/Archives/edgar/data/93751/000009375125000521/XML_Infotable.xml) |
| 2025 Q2 | State Street Corp (CIK 0000093751) | TRV | 4179243.678 | 1 | [EDGAR information table](https://www.sec.gov/Archives/edgar/data/93751/000009375125000521/XML_Infotable.xml) |
| 2025 Q2 | BlackRock, Inc. (CIK 0002012383) | AAPL | 235810229.423 | 32 | [EDGAR information table](https://www.sec.gov/Archives/edgar/data/2012383/000106002125000120/form13fInfoTable.xml) |
| 2025 Q2 | BlackRock, Inc. (CIK 0002012383) | TRV | 5765928.861 | 23 | [EDGAR information table](https://www.sec.gov/Archives/edgar/data/2012383/000106002125000120/form13fInfoTable.xml) |
| 2025 Q2 | Vanguard Group Inc. (CIK 0000102909) | AAPL | 290506933.377 | 7 | [EDGAR information table](https://www.sec.gov/Archives/edgar/data/102909/000175272425185843/13F_0000102909_20250630.xml) |
| 2025 Q2 | Vanguard Group Inc. (CIK 0000102909) | TRV | 5898455.717 | 6 | [EDGAR information table](https://www.sec.gov/Archives/edgar/data/102909/000175272425185843/13F_0000102909_20250630.xml) |
| 2026 Q2 | State Street Corp (CIK 0000093751) | AAPL | 177993996.255 | 1 | [EDGAR information table](https://www.sec.gov/Archives/edgar/data/93751/000009375126000507/XML_Infotable.xml) |
| 2026 Q2 | State Street Corp (CIK 0000093751) | TRV | 5184870.002 | 1 | [EDGAR information table](https://www.sec.gov/Archives/edgar/data/93751/000009375126000507/XML_Infotable.xml) |
| 2026 Q2 | BlackRock, Inc. (CIK 0002012383) | AAPL | 337005479.182 | 34 | [EDGAR information table](https://www.sec.gov/Archives/edgar/data/2012383/000201238326003238/form13fInfoTable.xml) |
| 2026 Q2 | BlackRock, Inc. (CIK 0002012383) | TRV | 6915908.608 | 22 | [EDGAR information table](https://www.sec.gov/Archives/edgar/data/2012383/000201238326003238/form13fInfoTable.xml) |
| 2026 Q2 | Vanguard Fiduciary Trust Co. (CIK 0000933478) | AAPL | 24154082.648 | 1 | [EDGAR information table](https://www.sec.gov/Archives/edgar/data/933478/000093347826000015/13F_0000933478_20260630.xml) |
| 2026 Q2 | Vanguard Fiduciary Trust Co. (CIK 0000933478) | TRV | 393886.309 | 1 | [EDGAR information table](https://www.sec.gov/Archives/edgar/data/933478/000093347826000015/13F_0000933478_20260630.xml) |

## SIC issuer lineage correction

`report_drafts/INPUT_AUDIT.md` identified that `DD` was assigned to legacy CIK 0000030554 after the 2017 merger and that historic `DOW`/Dow Chemical filings under CIK 0000029915 were missing. The corrected `sic_panel.csv` now follows these issuer/ticker intervals; `effective_from` remains the filing date at which the SEC header SIC became observable, rather than the ticker-transition date.

| Ticker identity interval | Issuer CIK | SIC-panel treatment |
|---|---:|---|
| DOW / Dow Chemical, through 2017 merger | 0000029915 | Added dated 10-K header rows 2010-02-19 through 2017-02-09. |
| DWDP, from 2017-09-01 through 2019-06-02 | 0001666700 | Kept dated filed-header rows 2018-02-15 and 2019-02-11 as DWDP. |
| DOW / Dow Inc., from 2019-04-01 | 0001751788 | Retained its SEC header rows; first post-separation annual SIC observation is the 2020-02-07 filing. |
| DD / continuing DuPont issuer, from 2019-06-03 | 0001666700 | Relabeled filed-header rows from 2020-02-14 onward as DD. |
| DD / legacy E. I. du Pont, before 2017 merger | 0000030554 | Retained its dated rows only through the last pre-merger 10-K (2017-02-02); no row after 2017-08-31 remains under this CIK. |

The corrected output contains 777 dated SIC observations across 45 ticker labels and has no blank SIC values. The corrected build step is `python r4_L4/data/fix_sic_lineage.py`; it rebuilds the affected CIK histories from SEC submissions and 10-K headers and refreshes `sic_panel_coverage.csv`. A row-level check finds zero post-2017 DD rows under CIK 0000030554. The source audit is [INPUT_AUDIT.md](../../report_drafts/INPUT_AUDIT.md).

Identity dates and SIC evidence are supported by the SEC filings cited in the audit: [Dow Chemical 2016 10-K, CIK 29915](https://www.sec.gov/Archives/edgar/data/29915/000002991517000011/dow201610k.htm); [DowDuPont 2017 10-K and DWDP listing](https://www.sec.gov/Archives/edgar/data/1666700/000166670018000009/a2017dwdp10-k.htm); [Dow Inc. separation and 2019-04-01 independent trading](https://www.sec.gov/Archives/edgar/data/1751788/000119312519069293/d502004dex991.htm); and [DuPont 2019 10-K, CIK 1666700](https://www.sec.gov/Archives/edgar/data/1666700/000166670020000006/dupont201910-k.htm).

## Files updated

- `13f_development_pit_positions.csv` and `13f_holder_by_dow_stock.csv`: normalized post-2023 filing values to USD thousands.
- `13f_top50_pit_roster.csv`: normalized post-2023 manager total values to USD thousands.
- `sic_panel.csv` and `sic_panel_coverage.csv`: repaired ticker/CIK history for Dow and DuPont issuers.
- `fix_13f_value_units.py` and `fix_sic_lineage.py`: data-only correction scripts.

