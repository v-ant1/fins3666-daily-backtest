# X — fixed co-movement network pressure

**Verdict: FAIL-GATE; no outcome test.** This is a direct reading of Advik’s propagation thesis: pressure in a stock predicts a later move in its historically co-moving Dow peers. But the requested graph-estimation period (Dow data before 2020-06) is sealed by the project data rules, and a fixed correlation network with pressure diffusion also comes very close to the original heat implementation. I did not load any pre-2020-06 Dow data or compute any signal or return outcomes.

## Proposed single direction

For each focal Dow name, use a fixed, undirected graph whose edge weights are pairwise return co-movement estimates from a pre-2020-06 period. On each development formation date, form a one-week pressure score from the other connected Dow names’ trailing signed-volume/close-location pressure, excluding the focal name; predict a **positive** focal-stock return over the next five sessions. A single static graph and a single one-week pressure window are intended; this is not a parameter sweep. The test would need to freeze the network estimator and edge rule before outcomes and control for the focal stock’s own pressure.

The signal is a cross-stock pressure measure, not a generic target-stock return rank: the source pressure is computed on connected names, then aggregated for the focal name. The graph date range and training period cannot be executed by this worker because that requires reading sealed Dow history.

## Gates (a)–(e)

### (a) Literature — partial support, not direct confirmation

Menzly and Ozbas find cross-predictability among economically linked customer and supplier industries and report that it is weaker where analyst coverage and institutional ownership are higher ([“Market Segmentation and Cross-predictability of Returns,” *Journal of Finance* 65 (2010), DOI 10.1111/j.1540-6261.2010.01578.x](https://doi.org/10.1111/j.1540-6261.2010.01578.x)). That supports slow information transfer across linked firms, but their links are supply-chain relationships, not return-correlation edges, and their predictor is return/news information rather than measured buying pressure.

Lo and MacKinlay show that cross-autocorrelations can produce lead-lag effects, including large-stock returns leading smaller-stock returns ([“When Are Contrarian Profits Due to Stock Market Overreaction?,” *Review of Financial Studies* 3 (1990), DOI 10.1093/rfs/3.2.175](https://doi.org/10.1093/rfs/3.2.175)). This supports return lead-lag as a distinct statistical mechanism, but it does not establish that CLV/signed-volume buying pressure transmits along a fixed Dow co-movement graph. Neither paper provides an effect estimate for this proposed pressure score or a post-2020 Dow portfolio.

### (b) Mega-cap and post-2020 case — weak

The case for mega-caps is that economically connected, liquid firms can still react at different speeds to shocks, while a fixed pre-period graph avoids estimating links on the same development returns used for testing. The counterargument is substantial: the cited mechanisms either rely on explicit production links or on size-related lead-lag effects, and both may attenuate in liquid, heavily followed mega-caps. Neither source demonstrates that pressure transmission persists in Dow names after 2020. The project’s prior workflow also states that rolling return correlation captures co-movement but may not identify who transmits pressure to whom.

### (c) Power — low under the SIC2-cluster design

I ran `r4_harness/power_sim.py` with 499 S&P names, 54 SIC2 clusters, 298 weekly dates, horizon 5 (NW lag 4), 0.20 serial-correlation assumption, 5,000 simulations, and a hypothetical planted IC of 0.0183. The cluster-adjusted date-level IC SD was set to `sqrt((1 + (499/54 - 1)*0.15)/(54 - 1)) = 0.20538`, using an assumed within-SIC2 correlation of 0.15. The simulated probability of NW *t* ≥ 2 was **25.4%**, and the 80%-power MDE was **0.0396**. The 0.0183 input is a sensitivity point, not an estimate from either paper or from project outcomes.

SIC2 is the requested/available cluster structure, but the proposed network crosses industries; SIC2 clustering does not fully represent graph dependence. Thus the simulation is only a standardized gate check and may overstate power if neighboring stock-pairs create additional dependence. It does not show that the signal exists.

Reproduction command:

```powershell
python r4_harness/power_sim.py --assets 499 --dates 298 --horizon 5 --signal-autocorrelation 0.2 --ic-sd 0.20538 --mean-ic 0.0183 --simulations 5000 --seed 20261120
```

### (d) Free-data feasibility — development inputs exist; required graph does not

The development-only `r6_C1/INPUT_QA.md` confirms a Dow component panel with 1,488 sessions from 2020-11-27 through 2026-10-30, 43,944 asset-date rows across 33 ticker identities, and full roster-bar coverage from 2021Q1 onward (2020Q4 is incomplete). The same QA reports an S&P panel with 716,987 asset-date rows across 564 ticker identities. These checks establish that daily development inputs exist; they do not establish any co-movement or pressure effect.

The graph in this brief must be estimated using pre-2020-06 Dow returns. Those data are sealed and may not be loaded, downloaded, plotted, or used to calculate correlations under the project-wide rule. The L4 availability-only exception cannot be used to estimate edge weights. The development panel starts in November 2020, so it cannot supply the required earlier graph either. **Data gate fails before signal construction.** Do not substitute a later graph or inspect the holdout as a workaround.

### (e) Novelty and exclusions — not sufficiently distinct

- **E1:** E1 uses same-industry peer pressure with SIC membership links and monthly formation. This proposal would instead use a fixed return-co-movement graph, cross-industry source names, and a weekly horizon. The network definition and horizon differ, but both ask whether peer buying pressure predicts returns; novelty is partial.
- **J1:** J1 is a weekly SIC2-relative own-stock return-reversal signal. This proposal uses positive peer-pressure persistence on a non-SIC graph; it does not change J1’s horizon, turnover, or sign to rescue J1. The mechanism is distinct from J1, although the common weekly timing alone is not a novelty claim.
- **Prior correlation-heat implementation and existing P2 screen:** the original strategy already diffuses OHLCV pressure on a return-correlation graph, so replacing its rolling graph with a fixed historical one is a limited change. The existing `r6_ideasP2.md` also covers pressure-confirmed co-movement pairs, though it predicts pair-spread convergence rather than focal-stock continuation. R5’s tested networks use other link types, but the existing correlation-heat implementation and P2 make this a close repeat of the project’s prior network ideas.

This remains faithful to Advik’s propagation thesis in concept. However, the precise fixed network is unavailable under the sealed-data rule, and the direction is too close to the original correlation-heat approach to justify a new R6 variant under the exclusion instruction. **Novelty gate fails for this round.**

## Rank and criterion-4 view

This is one candidate, so it ranks **1 of 1** by thematic fit, but not as an advancement. Neither cited paper provides a signal-matched Dow excess Sharpe after 0.05%/side costs. The responsible evidence-only expectation is **no positive Sharpe credit (central planning value 0.0; one-sided null-tail p proxy 0.50)**, not a claim that realized Sharpe is zero. The goal’s criterion-4 planning bar is about 0.8 annualized excess Sharpe after costs and Holm; this proposal has no documented route to that threshold, and no empirical estimate is permitted here. My subjective chance of clearing the full gates is **below 1%**, chiefly because the required graph cannot be built under current data rules and the mechanism closely repeats the original strategy.

**Recommendation: do not freeze or test this direction.** A future reconsideration would require a user-approved, explicitly unsealed source for pre-2020-06 co-movement estimates and a novelty decision that distinguishes the graph from the original pressure-heat method. No holdout data or outcomes were used in this screen.
