# Dossier 2 — ETF flow shocks through constituent holdings

## Pitch and thesis fit

Measure an ETF’s demand-driven or arbitrage-driven primary-market creation/redemption, then trace the signed pressure to its held Dow stocks and to other stocks linked through overlapping ETF baskets. The direction preserves Advik’s network-spread thesis using a dated holdings-weight network instead of symmetric return correlations. Its core prediction is temporary non-informational demand: a creation pushes held stocks in the buy direction on the event, then that pressure partially reverses over the following few sessions. It explicitly separates the unexpected, information-bearing component because that can continue rather than reverse.

## L1 root causes this addresses

The current pressure blend has five-day IC +0.0037 (t=0.38) and heat IC −0.0017 (t=−0.14); heat is a smoothed co-movement signal, not source-to-recipient transmission. D2 replaces that graph with observed ETF holdings and dates the initiating flow event, directly addressing L1 root causes 1 (pressure blend mixes predictive signs) and 2 (co-movement graph does not measure propagation). The event test before portfolio addresses root cause 3 (weak/unstable effect was not established first). It cannot solve root cause 5 (30-name power) and only manages, not proves a solution to, root cause 4 (turnover/costs). L1’s top-five heat portfolio turned 161.5% of NAV weekly and incurred 8.07 bp per rebalance; EW30 turned 2.4% and cost 0.12 bp. L1’s postmortem cost-calibration IC break-even is ~0.0127 (but `cost_analysis.csv` says 0.00605; reconcile before treating either as a decision threshold).

## Mechanism and evidence

Ben-David, Franzoni and Moussawi find ETF ownership linked to greater stock volatility and negative return autocorrelation; their paper gives a plausible arbitrage path from ETF liquidity shocks to constituents. Xu, Yin and Zhao show ETF flows mix informative and non-informative demand: flow signs cannot all be assumed to reverse, and secondary-market imbalance and NAV mispricing help decompose the components. Antón and Polk provide complementary evidence that shared active-fund owners link stocks through demand-induced comovement/reversal.

- Ben-David, Franzoni & Moussawi (2018), “Do ETFs Increase Volatility?,” *Journal of Finance*: [DOI](https://doi.org/10.1111/jofi.12727). **Verified L2 card 6 and L3 card 8.**
- Xu, Yin & Zhao (2022), “Are the Flows of Exchange-Traded Funds Informative?,” *Financial Management*: [DOI](https://doi.org/10.1111/fima.12396). **Verified L3 card 9 and citation audit.** The card/audit show that informative flow need not reverse, so the dossier’s demand-flow sign must be frozen in advance.
- Antón & Polk (2014), “Connected Stocks,” *Journal of Finance*: [DOI](https://doi.org/10.1111/jofi.12149). **Verified L3 card 3.**
- Modern index-pressure decay caution: Greenwood & Sammon (2022/2025), “The Disappearing Index Effect”: [NBER working paper](https://www.nber.org/papers/w30748). Additions/deletions were statistically indistinguishable from zero over 2010–20 in the audited L2 card; this is adjacent evidence, not a direct ETF flow replication.

## Exact signal and network

Use U.S. equity ETFs with holdings in the Dow only; no cross-asset ETF is included. For ETF `e` and date `t`, define fractional creation/redemption flow `F_e,t=(shares_e,t−shares_e,t−1)/shares_e,t−1`, adjusted for splits/distributions. Define secondary-market order imbalance `IB_e,t=(buyer-initiated shares−seller-initiated shares)/shares_e,t−1`, using signed ETF trades/quotes, and NAV mispricing `M_e,t=(ETF close−NAV)/NAV`. Separate demand, arbitrage and unexpected flow by fitting `F_e,t=α_e+βI_e IB_e,t+βM_e M_e,t+u_e,t` using only the prior 252 sessions (minimum 126); calculate `Fdem=βI×IB`, `Farb=βM×M`, and `Funexp=u`. Scale fractional flow components to dollars by lagged AUM. This rolling fit avoids full-sample decomposition leakage.

Let `w_e,i,t−1` be the last constituent weight publicly available before t. The proposed primary constituent pressure is `Pdem_i,t = Σ_e [w_e,i,t−1 × AUM_e,t−1 × Fdem_e,t / ADV20$_i,t−1]`, where `ADV20$` is the prior 20-session mean daily dollar volume. The stock-to-stock network is `A_i,j,t = Σ_e [AUM_e,t−1 × w_e,i,t−1 × w_e,j,t−1]` for i≠j, row-normalized to `W`; network-exposed pressure is `NPdem_i,t = Σ_j W_i,j,t−1 × Pdem_j,t`. The event source is a demand-driven ETF flow; the holdings edge is not learned from same-day returns. Preserve the flow’s public release timestamp to prevent look-ahead. L3 red-team warns that overlapping ETFs may make this graph dense and non-directional, and shocks may be market-wide rather than directed transmission.

L4 confirmed a successful current [SSGA holdings](https://www.ssga.com/us/en/intermediary/fund-finder) workbook pull, but that only proves current holdings access. [SEC N-PORT](https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets) structured holdings extend October 2019–September 2026 at monthly frequency with filing lags; that covers most development dates but not October 2026, and only the final year of the 2010–20 holdout. SPY and DIA have coverage caveats. A robust **daily historical holdings archive is not assured**. Daily ETF NAV/shares may allow flow reconstruction for some funds, but it is labor-intensive and not a universal feed; commercial FactSet/Morningstar flow estimates need access confirmation. L3 red-team also warns that overlapping ETF baskets can produce dense, ambiguous edges and that flow shocks may be market-wide rather than directed transmission.

**Development availability:** Dow daily prices exist. Current issuer holdings and a development-date SEC filing/sample exist, but the historical daily network, standardized daily flow series, ETF signed-trade imbalance and historical NAV mispricing panel were not established. Monthly N-PORT plus its publication dates is a partial holdings route only; it does not supply the daily flow decomposition needed for the primary test.

**Holdout replicability:** ETF holdings/N-PORT do not cover the 2010–2020 holdout at the required daily frequency; N-PORT offers at best the final holdout year, while archived vendor/issuer holdings and flows for 2010–19 are unverified. The 2010 Dow price panel itself has three unresolved windows (KFT, DWDP, WBA) and the UTX→RTX proxy. No holdout signal should be computed until the user chooses a coverage route and the data is audited.

## Prediction, tests and portfolio

Predicted sign: positive demand-driven creation yields positive constituent pressure in the first full trading session after the flow is publicly available and a negative residual-return response over event-days +3 to +5 as temporary pressure unwinds; redemption has the opposite signs. Define event-day 0 as that first full session, never the ETF flow date if the shares/NAV update arrived after the stock close. Test days +1 and +3 to +5 separately. The unexpected component is a prespecified information-continuation counter-hypothesis; no universal reversal is assumed for it.

First run an event study of residual stock returns/pressure by event time (0, +1, +3, +5 sessions), weighting treated names by `w_e,i`; event day 0 is the first full session after the flow is public. Separately test whether `NPdem_i,t` predicts 1/3/5-day returns after controlling for own pressure, same-day return, market and sector returns. Use event/date-clustered inference plus Newey–West on date-level rank-IC series, lag h−1; correct the family with Holm. Require the expected event-day-0 sign and post-event reversal, NW t≥2 for the registered response, and no effect for placebos before a portfolio.

**Placebos:** permute ETF constituent weights across Dow names within sector/size bins while preserving each ETF’s flow series and exposure distribution; use future flows as timing placebos; compare with sector- and market-matched controls. Similar placebo effects falsify the network channel.

**Portfolio after mechanism gate:** fade the five-session cumulative `NPdem` observed as of the flow publication time: long the most redemption-pressured constituents and short the most creation-pressured constituents, equal-weight, dollar-neutral, event-triggered from the next available open and with no more than weekly formation. This is a long-short strategy; a 5-name long-only diagnostic would also exceed 50% active share vs EW30. Expected turnover is unknown before implementation; impose ≤50% total traded notional per rebalance. At the L1 161.5% turnover benchmark, its reported incremental cost vs EW30 is 7.95 bp/week; this is not transferable as ETF alpha. At the proposed cap, 5 bp/side costs ≤2.5 bp per rebalance before benchmark cost. Do not advance if gross edge does not cover realized costs and turnover.

## Variants and selection rule

1. Primary: demand-driven component `Fdem` weighted by last public holdings.
2. Arbitrage-driven component `Farb` weighted by the same holdings; keep it separate from the demand component.
3. Unexpected residual `Funexp` as an information-continuation counter-hypothesis: predict a same-sign next-session response, not reversal, and do not select it as a substitute by portfolio performance.

Variant 1 is the primary test. Variants 2–3 are mechanism comparisons and cannot replace a failed primary based on returns. If trade-sign and flow-decomposition inputs fail the pre-outcome coverage gate, mark daily D2 infeasible; no weaker daily proxy is promoted after outcomes. For each preregistered component, require its stated sign, NW t≥2 after Holm, and null shuffled-link/future-flow placebos.

## Strongest objection and falsifier

The strongest objection is that ETF ownership evidence is not itself a profitable daily flow strategy: the main 2000–15 paper establishes volatility/negative autocorrelation, while Liao et al. show some flow components are informative and need not reverse. L4 has only current holdings proof and monthly lagged N-PORT for historical weights; full 2020–26 daily network plus full 2010–20 holdout replication is unverified. Falsify D2 if holdings-weighted flows do not produce the predicted constituent event response, if informative/demand classification changes the sign, if shuffled links or future flows predict similarly, or if 5 bp/side costs erase the portfolio edge under the turnover limit.

## Feasibility, effort and risk

Scale: 1=low, 5=high. **Feasibility 1/5** (current holdings are accessible, but daily signed ETF trade flow, NAV, historical weights and holdout sources are not established); **effort 5/5** (flow decomposition, filing/release timing, holdings normalization and corporate actions); **risk 5/5** (dense ambiguous links, informative-flow mixture, sparse Dow cross-section, and cost uncertainty). Conditional priority: best network-mechanism dossier only if full historical inputs can be secured before preregistration.
