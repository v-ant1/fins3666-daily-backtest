# R6 idea screen: stock-split retail buying pressure

**Status: SCREEN ONLY — no signal outcomes, return calculations, or variant authorization.** The review uses one date-bounded Alpaca split-action query for NVDA in May–June 2024 and one SEC 8-K dated June 2024. It uses no prices, forward returns, signal values, or holdout data.

## Identity and immutable-path preflight

- **Proposed short name:** AC-SplitPressure.
- **One-sentence mechanism:** A split announcement and its effective date may draw attention and lower the nominal share price, enabling a short-lived wave of retail buying and temporary price pressure in large, expensive stocks.
- **Exact new output path:** `r6_ideas/AC_split_pressure.md`.
- **Path and name check:** This target did not exist before drafting; no `AC_split_pressure` screen or existing split-pressure proposal appears in the `r6_ideas` inventory or `R5_FINAL.md`. The coordinator's decision 176 assigned this new family for screening; this screen does not create a registered variant.
- **Allowed dates:** the Alpaca query and SEC filing are both in 2024. Earliest permissible worker data date is **2020-11-27**. No data path or request before that date was used; no holdout path was opened.
- **Preflight verdict: PASS.**

## 1. Overlap with prior work

No earlier `r6_ideas` proposal centers on stock-split events. The closest families are `P3.md` and `Y_news.md` (generic attention), `Z_minute_flow.md` (signed intraday pressure), and `W_events.md` (corporate events, but dividends, buybacks and index changes). The proposed distinguishing mechanism is a dated share-denomination and access shock: the split is a corporate action, fractional trading lets small-dollar investors buy into high-priced names, and an attention event may coordinate those trades. It does not estimate broad news tone, use generic attention ranks, or infer order direction from daily volume.

There is still meaningful overlap with attention and retail-flow work: the hypothesis needs attention to coordinate demand, and existing literature describes retail attention, price pressure and reversal. A split-specific event design is a genuinely different trigger, but a source change or a split dummy alone would not establish distinct buying pressure. The outcome-free screen must ask whether split events supply enough repeated, independent variation for a Dow strategy.

**Gate 1 — PASS at the idea-family level, with a substantial attention-mechanism overlap to address.** This is a new corporate-action trigger rather than a renamed daily attention feature; any future preregistration must keep the event trigger fixed and avoid adding a post-hoc attention filter.

## 2. Exact pressure mechanism and dated sources

### Candidate — split announcement/effective-date attention pulse

The economically relevant information date would be the first SEC filing acceptance timestamp at which an issuer discloses a forward split, not the split-adjusted price or the action provider's later process date. For a future point-in-time test, define an event pulse of one for the issuer from that first public filing through the fifth trading session after split-adjusted trading starts; otherwise zero. The intended direction is positive pressure during that event window, consistent with retail buying, with the pressure expected to be temporary. The filing would provide the announcement clock; Alpaca would cross-check split ratio and ex/effective dates. SEC and Alpaca actions would be joined by CIK/CUSIP and symbol with a contemporaneous identity map, not a current-ticker-only match.

This is a proposed event marker, not an observed signal. No returns, prices, ICs or event-window responses were calculated. A split is a discrete event, not a weekly score for all 30 Dow names; it cannot be filled out as a standard weekly rank signal without a justified tie rule for non-event names.

The [SEC 8-K for NVIDIA filed June 7, 2024](https://www.sec.gov/Archives/edgar/data/1045810/000104581024000144/nvda-20240607.htm) states that the company had announced a 10-for-1 split on May 22, that the amendment became effective June 7 after the close, and split-adjusted trading was expected to start June 10. The report uses Item 5.03 and 9.01, illustrating that SEC filed documents can distinguish an announcement, legal effective time and first split-adjusted trading date. In this example, however, the 8-K is filed after the May 22 public announcement; the filing date is not necessarily the first public-information date. A preregistration would need a defensible and uniform rule for identifying the earliest public disclosure, or treat the filing timestamp as a conservative later timestamp and accept that it misses part of the event response.

The [Alpaca corporate-actions endpoint](https://docs.alpaca.markets/us/reference/corporateactions-1) supports forward/reverse split queries and returns dates such as ex-date and process date. The documentation warns there is no guarantee of corporate-action creation time and provider/processing delays can mean records are unavailable immediately after announcement. Accordingly, the action API is useful to confirm event dates, but it cannot by itself provide a point-in-time announcement signal. Alpaca has not stated a clear historical start for this endpoint in the cited documentation; do not infer holdout coverage from a 2024 response.

**Gate 2 — PARTIAL / FAIL for a ready signal.** SEC and Alpaca can identify the event and execution clock in a 2024 case, but neither source alone supplies a clean, uniform first-public-announcement timestamp. The proposed event pulse also has no cross-sectional signal definition for the non-event Dow names.

## 3. Point-in-time coverage and independent breadth

I made one input-only Alpaca query for `NVDA`, limited to split types and `2024-05-20` through `2024-06-10`; no broader historical query was made. It returned **one forward-split record**. The returned date fields were ex-date 2024-06-10, record date 2024-06-07, payable date 2024-06-10 and process date 2024-06-10; the record did not expose a declaration date. This is consistent with the SEC example's first split-adjusted trading date, but demonstrates that the API result itself lacks the point-in-time field needed for an announcement-time signal.

| Coverage item, bounded to the 2024 example | Count | How obtained / limitation |
|---|---:|---|
| SEC 8-K examples read | 1 | NVIDIA's June 7, 2024 filing only. |
| Alpaca split-action records | 1 | One NVDA forward-split row from the date- and type-filtered query. |
| Issuers represented | 1 (NVDA) | The SEC filing and action row refer to the same issuer; not independent names. |
| Independent split events in sample | 1 | Same 10-for-1 split in two data sources, so the sources do not create two events. |
| Event/formation dates represented | 1 action ex-date (2024-06-10) | One action record only; the SEC filing separately identifies the 2024-06-07 legal effective time and split-adjusted trading expected for 2024-06-10. |
| SIC2 clusters | 1 issuer sector at most; not independently counted | No SIC panel was joined. One event cannot establish cluster breadth. |
| Nonmissing Dow signals / usable weekly dates | Not established | No complete split panel or Dow point-in-time event roster was built. |

These counts are a path/schema check, not a census of 2020-11-27 onward splits. NVIDIA is a single event and not evidence of recurring breadth. Splits can be announced first in press releases, earnings calls, proxy materials or other filings; SEC 8-K timing and item labels vary. Alpaca's action feed may be delayed and does not guarantee announcement availability, while issuer names, CIKs, CUSIPs and tickers can change. Reverse splits must be excluded by a predeclared rule. Any broader screen would need a date-filtered, complete development-only 8-K search plus action-feed reconciliation, with duplicate amendments and split dividends distinguished from forward splits.

The best post-2020 large-cap evidence located is Cboe's [split-market-structure study](https://www.cboe.com/insights/posts/stock-splits-lead-to-split-results-in-trading/). It examines 61 U.S. split stocks since 2020 across cap groups and three mega-caps (AAPL, TSLA, NVDA) available in its study period. Cboe reports an initial raw-share-volume jump in mega-caps, while split-adjusted volume did not show a sustained increase; adjusted mega-cap retail volume rose initially but weakened over later weeks. This is useful evidence that large-cap split events can attract short-lived retail activity, but it is a market-structure report rather than a broad post-2020 monthly return premium, and it does not prove a side-specific net-buying flow in every event.

**Gate 3 — FAIL.** The permitted small sample has one event and one issuer, not enough independent events or SIC2 clusters to support inference or portfolio coverage.

## 4. Effective breadth and power at a sourced plausible effect

Ikenberry, Rankine and Stice, [“What Do Stock Splits Really Signal?” *Journal of Financial and Quantitative Analysis* 31 (1996), DOI 10.2307/2331396](https://doi.org/10.2307/2331396), study 1,275 two-for-one splits and report a 3.38% announcement return, followed by 7.93% first-year and 12.15% three-year excess returns. The authors note managerial selection based on expected future performance. These are historical event-study/calendar returns, not a post-2020 large-cap weekly rank IC or pure retail pressure effect; the long horizon and selection make them unsuitable as a plausible IC for this R6 screen.

Da, Fang and Lin, [“Fractional Trading,” *Review of Financial Studies* 38 (2025), DOI 10.1093/rfs/hhae012](https://doi.org/10.1093/rfs/hhae012), study fractional trading's staggered introduction and report a 7 bp relative-return difference over a five-trading-day window after their attention set is created. That event set combines recent winners, losers and high Google search activity; it is not a split-announcement sample. Their paper provides direct U.S. evidence that fractional trading can intensify temporary pressure in high-priced stocks around attention, but does not give a stock-split-specific estimate or rank IC. Bartlett, McCrary and O'Hara, [“Tiny Trades, Big Questions: Fractional Shares,” *Journal of Financial Economics* 157 (2024), DOI 10.1016/j.jfineco.2024.103836](https://doi.org/10.1016/j.jfineco.2024.103836), use intraday trade patterns and a March 2021–March 2022 sample to identify fractional-like one-share prints and discuss split events as potentially attention generating. They also stress that data/reporting protocols obscure the scale of true fractional trades. Alpaca SIP records do not identify the retail account or fractional component, so these results cannot be treated as a directly observable signal in the available event file.

For a design-only power check, `r4_harness/power_sim.py` was run with 500 names, 312 weekly dates, horizon 5 / NW lag 4, null IC SD `1/sqrt(499)`, AR(1) 0.20, 5,000 draws, seed 20261111, event mode and a deliberately simple assumption of one event date per 52 weeks (about six active event weeks in six years). It returns about **5.85 event dates**, **4.29 effective dates**, and a nominal **80%-power MDE of 0.0608 IC**. At a planted weekly IC of 0.074—the rank-weighted top-half criterion-4 hurdle—it reports nominal `P(NW t ≥ 2) = 91.7%`; at a planted 0.020 assumption, it reports 45.4%. These are synthetic assumptions, not signal results. Event-rate is an illustrative rarity assumption, not estimated from returns or claimed as a full-development count.

This simulator does not apply Holm correction, block-bootstrap dependence, or event/SIC2 clustering and does not address the fact that only one or a few names may split in the Dow. The 7 bp RFS event-set spread is not a rank IC and cannot be converted without unsupported assumptions. Neither the 1996 event study nor the fractional-trading papers supply a directly comparable weekly Dow rank IC. There is therefore no sourced effect to declare adequate at the criterion's confidence level.

**Gate 4 — FAIL.** A synthetic test at the planning hurdle has nominal power, but effective event breadth is tiny and the cited studies do not provide an effect size matched to split events, weekly rank IC and mega-cap Dow names.

## 5. Criterion-4 portfolio feasibility first

The least demanding portfolio shape in [`CRITERION4_BOUND_BY_SHAPE.md`](../report_drafts/CRITERION4_BOUND_BY_SHAPE.md) is a weekly rank-weighted top-half Dow book (`RankTopHalf`), with 55% active share and an approximate 0.074 mean rank-IC hurdle at the study's low-autocorrelation setting. Preserve the benchmark EW30, 0.05% cost per side, active share at least 50%, turnover ≤50% per rebalance or costs below 25% of gross edge, and the one-sided block bootstrap with the growing Holm family. Those are fixed goal conditions, not tunable screen choices.

An announcement/ex-date dummy would be zero for almost every stock-week and ties would dominate the rank ordering. A rare split name cannot supply a persistent ordering of the rest of the Dow. A separate event-window trade could avoid the ties but would still have only a handful of independent events, making six-year Sharpe and block-bootstrap comparisons with EW30 uninformative. Ikenberry's 3.38% announcement return and 7.93% first-year return are not a pressure-only estimate or proof of a net tradable edge; Da–Fang–Lin's 7 bp five-session difference is from a different attention-set design. Neither offers enough to calculate a credible Dow excess Sharpe or gross-to-net cost ratio. Turnover is not estimable from one action event; event-triggered entry/exit could also create turnover spikes rather than the target cap.

**Gate 5 — STOP — FAIL: criterion-4 feasibility unsupported.** No documented split-specific, post-2020 mega-cap effect can be translated into the required weekly rank IC, and the rare-event signal shape is poorly matched to the long-only Dow-versus-EW30 criterion.

## 6. Holdout availability and protocol

No sealed data or holdout-specific paths were used. SEC 8-K records might provide historic split announcements, but no availability census was made outside the permitted window. Alpaca's corporate-action docs give no historical start date and warn of publication/processing delays; do not claim that it supports a clean 2010–2020 point-in-time holdout. Any future availability review or holdout evaluation must be coordinator-controlled under goal criterion 5 and must document any data gap before freezing. No worker should access sealed values for this screen.

**Gate 6 — PASS for screen discipline only.** No holdout inputs were required or used; holdout availability remains unverified.

## Final screen decision

| Gate | Verdict | Reason |
|---|---|---|
| (a) Literature | Partial | Split and fractional-trading pressure is documented, but event and horizon do not match a Dow weekly IC. |
| (b) Large-cap/post-2020 case | Partial | Cboe and fractional-trading papers support temporary retail activity in high-price stocks, but split-adjusted volume fades and not all studies isolate split events. |
| (c) Power | Fail | One staged action record; low effective event breadth; no sourced matched IC. |
| (d) Feasibility | Partial / Fail | One 2024 NVDA record aligns to a dated SEC filing, but Alpaca lacks guaranteed creation time and the 8-K may follow first public announcement. |
| (e) Novelty | Pass with overlap caveat | Split is a new event trigger, but the proposed pressure channel overlaps prior attention and retail-flow ideas. |
| Criterion-4 portfolio gate | Fail | Sparse event flags cannot justify the 0.074 weekly RankTopHalf IC or EW30-relative after-cost Sharpe hurdle. |
| Holdout rule | Pass for this screen | No holdout data read; availability not established. |

**Overall: STOP — FAIL. Do not register a variant or proceed to a portfolio runner.** The mechanism is plausible and has recent large-cap retail-activity evidence, but evidence does not show that split-specific buying pressure is frequent and persistent enough to clear the fixed Dow portfolio hurdle. The best counter-evidence is the temporary megacap retail-volume increase reported by Cboe and the fractional-trade pressure around attention events in Da–Fang–Lin; it does not establish the required split-specific rank IC or avoid the event-breadth and point-in-time timing problems.

**What could change the screen:** a complete, strictly development-date-filtered split-event panel with earliest-public-disclosure timestamps and a predeclared universe could verify whether event breadth is materially larger than the one-example check. Independent research would still need to establish a repeated large-cap, split-specific effect of a magnitude compatible with the weekly hurdle, and a feasible signal definition would need to rank the Dow in non-event weeks without introducing a second, post-hoc mechanism.

**Reviewer/date:** dispatched worker screen, 2026-11-11.

## Sources

- Ikenberry, Rankine & Stice (1996), [“What Do Stock Splits Really Signal?”](https://doi.org/10.2307/2331396).
- Da, Fang & Lin (2025), [“Fractional Trading,” *Review of Financial Studies*](https://doi.org/10.1093/rfs/hhae012).
- Bartlett, McCrary & O'Hara (2024), [“Tiny Trades, Big Questions: Fractional Shares,” *Journal of Financial Economics*](https://doi.org/10.1016/j.jfineco.2024.103836).
- Cboe, [“Stock Splits Lead to Split Results in Trading”](https://www.cboe.com/insights/posts/stock-splits-lead-to-split-results-in-trading/).
- SEC, [NVIDIA 2024 Form 8-K](https://www.sec.gov/Archives/edgar/data/1045810/000104581024000144/nvda-20240607.htm).
- Alpaca, [Corporate Actions API](https://docs.alpaca.markets/us/reference/corporateactions-1).
- Project planning threshold and shape: [`CRITERION4_BOUND_BY_SHAPE.md`](../report_drafts/CRITERION4_BOUND_BY_SHAPE.md); synthetic harness: [`power_sim.py`](../r4_harness/power_sim.py).

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
