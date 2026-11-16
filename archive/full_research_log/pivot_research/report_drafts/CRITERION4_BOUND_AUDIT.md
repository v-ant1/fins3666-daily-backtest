# Criterion-4 feasibility bound audit

**Scope.** This is an independent, outcome-free audit of [Round Q](../r6_ideas/Q.md), the fixed criterion 4, and coordinator decision 88. I used algebraic planning assumptions and the shared rank-IC-to-return mapping; no prices, returns, project outcomes, signals, or holdout data were opened. The numeric IC bounds below are conditional illustrations, not forecasts or empirical estimates.

## Finding in brief

Q is right that criterion 4 is a severe hurdle and that the bound rises when the Holm family grows. Its specific IC figures are not a dependable lower bound, however: it applies `IR ≈ IC × sqrt(12)` without defining whether IR is the active information ratio or the portfolio's standalone Sharpe, and it counts monthly dates but not the 30-name cross-section or the top/bottom portfolio weights. For a top-five Dow portfolio versus EW30, a transparent independent-name benchmark gives an IC near **0.083–0.087** for the Holm-adjusted excess-return test, before realistic dependence penalties; that is much lower than Q's **0.294**. For a market-neutral long-short illustration, explicitly accounting for EW30's return hurdle and the active-return variance gives an IC near **0.31–0.32** at a stated 16% annual EW30-volatility assumption, versus Q's **0.52**. The long-short number is especially assumption-sensitive; without EW30 volatility and the strategy/EW30 covariance, no unique IC minimum can be derived.

Thus, Q's numerical bounds are **too pessimistic in the stated illustrations**, particularly for long-only. Its qualitative conclusion—none of the screened effects is documented near a plausible after-cost, family-adjusted Dow hurdle—remains credible. Decision 76's “about 0.8” active-Sharpe screen is also a rough feasibility rule: a six-year, one-sided normal approximation at the current Holm thresholds implies about **1.00–1.05** annual active Sharpe before dependence penalties.

## What the test actually requires

Criterion 4 is conjunctive: net cumulative return must exceed EW30, the portfolio Sharpe must exceed EW30's, and the one-sided block-bootstrap p-value for positive net excess return must pass Holm over the R6 family. The fixed decision log reports EW30 Sharpe around 0.9 and currently has nine R6 endpoints; decision 88 says the family continues to grow. The actual bootstrap threshold depends on the endpoint's rank among all raw p-values and on future family additions.

With six years treated as six independent annual observations, an annualized information ratio (IR_A) for the **active return series** has approximate one-sided statistic (IR_A\sqrt{6}). Under the current nine-slot family, the first Holm cutoff is 0.05/9 = 0.00556 (normal z≈2.54). The two already-small placebo p-values H2 and H8 are each about 0.001996, so a future endpoint that is the next-smallest would face rank 3 and cutoff 0.05/7 = 0.00714 (z≈2.45). If the family grows to 12 slots and those two remain the smaller p-values, a rank-3 endpoint faces 0.05/10 = 0.005 (z≈2.58). Those correspond to annual active Sharpe of approximately **1.00–1.05**. If active returns are serially dependent or clustered, the required ratio is higher. The coordinator's 0.8 screen would imply z≈1.96, raw p≈0.025 under this six-year approximation; that alone does not clear a likely Holm step in a growing family.

The harness's circular block bootstrap uses daily excess returns, 10-session circular blocks, and 5,000 draws. The calculation above is a planning approximation to that test, not a substitute for it. A block bootstrap cannot be exactly inferred from a Sharpe ratio: the return path, serial dependence, block length, benchmark covariance, and the final Holm family all matter.

## Long-only top-five Dow versus EW30

For an illustrative monthly design, use 30 names, top (K=5), total-notional turnover 20% per rebalance, 0.05% cost per dollar traded, and **6% monthly cross-sectional return dispersion**. The 6% is the planning assumption already used in R6 hurdle work, not an observed price statistic. Twelve monthly rebalances cost about 0.01% NAV each, or **0.12% simple NAV per year**. The cost-only floor from `break_even_rank_ic(0.20, 0.06, 0.0005, 5/30)` is **IC=0.001155**. This is tiny relative to the inferential hurdle; no extra impact or borrow cost is assumed.

Using the harness's linear rank mapping, a monthly top-five active gross return is approximately

`IC × 0.06 × sqrt(12) × (0.5 − (5/30)/2) = IC × 0.08660`.

Under an independent, equal-volatility 30-name cross-section, the active weights are +1/6 on each selected name and −1/30 on the other 25, with squared-weight sum 1/6. The illustrative monthly active-return SD is therefore `0.06 × sqrt(1/6) = 2.45%`, or 8.49% annualized. This gives an annual active Sharpe of approximately `12.25 × IC` before costs. Requiring the annual active ratio to clear the current-Holm, six-year approximation of 1.00–1.04 implies **IC≈0.082–0.085** before costs; adding the 20%-turnover cost drag raises that to approximately **0.083–0.087**. At 12 Holm slots, the analogous rank-3 estimate is about **0.087** (about **0.089** if the endpoint must pass the first Holm step).

In this illustrative model, a positive active IR near 1.0 also makes the long-only total Sharpe exceed a 0.9 EW30 Sharpe: the active weight vector sums to zero, so under equal common covariance the benchmark component cancels from active risk. For example, if annual active SD is half EW30 SD and active returns are uncorrelated with EW30, an active IR of 1.0 gives total portfolio Sharpe about 1.25. This condition is model-dependent; if the active portfolio's covariance or risk differs, recompute directly from `μ_portfolio`, `σ_portfolio`, and EW30 rather than using a standalone IC rule.

The **0.083–0.089** IC values are optimistic lower bounds, not the expected effect size: correlated industry shocks reduce independent breadth; a 20% turnover cap can prevent the target basket from being held; realized active risk can exceed this independent-weight illustration; and the long-only portfolio must independently meet the Sharpe comparison. Even after these caveats, Q's **0.294** conversion is about 3.3–3.5 times higher because its `sqrt(12)` equation omits the cross-sectional active-risk scale for a concentrated top-five-versus-benchmark portfolio. The exact criterion-4 IC is not identifiable from the stated family size and benchmark Sharpe alone.

## Long-short portfolio against EW30

For comparison, consider a fixed monthly long-short book that holds the top five at +50% gross exposure and bottom five at −50%, with total traded notional capped at 20% per rebalance and the same cost rate. Under the same linear percentile-rank mapping, its expected gross monthly return per unit rank IC is also about 0.08660: it is half the top-versus-bottom tail spread, while the top-five-versus-EW30 active portfolio is the top tail against the cross-section. This mapping uses cross-sectional return dispersion, not an assumption that monthly IC equals a portfolio Sharpe.

The benchmark hurdle is materially different for a market-neutral book. If EW30's Sharpe is 0.9 and the long-short's own volatility is half EW30's, merely having a higher Sharpe and positive mean excess requires its standalone Sharpe to exceed **1.8**. But passing the Holm-adjusted excess-return test requires more than that. To make the dependency explicit, use an **illustrative** annual EW30 volatility of 16%, so its implied mean return at Sharpe 0.9 is 14.4%; take long-short volatility as 8% and assume zero long-short/EW30 correlation. The annual SD of the excess series is then `sqrt(0.16² + 0.08²)=17.9%`. A rank-3 Holm threshold over six years requires expected active excess of approximately 17.9–18.8% annually (active IR 1.00–1.05), on top of EW30's 14.4% mean. The net long-short mean must therefore be about **32.3–33.2% annually**, corresponding to an annualized standalone Sharpe around **4.0–4.2**. With 0.12% annual trading cost and the harness's linear IC-to-return mapping of about 1.039 annual return per IC, this is approximately **IC=0.31–0.32**.

This is not a universal minimum: change EW30 volatility, excess-return covariance, holding period, or effective sample size and the estimate changes. More importantly, the candidate must clear *both* the return-over-EW30 and portfolio-Sharpe-over-EW30 gates, not simply obtain a high standalone market-neutral Sharpe. Q's `IC≈0.52` follows by applying `IC×sqrt(12)` to a standalone Sharpe hurdle of 1.8; that mapping does not use the actual cross-sectional rank-to-tail return conversion, and it omits the separate family-adjusted excess-return test. Under the explicit 16%/zero-correlation illustration, **0.52 is too pessimistic by roughly 1.6×**; at materially higher EW30 volatility or worse costs, the long-short IC can approach it. Without benchmark volatility and covariance, Q's number is not an identified lower bound.

## Audit verdict on decisions 76 and 88

- **Decision 76:** the 0.8 annual excess-Sharpe screen is a useful order-of-magnitude filter, but the six-year Holm approximation supports about 1.00–1.05 before dependence penalties when a portfolio endpoint is near rank 3. It is too low to stand alone as a guaranteed pass threshold.
- **Decision 88 / Round Q:** the qualitative feasibility conclusion is supported by the strict dual benchmark and multiplicity requirements plus the absence of documented post-2020 mega-cap effects of this magnitude. The specific `0.29` monthly IC for a long-short zero-mean significance hurdle is not the right long-only benchmark-relative calculation; Q's `0.52` market-neutral figure is also not uniquely identified and omits the Holm excess-return requirement. On the stated planning example, the long-only hurdle is around 0.08–0.09 IC, while the long-short hurdle after including EW30's mean is around 0.31–0.32 IC. These still represent very large, unsupported effects in the existing R5/R6 search space, but the dossier should not present 0.29/0.52 as universal mathematical minima.
- **What remains unknown:** exact minimums require the annualized EW30 volatility, candidate/benchmark covariance, realized turnover path under the cap, time-series dependence, the portfolio's actual score-return relation, and the final Holm family size and p-value ordering. None can be recovered from an assumed IC or Sharpe alone, and estimating them from project outcomes is outside this audit.

## Sources inspected

- [Round Q calculation](../r6_ideas/Q.md).
- [R6 decisions, especially items 76 and 88](../specs/r6_decisions.md).
- [R6 goal and fixed criterion 4](../specs/r6_goal.md).
- [Harness rank-IC mapping and bootstrap implementation](../r4_harness/phase3.py).
- [Harness synthetic power simulator documentation](../r4_harness/POWER_SIM.md).

*This report is an assumption-based audit only. No outcomes or holdout data were used.*
