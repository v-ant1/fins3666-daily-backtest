# D1 — Signal-only power analysis

## Design

This is synthetic planning, not a prediction test. It uses the existing `r4_harness/power_sim.py`; the simulator accepts assumptions and generates date-level noise and a planted mean IC, and does not load project returns. The tested hypothesis is a positive mean daily rank IC. Horizon is fixed at five sessions, with Newey–West Bartlett lag 4, 5,000 simulations, and the development window 2020-11-27 through 2026-10-30: 1,488 NYSE sessions. The S&P wide-universe mechanism case uses 500 nominal names; the Dow portfolio case uses 30.

### SIC-cluster stress

To avoid treating every stock as independent, the IC-SD stress sets effective independent names to the **minimum** point-in-time count of distinct two-digit SIC groups in the active roster. The SIC membership inputs are metadata from `r6_C1/sp500_sic_membership.csv` and `r6_C1/dow_sic_membership.csv`; for the June 2026 Dow change, the group count replaces VZ's SIC2 with GOOGL's SEC SIC2. The minimum and median active group counts are 53/54 for S&P and 18/19 for Dow. Using the standard null-rank approximation with group count `G`, the supplied SD is `1/sqrt(G - 1)`, yielding 0.138675 for S&P and 0.242536 for Dow. This deliberately uses the least cluster breadth observed in the sample.

Temporal dependence is stressed using the larger of (i) the median individual-stock lag-1 autocorrelation of the FINRA short-volume ratio and (ii) the lag-1 autocorrelation of the cross-sectional mean ratio. These are measured **signal** autocorrelations, not return-IC autocorrelations: 0.853545 for S&P and 0.688463 for Dow. They are conservative dependence inputs, not calibrated estimates of future IC dependence. This choice materially reduces simulated power versus the harness's default low-autocorrelation examples.

## Results

| Universe | Sessions | Min/median SIC2 groups | IC SD stress | Signal ACF1 stress input | Effective N | 80% MDE | Power at IC 0.0183 | Power at IC 0.026 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S&P 500 mechanism | 1,488 | 53 / 54 | 0.138675 | 0.853545 | 376.7 | 0.02030 | 0.631 (MC SE 0.0068) | 0.825 (MC SE 0.0054) |
| Dow 30 portfolio-use case | 1,488 | 18 / 19 | 0.242536 | 0.688463 | 492.5 | 0.03106 | 0.412 (MC SE 0.0070) | 0.619 (MC SE 0.0069) |

The S&P case has about 63% simulated power at the lower 0.0183 hurdle and about 82% at 0.026. The Dow case has only about 41% and 62%, respectively; with this cluster stress its 80% MDE is about 0.031. Thus a wide-universe mechanism test could be adequately powered only toward the upper assumed IC range, while the Dow-sized case is underpowered across the stated range in this conservative simulation.

The simulator's effective N is date-level after the specified AR(1)/HAC design effect; it is not 1,488 times the number of names. The SIC group count changes the assumed cross-sectional IC standard deviation, while the signal ACF proxy changes the temporal design effect. Cross-SIC dependence, date-varying industry structure, roster measurement error, and missing FINRA rows are not fully modeled. These outputs are not evidence that the signal predicts returns, and do not justify proceeding to outcome testing on their own.

Exact assumptions, SIC-group date counts, and raw simulator outputs are in `power_inputs.csv`, `sp500_sic_cluster_counts.csv`, `dow_sic_cluster_counts.csv`, and `power_simulations.txt`. Reproduce with:

```powershell
python r6_D1/power_analysis.py
```

The script derives its autocorrelation inputs from `r6_data/finra_regsho/signal_statistics.csv`, derives cluster counts from SIC metadata only, and calls `r4_harness/power_sim.py`. It never reads prices, returns, or outcome data.
