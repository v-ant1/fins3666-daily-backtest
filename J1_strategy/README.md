# J1: Weekly Within-Industry Reversal

## Design

Each week the strategy buys the five Dow stocks that have fallen furthest behind their industry peers over the previous five sessions, and holds them until the next review. A stock pushed below its peers by temporary selling should recover when the pressure fades, so the strategy is in effect paid for supplying liquidity to those sellers. This rule, referred to as J1, was the stronger of two reversal ideas in a screening of potential strategies.

## Score

Stocks are traded from the point-in-time Dow 30, but peers are drawn from the wider point-in-time S&P 500 so that each industry has enough members. For Dow stock $i$ at review date $t$, the five-session return is compared with the average five-session return of the other S&P 500 stocks in the same two-digit SIC industry, $\mathcal{P}_{i,t}$:

$$
r_{5,i,t} = \frac{P^{\text{adj}}_{i,t}}{P^{\text{adj}}_{i,t-5}} - 1,
\qquad
\bar r_{5,-i,t} = \frac{1}{|\mathcal{P}_{i,t}|}\sum_{j\in\mathcal{P}_{i,t}} r_{5,j,t},
\qquad
s_{i,t} = r_{5,i,t} - \bar r_{5,-i,t}.
$$

A stock needs at least one other peer to receive a score. A low score means the stock has lagged behind its industry over the past week.

## Trading rules

1. **Review:** every fifth trading session.
2. **Selection:** buy the five Dow stocks with the lowest scores, 20% of the portfolio each, long only.
3. **Timing:** scores use closing prices on the review date; trades happen at the next session's open.
4. **Cost:** 0.05% of each dollar traded, charged on actual trades.
5. **Benchmark:** equal-weighted point-in-time Dow 30 (EW30).

## Results (development period, 27 Nov 2020 to 30 Oct 2026)

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

| Signal test | Result |
|---|---:|
| Average rank correlation with next-week relative return | 0.0148 |
| Newey-West t-statistic | 2.08 |
| Placebo test p-value | 0.002 |

**In plain terms:** the signal did predict which stocks would recover, but trading costs ate about two-thirds of the gross gain. J1 ended only slightly ahead of the benchmark on return, with a lower Sharpe ratio.

## Folder contents

| Folder | Contents |
|---|---|
| [`code/`](code/) | `build_inputs.py` and `stage_j1_prices.py` build the signal and price inputs; `run_j1.py` runs the test; `test_j1_synthetic.py` checks the code on made-up data |
| [`spec/`](spec/) | The specification, frozen before any results were seen |
| [`results/`](results/) | Results, input quality checks and run notes |

The scripts were written for the original research folder layout, so file paths inside them may need adjusting to point at [`../data/`](../data/).
