# Cycle 3 fallback direction: ETF flow pressure through basket links

**Status: conditional research candidate, not a frozen pre-registration. No outcome data or holdout data were accessed for this proposal.** This is a deliberately low-confidence final candidate if D7 fails; do not run it unless the input-only gate below passes before any returns are examined.

## Direction

Measure actual ETF share creations and redemptions, then test whether the signed demand shock transmitted through the ETFs' disclosed stock baskets predicts short-horizon returns among Dow constituents. This changes the pressure measure from stock candles or earnings reactions to external fund-demand flow, and changes the relation from common owners, industries, or supply-chain links to ETF baskets.

The mechanism is plausible but narrow. Ben-David, Franzoni, and Moussawi (2018) find ETF ownership can transmit ETF-market liquidity shocks to underlying stocks through arbitrage, increasing volatility and negative stock-price autocorrelation. Da and Shive (2017) document ETF activity-related stock comovement and evidence of subsequent reversals. These findings support transmission of demand shocks, while also warning that any price pressure may reverse rather than persist. They do not establish a profitable Dow prediction from public ETF data. [Ben-David, Franzoni & Moussawi (2018), *Do ETFs Increase Volatility?*, Journal of Finance, DOI 10.1111/jofi.12727](https://doi.org/10.1111/jofi.12727); [Da & Shive (2017), *Exchange Traded Funds and Asset Return Correlations*, European Financial Management, DOI 10.1111/eufm.12137](https://doi.org/10.1111/eufm.12137).

## Fixed test concept

- **Universe:** the Dow 30 point-in-time roster and exactly six U.S. equity ETFs: SPY, IVV, VOO, QQQ, DIA, and IWM. Use no replacements.
- **ETF flow:** for ETF `e` on session `t`, compute `F[e,t] = (Shares[e,t] - Shares[e,t-1]) * NAV[e,t-1] / AUM[e,t-1]`, with share splits adjusted. Use only share counts and NAV values publicly timestamped by the close of `t`. Flow is usable on the next trading session. This is a proxy for net creations/redemptions; it is not observed AP order flow.
- **Basket links:** `B[e,i,t]` is ETF `e`'s disclosed fraction of assets in Dow stock `i`, from the latest basket record public before session `t`. A filing or basket file becomes usable on the next trading session after its publication. Build the weighted stock graph `A[i,j,t] = sum_e B[e,i,t] * B[e,j,t]`, set the diagonal to zero, then row-normalize nonzero rows to form `W[i,j,t]`. No return correlations or SIC substitutions.
- **Direct and propagated pressure:** direct stock demand is `D[i,t] = sum_e F[e,t] * B[e,i,t]`. The single primary network score is the cross-sectionally demeaned `N[i,t] = sum_(j != i) W[i,j,t] * D[j,t]`, standardized across names each date. Prediction: **positive** rank IC between `N[i,t]` and stock `i`'s EW30-excess return from next-session open through the fifth-session close. This one five-session horizon tests whether pressure reaches connected constituents after its public observation; do not select another horizon after seeing data.
- **Placebos:** (1) independently circular-shift each ETF's basket ticker labels by a fixed seven-position circular offset within the dated Dow roster, preserving each ETF's weight distribution; (2) shift each ETF flow series by 20 trading sessions while leaving baskets unchanged. The actual network score must exceed the placebo distribution in the predicted direction.
- **Portfolio, only after a mechanism pass:** weekly long the five highest network scores and short the five lowest, equal-weighted, market-neutral; 0.05% cost per traded side. This is long-short, but turnover must still be reported. The 0.0183 value is the project's calibrated top-five weekly mean-IC cost hurdle, not a universal ETF-flow threshold; use it as the conservative screening hurdle and do not reinterpret it after results.

## Input-only feasibility gate — fixed before any input inspection

Declare the design **INFEASIBLE** without opening or calculating any stock return, IC, or performance if any condition fails:

1. All six named funds must have a verifiable, timestamped free daily history of split-adjusted shares outstanding, NAV, and AUM covering at least **1,000 common trading sessions** within 2020-11-27 through 2026-10-30.
2. Each ETF must have free timestamped holdings/basket files usable point-in-time on at least **80%** of those sessions, with at least **25 of the 30 contemporaneous Dow names** represented on each counted date.
3. The resulting off-diagonal stock graph must have a median daily density between **5% and 80%**, inclusive, and at least **20 names** must have three or more nonzero incoming neighbors on at least **80%** of counted dates. Density is checked from links only; do not inspect outcomes or relax the bounds.
4. ETF share-count changes, split adjustments, basket publication times, and AUM fields must reconcile internally from the published source records. If historical fund data is retrievable only from a paid vendor or with retrospective/unverifiable timestamps, the gate fails.

These gates are intentionally demanding. The current evidence suggests popular broad equity ETF baskets could make the 30-stock projection nearly complete, reducing the network score to a market-like average. The gate prevents that structure from being called network transmission.

## Expected edge, turnover, and chance of success

Weekly re-ranking and a ten-name long-short book are likely to trade more than **50% of one-way NAV** at some rebalances; the input gate cannot establish turnover. Given the short horizon, small cross-section, likely dense basket graph, delayed or incomplete free flow history, and reversal evidence, I judge the chance of clearing both the mechanism test and the 0.0183 screening hurdle at **about 5%**. This is a subjective planning estimate, not a computed probability. The approach should not advance if the input gate fails, and a positive first-week pressure response would still need to survive the preregistered placebo and net-cost tests.

## Main failure modes and distinction

Public shares outstanding may be unavailable daily or may be published too late to support a short-horizon test; changes in ETF shares do not identify the direction or timing of every constituent trade. Broad index funds may link almost every Dow name, leaving no useful peer contrast. Price pressure may reverse quickly, as the cited evidence suggests. A significant association could reflect common market news or ETF arbitrage rather than persistent buying pressure.

This differs from D4's daily CLV pressure through common 13F owners, D5's same-industry CLV leader/follower, D6's equity-bond ETF return cross-lag, and D7's customer-earnings shock through customer-supplier links. It instead asks whether **public ETF primary-market creations/redemptions create signed underlying-basket demand that spreads across a holdings-overlap graph**. It does not reuse country ETFs or sealed holdout tickers.



