# Event-driven buying pressure: screened near-misses

**Verdict: no new direction advances.** I ranked the three requested event families by the strength of the published effect that is most relevant to future returns, checked each against the R6 idea inventory and `R5_FINAL.md`, and ran design-only S&P cross-sectional power simulations. Each family either duplicates work already screened in R5/R6 or lacks observable free data for the claimed pressure; none is eligible for another direction under the exclusion rule.

The order below ranks the **literature-supported mechanism**, not an estimated Dow strategy return. No project price outcomes, signal-return calculations, or sealed holdout data were accessed. The local coverage checks use only staged development metadata and event calendars.

## Screening setup

- **Development boundary:** 2020-11-27 through 2026-10-30 for available R6 market inputs. Dividend QA starts at 2020-06-01 and explicitly excludes earlier history; no holdout-era dividend data were inspected.
- **Power design:** `r4_harness/power_sim.py`, 5,000 synthetic replications per case, positive planted mean rank IC = 0.020 (a sensitivity benchmark only), 499 S&P names, 54 SIC2 clusters, and assumed within-SIC2 correlation 0.15. The supplied per-date IC SD is 0.20538, calculated as `sqrt((1 + (499/54 - 1)*0.15)/(54 - 1))`. This is a conservative cluster-mean approximation, not an empirical estimate. I set `horizon=3` (NW lag 2); quarterly disclosures and repeated signals make the assumed dates optimistic for genuinely independent information.
- **Coverage is not signal evidence:** filing counts, dividend dates, and index announcements establish input availability only. They do not test the proposed signals or their returns.

## Ranking

| Rank | Candidate mechanism | Best relevant evidence | Gate decision |
|---:|---|---|---|
| 1 | Dividend reinvestment / dividend-seeking demand | Published dividend-month and mutual-fund “juicing” evidence; closest direct demand mechanism | **KILL — duplicate R1/P1; actual reinvestment flow is not observed** |
| 2 | Index float/share-count reweights | Index demand can move prices, but post-float-adjustment inclusion effects attenuated and historical float events often reverse | **KILL — overlaps R5 index-change and passive-index demand; no free PIT float-change panel** |
| 3 | Issuer buyback execution | Actual open-market buying is a direct pressure source, but the available large-firm result is null and reports are delayed | **KILL — already screened in `M_SURVEY.md`; filing tables do not timestamp executions** |

## 1. Dividend reinvestment and dividend-seeking demand

### (a) Verified papers and effect

Hartzmark and Solomon document positive abnormal returns in predicted dividend-payment months and relate the run-up to demand for dividends, with reversals after ex-dates ([*The Dividend Month Premium*, JFE, DOI 10.1016/j.jfineco.2013.02.015](https://doi.org/10.1016/j.jfineco.2013.02.015)). Harris, Hartzmark and Solomon find mutual funds buy stocks ahead of dividends to inflate reported fund distributions in 7.4% of fund-years, and that “juicing” is associated with larger fund inflows ([*Juicing the Dividend Yield*, JFE, DOI 10.1016/j.jfineco.2015.04.001](https://doi.org/10.1016/j.jfineco.2015.04.001)). A German large-cap study reports a 1.79% cumulative abnormal return over the 45 days before ex-date and monthly strategy alphas of 0.13–0.47%, but its sample ends in 2017 and turnover is about 220–261% per year ([Czaja et al., DOI 10.1057/s41260-021-00215-3](https://doi.org/10.1057/s41260-021-00215-3)). That result is not a post-2020 US Dow effect or a low-turnover DRIP estimate.

### (b) Mega-cap and post-2020 case

The closest implementable proxy would mark a stock as a predicted payer in the coming month using its publicly known prior-year ex-date cadence, then test the return before the ex-date. That is the R1/P1 signal definition, not an independent reinvestment-flow measure.

The mechanism is plausible in large firms because dividend clienteles and mutual funds can trade liquid mega-cap shares before predictable ex-dates. The cited papers do not document a surviving post-2020 US mega-cap alpha, however. Their evidence concerns predicted payer months, dividend-seeking funds, or non-US observations, not measured reinvestment dollars in current Dow constituents. The documented post-ex-date reversal also makes a month-long positive sign an empirical question.

### (c) Power check

For a monthly payer schedule, I used 72 dates, three-month forward returns, autocorrelation assumption 0.80, and the common SIC2 cluster SD described above. The synthetic probability of NW *t* ≥ 2 at a planted IC of 0.020 is **24.2%**; the simulated 80%-power MDE is **0.1086**. These are design diagnostics, not observed power for the dividend signal; they show a 0.020 effect is hard to identify over six years once the SIC2 uncertainty assumption and serial dependence are imposed.

### (d) Free-data feasibility

The staged `r6_data/dividends/QA.md` reports 10,772 ex-date rows from 2020-06-01 through 2026-10-31, 9,786 rows where the issuer was a point-in-time S&P constituent on ex-date, and 2,504 matched Nasdaq payment dates inside the development window. This supports a schedule proxy. The file contains per-share dividend amounts and dates, **not aggregate investor reinvestment orders or DRIP participation**, and payment-date coverage is partial. The earlier history needed to form a safe 12-month schedule is unavailable at the start of development; QA requires those dates to be marked insufficient-history. Thus free data can identify likely payout dates, not the claimed flow shock.

### (e) Novelty, thesis fit, and verdict

Dividend-seeking is a good conceptual fit for buying pressure, but predicted dividend-month timing is already the R1/P1 direction in the R6 materials; Harris et al. is a mechanism supporting that same family, not a distinct signal. A reinvestment-specific flow signal would need DRIP participation or actual reinvestment orders, which the staged data do not contain. **KILL: duplicates R1/P1 and fails the flow-measurement novelty/data gate.**

## 2. Index float and share-count changes

### (a) Verified papers and effect

Shleifer finds positive abnormal returns around S&P 500 inclusion related to index-fund buying, consistent with downward-sloping demand ([*Do Demand Curves for Stocks Slope Down?*, Journal of Finance, DOI 10.1111/j.1540-6261.1986.tb04518.x](https://doi.org/10.1111/j.1540-6261.1986.tb04518.x)). Hrazdil’s study of the 2005 S&P 500 move to float-adjusted weights reports a −1.54% event-week excess return for affected stocks followed by reversal over the next 30 days ([*The Effect of Demand on Stock Prices*, DOI 10.1108/03074350910973676](https://doi.org/10.1108/03074350910973676)). Patel’s later cross-sectional analysis finds that stock-supply measures matter for inclusion effects but specifically notes the reduction after float-adjusted weighting ([*S&P 500 Inclusions and Stock Supply*, Journal of Empirical Finance, DOI 10.1016/j.jempfin.2018.07.004](https://doi.org/10.1016/j.jempfin.2018.07.004)). These findings establish that mechanical demand and available float can matter; they do not establish persistent next-month buying pressure after 2020.

### (b) Mega-cap and post-2020 case

The distinct share-count version would measure each incumbent’s change in index-provider float-adjusted shares (and implied benchmark weight) from the previous public update, then sign the mechanical buy/sell required at the effective date. That series is not the same as adding or deleting an index constituent, but it is still index/passive demand.

The index-fund channel is economically relevant for mega-caps because benchmarked assets trade to maintain weights. But free-float reweighting is designed to represent investable supply, and the 2005 event study finds a short-lived effect that reversed. S&P Dow Jones Indices’ review of additions and deletions from 1995 to 2021 also reports that the familiar inclusion effect attenuated over time, with liquidity one possible explanation ([S&P DJI research](https://www.spglobal.com/spdji/en/research/article/what-happened-to-the-index-effect-a-look-at-three-decades-of-sp-500-adds-and-drops/)). There is no qualifying published post-2020 Dow result here. Incumbent-share float updates could still cause index trades, but event effect sizes and drift after execution are unknown.

### (c) Power check

The available Dow index-change screen has **three independent announcement dates** over the development interval. I used three event dates, horizon three, SIC2 cluster SD 0.20538, and a planted IC of 0.020. The simulator returned **28.1%** NW-*t* detection and an 80%-power MDE of **0.3832**; with only three dates, this power output is not reliable as a pass claim and the MDE is prohibitive. It confirms severe event scarcity. A more frequent float-adjustment series might have more events, but no such point-in-time event history is staged, so assuming one would inflate power without verified coverage.

### (d) Free-data feasibility

The fixed R5 index-change feasibility audit found three DJIA announcement dates (2024-02-20, 2024-11-01, 2026-06-23), versus its fixed minimum of 20, and ruled the Dow index-change direction infeasible before outcomes (`R5_FINAL.md`, `r5_L3/INDEX_CHANGE_FEASIBILITY.md`). The SEC cache offers public filings and XBRL facts; the official SEC APIs document free submissions and extracted XBRL access ([SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)). But outstanding-share facts are not index-provider investable-float factors, and no free point-in-time Dow index-factor history or float-change dates were found among the staged files. The local cache contains 929 SEC submission archive files and 441 10-Q/K filing rows dated in development; that count only demonstrates that disclosure records exist, not that float adjustments can be reconstructed.

### (e) Novelty, thesis fit, and verdict

The mechanical reweighting mechanism is buying pressure and fits the thesis at event scale. However, R5 already screened Dow index-change pressure and found too few independent events, while R6 P4 covers changes in passive index ownership. A separate daily float-factor signal would be technically distinct from constituent addition/deletion, but it remains in the same excluded index/passive-demand family and lacks a verified point-in-time float series. **KILL under the novelty and input-feasibility gates; do not broaden beyond the pre-existing Dow event screen as a rescue.**

## 3. Buyback-execution windows from 10-Q repurchase tables

### (a) Verified papers and effect

Gunn extracts monthly actual repurchase quantities from 10-Q/10-K filings and finds positive abnormal returns for small and medium firms, but **not for large firms**; he also finds filing-date abnormal returns around disclosure ([*Share Repurchases: Market Timing and Abnormal Returns*, University of Chicago repository](https://knowledge.uchicago.edu/records/0hm3v-qx219)). Lee, Park and Pearson report 5-day announcement CARs of 1.19% in 2002–2006 and 1.24% in 2007–2014, but those are announcement responses rather than post-disclosure persistence from measured execution ([DOI 10.1016/j.jcorpfin.2019.101552](https://doi.org/10.1016/j.jcorpfin.2019.101552)). Guest, Kothari and Venkat review evidence on repurchases and caution against treating announced authorization as equivalent to actual buying ([DOI 10.1111/fima.12415](https://doi.org/10.1111/fima.12415)). No cited paper supplies a positive post-2010 mega-cap forward-return effect from an execution window that could anchor an R6 expected return.

### (b) Mega-cap and post-2020 case

The proposed observable would be shares repurchased (or dollars as a fraction of ADV) in the 10-Q/K monthly table, becoming tradable only after EDGAR filing acceptance. That timestamp is when the information is public, not when the issuer bought the shares.

Issuer purchases are direct demand and can be substantial relative to daily volume, so they match the thesis mechanically. Yet the directly relevant large-firm finding is null, and disclosure-date reactions may reflect information about the buyback rather than persistent execution pressure. SEC quarterly tables summarize completed purchases by calendar month after the quarter has ended; a trader can observe the filing but cannot reconstruct the exact execution dates or test only the days on which an issuer was actively buying. The historical literature does not show this survives for mega-caps after 2020.

### (c) Power check

For quarterly filings across six years, I used 24 dates, horizon three, SIC2 cluster SD 0.20538, and planted IC 0.020. Synthetic probability of NW *t* ≥ 2 is **14.7%**, with an 80%-power MDE of **0.1613**. This is not a literature effect estimate; the 0.020 planted value is a sensitivity point. The effective sample size falls to 13.1 under the simulator’s lag-2 dependence adjustment, before accounting for filing clusters or the fact that the underlying repurchases occurred before disclosure.

### (d) Free-data feasibility

The free SEC EDGAR submissions/XBRL APIs are accessible without an API key, and staged local SEC metadata includes 929 submissions archives. A development-date-only metadata count found 441 10-Q/K filing rows across the cache between 2020-11-27 and 2026-10-30. That is a cheap check of filing availability, **not** a parse or coverage audit of issuer repurchase tables. The existing R6 literature screen already concluded that 10-Q/K tables are delayed aggregate amounts and cannot establish daily execution pressure (`r6_ideas/M_SURVEY.md`).

### (e) Novelty, thesis fit, and verdict

Actual buybacks are a literal issuer-buying-pressure mechanism, but `M_SURVEY.md` already screened this exact signal family and found no positive large-firm persistence result. Recasting the same 10-Q/K table as an execution-window event would not create a new data source or execution timestamp. **KILL: duplicate of the R6 buyback screen, with an unresolved measurement delay and no qualifying large-cap effect.**

## Overall decision

No candidate clears all gates (a)–(e). The evidence-based expected Dow excess Sharpe is **not estimable** for all three; assigning a positive numerical value from the cited event studies would confuse short-window event returns with an implementable post-event portfolio. The highest-ranked dividend mechanism is already registered and its staged data observe dates, not DRIP flows. The index and buyback candidates likewise duplicate prior screens or fail the needed input gate. **No new variant is recommended; no outcomes or holdout work should follow from this screen.**
