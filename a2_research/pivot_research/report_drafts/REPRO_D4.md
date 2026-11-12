# Independent D4 primary-result reproduction

## Result

I independently re-derived D4-1 from `r4_harness/runs/D4/D4_INPUTS.npz` using a new minimal script at `report_drafts/repro/reproduce_d4.py`. The script does not import the D4 runner, input builder, or harness. It reads the saved adjusted open and close matrices, forms each stock's return from adjusted open at session `t+1` to adjusted close at `t+5`, ranks that return against the saved NCP score within the point-in-time roster on each date, and averages the date-wise Spearman correlations.

| Measure | Independent result | Saved D4 result | 3 significant figures |
|---|---:|---:|---:|
| Mean primary IC | −0.018073998721416292 | −0.018073998721416292 | −0.0181 |
| Newey–West t, Bartlett lag 4 | −2.41949162378736 | −2.41949162378736 | −2.42 |
| Finite IC dates | 1,479 | 1,479 | — |

Both statistics match exactly at the stored precision, and therefore agree to three significant figures. The development bundle covers 1,488 sessions from 2020-11-27 through 2026-10-30; the independent calculation used no holdout data. Reproduction output is saved in `report_drafts/repro/REPRO_D4_VALUES.json`.

## Preflight and trial-log audit

The results report says the first guarded preflight stopped at an NCP consistency check because the runner incorrectly required the target stock's own CLV5 to be present. That invocation stopped before computing endpoint statistics or adding a trial row. After the check was corrected, the registered D4-1 through D4-8 endpoint run completed once. The report says a later formatting error happened after the endpoint JSON had been saved; the Markdown and log rows were then finalized from that saved result without recomputing the outcomes.

I checked `specs/r4_trials.md`: D4 endpoints D4-1 through D4-8 appear as rows 16–23, exactly once each, with eight distinct endpoint labels. This makes the D4 endpoint log complete and single. D4-9 is the portfolio endpoint and was neither run nor logged, as the frozen mechanism-stage instructions require.

## Interpretation

The registered prediction was a positive IC: stronger peer CLV pressure should rank stocks with higher subsequent returns. The observed IC is negative and its Newey–West t-statistic is significantly below zero in the negative direction. In plain English, within this sample, stocks with stronger common-owner peer pressure tended to have lower subsequent returns in relative rank—a short-term reversal pattern that runs opposite to the registered persistence/spread prediction. This is a description of the mechanism result only; it does not propose a trading rule.
