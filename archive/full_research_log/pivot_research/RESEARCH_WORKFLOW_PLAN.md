# Research and testing workflow plan (draft, 2026-11-10)

Goal: find a market approach with a real edge that keeps the core of Advik's thesis. Small reweightings of the equal-weight basket are out of scope. Run under `C:\Users\musta\Desktop\UNSW\SSI\ORCHESTRATION.md`:
- at most 4 GPT-6 Luna terminals, reused across tasks;
- briefs written to the Task-spec contract;
- Claude plans, briefs and reviews, and writes no implementation code;
- pre-registration and a fresh holdout.

## What the user asked for
1. Diagnose why the current approach fails, properly. Round 3 churned out variants instead of explaining the failure.
2. Find substantial new directions through real online research, keeping the thesis core.
3. Brief the Luna agents properly on how to search, read and judge sources.
4. Run this as a proper Orca workflow with gates where the user decides.

## Why we likely got nothing (hypotheses for Phase 0 to test)
- **Weak test setup.** 30 large, liquid names, daily data and windows of 1-2 years leave little room for an edge. By the fundamental law of active management (IR ≈ IC × √breadth), even a real edge would rarely show up as significant.
- **The network measures the wrong thing.** Same-window return correlation captures co-movement, not which stock's pressure flows into which. So "heat" mostly averages neighbours' noise.
- **Portfolios came before evidence.** We never checked whether the signal predicts returns at each horizon or how quickly that fades. We went straight to portfolios, and costs swamped any small effect.
- **The variants drifted away from the thesis.** Most of the ~100 were generic factor ideas (skewness, volatility, beta, and so on), so they never tested the thesis itself.

## Workflow (4 Luna workers)

| Phase | Worker(s) | Output |
|---|---|---|
| 0. Post-mortem | L1, forensic analyst | Signal-vs-future-return rank correlation at 1-20-day horizons and how fast it fades; contribution of each component; what the heat term does mathematically (eigen and spectral breakdown of the graph filter); the smallest edge detectable given breadth and sample length; cost break-even |
| 1. Deep research | L2 (price-pressure literature), L3 (networks and how pressure spreads) | Evidence cards from real papers, gathered under the search protocol below |
| 1b. Data scouting | L4 | What we can actually get: FactSet (UNSW access), intraday bars, 13F common ownership, ETF holdings, supply-chain links, short interest |
| 2. Direction dossiers | L2 and L3 synthesise; Claude reviews | 3-4 substantially different directions, each with mechanism, evidence, data and a test design. **User decision gate: the user picks.** |
| 3. Testing | L1 (implementer) | Hypothesis-first tests (event studies, predictive power by horizon) before any portfolio; pre-registered; fresh holdout |

## The kind of direction meant (keeps "pressure spreads through a network")
- **Pressure through common ownership.** Fund flows force the same trades across stocks held by the same funds, so build the network from shared institutional or ETF holdings, not return correlation (Anton and Polk 2014; Greenwood and Thesmar 2011; Ben-David, Franzoni and Moussawi 2018).
- **Pressure through economic links.** Supplier and customer links carry information with a lag (Cohen and Frazzini 2008).
- **Real order-flow pressure.** Measure pressure from intraday signed order flow or order-flow imbalance instead of daily candles. The course guide prefers intraday data anyway.
- **Event-based tests.** Find large pressure shocks in one stock, then measure how its network neighbours respond over the next 1-10 days, instead of ranking a weekly top 5.

## Research protocol for L2 and L3
- **Sources:** Google Scholar, SSRN, NBER, arXiv q-fin, and the top journals (JF, JFE, RFS, plus JFQA and RoF), with a fixed list of search terms.
- **Widening the search:** follow references backwards and citing papers forwards from 3-5 key papers.
- **Reading:** the abstract, introduction, data section and main results table; go deeper only when needed.
- **Evidence card for each paper:**
  - claim and mechanism
  - data, sample and horizon
  - effect size and t-statistic
  - whether it survived after publication or in replications
  - whether we can get the data
  - a DOI or link
- **Checks:**
  - Every citation needs a verified link. Anything unverified is flagged, never invented.
  - Separate what a paper shows from what it speculates.
  - Note any criticism or failed replication.

## Open questions for the user (before the briefs are written)
1. **Advik's thesis:** what is its core in your words? Assumed: "measurable buying pressure persists and spreads through a network of related stocks" (pressure plus heat diffusion). Is that right, or is it narrower?
2. **Data:** FactSet access? Any intraday or trades-and-quotes data?
3. **Time and git:**
   - The report is due 20 Nov. Are 3-4 days for Phases 0-2 acceptable?
   - The playbook ends every brief with commit, push and opening a PR, but `pivot_research` is not a git repo. Initialise one, or skip that step here?
