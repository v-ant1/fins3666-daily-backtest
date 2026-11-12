# D4 draft — quarterly common-owner graph carrying daily CLV pressure

STATUS: DRAFT - NOT FROZEN

This is L3 BUILDABLE Candidate 1, distinct from D3: its daily pressure proxy is OHLCV CLV and its quarterly 13F graph is the proposed network. No frozen date or hash is included.

## Hypothesis, sign, horizon

Positive pressure among stocks connected by a publicly reported common institutional owner predicts positive short-horizon pressure/returns in the linked Dow stock. The hypothesis is daily pressure spread through a dated ownership graph; CLV remains a location-in-range proxy, not signed order flow.

## Signal, network, assets and dates

Use the point-in-time Dow roster and daily OHLCV. For each stock-day, CLV=(2C−H−L)/(H−L); set CLV=0 if H=L. Daily pressure is the mean raw CLV over sessions t−4:t. Use SEC 13F positions only after the actual filing acceptance/public timestamp. Structured SEC 13F begins 2013 Q1; earlier filings exist in EDGAR archives but need manual parsing and identifier mapping. Convert each reporting manager's quarter-end holding value to a Dow stock weight within the manager's reported Dow positions, using point-in-time CUSIP-to-security mapping. For each stock pair, A_i,j,q = cosine similarity of these manager-weight vectors; set diagonal to zero and row-normalize to W. Refresh only upon newly public filing; allow a graph to persist up to 135 calendar days after the last usable filing, then mark unavailable. The network pressure is NCP_i,t = Σj W_i,j,t × mean(CLV_j,t−4:t), where W was public before t.

Development daily bars/rosters are confirmed from 2020-11-27–2026-10-30; no complete parsed 13F edge file is confirmed. Holdout filings are public, but structured data starts in 2013 Q1 and the 2010–12 graph requires parsing; pre-June 2020 Dow return/signal calculations are prohibited. L4 has 37/40 security windows; KFT, DWDP, WBA unresolved and UTX→RTX lineage proxy.

## Single primary mechanism test and placebo set

Primary: date-wise Spearman rank correlation of NCP_i,t with next-open-to-close return through t+5, adjusted close[t+5]/adjusted open[t+1]−1. Remove same-date EW30 return from each asset (ranking is invariant to common subtraction); NW Bartlett lag 4 across dates. Predicted mean IC positive; require NW t≥2. This is a daily predictive test, not causal evidence by itself.

Placebos: 500 degree-preserving rewires of W with edge weights reassigned (seed 20261110); random links preserving edge count/weight distribution; and graph sequence shifted 20 sessions relative to signal. Require true mean IC to exceed the 95th percentile of each placebo distribution; each shifted/random IC must have |NW t|<2.

## Variants and selection rule

1. Primary 13F common-owner cosine graph and five-day mean peer CLV.
2. Same reporting-manager positions, overlap edge weight Σf min(v_f,i,v_f,j) after manager-level unit-sum scaling.
3. Direct peer-pressure score with no graph as a benchmark (mean peer CLV among same two-digit SIC Dow names).

Variant 1 alone advances. Variants 2–3 cannot replace it because of higher returns. No graph thresholds or pressure windows may be altered.

## Portfolio, costs and inference

After the mechanism gate: long the five highest NCP names, equal-weight, next-open execution every fifth session, 83.3% active share versus EW30 at formation; cap total traded notional/NAV at 50.0%, charge 5 bp per dollar traded. Apply the fixed 0.005481 L1-helper cost-only reference IC from the top-five inputs in D1, with its stated limitation: it is a scale check, not evidence this CLV/13F score earns it. Require gross active edge ≥4× realized costs, positive net excess and higher net Sharpe than EW30. Inference: one-sided 10-session circular block bootstrap, 5,000 draws, seed 20261110; Holm across fixed 24 endpoints; DSR trial_count=30; portfolio p<0.05 adjusted.

## Holdout procedure and pass rule

Coordinator-only one-shot frozen run. Full required interval 2010-01-01–2020-10-31 is blocked by the pre-2020-06 outcome prohibition; no worker or coordinator computation can use the prohibited segment under the current rule. An authorized 2020-06-01–2020-10-30 slice is only a truncated diagnostic. Full authorized pass: positive five-session sign, net excess and Sharpe above EW30, one-sided 10-session bootstrap p<0.10; report including/excluding DWDP window. No imputation for missing names. Unresolved network/price coverage means no pass.

