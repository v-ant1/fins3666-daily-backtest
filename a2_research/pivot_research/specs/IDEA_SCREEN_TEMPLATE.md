# R6 Idea Screen

**Status:** SCREEN ONLY — no signal outcomes, no return calculations, and no variant is authorized by this document.

Use this screen before writing or freezing any preregistration. Fill every section in order. If a gate fails, state **STOP — FAIL** with the specific reason and do not continue to a portfolio runner or variant. Cite real sources with a working DOI or URL; distinguish documented results from your inference.

## Identity and immutable-path preflight

- Proposed short name and one-sentence mechanism:
- Exact new output path(s), using forward slashes:
- Confirm each exact target path does not already exist:
- Confirm these names have not been used by a prior round or another worker:
- Development date range and earliest permissible worker-path date: **2020-11-27**.
- Confirm no worker input or output path refers to data before 2020-11-27, a holdout folder, or an unapproved date range:
- If any path, date, or data meaning is ambiguous, stop and obtain coordinator review before any data pull.

## 1. Overlap with prior work

- Search `r6_ideas/*.md`, `R5_FINAL.md`, and the direction/decision registry. List the nearest tested or rejected ideas and explain the actual mechanism difference.
- Does this repeat a prior signal with renamed inputs, horizon, or universe? If yes, **STOP — FAIL**.
- Verdict: PASS / FAIL, with reason.

## 2. Exact pressure measure and dated data source

- Define the pressure variable precisely, including units, aggregation, sign, timestamp, and information available as of formation.
- Identify the source, URL/DOI, licensing/access limits, point-in-time mapping, and actual development-window date coverage.
- State the formation and prediction dates without using future information.
- Confirm this screen uses no forward returns, ICs, portfolio returns, or other signal outcomes.
- Verdict: PASS / FAIL, with reason.

## 3. Point-in-time coverage and independent breadth

- Give counts for usable dates, names, nonmissing signals, independent events, and independent SIC2/other clusters. State how each count was obtained using input-only coverage checks.
- Explain survivorship, symbol changes, reporting delays, missingness, and any selection caused by source availability.
- If evidence comes from a paper, verify its universe, dates, horizon, and sample size; do not assume it transfers to present-day mega-caps.
- Verdict: PASS / FAIL, with reason.

## 4. Effective breadth and power at a sourced plausible effect

- Cite a plausible effect-size range from independent research that matches this signal, horizon, and large-cap setting; give the source's actual sample and estimator.
- Estimate effective breadth after serial dependence and industry/event clustering. State the assumptions and use `r4_harness/power_sim.py` or an equivalent predeclared calculation.
- Report power at the cited plausible effect and the minimum effect needed for 80% power. Do not use an effect estimated from this project's outcomes.
- If the effect-size evidence or breadth cannot support a useful test, **STOP — FAIL**.
- Verdict: PASS / FAIL, with reason.

## 5. Criterion-4 portfolio feasibility first

Before proposing any full test, show that the hypothesized effect could plausibly support the fixed goal criterion: positive net excess return over EW30 after costs, Sharpe above EW30, and one-sided block-bootstrap evidence with Holm adjustment for the R6 family. Do not relax the goal.

- Specify the intended Dow portfolio, rebalancing cadence, position count, turnover estimate/cap, active-share requirement, benchmark, and cost model.
- Give the independently sourced effect range and translate it to a portfolio-level excess-return/Sharpe range under stated assumptions; include costs, effective breadth, six-year sample length, bootstrap dependence, and current/growing Holm-family size.
- Compare the implied range with `report_drafts/CRITERION4_BOUND_AUDIT.md` and/or the preregistered `break_even_rank_ic` calculation. Label all assumptions as assumptions.
- If the best defensible effect is below the criterion-4 feasibility bound, mark **STOP — FAIL: criterion-4 infeasible**. Do not commission a portfolio run merely to learn what this screen can establish.
- Verdict: PASS / FAIL, with reason.

## 6. Holdout availability and protocol

- State whether any holdout path or holdout-specific input is needed. Screening must not open, read, download, or calculate on sealed holdout data.
- Name the later coordinator-controlled holdout protocol and the availability-only evidence needed before it can be considered.
- Verdict: PASS / FAIL, with reason.

## Final screen decision

- Overall: **ADVANCE TO COORDINATOR REVIEW** only if every gate above passes; otherwise **STOP — FAIL**.
- What evidence could change this decision?
- Reviewer/date:

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
