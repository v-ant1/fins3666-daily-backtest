# Pre-registered selection protocol (written before this worker's runs)

## Variants fixed in advance

All portfolios are long-only, fully invested across the 30 names and rebalance every 21 sessions on the official next-open grid. The 63 completed daily close-to-close returns ending at each signal close define risk estimates. Each run uses actual traded notional, 5 bp per side, including initial and terminal costs. Eight portfolios are included: equal weight (EW30), inverse volatility (`ivol63`), inverse weighted degree (`low_degree`), inverse eigenvector centrality (`low_eigen`), inverse heat-kernel connectivity (`inv_heat`), hierarchical risk parity (`hrp`), inverse degree times inverse volatility (`degree_ivol`), and inverse heat connectivity times inverse volatility (`heat_ivol`). The undirected graph symmetrizes the union of each node's five strongest positive correlations in the 63-session window; heat uses exp(-L) with unit diffusion time. The blends multiply normalized component weights then renormalize. HRP uses single-linkage clustering on correlation distance and recursive inverse-variance bisection.

## Selection rule

Use only the two selection windows, Dow 30 (2020-11-27 through 2022-12-30) and cross-asset 30 ETFs over the same dates. For each of the eight portfolios calculate annualized daily-return Sharpe (zero risk-free rate) and average actual traded notional divided by pre-trade equity per rebalance. Exclude any portfolio above 50% mean notional turnover per rebalance in either universe. Among the remaining portfolios select the one with the highest simple average of its two universe Sharpes. Break ties by higher average information ratio versus that universe's EW30, then by lower average maximum drawdown magnitude, then lower average turnover. EW30 is eligible and can be selected. Freeze this one portfolio and report it unchanged on every registered test window. If no portfolio qualifies, freeze EW30. No parameter or portfolio changes are allowed after selection.

## Tests to report once

Dow 30: 2023-01-03..2024-02-23, 2024-12-06..2025-12-31, and 2026-01-02..2026-10-30. Cross-asset 30 ETFs: 2023-01-03..2026-10-30. Also report all eight fixed portfolios descriptively on the tests to show the full pre-specified screen, without selecting from test results.

## Inference plan

Use daily strategy-minus-EW30 returns; report annualized Sharpe, information ratio, maximum drawdown, CAGR, and turnover. Bootstrap the mean active return with a circular 10-session block bootstrap, 5,000 draws, seed 3666, two-sided, demeaned under the null and plus-one p-value correction. Report a deflated Sharpe probability using an effective cumulative trial count of 78 (the approximately 70 previous variants plus these eight). The 78 independent-trial approximation is deliberately conservative but cannot model dependence among related variants; treat results as descriptive, not proof.
