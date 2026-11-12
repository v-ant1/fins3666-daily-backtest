# D5 Evaluation of Results

## Direction summary

D5 tested whether five-session CLV pressure at the highest-dollar-volume Dow name in a two-digit-SIC group predicts same-sign next-week returns for its industry followers. The pre-outcome input gate passed: all 293 eligible fifth-session dates met the registered minimum, with 11 directed pairs per eligible date. The primary mechanism gate failed; under the preregistration this ends D5, so its portfolio and sealed holdout were not run.

| Direction | Mechanism prediction and horizon | Input feasibility | Mechanism estimate and gate | Placebo conclusion | Portfolio gate | Holdout gate | Overall status |
|---|---|---|---|---|---|---|---|
| D5 | Positive five-session follower rank IC from a 20-session dollar-volume leader's five-session CLV pressure to followers' next-open through fifth-close returns; mean IC ≥ 0.0183 and NW t ≥ 2.0 | Pass: 293/293 eligible dates; 11 directed pairs on each; at least 3 leaders and 3 SIC groups per date | **Fail:** mean IC 0.007455, NW t(4)=0.5644, one-sided raw p=0.286249; both registered primary thresholds missed | Mixed: reverse and shifted controls satisfy `|NW t|<2`, but permuted-leader comparison fails because observed percentile is 69.4%, below 95%, with randomization p=0.307385 | Not run: primary mechanism gate failed | Not run: only coordinator may run holdout, and D5 did not advance | **Failed; killed under frozen rule. No sensitivity rescue.** |

## Mechanism and placebo evidence

| Direction / endpoint | Estimate and horizon | NW statistic / raw p or randomization result | Frozen criterion | Pass, fail, or descriptive |
|---|---|---|---|---|
| D5-1 primary, 20-session graph | Mean rank IC 0.007455; five-session follower return | NW t(4)=0.5644; one-sided raw p=0.286249 | Mean IC ≥0.0183 and NW t≥2.0 | **Fail** |
| D5-2 reverse-edge deterministic control | Mean rank IC −0.001445 | NW t(4)=−0.0759; two-sided raw p=0.939479 | `|NW t|<2.0` | Pass as a negative-control check; not evidence that the network effect is null |
| D5-3 within-SIC leader permutations | Observed mean IC 0.007455; null 95th percentile 0.015677 | Observed percentile 69.4%; one-sided randomization p=0.307385; pooled null-series NW t=0.4879 | Observed IC above the 95th percentile of the 500-draw distribution | **Fail** |
| D5-4 fixed 20-session-shifted graph | Mean rank IC −0.004250 | NW t(4)=−0.3052; two-sided raw p=0.760208 | `|NW t|<2.0` | Pass as a deterministic control; not evidence that the network effect is null |
| D5-5 60-session sensitivity | Mean rank IC 0.003702; five-session follower return | NW t(4)=0.2675; one-sided raw p=0.394527 | Reported sensitivity; variant 1 alone can advance | Descriptive/inferential endpoint reported, but cannot replace failed primary |
| D5-6 portfolio net excess vs EW30 | Not measured | Not run | Tested only after primary mechanism gate passes | Not run |

The within-SIC permutation distribution used 500 draws and seed `20261110`; its observed 95th-percentile threshold is larger than the observed primary mean IC. The reverse-edge and shifted-graph results are near zero and meet the frozen absolute-t thresholds, but that is not a test of practical equivalence and does not repair the failed randomized-link comparison. D5 therefore does not show that the proposed SIC leader-to-follower network predicts returns beyond the registered control.

## Portfolio, multiplicity, and interpretation

No D5 portfolio was formed or evaluated. Gross/net performance versus EW30, Sharpe, drawdown, turnover, costs, active share, portfolio bootstrap p-value, and DSR are **not run**, not zero and not failed estimates. The trial log records five D5 inferential endpoints; the sixth registered D5 endpoint is the portfolio endpoint and remains not run.

Raw p-values above are those in `r4_harness/runs/D5/MECHANISM_RESULTS.md`. Holm-adjusted values are **pending the coordinator's complete 21-endpoint family calculation** and must not be inferred from D5-only p-values. D5's frozen selection rule bars variant 2 from rescuing variant 1.

**Plain-English reading:** the SIC leader CLV score did not meet the required effect-size or statistical-strength gate, and actual SIC-linked leaders did not beat the within-industry randomized control. The two deterministic controls were quiet, but that does not provide positive evidence of a network mechanism. D5 failed before portfolio testing and supplies no evidence that its signal survives costs or the holdout.

**Disclosed D5 timing deviation (R5 decision 9):** the SIC panel records filing dates rather than EDGAR acceptance timestamps, so the frozen 16:00 prior-session cutoff is implemented as usable on the first NYSE session strictly after the filing date. This imposes a later availability cutoff and is conservative with respect to look-ahead; report it with any D5 result. The DD and pre-2019 DOW lineage corrections in decision 8 are holdout-only according to the recorded decision and do not change this development result; L4 must repair/audit them before any holdout run.
