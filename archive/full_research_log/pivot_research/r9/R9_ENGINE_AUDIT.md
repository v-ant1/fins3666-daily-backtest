# R9 Engine Audit

**Scope.** Development-only audit using `r9/data/J2_DEV_FROM_20201127.npz` and the J1 score bundle filtered to 2020-11-27 through 2026-10-30. No sealed holdout input or pre-2020-11-27 data was opened. `r9/holdout_runner.py` was not run; `specs/r9_HOLDOUT_APPROVED.txt` was not created. The implementation corrections and the variance decision are recorded in `specs/r9_decisions.md`.

## Verdict

**A/B/C verdict:** A Predictability: J1 passed its registered mechanism and placebo tests, but the portfolio edge remains small and unstable. B Net profitability: marginal and construction-dependent; V5 has positive dev excess, but p=0.188 and a net Sharpe advantage of 0.0435 over EW30. C Qualification: not qualified; holdout remains blocked pending supervisor/user approval after this audit.

## DSR defect and correction

The old implementation in `r9/j2_variants.py:55-71` compared the observed daily Sharpe directly with `E[max Z]` (about 1.7 at 15 trials), as if the cross-trial daily-Sharpe standard deviation were one. Daily Sharpe is around 0.05–0.06 here, so the old DSR underflowed to 0.0000 for every variant. The corrected threshold is `SR0 = sqrt(V) * E[max Z]`, with the existing skew/kurtosis adjustment retained. The primary variance decision was logged before corrected DSR calculations.

R6 counted three trials (D1/E1/J1), but the R6 final record says D1 and E1 never reached a portfolio run. Their portfolio Sharpe estimates do not exist. Therefore an exact cross-trial variance across all 15 portfolio Sharpes cannot be reconstructed without inventing observations. The table uses the sample variance, ddof=1, of the 12 available corrected R9 daily Sharpe estimates (`V=0.0000841539`) while retaining the 15-trial expected maximum; it also gives the requested null alternative `V=1/(T-1)`. This is a disclosed 12-stream estimate, not a 15-observation estimate. The holdout helper now defaults to that available estimate; a true 15-stream primary estimate would require the missing R6 returns.

| Variant | Old DSR (unscaled) | Corrected primary: observed R9 V, 15 trials | Null alternative: V=1/(T-1) |
|---|---:|---:|---:|
| V0 | 0.0000 | 0.9148 | 0.5848 |
| V1 | 0.0000 | 0.7026 | 0.2652 |
| V2 | 0.0000 | 0.8230 | 0.4088 |
| V3 | 0.0000 | 0.9328 | 0.6317 |
| V4 | 0.0000 | 0.8983 | 0.5458 |
| V5 | 0.0000 | 0.9422 | 0.6631 |
| V6 | 0.0000 | 0.7955 | 0.3706 |
| V7 | 0.0000 | 0.8246 | 0.4104 |
| V8 | 0.0000 | 0.8677 | 0.4829 |
| V9 | 0.0000 | 0.7002 | 0.2630 |
| V10 | 0.0000 | 0.8881 | 0.5236 |
| V11 | 0.0000 | 0.8128 | 0.3935 |

The R6 helper in `r4_harness/phase3.py:385-397` has the same unscaled expected-maximum bug. It and other frozen R6 files were left untouched. The implementation fix is in `r9/holdout_runner.py:123-142`; the development correction is in `r9/j2_variants_v2.py:55-74, 405-420`.

## Turnover reconciliation

One definition is used throughout: **buys plus sells divided by NAV at the rebalance**, averaged over scheduled rebalance dates. In the weight-based engine this equals `sum(abs(target_weight - pretrade_weight))`; a full swap can therefore be 200%. The V0 J1 baseline has a registered 50% trade cap, so both its mean and maximum are 50%. Other variants have no such cap and may reach 200%. Smoothing turnover declines as its window grows (98.46% → 82.40% → 69.66%); those means remain above capped V0 because V0 is capped. V3/V4/V5 maximum 200% means a full replacement can still occur on some dates.

| Variant | Mean turnover | Maximum turnover |
|---|---:|---:|
| V0 | 50.00% | 50.00% |
| V1, corrected | 136.73% | 200.00% |
| V2 | 103.84% | 200.00% |
| V3 | 98.46% | 200.00% |
| V4 | 82.40% | 200.00% |
| V5 | 69.66% | 200.00% |
| V6 | 139.42% | 200.00% |
| V7 | 103.06% | 176.75% |
| V8 | 78.55% | 141.81% |
| V9 | 141.44% | 200.00% |
| V10 | 69.15% | 98.68% |
| V11 | 103.00% | 149.94% |

Turnover is calculated in `r9/j2_variants_v2.py:258-266`; the V0 cap is applied at lines 255-257. The independent J1 replay uses the same L1 turnover definition at `report_drafts/repro/j1_portfolio_replay.py:103-111`. The apparent inconsistency was a cap difference and was not a buy-only versus buys-plus-sells mismatch.

## V1 empty-book bug

V1's -89.59% excess return on 0.35% mean turnover was an implementation bug. `target_for` prefilled each selected name with 1/k, then calculated residual capital as `1 - target.sum()` while those provisional fill weights were still present. With five new names, residual capital became zero and all five final weights were reset to zero. The engine then held an empty cash book; its weight sum and number of holdings were both zero throughout the run. This explains the anomalous near-zero turnover and large relative loss.

The original defect is in `r9/j2_variants.py:177-186`; the correction clears provisional fill weights before allocating residual capital (`r9/j2_variants_v2.py:180-191`). V1 now maintains a fully invested five-name book (weight sum 1.0; five names) but still returns **-42.77% net excess**, with **136.73% mean / 200% maximum turnover**. That is a poor strategy result, not a remaining empty-book defect.

## V0 versus official J1

The official J1 result is **+1.03%** net cumulative excess over EW30 (`R6_FINAL.md:111`; exact saved value +1.0276%). V0's common-window replay is **+5.15%**. The all-variant development engine chooses 2021-03-04 as its first formation because every candidate needs a valid target/lookback; its first return is 2021-03-05. The official J1 daily series begins 2020-11-30, after initializing in the earlier development period and skipping ten insufficient-signal formations.

On the matched return dates from 2021-03-05 through 2026-10-30, the official series compounds to **+5.77%** strategy-minus-EW30, versus **+5.15%** for V0 (0.62 pp difference). Daily correlations are 0.9985 for strategy and 0.9990 for EW30; mean absolute daily differences are 0.0201 pp and 0.0205 pp. Thus the start/slice accounts for most of the headline gap: the official full-window +1.03% includes the early period that the R9 common-start replay excludes. The remaining common-window difference reflects the different starting book/state and path implementation; it is small day to day but not an exact match. Both use the same staged J1 signal bundle and development price source, with R9 consuming the trimmed 2020-11-27+ panel.

## Corrected 12-variant rerun and unchanged selection

All 12 variants were rerun from the allowed development panel in `r9/j2_variants_v2.py`, with identical 2021-03-04 common formation, costs and bootstrap settings. Rule 5 remains exactly the preregistered rule: highest strategy net Sharpe among active share ≥50% and cost/gross edge <50%, ties by lower turnover (`specs/r9_rules.md`, rule 5; `r9/j2_variants_v2.py:422-426`). V3/V4/V5 remain eligible; **V5 still wins**. Its corrected DSR is below the 0.95 gate under both reported variance choices. This development rerun did not change J2 or its frozen preregistration.

| Variant | Net excess | Strategy net Sharpe | Mean turnover | Cost / gross edge | Rule-5 eligible |
|---|---:|---:|---:|---:|:---:|
| V0 | +5.15% | 0.8360 | 50.00% | 53.18% | No |
| V1 | -42.77% | 0.4816 | 136.73% | n/a | No |
| V2 | -17.68% | 0.6484 | 103.84% | 236.30% | No |
| V3 | +32.60% | 0.8871 | 98.46% | 34.46% | Yes |
| V4 | +12.05% | 0.7941 | 82.40% | 46.05% | Yes |
| V5 | +40.13% | 0.9239 | 69.66% | 22.49% | Yes |
| V6 | -24.74% | 0.6063 | 139.42% | n/a | No |
| V7 | -25.66% | 0.6504 | 103.06% | n/a | No |
| V8 | -18.71% | 0.7276 | 78.55% | 1,508.48% | No |
| V9 | -45.86% | 0.4788 | 141.44% | n/a | No |
| V10 | -3.99% | 0.7706 | 69.15% | 95.23% | No |
| V11 | -22.84% | 0.6319 | 103.00% | 679.13% | No |

The rerun output, including input hashes, full daily development series and diagnostics, is `r9/R9_VARIANTS_V2.json`. Original `r9/j2_variants.py`, `r9/R9_VARIANTS.json`, `specs/r9_variant_log.md` and `specs/r9_prereg/J2.md` were not changed.

## Probability of passing all Rule-6 gates

A planning simulation resampled paired PIT-EW30 daily returns and centered V5 excess-return residuals in circular 10-session blocks, then added V5's observed development mean excess (0.0001575/day; about 3.97% simple annualized) as the assumed true effect. It generated 3,000 synthetic 10.8-year paths (2,722 sessions; seed 20261111). Gates were net cumulative excess >0, annualized net Sharpe above EW30, one-sided p<0.05, and corrected DSR>0.95. The p gate uses a Bartlett HAC normal approximation with lag 9 as a computational approximation to the registered block-bootstrap p; this is a planning simulation, not a holdout test.

| Gate | Estimated pass probability, primary V | Null-variance sensitivity |
|---|---:|---:|
| Positive net cumulative excess | 85.7% | 85.7% |
| Net Sharpe above EW30 | 58.8% | 58.8% |
| One-sided p < 0.05 | 35.6% | 35.6% |
| DSR > 0.95 | 72.4% | 34.3% |
| **All four gates** | **32.7% (MC SE 0.9 pp)** | **21.6% (MC SE 0.8 pp)** |

The point estimates are above the requested ~20% trigger, but the null-variance sensitivity is close to it, and the primary 15-stream variance is unavailable. If running a parallel path to reduce the one-shot risk, the stronger candidate is **S&P weekly with a turnover cap**: it tests the portfolio construction directly in a broader universe, while D1 remains an R6 near-miss that did not reach a portfolio stage. This is a recommendation only; no parallel trial was started or logged here.

## File references and status

- DSR old R9 formula: `r9/j2_variants.py:55-71`; corrected formula and variance default: `r9/holdout_runner.py:121-142`.
- Same DSR defect in R6 helper: `r4_harness/phase3.py:385-397`.
- Variant target construction and V1 correction: `r9/j2_variants_v2.py:94-191`; turnover/cost mechanics: `r9/j2_variants_v2.py:248-266`.
- Rule-5 selection and output: `r9/j2_variants_v2.py:398-456`; unchanged rule text: `specs/r9_rules.md` rule 5.
- Decision and implementation-correction log: `specs/r9_decisions.md`.

**Holdout remains blocked.** The DSR implementation is corrected, but the audit does not authorize a holdout run and does not create the approval marker.
