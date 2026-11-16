# Round 3: Deep inverse-heat connectivity optimization

## Scope and registered protocol

Selection rule and seven candidate definitions were written before selection runs in [PREREG.md](PREREG.md). The selection periods were Dow and cross-asset 2020-11-27 through 2022-12-30. The highest average daily Sharpe among candidates with mean turnover no greater than 50% in both universes was frozen in [FROZEN_CHOICE.md](FROZEN_CHOICE.md). The frozen rule is the 15 lowest unit-time heat connectivity names with inverse-connectivity weights, rebalanced every 21 sessions; costs are 5 bp per side on actual traded notional with next-open fills.

## Selection results

| Variant | Universe | Total P&L | CAGR | Sharpe | Max DD | Turnover / rebalance | Tracking error vs EW | Active share |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Full universe inverse connectivity k=1 | Dow selection | 14.40% | 6.64% | 0.48 | -21.37% | 5.6% | 0.34% | 2.4% |
| Full universe inverse connectivity k=2 | Dow selection | 14.78% | 6.81% | 0.49 | -20.98% | 8.0% | 0.72% | 4.8% |
| Equal weight in lowest-connectivity 15 | Dow selection | 10.93% | 5.09% | 0.40 | -19.16% | 45.9% | 5.06% | 50.0% |
| Inverse connectivity in lowest 10 | Dow selection | 15.44% | 7.11% | 0.54 | -16.07% | 56.3% | 7.31% | 66.7% |
| Inverse connectivity in lowest 15 | Dow selection | 11.84% | 5.50% | 0.43 | -18.75% | 45.4% | 5.10% | 50.0% |
| Lowest 15 plus 21-day reversal | Dow selection | 10.44% | 4.86% | 0.36 | -19.73% | 112.0% | 7.17% | 60.7% |
| Lowest 15 plus reversal, 63-session rebalance | Dow selection | 21.11% | 9.59% | 0.65 | -12.90% | 132.7% | 6.88% | 60.1% |
| Full universe inverse connectivity k=1 | Cross-asset selection | 8.55% | 4.00% | 0.52 | -8.71% | 39.2% | 12.19% | 49.5% |
| Full universe inverse connectivity k=2 | Cross-asset selection | 11.64% | 5.40% | 0.64 | -8.71% | 33.2% | 13.96% | 70.1% |
| Equal weight in lowest-connectivity 15 | Cross-asset selection | 4.34% | 2.05% | 0.27 | -16.40% | 32.4% | 5.07% | 50.0% |
| Inverse connectivity in lowest 10 | Cross-asset selection | 18.42% | 8.42% | 0.86 | -8.71% | 43.0% | 14.25% | 78.6% |
| Inverse connectivity in lowest 15 | Cross-asset selection | 13.85% | 6.40% | 0.75 | -8.71% | 45.3% | 13.29% | 69.2% |
| Lowest 15 plus 21-day reversal | Cross-asset selection | -1.85% | -0.89% | -0.07 | -15.65% | 104.9% | 5.99% | 60.1% |
| Lowest 15 plus reversal, 63-session rebalance | Cross-asset selection | 4.40% | 2.08% | 0.25 | -14.16% | 122.5% | 6.98% | 59.8% |

Selection rule chose `low15_inv`: average Sharpe 0.595, with turnover 45.4% in Dow and 45.3% in cross-asset. Although the selection Sharpe exceeds EW30 in the cross-asset window, this is a screen winner and not evidence of a persistent premium. The 10-name and reversal variants breach the turnover ceiling in at least one selection universe.

## Development test results

Each held-out window is reported once for the frozen variant against schedule-matched EW30 and SPY. Costs are after the actual-trade 5 bp/side model. Block p is a two-sided circular 10-session block bootstrap of strategy-minus-EW daily returns, 5,000 draws, seed 3666, plus-one correction. DSR uses 85 cumulative trials (approximately 70 prior variants + eight Round 2 portfolios + seven Round 3 candidates), using the independent-trial approximation.

| Test period | Strategy total | EW30 total | SPY total | Sharpe | EW Sharpe | IR | Tracking error | Max DD | Turnover | Active share | Block p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dow OOS1 | 16.35% | 20.79% | 34.81% | 1.27 | 1.52 | -0.77 | 4.34% | -8.49% | 47.8% | 50.0% | 0.3999 | 13.2% |
| Dow OOS2 | 1.54% | 11.69% | 13.89% | 0.17 | 0.74 | -1.66 | 5.48% | -15.51% | 42.2% | 50.0% | 0.1002 | 1.1% |
| Dow 2026 | 22.37% | 13.62% | 11.69% | 2.20 | 1.43 | 1.18 | 7.58% | -5.95% | 37.6% | 50.0% | 0.2547 | 32.0% |
| Cross-asset OOS | 42.27% | 32.54% | 107.18% | 1.19 | 0.95 | 0.23 | 8.16% | -7.43% | 52.3% | 59.1% | 0.6623 | 44.4% |

The equal-weighted average of the four window total-return differences (strategy minus EW30) is +0.97%; the concatenated daily active series compounds to -0.73%. The pooled daily active mean is 0.15% annualized, with block-bootstrap p=0.956; pooled strategy DSR is 62.9% at 85 trials. Because the windows include separate universes and overlapping dates, this is a descriptive pooled diagnostic.

## Round 3 criteria 1-5

| Criterion | Result |
|---|---|
| 1. Selection only on registered periods under written rule | PASS |
| 2. Sharpe above EW in at least 3 of 4 tests and positive pooled excess | FAIL (2/4 Sharpe wins; average window excess +0.97 pp) |
| 3. Clearly different: tracking error >=3% or active share >=20% | PASS (mean TE 6.39%; mean active share 52.3%) |
| 4. Pooled block p <0.10 with DSR reported | FAIL (p=0.956; pooled DSR 62.9% at 85 trials) |
| 5. Turnover <=50% per rebalance in all tests | FAIL (range 37.6% to 52.3%) |

The frozen candidate is not a direction that meets the full success definition. Its out-of-sample evidence is mixed; the low-connectivity concentration does produce a material active portfolio, but pooled inference and per-window turnover do not meet the pre-set hurdles. The sealed holdout remains for the coordinator and was not run here.

## Connectivity versus low beta

The same-universe low-beta factor sorts assets by beta to the universe EW portfolio using the previous 63 daily returns, then takes the bottom ten minus EW30. The pooled OLS slope of strategy active returns on this factor is 0.378 (t=21.28, R2=0.208; n=1724). This descriptive relationship helps identify a possible beta proxy; it does not establish a causal mechanism.

## Economic interpretation and refinement

The hypothesis is diversification: peripheral assets may have less exposure to network-wide shock transmission (Billio et al., 2012; Diebold and Yilmaz, 2014; Pozzi, Di Matteo and Aste, 2013). Concentrating in the least-connected 15 makes the book materially different from EW30, but the held-out evidence is mixed and turnover exceeds the 50% limit in the cross-asset test. The positive low-beta-factor slope suggests connectivity may partly proxy beta; that resembles the low-beta effect discussed by Frazzini and Pedersen (2014), though this long-only rule is not their market-neutral BAB strategy. Connectivity may also reflect sector composition and noisy short-window correlations rather than a durable contagion premium. EW30 remains the sensible default.

### Reproduction

From `r3_invheat`, run these exact commands:

```powershell
cd .\dow
py -3 code\pivot_backtest.py --runset=selection --cost=actual --reb=21 --roster=2020-08-31 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2022-12-30 --tag=r3_selection_dow
cd ..\xasset
py -3 code\pivot_backtest.py --runset=selection --cost=actual --reb=21 --roster=xasset30 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2022-12-30 --tag=r3_selection_xasset
cd ..\dow
py -3 code\pivot_backtest.py --cost=actual --reb=21 --roster=2020-08-31 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2024-02-23 --tag=r3_test_dow_early
py -3 code\pivot_backtest.py --cost=actual --reb=21 --roster=2024-11-08 --anchor=2024-12-06 --win-first=2024-12-06 --win-last=2026-10-30 --tag=r3_test_dow_recent
cd ..\xasset
py -3 code\pivot_backtest.py --cost=actual --reb=21 --roster=xasset30 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2026-10-30 --tag=r3_test_xasset
cd ..
py -3 analyze_r3.py
```

The first Dow OOS1 engine run emitted all pre-registered candidates because the test-only output filter had not applied. The frozen choice had already been selected and written down before any test results; only `low15_inv` is evaluated here. Later test runs emitted EW30 and the frozen choice only. There was no post-test tuning.

### Testing and validation

The copied engine's synthetic cost checks, actual-notional reconciliation, missing-data/calendar guards, and sampled future-truncation invariance checks passed on the recorded runs. The portable weight function was compared with the frozen selection ledger on cross-asset signal date 2020-11-25: it selected the same 15 names, with a maximum absolute weight difference of 3.6e-9 and a weight sum of 1. The selection screen comprised seven candidate definitions, each run once in each of the two selection universes.

### Refinement

Do not alter the choice based on these test outcomes. This seven-variant screen covered k=1/k=2 tilts, top-10/top-15 concentration, 21-day reversal, and 21/63-session rebalance. Within the 12-variant cap, it did not test k=3, rank tilts, tau changes, top-10 graph density, a 126-session correlation window, or a no-trade band; those remain untested options rather than negative results. A next development cycle can pre-register those options and test whether a beta-neutralized connectivity signal adds anything.

### Frozen strategy function

[frozen_strategy.py](frozen_strategy.py) exposes a function taking any folder of 30 daily adjusted-price CSVs and returns the frozen weights for a signal date.

### Charts

![Equity](frozen_choice_equity.png)

![Drawdown](frozen_choice_drawdown.png)

### Sources

- Billio, M., Getmansky, M., Lo, A. W., and Pelizzon, L. (2012), 'Econometric measures of connectedness and systemic risk in the finance and insurance sectors,' *Journal of Financial Economics*, 104(3), 535-559. [DOI](https://doi.org/10.1016/j.jfineco.2011.12.010).
- Diebold, F. X. and Yilmaz, K. (2014), 'On the network topology of variance decompositions: Measuring the connectedness of financial firms,' *Journal of Econometrics*, 182(1), 119-134. [DOI](https://doi.org/10.1016/j.jeconom.2014.04.012).
- Pozzi, F., Di Matteo, T. and Aste, T. (2013), 'Spread of Risk across Financial Markets: Better to Invest in the Peripheries,' *Scientific Reports*, 3, 1665. [DOI](https://doi.org/10.1038/srep01665).
- Bailey, D. H. and Lopez de Prado, M. (2014), 'The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality,' *The Journal of Portfolio Management*, 40(5), 94-107. [DOI](https://doi.org/10.3905/jpm.2014.40.5.094).
- Frazzini, A. and Pedersen, L. H. (2014), 'Betting Against Beta,' *Journal of Financial Economics*, 111(1), 1-25. [DOI](https://doi.org/10.1016/j.jfineco.2013.10.005).
