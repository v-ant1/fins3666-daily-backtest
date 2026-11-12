# D4 development input QA

Sample: 2020-11-27 to 2026-10-30 (1,488 SPY trading dates); 36 unique assets across point-in-time Dow rosters. This is input construction only: no forward returns, mechanism tests, or portfolios were loaded or computed. Price files were date-filtered to 2020-11-27..2026-10-30 before OHLCV fields were parsed. 13F quarters before 2020-06-01 were rejected before positions were parsed.

**Manager-roster status:** `C:\Users\musta\Desktop\UNSW\SSI\FINS3666\A2\pivot_research\r4_L4\data\13f_top50_pit_roster.csv`: loaded 25 development-era report-quarter cohorts. The point-in-time top-50 roster was loaded and used for each available report-quarter cohort; this build does not use the fixed Q2 2026 manager cohort. Re-run only if the roster or underlying filings change before D4 freeze.

## Network construction

Uses the L4 `13f_holder_by_dow_stock.csv` position panel and filing coverage dates. Each currently eligible manager contributes their latest filing usable before close; a filing dated d becomes usable on the next trading session. Manager positions are value-normalized over that report-quarter Dow holdings roster, combined into stock vectors, converted to cosine overlap, and masked to the point-in-time Dow roster. Diagonal entries are zero, and each nonzero row is normalized for NCP. Each filing can update the graph as soon as it becomes usable; the graph is carried between filings.

Graph age is reported in calendar days and elapsed calendar-quarter boundaries since the latest incorporated filing. Staleness follows the preregistration: strictly more than six calendar months old; stale graphs are retained.

## Quarterly 13F coverage

| Report quarter | Panel public date | Parsed managers (of 50) | Dow names in quarter roster | Names with positive edges | Positive links | Possible links | Density |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2020-06-30 | 2020-09-17 | 50 | 30 | 29 | 406 | 435 | 0.933 |
| 2020-09-30 | 2020-11-19 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2020-12-31 | 2021-02-19 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2021-03-31 | 2021-06-23 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2021-06-30 | 2021-08-24 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2021-09-30 | 2021-12-01 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2021-12-31 | 2022-02-25 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2022-03-31 | 2022-06-03 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2022-06-30 | 2022-08-17 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2022-09-30 | 2022-12-06 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2022-12-31 | 2023-02-15 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2023-03-31 | 2023-05-22 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2023-06-30 | 2023-08-15 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2023-09-30 | 2023-11-15 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2023-12-31 | 2024-02-15 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2024-03-31 | 2024-05-16 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2024-06-30 | 2024-08-15 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2024-09-30 | 2024-11-15 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2024-12-31 | 2025-02-14 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2025-03-31 | 2025-05-19 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2025-06-30 | 2025-08-15 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2025-09-30 | 2025-11-14 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2025-12-31 | 2026-02-19 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2026-03-31 | 2026-05-21 | 50 | 30 | 30 | 435 | 435 | 1.000 |
| 2026-06-30 | 2026-08-14 | 50 | 30 | 30 | 435 | 435 | 1.000 |

## Network density and AAPL/TRV check

All 25 report-quarter panels have 50 parsed managers. AAPL and TRV each have at least one positive-weight connection on all 1,488 development dates, and the direct AAPL–TRV edge is positive on all 1,488 dates. This confirms the earlier missing-position issue is resolved in this development build.

The network is nearly complete: 24 of 25 quarterly graphs contain all 435 possible links (density 1.000); the 2020-06-30 panel contains 406/435 links (density 0.933). Thus, for 24 panels, topology-based rewiring cannot change which links exist; a placebo that preserves topology can only change weight assignments. This is a limitation of what the frozen network placebos can distinguish, not a change to the specification.

Because most graphs are dense, I compared each NCP with the equal-weight mean of the same date's finite-CLV positive peers. Across 44,375 asset-date comparisons, the absolute difference averaged 0.01263 CLV points (95th percentile 0.03649; maximum 0.20058); the mean signed difference was 0.00118. The average daily cross-sectional standard deviation of these differences was 0.01234. For context, row-normalized weights had mean within-row standard deviation 0.01224, mean largest peer weight 0.06076, and mean effective peer count 25.56. These are input/signal-construction diagnostics only; no returns, ICs, or mechanism results were computed.

## Daily network age and staleness

Network is available on 1,488/1,488 development dates (100.0%). Age distribution across available network dates: min 1, median 17, p90 56, p95 62, max 77 calendar days; elapsed calendar-quarter boundaries min/median/p90/max 0/0/1/1. Manager count across available dates: min/median/p90/max 50/50/50/50 of a 50-manager point-in-time roster.

Per-date coverage, edge counts, and density are in `network_age_by_date.csv` (one row for every development trading date). Across available dates, positive edge count min/median/p90/max is 378/435/435/435, and density min/median/p90/max is 0.869/1.000/1.000/1.000. At least five finite NCP names are available on 1488/1488 dates. The input coverage gate is PASS (all dates have a network, five names with scores, and no >2-quarter-stale observations); this is not the mechanism gate.

| Age bin | Available network dates | Share of available dates |
|---|---:|---:|
| 0-45 days | 1192 | 80.1% |
| 46-90 days | 296 | 19.9% |
| 91-180 days | 0 | 0.0% |
| >180 days | 0 | 0.0% |

Daily asset-date signal observations with graph age strictly over six calendar months: 0/44,495 (0.00% of valid NCP observations). A date with no public network panel remains unavailable and does not enter this denominator.

## Signal construction and artifacts

Raw daily CLV is `(2C-H-L)/(H-L)`, zero when `H=L`; D4 pressure is the mean raw CLV over the current and prior four sessions. NCP is `NCP[i,t] = sum_j W[i,j,t] * CLV5[j,t]` on the point-in-time roster; `W` is carried-forward cosine adjacency row-normalized per source and incorporates filings only after their next-session availability. This deliberately follows D4 draft semantics, rather than applying the generic builder’s past-z-scored CLV helper.

Artifacts: `D4_INPUTS.npz` (assets, development dates, active-roster mask, raw CLV5, NCP, adjacency, row weights, age, latest filing date, manager count and stale flags); `quarter_coverage.csv`; and `network_age_by_date.csv`. All source tables and price bars used here are development-era only.

## Frozen runner gate

`run_mechanism.py` contains the preregistered primary mechanism/placebo runner. It validates the D4 frozen date and matching SHA-256 before opening input arrays or any price files, and refuses execution while the PIT roster is missing or when the saved input bundle predates it. The required `--check-freeze` smoke check refused this unfrozen D4 draft with exit code 2; see `RUNNER_REFUSAL.txt`. The mechanism runner was not run.
