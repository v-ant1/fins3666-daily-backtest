# B4 revised — news co-mention / attention network pressure

**Current disposition: FAIL-GATE. Free-data buildable: yes in principle, but not ready for a preregistration.** This revision uses two complete GDELT GKG sample months inside the development period. It reports input coverage only: no prices, returns, pressure signals, or trading outcomes were read or calculated, and no holdout dates were accessed.

## Definition being reviewed

For each week, create a graph from GDELT GKG organization names that exactly match point-in-time Dow company alias lists. A proposed test would use the graph formed before a signal window, then ask whether signed pressure at one source company predicts same-sign pressure/returns at linked Dow peers over a fixed short horizon. The GDELT co-mention graph is undirected: co-mention alone does not establish which firm led, the economic nature of the link, or causal transmission. A preregistration would have to freeze chronology, source-pressure definition, target horizon, market adjustment, and the network placebo; this file does not authorize testing.

## Gate (a) — literature: PASS for plausibility, not for this exact signal

- Scherbina and Schlusche report that firms co-mentioned in news stories cross-predict one another’s later returns, including after removing customer–supplier pairs. The cited version is an AEI/SSRN working paper, not a peer-reviewed journal publication: [DOI 10.2139/ssrn.2363436](https://doi.org/10.2139/ssrn.2363436).
- Chen, Guo, and Tu find that co-mention strength predicts return comovement and correlated fundamentals among media-connected firms. Their result is about comovement, not necessarily a tradable return alpha: [Journal of Economic Dynamics and Control (2021), DOI 10.1016/j.jedc.2021.104191](https://doi.org/10.1016/j.jedc.2021.104191).
- Hirshleifer, Peng, and Wang find that social connectedness affects earnings-announcement reactions and subsequent dynamics. Social connectedness is not the same network as news co-mentions, so this is adjacent support only: [Review of Financial Studies, DOI 10.1093/rfs/hhae025](https://doi.org/10.1093/rfs/hhae025).

These references motivate a news-link hypothesis. None verifies that short-horizon signed buying pressure propagates across current Dow firms after 2020.

## Gate (b) — why it might survive in post-2020 mega-caps: PARTIAL / adverse coverage evidence

News articles can expose cross-industry ties, competition, shared products, financing, or common exposure that standard sector labels miss. Those complex relations could leave a short information-processing lag even in large firms. The counterargument is stronger for the Dow: its companies are widely reported and closely followed, and recurring co-mentions can reflect common news or broad-market stories rather than information diffusion.

The input sample confirms frequent mentions, but also shows a dense graph. In March 2021, an average of 201 of 435 possible links was active per week; in March 2025, the average was 183 of 435. That density weakens the claim that co-mention isolates a small set of informative peers. The sample cannot establish post-2020 alpha or absence of arbitrage because it contains no return or pressure observations.

## Gate (c) — power: conditional simulation; Dow remains weak at a 1% rank-IC scenario

The input-only sample contains at least one matched co-mention pair in all 11 observed weeks (5/5 in 2021-03 and 6/6 in 2025-03). This is a small source-coverage check, not an estimate of the probability that a future pressure shock has a usable target. The graph contains 156–246 active pairs in the five 2021 weeks and 96–246 in the six 2025 weeks.

For a planned five-session forward rank-IC series, `r4_harness/power_sim.py` was run with 1,479 daily observations (the development-date count in the prior R5 mechanism manifest), horizon 5, date-level IC autocorrelation 0.20, 2,000 simulations, and the helper’s default null IC SD `1/sqrt(N−1)`. This is a synthetic design calculation, not a data estimate. At a hypothetical mean rank IC of 0.010, simulated probability of reaching Newey–West *t* ≥ 2 was 1.000 for an always-covered S&P 500 cross-section and 0.414 for the Dow 30; the helper’s 80%-power MDEs were 0.00388 and 0.01609, respectively. The simulation’s expected effective date count was 1,075.6 with NW lag 4. The helper output is saved at `r6_data/gdelt_sample/power_sim_outputs.json`.

**Interpretation:** a 1% mean rank-IC assumption would clear the synthetic S&P 500 power check but not the Dow check. The sample here only counted Dow organization matches; no S&P 100/500 GDELT coverage panel was built, so full 500-name coverage is an explicit simulation assumption, not a verified fact. The Dow’s observed dense network and one unmatched constituent make its assumed 30-name cross-section optimistic. Gate (c) is therefore **not passed** for the required Dow test.

## Gate (d) — exact data and observed input coverage: PARTIAL; point-in-time quality and precision unverified

**Source and method.** GDELT describes its data as free/open and provides the official GKG archive index ([GDELT data downloads](https://www.gdeltproject.org/data.html); [official GKG archive index](https://data.gdeltproject.org/gkg/index.html)). Its codebook documents tab-delimited GKG records and organization entities, and warns that the named-entity extractor errs toward inclusion, so organization names can be false positives ([GKG 2.1 codebook](https://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf)). I pulled the official daily GKG archive for every date in 2021-03 and 2025-03: 62 compressed files totaling 1,923,574,466 bytes. The archive records are processed GKG output from the 15-minute stream, preserved in their original compressed daily files.

**Matching rule.** A row is a match when a semicolon-separated `ORGANIZATIONS` entity exactly equals a normalized alias in `company_aliases.csv` (case-fold, remove punctuation and spaces; no fuzzy substring match). The raw rows are deduplicated by source URL within week; a pair is counted once per distinct URL/week if both roster aliases occur in that row. This method is reproducible but is not a precision audit. The roster is point-in-time: March 2021 uses the post-August-2020 Dow roster, and March 2025 reflects Amazon’s 2024 addition plus Nvidia and Sherwin-Williams replacing Intel and Dow in November 2024 ([2021 roster reference](https://www.monash.edu/business/ebs/research/publications/ebs/2023/wp17-2023.pdf); [Amazon replaces Walgreens, Feb. 2024](https://press.spglobal.com/2024-02-20-Amazon-com-Set-to-Join-Dow-Jones-Industrial-Average-Uber-to-Join-Dow-Jones-Transportation-Average); [Nvidia and Sherwin-Williams additions, Nov. 2024](https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20241101-1475162/1475162_djiadjuaintcdowaes.pdf)).

| Sample month | GKG rows scanned | Distinct article URLs with ≥1 exact Dow match | Roster names with ≥1 match | Weeks with ≥1 active pair | Mean weekly active edges / 435 | Mean edge density | Density range |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-03 | 2,196,470 | 85,625 | 29/30 | 5/5 | 201 | 46.2% | 35.9–53.6% |
| 2025-03 | 2,684,950 | 92,450 | 29/30 | 6/6 | 183 | 42.1% | 22.1–56.6% |

Weekly density is `number of distinct Dow pairs with ≥1 co-mention article during that week / 435 possible pairs`; the March 2025 first and last weeks and the March 2021 last week are partial calendar weeks. Full intervening weeks averaged 48.8% density in 2021-03 and 51.1% in 2025-03.

| Week starting Monday | 2021-03 active edges | Density | Week starting Monday | 2025-03 active edges | Density |
|---|---:|---:|---|---:|---:|
| 2021-03-01 | 212 | 48.7% | 2025-02-24* | 115 | 26.4% |
| 2021-03-08 | 231 | 53.1% | 2025-03-03 | 246 | 56.6% |
| 2021-03-15 | 173 | 39.8% | 2025-03-10 | 233 | 53.6% |
| 2021-03-22 | 233 | 53.6% | 2025-03-17 | 194 | 44.6% |
| 2021-03-29* | 156 | 35.9% | 2025-03-24 | 216 | 49.7% |
| — | — | — | 2025-03-31* | 96 | 22.1% |

`*` Partial calendar week inside the requested month; only March dates are included.

**Per-company article coverage.** Full counts are in `r6_data/gdelt_sample/202103_company_coverage.csv` and `202503_company_coverage.csv`. The exact alias matcher found 29/30 firms in each month. MMM/3M had **zero** exact organization-name matches in both months, so it is not in the graph under the frozen alias list. Some other counts are low: Salesforce (CRM) had 8 URLs in 2021-03; Travelers (TRV) 17; in 2025-03, Amazon (AMZN) had 6, Sherwin-Williams (SHW) 21, and Travelers 85. A low count can reflect sparse news, missed naming variants, or entity-resolution failure; it is not evidence of no real-world coverage.

**False-positive and false-negative risk.** Exact-name matching avoids loose substring hits, but it cannot disambiguate an organization named “Apple” from ordinary discussion of apples, “Visa” from immigration visas, or “Travelers” from generic people/travel language if GDELT classified the text as an organization. “Home Depot” is less ambiguous but retail references can still be generic or incorrectly tagged. The project codebook explicitly warns that the organization extractor errs toward inclusion. Conversely, GDELT may miss aliases or use a different registered name; the zero MMM match is a concrete coverage failure under these aliases. No hand-labeled article audit was performed, so precision is unknown and the counts should be treated as upper-bound candidate matches rather than confirmed company mentions.

**Artifacts in `r6_data/gdelt_sample/`.** The 62 source ZIPs are under `202103/` and `202503/`; the downloader/parser is `gdelt_sample_pipeline.py`; URLs and byte counts are in `download_manifest.csv`; matching aliases are in `company_aliases.csv`; matched article URLs and names are in the monthly `*_daily_audit.csv`; company totals are in the `*_company_coverage.csv`; weekly pair totals and densities are in the `*_weekly_pairwise.csv`; full week-by-week pair counts are in `*_pair_counts.csv`; summary counts are in `sample_summary.csv`.

The data are free to download. The sample does **not** verify historical issuer-name mapping for every GDELT article, alias recall, precision against article text, S&P 500 coverage, or full development-period graph stability. Gate (d) is **partially passed** for free-file availability and observed Dow row coverage, but fails the required link-quality/coverage assurance until a separate, predeclared precision audit and complete eligible-week manifest are completed.

## Gate (e) — novelty: modest measurement extension

News co-mention networks and linked-firm return predictability are already in the literature. The incremental contribution would be to form the relation graph strictly from prior-dated GKG entities, then test whether a defined signed buying-pressure shock predicts a later response along those links, with a shuffled-link placebo. That is a test-design and measurement extension, not a new news-network mechanism. The high observed graph density also means the proposal must show that its pressure transmission adds information beyond market, industry, and broad news effects; GDELT’s free access alone is not a novelty claim.

## Decision

**FAIL-GATE.** The two-month pull confirms that GDELT is freely accessible and usually contains multiple Dow names in the same articles, but it also reveals dense graphs, one absent company, low counts for several names, and unresolved entity precision. The synthetic power check is conditional on assumed universe coverage and shows inadequate Dow power at a 1% mean rank-IC scenario. Do not freeze or run this idea until the name matcher has a manually audited precision sample, full-period eligible-link coverage is checked without outcome fields, the wider point-in-time S&P coverage is established, and the Dow power hurdle is credible.
