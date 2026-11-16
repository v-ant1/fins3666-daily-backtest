# D1 frozen-runner specification map

`run_d1.py` is a guarded implementation of frozen `specs/r6_prereg/D1.md`. It does not download data, read holdout files, or store precomputed returns. The runner defaults to a non-executing status message; only the coordinator's explicit `--execute` invokes outcome computation. `--check-freeze` validates only the frozen date and canonical SHA256.

## Frozen controls to code

| Frozen D1 item | Runner implementation |
|---|---|
| Freeze/hash, explicit authorization, retained lock | `@guarded_runner(prereg_path=PREREG, run_dir=RUN_DIR)`; validation is also available through `--check-freeze`. |
| Development dates only | `validate_bundle` requires 1,614 ordered sessions within 2020-06-01–2026-10-30; analysis uses 2020-11-27–2026-10-30. |
| Input-only joint gate before signals/outcomes and price bundle | `run_d1` reads `joint_coverage_manifest.json` first; `coverage_manifest_gate` checks development-only/presence-only flags, exact t−4..t and t+2..t+6 windows, ≥90% formation joint member-day coverage for S&P and Dow, and ≥80% S&P dates with ≥250 names. `run_coverage_first` does not call the NPZ bundle loader if the manifest gate fails. After it passes, the bundle's own input-only `joint_coverage_gate` is rechecked before `_signals` or `_forward_returns`. |
| PIT price gaps / no survivor substitution | Input `*_roster` is date specific; a name is eligible only when roster, paired ratio, price input, and required dates are available. No filling or proxy lineage is performed in the runner. The prepared bundle must preserve PIT ticker lineage and decision 27's per-date availability mask. |
| Paired Reg SHO ratio | `*_ratio` must already be `ShortVolume/TotalVolume` built from matched valid facility rows; `ShortVolume` includes short-exempt volume, and `ShortExemptVolume` is not added/subtracted. The runner never imports a separate consolidated denominator. |
| Five-session `R` and negative-pressure `P=-R` | `_signals`: arithmetic mean of exactly five finite nonnegative paired daily ratios; otherwise NaN. |
| Formation schedule and t+2 entry | `_formation_indices` selects every fifth session from 2020-11-27; `_forward_returns` aligns t+2 adjusted open to t+6 adjusted close. |
| S&P mechanism and NW lag 4 | `r4_harness.ic_engine.cross_sectional_ic(..., nw_lag=4)` on formation dates with PIT roster and paired score/forward-input mask. H1 p is the one-sided normal-tail p for the registered NW t. |
| SIC2 shuffle, 500 draws, fixed seed | `_stratified_shuffle` permutes scores only within date and SIC2, with singletons fixed; 500 null means use seed 20261111. H2 checks observed IC > null 95th percentile and one-sided randomization p <0.05. |
| Dow top five, initial EW30, t+2, 50% total turnover cap | `_wealth_path` initializes in EW30 at the preceding close, trades on formation+2 open, selects highest `P` / lowest `SR`, and applies a pro-rata total buys-plus-sells/NAV cap of 0.50 at each strategy rebalance. EW30 benchmark uses the same dates/universe and costs. |
| 0.05% per dollar traded / net edge | `COST_RATE=0.0005`; H3 reports net excess, gross active edge, cost/gross ratio, Sharpe, active share and realized turnover. |
| 10-session circular block bootstrap, 5,000 draws, seed 20261111 | `r4_harness.phase3.circular_block_bootstrap_pvalue`; H3 raw p plus full R6-H1..H3 Holm p. |
| Unique R6 strategy count for DSR | `_r6_variant_count` reads the coordinator's `R6 variants used: n/30` value in `specs/r6_decisions.md`; current D1 count is 1. It does not count endpoints as variants. |
| One logged row per endpoint | Actual authorized run writes `r6_D1/run/D1_ENDPOINTS.csv` with exactly `R6-H1`, `R6-H2`, `R6-H3`; blocked endpoints have empty raw p and use `p=1` only for Holm adjustment. The three rows are endpoint records, not three strategy variants. |

## Staged input bundle

The input-only audit at `r6_D1/joint_coverage_manifest.json` must exist and pass first. It records 94.843% S&P and 97.494% Dow formation joint member-day coverage, 297/298 S&P dates with at least 250 eligible names, and 51 residual S&P tickers without price bars. The coordinator/run owner must also stage a development-only `r6_D1/D1_INPUTS.npz` with these arrays. Each universe matrix is assets × 1,614 sessions; dates are a shared sorted ISO-date vector for NYSE sessions from 2020-06-01 through 2026-10-30.

| Key | Shape/type | Meaning |
|---|---|---|
| `dates` | `(1614,)`, strings | Development session dates only. |
| `sp500_names`, `dow_names` | `(N,)`, strings | Unique PIT symbol identifiers aligned across each universe's matrices. |
| `sp500_roster`, `dow_roster` | `(N, 1614)`, bool | PIT membership mask. |
| `sp500_ratio`, `dow_ratio` | `(N, 1614)`, float | Valid paired FINRA facility short-volume ratio; missing observations are NaN. |
| `sp500_adjusted_open`, `dow_adjusted_open` | `(N, 1614)`, float | Adjusted open as registered: raw open × adjusted close / raw close. |
| `sp500_adjusted_close`, `dow_adjusted_close` | `(N, 1614)`, float | Adjusted close. |
| `sp500_sic2`, `dow_sic2` | `(N, 1614)`, strings | Date-specific two-digit SIC group, blank if unavailable. |

`validate_bundle` rejects dates before 2020-06-01 and duplicate/out-of-order dates. The bundle contains input prices and ratios only; the runner derives signal and forward returns after the gate. It must not contain a return or signal-outcome array. Any point-in-time price repair and ticker alias resolution must happen before staging and be documented in the coverage manifest.

## Endpoint rows and no-run behavior

The R6 family is separate from R5. The endpoint mapping is:

| ID | Frozen endpoint | Raw statistic |
|---|---|---|
| R6-H1 | D1-1 S&P 500 mechanism | Mean date-wise Spearman IC; NW t lag 4; one-sided raw p. |
| R6-H2 | D1-2 SIC2 shuffle placebo | Observed mean IC vs the 500-draw SIC2-stratified null; one-sided randomization p. |
| R6-H3 | D1-3 Dow portfolio | Net cumulative excess vs point-in-time EW30; one-sided circular block-bootstrap p. |

If the input-only manifest gate fails, the runner logs all three IDs as `not run` with no raw p-values and exits before calling the bundle loader. If the post-load input-only consistency gate fails, the runner stops before calculating signals/returns and logs the same blocked rows. If H1 or H2 fails, H3 is `not run`; its fixed Holm slot receives conservative `p=1` for adjustment only. Running the runner without `--execute` does not load the manifest or bundle, acquire a lock, compute statistics, or write outcome artifacts.

## Diff normalization

`r4_harness.prereg_diff` tokenizes `5,000` as `0` and misses some explicit phrases such as “500 independent shuffles” and “next five-session horizon”. `prereg_diff_text()` makes formatting-only changes to an in-memory copy (remove thousands separators and add explicit numeric labels for already registered horizon, variant and endpoint IDs) before invoking the harness. It does not alter `D1.md`, its frozen hash, or any design parameter. The saved `PREREG_DIFF.txt` includes the extracted facts, declared settings and zero differences.
