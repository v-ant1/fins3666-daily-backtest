# D5 mechanism and placebo results

**Mechanism gate: FAIL.** Development sample: 2020-11-27 to 2026-10-30; 1488 sessions.
Only development prices were used. The portfolio stage and sealed holdout were not run.

## Pre-outcome graph gate

Input-only feasibility gate: PASS, 293/293 eligible fifth-session dates met the minimum of 10 pairs, 3 leaders and 3 SIC groups. There were 11 directed pairs on each eligible date (see `INPUT_QA.md` and `D5_GRAPH_BY_DATE.csv`).

## Registered endpoints

| Endpoint | Mean rank IC / statistic | NW t (lag 4) | Raw p-value | Result |
|---|---:|---:|---:|---|
| Variant 1 primary, 20-session graph (one-sided NW) | 0.007455 | 0.5644 | 0.286249 | FAIL (mean ≥ 0.0183 and t ≥ 2) |
| Reverse-edge deterministic control (two-sided NW) | -0.001445 | -0.0759 | 0.939479 | PASS (|t| < 2) |
| Within-SIC leader permutations, observed vs null (one-sided randomization) | observed 0.007455; null p95 0.015677 | pooled null-series t 0.4879 | 0.307385 | FAIL |
| Fixed 20-session shifted graph (two-sided NW) | -0.004250 | -0.3052 | 0.760208 | PASS (|t| < 2) |
| Variant 2 sensitivity, 60-session graph (one-sided NW) | 0.003702 | 0.2675 | 0.394527 | Reported only; cannot replace variant 1 |
| Variant 1 net portfolio excess vs EW30 (one-sided block bootstrap) | — | — | Not run | Portfolio stage excluded from this task |

## Permutation null distribution

- Draws: 500; fixed seed: `20261110`; finite-sample one-sided randomization p-value: 0.307385; observed percentile: 69.4%.
- Mean-IC quantiles (min, 5th, 25th, median, 75th, 95th, max): -0.022114, -0.007877, -0.000836, 0.003905, 0.008965, 0.015677, 0.028647.
- Full draw-by-draw mean IC and Newey–West t values are in `D5_PLACEBO_DRAWS.csv`.
- Time shift is one fixed, deterministic 20-session control, as clarified before freeze; its endpoint is the two-sided Newey–West test, not a randomized p-value.

## Plain-English reading

At least one registered primary or placebo condition failed, so D5 does not advance to a portfolio test.
The 60-session version is a fixed sensitivity only. Raw p-values are shown here; goal-wide Holm adjustment is maintained by the coordinator in `specs/r4_trials.md` and the corresponding Holm manifest, not recalculated in this run.

## Trial logging

Every computed D5 mechanism endpoint was appended through the harness trial logger. The portfolio endpoint is not logged as an outcome because it was not run.
