# F1 — Earnings-announcement peer-pressure spillover

**STATUS: DRAFT - NOT FROZEN.** This design contains no F1 outcome results. The coordinator may freeze it only after the listed inputs and coverage gates are checked without outcomes and before any return, IC, event-response, or portfolio statistic is computed.

## Hypothesis, sign and horizon

A positive first-session market response to a Dow issuer's earnings announcement predicts positive next-week returns in its other Dow names connected through the latest public common-owner 13F network; a negative response predicts negative peer returns. The proposed channel is short-horizon information/pressure transmission. Event returns are a pressure proxy and do not distinguish information from uninformed demand. The primary horizon is five trading sessions.

## Universe, inputs, timing, and network

- **Prices and roster:** point-in-time Dow 30 daily OHLCV, development period 2020-11-27 through 2026-10-30. Use the same date-specific Dow roster in the coordinator's one-shot holdout. Do not load or calculate any worker-side Dow prices, returns, or signals before 2020-06.
- **Earnings-event input:** L4 builds `r4_L4/data/8k_item202_events.csv` from free SEC EDGAR submissions and archived Form 8-K filings for each point-in-time Dow issuer. Required fields: CIK, point-in-time ticker/security mapping, accession, form, Item 2.02 flag verified from filing text/index, SEC filing date, EDGAR acceptance timestamp, release timestamp if explicitly stated in the furnished exhibit, quarter/year indicator, and filing URL. Deduplicate amendments and multiple filings referring to the same earnings release. L4 must report issuer/date coverage before outcomes; L1 owns the frozen event parser and test implementation.
- **Event availability:** define public time as the later of the EDGAR acceptance timestamp and an explicit release timestamp in the exhibit. If the exhibit gives no release timestamp, use acceptance time. A filing becomes usable only on the next trading day after its SEC filing date, consistent with the project rule. The response session d is the first regular NYSE session whose open is after both that next-trading-day availability point and the public time. Never assign the event to a session already in progress when it became public.
- **Network input:** L4 builds/maintains the point-in-time top-50 13F roster, `13f_holder_by_dow_stock.csv`, dated `13f_cosine_overlap_edges.csv`, filing coverage, and historical holdout link data. Use only the latest graph whose component filings and roster were available by the event response close. A 13F filing dated f is usable starting on the next trading day after f. Carry forward the latest public graph; report age and flag it stale when older than two calendar quarters. Never use a fixed Q2 2026 roster historically. L4 prepares these inputs; L1 does not edit source panels.
- **Point-in-time identity:** use the SEC CIK for event identity and the project's date-specific security map for prices. Do not use current tickers to map an issuer historically. Exclude events without a verified Item 2.02 item, accepted timestamp, or valid point-in-time price mapping.

## Primary mechanism test and fixed placebos

For source k with response session d, define its signed shock `u[k,d] = (adjusted_close[k,d] / adjusted_close[k,d−1] − 1) − EWReturn[other available point-in-time Dow names,d]`. The EW comparator excludes k and uses only other names with valid d−1 and d prices; this fixed market adjustment needs no external market proxy. At close d, define the peer score `E[j,d] = Σk u[k,d] × W[k,j,d]`, where W is the directed row-normalized common-owner cosine graph; diagonal entries are zero. Aggregate simultaneous sources by the displayed sum. Exclude source firms and target firms with their own verified Item 2.02 response session within d−5 through d+5. Retain one score/return pair per target and response date.

For each response date with at least three finite target pairs, calculate Spearman rank IC between E and target `adjusted_close[d+5] / adjusted_open[d+1] − 1`. Report the date-wise IC series, its mean, number of event dates and Newey–West t with Bartlett lag 4 across event dates in chronological order. Variant 1 passes only if mean IC ≥ 0.0183, its sign is positive, and NW t ≥ 2.00. This is a prediction test, not causal identification.

Use two fixed variant-1 placebos with NumPy `default_rng(20261110)`, 500 draws per randomized family, and the same eligible event dates/returns: (1) degree-preserving directed double-edge swaps, exactly 10×E attempts per graph, skipping self-edges and duplicate edges, then randomly permuting the original edge-weight multiset and row-normalizing; (2) shift the dated graph exactly 20 trading sessions earlier, circularly. For each family report all placebo IC draws, one-sided randomization p `(1 + count(placebo ≥ observed))/(501)`, and observed-statistic percentile. The observed IC must exceed the 95th percentile and each randomization p must be <0.05. For each family also average draw-specific date-level ICs date-by-date; its two-sided 90% Newey–West confidence interval (Bartlett lag 4) must be entirely within [−0.00577,+0.00577], and the 95th percentile of absolute draw-specific mean ICs must be below 0.00577. The 0.00577 margin is the disclosed cost-only placebo-equivalence scale, not the advancement hurdle. Report all draws and equivalence results. A failed primary or placebo gate ends F1; no later variant or portfolio can rescue it.

## Variants and selection rule

1. **Primary:** five-session market-adjusted source response and point-in-time common-owner graph, as defined above.
2. **Fixed sensitivity:** the same event shock and timing, but W assigns equal weight to all other point-in-time Dow names sharing the source issuer's exact two-digit SIC major group from `sic_panel.csv`; no same-industry target means no score. No three- or four-digit SIC alternative is allowed.

Variant 2 is a registered sensitivity only, cannot replace a failed variant 1, and cannot advance to a portfolio or holdout. Report its mean IC and NW lag-4 t with the predicted positive sign. No third variant, parameter sweep, or post-outcome event filter is permitted.

## Portfolio, costs and inference

Only after variant 1 passes all mechanism and placebo gates, form an event portfolio on the first eligible response date and then on each subsequent eligible response date at least five trading sessions after the prior portfolio formation. On a formation date with positive mean source shock, rank non-source names with a finite positive E score; require at least five and hold the five highest equal-weight from the next session open through the fifth session close. This is a concentrated long-only buying-pressure book with 83.3% active share when all 30 names are in the benchmark; calculate actual active share each date and require it to be at least 50%. Compare with EW30 over the identical available names and dates. Skip a formation date without a positive mean source shock or five positive peer scores; do not fill missing names or use negative scores as long positions.

Charge 0.05% per dollar of total traded notional using the harness actual-trade engine. Cap total traded notional/NAV at 0.50 per rebalance. Require primary mean IC ≥0.0183, positive net excess return over EW30, net Sharpe above EW30, gross active edge at least four times realized costs, and average turnover ≤0.50 per rebalance. The 0.0183 hurdle is L1's conservative reconciled top-five weekly reference (1.58751 NAV incremental turnover and 0.030075 cross-sectional dispersion); it is not an F1 outcome estimate. Report the separate helper floor `r4_harness.break_even_rank_ic(0.50,0.03007510102898867,0.0005,top_fraction=5/30)=0.00577` for comparison, but do not use it to lower the hurdle.

For portfolio inference use one-sided circular block bootstrap, 5,000 draws, 10-session blocks, seed `20261110`. Report raw and Holm-adjusted p-values, net excess return, net Sharpe, active share, turnover, costs, cost/gross-edge ratio, and DSR with `trial_count=30`. Portfolio pass requires positive net excess, higher net Sharpe than EW30, cost gates above, and Holm-adjusted p<0.05.

## Registered Holm endpoints

Before any goal outcome is computed, the coordinator enters these named F1 endpoints plus every endpoint from all other registered D4–D6 and fallback dossiers into the single frozen `specs/r4_trials.md` family. Apply Holm once across the full family; report raw and adjusted values and do not remove failed endpoints.

1. F1 variant 1 five-session peer rank IC, one-sided positive Newey–West lag-4 p-value.
2. F1 variant 1 observed-versus-degree-preserving graph placebo, one-sided randomization p-value.
3. F1 variant 1 observed-versus-20-session-shifted graph placebo, one-sided randomization p-value.
4. F1 degree-preserving placebo equivalence test, maximum one-sided TOST p-value using the fixed ±0.00577 margin.
5. F1 shifted-graph placebo equivalence test, maximum one-sided TOST p-value using the fixed ±0.00577 margin.
6. F1 variant 2 two-digit-SIC five-session IC, one-sided positive Newey–West lag-4 p-value.
7. F1 variant 1 portfolio net excess return over EW30, one-sided circular block-bootstrap p-value.

No other F1 statistic receives an inferential p-value or confidence claim unless the coordinator adds it to the manifest before outcomes. The full-goal DSR count remains 30 and is separate from Holm.

## Sealed holdout procedure and pass rule

Only the coordinator may run F1 once after freezing the inputs, code, and this preregistration. Use Dow 2010-01-01 through 2020-10-31 with point-in-time roster and the identical event, network, scoring, execution, and cost rules. Disclose the known gaps: KFT, DWDP, and WBA unavailable; UTX represented by RTX lineage. Use EW over available names, no imputation, and report the DWDP membership window with and without DWDP. Disclose missing EDGAR events, 13F graph age/coverage and all price gaps. Workers must not access holdout prices, returns, or signals. Holdout passes only with positive mean IC ≥0.0183, positive net excess return, net Sharpe above EW, and one-sided 10-session block-bootstrap p<0.10. If inputs prevent the frozen run, call it infeasible; do not substitute a window or retry.

## Evidence and input ownership

- Ramnath (2002), “Investor and Analyst Reactions to Earnings Announcements of Related Firms,” *Journal of Accounting Research* 40(5), 1351–1376. https://doi.org/10.1111/1475-679X.t01-1-00057
- Hameed, Morck, Shen & Yeung (2015), “Information, Analysts, and Stock Return Comovement,” *Review of Financial Studies* 28(11), 3153–3187. https://doi.org/10.1093/rfs/hhv042
- Thomas & Zhang (2008), “Overreaction to Intra-industry Information Transfers?”, *Journal of Accounting Research* 46(4), 909–940. https://doi.org/10.1111/j.1475-679X.2008.00294.x
- SEC, EDGAR APIs and Form 8-K Item 2.02: https://www.sec.gov/search-filings/edgar-application-programming-interfaces and https://www.sec.gov/forms/form8-k.pdf

L4 builds the historical event, identity, PIT 13F, and SIC input panels; L1 builds/tests the frozen signal and portfolio code; the coordinator freezes the endpoint manifest and alone runs the holdout. The event papers establish peer information transfer and overreaction in wider samples, not a Dow-only profitable pressure strategy.

## Ready for freeze checklist

- [ ] L4 `8k_item202_events.csv` is complete for the point-in-time Dow universe in both periods; every item and acceptance timestamp is auditable, with duplicate amendments resolved before outcomes.
- [ ] `13f_top50_pit_roster.csv`, holder, coverage, and dated cosine-edge inputs exist; next-trading-day availability and graph age are verified for development/holdout without prices.
- [ ] `sic_panel.csv` covers variant 2 and its fixed two-digit mapping; event, filing, and target overlap rules are implemented exactly.
- [ ] Input-only count gate passes: at least 100 distinct SEC earnings releases per period after the stated accession/amendment deduplication, 20 event dates with at least three valid linked targets, and at least five positive peer scores on a date with positive mean source shock. If not, F1 is infeasible before outcomes; no broadening.
- [ ] Coordinator has registered all seven F1 endpoints and the full-goal Holm family, including D4–D6 and F2/F3, in `specs/r4_trials.md` before outcome access.
- [ ] The 0.0183 advancement hurdle, 0.00577 placebo-equivalence margin, 0.05%/side cost, and 50% turnover cap are implemented without substitutions.
- [ ] The coordinator's holdout gaps and one-shot procedure are recorded. Add a freeze date and SHA-256 only after checks pass and before any F1 outcome.

All dates, windows, cutoffs, thresholds, costs, seeds and draw counts are fixed. This is a DRAFT and is not an outcome result.


