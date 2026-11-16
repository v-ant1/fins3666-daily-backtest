# R6 Idea Screen AF — 52-week-high price barrier

**Verdict: STOP — FAIL.** The 52-week-high anchor has published evidence for medium-horizon momentum and a recent paper finds it conditions one-month momentum/reversal, but this is already close to prior own-stock and peer-high screens. The evidence does not establish a post-2020 Dow-size rank IC large enough for the fixed criterion-4 hurdle, and the six-year monthly sample has weak power after serial dependence and Holm correction.

**Scope and safety.** This is a screen only. No signal values, forward returns, portfolio returns, ICs, or other project outcomes were computed or inspected, and no holdout data were accessed. The only local data check used the date column of development price files, filtered from 2020-11-27 onward; it did not read price values. A synthetic-only call to `r4_harness/power_sim.py` used design assumptions, not project observations.

## Identity and immutable-path preflight

- **Proposed short name and mechanism:** AF — investors anchor on the salient one-year price maximum and adjust slowly to positive information; proximity to the 52-week high may therefore mark persistent buying pressure and continuation.
- **Exact new output path:** `r6_ideas/AF_52wk.md`.
- **Path preflight:** the exact target did not exist before this screen. The output name was not found in the existing R6 directory or decision registry.
- **Closest prior-name check:** Decision 184 assigned the 52-week-high barrier idea to Round AF. The date-bounded development price files cover 2021-01-04 through 2026-10-30; the screen's earliest permissible worker-path date remains **2020-11-27**.
- **Path/date check:** no worker input or output path used holdout data or an earlier price-data date. No sealed-holdout file was opened.

## 1. Overlap with prior work

The nearest screens are `r6_ideas/B.md`, which discussed standalone 52-week-high anchoring but did not advance it, and `r6_ideas/E.md`, which rejected a *peer* 52-week-high breadth score multiplied by peer buying pressure. AF's candidate is the simpler own-stock pressure proxy: distance of a stock's month-end close from its trailing 52-week high. It does not add a network or volume-pressure component. Its economic interpretation is continuation near the barrier, not a distinct measurement of signed order flow.

This is not a renamed signal relative to E's peer-aggregation formula, but it substantially overlaps B's standalone idea and the core George–Hwang characteristic. The specific Dow, post-2020 monthly portfolio has not been run, yet novelty is weak and the direction risks becoming an ordinary momentum tilt rather than measuring pressure spreading through related assets.

**Verdict: FAIL.** The signal is technically distinct from E's peer composite, but it is not sufficiently novel relative to the earlier standalone 52-week-high discussion and does not add the network mechanism central to the thesis.

## 2. Exact pressure measure and dated data source

If reconsidered, use one fixed signal at each month-end formation close:

\[
H_{i,t}=P^{split}_{i,t}/\max(P^{split}_{i,d}:d\in[t-251,t]),
\]

where `P_split` is the split-adjusted daily close, and the denominator includes the formation date and the preceding 251 completed US trading sessions. A higher value means the stock is closer to its one-year high; the prespecified sign is **positive**. Form monthly, execute no earlier than the next session open, and evaluate the next 21 US sessions. Require a full 252-session trailing window, and exclude any formation with a missing observation or unresolved corporate-action adjustment. There is one variant and no window, sign, or horizon sweep.

The local development source is the daily OHLCV panel in `repo/prices-daily/` (33 symbol files, including non-Dow/reference series); its supplied dates start 2021-01-04, so the first full 252-session formation cannot occur until roughly late December 2021. This is too late to use pre-2020-11-27 history for warm-up. These files have an `adjclose` field, but the screen did not verify whether a split-adjusted high/close series is consistently available or whether `adjclose` incorporates dividends; a frozen implementation must use a split-adjusted *price* ratio and document corporate-action treatment.

The core academic evidence is George and Hwang, [“The 52-Week High and Momentum Investing,” *Journal of Finance* 59 (2004), 2145–2176](https://doi.org/10.1111/j.1540-6261.2004.00695.x). They find that nearness to the 52-week high explains much of conventional momentum's predictive power, improves on individual and industry past-return measures, and does not exhibit long-run reversal in their sample. Their US CRSP study predates 2010, so it is mechanism evidence rather than a post-2020 estimate.

Recent evidence is mixed and conditional. Chen, Stivers, and Sun, [“Short-term Momentum and Reversals, Turnover, and a Stock’s Price-to-52-week-High Ratio,” *Journal of Empirical Finance* 79 (2024), article 101556](https://doi.org/10.1016/j.jempfin.2024.101556), report that one-month stock-return behavior shifts from reversal toward momentum when both turnover and price-to-high are relatively high; the effect is robust to their subperiod analyses and risk adjustments. This supports a mechanism among liquid names but is not an unconditional 52-week-high rank-IC estimate, and the turnover interaction is not part of this one-signal candidate. Lasfer and Ye, [“Corporate insiders’ exploitation of investors’ anchoring bias at the 52-week high and low,” *Financial Review* 59 (2024), 391–432](https://doi.org/10.1111/fire.12371), use US CRSP observations over 1994–2018 and find the standalone price-high relation persists in that sample, while insider-conditioned trades contain additional information. Their sample includes post-2010 years but does not isolate a post-2020 Dow effect.

**Verdict: PASS as a precisely definable, development-window signal; FAIL as a verified measure of buying pressure.** Price proximity is observable and timestamped, but it is a price characteristic, not transaction-level signed buying pressure.

## 3. Point-in-time coverage and independent breadth

The input-only coverage check read only date columns from `repo/prices-daily/*.csv`, applying the 2020-11-27 lower bound. The 33 series shared 1,464 dated sessions from 2021-01-04 through 2026-10-30, with 1,464 rows per series on the common grid. A 252-session warm-up leaves 1,213 daily formation endpoints after the lookback requirement. At month-end, the approximate usable window is December 2021–October 2026, or **59 month-end formations**. These are date-grid counts, not signal-availability or performance counts.

| Coverage quantity | Input-only result | Interpretation |
|---|---:|---|
| Price-series files | 33 | Includes benchmark/reference and supplemental tickers; not 33 Dow constituents |
| Common development sessions | 1,464 | 2021-01-04 to 2026-10-30; date column only |
| Sessions remaining after 252-session warm-up | 1,213 | Calendar-grid capacity, not nonmissing signal count |
| Candidate month-end dates after warm-up | about 59 | December 2021–October 2026 |
| Dow names at each point-in-time formation | 30 intended | Requires a separate point-in-time roster join before testing |
| Nonmissing signal observations inspected | 0 | Signal values were not calculated |
| Independent events | Not applicable | This is a continuously ranked characteristic, not an event study |
| Independent SIC2 clusters verified | 0 | No SIC count was inferred; dependence may reduce effective breadth further |

The downloaded panel appears to provide a common date grid but the screen did not inspect numeric price fields, calculate the high ratio, or confirm split adjustment. Ticker files alone do not solve historical constituent membership, delisted-name coverage, or corporate-action mapping; survivorship can remain if the roster and price panel are not joined point-in-time. Across a 30-stock Dow cross-section, SIC2 dependence and shared market shocks mean 30 names cannot be treated as 30 independent observations each month. No signal nonmissingness or cluster count is claimed.

**Verdict: FAIL.** Input dates exist for a mechanically useful warm-up, but there are only about 59 monthly time points, and the point-in-time universe, adjusted-price availability, nonmissing signals, and SIC2 breadth have not been established.

## 4. Effective breadth and power at a sourced plausible effect

George–Hwang's published result is a medium-term portfolio/momentum finding; it does not report a monthly rank IC for a 30-name Dow. The 2024 Chen–Stivers–Sun paper documents conditional one-month continuation at high turnover and high price-to-high ratio, but it does not provide a directly transferable rank IC for the unconditional signal proposed here. The 2024 Financial Review study conditions on insider purchases or sales and likewise cannot supply the candidate's standalone effect. Thus the best defensible plausible effect range for this exact monthly mega-cap signal is **unknown**. For design sensitivity only, 0.01 and 0.02 mean rank ICs are illustrative low-effect assumptions, not evidence or project estimates.

I ran the synthetic harness with `universe_size=30`, `n_dates=59`, `horizon=21`, Newey–West lag 20, cross-sectional null IC SD `1/sqrt(29)`, signal autocorrelation `rho=0.5`, 5,000 simulations, and seed `20261111`. The harness estimates 21 effective time observations after its lag-20 design effect. At planted mean rank IC **0.02**, power for the harness's unadjusted one-sided NW `t >= 2` rule is **18.86%**; its approximate 80%-power MDE for that rule is **0.115**. This is a synthetic result only. It does not account for SIC2 clusters or multiplicity and is therefore optimistic relative to the actual decision rule.

The R6 family has continued to grow; use at least 24 endpoints for planning. The criterion-4 shape audit gives a monthly rank-weighted top-half hurdle of approximately **0.160 IC** at `rho=0.5` for its 24-test six-year synthetic design. The exact AF portfolio is not registered; this is a comparator, not a new relaxed hurdle. Holm's first-step one-sided cutoff is `0.05/24 = 0.00208`, stricter than the harness's `t >= 2` threshold. Neither the historical literature nor this screen's assumptions demonstrate an effect close to the 0.160 portfolio hurdle.

**Verdict: FAIL.** No matching published effect size supports a useful test, and even the optimistic synthetic sensitivity implies low power well below the monthly criterion-4 comparison bound.

## 5. Criterion-4 portfolio feasibility first

The only candidate portfolio would rank the point-in-time Dow 30 monthly by the own-stock 52-week-high ratio and hold a fixed top-half rank-weighted long-only book, compared with EW30. The shape audit's rank-weighted top-half active share is 55%, meeting the 50% floor. Rebalance monthly, charge 0.05% per side on buys and sells, and require total-notional turnover no greater than 50% per rebalance unless costs are demonstrated below one quarter of gross edge. Any missing-price rule and benchmark cohort must follow the frozen decision-63 carry-and-delayed-sale rule if the idea ever reaches preregistration.

There is no sourced expected rank IC for this 30-name implementation, so expected net excess return and Sharpe cannot be responsibly translated. The high-high/turnover conditional results in the 2024 paper are not an estimate for top-half Dow weights, and its gross effects cannot be relabeled as this candidate's IC. The monthly hurdle proxy (~0.160 at `rho=.5` in the shape audit) exceeds the optimistic synthetic t≥2 MDE (~0.115); Holm, cluster dependence, implementation costs and the criterion's Sharpe/bootstrap conditions only make the hurdle harder. Turnover for this signal was not computed, and no cost savings may be assumed.

**Verdict: FAIL — criterion-4 feasibility unsupported.** The fixed goal criterion is not shown to be attainable from the available evidence.

## 6. Holdout availability and protocol

This screen did not use a holdout path or any holdout-specific input. If an independently sourced signal and all prior gates later pass, only the coordinator may run the frozen code once on the sealed Dow holdout under goal criterion 5; before that, L4 may check availability only (roster/row counts) without opening prices or computing returns. No worker should read sealed data.

**Verdict: PASS for this screen's no-access protocol; no holdout test is authorized.**

## Final screen decision

**Overall: STOP — FAIL.** The high-price barrier is a plausible behavioral mechanism, but this proposed own-stock feature overlaps prior R6 discussion, is not a direct measure of signed buying pressure, has no directly comparable post-2020 mega-cap effect-size evidence, and appears underpowered against the monthly criterion-4 bound.

Evidence that could change the decision: a genuinely independent large-cap study reporting post-2010 cross-sectional rank IC for the standalone 52-week-high ratio at a monthly horizon; date-safe point-in-time Dow roster and split-adjusted price coverage confirming the signal can be measured; realistic turnover and transaction-cost evidence; and a preregistered power design showing the effect can clear the current Holm-adjusted hurdle. No variant is authorized now.

Reviewer/date: worker screen, 2026-11-11.

### Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
