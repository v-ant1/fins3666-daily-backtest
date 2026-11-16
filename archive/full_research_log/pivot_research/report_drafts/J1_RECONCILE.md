# J1 portfolio return reconciliation

## Finding

The cause of the reported **+1.03% vs −2.66%** discrepancy is that the independent portfolio replay was not preserved as an auditable implementation/output. `report_drafts/REPRO_J1.md` records the −2.66% summary, but has no daily strategy or EW30 return series, portfolio code, or turnover/cost ledger. The named `report_drafts/repro/j1_reference.py` implements only the mechanism IC and SIC2 placebo; its CLI accepts synthetic self-tests only. Its companion `report_drafts/REPRO_J1_PLAN.md` explicitly excludes the Dow portfolio calculation. Therefore there is no independent daily series to compare, and the workspace evidence cannot identify whether the one-off replay differed on compounding, execution costs, or benchmark cohort.

For the **authorized frozen J1 run**, the supported number is **+1.0276019 percentage points** net cumulative excess (reported as +1.03%). `r6_J1/J1_RESULTS.json` contains 1,487 strategy and 1,487 EW30 daily net returns with matching return-date indices (127 through 1613). Compounding the saved strategy series gives **+96.2141599%**; compounding the saved EW30 series gives **+95.1865579%**; their difference is **+1.0276019 percentage points**, exactly matching the saved `net_excess_return`. The saved gross return series and summary also agree with this cumulative-difference convention.

The **−2.66%** figure is not supported by a saved return path and must be treated as an unreproducible replay figure, not as a second verified estimate of J1. This is an evidence-quality conclusion: the official saved series is internally consistent, but the missing independent portfolio implementation prevents a code-level diagnosis of the erroneous −2.66% calculation.

## Cross-checks and verdict

- The official strategy and EW30 net series have equal length and identical date indices; no calendar-alignment discrepancy appears in the saved output.
- Official net Sharpe is **0.823179** versus **0.902267** for EW30, and the official net-excess bootstrap p-value is **0.449110** (Holm-adjusted **1.000000**). J1 remains a **failure** under its frozen portfolio criteria regardless of which cumulative-excess figure is considered.
- No signal was rebuilt, no new variant was tested, and no holdout data were accessed. The review used the frozen J1 output and its associated report/code artifacts only.

## What would close the remaining audit gap

To attribute the −2.66% figure to a specific implementation error, preserve the independent portfolio runner and its daily strategy/EW30 returns, fill-date holdings, executed turnover, and cost arrays. Diff those records against the official `portfolio.net` and `portfolio.ew_net` arrays by date. The current independent mechanism helper cannot be rerun to produce those portfolio records.
