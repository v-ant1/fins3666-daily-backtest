# Independent criterion-4 bound check (synthetic)

**Scope.** This note estimates the rank-IC scale needed for a top-five Dow-like book to clear criterion 4: positive net excess return versus EW30, higher net Sharpe than EW30, and a one-sided block-bootstrap result that survives Holm adjustment. All inputs below are design assumptions or synthetic Monte Carlo output; I did not load project price, signal, or holdout data for these calculations.

**Process disclosure.** During initial context gathering, I accidentally opened `CRITERION4_BOUND_AUDIT.md` and a portion of `specs/r4_trials.md` before finishing this independent derivation. The trial log displayed outcome rows. I did not use those outcomes in the calculations below, but this means the requested blind ordering was not preserved; the report is an independent calculation, not a blinded replication. No holdout files or values were opened.

## Assumptions and method

I modeled 30 names, a six-year daily series (1,500 sessions), 6% monthly cross-sectional/idiosyncratic dispersion, and 0.05% transaction cost per dollar of total traded notional. A common factor supplies approximately 16% annual volatility; combined with 20.8% annualized idiosyncratic volatility, this implies about 0.37 pairwise name correlation and an EW30 annual volatility near 16.4%. I set EW30's assumed Sharpe to 0.9, so its annual mean is about 14.8%. These are deliberately explicit synthetic inputs, not measured Dow statistics.

For a long-only top-five book, the active weights versus EW30 are +1/5 in each selected name and −1/30 in every name, so the sum of squared active weights is 1/6. The implied active-return standard deviation is 6% × √(1/6) = 2.45% per month, or 8.49% annualized. For a 100%-gross long-short book (+10% in each of the top five and −10% in each of the bottom five), the squared weights sum to 0.20, implying 2.68% monthly and 9.30% annual active volatility. The common factor cancels from both active books under this equal-covariance model.

I used the harness's rank-to-tail planning map: expected monthly top-five active gross return ≈ IC × monthly dispersion × √12 × (0.5 − 5/60), or about **0.0866 × IC** at 6% dispersion. The long-short book has the same first-order coefficient at 100% gross exposure. The annual gross-return coefficients are about 1.04 × IC for monthly, 2.13 × IC for weekly, and 4.76 × IC for daily rebalancing. This linear map is a planning approximation; actual rank, turnover, cap binding, and weight drift can change it.

For the Holm test, I used the conservative first-step threshold for 21 endpoints, p < 0.05/21 = 0.00238 (normal one-sided z ≈ 2.82). I also report an 80% power target, which uses z ≈ 2.82 + 0.84 = 3.66. Holm may permit a larger p-value for an endpoint later in the ordered step-down, but its rank is unknown before the family results exist, so the first-step threshold avoids assuming a favorable rank.

The design-level power check used the existing synthetic-only `power_sim.py` with 30 names, 6 years of observations, null rank-IC SD 1/√29, 1,000 Monte Carlo replications, and these illustrative signal autocorrelations: 0.25 monthly (72 observations, NW lag 20), 0.65 weekly (312 observations, NW lag 4), and 0.90 daily (1,500 observations, NW lag 0). The simulator reports the following 80%-power MDEs for its t ≥ 2 gate, before Holm: monthly 0.079, weekly 0.048, daily 0.014. Scaling the critical normal deviation from 2 + 0.84 to 2.82 + 0.84 gives Holm-first-step mechanism MDEs of approximately 0.102, 0.061, and 0.018. The portfolio estimates below are separate: they include active portfolio risk, benchmark mean where relevant, trading cost, and the multiple-test cutoff.

To turn the block-bootstrap cutoff into an effective-time planning number, I used the same autocorrelation assumptions. Monthly and weekly effective counts come from `power_sim.py`'s Bartlett HAC design effect: 44.4 effective monthly observations (3.70 effective years) and 123 effective weekly observations (2.37 years). Daily uses a ten-session block design effect of 7.28 under AR(1) ρ=0.90, giving about 206 effective sessions (0.82 years). This daily adjustment is intentionally conservative and is only a planning proxy for a circular block bootstrap, not a substitute for applying the bootstrap to a realized path.

## Estimated IC hurdle

The table gives the approximate IC required to reject the Holm first-step null at either 50% detection probability (the critical effect at the threshold) or 80% power. Costs assume 20% total-notional turnover per rebalance: annual cost is 0.12% monthly, 0.50% weekly, or 2.52% daily. For long-only, the test is on net excess versus EW30; with common risk cancelling, the resulting edge also clears the Sharpe comparison in this model. For long-short, the strategy must first cover EW30's assumed 14.8% annual mean, then produce enough excess return for the Holm test; this is why its IC bar is much higher.

| Rebalance | Long-only IC, 50% power | Long-only IC, 80% power | Long-short IC vs EW30, 50% power | Long-short IC vs EW30, 80% power |
|---|---:|---:|---:|---:|
| Monthly | 0.121 | **0.157** | 0.410 | **0.490** |
| Weekly | 0.077 | **0.099** | 0.235 | **0.283** |
| Daily | 0.061 | **0.077** | 0.160 | **0.197** |

The 80%-power estimates are the more useful planning hurdles. They are not literal necessary-and-sufficient thresholds: power depends on the path, the endpoint's Holm rank, the cost actually paid, and the active portfolio's realized risk. Under a larger 30-endpoint family, the first-step z cutoff rises from about 2.82 to 2.94; the 80%-power estimates rise by roughly 3%, to about 0.162/0.102/0.080 for long-only and 0.505/0.292/0.204 for long-short.

The daily numbers are especially assumption-sensitive. A ten-session bootstrap preserves at most nine daily lags, while the assumed daily signal persistence is 0.90; if persistence extends beyond ten sessions, the test can be less powerful than shown. Conversely, if the strategy's actual signal is less persistent or its active-return volatility is lower, daily power can improve. A 50% rather than 20% turnover assumption adds 0.18%, 0.76%, and 3.78% annual cost at monthly, weekly, and daily frequency; the approximate 80%-power ICs rise by another 0.002, 0.004, and 0.008 respectively.

## Long-short interpretation

A market-neutral long-short book is not a like-for-like EW30 benchmark. Under the specified common-factor model it has 9.30% annual volatility and zero market covariance, while EW30 has 16.4% volatility and an assumed Sharpe of 0.9. Merely exceeding EW30 Sharpe would require a long-short mean above roughly 8.4% annually, but criterion 4 also requires positive excess over EW30 and a significant Holm-adjusted excess. The latter dominates: the 80%-power long-short mean hurdle is about 50.9%, 60.3%, and 93.8% net annual return for monthly, weekly, and daily rebalance in this design. These large means translate to the IC figures above. A conventional market-neutral test against zero would be materially easier, but it would not establish the stated EW30 excess-return criterion.

## Comparison with the existing audit

The audit's monthly long-only estimate of roughly 0.083–0.087 is below this model's 50%-power estimate of 0.121 and 80%-power estimate of 0.157. The difference has three sources: this calculation includes positive serial dependence in date-level ICs, uses the conservative first Holm step for 21 tests, and states an 80%-power target rather than treating a just-significant expected statistic as a dependable design. If serial dependence is set to zero and only the critical boundary (about 50% power) is required, the estimate falls near 0.095; that is close to the audit's range, though still somewhat above it under the first Holm step. So the audit is reasonable as an optimistic order-of-magnitude illustration, but too optimistic if presented as a robust minimum with the dependence and power assumptions used here.

The audit's long-short estimate of about 0.31–0.32 is also below this design's 50%-power 0.410 and 80%-power 0.490 monthly estimates. Its estimate assumes a rank-3 Holm approximation, no positive serial-dependence penalty, and a just-significant expected return rather than 80% power. Under those lighter assumptions, an estimate nearer 0.31 is plausible; it is not a universal lower bound. A stronger common-factor mean, a higher EW30 Sharpe, or positive covariance between the active strategy and EW30 would alter the result.

## Bottom line and limits

Under an explicit 30-name, 6%-dispersion, 0.37-correlation synthetic design and an 80%-power Holm-first-step standard, the IC hurdles are approximately **0.157/0.099/0.077** for long-only monthly/weekly/daily and **0.490/0.283/0.197** for long-short versus EW30. The audit's monthly long-only estimate is an optimistic boundary rather than a robust power target; its long-short estimate likewise omits the conservative first Holm step and dependence/power margin. These results are design calculations only: they are not measured Dow effects, do not predict any candidate's performance, and do not use or characterize the sealed holdout.

## Reproducibility references

- `r4_harness/power_sim.py` provides the synthetic rank-IC Monte Carlo and HAC effective-count calculation.
- `r4_harness/phase3.py` documents the 10-session circular block-bootstrap p-value and Holm step-down calculation; its bootstrap is centered under the null and tests positive mean excess.

