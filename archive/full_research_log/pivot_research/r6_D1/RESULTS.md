# D1 single authorized development run

## Run controls and inputs

- Frozen preregistration: `specs/r6_prereg/D1.md`, frozen 2026-11-11, SHA256 `d5059ac49ba2d2d4c5450c01632011a9f3a673dc1e8de7821d9713d6cb9ac26e`.
- The input-only coverage manifest passed before the runner loaded `D1_INPUTS.npz`. Strict joint formation member-day coverage was 94.843% for the S&P 500 and 97.494% for the Dow 30; 297 of 298 scheduled S&P dates (99.664%) had at least 250 eligible names. The S&P 51-name price-gap list was handled with the frozen per-date exclusion rule.
- The run-specific consistency gate also passed: 1,488 development sessions, 297 outcome-eligible formation dates, 95.265% S&P and 98.182% Dow formation-date member coverage, and 100% of S&P formation dates above the 250-name threshold.
- Development input bundle SHA256: `33b977f9454b50f1d197751a6883d92bdd45e3041ed92082a18e43fc32108538`. It contains 1,614 sessions from 2020-06-01 through 2026-10-30, 622 S&P ticker rows and 37 point-in-time Dow ticker rows. Dow OHLC fields were parsed only for dates on or after 2020-06-01; no holdout input was loaded.
- The run directory and lock were absent before execution, and there were no prior mechanism artifacts. The guarded runner created and retained `.runner.lock`; this was the only `--execute` invocation. No code was changed after execution started.

## Endpoint results

| Endpoint | Estimate / statistic | Raw p | Holm p (R6 only) | Result |
|---|---:|---:|---:|---|
| R6-H1 — S&P 500 mechanism | Mean date-wise Spearman IC = **0.0093742**; Newey–West t(4) = **1.9080** | 0.028195 | 0.056390 | **FAIL**: IC is positive and exceeds 0.0043301, but NW t is below 2.00. |
| R6-H2 — SIC2 shuffle placebo | Observed mean IC = **0.0093742**; empirical null 95th percentile = **0.0042863** | 0.001996 | 0.005988 | **PASS**: observed IC exceeds the null 95th percentile. |
| R6-H3 — Dow portfolio | Not evaluated | — | 1.000000 (reserved slot) | **NOT RUN**: H1 failed its required NW-t gate, so the sequential rule stops before portfolio analysis. |

The endpoint log `run/D1_ENDPOINTS.csv` contains exactly one row for each of R6-H1, R6-H2 and R6-H3. The H1 raw one-sided p-value is below 0.05, but this does not override the preregistered NW-t threshold; its R6-family Holm-adjusted p-value is 0.056390.

## Placebo details

The fixed SIC2-stratified shuffle used 500 draws and seed 20261111, permuting eligible scores within date and SIC2 while leaving singleton groups fixed. The saved runner output records the empirical 95th percentile (0.0042863) and randomization p-value (0.001996), equivalent to zero of 500 shuffled means at least as large as the observed statistic with the plus-one correction. The runner did not retain all 500 null means, so other distribution summaries (such as its minimum, median, maximum or histogram) are unavailable; they were not reconstructed because the run was authorized exactly once.

## Portfolio diagnostics

The portfolio endpoint was not run. Therefore net and gross excess returns, Sharpe versus EW30, realized turnover, active share, transaction costs, circular-block-bootstrap p-value and deflated Sharpe ratio are **not estimated**; these fields are not failures or zeros. The frozen stop rule excludes H3 after H1 fails.

## Artifacts and scope

The complete machine-readable result is `run/D1_RESULTS.json`, and the one-row-per-endpoint log is `run/D1_ENDPOINTS.csv`. This report records the only authorized development run; it contains no holdout analysis and no rerun was attempted.
