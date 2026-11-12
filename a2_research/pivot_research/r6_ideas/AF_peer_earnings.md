# R6 Idea Screen: intra-industry earnings information transfer

**Status:** SCREEN ONLY — no project signal outcomes, no return calculations, and no variant is authorized by this document.

## Identity and immutable-path preflight

- **Proposed short name:** AF-peer-earnings. An early-announcing firm's earnings-window market-adjusted return is treated as an information/pressure shock that may predict same-sign returns for SIC2 peers that have not yet reported.
- **Exact new output path:** `r6_ideas/AF_peer_earnings.md`.
- **Path check:** this target did not exist before writing; this is the only created or modified file.
- **Name check:** AF is a new filename. The economic direction is not new: K.md already screened the identical early-announcer-to-later-announcer SIC2 transfer as its Direction 2. Frozen K1 is only own-firm announcement drift; the distinction is detailed below.
- **Development window:** 2020-11-27 through 2026-10-30; all EDGAR row counts below were filtered to this interval. No return series, prices, or holdout files were loaded.
- **Data-boundary note:** while reviewing the existing clock QA, I saw a year-level 2020 filing total that combines June–October with November–December. I did not use that aggregate in the analysis below; all reported event counts were recomputed from the event CSV using the exact UTC lower and upper bounds. No pre-window filing rows, prices, outcomes, or sealed-holdout contents were inspected.

## 1. Overlap with prior work

Frozen **K1** is own-firm earnings-announcement return drift: a firm's first full post-acceptance-session abnormal return predicts its own later abnormal return. This proposal instead transfers a source firm's earnings-window return to a different, same-industry Dow firm before the target's own announcement. The constructs and unit of prediction differ.

However, K.md's earlier **Direction 2** is essentially this exact proposal: a first-announcer's first full-session abnormal return predicts five-session abnormal returns of same-SIC2 firms that have not announced. It was screened and marked fail-gate because there was no post-2010 mega-cap support, event-season/SIC2 power was weak, and the cost hurdle was high. It was not frozen or run, so the present document does not repeat a tested result; it does duplicate a previously failed idea screen. **E1** also used SIC2 peers and staged earnings metadata, but its signal was 21-session dollar-volume-weighted close-location value (CLV) pressure and its horizon was monthly. The proposed event return is different from E1's CLV measure, but the industry-network frame and the null E1 mechanism result are relevant caution.

The new wording does not resolve the prior failure: the earliest-announcer return, target-not-yet-announced filter, and SEC acceptance-time clock are the same core proposal as K Direction 2. Calling it AF does not make it novel.

**Verdict: FAIL — the exact signal was already screened and failed its non-outcome gates in K.md Direction 2.** It is distinct from frozen K1 and differs in measure from E1, but is not a new direction relative to the broader prior-screen record.

## 2. Exact pressure measure and dated data source

For source firm `j` with an eligible Form 8-K/8-K/A Item 2.02 acceptance timestamp `a`, map acceptance to the first full regular session whose open is strictly after `a`; exclude filings accepted during regular trading hours because the first tradable session cannot be identified from this clock alone. Define the source shock as that session's close-to-close stock return minus the broad-market return. At that close, for each point-in-time Dow target `i` with the same dated SIC2 and no own Item 2.02 acceptance yet in the current reporting season, the proposed score is the equal-weight average of the latest eligible source shock(s) from the preceding five trading sessions. The positive hypothesis is that higher peer shock predicts higher target market-adjusted returns from the next open through the close before the target's own announcement, capped at five sessions. A frozen test would need a deterministic rule for simultaneous source filings, amended filings, overlapping peer shocks, and target-event truncation before any outcome work.

The staged clock is `r6_data/earnings_clock_sp500.csv`, built from SEC EDGAR submissions metadata and the point-in-time S&P roster. It contains Item 2.02 8-K/8-K/A filings with acceptance timestamp, active ticker and CIK, form, filing/report dates, and SIC/roster lineage is separately staged. SEC submissions are public and free; documentation is at [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces). The clock records SEC acceptance time, not the original public earnings release; release ordering may differ, especially when a press release predates the filing. The historical-price source must be aligned to the same development period, PIT issuer lineage, and 2020-11-27 start. No price or return field was used in this screen.

An input-only streaming pass applied `2020-11-27T00:00:00Z <= acceptance_timestamp_utc < 2026-10-31T00:00:00Z` before counting rows. The filtered slice has **12,397 filing rows**, **597 distinct tickers**, **594 CIKs**, and filings in **25 calendar-quarter clusters touched**; it includes **12,333 8-K** and **64 8-K/A** rows, with **6,622 BMO**, **5,406 AMC**, and **369 intraday** acceptance classifications. These are raw clock rows, not deduplicated issuer-quarter events or matched source-target events.

**Verdict: PARTIAL.** A date-bounded, outcome-free event clock exists and supports a candidate definition, but the acceptance-time proxy is not verified first-public-release time and the overlap/conflict rules have not been fixed.

## 3. Point-in-time coverage and independent breadth

The counts above cover the staged S&P clock, not valid event returns or Dow target windows. The filtered period touches 25 calendar quarters, including partial endpoints; a six-year planning design conservatively uses at most **24 quarter/earnings-season inference clusters**. The previous K screen used **54 S&P SIC2 groups** and **18 Dow SIC2 groups** as planning breadth assumptions. These are not counts of independent event shocks: announcements cluster within SIC2 and earnings season. A date-filtered join of event rows to complete source prices, PIT Dow target membership, dated SIC2, non-announcement status, and five-session pre-target windows has not been made. Consequently usable event dates, matched Dow names per date, nonmissing scores, unique source shocks, and actual independent SIC2 clusters are **unknown**.

This is a serious coverage limitation, not an invitation to use current SIC or current Dow constituents. Item 2.02 metadata misses earnings releases not indexed under that item; amended filings can duplicate events; ticker changes need CIK lineage; after-hours/BMO timing differs; the filing acceptance can lag press-release availability; and price history is not complete for every PIT S&P symbol. K1's input-manifest checks showed that only 687 of 11,041 eligible clock events were Dow events under its own event-time and input rules, but that count belongs to K1's frozen own-firm design and does not establish peer-pair coverage here.

**Verdict: FAIL — there is no measured source-target event coverage or matched independent breadth for this signal.** The 12,397 raw filings cannot substitute for 24 independent seasons or for usable Dow peer events.

## 4. Effective breadth and power at a sourced plausible effect

Ramnath (2002) studies non-announcing firms' and analysts' responses to first-announcer earnings news and reports that early-announcer forecast errors predict subsequent announcers' forecast errors and that incomplete updating is followed by predictable returns in the days after the first report. The paper is *Journal of Accounting Research* 40(5), 1351–1376, DOI [10.1111/1475-679X.t01-1-00057](https://doi.org/10.1111/1475-679X.t01-1-00057). Thomas and Zhang (2008), *Journal of Accounting Research* 46(4), 909–940, DOI [10.1111/j.1475-679X.2008.00294.x](https://doi.org/10.1111/j.1475-679X.2008.00294.x), find the peer-announcement response of late announcers is negatively related to their response at their own earnings announcement, consistent with overreaction and correction. These papers support information transfer but do not establish persistent buying pressure in current Dow names or a transferable rank IC for the proposed exact event score. Their evidence is pre-2010; I found no verified post-2010 U.S. mega-cap study showing this exact transfer survives.

Counterevidence is especially relevant for this liquid universe: Chung, Hrazdil and Trottier (2015), [“On the efficiency of intra-industry information transfers: The dilution of the overreaction anomaly,” DOI 10.1016/j.jbankfin.2015.08.013](https://doi.org/10.1016/j.jbankfin.2015.08.013), report that the Thomas–Zhang overreaction anomaly is specific to an earlier sample and decays as price formation becomes more efficient. Thus the literature supplies no defensible numerical large-cap mean rank IC matching the intended next-five-session target return. Do not treat announcement CARs as this signal's forward IC.

For a transparent synthetic planning check, reuse the K Direction 2 event-season design: 24 quarterly clusters, one IC observation per season, AR(1) correlation 0.50, Newey–West lag 4, `ic_sd = 1/sqrt(SIC2_groups − 1)`, and 20,000 draws. A candidate five-session, top-five Dow book with a 40% total-notional replacement cap, 4% assumed cross-sectional dispersion, and 0.05% cost per traded dollar has a **cost-ratio** IC hurdle of **0.013856** under `r4_harness.phase3.break_even_rank_ic`; this is a design threshold, not a literature effect. `r4_harness/power_sim.py` gives **14.72%** power at that hurdle for 54 S&P SIC2 groups (80%-power MDE **0.11885**) and **12.53%** for 18 Dow SIC2 groups (MDE **0.20985**). Power at a lower undocumented effect would be lower. The synthetic model does not use project returns or signals.

**Verdict: FAIL — event-season clustering leaves low power, and there is no sourced large-cap effect size to support the required test.**

## 5. Criterion-4 portfolio feasibility first

The only plausible long-only shape is a weekly event-driven top-five Dow portfolio, active share **83.3%** versus EW30 when all names are eligible. On each active earnings-season rebalance, permit at most one name replacement: sell 20% NAV and buy 20%, or **40% total notional turnover**, below the 50% per-rebalance cap. At 0.05% per side/total traded notional convention, that replacement costs **2 bp**. Up to 24 active event weeks/year imply up to **48 bp/year** trading costs; to hold costs below one quarter of gross edge, the gross strategy edge would need to exceed **192 bp/year**. The 4% five-session dispersion and 24-event-week count are planning assumptions from the previous K event screen, not measured Dow quantities.

The 24-cluster power design has a 0.013856 cost-ratio IC hurdle but 80%-power MDEs of 0.11885 for S&P and 0.20985 for Dow; the source papers provide no matching post-2010 Dow-scale rank IC or strategy-level return to support a gross edge near 192 bp/year. Thomas–Zhang's correction finding also makes the sign and persistence unstable. Against the existing 21-endpoint Holm family (which would grow if this were registered), six-year dependence, and a block-bootstrap requirement, no expected Dow excess Sharpe or one-sided p-value can honestly be projected from these papers. Criterion 4 requires net excess over EW30, higher Sharpe, and Holm-adjusted bootstrap p<0.05; this screen cannot establish feasibility.

**Verdict: FAIL — criterion-4 feasibility is unsupported and the same cost/power failure was already documented for K Direction 2. Do not commission a portfolio run.**

## 6. Holdout availability and protocol

No holdout path or holdout-specific input is needed or was accessed. Any eventual holdout test would be run once by the coordinator under **goal criterion 5**, only after a frozen approach passes development gates. No availability-only holdout evidence is needed for this failed screen.

**Verdict: PASS — sealed holdout untouched.**

## Final screen decision

**Overall: STOP — FAIL.** This repeats K.md Direction 2, lacks a valid modern Dow effect-size case, has only 25 calendar quarter clusters in the raw clock and no matched source-target coverage manifest, and is underpowered at the already-high turnover-aware cost threshold. It remains a coherent information-transfer hypothesis, but the announcement-return proxy is not direct buying-flow evidence and does not clear the required investment gates.

Evidence that could change this decision would be a genuinely new, independent post-2010 U.S. large-cap study with an effect size reported for this exact five-session transfer measure, plus a fully input-only matched-event/SIC2 coverage report showing enough Dow target opportunities and a power design that clears the frozen threshold without reusing this project's outcomes.

### References

- Ramnath, S. (2002). “Investor and Analyst Reactions to Earnings Announcements of Related Firms: An Empirical Analysis.” *Journal of Accounting Research*, 40(5), 1351–1376. [https://doi.org/10.1111/1475-679X.t01-1-00057](https://doi.org/10.1111/1475-679X.t01-1-00057).
- Thomas, J. K., & Zhang, F. (2008). “Overreaction to Intra-industry Information Transfers?” *Journal of Accounting Research*, 46(4), 909–940. [https://doi.org/10.1111/j.1475-679X.2008.00294.x](https://doi.org/10.1111/j.1475-679X.2008.00294.x).
- Chung, D. Y., Hrazdil, K., & Trottier, K. (2015). “On the efficiency of intra-industry information transfers: The dilution of the overreaction anomaly.” *Journal of Banking & Finance*, 60, 153–167. [https://doi.org/10.1016/j.jbankfin.2015.08.013](https://doi.org/10.1016/j.jbankfin.2015.08.013).
- U.S. Securities and Exchange Commission. [EDGAR application programming interfaces](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).

**Reviewer/date:** dispatched screen / 2026-11-11.
