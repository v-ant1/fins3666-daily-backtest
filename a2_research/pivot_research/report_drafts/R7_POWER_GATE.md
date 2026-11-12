# R7 S&P 500 power gate — synthetic criterion-4 rerun

**Decision: GO — narrowly and conditionally.** Under the permitted fallback effect range of 0.01–0.03 rank IC, only one tested configuration clears the approximate 80%-power Holm hurdle while meeting the 50% turnover and active-share rules: weekly rank-weighted top-half with a hard 50%-notional rebalance cap, and a high signal-persistence assumption (ρ=0.8). Its required rank IC is about **0.028**, at the upper edge of the fallback range. All monthly configurations and all other weekly configurations require more than 0.03 or fail active share / turnover. This GO is only the §5 power gate; it does not validate a predictor or waive the remaining R7 data, literature, placebo, portfolio, and holdout gates.

## Scope and inputs

- **Synthetic only:** no project prices, signals, forward returns, portfolio returns, holdout values, or data outcomes were read or simulated.
- **Target universe:** 500 point-in-time eligible U.S. stocks per rebalance date, as a planning approximation to the S&P 500. Membership and delisting quality are not verified by this calculation.
- **Benchmark:** equal-weight S&P 500, formed from the same 500 names at each date. Its annual Sharpe is assumed to be 0.90, consistent with the prior synthetic audit; this is not an estimate of realized S&P 500 performance.
- **Observations:** 72 monthly or 312 weekly dates over six years. The effective date counts reuse the autocorrelation/HAC values in `CRITERION4_BOUND_BY_SHAPE.md`: monthly 46.7 / 24.5 / 9.7 at ρ=0.2 / 0.5 / 0.8; weekly 191.4 / 124.8 / 83.2. These are design approximations, not project sample sizes.
- **Return dispersion and risk:** retain the earlier synthetic assumptions of 6% monthly cross-sectional idiosyncratic dispersion, 16% annual common-factor volatility, and 20.8% annual idiosyncratic volatility. This gives equal-weight S&P 500 annual volatility of about 16.03%; at assumed Sharpe 0.90, annual mean is about 14.42%. The model assumes equal pairwise correlation and independent active/idiosyncratic component across names.
- **Costs and turnover:** 0.05% per dollar of total traded notional (buys plus sells). A shape passes the turnover gate if average total-notional turnover is ≤50% per rebalance; otherwise it must have costs below 25% of gross active edge.
- **Holm / power:** use 30 hypotheses as a conservative representation of “about 24+” tests. The first Holm cutoff is 0.05/30 = 0.00167, one-sided normal critical value 2.935; adding 0.842 for 80% power gives a target statistic of 3.777. The final Holm step-down rank is unknown, so this first-step cutoff is conservative.
- **Effect-size input:** `specs/r7_effect_sizes.md` was absent when checked. As requested, compare with a fallback literature-scale range of **0.01–0.03 rank IC**. This range is a planning comparison only, not a verified published effect estimate for any candidate.

## Shapes

- **Top decile:** equal-weight top 50 names; target active share 90% versus EW500.
- **Top quintile:** equal-weight top 100 names; target active share 80%.
- **Rank-weighted top half:** bottom 250 weights zero; top-250 weights increase linearly from rank weight 1 through 250; target active share 56.2%.
- **Full target:** rebalance directly to the selected target weights.
- **Low-turnover (Cap50):** at each formation, move linearly from current weights toward the new target only as far as a hard 0.50 total-notional turnover cap allows. The table reports the resulting simulated active share; it is not assumed to retain target active share automatically.

The rank IC-to-return mapping uses a Gaussian copula: Pearson correlation is `2 × sin(π × rank_IC / 6)`. For each shape, the expected standardized-score exposure and target turnover were estimated using synthetic Gaussian cross-sections with signal autocorrelation ρ=0.2/0.5/0.8. The Cap50 strategy’s exposure, active variance, and active share were estimated after applying the per-rebalance interpolation rule. Annual net-edge requirements are the larger of (a) the 80%-power Holm-first-step active-return hurdle and (b) the mean needed for the strategy’s Sharpe to exceed the equal-weight benchmark, plus the modeled transaction costs. No asset-return paths were generated.

## Required rank IC and turnover — monthly

Each cell gives **required mean rank IC / mean total-notional turnover / costs as a share of gross active edge / active share**. The triplets are ordered ρ=0.2 / 0.5 / 0.8. Turnover and Cap50 activity are synthetic score-transition estimates; target active shares are exact from the weights.

| Shape | Full target | Low-turnover Cap50 |
|---|---|---|
| Top decile | 0.048 / 1.656 / 15.7% / 90%; 0.062 / 1.353 / 9.9% / 90%; 0.093 / 0.879 / 4.3% / 90% | 0.060 / 0.500 / 11.4% / 51.1%; 0.067 / 0.500 / 7.2% / 58.8%; 0.085 / 0.500 / 3.3% / 75.0% |
| Top quintile | 0.042 / 1.432 / 19.4% / 80%; 0.053 / 1.127 / 12.1% / 80%; 0.078 / 0.711 / 5.2% / 80% | 0.050 / 0.500 / 15.1% / 39.3%; 0.056 / 0.500 / 9.4% / 48.2%; 0.073 / 0.500 / 4.4% / 67.1% |
| Rank-weighted top half | 0.035 / 1.180 / 23.6% / 56.2%; 0.044 / 0.919 / 14.8% / 56.2%; 0.063 / 0.574 / 6.4% / 56.2% | 0.039 / 0.500 / 17.9% / 31.5%; 0.045 / 0.500 / 11.4% / 40.1%; 0.063 / 0.500 / 5.8% / 53.9% |

## Required rank IC and turnover — weekly

| Shape | Full target | Low-turnover Cap50 |
|---|---|---|
| Top decile | 0.035 / 1.656 / 43.6% / 90%; 0.037 / 1.353 / 33.8% / 90%; 0.038 / 0.879 / 21.3% / 90% | 0.040 / 0.500 / 34.9% / 51.1%; 0.037 / 0.500 / 26.3% / 58.8%; 0.034 / 0.500 / 17.1% / 75.0% |
| Top quintile | 0.033 / 1.432 / 50.0% / 80%; 0.034 / 1.127 / 38.9% / 80%; 0.034 / 0.711 / 24.7% / 80% | 0.037 / 0.500 / 42.4% / 39.3%; 0.033 / 0.500 / 32.3% / 48.2%; 0.031 / 0.500 / 21.8% / 67.1% |
| Rank-weighted top half | 0.030 / 1.180 / 56.1% / 56.2%; 0.030 / 0.919 / 44.6% / 56.2%; 0.029 / 0.574 / 29.1% / 56.2% | 0.030 / 0.500 / 47.4% / 31.5%; 0.028 / 0.500 / 37.3% / 40.1%; **0.028 / 0.500 / 27.0% / 53.9%** |

An unbolded high-turnover case can still satisfy the turnover clause when cost/gross is under 25% (for example, weekly top decile at ρ=0.8). The low-turnover cases are at the 50% turnover ceiling by construction, so their cost/gross percentage is descriptive and does not determine that branch of the gate. The low-turnover rank-weighted half fails the separate ≥50% active-share requirement at ρ=0.2 and 0.5; it clears it only at ρ=0.8.

## Comparison with effect-size range and §5 decision

| Rebalance / shape | Best relevant hurdle | Comparison with fallback 0.01–0.03 | §5 assessment |
|---|---:|---|---|
| Monthly, any of the six variants | 0.035 (full rank-weighted half at ρ=0.2); other shapes are higher | Even the lowest monthly requirement is above 0.03. | **NO-GO monthly.** |
| Weekly, full targets | 0.029 (rank-weighted half at ρ=0.8), but turnover 57.4% and costs/gross 29.1% fail both turnover alternatives | Numerically within the fallback range, but the configuration fails the turnover rule. | **NO-GO full target.** |
| Weekly, Cap50 top decile | 0.034–0.040 | Above the 0.03 upper bound. | **NO-GO.** |
| Weekly, Cap50 top quintile | 0.031–0.037; active share also falls below 50% at ρ=0.2/0.5 | Above 0.03 at all three persistence assumptions. | **NO-GO.** |
| Weekly, Cap50 rank-weighted top half | 0.030 / 0.028 / **0.028**; active share 31.5% / 40.1% / **53.9%** | At ρ=0.8 the required 0.028 lies within, near the upper end of, the fallback range. At ρ=0.2/0.5 it fails the active-share floor. | **Narrow conditional GO only at ρ=0.8.** |

The high-persistence case is fragile: moving from ρ=0.8 to ρ=0.5 lowers Cap50 rank-weighted-top-half active share below the required 50%, and the best eligible weekly rank IC then rises to 0.033 (top quintile) while also failing active share at ρ=0.5. The generic fallback range is not a substitute for L3's paper-supported effect estimates; if the cited, signal-matched effects do not credibly reach approximately 0.028 weekly, this narrow GO becomes NO-GO before idea generation. Likewise, the assumed ρ=0.8 must be justified ex ante rather than selected after seeing a signal's persistence.

## GO / NO-GO under §5

**GO — narrowly, for idea-generation screening only:** the weekly, rank-weighted top-half, Cap50 configuration requires about **0.028 rank IC** at 80% power under the conservative 30-test Holm cutoff when signal persistence is ρ=0.8; it has 50% simulated turnover and 53.9% active share. This lies inside the fallback 0.01–0.03 range, so the §5 rule does not require stopping all R7 search. The other tested monthly and weekly configurations are NO-GO under the same rule. Before any screen starts, L3 must provide a literature-supported effect estimate at or above this hurdle and the team must verify that ρ=0.8 is a plausible predeclared design assumption; failure of either check converts the overall gate to **NO-GO**.

## Limits

This is a conditional design estimate, not a power guarantee or strategy result. The 500-name point-in-time universe, EW500 benchmark Sharpe, cross-sectional dispersion, common/idiosyncratic risk split, Gaussian score distribution, rank-to-return copula, persistence, and Holm family size are assumptions. The simulation does not verify S&P membership, delistings, trading costs, or the availability of a sealed holdout. The permitted “GO” means only that one synthetic configuration has a plausible effect-size route under the stated assumptions; R7 §4 and all later research gates still apply.
