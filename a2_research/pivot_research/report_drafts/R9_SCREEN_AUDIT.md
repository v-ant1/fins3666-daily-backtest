# R9 screen-criteria audit

## Finding

**Some screens likely rejected viable research leads, though that does not show they would pass the Dow portfolio test.** Free-data availability and published-effect size were overused as early kill rules. The later bar was severe: expected Dow excess Sharpe around 0.8 at ≤20% monthly turnover and a 0.074 weekly rank-IC planning hurdle. ([specs/r6_decisions.md:98-101](../specs/r6_decisions.md); [specs/r6_decisions.md:196-201](../specs/r6_decisions.md))

## Gates actually applied

| Gate | Wording in the record |
|---|---|
| Distinct thesis / overlap | A prior paper was to support the mechanism, not automatically kill it; the novelty check was a “novelty note,” while overlap and weak identification were still used in screens. ([specs/r6_decisions.md:15-17](../specs/r6_decisions.md)) |
| Data | Screens sought “free, usable inputs,” plus point-in-time coverage and a valid public-availability clock; later files explicitly allowed Alpaca inputs. ([r6_ideas/M_SURVEY.md:39](../r6_ideas/M_SURVEY.md); [specs/r6_decisions.md:176-185](../specs/r6_decisions.md)) |
| Mechanism power / breadth | Mechanism power is estimated on a wider PIT S&P 100/500; “the edge must show in the Dow portfolio.” Event-date dependence still limits effective breadth. ([specs/r6_decisions.md:22-23](../specs/r6_decisions.md); [r6_ideas/Y_seasonal_flows.md:19-27](../r6_ideas/Y_seasonal_flows.md)) |
| Published evidence and cost hurdle | R6’s survey sought post-2010 large-cap evidence around a 0.02 monthly rank-IC comparison; later screens used a large-cap IC ≥0.06 or equivalent weekly spread, against portfolio-shape hurdles of 0.074 weekly / 0.120 monthly. ([r6_ideas/M_SURVEY.md:4,8-12,39](../r6_ideas/M_SURVEY.md); [specs/r6_decisions.md:199-205](../specs/r6_decisions.md)) |
| Fixed sign / timing | Hypotheses had to state an ex-ante sign and information-available formation time; a post-result sign inversion was rejected as non-confirmatory. ([r6_ideas/AE_analyst_ratings.md:29-35](../r6_ideas/AE_analyst_ratings.md); [specs/r6_decisions.md:158-161](../specs/r6_decisions.md)) |
| Independent review | Screens were intended to be cross-red-teamed; some rounds used reciprocal reviews, but at least one direction was designed and red-teamed by the same worker. ([specs/r6_decisions.md:7,28-34,154,158-165](../specs/r6_decisions.md)) |

## Dominant kill gate tally

I coded one primary reason per index row, taking the first binding reason in its short “Main kill reason” summary; bundled and red-team rows count separately, so this is a row tally, not 73 independent hypotheses. The index says it covers 71 screen files and expands bundles into 73 rows; seven frozen directions are separate and not killed in this tally. ([specs/r6_screened_index.md:3-7,82-90](../specs/r6_screened_index.md))

| Primary kill gate | Count | Screen rows assigned to it |
|---|---:|---|
| Overlap / no distinct thesis | 28 | A, A-REDTEAM, AC-priceweight, AF-peer-earnings, AG-close, AH-foreign, AL-exdate, AO-liquidity, AO-windowdress, AQ-funding, B, B-REDTEAM, C, C-REDTEAM, D, E, I, J, K, Q, S4, S5, U-fundflow, W-events, W-highIC, X-comovenet, X-options, Y-seasonal |
| Free/PIT source, coverage, or identification | 24 | AA-highIC, AB, AE-analyst, AE-BJZZ, AI-crypto, AI-quadwitch, AJ-buyback, AJ-supply, AK-passive, AK-sector, AL-Google, AM-lockup, AN-Rule201, AP-popularity, AQ-roll, B4, H, L, N, S6, T-daily, U-COT, U-cross, Z-minute |
| Event count / power | 8 | AC-split, AD-FOMC, AD-taxloss, AG-flowday, AH-Treasury, AM-activist, AN-insider, F |
| Published effect / cost scale | 11 | AA-event, AF-52wk, AP-DTC, G, M, P3, P4, V-recent-lit, Y-news, Z-auction, Z-intraday-mom |
| Sign / timing / confirmatory design | 2 | T-D4R, V-microstructure |

Many index summaries name multiple gates, so these are approximate primary-reason assignments, not proof of viability. ([specs/r6_screened_index.md:9-81](../specs/r6_screened_index.md))

## On-paper calibration of known effects

Strictly applied, literature is a lead, not a pass: it must fit the large-cap horizon, have PIT inputs, support the fixed sign and timing, survive overlap review, and plausibly clear the portfolio hurdle.

| Documented effect | Gate result on paper |
|---|---|
| Short-term reversal | **Fails the full hurdle, but is a viable mechanism lead.** Large-firm monthly reversal evidence exists through 2021, and industry-relative reversals are documented, but the magnitude/horizon is not the R6 weekly SIC2 Dow strategy’s matched estimate. The screen did advance J1 with an honest low-power statement, showing the literature gate was not always absolute. ([specs/r7_effect_sizes.md:20,27](../specs/r7_effect_sizes.md); [specs/r6_decisions.md:60-66](../specs/r6_decisions.md)) |
| Industry momentum | **Fails exact transport / scale; viable for screening.** The log explicitly used Moskowitz–Grinblatt as a monthly low-turnover lead, but the available record does not establish a post-2010 Dow-size, pressure-based effect at the later 0.074/0.120 design hurdle. ([specs/r6_decisions.md:18,199](../specs/r6_decisions.md)) |
| Post-earnings drift | **Fails current large-cap effect scale.** R6 had an available SEC earnings clock, but the effect-size review says no comparable post-2010 large-cap post-release drift estimate was found and cites attenuation for large firms. ([specs/r7_effect_sizes.md:21,27](../specs/r7_effect_sizes.md); [specs/r6_decisions.md:67-73](../specs/r6_decisions.md)) |
| Analyst revisions | **Fails free-source observability; not the economic idea.** A signed, timely upgrade/downgrade signal is distinct and plausible, but Alpaca news did not expose normalized rating-change fields; FactSet/I/B/E/S access was treated as unavailable to workers. ([r6_ideas/AE_analyst_ratings.md:19-37](../r6_ideas/AE_analyst_ratings.md); [specs/r6_decisions.md:4,10,101](../specs/r6_decisions.md)) |
| Short interest | **Fails PIT history and matched effect scale, not sign plausibility.** Published work supports a negative relation for high short interest / DTC, including larger stocks in older samples, but the free all-listed historical panel was not established; the log expressly left the path open if licensed data were supplied. ([r6_ideas/L.md:22-31,38-40](../r6_ideas/L.md); [specs/r6_decisions.md:73,101](../specs/r6_decisions.md)) |
| 52-week high | **Fails novelty / exact scale, while remaining a viable predictor lead.** Published work supports momentum and recent conditional continuation among high-turnover/high-price-to-high names; it does not establish an unconditional post-2020 Dow pressure effect at the fixed hurdle. Daily OHLCV is observable. ([r6_ideas/AF_52wk.md:15-21,35-39](../r6_ideas/AF_52wk.md)) |
| Overnight returns | **Fails exact horizon / durability.** Published large-cap evidence is material, but the summarized result uses year-long signal and holding periods and has conflicting evidence; it is not a matched weekly Dow pressure estimate. ([specs/r7_effect_sizes.md:22,27](../specs/r7_effect_sizes.md)) |
| Turn-of-month | **Fails the stock-ranking and event-breadth gates.** Papers support a month-end mechanism in liquid stocks, but not which Dow name should outperform; 72 monthly events remain 72 common shocks, not 500 independent event replications. ([r6_ideas/Y_seasonal_flows.md:21-27,35-39](../r6_ideas/Y_seasonal_flows.md)) |

## Gate verdicts and reasonable relaxations

| Gate | Verdict | Evidence and practical relaxation |
|---|---|---|
| Free data only | **Too strict for discovery.** The log recognizes UNSW FactSet/I/B/E/S/Compustat as paths still open, yet early worker inability to complete an interactive login blocked those ideas. Let licensed sources qualify when access is available through UNSW; assess permissions, history, PIT timestamps, and coverage separately before registration. ([specs/r6_decisions.md:4,73,101](../specs/r6_decisions.md)) |
| Published large-cap effect above cost hurdle | **Too strict as an idea filter; appropriate as a portfolio go/no-go.** Requiring a directly matched published effect at or above the 0.074/0.120-style threshold excludes established mechanisms whose papers use different universes or outcomes. Keep a clear evidence grade and transfer gap; allow a low-cost, one-variant mechanism screen when the literature supports the sign and the data/power are adequate, then preserve the portfolio bar. ([specs/r6_decisions.md:63,98,199-205](../specs/r6_decisions.md); [specs/r7_effect_sizes.md:27](../specs/r7_effect_sizes.md)) |
| Dow-only vs S&P event power | **Too strict if Dow-only counts were used for mechanism power; event-date clustering remains appropriate.** The coordinator corrected mechanism estimation to PIT S&P 100/500, with Dow portfolio proof separately. For common shocks, the independent dates—not the stock count—still govern power. Pool S&P breadth, cluster by date/industry, retain the Dow portfolio test. ([specs/r6_decisions.md:14,22-23](../specs/r6_decisions.md); [r6_ideas/Y_seasonal_flows.md:19-27](../r6_ideas/Y_seasonal_flows.md)) |
| Overlap | **Appropriate in principle, inconsistent in use.** Overlap should prevent duplicates and result-driven rescues; the log overturned two Z-round rationales after Alpaca filled data gaps. Compare mechanisms briefly and credit new data or identification when it changes the test. ([specs/r6_decisions.md:16,187-191](../specs/r6_decisions.md)) |
| Sign and timing | **Appropriate.** The post-hoc reversal proposal was rejected because its sign followed a known result; availability timestamps matter for news and filings. Keep a fixed sign/clock, but permit a new independent preregistration where the sign is grounded in literature before outcomes. ([specs/r6_decisions.md:158-161](../specs/r6_decisions.md); [r6_ideas/AE_analyst_ratings.md:31-35](../r6_ideas/AE_analyst_ratings.md)) |
| Same workers propose and judge | **Too loose.** Reciprocal reviews helped, but L2 both designed and red-teamed D4R. Require a reviewer outside the author pair and coordinator adjudication for documented gate disputes. ([specs/r6_decisions.md:154,158-165](../specs/r6_decisions.md)) |

## Most likely wrongly rejected leads

1. **Analyst rating revisions:** distinct signed signal; likely rejected because the proxy lacked fields, while licensed structured ratings may exist. ([r6_ideas/AE_analyst_ratings.md:19-37](../r6_ideas/AE_analyst_ratings.md))
2. **Short interest / DTC:** well-documented sign and larger-stock support; the free-history condition, not the economics, killed it. ([r6_ideas/L.md:22-40](../r6_ideas/L.md))
3. **Industry momentum / linked-firm spillovers:** established monthly mechanism and potentially low turnover, but strict matched-population evidence and overlap interpretation blocked it. ([specs/r6_decisions.md:18,199-201](../specs/r6_decisions.md))
4. **Turn-of-month demand:** strong liquid-stock calendar literature, but only a weak stock-ranking translation; could be retained as a mechanism lead, not presumed a portfolio pass. ([r6_ideas/Y_seasonal_flows.md:35-39](../r6_ideas/Y_seasonal_flows.md))
5. **52-week-high anchoring:** clear public input and published conditional effect; rejected partly for proximity to earlier screens and lack of an exact modern Dow estimate. ([r6_ideas/AF_52wk.md:15-21,35-39](../r6_ideas/AF_52wk.md))

## Suggested limitation paragraph

This audit reviews screening decisions and published evidence only; it does not estimate whether any rejected signal earns returns in the project universe. The index summarizes screen files and sometimes combines several reasons, so the kill-gate tally is a manual primary-reason classification rather than a count of independent tests. Published effects differ in universe, horizon, signal definition, and cost treatment, so their relevance to a Dow portfolio is uncertain. A screen that rejected an idea identifies a research lead, not a strategy that would have passed the portfolio criteria. The results therefore support a more balanced discovery process, but do not establish that the fixed portfolio hurdle should be changed.


