# R6 Idea Screen AH — Treasury-auction demand pressure into rate-sensitive Dow stocks

**Status: SCREEN ONLY — no signal outcomes, return calculations, or variant authorized. Overall verdict: STOP — FAIL.** Treasury issuance can create short-lived price pressure in Treasury securities, and independently identified Treasury supply shocks affect aggregate equity prices. But the published evidence does not establish a post-2020 cross-sectional rank IC for rate-sensitive mega-cap stocks, while the development-only long-end-auction sample falls to 29 separated event episodes after the required warm-up and clustering. The data source is accessible; evidence for a criterion-4 tradable Dow edge is not.

## Identity and immutable-path preflight

- **Short name and mechanism:** AH Treasury auction demand. Weak demand at a long-maturity Treasury auction may push yields up; Dow names with higher prior yield sensitivity should respond more than other constituents, transmitting bond-market pressure across assets.
- **Exact new output path:** `r6_ideas/AH_treasury_auction.md` only.
- **Target-path check:** this exact file did not exist before authoring. No existing file was replaced.
- **Prior-name and decision check:** decision 190 assigned the AH Treasury-auction screen; no prior direction is named AH. Relevant overlap is documented in Gate 1.
- **Development date range:** 2020-11-27 through 2026-10-30. The Treasury API request itself was restricted to auction dates from 2020-11-27 through 2026-10-30; the Dow component Parquet scan used a read-time date filter for the same interval.
- **Holdout and path check:** no worker input or output path points to sealed holdout data. The literature's older sample periods are cited as published evidence, not project input files.
- **Ambiguity:** “auction cycle” can mean predictable calendar pressure or a surprise in realized auction demand. This screen fixes the proposed measure to a same-day bid-to-cover surprise, observed only after auction results are released; it does not treat the known auction calendar itself as a surprise.

## 1. Overlap with prior work

| Nearest prior direction | Prior question | AH distinction and overlap |
|---|---|---|
| `r6_ideas/U_crossasset.md` and R5 D6 | Monthly Treasury-basket price trend predicting SPY, with own-index trend controls | AH uses auction-level demand surprise, not bond-basket momentum, and tests cross-sectional Dow response conditional on prior stock sensitivity to yields. Both are Treasury-to-equity transmission ideas, so the economic family overlaps. |
| R5 index/ETF-flow feasibility screens and `R5_FINAL.md` | Primary-market ETF creations/redemptions and index flows | AH uses official Treasury auction demand, a different market and source. It still tests a common external funding/supply shock spilling into equities. |
| `r6_ideas/AG_flowday_reversal.md` | SPY/DIA volume-tail days and Dow residual reversal | AH's trigger is Treasury bid demand, not ETF volume, and its signal is yield sensitivity rather than event-day residual losers. Both are event-conditioned cross-asset pressure proposals. |
| `r6_ideas/AD_fomc.md` | FOMC-window premium sorted by stock beta | AH is a Treasury issuance event, not a monetary-policy announcement; its beta is to Treasury-yield changes. Both use exposure-sorted Dow responses to a scheduled macro-financial event. |

The candidate is not a renamed D6 trend: the event source and cross-sectional exposure design differ. It is nevertheless a close conceptual neighbor of the previously screened Treasury and macro-event directions. As no prior direction has demonstrated a passing development mechanism, the overlap alone is not a rescue or evidence of an edge.

**Verdict: PARTIAL / FAIL for novelty.** The auction-demand interaction is distinct at the signal level, but it remains inside the existing Treasury/cross-asset family and shares its central identification challenge.

## 2. Exact pressure measure and dated data source

If reconsidered, freeze this single design without parameter search:

1. Keep only original 10-year notes and 20- and 30-year bonds (`reopening=No` in Treasury's exact-term records; do not mix reopenings with different remaining-term labels). For auction (a), define weak demand as the negative within-tenor standardized log bid-to-cover ratio: `weak_a = -z(log(BTC_a))`, with mean and standard deviation calculated from the prior 12 completed auctions of the same exact term, excluding auction (a). The warm-up starts at the permitted development boundary; no pre-2020-11-27 auction contributes to this baseline.
2. For each Dow name (i), estimate `beta_i,a` by OLS of its daily close-to-close return on the daily change in the 10-year Treasury yield over the prior 252 completed sessions. Both series are restricted to observations on or after 2020-11-27 and strictly before the auction result is observable. The candidate score at the auction result is `score_i,a = weak_a × beta_i,a`. The pre-specified expected sign is positive: a weak-demand shock raises yields, so stocks with a more positive prior stock-return/yield-change beta should outperform stocks with a more negative beta. This is an exposure-based inference, not a result reported by the papers below.
3. Use the point-in-time Dow roster at the next open and enter no earlier than that open. Predict each stock's next five-session return from the entry open to the close on session five, relative to the same-event EW30 basket. The primary mechanism statistic would be the positive mean daily/event rank IC across usable auction events; average any multiple event-date ICs within each seven-calendar-day episode before testing, use a five-session NW lag for the unclustered planning reference, and use an event-week block procedure in the frozen test. Multiple 10-, 20-, and 30-year auctions within seven calendar days form one auction episode for the screen's effective-breadth calculation.

The source is the U.S. Treasury's [TreasuryDirect Auction Query](https://www.treasurydirect.gov/auctions/auction-query/) and its machine-readable [Fiscal Data Treasury Securities Auctions endpoint](https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query). TreasuryDirect documents filtering by security and date and exporting query results; its query help identifies bid-to-cover and bidder information among available columns. The public API is free and needs no credential for this query. It provides auction dates, terms, reopening status, and results fields, but its historical result table is not an immutable vintage archive; a later test would need to preserve source timestamps and original announcements/results to document exactly when each field became observable. The candidate requires no licensed holdings file.

The auction coverage pull queried only `auction_date, security_type, security_term, reopening, record_date`; it did **not** request or inspect bid-to-cover, bidder shares, auction yields, Dow price/return fields, or any signal/outcome. The endpoint was filtered before retrieval to `auction_date:gte:2020-11-27,auction_date:lte:2026-10-30`. The DGS10 source was requested with the same start and end bounds, and no yield values were printed or used in a calculation. No worker market data before 2020-11-27 was loaded. Source access is therefore established for the dated auction calendar and yield-input dates, while the required signal values and their release-time audit remain untested.

**Verdict: PARTIAL.** A demand surprise can be defined from public auction results, and the required timestamp can be respected by delaying entry until the next open. But no bid-to-cover or other auction-result values were read for this screen, the archived results do not themselves prove original release timestamps, and the stock-yield exposure has not been computed.

## 3. Point-in-time coverage and independent breadth

The Treasury auction API returned 2,539 records (including bills) for the date-filtered window, with 1,156 distinct auction dates overall. For notes and bonds, there were 637 records on 552 distinct dates: 482 note records and 155 bond records. The proposed original nominal 10-, 20-, and 30-year auctions (`reopening=No`) contain 87 records on 87 dates: 35, 23, and 29 records by term, respectively. After excluding each term's first 12 within-window observations for the trailing demand baseline, 51 dates remain (23 ten-year, 11 twenty-year, and 17 thirty-year); merging dates no more than seven calendar days apart leaves **29 event episodes**, from 2023-01-19 through 2026-08-19.

For issuer roster coverage, `r6_C1/dow_components_dev.parquet` was scanned through PyArrow with a predicate requiring `date >= 2020-11-27`, `date < 2026-10-31`, and `date` equal to one of the eligible auction dates. Only `date` and `ticker` columns were selected. All 51 eligible auction dates have 30 roster rows; the un-warmed subset has 87 of 87 dates with at least one row and 79 with all 30 names. The eight incomplete dates all occur in December 2020, before the term-specific 12-auction warm-up would allow a signal. The filtered Dow file spans 1,488 development dates and 33 historical tickers overall; no price values were inspected for this screen. These are coverage counts, not evidence that yield betas can be estimated accurately or that all observations have appropriate PIT weights.

| Input-only breadth check | Result | Interpretation |
|---|---:|---|
| Treasury auction records, all security types | 2,539 | API records date-filtered to the development window; no auction-result values requested |
| Note/bond records / unique auction dates | 637 / 552 | Broad coupon-auction calendar coverage |
| 10/20/30-year records / dates | 87 / 87 | Candidate long-end source dates |
| Events after prior-12-same-term warm-up | 51 | Warm-up entirely inside development-only boundary |
| Seven-calendar-day non-overlapping episodes | **29** | Effective event breadth used for power planning |
| Eligible dates with complete 30-name Dow roster | 51 / 51 | Only identifiers and dates read at those dates |
| Complete rosters before warm-up | 79 / 87 | Eight December 2020 dates have one row and are not usable for the full book |
| FRED DGS10 rows / nonmissing dates | 1,546 / 1,482 | Request bounds were 2020-11-27 through 2026-10-30; no yield values used |
| SIC2 event clusters | Not used | Cross-sectional dependence is common exposure to the same Treasury shock; event episodes are the relevant time clusters |
| Nonmissing signal values / signal observations read | 0 / 0 | No bid-to-cover, yield, or stock return values were queried |

The roster is historical, but the screen did not audit constituent change dates, corporate-action/symbol lineage, or the date at which a Treasury result became publicly visible. Prior-12 auction windows and 252-session betas are especially sensitive to reopenings, tenor definitions, missing yield sessions, and any backfilled series. Auctions in the same week share issuance information and market conditions, so 29 episodes should not be treated as 29 independent cross-sections of 30 independent names. There is no need for SIC2 grouping in the proposed beta exposure, but common-event dependence is unavoidable.

**Verdict: FAIL for breadth.** The PIT roster covers every warmed event, but only 29 separated episodes survive before counting serial dependence, and no exposure or auction-demand coverage was verified at the value level.

## 4. Effective breadth and power at a sourced plausible effect

The closest direct Treasury-cycle evidence is Lou, Yan, and Zhang, [“Anticipated and Repeated Shocks in Liquid Markets,” *Review of Financial Studies* 26(8), 1891–1912 (2013)](https://doi.org/10.1093/rfs/hht034). Their U.S. Treasury study reports secondary-market Treasury prices falling before scheduled auctions and recovering afterwards, attributed to dealer risk capacity and slow-moving end-investor capital; the published sample is January 1980 to June 2008 and covers 2-, 5-, and 10-year note auctions. Its return spread is in Treasury securities, not a Dow stock cross-sectional rank IC.

Phillot, [“US Treasury Auctions: A High-Frequency Identification of Supply Shocks,” *American Economic Journal: Macroeconomics* 17(1), 245–273 (2025)](https://doi.org/10.1257/mac.20210243), identifies supply surprises from Treasury futures-price changes around auction announcements in 1998–2020 and reports higher yields and lower aggregate stock prices after supply shocks. That is an important cross-asset bridge, but the sample ends at 2020 and the reported equity effect is aggregate, not a five-session Dow cross-sectional IC conditional on each stock's yield beta. A 2026 New York Fed staff report, [“Intraday Price Pressure and Order Flow Around U.S. Treasury Auctions”](https://www.newyorkfed.org/research/staff_reports/sr1188.html), uses 33 years of intraday Treasury data and reports that auction-day yield pressure reverses after the auction, while the pressure has not increased in recent years as non-dealer demand has expanded. This is counter-evidence to assuming that an old auction premium persists in the modern period.

There is **no sourced plausible mean IC range in the unit required here**. It would be incorrect to convert Lou et al.'s Treasury basis-point effect or Phillot's aggregate stock response into a Dow rank IC. As an explicitly hypothetical planning sensitivity only, I ran `r4_harness/power_sim.py` with 30 assets, 29 seven-day-separated episodes, horizon 5, AR(1) signal autocorrelation ρ=0.20, default null-rank-IC SD `1/sqrt(29)`, 5,000 simulations, and seed `20261111`. The one-sided unadjusted `NW t >= 2` power is 13.2% at mean IC 0.020 and the unadjusted 80%-power MDE is **0.1149**. At **0.074**, a separate external weekly rank-weighted-top-half planning comparator from `report_drafts/CRITERION4_BOUND_BY_SHAPE.md` (not a published AH estimate), power is only **53.4%**. The simulation's mean effective count is 21.1, with NW lag 4; it does not include Holm, a block bootstrap, cross-stock common-event dependence, or the additional uncertainty of yield-beta estimation.

**Verdict: FAIL.** The literature establishes Treasury-market auction pressure and aggregate equity transmission, but supplies no matched post-2020 Dow effect estimate; the planning MDE is larger than the external rank-IC comparator even before familywise error or common-shock dependence.

## 5. Criterion-4 portfolio feasibility first

The coherent portfolio shape would be a dollar-neutral long-short book, buying the five highest event scores and shorting the five lowest, formed only after the official auction result and entered at the next open. It has 100% active share relative to EW30 by the usual long-short definition. A signal is generated only after a 10-, 20-, or 30-year auction; overlapping five-session holdings during clustered auctions would require a frozen exposure cap and an explicit execution rule. Use 0.05% per side on actual turnover and compare net returns with EW30 as required by the goal. Do not count the result-day move because it is known only after the auction result arrives.

The 29 episode count is far below six years of weekly rebalance opportunities, and the relevant effective count is lower again after the simulation's serial-dependence adjustment (about 21). The weekly rank-weighted top-half synthetic hurdle of 0.074 is used only as an optimistic comparator; it is not the exact hurdle for this event-driven long-short book. The synthetic shape audit's long-short hurdle is much larger and depends on its assumed EW30 Sharpe and portfolio-return model. Neither cited Treasury paper reports a Dow-specific effect that can be translated into net long-short excess Sharpe, turnover, or block-bootstrap p after Holm. Replacing all five names at an episode could generate substantial two-sided turnover; no rank transition or return outcome was computed, so it cannot be shown to satisfy the 50% turnover cap or cost-to-gross-edge exception.

For the currently at-least-24-test R6 family, a Holm first-step p threshold is `0.05/24 = 0.00208`; the family may grow. The power simulation above tests only `t >= 2` and is therefore materially easier than the criterion-4 portfolio test. The old treasury price-cycle and aggregate supply-shock estimates are not sufficient evidence for positive net excess return, Sharpe above EW30, and the required Holm-adjusted block-bootstrap result.

**Verdict: STOP — FAIL: criterion-4 feasibility unsupported.** The available independent evidence does not show a sufficiently large, low-turnover Dow cross-sectional effect, and the synthetic sample is too small to support a confident portfolio claim.

## 6. Holdout availability and protocol

This screen needed no holdout path or holdout-specific input; no sealed file was opened, read, downloaded, or queried. If a future coordinator decision ever authorizes a test after all gates pass, the coordinator-controlled frozen-code run would follow goal criterion 5, once only, against the sealed 2010-01 to 2020-10 Dow panel with point-in-time roster and the required available-name EW30 benchmark. L4 may establish availability only by roster and row counts before any user-approved substitute decision; it must not calculate returns or signals. This screen authorizes no such test.

**Verdict: PASS for no-access protocol; no holdout test is authorized.**

## Final screen decision

**Overall: STOP — FAIL.** Treasury auctions offer a documented source of bond-market price pressure and supply shocks can affect aggregate equity prices, but neither the modern evidence nor the input-only checks establish an actionable post-2020 large-cap cross-sectional effect. The long-end sample leaves only 29 separated event episodes, a 0.074 illustrative effect has 53.4% synthetic unadjusted power, and the actual criterion-4 effect, turnover, costs, and Holm-adjusted portfolio feasibility are unsupported. Do not preregister or spend a variant on AH.

Evidence that could change the decision would be a point-in-time record of auction demand-release timestamps; independent replication of a five-session Dow yield-beta rank IC after 2020; robust post-2020 auction-pressure persistence despite the recent evidence of weaker dealer pressure; and a cluster-aware simulation showing adequate Holm-adjusted power at an independently sourced matched effect, alongside a turnover/cost design compatible with criterion 4.

Reviewer/date: worker screen, 2026-11-11.

### Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
