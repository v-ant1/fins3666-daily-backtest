# Evidence cards — price pressure, persistence and measurement

**Scope:** These cards summarize linked sources, not findings for this project. “Not reported” means the opened source did not provide the number; I do not guess. VERIFIED means a primary journal/NBER/author paper or publisher source was opened.

## 1. Campbell, Grossman and Wang (1993) — volume-conditioned reversal
- **Citation/status:** “Trading Volume and Serial Correlation in Stock Returns,” *QJE* 108(4), 905–939. [DOI](https://doi.org/10.2307/2118454), [author PDF](https://web.mit.edu/wangj/www/pap/CampbellGrossmanWang93.pdf). **VERIFIED, peer-reviewed.**
- **Claim/mechanism:** Risk-averse liquidity providers accommodate noninformational pressure and require return compensation; daily return autocorrelation falls on high-volume days.
- **Data/horizon:** US indexes and individual large stocks; daily returns/volume, historical sample through 1987; next-day/first-order autocorrelation.
- **Effect:** In 1975–87, the volume term is significant (t=2.9) but raises R² only 4.3% to 4.6%. Conditional reversal evidence, not net portfolio alpha. No trading costs evaluated.
- **Limitations:** The source is a historical conditional-autocorrelation result. No dedicated replication was found in logged searches; that is not evidence of non-replication.
- **Thesis relevance 3/3; feasibility 3/3** for coarse daily OHLCV. **Prediction:** high-volume noninformational price shocks reverse in 1–5 days, with pressure/news conditioning needed.

## 2. Llorente, Michaely, Saar and Wang (2002) — information vs risk-sharing
- **Citation/status:** “Dynamic Volume-Return Relation of Individual Stocks,” *RFS* 15(4), 1005–1047. [DOI](https://doi.org/10.1093/rfs/15.4.1005), [author PDF](https://web.mit.edu/wangj/Public/Publication/Llorente-Michaely-Saar-Wang02.pdf). **VERIFIED, peer-reviewed.**
- **Claim/mechanism:** Hedging/risk-sharing trades reverse; private-information speculative trades continue while news is gradually impounded.
- **Data/horizon:** NYSE/AMEX individual-stock panel; daily returns/volume; next-day return autocorrelation conditional on volume.
- **Effect:** Smaller/high-spread stocks show more continuation after high-volume days; large/low-spread stocks show little continuation and mostly reversal. Opened conclusion gives no single bps/t-stat. No net costs studied.
- **Limitations:** Their result varies by information asymmetry, not universal. Dow mega-caps resemble the low-information-asymmetry group.
- **Relevance 3/3; feasibility 3/3** for coarse volume conditions. **Prediction:** daily pressure sign depends on independently identified liquidity vs information shock; 1–5 days.

## 3. Avramov, Chordia and Goyal (2006) — reversal can be untradeable
- **Citation/status:** “Liquidity and Autocorrelations in Individual Stock Returns,” *JF* 61(5), 2365–2394. [DOI/publisher](https://doi.org/10.1111/j.1540-6261.2006.01060.x). **VERIFIED, peer-reviewed.**
- **Claim/mechanism:** Reversals are strongest for high-turnover, low-liquidity losers where immediacy pressure is large; these names have highest spreads/impact costs.
- **Data/horizon:** US individual stocks; short-horizon reversal/contrarian returns, particularly monthly.
- **Effect:** Author working copy says contrarian profits are smaller than likely costs. Publisher abstract gives no unified bps or t-stat, so none quoted.
- **Limitations:** Direct evidence against assuming statistical reversals are tradable. Dow may have smaller gross effect but lower costs.
- **Relevance 3/3 (against); feasibility 3/3** to stratify, though OHLCV misses spreads. **Prediction:** gross reversal after liquidity shocks, but cost-adjusted edge may vanish.

## 4. Coval and Stafford (2007) — mutual-fund fire sales
- **Citation/status:** “Asset Fire Sales (and Purchases) in Equity Markets,” *JFE* 86(2), 479–512. [DOI/JFE record](https://doi.org/10.1016/j.jfineco.2006.09.007). **VERIFIED, peer-reviewed.**
- **Claim/mechanism:** Fund outflows force sales in overlapping holdings; inflows force purchases. Constrained liquidity supply causes temporary price pressure.
- **Data/horizon:** US mutual-fund flows and holdings/trades, 1980–2004; monthly measurements and subsequent monthly returns.
- **Effect:** In the main event-study results (Table 4), forced-sale stocks fall 7.90% over the event quarter (t=−3.45) and rebound 6.13% over the next 12 months (t=2.47); this is not an annualized net portfolio result. The paper reports no implementation costs.
- **Limitations:** Strong identification of non-opportunistic flow, but requires historical flows and holdings; current quarterly 13F can be delayed and noisy.
- **Relevance 3/3; feasibility 2/3** with FactSet/holdings, 1/3 OHLCV alone. **Prediction:** recent forced demand predicts returns during deployment, then weeks/months reversal; same-holder assets co-move.

## 5. Lou (2012) — predictable flow-induced trading
- **Citation/status:** “A Flow-Based Explanation for Return Predictability,” *RFS* 25(12), 3457–3489. [DOI](https://doi.org/10.1093/rfs/hhs103), [author PDF](https://personal.lse.ac.uk/loud/flows.pdf). **VERIFIED, peer-reviewed.**
- **Claim/mechanism:** Sum flow-induced trades across funds' lagged holdings to estimate a demand shock; predictable mutual-fund flows forecast return during deployment and reverse as pressure dissipates.
- **Data/horizon:** US funds/stock holdings and flows, monthly; expected pressure predicts stock/fund returns in following year with reversal in subsequent years.
- **Effect:** In Table V, top-minus-bottom expected-FIT deciles return 5.28% (t=2.63) in the year after formation and −5.67% (t=−2.17) over the following two years; the portfolios are formed at quarter end and held for twelve quarters. These are gross cross-sectional portfolio returns, not daily Dow estimates.
- **Limitations:** Flow measures can mechanically include returns unless correctly constructed; holdings/flows are absent from OHLCV.
- **Relevance 3/3; feasibility 2/3** with FactSet/EDGAR holdings. **Prediction:** lagged FIT forecasts positive monthly returns during flow deployment; reversal after 12–24 months.

## 6. Ben-David, Franzoni and Moussawi (2018) — ETF flow transmission
- **Citation/status:** “Do ETFs Increase Volatility?,” *JF* 73(6), 2471–2535. [DOI/Wiley](https://doi.org/10.1111/jofi.12727), [NBER paper](https://www.nber.org/papers/w20071). **VERIFIED, peer-reviewed; NBER full text opened.**
- **Claim/mechanism:** ETF mispricing and creations/redemptions induce arbitrage in constituent stocks, propagating noisy pressure and subsequent reversals.
- **Data/horizon:** US ETF ownership/flows and constituent stocks; intraday and daily, with return response through 5–20 days.
- **Effect:** The NBER working paper’s abstract reports that 1 SD more ETF ownership is associated with 16% higher daily volatility. In the S&P 500 sample, 1 SD ETF mispricing at mean ownership predicts +0.085% on day zero and −0.344% over the next trading month; 1 SD ETF flows at mean ownership correlate with −0.156% next-20-day returns. These are reported as estimates in the paper’s return-response tables; the cited passages do not give their t-statistics. Smaller Russell 3000 effects.
- **Limitations:** Holdings/flows required; event can be short-lived. Strong relevance to large liquid constituents.
- **Relevance 3/3; feasibility 2/3** with ETF holdings/flows, 1/3 OHLCV. **Prediction:** signed creation/redemption shock maps into same-day constituent pressure and 1–20-day reversal.

## 7. Lee and Ready (1991) — sign intraday trades
- **Citation/status:** “Inferring Trade Direction from Intraday Data,” *JF* 46(2), 733–746. [DOI/Wiley](https://doi.org/10.1111/j.1540-6261.1991.tb02683.x), [author-readable PDF](https://www.acsu.buffalo.edu/~keechung/MGF743/Readings/Inferring%20trade%20direction%20from%20intraday%20data.pdf). **VERIFIED, peer-reviewed.**
- **Claim/mechanism:** Trade direction is inferred from quote position and tick rule; stale or post-trade quote timestamps and inside-spread trades cause errors.
- **Data/horizon:** 150 NYSE firms and AMEX intraday trade/quote data in 1988; trade-level classification.
- **Effect:** Tick rule correctly labels 92.1% of trades at ask as buys and 90.2% at bid as sells where quotes are unambiguous. About 30% of trades remain inside-spread after timing correction. Classification rates, not return alpha.
- **Limitations:** Quote/timestamp quality and market regime matter. No trading-alpha claim.
- **Relevance 3/3; feasibility 1/3** without TAQ/FactSet. **Prediction:** independently signed imbalance should outperform candle proxies at 1–5 days after controlling for contemporaneous return/volume.

## 8. Easley, López de Prado and O’Hara (2012) — BVC/VPIN
- **Citation/status:** “Flow Toxicity and Liquidity in a High-frequency World,” *RFS* 25(5), 1457–1493. [DOI/publisher](https://doi.org/10.1093/rfs/hhs053). **VERIFIED, peer-reviewed publisher abstract opened.**
- **Claim/mechanism:** VPIN measures absolute imbalance in equal-volume buckets; bulk-volume classification estimates buys/sells from price moves in each bucket, intending to flag adverse-selection/toxicity risk.
- **Data/horizon:** High-frequency volume-time observations; short-term volatility/toxicity indicator.
- **Effect:** Authors call VPIN useful for short-term toxicity-driven volatility; accessible source gives no numeric effect/t-stat.
- **Limitations:** Needs intraday data and an approximate classifier; BVC can conflate volatility and toxicity. See counterevidence card 9. Not recoverable faithfully from daily OHLCV.
- **Relevance 2/3; feasibility 1/3 intraday, 0/3 daily bars. Prediction:** only useful if it adds to volume/volatility baselines for short horizons.

## 9. Andersen and Bondarenko (2014) — counterevidence on VPIN
- **Citation/status:** “VPIN and the Flash Crash,” *Journal of Financial Markets* 17, 1–46. [DOI](https://doi.org/10.1016/j.finmar.2013.05.005), and Andersen & Bondarenko’s separate follow-up, “Reflecting on the VPIN Dispute,” *Journal of Financial Markets* 17(1), 53–64, [journal record](https://pure.au.dk/portal/da/publications/reflecting-on-the-vpin-dispute-2/). **VERIFIED, peer-reviewed.**
- **Claim/mechanism:** VPIN is mechanically related to volume/volatility; after controlling these, it has no incremental short-run volatility prediction. Results depend sharply on trade classifier.
- **Data/horizon:** S&P 500 futures tick data, flash-crash period; intraday volatility prediction.
- **Effect:** No incremental predictive content after controls and no unusual pre-crash VPIN high. Abstract gives no coefficient/t-stat.
- **Limitations:** Direct peer-reviewed challenge to VPIN. Do not treat a volatility proxy as pressure evidence.
- **Relevance 3/3 contra; feasibility 1/3. Prediction:** toxicity proxy must beat a volume/volatility-only baseline out of sample.

## 10. Amihud (2002) — daily illiquidity proxy
- **Citation/status:** “Illiquidity and Stock Returns: Cross-Section and Time-Series Effects,” *Journal of Financial Markets* 5(1), 31–56. [DOI](https://doi.org/10.1016/S1386-4181%2801%2900024-6), [author PDF](https://www.cis.upenn.edu/~mkearns/finread/amihud.pdf). **VERIFIED, peer-reviewed.**
- **Claim/mechanism:** Daily |return|/dollar-volume estimates price response per dollar; expected illiquidity associates positively with expected returns, while unexpected illiquidity associates negatively with contemporaneous returns.
- **Data/horizon:** NYSE daily observations, 1964–97, aggregated over periods; long-horizon liquidity-premium tests.
- **Effect:** Positive, highly significant expected-return relation; no unified coefficient/t-stat in opened abstract passage. Stronger effects in small firms.
- **Limitations:** Unsigned measure; says nothing about whether buyer or seller caused the move. Not a pressure signal.
- **Relevance 1/3; feasibility 3/3. Prediction:** use as liquidity/cost control; pressure effects should be stronger in high-ILLIQ states.

## 11. Kyle (1985) — theory behind signed-flow price impact
- **Citation/status:** “Continuous Auctions and Insider Trading,” *Econometrica* 53(6), 1315–1335. [JSTOR DOI](https://doi.org/10.2307/1913210), [paper PDF](https://people.hec.edu/lovo/wp-content/uploads/sites/28/2019/03/Continuous-auctions-and-insider-trading.pdf). **VERIFIED, peer-reviewed.**
- **Claim/mechanism:** Market makers infer private information from aggregate signed order flow; informed traders spread trades over time. Kyle lambda is price impact per signed net flow.
- **Data/horizon:** Theory model, not an empirical stock sample.
- **Effect:** No empirical estimate/t-stat. Model implies information is incorporated by end of trading.
- **Limitations:** Explains why signed flow can be informative but cannot validate OHLCV proxies or imply net alpha.
- **Relevance 2/3; feasibility 1/3 with signed flow, 0/3 exact lambda from OHLCV. Prediction:** estimate price response and decay from actual signed flow if TAQ exists.

## 12. Lou, Polk and Skouras (2019) — overnight/intraday tug of war
- **Citation/status:** “A Tug of War: Overnight versus Intraday Expected Returns,” *JFE* 134(1), 192–213. [DOI](https://doi.org/10.1016/j.jfineco.2019.03.011), [author PDF](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf). **VERIFIED, peer-reviewed.**
- **Claim/mechanism:** Investor clienteles trade at different market times: overnight and intraday stock returns each continue but cross-period reversal offsets them; strategies can earn return only in one segment.
- **Data/horizon:** US stocks and 14 strategies, overnight and open-close returns over long historical samples; daily components and monthly strategy returns.
- **Effect:** Example low-investment strategy intraday CAPM alpha +0.97% (t=4.39) and overnight three-factor alpha −0.28% (t=−2.10). Not a pressure strategy. Paper finds effects persist over years.
- **Limitations:** Their large/value-weight sample finds no close-to-close short-term reversal. Components do not identify flow source.
- **Relevance 2/3; feasibility 3/3** from OHLC. **Prediction:** test pressure separately overnight, intraday and close-close for 1–5 days; opposite signs may cancel.

## 13. Boehmer, Jones, Zhang and Zhang (2021) — marketable retail flow
- **Citation/status:** “Tracking Retail Investor Activity,” *JF* 76(5), 2249–2305. [DOI/Wiley](https://doi.org/10.1111/jofi.13033), [full paper](https://vintagequants.com/wp-content/uploads/2024/09/Paper20Xiaoyan20Zhang.pdf). **VERIFIED, peer-reviewed.**
- **Claim/mechanism:** Venue, trade size and price-improvement data identify marketable retail orders. Net retail buying predicts positive returns; less than half is attributed to flow persistence, while authors describe information interpretation as suggestive.
- **Data/horizon:** TAQ/CRSP US stocks, 2010–15; weekly Fama–MacBeth regressions; signal fades by ~12 weeks.
- **Effect:** About 10 bps next-week high/low difference in abstract. In largest-cap tercile, weekly IQR spread 2.6 bps (t=3.68), versus 21.9 bps (t=13.90) smallest-cap tercile. Table III’s baseline one-week retail-imbalance coefficient is 0.0009 (t=15.60); t=10.61 appears in a separate specification adding public-news controls (Table IX). Gross, no Dow-specific after-cost result.
- **Limitations:** Signal weaker but present in large names; requires trade-level data. 2024 arXiv re-examination identified in search log is a reason for caution.
- **Relevance 3/3; feasibility 1/3 absent TAQ. Prediction:** positive retail imbalance predicts next week; weaker in Dow mega-caps; test 1/5/20 days.

## 14. Cont, Kukanov and Stoikov (2014) — order-flow imbalance
- **Citation/status:** “The Price Impact of Order Book Events,” *Journal of Financial Econometrics* 12(1), 47–88. [DOI/publisher abstract](https://doi.org/10.1093/jjfinec/nbt003), [paper](https://arxiv.org/abs/1011.6402). **VERIFIED, peer-reviewed.**
- **Claim/mechanism:** Short-interval price changes are mainly explained by best-bid/ask OFI, including market/limit orders and cancellations; impact slope varies inversely with depth. Trade volume alone is noisier.
- **Data/horizon:** NYSE TAQ for 50 US stocks; short intraday intervals.
- **Effect:** Linear price-change/OFI relation; publisher abstract does not expose a single coefficient/t-stat. This is contemporaneous impact, not next-day alpha.
- **Limitations:** Requires order book/quote updates; daily OHLCV cannot reconstruct cancellations/depth.
- **Relevance 3/3; feasibility 1/3 with quotes, 0/3 OHLCV. Prediction:** lagged cross-asset OFI forecasts related-asset returns only if propagation is real.

## 15. Chordia, Roll and Subrahmanyam (2002) — market order imbalance
- **Citation/status:** “Order Imbalance, Liquidity, and Market Returns,” *JFE* 65(1), 111–130. [Caltech author record](https://authors.library.caltech.edu/records/z2akv-j0p87). **VERIFIED, peer-reviewed record/abstract.**
- **Claim/mechanism:** Signed aggregate buy-minus-sell orders add information beyond volume/liquidity; market imbalances rise after declines, and large negative-return/sell-imbalance days reverse.
- **Data/horizon:** NYSE aggregate daily order imbalance and returns; contemporaneous/lagged daily response.
- **Effect:** “Strongly affected” lagged market returns per abstract; no number/t-stat exposed.
- **Limitations:** Market aggregate, not individual-stock cross-section; daily signed orders not present in OHLCV.
- **Relevance 2/3; feasibility 1/3. Prediction:** negative market shocks with high sell imbalance reverse; control for common market component in Dow tests.

## 16. Harris and Gurel (1986) — index inclusion price pressure
- **Citation/status:** “Price and Volume Effects Associated with Changes in the S&P 500 List: New Evidence for the Existence of Price Pressures,” *JF* 41(4), 815–829. [DOI/Wiley](https://doi.org/10.1111/j.1540-6261.1986.tb04550.x). **VERIFIED, peer-reviewed publisher record.** The DOI previously attached to Shleifer was for this Harris–Gurel paper; Shleifer’s “Do Demand Curves for Stocks Slope Down?” is a different article.
- **Claim/mechanism:** Index additions create mechanical fund demand and an upward event-window price impact.
- **Data/horizon:** S&P 500 additions; announcement/short event window.
- **Effect:** Publisher abstract reports an addition-announcement rise exceeding 3%, nearly fully reversed after two weeks; it gives no t-stat. Historical effect may not be current.
- **Limitations:** Event-level not daily broad-stock signal; requires event/holdings to attribute causality.
- **Relevance 2/3; feasibility 2/3 with notice/holdings. Prediction:** event demand shocks move additions and linked names over announcement-to-effective window.

## 17. Greenwood and Sammon (2023 working paper) — index effect decay
- **Citation/status:** “The Disappearing Index Effect,” revised Nov. 2023. [HBS author PDF](https://www.hbs.edu/ris/Publication%20Files/23-025_563e45c6-df92-4d9c-ae05-608d4d0acab1.pdf), [NBER WP](https://www.nber.org/papers/w30748). **VERIFIED working paper, not peer-reviewed in accessed version.**
- **Claim/mechanism:** S&P price impact collapsed as market supply became more elastic/anticipation increased.
- **Data/horizon:** S&P additions/deletions by decade; event returns up to 100 trading days.
- **Effect:** The opened NBER paper reports addition abnormal returns of 7.6% in the 1990s and 0.8% in 2010–20; deletion returns were −16.1% in the 1990s and −0.6% in 2010–20, statistically indistinguishable from zero. The HBS working-paper version gives closely related decade estimates (7.4% and 0.3% additions; −16.1% and −0.6% deletions); the exact version should be named when citing a figure.
- **Limitations:** Strong counterevidence for a contemporary index event trade; these are not Dow-specific.
- **Relevance 2/3 contra; feasibility 2/3. Prediction:** modern event signal should be weak and must beat no-event placebo.

## 18. McLean–Pontiff (2016) and Hou–Xue–Zhang (2020) — decay and replication
- **Citation/status:** McLean & Pontiff, “Does Academic Research Destroy Stock Return Predictability?,” *JF* 71(1), 5–32. [DOI](https://doi.org/10.1111/jofi.12365). Hou, Xue & Zhang, “Replicating Anomalies,” *RFS* 33(5), 2019–2133. [DOI](https://doi.org/10.1093/rfs/hhy131); the opened full-text numeric evidence below is from their [NBER working paper](https://www.nber.org/papers/w23394). **McLean–Pontiff VERIFIED, peer-reviewed source opened; Hou et al. VERIFIED as NBER working paper and publisher journal record, with working-paper full text opened.**
- **Claim/mechanism:** Published predictors weaken after the original sample/publication; stricter variable construction and replication controls shrink anomaly sets.
- **Data/horizon:** McLean–Pontiff compare in-sample, post-sample and post-publication for 97 predictors. Hou et al. re-examine a large anomaly library with stricter replications.
- **Effect:** McLean–Pontiff report 26% average out-of-sample decay and 58% total decay after publication relative to the original in-sample returns (32 percentage points additional after the out-of-sample decline). Hou, Xue and Zhang’s NBER working-paper analysis reports 286 of 447 anomalies insignificant at the 5% level and 380 of 447 insignificant under a t-statistic threshold of 3; these counts are from the working-paper version. Cross-anomaly estimates, not pressure-specific.
- **Limitations:** Results are sensitive to screens and implementation; they reinforce preregistration and reporting failures, not rejection of all pressure mechanisms.
- **Relevance 2/3; feasibility 3/3** for design. **Prediction:** exact frozen pressure hypotheses must survive development replication and fresh holdout.

## Measurement comparison
| Measure | Measures | Required data | Limitation / project use |
|---|---|---|---|
| Signed volume | Aggressor buy minus sell quantity/value | Trade signs (Lee–Ready or exchange flag) | OHLCV volume is unsigned; sign(return)×volume is only a crude proxy |
| OFI | Quote-level supply/demand including cancellations | Intraday quotes/order book | Better contemporaneous pressure; not available from daily candles |
| BVC/VPIN | Volume-time signed imbalance / toxicity | High-frequency trades/prices | Volatility confound; classifier contested; not daily OHLCV |
| Amihud | |return| / dollar volume | Daily close and volume | Unsigned illiquidity/cost proxy, not buying pressure |
| Kyle lambda | Price response per signed net flow | Signed flow and prices | Cannot estimate faithfully without flow |
| CLV | Close position within daily high-low: (2C−H−L)/(H−L) | Daily OHLC | Not buyer/seller classification; gap/news/auction prints contaminate |
| Overnight/intraday split | Close-open vs open-close return | Daily OHLC | Available; return timing is not investor identity |
| Retail imbalance | Marketable retail initiated buy-sell flow | TAQ, venues, trade sizes, price improvement | Not in daily OHLCV; documented effect weaker in large caps |
| ETF/fund pressure | Holdings-weighted flows / forced demand | Point-in-time holdings and daily/monthly flows | Not recoverable from prices; current index impact has decayed |

**Measurement conclusion:** Daily OHLCV permits a coarse pressure proxy and overnight/intraday decomposition; it cannot measure signed flow, depth, quote cancellations, investor identity, ETF ownership or fund demand. Treat CLV, sign(return)×volume and Amihud as proxies/controls; never call them observed order flow or Kyle lambda.


