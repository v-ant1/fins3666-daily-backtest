# R6 Idea Screen: SIC-peer Amihud illiquidity shocks

**Status:** SCREEN ONLY — no signal outcomes, no return calculations, and no variant is authorized by this document.

## Identity and immutable-path preflight

- **Proposed short name and mechanism:** AO — a temporary liquidity shock among same-industry S&P firms may be learned from or transmit to their Dow peers, creating short-horizon peer price pressure.
- **Exact new output path:** `r6_ideas/AO_liquidity_shock.md`.
- The exact target path was checked before writing and did not exist. The name was also checked against the existing `r6_ideas` filenames.
- The permitted project range is 2020-11-27 through 2026-10-30; the only market-data feasibility sample read for this screen is dated in 2024. Date predicates were applied when reading the Parquet minute panel and dated SIC/roster tables. The small JSON bar-probe files contain only their named 2024 sample dates.
- No path to the holdout was used. No project forward returns, ICs, signal outcomes, or portfolio outcomes were computed. Result-bearing sections of `R5_FINAL.md` and decision-log outcome lines were not opened; the overlap review below uses the named R6 idea screens and preregistration design only.
- If a later reviewer requires a broader inventory than the permitted overlap checks, stop before any additional data or outcome access and ask for coordinator review.

## 1. Overlap with prior work

| Nearest work | What it already tests | Difference and remaining overlap |
|---|---|---|
| J1 weekly SIC2-relative reversal (`specs/r6_prereg/J1.md`, `r6_ideas/J.md`) | A stock's prior five-session return relative to SIC2 peers predicts the next week's peer-relative return; S&P mechanism, Dow portfolio. | This candidate uses peer illiquidity shocks, not prior relative returns. It reuses the same SIC2 cross-asset edge and short weekly horizon. |
| G1 own-stock high-volume visibility (`specs/r6_prereg/G1.md`) | Positive effect of each stock's own five-session standardized volume shock over the next 21 sessions. | Amihud combines absolute price movement with dollar volume and here aggregates across other same-industry firms; it is not an unsigned volume-only attention score. The shared price/volume inputs and liquidity-demand interpretation make it adjacent. |
| Z minute-flow screens (`r6_ideas/Z_minute_flow.md`, `Z_intraday_mom_rescreen.md`, `Z_auction_eod.md`) | Minute-bar signed-flow proxies, peer-flow ideas, intraday momentum and close/auction pressure. | Amihud is unsigned and measures price impact per dollar rather than buyer-initiated flow; the SIC2 peer-transfer question overlaps the Z peer-flow direction, while this measure is not a relabeling of signed flow. |
| AG closing liquidity-gap screen (`r6_ideas/AG_close_liquidity.md`) | Close-auction price displacement / liquidity-gap reversal. | Different frequency and statistic, but both use liquidity-stress language and short-horizon price adjustment. |

**Verdict: PASS narrowly on signal novelty.** No reviewed J1, G1, or Z design uses peer Amihud illiquidity as its input. The SIC2 propagation graph and short horizon are reused, so any later registration would need to keep the exact variable and not add signed-flow or return-reversal substitutions. The literature supports liquidity spillover mechanisms in specific settings but does not establish that this bar-based peer signal is buying pressure in Dow firms.

## 2. Exact pressure measure and dated data source

**One fixed candidate, if the coordinator authorizes further work:** For source S&P issuer `j` on completed regular-session day `d`, compute the standard daily Amihud ratio

```text
ILLIQ[j,d] = abs(split-adjusted close-to-close return[j,d])
             / (raw close[j,d] * raw share volume[j,d])
```

The ratio is absolute daily return per dollar traded. Using only the previous 60 valid sessions of that source issuer, standardize the ratio in levels:

```text
z[j,d] = (ILLIQ[j,d] - mean(ILLIQ[j,d-60:d-1]))
         / sample_sd(ILLIQ[j,d-60:d-1])
```

Require 60 prior observations and positive dollar volume; a zero baseline standard deviation or a missing bar gives a missing score. No winsorization, alternate baseline, or other transform is proposed. At each Friday close `t`, each Dow target `i` receives the equal-weight mean of source peers' `z[j,d]` for each of the last five completed sessions `t-4,...,t`, then averaged over those five sessions. Source peers are point-in-time S&P constituents with the same dated SIC2 as target `i`; exclude the target's own issuer/CIK and require at least two distinct source peers per day. Higher score means peers recently became more illiquid. The fixed hypothesis sign is **negative**: elevated peer liquidity stress predicts lower Dow target returns over the next five sessions. This tests stress transmission, not positive buying pressure.

Formation is at the Friday close using only bars and SIC2 records effective by that close; prediction, if later authorized, is the Dow target's adjusted open-to-close return from the next session's open through the fifth session's close, relative to available-name EW30. Use non-overlapping five-session formations. The 60-session warm-up starts no earlier than 2020-11-27; no earlier warm-up data may be read. The exact first formation date must be fixed from the development calendar and input availability before outcomes.

The candidate data source is Alpaca historical stock bars, with daily OHLCV for the primary measure and one-minute OHLCV as a coverage/reconciliation input. Alpaca documents `1Day` and minute timeframes, feed selection (including SIP and IEX), timestamps, and pagination in its [historical bars API](https://docs.alpaca.markets/us/reference/stockbars); its [market-data FAQ](https://docs.alpaca.markets/us/v1.1/docs/market-data-faq) describes bar aggregation. API authentication and the required historical feed entitlement must be confirmed for a full research pull. Local staged samples establish a few rows can be read; they do not establish bulk access rights, completeness, or a free full-history entitlement. SIC2 and membership must be point-in-time, not current classifications applied retroactively.

No signal values or outcomes were computed. The 2024 read only checked dated bar counts and dated membership/SIC coverage.

**Verdict: FAIL for ready-to-test data completeness.** The staged 2024 sample is small, the minute bars have a missing-row example, and a point-in-time Amihud signal panel has not been coverage-audited over the development window.

## 3. Point-in-time coverage and independent breadth

The input-only coverage checks are restricted to 2024. Arrow scan filters were applied to Parquet minute rows by `timestamp`; SEC SIC rows were restricted at scan time to effective dates on or after 2020-11-27 and before 2025-01-01; SIC snapshots were then taken no later than 2024-12-31. PIT membership intervals were filtered at scan time to overlap 2024.

| Input-only item | 2024 count | How obtained |
|---|---:|---|
| S&P PIT tickers | 520 | Unique roster tickers with membership intervals overlapping 2024 |
| S&P tickers with dated SIC | 514 | Latest eligible SIC record for each of those tickers, using only development-safe rows; 53 SIC2 groups |
| Dow PIT tickers represented | 33 | Unique ticker intervals overlapping 2024; roster membership changed during the year |
| Dow SIC2 groups | 19 | Distinct SIC2 groups among those dated Dow intervals; all 19 overlapped the S&P SIC2 set |
| Daily-bar probe | 3 symbols × 3 sessions | The bounded 2024 probe contains AAPL, CAT, and JNJ for 2024-06-03 through 2024-06-05 (nine symbol-days total) |
| Minute-bar sample | 4 symbols × 19 dates | June 2024 filtered timestamp rows: AAPL/MSFT/JNJ 7,410 each; CAT 7,368; dates 2024-06-03 through 2024-06-28 |
| Candidate score dates / names / nonmissing signals | Not computed | This screen did not calculate Amihud values or build a signal panel |
| Independent liquidity-shock events | Not counted | No Amihud values or thresholds were computed |

The minute sample shows three symbols with 390 bars per date-equivalent month coverage and CAT with 42 fewer bars than 19 × 390; the exact cause and daily distribution of those missing bars were not investigated. The small daily probe establishes only three sessions for three names. Neither sample demonstrates full-panel daily signal coverage for 520 S&P names or continuous Dow peer coverage. SEC SIC histories can lag corporate classification changes; issuer/ticker changes, delistings, halts, missing bars, and the distinction between split-adjusted returns and raw dollar volume require a frozen point-in-time input QA. The mechanical cross-section is at most 30 Dow names and only 19 SIC2 groups in the 2024 membership slice; names within each SIC2 receive the same or very similar source-peer score, producing rank ties and substantially fewer independent signals than 30.

**Verdict: FAIL.** The observed sample is too small to establish valid daily/minute coverage, and the 19-group target breadth implies clustered, tied scores rather than 30 independent observations.

## 4. Effective breadth and power at a sourced plausible effect

### Literature evidence and transfer limits

- Amihud, [“Illiquidity and Stock Returns: Cross-Section and Time-Series Effects,” *Journal of Financial Markets* 5(1), 31–56 (2002)](https://doi.org/10.1016/S1386-4181(01)00024-6), defines illiquidity using average absolute daily return divided by dollar volume. The paper studies NYSE common stocks in 1963–1997, with monthly Fama–MacBeth cross-sections over 1964–1997 (408 months). It reports higher expected returns for stocks with higher expected illiquidity, while contemporaneous stock returns are negatively related to unexpected market illiquidity; the premium is stronger among smaller firms. This is a long-horizon expected-risk-premium result and contemporaneous market-liquidity result, not a one-week interfirm SIC2 spillover or a Dow rank IC.
- Honkanen and Schmidt, [“Learning from Noise? Price and Liquidity Spillovers around Mutual Fund Fire Sales,” *Review of Asset Pricing Studies* 12(2), 593–637 (2022)](https://doi.org/10.1093/rapstu/raab029), study U.S. mutual-fund fire-sale shocks and economic peers. Their paper describes an event sample spanning 1996–2013 and finds that the peer price-pressure/reversal effect is around one-third of the source-stock effect, with spillovers to liquidity; peer price effects reverse over following months. This is a forced-sale event signal on economic peers, not Amihud z-scores, not SIC2-only links, and not a modern Dow weekly IC.
- Bongaerts, Roll, Rösch, van Dijk, and Yuferova, [“How Do Shocks Arise and Spread Across Stock Markets? A Microstructure Perspective,” *Management Science* 68(4), 3071–3089 (2022)](https://doi.org/10.1287/mnsc.2021.3979), analyze intraday stock-price, market-liquidity, and trading-activity shocks across international markets. They report liquidity shocks are typically isolated and transitory and find little evidence that liquidity shocks drive price shocks or non-fundamental contagion. The market-wide cross-country design is not a same-industry firm-level rank IC, but it cautions against assuming any liquidity shock is an equity price-pressure signal.

The mechanism is plausible by analogy: investors may infer information from a temporary illiquidity/price-impact change in a related firm, and the fire-sale literature documents peer price and liquidity spillovers. However, the Amihud ratio is unsigned. It cannot distinguish buy-side from sell-side pressure; high values may be caused by information-driven moves or low dollar volume. The source literature does not provide a directly comparable post-2020 mega-cap weekly rank IC or a defensible numeric effect for this exact statistic. Large-cap liquidity and high analyst/investor coverage make temporary price-impact transmission less likely to persist; any network effect might occur quickly and disappear before next-week execution. The sign of a future-return effect is not pinned down by Amihud's risk-premium result.

### Synthetic power sensitivity

I ran `r4_harness/power_sim.py` using design assumptions only: 30 Dow targets, 286 non-overlapping weekly formation dates after a 60-session warm-up in the six-year development span, five-session horizon (NW lag 4), signal autocorrelation 0.5, and cross-sectional IC SD 0.19359. The IC SD is a design approximation using 19 SIC2 groups and assumed within-group dependence of 0.15; it is not estimated from project data. At an **illustrative, unsourced** planted mean IC of 0.02, 5,000 synthetic simulations with seed 20261111 gave `P(NW t ≥ 2) = 25.00%`, mean effective date count 128.54, and unadjusted 80%-power MDE 0.04852. This is not power at a sourced plausible effect because no independent paper reports a matching metric and setting. The simulator also does not impose exact within-SIC2 ties in scores, so its power is optimistic.

For a planning comparison only, applying the conservative one-sided 24-test Holm first-step approximation (z ≈ 2.87) used by the synthetic criterion-4 shape study raises the approximate 80%-power threshold to about 0.063. This is a normal-approximation scaling of the unadjusted MDE, not a Holm simulation and not an inspection of the current R6 family manifest. The actual cumulative family was not opened.

**Verdict: FAIL.** No sourced signal-matched effect exists for the power calculation; at the illustrative 0.02, synthetic power is only 25%, and the target cross-section is heavily clustered.

## 5. Criterion-4 portfolio feasibility first

If every earlier gate were later reconsidered and passed, the fixed portfolio candidate would rank the 30 point-in-time Dow constituents weekly by the peer illiquidity score, using a stable ticker tie-break for equal SIC2 scores, then use the rank-weighted top-half shape from `report_drafts/CRITERION4_BOUND_BY_SHAPE.md`: 15 long positions, active share about 55%, benchmarked against same-date EW30. Charge 0.05% per side; apply the exact decision-63 missing-price carry-and-sale rule to both books; require positive net excess return, higher net Sharpe than EW30, and one-sided block-bootstrap evidence with Holm adjustment across the full R6 family. Apply DSR using the cumulative trial count at execution. These are fixed-goal conditions, not relaxed for the screen.

The synthetic shape study gives a weekly 80%-power rank-IC hurdle of about 0.083 for RankTopHalf when signal autocorrelation is 0.5. Its assumed turnover is 91% per weekly rebalance; the simulated cost/gross-edge ratio is 16.7%, so it meets the design's alternative cost-ratio condition (<25%) under that hypothetical continuous-score model. The candidate's SIC2-constant scores create large ties, so that turnover and cost ratio may not transfer; no candidate turnover or cost was measured. There is no sourced estimate for this candidate's weekly rank IC, Sharpe, or expected peer return. The event-study magnitude from Honkanen and Schmidt cannot be converted into a rank IC without unsupported assumptions. Neither the criterion-4 excess Sharpe nor the Holm-adjusted bootstrap result can be credibly projected.

**Verdict: STOP — FAIL, criterion-4 infeasible on current evidence.** No evidence supports an effect near the synthetic 0.083 hurdle after costs, dependence, and Holm adjustment. Do not commission a portfolio run to learn this from outcomes.

## 6. Holdout availability and protocol

No holdout-specific input is needed for this screen. No sealed holdout price, roster, signal, or return was accessed. The candidate fails earlier gates and should not advance. If a future direction passes all screens and receives authorization, holdout work remains coordinator-controlled under goal criterion 5 after the code, preregistration, and input manifests are frozen and verified; any availability check must be limited to the specified availability-only roster/row-count evidence.

**Verdict: PASS for screen data handling only; no holdout test is proposed.**

## Final screen decision

**Overall: STOP — FAIL.** The Amihud variable is distinct from J1, G1, and Z inputs, but it is unsigned and does not identify buying pressure; the local 2024 sample does not establish full input coverage; the relevant peer-spillover literature concerns specific forced-sale events rather than this daily ratio; and no sourced effect plausibly clears the criterion-4 weekly hurdle.

Evidence that could change this decision would include a complete date-filtered development-only input audit, a directly relevant post-2020 U.S. large-cap study with a weekly SIC-peer effect estimate in rank-IC units, and independent evidence that an unsigned Amihud spike has a stable directional relationship with target-peer returns after excluding the target's own signal and common industry news. Do not calculate signal outcomes or run a portfolio unless all gates are re-reviewed and pass.

**Reviewer/date:** dispatched worker / 2026-11-11.

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
