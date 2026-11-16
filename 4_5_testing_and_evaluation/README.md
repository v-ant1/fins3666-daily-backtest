# Sections 4 and 5: Testing, validation and evaluation of J1

**Start here.** Every number in Section 4 of the report is in the tables below, and every one can be regenerated with:

```
cd 4_5_testing_and_evaluation/metrics
python compute_metrics.py      # writes metrics_summary.csv and yearly_returns.csv
```

| Report item | File |
|---|---|
| Table 4 (earlier vs final backtester) | [`figures/Table4_backtester_versions.png`](figures/Table4_backtester_versions.png) |
| Table 5 (J1 full metrics) | [`figures/Table5_J1_backtest_results.png`](figures/Table5_J1_backtest_results.png) |
| Figure 1 (equity curve) | [`figures/Figure1_J1_equity_curve.png`](figures/Figure1_J1_equity_curve.png) |
| All metrics, every run, in-sample and out-of-sample | [`metrics/metrics_summary.csv`](metrics/metrics_summary.csv) |
| J1 vs EW30 by calendar year | [`metrics/yearly_returns.csv`](metrics/yearly_returns.csv) |

## 1. In-sample vs out-of-sample at a glance

| Sample | Period | Strategy | Net return | EW30 net return | Sharpe (strategy / EW30) | Bootstrap p |
|---|---|---|---:|---:|---:|---:|
| **In-sample** (development) | 30 Nov 2020 – 30 Oct 2026 | J1 | 96.21% | 95.19% | 0.823 / 0.902 | 0.449 |
| In-sample, common window | 5 Mar 2021 – 30 Oct 2026 | J1 (V0) | 95.64% | 90.48% | 0.836 / 0.880 | 0.391 |
| In-sample, common window | 5 Mar 2021 – 30 Oct 2026 | J2 (V5) | 130.61% | 90.48% | 0.924 / 0.880 | 0.188 |
| **Out-of-sample** (holdout, opened once) | 3 Feb 2016 – 30 Oct 2020 | J2 | 72.54% | 77.81% | 0.608 / 0.727 | 0.478 |

- J1 was never run on the holdout; only the final refined strategy (J2, Section 6) was, once. Its deflated Sharpe ratio there was 0.840 (pass mark 0.95), so it **failed** out-of-sample.
- The holdout is *earlier* than the development period, so it is a different market regime. A forward test is the remaining check (Section 7).
- Sources: [`results/J1_RESULTS.json`](results/J1_RESULTS.json), [`../6_refinement_J2/results/R9_VARIANTS_V2.json`](../6_refinement_J2/results/R9_VARIANTS_V2.json), [`../6_refinement_J2/results/HOLDOUT_RESULT.json`](../6_refinement_J2/results/HOLDOUT_RESULT.json).

## 2. J1 full metrics (in-sample, net of 0.05% costs)

Daily returns, 252 days a year, zero risk-free rate.

| Group | Measure | J1 | EW30 |
|---|---|---:|---:|
| Signal | Mean IC / Newey–West t | 0.0148 / 2.08 | — |
| Signal | Placebo p (500 shuffles) | 0.002 | — |
| Return | Net cumulative return | 96.21% | 95.19% |
| Return | CAGR | 12.10% | 12.00% |
| Risk | Annualised volatility | 15.31% | 13.59% |
| Risk | Maximum drawdown | −21.90% | −21.37% |
| Risk | Daily 95% VaR / expected shortfall | 1.48% / 2.13% | 1.28% / 1.94% |
| Risk-adjusted | Sharpe | 0.823 | 0.902 |
| Risk-adjusted | Sortino | 1.20 | 1.32 |
| Risk-adjusted | Calmar | 0.55 | 0.56 |
| Relative | Beta / correlation | 1.04 / 0.92 | — |
| Relative | Annualised alpha | −0.12% | — |
| Relative | Tracking error / information ratio | 5.98% / 0.06 | — |
| Relative | Weeks beating EW30 | 48.8% | — |
| Relative | Bootstrap p (net excess) | 0.449 | — |
| Trading | Weekly reviews / mean turnover | 298 / 48.2% | — |
| Trading | Total costs | 10.36% | 0.49% |
| Trading | Costs / gross edge | 66.2% | — |

### By calendar year

| Year | J1 | EW30 | Difference |
|---|---:|---:|---:|
| 2020 (Dec only) | 2.8% | 2.8% | 0.0% |
| 2021 | 19.7% | 19.8% | −0.1% |
| 2022 | −1.6% | −6.7% | **+5.1%** |
| 2023 | 19.9% | 16.6% | **+3.2%** |
| 2024 | 10.2% | 13.2% | −3.1% |
| 2025 | 11.2% | 15.0% | −3.8% |
| 2026 (to Oct) | 10.4% | 11.8% | −1.4% |

## 3. Earlier backtester iteration

Our first backtester was built for the original heat-diffusion strategy. Its weaknesses (fixed Dow roster, no turnover cap, ~142% traded per rebalance, Sharpe below EW30) led to the rebuilt J1 backtester: point-in-time Dow membership, S&P 500 industry peers, SIC codes used only after SEC filing, a 50% turnover cap, and a signal test before any portfolio test.

| Backtester | Period | Net return (strategy / EW30) | Sharpe (strategy / EW30) | Traded per rebalance |
|---|---|---:|---:|---:|
| Earlier (heat-diffusion) | 27 Nov 2020 – 23 Feb 2024 | 39.78% / 38.33% | 0.65 / 0.76 | 142% |
| Earlier (heat-diffusion) | 6 Dec 2024 – 31 Dec 2025 | 2.49% / 11.96% | 0.22 / 0.75 | 142% |
| Final (J1) | 27 Nov 2020 – 30 Oct 2026 | 96.21% / 95.19% | 0.823 / 0.902 | 48% |

Earlier-backtester outputs: [`results/earlier_engine_heat_diffusion/`](results/earlier_engine_heat_diffusion/). To rerun, from [`../archive/vedant_heat_diffusion_original/code/`](../archive/vedant_heat_diffusion_original/code/):

```
python pressure_heat_backtest_daily.py --cost=actual --buffer=8
python pressure_heat_backtest_daily.py --cost=actual --buffer=8 --roster=2020-08-31 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2024-02-23 --tag=daily_early
```

## 4. How J1 was tested

1. **Data split.** All development and testing of J1 used 27 Nov 2020 – 30 Oct 2026. The 2016–2020 holdout was sealed and only opened once, for the final refined strategy (J2, Section 6).
2. **Frozen before results.** The J1 specification ([`../3_strategy_J1/spec/`](../3_strategy_J1/spec/)) was fixed and hashed before any result was seen. Only one signal, sign and horizon was allowed.
3. **Signal test.** On each weekly review date, the Spearman rank correlation (IC) between each S&P 500 stock's score and its next five-session return relative to its industry peers. The average IC is tested with a Newey–West t-statistic (lag 4). A placebo test shuffles scores within each date and industry 500 times.
4. **Portfolio backtest.** The five lowest-scoring Dow stocks are bought at the next open, with 0.05% charged on every trade, and compared with EW30 on the same dates.
5. **Robustness.** A block bootstrap (10-session blocks, 5,000 draws) on net excess return, and a deflated Sharpe ratio that adjusts for the number of trials.

## 5. Backtesters

| File | What it does |
|---|---|
| [`backtesters/run_j1.py`](backtesters/run_j1.py) | The official J1 runner: signal test, placebo, portfolio backtest and statistics |
| [`backtesters/j1_portfolio_replay.py`](backtesters/j1_portfolio_replay.py) | An independent re-implementation of the J1 portfolio, used to check the official result |
| [`backtesters/j1_reference.py`](backtesters/j1_reference.py) | Reference functions used by the replay |
| [`../6_refinement_J2/code/j2_variants_v2.py`](../6_refinement_J2/code/j2_variants_v2.py) | The variant engine used in Section 6 (J1 is variant V0) |
| [`../archive/vedant_heat_diffusion_original/code/`](../archive/vedant_heat_diffusion_original/code/) | Vedant's original heat-diffusion backtester (earlier design) |

