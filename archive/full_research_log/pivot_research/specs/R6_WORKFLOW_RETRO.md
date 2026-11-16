# R6 workflow retrospective

## Where the time went

The largest recurring cost was idea generation after the feasibility screen had already become binding. Rounds repeatedly stopped at the gate because they overlapped tested work, lacked a usable historical pressure measure, had too few independent events or network clusters, or had too little power at a plausible effect. The decision log records 18 candidate families in rounds S–X failing before a registered test. The process kept reopening the search despite the earlier conclusion that free-data effects were unlikely to clear criterion 4.

The second cost was execution recovery. Runner attempts stopped before results could be saved because governance checks and bookkeeping were inconsistent: Holm manifest hashing and null-slot conventions, trial-count assumptions, helper return keys, and the default preregistration directory disagreed with the actual R6 setup. Tests mocked helpers, so they missed a production-path key mismatch. Separate from those crash loops, the record notes a brief that pointed at sealed pre-2020 data and an idea brief that reused `r6_ideas/F.md`, overwriting an earlier file. These are preventable contract and path errors.

## Why ideas kept failing

The screen initially emphasized whether a mechanism was plausible and whether its effect could be detected. The binding requirement was stronger: criterion 4 needed a tradable Dow portfolio that beat EW30 after costs, with higher Sharpe and family-adjusted bootstrap evidence. The feasibility audit estimates a long-only top-five strategy would need rank IC around 0.085; the documented large-cap effects were generally around 0.01–0.03. Better screening can avoid spending variants on implausible ideas, but it cannot make weak effects large enough.

Data quality narrowed the feasible set further. Public daily OHLCV proxies such as CLV, volume shocks, short-sale volume, and calendar effects do not directly observe buyer-initiated trades. Some candidate measures were sparse or lacked point-in-time historical coverage; coarse peer or sector groupings also reduced effective breadth. This creates a two-part failure: the available data often measured pressure indirectly or incompletely, while even the better documented effects sat below the portfolio hurdle. The next research step should prioritize verified signed flow and its coverage before proposing another proxy.

## Changes ranked by impact

1. **Build one shared runner template, with governance first.** Add `r4_harness/runner_template.py` as the only supported runner skeleton. Its pre-analysis sequence should validate frozen preregistration/hash, input manifest and date bounds, endpoint-family digest and reserved slots, trial count, output paths, and one-shot lock before loading outcome arrays. It should call the existing helpers in `phase3.py` and `runner_guard.py`, expose explicit project paths as arguments, write a complete result bundle atomically before appending the trial log, and record errors without printing partial statistics. Add `r4_harness/tests/test_runner_template_e2e.py` using temporary fixtures and the real Holm, Newey–West, bootstrap, DSR, and result-writer helpers; assert the complete standard result file and trial append. Keep existing runners untouched; migrate only future directions.

2. **Use one idea-screen template that kills weak candidates in one pass.** Add `specs/IDEA_SCREEN_TEMPLATE.md` and require every idea brief to answer, in order: overlap with prior families; exact pressure measure and dated data source; point-in-time coverage and event/cluster counts; effective breadth and power at a sourced plausible effect; criterion-4 feasibility after costs and Holm; and holdout availability. Any failed item ends the screen with a named reason; no portfolio runner or variant is commissioned. Include required citations with working DOI/URL and prohibit outcome-data inspection during screening. Update the Task-spec brief contract in `ORCHESTRATION.md` (SSI standing-rules section) to require this screen, forward-slash exact output paths, and “do not overwrite existing files.”

3. **Make direct signed flow the next data question.** Add `specs/SIGNED_FLOW_DATA_AUDIT.md` before any new signal brief. It should audit development-window-only availability of trades and quotes, exchange coverage (SIP vs venue-limited), trade signing method, timestamps, symbol mapping/corporate actions, survivorship and missingness, costs, and whether the same source supports the required holdout period. The R6 data brief should explicitly stop if signed flow cannot be validated; do not relabel daily candle proxies as order flow.

4. **Separate feasibility research from signal testing.** Add a short “criterion-4 first” checklist to `specs/r4_goal.md` or the new idea-screen template. Require an independently sourced effect-size range and a portfolio-level feasibility argument before registration, while preserving the fixed criteria. If the evidence cannot plausibly reach the hurdle with available breadth, mark the family infeasible rather than using a full test to learn what the screen could establish.

5. **Add brief preflight and immutable artifact naming.** Require exact target paths to be checked for existence before workers write, prohibit reusing prior round filenames, and check date bounds against the sealed-holdout rule in every data brief. This directly addresses the overwritten round file and the unsafe date instruction; route any ambiguity through coordinator review before a pull starts.

This retrospective reports workflow and feasibility lessons only. It does not add or reproduce strategy outcomes, access holdout data, or change existing runners.

## Source record

`specs/r6_decisions.md`; `R6_FINAL.md`; `ORCHESTRATION.md`; `r4_harness/README.md`, `runner_guard.py`, `phase3.py`, `r4_harness/r6/k1_runner.py`, `g1_runner.py`, and their synthetic tests.
