# R6 Idea Screen — Z: minute-bar signed-flow pressure

**Status:** SCREEN ONLY — no signal outcomes, return calculations, or variant authorization. **Overall verdict: STOP — FAIL.**

This screen uses only the 2024 samples already staged in `r6_data/alpaca/`. It did not request or load market data dated before 2020-11-27, calculate any signal, or inspect any forward return. The paper samples discussed below have their own historical research windows; those are literature descriptions, not project data pulls.

## Identity and immutable-path preflight

- **Proposed short name:** Z minute-flow pressure. Candidate measures are (1) bulk-volume-classified intraday imbalance, (2) daily signed order-imbalance persistence, and (3) leave-one-out SIC2 peer flow.
- **Exact new output path:** `r6_ideas/Z_minute_flow.md`.
- **Existence check:** the target path was absent before writing this file.
- **Name check:** `Z_minute_flow` was not present among the existing `r6_ideas` files or the R5 final-draft artifact names.
- **Permitted data period:** project worker inputs begin no earlier than **2020-11-27**; the only price-data files read for this screen are 2024 samples in `r6_data/alpaca/`.
- **Holdout boundary note:** decision 154 says Alpaca stock history begins in 2016 and a future coordinator-only Alpaca holdout could cover **2016-01 through 2020-10**, with **2010–2015 disclosed as a data gap**. No such holdout input was opened, requested, or used here.
- **Path/date ambiguity:** none for the 2024 feasibility check. Any future bulk pull or holdout request still requires coordinator authorization and a frozen specification.

## 1. Overlap with prior work

| Candidate | Nearest prior work | Difference and remaining overlap | Gate |
|---|---|---|---|
| BVC minute flow | D1 Reg SHO short-sale volume; D2 OTC non-ATS flow; the earlier signed-flow and microstructure screens | Reg SHO records short-sale-marked volume, not buyer- versus seller-initiated total flow. BVC attempts to infer trade-side volume from price changes, but its bar-based estimate is still a proxy and can overlap daily price/volume scores. BVC/VPIN's main literature construct is flow toxicity and liquidity risk, not a clean positive-return pressure signal. | **FAIL**: not a distinct, validated directional return mechanism with a sourced effect. |
| Daily imbalance persistence | Earlier signed-flow and intraday pressure concepts; the marketable-retail-imbalance literature in `r6_ideas/M_SURVEY.md` | Consolidated all-market bar-derived net imbalance is different from retail-only TAQ trade classifications and short-sale volume, but the empirical hypothesis is close to candidate 1 once BVC bars are aggregated by day. Treat these as competing measurement designs under one family, not two independent discoveries. | **FAIL**: overlap plus no compatible modern large-cap magnitude. |
| SIC2 peer-flow spillover | **E1**, monthly SIC2 peer CLV pressure; D4 ownership-network links; other SIC peer-pressure ideas | A valid signed-flow measure is conceptually different from E1's close-location-value (CLV) proxy, but uses the same leave-one-out SIC2 edge and asks the same peer-pressure-to-return question. It is a useful measurement improvement in principle, but is not sufficiently novel for a new family without a newly justified network mechanism. | **FAIL**: too close to E1 on graph, target, and thesis; order-book flow not in the bar bundle. |

The closest **positive reason** to consider the track is that signed buyer/seller pressure is more direct than candle CLV. The closest **negative reason** is that an aggregated minute bar is not a signed trade: it has no buyer/seller initiator tag, and OHLCV cannot recover the contemporaneous quote or limit-order-book event path.

## 2. Exact pressure measure and dated data source

All three candidates would use SIP one-minute bars, with only information timestamped at or before the formation close, and would use the point-in-time universe/SIC mapping separately. There is no proposal to use a 2016–2020 price series during this screen.

### Candidate 1 — BVC imbalance over the prior 21 sessions

For each name and minute, estimate buy- and sell-side volume from the price change of equal-volume buckets using a fixed normal-CDF BVC rule; daily signed imbalance is `(estimated buy volume - estimated sell volume) / total eligible volume`. The candidate score would be the trailing 21-session mean daily imbalance, known after the last formation-day bar is finalized, predicting the next 21-session return with a **positive** sign. This is an estimated side classification, not observed aggressor-side volume. The original BVC method uses volume-synchronized buckets; applying it to 1-minute OHLCV would be an adaptation because minute bars are time bars and do not disclose within-minute trade ordering.

Easley, López de Prado and O’Hara, [“Flow Toxicity and Liquidity in a High-Frequency World,” *Review of Financial Studies* 25 (2012), 1457–1493](https://doi.org/10.1093/rfs/hhs053), introduce BVC as part of VPIN/flow-toxicity measurement. Their published use is about adverse selection/liquidity risk, including E-mini S&P 500 futures, rather than a stock-level monthly signed-flow premium. Chakrabarty, Pascual and Shkilko, [“Evaluating Trade Classification Algorithms: Bulk Volume Classification versus the Tick Rule and the Lee-Ready Algorithm,” *Journal of Financial Markets* 25 (2015), 52–79](https://doi.org/10.1016/j.finmar.2015.06.001), find BVC less accurate than tick and Lee–Ready classification even in frequently traded and largest stocks; the paper does not provide a post-2020 Dow monthly-return effect.

### Candidate 2 — daily signed-imbalance persistence

Use the same fixed minute-bar direction-classification rule, aggregate all eligible minute-volume estimates to a daily signed imbalance, and form a fixed 21-session average as of month-end. Predict the next 21-session return with a **positive** sign, motivated by order-splitting/temporary-price-pressure evidence. This is an aggregate daily flow persistence measure, not a retail-flow score; no investor category can be inferred from OHLCV. The aggregation is prior-only; it must not use the formation day's next-session price or any later bar.

Chordia and Subrahmanyam, [“Order Imbalance and Individual Stock Returns: Theory and Evidence,” *Journal of Financial Economics* 72 (2004), 485–518](https://doi.org/10.1016/S0304-405X(03)00175-2), use transaction-based order signs for NYSE stocks over 1988–1998 (about 1,322 names on average). They report a positive lagged-imbalance/return relation consistent with inventory pressure and statistically significant imbalance strategies; their model also makes the lagged sign reverse after controlling for current imbalance. The paper does not report a rank IC comparable to this screen or establish an effect in post-2010 mega-caps. Chordia, Roll and Subrahmanyam, [“Evidence on the Speed of Convergence to Market Efficiency,” *Journal of Financial Economics* 76 (2005), 271–292](https://doi.org/10.1016/j.jfineco.2004.06.004), find daily order imbalance persistent even as daily returns are not serially correlated, emphasizing that order-flow persistence does not imply persistent standalone return continuation.

### Candidate 3 — leave-one-out SIC2 peer signed flow

At each monthly formation close, compute each source firm's trailing 21-session signed imbalance by the fixed rule above, then average the peers' values within dated SIC2, excluding the target firm. Predict the target's next 21-session return with a **positive** sign. SIC2 and roster membership must be point-in-time; the score is not defined if the target has no eligible peer. This explicitly tests pressure transmission, but the graph/hypothesis overlaps E1.

Cont, Cucuringu and Zhang, [“Cross-Impact of Order Flow Imbalance in Equity Markets,” *Quantitative Finance* 23 (2023), 1373–1393](https://doi.org/10.1080/14697688.2023.2236159), use Nasdaq LOBSTER event data for the top 100 S&P 500 names during 2017–2019. Lagged cross-asset order-book OFI improves forecasts at short horizons, with effects decaying rapidly; the article does not establish monthly rank IC or after-cost Dow performance. Hasbrouck and Seppi, [“Common Factors in Prices, Order Flows, and Liquidity,” *Journal of Financial Economics* 59 (2001), 383–411](https://doi.org/10.1016/S0304-405X(00)00091-X), document common order-flow factors in the Dow 30 and find order-flow commonality explains a substantial share of return commonality, but do not establish future SIC2 peer return drift. Hameed, Morck, Shen and Yeung, [“Information, Analysts, and Stock Return Comovement,” *Review of Financial Studies* 28 (2015), 3153–3187](https://doi.org/10.1093/rfs/hhv042), support industry information transmission from prominent to neglected firms, but the transmitted variable is information/price movement, not measured signed buying pressure.

**Source and timing for all candidates.** The local `r6_data/alpaca/ALPACA_AUDIT.md` records that 2024 SIP minute-bar and daily-bar queries succeeded and that one-minute bars have timestamp, OHLC, volume, trade count, and VWAP fields. Alpaca describes the [historical bars schema](https://docs.alpaca.markets/us/reference/stockbarsingle-1) and notes that bars aggregate eligible trades; its [market-data FAQ](https://docs.alpaca.markets/us/v1.1/docs/market-data-faq) explains timestamps, conditions, and feed differences. Use `feed=sip`, not IEX, for consolidated market coverage; availability of historical SIP samples does not imply free real-time SIP entitlement or a complete archival panel. The screen computes no forward returns, ICs, portfolio returns, or outcome statistics.

## 3. Point-in-time coverage and independent breadth

The permitted 2024 sample-only count check found:

| File | Scope | Symbols | Sampled dates/interval | Rows with expected `t,o,h,l,c,v,n,vw` fields | What it establishes |
|---|---|---:|---|---:|---|
| `r6_data/alpaca/bars_1min_dow_2024.json` | SIP, AAPL/CAT/JNJ | 3 | Six minute labels on 2024-06-03 | 18/18 | Schema works for three Dow names and a six-minute window. |
| `r6_data/alpaca/bars_1day_dow_2024.json` | SIP, AAPL/CAT/JNJ | 3 | 2024-06-03 through 2024-06-05 | 9/9 | Daily OHLCV/count/VWAP fields are present for those three sample dates. |

These are **sample coverage counts only**, not signal coverage: no buy/sell signs, imbalance values, return values, eligible-name counts, price gaps, or outcomes were computed. The one-minute file covers one date and six minute bars per symbol, not a full session; it supplies 3 distinct names and 0 independently measured event clusters. No point-in-time SIC2 code is in these bar records, so SIC2 group count is **not available from this sample**. The sample is too small to establish S&P 500 or Dow-wide historical completeness, survivorship, symbol-lineage coverage, stable session counts, or the proportion of valid monthly observations.

Coverage risks and prerequisites:

- The 2024 illustrative sample uses current symbol labels; a full test needs the point-in-time S&P/Dow rosters and corporate-action/ticker lineage and must explicitly disclose surviving-name selection.
- One-minute bars omit minutes with no qualifying trades and may be revised for late prints; time bars can also hide within-minute sequencing. A formation rule must fix regular-session hours, auction treatment, trade conditions, missing-minute handling, and late-bar finalization.
- BVC needs volume-synchronized buckets and price changes at the bucket boundary; time bars require an interpolation or adaptation rule. Tick-rule/Lee–Ready alternatives need transaction observations; quote-based classification needs synchronized quotes, which are outside the requested bar bundle.
- A “peer flow” group requires a separate dated SIC2 join. The 2024 symbol sample contains no issuer industry metadata, and no cluster count is inferred from names.
- The project audit estimates about 30,000 SIP minute-bar pages for a full S&P 500 development panel. It characterizes such a pull as technically available, but it is separate from this three-symbol sample and does not prove PIT completeness.

**Verdict:** **FAIL** for all three candidates at this gate. The local sample establishes schema feasibility but not point-in-time coverage, nonmissing signal frequency, independent event count, or industry breadth.

## 4. Effective breadth and power at a sourced plausible effect

The literature establishes some directional or short-horizon relationships, but it does **not** give a compatible monthly cross-sectional rank IC for these exact bar-derived scores in post-2010 mega-cap stocks. I therefore do not claim an empirically sourced effect range. For design sensitivity only, I ran `r4_harness/power_sim.py` with 1,450 daily formation observations (roughly six years), five-session horizon / Newey–West lag 4, signal autocorrelation 0.20, 1,000 simulations, fixed seed `20261111`, and its default null rank-IC SD (1/\sqrt{N-1}). Two cross-sections were used: 500 names and a conservative 70 independent SIC2-group proxy. The effect grid is an **assumption grid**, not an effect inferred from the project or a paper.

| Synthetic design | IC 0.005 power | IC 0.010 | IC 0.020 | IC 0.050 | IC 0.083 | 80%-power MDE |
|---|---:|---:|---:|---:|---:|---:|
| S&P proxy, 500 independent names | 0.941 | 1.000 | 1.000 | 1.000 | 1.000 | 0.0039 |
| SIC2 cluster proxy, 70 independent groups | 0.279 | 0.749 | 0.999 | 1.000 | 1.000 | 0.0105 |

These are powers for the simulator's unadjusted **NW t ≥ 2 mechanism test**, not Holm-adjusted power, portfolio-level power, or observed IC results. The SIC2 calculation treats the 70 groups as independent cells; it does not measure actual cluster count or dependence in the 2024 sample. The 2023 cross-impact study has a large-cap sample and post-2010 intraday evidence, but its outcome is very short-horizon forecasts using order-book events. Its result cannot be transported into a 21-session bar-derived rank IC without an unsupported conversion. Chordia–Subrahmanyam’s older daily result is also not a quantified modern large-cap effect estimate.

**Verdict:** **FAIL.** Sensitivity shows that an assumed 0.01–0.02 IC could be detected in a large simulated panel, but no matched, independently sourced plausible IC exists for these exact signals. Power is not evidence that the effect reaches the portfolio hurdle.

## 5. Criterion-4 portfolio feasibility first

For a common comparable screen, suppose the Dow book is long-only top five, monthly formation/rebalance, no shorts, a 20% total-notional turnover cap per rebalance, at least 50% active share, 0.05% cost per traded dollar, and an available-name EW30 benchmark. These are planning assumptions, not a portfolio run. The six-year development sample supplies at most about 72 monthly observations; the current R6 Holm manifest contains 21 endpoints, so a future three-endpoint confirmatory family would have at least 24, and later additions could raise it further.

The independent [criterion-4 bound audit](../report_drafts/CRITERION4_BOUND_AUDIT.md) estimates that top-five Dow versus EW30 needs a monthly rank IC around **0.083–0.087** to have a plausible path to positive net excess, Sharpe above EW30, and a one-sided block-bootstrap result after Holm, under its explicit assumptions. `break_even_rank_ic` gives a much smaller cost-only floor near **0.001155** at 20% turnover and 6% monthly return dispersion; that floor does not establish statistical or Sharpe feasibility. The public studies above do not report the matching effect. The BVC paper's accuracy comparison is not a return IC; Chordia–Subrahmanyam report significance but no transferable mega-cap monthly rank IC; Cont et al. report one-minute model forecasts with no direct basis for a monthly IC. No evidence supports effects near 0.083 for these designs.

**Dow book verdicts:**

- **BVC:** **STOP — FAIL: criterion-4 infeasible.** Side-classification error and the lack of a sourced large-cap monthly effect prevent a credible excess-Sharpe/after-cost case.
- **Daily order-imbalance persistence:** **STOP — FAIL: criterion-4 infeasible.** The older persistence result does not establish a modern mega-cap signal of the required magnitude; return autocorrelation can be absent even when flow is persistent.
- **SIC2 peer flow:** **STOP — FAIL: criterion-4 infeasible.** The best direct cross-impact evidence is minute-scale and order-book-based; no sourced monthly effect can justify the 0.083–0.087 range, and the setup substantially repeats E1's peer hypothesis.

At 0.05% per side, 20% monthly turnover, top-five active weights, and a six-year sample, none has an evidence-based net return, Sharpe, or Holm-adjusted block-bootstrap path. No criterion is relaxed and no portfolio simulation on project outcomes was performed.

## 6. Holdout availability and protocol

This screen has no holdout-specific input and did not inspect, request, read, plot, or calculate on sealed prices, returns, or signals. Decision 154 records that Alpaca's stock history starts around 2016; a future criterion-5 run using that source must pre-register the available **2016-01 to 2020-10** portion and disclose the unavailable **2010–2015** period as a data gap. That statement is availability metadata only; it does not authorize a worker to pull those dates. Only a coordinator-controlled run after preregistration, code, and input manifests are frozen and hash-verified may touch the approved holdout inputs.

Availability evidence for a later coordinator review would include source coverage, point-in-time security membership and ticker lineage, SIC panel coverage, known missing names/dates, and a documented reason for the 2010–2015 gap. This screen does not claim any of those holdout values or coverage counts.

**Verdict:** **FAIL to advance**: the signed-flow idea is not currently justified for holdout review because the earlier gates failed.

## Final screen decision

- **Overall:** **STOP — FAIL.** No candidate passes all gates; no preregistration or variant should be commissioned from this screen.
- **Expected-edge rank (highest first, not data convenience):**
  1. **SIC2 peer cross-impact.** Best direct large-cap and post-2010 mechanism evidence, but the published signal is order-book OFI at short horizons, not bar-derived monthly pressure; it overlaps E1 and fails data/hurdle tests.
  2. **Daily signed-imbalance persistence.** A plausible inventory-pressure mechanism has classic daily evidence, but sign can reverse conditional on current imbalance, the sample predates 2010, and modern large-cap magnitude is unestablished.
  3. **BVC imbalance.** BVC is most directly tied to the named method, but the evidence is about flow toxicity and classification, BVC is less accurate than trade-by-trade rules even for the most active names, and no large-cap directional return edge is sourced.
- **Evidence that could change the decision:** a licensed/validated buyer-initiated trade or order-book input with point-in-time coverage for the development universe, a strictly pre-specified independent mechanism test, and an independently documented effect-size range consistent with the criterion-4 hurdle. A larger simulation sample alone would not change the feasibility verdict.
- **Reviewer/date:** L2 screen, 2026-11-11.

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
