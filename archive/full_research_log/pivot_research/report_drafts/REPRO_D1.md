# D1 H1 Independent Reproduction

## Result

I independently re-derived the D1 S&P 500 mechanism endpoint from the development-only input bundle. The bundle SHA256 is `33b977f9454b50f1d197751a6883d92bdd45e3041ed92082a18e43fc32108538`, matching the value recorded in `r6_D1/RESULTS.md`; the script refuses to run if this hash changes.

| Statistic | Independent result | `r6_D1/RESULTS.md` | Difference from displayed value | 3 significant figures |
|---|---:|---:|---:|---:|
| Mean date-wise Spearman IC | 0.00937419239 | 0.0093742 | −0.00000000761 | **0.00937** |
| Newey–West t, lag 4 | 1.90801079 | 1.9080 | +0.00001079 | **1.91** |

There is no material discrepancy: both values agree with the recorded results to three significant figures, and the tiny differences above are consistent with rounding in `RESULTS.md`.

## Reproduction method

Run from the project root with `python report_drafts/repro/reproduce_d1_h1.py`. The script independently:

1. Verifies the input bundle SHA256 and checks its dates are within 2020-06-01 through 2026-10-30.
2. Forms the frozen five-session negative-pressure score as the negative arithmetic mean of the paired nonnegative facility short-volume ratios.
3. Computes the registered t+2 adjusted-open to t+6 adjusted-close forward return, selects the every-fifth-session formations beginning 2020-11-27, and applies the point-in-time S&P roster plus finite-score and finite-forward-return mask.
4. Calculates each formation-date Spearman rank correlation, averages the 297 finite ICs, and applies the Bartlett Newey–West mean t-statistic with lag 4.

The run reported 1,614 bundle sessions, 297 formation dates, 297 finite ICs, and 458–500 eligible names per formation. The independent script does not import or invoke the guarded D1 runner and does not write endpoint logs. It reads no data outside the specified development bundle and does not access holdout data.

## Files

- Independent script: [`repro/reproduce_d1_h1.py`](repro/reproduce_d1_h1.py)
- Frozen result for comparison: [`../r6_D1/RESULTS.md`](../r6_D1/RESULTS.md)
