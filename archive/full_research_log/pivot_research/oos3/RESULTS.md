# Extra out-of-sample tests of the frozen lead-lag pivot (run 2026-11-10)

All parameters frozen (w1_engine/code/pivot_backtest.py, top 5, buffer 8, every 5 sessions, next-open fills, 0.05%/side actual costs). Full-window total returns.

## Test 3: Dow 30, 2026-01-07 to 2026-10-30 (42 rebalances, 2024-11-08 roster, repo data)
| Variant | Return | Vol | MaxDD | Sharpe |
|---|---|---|---|---|
| leadlag50 (pivot) | 6.93% | 18.4% | -11.43% | 0.54 |
| heat50 (original) | 9.05% | 19.1% | -15.12% | 0.65 |
| pressure only | -4.49% | 17.9% | -18.30% | -0.22 |
| EW30 | 11.20% | 11.3% | -8.52% | 1.21 |
| resrev50 | 25.65% | 15.8% | -6.90% | 1.85 |
| rev21 | 19.03% | 18.6% | -8.51% | 1.24 |
| SPY (open basis) | 9.18% | | | |
Caveat: roster frozen at 2024-11-08; any 2026 Dow changes and the June 2026 HON spin-off basis are not handled.

## Test 4: 30 sector/industry ETFs (pre-registered list in etf_basket.txt), 2020-11-27 to 2026-10-30 (298 rebalances, yfinance data)
| Variant | Return | Vol | MaxDD | Sharpe |
|---|---|---|---|---|
| leadlag50 (pivot) | 38.06% | 19.5% | -28.36% | 0.38 |
| heat50 (original) | 26.00% | 21.4% | -29.37% | 0.29 |
| pressure only | 57.54% | 19.5% | -28.25% | 0.49 |
| EW30 ETFs | 111.13% | 17.6% | -21.41% | 0.81 |
| resrev50 | 23.43% | 19.7% | -24.15% | 0.28 |
| rev21 | 94.61% | 24.0% | -25.84% | 0.59 |
| SPY (open basis) | 107.71% | | | |

Reproduce: from w1_engine: `py -3 code/pivot_backtest.py --cost=actual --buffer=8 --win-first=2026-01-02 --win-last=2026-10-30 --mode=all --construct=top5 --tag=oos3_dow2026`; from oos3/etf: `py -3 code/pivot_backtest.py --cost=actual --buffer=8 --roster=etf30 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2026-10-30 --mode=all --construct=top5 --tag=oos3_etf30`.

## Test 5: 30 cross-asset ETFs, no shared holdings (pre-registered list in xasset_basket.txt), 2020-11-27 to 2026-10-30 (298 rebalances, yfinance)
Replaces Test 4 as the main second-universe test (Test 4's sector ETFs overlap heavily in holdings).
| Variant | Return | Vol | MaxDD | Sharpe |
|---|---|---|---|---|
| leadlag50 (pivot) | -8.35% | 12.4% | -43.41% | -0.06 |
| heat50 (original) | -14.54% | 14.8% | -54.24% | -0.11 |
| pressure only | -10.05% | 12.7% | -42.50% | -0.08 |
| EW30 cross-asset | 34.50% | 8.7% | -15.84% | 0.62 |
| resrev50 | 1.62% | 13.5% | -44.72% | 0.09 |
| rev21 | 22.00% | 15.7% | -17.16% | 0.29 |
Reproduce from oos3/xasset: `py -3 code/pivot_backtest.py --cost=actual --buffer=8 --roster=xasset30 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2026-10-30 --mode=all --construct=top5 --tag=xasset30`
