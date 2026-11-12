# R6 Idea Screen AD — year-end tax-loss selling and January reversal

**Verdict: STOP — FAIL. Do not register a variant or commission a runner.** The old literature makes tax-loss-induced selling and a turn-of-year rebound plausible, but it does not establish an economically large, present-day mega-cap effect in a form that can clear the R6 portfolio hurdle. Only five independent annual January windows are available in the permitted development interval, and the conservative synthetic power check is inadequate even when planted at the weekly rank-IC hurdle from the shape audit.

No project signal, forward return, portfolio return, IC, or other outcome was calculated or inspected. The only local data read was a Parquet query filtered to dates from 2020-11-27 through 2026-10-30, selecting `date` and `ticker` labels only.

## Identity and immutable-path preflight

- **Proposed short name:** AD, tax-loss selling / January reversal.
- **Mechanism:** year-end selling pressure on prior-calendar-year losers abates after the turn of the year; if prices are temporarily depressed, the same losers rebound during January.
- **Exact new output path:** `r6_ideas/AD_taxloss.md`.
- **Target check:** the exact path did not exist before this screen. No other `r6_ideas/AD*` file was present.
- **Development window:** 2020-11-27 through 2026-10-30; this is also the earliest permitted worker-path date.
- **Holdout/path check:** no holdout paths or files were read, and no project path outside the permitted development window was used. The only data path queried was `r6_data/sp500_ohlcv_dev_gapfilled.parquet`, with an explicit date predicate at the read call.
- **Verdict:** PASS for path and date safety.

## 1. Overlap with prior work

The nearest existing screen is `r6_ideas/Y_seasonal_flows.md`, which rejected broad turn-of-month, quarter-end, and pre-holiday OHLCV calendar proxies. AD instead ranks stocks by a tax-loss proxy (prior-calendar-year total return) and tests a single January reversal window. This is a distinct, named economic mechanism and is not a renamed month-end signal. `P3.md` covers high-MAX/lottery-attention reversal, while `W_events.md` covers other event-based pressure; neither uses taxable investors’ year-end loss realization. The `R5_FINAL.md` and `specs/r6_decisions.md` searches showed no prior AD/tax-loss/January signal registered or tested; decision 178 explicitly assigned the year-end tax-loss idea to Round AD.

This is not the same as a general January long-market position: it is a cross-sectional, prior-loss-conditioned stock selection. It may still overlap with generic loser reversal and known seasonal patterns, so novelty is only mechanism-level; the strong direct literature is support, not novelty.

- **Verdict:** PASS for distinctness from the screened R6 signals, with a material overlap caveat from generic reversal / seasonality.

## 2. Exact pressure measure and dated data source

**One candidate only; no parameter variants.** At the close on the final US trading day of calendar year *y*, compute each stock’s split- and distribution-adjusted total return from the final close of year *y−1* through the final close of year *y*. Define the selling-pressure score as the negative of that return: the more negative the prior-year return, the higher the presumed year-end tax-loss pressure. Freeze the cross-sectional ranks at that close. The prediction window is the first 21 US trading sessions of January *y+1*, entered at the first session’s open and exited at the 21st session’s close. Signal timestamps are after the final December close, so the December close itself is not tradeable as part of the January return.

The planned research sources are historical price/total-return data and point-in-time constituent membership, not tax lots or investor identity. The existing staged S&P development panel is `r6_data/sp500_ohlcv_dev_gapfilled.parquet`; it has daily date/ticker and OHLCV/adjusted-close fields. Adjusted-close construction and the supplied point-in-time roster must be validated before any preregistration: raw adjusted-close conventions can mishandle distributions, splits, symbol changes, and delisting proceeds. The daily panel is an input-availability source, not direct evidence that a loss was held in a taxable account. Public financial data can supply returns and membership, but not tax basis, realized gains elsewhere in a holder’s portfolio, wash-sale constraints, or the identity/size of tax-sensitive owners.

A complete 2020 calendar-year loss score is prohibited because it would require January–October 2020 data. The first eligible formation is therefore **2021-12-31**, using the 2021 calendar-year return whose base close is 2020-12-31; that base date is inside the allowed window. The first prediction period is January 2022. The last eligible formation is **2025-12-31**, predicting January 2026. A December 2026 formation is outside available development dates and cannot contribute an outcome.

- **Verdict:** PARTIAL. The price-based proxy is reproducible from public daily data after a data-quality review, but it is a proxy for tax-loss pressure, not a direct measure of it.

## 3. Point-in-time coverage and independent breadth

A date-predicate query over `r6_data/sp500_ohlcv_dev_gapfilled.parquet` selected only `date` and `ticker`, with bounds `2020-11-27 <= date <= 2026-10-30`. It returned 1,488 distinct sessions and 566 distinct ticker labels in the bounded panel. At the five eligible December formation dates, the panel had 470, 479, 484, 489, and 496 tickers. Of those, 453, 463, 470, 474, and 478 respectively also had a row at the prior December base close. January windows contained 20, 20, 21, 20, and 20 sessions, with 470, 479, 484, 489, and 496 names intersecting the formation-date panel and that January-window union. These are input-presence counts only; no prices or signals were examined.

| Coverage unit | Count | How obtained |
|---|---:|---|
| Usable formation dates | 5 (2021-12-31 to 2025-12-31) | Calendar dates matched to bounded panel labels |
| Independent January event years | 5 | One non-overlapping January window per year, 2022–2026 |
| Names with both annual endpoint rows | 453–478 per formation | Date/ticker rows at prior and current December closes |
| January sessions per event | 20–21 | Distinct bounded panel dates in January |
| SIC2 groups | Not measured | This price panel has no SIC field; the staged SIC input is CSV without predicate pushdown, so it was not opened for this screen |

Point-in-time membership does not fully cure survivorship: the staged S&P panel contains only the roster/data availability reflected in its own construction, and active constituents at December formation must be explicitly matched before any later test. A usable ticker at both endpoints is necessary but does not by itself establish full return history, a correctly back-adjusted corporate-action series, or a valid delisting return. Names dropped before December may also be missing from the usable cohort. The Dow portfolio would have at most 30 names at a formation and no more than five annual events. The event-level sample, not the count of names, limits inference; the cross-sectional names share the same tax-calendar shock.

- **Verdict:** FAIL for sufficient independent breadth. Five annual observations cannot support the specified multiple-testing and block-bootstrap inference, and the SIC2 cluster count is not available from the permitted coverage query.

## 4. Effective breadth and power at a sourced plausible effect

### What the literature actually measures

Dyl, [“Capital Gains Taxation and Year-End Stock Market Behavior,” *Journal of Finance* 32 (1977), 165–175](https://doi.org/10.1111/j.1540-6261.1977.tb03250.x), documents year-end volume and stock-market behavior consistent with tax-sensitive selling; it is historical market evidence, not a post-2010 mega-cap rank IC. Grinblatt and Moskowitz, [“Predicting Stock Price Movements from Past Returns: The Role of Consistency and Tax-Loss Selling,” *Journal of Financial Economics* 71 (2004), 541–579](https://doi.org/10.1016/S0304-405X(03)00176-4), find tax-loss selling and return consistency affect the cross-section, but their estimator and broad historical universe do not provide an annual January rank IC for modern Dow constituents. Poterba and Weisbenner, [“Capital Gains Tax Rules, Tax-Loss Trading, and Turn-of-the-Year Returns,” *Journal of Finance* 56 (2001), 353–368](https://doi.org/10.1111/0022-1082.00328), use 1963–1996 NYSE/AMEX evidence and show that the loss/turn-of-year association varies with tax regimes; they do not establish post-2020 large-cap effect persistence.

The more recent evidence is a warning about transport. Sikes, [“The Turn-of-the-Year Effect and Tax-Loss-Selling by Institutional Investors,” *Journal of Accounting and Economics* 57 (2014), 22–42](https://doi.org/10.1016/j.jacceco.2013.12.002), finds the direct institutional tax-loss link and a 47 bp per-day relation for tax-sensitive institutions’ realized losses, but explicitly finds the return impact among **small-capitalization stocks**. Chaudhuri, Burnham, and Lo, [“An Empirical Evaluation of Tax-Loss-Harvesting Alpha,” *Financial Analysts Journal* 76 (2020), 99–108](https://doi.org/10.1080/0015198X.2020.1760064), use the 500 largest CRSP securities over 1926–2018 and estimate tax *alpha* from tax-loss-harvesting, not pre-tax January reversal returns; their 1.08% annual tax benefit is not a stock-return edge. I found no credible, matched post-2010 large-cap result reporting a rank IC for this exact signal. Thus there is **no defensible sourced plausible effect size in the required unit**.

### Synthetic power check

To make the limitation concrete, I ran `r4_harness/power_sim.py` with synthetic inputs only: 500 names, five annual event-date IC observations, horizon 1 in event time (NW lag 0), signal autocorrelation 0.2, 10,000 simulations, and cross-sectional IC SD `1/sqrt(60) = 0.1291` as a conservative proxy for about 60 independent SIC2 clusters. The cluster count/SD is an explicit planning assumption, not a measured property of the panel. No project return or signal was supplied to the simulator.

| Planted mean rank IC | Power for one-sided NW t ≥ 2 | 80% MDE for t ≥ 2 |
|---:|---:|---:|
| 0.020 | 16.6% | 0.164 |
| 0.074 | 40.8% | 0.164 |
| 0.100 | 55.0% | 0.164 |
| 0.150 | 77.9% | 0.164 |

The 0.074 row is the weekly `RankTopHalf` threshold from `report_drafts/CRITERION4_BOUND_BY_SHAPE.md`, **not** a literature estimate for annual tax-loss selling. It is already well below 80% power under the simple t≥2 rule. R6 currently uses at least 24 endpoints; the first Holm cutoff is `0.05/24 = 0.00208` (approximately one-sided z=2.87). Under the same normal approximation, 80% power at that cutoff requires a mean IC around `(2.87 + 0.84) × 0.1291/sqrt(5) ≈ 0.215`, before any correction for event-year dependence or uncertainty in the cluster SD. This is a diagnostic calculation, not an observed effect.

- **Verdict:** FAIL. No compatible sourced effect exists, and only five annual date-level observations make power inadequate even at the unrelated weekly feasibility hurdle.

## 5. Criterion-4 portfolio feasibility first

A clean, fixed portfolio mapping would rank the Dow’s 30 point-in-time names by the signal and hold a **rank-weighted top half** long-only book through the first 21 January sessions, compared with EW30. The portfolio has 55% active share under the shape-audit weighting rule. It would trade at the first January open, pay 0.05% per side, and liquidate at the window end; exact turnover cannot be estimated without calculating the signal ranks and is not claimed here. The one-year rebalance spacing likely reduces annual trade count, but does not solve the fact that a single end-of-year event can produce substantial position turnover. No cost-to-edge ratio can be established because no defensible gross edge is sourced.

The shape audit’s **weekly** RankTopHalf bound is about 0.074 rank IC at low signal persistence, with an assumed six-year weekly return path; that estimate cannot be carried over to this annual design. The five independent January windows (versus about 312 weekly observations in the audit) are too few for the required block bootstrap and Holm family, and the t≥2 power check gives only 40.8% power at IC 0.074. The realistic effect that might survive among mega-caps is undocumented and may be smaller or absent. Even with 5 bp/side costs and a low annual rebalance frequency, the full criterion—positive net excess return, Sharpe above EW30, and Holm-adjusted one-sided block-bootstrap significance—is not plausibly established from this sample.

- **Verdict:** FAIL — criterion-4 feasibility is unsupported. No portfolio outcome was calculated.

## 6. Holdout availability and protocol

This screen did not use or require any holdout value. The sealed Dow 2010-01-01 through 2020-10-31 and all restricted country ETF series remain untouched. A later coordinator-controlled criterion-5 evaluation could only be considered after all development gates pass, a frozen preregistration and independent runner are reviewed, and an availability-only check confirms the required point-in-time roster and raw price rows without examining returns or signals. This idea fails before that stage, so no holdout run is authorized or recommended.

- **Verdict:** PASS for respecting the holdout protocol; no holdout availability claim was made.

## Final screen decision

**Overall: STOP — FAIL.** The historical price-pressure story is real enough to motivate this screen, and the Dow price data would make the simple loser proxy easy to form. But there is no documented post-2010 mega-cap effect size in compatible rank-IC units, and the data window contains only five independent annual January events; a six-year portfolio comparison with Holm and block-bootstrap inference is not credible at that breadth. Direct tax-lot or tax-sensitive investor transaction data, a longer untouched event sample, and large-cap out-of-sample rank-IC evidence could change the assessment; none is available in this screen.

### Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.

**Reviewer:** Round AD screen, 2026-11-11.
