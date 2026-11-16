# D2 draft — ETF demand and constituent reversal

STATUS: DRAFT - NOT FROZEN

No FROZEN date or hash is included. Daily inputs and historical holdings are not confirmed, so no test is authorized by this draft.

## Hypothesis, sign, horizon

A non-informational ETF creation shock puts temporary buy pressure on its reported Dow constituents; once the shock is public, higher creation-exposed constituents have positive event-session pressure and negative residual returns over the following five sessions as demand unwinds. Redemptions imply the opposite signs. This is a holdings-network transmission hypothesis; the unexpected information-bearing flow component is not assumed to reverse.

## Signal, network, assets and dates

ETF eligibility is fixed by rule: U.S.-listed equity ETFs launched by 2010-01-01 with at least one Dow constituent in the first point-in-time holdings record; freeze the resulting identifier list before outcome data. For ETF e, daily fractional primary-market flow F_e,t = (shares outstanding[t]−shares outstanding[t−1])/shares outstanding[t−1], adjusted for splits/distributions. Secondary-market imbalance IB_e,t = (buyer-initiated shares−seller-initiated shares)/lagged shares outstanding; premium M_e,t=(close−NAV)/NAV. Estimate F = α + βI IB + βM M + u using only prior 252 sessions, requiring 126 complete observations. Fdem=βI IB is the primary non-information-demand component; all inputs must have been publicly available before the event session.

Let w_e,i,t−1 be the latest constituent weight disclosed before t, and lagged AUM and stock ADV20$ use only prior observations. Constituency pressure P_i,t = Σe(w_e,i,t−1 × AUM_e,t−1 × Fdem_e,t / ADV20$_i,t−1). Directed flow source e connects to constituent i with edge w_e,i,t−1; the stock network has A_i,j,t = Σe(AUM_e,t−1 × w_e,i,t−1 × w_e,j,t−1), i≠j, row-normalized. This is an exposure network, not a return-correlation graph.

Development Dow prices are confirmed for 2020-11-27–2026-10-30. L4 has current issuer holdings proof and monthly N-PORT coverage October 2019–September 2026; daily point-in-time holdings, daily shares/NAV, signed ETF trades and public release timestamps are unverified. The L4 data inventory says SPY/DIA filing coverage needs fund-by-fund checking. Holdout daily flow/holdings back to 2010 are unverified and the Dow has unresolved KFT, DWDP, WBA and UTX lineage gaps. This direction fails the data gate absent complete fields.

## Single primary mechanism test and placebo set

Primary event study: event e,t is a positive Fdem shock above that ETF's trailing 252-session 90th percentile, calculated using past observations only and requiring the 126-session model history. Event date 0 is the first full stock session after flow publication. Treated stock response is cumulative market-adjusted return from event sessions +1 through +5, weighted by w_e,i,t−1; compare with Dow names having zero holdings exposure to e. Estimate mean treated-minus-control response with Newey–West lag 4 on the date-level event-response series, clustering multiple ETF events on the same date. Prediction is negative for the post-event five-session response. Event-session constituent pressure is reported as a sign check, not a second primary test. Require NW t≤−2 and no pre-event response of comparable size.

Placebos: 500 within-date permutations of ETF constituent weights across Dow names within the same two-digit sector, preserving ETF flows and each ETF's holdings count; future flow shifted 5 sessions; and zero-exposure matched controls. Require real event statistic beyond the 95th percentile in the predicted negative tail; shifted-flow placebo |NW t|<2.

## Variants and selection rule

1. Primary: Fdem, the imbalance-predicted component.
2. Mechanism comparison: Farb=βM M, the arbitrage/mispricing component; predicted pressure/reversal signs are reported separately.
3. Counter-hypothesis: Funexp=u, the unexplained component; test same-sign continuation over five sessions.

Variant 1 alone determines advancement. Variants 2–3 cannot substitute for a failed primary. No other ETF filters, event quantiles or rolling windows may be tried.

## Portfolio, costs and inference

After passing the mechanism test: once per fifth session, long equal-weight the five lowest P_i,t names (largest predicted redemption/fade exposures) using the next open, with a top-five concentrated long-only book; active share is 83.3% versus EW30. Cap total traded notional/NAV at 50.0% each fill; charge 5 bp per dollar traded, actual-trade cost engine. The cost-only rank-IC reference is 0.005481 under the fixed L1 helper inputs specified in D1; because D2 is an event-driven flow signal, it is a conservative scale comparison only. Require gross active edge ≥4× total costs, positive net excess return, and net Sharpe above EW30. Inference: 5,000 one-sided circular bootstrap draws, 10-session blocks, seed 20261110; fixed 24-endpoint Holm family and DSR trial_count=30; portfolio Holm-adjusted p<0.05.

## Holdout procedure and pass rule

Coordinator only, one frozen run. The full goal holdout is 2010-01-01–2020-10-31, but pre-2020-06 Dow outcome calculations are prohibited by the shared rule; do not access them. Any authorized 2020-06-01–2020-10-30 post-cutoff run is only a truncated diagnostic and cannot satisfy the full holdout gate. If full-period access is later explicitly reconciled, require same negative +1:+5 response, net portfolio excess >0, net Sharpe > EW30, and Holm-adjusted block-bootstrap p<0.10. Report with and without the DWDP window; no missing-name imputation or network backfilling. Current holdings/flow coverage does not establish 2010–20 replicability, so the current status is holdout-infeasible.

