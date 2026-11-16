# R6 Idea Screen: BJZZ retail marketable-order imbalance in Dow names

**Status:** SCREEN ONLY — no signal outcomes, no return calculations, and no variant is authorized by this document.

## Identity and immutable-path preflight

- **Proposed short name:** AE-BJZZ-Dow. Sub-penny-priced off-exchange trades classified as retail buys or sells provide a daily retail marketable-order imbalance; persistent net retail buying is hypothesized to predict positive next-week returns.
- **Exact new output path:** `r6_ideas/AE_retail_bjzz.md`.
- **Path check:** the target did not exist before this screen. No other path is created or modified.
- **Name check:** `AE_retail_bjzz.md` is new; AE was assigned by decision 181. The BJZZ concept has appeared in prior screening discussion, so novelty is assessed explicitly below rather than presented as a wholly new mechanism.
- **Development range:** 2020-11-27 through 2026-10-30; earliest permissible worker date 2020-11-27. The only SIP probe used 2024-06-03.
- **Path/data check:** the probe requested only SIP trades for the 30 Dow constituents on 2024-06-03 UTC. No sealed-holdout or earlier data were requested or opened.

## 1. Overlap with prior work

Decision 181 assigned a screen of the BJZZ sub-penny rule using Alpaca SIP trades. The closest earlier work is D2 and the retail-flow discussion in `M_SURVEY.md`: D2 used FINRA OTC/non-ATS aggregate volume, which has no buyer-versus-seller side, and was rejected as an inadequate signed retail-pressure proxy. This screen would classify off-exchange prints individually by price-improvement location and compute signed buy-minus-sell share volume. It is therefore a more specific operational measure, not merely a renamed D2 variable.

The conceptual mechanism is still the same broad retail order-imbalance family previously discussed, and the BJZZ classifier itself is not novel. The only defensible novelty is that the staged SIP endpoint appears to make the classifier pullable for Dow names. This is a meaningful data-feasibility change but not a new economic hypothesis; any future work would need to disclose this overlap.

**Verdict: PASS WITH MATERIAL OVERLAP.** It is distinct in observable and source from D2, consistent with the explicit AE assignment, but should not be described as a novel pressure mechanism.

## 2. Exact pressure measure and dated data source

For each Dow common stock `i` and trading day `d`, use Alpaca historical SIP trades. Retain eligible off-exchange/TRF prints (the BJZZ paper identifies the TAQ TRF exchange code D), after excluding canceled/corrected records and non-eligible conditions according to the paper and source documentation. For each price `P`, set `Z = 100 × mod(P, 0.01)`, in cents. Classify `0 < Z < 0.4` as a retail sell and `0.6 < Z < 1.0` as a retail buy; exclude exact-cent prints and the middle range. Daily imbalance is

\[
I_{i,d}=\frac{V^{buy}_{i,d}-V^{sell}_{i,d}}{V^{buy}_{i,d}+V^{sell}_{i,d}},
\]

where `V` is share volume. A fixed five-session pressure score would be the equal-weight mean of the five daily imbalances ending at formation close `t`, requiring a positive denominator on all five days. Rank the score cross-sectionally; execute no earlier than the next session's open and predict the subsequent five-session return. The specific five-day aggregation is a proposed implementation choice, not a claim that it is identical to every BJZZ specification.

The source is [Alpaca historical stock trades](https://docs.alpaca.markets/us/reference/stocktradesingle-1), on its SIP feed; Alpaca describes feed access and limitations in its [Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq) and [market-data plan documentation](https://docs.alpaca.markets/us/v1.1/docs/about-market-data-api). Historical SIP is available through the authenticated API, but a successful historical request does not itself establish free-plan entitlements, downstream redistribution rights, or indefinite storage rights. Conditions, trade corrections, and exchange mapping must be point-in-time handled and validated before a preregistration.

The feasibility probe was strictly date-filtered to `2024-06-03T00:00:00Z` through `2024-06-04T00:00:00Z` for the 30 Dow names. It counted response records and decompressed response bytes only; it did not inspect prices, classify trades, construct imbalances, or calculate outcomes. No full-period eligible-day or signal coverage check was performed.

**Verdict: PASS for a precisely specified candidate measure and a one-day access probe; no outcomes used.** The license/entitlement and condition-filter issues remain unresolved.

## 3. Point-in-time coverage and independent breadth

The one-day probe returned trade records for all 30 Dow symbols, comprising **4,106,059 records**, **411 pages**, and **416,760,062 bytes** of decompressed JSON response bodies in **188.369 seconds**. These are input-volume counts, not valid-print counts: records were not classified and do not prove that every ticker-day has buy and sell volume under the prescribed filter.

The development panel contains about 1,488 market sessions, giving at most that many daily observations per name and about 297 non-overlapping weekly formations after the five-session warm-up. This is a date-count upper bound, not a measured signal-coverage count. Usable dates, eligible-print names, nonmissing signals after the rule, and point-in-time SIC2 independent clusters were **not measured**, since the task authorized only one feasibility sample and no full-period signal construction. The single day contains 30 names but only one common-date event; it cannot establish independent breadth. Corrections, cancellations, conditions, symbol history, roster entry/exit, and irregular trade availability may reduce coverage further.

**Verdict: FAIL — insufficient full-window input-only coverage and cluster counts to clear the template's coverage gate.** The sample establishes technical access and scale only.

## 4. Effective breadth and power at a sourced plausible effect

Boehmer, Jones, Zhang and Zhang's *Tracking Retail Investor Activity* uses US TAQ off-exchange/TRF trades from 2010–2015, roughly 3,000 firms per day. Their weekly Fama–MacBeth tests use Newey–West lag 5. They report a broad-sample interquartile retail-imbalance return spread of **10.89 basis points per week** (Table III; t=15.60), but the effect is much smaller for the largest market-cap tercile: **2.6 bp per week** (Table IV; coefficient 0.0003, t=3.68). These are portfolio spreads, not rank ICs, and neither is evidence for today's Dow names.

For a rough scale translation only, dividing the large-cap spread (0.00026) by `1.349 × 4.25%` weekly cross-sectional dispersion gives an approximate rank-IC proxy of **0.0045**; the broad-sample spread gives about **0.019**. The 4.25% dispersion is a planning assumption from `report_drafts/CRITERION4_BOUND_BY_SHAPE.md`, not a measured Dow statistic. This conversion is illustrative and not an estimator reported by BJZZ.

The six-year Dow design has at most 297 non-overlapping weekly dates and 30 names per date. Date-level dependence and shared market/event shocks make the nominal 8,910 name-date observations far from independent. A synthetic call to `r4_harness/power_sim.py` with 297 weekly dates, horizon 5, NW lag 4, autocorrelation 0.2, 5,000 simulations and seed 20261111 gives power **6.64%** at planted IC 0.0045 and **33.36%** at planted IC 0.019; the simulated 80%-power minimum detectable IC is **0.0359**. This power calculation is planning-only and uses no observed project signals or returns.

Recent evidence makes transfer less credible: Ardia, Aymard and Cenesizoglu, “Revisiting Boehmer et al. (2021): recent period, alternative method, different conclusions,” finds the original retail-order-imbalance measure loses weekly-return predictive power in large caps during 2016–2021. Barber, Huang, Jorion, Odean and Schwarz validate the sub-penny classifier against 85,000 actual retail trades from six brokerage accounts in 2021–2022 and find it identifies only 35% of retail trades and mis-signs 28% of those identified; stock-level measures are often uninformative.

**Verdict: FAIL — the large-cap effect is too small for useful power, and the later-period evidence is adverse.**

## 5. Criterion-4 portfolio feasibility first

A plausible long-only design would rank the 30 Dow names weekly and use a rank-weighted upper-half portfolio (active share 55%), benchmarked against EW30, with 0.05% cost per side. This shape is the lowest weekly long-only hurdle documented in `report_drafts/CRITERION4_BOUND_BY_SHAPE.md`: rank IC **0.074** for 80% power at signal autocorrelation 0.2, 116% average total-notional turnover, and annual costs equal to 24.1% of gross active edge. The alternate ≤50%-turnover criterion does not hold at the audit's 116% estimate; the design relies on the cost/gross-edge branch.

Both literature-based proxies fall below that hurdle: 0.019 broad-market (3.9 times smaller) and 0.0045 large-cap (about 16 times smaller). If gross edge scaled linearly with IC while turnover stayed at the audited level, the corresponding cost/gross-edge ratios would be roughly 94% and 396%, respectively; these are arithmetic feasibility illustrations, not strategy results. At 0.05% per side, this does not credibly support positive net excess return, Sharpe above EW30, or one-sided block-bootstrap significance after the growing R6 Holm family. No expected Dow Sharpe or bootstrap p-value is reported because the cited papers do not provide a matching modern Dow portfolio estimate and this screen has no return outcomes. The cumulative trial count and Holm adjustment would make the hurdle harder, not easier.

The later-period large-cap replication reports the original BJZZ measure no longer predicts weekly returns and its long-short portfolio is no longer profitable. Together with the classifier's measured false-sign rate, this rules out treating the old full-sample spread as a plausible current Dow effect.

**Verdict: FAIL — criterion-4 infeasible at the documented large-cap effect; even the broad-sample proxy is below the hurdle.** Do not commission a portfolio run under this screen.

## 6. Holdout availability and protocol

No holdout path, data, or holdout-specific input is needed or was accessed. Any eventual holdout evaluation must be coordinator-controlled under **goal criterion 5**; Alpaca history begins in 2016, so any applicable 2010–2015 gap must be disclosed rather than filled by worker retrieval. No availability-only holdout check was needed for this failed screen.

**Verdict: PASS — sealed holdout untouched; protocol deferred to criterion 5.**

## Final screen decision

**Overall: STOP — FAIL.** The single-day pull shows the historical SIP trade endpoint is technically usable but data volume is substantial; full-window filtered coverage is unverified, statistical power at the large-cap documented effect is only 6.64%, the 2016–2021 large-cap replication is adverse, and expected effect is far below criterion 4. The implementation also overlaps the previously discussed retail-imbalance family and does not introduce a new mechanism.

Evidence that could change the screen would be independent post-2020 large-cap evidence for this exact classifier with a rank-equivalent effect near or above the 0.074 weekly hurdle, sufficiently broad valid-print coverage, and confirmed data rights. Such evidence must be established without looking at this project's signal outcomes.

### References

- Boehmer, E., Jones, C. M., Zhang, X., & Zhang, X. (2021). “Tracking Retail Investor Activity.” *The Journal of Finance*, 76(5), 2249–2305. [https://doi.org/10.1111/jofi.13033](https://doi.org/10.1111/jofi.13033).
- Ardia, D., Aymard, S., & Cenesizoglu, T. (2026). “Revisiting Boehmer et al. (2021): recent period, alternative method, different conclusions.” *Financial Markets and Portfolio Management*, 40(2), 273–306. [https://doi.org/10.1007/s11408-025-00487-4](https://doi.org/10.1007/s11408-025-00487-4).
- Barber, B. M., Huang, X., Jorion, P., Odean, T., & Schwarz, C. (2024). “A (Sub)penny for Your Thoughts: Tracking Retail Investor Activity in TAQ.” *The Journal of Finance*. [https://doi.org/10.1111/jofi.13334](https://doi.org/10.1111/jofi.13334).
- Alpaca. [Historical stock trades API](https://docs.alpaca.markets/us/reference/stocktradesingle-1); [Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq); [market-data plan documentation](https://docs.alpaca.markets/us/v1.1/docs/about-market-data-api).

**Reviewer/date:** dispatched screen / 2026-11-11.
