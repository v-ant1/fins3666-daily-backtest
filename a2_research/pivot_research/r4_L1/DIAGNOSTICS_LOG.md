# Round 4 L1 diagnostics log

These are forensic analyses of the existing pressure plus heat method, not new trading variants. No trial-budget entries were consumed. All code and outputs are confined to `r4_L1/`.

| Diagnostic | Implementation | Output |
|---|---|---|
| Predictive rank IC | Daily cross-sectional Spearman IC for the equal-rank pressure blend, its three ingredients, heat, and plain neighbour average; 1/2/5/10/20-session close-to-close and next-open-to-close outcomes; Newey–West t-statistics with lag `horizon - 1`. | `rank_correlations.csv`, `ic_by_horizon.png` |
| Components | Pooled correlations of each component's cross-sectional ranks. The three ranked components enter the pressure blend with equal one-third weights. | `component_correlations.csv` |
| Graph filter | Rebuilt the original positive top-five, symmetrized correlation graph and `exp(-L)` filter on each 63-return window. Reported filter trace by Laplacian eigenvalue, filter effective rank, heat/neighbour and heat/sector-pressure similarity. | `graph_diagnostics.csv`, `heat_spectrum.png` |
| Graph stability | Jaccard overlap of undirected edges between consecutive five-session graph snapshots. | `edge_overlap.csv` |
| Power and cost | HAC standard error threshold for 5-day pressure IC; optimistic fundamental-law IC for annual IR 0.5; unbuffered weekly top-five heat50 portfolio simulated against EW30 with gross and 0.05% per-side costs; empirical weekly IC-to-active-return break-even calibration. | `power_cost_summary.csv`, `cost_analysis.csv` |
| Regime and sector | Five-day close-to-close ICs by calendar year and broad sector. Sectors are manually mapped from Dow constituents to broad GICS-style groups; sectors with fewer than four names are omitted. | `subgroup_diagnostics.csv` |

Run from the project root with `python r4_L1/run_diagnostics.py`. Dependencies: Python 3, NumPy, SciPy, and Matplotlib. The script reads only `repo/prices-daily*` and `repo/prices-daily-delisted` files, rejects rows before 2020-06-01 before parsing prices, and writes all generated artifacts under `r4_L1/`.
