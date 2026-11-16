# R11 H1 ideas — one-hour intraday buying pressure

**Scope:** literature and design research for one-hour bars, PIT S&P 500 and Dow 30 large caps. This is paper-only. No price, return, bar, r11/data, or sealed file was opened. The 2016–2026 hourly panel is a planned input, not inspected coverage.

## Decision summary

Hourly bars allow tests of when pressure arrives and how long it lasts. They do not identify buyer-initiated flow: OHLCV-based signed-volume scores remain proxies. Most cited results use half-hour bars, older daily or weekly horizons, a market ETF, or direct order-flow fields; those effect sizes cannot be carried over as expected one-hour S&P/Dow returns.

I recommend four candidates for mechanism preregistration: SIC2 peer lead-lag, low-volume opening-gap fade, direct signed one-hour order-flow persistence, and first-hour-to-last-hour market momentum. None has a matched one-hour stock-level effect estimate that supports a production strategy. The first two use hourly OHLCV plus PIT industry data; signed flow requires trades/quotes; the market-level idea has a direct literature rationale but no per-trade stock estimate.

The nearest published bp anchors are Heston et al.'s 3.11 bp same-slot next-day half-hour spread and Baltussen, Da and Soebhag's 3.49–4.56 bp final-half-hour reversal spread. At a 50% winner-curse haircut these are 1.56 bp and 1.75–2.28 bp. The one-hour adaptations are not the same tests, and the latter is already covered by the closing-hour screens. A fully entered and exited one-hour sleeve turns over 200% of gross exposure per signal day. At 1/2/5 bp one-way costs, a round trip needs 2/4/10 bp gross per dollar deployed, before spread impact or other slippage. Every full-book daily one-hour sleeve exceeds the earlier R6 50% turnover limit on turnover alone.

Odds below are subjective chances that the exact candidate's mean edge remains above the stated friction after halving any nearby literature effect. They are not probabilities of clearing all R6 inference, Sharpe, active-share, turnover, or holdout gates.

## Common design and cost convention

- Times are U.S. Eastern; intervals are regular-session bars: 09:30–10:30, 10:30–11:30, …, 15:00–16:00.
- A signal is available at the preceding bar close. Enter at the next hourly bar open; exit at that bar's close. The signal cannot use its holding bar.
- Each candidate enters and exits at most once per name per day. A 100% gross book entered then closed has 200% gross turnover per signal day. Basket replacement can add turnover.
- Cost break-even is per dollar of gross exposure for one completed round trip: 2 × one-way cost, or 2/4/10 bp at 1/2/5 bp one-way. It excludes impact and extra rebalancing.
- “Hourly OHLCV only” means bars plus PIT membership/security mapping. PIT SIC2, index weights or ETF primary-market flows are extra inputs where stated. Hourly OHLCV cannot establish aggressor side.

## Ranked candidates

### 1. SIC2 peer lead-lag into the next hour — pressure spreads

**Mechanism.** Common industry information may arrive first in more informative firms and diffuse later to related firms. Hou finds the stock lead-lag effect is predominantly intra-industry and consistent with slow diffusion of negative information; evidence is daily/weekly and stronger in small, neglected industries ([Hou, 2007](https://doi.org/10.1093/revfin/hhm003)).

**Exact rule.** At 10:30 compute each stock's leave-one-out PIT-SIC2 equal-weight peer return for 09:30–10:30. Rank stocks by that peer return. Long the top quintile and short the bottom quintile for 10:30–11:30, with frozen SIC2 and security IDs.

**Literature effect.** No compatible one-hour bp/trade estimate; matched planning estimate is 0 bp. Weekly/monthly evidence does not support an assumed one-hour premium.

**Turnover/costs.** 200% gross turnover per signal day; break-even 2/4/10 bp at 1/2/5 bp one-way.

**Data.** Hourly OHLCV plus PIT SIC2 and PIT index membership.

**Prior overlap.** Same graph/thesis as E1 and R10 S3, but one-hour lag rather than monthly CLV, industry momentum, or prior-month peer response: [E1](../../specs/r6_prereg/E1.md), [R10 S3](../../r10/S3/SCREEN.md), [R6 E](../../r6_ideas/E.md). Count as adjacent, not independent.

**Chance after 50% haircut.** Subjective cost-only chance: 5% / 2% / <1% at 1/2/5 bp one-way; lower under strict R6 portfolio gates.

### 2. Opening-gap fade when the first hour is quiet — pressure reverses

**Mechanism.** A low-volume opening gap may be temporary liquidity demand; a gap with high opening volume may reflect information assimilation. Evidence is mixed: a 2010–2019 U.S. index-stock study reports about 30 bp open-to-close continuation for positive full gaps in S&P 500 names, not a one-hour low-volume fade ([Aiche, Cohen and Griskin, 2024](https://doi.org/10.1007/s10614-023-10363-w)).

**Exact rule.** At 10:30 calculate overnight gap g = log(open at 09:30 / prior close) and opening-hour dollar-volume surprise versus the median of the prior 20 09:30–10:30 bars. Among names with surprise below their own median, rank by negative g: long the largest negative gaps and short the largest positive gaps, holding 10:30–11:30. Freeze this single median split; do not sweep thresholds.

**Literature effect.** Nearest number is +30 bp for positive full-gap open-to-close continuation, the opposite sign and a different horizon. Matched fade estimate: 0 bp; the published number is an adverse continuation benchmark.

**Turnover/costs.** 200%; break-even 2/4/10 bp at 1/2/5 bp one-way.

**Data.** Hourly OHLCV, prior regular-session close and PIT membership. No news filter.

**Prior overlap.** Related to S1-03 overnight-return persistence and the broader R6 reversal family; entry time, fade sign and first-hour volume condition define the new question. Keep separate from daily overnight persistence: [R10 S1](../../r10/S1/SCREEN.md), [T-daily](../../r6_ideas/T_daily.md).

**Chance after 50% haircut.** 1% / <1% / <1% at 1/2/5 bp. The closest S&P result has the opposite sign.

### 3. Signed one-hour order-flow persistence — direct pressure persists

**Mechanism.** Order splitting can make signed imbalances persistent and create temporary pressure. Chordia and Subrahmanyam find positive lagged-imbalance/return relations in daily NYSE data, with a sign reversal after conditioning on current imbalance ([Chordia & Subrahmanyam, 2004](https://doi.org/10.1016/S0304-405X(03)00175-2)). This is the most direct pressure measure in this list.

**Exact rule.** Compute buyer-initiated minus seller-initiated dollar volume for 09:30–10:30 divided by total eligible dollar volume, using a frozen trade-signing rule and consolidated trade/quote timestamps. At 10:30 long the top imbalance quintile and short the bottom quintile for 10:30–11:30. Freeze trade-condition handling and quote matching before outcome access.

**Literature effect.** The cited study reports statistically significant daily imbalance-strategy returns but no transferable one-hour mega-cap bp/trade estimate. Matched planning estimate: 0 bp. Do not substitute an OHLCV candle score for signed flow.

**Turnover/costs.** 200%; break-even 2/4/10 bp at 1/2/5 bp one-way.

**Data.** Extra consolidated trades plus synchronized quotes or validated order-book imbalance feed, as well as hourly OHLCV and PIT mapping. Bar-derived bulk-volume classification is a different, noisier signal.

**Prior overlap.** Adjacent to D1 and failed R6 signed/minute-flow proposals, especially [Z minute-flow](../../r6_ideas/Z_minute_flow.md). Novelty is the direct signed hourly measure predicting the next hour. Stop if full PIT signed data cannot be sourced; do not fall back to OHLCV.

**Chance after 50% haircut.** 5% / 2% / <1%, conditional on full PIT signed data.

### 4. First-hour pressure predicts last-hour market return — pressure persists

**Mechanism.** Early information and delayed portfolio rebalancing can carry market pressure into the close. Gao, Han, Li and Zhou find the first half-hour market return predicts the last half-hour in SPY; OOS predictive R² is 1.7%, and the mean-variance certainty-equivalent gain is 6.35% annually at risk aversion 5 ([Gao et al., 2018](https://doi.org/10.1016/j.jfineco.2018.05.009)). These are market-level results, not stock-level long-short payoffs.

**Exact rule.** At 10:30 calculate the equal-weight PIT-universe return from the 09:30 open. At 15:00, go long the equal-weight PIT S&P/Dow sleeve if the first-hour return is positive and short it if negative; hold only 15:00–16:00. Do not rank individual stocks by their first-hour return in this candidate.

**Literature effect.** No published bp per constituent trade. Gao reports R² and annual utility, not the one-hour stock spread required here. Matched planning estimate: 0 bp; do not convert R² or utility into bp/trade.

**Turnover/costs.** 200%; break-even 2/4/10 bp at 1/2/5 bp one-way.

**Data.** Hourly OHLCV and PIT S&P/Dow membership. A fixed ETF OHLCV proxy may validate timing but cannot replace the stock-universe result.

**Prior overlap.** Same Gao mechanism as [Z intraday momentum](../../r6_ideas/Z_intraday_mom_rescreen.md), but this is market time-series timing and Z tested a cross-sectional stock ranking. Both carry the daily cost problem.

**Chance after 50% haircut.** 2% / 1% / <1% at 1/2/5 bp.

### 5. Hourly return-volume pressure persistence — OHLCV proxy

**Mechanism.** Llorente et al.'s model predicts continuation when moves reflect speculative/informed trading and reversal when they reflect risk-sharing; they find the volume-autocorrelation relation varies with informed trading ([Llorente et al., 2002](https://doi.org/10.1093/rfs/15.4.1005)). Volume alone does not identify the trading motive.

**Exact rule.** At 10:30 score each name as its 09:30–10:30 residual return × log of opening-hour dollar volume divided by its prior 20 same-hour median. Rank cross-sectionally; long top quintile and short bottom quintile for 10:30–11:30. Fix the positive sign and formula before testing.

**Literature effect.** No compatible hourly return-spread estimate; classic work uses daily signed flow or inferred trade motive. Matched planning estimate: 0 bp. Heston et al. find volume and imbalance patterns accompany intraday return seasonality but do not explain it ([Heston et al., 2010](https://doi.org/10.1111/j.1540-6261.2010.01573.x)).

**Turnover/costs.** 200%; break-even 2/4/10 bp at 1/2/5 bp one-way.

**Data.** Hourly OHLCV and PIT membership, with frozen adjustment and volume normalization rules.

**Prior overlap.** Closest to S1-01 abnormal-volume pressure, S1-02 volume-weighted CLV, S1-04 volume/return alignment, and Z minute-flow: [R10 S1](../../r10/S1/SCREEN.md), [Z minute-flow](../../r6_ideas/Z_minute_flow.md). The time scale changes; OHLCV still does not measure buyer pressure directly.

**Chance after 50% haircut.** 3% / 1% / <1% at 1/2/5 bp.

### 6. Immediate next-hour reversal of stock-specific pressure — pressure reverses

**Mechanism.** Short-lived liquidity imbalances can reverse, while bid-ask bounce can create apparent very-short-horizon reversal. Heston et al. document nearby half-hour reversal and identify temporary liquidity imbalance and bounce as contributors; Llorente et al. provide an inventory/risk-sharing channel.

**Exact rule.** At 10:30 calculate each stock's 09:30–10:30 return less the PIT-universe equal-weight return. Long the bottom quintile and short the top quintile for 10:30–11:30. Use this one fixed midday slot, with no search across hours.

**Literature effect.** No comparable one-hour top-minus-bottom estimate. The nearest quantified Heston number is 3.11 bp per half-hour for same-slot next-day continuation, which has the opposite sign/horizon. Matched reversal estimate: 0 bp.

**Turnover/costs.** 200%; break-even 2/4/10 bp at 1/2/5 bp one-way.

**Data.** Hourly OHLCV and PIT membership; midpoint quotes would separate price reversal from bounce.

**Prior overlap.** Own-stock reversal overlaps frozen J1 and intraday close/reversal concepts in [Z auction/EOD](../../r6_ideas/Z_auction_eod.md); here the fixed window is midday.

**Chance after 50% haircut.** 3% / 1% / <1% at 1/2/5 bp.

### 7. Overnight-versus-intraday clientele reversal — cross-period pressure

**Mechanism.** Investor groups trade at different times; overnight and intraday return components can show distinct continuation and reversal. Lou, Polk and Skouras find firm-level overnight and intraday continuation alongside offsetting cross-period reversal and relate return decomposition to institutional trading clienteles ([Lou et al., 2019](https://doi.org/10.1016/j.jfineco.2019.03.011)).

**Exact rule.** At the 09:30 open compute each name's prior 20-session mean overnight return (prior close to open). Short the top quintile and buy the bottom quintile for 09:30–10:30 to test whether historically strong overnight pressure reverses into the first regular-session hour. Freeze the 20-session window.

**Literature effect.** No directly reported one-hour stock-trade estimate. Matched planning estimate: 0 bp; factor-return decompositions cannot be translated to one-hour returns without additional assumptions.

**Turnover/costs.** 200%; break-even 2/4/10 bp at 1/2/5 bp one-way.

**Data.** Hourly OHLCV including prior closes, PIT membership and split/dividend-safe prices.

**Prior overlap.** Same overnight input family as S1-03 and T-daily, with reversed sign and a first-hour target: [R10 S1](../../r10/S1/SCREEN.md), [T-daily](../../r6_ideas/T_daily.md). Treat as adjacent evidence.

**Chance after 50% haircut.** 1% / <1% / <1% at 1/2/5 bp.

### 8. Same-slot hourly continuation from the prior day — pressure repeats

**Mechanism.** Predictable investor demand at recurring times can persist at the same clock time across sessions. Heston, Korajczyk and Sadka report a 3.11 bp top-minus-bottom-decile spread per half-hour for the same interval next day, lasting at daily multiples; their paper also flags trading-cost limits ([Heston et al., 2010](https://doi.org/10.1111/j.1540-6261.2010.01573.x)).

**Exact rule.** At 09:30 rank stocks by the prior session's 09:30–10:30 return. Long the top decile and short the bottom decile during today's 09:30–10:30 interval. Use only this first-hour slot.

**Literature effect.** Adjacent benchmark +3.11 bp per half-hour; 50% haircut +1.56 bp. The paper's half-hour estimate is not the one-hour adaptation. Even at 1 bp one-way, the 2 bp round-trip break-even exceeds the half-sized benchmark.

**Turnover/costs.** 200%; break-even 2/4/10 bp at 1/2/5 bp one-way.

**Data.** Hourly OHLCV and PIT membership/security mapping.

**Prior overlap.** Directly repeats T1 in [T-daily](../../r6_ideas/T_daily.md); the bar duration changes from 30 minutes to one hour. Do not count as an independent discovery.

**Chance after 50% haircut.** 1% / <1% / <1% at 1/2/5 bp. Not a new confirmatory family unless treated as a resolution replication.

### 9. Final-hour cross-sectional reversal — late pressure reverses

**Mechanism.** Close-time buying pressure in intraday losers can cause a final-hour rebound. Baltussen, Da and Soebhag report 3.49 bp value-weighted to 4.56 bp equal-weighted low-minus-high spread in the last 30 minutes, using a rest-of-day signal and a skipped 30-minute interval. They discuss close-time retail demand and short-seller risk management, and caution that frequent turnover can make it unexploitable after costs ([2024 working paper](https://www3.nd.edu/~zda/EOD.pdf)).

**Exact rule.** At 15:00 rank stocks by return from prior close through 15:00, long bottom quintile and short top quintile from 15:00 to 16:00. This adapts the paper's signal/holding window to hourly bars and removes its skip interval; its effect estimate does not transfer exactly.

**Literature effect.** Adjacent half-hour benchmark +3.49–4.56 bp; 50% haircut +1.75–2.28 bp. This barely covers a 2 bp round trip at the optimistic end and falls short of 4/10 bp.

**Turnover/costs.** 200%; break-even 2/4/10 bp at 1/2/5 bp one-way.

**Data.** Hourly OHLCV and PIT membership; the 15:00 bar must be finalized before entry.

**Prior overlap.** Strong repeat of [Z auction/EOD](../../r6_ideas/Z_auction_eod.md), [AG close-liquidity](../../r6_ideas/AG_close_liquidity.md), and T2 in [T-daily](../../r6_ideas/T_daily.md). Earlier screens lacked a full intraday panel but also identified cost and novelty problems; hourly data resolve only the resolution gap.

**Chance after 50% haircut.** 10% / 2% / <1% at 1/2/5 bp. Best nearby bp evidence, weak investability after costs and overlap.

### 10. ETF/index closing pressure into constituents — index demand spreads

**Mechanism.** ETF arbitrage and leveraged-ETF rebalancing can transmit demand to holdings, and index tracking/hedging can concentrate near the close. Barbon and Buraschi link dealer gamma and delta hedging to intraday momentum/reversal ([2021 working paper](https://www.abarbon.com/assets/Barbon_Buraschi_2021_Gamma_Fragility.pdf)). Box et al.'s intraday ETF/underlying study finds little evidence that secondary-market ETF trades lead constituent returns ([Box et al., 2021](https://doi.org/10.1016/j.jfineco.2021.04.023)).

**Exact rule.** At 15:00 calculate SPY/DIA one-hour return × same-hour dollar-volume surprise. For each PIT constituent multiply the relevant ETF score by dated index weight; go long the top quintile and short the bottom quintile from 15:00 to 16:00. Register S&P and Dow as separate tests only if their priors and family correction are fixed.

**Literature effect.** No compatible constituent-level bp/trade estimate; ETF returns alone did not lead constituent prices in Box et al. Matched planning estimate: 0 bp. Bar volume is not ETF creation/redemption flow.

**Turnover/costs.** 200%; break-even 2/4/10 bp at 1/2/5 bp one-way.

**Data.** Hourly OHLCV plus PIT index constituents/weights. Direct primary-market flow or creation/redemption records would be required to call this measured ETF flow.

**Prior overlap.** Repeats AC/DIA weighting, AG-flowday and ETF-flow families; see [R6 index](../../specs/r6_screened_index.md) and [AG close-liquidity](../../r6_ideas/AG_close_liquidity.md). OHLCV does not establish flow identity.

**Chance after 50% haircut.** <1% / <1% / <1% at 1/2/5 bp.

## Four candidates for preregistration

These are the best research shortlist after considering mechanism, hourly resolution, observable inputs and overlap, not four expected winners:

1. **SIC2 peer lead-lag:** fix one peer graph, source hour and target hour. Treat it as a timing extension of E1/S3 and correct for that family.
2. **Opening-gap fade conditional on low first-hour volume:** fix one median volume split and 10:30 entry. Direction is uncertain; nearest S&P result points to continuation.
3. **Signed one-hour order-flow persistence:** preregister only after securing full PIT signed trades/quotes. Do not substitute CLV or BVC after a failed data gate.
4. **Market first-hour-to-last-hour continuation:** keep outcome market-level and portfolio equal-weight PIT S&P/Dow; do not turn it into a cross-sectional sort after outcomes.

Do not promote same-slot continuation or final-hour reversal as new discoveries. They replicate prior R6 T1 and Z/AG directions. Their half-sized nearby effects are below the 2 bp round-trip cost at 1 bp one-way for same-slot continuation and reach it only at the optimistic end for final-hour reversal. Both daily books also exceed the prior 50% turnover cap.

## Literature notes

- Gao, Han, Li and Zhou, “Market Intraday Momentum,” *Journal of Financial Economics* 129 (2018), 394–414. [DOI](https://doi.org/10.1016/j.jfineco.2018.05.009). Market ETF first/last-half-hour prediction; OOS R² and certainty-equivalent utility are not stock-level bp/trade.
- Heston, Korajczyk and Sadka, “Intraday Patterns in the Cross-Section of Stock Returns,” *Journal of Finance* 65 (2010), 1369–1407. [DOI](https://doi.org/10.1111/j.1540-6261.2010.01573.x), [paper PDF](https://econ.au.dk/fileadmin/site_files/filer_oekonomi/subsites/creates/Seminar_Papers/2008/heston.pdf). Reports 3.11 bp per half-hour same-slot next day; also documents nearby reversal and cost limits.
- Llorente, Michaely, Saar and Wang, “Dynamic Volume-Return Relation of Individual Stocks,” *Review of Financial Studies* 15 (2002), 1005–1047. [DOI](https://doi.org/10.1093/rfs/15.4.1005). Theory separates speculative and risk-sharing trades; empirical design is daily.
- Chordia and Subrahmanyam, “Order Imbalance and Individual Stock Returns: Theory and Evidence,” *Journal of Financial Economics* 72 (2004), 485–518. [DOI](https://doi.org/10.1016/S0304-405X(03)00175-2). Signed imbalance is more direct than OHLCV; tests use daily NYSE flow.
- Hou, “Industry Information Diffusion and the Lead-Lag Effect in Stock Returns,” *Review of Financial Studies* 20 (2007), 1113–1138. [DOI](https://doi.org/10.1093/revfin/hhm003). Intra-industry lead-lag, especially with sluggish negative-information adjustment.
- Lou, Polk and Skouras, “A Tug of War: Overnight versus Intraday Expected Returns,” *Journal of Financial Economics* 134 (2019), 192–213. [DOI](https://doi.org/10.1016/j.jfineco.2019.03.011). Distinct overnight/intraday continuation and cross-period reversal, without one-hour stock-trade size.
- Baltussen, Da and Soebhag, “End-of-Day Reversal” (November 2024 working paper). [PDF](https://www3.nd.edu/~zda/EOD.pdf). Reports 3.49–4.56 bp per final-half-hour spread and flags frequent rebalancing costs.
- Box, Davis, Evans and Lynch, “Intraday Arbitrage between ETFs and Their Underlying Portfolios,” *Journal of Financial Economics* 141 (2021), 1078–1095. [DOI](https://doi.org/10.1016/j.jfineco.2021.04.023). Finds little evidence ETF secondary-market trading leads constituent returns.
- Aiche, Cohen and Griskin, “Stocks Opening Price Gaps and Adjustments to New Information,” *Computational Economics* 63 (2024), 877–891. [DOI](https://doi.org/10.1007/s10614-023-10363-w). Reports daily gap following, including about 30 bp open-to-close for positive full gaps in S&P 500 names; not the proposed fade.
- Barbon and Buraschi, “Gamma Fragility” (2021 working paper). [PDF](https://www.abarbon.com/assets/Barbon_Buraschi_2021_Gamma_Fragility.pdf). Supports a hedging-pressure channel; OHLCV does not identify dealer gamma.

## Screen conclusion

The hourly panel can test timing patterns at higher resolution than daily OHLCV. The literature still does not support a matched, after-cost one-hour effect for PIT S&P/Dow stock portfolios. Use the four shortlisted ideas for fixed mechanism preregistrations only; resolve expected hourly bp, turnover and full input manifests before calling any an investable strategy.


