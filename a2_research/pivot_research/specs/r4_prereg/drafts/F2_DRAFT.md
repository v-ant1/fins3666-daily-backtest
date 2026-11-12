# F2 — 13F position-change pressure across common owners

**STATUS: DRAFT - NOT FROZEN.** This is a fallback pre-registration only; no F2 outcomes have been computed. The coordinator freezes it only after input-only availability checks and the full Holm manifest are locked, before any signal/return statistic.

## Hypothesis, sign and horizon

Net buying disclosed in point-in-time institutional 13F positions predicts positive five-session returns in other Dow firms linked through common ownership. The primary test asks whether institution-reported position change propagates to connected holdings after the filing is public. Form 13F is a delayed long-position snapshot; position change is not a direct measure of actual trades and does not reveal short positions.

## Universe, inputs, timing and network

- **Universe:** point-in-time Dow 30 daily OHLCV and point-in-time issuer/security map. Development dates are 2020-11-27 through 2026-10-30. The coordinator alone runs the frozen 2010-01-01 to 2020-10-31 Dow holdout.
- **13F inputs:** L4 builds/maintains `13f_holder_by_dow_stock.csv`, `13f_filing_coverage.csv`, `13f_cosine_overlap_edges.csv`, `13f_top50_pit_roster.csv`, and the 2010–2020 holdout-period link panels. The roster ranks the top 50 filers by reported 13F value in each report quarter and records when membership becomes public. Do not use a current fixed roster historically. The coordinator can use only point-in-time inputs built by L4; workers never inspect holdout prices or returns.
- **Position fields:** require CUSIP/issuer identity, manager CIK, report date, filing date and timestamp, reported share amount, reported value, and a coverage flag. L4 additionally builds a free split-factor adjustment field for reported share quantities using the price-panel corporate-action metadata. If a split cannot be mapped, exclude that issuer-manager-quarter pair and disclose its count; do not treat a split as buying/selling. Missing filing/position coverage is missing, not zero.
- **Position change:** for manager m and issuer i at report quarter q, compute `Δshares[m,i,q] = split_adjusted_shares[m,i,q] − split_adjusted_shares[m,i,q−1]`. Mark the change at q's adjusted close, `D[m,i,q] = Δshares[m,i,q] × adjusted_close[i,q]`. Define the manager's prior-quarter Dow-sleeve denominator as `A[m,q] = Σi split_adjusted_shares[m,i,q−1] × adjusted_close[i,q]`. Define issuer flow pressure `f[i,t] = (1/M[t]) × Σm∈M[t] D[m,i,q_m] / A[m,q_m]`, where q_m is manager m's latest report quarter with both q_m and q_m−1 position records publicly usable by t, M[t] contains only managers who belong to the then-public PIT top-50 roster and have complete pair coverage, and M[t] is the finite eligible manager set. Use zero only for a security explicitly absent from a complete filed holdings table; otherwise preserve missingness. If M[t] is empty or a denominator is zero, the score is unavailable.
- **Availability:** a 13F filing and PIT roster row dated d become usable on the next trading day after d. At signal close t, include only filings and roster memberships whose effective date is no later than t. Recompute f only when a new eligible position filing or roster becomes usable; carry the last public f between updates. For graph W, use the latest publicly available positions at t, update after each filing becomes usable, zero the diagonal, and row-normalize nonzero rows. `S[j,t] = Σi W[i,j,t] × f[i,t]`. Report graph age in calendar days and elapsed quarter boundaries; flag age > two calendar quarters but retain those dates and report the count/manager coverage.
- **Input owners:** L4 builds point-in-time roster, position, security mapping, split-factor, coverage, and dated graph panels for development and permitted holdout link inputs. L1 implements the frozen signal, inference, and portfolio using development prices only. The coordinator freezes the manifest and alone runs the holdout.

## Primary mechanism test and fixed placebos

Test only signal dates t at the close of the next trading day on which one or more new eligible 13F rows or roster changes became usable. At each date with at least three finite score/return pairs, calculate Spearman rank IC between S[j,t] and target `adjusted_close[j,t+5] / adjusted_open[j,t+1] − 1`. Report the date-wise IC, mean, number of updates, and Newey–West t with Bartlett lag 4 across update dates in chronological order. The positive mechanism gate is mean IC ≥0.0183 and NW t≥2.00. This is a predictive test of disclosure-timed pressure, not proof of actual trading by the filing date.

For variant 1 use two fixed placebo families and one `default_rng(20261110)` stream, 500 draws per randomized family, using exactly the observed update dates and target returns: (1) for every graph, attempt exactly 10×E directed double-edge swaps, skipping self-edges and duplicates, preserving node in- and out-degree; randomly reassign the observed edge-weight multiset and row-normalize; (2) use the actual dated graph from exactly 20 trading sessions earlier, wrapping the dated graph sequence circularly. For each family report all 500 IC statistics, one-sided randomization p `(1+count(placebo≥observed))/501`, and observed percentile. Require observed IC above the 95th percentile and p<0.05 for both families. For each family average its draw-level date ICs date-by-date, report mean and two-sided 90% NW interval (Bartlett lag 4), and require the entire interval inside [−0.00577,+0.00577]; also require the 95th percentile of absolute draw-specific mean ICs <0.00577. This is an equivalence test for negligible placebo effects; failure of either placebo gate ends F2. The 0.00577 margin is the cap-based cost-only reference, not the 0.0183 advancement hurdle.

## Variants and selection rule

1. **Primary:** common-owner graph propagation of split-adjusted reported share changes, as defined above.
2. **Fixed diagnostic:** direct issuer flow pressure `f[j,t]` without graph propagation, with the same update dates, target and horizon. It tests whether the network adds information; it cannot advance or replace a failed variant 1.

Report variant 2's date IC series, mean and Newey–West lag-4 t using the expected positive sign. No third variant, alternate filing lag, position/value proxy, manager count, lookback, or graph threshold may be tested. Variant 1 alone can advance to portfolio and holdout.

## Portfolio, costs and inference

Only after variant 1 passes its mechanism and placebo gates, carry its latest public score forward and rebalance every fifth trading session, beginning on the first eligible signal date. Go long the five highest scores and short the five lowest finite scores, equal-weight within each side at +10%/−10% of NAV per name; ties break by ticker in ascending ASCII order. The design is dollar-neutral and long-short, so it meets the substantial-change requirement. Use point-in-time available names only. Compare the net long-short return with zero and also report its excess return and Sharpe relative to EW30 on identical dates. Charge 0.05% per dollar of gross traded notional; cap total traded notional/NAV at 0.50 each rebalance using the harness actual-trade convention.

Require primary mean IC≥0.0183, positive net return, net Sharpe above EW30, gross active edge at least four times realized costs, and average total-notional turnover≤0.50 per rebalance. The 0.0183 hurdle is the conservative L1-reconciled top-five weekly reference (1.58751 NAV incremental turnover, 0.030075 cross-sectional dispersion); it is not an F2 estimate. Also disclose `r4_harness.break_even_rank_ic(0.50,0.03007510102898867,0.0005,top_fraction=5/30)=0.00577` as the cap-based cost-only helper floor; it does not lower the advancement hurdle.

For the portfolio endpoint use one-sided circular block bootstrap, 5,000 draws, 10-session blocks, seed `20261110`. Report raw/Holm-adjusted p, net return, EW30-relative net excess, Sharpe, turnover, costs, gross-edge/cost ratio, and DSR with `trial_count=30`. Portfolio pass requires positive net excess over EW30, Sharpe above EW30, gross edge ≥4× costs, turnover≤0.50, and Holm-adjusted p<0.05.

## Registered Holm endpoints

The coordinator records these named endpoints and every already registered D4–D6/F1/F3 endpoint in one frozen `specs/r4_trials.md` manifest before any outcome. Holm is applied once to the whole family; all raw and adjusted p-values are reported, including failures.

1. F2 variant 1 five-session propagated-flow IC, one-sided positive NW lag-4 p-value.
2. F2 variant 1 observed-versus-degree-preserving placebo, one-sided randomization p-value.
3. F2 variant 1 observed-versus-20-session-shifted graph placebo, one-sided randomization p-value.
4. F2 degree-preserving placebo equivalence, maximum one-sided TOST p-value at ±0.00577.
5. F2 shifted-graph placebo equivalence, maximum one-sided TOST p-value at ±0.00577.
6. F2 variant 2 direct-flow five-session IC, one-sided positive NW lag-4 p-value.
7. F2 variant 1 portfolio net excess return over EW30, one-sided block-bootstrap p-value.

DSR uses the full goal trial count of 30 and is separate from Holm. No further endpoint is inferred after outcomes.

## Sealed holdout procedure and pass rule

Only the coordinator runs the frozen holdout once, on the point-in-time Dow 2010-01-01 through 2020-10-31, using identical roster, filings, position changes, graph, next-day availability, execution, costs and inference. Disclose the known gaps: KFT, DWDP, and WBA unavailable; UTX via RTX lineage; EW uses available names; report DWDP's membership window both included and excluded. Report missing 13F rows, corporate-action exclusions, graph age, manager coverage, and dates with fewer than three pairs. Do not let workers open holdout prices, returns, or signals. Pass requires positive IC≥0.0183, positive net excess, net Sharpe above EW30, and one-sided 10-session block-bootstrap p<0.10. Begin F2 scoring at the first signal date for which both current and prior report-quarter positions are in the permitted 2010–2020 link panel; report unavailable earlier dates and do not request pre-2010 link inputs. If permitted rows cannot supply the required prior/current quarter or PIT membership, report infeasible; do not replace the sample, roster, or specification.

## Evidence and input ownership

- Coval & Stafford (2007), “Asset Fire Sales (and Purchases) in Equity Markets,” *Journal of Financial Economics* 86(2), 479–512. https://doi.org/10.1016/j.jfineco.2006.09.007
- Lou (2012), “A Flow-Based Explanation for Return Predictability,” *Review of Financial Studies* 25(12), 3457–3489. https://doi.org/10.1093/rfs/hhs103
- Antón & Polk (2014), “Connected Stocks,” *Journal of Finance* 69(3), 1099–1127. https://doi.org/10.1111/jofi.12149
- SEC, Form 13F: https://www.sec.gov/files/form13f.pdf

Coval–Stafford and Lou support temporary flow-related pressure and price impact in broader fund/stock samples; Antón–Polk motivates shared-owner networks. None validates this delayed 13F position-change proxy as actual trades or a Dow-only short-horizon strategy. L4 owns PIT filing, roster, and link panels; L1 owns frozen tests; coordinator owns the endpoint manifest and single holdout.

## Ready for freeze checklist

- [ ] L4's 13F PIT top-50 roster exists by report quarter, with documented public availability date in both periods; the fixed Q2 2026 roster is not used historically.
- [ ] L4 verifies report/filing dates, manager/security IDs, share amounts, missing-position semantics, coverage, prior-quarter joins, split adjustment, and the next-trading-day effective date without loading holdout prices.
- [ ] The input-only feasibility gate passes in both periods: at least 100 distinct usable manager filing updates, at least 20 update dates with 20+ finite scores, at least three nonzero directed peers per eligible update date on 80% of dates; report the full distributions. Otherwise declare infeasible before outcomes and do not broaden the panel.
- [ ] Dated graph input and stale-age reporting are reproducible; both fixed graph placebo procedures are implemented exactly.
- [ ] Coordinator records all seven F2 endpoints and the complete D4–D6/F1–F3 Holm family before outcomes.
- [ ] The 0.0183 hurdle, 0.00577 placebo-equivalence margin, 0.05%/side costs, 50% turnover cap, and long-short weights are fixed in code.
- [ ] Coordinator records the one-shot holdout gaps; add freeze date and SHA-256 only after all checks pass and before any outcome.

All numerical choices, dates, windows, weights, thresholds, costs, seeds and draw counts are fixed. This document remains DRAFT - NOT FROZEN and reports no outcomes.

