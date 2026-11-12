# R6 Idea Screen AG — Dow reversal after index-ETF volume shocks

**Overall verdict: STOP — FAIL.** A prior published practitioner study directly links high ETF-volume days to temporary constituent comovement and proposes buying oversold names after an ETF selloff, but the measure is unsigned secondary-market trading volume rather than net ETF buying or selling. The date-safe development inputs are present, yet the sample yields only 37 volume-shock episodes after a simple five-session clustering rule, the literature does not supply a post-2020 Dow rank IC, and the fixed criterion-4 feasibility is unsupported.

**Screen boundary.** No future/forward returns, signal-outcome statistics, ICs, portfolio returns, Sharpe ratios, or holdout values were computed or inspected. The only numeric event counts below come from current or past **input-side** volume data; Dow coverage checks read only dates and tickers. Every Parquet read was filtered at read time to `date >= 2020-11-27` and `date < 2026-10-31`; rolling volume thresholds used only those filtered rows, with a 252-session warm-up, and no statistic includes earlier rows.

## Identity and immutable-path preflight

- **Short name and mechanism:** AG — unusually high SPY/DIA secondary-market trading volume may coincide with indiscriminate index-basket pressure; Dow names that underperform their market-model expectation on those dates may subsequently rebound as that pressure dissipates.
- **Exact new output:** `r6_ideas/AG_flowday_reversal.md`.
- **Path preflight:** this exact target did not exist before the screen. No output or input path points to the sealed holdout or a date before 2020-11-27.
- **Development range:** 2020-11-27 to 2026-10-30. The event threshold requires 252 completed sessions after the permitted start; the first eligible event date is 2021-11-29.
- **Name/decision check:** decision 187 requested this AG screen. No existing file uses this exact path or name.

## 1. Overlap with prior work

| Nearby direction | What it tested | AG distinction and remaining overlap |
|---|---|---|
| J1 | Weekly SIC2-relative own-stock return reversal over ordinary weeks | AG conditions on a high-volume SPY/DIA event and measures constituent residual underperformance on that event. Both use a short-horizon reversal sign and the same Dow names, so AG is adjacent and cannot use J1's outcome as supporting evidence. |
| D4 | Daily common-owner 13F graph, close-location pressure, and subsequent connected-stock response | AG uses a broad index-ETF volume event, no 13F edges or graph diffusion, and a constituent residual-return shock. The reversal sign is independently motivated by published ETF-volume work, not selected by flipping D4's previously observed sign. The shared Dow sample and reversal outcome still make the family nearby. |
| P1 | Monthly own-stock overnight return momentum | AG has an index-ETF volume trigger, close-to-close/residual cross-section, negative reversal sign, and event-driven formation. It does not use overnight momentum. |
| H / R5 ETF-flow screen | Sector-ETF OHLCV pressure transmission; later primary-market ETF creation/redemption feasibility failure | AG uses two broad index ETFs, a trailing volume-tail event, and cross-sectional reversal among Dow names. It does not claim to measure creations/redemptions. It remains a close member of the ETF-pressure family, and unsigned volume cannot identify net flow direction. |

The strongest direct precedent is already an ETF-volume-spike/constituent-reversal idea, so this is a transport and measurement test rather than a new mechanism. The narrower index trigger and residual underperformer selection make the estimand more specific, but they do not erase the overlap.

**Verdict: PARTIAL / FAIL for novelty.** This is distinguishable from J1, D4, and P1 on its source and event-conditioned score, but it is close to H and to prior ETF-flow pressure work. The application is not strong enough to support a new variant given the other failed gates.

## 2. Exact pressure measure and dated data source

If the idea were ever reconsidered, freeze this single event design without parameter search:

1. For SPY and DIA independently, flag date `t` when that ETF's reported share volume is at least the 95th percentile of its own volume over the **previous 252 completed US trading sessions**, excluding `t`. A date is an event if either ETF meets the fixed threshold; same-date SPY and DIA triggers count as one date, not two.
2. At an event close, use the point-in-time Dow roster and a market model fitted only on the prior 252 completed sessions to calculate each stock's same-day residual return against the triggered ETF (SPY for an SPY-only trigger, DIA for DIA-only; average the two ETF residuals if both trigger). The proposed overreaction signal is the negative of that event-day residual: the most negative residual is the strongest presumed oversold/pressure name.
3. Predict positive residual return over the next five US sessions, entering no earlier than the next session open. The registered sign would be negative relation between event-day residual and next-five-session residual return (equivalently, a positive relation between the negated residual score and next-five-session residual).

This is a proposed measurement definition only; the score and outcome are not calculated here. The source is `r6_data/etf/etf_ohlcv_dev.parquet`, which contains daily ETF OHLCV; the issuer cross-section can be joined from `r6_C1/dow_components_dev.parquet`, which contains point-in-time Dow components and adjusted prices/return fields. These are internal staged inputs, not a claim of a public right to redistribute vendor data; any later report must document original vendor/licensing provenance. Point-in-time roster membership is required at each event date. The proposed volume measure is *secondary-market share turnover*, not creations/redemptions, net buying, or the primary-market flow of ETF shares.

The direct published example is Lynch, Page, Panariello, Tzitzouris, and Giroux, [“The Revenge of the Stock Pickers,” *Financial Analysts Journal* (2019), 34–43](https://doi.org/10.1080/0015198X.2019.1572358). It uses 11 ETFs and 240 volume-spike events over 2010–2017. The authors condition on an ETF price decline, use low ETF-beta constituent “outsiders,” and report cumulative after-cost alpha over holding windows up to 40 days. It is a practitioner article, and the authors disclose that they work for an active manager; its event-conditioned beta-sorted result is not the rank IC of this AG definition.

Important counter-evidence is Box, Davis, Evans, and Lynch, [“Intraday Arbitrage between ETFs and Their Underlying Portfolios,” *Journal of Financial Economics* 141 (2021), 1078–1095](https://doi.org/10.1016/j.jfineco.2021.04.023). On 423 US equity ETFs with minute-level ETF and constituent data over 2006–2015, they find little evidence that ETF trading drives constituent returns, including at daily frequency. Ben-David, Franzoni, and Moussawi, [“Do ETFs Increase Volatility?” *Journal of Finance* 73 (2018), 2471–2535](https://doi.org/10.1111/jofi.12727), find higher ETF ownership increases underlying-stock volatility and negative autocorrelation using index-membership variation; that supports a general arbitrage/pressure channel, not daily ETF-volume-spike predictability. Together, these are mixed evidence rather than a clean, directly matching two-paper estimate.

**Verdict: PARTIAL.** The signal can be specified and its raw inputs exist, but ETF volume alone does not tell whether investors were buying or selling, and published studies do not identify this exact volume-only event score.

## 3. Point-in-time coverage and independent breadth

Feasibility reads used PyArrow dataset filters at read time. The ETF query applied the start/end date filters and the `ticker in {SPY,DIA}` predicate before reading `date`, `ticker`, and `volume`. The Dow component query applied the date filter before reading only `date` and `ticker`. No Parquet aggregation included a row dated before 2020-11-27.

| Input-only coverage check | Result | Meaning |
|---|---:|---|
| Filtered SPY rows / sessions | 1,488 / 1,488 | 2020-11-27–2026-10-30 |
| Filtered DIA rows / sessions | 1,488 / 1,488 | 2020-11-27–2026-10-30 |
| Common SPY/DIA sessions | 1,488 | Both are present throughout the sampled development dates |
| Dates with a complete prior 252-session threshold | 1,236 per ETF | Rolling threshold starts 2021-11-29; uses only post-cutoff input rows |
| SPY / DIA volume-threshold crossings | 63 / 81 | Volume is at or above its trailing p95; input-side events only |
| Unique dates after same-day SPY/DIA deduplication | 109 | 35 dates triggered both ETFs; 28 SPY-only; 46 DIA-only |
| Episodes after merging events within five sessions | 37 | Conservative event-clustering assumption for power/overlap, not a selected return window |
| Dow input dates / distinct historical tickers | 1,488 / 33 | Maximum 30 component names per date; median 30, minimum 1 |
| Dow event dates with component rows | 109 / 109 | Exactly 30 rows/names on every event date in the staged component input |
| Nonmissing cross-sectional signal values inspected | 0 | No stock or ETF price/return signal values were read for this screen |
| SIC2 clusters verified on events | 0 | No SIC grouping is part of this single-index event hypothesis; residual cross-sectional dependence remains |

These counts establish date and roster-row availability, not a stable 30-name six-year panel: the component input has 33 distinct historical tickers and some non-event dates have fewer than 30 components. Event dates are selected by a rolling volume tail, and nearby triggers are not independent; five-session episode merging leaves 37 source-shock clusters. No post-2020 performance transfer has been established. The 2019 paper's 240 events combine 11 funds and eight years, so its count is not a Dow-only event count and cannot be transplanted to AG. Symbol entry/exit, the UTX-to-RTX lineage, and possible vendor corrections require explicit point-in-time handling. The screening query did not open roster history outside the date filter or use event dates before the first complete rolling window.

**Verdict: PARTIAL / FAIL.** ETF and Dow date coverage is adequate at the raw-input level, but the independent event breadth is small and the effective cross-sectional independence is lower than 30 because all names share one or two index shocks.

## 4. Effective breadth and power at a sourced plausible effect

No cited paper reports a weekly rank IC for residual Dow-name reversal after a SPY/DIA volume-tail event. The 2019 study's conditional 40-day, low-beta “outsider” portfolio result is not a numeric rank IC, and it uses a different trigger (ETF price decline) and selector. Box et al. are direct counter-evidence for the underlying ETF-to-constituent transmission premise. Therefore the best defensible effect size for this candidate in Dow rank-IC units is **unknown**; I do not convert the published portfolio alpha into a fabricated IC.

For a planning sensitivity only, `r4_harness/power_sim.py` was run with 30 assets, 37 five-session-separated event episodes, horizon 5 / NW lag 4, signal autocorrelation `rho=0.20`, default null-rank IC SD `1/sqrt(29)`, 5,000 simulations, and seed `20261111`. This deliberately treats each episode as one observation; it does not model clustered SIC2 errors, event-day common shocks inside an episode, or Holm. At an illustrative mean IC of **0.020**, unadjusted `P(NW t >= 2)` is **13.0%**, and the unadjusted 80%-power MDE is **0.1017**. At **0.074**, used only as a comparator to the weekly rank-weighted-top-half threshold in the criterion-4 shape audit (not as a literature estimate), power is **60.0%**. The episode count, 0.020 and 0.074 are planning inputs; none is an observed effect.

R6 contains at least 24 endpoints, so Holm's first-step p threshold is `0.05/24 = 0.00208`, stricter than the simulator's raw `t >= 2` rule. The 37 episodes also share dates and common market shocks, making the nominal simulation optimistic. No cluster-adjusted design shows that the relevant effect is measurable at this breadth.

**Verdict: FAIL.** There is no independently sourced effect in the required unit, and the sensitivity simulation has low power even at an external weekly hurdle before Holm and common-shock dependence.

## 5. Criterion-4 portfolio feasibility first

A hypothetical Dow implementation would rank eligible point-in-time constituents by their negative market-model residual on each qualifying event date, hold the five most negative residual names long for five sessions, and use EW30 as the benchmark. Top five of 30 has 83.3% active share. Apply 0.05% per side costs to actual total traded notional. Under the current coordinator feasibility screen, require expected Dow excess Sharpe of at least 0.8 after costs while maintaining average total-notional turnover at or below 20% per month. No signal outcomes or portfolio accounting were computed.

The 2019 paper reports a different 40-day beta-adjusted outsider portfolio across multiple ETFs, not a Dow top-five expected excess Sharpe or rank IC; no defensible translation to the ≥0.8 excess-Sharpe requirement is possible. Replacing one name in an equal-weight top-five book trades 40% of NAV (20% sale plus 20% purchase) at a rebalance, above the current 20%-per-month screen if done monthly; slower turnover would dilute the event response. There are only 37 five-session episodes in the input-only development count and clustered dates can coincide with major market news. Actual turnover, costs as a share of edge, and Sharpe remain unknown, not zero.

The idea therefore fails the criterion-4-first rule: no independent study provides the needed Dow portfolio effect, and the direct event sample does not establish the required low-turnover, high-Sharpe feasibility. It should not be sent to an outcome runner just to discover its returns.

**Verdict: FAIL — criterion-4 feasibility unsupported.**

## 6. Holdout availability and protocol

No holdout path or holdout-specific input is needed for this screen, and no sealed file was read, opened, downloaded, or queried. If a future independent review ever clears all prior gates, only the coordinator may execute frozen code once under goal criterion 5; any L4 availability check must remain roster/row-count only. This screen authorizes no holdout run.

**Verdict: PASS for no-access protocol; no holdout test is authorized.**

## Final screen decision

**Overall: STOP — FAIL.** The 2019 literature gives a close mechanism precedent, and the date-filtered ETF/Dow inputs exist, but volume is unsigned, direct post-2020 mega-cap evidence is missing, effective event breadth is only 37 clusters under the stated rule, synthetic power is inadequate, and criterion-4 turnover/Sharpe feasibility is unsupported. The screen does not authorize a variant, preregistration, or runner.

Evidence that could change the decision would include a separately replicated post-2020 large-cap event effect with a matched rank-IC or portfolio-Sharpe estimate, demonstrated directionally meaningful ETF pressure rather than volume alone, validated PIT market-model coverage, a cluster-aware power result that clears the current Holm family, and a turnover design that plausibly meets the ≤20% monthly and excess-Sharpe ≥0.8 gates. Reviewer/date: worker screen, 2026-11-11.

### Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
