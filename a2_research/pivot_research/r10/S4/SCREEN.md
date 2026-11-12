# R10 S4 — Calendar, seasonality and low-risk screen

**Decision: NO-GO for freezing all six ideas.** Each preregistered hypothesis was measured once on the development panel. None satisfies the gate of net excess > 0, Newey–West t ≥ 2 and 2010–2015 haircut pass probability ≥ 30%.

| Idea | N months | Net excess/month | NW t (lag 3) | 2010–15 projected N / MDE | Haircut pass probability | Net excess at 5 / 10 / 20 bp one-way | Positive years | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| S4-01 Low realized volatility | 68 | −0.129% | −0.49 | 68 / 0.729% | 3.1% | −0.106% / −0.129% / −0.177% | 3/6 | NO-GO |
| S4-02 Low market beta | 68 | −0.330% | −1.07 | 68 / 0.861% | 1.7% | −0.307% / −0.330% / −0.377% | 2/6 | NO-GO |
| S4-03 Turn-of-month seasonality | 62 | +0.196% | +0.89 | 62 / 0.703% | 9.7% | +0.218% / +0.196% / +0.152% | 4/6 | NO-GO |
| S4-04 Pre-holiday seasonality | 68 | −0.161% | −0.95 | 68 / 0.511% | 2.1% | −0.127% / −0.161% / −0.228% | 2/6 | NO-GO |
| S4-05 52-week-high proximity | 61 | −0.216% | −0.92 | 61 / 0.720% | 2.2% | −0.168% / −0.216% / −0.312% | 1/6 | NO-GO |
| S4-06 Residual momentum | 58 | +0.338% | +1.49 | 58 / 0.702% | 14.8% | +0.360% / +0.338% / +0.294% | 5/6 | NO-GO |

## GO list

None. S4-06 is the strongest result, with +0.338% monthly net excess and five positive years, but its NW t is 1.49 and haircut pass probability is 14.8%. S4-03 also has positive net excess, but its t is 0.89 and probability is 9.7%.

## Frozen designs and execution

All six definitions were appended to `specs/r10_trial_log.md` before outcomes. The shared monthly harness uses adjusted closes and PIT roster from `r9/data/J2_DEV_FROM_20201127.npz`, calendar month-end formations, equal-weight long-only top quintiles, and the EW PIT S&P benchmark on matching formation/exit dates. It charges 10 bp one-way on absolute weight changes, including initial entry; sensitivities use the same weights and returns at 5 and 20 bp. NW t uses lag 3. The 2010–2015 planning rule projects N from observed monthly sample rate across six years, uses MDE = 2.4865 × sample SD / sqrt(N), and estimates the positive-mean gate probability after halving the dev mean. These are planning estimates, not holdout results.

The synthetic-only harness passed for all six selectors before the outcome run. An initial real-data attempt stopped before cohort calculations because pandas rejected a NumPy date scalar; that issue was fixed and recorded before rerunning synthetic validation. The one corrected development run then produced all six outcomes. Its 52-week-high calculation emitted an all-NaN-slice warning for assets with no prices in the window; those assets fail the preregistered 200-observation eligibility minimum, and no result was rerun or adjusted after outcome access.

The observed annual positive counts were 3/6, 2/6, 4/6, 2/6, 1/6 and 5/6 for S4-01 through S4-06 respectively. Average benchmark price coverage was 95.5%; average signal eligibility coverage ranged from 76.5% to 91.1% of the PIT roster depending on signal. The S&P session calendar itself defines pre-holiday sessions as dates before a gap of at least three calendar days; no external holiday file was used.

Only the named development NPZ was used. Dates were bounded to 2020-11-27 through 2026-10-30 before price/roster slices were selected. No sealed holdout files, pre-boundary price/return values, API credentials or order routes were accessed. Historical 2010–2015 point-in-time membership and adjusted-price completeness remain unverified; the projected N is not observed holdout coverage.

## Artifacts

- `s4_screen.py` — shared harness, synthetic validation and single development runner.
- `DEV_RESULT.json` — cohort-level outcomes and metric summaries.
- `specs/r10_trial_log.md` — six frozen registrations, pre-outcome crash/fix and outcome record.

