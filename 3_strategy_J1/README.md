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

## Folder contents

| Folder | Contents |
|---|---|
| [`code/`](code/) | `build_inputs.py` builds the J1 scores; `stage_j1_prices.py` prepares the price arrays; `test_j1_synthetic.py` checks the code on made-up data |
| [`spec/`](spec/) | The J1 specification, frozen before any results were seen |

The backtester and results are in [`../4_5_testing_and_evaluation/`](../4_5_testing_and_evaluation/); the refinement into J2 is in [`../6_refinement_J2/`](../6_refinement_J2/). Input data is in [`../2_data/`](../2_data/).

The scripts were written for the original research folder layout, so file paths inside them may need adjusting to point at `../2_data/`.
