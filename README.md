# FINS3666 Group Project: Buying-Pressure Strategy

This repository holds the trading strategy, code and data behind our FINS3666 report.

## The selected strategy: J1, weekly within-industry reversal

Each week, buy the five Dow 30 stocks that have fallen furthest behind their industry peers over the last five trading sessions, and hold them until the next weekly review.

Everything for it is in **[`J1_strategy/`](J1_strategy/)**: how it works, the code, the frozen specification and the results.

## Repository map

| Folder | What is in it |
|---|---|
| [`J1_strategy/`](J1_strategy/) | **Start here.** The selected strategy: design, code, specification and results |
| [`data/`](data/) | The input data used to build and test J1 (report Section 3) |
| [`other_strategies/`](other_strategies/) | One-page PDFs of the other strategies that showed a positive edge but were not statistically significant, plus a summary of all attempts |
| [`archive/`](archive/) | Earlier work, kept for reference: Vedant's original heat-diffusion backtest and the full research log |

## Data period and costs

- Development data: 27 November 2020 to 30 October 2026.
- Universes: point-in-time Dow 30 (traded) and point-in-time S&P 500 (industry peers).
- Trading cost: 0.05% of each dollar traded.
- Benchmark: equal-weighted Dow 30.

Price data comes from public sources (Yahoo Finance and Alpaca); industry codes come from SEC EDGAR.
