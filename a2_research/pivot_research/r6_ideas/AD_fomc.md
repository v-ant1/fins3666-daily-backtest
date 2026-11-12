# R6 idea screen — AD FOMC pre-announcement exposure

**Status: SCREEN ONLY. Overall: STOP — FAIL.** No project signal values, forward returns, ICs, or portfolio outcomes were calculated. The only project-date boundary considered is 2020-11-27 through 2026-10-30; no earlier project data or holdout values were accessed.

## Identity and immutable-path preflight

- **Short name and mechanism:** AD-FOMC exposure. A market-wide pre-FOMC return premium, if it persists, could create cross-sectional relative returns among Dow stocks proportional to their pre-estimated market beta; beta is an exposure map, not a direct measure of buy flow.
- **Exact new output path:** `r6_ideas/AD_fomc.md`.
- **Existence/name check:** the exact path did not exist immediately before this write. Search of `r6_ideas/*.md`, `R5_FINAL.md`, and `specs/r6_decisions.md` found no previous FOMC pre-announcement beta-sorted Dow idea.
- **Development period / earliest allowed worker data date:** 2020-11-27 to 2026-10-30; 2020-11-27. Older dates below refer only to published papers, not project data.
- **Path/data check:** this screen uses the published Alpaca audit and input inventories for feasibility; it reads no earlier project-date rows, no holdout path, and no return or signal columns. No project data pull was made.
- **Ambiguity:** a future test must freeze whether an event is an ordinary scheduled statement meeting and exclude unscheduled meetings; the proposal below fixes that rule. This does not change the screen verdict.

## 1. Overlap with prior work

The nearest screened directions are the cross-asset FOMC cycle or Treasury-pressure proposals in `r6_ideas/U_crossasset.md`, the monthly Treasury trend proposal D6, and generic beta/factor tilts in earlier R5 work. Those ask whether Treasury or other asset prices/flows predict equity returns, or hold broad beta/trend exposures over ordinary periods. This screen instead isolates the scheduled 24-hour pre-announcement window and tests whether a **pre-estimated stock-level beta exposure** maps a previously documented market-wide calendar premium into relative returns. The beta sort is proposed only for the pre-event window, is not a Treasury signal, and does not use a beta estimated from the event's return.

This is a distinct timing hypothesis, but its distinction is mainly the event condition and beta exposure. It does not measure actual buying pressure, and it is not the direct stock-level pressure mechanism required by Advik's thesis. The 2019 FOMC-cycle paper is also adjacent rather than the same daily event-window signal.

**Overlap verdict: PASS on exact prior-signal duplication; FAIL on thesis fit (see below).**

## 2. Exact pressure measure and dated data source

### Frozen candidate definition for screening

Use scheduled FOMC decision announcements listed on the Federal Reserve's public [meeting calendars](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm); omit unscheduled emergency announcements. For event date `d`, define each stock's exposure as a trailing ordinary-least-squares market beta estimated from its 252 most recent daily close-to-close returns, ending on the last completed session before the start of the pre-announcement window. Rank the point-in-time Dow constituents by beta, with higher beta expected to outperform. The same definition would be evaluated first in the point-in-time S&P 500 with SIC2-relative ranking/controls.

The historical paper's core window is 2:00 p.m. ET on the trading day before the scheduled announcement to immediately before 2:00 p.m. ET on announcement day. In a later authorized implementation, exposure is known before entry: form the rank at the previous-session close using beta data ending before that close, enter at the 2:00 p.m. bar open on the previous trading day, and liquidate before the announcement-day 2:00 p.m. release bar. Exclude meetings whose date/time is not on the scheduled calendar. Use SIP minute bars for timestamped execution boundaries; official Fed calendars define the event timestamp. Only bars dated 2020-11-27 through 2026-10-30 could be used by this project.

This is an **exposure-to-common-premium** design, not a measured signed-flow score. No data in the staged bundle identifies buyer-initiated trades or investor flow during this window. Beta may also load on ordinary market risk, so a cross-sectional relation would not by itself establish causal pressure transmission.

**Input feasibility and access limits.** The Federal Reserve calendar is public and gives meeting dates; the board's meeting statement releases identify the scheduled 2:00 p.m. time (see the [calendar](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) and a [statement-release example](https://www.federalreserve.gov/newsevents/pressreleases/monetary20260729a.htm)). The staged [Alpaca audit](../r6_data/alpaca/ALPACA_AUDIT.md) records SIP minute-bar availability and historical market-data coverage, while `r6_data` already holds OHLCV and point-in-time roster/SIC inputs for development. Alpaca access/retention terms and complete per-name event-window coverage would still need a date-filtered input-only QA before freezing. No event-window prices or beta values were computed here.

**Gate (a), source definition: PASS.** The event is public and dated; the exposure can be computed using past-only market data. The signal is reproducible in principle, but its relationship to *buying* pressure is not established.

## 3. Point-in-time coverage and independent breadth

The R6 development panel spans 2020-11-27 through 2026-10-30, with about 1,488 trading sessions in the staged OHLCV inventory and at most 30 Dow constituents per event. The scheduled-meeting cadence is eight meetings per year according to the Federal Reserve. After requiring a full 252-session beta warm-up wholly inside the allowed data window, the usable event ceiling is approximately 40 meetings (roughly late 2021 through October 2026); the exact count must be generated from the official calendar in a later input-only QA. This is an upper bound: holidays, missing minute bars, event-day trading halts, roster histories, and beta missingness can reduce it.

The point-in-time S&P panel has at most about 500 names and 53 SIC2 groups in the development inventory. The Dow has at most 30 eligible names and substantially fewer independent SIC2 groups (about 18 in the existing roster summary). The inferential observations are event dates, not 30 stocks × 40 events as if independent: each event creates one common market shock, and cross-sectional outcomes within SIC2 share shocks. The mechanism test should report event-date coverage and use SIC2 ranks, but SIC2 controls cannot manufacture more independent FOMC events.

Survivorship is controlled only if the S&P and Dow rosters are joined point-in-time at each formation. Corporate actions and symbol lineage must be handled as in the staged point-in-time data; a stock needs all 252 daily returns within the permitted window. The official event calendar is fixed before looking at returns. This screen has not counted qualifying rows or dates from price files, so full event-by-name coverage remains unverified.

**Gate (d), cheap input feasibility: PARTIAL / FAIL for a frozen test.** Public event dates and a documented SIP input path exist, but this screen has not verified the exact number of eligible event dates, full bar coverage, or each event-date roster join from date-filtered project rows. Those input-only checks are prerequisites, not permission to inspect outcomes.

## 4. Effective breadth and power at a sourced plausible effect

### Literature and effect-size transfer

Lucca and Moench, [“The Pre-FOMC Announcement Drift,” *Journal of Finance* 70(1) (2015), 329–371, DOI 10.1111/jofi.12196](https://doi.org/10.1111/jofi.12196), analyze U.S. equities around scheduled meetings from September 1994 to March 2011. They report an average S&P 500 excess return of about 49 basis points over the 24 hours before the announcement, approximately 80% of the realized equity premium in that sample. This is a **market-wide** event return, not a stock-level cross-sectional beta rank IC.

Kurov, Wolfe and Gilbert, [“The Disappearing Pre-FOMC Announcement Drift,” *Finance Research Letters* 40 (2021), 101781, DOI 10.1016/j.frl.2020.101781](https://doi.org/10.1016/j.frl.2020.101781), extend the analysis through December 2019. They find the drift essentially disappeared after 2015, both for announcements with Chair press conferences and those without. This is directly adverse to a post-2020 transfer claim.

Cieslak, Morse and Vissing-Jorgensen, [“Stock Returns over the FOMC Cycle,” *Journal of Finance* 74(5) (2019), 2201–2248, DOI 10.1111/jofi.12818](https://doi.org/10.1111/jofi.12818), study U.S. and international equity returns since 1994 through 2016. They document a cycle in which equity premia accrue in even-numbered weeks since an FOMC meeting and discuss monetary-policy information/risk-premium channels. This broad cycle evidence is not a replication of the 24-hour pre-announcement premium, nor a cross-sectional Dow beta effect. Knox and Vissing-Jorgensen's 2025 Annual Review summarizes the pre-FOMC drift alongside announcement-window and FOMC-cycle evidence, emphasizing that monetary-policy returns can reflect changes in yields, equity premia, and expected dividends rather than a single flow channel ([“The Effect of the Federal Reserve on the Stock Market,” DOI 10.1146/annurev-financial-090524-120826](https://doi.org/10.1146/annurev-financial-090524-120826)).

No verified source located here reports a post-2020 U.S. mega-cap **cross-sectional beta-sort IC**, or a point estimate that can be mapped into one. The 49 bp aggregate return cannot be multiplied by an assumed beta spread and presented as a sourced Dow excess return. That mapping would require an independently sourced beta dispersion and a stable positive post-2020 market drift; neither is provided by the studies above.

### Synthetic power calculation

I ran the synthetic-only `r4_harness/power_sim.py` with `assets=30`, `dates=40`, `horizon=2` (Newey–West lag 1), `signal_autocorrelation=0.2`, default null rank-IC standard deviation `1/sqrt(29)`, 5,000 simulations, seed `20261111`, and a planted mean rank IC of 0.020 **as a sensitivity scenario only**. It gives `P(NW t ≥ 2)=12.72%` (Monte Carlo SE 0.0047), effective N 33.3, and an 80%-power minimum detectable effect of 0.0914 for the mechanism t≥2 gate. The 0.020 scenario is not a paper estimate and not a project result. A Holm-adjusted hurdle would require a larger effect.

This calculation is intentionally favorable in one respect: it treats each event as independent and all 30 names as useful for within-date rank precision. SIC2 clustering, common market shocks, event-to-event dependence, and only about 18 Dow industry groups reduce effective breadth. More fundamentally, there is no matched effect size at which to claim adequate power. The 49 bp S&P aggregate return is not a candidate cross-sectional IC.

**Gate (b), post-2020 mega-cap plausibility: FAIL. Gate (c), power at an evidence-based plausible effect: FAIL.** The best exact-event large-market estimate is old and the extension finds disappearance after 2015; no post-2020 Dow-size stock-level effect is established.

## 5. Criterion-4 portfolio feasibility first

The most favorable applicable shape in `report_drafts/CRITERION4_BOUND_BY_SHAPE.md` is the rank-weighted top half, which has about 55% active share and an 80%-power weekly IC hurdle of **0.074** under its stated assumptions. That bound assumes a weekly signal, around 312 observations over six years, and a specified persistent-score design. It is already a poor fit for this sparse event design: after the 252-session warm-up, there are only about 40 event windows, approximately 6–7 per year. The synthetic event power check's pre-Holm MDE of 0.083 for the weaker `t≥2` mechanism test illustrates the loss of breadth; criterion-4 portfolio significance and Holm adjustment require more, not less.

For a future benchmarked book, the only plausible shape considered is to hold the EW30 baseline outside the window, and switch to a rank-weighted top-half Dow book from 2:00 p.m. on the prior trading day until just before the scheduled release, then restore EW30. On an event rebalance, the transition from EW30 to a 55%-active-share book and back implies roughly 110% total-notional turnover per event if the full active deviation is reversed; at 0.05% per side this is approximately 5.5 bp of NAV per event, before market impact. At ~40 events that is ~2.2% cumulative simple cost over the sample, or about 0.37% annualized. These are arithmetic estimates from the shape's active share, not observed turnover or returns. A position could be engineered to lower costs, but shrinking the deviation risks failing active share and does not solve the evidence gap.

There is no defensible event-window cross-sectional IC, expected Dow excess Sharpe, or bootstrap p-value range to translate from the papers. The aggregate 49 bp historical market return cannot be treated as the top-half-versus-EW30 return. If the beta spread were to capture only a fraction of that premium, both the fraction and the persistence after 2015 are unknown; assigning a numeric expected Sharpe or bootstrap p-value would invent evidence. The test would also enter the existing R6 Holm family (21 endpoints at the prior G1 stage; the current family may be larger), use the coordinator's block bootstrap, and DSR at the cumulative variant count. No claim of positive net excess, Sharpe superiority, or Holm-adjusted evidence is supportable.

**Gate (e), criterion-4 feasibility: STOP — FAIL.** The plausible *matched* effect range is unavailable, the post-2015 update is adverse, and the event count is far below the weekly design underpinning the 0.074 IC hurdle. The documented market-wide 49 bp statistic is not evidence that this long-only beta-ranked Dow book can beat EW30 after costs.

## 6. Holdout availability and protocol

No holdout-specific input is required for this screen, and no sealed data was read or requested. A later frozen idea would be governed by goal criterion 5 under the coordinator's one-shot protocol, after an authorized development pass and explicit holdout availability checks. Alpaca's stated history availability is not permission for this worker to fetch any observations before 2020-11-27; the 2010–2020 holdout remains entirely untouched here.

**Holdout verdict: PASS for non-access discipline.**

## Final screen decision

- **Overall: STOP — FAIL. Do not preregister or run this direction.** Exact prior-signal duplication is not the problem: the event timing is distinct. The problems are that the signal is a beta exposure rather than observed buying pressure, documented post-2015 evidence reports the broad drift disappeared, no paper supplies a matching cross-sectional mega-cap effect, and only about 40 usable event dates remain after a development-only beta warm-up.
- **Gate summary:** overlap of exact signal: PASS; exact dated source definition: PASS; input coverage: PARTIAL / FAIL pending date-filtered coverage QA; thesis fit and post-2020 transfer: FAIL; power at sourced plausible effect: FAIL; criterion-4 portfolio feasibility: FAIL; holdout discipline: PASS.
- **What could change the decision:** independent post-2020 evidence of a positive Dow-size beta-sorted rank IC on scheduled pre-announcement windows, plus input-only verification of event/date coverage and a feasible six-year criterion-4 power/cost projection. That evidence must precede any project outcome calculation.
- **Subjective probability of passing the full R6 criteria if later tested:** **below 1%**, judgment only. This reflects the direct disappearance finding after 2015, lack of a cross-sectional effect estimate, sparse event breadth, and weak fit to measured buying pressure.
- **Reviewer/date:** L3, 2026-11-11.

## Sources checked

- Lucca and Moench (2015), [DOI 10.1111/jofi.12196](https://doi.org/10.1111/jofi.12196).
- Kurov, Wolfe and Gilbert (2021), [DOI 10.1016/j.frl.2020.101781](https://doi.org/10.1016/j.frl.2020.101781).
- Cieslak, Morse and Vissing-Jorgensen (2019), [DOI 10.1111/jofi.12818](https://doi.org/10.1111/jofi.12818).
- Knox and Vissing-Jorgensen (2025), [DOI 10.1146/annurev-financial-090524-120826](https://doi.org/10.1146/annurev-financial-090524-120826).
- Federal Reserve, [FOMC meeting calendars](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm).
- `r4_harness/power_sim.py`, `report_drafts/CRITERION4_BOUND_BY_SHAPE.md`, `r6_data/alpaca/ALPACA_AUDIT.md`, `specs/r6_goal.md`, `specs/r6_decisions.md`.
