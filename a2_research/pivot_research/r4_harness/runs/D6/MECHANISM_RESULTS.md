# D6 mechanism and placebo results

**Primary mechanism gate: FAIL.** Frozen preregistration SHA-256 verified: `341a406f0de406a989bc3fe6195de08f127592f011e7bd975eb1519bd71949dd`.
Development targets: 2021-08–2026-09, 62 monthly observations. Only the five specified ETF development inputs were opened.
No portfolio stage or holdout data were run or opened.

## Registered endpoints

| Endpoint | Estimate / comparison | NW SE | NW t (lag 11) | Raw p | Holm adjusted p | Status |
|---|---:|---:|---:|---:|---|---|
| D6-1 12-minus-1 Treasury basket → SPY, β>0 | 0.0769213 | 0.100374 | 0.766344 | 0.221736 | Pending complete family | FAIL |
| D6-2 12-minus-1 SPY → equal-weight Treasury, β<0 | 0.00156874 | 0.0205715 | 0.0762576 | 0.530393 | Pending complete family | Secondary; cannot rescue primary |
| D6-3 observed vs circularly shifted bond signal, one-sided | observed β=0.0769213; null 95th pct=0.0949808; percentile=94.6% | — | — | 0.0558882 | Pending complete family | FAIL (β>95th pct required) |
| D6-4 six-minus-one Treasury basket → SPY, β>0 | 0.33799 | 0.128845 | 2.62323 | 0.004355 | Pending complete family | Sensitivity; cannot replace primary |
| D6-5 six-minus-one SPY → equal-weight Treasury, β<0 | 0.0480303 | 0.0409726 | 1.17225 | 0.879452 | Pending complete family | Sensitivity; cannot replace primary |
| D6-6 portfolio net excess vs EW5, β>0 | — | — | — | Not run | Not calculated | Not run (outside task scope) |

## Circular-shift placebo distribution

500 draws; seed `20261110`; offsets uniformly sampled with replacement from 12 through 50 sessions in the monthly observation index. The SPY own-trend control, SPY target series, and internal order of the circularly shifted bond signal were preserved.
Bond-to-SPY placebo-coefficient summary: min -0.148286, 5th pct -0.130439, 25th pct -0.0910929, median -0.0568858, 75th pct 0.0225566, 95th pct 0.0949808, max 0.159174; mean -0.0344883; SD 0.0696048.
The observed coefficient percentile is 94.6%; the one-sided finite-sample randomization p-value is 0.0558882. Full draw coefficients are in `D6_PLACEBO_BETAS.csv`.

## Fixed diagnostics

The 12-minus-1 reversed-direction regression is reported as D6-2 above. Target-own-trend-only regressions are reported below; they are diagnostics and are not Holm endpoints.
| Diagnostic | β | NW SE | NW t (lag 11) |
|---|---:|---:|---:|
| 12-minus-1: spy return on spy own trend | 0.0105878 | 0.0227404 | 0.465595 |
| 12-minus-1: treasury return on bond own trend | -0.0150435 | 0.0201063 | -0.748197 |
| six-minus-one: spy return on spy own trend | -0.0186322 | 0.0554852 | -0.335806 |
| six-minus-one: treasury return on bond own trend | -0.0198457 | 0.0687024 | -0.288865 |

## Interpretation and multiple testing

The primary gate fails because one or more of the frozen requirements (positive coefficient, Newey–West t≥2, and coefficient above the placebo 95th percentile) were not met.
The six frozen endpoints remain in the goal-wide Holm family. Holm-adjusted p-values are pending the coordinator’s complete D4–D6 outcome family; D4 endpoints have not all been run and D6-6 was not run because this dispatch excludes the portfolio stage. Raw p-values for all mechanism endpoints are shown above; no endpoint was dropped or rescued.

## Trial logging

D6 endpoints 1–5 were recorded through `run_registered_trial` and the harness `append_trial` logger in `specs/r4_trials.md`. D6-6 is recorded as not run in this report and was not logged as an outcome.
