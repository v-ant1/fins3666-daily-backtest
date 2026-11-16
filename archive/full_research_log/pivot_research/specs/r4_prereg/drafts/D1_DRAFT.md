# D1 draft — retail marketable-flow continuation

STATUS: DRAFT - NOT FROZEN

No FROZEN date or hash is included. This draft is contingent on data access and may not be executed until selected and frozen by the coordinator.

## Hypothesis, sign, horizon

Among point-in-time Dow constituents, greater signed marketable retail buying pressure predicts higher stock returns over the next five trading sessions. This is a direct persistence test; it makes no network-spread claim. If the measure cannot be constructed faithfully from documented transaction and quote fields, D1 is infeasible and daily OHLCV is not a substitute.

## Signal, assets and dates

Universe: point-in-time Dow 30 constituents on each date. Development prices exist for 2020-11-27 through 2026-10-30; D1 additionally needs TAQ trades/quotes and classifier fields for that full interval. UNSW lists premium TAQ with U.S. history from 1993, and WRDS specifies daily product from 2003-09-10 to present, which spans both requested periods; team access and retail-classifier field coverage remain unverified. No project intraday panel is confirmed. Daily price/roster data are development-confirmed.

For stock i and session t, classify marketable retail trades using the frozen published venue, trade-size and price-improvement classification procedure. Let R_i,t = (retail buyer-initiated dollar volume − retail seller-initiated dollar volume) / total marketable retail dollar volume. Define R5_i,t as total signed retail dollars across sessions t−4 through t divided by total marketable retail dollars across those sessions. Exclude a day with no classified retail dollar volume; do not impute. Signal timestamp is session close after all inputs are public; execution is next session open.

There is no network: the mechanism is direct pressure persistence. Inputs: TAQ trades, quotes, venue and classifier fields; point-in-time Dow membership and identifiers; daily adjusted open/close for returns and EW30 benchmark. Development: TAQ availability is not verified for this team. Holdout: full 2010–2020 TAQ may exist at vendor level, but no project access or complete Dow identifier panel is confirmed. Current L4 reports KFT, DWDP and WBA unresolved and UTX proxied by RTX.

## Single primary mechanism test and placebo set

Primary: each date's Spearman rank correlation between R5_i,t and next-open-to-close return through t+5, defined as adjusted close[t+5]/adjusted open[t+1]−1. Test the date series mean against zero with Newey–West Bartlett lag 4. Require positive mean IC and t≥2.

Placebos: 500 within-stock-day permutations of retail buy/sell labels preserving each day's classified trade count and dollar volume (seed 20261110); and a timing placebo shifting the retail signal five sessions forward. Require the real primary statistic to exceed the 95th percentile of the one-sided label-shuffle distribution; the timing placebo must have |NW t|<2. Variant 3 is not a replacement if the primary fails.

## Variants and selection rule

1. Primary: dollar-volume imbalance R5 using the specified retail classifier.
2. Sensitivity: share-volume imbalance using the same classifier and dates.
3. Sensitivity: quote-midpoint signing, only if TAQ quote timestamps permit the identical day/session mapping.

Run no additional windows or classifier thresholds. Variant 1 is the only basis for advancing. Variants 2–3 are reported as sensitivity results, never selected by return performance. If required fields are unavailable, stop D1 before joining future returns.

## Portfolio, costs and inference

After the mechanism gate only: equal-weight long the top five Dow names ranked by R5; rebalance every fifth session starting on the first eligible development fill date; use next-open fills and hold until the next scheduled fill. This has 83.3% active share versus EW30 at formation. Cap total traded notional (buys plus sells)/pre-trade NAV at 50.0% per rebalance; if the uncapped target exceeds it, scale trades proportionally without changing ranks. Charge 0.0005 per dollar traded on each side through the actual-trade engine.

Cost hurdle: positive net excess return and higher net Sharpe than EW30 are mandatory. The harness L1 rank-IC helper, applied to the L1 5-session dispersion 0.0300751, total-turnover cap 0.50 less EW30 turnover 0.0241638, 5 bp/side cost and top fraction 5/30, gives a cost-only reference IC of 0.005481. This is a frozen scale check, not a forecast or a claim that D1 inherits L1's return dispersion. Require gross active edge ≥4× realized total trading cost so costs consume no more than one quarter of gross edge.

Portfolio inference: one-sided circular block bootstrap of candidate-minus-EW30 daily returns, 5,000 draws, 10-session blocks, seed 20261110. Holm family is fixed at 24 endpoints: three registered mechanism variants and one portfolio endpoint for each of six dossiers. Require Holm-adjusted p<0.05. Report DSR using trial_count=30. All DSR/portfolio calculations occur only after mechanism/placebo gates.

## Holdout procedure and pass rule

Only the coordinator may invoke the harness holdout runner, once, on frozen code/config; no worker reads or computes sealed outcomes. The required project holdout is 2010-01-01–2020-10-31, but the shared data rule prohibits any pre-2020-06 Dow return or signal calculation. Until the coordinator resolves this conflict under the project rules, no full-holdout pass can be claimed. If the coordinator authorizes the permitted post-cutoff slice, run 2020-06-01–2020-10-30 with no pre-June price warm-up, and report it only as a truncated diagnostic, not the required full holdout. Full pass rule, if an authorized full interval is later available: same positive 5-session sign; net excess return >0 and net Sharpe > EW30; one-sided 10-session bootstrap p<0.10; report the mandated result both including and excluding the DWDP membership window. KFT/WBA gaps and UTX lineage must be resolved or reported without imputation; absent coverage means infeasible, not pass.

