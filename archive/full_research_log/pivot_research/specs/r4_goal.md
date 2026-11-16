Find 2–3 genuinely different trading approaches with a real, non-overfit edge for the FINS3666 project, following RESEARCH_WORKFLOW_PLAN.md and C:\Users\musta\Desktop\UNSW\SSI\ORCHESTRATION.md. Main universe: Dow 30 daily data, 2020-11 to 2026-10. At most one approach may use a different asset set (for example cross-asset ETFs), but only with an asset-appropriate method; the earlier "treat ETFs like stocks" test does not count.

An approach counts only if it meets ALL of these:
1. THESIS AND SUBSTANCE: it keeps the core of Advik's thesis (measurable buying pressure that persists and/or spreads through a network of related assets). It is a substantial change of direction, not a reweighting of the equal-weight basket: active share of at least 50%, or a long-short / market-neutral design. It comes from the Phase 1 research and is backed by at least 2 verified papers (working DOI or link).
2. PRE-REGISTERED: before any outcome data is touched, the approach has a written, frozen pre-registration (specs/r4_prereg/<approach>.md) stating the hypothesis, the predicted sign and horizon, at most 3 variants, the selection rule and the tests. Nothing is re-specified after results are seen.
3. MECHANISM EVIDENCE (development data, Dow 2020-11 to 2026-10): the signal predicts returns with the pre-registered sign. The rank correlation between signal and future returns, or the event-study response, must have a Newey-West t-stat of at least 2.0. A placebo version (shuffled network or random links) must show no such effect.
4. TRADABLE EDGE (same data): after 0.05%/side costs, the approach has positive excess return over EW30 and a higher Sharpe. Its block-bootstrap p-value is below 0.05 after a Holm correction across every pre-registered test in this goal. The deflated Sharpe ratio is reported at the full trial count. Average turnover is 50% or less per rebalance, unless costs are shown to stay below a quarter of the gross edge.
5. SEALED HOLDOUT: on frozen code, the coordinator runs it ONCE on data no one has looked at: the Dow 30 with point-in-time rosters, 2010-01 to 2020-10. If that data proves infeasible, L4 proposes a substitute and the user approves it before any testing starts. The holdout must keep the same sign, beat EW30's Sharpe, and have p < 0.10.

ANTI-OVERFITTING RULES:
- A hard budget of 30 variants for the whole goal, logged in specs/r4_trials.md.
- Hypotheses come from the literature and mechanism first, and the predictive tests (rank correlation, event studies) come before any portfolio.
- Workers never see or touch holdout data.
- No parameter sweeps.
- Report every test, including failures.

WORKERS: at most 4 GPT-6 Luna agents (high effort) in Orca orchestration, following the ORCHESTRATION.md standing rules:
- reuse terminals with `--terminal`, never leave one idle, and do not start a new agent per cycle;
- every brief follows the Task-spec contract;
- Claude plans, briefs and reviews, and writes no implementation code.
Roles: L1 forensic analyst then implementer, L2 pressure-literature researcher, L3 network and propagation researcher, L4 data scout.
Phases:
- Phase 0: post-mortem of the current strategy.
- Phase 1: research using the protocol in the plan.
- Phase 2: direction dossiers. STOP at the user decision gate and wait for the user to choose the directions; stopping there is allowed.
- Phase 3: pre-register, test, then run the holdout.

STOP when 2–3 approaches pass all five criteria, or when the 30-variant budget or 3 testing cycles are used up. In that case, report the honest negative result with the full trial count.
