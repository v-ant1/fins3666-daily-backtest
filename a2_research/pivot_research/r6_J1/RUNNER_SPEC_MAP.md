# J1 runner-to-preregistration map

`run_j1.py` implements the sole frozen J1-V1 design in `specs/r6_prereg/J1.md`. It does not run on import or by default: the `@guarded_runner` requires an explicit `--execute`, a valid frozen date and content hash, an unused run lock, and no existing `MECHANISM_*` artifacts. This dispatch did not pass `--execute` and did not compute project outcomes.

## Registered choices

| Preregistration | Runner location |
|---|---|
| Five-session trailing stock return less leave-one-out same-SIC2 mean; negative prediction of the next five-session peer-relative return | `build_j1_panels`; `_direction_ic` passes the negative raw signal to `r4_harness.ic_engine.cross_sectional_ic`. Returns align from next-session adjusted open to adjusted close at `t+5`. Before analysis, `validate_feature_bundle` checks the recomputed input signal/mask/SIC2 against L3's parquet feature rows. |
| Weekly formation, first date 2020-11-27 | `FORMATION_STEP=5`; `_analyze` requires that exact S&P date and selects every fifth session from its index. The Dow portfolio uses the same S&P-anchored formation dates by date join. |
| S&P 500 mechanism, NW lag 4, direction-adjusted mean IC at least 0.0034641016 and NW t at least 2 | `NW_LAG`, `COST_IC_FLOOR`, and `mechanism_pass`; inference comes from the shared masked IC engine. |
| Within-date SIC2 score-label shuffle, 500 draws, seed 20261111; save every draw | `_sic2_shuffle`; it permutes scores within the active SIC2 group for each date, calculates the unchanged direction-adjusted mean IC, and returns all 500 values. |
| After H7 and H8 pass, buy five lowest-score Dow names at next open, starting from EW30, maximum 50% total notional turnover per rebalance | `_target_weights`, `_simulate_book`, `_simulate_ew`; actual shares are rebalanced pro rata until buys+sells/NAV is within the cap. Per-side cost is 0.0005 times total actual traded notional. |
| Active share at least 50%, EW30 benchmark, net excess and Sharpe, turnover/cost reporting | `_portfolio`; the portfolio gate requires positive net excess, Sharpe above EW30, cap compliance, active share, and Holm-rejected H9. The preregistered cap route is the turnover cap; the cost/gross-edge ratio is diagnostic. |
| 10-session circular block bootstrap, 5,000 draws, seed 20261111; DSR at cumulative R6 strategy count | `_portfolio`; `circular_block_bootstrap_pvalue`, `deflated_sharpe_ratio`, and `_trial_count`. The trial count reads `R6 variant N: NAME` entries from the R6 manifest only, excluding legacy trial rows and endpoints. |
| Holm family endpoints R6-H7 through R6-H9 | `_read_holm` requires a matching manifest hash, all three current slots, and p-values for every other endpoint. `_write_endpoint_log` writes one output row per H7-H9; H9 is labelled not run when H7/H8 fail and receives p=1 only for the established blocked-slot Holm convention. |
| Frozen one-shot governance | `validate_frozen_prereg` is applied by `guarded_runner`; the harness lock is retained if a run starts, and an existing `MECHANISM_*` artifact blocks a second run. |

## Input bundle contract

L3's current `signal_bundle.parquet` is a **formation-level backward-looking signal and coverage table** with columns `universe`, `formation_date`, `ticker`, `sic2`, `relative_return`, and `relative_return_mask`. It is passed as `--features` and is checked against signal values recomputed from the price bundle. By itself it is not enough to calculate the preregistered next-open outcomes or daily portfolio. `r6_J1/J1_PRICES_DEV.npz` is now staged from the development-only OHLC sources and point-in-time roster/SIC panels. The normalized NPZ contains two independently shaped universes, all matrices are assets × dates, and it contains no precomputed returns or ICs.

| Required key prefix | Shape | Meaning |
|---|---|---|
| `{sp500,dow}_dates` | `(T,)` | Strictly increasing ISO trading dates, 2020-06-01–2026-10-30 inclusive (1,614 sessions). The S&P calendar includes 2020-11-27; Dow scheduled dates are joined to it. |
| `{sp500,dow}_assets` | `(N,)` | Unique point-in-time security identifiers aligned to all matrix rows. |
| `{sp500,dow}_roster` | `(N,T)` bool | Point-in-time roster membership. |
| `{sp500,dow}_sic2` | `(N,T)` strings | Dated SIC2 code, blank when unavailable. |
| `{sp500,dow}_adjusted_open`, `{sp500,dow}_adjusted_close` | `(N,T)` float | Adjusted prices; unavailable bars are NaN. |

`run_j1.py` now defaults to `J1_PRICES_DEV.npz`. `stage_j1_prices.py` builds it using date-filtered reads beginning 2020-06-01: S&P prices come from `r6_data/sp500_ohlcv_dev_gapfilled.parquet`; Dow prices combine already adjusted `r6_C1/dow_components_dev.parquet` with adjusted opens derived from `r6_data/dow_dev_gapfill.parquet`; PIT rosters and the dated SIC2 panel come from the listed CSVs. Adjusted open is `raw_open * adj_close / raw_close` when built from raw OHLCV. Missing bars are NaN; the 51 unresolved S&P PIT histories remain present as rows and have no price entries. The staged dimensions are S&P `(622, 1614)` and Dow `(37, 1614)`; there are 571 S&P and 33 Dow asset rows with at least one price bar. The Dow adjusted open/close cells for matching roster names from 2026-06-29 through 2026-10-30 are sourced from the S&P panel, including the 88-session GOOGL gap. SHA256 after this overlay: `517f85becd0a07fa094a0492e5fe7b3f36170109082b249d5c8a3149d88f5584` (also recorded in `J1_PRICES_DEV_manifest.json`).

The loader accepts documented aliases (`*_names`, `*_roster_mask`, `*_sic2_codes`, `*_adj_open`, `*_adj_close`) but requires both S&P and Dow values. It rejects pre-2020-06 or post-2026-10-30 dates, duplicate labels, mismatched axes, and unordered calendars. Any OHLC adjustment and construction of this normalized price bundle are input staging, not signal/outcome results. The runner derives the peer score and forward return itself after the guard; the parquet's `relative_return` column is input QA cross-check material, not a forward label.

## Placebo and endpoint files

The frozen Holm-family JSON is provided by the coordinator as `--holm-family`; it must have a unique ordered endpoint `manifest`, SHA256 of the newline-joined manifest, and a `p_values` entry for every endpoint other than H7-H9. The checked-in `R6_ENDPOINTS.csv` reserves one no-result row each for H7, H8, H9; an authorized run replaces those placeholders with raw and Holm p-values/statuses. `J1_RESULTS.json` contains the complete 500-shuffle distribution and (when reached) all portfolio/bootstrap values. The runner's lock and outcome artifacts make reruns fail closed.

## Synthetic validation

Run from the project root:

```powershell
python -m unittest r6_J1.test_j1_synthetic -v
python -m r4_harness.prereg_diff r6_J1/J1_PREREG_DIFF_SOURCE.md r6_J1/prereg_diff_config.json
```

Both commands are input-code checks only. Do not pass `--execute` unless the coordinator authorizes an outcome run after confirming input QA and the Holm file.

Diff procedure: the harness CLI compares a mechanically normalized copy (`J1_PREREG_DIFF_SOURCE.md`) to `prereg_diff_config.json`, so it captures the two distinct turnovers, top-five K, 5/30 rank fraction, and 500/5,000 draw counts that its raw markdown parser otherwise tokenizes imperfectly. The frozen source remains untouched and is checked by the synthetic freeze/hash test.
