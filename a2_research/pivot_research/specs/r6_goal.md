Work fully autonomously. NEVER ask the user anything or wait for input. Log every decision and reason in specs/r6_decisions.md and keep going.

DELIVERABLE: 2–3 genuinely different trading approaches with a real, non-overfit edge over EW30, written up in A2/pivot_research/R6_FINAL.md. Keep researching, building and testing until 2–3 pass. Running out of ideas is not an end state: start a fresh research round. Getting through directions is never progress; only passing edges count.

START FROM: R5_FINAL.md and RESEARCH_WORKFLOW_PLAN_REVISED.md §10 (round-5 retrospective). Dead: D4–D7, index-change and ETF-flow. Reuse the harness, data and holdout setup.

IDEA GATE (before any build): each direction needs:
(a) 2+ verified papers;
(b) a written case for why the edge survives in mega-caps after 2020 and has not been arbitraged away;
(c) a power check: enough events or cross-section to reach t ≥ 2 at a plausible effect size;
(d) a cheap data-feasibility pull done first;
(e) a novelty note: what is new versus the published result.
An independent worker red-teams (a)–(e). Rank ideas by expected edge, not by ease.

SEARCH SPACE: Advik's thesis: buying pressure that persists, spreads or reverses through related assets. Trade the Dow 30 daily, 2020-11 to 2026-10. Mechanisms may be estimated on a wider point-in-time universe (S&P 100 or 500) for power, but the edge must show in the Dow portfolio. Free data plus UNSW FactSet only. Daily to monthly horizons; long-only (active share ≥ 50%) or long-short.

PASS CRITERIA (fixed: never loosen, reinterpret or waive):
1. Thesis fit; 2+ verified papers.
2. Pre-registration frozen (FROZEN date plus prereg_digest of the file content) before outcomes; at most 3 variants.
3. Development: the pre-registered sign, NW t ≥ 2; placebo links show no effect.
4. After 0.05% per side: excess return and Sharpe above EW30; block-bootstrap p < 0.05 after Holm across all R6 tests; DSR at the cumulative trial count; turnover ≤ 50% or costs < 25% of gross edge.
5. A one-shot coordinator holdout: Dow 2010-01 to 2020-10, point-in-time, gaps disclosed. Same sign, Sharpe above EW, p < 0.10.

ANTI-OVERFIT: 30 new variants, logged in r4_trials.md. Mechanism tests before portfolios. No sweeps. A failed mechanism kills the direction: no sign flips, rescue variants or source switches. The D4 reversal may only return as a NEW pre-registration. Workers never touch the holdout. Strong or late results get an independent reproduction. Report every test.

PROCESS: before any real run, a runner-vs-prereg diff and synthetic tests. Runners refuse without --execute. One owner per run. Fix input bugs before freezing.

STOP: 2–3 passes, or the deadline 2026-11-18 23:59 AEST. Then write R6_FINAL.md: passes, every direction, trial count and an honest conclusion. Near-misses are labelled NOT passing.

WORKERS: 4 GPT-6 Luna (high), reuse terminals. Keep 2+ directions in preparation at all times (specs/r6_backlog.md). One inbox wait; reassign at once; no idle workers. L1 implements; L2 and L3 research, red-team and draft; L4 data only. Claude plans, reviews, freezes and runs the holdout; it writes no code.
