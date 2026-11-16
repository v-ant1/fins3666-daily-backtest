# Sections 4 and 5: Testing, validation and evaluation of J1

## How J1 was tested

1. **Data split.** All development and testing of J1 used 27 Nov 2020 – 30 Oct 2026. The 2016–2020 holdout was sealed and only opened once, for the final refined strategy (J2, Section 6).
2. **Frozen before results.** The J1 specification ([`../3_strategy_J1/spec/`](../3_strategy_J1/spec/)) was fixed and hashed before any result was seen. Only one signal, sign and horizon was allowed.
3. **Signal test.** On each weekly review date, the Spearman rank correlation (IC) between each S&P 500 stock's score and its next five-session return relative to its industry peers. The average IC is tested with a Newey–West t-statistic (lag 4). A placebo test shuffles scores within each date and industry 500 times.
4. **Portfolio backtest.** The five lowest-scoring Dow stocks are bought at the next open, with 0.05% charged on every trade, and compared with EW30 on the same dates.
5. **Robustness.** A block bootstrap (10-session blocks, 5,000 draws) on net excess return, and a deflated Sharpe ratio that adjusts for the number of trials.

## Backtesters

| File | What it does |
|---|---|
| [`backtesters/run_j1.py`](backtesters/run_j1.py) | The official J1 runner: signal test, placebo, portfolio backtest and statistics |
| [`backtesters/j1_portfolio_replay.py`](backtesters/j1_portfolio_replay.py) | An independent re-implementation of the J1 portfolio, used to check the official result |
| [`backtesters/j1_reference.py`](backtesters/j1_reference.py) | Reference functions used by the replay |
| [`../6_refinement_J2/code/j2_variants_v2.py`](../6_refinement_J2/code/j2_variants_v2.py) | The variant engine used in Section 6 (J1 is variant V0) |
| [`../archive/vedant_heat_diffusion_original/code/`](../archive/vedant_heat_diffusion_original/code/) | Vedant's original heat-diffusion backtester (earlier design) |

## J1 results (development period)

Source: [`results/RESULTS.md`](results/RESULTS.md).

| Measure | J1 | EW30 |
|---|---:|---:|
| Net cumulative return | 96.21% | 95.19% |
| Net excess return | +1.03% | — |
| Net Sharpe ratio | 0.823 | 0.902 |
| Maximum drawdown (net) | −21.90% | −21.37% |
| Mean turnover per review | 48.2% | — |
| Total trading costs | 10.36% | 0.49% |
| Costs as a share of gross edge | 66.2% | — |
| Bootstrap p-value (net excess) | 0.449 | — |

| Signal test | Result |
|---|---:|
| Average IC (direction-adjusted) | 0.0148 |
| Newey–West t-statistic | 2.08 |
| Placebo p-value | 0.002 |
| Review dates with ≥250 eligible S&P 500 stocks | 286 of 298 |

In the shorter common window used for Section 6, the same J1 rule (variant V0) gave +5.15% net excess, a net Sharpe of 0.836 against 0.880, and costs of 53.2% of the gross edge (see [`../6_refinement_J2/results/R9_VARIANTS.md`](../6_refinement_J2/results/R9_VARIANTS.md)).
