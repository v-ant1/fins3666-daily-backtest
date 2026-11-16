# R6 Idea Screen AO — Quarter-end window dressing from 13F changes

**Overall: STOP — FAIL.** The literature documents some quarter-end price pressure from fund trades and a Q4 increase in pension-fund selling of losers, but Form 13F only reports quarter-end positions after the fact. A 13F change cannot reveal whether shares were bought during the quarter-end close window, and the post-filing signal would be stale by up to 45 days. The proposed measure also substantially repeats S5's active-manager quarterly 13F change signal; only the interpretation as reporting-date window dressing is new. No project signal outcomes, returns, ICs, portfolio results, or holdout data were used.

## Identity and immutable-path preflight

- **Proposed name and mechanism:** AO — use point-in-time public 13F changes in Dow holdings to proxy quarter-end fund buying intended to improve reported portfolios, with temporary price pressure expected to reverse after the reporting date.
- **Exact new output path:** `r6_ideas/AO_windowdress.md`.
- **Path check:** the target did not exist before this screen; it is new.
- **Name/overlap check:** no existing file is named AO. S4–S6 and the related quarter-end screens are discussed below; this is not presented as a novel signal.
- **Development dates:** 2020-11-27 through 2026-10-30; earliest permitted worker data date is 2020-11-27.
- **Input dates:** the staged SEC-derived 13F development panel was scanned with read-time predicates requiring both report date and public filing-availability date to fall within 2020-11-27–2026-10-30. No earlier rows, market returns, outcome files, Holm-family file, or decision-log outcome lines were opened. The later sealed holdout was not accessed.

## 1. Overlap with prior work

- **S5 — active-manager 13F herding changes:** this is the closest match. S5 ranks stocks using manager-level changes in quarterly holdings. AO would interpret quarter-end 13F changes specifically as window dressing, possibly conditioning on the last quarter of the year. Both are the same quarterly ownership-change input and the same Dow stock-level cross-section. The reports do not identify actual transaction dates, so the “window dressing” label does not make the observable distinct.
- **Y_seasonal_flows — quarter-end window-dressing pressure:** Y tests quarter-end timing with an OHLCV pressure proxy and rejects it because the proxy cannot isolate institutional flow and the calendar sample is sparse. AO swaps in 13F positions but does not gain transaction timing; it inherits the same event-count limit.
- **S4 — option-expiration/month-end pressure:** the institutionally timed quarter-end branch is nearby but S4 is mainly calendar/option pressure. S6 is public attention and is not the same mechanism.
- **P4 / AK_passive_weight:** these examine passive ownership levels or passive demand rather than active-manager reporting incentives. They are adjacent 13F/ownership inputs but not the closest duplicate.

No matching portfolio rule or result is needed to identify the S5 duplication. The task bars reading decision-log outcome lines, so I did not inspect them; any registry-only cross-reference remains for the coordinator.

- **Verdict: FAIL — substantial overlap.** AO is a relabeling or narrow conditioning of the already screened active-manager 13F holdings-change direction in S5, not a sufficiently distinct pressure measure.

## 2. Exact pressure measure and dated data source

### Candidate definition, if the coordinator nevertheless wants it recorded

At each calendar quarter-end, for every Dow issuer *i*, calculate a reported ownership-change score from managers that filed holdings for both quarter *q* and quarter *q−1*:

`score(i,q) = sum_m [split-adjusted shares(m,i,q) − split-adjusted shares(m,i,q−1)] / shares_outstanding(i,q)`.

Exclude option positions, omit managers without a filing in both quarters rather than treating them as sellers, aggregate duplicate security classes only under a frozen CUSIP-to-issuer rule, and use the then-current Dow roster. A positive net change is the hypothesized pressure measure. The direct window-dressing event hypothesis is a positive price impact into quarter-end followed by a negative five-session reversal; that is the sign/horizon in the papers, but this 13F proxy cannot be observed at that time. If instead the share-change score is traded after filings with a positive five-session forecast, that is a post-disclosure continuation test like S5, not a window-dressing test. This candidate definition is only a screen; it is not authorized for outcome testing.

That definition cannot be formed at quarter-end. The share counts are point-in-time quarter-end snapshots, but managers disclose them later. The direct window-dressing claim predicts a rise into the quarter-end close followed by a reversal over the next sessions; 13F cannot timestamp or identify those trades. A feasible **different** signal timestamp would be a fixed cutoff after the SEC Form 13F deadline, using only filings public by that timestamp and omitting late or missing filers. The forecast would then begin at the next session's open. A positive five-session forecast would test post-disclosure continuation in disclosed positions (the S5 herding mechanism), while a reversal forecast at that late date would not be the documented close-window reversal. 13F holdings changes also do not distinguish purchases from other changes in positions during the quarter.

The SEC [Form 13F FAQ](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f) states that holdings and their fair market values are reported as of calendar quarter-end and filings are due within 45 days. The filing is free on EDGAR; the staged panel is sourced from those filings and includes filing availability dates. Coverage is limited to securities on the Section 13(f) list and qualifying managers, can be delayed by late amendments or confidential treatment, and omits short positions and any within-quarter trade path. A CUSIP-to-issuer and split adjustment history is required; ticker-only joins risk symbol changes, class duplication, delistings, and survivorship.

### What the papers establish

- Lakonishok, Shleifer, Thaler, and Vishny, [“Window Dressing by Pension Fund Managers” (1991)](https://doi.org/10.3386/w3617), analyze 769 pension funds with $129 billion in assets at the end of 1989. They find that managers sell poorly performing stocks disproportionately and that relative selling of losers accelerates in Q4. This is holdings/trading behavior, not a Dow stock-level return prediction, and the sample predates current disclosure rules and passive-market structure.
- Carhart, Kaniel, Musto, and Reed, [“Leaning for the Tape: Evidence of Gaming Behavior in Equity Mutual Funds,” *Journal of Finance* 57 (2002), 661–693](https://doi.org/10.1111/1540-6261.00438), study U.S. diversified equity funds and stock prices over historical samples including daily mutual-fund observations from 1985–1997. They report quarter-end price inflation from last-minute purchases of stocks already held; estimated fund-level inflation ranges from 0.5% per year for large-cap funds to more than 2% for small-cap funds. This is a fund-NAV/closing-window effect, not a cross-sectional IC for the quarter-end holding change disclosed weeks later.
- Duong and Meschke, [“The Rise and Fall of Portfolio Pumping Among U.S. Mutual Funds,” *Journal of Corporate Finance* 60 (2020), 101530](https://doi.org/10.1016/j.jcorpfin.2019.101530), examine fund indices/holdings over 1993–2011 and institutional transaction records for roughly 400 institutions over 1999–2011. They find quarter-end spikes and abnormal buying decline following heightened regulatory attention; declines are largest around year-ends and for small-cap/better-performing funds. This is important counterevidence to carrying older magnitudes into 2020–2026 mega-caps.
- Gormley, Kaplan, and Verma, [“More Informative Disclosures, Less Informative Prices? Portfolio and Price Formation Around Quarter-Ends,” *Journal of Financial Economics* 146 (2022), 665–688](https://doi.org/10.1016/j.jfineco.2021.10.004), use fund trade-level data for 1998–2008. They find funds accelerate completion of existing positions into quarter-end but delay starting new positions until quarter-start; quarter-end returns are 32% less informative about 30-day price changes. This establishes altered trading and price formation, not a signed return forecast from public 13F net-share changes.
- A more recent, still-unpublished working paper by Lim, [“What Does Mandatory Portfolio Disclosure Reveal? A Placebo Test of the 13F Regime” (2026)](https://ssrn.com/abstract=7204639), reports 29,421 security events from 894 filings by 26 managers over 2013–2026. It reports a two-day abnormal-return difference around newly disclosed/materially increased positions of about −7 bp under equal security-event weighting, while alternative filing-weighted estimates range −2 to −6 bp; the estimates are not all statistically significant at 5%. This is a filing-disclosure event estimate for selected managers, not evidence of quarter-end window-dressing pressure in Dow stocks.

- **Verdict: partial literature support, failed measurement gate.** The quarter-end behavior is documented, but the public filing does not time the purchase or provide a usable quarter-end pressure observation. The cited effects do not directly support the proposed post-filing Dow signal or its positive five-session sign.

## 3. Point-in-time coverage and independent breadth

### Input-only development coverage check

I used PyArrow's CSV dataset scanner with predicates on **both** `report_date` and `availability_filing_date` in the allowed development window. The resulting rows were metadata/coverage only; no holding quantities, prices, or returns were read into the check.

| Coverage item | Filtered result | Interpretation / limit |
|---|---:|---|
| 13F holdings rows | 223,932 | Input rows only, not trades or outcome observations |
| Report quarters | 23, 2020-12-31 to 2026-06-30 | Q3 2026 is not yet public within the 2026-10-30 cutoff |
| Distinct managers | 142 | Selected staged manager universe, not all holders |
| Distinct tickers across panel | 33 | Constituent turnover/security mapping over time |
| Names per report quarter | 30 in each of 23 quarters | Intended Dow-size coverage, not a complete transaction history |
| Filing availability dates | 274, 2021-01-12 to 2026-08-14 | Staggered disclosures; the common formation timestamp is much later than the report date |
| Independent quarter-end observations | At most 23 | Same-date issuer observations share market and reporting shocks; no 30×23 independent-event assumption |
| Independent manager/issuer trade events | Not available | 13F does not include transaction timestamps or an event count |

The sample has only 23 report quarters within the dates that are both eligible and public. This is before considering the actual signal's nonzero changes, common-filing timing, manager overlap, or industry correlation. The 33 total tickers across quarters reflect changing names/mappings; only 30 names appear per quarter. The input panel is useful for a Dow coverage prototype but cannot identify end-of-quarter buys or construct a direct S&P spillover test. The panel counts were obtained from the staged `r4_L4/data/13f_development_pit_positions.csv`, a selected SEC-derived extract, not from a whole-market holdings census.

- **Verdict: FAIL for measuring the event; partial for basic input availability.** Twenty-three public quarter observations are available, but the exact pressure event, independent event count, and within-quarter purchases are not observable.

## 4. Effective breadth and power at a sourced plausible effect

The studies provide no effect-size range that matches a five-session Dow cross-sectional rank IC from public holdings changes. Carhart's 0.5% annual large-cap fund-level inflation is not a stock-level return estimate and is tied to last-minute orders in an older period. Duong and Meschke document that the phenomenon declined after increased scrutiny. Gormley et al.'s 32% reduction in price informativeness is not a return or IC magnitude. Lim's recent −7 bp two-day filing-event estimate has a different event and outcome and is not consistently significant. None can be responsibly converted into an expected positive Dow rank IC.

For design sensitivity only, I ran the project's synthetic-only `r4_harness/power_sim.py` with 30 assets, 23 quarterly observations, horizon 1 quarter (no overlap; NW lag 0), assumed date-level IC autocorrelation 0.20, 5,000 simulations, and seed 20261111. The null IC standard deviation is the tool's conventional `1/sqrt(30−1)` approximation. This is not calibrated to project outcomes or to any paper's effect.

| Planted mean IC | Purpose | `P(NW t ≥ 2)` | Monte Carlo SE | 80%-power MDE |
|---:|---|---:|---:|---:|
| 0.0183 | Illustrative small planning effect; no paper estimate | 12.38% | 0.00466 | 0.1100 |
| 0.083 | Long-only monthly feasibility-bound comparison only; not directly comparable to quarterly IC | 57.44% | 0.00699 | 0.1100 |

The criterion-4 bound audit reports an optimistic monthly top-five-versus-EW30 IC around 0.083–0.089 before realistic dependence penalties. The 23-quarter design needs an IC around 0.11 for 80% power under this simple simulator; even planting 0.083 yields only 57% power. The quarter-level date ICs are likely dependent across quarters, and same-date issuer observations are not independent because market and sector shocks are common. These assumptions do not establish a useful mechanism test. More fundamentally, the literature has no signal-matched positive or negative Dow effect to plant.

- **Verdict: FAIL.** No sourced, appropriately matched effect supports adequate power; the available 23-quarter sample is too small for the planning benchmark even before event and sector dependence.

## 5. Criterion-4 portfolio feasibility first

The closest tradable design would form at a fixed point after each 13F quarter filing deadline, rank the 30 current Dow members by aggregate normalized position increase among continuing managers, and hold the top 15 stocks equally weighted until the next quarterly signal. It would use 50% active share versus EW30, a 50% turnover cap per rebalance, and 0.05% cost per dollar traded on each side. Late filings and amendments would be excluded after the formation cutoff; a holding not reported in both quarters would be missing, not a sale. This is a quarterly *post-disclosure* position-change strategy, not a trade on the quarter-end buying event.

The fixed goal still requires positive net excess return versus EW30, higher portfolio Sharpe, and a one-sided block-bootstrap p-value passing Holm across the complete R6 family. The six-year active-Sharpe planning threshold in the criterion-4 audit is approximately 1.00–1.05 around the currently illustrated Holm ranks, before dependence penalties; its monthly top-five illustration uses an IC around 0.083–0.089. That bound is not an exact quarterly top-half conversion, but it shows the scale of documented evidence needed. The 13F papers offer no compatible stock-level effect or net return range, and one of the recent findings is a small negative filing-event estimate rather than positive continuation. No defensible portfolio-level net excess return or Sharpe range can be inferred. With only 23 quarterly observations and a 50% turnover cap, a portfolio run would not resolve the missing event measurement and would be underpowered.

- **Verdict: FAIL — criterion-4 feasibility is unsupported.** Do not authorize a portfolio test; no direct effect estimate supports costs, turnover, benchmark outperformance, Sharpe, block bootstrap, or the full Holm family.

## 6. Holdout availability and protocol

No holdout path or holdout-specific input was needed or accessed. Holdout availability remains unverified. Under goal criterion 5, any later holdout test is coordinator-controlled after a frozen preregistration and code pass all development gates; only an availability-only check may precede it. This failed screen does not request or authorize such a check.

- **Verdict: PASS for the no-holdout screening constraint; availability not assessed.**

## Final screen decision

**Overall: STOP — FAIL.** S5 already covers active-manager 13F position changes; Y already screens quarter-end window-dressing pressure. Quarter-end fund pressure is plausible from the literature, but its strongest evidence uses transaction-level or closing-price data, while 13F holdings are stale snapshots disclosed up to 45 days later. The modern evidence shows reduced or altered pressure and supplies no signal-matched Dow-size return effect. Twenty-three quarterly observations, unknown actual event counts, turnover, and the strict criterion-4 requirements do not justify further testing.

Evidence that could change this verdict would be a free, point-in-time institutional transaction panel identifying stock-level quarter-end buys and sellers in the Dow, a post-2020 mega-cap estimate of the next-session/next-week peer or stock-level response, and sufficient independent quarterly observations to meet power and after-cost feasibility thresholds. A 13F holdings change alone cannot supply those inputs.

**Reviewer/date:** dispatched worker screen, 2026-11-11.

## Sources

- SEC, [Frequently Asked Questions About Form 13F](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f).
- Lakonishok, Shleifer, Thaler, and Vishny (1991), [“Window Dressing by Pension Fund Managers”](https://doi.org/10.3386/w3617).
- Carhart, Kaniel, Musto, and Reed (2002), [“Leaning for the Tape: Evidence of Gaming Behavior in Equity Mutual Funds”](https://doi.org/10.1111/1540-6261.00438).
- Duong and Meschke (2020), [“The Rise and Fall of Portfolio Pumping Among U.S. Mutual Funds”](https://doi.org/10.1016/j.jcorpfin.2019.101530).
- Gormley, Kaplan, and Verma (2022), [“More Informative Disclosures, Less Informative Prices? Portfolio and Price Formation Around Quarter-Ends”](https://doi.org/10.1016/j.jfineco.2021.10.004).
- Lim (2026 working paper), [“What Does Mandatory Portfolio Disclosure Reveal? A Placebo Test of the 13F Regime”](https://ssrn.com/abstract=7204639).
- Project design-only references: [`S4-S6.md`](S4-S6.md), [`Y_seasonal_flows.md`](Y_seasonal_flows.md), [`CRITERION4_BOUND_AUDIT.md`](../report_drafts/CRITERION4_BOUND_AUDIT.md), [`power_sim.py`](../r4_harness/power_sim.py).

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
