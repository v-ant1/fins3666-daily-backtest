# R6 idea screen: GDELT news tone and attention

**Status: pre-outcome research and input-feasibility screen.** This document proposes no frozen strategy and authorizes no variant. I used no forward returns, IC outcomes, portfolio outcomes, or holdout inputs; the data review below is limited to development-window GDELT file availability and article-coverage metadata.

## Ranking by expected edge

The rank reflects the size and directness of the mechanism suggested by existing papers, before eligibility. Both proposals fail at least one required gate. Probabilities are subjective chances of a full R6 pass, not estimates from results.

| Rank | Candidate | Gate verdict | Chance of full pass | Main limitation |
|---:|---|---|---:|---|
| 1 | Firm-level pessimistic news tone as temporary selling pressure | **FAIL-GATE** | 1% | Strong conceptual pressure/reversal evidence, but modern Dow tone coverage and stock-level sign are unvalidated; GDELT tone is document-level and may describe fundamentals. |
| 2 | Abnormal firm-specific news volume as attention-driven buying pressure | **FAIL-GATE** | <1% | Free input exists, but Fang–Peress's coverage result is strongest in small/neglected stocks and is an information-recognition effect, not evidence that news volume creates buying pressure in Dow names. |

**Excluded before ranking:** a graph of firms co-mentioned in GDELT articles is already the tested proposal in [B4_REVISED.md](B4_REVISED.md); the earnings-calendar memory-cue mechanism is already in [V_recent_lit.md](V_recent_lit.md). I do not repeat either as a candidate here. The first candidate is also adjacent to P3's attention-driven MAX hypothesis, and the second overlaps its broad attention channel. These overlaps are accounted for in gate (e).

## Common development-only feasibility check

GDELT's public [GKG 2.1 codebook](https://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf) describes document-level average tone (roughly −100 to +100) and extracted organization names. An input-only local sample already covers two full development months: March 2021 has 2,196,470 GKG rows and 85,625 distinct URLs with an exact match to at least one Dow company alias; March 2025 has 2,684,950 rows and 92,450 such URLs. The fixed exact-alias match found 29 of 30 Dow companies in each month; these are candidate matches, not precision-validated company-specific financial stories. I also made a cheap HEAD request for `https://data.gdeltproject.org/gkg/20251017.gkg.csv.zip`, a date inside development, which returned HTTP 200 and a 36,058,967-byte archive. A separate document-search API request was rate-limited (HTTP 429); I relied on the development-window bulk archive feasibility files already staged in `r6_data/gdelt_sample/` for the coverage counts.

This establishes that free article metadata files can be retrieved and contain many Dow-name matches. It does **not** establish full-period usable firm-level tone/volume coverage, point-in-time alias recall, or relevance/precision. Exact alias matches can capture generic references or articles mentioning a company incidentally, while missing aliases can exclude real coverage. The raw article counts below are not pressure signals and were not joined to prices.

## Shared synthetic power check

I ran `r4_harness/power_sim.py` with a 500-name S&P-sized cross-section, 72 monthly observations, a 21-session horizon (NW lag 20), AR(1) 0.20 for date-level ICs, 5,000 simulations, and the default null-rank IC SD `1/sqrt(499) = 0.0448`. With a planted direction-adjusted mean IC of 0.02, `P(NW t ≥ 2) = 0.9084` (Monte Carlo SE 0.0041); at 0.05, power is 1.000. The simulated 80% MDE is 0.01818 and effective N is about 48.97. These are synthetic, iid-cross-section planning assumptions; they do not include SIC2 clustering, sparse coverage, noisy article attribution, or Holm correction. They say only that a given assumed mean can produce a mechanism t-statistic. The project's optimistic portfolio bound is about 0.083–0.089 IC for a Dow top-five long-only book versus EW30 ([criterion-4 audit](../report_drafts/CRITERION4_BOUND_AUDIT.md)); a signal that merely clears the simulated mechanism MDE is far from establishing that tradable hurdle.

## Candidate 1 — firm-specific pessimistic tone as temporary pressure

**Proposed mechanism and sign.** At each month-end, aggregate only articles published before formation that GDELT associates with a point-in-time S&P 500 issuer. A preregistered version could use the month's company-attributed document tone, requiring a minimum article count and excluding ambiguous generic aliases. The literature suggests a negative-tone shock can impose temporary selling pressure. For a single-horizon proposal, use higher prior-month pessimism predicting a **positive** next-21-session return as the hypothesized reversal after that pressure; this sign is motivated by Tetlock's documented downward pressure followed by mean reversion. Do not also test the initial negative-pressure leg as a second horizon without declaring it as a separate endpoint.

### Gates (a)–(e)

**(a) Literature — partial pass.** Tetlock, [“Giving Content to Investor Sentiment: The Role of Media in the Stock Market,” *Journal of Finance* 62 (2007), DOI 10.1111/j.1540-6261.2007.01232.x](https://doi.org/10.1111/j.1540-6261.2007.01232.x), finds that unusually pessimistic Wall Street Journal market commentary predicts downward price pressure followed by a reversion to fundamentals, and extreme pessimism predicts high trading volume. Tetlock, Saar-Tsechansky, and Macskassy, [“More Than Words: Quantifying Language to Measure Firms’ Fundamentals,” *Journal of Finance* 63 (2008), DOI 10.1111/j.1540-6261.2008.01362.x](https://doi.org/10.1111/j.1540-6261.2008.01362.x), find that negative words in firm-specific WSJ/Dow Jones stories forecast lower earnings and brief stock-price underreaction, especially for fundamental stories. The first is market-level sentiment/pressure; the second shows that stock-level tone often carries fundamentals, not a pure demand shock. Neither establishes the proposed GDELT-to-Dow monthly reversal.

**(b) Large-cap and post-2020 survival — fail.** A shared media environment can still make pessimistic stories salient, and the behavioral/liquidity channel is plausible. But both cited samples are historical; neither verifies post-2020 survival in Dow mega-caps. Prominent firms' stories are rapidly disseminated and closely analyzed. In addition, GDELT's average document tone is not a finance-specific sentiment score, and attributing one article-level score to every named company can mix firm-specific news with broad or incidental mentions. No evidence in this review demonstrates a large-cap pressure premium.

**(c) Power — fail at tradable scale.** The common simulation shows 90.84% nominal S&P mechanism power at an assumed IC of 0.02, but this is before cluster, measurement-error, and multiple-test penalties. It reaches the 0.083–0.089 portfolio planning bound only if a much larger effect is assumed; that was not simulated or supported by these papers. Given only 72 monthly observations, an SIC2-aware assessment should be run before any registration, and a qualifying t-statistic alone would not imply criterion-4 feasibility.

**(d) Free-data feasibility — partial.** The development-window GDELT archive and existing two-month input-only samples demonstrate broad coverage and a tone field. But the sample shows only exact-name article matches, not manually verified firm-specific stories or the number of usable articles after a frozen relevance and minimum-count rule. Missing/ambiguous alias coverage for one Dow name per sample month is already visible. Before a preregistration, an outcome-free manifest would need point-in-time aliases, counts by issuer and formation date, missingness, a hand-audited article precision sample, and SIC2/date coverage; the feasibility data here do not establish those gates.

**(e) Novelty and overlap — partial, not eligible yet.** This uses text tone rather than P3's extreme-return MAX, B4's co-mention graph, or V_recent_lit's earnings-calendar memory cue. But it remains in the same broad attention/news family and risks becoming a news-tone overlay on the attention-reversal hypothesis. A genuinely distinct version must show that tone contributes beyond MAX, own-stock reversal, SIC2 and a generic news-volume control, with no post hoc source or dictionary selection. No such incremental mechanism is established at this idea stage.

**Disposition: FAIL-GATE.** Keep only as a research question if a precision-audited article sample and a credible post-2020 large-cap mechanism become available; do not consume a variant now.

## Candidate 2 — abnormal news volume as attention-driven buying pressure

**Proposed mechanism and sign.** Measure the issuer's number of relevant GDELT articles over a completed month relative to its own trailing baseline. The hypothesis is that a surge in attention attracts buying by attention-sensitive investors, temporarily pushes the price up, and predicts **negative** next-21-session returns as the demand pressure fades. This is a conjecture; article volume may instead proxy for genuine information, distress, or scheduled corporate events. A future design would need one article relevance rule and one volume normalization fixed before outcomes.

### Gates (a)–(e)

**(a) Literature — partial / adjacent.** Tetlock (2007, above) finds unusually high or low market pessimism coincides with high trading volume, supporting an attention/volume relation but not firm-level GDELT article counts. Fang and Peress, [“Media Coverage and the Cross-section of Stock Returns,” *Journal of Finance* 64 (2009), DOI 10.1111/j.1540-6261.2009.01493.x](https://doi.org/10.1111/j.1540-6261.2009.01493.x), find that stocks with no media coverage earn higher returns than heavily covered stocks, with the effect stronger for small, high-individual-ownership, low-analyst-following and high-idiosyncratic-volatility stocks. Their evidence concerns coverage and investor recognition, not a sudden news-volume shock causing temporary buying pressure. The papers motivate attention as relevant but do not establish this exact mechanism.

**(b) Large-cap and post-2020 survival — fail.** High news volume may draw new buyers, but Fang–Peress explicitly report stronger results in small and neglected firms, unlike Dow mega-caps. Major Dow issuers have near-continuous coverage, which compresses cross-sectional variation and makes a monthly abnormal-volume denominator noisy. News spikes can be positive or negative fundamental disclosures, so the same count can imply different directions. The reviewed literature gives no post-2020 large-cap evidence for a negative next-month return after a news-count surge.

**(c) Power — fail at tradable scale.** In the same synthetic S&P test, an assumed 0.02 direction-adjusted IC has 90.84% power for `NW t≥2`, but that number ignores sparse/noisy issuer-level coverage and SIC2 dependence. The assumed effect remains far below the Dow long-only planning bound of 0.083–0.089 IC, and the cited coverage premium cannot be converted to this signal's IC. No plausible effect of portfolio-required magnitude is established.

**(d) Free-data feasibility — partial.** The GDELT development-month sample confirms many exact-alias article URLs (85,625 in March 2021 and 92,450 in March 2025) and broad but not complete issuer coverage (29/30 in each month). These are input coverage counts only; they do not show that the articles concern the matched issuer, separate earnings from unrelated news, or provide stable point-in-time volume baselines. The 2025-10-17 bulk archive is available for 36.1 MB by HEAD check. A free-data route exists, but data quality/attribution and full-window coverage gates remain unresolved.

**(e) Novelty and overlap — fail.** This is a news-count feature rather than P3's MAX-return attention signal or B4's network links, but the mechanism is still generic attention-driven demand followed by reversal. Without identified buying activity, article counts do not observe buying pressure; calling them pressure would be a proxy assumption. It substantially overlaps the prior attention family and does not add the network transmission central to Advik's thesis. It fails the substance/novelty gate.

**Disposition: FAIL-GATE.** Do not register a variant absent a distinct pressure identification strategy and a documented large-cap post-2020 case.

## Overall gate verdict

| Candidate | (a) Literature | (b) Mega-cap/post-2020 | (c) Power | (d) Data | (e) Novelty/thesis | Result |
|---|---|---|---|---|---|---|
| Pessimistic tone and reversal | Partial | Fail | Synthetic mechanism pass only; portfolio hurdle unsupported | Partial; no relevance precision | Partial, overlaps attention/news | **FAIL-GATE** |
| Abnormal news volume and reversal | Partial | Fail | Synthetic mechanism pass only; portfolio hurdle unsupported | Partial; broad archive but attribution unresolved | Fail: generic attention proxy, no measured buying flow/network | **FAIL-GATE** |
| GDELT co-mention network | — | — | — | — | Already B4_REVISED | **Excluded as duplicate** |

No direction is ready for a preregistration or outcome test. The free archive makes descriptive research possible, but neither tone nor article counts establish who bought the stock or whether a pressure shock spreads across related firms. The strongest next step, if this family is revisited, is a small outcome-free relevance and alias-precision audit plus a SIC2-aware power check—not a signal or portfolio run.

## Sources and project screens

- [Tetlock (2007)](https://doi.org/10.1111/j.1540-6261.2007.01232.x); [Tetlock, Saar-Tsechansky & Macskassy (2008)](https://doi.org/10.1111/j.1540-6261.2008.01362.x); [Fang & Peress (2009)](https://doi.org/10.1111/j.1540-6261.2009.01493.x).
- [GDELT GKG 2.1 codebook](https://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf); [GDELT data page](https://www.gdeltproject.org/data.html).
- Overlap screens: [P3.md](P3.md), [B4_REVISED.md](B4_REVISED.md), [V_recent_lit.md](V_recent_lit.md), and [V_microstructure.md](V_microstructure.md).
- [Criterion-4 lower-bound audit](../report_drafts/CRITERION4_BOUND_AUDIT.md).

*No outcomes, price values, or sealed data were used. The GDELT manifests and samples are restricted to development dates on or after 2020-11-27.*
