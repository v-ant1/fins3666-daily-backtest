# R9 J2 development variants

## Scope and selection

This is an exploratory development-period comparison of the 12 candidates logged before the run in `specs/r9_variant_log.md`. The fixed J1 score was retained. The replay used the coordinator-provided `r9/data/J2_DEV_FROM_20201127.npz` panel (SHA-256 `58f82f61d0947e5174cf7c47cc319cde5c59942b1b59c607159e7eeae98f6153`), the J1 score bundle, R6 costs of 0.05% per dollar traded, and PIT EW30. No sealed holdout or pre-2020-11-27 data was accessed. All variants and EW30 start at the same first formation where every logged variant can form its target: 2021-03-04.

J1 contributes 3 prior R6 trials; the 12 logged R9 candidates give a full DSR trial count of 15. Bootstrap p-values use 10-session circular blocks, 5,000 draws and seed 20261111. Cost/gross edge is total strategy trading costs divided by gross cumulative strategy-minus-EW30 return; it is undefined when gross edge is non-positive. Active share is the formation-date average of half the absolute weight difference from same-date PIT EW30. DSR follows the R6 helper formula on daily strategy net returns and trial_count=15; values underflow to zero at machine precision.

| Variant | Net excess return | Net Sharpe (strategy / EW30; difference) | Mean / max turnover | Cost / gross edge | Active share | Bootstrap p | DSR (15 trials) | Rule-5 eligible |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| R9-V0 (J1) | +5.15% | 0.8360 / 0.8804 (−0.0444) | 50.00% / 50.00% | 53.18% | 55.86% | 0.3913 | 0.0000 | No |
| R9-V1 (2% no-trade band) | −89.59% | 0.4210 / 0.8804 (−0.4594) | 0.35% / 100.00% | n/a | 50.00% | 0.9902 | 0.0000 | No |
| R9-V2 (rank-8 hold buffer) | −17.68% | 0.6484 / 0.8804 (−0.2320) | 103.84% / 200.00% | 236.30% | 83.33% | 0.6247 | 0.0000 | No |
| R9-V3 (2-observation smoothing) | +32.60% | 0.8871 / 0.8804 (+0.0067) | 98.46% / 200.00% | 34.46% | 83.33% | 0.2146 | 0.0000 | Yes |
| R9-V4 (3-observation smoothing) | +12.05% | 0.7941 / 0.8804 (−0.0863) | 82.40% / 200.00% | 46.05% | 83.33% | 0.3333 | 0.0000 | Yes |
| R9-V5 (4-observation smoothing) | +40.12% | 0.9239 / 0.8804 (+0.0435) | 69.66% / 200.00% | 22.49% | 83.33% | 0.1884 | 0.0000 | Yes |
| R9-V6 (biweekly) | −24.74% | 0.6063 / 0.8804 (−0.2741) | 139.42% / 200.00% | n/a | 83.33% | 0.6727 | 0.0000 | No |
| R9-V7 (8 names) | −25.66% | 0.6504 / 0.8804 (−0.2300) | 103.06% / 176.75% | n/a | 73.33% | 0.7978 | 0.0000 | No |
| R9-V8 (10 names) | −18.71% | 0.7276 / 0.8804 (−0.1528) | 78.55% / 141.81% | 1,508.48% | 66.67% | 0.7694 | 0.0000 | No |
| R9-V9 (inverse volatility) | −45.86% | 0.4788 / 0.8804 (−0.4016) | 141.44% / 200.00% | n/a | 83.33% | 0.8798 | 0.0000 | No |
| R9-V10 (50% partial rebalance) | −3.99% | 0.7706 / 0.8804 (−0.1098) | 69.15% / 98.68% | 95.23% | 60.45% | 0.5119 | 0.0000 | No |
| R9-V11 (75% partial rebalance) | −22.84% | 0.6319 / 0.8804 (−0.2485) | 103.00% / 149.94% | 679.13% | 69.02% | 0.7061 | 0.0000 | No |

Selection was mechanical under the precommitted rule: keep variants with active share at least 50% and cost/gross edge below 50%, then choose the highest strategy net Sharpe, breaking ties by lower mean turnover. R9-V3, R9-V4 and R9-V5 qualify; R9-V5 wins with net Sharpe 0.9239 and mean turnover 69.66%. Its bootstrap p-value is 0.1884 and its DSR is 0.0000 at trial count 15, so this exploratory development selection is not a confirmatory result. J2 is frozen in `specs/r9_prereg/J2.md` and awaits user approval before any holdout action.

## Reproducibility

Runner: `r9/j2_variants.py`. Saved machine-readable output: `r9/R9_VARIANTS.json`. The JSON includes input hashes, per-variant results and the trial count. The independent replay follows the daily marking and next-open execution structure in `report_drafts/repro/j1_portfolio_replay.py`, with each logged R9 construction rule applied explicitly.
