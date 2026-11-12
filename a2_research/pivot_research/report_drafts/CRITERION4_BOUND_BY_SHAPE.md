# Criterion-4 hurdle by portfolio shape (synthetic)

**Scope.** This is a design-only extension of `report_drafts/CRITERION4_BOUND_VERIFY.md`. It estimates the 80%-power rank-IC hurdle for six Dow-like long-only or dollar-neutral shapes at monthly, weekly, and daily rebalance, with one-sided block-bootstrap p < 0.05 after Holm for a 24-test family. It uses no project outcomes, project prices, or holdout data.

## Common assumptions

- 30 names and six years: 72 monthly, 312 weekly, or 1,500 daily formation/return observations.
- Monthly cross-sectional/idiosyncratic return dispersion is 6%; common-factor annual volatility is 16%; idiosyncratic annual volatility is 20.8%. This gives about 0.37 cross-name correlation and EW30 annual volatility about 16.44%. Assumed EW30 Sharpe is 0.9, implying annual mean 14.8%. These are synthetic planning assumptions, not measured Dow moments.
- Trading cost is 0.05% per dollar of total traded notional (buys plus sells). The turnover feasibility rule is average turnover ≤50% per rebalance, or annual cost less than 25% of the gross active edge.
- Holm first-step p cutoff is 0.05/24 = 0.00208 (one-sided z ≈ 2.87). For 80% detection power, the signal needs noncentrality ≈2.87+0.84 = 3.71. This conservative first-step cutoff does not assume the portfolio endpoint will have a favorable Holm rank.
- Date-level signal autocorrelation is 0.2, 0.5, or 0.8. Effective observations are calculated with the harness synthetic `power_sim.py` HAC design (monthly NW lag 20, weekly lag 4); daily uses the ten-session Bartlett block design effect. Effective years used in the portfolio calculation are:

| Rebalance | ρ=0.2 | ρ=0.5 | ρ=0.8 |
|---|---:|---:|---:|
| Monthly (72 dates) | 3.89 | 2.04 | 0.81 |
| Weekly (312 dates) | 3.68 | 2.40 | 1.60 |
| Daily (1,500 sessions) | 4.14 | 2.29 | 1.10 |

`power_sim.py` estimates date-level IC effective counts; daily’s values above additionally apply a 10-session Bartlett design effect to AR(1) signal persistence. This is a planning approximation to the frozen circular block bootstrap, not a direct bootstrap of a real portfolio return path.

## Shapes and active share

Active share is 0.5 × sum(|strategy weight − EW30 weight|). The selected top-K books are equal weight. `RankTopHalf` sets the bottom 15 weights to zero and assigns the top 15 weights proportional to ranks 1 through 15 (weights `1/120, 2/120, …, 15/120`); it is a long-only rank-weighted tilt with 55% active share. Long-short books hold +50% in the selected upper group and −50% in the lower group; they have 100% active share versus EW30.

| Shape | Weights | Active share | Active variance factor Σ(w−EW)² |
|---|---|---:|---:|
| Top 5 | 20% each in 5 names | 83.3% | 0.1667 |
| Top 8 | 12.5% each in 8 names | 73.3% | 0.0917 |
| Top 10 | 10% each in 10 names | 66.7% | 0.0667 |
| Top 15 | 6.67% each in 15 names | 50.0% | 0.0333 |
| RankTopHalf | Linear rank weights in upper half | 55.0% | 0.0379 |
| LS tertiles | +50% in top 10, −50% in bottom 10 | 100.0% | 0.0500 |
| LS halves | +50% in top 15, −50% in bottom 15 | 100.0% | 0.0333 |

All requested long-only shapes meet the 50% active-share floor; Top15 sits exactly on it. The two long-short shapes are dollar-neutral but are benchmarked against EW30 here because that is the stated criterion-4 excess-return hurdle.

## IC hurdle and simulated turnover

Each cell reports **80%-power mean rank IC / average total-notional turnover / annual costs as a share of gross active edge / cost-turnover gate**. Turnover is simulated over 100,000 Gaussian score transitions per persistence value, with 30 names and cross-date score correlation ρ; no asset returns are used. Annual cost uses the horizon’s rebalance frequency. `PASS` means either turnover ≤50% or cost/gross edge <25%; `FAIL` means neither condition is met.

### Monthly rebalance

| Shape | ρ=0.2 | ρ=0.5 | ρ=0.8 |
|---|---|---|---|
| Top 5 | 0.155 / 151% / 5.4% / PASS | 0.209 / 121% / 3.2% / PASS | 0.325 / 79% / 1.3% / PASS |
| Top 8 | 0.140 / 130% / 6.2% / PASS | 0.188 / 102% / 3.6% / PASS | 0.291 / 65% / 1.5% / PASS |
| Top 10 | 0.135 / 117% / 6.5% / PASS | 0.181 / 91% / 3.8% / PASS | 0.280 / 57% / 1.5% / PASS |
| Top 15 | 0.131 / 87% / 6.8% / PASS | 0.175 / 67% / 3.9% / PASS | 0.271 / 42% / 1.6% / PASS |
| RankTopHalf | **0.120 / 116% / 7.2% / PASS** | 0.160 / 91% / 4.2% / PASS | 0.247 / 58% / 1.7% / PASS |
| LS tertiles | 0.596 / 117% / 1.5% / PASS | 0.747 / 91% / 0.9% / PASS | 1.068 / 57% / 0.4% / PASS |
| LS halves | 0.803 / 87% / 1.1% / PASS | 1.008 / 67% / 0.7% / PASS | 1.441 / 42% / 0.3% / PASS |

### Weekly rebalance

| Shape | ρ=0.2 | ρ=0.5 | ρ=0.8 |
|---|---|---|---|
| Top 5 | 0.091 / 151% / 18.8% / PASS | 0.105 / 121% / 13.1% / PASS | 0.120 / 79% / 7.4% / PASS |
| Top 8 | 0.084 / 130% / 21.2% / PASS | 0.095 / 102% / 14.6% / PASS | 0.109 / 65% / 8.1% / PASS |
| Top 10 | 0.081 / 117% / 22.2% / PASS | 0.092 / 91% / 15.1% / PASS | 0.105 / 57% / 8.4% / PASS |
| Top 15 | 0.079 / 87% / 23.1% / PASS | 0.090 / 67% / 15.7% / PASS | 0.101 / 42% / 8.7% / PASS |
| RankTopHalf | **0.074 / 116% / 24.1% / PASS** | 0.083 / 91% / 16.7% / PASS | 0.093 / 58% / 9.5% / PASS |
| LS tertiles | 0.310 / 117% / 5.8% / PASS | 0.354 / 91% / 4.0% / PASS | 0.405 / 57% / 2.2% / PASS |
| LS halves | 0.413 / 87% / 4.4% / PASS | 0.474 / 67% / 3.0% / PASS | 0.544 / 42% / 1.6% / PASS |

### Daily rebalance

| Shape | ρ=0.2 | ρ=0.5 | ρ=0.8 |
|---|---|---|---|
| Top 5 | 0.069 / 151% / 55.1% / FAIL | 0.072 / 121% / 42.3% / FAIL | 0.080 / 79% / 24.8% / PASS |
| Top 8 | 0.068 / 130% / 58.9% / FAIL | 0.068 / 102% / 45.4% / FAIL | 0.074 / 65% / 26.8% / FAIL |
| Top 10 | 0.067 / 117% / 60.2% / FAIL | 0.067 / 91% / 46.5% / FAIL | 0.072 / 57% / 27.5% / FAIL |
| Top 15 | 0.067 / 87% / 61.4% / FAIL | 0.066 / 67% / 47.6% / FAIL | **0.070 / 42% / 28.2% / PASS** |
| RankTopHalf | 0.063 / 116% / 62.7% / FAIL | 0.063 / 91% / 49.5% / FAIL | 0.066 / 58% / 30.2% / FAIL |
| LS tertiles | **0.166 / 117% / 24.3% / PASS** | 0.186 / 91% / 16.8% / PASS | 0.225 / 57% / 8.8% / PASS |
| LS halves | 0.211 / 87% / 19.4% / PASS | 0.241 / 67% / 13.1% / PASS | 0.297 / 42% / 6.6% / PASS |

Bold marks the smallest IC hurdle among the designs that satisfy the turnover/cost test for that rebalance frequency. Monthly and weekly, a rank-weighted long-only tilt has the smallest hurdle; weekly it is close to the cost-ratio ceiling at low signal persistence (24.1%). Daily, Top15 with ρ=0.8 is the cheapest qualifying long-only shape because its expected turnover drops below 50%; the less concentrated daily portfolios at lower persistence fail the cost/turnover test even though their IC thresholds look smaller. If a dollar-neutral book is required, LS tertiles have the lowest IC hurdle, while LS halves have lower turnover.

## Calculation details and caveats

For long-only target weights, the active monthly volatility is `6% × sqrt(Σ(w−EW)²)`; the weekly and daily values scale by `sqrt(h/21)` for h=5 and h=1. Long-short uses `sqrt(Σw²)` because its weights sum to zero. The rank-score slope is the Gaussian-copula Spearman-to-Pearson factor `2 sin(π IC/6) ≈ 1.047 × IC`; the synthetic score simulation estimates `E[w'z]` for each shape. Annual gross active return per IC is that slope × 6% dispersion scaled to the holding period × rebalance count. Required annual active mean is the larger of (a) the Holm one-sided threshold for the excess-return series at 80% power and (b) the mean needed for strategy Sharpe to exceed EW30. Costs are then added back to obtain the required gross signal effect.

For long-short, mean EW30 return is added to the required excess before dividing by the rank-to-return slope; simply testing long-short mean against zero would not satisfy criterion 4. All portfolios were compared to EW30. Common market risk cancels in active long-only weights and in dollar-neutral long-short; the assumed EW30 mean and volatility still enter the long-short excess and Sharpe checks.

These are conditional synthetic thresholds, not empirical findings or exact test guarantees. The criterion's realized block-bootstrap p-value depends on each return path and on the final Holm ordering; this note uses a conservative first-step cutoff and a design effective-sample approximation. Turnover changes with the signal construction, execution timing, score ties, position drift, and any turnover cap. In particular, daily results are highly sensitive to the assumed persistence and 10-session block length. A full implementation should validate these calculations with synthetic end-to-end portfolio paths before freezing a design.

## Reproducibility

- Rank/portfolio information ratio design: `r4_harness/power_sim.py` (synthetic-only date-level IC Monte Carlo and HAC effective-count calculation).
- Cost and rank-IC planning conventions and circular block bootstrap: `r4_harness/phase3.py`.
- This report's turnover and score-exposure estimates were computed from seeded Gaussian score transitions only (seed 8675309; 100,000 transitions for each ρ). No project return data were used.
