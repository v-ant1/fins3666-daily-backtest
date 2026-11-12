# EW basket timing and risk overlays

## Preregistered selection rule (written before test results)
Compare four round-number overlays: 6-month asset time-series momentum, 12-month asset time-series momentum, 10% volatility target, and 15% volatility target. Select the highest arithmetic mean annualized daily Sharpe across Dow and cross-asset IS, both 2020-11-27 to 2022-12-30; exact ties are resolved by the listed order. Test periods play no role in selection.

Frozen variant: **mom126** (mean IS Sharpe 0.329). All four candidates were run on both IS universes and every preregistered test period (24 universe-period-candidate runs; EW30 benchmark additionally on every segment).

## Design and implementation

The basket holds equal dollars in the 30 roster names at each five-session rebalance. Momentum candidates keep each name at its 1/30 weight only when its trailing 126 or 252 session adjusted-close return is positive; otherwise that slice stays in zero-return cash. Volatility candidates scale the entire EW basket by min(1, target / trailing annualized standard deviation of daily EW returns), using the previous 21 sessions and 10% or 15% targets. Rebalance execution uses the next session open, adjusted OHLC prices, 5 bp per side on actual traded notional, including drift and final liquidation. Cash earns 0%; short sales and borrowing are not used. The copied engine source and price files live under dow/ and xasset/.

## Selection-period results

|Variant|Dow IS Sharpe|Cross-asset IS Sharpe|Mean|
|---|---:|---:|---:|
|mom126|0.152|0.506|0.329|
|mom252|-0.016|-0.207|-0.112|
|vol10|0.213|0.022|0.118|
|vol15|0.367|0.114|0.240|

## Frozen choice: test results

Returns and risk are net of costs. SPY is buy-and-hold adjusted close with no added trading cost. IR is annualized active mean divided by tracking error against same-universe EW30. Bootstrap p-values use 5,000 circular 10-session block resamples of paired daily active returns under the zero-mean null; p-values are unadjusted. DSR follows Bailey and López de Prado (2014), using 74 total trials (about 70 prior variants plus these four); the independent-trial approximation is imperfect because strategies are correlated.

|Period|Strategy|CAGR|EW30 CAGR|SPY CAGR|Sharpe|EW30 Sharpe|SPY Sharpe|MaxDD|EW30 MaxDD|IR|Block p|DSR (74)|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|Dow test 1|mom126|8.85%|17.89%|29.99%|1.17|1.51|2.09|-5.47%|-8.89%|-1.62|0.084|0.121|
|Dow test 2|mom126|1.12%|11.31%|13.27%|0.16|0.75|0.74|-12.20%|-15.31%|-1.27|0.034|0.013|
|Dow test 3|mom126|8.45%|16.61%|14.26%|1.20|1.42|1.09|-4.51%|-8.52%|-1.22|0.333|0.092|
|Cross-asset test|mom126|4.21%|7.68%|21.05%|0.72|0.96|1.36|-5.58%|-6.90%|-0.85|0.062|0.158|

## Validation and evaluation

The tests use fixed dates and the same 30-name universe per comparison; every strategy and EW30 series is generated on the same five-session schedule with next-open fills. Signals use information available by the previous close. The two Dow rosters follow the project’s fixed 2020-08-31 and 2024-11-08 rosters. Results are daily-close marked and include actual-notional costs at each rebalance and final liquidation. The 2026 Dow period begins at the first eligible rebalance on the inherited five-session schedule after 2026-01-02.

The frozen overlay was partly in cash at each of these test rebalance dates: Dow test 1: 64.0% mean invested, 100% of rebalances with some cash; Dow test 2: 67.4% mean invested, 100% of rebalances with some cash; Dow test 3: 65.0% mean invested, 100% of rebalances with some cash; Cross-asset test: 70.8% mean invested, 100% of rebalances with some cash.

No test period is used to choose or alter the overlay. Four candidates were screened, so the apparent IS winner is subject to selection bias. The test 2 bootstrap p-value of 0.034 is evidence of negative active returns in that window, not an overlay benefit. The DSR is a rough multiple-testing correction and does not account for dependence across variants or the earlier ~70 trials individually.

## Refinement and report paragraph

This overlay keeps the broad equal-weight basket and changes only its market exposure. That is economically simpler than trying to forecast which of 30 names will win. Momentum gates leave part of the portfolio in zero-return cash, while volatility targeting reduces all holdings together when recent basket risk is high. The test should be judged against EW30 on Sharpe, active risk, and drawdown after turnover costs; if the frozen choice does not improve these consistently, the project conclusion should remain that the data do not support a reliable timing edge and EW30 is the appropriate baseline.

Figures for the chosen variant are in `outputs/dow_test_1_equity.png`, `outputs/dow_test_2_equity.png`, `outputs/dow_test_3_equity.png`, and `outputs/cross-asset_test_equity.png`. `outputs/period_metrics.csv` contains all candidates and periods; `outputs/overlay_diagnostics.csv` reports exposure, out-of-market frequency, and turnover for the frozen choice.

## Literature

- Faber, M. T. (2007), “A Quantitative Approach to Tactical Asset Allocation,” *Journal of Wealth Management*, 9(4), 69–79 (10-month moving-average timing rule).
- Moskowitz, T. J., Ooi, Y. H., and Pedersen, L. H. (2012), “Time Series Momentum,” *Journal of Financial Economics*, 104(2), 228–250.
- Moreira, A. and Muir, T. (2017), “Volatility-Managed Portfolios,” *Journal of Finance*, 72(4), 1611–1644.

## Reproduction

Run from `A2/pivot_research/r2_overlay` with Python 3 and the installed numpy, scipy, and matplotlib packages:
```powershell
py -3 overlay_research.py
```
The script sets the selection rule in `outputs/selection_rule.txt` before simulations, runs all four variants once per applicable segment, and writes the report tables, CSV diagnostics, and charts. The official copied pricing engine is `dow/code/pivot_backtest.py` or `xasset/code/pivot_backtest.py`; source engine folders were not edited.
