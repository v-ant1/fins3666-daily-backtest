# R7 Emergency Research Workflow

**Date:** 11 November 2026  
**Hard deadline:** 11 November 2026, 11:59 pm AEDT (Sydney)  
**Status:** Proposed prospective revision to R6

## 1. Immediate decision

Stop the current Dow 30 idea-generation loop.

R6 has tested seven frozen strategies and found zero passing strategies. Preserve those results, the 21-test Holm family, all decision logs and all frozen hashes. Do not rename failed strategies or rerun them as new discoveries.

R7 may change the trading universe, but must be clearly separated from R6. Retain the existing statistical thresholds, transaction-cost assumptions and trial accounting. Any changed benchmark or holdout must be declared before testing.

## 2. Revised research objective

Find up to 2–3 genuinely qualifying strategies consistent with the buying-pressure thesis, if the evidence supports them.

A strategy must still satisfy the original literature, pre-registration, signal, placebo, portfolio and holdout standards. The objective does not justify weakening these requirements.

Keep three questions separate when judging any candidate: (A) is there genuine return predictability, (B) can it be turned into a net-profitable, executable strategy, and (C) does it pass the R6/R7 qualification rules. A failure at C is not evidence of no edge at A, and every rejection must state which question it failed.

If no strategy passes by the deadline, submit the strongest reproducible findings and a clear negative-result conclusion. Do not label a promising but failed candidate as validated.

## 3. First priority: audit the data actually used

L1 and L4 must produce a single `R7_DATA_[MANIFEST.md](http://MANIFEST.md)` before further experiments.

For every dataset and every previously executed strategy, report:

- Exact input file paths, source and date range
- Number of rows, stocks and trading dates
- Missing observations and coverage by year
- Whether data is adjusted for splits, dividends and delistings
- Whether universe membership is point-in-time
- When each signal became publicly available
- Which strategy runs actually consumed the dataset

Separate data into **downloaded**, **cleaned**, **used in a frozen test**, and **not yet used**.

Do not initiate the proposed 0.6 TB trade-data pull or any other multi-hour download today.

## 4. Universe decision

**Preferred candidate:** S&amp;P 500 historical constituents, with daily data and a matching equal-weight S&amp;P 500 benchmark.

The larger universe must be used for portfolio construction, not merely for estimating signals.

Before approving the pivot, verify:

1. Historical stock membership and delisting treatment are sufficiently reliable.
2. Data coverage supports the proposed signal and trading dates.
3. The portfolio can be formed using information available at the decision time.
4. A genuinely sealed, comparable historical holdout is available.
5. A fresh power simulation shows a plausible route to passing the portfolio test.

If item 4 fails only because no sealed historical S&amp;P holdout exists, record whether a credible substitute (e.g. an untouched pre-sample period that can be built from staged data) is feasible, rather than treating the route as permanently closed.

If these conditions fail, do not proceed with an invalid S&amp;P 500 backtest. Document the obstacle and retain R6 as the defensible result.

## 5. Power gate before idea generation

L2 must rerun the criterion-4 simulations for the proposed universe and benchmark.

Test a small set of practical portfolio shapes, prioritizing long-only, diversified, low-turnover constructions. Retain 0.05% transaction costs per side and the existing turnover restriction.

Use effect sizes supported by the literature, not effect sizes chosen to make a strategy pass.

**Go/no-go rule:** If the simulated effect needed for a reasonable probability of success remains substantially above credible published effects, stop searching that configuration immediately.

No full idea screen should start until this gate passes.

**Exception: diagnose the near-misses before discarding them.** J1 passed the signal and placebo tests and earned about +14.9% gross over EW30, but weekly trading cost about 10.4%. That is an implementation/cost failure, not a signal failure. Before abandoning the pathway, one worker should produce a short gross-vs-net and turnover attribution and propose at most two prospectively specified, economically motivated lower-turnover designs (e.g. no-trade buffer, slower rebalance). These are new registered trials with full trial accounting, never a rescue of frozen J1. D1 (t = 1.91) should get the same short diagnosis of whether the shortfall is effect size or sample/estimation.

## 6. Idea selection

L3 maintains a searchable index of all approximately 66 previously screened idea families and seven executed strategies.

For each new direction:

1. Conduct a maximum five-minute duplicate, data and power check.
2. Reject immediately if it fails one of these, and log which gate rejected it (duplicate, data, power, universe or literature) so premature rejections can be audited later. Treat the literature check as a discovery-stage filter, not as proof the idea has no edge.
3. For survivors, obtain two verified papers and a mechanism relevant to the actual trading universe.
4. Have a second worker red-team the design.
5. Draft and freeze the pre-registration before any performance result is viewed.

Prioritize at most two genuinely distinct ideas today. Do not launch another broad sequence of dozens of screens.

Each idea retains the original maximum of three pre-registered variants. Maintain cumulative trial counts and disclose the earlier search history.

## 7. Execution and validation

Before any authorized run, the coordinator must verify:

- All referenced paths exist and output paths are unique.
- No sealed holdout dates can be read.
- The pre-registration hash matches.
- The input manifest and timestamps are valid.
- The real statistical helpers pass integration tests.
- The placebo hypothesis and interpretation of its p-value are explicit.
- The Holm family and deflated-Sharpe trial count are correct.

Run the signal test, placebo test and portfolio test in their prescribed order. Stop on failure.

No sign flips, threshold changes, alternative datasets or post-result rescue variants are permitted.

Open a suitable sealed holdout only for a candidate that has passed every preceding criterion.

## 8. Worker orchestration

**Claude, coordinator:** Controls the research queue, approves protocol changes, freezes specifications, authorizes executions and writes the final report.

**L1:** Data inventory, quality and point-in-time audit.

**L2:** Universe comparison, power simulations and portfolio feasibility.

**L3:** Literature, duplicate detection, idea screens and independent red-teaming.

**L4:** Runner integration tests, data provenance and execution readiness.

Each worker receives one bounded task with a unique output path and a required completion artifact.

The coordinator checks task acknowledgments shortly after dispatch, distinguishes progress reports from completed artifacts, and reassigns stalled work. No worker should spend hours repeating a screen already rejected.

## 9. Continuous review loop

Every 30 minutes, or after any completed experiment, the coordinator records:

- Time remaining until deadline
- Active and stalled workers
- Data and power-gate status
- New information since the previous review
- Frozen and executed trial counts
- Whether to continue, pivot or stop

Changes to the workflow are versioned and apply prospectively. Never alter a frozen strategy in response to its observed performance.

**Stop starting new experiments at least 90 minutes before the deadline.** Use the remaining time for reproducibility checks, interpretation and report preparation.

## 10. Required final output

By 11:59 pm AEDT on 11 November 2026, deliver:

- `R7_[FINAL.md](http://FINAL.md)`, with an accurate pass/fail table
- `R7_DATA_[MANIFEST.md](http://MANIFEST.md)`, distinguishing available data from data actually tested
- Reproducible scripts and frozen specifications
- A comparison of Dow 30 and any approved alternative universe
- An explanation of why candidates passed or failed
- A clear account of all protocol changes, tests and limitations

The final report must distinguish validated strategies, preliminary evidence and failed hypotheses. A finding of no qualifying strategy is acceptable; an unsupported claim of success is not.
