# R2 — Aggregate dividend-payment pressure into index constituents

**Verdict: FAIL-GATE for criterion 4; retain only as a low-cost, input-feasibility idea if the coordinator wants a mechanism-only study.** My subjective chance that this direction clears the complete R6 gates, including a six-year Dow portfolio beating EW30 with a Holm-significant result, is **about 2%**. I used no project outcomes, no return series, and no holdout data.

## Proposed direction

Test whether large, publicly scheduled aggregate cash-dividend payment days create reinvestment demand that reaches broad-market constituents. Define a daily aggregate payment-yield shock from dividend cash amounts whose payment dates were already announced by the prior close, scaled by the point-in-time market capitalization of the covered universe. The cross-sectional transmission score is this common shock interacted with each point-in-time Dow constituent’s index/passive-flow exposure; in a future frozen design, use available point-in-time Dow index weights as the transparent exposure proxy. The mechanism outcome would be next-session and short-window constituent returns, clustered by SIC2 and calendar date; the portfolio question is whether tilting toward the most exposed Dow names on high-payment days adds value to EW30.

This is a proposed design, not a result. The paper identifies aggregate market-level returns around payment flows; it does not show that high-index-weight Dow constituents outperform EW30 on those dates. A market-wide return forecast can be captured by a broad market holding, but does not by itself produce benchmark-relative alpha.

## Gates (a)–(e)

### (a) Literature and large-cap evidence

Hartzmark and Solomon’s *Predictable Price Pressure* (NBER Working Paper 30688, 2022) reports that dividend payments announced weeks earlier forecast value-weighted market returns: top-quintile payment days have returns four times those of the lowest quintile. In its market-return regressions, the top ten payment days have roughly **9.8–11.6 bp** higher value-weighted daily returns than other days, with a reported *t* of 2.39 for the 9.8 bp no-controls estimate (the year-by-month estimate is 11.6 bp); top-two-weeks-per-year days account for about 12% of the equity premium. The authors also report international evidence and market-level price multipliers of 1.5–2.3. Those estimates support a predictable aggregate demand channel, but are not a constituent-level return spread, a post-2010-only estimate, or a strategy Sharpe. The main US CRSP sample runs 1926-2018, so it includes large firms and some post-2010 years, but the paper reports no separate post-2010 estimate and does not establish recent mega-cap stability.

Hartzmark and Solomon’s separate *The Dividend Month Premium* (JFE, 2013) is adjacent evidence, not evidence for this aggregate signal: it studies own-stock dividend months in CRSP, January 1927–December 2011, and reports 37–53 bp monthly abnormal returns for simple difference portfolios, with post-ex-date reversals. It should not be used to inflate the expected aggregate-payment strategy’s return or Sharpe.

**Gate status: partial.** The pressure mechanism is credible and the payment calendar is knowable in advance, but the required transmission from aggregate market demand to *cross-sectional Dow excess returns over EW30* remains undocumented.

### (b) Frozen design and timing

Only dividend amounts and payment dates publicly declared by the prior session may enter the aggregate signal. A payment record without a usable prior declaration timestamp is excluded; no backfilled knowledge of future payment dates. Use a single short response window (payment date and next trading session) for the mechanism test, with the exact cumulative payment-yield formula, universe coverage and exposure proxy frozen before any outcome access. Exclude the directly paying issuer from the peer response as a robustness definition only if preregistered; do not change the primary sign or window after results.

For the portfolio, a feasible low-turnover interpretation is to update exposure monthly, keep holdings between updates, and hold the five Dow names with the largest point-in-time index/passive exposure only when the next month’s already-announced aggregate payment yield exceeds a predeclared threshold; otherwise retain EW30. This is a tentative implementation choice, not demonstrated to keep realized turnover under the criterion. A static high-weight tilt alone is not a pressure signal and cannot be presented as evidence of transmission.

### (c) Synthetic S&P 500 power screen (SIC2-cluster stress)

I ran `r4_harness/power_sim.py` with design assumptions only: 500 names, 1,500 calendar sessions, two-session horizon (Newey–West lag 1), signal/effect-series autocorrelation 0.20, nominal event rate 50/252 per session, negative-binomial date-clustering shape 0.5, and 500 simulations at seed 20261111. To stress SIC2 clustering, I used 54 effective groups, 499 names (about 9.24 names/group), and assumed within-industry residual correlation 0.15, giving the cluster-adjusted IC/effect SD `sqrt((1 + (9.24−1)×0.15)/(54−1)) = 0.2054`. The simulator returns effective N about **193**, 80%-power MDE **0.0370**, and **32.6%** power at a hypothetical planted event effect/IC of 0.020 (Monte Carlo SE 0.021).

The 0.020 is only a sensitivity point; Hartzmark–Solomon’s market-return coefficients cannot be converted into a SIC2-clustered cross-sectional rank IC. The assumed SIC2 correlation and event clustering are also planning choices, not estimates from this project. Thus the simulation quantifies a design’s weakness, not expected empirical power at a known effect. **Gate fails as evidence of adequate power:** no documented cross-sectional effect size is available to show that the mechanism clears the 0.037 MDE.

### (d) Criterion-4 feasibility, turnover and cost hurdle

The source’s 9.8–11.6 bp high-payment-day market-return difference is a **time-series market statistic**, not active return of exposed Dow stocks versus EW30. It supplies no defensible expected Dow excess Sharpe. The evidence-based base case is therefore **zero expected excess Sharpe versus EW30** (incremental alpha not established), with expected one-sided test *p* around 0.5 under a zero-edge null. For scale, a six-year monthly sample has only about 72 observations: an annualized Sharpe of 0.8 corresponds to a conventional *t* near `0.8×sqrt(6)=1.96`; clearing a nine-slot Holm first-step level of 0.05/9 requires a rough annualized Sharpe around `2.77/sqrt(6)=1.13`, before block-bootstrap and selection effects. The portfolio must also exceed the approximately **0.9 EW30 Sharpe** recorded in decision 76, so a merely positive or market-level effect is insufficient. I estimate the chance of both a positive excess and Holm-significant criterion-4 result at **under 2%** based on the cited evidence; no defensible point estimate for Dow alpha or bootstrap *p* can be derived from the paper.

If the portfolio is rebalanced monthly, cap total traded notional at **20% of NAV per rebalance** (0.05% per side; turnover means buys plus sells in aggregate, so do not double it). The harness helper’s illustrative rank-IC cost floors for a top-sixth book are:

| Assumed 21-session cross-sectional return dispersion | Cost-only break-even rank IC at 20% turnover |
|---:|---:|
| 5% | 0.00139 |
| 10% | 0.00069 |
| 15% | 0.00046 |

These are sensitivity calculations from `break_even_rank_ic(turnover=0.20, return_dispersion=..., cost_per_side=0.0005, top_fraction=1/6)`, not measured return dispersions. The mapping is `IC × dispersion × sqrt(12) × (0.5−top_fraction/2)` for gross active return per rebalance, versus costs `0.0005×turnover`; dispersion must be estimated input-only from eligible staged bars before preregistration. The cost floor is modest, but costs do not address the main problem: lack of documented EW30-relative alpha and the much higher Holm hurdle.

### (e) Data, novelty and feasibility

A quick input-only check used Nasdaq’s free dividend-history endpoint for five Dow names, restricting payment dates to the development window 2020-11-27 through 2026-10-30. It returned 23 AAPL and 24 MSFT payment-date rows; the same endpoint returned no dividend rows for JPM, KO and CAT, so those three are **unresolved endpoint coverage**, not evidence of zero dividends. Endpoint examples: [AAPL dividend history](https://api.nasdaq.com/api/quote/AAPL/dividends?assetclass=stocks) and [MSFT dividend history](https://api.nasdaq.com/api/quote/MSFT/dividends?assetclass=stocks). The pull read dividend metadata only (declaration/payment dates and cash amounts), not prices or returns; it wrote no local data file. Nasdaq’s per-symbol pages demonstrate a free starting source, not complete, point-in-time historical coverage for an S&P-wide aggregate. A full design needs a broad issuer universe, reliable dividend cash amounts, dates of public declaration, historical identifiers and coverage checks; it must exclude records not demonstrably public by formation.

The new angle is a **common aggregate cash-flow shock transmitted to constituent stocks**, rather than own-stock dividend-month demand, insider/short/volume pressure, return-correlation diffusion, industry peers or a 13F ownership network. The novelty is real but the exposure bridge is weak: point-in-time index weight is only a proxy for where dividend reinvestment flows go, and no documented source here validates that proxy for Dow-versus-EW30 performance. **Gate status: FAIL-GATE on criterion 4 and incomplete broad-data feasibility.** Do not freeze a portfolio preregistration unless an input-only full-universe payment-calendar audit first confirms reliable announcement timing and the coordinator accepts a mechanism-only test with the stated low chance of meeting criterion 4.

## Verdict

This is the strongest literature-backed dividend-pressure mechanism in the current R round, but it does **not** currently satisfy the binding feasibility gate. The cited evidence establishes predictable aggregate market returns, not a high-index-weight constituent spread or a Dow excess Sharpe above EW30; under a six-year, Holm-corrected portfolio test, that distinction is decisive. Proceed only if the goal permits a deliberately low-probability mechanism study and the full-universe free input audit passes before any outcomes are opened.

## Sources

- Hartzmark, S. M. and D. H. Solomon (2022), “Predictable Price Pressure,” NBER Working Paper 30688. [Paper and abstract](https://www.nber.org/papers/w30688); [full PDF](https://www.nber.org/system/files/working_papers/w30688/w30688.pdf).
- Hartzmark, S. M. and D. H. Solomon (2013), “The Dividend Month Premium,” *Journal of Financial Economics* 109(3), 640–660. [Publisher page and DOI 10.1016/j.jfineco.2013.02.015](https://doi.org/10.1016/j.jfineco.2013.02.015).
- Nasdaq, historical dividend calendar endpoints (example issuer pages linked in (e)); free source access checked 11 November 2026.
