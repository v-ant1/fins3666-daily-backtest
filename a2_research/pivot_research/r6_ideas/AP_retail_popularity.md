# R6 screen: retail popularity as buying pressure

**Status: SCREEN ONLY.** This is an input and literature screen, not an outcome test or authorization for a new variant. No project returns, forward outcomes, signal ICs, portfolio results, or holdout data were accessed or calculated.

## Identity and immutable-path preflight

- **Proposed name and mechanism:** AP retail popularity — a firm-specific popularity shock may focus retail investors on a Dow stock, attract marketable buying, and create short-lived price pressure.
- **Exact new output path:** `r6_ideas/AP_retail_popularity.md`.
- **Target absent before writing:** confirmed with a path check immediately before creation.
- **Name and overlap check:** the target name was not present in `r6_ideas/`. The nearest existing screens are `AL_google_trends.md`, `S4-S6.md` (especially S6), and `P3.md`; `Y_news.md` and `AB_alpaca_news.md` are also adjacent attention screens. I did not inspect run-result files, the Holm family, decision-log outcome lines, or `R5_FINAL.md`, to honor the no-outcomes constraint.
- **Development dates and earliest allowed input date:** 2020-11-27 to 2026-10-30; no input request or path predates 2020-11-27. The small API feasibility request was limited to 2024-01-01 through 2024-02-01.
- **Path/date preflight:** this document and the synthetic power tool are the only project files used beyond the cited idea screens and planning audit. No holdout paths were opened.

## 1. Overlap with prior work

- **S6 — Wikipedia page views:** same proposed observable (firm-article attention) and the same attention-induced buying/temporary-pressure mechanism. This is an exact duplicate, not a new signal.
- **AL — Google Trends:** substitutes ticker searches for article views, but it remains a generic attention proxy with the same behavioral path. AL already concluded that proxy substitution does not create a distinct pressure mechanism.
- **P3 — MAX / attention-lottery:** uses extreme returns rather than a popularity count, but tests the same own-stock attention and reversal family.
- **Y_news / AB_alpaca_news:** news volume or story tone can generate popularity spikes; a Wikipedia view series cannot distinguish a retail popularity event from firm news, product news, or controversy.
- **Retail-order measures:** AE screens sub-penny retail order imbalance. Direct retail executions would be a different observable; Wikipedia views are not retail trades, signed order flow, or an ownership count.
- **Verdict: FAIL.** The only free proxy with a dated, daily, broad public history found here is Wikipedia page views, already screened in S6; Google Trends is already screened in AL. Calling either “retail popularity” would relabel an existing attention test.

## 2. Exact pressure measure and dated data source

If the candidate were eligible, a single falsifiable specification would be daily firm-page popularity pressure:

`pop[i,t] = log(1 + views[i,t]) - median(log(1 + views[i,d])) over the prior 56 calendar days`.

The proposed sign would be positive for the next five trading sessions: a positive page-view surprise is hypothesized to attract retail buying. A weekly formation would use the most recent fully reported page-view day at least 48 hours before the Tuesday open, with an eight-week baseline ending before that date. The 48-hour buffer is a conservative design assumption, not a verified historical dissemination timestamp. Wikimedia says daily data can take 24 hours or longer to load and that 404 can mean either zero views or data not yet loaded; therefore, historical API values do not by themselves establish what a live investor saw at the intended formation time ([Wikimedia Analytics API availability and troubleshooting](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/troubleshooting.html)).

The free official [Wikimedia page-view API](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html) provides per-article daily data from 2015-07-01. Counts measure visits to an article, not identified retail traders or signed stock orders. Article-title changes, redirects, ambiguous company aliases, common-title pages, and missing/zero values need fixed handling. The feasibility check below requested only development-window dates. No page-view signal was computed for a full Dow panel, and no return or signal outcome was examined.

The literature supports attention-driven buying in general, but not this free proxy as a tradable, post-2020 Dow flow measure. Barber and Odean, [“All That Glitters: The Effect of Attention and News on the Buying Behavior of Individual and Institutional Investors,” *Review of Financial Studies* 21 (2008), 785–818, DOI 10.1093/rfs/hhm079](https://doi.org/10.1093/rfs/hhm079), use brokerage data and find individuals are net buyers of attention-grabbing stocks, including stocks in the news, with unusual volume, or extreme returns. This documents buying behavior, not Wikipedia-page-view-induced buying.

Barber, Huang, Odean, and Schwarz, [“Attention-Induced Trading and Returns: Evidence from Robinhood Users,” *Journal of Finance* 77 (2022), 3141–3190, DOI 10.1111/jofi.13183](https://doi.org/10.1111/jofi.13183), use Robinhood data and find attention-induced trading is stronger among Robinhood users; intense Robinhood buying forecasts negative returns, with average 20-day abnormal returns of −4.7% for the top stocks purchased each day. The underlying Robintrack population-count series covered May 2018–August 2020, not the development window; the paper’s measured buying is direct proprietary broker data, not a free popularity proxy. The published sign is a reversal after buying, not evidence that a popularity measure predicts positive next-week returns in mega-caps. The Berkeley summary reports herding-day gains followed by negative next-day returns and 20-day losses ([Berkeley Haas research summary](https://newsroom.haas.berkeley.edu/how-robinhoods-trading-app-spurs-investors-herding-instincts-prof-terrance-odean/)).

**Verdict: FAIL for a live, point-in-time buying-pressure measure.** A free attention count exists; it does not identify retail purchases, and its historical publication time is not archived in this screen.

## 3. Point-in-time coverage and independent breadth

- **Cheap development-only input pull:** for five unambiguous company article titles (Apple Inc., Microsoft, Amazon, Walt Disney, and JPMorgan Chase), I requested only `2024010100` through `2024020100` from the Wikimedia per-article daily endpoint. Each returned 32 date-stamped observations from Jan. 1 through Feb. 1, 2024, all with a nonmissing, nonzero count: 160 name-days total, zero missing and zero zeros in this convenience sample. Both endpoints are inside the permitted development window. Counts are input-availability checks only; they were not normalized into popularity signals or joined to stock data.
- **Usable panel coverage:** the five-page sample is not a point-in-time Dow roster panel and does not establish coverage for 30 constituent names across the full development span. Current article titles are not a dated company-identifier crosswalk.
- **Independent events and clusters:** no shock threshold was applied, so no popularity-event count is claimed. Five convenience-sample firms are not five independent events; a usable Dow SIC2 cluster count was not established.
- **Survivorship and selection:** pages were selected to check endpoint behavior, not sampled from historical Dow membership. Firms enter and leave the index; article names, ticker symbols, redirects, and company aliases can change. Events can be driven by product, legal, political, or corporate news rather than investor demand. The sample is too small to quantify these effects.
- **Post-2020 mega-cap case:** the 2008 study establishes that attention can affect retail purchase choices in historical brokerage data. The 2022 Robinhood study shows attention-led retail buying persists in its data, but its reported Robintrack ownership series ends in August 2020, before the eligible development period, and the reported post-purchase effect is negative over 20 days. Neither paper supplies a post-2020 Dow mega-cap estimate for page views.
- **Verdict: FAIL.** Free page-view input is technically reachable, but full point-in-time roster coverage, company-page mapping, event breadth, and retail-flow attribution are unverified.

## 4. Effective breadth and power at a plausible effect

Neither cited paper reports a mean date-level rank IC for a free firm-page-view signal among post-2020 mega-caps. The −4.7% Robinhood statistic is a 20-day abnormal-return result for stocks selected by actual brokerage buying, and it is negative; it cannot be converted into a page-view rank IC without imposing an unsupported map from views to signed orders and from abnormal returns to cross-sectional ranks. Thus there is **no literature-sourced plausible effect in the required metric**.

For a transparent sensitivity only, I ran `r4_harness/power_sim.py` with 308 weekly observations (approximately the eligible window length), five-session horizon, NW lag 4, assumed date-series autocorrelation 0.20, and 5,000 simulations. Since the actual independent breadth is unknown, I report an optimistic 30-name case and a conservative 10-effective-name stress. At an illustrative planted mean IC of 0.0183—which is **not** taken from either paper and is not an estimate—the 30-name case had 31.86% power, Monte Carlo SE 0.00659, effective N 223.99, and 80%-power MDE 0.03526. The 10-effective-name stress had 13.58% power, SE 0.00484, effective N 223.99, and MDE 0.06329. These simulations test only the harness’s assumed synthetic date-level IC series; they do not account for article mapping error, actual industry dependence, or Holm correction.

The lack of a matched literature effect is already a gate failure. Even the illustrative 0.0183 effect is well below the roughly 0.074 weekly rank-IC planning bound for a 55%-active-share RankTopHalf design in the synthetic criterion-4 shape audit; the 0.074 is a conditional planning result, not a universal mathematical minimum ([Criterion-4 bound by portfolio shape](../report_drafts/CRITERION4_BOUND_BY_SHAPE.md)).

- **Verdict: FAIL.** No sourced effect matches signal, horizon, universe, or sign; the labeled sensitivity case is underpowered and below the portfolio planning bound.

## 5. Criterion-4 portfolio feasibility first

- **Hypothetical portfolio:** weekly RankTopHalf long-only book, 15 Dow names with linear rank weights, 55% active share versus EW30; 0.05% per dollar traded on each side. No signal ranks or trades were generated.
- **Turnover and costs:** the shape audit’s weekly `RankTopHalf`, at assumed score autocorrelation 0.20, has 116% average total-notional turnover. The audit’s assumed cost-to-gross-edge ratio at its 0.074 IC bound is 24.1%, barely inside the rule allowing turnover above 50% only when costs are below one quarter of gross edge. These are synthetic shape assumptions, not observed strategy turnover or a predicted return.
- **Effect translation:** no page-view rank-IC estimate or expected active-return distribution is available to translate. The Robinhood paper’s −4.7% 20-day abnormal return is based on direct, intense buying and goes in a reversal direction; it is neither a page-view effect nor an estimate for a top-15 Dow portfolio. The 2008 attention paper reports purchase-choice evidence, not a portfolio premium.
- **Criterion-4 verdict: FAIL.** The only comparison available is a 0.074 planning IC bound, while the signal has no evidence-supported effect estimate and is an exact overlap with S6/AL. This is not a basis for portfolio testing; do not proceed to a runner or variant.

## 6. Holdout availability and protocol

No holdout path, data, or holdout-specific input is needed for this screen. The sealed 2010–2020 Dow panel and all pre-development values remain unopened. If a direction ever clears the development gates, the coordinator-controlled holdout protocol in goal criterion 5 would require the frozen one-time run on the point-in-time Dow roster, with an availability-only scout first; this failed proposal does not request or authorize that work.

- **Verdict: PASS for respecting the holdout rule.** No holdout values were accessed.

## Final screen decision

**Overall: STOP — FAIL.** The free page-view series is measurable, but it is already the exact S6 attention proxy; Google Trends is the same mechanism screened in AL. Moreover, neither literature effect is a sourced positive post-2020 Dow mega-cap rank IC, and the direct Robinhood-buying result is a subsequent reversal measured on proprietary brokerage data. No variant is proposed or authorized.

Evidence that could change the decision would be an ex-ante distinct popularity/retail-flow measure with a freely available point-in-time 2020-11-27 onward history, a post-2020 mega-cap effect estimate in a compatible rank-IC metric, and a preregistered design that clears both the power and criterion-4 cost hurdles without duplicating existing attention screens.

Reviewer/date: Orca worker, 2026-11-11.
