# Dossier 1 — Signed retail flow persistence

## Pitch and thesis fit

Test whether directly observed marketable retail buying is followed by short-horizon returns in the same direction among Dow members. This keeps Advik’s pressure thesis through persistence rather than a network claim: measure buyer-initiated demand directly, then ask whether it continues after the pressure day. This is a research candidate, not an OHLCV proxy strategy; without trade and quote data, the signal cannot be constructed faithfully.

## L1 root causes this addresses

L1 found the five-day blend had close-to-close IC +0.0037 (Newey–West t=0.38), while signed-volume IC was negative and diluted the positive CLV/intraday components. The heat five-day IC was −0.0017 (t=−0.14), and neighbour pressure was −0.0037 (t=−0.32). D1 removes the mixed, candle-based blend and tests a direct signed-flow signal before any portfolio. It does **not** address the invalid return-correlation network, limited breadth, unstable regimes, or cost problem. L1 reports the top-five portfolio traded 161.5% of NAV per weekly rebalance (vs 2.4% for EW30), cost 8.07 bp vs 0.12 bp, and ended with lower net Sharpe (0.60 vs 0.98).

## Mechanism and evidence

Boehmer et al. identify marketable retail buys using venue, trade size and price improvement; retail net buying predicts next-week returns in their 2010–15 sample, but the largest-cap IQR spread is only 2.6 bp weekly before costs. The audit also records Llorente et al.’s distinction between informed speculative flow that can continue and risk-sharing flow that tends to reverse. This direction tests persistence only; it does not assume every high-volume move continues.

- Boehmer, Jones, Zhang & Zhang (2021), “Tracking Retail Investor Activity,” *Journal of Finance*: [DOI](https://doi.org/10.1111/jofi.13033). **Verified in L2 card 13 and citation audit.**
- Llorente, Michaely, Saar & Wang (2002), “Dynamic Volume-Return Relation of Individual Stocks,” *Review of Financial Studies*: [DOI](https://doi.org/10.1093/rfs/15.4.1005). **Verified in L2 card 2 and citation audit.**
- Adverse evidence: Ardia, Aymard & Cenesizoglu (2024), “Revisiting Boehmer et al. (2021): Recent Period, Alternative Method, Different Conclusions”: [arXiv](https://arxiv.org/abs/2403.17095). L2’s red-team review records no large-cap predictability and no profitable long-short result in 2016–21; it is a working-paper critique, not one of the audited peer-reviewed cards.

## Exact signal and data

For each stock-day, classify marketable retail trades using the paper’s venue/size/price-improvement method. Define daily retail imbalance as `R_i,t = (retail buyer-initiated dollar volume − retail seller-initiated dollar volume) / total marketable retail dollar volume`. Aggregate over the last five sessions as `R5_i,t = sum(net retail dollars over 5 days) / sum(retail dollars over 5 days)`. No signal is created from CLV or `sign(return) × volume`.

There is no network in D1; the hypothesis is direct pressure persistence. Required records are point-in-time trade/quote data, venue and price-improvement fields, CRSP/FactSet daily returns and the contemporaneous Dow roster. L4 found no existing full-sample intraday dataset, no documented source for the old hourly feed, and no free source covering the 2020–26 panel. Yahoo intraday retention is rolling and inadequate; full-history alternatives require a licensed feed or paid product. UNSW TAQ/FactSet entitlement is **unconfirmed**.

**Development availability:** Daily Dow OHLCV exists and L1 used it, but that is insufficient for this signal. No development TAQ availability was established by L4.

**Holdout replicability:** No holdout TAQ source or historical retail classification feed was verified. In addition, Dow price windows are incomplete for KFT, DWDP and WBA, and UTX is represented only by an RTX lineage proxy. D1 is not holdout-ready until both trade data and security history are sourced.

## Prediction and test sequence

Prediction: higher signed retail imbalance predicts positive stock-specific close-to-close returns over 1 and 5 sessions; 20 sessions is a prespecified decay horizon, not an expected continuation claim. First compute date-wise Spearman rank IC for `R5` versus 1/5/20-day future residual returns, controlling for the signal-day return, total volume, market and sector moves. Use Newey–West standard errors with lag `h−1`; report overnight and intraday returns separately. Correct the registered horizon/specification family with Holm. No portfolio is permitted unless the prespecified positive 1- or 5-day mechanism passes the project’s NW t≥2 requirement and the placebo does not.

**Placebos:** Shuffle retail buy/sell labels within stock-day while preserving daily total volume; test future retail imbalance as a timing placebo; compare retail with non-retail signed flow. A placebo with a comparable positive IC falsifies the retail-specific mechanism.

**Portfolio after mechanism gate:** Equal-weight long top five and short bottom five names on the frozen signal, dollar neutral, weekly formation, no leverage tuning. A 5-long/5-short market-neutral portfolio is materially different from EW30; if a long-only comparison is needed, top-five equal-weight has approximately 83% active share versus EW30. Target total traded notional ≤50% of NAV per rebalance; actual expected turnover is unknown until the signal is built. If it exceeds the cap, do not proceed unless costs remain below one quarter of measured gross edge.

L1’s reported incremental cost versus EW30 is 7.95 bp per weekly rebalance at the old strategy’s 161.5% turnover. Its postmortem estimates a weekly blend-IC break-even near 0.0127; this is a rough, strategy-specific calibration, not transferable directly to retail flow. The machine-readable `cost_analysis.csv` instead reports 0.00605, so L1’s break-even figures require reconciliation before use. Use 0.0127 as the conservative warning until reconciled. At the 50% turnover cap, 5 bp/side implies up to 2.5 bp cost per rebalance before comparing with EW30.

## Variants and selection rule

At most three, frozen before any future-return field is joined:

1. Primary: dollar-volume imbalance with the paper’s retail trade classifier.
2. Same classifier, share-volume imbalance, to check scaling sensitivity.
3. Alternate quote-midpoint signing method, only if the necessary quote data are available.

Use variant 1 as primary. Variants 2–3 are robustness checks and cannot replace a failed primary based on which has the best return. Pass only if the primary has the predicted positive 1- or 5-day effect, Newey–West t≥2 after Holm correction, and shuffled-label placebo |t|<2; otherwise stop.

## Strongest objection and falsifier

The strongest objection is already documented: in Boehmer et al., the largest-cap weekly spread is 2.6 bp gross, while the 2024 re-examination reports that retail imbalance no longer predicts large-cap weekly returns in 2016–21 and its long-short strategy is no longer profitable. That evidence is closer to Dow megacaps than the original average cross-section and leaves little cost margin. Falsify D1 if the frozen 1/5-day sign is absent, the alternate trade-signing method reverses it, shuffled signs predict similarly, or gross portfolio edge does not exceed costs under the turnover cap.

## Feasibility, effort and risk

Scale: 1=low, 5=high. **Feasibility 1/5** (critical TAQ source unconfirmed for development and holdout); **effort 4/5** (trade classification, symbol mapping, and high-frequency processing); **risk 5/5** (published large-cap decay, weak breadth, costs). Recommendation: only pursue after a data-entitlement check; do not substitute daily candles.
