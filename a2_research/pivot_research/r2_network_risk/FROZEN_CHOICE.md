# Frozen choice (recorded before running test windows)

The pre-written rule in `SELECTION_PROTOCOL.md` selects `inv_heat`: inverse heat-kernel connectivity, with weights proportional to the reciprocal of each name's total off-diagonal row sum of exp(-L), calculated from the 63-session symmetric top-five positive correlation graph. It is the highest average selection-period Sharpe among portfolios that satisfy the 50% turnover ceiling.

| Portfolio | Dow IS Sharpe | ETF IS Sharpe | Average | Mean turnover Dow / ETF |
|---|---:|---:|---:|---:|
| EW30 | 0.47 | 0.09 | 0.28 | 4.7% / 3.1% |
| ivol63 | 0.51 | -0.63 | -0.06 | 8.9% / 9.1% |
| low_degree | 0.51 | 0.32 | 0.42 | 15.2% / 12.5% |
| low_eigen | 0.40 | 0.42 | 0.41 | 33.5% / 41.7% |
| **inv_heat** | **0.48** | **0.52** | **0.50** | **5.6% / 39.2%** |
| hrp | 0.54 | -1.28 | -0.37 | 28.0% / 25.4% |
| degree_ivol | 0.54 | -0.61 | -0.04 | 16.8% / 16.1% |
| heat_ivol | 0.52 | 0.06 | 0.29 | 9.2% / 39.9% |

The selection output was limited to 2020-11-27..2022-12-30 in both universes. The choice and weights are now frozen. Test windows are to be reported once with no changes.
