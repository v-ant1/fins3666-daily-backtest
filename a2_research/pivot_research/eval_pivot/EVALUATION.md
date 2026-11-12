# Daily return evaluation

Input: `..\eval_pivot\w1_earlier_fixed.csv` plus `..\eval_pivot\w1_recent_fixed.csv`. EW benchmark: `ew`; market benchmark: `spy`. Trials for DSR: **58**. Bootstrap: circular 10-session blocks, 5,000 draws, seed 3666 (period and strategy offsets applied).

## IS

| Strategy | Total | CAGR | Vol | Sharpe | Sortino | Max DD | DD duration (days) | VaR95 | ES95 | β SPY | α SPY (ann.) | ρ SPY | β EW | α EW (ann.) | ρ EW | TE | IR | 5d win % | Excess t | Block p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| leadlag50_top5 | 21.37% | 9.70% | 18.62% | 0.59 | 0.84 | -20.40% | 190 | 1.86% | 2.66% | 0.75 | 6.62% | 0.77 | 0.95 | 3.52% | 0.83 | 10.46% | 0.30 | 53.33% | 0.43 | 0.643 | 7.04% |
| rev21_tilt | 15.87% | 7.30% | 16.79% | 0.50 | 0.73 | -19.64% | 191 | 1.70% | 2.38% | 0.83 | 3.62% | 0.94 | 1.03 | 0.37% | 0.99 | 1.93% | 0.30 | 42.86% | 0.44 | 0.646 | 5.44% |
| heat50_top5 | 11.58% | 5.38% | 20.16% | 0.36 | 0.51 | -29.36% | 177 | 1.96% | 2.90% | 0.79 | 2.66% | 0.75 | 0.99 | -0.51% | 0.80 | 12.18% | -0.05 | 53.33% | -0.07 | 0.952 | 3.54% |

## OOS1

| Strategy | Total | CAGR | Vol | Sharpe | Sortino | Max DD | DD duration (days) | VaR95 | ES95 | β SPY | α SPY (ann.) | ρ SPY | β EW | α EW (ann.) | ρ EW | TE | IR | 5d win % | Excess t | Block p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| leadlag50_top5 | 28.91% | 24.98% | 14.76% | 1.59 | 2.44 | -8.30% | 148 | 1.46% | 1.77% | 0.82 | 1.23% | 0.72 | 1.02 | 5.96% | 0.78 | 9.18% | 0.68 | 47.37% | 0.73 | 0.394 | 25.97% |
| rev21_tilt | 21.01% | 18.23% | 11.51% | 1.51 | 2.31 | -9.07% | 85 | 1.09% | 1.45% | 0.76 | -3.28% | 0.86 | 1.00 | 0.22% | 0.99 | 1.62% | 0.19 | 50.88% | 0.20 | 0.833 | 23.59% |
| heat50_top5 | 25.27% | 21.88% | 15.07% | 1.39 | 2.12 | -15.71% | 214 | 1.51% | 1.91% | 0.85 | -2.22% | 0.73 | 1.01 | 3.69% | 0.76 | 9.84% | 0.39 | 50.88% | 0.41 | 0.719 | 19.62% |

## OOS2

| Strategy | Total | CAGR | Vol | Sharpe | Sortino | Max DD | DD duration (days) | VaR95 | ES95 | β SPY | α SPY (ann.) | ρ SPY | β EW | α EW (ann.) | ρ EW | TE | IR | 5d win % | Excess t | Block p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| leadlag50_top5 | 30.62% | 28.68% | 18.62% | 1.45 | 2.22 | -13.87% | 74 | 1.47% | 2.44% | 0.72 | 16.80% | 0.74 | 0.92 | 15.94% | 0.79 | 11.44% | 1.31 | 56.60% | 1.35 | 0.189 | 19.80% |
| rev21_tilt | 12.78% | 12.02% | 17.16% | 0.75 | 1.13 | -15.88% | 88 | 1.51% | 2.41% | 0.81 | 1.32% | 0.91 | 1.06 | 0.10% | 0.99 | 2.49% | 0.35 | 49.06% | 0.36 | 0.614 | 5.40% |
| heat50_top5 | 2.49% | 2.35% | 19.11% | 0.22 | 0.31 | -15.46% | 98 | 1.76% | 2.75% | 0.72 | -5.97% | 0.72 | 0.91 | -6.77% | 0.76 | 12.40% | -0.63 | 39.62% | -0.65 | 0.543 | 1.72% |

## Reading the results

Compare each strategy's return and risk with EW30 in each fixed period. A positive excess return is descriptive; evidence of reliable outperformance also requires the dependence-aware bootstrap test and must be read in light of the number of variants explored.

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

The bootstrap p-value resamples circular 10-day blocks from demeaned excess returns under the null, retaining local dependence approximately; a plus-one correction avoids zero p-values. DSR is the estimated probability that the strategy Sharpe exceeds the expected maximum Sharpe across 58 independent trials, using observed sample skewness and kurtosis following Bailey and López de Prado (2014). The independent-trial approximation cannot model correlation among historical variants and does not replace a joint, fully documented trial return matrix.

Charts: `cumulative_equity.png`, `drawdown.png`, `rolling_63d_excess.png`, and `excess_return_by_period.png`.
