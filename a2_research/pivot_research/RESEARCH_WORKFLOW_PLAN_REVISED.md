# Research and testing workflow — pressure and network diffusion

**Revised:** 2026-11-10  
**Source of truth:** *FINS3666 Strategy Development Daily.pdf*, §§3.1–3.11 (Vedant Vaghela). The PDF explicitly identifies the **hourly implementation as the primary design** and the **daily implementation as a rule-for-rule robustness design**. Obtain and audit the hourly companion document before claiming full primary-strategy reproduction.  
**Purpose:** Explain the existing model's performance, test its two economic hypotheses, and research *substantial, mechanism-consistent* improvements—not churn through factor variants or minor portfolio-weight changes.

## 1. Non-negotiable strategy core

The model proposes **two separate, testable hypotheses**:

1. **Measurable, short-lived price pressure.** Closing near the day's high, positive signed-volume activity, and daytime gains relative to overnight gaps may indicate buying pressure that persists briefly.
2. **Pressure diffuses across linked stocks.** A connected stock may respond to pressure originating elsewhere. The current implementation uses positive contemporaneous return correlations as *undirected proxies for links* and a spectral graph heat kernel as the mathematical diffusion operator. This is an analogy and a modelling hypothesis, **not** evidence of directional causality.

The research must preserve the idea **pressure originates in a stock, can persist, and may reach related stocks**. Alternative *measurements*, *links*, *propagation operators*, *horizons*, and *event-based implementations* are in scope if they test that idea. Generic volatility, skewness, beta, momentum, or sector strategies with no explicit pressure/transmission mechanism are out of scope. Do not assume network transmission is true before testing it.

### Baseline specification to freeze before diagnosis

The following is the **daily implementation**, with the primary hourly model to be matched separately against its companion specification. Use the daily design as written; do not quietly substitute a simpler approximation.

| Layer | Exact daily baseline from the strategy document |
|---|---|
| Market/universes | Point-in-time Dow 30 rosters: recent roster effective **8 Nov 2024** and earlier roster effective **31 Aug 2020**; use their stated valid study windows. Earlier period runs through **23 Feb 2024**; recent implementation uses the specified **6 Dec 2024** fill-grid anchor and, in the provided reproduction command, ends **31 Dec 2025**. |
| Data | Session adjusted O/H/L/C and full-session volume. Yahoo Finance except the disclosed WBA historical-data exception. Adjust raw OHLC by adjusted-close / close; log vendor and corporate-action caveats. No silent dropping of missing names. |
| Own pressure | Five-session **CLV**, five-session **signed volume** divided by a 25-session volume baseline, and five-session **intraday-minus-overnight** return measure. Convert each to tie-averaged percentile ranks across 30 names; average ranks equally into `p`. See §3.4 for exact formulae and zero-range handling. |
| Network | Last **63 sessions** of adjusted close-to-close returns; remove each day's equal-weight cross-sectional market return; Pearson pair correlations; positive links only; each node chooses up to **five** strongest; symmetrise; zero diagonal. See §3.5. |
| Diffusion | `L = D - W`; `K = exp(-1 * L)` via symmetric eigendecomposition. Set the **diagonal of K to zero** before calculating incoming heat. Standardise `p` cross-sectionally; heat is the kernel-weighted **average of other stocks' z-scored pressure**. If total incoming kernel weight is **≤ 0.05**, heat is missing, not zero. See §3.6. |
| Final score | Tie-averaged percentile re-rank of `p` and a separate percentile rank of defined incoming heat; **50% own / 50% incoming heat** when defined, otherwise own pressure only. |
| Portfolio | **Five equally weighted long-only stocks** (20% each); reviewed every **fifth session** on fixed, never-reset grid; top-eight **hold buffer** for incumbents; alphabetic tie-breaks. Signals at prior close, executions at next session's open, fractional shares, drift between reviews and rebalance at reviews. |
| Cost | **0.05% per side**, charged on **actual trades**, including entrant buys, exit sales, stayer rebalances, initial entry and terminal liquidation; post-cost equity solved as specified in §3.8. |
| Comparators | Pressure only, direct neighbour-weighted mean instead of kernel heat, equal-weight 30-name portfolio on same grid/costs, and SPY on a clearly stated basis; hourly versus daily on identical eligible windows. |

**Reproduction safeguards:** Do not run the daily backtest with bare CLI defaults: §3.10 says they apply the wrong cost convention and omit the hold buffer. Use the documented `--cost=actual --buffer=8` and relevant roster/anchor/window flags. Validate next-open timing, lookahead truncation invariance, fixed rosters and exact adjustment conventions before using P&L to reason about edge.

**Source limitations to retain:** The baseline PDF does *not* give performance results. It cannot establish that the strategy failed, what component failed, or whether costs caused a loss. Any such assertions are **questions for the post-mortem**, not findings. The available PDF documents the daily variant only; the hourly model must be sourced separately for exact reproduction.

## 2. Operating rules: Orca / Claude / GPT-6 Luna

Work under `C:\Users\musta\Desktop\UNSW\SSI\ORCHESTRATION.md` **after inspecting the actual file**. This workflow does not invent or supersede its Task-spec requirements.

- **Claude** owns scope, research questions, briefs, quality control, synthesis, user decision gates and review; **Claude does not write implementation code**.
- Use **at most four concurrent GPT-6 Luna terminals**, L1–L4, and reuse them across phases rather than spawning new ones per task.
- Each assignment has a written Task-spec-compliant brief: question, source files, frozen baseline, in/out of scope, methods, validation requirements, deliverables, acceptance criteria and stop conditions.
- Workers may propose tests but must **not silently change baseline definitions**, inspect a sealed holdout while designing, or promote backtest P&L to mechanism evidence.
- If the orchestration playbook requires git commits/PRs, confirm whether `pivot_research` should be initialised as a repository. Until that decision, save reproducible artifacts and diffs locally; do not claim to have pushed code.
- Present results at the gates below. **Only the user approves a change of thesis scope, new datasets with material cost, candidate directions for testing, or final promotion.**

## 3. Workflow and gates

| Phase | Owner | Deliverable | Exit / decision gate |
|---|---|---|---|
| **0A. Baseline audit** | **L1** | Executable specification, code-to-paper trace, source-data inventory, reproduction logs and discrepancy register for daily and (when available) hourly | **Gate A:** Claude verifies fidelity; user resolves any material deviation before interpreting results |
| **0B. Mechanism post-mortem** | **L1** (L4 assists data/stats) | Pressure predictiveness, network incremental value, mathematical diffusion diagnostics, uncertainty/power, turnover and costs, and a ranked failure tree | **Gate B:** User reviews what failed, what is merely uncertain and what is worth studying |
| **1A. Pressure research** | **L2** | Literature evidence cards on price/flow pressure, persistence, timing and decay, including adverse evidence | Completeness and source-quality review by Claude |
| **1B. Links/diffusion research** | **L3** | Literature evidence cards on propagation across shared ownership, ETFs, economic links and return-network alternatives | Completeness and source-quality review by Claude |
| **1C. Data and feasibility** | **L4** | Data-access matrix with point-in-time coverage, granularity, licensing, history, survivorship risk, timing and cost | **Gate C:** User approves feasible dataset and scope boundaries |
| **2. Direction dossiers** | **L2 + L3**, with L1/L4 feasibility input; Claude integrates | **3–4 genuinely different, mechanism-consistent directions**, each with explicit hypothesis, diagnostic, research basis, data needs and invalidation test | **Gate D:** User selects **one** primary direction (optional backup) before implementation |
| **3A. Pre-register and research-test** | **L1**; L4 independently checks | Signed test plan, baseline comparison, code and leakage checks; leading indicators and event tests before portfolio construction | **Gate E:** Proceed only if hypothesised mechanism shows evidence without holdout tuning |
| **3B. Portfolio and robustness test** | **L1**; Claude reviews | Executable rules, realistic trading assumptions, ablations, costs and stability checks; single pre-specified holdout evaluation | **Gate F:** User decides whether to adopt, reject, or report as inconclusive |
| **4. Report and handoff** | Claude synthesises; workers supply evidence | Traceable account of baseline, failures, proposed mechanism, tests, results, limitations, reproduction commands and negative findings | Final user sign-off |

Parallelise **0B** with literature and data scouting *only after the baseline specification is frozen*. Do not let research ideas contaminate baseline definitions or the untouched holdout.

## 4. Phase 0: forensic diagnosis of the actual strategy

### 0A. Fidelity first

1. Find the implemented daily script and hourly companion paper/code. Record source file versions, dates, hashes, code options and exact test windows.
2. Produce a **paper-to-code map** for each component: CLV, signed-volume denominator, intraday/overnight decomposition, tie handling, ranks, cross-sectional standardisation, market-demeaned correlations, graph symmetrisation, Laplacian/kernel, isolation threshold, heat re-rank, score reweighting, selection/buffer, fill timing, and actual-trade costs.
3. Reproduce the documented historical rosters and anchor grid; flag missing data and vendor exceptions; keep daily-versus-hourly frequency and feed differences explicit.
4. Validate with unit/property tests: identical-price zero-range handling, zero/absent connectivity, connected-component heat conservation **before diagonal removal**, kernel symmetry and nonnegativity (within tolerance), rank ties, future-truncation invariance, signal-close/next-open fills, and accounting identities.
5. Reproduce the original report outputs **if original reported results and artifacts exist**. No reproduction claims based only on the methods PDF.

### 0B. Sequential diagnostics (no portfolio optimisation yet)

**A. Does own pressure carry information?** Measure rank IC and long/short sorting diagnostics for own pressure and each raw/ranked component versus **forward stock-specific returns** at predeclared 1, 2, 5, 10 and 20-session horizons. Report market-adjusted and raw outcomes separately. Align future return windows with the close-signal/next-open trading convention. Use overlap-aware uncertainty estimates, date-level effective sample size and multiple-test-aware interpretation. Plot decay, conditional effects and uncertainty, not just mean IC.

**B. Does the network add predictive information?** Compare `(i)` own pressure, `(ii)` direct weighted neighbour pressure, `(iii)` heat-kernel incoming pressure, and `(iv)` network-only heat under the same dates and universe. Test incremental predictive value **conditional on own pressure**, not merely score correlation or returns of two portfolios. Analyse link stability, noise of 63-session correlations, connected components, weight distribution, own-versus-neighbour redundancy, and spectral smoothing of cross-sectional pressure. Cross-sectional return correlations show contemporaneous similarity, **not direction of transmission**.

**C. Does any effect actually move across neighbours?** Predefine pressure shocks and test their association with **subsequent** connected-stock responses, excluding the originating stock. Include non-neighbour and permuted/degree-matched graph controls and common-market/sector shocks. Distinguish same-session co-movement from lagged propagation. An event study cannot by itself prove causality.

**D. Is the portfolio able to monetise the observed signal?** After A–C, quantify pre-cost and post-cost performance, realised turnover (including buffered names and rebalancing trades), entry/exit contributions, cost break-even by turnover, delay from close signal to next-open fill, concentration, market/sector exposure and benchmark sensitivity. Explicitly test pressure-only, neighbour average, heat, equal-weight Dow and SPY as specified. Do **not** assume that 0.05% per side is achievable or that adjusted next opens are actual tradable fills.

**E. Are the estimates informative?** Estimate detectable effect sizes and confidence intervals from **observed dependence, time span, cross-sectional breadth and serial correlation**. The fundamental-law heuristic (`IR ≈ IC × sqrt(breadth)`) is not itself a sample-power calculation; avoid assuming that 30 names imply 30 independent bets. Compare the longer early-roster window with the recent one and the matched hourly/daily windows without treating one as a clean independent validation of a model already tuned on it.

**Output:** one diagnostic table per hypothesis (`supported` / `not supported` / `inconclusive`), strongest falsification, uncertainty, and which layer needs change: pressure proxy, link definition, diffusion rule, frequency/horizon, or execution. Preserve negative results.

## 5. Phase 1: evidence-led research and data scouting

### L2: price pressure and persistence

Research **why and when** net buying pressure might predict future returns and what proxies distinguish informational flow from temporary liquidity demand. Search both supportive and null findings: order-flow imbalance, trade-sign imbalance, intraday pressure, price impact and reversal, closing-location value, signed volume, overnight-versus-intraday return decomposition, institutional flow, ETF-induced demand, short-horizon lead-lag and decay. Explicitly identify whether a result concerns **contemporaneous impact, temporary reversal, or persistent post-shock drift**. Do not treat evidence of same-day impact as evidence of next-day predictability.

### L3: links, spillovers and diffusion

Investigate whether a link predicts **lagged influence**, not just correlation: common fund/ETF ownership, correlated institutional flows, supply-chain/customer links, shared investor clienteles, lead-lag effects and signed/directed transmission graphs. Contrast the baseline **symmetric return-correlation graph + `exp(-L)` heat filter** with economic-link networks, direction-aware lag models and non-diffusion neighbour aggregation. Ask whether averaging neighbours destroys a sparse shock, whether normalisation creates redundancy with own pressure, and what horizon a shock should take to propagate.

### L4: feasibility and point-in-time integrity

For **UNSW FactSet access (unconfirmed)**, assess actual entitlement and available historical coverage rather than assuming availability. Scout intraday OHLCV, trade/quote or signed-order-flow data, ETF holdings and historical constituents, institutional ownership/13F **filing dates and reporting lags**, supply-chain link vintages, short-interest publication lags and benchmark/corporate-action data. Record for each: endpoint/provider, right to access, earliest available timestamp, retrospective revisions, universe coverage, cost, practical retrieval effort and whether the proposed test can be carried out before the report deadline. In particular, a 13F position is not known on its quarter-end date; it becomes public at filing/publication time.

### Source protocol (L2 and L3)

**Search:** Google Scholar, SSRN, NBER, arXiv q-fin, JF/JFE/RFS/JFQA/RoF and credible working papers; targeted terms above plus backward references and forward citations for 3–5 anchor studies. Prefer full text over abstracts for numbers and claims. Research is distinct from merely listing plausible citations.

**Required evidence card for *each* material claim:**

- Full bibliographic identity and **verified DOI/stable URL**; source type, publication/working-paper date and revision version.
- Research question, hypothesised mechanism, what was *actually measured*, whether pressure and transmitted response are contemporaneous or lagged.
- Asset universe, period, frequency, data vintage, forecast horizon and economic/statistical effect size **with relevant uncertainty** (or `not reported`).
- Identification strategy, out-of-sample status, transaction costs and implementation feasibility.
- Replications, contradictory findings, limitations and likely transferability to our Dow/intraday setting.
- Whether the data can be accessed **as it was known at the historical signal date**.
- One explicit implication for a falsifiable test of **our two hypotheses**, plus a claim that would disconfirm it.

**Verification:** Never fabricate links, results or citations; mark inaccessible/unverified materials. Clearly separate paper results, author conjecture and our extrapolation. Do not cite a theoretical graph heat equation as empirical proof of stock-market diffusion.

## 6. Phase 2: candidate directions, not a variant factory

The following are **research candidates**, not established improvements. Select on evidence and data feasibility after Gates B/C:

1. **Pressure from actual trading imbalance.** Keep the pressure→network→response logic but replace OHLCV-derived pressure with a historically obtainable measure of executed order-flow imbalance / signed trading pressure. Ask whether it predicts *subsequent* returns, not just the simultaneous price move. Compare against frozen CLV/SVOL/OI proxy.
2. **Common-holdings flow transmission.** Define link weights from historical, publication-lagged shared ETF/fund holdings and investigate exogenous or measurable ownership-linked pressure shocks. Test whether the neighbours react later, versus identical placebo networks.
3. **Economic-link propagation.** Use historically known supplier/customer relationships to test a directional or lagged response following a price-pressure shock. Distinguish information diffusion from inventory-flow or fundamentals transmission, and assess whether this remains the same economic thesis or an adjacent mechanism.
4. **Shock-centred network strategy.** Preserve the original pressure signal but identify high-conviction **source-node shocks**; trade or analyse downstream neighbours only after a pre-specified lag. Compare graph heat, direct-neighbour propagation and no-network controls. This may be combined with one of the link definitions above but is a materially different **trading design**, not a trivial rank reweighting.

For **each dossier**, provide: causal/economic story; precise change from baseline; what remains fixed; 2+ pieces of verified support or a clearly labelled evidence gap; needed data and publication lags; expected sign and **pre-specified horizon**; simplest falsification/event-study design; baseline/placebo comparators; costs, capacity and execution issues; principal failure mode; minimal viable implementation; stop rule. State why it is *substantial*, not parameter tuning. **User chooses** the direction; do not auto-select the one with the best in-sample backtest.

## 7. Phase 3: testing without leakage or significance theatre

1. **Pre-register before touching the reserved holdout:** primary hypothesis, signal/graph definition, universe, prediction target, horizon, entry/exit timing, controls, outcome metric, minimum economically meaningful effect, ablations, exclusion/missing-data rules, cost assumptions and stopping criteria. Distinguish *exploratory* from *confirmatory* results.
2. **Assign roles to periods:** exploratory research/training window, development/validation period and a **chronologically later untouched holdout** with sufficient warmup and point-in-time constituent/data availability. Choose dates after inspecting only coverage and source availability, **not realised returns**. If a truly fresh holdout is unavailable because prior rounds examined all dates, say so and use an explicitly lower-confidence forward test or genuinely new, unexamined dataset.
3. **Test mechanism first:** own-pressure forward predictiveness; propagation conditional on source shock; network-vs-placebo incremental value; decay/horizon; realistic uncertainty. Do not create a portfolio from an unsupported signal just because a ranking backtest looks good.
4. **Then test investability:** identical eligibility, timing, execution and cost basis across variants; cost sensitivity beyond the source's assumed 5 bps per side; turnover, spread/slippage proxies if available, capacity, downside risk, exposure and regimes. For daily-vs-hourly comparisons, preserve same rules and overlapping periods rather than silently retuning each frequency.
5. **Evaluate the sealed holdout once.** Report primary pre-registered result including nulls/negative findings; do not re-optimise based on holdout results and then relabel the same data a fresh test. Any further changes are new exploratory work requiring a new untouched test.

**Promotion criterion:** The direction must have reproducible, point-in-time-correct evidence of the intended **lagged pressure transmission**, incremental usefulness beyond pressure-only/no-network controls, and a plausible post-cost trading case. If one condition fails, reject it or record it as inconclusive—do not hunt through additional variants to force a win.

## 8. Required handoffs and reporting format

Each worker outputs to a versioned directory with `README`, source links/IDs, assumptions, data coverage, reproducible commands, exact outputs, checks and limitations. Claude maintains a **decision log**: gate, evidence considered, user instruction, authorised scope, and discarded alternatives. Final report must keep **baseline model**, **diagnostic findings**, **research evidence**, **experimental modifications** and **sealed holdout results** distinct; never describe the daily robustness model as if it were the hourly primary strategy.

**Suggested task slots (reused, not multiplied):**

- **L1 — Forensics / implementation:** audited replica; signal/graph diagnostics; pre-registered candidate implementation and testing.
- **L2 — Pressure literature:** verified price-pressure literature, replication critiques, pressure-direction dossier.
- **L3 — Network literature:** verified spillover evidence, graph-mechanism critique, network-direction dossier.
- **L4 — Data and independent validation:** access audit, point-in-time timestamps, statistical/power review, leakage and accounting checks.

## 9. Items awaiting user input (do not block preliminary audit or literature review)

1. **Authorship / thesis ownership:** The uploaded daily paper is credited to **Vedant Vaghela**, while the previous draft calls this *Advik's thesis*. Confirm whether the desired core is Vedant's documented two-hypothesis model, a joint/team thesis, or an additional Advik-specific document. Until clarified, use the uploaded PDF as the specification, not an assumed personal attribution.
2. **Primary source:** Location of the **hourly companion paper and code**, plus baseline results and earlier rounds' experiment logs. The daily PDF alone cannot establish the hourly rule-for-rule implementation in code.
3. **Data rights:** Actual FactSet credentials/entitlements, intraday or trade/quote coverage, and permission to use external ownership/supply-chain data.
4. **Timing:** Is the previously stated **20 November report deadline** still binding, and how much time may be allocated to investigation before testing? Do not make the plan depend on a fixed 3–4-day phase budget without consent.
5. **Git:** Initialise `pivot_research` as a repo to satisfy playbook commits/PRs, or record an explicit exception for local-only work.

**Default next action:** Claude briefs L1 on the **0A baseline audit** and L2/L3 on source-verified literature gathering; L4 checks dataset feasibility. The team must present a coherent Phase 0 diagnosis and evidence-backed direction dossiers before asking the user to authorise strategy changes.

## 10. Round 5 retrospective (2026-11-11)

**Outcome:** 0 of the target 2–3 approaches passed. D4 failed with a significant wrong sign (IC −0.0181, t −2.42: reversal). D5 failed (t 0.56) and D6 failed (t 0.77). D7, index-change and ETF-flow were infeasible at their input gates. 6 of the 30 variants were used. The holdout is unopened. Full record: `R5_FINAL.md`, `specs/r5_decisions.md` (items 1–36).

### Was it in depth?
- **Governance: yes.** Frozen pre-registrations, placebos, Newey-West, goal-wide Holm, independent reproduction of every failure, and disclosed deviations. Credible nulls.
- **Idea depth: no.** Most effort went to process, not to asking why an idea should work in 30 mega-caps. Several failures were predictable before any build:
  - D4: 50 broad managers hold every Dow name, so the network was almost complete (24 of 25 quarters) and carried little information.
  - D5: two-digit SIC groups in the Dow have one or two members each, which gives a thin graph.
  - D7: mega-caps rarely disclose a customer above 10% of revenue (3 pairs found).
  - Index-change: 3 events in 6 years.
  - ETF-flow: no free daily creation/redemption data.
  A one-hour feasibility and power check would have killed four of these up front.

### Was it novel?
Mostly not. Every direction was a known published anomaly placed in the hardest universe for it:
- D4: Anton & Polk 2014 (connected stocks).
- D5: Hou 2007 (industry lead-lag).
- D6: cross-asset time-series momentum (Moskowitz, Ooi & Pedersen 2012).
- D7: Cohen & Frazzini 2008 (customer-supplier links).
- Index-change and ETF-flow: standard event studies.

None added a new measurement or a new link. The only unexpected result was the **D4 common-owner reversal**, the one genuinely informative finding.

### Process failures (to fix)
- Freeze hashes computed on the file path instead of the content (fixed; decision 15).
- An accidental D6 real-data run by a runner without guards (decision 17).
- A D4 runner that did not implement the frozen endpoints (decision 23).
- AAPL and TRV missing from the 13F panel, plus 13F unit changes; both found only after the freeze (decisions 16 and 24).
- Stale or failed tasks that never started (D7 links ran late), plus heartbeat noise in the coordinator loop.

### Changes for round 6 (`specs/r6_goal.md`)
1. **An idea gate before any build:** 2+ papers, a written case for why the edge survives in post-2020 mega-caps, a power check, a cheap data pull first, and a novelty note. Each is red-teamed independently.
2. **Rank ideas by expected edge,** not by ease or cost.
3. **Estimate the mechanism on a wider point-in-time universe** (S&P 100 or 500) for power; trade the Dow 30.
4. **UNSW FactSet allowed** (supply chain, ownership, estimates).
5. **No cycle cap.** Search continues until 2–3 pass or the 2026-11-18 deadline; working through directions is not progress.
6. **Process guards:**
   - a runner-vs-pre-registration diff and synthetic tests before any real run;
   - `--execute` guards and one owner per run;
   - input bugs fixed before freezing;
   - hashes always computed with `prereg_digest(content)`.
7. **The pass criteria are unchanged and locked.** The D4 reversal can return only as a new pre-registration, never as a relabelled D4 pass.
