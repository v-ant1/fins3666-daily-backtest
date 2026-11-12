# Preregistration: R3 implementer cycle 3

Written before cycle 3 test-period analysis. Cumulative DSR trial input: 94 (approximate: 88 inherited + six cycle 3 candidates; variants are correlated).

## Frozen protocol

- Data: the supplied point-in-time Dow 30 and fixed 30-asset cross-asset files only. No sealed-holdout roster or prices will be accessed.
- Signal timing: signal after close from completed daily bars, execute at next eligible open. Enforce every specified 63-session history; no shortening or imputation. Adjusted close returns use the supplied adjusted close. Distribution uses both split-adjusted close and dividend-adjusted close and fails on inconsistent/missing inputs.
- Six tested candidates, exactly: IDIOSKEW63_a08, COSKEW63_a08, DIST63_a08, DIST63_a10, GAPVOL63_a08, GAPSHARE63_a08. Scores and formulas follow IDEAS_cycle3.md exactly. Larger desirability receives higher rank weight; average ranks for ties; r=(rank-1)/29; w=(1/30)*(1+a*(2*r-1)); a=.8 except DIST63_a10 where a=1.0.
- Long-only, fully invested, 30 names. Rebalance every 21 eligible sessions on the engine grid anchored at 2020-11-27. Skip only when target-vs-drifted L1 weight difference is below 1% of NAV; otherwise trade to target. Costs are 0.05% per side on actual traded notional, including initial purchase and final liquidation. EW30 uses the validated engine schedule, fills and costs.
- Selection, separately within the three idea families: use Dow and cross-asset selection periods 2020-11-27 through 2022-12-30 only. Exclude a candidate if signal validation fails or average actual turnover exceeds 50% per rebalance in either universe. Freeze the candidate with highest unweighted mean of the two net annualized daily Sharpes; ties go to lower mean turnover, then first listed. If neither candidate qualifies, freeze EW30. Record all three frozen choices before running any development test window.
- Test each frozen family exactly once on Dow 2023-01-03..2024-02-23, Dow 2024-12-06..2025-12-31, Dow 2026-01-02..2026-10-30, and cross-asset 2023-01-03..2026-10-30. No changes after test results. Report criteria 1-5, pooled bootstrap p-value and deflated Sharpe using 94 trials. Bootstrap: circular blocks of 10 sessions, 10,000 draws, one-sided excess-return test against EW30.
- Validate future truncation on every candidate signal by comparing weights from full and truncated histories at first, middle, and last eligible dates. Report attempted and completed series; technical verification reruns will be disclosed.

## Exact signal definitions

See r3_research/IDEAS_cycle3.md: (1) leave-one-out benchmark OLS residual population skew, score negative residual skew; (2) leave-one-out population co-skew, score raw co-skew; (3) 63-session distribution contribution `(adjclose_t/adjclose_(t-63))-(close_t/close_(t-63))`, a=.8 or 1; (4) 63-session sample SD of adjusted overnight gap times sqrt(252), negative score; (5) overnight squared-gap share of overnight plus intraday squared returns, negative score. Prices must be positive and all required observations present; fail invalid signal dates/runs.
