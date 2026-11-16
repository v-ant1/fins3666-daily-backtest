# Official-engine implementation and validation

## Outcome

The copied official engine now supports `pressure`, `heat50`, `nbr50`, `ew`, `resrev50`, `leadlag50`, and `rev21`, with either the existing buffered top-five book or a long-only rank tilt. The top-five portfolio keeps the original every-five-session rebalance, top-eight hold buffer, next-open fills, and 0.05% per-side actual-trade cost. The tilt holds all 30 names at weights `(1/30) * (1 + 0.5 * (2 * rank - 1))`; rank is the mode's percentile rank from 0 to 1.

The legacy modes reproduce the supplied official results to two decimal places:

| Window | Pressure | Heat50 | EW30 |
|---|---:|---:|---:|
| Earlier, 2020-11-27 to 2024-02-23 (full window) | 7.89% | 39.78% | 38.33% |
| Recent, 2024-12-06 to 2025-12-31 (full window) | 11.69% | 2.49% | 11.96% |

The fixed evaluation periods are IS 2020-11-27 to 2022-12-30, OOS1 2023-01-03 to 2024-02-23, and OOS2 2024-12-06 to 2025-12-31. Every signal mode passed the future-truncation invariance check on the first, middle, and final sampled signal date in each official window; top-five selections and tilt weights were also identical after truncation. The original synthetic cost, missing-data, ledger, and calendar assertions remain active.

## Constructions and reconciliation with round one

- `resrev50`: 50% pressure rank plus 50% rank of the weighted one-hop average of positive-edge graph neighbours' five-session market-demeaned returns, less the stock's own five-session market-demeaned return. The graph uses the symmetric top-five positive 63-session market-demeaned return-correlation graph.
- `leadlag50`: 50% pressure rank plus 50% rank of incoming leaders' pressure. A directed edge from leader `j` to target `i` is the positive correlation of `j`'s lagged daily market-demeaned return with `i`'s current return over the 63-session window; each target keeps its five strongest positive edges. This is the network agent's `leadlag_p` construction, implemented in the official engine.
- `rev21`: rank of the negative own 21-session close-to-close return, with the highest reversal score ranked highest.

The signal agent's “neighbour lead-lag” used neighbours' five-day returns as the signal (and separately tested its sign-flip); it was not a 50/50 pressure blend with leaders' pressure. Its “residual rev5” residualized own returns against the EW market return, also unlike this graph-neighbour residual reversal. The network agent's lead-lag pressure definition matches `leadlag50`; its exact `resid_rev` code used heat-kernel-diffused peer returns, whereas this task's explicit one-hop mean-neighbour definition is what `resrev50` implements. Thus the round-one numbers describe different signal constructions and simplified harnesses, while the following figures use the same official fills and actual-cost engine.

Results are descriptive. Positive excess CAGR in a cell is not evidence of outperformance; no significance test is reported here, and the fixed short periods plus the 14 tested mode/construction variants make isolated positive cells especially vulnerable to selection noise. No OOS period was used to choose a mode or parameter.

## Results

Figures are annualized CAGR, excess CAGR versus same-window EW30, zero-risk-free Sharpe, maximum drawdown, mean actual notional traded per rebalance divided by pre-trade equity, and annualized geometric cost drag. Values are rounded to two decimal places. Turnover is dollar notional turnover, not the share of names changed.

### IS: 2020-11-27 to 2022-12-30

| Variant | CAGR | Excess vs EW30 | Sharpe | MaxDD | Turnover / rebalance | Cost drag / year |
|---|---:|---:|---:|---:|---:|---:|
| pressure / top5 | -0.94% | -7.71 pp | 0.04 | -27.55% | 140.68% | 3.49% |
| pressure / tilt | 5.00% | -1.77 pp | 0.38 | -22.49% | 32.75% | 0.84% |
| heat50 / top5 | 5.38% | -1.39 pp | 0.36 | -29.36% | 143.79% | 3.57% |
| heat50 / tilt | 5.06% | -1.71 pp | 0.39 | -22.73% | 25.64% | 0.67% |
| nbr50 / top5 | 1.36% | -5.41 pp | 0.17 | -27.99% | 143.75% | 3.57% |
| nbr50 / tilt | 5.08% | -1.69 pp | 0.39 | -22.60% | 26.24% | 0.68% |
| EW30 / top5 | 6.77% | 0.00 pp | 0.48 | -21.38% | 2.25% | 0.08% |
| EW30 / tilt | 6.77% | 0.00 pp | 0.48 | -21.38% | 2.25% | 0.08% |
| resrev50 / top5 | -2.90% | -9.67 pp | -0.06 | -22.81% | 149.06% | 3.70% |
| resrev50 / tilt | 5.75% | -1.02 pp | 0.43 | -21.82% | 15.99% | 0.42% |
| leadlag50 / top5 | 9.70% | +2.93 pp | 0.59 | -20.40% | 138.40% | 3.44% |
| leadlag50 / tilt | 5.79% | -0.98 pp | 0.43 | -22.17% | 24.18% | 0.63% |
| rev21 / top5 | 2.75% | -4.01 pp | 0.23 | -25.50% | 61.12% | 1.55% |
| rev21 / tilt | 7.30% | +0.53 pp | 0.50 | -19.64% | 18.34% | 0.48% |

### OOS1: 2023-01-03 to 2024-02-23

| Variant | CAGR | Excess vs EW30 | Sharpe | MaxDD | Turnover / rebalance | Cost drag / year |
|---|---:|---:|---:|---:|---:|---:|
| pressure / top5 | 8.77% | -9.12 pp | 0.65 | -15.57% | 153.65% | 3.82% |
| pressure / tilt | 18.62% | +0.72 pp | 1.57 | -8.49% | 33.04% | 0.87% |
| heat50 / top5 | 21.88% | +3.98 pp | 1.39 | -15.71% | 139.43% | 3.48% |
| heat50 / tilt | 19.37% | +1.48 pp | 1.63 | -8.26% | 24.00% | 0.64% |
| nbr50 / top5 | 29.37% | +11.47 pp | 1.78 | -13.20% | 143.73% | 3.57% |
| nbr50 / tilt | 19.33% | +1.44 pp | 1.63 | -8.20% | 24.85% | 0.66% |
| EW30 / top5 | 17.89% | 0.00 pp | 1.51 | -8.89% | 2.10% | 0.10% |
| EW30 / tilt | 17.89% | 0.00 pp | 1.51 | -8.89% | 2.10% | 0.10% |
| resrev50 / top5 | 19.28% | +1.38 pp | 1.29 | -12.85% | 138.38% | 3.44% |
| resrev50 / tilt | 17.41% | -0.48 pp | 1.48 | -9.13% | 15.32% | 0.43% |
| leadlag50 / top5 | 24.98% | +7.09 pp | 1.59 | -8.30% | 141.58% | 3.50% |
| leadlag50 / tilt | 18.86% | +0.97 pp | 1.58 | -8.36% | 24.41% | 0.65% |
| rev21 / top5 | 31.23% | +13.34 pp | 1.87 | -7.23% | 65.16% | 1.65% |
| rev21 / tilt | 18.23% | +0.34 pp | 1.52 | -9.07% | 17.56% | 0.48% |

### OOS2: 2024-12-06 to 2025-12-31

| Variant | CAGR | Excess vs EW30 | Sharpe | MaxDD | Turnover / rebalance | Cost drag / year |
|---|---:|---:|---:|---:|---:|---:|
| pressure / top5 | 11.00% | -0.26 pp | 0.66 | -14.64% | 144.97% | 3.65% |
| pressure / tilt | 12.76% | +1.51 pp | 0.84 | -14.24% | 32.79% | 0.91% |
| heat50 / top5 | 2.35% | -8.91 pp | 0.22 | -15.46% | 142.10% | 3.58% |
| heat50 / tilt | 12.37% | +1.11 pp | 0.81 | -14.60% | 24.02% | 0.69% |
| nbr50 / top5 | -1.64% | -12.89 pp | 0.01 | -14.14% | 144.31% | 3.64% |
| nbr50 / tilt | 12.49% | +1.24 pp | 0.81 | -14.56% | 24.94% | 0.72% |
| EW30 / top5 | 11.26% | 0.00 pp | 0.75 | -15.31% | 2.51% | 0.16% |
| EW30 / tilt | 11.26% | 0.00 pp | 0.75 | -15.31% | 2.51% | 0.16% |
| resrev50 / top5 | 19.59% | +8.34 pp | 1.04 | -12.10% | 137.92% | 3.48% |
| resrev50 / tilt | 11.87% | +0.62 pp | 0.78 | -14.84% | 15.33% | 0.48% |
| leadlag50 / top5 | 28.68% | +17.42 pp | 1.45 | -13.87% | 140.68% | 3.55% |
| leadlag50 / tilt | 11.92% | +0.66 pp | 0.79 | -14.47% | 22.77% | 0.66% |
| rev21 / top5 | 19.53% | +8.27 pp | 0.85 | -18.11% | 66.90% | 1.75% |
| rev21 / tilt | 12.02% | +0.76 pp | 0.75 | -15.88% | 18.06% | 0.54% |

## Variant count and reproducibility

We ran 14 mode/construction combinations in each official window: seven modes times top5 and tilt, or 28 full-window runs. This yields 42 fixed period-by-variant results (14 per period); EW30 / top5 and EW30 / tilt are intentionally both counted and are identical. The 14 combinations are the complete reported grid; no additional variants were run. Daily equity and benchmark series, period metric CSVs, picks, trades, and cost details are in `outputs_rerun/`.

Run these commands from `w1_engine` to reproduce the full grid, per-day equity files, invariance checks, and period results:

```powershell
python code\pivot_backtest.py --cost=actual --buffer=8 --roster=2020-08-31 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2024-02-23 --mode=all --construct=both --tag=w1_earlier
python code\pivot_backtest.py --cost=actual --buffer=8 --mode=all --construct=both --tag=w1_recent
```

The resulting daily equity files are `outputs_rerun/w1_earlier_actualcost_buf8_equity_variants.csv` and `outputs_rerun/w1_recent_actualcost_buf8_equity_variants.csv`; their columns include each mode/construction, `ew`, and `spy`. Period metric files with unrounded values are the corresponding `*_period_results.csv` files.
