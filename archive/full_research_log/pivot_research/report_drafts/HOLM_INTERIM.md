# Interim Holm correction for D4–D6

This table applies the Holm step-down correction to the full 21-endpoint family listed in `specs/r4_trials.md`: nine D4 endpoints, six D5 endpoints and six D6 endpoints. Raw p-values below are copied from the trial log. The three portfolio endpoints were not run because their mechanism gates failed; as requested, each is included as p=1 for this interim family calculation. D6's accidental and official log rows (rows 6–10 and 11–15) report identical values, so each D6 endpoint is counted once.

Holm adjusted p-values are calculated by sorting all 21 raw p-values from smallest to largest, multiplying the p-value at sorted rank *i* by `21 − i + 1`, taking the cumulative maximum, and capping at 1. In plain English, this makes it harder for a result to look significant just because many registered tests were tried; it controls the chance of at least one false positive across this family. A raw p-value is the unadjusted result for one endpoint. No new mechanism or portfolio outcome was computed. Endpoint labels follow each preregistration and the goal-wide manifest.

| Endpoint | Registered test | Trial-log source | Raw p | Holm-adjusted p |
|---|---|---:|---:|---:|
| D4-1 | Variant 1 primary NCP mean rank IC, positive | 16 | 0.99222889 | 1.00000000 |
| D4-2 | Variant 1 vs degree-preserving graph, randomization | 17 | 0.95608782 | 1.00000000 |
| D4-3 | Variant 1 vs random-link graph, randomization | 18 | 0.97804391 | 1.00000000 |
| D4-4 | Variant 1 vs fixed 20-session shift | 19 | 0.73387050 | 1.00000000 |
| D4-5 | Degree-placebo equivalence | 20 | 0.48573705 | 1.00000000 |
| D4-6 | Random-link-placebo equivalence | 21 | 0.17794169 | 1.00000000 |
| D4-7 | Shifted-placebo equivalence | 22 | 0.91798249 | 1.00000000 |
| D4-8 | Variant 2 mean rank IC, positive | 23 | 0.78471021 | 1.00000000 |
| D4-9 | Variant 1 net excess return vs EW30, one-sided block bootstrap | Not run | 1.00000000* | 1.00000000 |
| D5-1 | Variant 1 primary follower mean rank IC, positive | 1 | 0.28624857 | 1.00000000 |
| D5-2 | Reverse-edge mean IC, two-sided | 2 | 0.93947879 | 1.00000000 |
| D5-3 | Observed vs within-SIC permuted-leader placebo | 3 | 0.30738523 | 1.00000000 |
| D5-4 | Fixed 20-session shifted-graph mean IC, two-sided | 4 | 0.76020789 | 1.00000000 |
| D5-5 | Variant 2 60-session sensitivity mean IC, positive | 5 | 0.39452692 | 1.00000000 |
| D5-6 | Variant 1 net excess return vs EW30, one-sided block bootstrap | Not run | 1.00000000* | 1.00000000 |
| D6-1 | 12-minus-1 bond-to-SPY coefficient, positive | 11 (duplicate of 6) | 0.22173578 | 1.00000000 |
| D6-2 | 12-minus-1 SPY-to-Treasury coefficient, negative | 12 (duplicate of 7) | 0.53039291 | 1.00000000 |
| D6-3 | Primary coefficient vs circular-shift placebo | 13 (duplicate of 8) | 0.055888224 | 1.00000000 |
| D6-4 | 6-minus-1 bond-to-SPY sensitivity, positive | 14 (duplicate of 9) | 0.0043550034 | 0.09145507 |
| D6-5 | 6-minus-1 SPY-to-Treasury sensitivity, negative | 15 (duplicate of 10) | 0.87945218 | 1.00000000 |
| D6-6 | Portfolio net excess return vs EW5, positive | Not run | 1.00000000* | 1.00000000 |

\* Assigned p=1 only for this interim Holm family because the registered portfolio endpoint was not run. It is not an observed p-value.

## Reading

No endpoint in this 21-test family has a Holm-adjusted p-value below 0.05. The smallest adjusted value is 0.091455 for D6-4, a registered six-minus-one sensitivity; it does not change the failed primary mechanism or advance a portfolio. This is an interim correction of logged raw p-values and the explicitly assigned p=1 values for the unrun portfolio tests. The coordinator maintains the authoritative endpoint family and trial record in `specs/r4_trials.md`.

**Terms:** an endpoint is one pre-specified statistical question. D4/D5 rank IC is the correlation between a signal's stock ranking and the later-return ranking. A placebo is a deliberately broken link or timing comparison. “Six-minus-one” means a six-month trend excluding the latest month. The 21 endpoints (9 D4, 6 D5, 6 D6) are not 21 strategy variants; the fixed DSR trial-count input is 30. The p=1 entries are bookkeeping assignments for the unrun portfolio endpoints, not measured evidence that their effects are absent.
