Work fully autonomously until this goal is met. NEVER ask the user what to do, which direction to take, or to confirm a choice, and never stop to wait for input. At every decision point, apply the rules below, log the decision with its reason in specs/r5_decisions.md, and keep going. The only reason to stop is the stop rule at the end.

OBJECTIVE: find 2–3 genuinely different trading approaches with a real, non-overfit edge for the FINS3666 project. Build on the round-4 work in A2/pivot_research (r4_L1–L4, r4_harness incl. builders, r4_dossiers, specs/r4_prereg/drafts, r4_L4/data). Follow C:\Users\musta\Desktop\UNSW\SSI\ORCHESTRATION.md. Main universe: Dow 30 daily, 2020-11 to 2026-10.

PRE-MADE DECISIONS (do not re-ask):
- Direction order: D4 (common-owner CLV pressure, 50-filer 13F network) and D5 (directed industry leader→follower; L4 builds a dated SIC panel from 10-K headers first) run IN PARALLEL. If either fails or proves infeasible, move to the next in this order: D6 (cross-asset trend, asset-appropriate, monthly), then a new research cycle by L2/L3 for fresh buildable directions. D1–D3 only if their data turns out to be available for free.
- 13F network after the last public filing: carry it forward and report its age; mark observations where the network is more than 2 quarters stale.
- Holdout route: the Dow 30 with point-in-time rosters, 2010-01 to 2020-10, WITH THE GAPS DISCLOSED (KFT, DWDP, WBA missing; UTX proxied by RTX lineage). EW benchmark over the available names. Report DWDP's window both with and without. No paid data.
- Freezing: the coordinator freezes a pre-registration (adds 'FROZEN: <date>' and a hash) as soon as its data inputs are built and checked, before any outcome is computed.

AN APPROACH COUNTS only if ALL hold:
1. Keeps Advik's thesis (buying pressure that persists and/or spreads through a network of related assets); active share of at least 50% or a long-short design; backed by at least 2 verified papers.
2. A pre-registration frozen before any outcome data: hypothesis, sign, horizon, at most 3 variants, selection rule and tests.
3. Mechanism evidence on development data with the pre-registered sign, Newey-West t >= 2.0; a placebo (shuffled or random links) shows no such effect.
4. After 0.05%/side costs: positive excess return and higher Sharpe than EW30. Block-bootstrap p < 0.05 after Holm correction across all tests in this goal. Deflated Sharpe reported. Turnover 50% or less per rebalance, or costs below a quarter of the gross edge.
5. Sealed holdout run ONCE by the coordinator on frozen code: same sign, Sharpe above EW30, p < 0.10.

ANTI-OVERFITTING:
- Hard budget of 30 variants in total, logged in specs/r4_trials.md.
- Predictive and mechanism tests come before portfolios.
- No parameter sweeps.
- Workers never touch holdout data.
- Report every test, including failures.
- A failed mechanism test kills the direction: no rescue variants.

WORKER UTILISATION (mandatory):
- Exactly 4 GPT-6 Luna (high) workers, reusing the existing terminals with --terminal.
- Keep a BACKLOG of ready tasks in specs/r5_backlog.md, created up front with task-create and --deps, so that whenever any worker finishes, its next task starts within the same coordinator turn.
- No worker may sit idle while the backlog holds runnable work. When the critical path is blocked, give idle workers useful parallel work: data builds, red-team or audit of other workers' outputs, report-section drafts, reproducibility checks, the next direction's preparation.
- Use ONE inbox wait over the whole Run (check --wait covering all workers), process EVERY message in the delivery, reassign immediately, then wait again.
- After each delivery, run worker-list and confirm all 4 are busy. If not, assign work before waiting.

ROLES (flexible to keep everyone busy): L1 implementer and tester; L2 and L3 research, pre-registration drafting, red-team and report drafting; L4 data only (barred from design and implementation because of the DWDP exposure). Claude plans, briefs, reviews, freezes pre-registrations and runs the holdout; it writes no implementation code.

STOP only when 2–3 approaches pass all five criteria, or when the 30-variant budget or 3 testing cycles are exhausted. Then write a final report (A2/pivot_research/R5_FINAL.md) with results for every direction, the full trial count and an honest conclusion.
