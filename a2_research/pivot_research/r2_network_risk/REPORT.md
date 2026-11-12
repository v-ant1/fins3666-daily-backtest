# Network risk allocation: testing and evaluation

## Scope and selection rule

This screen tests whether a correlation network helps allocate risk across all 30 assets, even though earlier network scores did not reliably predict short-term returns. Every portfolio is long-only and fully invested. A candidate is rebalanced every 21 sessions, using the prior 63 completed daily returns and the official next-open fill, actual traded notional cost at 5 bp per side, terminal liquidation, and same-grid EW30 benchmark. No short positions or leverage are used.

The selection rule was written in [`SELECTION_PROTOCOL.md`](SELECTION_PROTOCOL.md) before seeing these selection outputs: choose the highest average daily Sharpe across Dow 30 and cross-asset 30 ETF selection windows (2020-11-27..2022-12-30), subject to mean turnover no higher than 50% of equity per rebalance in either universe. Ties break on average information ratio, then max drawdown, then turnover. EW30 is eligible; if none qualify, select EW30. The chosen variant and parameters were frozen in [`FROZEN_CHOICE.md`](FROZEN_CHOICE.md) before test periods were run.

## Eight fixed portfolios and economic rationale

All candidates allocate to all 30 constituents; no forecast of expected return is made. The correlation graph follows the project's 63-session network convention: positive correlations only, each name retains its five strongest links, and the undirected graph is the union of those links. The heat kernel uses exp(-L) with unit diffusion time.

- **EW30:** equal weights; a low-estimation-error reference that is hard to beat reliably in portfolio-selection studies (DeMiguel, Garlappi and Uppal, 2009).
- **Inverse volatility (`ivol63`):** weight each name inversely to 63-session volatility, aiming to avoid allowing the most volatile names to dominate portfolio risk.
- **Low degree (`low_degree`):** allocate more to names with fewer or weaker direct positive-correlation links, as a simple proxy for network peripherality (Pozzi, Di Matteo and Aste, 2013; Peralta and Zareei, 2016).
- **Low eigenvector centrality (`low_eigen`):** reduce weights in names connected to other well-connected names; this extends the peripherality idea beyond direct link count.
- **Inverse heat connectivity (`inv_heat`):** allocate less to names whose unit-time heat-kernel influence spreads more broadly through the graph, aiming to avoid assets whose shocks have a wide network footprint.
- **HRP (`hrp`):** cluster assets using correlation distance, then allocate recursively by cluster variance; this is intended to reduce concentration and covariance-inversion sensitivity (Lopez de Prado, 2016).
- **Degree plus inverse volatility (`degree_ivol`):** combine direct network peripherality with individual volatility control.
- **Heat plus inverse volatility (`heat_ivol`):** combine lower shock-spread connectivity with individual volatility control.

The network papers motivate a diversification hypothesis; they do not establish that these simplified rules work in this sample. In particular, the inverse centrality and heat rules are transparent heuristics, not mean-variance-optimal weights.

## Selection results

The selection-period table uses only the registered IS windows. Return and Sharpe are after actual-trade costs; turnover is mean traded notional / pre-trade equity per rebalance. Excess is annualized CAGR minus same-universe EW30 CAGR.

| Portfolio | Dow CAGR | Dow excess | Dow Sharpe | Dow maxDD | Dow turnover | ETF CAGR | ETF excess | ETF Sharpe | ETF maxDD | ETF turnover | Avg Sharpe |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EW30 | 6.53% | +0.00 pp | 0.47 | -21.67% | 4.7% | 0.37% | +0.00 pp | 0.09 | -16.14% | 3.1% | 0.28 |
| Inverse volatility | 6.72% | +0.19 pp | 0.51 | -19.68% | 8.9% | -3.65% | -4.03 pp | -0.63 | -14.89% | 9.1% | -0.06 |
| Low degree | 6.94% | +0.41 pp | 0.51 | -20.67% | 15.2% | 2.55% | +2.17 pp | 0.32 | -13.33% | 12.5% | 0.41 |
| Low eigenvector centrality | 4.92% | -1.61 pp | 0.40 | -19.37% | 33.5% | 4.74% | +4.36 pp | 0.42 | -9.33% | 41.7% | 0.41 |
| Inverse heat connectivity | 6.64% | +0.12 pp | 0.48 | -21.37% | 5.6% | 4.00% | +3.63 pp | 0.52 | -8.71% | 39.2% | 0.50 |
| HRP | 6.62% | +0.09 pp | 0.53 | -17.72% | 28.0% | -2.77% | -3.14 pp | -1.28 | -7.84% | 25.4% | -0.37 |
| Low degree × inverse volatility | 7.04% | +0.51 pp | 0.54 | -18.82% | 16.8% | -2.48% | -2.85 pp | -0.61 | -10.02% | 16.1% | -0.04 |
| Inverse heat × inverse volatility | 6.83% | +0.30 pp | 0.52 | -19.42% | 9.2% | 0.20% | -0.18 pp | 0.06 | -8.71% | 39.9% | 0.29 |

The frozen rule selects `inv_heat` with average Sharpe 0.50, versus 0.28 for schedule-matched EW30. All eight portfolios met the turnover cap in both selection universes. This is a narrow screen winner: on the Dow it only exceeded EW30's annualized return by 0.12 percentage points, and the ETF selection window's 3.63-point excess accounts for most of the average-Sharpe advantage.

## Evaluation

### Test-period results: all registered portfolios

All portfolios are shown descriptively; the frozen choice was not changed after selection.

| Period | Portfolio | Total return | CAGR | Sharpe | IR vs EW30 | MaxDD | Turnover |
|---|---|---:|---:|---:|---:|---:|---:|
| Dow OOS1 | EW30 | 20.79% | 18.04% | 1.52 | - | -8.92% | 4.6% |
| Dow OOS1 | Inverse volatility | 17.80% | 15.47% | 1.41 | -1.30 | -8.30% | 9.5% |
| Dow OOS1 | Low degree | 19.56% | 16.98% | 1.47 | -0.72 | -8.54% | 17.7% |
| Dow OOS1 | Low eigenvector centrality | 17.41% | 15.13% | 1.40 | -0.72 | -7.76% | 35.3% |
| Dow OOS1 | Inverse heat connectivity | 20.49% | 17.78% | 1.51 | -0.66 | -8.68% | 6.8% |
| Dow OOS1 | HRP | 12.49% | 10.89% | 1.08 | -1.67 | -8.58% | 29.1% |
| Dow OOS1 | Low degree × inverse volatility | 16.79% | 14.60% | 1.37 | -1.26 | -7.93% | 17.5% |
| Dow OOS1 | Inverse heat × inverse volatility | 17.58% | 15.28% | 1.40 | -1.32 | -8.11% | 9.4% |
| Dow OOS2 | EW30 | 11.69% | 11.00% | 0.74 | - | -15.34% | 5.0% |
| Dow OOS2 | Inverse volatility | 9.94% | 9.36% | 0.67 | -0.79 | -14.32% | 10.0% |
| Dow OOS2 | Low degree | 6.13% | 5.77% | 0.44 | -1.92 | -14.92% | 15.2% |
| Dow OOS2 | Low eigenvector centrality | 0.59% | 0.56% | 0.11 | -1.18 | -12.05% | 40.9% |
| Dow OOS2 | Inverse heat connectivity | 10.56% | 9.94% | 0.68 | -1.16 | -15.22% | 7.4% |
| Dow OOS2 | HRP | 3.43% | 3.23% | 0.29 | -1.59 | -13.69% | 36.1% |
| Dow OOS2 | Low degree × inverse volatility | 5.10% | 4.81% | 0.40 | -1.81 | -14.04% | 17.2% |
| Dow OOS2 | Inverse heat × inverse volatility | 9.01% | 8.48% | 0.62 | -1.10 | -14.22% | 10.6% |
| Dow 2026 | EW30 | 13.62% | 16.65% | 1.43 | - | -8.46% | 6.1% |
| Dow 2026 | Inverse volatility | 14.35% | 17.54% | 1.53 | 0.32 | -7.97% | 10.1% |
| Dow 2026 | Low degree | 16.47% | 20.19% | 1.80 | 1.24 | -7.52% | 15.8% |
| Dow 2026 | Low eigenvector centrality | 12.11% | 14.77% | 1.23 | -0.17 | -6.35% | 43.1% |
| Dow 2026 | Inverse heat connectivity | 15.10% | 18.48% | 1.63 | 1.25 | -8.04% | 9.4% |
| Dow 2026 | HRP | 17.38% | 21.31% | 1.96 | 0.73 | -6.01% | 37.4% |
| Dow 2026 | Low degree × inverse volatility | 16.97% | 20.81% | 1.92 | 1.10 | -6.95% | 17.1% |
| Dow 2026 | Inverse heat × inverse volatility | 15.65% | 19.17% | 1.73 | 0.78 | -7.50% | 12.1% |
| Cross-asset OOS | EW30 | 32.54% | 7.67% | 0.95 | - | -6.98% | 2.9% |
| Cross-asset OOS | Inverse volatility | 22.55% | 5.48% | 1.11 | -0.55 | -5.13% | 8.3% |
| Cross-asset OOS | Low degree | 28.52% | 6.80% | 0.85 | -0.22 | -7.32% | 12.6% |
| Cross-asset OOS | Low eigenvector centrality | 26.78% | 6.42% | 0.89 | -0.11 | -9.90% | 39.8% |
| Cross-asset OOS | Inverse heat connectivity | 42.30% | 9.69% | 1.36 | 0.28 | -6.58% | 36.3% |
| Cross-asset OOS | HRP | 17.89% | 4.41% | 1.88 | -0.51 | -1.61% | 39.5% |
| Cross-asset OOS | Low degree × inverse volatility | 22.73% | 5.52% | 1.43 | -0.48 | -3.78% | 15.2% |
| Cross-asset OOS | Inverse heat × inverse volatility | 28.26% | 6.74% | 1.54 | -0.14 | -3.84% | 35.6% |

### Frozen inverse-heat choice versus benchmarks

The p-value is a two-sided circular 10-session block bootstrap on daily active returns, demeaned under the null, 5,000 draws, seed 3666, plus-one correction. DSR is the estimated probability of exceeding the expected best Sharpe among 78 effective cumulative trials.

| Period | Strategy return | EW30 return | SPY return | CAGR | Sharpe | EW Sharpe | MaxDD | EW MaxDD | IR | TE | Block p | DSR | Turnover |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dow OOS1 | 20.49% | 20.79% | 34.81% | 17.78% | 1.51 | 1.52 | -8.68% | -8.92% | -0.66 | 0.35% | 0.513 | 20.2% | 6.8% |
| Dow OOS2 | 10.56% | 11.69% | 13.89% | 9.94% | 0.68 | 0.74 | -15.22% | -15.34% | -1.16 | 0.85% | 0.283 | 3.9% | 7.4% |
| Dow 2026 | 15.10% | 13.62% | 11.69% | 18.48% | 1.63 | 1.43 | -8.04% | -8.46% | 1.25 | 1.21% | 0.179 | 16.9% | 9.4% |
| Cross-asset OOS | 42.30% | 32.54% | 107.18% | 9.69% | 1.36 | 0.95 | -6.58% | -6.98% | 0.28 | 6.39% | 0.583 | 58.3% | 36.3% |

### Plain-English evaluation

The selected heat-connectivity allocation gave mixed held-out results. It slightly trailed schedule-matched EW30 in the 2023 to early 2024 Dow window and the 2024-2025 Dow window, then beat it in the 2026 Dow window and in the longer cross-asset test. The cross-asset excess was not statistically distinguishable from zero under the 10-session block bootstrap (p = 0.583); none of the four test-window bootstrap p-values is below 0.05. Its 2026 Dow information ratio was positive, but that window is short and its bootstrap p-value is 0.179. The low DSR in Dow 2025 (3.9%) and the 78-trial DSR elsewhere reinforce that this is not robust evidence of a repeatable advantage. The result supports keeping network connectivity as a risk-allocation hypothesis for prospective tracking, not claiming that the network improves returns. EW30 remains a sensible default.

All weight rules rebalance only every 21 sessions and average turnover stayed below the pre-registered ceiling. The selected inverse-heat portfolio traded 5.6% and 39.2% of equity per rebalance in the two selection periods, and 6.8%, 7.4%, 9.4%, and 36.3% in the four tests. Flat costs omit spread variation, market impact, taxes, and tracking effects; these results use daily adjusted OHLCV bars and the supplied 5 bp per-side assumption. The 30-name graph is estimated from a short rolling window, so edges and centralities may change materially with a different lookback or graph threshold. No additional tuning was done.

### Significance and trial accounting

The report includes a circular 10-session block-bootstrap test of daily inverse-heat returns in excess of same-grid EW30, using 5,000 draws, seed 3666 and a plus-one p-value correction. DSR follows Bailey and Lopez de Prado (2014); the effective trial count is 78 (approximately 70 previously explored strategy variants plus these eight pre-specified portfolios, including EW30). The DSR uses an independent-trial approximation and cannot model dependence among these closely related portfolios; it should be read as a sensitivity summary. The 8 portfolio definitions generated 16 selection-series evaluations and 32 test-series evaluations; these repeated market windows are not counted as 48 independent strategy trials.

## Testing and validation

The copied engine retained its synthetic actual-cost self-tests, ledger-to-equity reconciliation, missing-data fail-fast checks, calendar checks and next-open fills. All eight weight vectors passed future-truncation invariance at the first, middle and final sampled signal date in each of the five engine runs. Each engine run emitted eight full-universe portfolio series and a same-schedule EW30/SPY benchmark. The equity CSV writer was corrected in these copies so its header matches the output rows and the EW column is not duplicated; all five runs were repeated after that correction. The reconciled daily equity CSVs, per-rebalance costs and trade ledgers are in each universe's `outputs_rerun` folder.

## Refinement

Keep EW30 as the default comparison and treat inv_heat as a frozen candidate for prospective tracking. Do not retune its 63-session window, five-link graph, unit diffusion time or 21-session rebalance rule from these test results. A later review can check whether network membership is stable across windows and whether any excess return persists under the same cost and fill assumptions.

### Reproduction commands

Start in the `r2_network_risk` folder; the commands change into each universe folder. Python and numpy/scipy are required. These five commands reproduce the two selection windows and the three test data batches; all eight fixed portfolios are evaluated by each command. The 2026 Dow test is sliced from the frozen 2024-roster run, and the cross-asset test is sliced to the registered 2023-2026 dates.

```powershell
# Selection: Dow 30
cd .\dow
py -3 code\pivot_backtest.py --cost=actual --reb=21 --roster=2020-08-31 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2022-12-30 --tag=selection_dow

# Selection: cross-asset 30 ETFs
cd ..\xasset
py -3 code\pivot_backtest.py --cost=actual --reb=21 --roster=xasset30 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2022-12-30 --tag=selection_xasset

# Test: Dow 2023-01-03..2024-02-23
cd ..\dow
py -3 code\pivot_backtest.py --cost=actual --reb=21 --roster=2020-08-31 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2024-02-23 --tag=test_dow_earlier

# Test: Dow 2024-12-06..2026-10-30 (report 2024-12-06..2025-12-31 and 2026-01-02..2026-10-30 separately)
py -3 code\pivot_backtest.py --cost=actual --reb=21 --roster=2024-11-08 --anchor=2024-12-06 --win-first=2024-12-06 --win-last=2026-10-30 --tag=test_dow_recent

# Test: cross-asset 30 ETFs; report 2023-01-03..2026-10-30
cd ..\xasset
py -3 code\pivot_backtest.py --cost=actual --reb=21 --roster=xasset30 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2026-10-30 --tag=test_xasset

# Rebuild summary tables and PNG charts
cd ..
py -3 analyze_risk.py
```

### References

- DeMiguel, V., Garlappi, L. and Uppal, R. (2009), "Optimal Versus Naive Diversification: How Inefficient Is the 1/N Portfolio Strategy?", *Review of Financial Studies*, 22(5), 1915-1953. [DOI: 10.1093/rfs/hhm075](https://doi.org/10.1093/rfs/hhm075).
- Pozzi, F., Di Matteo, T. and Aste, T. (2013), "Spread of Risk across Financial Markets: Better to Invest in the Peripheries", *Scientific Reports*, 3, 1665. [DOI: 10.1038/srep01665](https://doi.org/10.1038/srep01665).
- Peralta, G. and Zareei, A. (2016), "A Network Approach to Portfolio Selection", *Journal of Empirical Finance*, 38(A), 157-180. [DOI: 10.1016/j.jempfin.2016.06.003](https://doi.org/10.1016/j.jempfin.2016.06.003).
- Lopez de Prado, M. (2016), "Building Diversified Portfolios that Outperform Out of Sample", *The Journal of Portfolio Management*, 42(4), 59-69. [DOI: 10.3905/jpm.2016.42.4.059](https://doi.org/10.3905/jpm.2016.42.4.059).
- Bailey, D. H. and Lopez de Prado, M. (2014), "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality", *The Journal of Portfolio Management*, 40(5), 94-107. [DOI: 10.3905/jpm.2014.40.5.094](https://doi.org/10.3905/jpm.2014.40.5.094).



