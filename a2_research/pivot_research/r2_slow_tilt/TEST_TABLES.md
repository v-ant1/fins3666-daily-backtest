# Held-out test results

Returns, Sharpe, and drawdowns are computed from daily close-marked net equity and include 5 bp per-side transaction costs. CAGR uses 252 sessions per year. The benchmark EW30 is reset to equal weights on the same 21-session grid. SPY is buy-and-hold on the engine calendar. Information ratio and p-values use paired daily strategy-minus-EW30 returns.

| Test window | Tilt CAGR | EW30 CAGR | SPY CAGR | Tilt Sharpe | EW30 Sharpe | SPY Sharpe | Tilt max DD | EW30 max DD | SPY max DD | IR vs EW30 | Block p | DSR prob. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dow 2023-01-03 to 2024-02-23 | 20.3% | 17.3% | 30.5% | 1.66 | 1.47 | 2.13 | -8.8% | -8.9% | -10.0% | 1.70 | 0.016 | 0.260 |
| Dow 2024-12-06 to 2025-12-31 | 9.9% | 10.9% | 13.1% | 0.65 | 0.74 | 0.73 | -15.5% | -15.3% | -18.8% | -0.35 | 0.598 | 0.038 |
| Dow 2026-01-02 to 2026-10-30 | 18.8% | 16.8% | 14.0% | 1.51 | 1.45 | 1.08 | -9.4% | -8.5% | -8.9% | 0.79 | 0.496 | 0.148 |
| Cross-asset 2023-01-03 to 2026-10-30 | 7.5% | 7.5% | 21.2% | 0.91 | 0.93 | 1.37 | -6.9% | -7.0% | -18.8% | 0.02 | 0.954 | 0.259 |

Turnover is average actual traded notional divided by pretrade equity per rebalance, excluding the initial investment. Cost drag is annualized geometric drag from actual-cost factors, including final liquidation.

| Test window | Tilt turnover / rebalance | EW30 turnover / rebalance | Tilt cost drag / yr | EW30 cost drag / yr |
|---|---:|---:|---:|---:|
| Dow 2023-01-03 to 2024-02-23 | 39.1% | 4.6% | 0.31% | 0.11% |
| Dow 2024-12-06 to 2025-12-31 | 37.8% | 5.0% | 0.31% | 0.12% |
| Dow 2026-01-02 to 2026-10-30 | 40.0% | 6.5% | 0.34% | 0.16% |
| Cross-asset 2023-01-03 to 2026-10-30 | 34.6% | 2.8% | 0.23% | 0.04% |
