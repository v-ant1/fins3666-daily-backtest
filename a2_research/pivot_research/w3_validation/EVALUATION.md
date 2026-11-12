# Daily return evaluation

Input: `run\outputs_rerun\w3_earlier_official_actualcost_buf8_equity_variants.csv` plus `run\outputs_rerun\w3_recent_official_actualcost_buf8_equity_variants.csv`. EW benchmark: `ew`; market benchmark: `spy`. Trials for DSR: **44**. Bootstrap: circular 10-session blocks, 5,000 draws, seed 3666 (period and strategy offsets applied).

## IS

| Strategy | Total | CAGR | Vol | Sharpe | Sortino | Max DD | DD duration (days) | VaR95 | ES95 | β SPY | α SPY (ann.) | ρ SPY | β EW | α EW (ann.) | ρ EW | TE | IR | 5d win % | Excess t | Block p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pressure | -1.96% | -0.94% | 18.89% | 0.04 | 0.06 | -27.55% | 223 | 1.97% | 2.69% | 0.75 | -3.54% | 0.76 | 0.95 | -6.63% | 0.82 | 10.96% | -0.64 | 46.67% | -0.93 | 0.324 | 1.53% |
| heat50 | 11.58% | 5.38% | 20.16% | 0.36 | 0.51 | -29.36% | 177 | 1.96% | 2.90% | 0.79 | 2.66% | 0.75 | 0.99 | -0.51% | 0.80 | 12.18% | -0.05 | 53.33% | -0.07 | 0.950 | 4.44% |
| nbr50 | 2.86% | 1.36% | 19.33% | 0.17 | 0.23 | -27.99% | 224 | 1.91% | 2.81% | 0.75 | -1.16% | 0.74 | 0.94 | -4.21% | 0.79 | 11.80% | -0.39 | 52.38% | -0.57 | 0.600 | 2.36% |

## OOS1

| Strategy | Total | CAGR | Vol | Sharpe | Sortino | Max DD | DD duration (days) | VaR95 | ES95 | β SPY | α SPY (ann.) | ρ SPY | β EW | α EW (ann.) | ρ EW | TE | IR | 5d win % | Excess t | Block p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pressure | 10.05% | 8.77% | 14.64% | 0.65 | 0.97 | -15.57% | 255 | 1.43% | 1.78% | 0.83 | -12.91% | 0.73 | 1.02 | -7.92% | 0.79 | 9.03% | -0.85 | 50.88% | -0.90 | 0.285 | 6.14% |
| heat50 | 25.27% | 21.88% | 15.07% | 1.39 | 2.12 | -15.71% | 214 | 1.51% | 1.91% | 0.85 | -2.22% | 0.73 | 1.01 | 3.69% | 0.76 | 9.84% | 0.39 | 50.88% | 0.41 | 0.724 | 22.68% |
| nbr50 | 34.08% | 29.37% | 15.19% | 1.77 | 2.79 | -13.20% | 207 | 1.42% | 1.89% | 0.86 | 3.60% | 0.73 | 1.04 | 9.17% | 0.77 | 9.62% | 1.02 | 54.39% | 1.09 | 0.280 | 36.71% |

## OOS2

| Strategy | Total | CAGR | Vol | Sharpe | Sortino | Max DD | DD duration (days) | VaR95 | ES95 | β SPY | α SPY (ann.) | ρ SPY | β EW | α EW (ann.) | ρ EW | TE | IR | 5d win % | Excess t | Block p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pressure | 11.69% | 11.00% | 18.49% | 0.66 | 0.91 | -14.64% | 45 | 1.82% | 2.83% | 0.77 | 1.32% | 0.80 | 0.96 | 0.64% | 0.83 | 10.26% | 0.02 | 47.17% | 0.02 | 0.983 | 6.10% |
| heat50 | 2.49% | 2.35% | 19.11% | 0.22 | 0.31 | -15.46% | 98 | 1.76% | 2.75% | 0.72 | -5.97% | 0.72 | 0.91 | -6.77% | 0.76 | 12.40% | -0.63 | 39.62% | -0.65 | 0.547 | 2.22% |
| nbr50 | -1.74% | -1.64% | 18.79% | 0.01 | 0.01 | -14.14% | 90 | 1.85% | 2.63% | 0.73 | -10.17% | 0.75 | 0.93 | -11.03% | 0.79 | 11.50% | -1.03 | 41.51% | -1.06 | 0.282 | 1.31% |

## Reading the results

Heat50 cumulative return relative to EW30 is IS -3.10%, OOS1 4.65%, OOS2 -9.48%. The sign changes across periods, and no heat50 block-bootstrap p-value is below 5%, so these observed differences do not establish statistically reliable outperformance. The same tables show pressure-only and neighbour-average results, so the heat blend should be judged against both the benchmark and its simpler controls; one favourable subperiod alone is not evidence of a persistent edge.

## Validation design

The evaluation periods were fixed before inspecting these outputs: IS 2020-11-27–2022-12-30, OOS1 2023-01-03–2024-02-23, and OOS2 2024-12-06–2025-12-31. Only IS is suitable for selecting among candidates; OOS1 and OOS2 are held-out checks and are not used to retune parameters. For each strategy and period, report daily-return diagnostics, a conventional excess-return t-statistic, and a two-sided circular 10-session block-bootstrap test with 5,000 draws against zero mean excess return versus EW30. Because roughly 44 or more signal and portfolio variants were explored across the broader research process, the DSR uses a trial count of 44 by default to account approximately for selection; this independent-trial adjustment is a sensitivity summary and cannot recover dependence across trials. No outperformance claim is made from a positive point estimate alone.

## Usage

A pivot equity CSV with `date`, one or more strategy wealth-index columns, `ew`, and `spy` can be evaluated in one command from this folder:

```powershell
py -3 evaluate.py path\to\pivot_equity.csv --outdir path\to\evaluation
```

Strategy columns are inferred automatically; pass `--strategies candidate_a candidate_b` to select them, `--trials 44` to set the documented search count, or repeat `--append another.csv` for separately initialized windows. The output folder receives this report and all four PNG charts. The date column must be ascending and unique, wealth indexes finite and positive, and a gap greater than 10 calendar days resets the wealth series to its $1 baseline.

## Definitions

Returns are computed from adjacent wealth observations; at a gap longer than 10 calendar days the input is treated as a separately initialized wealth segment and reset to its $1 base. Annualisation uses 252 sessions. Volatility and Sharpe use sample standard deviation and a zero risk-free rate. Sortino uses the root mean square of negative daily returns with a zero target. Maximum drawdown is the worst peak-to-trough decline; duration is the longest consecutive daily span below a running peak before recovery. Historical VaR95 is the 95th percentile of daily loss (so positive means loss); ES95 is the average loss at or beyond that cutoff. CAPM alpha is the annualised arithmetic daily intercept against each benchmark. Tracking error and information ratio use daily strategy-minus-EW30 returns. Five-session win rate uses non-overlapping blocks anchored at the period start and compares compounded returns. The excess-return t-stat is the ordinary two-sided daily-mean statistic and does not adjust for serial dependence.

The bootstrap p-value resamples circular 10-day blocks from demeaned excess returns under the null, retaining local dependence approximately; a plus-one correction avoids zero p-values. DSR is the estimated probability that the strategy Sharpe exceeds the expected maximum Sharpe across 44 independent trials, using observed sample skewness and kurtosis following Bailey and López de Prado (2014). The independent-trial approximation cannot model correlation among historical variants and does not replace a joint, fully documented trial return matrix.

Charts: `cumulative_equity.png`, `drawdown.png`, `rolling_63d_excess.png`, and `excess_return_by_period.png`.
