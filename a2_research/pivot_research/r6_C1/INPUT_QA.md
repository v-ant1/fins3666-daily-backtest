# C1 input QA (development dates only)

This report checks inputs, roster membership, and point-in-time SIC availability only. The builder loaded adjusted OHLCV, then created same-day overnight and intraday returns; it did not load or compute forward returns, return outcomes, ICs, or strategy performance. No holdout data were accessed. The input window is 2020-11-27 through 2026-10-30.

### Dow

- Dates in component panel: 2020-11-27 through 2026-10-30 (1,488 sessions).
- Asset-date component rows: 43,944; distinct tickers: 33; missing same-day components: 0; first-session overnight values without a prior in-window close: 30.
- Earliest available price file begins 2020-11-27; daily quarter coverage is in the table below.


| Quarter | Sessions | Median bars names | Minimum bars names | Median PIT roster | Median bar coverage | Dates with full-roster bars |
|---|---:|---:|---:|---:|---:|---:|
| 2020Q4 | 24 | 1 | 1 | 30 | 3.33% | 0.00% |
| 2021Q1 | 61 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2021Q2 | 63 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2021Q3 | 64 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2021Q4 | 64 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2022Q1 | 62 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2022Q2 | 62 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2022Q3 | 64 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2022Q4 | 63 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2023Q1 | 62 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2023Q2 | 62 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2023Q3 | 63 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2023Q4 | 63 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2024Q1 | 61 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2024Q2 | 63 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2024Q3 | 64 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2024Q4 | 64 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2025Q1 | 60 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2025Q2 | 62 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2025Q3 | 64 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2025Q4 | 64 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2026Q1 | 61 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2026Q2 | 62 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2026Q3 | 64 | 30 | 30 | 30 | 100.00% | 100.00% |
| 2026Q4 | 22 | 30 | 30 | 30 | 100.00% | 100.00% |

### S&P 500

- Dates in component panel: 2020-11-27 through 2026-10-30 (1,488 sessions).
- Asset-date component rows: 716,987; distinct tickers: 564; missing same-day components: 0; first-session overnight values without a prior in-window close: 564.
- Earliest available price file begins 2020-11-27; daily quarter coverage is in the table below.


| Quarter | Sessions | Median bars names | Minimum bars names | Median PIT roster | Median bar coverage | Dates with full-roster bars |
|---|---:|---:|---:|---:|---:|---:|
| 2020Q4 | 24 | 461 | 461 | 505 | 91.29% | 0.00% |
| 2021Q1 | 61 | 463 | 461 | 505 | 91.68% | 0.00% |
| 2021Q2 | 63 | 465 | 463 | 505 | 92.08% | 0.00% |
| 2021Q3 | 64 | 467 | 466 | 505 | 92.48% | 0.00% |
| 2021Q4 | 64 | 467 | 467 | 505 | 92.48% | 0.00% |
| 2022Q1 | 62 | 471 | 469 | 505 | 93.27% | 0.00% |
| 2022Q2 | 62 | 473 | 472 | 504 | 93.85% | 0.00% |
| 2022Q3 | 64 | 473 | 473 | 503 | 94.04% | 0.00% |
| 2022Q4 | 63 | 477 | 475 | 503 | 94.83% | 0.00% |
| 2023Q1 | 62 | 479 | 479 | 503 | 95.23% | 0.00% |
| 2023Q2 | 62 | 482 | 481 | 503 | 95.83% | 0.00% |
| 2023Q3 | 63 | 483 | 482 | 503 | 96.02% | 0.00% |
| 2023Q4 | 63 | 483 | 481 | 503 | 96.02% | 0.00% |
| 2024Q1 | 61 | 484 | 484 | 503 | 96.22% | 0.00% |
| 2024Q2 | 63 | 485 | 484 | 503 | 96.42% | 0.00% |
| 2024Q3 | 64 | 486 | 486 | 503 | 96.62% | 0.00% |
| 2024Q4 | 64 | 486 | 486 | 503 | 96.62% | 0.00% |
| 2025Q1 | 60 | 489 | 489 | 503 | 97.22% | 0.00% |
| 2025Q2 | 62 | 489 | 489 | 503 | 97.22% | 0.00% |
| 2025Q3 | 64 | 493 | 490 | 503 | 98.01% | 0.00% |
| 2025Q4 | 64 | 494 | 494 | 503 | 98.21% | 0.00% |
| 2026Q1 | 61 | 496 | 496 | 503 | 98.61% | 0.00% |
| 2026Q2 | 62 | 498 | 496 | 503 | 99.01% | 0.00% |
| 2026Q3 | 64 | 500 | 499 | 503 | 99.40% | 0.00% |
| 2026Q4 | 22 | 502 | 502 | 503 | 99.80% | 4.55% |

## Point-in-time industry link coverage

A SIC observation is made available from the next trading day after its SEC filing date. Membership files store SIC2/SIC3 intervals; edge files represent pairwise same-industry overlaps during those intervals. Counts below are input coverage, not outcome evidence.

| Universe | Price tickers | Tickers with dated SIC | SIC coverage | SIC2 linked pairs | SIC3 linked pairs |
|---|---:|---:|---:|---:|---:|
| Dow | 33 | 33 | 100.0% | 297 | 116 |
| S&P 500 | 564 | 558 | 98.9% | 68,636 | 27,738 |

### Dated SIC coverage by available universe

Dow SIC panel source: [`r4_L4/data/sic_panel.csv`](../r4_L4/data/sic_panel.csv); the 2-digit/3-digit dates in the emitted files are shifted to the following observed trading day. S&P SIC source: SEC 10-K filing headers pulled from the free [SEC EDGAR submissions and filing APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), supplemented with L4's dated SIC records for retired symbols absent from SEC's current ticker map. Current S&P roster source is [`r6_data/sp500_pit_roster.csv`](../r6_data/sp500_pit_roster.csv), whose manifest describes a reconstructed PIT roster; issuer identity and missing-price mapping need further audit.

| Universe | Quarter | Median available names with dated SIC | Minimum names with dated SIC | Median 2-digit SIC groups |
|---|---|---:|---:|---:|
| Dow | 2020Q4 | 1 | 0 | 1 |
| Dow | 2021Q1 | 30 | 1 | 18 |
| Dow | 2021Q2 | 30 | 30 | 18 |
| Dow | 2021Q3 | 30 | 30 | 18 |
| Dow | 2021Q4 | 30 | 30 | 18 |
| Dow | 2022Q1 | 30 | 30 | 19 |
| Dow | 2022Q2 | 30 | 30 | 19 |
| Dow | 2022Q3 | 30 | 30 | 19 |
| Dow | 2022Q4 | 30 | 30 | 19 |
| Dow | 2023Q1 | 30 | 30 | 19 |
| Dow | 2023Q2 | 30 | 30 | 19 |
| Dow | 2023Q3 | 30 | 30 | 19 |
| Dow | 2023Q4 | 30 | 30 | 19 |
| Dow | 2024Q1 | 30 | 30 | 19 |
| Dow | 2024Q2 | 30 | 30 | 19 |
| Dow | 2024Q3 | 30 | 30 | 19 |
| Dow | 2024Q4 | 30 | 30 | 19 |
| Dow | 2025Q1 | 30 | 30 | 19 |
| Dow | 2025Q2 | 30 | 30 | 19 |
| Dow | 2025Q3 | 30 | 30 | 19 |
| Dow | 2025Q4 | 30 | 30 | 19 |
| Dow | 2026Q1 | 30 | 30 | 19 |
| Dow | 2026Q2 | 30 | 30 | 19 |
| Dow | 2026Q3 | 30 | 30 | 19 |
| Dow | 2026Q4 | 30 | 30 | 19 |
| S&P 500 | 2020Q4 | 446 | 0 | 55 |
| S&P 500 | 2021Q1 | 455 | 451 | 54 |
| S&P 500 | 2021Q2 | 459 | 457 | 54 |
| S&P 500 | 2021Q3 | 460 | 458 | 54 |
| S&P 500 | 2021Q4 | 460 | 460 | 55 |
| S&P 500 | 2022Q1 | 463 | 462 | 55 |
| S&P 500 | 2022Q2 | 469 | 467 | 54 |
| S&P 500 | 2022Q3 | 469 | 467 | 54 |
| S&P 500 | 2022Q4 | 473 | 469 | 54 |
| S&P 500 | 2023Q1 | 475 | 474 | 54 |
| S&P 500 | 2023Q2 | 477 | 476 | 54 |
| S&P 500 | 2023Q3 | 478 | 475 | 54 |
| S&P 500 | 2023Q4 | 477 | 475 | 54 |
| S&P 500 | 2024Q1 | 478 | 478 | 54 |
| S&P 500 | 2024Q2 | 479 | 477 | 54 |
| S&P 500 | 2024Q3 | 480 | 477 | 54 |
| S&P 500 | 2024Q4 | 479 | 479 | 54 |
| S&P 500 | 2025Q1 | 484 | 483 | 54 |
| S&P 500 | 2025Q2 | 487 | 487 | 54 |
| S&P 500 | 2025Q3 | 491 | 488 | 54 |
| S&P 500 | 2025Q4 | 492 | 490 | 54 |
| S&P 500 | 2026Q1 | 494 | 492 | 54 |
| S&P 500 | 2026Q2 | 496 | 494 | 54 |
| S&P 500 | 2026Q3 | 498 | 496 | 54 |
| S&P 500 | 2026Q4 | 500 | 499 | 53 |

The following S&P price tickers have no dated SIC interval in the assembled SEC+L4 panel: EQR, HONA, MBC, SOLS, VYLR, WLTW. Some entered near the end of the window and have no 10-K SIC filing yet; retired/relabelled tickers can also be absent from the current SEC ticker map. S&P price rows also have gaps versus the roster, so this is not a complete 500-name time series on every session. For dates with fewer bars, missing tickers are not silently imputed. The Dow price source has a material early-window gap: daily bars for 29 of the 30 initial constituents begin on 2021-01-04, while WBA has earlier rows; consequently the initial portion before 2021-01-04 is incomplete and no signal should be calculated on those sparse cross-sections.

Dow point-in-time changes follow official S&P DJI announcements: [August 2020 additions](https://press.spglobal.com/2020-08-24-Salesforce-com-Amgen-and-Honeywell-International-Set-to-Join-Dow-Jones-Industrial-Average), [Amazon addition](https://press.spglobal.com/2024-02-20-Amazon-com-Set-to-Join-Dow-Jones-Industrial-Average-Uber-to-Join-Dow-Jones-Transportation-Average), and [November 2024 additions](https://press.spglobal.com/2024-11-01-NVIDIA-and-Sherwin-Williams-Set-to-Join-Dow-Jones-Industrial-Average-Vistra-to-Join-Dow-Jones-Utility-Average?asPDF=1).

## Output files

- `dow_components_dev.parquet` and `sp500_components_dev.parquet`: adjusted open/close, overnight return, intraday return, and their relative component spread, on development dates only.
- `dow_sic_membership.csv`, `dow_industry_links.csv`, `sp500_sic_membership.csv`, `sp500_industry_links.csv`: dated two-/three-digit SIC classifications and pairwise link intervals.
- `coverage_by_quarter.csv`, `input_manifest.json`: machine-readable coverage and provenance checks.

## Final C1 signal-input addendum (decision 26; input only)

The final C1 input is the **leave-one-out mean of same-SIC3 peer intraday returns**. For each security and date, its own signal component is the compounded adjusted open-to-close return over the latest five trading sessions, `product(1 + intraday_return) - 1`; for each target, the signal is the equal-weight mean of those trailing-five values for other active, point-in-time SIC3 members. A score is emitted only when at least two valid other peers are present. SIC intervals are used only when active on the signal date; the existing interval construction makes an SEC filing usable from the next trading session. This is a signal-only replacement for C1's earlier CLV proposal and is distinct from E1's peer CLV input.

The build used the already-built development-only Dow and S&P 500 component panels and dated SIC membership inputs. The input date range is 2020-11-27 through 2026-10-30; no forward prices, outcomes, or ICs were loaded or computed. The builder emits `peer_intraday_signal_dev.parquet`, with one row per available component-panel member/date and columns for SIC3, own trailing-five intraday return, number of valid peer names, peer signal, and availability flags. `peer_signal_coverage_by_date.csv` summarizes the daily cross-section; `peer_signal_coverage_by_ticker.csv` reports coverage by name among dates present in the component panels; `peer_signal_manifest.json` records definitions and input-only status.

| Universe | Weekly formation dates | Median peer-score names | Minimum peer-score names | Dates with ≥250 names |
|---|---:|---:|---:|---:|
| S&P 500 | 297 | 359 | 326 | 297 / 297 |
| Dow 30 | 297 | 6 | 0 | 0 / 297 |

Peer counts among names with scores have a median of 12 for the S&P 500 and 2 for the Dow. The Dow's low coverage is consistent with the narrow 30-name universe partitioned into SIC3 groups; missing scores remain missing. These are input coverage figures, not predictive evidence. Coverage is conditional on rows in the existing component panel; prior S&P roster-gap and Dow early-window limitations documented above still apply.

`build_peer_intraday_signal.py` reproduces the signal panel and coverage files with one command: `python r6_C1/build_peer_intraday_signal.py`. It uses only current development component and SIC3 membership files. `power_analysis.py` then regenerates the synthetic power calculation and `POWER.md`.


The matched synthetic S&P power analysis is in `POWER.md`. With 297 weekly dates, median 47 SIC3 clusters, mean cluster size 7.660, ICC assumption 0.15, and literature IC SD 0.15 inflated to 0.2121, simulated power is 32.2% at hypothetical IC 0.0183 and 55.2% at 0.026; the 80% MDE is 0.0349. This does **not** meet an 80%-power gate at 0.0183 under these assumptions. These are synthetic design results based on signal-only autocorrelation and SIC3 group sizes, not observed ICs or outcomes; the script uses the shared `r4_harness/power_sim.py` with horizon 5/NW lag 4.
