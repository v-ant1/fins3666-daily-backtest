# R6 effect-first screen — large-cap predictors against the hurdle

**Screen status: STOP — FAIL.** I first looked for published large-cap effects that could plausibly clear the stated weekly 0.074 or monthly 0.120 rank-IC scale. One nonlinear price-chart predictor has an unusually large reported top-500 weekly long-short Sharpe, so it is the sole provisional survivor of the literature-only screen; the full screen below then fails because the return effect is not a direct signed-pressure measure, the reported period is pooled, turnover overwhelms the stated cost assumption, and the paper's trained model cannot be reproduced from the six-year 30-name project sample without substantial new model development. No project signal, forward return, IC, portfolio return, or outcome was calculated.

## 1. Published effect ranking (completed before thesis/data/novelty screening)

| Rank | Predictor and source | Documented large-cap effect | Date/horizon details | Hurdle assessment |
|---:|---|---|---|---|
| 1 | Nonlinear price/volume chart-image score — Jiang, Kelly and Xiu (2023), [*Journal of Finance*](https://doi.org/10.1111/jofi.13268). | Largest-500 restriction: weekly 15-day-image/five-day-return H-L portfolio reports **0.12% per five-day holding period, annualized Sharpe 1.02, and 712% monthly turnover**. This is a large-cap portfolio statistic, not a rank IC. | Trained 1993–2000, held fixed OOS 2001–2019. So the OOS window contains 2011–2019, but the paper does **not** isolate the largest-500 result for that post-2010 subperiod. | **Closest scale match, conditional:** the reported long-short Sharpe is substantial, but not a rank-IC equivalent without assumptions. Turnover is separately assessed below. |
| 2 | Marketable retail order imbalance — Boehmer, Jones, Zhang and Zhang (2021), [*Journal of Finance*](https://doi.org/10.1111/jofi.13033). | In the largest market-cap tercile, the one-week quintile spread is **0.067% (6.7 bp), t=1.78**; longer-horizon long-short results for that tercile are statistically insignificant. | Main sample focuses on 2010–2015; next-week cross-section. | **Below requested scale:** no published R6-equivalent rank IC, and the large-cap effect is small and weakly significant. |
| 3 | Cross-asset order-flow imbalance — Cont, Cucuringu and Zhang (2023), [*Quantitative Finance*](https://doi.org/10.1080/14697688.2023.2236159). | Top-100 S&P names; lagged OFI predicts at short intraday horizons, with rapid decay. No weekly/monthly large-cap spread or rank IC matching this hurdle is reported. | Nasdaq/LOBSTER event data 2017–2019; intraday. | **Not comparable:** relevant cross-asset effect, but no evidence it reaches the weekly/monthly hurdle. |
| 4 | 52-week-high anchoring / price momentum — George and Hwang (2004), [*Journal of Finance*](https://doi.org/10.1111/j.1540-6261.2004.00695.x); Chen, Stivers and Sun (2024), [*Journal of Empirical Finance*](https://doi.org/10.1016/j.jempfin.2024.101556). | The recent study documents conditional one-month continuation when both turnover and price-to-high are high; it does not give a standalone post-2020 mega-cap effect at the requested scale. | Published 2024; conditional one-month effect. | **No scale evidence:** an effect-size estimate comparable to the hurdle is not established. |

## 2. Second-stage screen of thesis fit, data and prior work

| Rank | Pressure-thesis fit | Available inputs / implementation | Nearest existing R6 screens | Second-stage result |
|---:|---|---|---|---|
| 1 | **Indirect fit:** chart shape may reveal temporary pressure persistence or reversal; it observes no buyer/seller signs and does not identify causal buying pressure. | Staged daily OHLCV can form image inputs; it does not include the paper's pretrained model or the paper's pre-2001 training set. A new six-year Dow CNN would be a different model. | `AF_52wk.md` (one-year price barrier), `B.md` (price/trend ideas), `Z_intraday_mom_rescreen.md` and `Z_minute_flow.md` (price/flow proxies). The nonlinear learned image mapping differs from a fixed 52-week-high ratio or signed-bar proxy, but remains an own-stock price-history signal. | **Provisional survivor → full screen below; final fail.** |
| 2 | **Direct fit:** marketable retail net buying is interpreted as partly persistent pressure and partly information. | The relevant retail trade classifier is not present in the staged Alpaca OHLCV fields. | `AE_retail_bjzz.md`, `AP_retail_popularity.md`, `Z_minute_flow.md`, and `M_SURVEY.md` already screen retail or signed minute flow. | **FAIL:** scale, source availability, and novelty gates. |
| 3 | **Strong conceptual fit:** signed peer order-book pressure can transmit across assets. | Alpaca minute OHLCV does not include event-level queue depth or OFI; LOBSTER is a different, non-staged input. | Peer-flow / SIC network family in `Z_minute_flow.md`, `AA_highIC_lit.md`, and `X_comovenet.md`. | **FAIL:** no comparable effect statistic and no distinct/available book input. |
| 4 | **Possible persistence**, but price barrier is not signed flow. | Daily price data exist, but this was already screened. | `AF_52wk.md`, `B.md`, and the peer-high discussion in `E.md`. | **FAIL:** previously screened and not new. |

The sole provisional survivor is evaluated against the full template below. A published effect that is detectable among hundreds of names is not automatically evidence for the 30-name project, and a weekly portfolio Sharpe is not a measured rank IC.

---

# R6 Idea Screen — AR nonlinear price/volume chart pressure

**Status:** SCREEN ONLY — no signal outcomes, forward-return calculations, portfolio returns, or variant authorization.

## Identity and immutable-path preflight

- **Proposed short name and mechanism:** AR chart-pressure patterns; nonlinear interactions among a stock's recent price path and volume may identify continuing or reversing price pressure.
- **Exact new output path:** `r6_ideas/AR_effect_first.md`.
- **Existence check:** this exact path was absent before this report was created.
- **Name/overlap check:** `AR_effect_first` is new. I reviewed existing `r6_ideas/*.md` screens for the nearest overlaps listed above. I did not open `R5_FINAL.md`, the Holm family, decision outcome lines, or runner outputs because this task is a no-outcomes literature screen.
- **Development boundary:** project input counts below use only rows satisfying `date >= 2020-11-27`; no worker input before that date or any holdout path was used.
- **Path/date ambiguity:** none for the read-only coverage count or report target.

## 1. Overlap with prior work

`AF_52wk.md` tests a single own-stock distance-to-52-week-high measure, while `Z_intraday_mom_rescreen.md` screens intraday price continuation and `Z_minute_flow.md` screens bar-derived imbalance. The candidate here is the published nonlinear transformation of a multi-day OHLC, volume and moving-average image. It is not the same fixed characteristic or a signed-flow estimate. It nevertheless shares the same own-name price-history substrate, and its mechanism is not demonstrably buying pressure. The model's Table V reports small average cross-sectional correlations between its short-horizon forecasts and 52-week-high (`−0.04`) and weekly trend (`−0.34`), suggesting distinct forecasts in its sample, but that is not proof of novelty in this project's 30-name implementation.

**Verdict: PARTIAL / FAIL for thesis novelty.** The model is a meaningfully different predictor, but adapting a black-box price forecast to this project does not directly test pressure persistence, pressure transmission, or reversal. No network or independent buying-pressure input is present.

## 2. Exact pressure measure and dated data source

The published score is the CNN's predicted probability of a positive five-day return from a chart image containing a 15-trading-day history of daily open, high, low, close, volume, and moving averages. In the paper, the image score is formed at the signal date and used to rank stocks for the following five-day return; the actual model is trained using 1993–2000 U.S. data, then fixed throughout its 2001–2019 test period. This is the paper's predictor, not a signal I reconstructed. Its interpretation as latent buying-pressure continuation/reversal is **my inference**, not the authors' identified causal mechanism.

The staged project input inspected was `r6_data/sp500_ohlcv_dev.parquet`; I read only `date` and `ticker` columns with a PyArrow filter `date >= 2020-11-27`. The filter returned **716,987 rows, 1,488 dates, and 564 distinct ticker labels**, spanning 2020-11-27 to 2026-10-30. These are input coverage counts, not price statistics or signal/outcome measures. The input has daily OHLCV, but the project development panel does not provide a ready-trained chart model, an eight-year prior training sample, or a point-in-time training/validation/test protocol equivalent to the paper. The extra ticker labels do not establish a fixed 500-name point-in-time roster.

Sources:

- Jiang, Kelly and Xiu, [“(Re-)Imag(in)ing Price Trends,” *Journal of Finance* 78 (2023), 3193–3247](https://doi.org/10.1111/jofi.13268), [paper PDF](https://economics.yale.edu/sites/default/files/2023-11/The%20Journal%20of%20Finance%20-%202023%20-%20JIANG%20-%20Re%25E2%2580%2590%20Imag%20in%20ing%20Price%20Trends_0.pdf). The paper states its U.S. sample is 1993–2019, its model is trained/validated once on 1993–2000 and held fixed in 2001–2019, and Table IV restricts the universe to the largest 500 stocks.
- Boehmer, Jones, Zhang and Zhang, [“Tracking Retail Investor Activity,” *Journal of Finance* 76 (2021), 2249–2305](https://doi.org/10.1111/jofi.13033), an adjacent, direct-flow benchmark. The largest-cap tercile's weekly spread is only 6.7 bp with t=1.78; this does not validate the chart CNN as a buying-pressure measure.
- Murray, Xia and Xiao, [“Charting by Machines,” *Journal of Financial Economics* 153 (2024), article 103791](https://doi.org/10.1016/j.jfineco.2024.103791), use trailing 12 monthly cumulative returns rather than the chart image and report forecast power among the largest 500 stocks and in their 2015–2022 subperiod. This is a second large-cap nonlinear price-history result, but the paper's forecast is not a signed pressure measure, so it is corroborative context rather than an independent effect estimate for this candidate.

**Verdict: FAIL for exact reproduction from available project inputs.** Daily price and volume fields exist, but the paper's learned model and pre-2020 training history are not part of the permitted development data; fitting a new CNN on the project's short sample would be a materially new model and cannot inherit the published effect-size estimate.

## 3. Point-in-time coverage and independent breadth

The input-only filtered read gives 1,488 distinct development dates and 564 ticker labels in the staged S&P OHLCV panel. It does not establish 564 simultaneous active names on each date, corporate-action-adjusted image construction, the number of complete 15-day image windows by name, SIC2/event breadth, or signal nonmissingness. No signal was formed, and therefore usable signal counts are **not established**. The published effect's large-cap universe is selected monthly by market capitalization; the staged file's ticker labels do not substitute for that dated ranking. Survivorship and symbol-lineage completeness remain unresolved.

**Verdict: FAIL.** The sample row counts show that daily OHLCV is staged, but they do not establish enough point-in-time breadth or independent names for a robust model trained and tested solely within this project's permitted window.

## 4. Effective breadth and power at a sourced plausible effect

The source reports a top-500 H-L Sharpe of **1.02** for the weekly 15/R5 image model and 0.12% per five-day holding-period return. It does not report a rank IC for the top-500 restriction, and it aggregates the large-cap test statistic over 2001–2019 rather than isolating 2011–2019. Thus it is not valid to claim that this equals the requested weekly rank-IC hurdle of 0.074. The separate reported Sharpe is a strong literature effect-size clue, but it is not an effect estimate for a 30-name top-half strategy.

For design sensitivity only, I ran `r4_harness/power_sim.py` with **30 assets, 312 weekly dates, 5-day horizon, signal autocorrelation 0.20, planted mean IC 0.074, 5,000 simulations, seed 20261111**. The synthetic harness produced 100% power for its one-sided NW t≥2 statistic and an 80%-power minimum detectable IC of 0.0350. This is not Holm-adjusted and the planted IC is a threshold scenario, not a paper-derived conversion or an estimate from project returns. The project cannot inherit the paper's estimated chart model, so the actual plausible rank IC for the proposed 30-name implementation remains **unknown**.

**Verdict: FAIL.** The paper's reported weekly long-short Sharpe is not the requested 30-name rank IC, the pooled test window does not isolate the post-2010 large-cap subperiod, and no published effect can be assigned to a newly fitted six-year Dow CNN without assuming transfer.

## 5. Criterion-4 portfolio feasibility first

A hypothetical portfolio would use the synthetic audit's weekly `RankTopHalf` shape: rank-weight the top 15 of 30 Dow names, with 55% active share, rebalance weekly, and compare net returns against EW30. The cost convention is 0.05% of total traded notional (buys plus sells); the audit reports 116% average total-notional turnover at signal persistence 0.20, with estimated costs at 24.1% of gross active edge at the hurdle. The audit's weekly 80%-power threshold is **0.074 mean rank IC** at ρ=0.20 (and 0.083 at ρ=0.50); these are synthetic design values, not empirical findings.

The paper's 15/R5 top-500 portfolio turns over **712% per month**. At a rough 5-bp-per-side cost rate and interpreting turnover as monthly total-notional turnover, that corresponds to an illustrative monthly cost of about 0.356% (0.05% × 7.12), versus the published 0.12% per five-day gross H-L return. The figures are not perfectly apples-to-apples because the return is a 5-session holding-period spread and turnover is monthly, but even the simple comparison warns that the source's very high-turnover effect cannot be assumed to survive the project cost rule. The source does not publish a matching net return or top-500 cost-adjusted result in the cited table.

**Verdict: FAIL — criterion-4 feasibility is not established.** No defensible conversion maps the paper's top-500 long-short Sharpe to the Dow rank-weighted top-half edge, and reported turnover makes the gross published effect unlikely to clear the required costs. Holm correction and the growing R6 family make the hurdle harder, not easier. No expected project Sharpe or bootstrap p-value is asserted.

## 6. Holdout availability and protocol

No holdout-specific input or path was used, opened, or requested. A future coordinator-controlled holdout would require a frozen model architecture, weights-training protocol, dated roster, and identical signal construction before the single authorized holdout execution; availability and date coverage must be checked by the coordinator before any outcome access. The source paper's old training sample is literature context, not the project's sealed holdout.

**Verdict: PASS for non-access; future availability remains unverified.**

## Final screen decision

**Overall: STOP — FAIL.** The published CNN pattern has a large-cap weekly spread and unusually strong reported Sharpe, but it is not a measured rank-IC result, its large-cap result is not isolated to the post-2010 subperiod, it does not identify signed buying pressure, the data do not support faithful training/reproduction, and the published turnover is incompatible with assuming the gross effect survives project costs. The retail-flow and cross-impact candidates fit pressure more directly but fail the effect-size, input, or overlap screens. No candidate is authorized for preregistration or portfolio testing.

Evidence that could change the decision would be an independent post-2010 large-cap replication reporting weekly rank IC or a directly comparable 30-name spread, a low-turnover/after-cost result, and a frozen implementable model trained without touching project outcomes.

**Reviewer/date:** dispatched worker / 2026-11-11.

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Effect-first idea screening.** Before proposing a new signal, identify published post-2010 U.S. large-cap predictors whose documented rank IC is comparable to the portfolio-shape hurdle or whose directly comparable long-short spread and Sharpe are explicitly reported. State the source universe, subperiod, horizon, turnover, and whether the statistic is an IC, spread, or Sharpe; do not infer equivalence without labeled assumptions. Rank candidates by documented effect size first, then screen thesis fit, novelty, point-in-time data coverage, power, and after-cost criterion-4 feasibility. Only candidates that survive those screens receive a complete `specs/IDEA_SCREEN_TEMPLATE.md`; a failed gate ends the work. Do not inspect outcomes or sealed holdout data while screening.
