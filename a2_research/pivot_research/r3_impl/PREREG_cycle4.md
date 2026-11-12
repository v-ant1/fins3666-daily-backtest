# Preregistration: R3 implementer cycle 4

Saved before reading any cycle 4 test-period results. DSR cumulative trial count: approximately 98 (94 inherited plus four unique candidates; prior inventory approximate and correlated).

## Shared protocol and selection rule

- Use only the supplied Dow 30 (point-in-time roster) and cross-asset 30 files. Do not inspect or download the sealed-holdout list or data.
- Signal after close using completed prices and volumes. Execute next eligible session open on the 21-session engine grid anchored at 2020-11-27. Use .05% per side actual-trade costs, including initial purchase and terminal liquidation. Apply the validated engine's 1% L1 whole-rebalance no-trade band and compare to same-grid EW30.
- All scores are higher-is-more-desirable. Rank ascending with average ranks q from 0 to 1; target `w_i=(1/30)*(1+(2*q_i-1))` (a=1.0). Fully invested, long only, 30 names, no leverage/cash. All required observations must exist; do not shorten or impute.
- Exactly four candidates: `HVOL21_K15`, `HVOL21_K20`, `WEEKDAY63_SHR10`, `MONTHPHASE63_SHR10`. No further parameters.
- Selection windows only: Dow and cross-asset 2020-11-27 through 2022-12-30. For the two-candidate high-volume family, reject candidates with any invalid signal dates or mean actual turnover >50% in either universe; select highest unweighted mean of the two net annualized daily Sharpes, ties by lower mean turnover then listing order. For the one-candidate weekday and month-phase families, freeze the candidate only if valid and at or below the same turnover cap in both universes; otherwise freeze EW30. Save all choices before any development test run.
- Test every frozen non-EW family once on Dow 2023-01-03..2024-02-23, Dow 2024-12-06..2025-12-31, Dow 2026-01-02..2026-10-30, and cross-asset 2023-01-03..2026-10-30. No retuning.
- Report return, Sharpe, drawdown, TE, IR, active share, turnover, pooled 10-session circular block-bootstrap p-value (one-sided, 10,000 draws) and DSR using 98 trials. Evaluate criteria 1-5, and call out whether realized TE reaches the proposal's 3% target even if active share satisfies criterion 3.
- Future truncation compares signal weights computed with price/volume arrays ending at the signal close against full arrays. Month-phase may additionally use only the next 21 session *dates* from the known calendar to form phase counts; it must not inspect any later prices or volumes. Compare while retaining the known calendar dates.

## Exact candidate signals (IDEAS_cycle4.md)

- `HVOL21_K15` / `HVOL21_K20`: per asset dollar volume `raw close * volume`; for each event date d=t-83..t-21 compute shock versus median dollar volume of d-20..d-1, retain shocks >=1.5 or >=2.0, and average the adjusted-close forward 21-session return from d to d+21. Require at least five qualifying events at every used date; otherwise candidate invalid. Larger mean event return ranks higher.
- `WEEKDAY63_SHR10`: over 63 completed adjusted-close returns, compute same-date EW30 residuals; for each Monday-Friday average asset residual, shrink by n/(n+10), and equally average the five weekday means. Require >=8 observations for each weekday/asset.
- `MONTHPHASE63_SHR10`: over 63 completed adjusted-close returns, compute same-date EW30 residuals; average and shrink by n/(n+10) separately for calendar days 1-15 and 16-end. Weight these estimates by the counts of each phase among the next 21 eligible session dates. Require >=15 observations per phase/asset. Use only future calendar dates, never future observations.
