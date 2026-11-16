# R2-2: Slow, low-turnover relative-value tilt

## Research question and frozen specification

Can a low-strength monthly reversal tilt improve on equal weighting after realistic turnover costs, across both Dow stocks and a fixed 30-ETF cross-asset basket?

The strategy holds all 30 assets. At each 21-session rebalance, it ranks names cross-sectionally and sets weights to `(1/30) * (1 + 0.5 * (2 * rank - 1))`, where rank is a percentile from 0 to 1. The frozen signal is negative 21-session return divided by trailing 63-session annualized volatility. Signals use adjusted closes through the session before the next-open fill. It is a simple volatility-scaled own-return reversal proxy, not the factor-residual method in Blitz et al. The portfolio is long-only and fully invested; its target weights range from 1.67% to 5.00%.

The tilt idea follows the broad short-horizon reversal evidence in Jegadeesh (1990) and Lehmann (1990), while the volatility scaling is a risk-control choice motivated by residual-reversal research. Those papers use different samples and constructions, so they motivate a hypothesis rather than validate this implementation. Actual-trade costs are 0.05% of traded notional per side; fills are at the next session's open, and the final liquidation is charged. EW30 is reset to equal weights on the same 21-session grid so the comparison shares timing and fills. SPY is buy-and-hold on the same calendar; it is a broad equity comparator rather than a matched cross-asset benchmark.

## Preregistered selection and candidate results

The selection-only dates were 2020-11-27 to 2022-12-30 in both universes. The rule, recorded before the first performance result, excludes a candidate if average traded notional exceeds 50% of pretrade equity per rebalance in either universe, then picks the eligible candidate with the highest unweighted mean Sharpe across the two universes; ties go to lower mean turnover and then lower alpha. Sharpe is annualized from daily net returns with a zero risk-free rate.

The initially listed 12-1 momentum candidate was removed before the first run because the cross-asset history begins 2020-06-01, leaving fewer than 252 prior sessions at the start of selection. This amendment preserved the identical required selection dates across universes. Three candidates remained and all were evaluated in both universes.

| Candidate | Dow IS Sharpe | Dow turnover / rebalance | Cross-asset IS Sharpe | Cross-asset turnover / rebalance | Mean Sharpe | Decision |
|---|---:|---:|---:|---:|---:|---|
| 21-day reversal tilt, a=0.5 | 0.4685 | 38.53% | -0.0407 | 35.16% | 0.2139 | Eligible |
| 21-day reversal tilt, a=1.0 | 0.4616 | 73.52% | -0.1632 | 68.08% | 0.1492 | Excluded by turnover cap |
| Volatility-scaled 21-day reversal tilt, a=0.5 | 0.4695 | 38.97% | -0.0157 | 35.10% | **0.2269** | **Frozen choice** |

The frozen candidate's selection-period CAGR was 6.65% in Dow versus 6.53% EW30, and -0.60% in cross-asset versus 0.37% EW30. Its mean Sharpe edge over the unscaled 0.5 tilt was small. The choice follows the preregistered rule, not a claim of strong selection evidence. The signed choice and exact selection values are in [FROZEN_CHOICE.md](FROZEN_CHOICE.md); the protocol and amendment are in [PREREGISTRATION.md](PREREGISTRATION.md).

## Held-out results

Each held-out window uses the frozen candidate and is reported once below. Four identical test commands were replayed only to persist the EW30 cost ledgers; the strategy, parameters, and reported outputs were unchanged. CAGRs, Sharpe, and maximum drawdowns use daily net equity. Information ratio is annualized paired daily active return divided by its tracking error. Block-bootstrap p-values test the two-sided null of zero mean daily active return versus EW30, using circular 21-session blocks and 10,000 resamples. P-values are unadjusted across the four reported windows. The deflated-Sharpe probability compares each annualized Sharpe with the expected maximum null Sharpe across approximately 73 total candidate variants (about 70 prior variants plus these three), using a finite-sample skew/kurtosis adjustment and an independent-trial approximation. It is a screening statistic, not a formal correction for correlated strategies or serial dependence.

| Test window | Tilt CAGR | EW30 CAGR | SPY CAGR | Tilt Sharpe | EW30 Sharpe | SPY Sharpe | Tilt max DD | EW30 max DD | SPY max DD | IR vs EW30 | Block p | DSR prob. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dow 2023-01-03 to 2024-02-23 | 20.3% | 17.3% | 30.5% | 1.66 | 1.47 | 2.13 | -8.8% | -8.9% | -10.0% | 1.70 | 0.016 | 0.260 |
| Dow 2024-12-06 to 2025-12-31 | 9.9% | 10.9% | 13.1% | 0.65 | 0.74 | 0.73 | -15.5% | -15.3% | -18.8% | -0.35 | 0.598 | 0.038 |
| Dow 2026-01-02 to 2026-10-30 | 18.8% | 16.8% | 14.0% | 1.51 | 1.45 | 1.08 | -9.4% | -8.5% | -8.9% | 0.79 | 0.496 | 0.148 |
| Cross-asset 2023-01-03 to 2026-10-30 | 7.5% | 7.5% | 21.2% | 0.91 | 0.93 | 1.37 | -6.9% | -7.0% | -18.8% | 0.02 | 0.954 | 0.259 |

| Test window | Tilt turnover / rebalance | EW30 turnover / rebalance | Tilt cost drag / year | EW30 cost drag / year |
|---|---:|---:|---:|---:|
| Dow 2023-01-03 to 2024-02-23 | 39.1% | 4.6% | 0.31% | 0.11% |
| Dow 2024-12-06 to 2025-12-31 | 37.8% | 5.0% | 0.31% | 0.12% |
| Dow 2026-01-02 to 2026-10-30 | 40.0% | 6.5% | 0.34% | 0.16% |
| Cross-asset 2023-01-03 to 2026-10-30 | 34.6% | 2.8% | 0.23% | 0.04% |

Turnover is actual traded notional divided by pretrade equity, averaged over rebalances and excluding the initial investment. Cost drag is the annualized geometric drag from actual cost factors, including the terminal liquidation. The tilt traded roughly 35–40% of equity per 21-session rebalance, compared with 3–7% for EW30; its lower frequency kept estimated cost drag below 0.35% per year under the fixed 5 bp assumption.

![Net equity paths for the four held-out windows](chosen_variant_test_periods.png)

## Evaluation and plain-English summary

The selected tilt beat EW30 on CAGR and Sharpe in the first Dow window and in 2026, slightly trailed it in the 2024–25 Dow window, and was effectively tied on return but marginally weaker on Sharpe in cross-asset ETFs. It beat SPY only in the 2026 Dow window; SPY had the higher CAGR in the other three windows. One block-bootstrap active-return result was nominally small (p=0.016), but it was not repeated across the other tests, and no deflated-Sharpe probability exceeded 0.26. The result is mixed and does not establish a reliable edge. The strategy is implementable at modest turnover under the assumed costs, but it does not justify replacing EW30 as the default portfolio.

## Testing and validation

The local copies of the supplied official engine passed the actual-cost synthetic checks, future-truncation invariance at three sampled signal dates per run, complete-data checks, session-calendar checks against SPY, independent traded-notional/cost reconciliation, and ledger-to-equity reconciliation. The equity CSV header and row shape were repaired in the local copy so both EW30 and SPY are explicitly present. EW30's same-grid rebalance costs were also saved to a separate cost ledger. The input data had no zero-volume cells in the required test intervals. These checks validate implementation and arithmetic; they do not validate the strategy's expected return.

Run inventory: three candidate variants were tested in each of two selection universes (six successful selection evaluations), followed by the frozen candidate in four held-out windows. The four exact held-out commands were replayed once to persist the EW30 cost ledgers; no parameters or choices changed. Six earlier invocations stopped at future-truncation assertions caused by signal-routing code errors, before any performance output; those were fixed before the successful selection runs. Thus the analysis used 3 active variants, about 73 total variants including the roughly 70 earlier candidates, 10 unique successful strategy-window evaluations (6 selection plus 4 test), 4 identical test replays for accounting output, and 6 aborted technical attempts.

Important limits: daily adjusted OHLCV is not quote data, so spread and market impact are not directly observed. The fixed 5 bp per-side charge omits variable impact, taxes, and other implementation frictions. The Dow roster is point-in-time; the cross-asset basket is a fixed list and the sample is short for reliable inference. The selection choice was based on only 527 daily observations in each universe. The independent-trial assumption in the deflated-Sharpe approximation is especially rough because the tested tilts are closely related.

## Reproduction

Run from `r2_slow_tilt\Dow` or `r2_slow_tilt\xasset` as indicated. These are the six selection commands, using only the registered selection window:

```powershell
# From r2_slow_tilt\Dow
py -3 code\pivot_backtest.py --cost=actual --roster=2020-08-31 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2022-12-30 --reb=21 --mode=rev21_a05 --construct=tilt --tag=sel_rev21a05
py -3 code\pivot_backtest.py --cost=actual --roster=2020-08-31 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2022-12-30 --reb=21 --mode=rev21_a10 --construct=tilt --tag=sel_rev21a10
py -3 code\pivot_backtest.py --cost=actual --roster=2020-08-31 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2022-12-30 --reb=21 --mode=volrev21_a05 --construct=tilt --tag=sel_volrev21a05

# From r2_slow_tilt\xasset
py -3 code\pivot_backtest.py --cost=actual --roster=xasset30 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2022-12-30 --reb=21 --mode=rev21_a05 --construct=tilt --tag=sel_rev21a05
py -3 code\pivot_backtest.py --cost=actual --roster=xasset30 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2022-12-30 --reb=21 --mode=rev21_a10 --construct=tilt --tag=sel_rev21a10
py -3 code\pivot_backtest.py --cost=actual --roster=xasset30 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2022-12-30 --reb=21 --mode=volrev21_a05 --construct=tilt --tag=sel_volrev21a05
```

After freezing `volrev21_a05`, reproduce the held-out runs:

```powershell
# From r2_slow_tilt\Dow
py -3 code\pivot_backtest.py --cost=actual --roster=2020-08-31 --anchor=2023-01-03 --win-first=2023-01-03 --win-last=2024-02-23 --reb=21 --mode=volrev21_a05 --construct=tilt --tag=test_dow_oos1
py -3 code\pivot_backtest.py --cost=actual --roster=2024-11-08 --anchor=2024-12-06 --win-first=2024-12-06 --win-last=2025-12-31 --reb=21 --mode=volrev21_a05 --construct=tilt --tag=test_dow_oos2
py -3 code\pivot_backtest.py --cost=actual --roster=2024-11-08 --anchor=2026-01-02 --win-first=2026-01-02 --win-last=2026-10-30 --reb=21 --mode=volrev21_a05 --construct=tilt --tag=test_dow_2026

# From r2_slow_tilt\xasset
py -3 code\pivot_backtest.py --cost=actual --roster=xasset30 --anchor=2023-01-03 --win-first=2023-01-03 --win-last=2026-10-30 --reb=21 --mode=volrev21_a05 --construct=tilt --tag=test_xasset
```

From the `r2_slow_tilt` folder, regenerate block-bootstrap results, tables, and the chart with:

```powershell
py -3 analyze_results.py
```

The analysis uses a fixed random seed, 10,000 circular moving-block bootstrap samples, and 21-session blocks. Daily equity files, period metrics, cost ledgers, trades, and signal picks are under each universe's `outputs_rerun\` directory.

## References

- Jegadeesh, N. (1990), “Evidence of Predictable Behavior of Security Returns,” *The Journal of Finance*, 45(3), 881–898. [DOI](https://doi.org/10.1111/j.1540-6261.1990.tb05110.x).
- Lehmann, B. N. (1990), “Fads, Martingales, and Market Efficiency,” *The Quarterly Journal of Economics*, 105(1), 1–28. [DOI](https://doi.org/10.2307/2937816).
- Blitz, D., Huij, J., Lansdorp, S. D., and Verbeek, M. (2013), “Short-Term Residual Reversal,” *Journal of Financial Markets*, 16(3), 477–504. [DOI](https://doi.org/10.1016/j.finmar.2012.10.005).
- Novy-Marx, R. and Velikov, M. (2016), “A Taxonomy of Anomalies and Their Trading Costs,” *The Review of Financial Studies*, 29(1), 104–147. [DOI](https://doi.org/10.1093/rfs/hhv063).


