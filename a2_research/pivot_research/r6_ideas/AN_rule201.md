# R6 Idea Screen AN — Rule 201 trigger pressure to Dow SIC peers

**Overall: STOP — FAIL. Do not register a variant or start a runner.** Rule 201 is a real, discrete constraint: a security that falls at least 10% from its prior close becomes subject to a short-sale price test through the trigger day and the following trading day. Research finds a local positive return effect on trigger securities in one design, while another study reports no clear benefits; neither documents the proposed SIC-peer effect in post-2020 Dow mega-caps. An official Nasdaq trigger file is freely obtainable, but a single-market sample and FINRA’s unsigned short-volume file do not provide the complete point-in-time peer panel; the effect cannot be translated into criterion-4 peer rank IC or portfolio returns.

This is screening only. I calculated no project signal, forward return, IC, portfolio return, or other signal outcome and did not inspect holdout data.

## Identity and immutable-path preflight

- **Proposed short name and mechanism:** AN — a Rule 201 restriction may displace constrained short sellers from a sharply falling S&P 500 issuer into same-SIC2 Dow peers, creating short pressure in those peers over the next session/week.
- **Exact new output path:** `r6_ideas/AN_rule201.md`.
- **Path check:** the exact target did not exist before this screen; this file is new.
- **Development date range:** 2020-11-27 through 2026-10-30. The empirical feasibility checks below used a single date within the development range, 2024-06-03.
- **Input paths:** public SEC/FINRA/Nasdaq information with dates explicitly bounded at read/request time, plus prior idea and planning documents. No input path used pre-2020-11-27 returns or holdout data.
- **No reused name:** no matching output file or prior exact Rule 201 screen was found. The decision registry was not opened because this task forbids reading decision-log outcome lines; any registry-only overlap remains for coordinator review.

## 1. Overlap with prior work

The nearest prior ideas are `D`, which studies daily FINRA Reg SHO short-sale volume, and `L`, which studies short interest/days-to-cover. Their signals describe reported short-sale activity or outstanding positions; Rule 201 instead records an exchange-determined price-test restriction following an extreme decline. The new idea is therefore not the same measure under a new name. However, it is in the same short-sale pressure family, and FINRA’s daily short-sale volume cannot substitute for the trigger status. A targeted search of all `r6_ideas/*.md` and `R5_FINAL.md` found no exact circuit-breaker/SIC-peer signal.

- **Verdict: PASS with material family overlap.** Rule 201 status is a distinct institutional event, but it is adjacent to D/L’s short-flow and short-position mechanisms. The decision registry was not read under the task’s outcome-line restriction.

## 2. Exact pressure measure and dated data source

### Candidate signal, if reconsidered

Form after the Friday trigger-day file has actually been published by the listing market, using a point-in-time set of S&P 500 companies with a new Rule 201 trigger during the completed week. Use the trigger-day record, not a next-day carryover, and retain trigger time if available. Because the file is published after the close, there is no Friday-close trade; the earliest trade is the next full session's open. For a Dow target *j*, define `peer_trigger_exposure[j,t]` as the number of triggered S&P source issuers with the same point-in-time SIC2 code as *j*, divided by the number of S&P source issuers in that SIC2. Exclude *j* itself if it is also a source name. Missing S&P or Dow SIC2 is missing, not zero. The sign hypothesis is **negative**: constrained short sellers unable to execute marketable short orders in the trigger security may substitute into same-industry Dow peers. The proposed outcome is each peer's return over the next five full sessions, beginning with the next session's open after formation.

The signal uses only trigger reports already disseminated by the formation timestamp, plus point-in-time S&P/Dow rosters and SIC2. Rule 201 applies for the rest of the trigger day and the following trading day, unless an exception applies; the trigger itself is determined by the listing market, not inferred from a daily short-volume value. SEC staff guidance states that the trigger test uses eligible regular-hours last-sale prices and that the listing market makes and disseminates the determination. A practical signal cannot use data released after formation; official trigger records are preferable to approximating the rule from daily OHLC lows.

SEC [Rule 201 FAQs](https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions-7) explain the 10% threshold, listing-market determination, and duration. Nasdaq’s [Short Sale Circuit Breaker page](https://www.nasdaqtrader.com/Trader.aspx?id=ShortSaleCircuitBreaker) provides downloadable historical daily files, and its [field definitions](https://www.nasdaqtrader.com/Trader.aspx?id=SSCircuitBreakerdefs) define the trigger-time field. FINRA [daily short-sale volume data](https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files) is a separate product: it aggregates reported off-exchange short transactions, does not identify Rule 201 triggers, and is not consolidated exchange-wide short volume. Listing-market breadth, historical ticker lineage, and SIC2 assignment all require validation.

### What the external evidence establishes

- Barardehi, Bird, Karolyi, and Ruchti, “Are Short-selling Restrictions Effective?” (OFR Working Paper 23-08, 2023), [paper](https://www.financialresearch.gov/working-papers/files/OFRwp-23-08-are-short-selling-restrictions-effective.pdf), [summary](https://www.financialresearch.gov/working-papers/2023/10/11/are-short-selling-restrictions-effective/). The paper’s main sample covers March 2011–March 2013; it reports 5,296 trigger episodes across 1,891 stocks and 5,547 restricted stock-days. Its design compares same-hour stock observations just above versus below the −10% threshold; the authors report about 35 basis points higher daily returns and 8% lower short-sale volume for restricted stocks, with return effects not reversing after restrictions lift. This is an own-stock local threshold estimate using CRSP/TAQ and FINRA short-sale transaction data, not an SIC-peer effect, not a weekly rank IC, and not a post-2020 Dow estimate. The sample’s mean/median market cap and composition are not a substitute for testing the Dow universe.
- Jain, Jain, and McInish, “Short Selling: The Impact of SEC Rule 201 of 2010,” *Financial Review* 47(1), 37–64 (2012), [DOI 10.1111/j.1540-6288.2011.00320.x](https://doi.org/10.1111/j.1540-6288.2011.00320.x). Their daily/intraday analysis before and after Rule 201 reports no clear benefits for valuation, liquidity, execution quality, or stability; they report short sellers are more active before negative returns than after severe declines. It is evidence that the own-stock mechanism is contested, not a peer-spillover estimate.
- SEC Rule 201 itself is a policy rule, not an empirical claim: the restriction limits covered short-sale orders at or below the current national best bid after the listing-market trigger. It does not compel a long purchase or compel short sellers to trade another issuer. The proposed substitution into industry peers is therefore a new, uncertain inference.

- **Verdict: PASS for a precisely defined candidate; FAIL for directly supported peer pressure.** The signal can be defined ex ante, but the source literature does not establish the negative SIC-peer effect.

## 3. Point-in-time coverage and independent breadth

### Cheap development-only feasibility pull

I requested the official Nasdaq daily circuit-breaker file for **2024-06-03** only, at `https://www.nasdaqtrader.com/dynamic/symdir/shorthalts/shorthalts20240603.txt`. The server returned HTTP 200, header `Symbol,Security Name,Market Category,Trigger Time`, and **531 data rows**. Nasdaq documents that the file date is the trade date and that trigger time is when the stock met the covered-list criteria. This verifies that a free, date-specific Nasdaq input exists; it is not a count of eligible S&P issuers, Dow peers, or independent SIC2 events, and it does not cover other listing markets by itself.

As a separate data-semantics check, the public FINRA daily file for the same development date, `https://cdn.finra.org/equity/regsho/daily/CNMSshvol20240603.txt`, returned **9,900 data rows**. I counted rows only and did not output or analyze volume values. FINRA describes these as aggregated reported off-exchange short-sale transactions; this file has no Rule 201 trigger status or trigger timestamp. It cannot measure the event mechanism directly.

| Coverage item | Input-only result | Limitation |
|---|---:|---|
| Official Nasdaq trigger-list dates pulled | 1 date, 2024-06-03 | Not a full development-window panel |
| Nasdaq trigger-list rows on sample date | 531 | Nasdaq source scope only; not 531 independent events or SIC2 clusters |
| FINRA daily short-volume rows on sample date | 9,900 | Not Rule 201 status and not full-market short volume |
| Fully validated S&P source trigger events | 0 verified in this screen | No PIT S&P join was made |
| Dow names with nonmissing peer-trigger score | Not established (30 intended targets) | Requires point-in-time rosters/SIC2 join across trigger sources |
| Independent trigger weeks / SIC2 clusters | Not established | Trigger events cluster by market stress and industry; row counts cannot estimate breadth |
| Staged Rule 201 trigger panel in `r6_data` | None found by filename search | Existing FINRA raw daily files are short-volume files, not trigger status |

The coverage problem is not whether a single free Nasdaq sample can be fetched; it is reconstructing a complete, point-in-time, multi-market trigger panel and joining it to contemporaneous S&P/Dow membership and SIC2. Symbol changes, mergers, ticker reuse, and listing-market coverage can create missed or duplicated issuer events. Trigger events are selected from stocks after a large negative price move and cluster heavily during market stress; source triggers in one SIC2 share common conditions, so their event count is not the effective number of independent observations. The 531 rows on one day cannot be used as event rate or cross-sectional peer coverage.

- **Verdict: FAIL.** One day of Nasdaq records proves basic free-data access, but usable full-universe event-date and independent-SIC2 counts remain unestablished.

## 4. Effective breadth and power at a sourced plausible effect

The most relevant independent magnitude is the OFR paper’s local own-stock estimate (about 35 basis points over the restriction interval in March 2011–March 2013, estimated from same-hour observations around the −10% threshold). It is not the same dependent variable as a five-session Dow peer return or mean cross-sectional rank IC. Jain et al. find no clear overall benefits and do not provide a positive peer effect either. **No published, signal-matched peer effect range exists**, so the evidence cannot be planted into the planned test as an expected effect.

For design sensitivity only, I ran the synthetic-only `r4_harness/power_sim.py` at 30 assets, 312 weekly dates, five-session horizon/NW lag 4, signal autocorrelation 0.2, cluster shape 0.5, 10,000 simulations, seed 20261111, and a planted mean event-date rank IC of 0.074. The 0.074 is the synthetic weekly RankTopHalf criterion-4 planning hurdle at rho=0.2 in `CRITERION4_BOUND_BY_SHAPE.md`; it is not a lockup/Rule 201 estimate. Two event-rate assumptions illustrate sensitivity:

| Assumed event rate | Mean event dates | Mean events over six years | Effective event dates | Power at planted IC .074 for NW t ≥ 2 | 80%-power minimum detectable IC |
|---|---:|---:|---:|---:|---:|
| 0.10 per week (sparse sensitivity) | 27.14 / 312 | 31.19 | 19.74 | 54.4% (MC SE .0050) | .111 |
| 0.80 per week (optimistic market-rate extrapolation) | 118.59 / 312 | 249.66 | 86.25 | 99.0% (MC SE .0010) | .039 |

The optimistic rate is a mechanical upper scenario, not measured Dow breadth: scaling the OFR sample’s 5,296 events over 1,891 stocks and roughly 108 weeks to 30 stocks yields approximately 0.8 events/week, before acknowledging Dow mega-cap selection and the paper’s strong date clustering. The sparse scenario is a sensitivity bound, not a measured trigger rate. The power tool’s event model does not encode SIC2-level common shocks, incomplete market coverage, or errors in membership joins; both rows are unadjusted one-sided NW t≥2 tests, not Holm-adjusted block-bootstrap power. There are at most 30 Dow target names and fewer independent SIC2 groups; the number of groups with actual triggers is unknown. Thus even the optimistic result does not establish useful power at a *sourced peer effect* because no such effect estimate is available.

- **Verdict: FAIL.** Scenario power ranges widely with an unknown event rate, and the only published 35bp effect is an own-stock local estimate. No compatible large-cap peer effect or independent industry breadth supports a confirmatory test.

## 5. Criterion-4 portfolio feasibility first

If reconsidered after a mechanism pass, a weekly long-only portfolio could rank Dow names by **negative** same-SIC2 trigger exposure and hold the top 15 with linear rank weights (active share 55%) versus EW30; 0.05% cost per side. The source portfolio would rebalance weekly; measured turnover is unavailable, and the synthetic bound’s 116% weekly turnover at rho=0.2 would require a 50% cap, which may materially attenuate sparse-event exposure. Its annual cost estimate is 24.1% of gross active edge if the edge exists. The project’s fixed criterion remains positive net excess return, Sharpe above EW30, and one-sided block-bootstrap evidence after Holm; this screen does not relax it.

The criterion-4 planning note gives **0.074 weekly RankTopHalf IC** at rho=0.2 and 0.083 at rho=0.5 (80% power under its first-step Holm approximation for a 24-endpoint family). The OFR estimate cannot be translated to a cross-sectional peer rank IC or long-only Dow portfolio excess return because it concerns restricted trigger securities, not their SIC peers. No defensible peer portfolio excess return or Sharpe range can therefore be supplied; assigning the own-stock 35bp effect to industry peers would be an unsupported assumption. The event-style signal is also a sell-pressure/short-substitution hypothesis, so long-only implementation would require successfully avoiding affected peers rather than receiving direct buying pressure.

- **Verdict: FAIL — criterion-4 feasibility is unsupported.** There is no evidence that the peer effect clears the 0.074–0.083 IC hurdle after turnover limits, 0.05% per-side costs, bootstrap dependence, and Holm adjustment.

## 6. Holdout availability and protocol

No holdout-specific input was needed, and no sealed values were accessed. This screen does not establish holdout availability. Any later holdout work is coordinator-controlled under goal criterion 5, after all development gates pass and the design is frozen; only its permitted availability-only check may be done before that stage. No pre-2020-11-27 market data were requested or loaded.

- **Verdict: PASS for this screen’s no-holdout rule; availability remains unverified.**

## Final screen decision

**Overall: STOP — FAIL.** Rule 201 creates a genuine, short-lived restriction on the trigger issuer, but it neither forces a purchase nor directly constrains same-industry peers. Existing studies offer conflicting own-security evidence, no post-2020 Dow mega-cap peer estimate, and no verified complete multi-market SIC2 panel; sparse-event power and the after-cost portfolio hurdle therefore cannot be established. Do not authorize a preregistration or runner from this screen.

Evidence that could change the decision would include a complete, point-in-time multi-listing-market trigger file for the development window; verified S&P/Dow/SIC2 joins and independent event-cluster counts; and external evidence or a separately authorized mechanism study establishing a peer effect with plausible magnitude sufficient for the unchanged criterion-4 hurdle.

**Reviewer/date:** dispatched worker screen, 2026-11-11.

## Sources

- SEC, [Rule 201 FAQs](https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions-7).
- Nasdaq Trader, [Short Sale Circuit Breaker archive](https://www.nasdaqtrader.com/Trader.aspx?id=ShortSaleCircuitBreaker), [field definitions](https://www.nasdaqtrader.com/Trader.aspx?id=SSCircuitBreakerdefs).
- FINRA, [Daily Short Sale Volume Files](https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files), [Short Interest — What It Is, What It Is Not](https://syndication.finra.org/content/short-interest-what-it-what-it-is-not).
- Barardehi et al. (2023), [OFR Working Paper 23-08](https://www.financialresearch.gov/working-papers/files/OFRwp-23-08-are-short-selling-restrictions-effective.pdf).
- Jain, Jain & McInish (2012), [“Short Selling: The Impact of SEC Rule 201 of 2010”](https://doi.org/10.1111/j.1540-6288.2011.00320.x).
- Project design-only references: [`CRITERION4_BOUND_BY_SHAPE.md`](../report_drafts/CRITERION4_BOUND_BY_SHAPE.md), [`power_sim.py`](../r4_harness/power_sim.py).

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
