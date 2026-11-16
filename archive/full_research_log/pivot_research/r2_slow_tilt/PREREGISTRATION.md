# R2-2 protocol preregistration (written before selection runs)

## Candidate set (four variants originally listed; three active after amendment)
All candidates use the supplied daily adjusted OHLCV data, 0.05% cost per side on actual traded notional, next-open fills, and a 21-session rebalance interval. Each is a long-only, fully invested tilt across all 30 assets: `weight_i = (1/30) * (1 + a * (2 * rank_i - 1))`, with percentile ranks on [0,1]. All strategies and EW30 start at the same selection anchor and use the point-in-time Dow roster. Candidate signals:

1. `rev21_a05`: ascending percentile rank of negative 21-session close-to-close return, a=0.5.
2. `rev21_a10`: same signal, a=1.0.
3. `volrev21_a05`: ascending percentile rank of negative 21-session return divided by trailing 63-session annualized volatility (risk-scaled contrarian return), a=0.5.
4. `mom12_1_a05`: ascending percentile rank of 12-month return skipping the most recent 21 sessions, a=0.5 (252-session formation, 21-session skip). This is the opposite-hypothesis momentum candidate.

## Selection rule
Use only the preregistered selection dates 2020-11-27 through 2022-12-30 in Dow 30 and cross-asset 30. For each candidate, compute annualized daily Sharpe (zero risk-free rate) and average actual traded notional / pretrade equity per rebalance in each universe. Exclude a candidate if its mean turnover exceeds 50% in either universe. Among remaining candidates, choose the one with the highest unweighted mean of its two universe Sharpes. Break ties by lower mean turnover, then lower alpha. If no active candidate qualifies, freeze EW30. Do not use any test-period result in this choice.

## Test periods (one report, no retuning)
Dow: 2023-01-03..2024-02-23, 2024-12-06..2025-12-31, and 2026-01-02..2026-10-30. Cross-asset: 2023-01-03..2026-10-30. Report against same-universe EW30 and SPY, after costs, with Sharpe, information ratio, max drawdown, turnover, cost drag, block-bootstrap p-values, and deflated Sharpe adjusted for the cumulative approximate 70 prior variants plus the three active candidate variants (about 73 total).

The originally listed candidate count was four; the amendment below removes 12-1 momentum before any selection run, leaving three active candidate variants. EW30 is the benchmark, not a candidate. A full IS run for each candidate-universe pair is one selection run. Full test runs happen only after the chosen candidate is recorded in the frozen-choice file.
## Preregistration amendment (before first result)

The cross-asset price files begin 2020-06-01 and have no earlier lookback history. A 252-session formation period is therefore unavailable for the first part of the required 2020-11-27..2022-12-30 selection interval. To keep both selection samples on the identical required dates, remove `mom12_1_a05` from the tested candidate set before any selection run. Three active candidates remain. No returns, performance metrics, or test-period data were examined when making this amendment. The 12-1 momentum idea is not evaluated in this worker's report.


