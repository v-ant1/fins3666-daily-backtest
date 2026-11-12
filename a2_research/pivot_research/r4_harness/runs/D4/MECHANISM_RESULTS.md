# D4 mechanism and placebo results

**Mechanism gate: FAIL.** Frozen SHA-256 verified: `ff169ae4e5339364a400b8bec85e9251c77862923dc94c0049f23d79a9059421`.
Development sample: 2020-11-27 to 2026-10-30; 1,488 sessions. No portfolio or holdout run.

## Registered endpoints

| Endpoint | Estimate / test | NW t (lag 4) | Raw p-value | Result |
|---|---:|---:|---:|---|
| D4-1 primary IC | -0.018074 | -2.41949 | 0.992229 | FAIL |
| D4-2 degree-preserving comparison | observed -0.018074; null p95 0.00645968 | -2.41949 | 0.956088 | FAIL |
| D4-3 random-link comparison | observed -0.018074; null p95 0.00921569 | -2.41949 | 0.978044 | FAIL |
| D4-4 fixed 20-session shift comparison | paired mean difference -0.00225443 | -0.624561 | 0.733871 | FAIL |
| D4-5 degree placebo equivalence | mean -0.00562786; 90% CI [-0.0121659, 0.000910169] | NA | 0.485737 | FAIL |
| D4-6 random-link placebo equivalence | mean -0.0033827; 90% CI [-0.00763595, 0.000870545] | NA | 0.177942 | FAIL |
| D4-7 shifted placebo equivalence | mean -0.0158196; 90% CI [-0.0276978, -0.00394135] | NA | 0.917982 | FAIL |
| D4-8 variant-2 IC | -0.00683667 | -0.7882 | 0.78471 | DIAGNOSTIC |

## Randomized placebo distributions

| Family | Draws | Mean IC quantiles (min, 5th, 25th, median, 75th, 95th, max) | p95 absolute draw mean |
|---|---:|---|---:|
| degree_preserving | 500 | -0.0328457, -0.0170691, -0.0103046, -0.00546044, -0.000957614, 0.00645968, 0.0123698 | 0.0170691 |
| random_links | 500 | -0.0267473, -0.0151998, -0.00878863, -0.00346162, 0.00172665, 0.00921569, 0.0188137 | 0.0160242 |

The 20-session shift is the frozen deterministic circular alignment, not a randomized family. Its endpoint is the paired Newey–West comparison of the primary and shifted date-wise IC series; the shifted-series equivalence test is reported separately.

## Placebo equivalence checks

| Family | Mean averaged IC | 90% NW CI | Larger TOST p | p95 absolute draw mean | Margin | Result |
|---|---:|---:|---:|---:|---:|---|
| degree-preserving | -0.00562786 | [-0.0121659, 0.000910169] | 0.485737 | 0.0170691 | 0.00577 | FAIL |
| random-link | -0.0033827 | [-0.00763595, 0.000870545] | 0.177942 | 0.0160242 | 0.00577 | FAIL |
| fixed 20-session shift | -0.0158196 | [-0.0276978, -0.00394135] | 0.917982 | 0.0158196 | 0.00577 | FAIL |

## Plain-English reading

A direction advances only if the primary IC, all three placebo comparisons, and all three placebo-equivalence checks pass. Variant 2 is an inferential diagnostic and cannot replace variant 1. Raw p-values are shown; round-wide Holm adjustment remains the coordinator’s responsibility.

## Trial logging

Endpoints D4-1 through D4-8 were each recorded once through the harness trial logger. The portfolio endpoint D4-9 was not run or logged as an outcome.
A preflight invocation stopped at the saved-NCP check before endpoint statistics because the old runner incorrectly required target-own CLV5. After removing that check, the endpoint computation ran once. A formatting error occurred after results were saved; Markdown and trial rows were finalized from that saved JSON without rerunning or recomputing endpoints.
