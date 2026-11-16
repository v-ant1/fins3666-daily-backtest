# D3 draft — mutual-fund expected flow through common owners

STATUS: DRAFT - NOT FROZEN

No FROZEN date or hash is included. Data availability is partial; do not substitute 13F holdings changes for fund flows.

## Hypothesis, sign, horizon

Stocks with positive expected flow-induced demand from common-owner mutual funds have higher next-month returns while demand is deployed. A network-pressure score from neighboring stocks' expected demand adds predictive information beyond own expected demand. Forced realized outflows are a distinct negative-pressure mechanism and are not blended with expected positive demand.

## Signal, network, assets and dates

For fund f and month m, realized flow rate g_f,m = [TNA_f,m − TNA_f,m−1 × (1+r_f,m)] / TNA_f,m−1, using total return r and month-end net assets. Forecast expected flow ĝ_f,m with one expanding pooled fund regression of prior g on lagged 12-month excess return; require 36 earlier monthly observations and estimate strictly before month m. Expected dollar demand to stock i is EFIT_i,m = Σf[TNA_f,m−1 × ĝ_f,m × h_f,i,m−1]/MktCap_i,m−1. h is the latest disclosed holding weight public at signal time. No future filing is backfilled. Build common-owner edges A_i,j,m = Σf[TNA_f,m−1 × h_f,i,m−1 × h_f,j,m−1], i≠j; row-normalize to W. Primary signal NFP_i,m = Σj W_i,j,m−1 × EFIT_j,m. Rebalance/test only after both flow estimate inputs and holdings are public.

Universe: point-in-time Dow members. Development price range 2020-11-27–2026-10-30. UNSW lists CRSP Survivor-Bias-Free Mutual Funds from 1962, including monthly/daily returns, NAV and monthly TNA; its page also lists Thomson Reuters Mutual Funds holdings and MFLinks. Entitlement to these tables for an undergraduate team and actual extraction coverage are unconfirmed. SEC 13F structured data starts in 2013 Q1 and is a delayed institutional ownership proxy, not monthly mutual-fund TNA/flow. Holdout 2010–20 flow and holdings panel is not verified; KFT, DWDP, WBA and UTX lineage gaps remain.

## Single primary mechanism test and placebo set

Primary: monthly cross-sectional Spearman rank correlation between NFP at the first date all required inputs are public and next month's stock residual return, computed against the point-in-time Dow cross-section. Residual return is adjusted stock return minus same-month Dow equal-weight return. NW Bartlett lag 0 (non-overlapping one-month outcomes). Prediction is positive; require mean IC>0 and NW t≥2. This is the only primary mechanism test; realized-flow/event summaries are not used to select the model.

Placebos: 500 permutations of fund holding weights among Dow names within sector and market-cap tercile (from prior month data), preserving fund-level flows; shift each fund flow date forward one quarter; and permute common-owner network edges preserving degree. Require primary network effect to exceed the one-sided 95th percentile of placebo statistics and future-date placebo |NW t|<2.

## Variants and selection rule

1. Realized flow exposure using g instead of ĝ (descriptive baseline, not selected).
2. Own expected flow EFIT without neighbor network (network increment baseline).
3. Primary NFP from neighbors' EFIT.

Variant 3 is the only thesis test. Require incremental rank prediction beyond own EFIT with the predicted sign and NW t≥2; no choice by portfolio return. If monthly TNA or time-stamped holdings cannot be assembled before outcomes, stop as infeasible.

## Portfolio, costs and inference

After mechanism pass: monthly next-open rebalance, long equal-weight the five highest NFP Dow stocks; active share at formation 83.3% versus EW30. Use only publicly available monthly updates and carry forward the most recent disclosed holdings until replaced. Total traded notional/NAV cap is 50.0%; charge 5 bp per dollar traded using actual share-level transactions. Cost-only IC reference is 0.005481 from the L1 long-only top-five helper inputs (weekly Dow dispersion), explicitly a benchmark-scale reference because D3 is monthly. Require gross active edge ≥4× realized costs, positive net excess return and net Sharpe above EW30. Inference: 5,000 one-sided circular bootstrap draws, 10 monthly-observation blocks, seed 20261110; Holm family fixed at 24 endpoints, DSR trial_count=30; portfolio adjusted p<0.05.

## Holdout procedure and pass rule

The coordinator alone may run one frozen harness holdout. The required interval 2010-01-01–2020-10-31 conflicts with the rule forbidding pre-2020-06 Dow outcome calculations; no full-period holdout can run unless governance resolves this conflict. Do not compute the prohibited segment. If authorized to run only 2020-06-01–2020-10-30, label it truncated, not a required-holdout pass. Full pass if later authorized: same positive next-month sign; net excess return>0 and net Sharpe>EW30; one-sided 10-month block-bootstrap p<0.10; report with and without DWDP membership window. Missing securities or stale holdings are disclosed, never imputed; current data do not clear this holdout.

