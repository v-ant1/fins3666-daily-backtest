# F3 — Overnight versus intraday pressure through common ownership

**STATUS: DRAFT - NOT FROZEN.** No F3 outcomes have been computed. The coordinator freezes this specification only after the inputs, coverage gates, and full Holm endpoint family are checked before any signal-return or portfolio outcome is calculated.

## Hypothesis, sign and horizon

A five-session network score made from positive overnight pressure predicts same-sign overnight returns in connected Dow names over the next five overnight intervals. The hypothesis applies persistent overnight demand to a common-owner network; an opposite-sign intraday response is a registered diagnostic. The source literature documents own-stock overnight/intraday continuation and cross-period reversal, not network transmission.

## Universe, inputs, timing and network

- **Universe and prices:** point-in-time Dow 30 daily OHLCV, development 2020-11-27 through 2026-10-30. The coordinator uses the same roster and inputs for the one-time 2010-01-01 to 2020-10-31 holdout. Workers must not open, plot, or compute pre-2020-06 Dow prices, returns, or signals.
- **Price adjustment:** for daily session t, `adjusted_open[t] = raw_open[t] × adjusted_close[t] / raw_close[t]`, using the project's split- and distribution-adjusted close. If raw close is zero or missing, that session is unavailable. `ON[i,t] = ln(adjusted_open[i,t] / adjusted_close[i,t−1])`; `ID[i,t] = ln(adjusted_close[i,t] / adjusted_open[i,t])`. No alternative price convention is permitted.
- **Network:** L4 supplies the dated `13f_top50_pit_roster.csv`, holder records, filing coverage, and `13f_cosine_overlap_edges.csv` for development plus permitted holdout-period link inputs. Each filing and roster membership dated d is usable only from the next trading day after d. At t close use the latest graph publicly available by t, carry it forward, zero diagonal, and row-normalize nonzero rows. Report graph age; flag age over two calendar quarters but retain it. No fixed current roster, future filings, return correlation, SIC filter, or outcome-selected edge is allowed. L4 builds inputs and point-in-time maps; L1 builds the frozen signal and tests; the coordinator alone executes holdout.
- **Available signal:** at close t, `N_ON[j,t] = Σi W[j,i,t] × mean(ON[i,t−4:t])` and `N_ID[j,t] = Σi W[j,i,t] × mean(ID[i,t−4:t])`. `W[j,i,t]` is the row-normalized common-owner weight of neighbor i in target j's dated network. Require five valid source sessions for a score; if no valid nonzero network row exists, score unavailable. A score at t is first tradable at the next session's open.

## Primary mechanism test and fixed placebos

For every date with at least three finite target pairs, calculate the cross-sectional Spearman IC between N_ON[j,t] and target j's cumulative five overnight log return `Σr=t+2..t+6 ON[j,r]`. This starts with the close[t+1]-to-open[t+2] interval, after a signal made at close t can first be traded at open[t+1]; it excludes the untradeable close[t]-to-open[t+1] move. Report the date-wise IC series, mean, eligible date count, and Newey–West t with Bartlett lag 4. Require a positive mean IC ≥0.0183 and NW t≥2.00 for variant 1. The rank-IC hurdle is the conservative L1-reconciled top-five weekly reference, not an F3 estimate.

Use two fixed variant-1 placebos with one NumPy `default_rng(20261110)` generator and 500 draws per randomized family: (1) for each graph attempt exactly 10×E directed degree-preserving double-edge swaps, skipping self-edges/duplicates, and randomly reassign its edge-weight multiset; (2) pair t with the graph exactly 20 trading sessions earlier, with circular wrap. Re-zero diagonals and row-normalize after each graph change. For each family report all placebo IC draws, one-sided randomization p `(1+count(placebo≥observed))/501`, and observed percentile. Require observed IC above the 95th percentile and p<0.05 for both. For each family also calculate the mean of the draw-specific date ICs date-by-date and its two-sided 90% Newey–West interval (Bartlett lag 4); require the entire interval within [−0.00577,+0.00577] and the 95th percentile of absolute draw-specific mean ICs below 0.00577. This equivalence requirement tests practical null placebos; a nonsignificant placebo t alone is insufficient. The ±0.00577 margin is the cost-only scale reference and is not the 0.0183 advancement hurdle. A failed primary or placebo gate stops F3; variant 2 cannot rescue it.

## Variants and selection rule

1. **Primary:** five-session N_ON network signal and its next five tradable overnight intervals above.
2. **Fixed session sensitivity:** five-session N_ID network signal and target `Σr=t+1..t+5 ID[j,r]`, the next five intraday intervals. Report its mean IC and Newey–West lag-4 t with the predicted positive sign. It cannot replace a failed variant 1 or advance to portfolio/holdout.

No alternative overnight cutoff, open/close formula, signal window, graph, or horizon is allowed. No third variant or parameter sweep is registered.

## Portfolio, costs and inference

After variant 1 passes the mechanism/placebo gates, rank the valid N_ON scores on the fixed weekly schedule: start at the first valid fifth-session formation date and rebalance every fifth trading session thereafter. At each formation go long the five highest scores, equal-weight, at the next session open and hold until the open of session t+6; break ties by ticker ascending. This is five complete sessions and matches the primary overnight target endpoint after the entry open. Compare with EW30 over the same available names. With all 30 names eligible this top-five book has 83.3% active share; calculate actual active share and require ≥50%. Do not form a portfolio if fewer than five finite scores exist.

Charge 0.05% per dollar of total traded notional with the harness actual-trade engine and cap total traded notional/NAV at 0.50 per rebalance. Require positive net excess return vs EW30, net Sharpe above EW30, gross active edge ≥4× realized costs, average turnover ≤0.50, and primary mean IC≥0.0183 before the portfolio can pass. Disclose the helper floor `r4_harness.break_even_rank_ic(0.50,0.03007510102898867,0.0005,top_fraction=5/30)=0.00577` for comparison only; it does not replace the higher 0.0183 advancement hurdle. L1's 0.0183 reference reconciles 1.58751 NAV incremental weekly turnover and 0.030075 cross-sectional dispersion; neither is an F3 estimate.

For portfolio inference use one-sided circular block bootstrap, 5,000 draws, 10-session blocks, seed `20261110`; report raw/Holm-adjusted p, net excess, net Sharpe, active share, turnover, costs, cost/gross-edge ratio, and DSR with `trial_count=30`. Portfolio pass requires positive net excess, net Sharpe above EW30, the cost/turnover gates, and Holm-adjusted p<0.05.

## Registered Holm endpoints

The coordinator registers these F3 endpoints and all endpoints from D4–D6/F1/F2 in the one full-goal family in `specs/r4_trials.md` before outcome access. Holm is applied once to the full named manifest; no endpoint is dropped after results.

1. F3 variant 1 five-overnight-interval N_ON IC, one-sided positive NW lag-4 p-value.
2. F3 variant 1 observed-versus-degree-preserving graph placebo, one-sided randomization p-value.
3. F3 variant 1 observed-versus-20-session-shifted graph placebo, one-sided randomization p-value.
4. F3 degree-preserving graph placebo equivalence, maximum one-sided TOST p-value at ±0.00577.
5. F3 shifted-graph placebo equivalence, maximum one-sided TOST p-value at ±0.00577.
6. F3 variant 2 five-session N_ID-to-intraday IC, one-sided positive NW lag-4 p-value.
7. F3 variant 1 portfolio net excess return over EW30, one-sided block-bootstrap p-value.

Report raw and Holm-adjusted p-values for all seven. DSR uses the full-goal 30-variant count and is separate from Holm. No other F3 statistic receives inferential wording unless it is added to the manifest before outcomes.

## Sealed holdout procedure and pass rule

Only the coordinator may run F3 once on the Dow 2010-01-01 to 2020-10-31 point-in-time roster after freezing code/specification. Use the same exact signal, adjustment, next-day filings, graph, costs, weekly portfolio and inference. Disclose the known gaps: KFT, DWDP and WBA unavailable; UTX via RTX lineage; calculate EW on available names, no imputation, and report DWDP membership both included and excluded. Disclose unavailable bars, graph age, and stale coverage. Workers must never inspect holdout prices, returns, or signals. Pass requires positive mean IC≥0.0183, positive net excess, Sharpe above EW30 and one-sided 10-session block-bootstrap p<0.10. If the required PIT graph or OHLCV fields are unavailable, mark holdout infeasible and do not substitute assets or windows.

## Evidence and input ownership

- Lou, Polk & Skouras (2019), “A Tug of War: Overnight versus Intraday Expected Returns,” *Journal of Financial Economics* 134(1), 192–213. https://doi.org/10.1016/j.jfineco.2019.03.011
- Antón & Polk (2014), “Connected Stocks,” *Journal of Finance* 69(3), 1099–1127. https://doi.org/10.1111/jofi.12149
- Greenwood & Thesmar (2011), “Stock Price Fragility,” *Journal of Financial Economics* 102(3), 471–490. https://doi.org/10.1016/j.jfineco.2011.06.003

Lou et al. document same-session continuation and cross-period reversal in broad stock portfolios, not network transmission; Antón–Polk and Greenwood–Thesmar motivate ownership-network demand exposure. All cited work has wider samples and does not validate this Dow daily design.

## Ready for freeze checklist

- [ ] L4 verifies the development OHLCV open/close/adjustment schema and daily history, without touching holdout prices; coordinator confirms the holdout bar fields and disclosed gap treatment for its one-shot run.
- [ ] L4 `13f_top50_pit_roster.csv`, holder, filing coverage and dated common-owner graph cover both required intervals with next-trading-day availability and graph-age fields; the fixed Q2 2026 cohort is not used historically.
- [ ] Input-only breadth gate passes: at least 500 dates per period with at least 20 finite target scores and three nonzero common-owner peers per score. If not, declare infeasible before outcomes and stop.
- [ ] The specified adjusted-open formula, ON/ID definitions, prior-five signal windows, t+2…t+6 ON target, t+1…t+5 ID target and weekly execution are implemented exactly.
- [ ] Coordinator registers all seven F3 endpoints and complete goal-wide D4–D6/F1–F3 family before outcomes.
- [ ] The 0.0183 hurdle, ±0.00577 placebo margin, 0.05% cost, 50% turnover cap and 5,000-draw bootstrap are fixed.
- [ ] Coordinator records holdout gaps and one-shot route; add FROZEN date and SHA-256 only after all input checks and before any outcome.

All numerical choices, windows, costs, thresholds, seeds and draw counts are fixed. This is a DRAFT, not a result.



