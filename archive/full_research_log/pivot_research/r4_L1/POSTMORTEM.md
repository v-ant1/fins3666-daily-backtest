# Round 4 L1: pressure plus heat post-mortem

## Finding

On the Dow 30 development sample, the pressure blend has little reliable predictive power and the heat term adds no broad continuation effect. The unbuffered heat50 portfolio beats EW30 before costs, but its high weekly turnover gives back that edge: it finishes below EW30 after 0.05% per-side costs and has a lower Sharpe. The central failure is a weak, partly offsetting pressure signal, smoothed across a co-movement graph that does not show useful short-horizon return propagation.

## Method and sample

This analysis uses 30-name point-in-time Dow rosters for 2020-11-27 through 2026-10-30, applying the 2020-08-31 roster until the 2024-02 AMZN/WBA swap and the 2024-02 roster until the 2024-11 NVDA/SHW changes. The signal calculations have the required 63-session return warm-up; daily rows before 2020-06-01 are rejected before price fields are parsed. There are 1,488 signal dates; forward horizons have 1,468–1,487 usable daily IC observations. The script reconstructs the original five-day close-location value (CLV), signed volume and intraday-minus-overnight measures, their equal-weight percentile-rank pressure blend, and the positive top-five symmetrized 63-day correlation graph with `exp(-L)` heat. All forward-return calculations are strictly after the signal date.

For horizon *h*, close-to-close is close(T) to close(T+h); next-open-to-close is open(T+1) to close(T+h). Newey–West uses lag *h−1* for the daily IC series. A positive rank IC means continuation; a negative value means reversal. The separate market-demeaned calculation subtracts that date's same cross-sectional mean return from every stock. Because that subtracts one common scalar, it cannot change cross-sectional ranks: every mean IC and t-stat is exactly unchanged. This is a property of rank IC, not evidence that market exposure is irrelevant.

## Predictive power by horizon

Cells show mean Spearman IC / Newey–West t-stat. Full precision and date counts are in [`rank_correlations.csv`](rank_correlations.csv). Raw and market-demeaned results are identical for the reason above.

### Close-to-close

| Signal | 1 day | 2 days | 5 days | 10 days | 20 days |
|---|---:|---:|---:|---:|---:|
| Pressure blend | +0.0049 / 0.77 | +0.0056 / 0.76 | +0.0034 / 0.34 | +0.0149 / 1.29 | +0.0040 / 0.37 |
| CLV | +0.0058 / 0.95 | +0.0086 / 1.23 | +0.0111 / 1.16 | +0.0215 / 1.90 | +0.0072 / 0.65 |
| Signed volume | −0.0019 / −0.29 | −0.0017 / −0.23 | −0.0058 / −0.61 | −0.0026 / −0.24 | −0.0081 / −0.73 |
| Intraday minus overnight | +0.0070 / 1.10 | +0.0070 / 0.97 | +0.0031 / 0.31 | +0.0177 / 1.47 | +0.0068 / 0.62 |
| Heat | −0.0065 / −0.81 | −0.0032 / −0.34 | −0.0015 / −0.12 | +0.0116 / 0.79 | +0.0115 / 0.78 |
| Neighbour average | −0.0026 / −0.35 | −0.0021 / −0.24 | −0.0034 / −0.29 | +0.0072 / 0.52 | +0.0034 / 0.24 |

### Next-open-to-close

| Signal | 1 day | 2 days | 5 days | 10 days | 20 days |
|---|---:|---:|---:|---:|---:|
| Pressure blend | +0.0114 / 1.80 | +0.0108 / 1.49 | +0.0042 / 0.43 | +0.0150 / 1.30 | +0.0043 / 0.40 |
| CLV | +0.0142 / 2.34 | +0.0142 / 2.05 | +0.0132 / 1.40 | +0.0223 / 1.98 | +0.0078 / 0.70 |
| Signed volume | −0.0021 / −0.33 | −0.0010 / −0.14 | −0.0082 / −0.87 | −0.0039 / −0.36 | −0.0085 / −0.76 |
| Intraday minus overnight | +0.0145 / 2.30 | +0.0130 / 1.86 | +0.0045 / 0.46 | +0.0189 / 1.58 | +0.0074 / 0.67 |
| Heat | −0.0089 / −1.19 | −0.0046 / −0.52 | −0.0058 / −0.48 | +0.0111 / 0.76 | +0.0107 / 0.72 |
| Neighbour average | −0.0035 / −0.49 | −0.0033 / −0.39 | −0.0069 / −0.61 | +0.0070 / 0.51 | +0.0025 / 0.18 |

The clearest positive evidence is limited to the one-day next-open-to-close CLV and intraday-minus-overnight components (t=2.34 and 2.30). CLV remains just above t=2 at two days, then falls below it by five days. That continuation does not survive at t≥2 in the combined pressure signal at any tested horizon. Signed volume is consistently negative, a reversal component that dilutes the positive parts. Heat and the plain neighbour average are negative at one to five days, then weakly positive at 10–20 days without significance. This is not evidence of durable pressure persistence or spread.

![Cross-sectional rank IC by horizon](ic_by_horizon.png)

## Component anatomy

| Pair of component rank scores | Correlation |
|---|---:|
| CLV – signed volume | +0.496 |
| CLV – intraday minus overnight | +0.599 |
| Signed volume – intraday minus overnight | +0.316 |

The pressure score gives each ranked component exactly one-third weight. With the three rank-score variances normalized equally, covariance accounting attributes approximately 36.0% of blend variance to CLV, 31.1% to signed volume and 32.9% to intraday-minus-overnight. The similar variance shares hide different predictive signs: the signed-volume piece generally reverses while the other two continue. The blend consequently has a smaller short-horizon edge than the best one-day component. See [`component_correlations.csv`](component_correlations.csv).

## What heat actually does

The heat operator is the graph filter `exp(-L)` applied to standardized pressure, with its diagonal removed and rows normalized. It downweights high-frequency graph modes, but it is a diffuse smoother rather than a directional propagation model: the graph is based on contemporaneous return co-movement, not lead-lag pressure transmission.

| Laplacian eigenvalue | Modes across graph dates | Share of filter trace | Mean `exp(-λ)` |
|---|---:|---:|---:|
| Approximately 0 to 0.25 | 1,503 | 24.1% | 0.998 |
| 0.25 to 0.5 | 777 | 8.4% | 0.674 |
| 0.5 to 1 | 2,512 | 18.7% | 0.463 |
| 1 to 2 | 8,292 | 30.1% | 0.225 |
| 2 to 4 | 17,393 | 17.3% | 0.062 |
| 4 and above | 14,163 | 1.4% | 0.006 |

The mean filter-weighted Laplacian eigenvalue is 1.135, and the mean per-graph spectral effective rank is 13.00 of 30. About 24% of filter trace is in near-constant/low-frequency modes; about 49% lies in modes with eigenvalue at least 1. The table pools graph-date modes and filter trace fractions; slight rounding aside, the shares sum to 100%.

Heat is highly similar to the plain neighbour average (pooled Pearson correlation 0.828), which shows that most of the distinction from the pressure signal is graph averaging itself. Heat correlates only 0.206 with the same-date sector average of own-pressure ranks. A correlation with the cross-sectional market-wide mean rank is undefined because percentile-rank construction forces that mean to be 0.5 every date; this cannot be used as a meaningful comparison. Consecutive five-session graph snapshots have mean undirected edge Jaccard overlap 0.745 (median 0.752): the edges are moderately persistent, but they still change enough to shuffle which peers enter the smoothing step. Detailed observations are in [`graph_diagnostics.csv`](graph_diagnostics.csv) and [`edge_overlap.csv`](edge_overlap.csv).

![Heat filter spectral mass by Laplacian eigenvalue](heat_spectrum.png)

## Power and costs

There are 1,488 daily signal dates, but the overlapping five-day pressure IC series has a Newey–West standard error of 0.00977. A mean IC of about **0.0195** would be needed for |t|=2 under that realized standard error. The observed five-day pressure IC is **0.0034**, about 17% of that threshold; its t-statistic is 0.34.

Under the optimistic fundamental law, 30 independent names times 52 independent weekly forecasts gives annual breadth 1,560. An annual portfolio IR of 0.5 would then require IC of **0.0127** (`0.5 / √1,560`). The observed pressure IC is about 27% of that. This breadth assumption is generous: correlated Dow returns and overlapping holding periods reduce effective breadth, so the required IC in practice is higher.

The unbuffered top-five heat50 implementation was simulated with next-session-open fills every five sessions, equal weights, and the stated 0.05% per-side cost. Cumulative return and daily-mark Sharpe are:

| Portfolio | Gross return | Gross Sharpe | Net return | Net Sharpe | Mean total traded notional per rebalance | Mean net cost / NAV per rebalance |
|---|---:|---:|---:|---:|---:|---:|
| Heat50 top five | +133.2% | 0.85 | +83.3% | 0.64 | 161.2% | 0.0806% |
| EW30 | +102.6% | 0.92 | +101.7% | 0.92 | 2.4% | 0.0012% |

The gross active return is +30.5 percentage points over EW30, but after costs the strategy is −18.4 points behind; its Sharpe is already lower than EW30 before costs. At the observed turnover, the strategy's incremental cost over EW30 averages 0.0794% of NAV per rebalance. An empirical weekly calibration regressing gross active return on the same week's blend IC estimates that a mean IC of about **0.0061** would be needed to cover that incremental cost. The realized weekly blend IC averages −0.0030. This is an in-sample linear cost calibration, not a structural law; its point is the scale of the required edge, not a forecast.

### Break-even reconciliation

The **0.0127** figure above is the optimistic fundamental-law IC for annual IR 0.5 with breadth 30 × 52; it is not a weekly cost break-even. The **0.00605** empirical estimate in `power_cost_summary.csv` is `(incremental weekly cost − fitted intercept) / fitted slope`: incremental cost is 0.00079375 of NAV, the gross-active-return regression has slope 0.0347085 per unit weekly Spearman IC and a positive 0.00058367 intercept. That fitted intercept credits the strategy with an in-sample baseline return, so 0.00605 is a regression-based break-even, not a cost-only hurdle. For a cost-only calculation, average cross-sectional standard deviation of weekly next-open-to-close returns is 0.030075, incremental total-notional turnover versus EW30 is 1.58751 of NAV, and the 0.05% per-side charge therefore costs `0.0005 × 1.58751 = 0.00079375` per rebalance. Assuming the top 5 of 30 long-only portfolio's return scales linearly with standardized percentile rank, a one-unit Spearman IC maps to `0.030075 × √12 × (0.5 − 5/60) = 0.04339` active return; the resulting cost-only hurdle is `0.00079375 / 0.04339 = 0.0183`. This is the appropriate advance hurdle under those explicit turnover, dispersion and rank-to-return assumptions; `cost_analysis.csv` and `power_cost_summary.csv` record the hurdle and inputs. The two methods answer different questions, and neither should be presented as a universal IC threshold.

## Regime and sector checks

Five-day pressure IC changes sign across years: +0.015 in 2021, −0.022 in 2022, +0.033 in 2023, +0.015 in 2024, −0.009 in 2025 and −0.017 in 2026; none of those yearly pressure t-stats reaches 2. Heat is negative in 2021–22 and 2024–25, but positive in 2023 (+0.064, t=2.62) and 2026 (+0.026, t=0.82). The 2020 heat estimate is −0.199 with t=−3.64 but includes only 24 late-November/December dates, so it is a short partial-year sample and not stable regime evidence.

No broad sector's five-day pressure or heat IC has |t|≥2. The largest descriptive sector observations are heat IC +0.023 in Staples (t=0.82) and pressure IC +0.026 in Health (t=1.13); several sector-year buckets have small and changing constituents. There is no evidence that the full-sample rank correlation is reliably concentrated in one sector. The full splits are in [`subgroup_diagnostics.csv`](subgroup_diagnostics.csv).

## Ranked root causes

1. **The pressure blend combines components with conflicting signs.** Signed-volume IC is negative at every close-to-close horizon and has a negative 5-day next-open-to-close IC (−0.0082), while CLV and intraday-minus-overnight are positive. The blend's five-day close-to-close IC is only +0.0034 (t=0.34), despite a one-day CLV next-open-to-close IC of +0.0142 (t=2.34). The short-lived component signal is diluted before portfolio selection.
2. **Heat averages co-movement without measuring directional transmission.** Its five-day IC is −0.0015 (t=−0.12), and plain neighbours are also negative (−0.0034, t=−0.29). Heat is strongly correlated with that plain neighbour average (0.828), so the exponential graph filter mostly smooths noisy peer pressure; it does not establish that pressure leads neighbour returns.
3. **The edge is not stable over time or horizon.** Pressure changes sign across years, while heat's only notable positive year is 2023. The daily signal tests show weak/insignificant results at 1–20 days except two component-level one-day next-open-to-close observations and a just-significant two-day CLV result. The apparent effect is too fragile to support a fixed weekly top-five rule.
4. **Weekly concentration magnifies costs and idiosyncratic return risk.** The no-buffer portfolio trades total notional equal to 161.2% of NAV per rebalance, versus 2.4% for EW30. It earns +30.5 points of gross active return, yet loses 18.4 points versus EW30 after costs and has a lower net Sharpe (0.64 vs 0.92).
5. **The sample is underpowered for a small IC.** A five-day IC near 0.0195 is needed for t=2 under observed serial dependence, and even the optimistic IR=0.5 fundamental-law threshold (0.0127) is several times the observed IC. Testing only 30 correlated mega-cap names makes effective breadth smaller still.

## What a new direction must do differently (inputs to L2 and L3)

- Preserve the buying-pressure hypothesis but measure pressure with a more direct source, such as signed intraday order flow or order-flow imbalance, and check its sign and decay before any portfolio test.
- Define the network from a plausible transmission channel (common ownership, supplier/customer links, or another dated relation). Test whether a source asset's pressure predicts later neighbour returns; contemporaneous return correlation alone is not a propagation mechanism.
- Start with pre-specified event studies or cross-sectional lead-lag tests at short horizons and compare against shuffled or random-link placebos. Require the effect to survive Newey–West inference and regime splits before discussing portfolio returns.
- If a portfolio is warranted, size its concentration and rebalance rate around the measured edge. Under the stated top-five rank mapping and observed incremental turnover and dispersion, the cost-only weekly hurdle is about 0.0183; use lower-turnover execution or a materially stronger, independently supported signal.
- Keep failures visible and do not use sector/year pockets or generic factor tilts as a substitute for evidence of pressure persistence or network spread.

## Reproduction and outputs

From the project root run `python r4_L1/run_diagnostics.py`. See [`DIAGNOSTICS_LOG.md`](DIAGNOSTICS_LOG.md) for the full diagnostic inventory and data guard. Machine-readable tables, charts and code are all in `r4_L1/`.
