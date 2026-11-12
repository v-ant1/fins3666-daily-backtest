# AQ — Scheduled commodity-index roll pressure into Dow energy and materials

**Status: SCREEN ONLY.** No commodity pressure signal, stock returns, ICs, portfolio results, or holdout data were calculated. The proposed direction fails the evidence, breadth, and criterion-4 gates; do not preregister or run it.

## Identity and immutable-path preflight

- **Short name and mechanism:** AQ / roll pressure. Predictable long-only commodity-index futures rolls may temporarily move nearby versus deferred futures prices; if this reveals a common demand shock, exposed Dow energy and materials firms might respond through earnings expectations or investor repricing.
- **Exact new output path:** `r6_ideas/AQ_roll_pressure.md`.
- **Path preflight:** the exact target did not exist before writing. No prior screen uses the `AQ_roll_pressure` filename.
- **Development dates:** 2020-11-27 through 2026-10-30; earliest permissible worker-path date is **2020-11-27**. The small Yahoo requests were bounded at read time to `period1=1606435200` (2020-11-27 UTC) and `period2=1793404800` (exclusive 2026-10-31 UTC).
- **Path/data checks:** only project workflow/prereg instructions, the screen template, synthetic hurdle report, non-outcome r6 idea screens, the power simulator, and four development-window continuous-futures timestamp fields were accessed. No path into a holdout folder or pre-cutoff project data was opened. `R5_FINAL.md` and outcome-bearing decision-log lines were not opened, so round-history novelty coverage is incomplete.
- No ambiguous input dates were used. The continuous-futures pull is not contract-level GSCI holdings or order flow; this limitation is retained below rather than silently treated as equivalent.

## 1. Overlap with prior work

I searched the existing `r6_ideas/*.md` titles and text for commodity futures, index rolls, and cross-asset pressure. The nearest screens are:

- `U_crossasset.md` proposed daily OHLCV pressure in continuous commodity futures interacted with issuer exposure, and separately CFTC positioning. Its daily-futures proposal was killed because free continuous-contract data do not establish a point-in-time contract roll tape or issuer-specific exposure panel, and the independent cross-section is small.
- `U_COT_redteam.md` killed COT-to-equity mapping: aggregate futures positions are not issuer-linked stock buying pressure and sector labels overstate independent breadth.
- `Y_seasonal_flows.md` and `AH_treasury_auction.md` are calendar or macro-flow screens, but not a commodity index futures roll.

AQ's only genuine difference from U is the **pre-known five-session index-roll calendar** and the hypothesis that large, scheduled futures trades create a temporary *commodity-curve* pressure shock. The target equity mapping, commodity-to-issuer transmission, and few common shocks are substantially the same as U. It is a narrow input/event-timing refinement, not a demonstrated new stock-pressure mechanism. Since the R5/decision registry was not reviewed under the no-outcomes restriction, I cannot certify whole-project novelty.

**Verdict: FAIL.** Partial novelty relative to U; not enough to clear the mechanism gate, and full registry novelty remains unverified.

## 2. Exact pressure measure and dated data source

A future research design would define the index-roll source as the preannounced S&P GSCI five-session roll window: on each S&P GSCI business day in the window, contracts are rolled from the nearby to the next contract. A possible *input-only* pressure measure would be the signed notional roll flow per commodity, normalized by that contract's prior 20-session volume, multiplied by a point-in-time issuer exposure sign/weight from the latest public filing. A producer and a cost-sensitive user would have opposite exposure signs. This is a proposed construction, **not computed here**; free source data reviewed did not provide the actual daily index quantities needed to calculate it.

S&P DJI's [GSCI methodology](https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-gsci-quick-guide.pdf) describes a five-business-day roll from the fifth through ninth GSCI business days of each month (with methodology exceptions). [Mou (2010)](https://doi.org/10.2139/ssrn.1716841) studies the futures-curve effect of this rolling activity. The public methodology provides the schedule, not the daily point-in-time contract quantities held and traded. Index levels and continuous-futures prices are not substitutes for those quantities.

The screen did a date-bounded, timestamps-only availability probe on Yahoo continuous futures for `CL=F`, `NG=F`, `HG=F`, and `GC=F`: each returned 1,493 daily timestamps from 2020-11-27 through 2026-10-30. I did not inspect OHLCV values. Source: [Yahoo Finance chart endpoint](https://query1.finance.yahoo.com/v8/finance/chart/CL%3DF?period1=1606435200&period2=1793404800&interval=1d). This confirms that a public proxy's dates exist; it does not show GSCI roll size, contract-switch details, or issuer exposure.

A non-lookahead formation rule, if the required inputs ever became available, would use the roll calendar announced in advance and the prior session's public positions/contract-volume data; any market response would be assessed only from the next regular U.S. equity session onward. Daily signed source quantities and filing-availability timestamps would be required to name exact signal timestamps. The proxy data do not support that rule as specified.

**Documented evidence and limits:**

- Mou (2010), *Limits to Arbitrage and Commodity Index Investment: Front-Running the Goldman Roll*, is an SSRN working paper using commodity-futures data from 2000 to March 2010. It reports economically/statistically significant futures price impact and futures strategies; it does **not** report Dow-stock ICs, equity spillover, or post-2020 mega-cap results. The sample predates the permitted project window but is cited as literature only; no pre-cutoff project data were accessed.
- Stoll and Whaley (2010/2011), [*Commodity Index Investing: Speculation or Diversification?*](https://doi.org/10.3905/jai.2011.14.1.050), evaluate commodity-index trading and conclude that rolling or establishing positions has little impact on futures prices. This is a relevant counterweight, not equity-spillover evidence.
- Tang and Xiong (2010), [*Index Investment and Financialization of Commodities*](https://doi.org/10.3386/w16385), document greater comovement among commodity futures, particularly index constituents, in the early-2000s/2008 period. This may support common commodity shocks but does not identify a direction into individual equities.
- Kilian and Park (2009), [*The Impact of Oil Price Shocks on the U.S. Stock Market*](https://doi.org/10.1111/j.1468-2354.2009.00568.x), find that structural oil shocks have different U.S. stock-market effects. These are oil-news/supply-demand shocks, not scheduled GSCI roll pressure.

No cited work establishes a positive stock-level signal from GSCI roll pressure in post-2020 mega-caps. There is no defensible sourced rank-IC or signed equity-spread effect for this exact mechanism.

**Verdict: FAIL.** The calendar and futures-market literature exist, but the required roll-quantity and issuer exposure data are not demonstrated as free, point-in-time inputs; the documented effect is in futures rather than the target equities.

## 3. Point-in-time coverage and independent breadth

Input-only coverage from this screen:

| Quantity | Count | How obtained / limitation |
|---|---:|---|
| Continuous-futures daily timestamps | 1,493 per symbol × 4 symbols (`CL=F`, `NG=F`, `HG=F`, `GC=F`) | Date-filtered Yahoo requests; timestamps only, 2020-11-27–2026-10-30. No values inspected. |
| Full scheduled monthly roll episodes in the allowed sample | 71 | Calendar count, December 2020 through October 2026; the November 2020 roll window predates the lower bound. Five trading sessions per nominal window, subject to index-calendar adjustments. |
| Roll-window session dates | Up to 355 | 71 × five per nominal window; not independent observations, and exact official holiday/exception schedule was not reconstructed. |
| Eligible point-in-time Dow names with verified commodity exposure | 0 verified | No issuer filings or exposure panel was coded in this screen. The intended universe would be Dow 30, but a usable name count cannot be claimed from sector labels alone. |
| Nonmissing issuer-level roll signals | 0 | No source quantity × issuer exposure signals were constructed. |
| Independent equity exposure clusters | At most 2 target groups (energy, materials), not measured | These are the requested broad sectors; each monthly roll is a common source shock. Four commodity contracts do not create four independent equity experiments. |

The actual GSCI includes more commodities than these four probe symbols; the four are just a cheap timestamp check, not a complete source universe. Continuous-futures vendors can back-adjust and change their contract stitching, and timestamps do not prove that the same listed maturity received the GSCI roll. The source's roll calendar is known in advance, but the traded quantities are missing. Dow membership and each firm's producer/input role change over time; current-sector labels or a present-day exposure map would introduce survivorship and classification error. No point-in-time filing map or coverage rate was verified.

The Mou study's futures sample is not an equity sample and predates 2020. The counterevidence from Stoll and Whaley addresses futures market impact, while Tang-Xiong concerns futures comovement; neither supplies the required post-2020 stock cross-section, event count, or equity estimator. No eligible stock-level effect estimate is available to transfer.

**Verdict: FAIL.** At most 71 monthly common-shock episodes and no verified nonmissing issuer signals; effective equity breadth is much smaller than the nominal Dow/S&P constituent count.

## 4. Effective breadth and power at a sourced plausible effect

There is no published, matching **equity** effect size to use as a plausible positive rank IC. Mou's reported arbitrage returns are for commodity-futures strategies, not equity ICs, and cannot be translated into one. I therefore ran sensitivity scenarios, explicitly not an estimated or literature-supported stock effect, using `r4_harness/power_sim.py`:

- monthly observations: 71 roll episodes; five-session forecast horizon; date-level signal autocorrelation 0.5; Newey-West lag 4; 5,000 synthetic draws; seed 20261111; trial planted mean rank IC 0.02;
- optimistic nominal breadth scenario: 500 names, default null rank-IC SD `1/sqrt(499)`;
- conservative common-shock stress: six effective cross-sectional units (an assumption for a few exposed subindustries), default SD `1/sqrt(5)`.

| Synthetic breadth assumption | Probability NW t ≥ 2 at planted IC 0.02 | Mean effective date count | 80% MDE for NW t ≥ 2 |
|---|---:|---:|---:|
| 500 nominal stocks | 72.18% | 31.91 | 0.0225 |
| 6 effective exposure units | 8.32% | 31.91 | 0.2250 |

The nominal-500 result is not a credible design power estimate: all names share the same monthly index roll and exposure groups, so the name count does not supply 500 independent flow events. Even the six-unit scenario tests a simple t≥2 threshold, which is less stringent than a one-sided p<0.05 after Holm across the R6 family; a Holm cutoff would require a still larger effect. The 0.02 planted value is merely an illustrative sensitivity, not a sourced effect. Since the signal's nonmissing exposures and correct event sizes are unknown, the actual power cannot be estimated responsibly.

**Verdict: FAIL.** No matching sourced effect exists, and common roll timing leaves a small effective cross-section and only 71 monthly episodes.

## 5. Criterion-4 portfolio feasibility first

A hypothetical implementation would assign each Dow name the fixed, filing-based signed commodity exposure × roll pressure and rebalance a rank-weighted top-half long-only book monthly. It would target at least 50% active share (the synthetic `RankTopHalf` shape has 55%), compare with EW30, and charge 0.05% per side. The synthetic shape report uses 91% total-notional turnover per monthly rebalance at signal autocorrelation 0.5; under its assumptions, modeled costs are 4.2% of gross active edge. This is a design benchmark, not an AQ turnover measurement.

The synthetic [criterion-4 shape bound](../report_drafts/CRITERION4_BOUND_BY_SHAPE.md) requires a **monthly RankTopHalf mean rank IC of about 0.160** under the autocorrelation-0.5 assumptions for 80% power against the fixed Sharpe/one-sided Holm criterion. No directly relevant paper reports an equity IC or long-short spread for GSCI roll pressure, let alone a value near 0.160. Mou's futures-curve strategy return cannot be compared as if it were a Dow rank IC. Stoll and Whaley's conclusion that commodity-index rolling has little effect in futures further weakens the premise. After source and issuer mapping costs, there is no defensible way to infer positive net EW30 excess return, a higher Sharpe, and Holm-significant block-bootstrap evidence.

**Verdict: STOP — FAIL: criterion-4 infeasible.** The fixed goal is not plausibly supported by any documented equity effect for this signal; no portfolio test is warranted.

## 6. Holdout availability and protocol

No holdout path, data, or holdout-specific source was opened. This direction would not require a new holdout source if it first passed development gates and the exact commodity contracts, point-in-time issuer exposure map, and schedule were available consistently in both periods; that condition is not met. No holdout availability claim is made.

Only after coordinator review and a frozen design could the coordinator perform the project’s availability-only roster/row-count check, then, if approved, run the frozen candidate once on the sealed Dow 30 holdout. This screen authorizes neither availability inspection nor a holdout run.

**Verdict: FAIL for advancement.** Later protocol remains coordinator-controlled; holdout availability is unestablished.

## Final screen decision

**Overall: STOP — FAIL.** GSCI rolling is a distinct, preannounced source-side futures-market event, but the published evidence is mixed and does not establish a measurable stock-side buying-pressure spillover. Free continuous-futures timestamps do not supply roll quantities or point-in-time issuer exposures; effective breadth is limited to at most a few common-shock groups; no matching equity effect supports power or the monthly IC hurdle.

Evidence that could change this decision: a free or approved point-in-time series of actual GSCI contract roll quantities and maturities; a reproducible filing-timestamped producer/input exposure panel with substantial Dow coverage; and independent post-2020 large-cap research documenting a stock-level signed effect of roll flow that approaches the criterion-4 bound. Such evidence would still require a new screen and coordinator review before preregistration.

**Reviewer/date:** dispatched worker; 2026-11-11.

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.

