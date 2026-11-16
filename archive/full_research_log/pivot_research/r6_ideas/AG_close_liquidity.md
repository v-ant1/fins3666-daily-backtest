# R6 Idea Screen AG — closing-auction liquidity-gap reversal

**Status: SCREEN ONLY. No signal outcomes, forward returns, ICs or portfolio results were calculated. Overall verdict: STOP — FAIL.** This screen asks whether the closing-auction price displacement relative to a pre-close reference is temporary and reverses after the auction. The input probe confirms a usable 2024 sample for three Dow names, but the proposed gap is a close-price-reversal proxy already covered by the Z auction/EOD screens, the directly relevant overnight leg is unavailable after the signal forms, and no matched large-cap rank-IC estimate clears criterion 4.

## Identity and path preflight

- **Short name / mechanism:** AG close-liquidity gap; an unusually large auction-clearing price move relative to the last regular-session pre-close VWAP is interpreted as temporary liquidity pressure and expected to reverse after the close.
- **Output:** `r6_ideas/AG_close_liquidity.md` only. This exact target did not exist at preflight.
- **Development boundary:** permitted data begins 2020-11-27. The only row reads for this screen were date-filtered to 2024-06-03. No November 2020 partition or any sealed folder was opened.
- **No outcomes:** I inspected schema and date-filtered row coverage only; I did not compute the gap, returns, signal ranks, predictability or strategy performance.

## 1. Overlap with prior work

Nearest screens are:

- [`Z_auction_eod.md`](Z_auction_eod.md), especially its signed closing-auction pressure / next-session reversal direction and its late-day cross-sectional reversal direction. Those use imbalance or pre-auction returns; this candidate substitutes the realized auction-price move relative to pre-close VWAP as the pressure proxy.
- [`T_daily.md`](T_daily.md) T2, which already screened signed closing-auction imbalance followed by reversal.
- [`Z_minute_flow.md`](Z_minute_flow.md), which covers minute-bar pressure and reversal-related microstructure features.

The measurement differs from signed imbalance: it does not claim to observe buyer-versus-seller quantity, only the auction-clearing price displacement. Economically and temporally, however, it is the same close-auction shock / temporary price-pressure / next-session reversal family. Bogousslavsky and Muravyev directly study auction-price deviations and their subsequent reversal, so renaming the input as a VWAP gap does not create a distinct mechanism. The Z screens already considered this economic family; their coordinator review retained the valid kills that close-auction size lacks a side and the reversal evidence is weak in mega-caps (decision 157).

**Gate 1: FAIL — insufficient novelty.** The candidate overlaps the auction-reversal screen and its primary literature, with only a different price reference used to proxy the same displacement.

## 2. Exact pressure measure and dated source

A single, non-swept candidate definition would be:

\[
g_{i,t}=10{,}000\,[\ln(P^{auction}_{i,t})-\ln(VWAP^{15:55-16:00}_{i,t})]
\]

in basis points, where `P_auction` is the official SIP closing-auction price and VWAP is the SIP one-minute bar VWAP over the final five regular-session minutes, both for issuer `i` on trading date `t`. Positive `g` means the closing auction cleared above the pre-close reference. It is only known after the closing auction. The proposed **tradable** test would therefore form after the close and enter at the next session's opening execution; it could test reversal from that next open through the next regular-session close, not the already elapsed close-to-open return. The overnight reversal in the cited work is thus evidence for temporary pressure, but is not itself capturable by this signal after formation.

The staged sources are `r6_data/alpaca/auctions/` (SIP auction event price/time) and `r6_data/alpaca/minute/` (SIP OHLCV/VWAP bars). The inputs carry `symbol`, timestamp, auction type, price/size or OHLCV/VWAP and point-in-time membership flags. A later preregistration would have to freeze event selection, the precise VWAP interval and timestamp conventions, corrections, missing-bar handling, and intersect the point-in-time Dow roster. Alpaca's endpoints document the auction and bar fields ([auctions](https://docs.alpaca.markets/us/reference/stockauctionsingle-1); [historical bars](https://docs.alpaca.markets/us/reference/stockbarsingle-1)); its market-data terms distinguish SIP historical feed access from free real-time SIP entitlement ([FAQ](https://docs.alpaca.markets/us/docs/market-data-faq)). No license or full-window entitlement was inferred from the sample.

**Gate 2: FAIL for tradable timing as a reversal test.** The candidate is observable after close, but the canonical overnight correction occurs before an order formed from it can execute. An open-to-close test would be a different, unsupported horizon and would need its own effect-size evidence.

## 3. Coverage and independent breadth

I used `pyarrow.parquet.read_table` with timestamp filters `2024-06-03 00:00 UTC <= timestamp < 2024-06-04 00:00 UTC` on the three 2024 sample symbols AAPL, CAT and JNJ. I did not read rows from any other date.

| Source | Date-filtered input-only result |
|---|---|
| Auction event partitions | AAPL 6 rows, CAT 10, JNJ 8; respectively 3, 5 and 4 rows tagged `close`; the tested date rows had non-null price and size. |
| One-minute bar partitions | AAPL 390 rows, CAT 389, JNJ 390; 30 rows per name in the final half-hour; VWAP was non-null on every date-filtered row. |

This confirms that the staged representation can expose closing events and the last-half-hour VWAP on this single date for three Dow constituents. It does **not** establish complete point-in-time coverage across 30 names or the development window, nor does it establish that each close-tagged event is the unique official close without a frozen event-selection rule. The input sample represents one independent date and three names; effective independent breadth for this screen is therefore unmeasured. The broader Z development inventory reports 1,488 dates, 500 S&P names and 53 SIC2 groups, but those counts are only an upper bound for a later S&P mechanism analysis, not observed coverage for this Dow gap variable. Survivorship and ticker changes require point-in-time membership; a later coverage audit must report date/name coverage without joining forward outcomes.

**Gate 3: FAIL — breadth and complete signal coverage are not established by a one-date, three-name probe.**

## 4. Literature effect and synthetic power

**Verified adjacent evidence:**

- Bogousslavsky and Muravyev, [“Who Trades at the Close? Implications for Price Discovery and Liquidity,” *Journal of Financial Markets* 66 (2023), 100852](https://doi.org/10.1016/j.finmar.2023.100852), study U.S. closing auctions in the modern high-volume regime. They report that price deviations from the auction reverse quickly and almost completely on average, including after half-spread adjustment. This is close to the proposed displacement mechanism and includes large U.S. stocks, but the abstracted result is not a cross-sectional rank IC or an after-cost Dow portfolio estimate.
- Cushing and Madhavan, [“Stock Returns and Trading at the Close,” *Journal of Financial Markets* 3 (2000), 45–67](https://doi.org/10.1016/S1386-4181(99)00012-9), study Russell 1000 transaction data from June 1997 to July 1998 plus NYSE MOC imbalance indications. They find systematic returns and reversal after imbalance publications. This is a different auction-information input and predates today's market structure.
- Vidovich and Zerjal, [“The End-of-Day Reversal After 2019” (6 November 2026 preprint)](https://arxiv.org/abs/2611.09286), report a dollar-volume-weighted reversal of 0.74 bp/day for the full index from 2020 onward, versus 3.05 bp/day in the 2023–2026 S&P sample that excludes about 80 heavily traded names; their discussion says the full-index weakness is concentrated in the very largest names. This is a return spread for late-day reversal, not an estimate for this auction-gap sort, but it is adverse large-cap evidence.

No source supplies a compatible post-2020 U.S. mega-cap **rank IC** for (g). “Almost complete reversal” is a fraction of auction displacement, not a dollar return magnitude; it cannot be converted to a cross-sectional IC without the distribution of gap sizes and covariances. The latest full-index 0.74 bp/day spread is below the 2.5 bp daily trading-cost amount at 50% turnover, but is not a return estimate for this exact candidate.

For scale only, I ran `r4_harness/power_sim.py` with 500 nominal names, 1,488 daily dates, horizon 2 (NW lag 1), AR(1) 0.20, IC SD 0.20538, 5,000 simulations, seed 20261111 and a **hypothetical, unsourced** planted mean rank IC of 0.0183. Under those assumptions it returns 83.86% probability of NW `t ≥ 2`, Monte Carlo SE 0.00520, effective N 1,240 and 80%-power MDE 0.01657. This is a sensitivity check only: IC SD 0.20538 is a planning assumption corresponding to 500 names, 53 SIC2 groups and within-group correlation 0.15; the simulator itself does not impose SIC2 clustering. The planted 0.0183 is not an effect estimate from the auction literature. It cannot be represented as power at a sourced plausible effect for this signal.

**Gate 4: FAIL — neither source evidence nor power supports the needed effect.** The criterion-4 bound audit's roughly 0.083–0.089 rank-IC illustration is monthly and not portable to this daily/overnight signal; no matched estimate approaches or can be validly compared with it.

## 5. Criterion-4 feasibility

A daily top-five portfolio against EW30 would have high active share, but frequent rank changes make a 50% total-notional turnover cap difficult. At that cap and the stated 0.05% per-side cost, linear transaction cost is at most `0.50 × 0.0005 = 0.00025` NAV, or **2.5 bp per session** (about 6.3% of NAV under simple 252-session annualization), before spread, auction execution shortfall or impact. The full-index 0.74 bp/day late-day reversal reported by Vidovich and Zerjal is smaller than this daily cost scale and is already not a Dow-specific estimate. The 3.05 bp/day estimate excludes the very heavily traded names that are the target here. Neither can be mapped to top-five versus EW30 excess Sharpe, block-bootstrap p, Holm-adjusted significance, or DSR without unsupported assumptions.

The closing-gap observation is only available after the auction; trading the overnight reversal is impossible with a signal formed from that same auction. Moving entry to the next open changes the payoff window, for which the cited papers do not report a transferable residual effect. Thus a cost-compliant and criterion-4 feasible portfolio cannot be defended before outcomes. The criterion-4 audit also requires positive net excess versus EW30, higher Sharpe and Holm-adjusted block-bootstrap evidence; the six-year R6 family makes this harder, not easier.

**Gate 5: FAIL — criterion-4 feasibility is not demonstrated, and the directly cited full-index effect scale is below daily costs.** No cost relaxation, extra variant, or post-hoc horizon change is proposed.

## 6. Holdout protocol

No holdout path, roster, price, signal or return was read or requested. Any later holdout work remains coordinator-controlled under goal criterion 5 after a frozen preregistration, runner and input manifests; Alpaca's documented history start does not authorize a worker to inspect any sealed values.

**Gate 6: PASS — holdout untouched.**

## Final screen decision

- **Overall: STOP — FAIL.** Gate 1 (novelty), Gate 2 (tradable timing), Gate 3 (full coverage/breadth), Gate 4 (matched effect/power) and Gate 5 (criterion-4 feasibility) fail; only holdout discipline passes.
- **Probability of clearing the full R6 criterion-4 stack:** below 1%, judgmental and not a statistical estimate. The one positive input-feasibility check does not offset overlap, timing and large-cap effect-size gaps.
- **What could change the decision:** an independent post-2020 Dow/mega-cap study of this exact auction-price-gap signal reporting a tradable post-open rank IC or net long-only result large enough to clear turnover, costs, Holm-adjusted inference and DSR. The current screen provides no basis to authorize a preregistration.
- **Reviewer/date:** dispatched worker, 2026-11-11.

## Sources and audit trail

- Bogousslavsky and Muravyev (2023), [DOI](https://doi.org/10.1016/j.finmar.2023.100852).
- Cushing and Madhavan (2000), [DOI](https://doi.org/10.1016/S1386-4181(99)00012-9).
- Vidovich and Zerjal (2026), [preprint](https://arxiv.org/abs/2611.09286).
- Alpaca [auction](https://docs.alpaca.markets/us/reference/stockauctionsingle-1), [minute-bar](https://docs.alpaca.markets/us/reference/stockbarsingle-1) and [market-data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq).
- Project context: [`Z_auction_eod.md`](Z_auction_eod.md), [`Z_minute_flow.md`](Z_minute_flow.md), [`T_daily.md`](T_daily.md), [`CRITERION4_BOUND_AUDIT.md`](../report_drafts/CRITERION4_BOUND_AUDIT.md), [`r6_goal.md`](../specs/r6_goal.md), and [`ALPACA_AUDIT.md`](../r6_data/alpaca/ALPACA_AUDIT.md).


