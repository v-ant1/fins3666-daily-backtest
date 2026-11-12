# R7 power-gate stress test — weekly rank-weighted top half

## Result

This is a synthetic stress test of the single conditional GO shape in `R7_POWER_GATE.md`: weekly rank-weighted top-half long-only, capped at 50% total-notional turnover, against an equal-weight 500-name S&P 500 benchmark. It reports the modeled Holm-adjusted power at four assumed weekly rank ICs and four assumed signal autocorrelations. No project prices, outcomes, signals, or holdout observations were read or simulated.

The Holm family is set to **27** (21 frozen R6 tests plus up to six R7 variants), giving the conservative first-step one-sided cutoff α=0.05/27 and z=2.902. The cumulative Sharpe trial count is **9** (seven R6 plus up to two R7 attempts).

| Signal ρ | Rank IC | Estimated power after Holm-27 | Annual costs / gross active edge | DSR probability, 9 trials | Active share | Mean total turnover / rebalance |
|---:|---:|---:|---:|---:|---:|---:|
| 0.6 | 0.015 | 6.2% | 61.7% | 38.4% | 43.9% | 50.0% |
| 0.6 | 0.020 | 36.1% | 46.3% | 77.5% | 43.9% | 50.0% |
| 0.6 | 0.025 | 79.7% | 37.0% | 96.3% | 43.9% | 50.0% |
| 0.6 | 0.030 | 97.8% | 30.9% | 99.7% | 43.9% | 50.0% |
| 0.7 | 0.015 | 6.7% | 55.0% | 43.7% | 48.6% | 50.0% |
| 0.7 | 0.020 | 32.1% | 41.2% | 79.8% | 48.6% | 50.0% |
| 0.7 | 0.025 | 71.6% | 33.0% | 96.4% | 48.6% | 50.0% |
| 0.7 | 0.030 | 94.6% | 27.5% | 99.7% | 48.6% | 50.0% |
| 0.8 | 0.015 | 6.4% | 50.0% | 45.6% | 53.7% | 50.0% |
| 0.8 | 0.020 | 27.5% | 37.5% | 79.0% | 53.7% | 50.0% |
| 0.8 | 0.025 | 62.6% | 30.0% | 95.5% | 53.7% | 50.0% |
| 0.8 | 0.030 | 89.3% | 25.0% | 99.5% | 53.7% | 50.0% |
| 0.9 | 0.015 | 6.3% | 39.4% | 51.7% | 56.0% | 40.7% |
| 0.9 | 0.020 | 21.7% | 29.5% | 81.0% | 56.0% | 40.7% |
| 0.9 | 0.025 | 48.8% | 23.6% | 95.4% | 56.0% | 40.7% |
| 0.9 | 0.030 | 76.5% | 19.7% | 99.3% | 56.0% | 40.7% |

## Method and interpretation

- **Portfolio exposure and costs:** 100 seeded synthetic paths of 500-name Gaussian score series, 312 weekly rebalances, and the same linear rank weights and Cap50 interpolation as the original gate. Rank IC is converted to Pearson correlation by `2 sin(π IC/6)`. Weekly cross-sectional idiosyncratic dispersion is 6% × √(5/21). Annual cost is 52 × 0.05% × simulated total-notional turnover; the reported cost share divides this by modeled gross active edge.
- **Power calibration:** preserve the prior gate's ρ=0.8, IC=0.028 80%-power boundary under its 30-test Holm first-step threshold. Update the critical value to 27 tests and scale standard error across ρ using the Bartlett/Newey-West lag-4 design effect from `r4_harness/power_sim.py`, anchoring its effective count at the prior report's 83.2 weekly observations at ρ=0.8. Power is the normal-tail probability for net active mean against zero at the 27-test cutoff. It is an analytic calibration to the earlier gate, not a fresh bootstrap of actual strategy returns.
- **DSR:** estimated net active Sharpe uses synthetic active variance from the score-weight paths and the stated return dispersion. DSR probability uses zero skew, zero excess kurtosis, the effective weekly sample count above, and the expected maximum of nine null Sharpe estimates (normal order-statistic approximation ≈1.521 standard errors). These are planning estimates; neither DSR nor power is observed strategy performance.
- **Eligibility:** the shape's required active share is at least 50%. The modeled portfolio misses that floor at ρ=0.6 and 0.7 despite a 50% turnover cap. At ρ=0.8 it clears active share (53.7%, consistent with 53.9% in the earlier 100-path run); at ρ=0.9 it clears both active-share and turnover requirements.

The stress test supports only a narrow design route: around **IC 0.028 at ρ=0.8** is the calibrated 80%-power boundary, and IC 0.030 produces 89.3% power there. At ρ=0.9, IC 0.030 is only 76.5% powered because effective sample size falls, although lower turnover reduces costs; that case needs an effect slightly above 0.030 to reach 80%. The DSR is already high at some cells where Holm-adjusted power is low; it answers a different, trial-deflated Sharpe question and does not replace the specified excess-return power gate.

`specs/r7_effect_sizes.md` now exists, but its conversions are explicitly “pseudo-ICs” and none is a matched estimate for this weekly S&P 500 portfolio and signal. The stress table therefore does not turn the conditional GO into permission to proceed: L3’s signal-matched evidence still needs to credibly support roughly 0.028 IC, and the high-persistence assumption must be justified before idea generation.

## Verdict

**Conditional GO remains narrow; no broader power pass.** The modeled route is around ρ=0.8 with IC≈0.028; ρ=0.9 requires slightly above 0.030, and ρ=0.6/0.7 fail the active-share rule. If credible, signal-matched evidence does not support the relevant hurdle, the §5 decision should be NO-GO.
