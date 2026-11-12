# C1 power analysis: final SIC3 peer intraday-return design

This is a synthetic, input-only power calculation. It used the final development signal panel and active SIC3 groups, but loaded no forward returns, outcome variables, or observed ICs. The mechanism is sampled weekly (every fifth trading session), with a five-session horizon and Newey–West lag 4.

## Assumptions

- Eligible S&P mechanism dates: 297 weekly dates with at least 250 names having a valid leave-one-out SIC3 peer score; median eligible names 359, minimum 326.
- Median SIC3 clusters among eligible scored names: 47; median mean cluster size: 7.660 names.
- Base IC-series SD: 0.150, literature calibration from Ding and Sun (2023), *The Statistics of Time Varying Cross-Sectional Information Coefficients* ([DOI](https://doi.org/10.1057/s41260-022-00295-9)); not estimated from project outcomes.
- SIC3 design effect: `1 + (mean cluster size - 1) × ICC`, with within-SIC3 ICC = 0.15 as a fixed sensitivity assumption. Median design effect = 1.9989; cluster-adjusted IC SD = 0.2121.
- Weekly signal autocorrelation input: -0.0008, the median per-name lag-one autocorrelation of within-date percentile ranks of the peer signal; this is input persistence, not IC autocorrelation.
- `r4_harness/power_sim.py`, horizon=5, Bartlett NW lag=4, 5,000 draws per planted effect; seed base 20261111, incremented by effect. This date-level AR(1) simulator applies SIC3 clustering through the SD design effect; it is a sensitivity approximation, not a full date-by-industry block bootstrap.

## Results

| Planted mean IC (hypothetical) | Power for NW t ≥ 2 | Monte Carlo SE | Effective dates | Effective N median | MDE at 80% power |
|---:|---:|---:|---:|---:|---:|
| 0.0183 | 0.322 | 0.007 | 297.0 | 297.4 | 0.0349 |
| 0.0260 | 0.552 | 0.007 | 297.0 | 297.4 | 0.0349 |

Effects 0.0183 and 0.026 are pre-outcome planning values carried from the red-team calibration; they are hypothetical IC values, not observations or estimates. Power below 80% at 0.0183 means the registered S&P mechanism would not meet its power gate under these assumptions. The manifest retains all simulation inputs and results.
