# Synthetic power simulator

`power_sim.py` estimates detection probability for a positive mean date-level IC or an event effect using simulated observations only. It does not read prices, returns, signals, or project results. A one-sided detection is defined as a Newey–West t-statistic **at least 2**, with Bartlett weights and lag `horizon - 1`.

## Assumptions and interpretation

- The universe size affects the default IC standard deviation only when `--ic-sd` is omitted: it uses the conventional null-rank-correlation approximation `1 / sqrt(assets - 1)`. This is an analytic planning approximation, not calibrated from this project. Supplying `--ic-sd` overrides it.
- Date-level observations are synthetic Gaussian noise with the requested stationary AR(1) serial correlation, plus the planted mean effect. The `signal_autocorrelation` input therefore acts as the assumed temporal autocorrelation of the tested date-level IC/effect series; it is a sensitivity assumption, not an estimate of an actual signal.
- In event mode, event counts per date follow a negative-binomial Gamma–Poisson mixture with specified mean `event_rate` and shape `event_cluster_shape`; its variance is `mu + mu^2/shape`. Only dates containing events enter the event test. The date observation's noise SD is `IC_SD / sqrt(event count)`, modeling averaging independent event-level noise within a date.
- Reported effective N is the mean number of observations divided by the Bartlett Newey–West design effect implied by the specified AR(1) coefficient. The 80% minimum detectable effect (MDE) is the normal planning approximation `(2 + z_0.80) × IC_SD × sqrt(design effect / observations)`, with event-mode variance reduced using the expected event count conditional on a nonzero count. It is not a second Monte Carlo search.
- Monte Carlo probability has finite-simulation error; `monte_carlo_se` reports its binomial standard error. At 1,000 simulations, that error is at most about 0.016.

All sample parameters below (`rho=.20`, planted mean IC `.02`, dates `1,500`) are illustrative synthetic assumptions. They are not estimates from development or holdout data. IC SD is set by the stated null approximation, `1/sqrt(N-1)`.

## Example synthetic planning table

The following table was generated with 1,000 simulations and fixed seed `20261110 + assets + horizon` for each case.

| Synthetic universe | Horizon | Dates | IC SD assumption | Mean effective N | P(NW t ≥ 2) | 80% MDE |
|---|---:|---:|---:|---:|---:|---:|
| Dow-sized (30) | 5 | 1,500 | 0.1857 | 1,090.9 | 0.913 | 0.0160 |
| Dow-sized (30) | 21 | 1,500 | 0.1857 | 1,020.2 | 0.909 | 0.0165 |
| S&P 100-sized | 5 | 1,500 | 0.1005 | 1,090.9 | 1.000 | 0.0086 |
| S&P 100-sized | 21 | 1,500 | 0.1005 | 1,020.2 | 1.000 | 0.0089 |
| S&P 500-sized | 5 | 1,500 | 0.0448 | 1,090.9 | 1.000 | 0.0039 |
| S&P 500-sized | 21 | 1,500 | 0.0448 | 1,020.2 | 1.000 | 0.0040 |

At the assumed +.02 planted mean, synthetic detection probability is high, while the Dow-sized MDE is 0.016 under these specific assumptions. This illustrates the consequences of the model inputs; it says nothing about whether any actual signal has that effect or autocorrelation.

## CLI examples

Each command operates on assumptions only; no data folder or input file is accepted.

```powershell
python r4_harness/power_sim.py --assets 30 --dates 1500 --horizon 5 --signal-autocorrelation 0.2 --mean-ic 0.02 --simulations 1000 --seed 20261115
python r4_harness/power_sim.py --assets 100 --dates 1500 --horizon 21 --signal-autocorrelation 0.2 --mean-ic 0.02 --simulations 1000 --seed 20261131
python r4_harness/power_sim.py --assets 500 --dates 1500 --horizon 5 --signal-autocorrelation 0.2 --mean-ic 0.02 --simulations 1000 --seed 20261615
python r4_harness/power_sim.py --assets 30 --dates 1500 --horizon 21 --signal-autocorrelation 0.2 --mean-ic 0.02 --simulations 1000 --seed 20261131
python r4_harness/power_sim.py --assets 100 --dates 1500 --horizon 5 --signal-autocorrelation 0.2 --mean-ic 0.02 --simulations 1000 --seed 20261115
python r4_harness/power_sim.py --assets 500 --dates 1500 --horizon 21 --signal-autocorrelation 0.2 --mean-ic 0.02 --simulations 1000 --seed 20261631
```

Clustered event-study planning uses expected events per calendar date and NB shape:

```powershell
python r4_harness/power_sim.py --assets 30 --dates 1500 --horizon 5 --ic-sd 0.10 --event-rate 0.08 --cluster-shape 0.30 --event-effect 0.08 --simulations 2000 --seed 61
```

## API

```python
from power_sim import simulate_power
result = simulate_power(
    universe_size=30, n_dates=1500, horizon=5,
    signal_autocorrelation=0.2,
    cross_sectional_ic_sd=0.10,
    planted_mean_ic=0.02,
    simulations=2000, seed=61,
)
```

For event mode, pass `event_rate`, `event_cluster_shape`, and `event_effect`; do not pass price or return arrays. The result includes detection probability, Monte Carlo SE, mean and median effective N, 80% MDE, assumed effect, and Newey–West lag.

## Tests

From the project root:

```powershell
python -m pytest r4_harness/tests/test_power_sim.py -q
```

Tests use only synthetic random draws and verify null/planted behavior, overlap adjustment, clustered-event handling, reproducibility, and input validation.
