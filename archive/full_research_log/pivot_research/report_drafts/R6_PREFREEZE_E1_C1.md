# R6 pre-freeze hostile review: E1 and C1

Scope: design, point-in-time timing, prebuilt input QA, and synthetic/input-only documentation only. No forward returns, ICs, portfolios, or holdout data were loaded or computed for this review. The reviewed drafts remain unfrozen.

## Verdicts

| Draft | Verdict | Reason |
|---|---|---|
| E1 | **FIX-THEN-READY** | The signal and inference are mostly specified, and the cost hurdle is arithmetically correct, but the current E1 input build fails the registered 250-name/date gate, its SEC classification availability rule is internally inconsistent, and its stale-signal equivalence placebo is not a valid zero-effect null for a persistence hypothesis. |
| C1 | **FIX-THEN-READY** | Its design is detailed and is materially different from E1, but the registered SIC4/OHLCV inputs do not exist in the inspected C1 artifacts, the displayed power analysis uses daily dates instead of weekly formation dates and is not cluster-adjusted as required, its future-signal placebo overlaps the outcome window, and its SEC classification timing needs the same clarification. |

Neither draft is ready to freeze as written. These are repairable design/input defects, not outcome-based judgments.

## E1 review

### Timing and computability

The 21-session CLV formula, dollar-volume weighting, leave-one-out SIC2 peer mean, month-end formation rule, rank IC, Newey–West lag 20, and long-only portfolio rule are all specified well enough to implement. The input-only `r6_E1/INPUT_QA.md` reports 72 scheduled month ends, but the last is 2026-10-30, the end of available development prices; a 21-session forward window cannot be observed from that date. Before outcomes, publish the formation/eligibility mask that removes dates lacking the full forward window using only the development price calendar.

The SIC availability wording conflicts: use the latest 10-K “accepted on or before t,” but also says a revised class is usable only on the next trading session after acceptance. Make the actual rule `sic_usable_from <= formation_date`, where `sic_usable_from` is the next trading session after acceptance; do not use a filing accepted on formation day at that formation close. Apply this exact rule to both current and historical classifications, and document the acceptance timestamp/date convention.

### Input gate and consistency

The current bundle fails the preregistered input gate. `r6_E1/INPUT_QA.md` says there are only **21** eligible S&P peer scores per monthly formation (minimum 21), and the `250-name / 80%-of-dates` gate is false. It also reports median dated-SIC coverage of **41** in its S&P summary while its quarterly table shows roughly 446–500; those summaries conflict and must be reconciled from the actual membership, pressure, and peer masks. The currently reported 51 unresolved PIT price histories and sparse SIC inputs remain material coverage gaps. Rebuild the bundle after repairing the SIC/peer-eligibility pipeline; preserve all missing-name disclosures and rerun the published input-only thresholds. Do not freeze if the 250-name/date gate still fails.

### Placebos, hurdle, turnover, multiplicity

The group-size-preserving SIC2 label shuffle is a usable test of whether the observed industry assignment matters beyond date-level group sizes, provided the eligible-member mask and group sizes are frozen before outcomes and the specified 500 date-wise shuffles are used. The 21-session **past** signal placebo is not a valid equivalence-to-zero test of a persistence hypothesis: a real persistent pressure process can leave the older score predictive. Replace its inferential requirement with a predeclared contrast of current versus stale signal (or a different null that is genuinely expected to be zero); do not interpret failure to reject a stale effect as a null or use it to select another signal.

The stated cost hurdle **0.0011547005 is correct under the helper’s stated assumptions**: total traded notional/NAV = 0.20, cost = 0.0005 per dollar of that total notional (buys plus sells counted once), assumed monthly cross-sectional return SD = 0.06, and top fraction = 5/30. The helper uses `cost × turnover / [dispersion × sqrt(12) × (0.5 − top_fraction/2)]`. This is an assumed linear rank-to-top-quantile return mapping, not an estimated alpha; the S&P mechanism IC does not establish the Dow portfolio’s realized hurdle or net success. Keep the net portfolio gates separate.

The 20% turnover cap is below the R6 50% cap. A full EW30-to-top-five target has 166.7% buys-plus-sells notional; the cap therefore permits only 12% of that target distance per rebalance, or about 10 percentage points of active share per rebalance from EW30. A stable target needs about five uncapped-direction rebalances to reach 50% active share; changing monthly targets can prevent that. The draft correctly makes average active share a hard pass gate and includes transition costs, but should publish the deterministic transition rule and report active-share feasibility as a portfolio gate, not assume the cap guarantees it. The portfolio’s gross-edge ≥4× costs requirement matches the 25%-of-gross cost branch.

E1 registers one strategy variant, within the ≤3 requested. Its four endpoint definitions are listed, but the current `specs/r4_trials.md` Holm manifest lists D5/D4/D6 endpoints and no E1/R6 endpoints. Before any outcomes, the coordinator must add E1 endpoints to the cumulative R6 family manifest and log E1-V1; state the actual cumulative unique-variant count for DSR. The draft’s instruction that the R6 family “starts empty” must be reconciled with the existing manifest instead of silently omitting already registered R6 endpoints.

## C1 review

### Timing and computability

The CLV, close×volume weighting, five-session signal window, leave-one-out peer average, weekly formation, controls, residualization, and next-five-session intraday outcome are precisely described. The final weekly formation must be limited to dates with five subsequent development sessions available; decide that eligibility from the calendar before outcomes.

As in E1, the classification rule must use the most recent classification whose next-session `usable_from` date is on or before formation, not a classification newly accepted on the formation date. The data schema explicitly confirms a second input blocker: the existing C1 component parquet has adjusted open/close and return components but **no high, low, or volume**, so it cannot build the registered CLV. Although C1 itself acknowledges this, its SIC4 links are also unavailable in the built files: `r6_C1/INPUT_QA.md` and its listed artifacts provide SIC2/SIC3 only, while the prereg points to `sp500_sic_membership_from_L4.csv` and `sp500_industry_links_from_L4.csv`; those names/contents do not supply the required SIC4 in the inspected bundle. Add matched development-only OHLCV and dated SIC4/CIK links, resolve ticker/issuer lineage, update the prereg’s filenames to the actual frozen-input filenames, then publish coverage and eligibility manifests. The existing 54-gap warning must be updated to the current 51 unresolved ticker histories without dropping the original gap disclosure; apply the 90% member-day and 250-name/80%-date gates to repaired/unrepaired data exactly as preregistered.

### Power and placebo validity

`r6_C1/POWER.md` is not the required power result for this design. Its S&P row uses **1,487 daily observations** and a daily rank-signal autocorrelation, while C1 forms every fifth session and has only about 300 planned weekly observations over this development span. It reports SIC2 clusters, not the required SIC4/date-block design, and explicitly says it does not reproduce a date-by-industry block simulation. Re-run the pre-outcome synthetic power analysis using the actual eligible weekly dates and SIC4 group sizes, fixed assumptions/seed/draw count, Monte Carlo error, and power at both 0.0183 and 0.026; the S&P gate is ≥80% at 0.0183. Current 88.5% power cannot be cited as passing that gate.

The shuffled SIC4 labels placebo is a reasonable fixed null if each date’s eligible mask and exact group-size multiset are frozen. The registered `PeerIP[t+5]` time-shift placebo is invalid as an equivalence-to-zero null as currently defined: PeerIP at `t+5` is based on CLV through `t+5`, while the outcome is intraday returns over `t+1` through `t+5`. Its signal window therefore overlaps the outcome window and can mechanically share the same price movement. Change the fixed shift/window so its CLV observations do not overlap any outcome session, then freeze the null and equivalence margin before outcomes; otherwise drop the equivalence claim and redesign the placebo. Do not retain the current overlapping series as a pass/fail negative control.

### Hurdle, turnover, and multiplicity

The C1 cost threshold **0.0043301270 is correct under the helper’s stated assumptions**: total buys-plus-sells turnover 0.50, 0.05% cost per dollar of total traded notional, assumed weekly cross-sectional SD 0.04, and top fraction 5/30. It is an approximate planning hurdle using a linear rank-percentile mapping. The primary is a residualized partial rank correlation, so the rank-to-top-five mapping is less direct than for a raw Spearman IC; retain the hurdle as a screening floor and let the registered actual net Dow portfolio gate decide success.

At a 50% total-notional cap, moving from EW30 toward a fixed top-five target permits a 30% pro-rata step per rebalance (the full target move is 166.7% total notional), adding about 25 percentage points of active share from EW30 per rebalance. Thus the turnover cap itself is feasible and below the 50% limit, but the ≥50% average-active-share condition is not guaranteed if weekly targets rotate. The prereg’s explicit failure rule for insufficient active share is appropriate; retain the first transition and its costs.

C1 contains one variant, within the ≤3 limit, and enumerates four endpoints. The coordinator must add these to the **cumulative R6** Holm manifest before outcomes; the existing trial log does not yet show C1/E1 endpoint additions or their strategy rows. Keep placebo and bootstrap draws out of the unique strategy count, and report the exact DSR count at execution.

## Are C1 and E1 genuinely different?

**Yes, as registered tests they are distinguishable, though they share a CLV peer-pressure input family.** E1 is monthly SIC2 peer pressure predicting next-21-session total return with an ordinary date-wise Spearman IC and a top-five monthly Dow implementation. C1 is weekly SIC4 peer pressure, residualized against own/peer intraday and overnight return controls, predicting only next-week intraday return via a partial rank IC. That changes industry granularity, horizon, outcome component, and incremental-information question; it is more than a renamed parameter variant. The distinction only survives if C1 uses actual high/low/volume CLV and SIC4 data—substituting open-to-close returns for CLV would collapse it into the anchor return-continuation study and violate its stated design.

## Conditions to pass before either freeze

1. Fix each filing-availability rule as next-session usable SIC, and freeze a correct date/member/forward-window mask without inspecting outcomes.
2. Reconcile E1’s conflicting SIC coverage summaries and rebuild it until the 250-name/80%-date gate passes; otherwise stop E1.
3. Supply C1 matched OHLCV plus dated SIC4 links and valid lineage; rebuild the 90% coverage and 250-name/80%-date manifests, or stop C1.
4. Replace E1’s stale-signal zero-equivalence test with a valid registered contrast/null; replace C1’s overlapping future-signal placebo window with a non-overlapping, predeclared placebo.
5. Rerun C1 power for weekly dates with date-and-industry blocks and demonstrate ≥80% at IC 0.0183; do not rely on the daily SIC2 sensitivity table.
6. Add all four endpoints for each surviving candidate to the complete cumulative R6 Holm manifest before any outcome, and log no more than the single V1 strategy for each; report the unique count for DSR.
7. Preserve the stated turnover, costs, active-share, and net-return gates. The break-even hurdle arithmetic is correct but assumption-based and does not replace portfolio validation.

No outcome-based conclusion is made here, and neither candidate is authorized to run until the listed gates are closed and the coordinator freezes the preregistration.
