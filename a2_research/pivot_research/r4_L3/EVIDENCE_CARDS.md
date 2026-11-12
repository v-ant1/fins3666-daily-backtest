# Evidence cards — networks and pressure propagation (L3)

Scope: literature review only; no backtests were run. “Shown” refers to reported empirical results, not a causal interpretation unless noted. Older papers mostly use monthly data and broader CRSP universes; those results do not establish viability in the 2020–2026 Dow 30.

## 1. VERIFIED — Cohen & Frazzini (2008), “Economic Links and Predictable Returns,” *Journal of Finance* 63(4), 1977–2011. [DOI / author PDF](https://doi.org/10.1111/j.1540-6261.2008.01379.x) | [opened PDF](https://pages.stern.nyu.edu/~afrazzin/pdf/Economic%20Links%20and%20Predictable%20Returns%20-%20Cohen%20and%20Frazzini.pdf)
- **Claim / mechanism:** Suppliers react with a lag to customer news because investors overlook salient value-chain links; customer returns proxy news about supplier cash flows.
- **Data / horizon:** US common stocks; material customer links disclosed under SFAS 131; monthly stock returns and linked-firm information, 1980–2004. Customer return in month *t* predicts supplier return in *t+1*.
- **Magnitude:** The headline strategy earns 1.55% per month (18.6% annualized; paper abstract). Table III reports 1.45% monthly Fama–French alpha (t=3.61) and 1.37% after adding Carhart momentum (t=3.12), for the 1981–2004 customer return sort. The separately reported one-year customer-momentum EW strategy is 1.13%/month (t=4.16); the VW/larger-stock result is about 70 bp/month and not statistically significant. Thus the evidence is materially weaker for large caps.
- **Large caps / costs / decay:** Tradable long-short construction includes priced stocks and value weighting; not a Dow-only or modern after-cost test. Direct post-publication replication evidence is mixed (see Card 16). Link data require historical Compustat segment/customer disclosures, not daily OHLCV.
- **Relevance 3/3; feasibility 1/3.** Strong directional economic network, but links are sparse and annual/quarterly disclosure-based and difficult to reconstruct for Dow daily tests.
- **Prediction:** Positive supplier return after positive customer pressure/news, over roughly the next month; isolate pressure/news from fundamentals in a Dow event study.

## 2. VERIFIED — Menzly & Ozbas (2010), “Market Segmentation and Cross-predictability of Returns,” *Journal of Finance* 65(4), 1555–1580. [Publisher / DOI](https://doi.org/10.1111/j.1540-6261.2010.01578.x)
- **Claim / mechanism:** Customer and supplier industries cross-predict each other as specialized investors and market segmentation slow information diffusion.
- **Data / horizon:** US stocks and linked industries; monthly return tests; lagged returns of economically related industries forecast focal stock returns. Publisher abstract reports the relationship is weaker for firms with more analyst coverage and institutional ownership.
- **Magnitude:** Publisher abstract and accessible record do not expose the headline table’s precise alpha/t-stat; no number is inferred here. Reported finding is positive, statistically significant cross-predictability (main results in the paper’s cross-predictability tables).
- **Large caps / costs / decay:** Coverage/ownership results imply the effect attenuates where information is better processed. No recent large-cap, after-cost validation located.
- **Relevance 3/3; feasibility 1/3.** A mechanism-based directed network, but industry input-output data are required; coarsely assigning 30 Dow names to industries would create confounding.
- **Prediction:** Positive next-month return from positive upstream/downstream peer return, stronger in less-covered firms; in Dow test control industry and own momentum.

## 3. VERIFIED — Antón & Polk (2014), “Connected Stocks,” *Journal of Finance* 69(3), 1099–1127. [Publisher / DOI](https://doi.org/10.1111/jofi.12149) | [author PDF](https://personal.lse.ac.uk/polk/research/ConnectedStocks.pdf)
- **Claim / mechanism:** Shared active mutual-fund owners predict excess return covariance; fund demand shocks propagate across portfolio holdings, producing over-comovement and reversal.
- **Data / horizon:** US stocks, active mutual-fund ownership and monthly returns; the paper focuses on relatively large stocks (above NYSE median) and reports results over 1980–2008. Network weights use common active ownership.
- **Magnitude:** The journal PDF (Table V) reports a five-factor alpha of 76 bp/month (t=4.96) for the connected-stock strategy: buy the low own-return/low connected-return composite and short the high/high composite. It averages five overlapping cohorts held for one to five months after skipping one month. This corrects the 62 bp/t=3.56 working-paper figure previously recorded; those figures came from a different version/specification and should not be presented as the published estimate.
- **Large caps / costs / decay:** Explicit large-stock analysis, a strength. Portfolio is long-short, but costs for the 2010s/2020s and after-publication persistence are not established here. Ownership quarterly and delayed.
- **Relevance 3/3; feasibility 2/3.** 13F holdings can form a quarterly, lagged co-ownership network; 13F misses intraperiod trades and reports with delay.
- **Prediction:** Conditional on same-sign recent pressure across connected holdings, expect over-comovement followed by reversal; test event response and split continuation versus reversal horizons.

## 4. VERIFIED — Greenwood & Thesmar (2011), “Stock Price Fragility,” *Journal of Financial Economics* 102(3), 471–490. [DOI / author PDF](https://doi.org/10.1016/j.jfineco.2011.06.003) | [opened PDF](https://www.hbs.edu/ris/Publication%20Files/Stock%20Price%20Fragility_eac0d3cb-4174-4a4f-af7d-610ff4e9de48.pdf)
- **Claim / mechanism:** Concentrated ownership and correlated fund liquidity shocks make stocks fragile to non-fundamental demand; fund ownership creates measurable cross-stock exposure to flows.
- **Data / horizon:** US mutual-fund holdings and flows; quarter-ahead daily volatility and comovement, main sample reported as 1990–2007 (the paper also discusses earlier ownership data).
- **Magnitude:** An increase in fragility from the 25th to 75th percentile predicts about 0.5% higher daily volatility (reported paper result); Table 3 regresses next-quarter volatility on fragility. This is a volatility result, not return-alpha evidence.
- **Large caps / costs / decay:** Original sample is focused on large common stocks. No direct tradable net-return claim. The fragility construct depends on flow covariance and ownership data, not return correlation alone.
- **Relevance 3/3; feasibility 2/3.** Provides a causal demand-risk rationale for ownership links, but estimating flow covariance across 30 firms is noisy.
- **Prediction:** Flow shocks to common owners induce synchronized pressure and higher next-quarter volatility; a return sign must be specified from the direction of the flow shock separately.

## 5. VERIFIED — Ali & Hirshleifer (2020), “Shared Analyst Coverage: Unifying Momentum Spillover Effects,” *Journal of Financial Economics* 136(3), 649–675. [DOI / published PDF](https://doi.org/10.1016/j.jfineco.2019.10.007) | [opened NBER version](https://www.nber.org/papers/w25201)
- **Claim / mechanism:** Shared analyst coverage identifies firms whose news is jointly processed; analysts update slowly across linked firms, creating connected-stock momentum.
- **Data / horizon:** US and developed international equities; monthly returns and analyst/broker coverage. Their Table 5 uses the prior month return of covered peers and reports monthly cross-sectional predictions; several linkage tests have distinct availability windows (e.g., customer links 1984–2006, technology links through 2012).
- **Magnitude:** Connected-firm momentum factor earns 1.68% monthly alpha, t=9.67 (paper abstract); one SD increase in the connected-firm return predicts +58 bp in the next monthly return (Table 5). The sample contains large and small stocks; in the table, technology-linked return is weak for large caps and only 12 bp per SD in a broader specification.
- **Large caps / costs / decay:** Broad universe and international checks; the paper does not establish contemporary after-cost large-cap performance. Analyst link data likely require I/B/E/S/FactSet.
- **Relevance 3/3; feasibility 1/3.** Excellent directional link, poor free-data fit; possible if UNSW FactSet includes analyst coverage history.
- **Prediction:** Positive one-month peer momentum for shared-analyst links; stronger for complex/indirect links and less-followed firms. A Dow test must account for analyst coverage level and avoid contemporaneous leakage.

## 6. VERIFIED — Hou (2007), “Industry Information Diffusion and the Lead-lag Effect in Stock Returns,” *Review of Financial Studies* 20(4), 1113–1138. [DOI / journal record](https://doi.org/10.1093/rfs/hhm003)
- **Claim / mechanism:** Slow diffusion of industry information explains much of the large-stock/ small-stock lead-lag effect; negative information adjusts sluggishly.
- **Data / horizon:** US stocks, monthly returns and industry classifications; big firms lead smaller firms predominantly within industry. The paper also links the effect to small firms’ post-announcement drift after big-firm earnings releases.
- **Magnitude:** Publisher-accessible abstract confirms direction, robustness, and heterogeneity but not the key table’s exact alpha/t-stat; no precise figure is asserted. Effect is at monthly horizons (lead-lag portfolios and earnings-response tests).
- **Large caps / costs / decay:** Effect is explicitly stronger for small, neglected, less competitive industries, so direct relevance to Dow constituents is limited. No after-cost large-cap result located.
- **Relevance 2/3; feasibility 3/3.** Industry labels are available, but Dow size dispersion is modest and industry peer momentum is easily confounded with conventional industry momentum.
- **Prediction:** Positive response of small/neglected same-industry stocks to large-firm lagged returns, especially after negative news; likely attenuated among Dow megacaps.

## 7. UNVERIFIED — Lo & MacKinlay (1990), “When Are Contrarian Profits Due to Stock Market Overreaction?” *Review of Financial Studies* 3(2), 175–205. [DOI](https://doi.org/10.1093/rfs/3.2.175) | [NBER paper](https://www.nber.org/papers/w2977)
- **Claim / mechanism:** Contrarian profits need not reflect own-stock reversal; positive cross-autocovariances and large-stock leadership can generate them.
- **Data / horizon:** US individual stocks and weekly portfolio returns; cross-autocovariances explain a substantial fraction of the strategy’s profits.
- **Magnitude:** The card’s prior “more than half” decomposition could not be checked against the cited primary text in this audit because the journal page and NBER PDF fetch failed. Retain only as a tentative summary pending direct review; no numeric estimate should be used. The source metadata and qualitative large-to-small lead are consistent with the cited journal record, but the detailed claim is downgraded.
- **Large caps / costs / decay:** Large-to-small lag explicitly shown, but no modern costs test. Results caution against labeling all reversal as overreaction.
- **Relevance 3/3; feasibility 3/3.** Directly testable with daily returns and size/attention partitions, but 30 Dow stocks provide little breadth.
- **Prediction:** Lagged leader returns can predict follower returns at short weekly horizons; placebo by permuting leader-follower links should remove cross-predictive component.

## 8. VERIFIED — Ben-David, Franzoni & Moussawi (2018), “Do ETFs Increase Volatility?” *Journal of Finance* 73(6), 2471–2535. [DOI](https://doi.org/10.1111/jofi.12727) | [author/NBER paper](https://www.nber.org/papers/w20071)
- **Claim / mechanism:** ETF trading and arbitrage transmit liquidity shocks into underlying constituents, raising non-fundamental volatility and short-run reversal.
- **Data / horizon:** US stocks with ETF ownership; identification exploits index membership changes; daily and intraday volatility. ETF ownership variation is linked to price volatility and autocorrelation.
- **Magnitude:** The opened April 2014 author version reports that a one-standard-deviation increase in ETF ownership is associated with 16% higher daily stock volatility (abstract). This is a working-paper estimate; the journal DOI page was inaccessible in this audit, so the 56 bp/month risk-premium claim previously attributed to the published version is removed pending direct table verification. The 16% figure is a volatility result, not a stand-alone flow strategy alpha.
- **Large caps / costs / decay:** Exogenous index membership strengthens identification; applies across ETF-held stocks. Short-horizon impact decays within days; transaction cost feasibility not established.
- **Relevance 3/3; feasibility 2/3.** ETF holdings/flow data can build exposure/overlap links, but identifying unexpected flows and historical holdings is harder than downloading daily prices.
- **Prediction:** Unexpected non-information ETF selling transmits a negative same-day constituent pressure then reversal over about 3–5 trading days; use flow direction and holdings weights.

## 9. VERIFIED — Liao Xu, Xiangkang Yin & Jing Zhao (2022), “Are the Flows of Exchange-Traded Funds Informative?” *Financial Management* 51(4), 1165–1200. [DOI / full text](https://doi.org/10.1111/fima.12396)
- **Claim / mechanism:** ETF creations/redemptions mix informative and non-informative demand; NAV premium/discount helps separate informed arbitrage from temporary basket pressure.
- **Data / horizon:** US ETF flows, prices and NAVs; daily panel from ETF inception (or Feb. 2001) through Dec. 2016; tested next-day and up to 40-day returns (Table 5).
- **Magnitude:** Unexpected ETF flows forecast next-day ETF returns, especially conditional on premiums/discounts; undecomposed flows show significantly negative ETF return coefficients on days +3 to +5. The authors find no systematic reversal after unexpected flows; some reversals follow demand-driven/arbitrage-driven flow components. Table 5 reports adjusted R² around 0.04–0.08. This is a useful counter to treating every flow as pressure.
- **Large caps / costs / decay:** Broad ETF universe; underlying-stock results need mapping through holdings. No reported after-cost strategy result in the opened section.
- **Relevance 3/3; feasibility 2/3.** Separating expected/unexpected and arbitrage/demand flow is key; ETF NAV/flow data may be accessible through FactSet or paid feeds.
- **Prediction:** A temporary ETF-demand component should reverse in held constituents after 3–5 days; an unexpected informative flow should not. Pre-specify the decomposition before testing.

## 10. VERIFIED — Diebold & Yilmaz (2012), “Better to Give than to Receive: Predictive Directional Measurement of Volatility Spillovers,” *International Journal of Forecasting* 28(1), 57–66. [DOI / paper record](https://doi.org/10.1016/j.ijforecast.2011.02.006)
- **Claim / method:** Generalized VAR forecast-error variance decompositions yield order-invariant total and directional connectedness (who transmits versus receives volatility).
- **Data / horizon:** Daily volatility in US stocks, bonds, FX and commodities, Jan. 1999–Jan. 2010; spillovers rose sharply during the global financial crisis, with stocks transmitting to other markets after Lehman.
- **Magnitude:** The study reports network spillover indices and directional decomposition; accessible abstract gives no single alpha/t-stat because this is a connectedness measure, not a return-prediction strategy.
- **Large caps / costs / decay:** Market aggregates, not a stock-level tradable test; VAR direction is conditional forecast variance, not structural causation. Rolling estimates can be unstable in a 30-node short sample.
- **Relevance 2/3; feasibility 2/3.** Useful directional diagnostics for volatility networks, less direct for signed buying pressure.
- **Prediction:** Past node shocks should improve forecast of neighbor volatility beyond own lags; do not interpret this as expected return without a separate test.

## 11. VERIFIED — Dimpfl & Peter (2012), “Using Transfer Entropy to Measure Information Flows Between Financial Markets,” SFB 649 Discussion Paper 2012-051. [University repository / PDF](https://doi.org/10.18452/4424)
- **Claim / method:** Transfer entropy measures directed conditional information flow without restricting relationships to linear dynamics; bootstrap inference is proposed.
- **Data / horizon:** Applied to CDS and corporate bonds, and VIX versus iTraxx Europe; tests pre-crisis, crisis and post-crisis periods.
- **Magnitude:** Method paper reports information transfer rather than a return strategy; no bps/Sharpe applies. The repository abstract does not expose a single effect size.
- **Large caps / costs / decay:** Not a stock portfolio study. TE requires discretization/density estimation and careful finite-sample/shuffle inference; 30 names × many directed pairs risks false edges.
- **Relevance 2/3; feasibility 2/3.** Could infer directed lagged pressure edges from daily signals, but data length and correction for pairwise testing are major constraints.
- **Prediction:** Past pressure at i contains information about future pressure at j conditional on j’s own history; test out-of-sample sign separately from TE edge discovery.

## 12. VERIFIED — Sandryhaila & Moura (2014), “Discrete Signal Processing on Graphs: Frequency Analysis,” *IEEE Transactions on Signal Processing* 62(12), 3042–3054. [DOI / author PDF](https://doi.org/10.1109/TSP.2014.2321121)
- **Claim / method:** Graph low/high frequency and filters can be defined via graph total variation; low-pass smooths neighboring node values, high-pass emphasizes differences/discontinuities.
- **Data / horizon:** Methods paper with sensor/classification illustrations; no financial return sample, horizon or trading result.
- **Magnitude:** Not applicable (no empirical financial effect size or t-stat).
- **Implication:** For a symmetric Laplacian, (e^{-\tau L}x) is a low-pass smoother. The residual (x-e^{-\tau L}x) is a high-pass/spectral residual, mathematically coherent as local disagreement, but it is not inherently buying pressure or return alpha. If pressure is expected to spread, the diffused level is the propagation measure; a high-pass residual instead tests pressure not yet shared by neighbors.
- **Relevance 2/3; feasibility 3/3.** Fully computable given a fixed graph, but the graph must be economically meaningful and chosen without outcome leakage.

## 13. VERIFIED — Moskowitz, Ooi & Pedersen (2012), “Time Series Momentum,” *Journal of Financial Economics* 104(2), 228–250. [DOI / author PDF](https://doi.org/10.1016/j.jfineco.2011.11.003)
- **Claim / mechanism:** Asset-specific returns persist from 1–12 months and partially reverse at longer horizons, consistent with underreaction followed by delayed overreaction.
- **Data / horizon:** 58 liquid futures/forwards across equity indexes, currencies, commodities and sovereign bonds; more than 25 years. 12-month excess return predicts own future returns, positive for all 58 instruments.
- **Magnitude:** The paper documents significant strategy returns across each market, and diversified risk-adjusted abnormal returns, but no single monthly alpha/t-stat is given in the opened abstract. Explicit horizon is one to twelve months with longer-run partial reversal.
- **Large caps / costs / decay:** Futures are liquid institutional instruments; transaction cost robust across instruments in paper discussion, but an ETF proxy has different roll, duration and currency exposures.
- **Relevance 2/3; feasibility 3/3 for ETF close data.** Establishes asset-specific own dynamics, not cross-asset network contagion.
- **Prediction:** Own trend may persist over months across asset classes; use volatility-scaled time-series signals per asset rather than cross-sectional ranking of unlike ETFs.

## 14. VERIFIED — Greenwood & Vayanos (2014), “Bond Supply and Excess Bond Returns,” *Review of Financial Studies* 27(3), 663–713. [DOI / journal page](https://doi.org/10.1093/rfs/hht133) | [NBER version](https://www.nber.org/papers/w13806)
- **Claim / mechanism:** Preferred-habitat investors and limited arbitrage transmit maturity-specific supply pressure into bond prices and expected excess returns.
- **Data / horizon:** Government bond maturity supply, term spreads and excess returns across maturities; historical US Treasury data; predictability tested over bond holding periods.
- **Magnitude:** In the opened NBER working-paper version, a one-standard-deviation increase in relative long-term debt supply is associated with 2.31% higher expected excess return on the 20-year bond (one-year horizon); Table III reports Newey–West t=2.84 for the 20-year univariate slope and Table IV t=2.62 after controls for term spread and Cochrane–Piazzesi. These exact estimates are attributed to the NBER version, not claimed as independently rechecked against the 2014 journal version. The paper reports stronger effects at longer maturities and cumulative horizons.
- **Large caps / costs / decay:** Government bond market, not equities; the implication is maturity-specific demand/supply pressure and duration risk, not an equity return link.
- **Relevance 2/3; feasibility 2/3.** Supports asset-appropriate measurement of bond pressure (issuance/maturity supply and duration) rather than generic ETF return correlation.
- **Prediction:** Relative long-maturity supply predicts excess returns on longer-duration bonds; do not transfer that sign mechanically to equities.

## 15. VERIFIED — Hou, Xue, Zhang & Van Nieuwerburgh (2020), “Replicating Anomalies,” *Review of Financial Studies* 33(5), 2019–2133. [DOI / RFS page](https://doi.org/10.1093/rfs/hhy131) | [NBER working paper](https://www.nber.org/papers/w23394)
- **Claim / negative evidence:** Common replication procedures and longer samples weaken many published cross-sectional return predictors; published significance alone is not a selection rule.
- **Data / horizon:** 447 anomaly variables in the NBER working-paper version; 452 in the final published article, US stocks, monthly cross-sectional portfolios.
- **Magnitude:** The three-author NBER working-paper version (2017) studies 447 signals: with NYSE breakpoints and value-weighted returns, 286/447 (64%) are insignificant at 5%, and 380/447 (85%) have |t| below 3. The later four-author RFS version studies 452 signals; these exact counts are not attributed to that final version. This is a warning against adopting a network effect from in-sample papers without a mechanism test.
- **Large caps / costs / decay:** Replications include NYSE breakpoints and controls but do not imply every network signal fails. Transaction costs further reduce some anomalies.
- **Relevance 3/3; feasibility 3/3.** Direct support for preregistration, few variants and independent placebo tests.
- **Prediction:** Require the network shock to predict future linked returns in the modern Dow sample, and reject if random links or common factors reproduce it.

## 16. VERIFIED — McLean & Pontiff (2016), “Does Academic Research Destroy Stock Return Predictability?” *Journal of Finance* 71(1), 5–32. [DOI / publisher page](https://doi.org/10.1111/jofi.12365) | [author PDF](https://gwern.net/doc/economics/2016-mclean.pdf)
- **Claim / negative evidence:** Published predictors weaken out of sample and further after publication, consistent with both data mining and arbitrage reducing returns.
- **Data / horizon:** 97 published cross-sectional predictors, portfolio returns in original sample, post-sample before publication and post-publication periods.
- **Magnitude:** Their headline estimates are roughly 26% lower post-sample and 58% lower post-publication than in-sample (article abstract/results); use as a literature-wide decay prior, not an estimate for network signals.
- **Large caps / costs / decay:** Broad anomaly portfolio evidence; not a transaction-cost study and not specific to network propagation.
- **Relevance 3/3; feasibility 3/3.** Reinforces need to report failure and resist selecting among many graph variants.
- **Prediction:** Expect effects documented before 2015 to be materially attenuated in 2020–2026 large caps.

## Sources searched but not promoted to VERIFIED evidence cards
- **Pitkäjärvi, Suominen & Vaittinen, “Cross-Asset Signals and Time Series Momentum,” JFE 2020.** Search found the publisher/SSRN records and reported result, but the accessible direct paper page could not be opened; not relied on in candidate selection. Re-open the actual paper before using it to justify a cross-asset return direction.
- **Lee, Sun, Wang & Zhang, “Technological Links and Predictable Returns.”** SSRN and JFE search record were found; JFE publisher page fetch was blocked in this run. Search result reports an old-sample monthly alpha but is not relied on; requires a successful direct-paper read before use.
- **Shared ownership evidence in smaller firms:** a later study finds large-stock linkage less important over time and small-stock results often insignificant; its accessible author manuscript is not a top-journal source. It cautions against assuming common ownership is uniformly stronger in today’s largest firms.
- **Transfer entropy across stock indices:** several peer-reviewed network papers use index-level or Chinese intraday data for network-state/systemic-risk measurement. They establish directional information-flow methods, not net return alpha for US large-cap equities.






## 17. VERIFIED — Coval & Stafford (2007), “Asset Fire Sales (and Purchases) in Equity Markets,” *Journal of Financial Economics* 86(2), 479–512. [DOI](https://doi.org/10.1016/j.jfineco.2006.09.007) | [HBS-hosted paper PDF](https://www.hbs.edu/ris/download.aspx?name=Asset+Fire+Sales+in+Equity+Markets.pdf)
- **Claim / mechanism:** Mutual-fund outflows force sales of common holdings, depressing their prices; stocks bought by funds receiving inflows can also experience flow-driven pressure, with subsequent reversals.
- **Data / horizon:** CRSP mutual-fund holdings and returns/Spectrum, US equities, 1980–2004. Flow-induced common-stock price pressure is documented across roughly the next two quarters, with subsequent reversal; this is a holdings/flow design, not a daily OHLCV signal.
- **Magnitude:** Table 8’s combined long expected-inflow purchases and short expected-fire-sale stocks reports 0.94% per month (t=3.18) equal weighted and 0.71% (t=1.96) value weighted in the cited specification. These are portfolio estimates in the paper’s sample, before our transaction-cost assumptions.
- **Large caps / costs / decay:** Broad US equity sample, not a Dow-only or modern-period validation. The required Spectrum fund data are not the free, point-in-time 13F data confirmed by L4; no claim of post-publication survival is made.
- **Relevance 3/3; feasibility 1/3.** Supports the mechanism of pressure through common holdings but shows why 13F ownership alone cannot identify daily flows or forced trades.
- **Prediction:** If a common-owner peer’s price pressure is informative, same-sign pressure may precede short-horizon return/price correction among linked names; directly testing flow-induced fire sales requires actual flow and position data, which this project lacks.

## 18. VERIFIED — Lou (2012), “A Flow-Based Explanation for Return Predictability,” *Review of Financial Studies* 25(12), 3457–3489. [DOI](https://doi.org/10.1093/rfs/hhs103) | [Author paper PDF](https://personal.lse.ac.uk/loud/flows.pdf)
- **Claim / mechanism:** Common mutual-fund flows transmit temporary demand shocks across stocks held by the same funds, creating predictability followed by reversal.
- **Data / horizon:** US stocks and mutual-fund flows/holdings from CRSP and Spectrum, 1980–2006; the signal uses flow-induced trading pressure. Effects are reported over quarters and subsequent years, not daily.
- **Magnitude:** Table V reports top-minus-bottom expected flow-induced trading (FIT) returns of 2.52% in the following quarter (t=3.96), 5.28% over the following year (t=2.63), and cumulative −5.67% over years 2–3 (t=−2.17).
- **Large caps / costs / decay:** Historical broad-stock results, not a 2020–26 Dow result; not presented as after-cost evidence. It relies on CRSP/Spectrum holdings and fund flow information unavailable in the confirmed free L4 data.
- **Relevance 3/3; feasibility 1/3.** Directly motivates the network mechanism but makes the unavailable flow/holdings inputs and slower horizon salient.
- **Prediction:** Fund-level demand pressure should move jointly held stocks with a short-to-medium horizon and later reversal; a quarterly 13F ownership graph without fund flows tests only a weaker peer-pressure proxy.

## 19. VERIFIED — Gao, Moulton & Ng (2017), “Institutional Ownership and Return Predictability Across Economically Unrelated Stocks,” *Journal of Financial Intermediation* 31, 45–63. [DOI](https://doi.org/10.1016/j.jfi.2016.07.004) | [Cornell author repository record](https://ecommons.cornell.edu/entities/publication/ad63b492-45a2-4678-9bad-216cf2fe8de0)
- **Claim / mechanism:** Common institutional owners are associated with weekly lead-lag predictability even for firms in different industries without customer-supplier links, consistent with portfolio reallocations transmitting demand.
- **Data / horizon:** US CRSP stocks and 13F institutional holdings, weekly tests over 1980–2010; the Cornell repository abstract states the industry-neutral hedge portfolio earns over 19 bps per week. This is a return-predictability test, not daily buying-pressure measurement.
- **Magnitude:** The repository abstract reports over 19 basis points per week for the industry-neutral long-short portfolio. The accessible abstract does not give a t-stat; none is inferred.
- **Large caps / costs / decay:** The result is not a modern Dow-only or 2020–26 replication and is not stated net of costs. Its 1980–2010 sample reaches the holdout era, but an older strategy result is not evidence of persistence after publication.
- **Relevance 3/3; feasibility 2/3.** Supports a common-owner network even where economic supplier links are absent; SEC 13F is plausible for quarterly topology, but daily propagation and point-in-time mapping remain unverified.
- **Prediction:** Prior pressure in a connected peer portfolio should predict same-direction residual price pressure or returns among common-owner peers over weekly horizons, conditional on own lags and industry/market controls.

## 20. VERIFIED — Pitkäjärvi, Suominen & Vaittinen (2020), “Cross-Asset Signals and Time Series Momentum,” *Journal of Financial Economics* 136(1), 63–85. [DOI](https://doi.org/10.1016/j.jfineco.2019.02.011) | [Authors’ paper PDF](https://assets.super.so/e46b77e7-ee08-445e-b43f-4ffd88ae0a0e/files/8e6baac4-b9ff-4769-9bff-3ed60dca467d.pdf) | [Author page](https://www.helsinki.fi/en/researchgroups/finance/research)
- **Claim / mechanism:** Bond and equity index return trends contain cross-asset information: country bond past returns predict equity returns positively, while equity past returns predict bond returns negatively; the paper interprets this as slow-moving capital/information across markets.
- **Data / horizon:** Monthly international bond and equity index returns, Jan 1980–Dec 2016. Cross-asset and own-asset trend signals use past returns over 1–12 months and are diversified across countries; this is not an ETF-flow or daily pressure result.
- **Magnitude:** Table 3 reports monthly XTSMOM alpha of 0.54% (t=4.32) versus passive bond/equity exposures, and 0.25% (t=3.16) controlling for the corresponding TSMOM and Fama–French–Carhart factors; Panel B gives 0.35% (t=2.69) with value/momentum-everywhere controls and 0.36% (t=3.15) when controlling XSMOM. Gross paper estimates; not our ETF after-cost expectation.
- **Large caps / costs / decay:** Index futures/index data, not individual large-cap stocks. It does not establish daily transmission, and its 1980–2016 result is not a post-publication test. It is an asset-specific design, not a universal signed network.
- **Relevance 2/3; feasibility 1/3 for the specified 30 ETFs.** Provides an asset-appropriate monthly equity-bond template, but the L4-confirmed cross-asset corpus does not cover the full 2010–20 holdout, and equivalent futures/curve/flow data for all asset classes are not confirmed.
- **Prediction:** At monthly horizons, prior bond-index trend should predict equity trend positively, while prior equity-index trend should predict bond trend negatively under the paper’s cross-asset construction; only a matched asset-class sample can test this.

## 21. VERIFIED — Chordia, Roll & Subrahmanyam (2002), “Order Imbalance, Liquidity, and Market Returns,” *Journal of Financial Economics* 65(1), 111–130. [DOI](https://doi.org/10.1016/S0304-405X(02)00136-8) | [Full paper PDF](https://dl.icdst.org/pdfs/files/910bb6cf2390c9809f5ddc743b83ff92.pdf)
- **Claim / mechanism:** Directly signed order imbalance is related to liquidity and returns, but predictive evidence is conditional and does not validate close-location value as signed buying pressure.
- **Data / horizon:** NYSE and S&P 500 stocks, 1988–1998, using Lee–Ready-signed transactions and quote data, not daily OHLCV bars. The paper tests daily market-level order imbalance and return dynamics.
- **Magnitude:** Table 4’s conditional results show negative serial relation after large negative return/imbalance events (reported coefficient estimates include −7.59, t=−2.36 and −8.42, t=−2.59 in the relevant specifications); broad lagged-imbalance forecasting is not robust once contemporaneous imbalance is included. This is conditional reversal evidence, not a general continuation effect.
- **Large caps / costs / decay:** S&P 500 portion provides large-cap relevance; not a costed strategy or post-publication validation. Trade signing requires transactions and quotes unavailable from ordinary daily OHLCV.
- **Relevance 2/3; feasibility 1/3.** Supports caution: CLV is only an intraday price-location proxy; it cannot recover buyer/seller initiation from the bar.
- **Prediction:** If direct negative order imbalance follows a large negative return, test conditional reversal at the next day; do not assign that sign to a CLV-only pressure signal without separate evidence.

## 22. VERIFIED — Harris & Gurel (1986), “Price and Volume Effects Associated with Changes in the S&P 500 List,” *Journal of Finance* 41(4), 815–829. [DOI / Wiley record](https://doi.org/10.1111/j.1540-6261.1986.tb04550.x)
- **Claim / mechanism:** S&P 500 additions induce temporary demand pressure from investors adjusting holdings; an addition is a plausibly non-fundamental demand shock, though index decisions may not be fully uninformative.
- **Data / horizon:** S&P 500 membership announcements and prices/volume, 1973–1983; announcement response and roughly two-week reversal.
- **Magnitude:** Publisher abstract reports >3% post-announcement rise, nearly fully reversed after two weeks.
- **Large caps / costs / decay:** Direct event stocks, not peer spillovers or a modern after-cost result. Historical institutional indexing differs from today's market.
- **Relevance 2/3; feasibility 2/3.** Supports an index event as a pressure shock; current Dow-only event count is the limiting factor.
- **Prediction:** Addition positive and deletion negative around announcement, with reversal over about two weeks; a peer-network effect remains untested.

## 23. VERIFIED — Woolridge & Ghosh (1986), “Institutional Trading and Security Prices: The Case of Changes in the Composition of the S&P 500 Index,” *Journal of Financial Research* 9(1), 13–24. [DOI / Penn State record](https://doi.org/10.1111/j.1475-6803.1986.tb00432.x)
- **Claim / mechanism:** Index-fund portfolio adjustments can create price and volume pressure around index membership changes.
- **Data / horizon:** S&P 500 additions/deletions, 1977–1983; abnormal return on the day after the event and relative trading activity in inclusion month.
- **Magnitude:** Penn State record reports additions positive and deletions negative the following day; relative activity rises in the inclusion month and falls afterward.
- **Large caps / costs / decay:** Event-stock evidence only; no modern peer propagation or transaction-cost result.
- **Relevance 2/3; feasibility 2/3.** Supports a signed event source, not a peer-edge effect.
- **Prediction:** Announcement-linked signed pressure at day +1; test spillover only as a distinct, feasibility-gated extension.

## 24. VERIFIED — Wurgler & Zhuravskaya (2002), “Does Arbitrage Flatten Demand Curves for Stocks?”, *Journal of Business* 75(4), 583–608. [DOI / University of Chicago JSTOR record](https://doi.org/10.1086/341636)
- **Claim / mechanism:** Risk-bearing arbitrageurs do not fully flatten demand when substitutes are imperfect; index inclusion price jumps are larger for stocks without close substitutes.
- **Data / horizon:** Stock inclusion into S&P 500; event price response and cross-sectional substitute availability.
- **Magnitude:** Abstract establishes a comparative result; no unsupported universal bps estimate is used here.
- **Large caps / costs / decay:** Index event stock result; does not estimate connected-peer returns or strategy costs.
- **Relevance 2/3; feasibility 1/3.** Helps explain heterogeneous index pressure but requires identifying substitute sets beyond a small Dow network.
- **Prediction:** Larger positive inclusion shock when close substitutes are scarce; peer spillover is not established.

## 25. VERIFIED — Ramnath (2002), “Investor and Analyst Reactions to Earnings Announcements of Related Firms: An Empirical Analysis,” *Journal of Accounting Research* 40(5), 1351–1376. [DOI / opened bibliographic abstract](https://doi.org/10.1111/1475-679X.t01-1-00057)
- **Claim / mechanism:** First announcers' earnings forecast errors convey information about subsequent announcing firms, but analysts and investors do not fully incorporate it initially.
- **Data / horizon:** Within-industry early and later announcers; analyst forecast revisions and returns in days following the first release. Accessible record omits sample dates, so none are inferred.
- **Magnitude:** Abstract reports predictable subsequent-announcer returns after the first announcement but provides no effect size or t-stat.
- **Large caps / costs / decay:** Event-news evidence, not pressure trading or a net-cost strategy. No modern Dow-only validation was verified.
- **Relevance 3/3; feasibility 3/3.** SEC 8-K events and Dow OHLCV permit a transparent short-horizon version; common-owner weighting is a new extension.
- **Prediction:** Same-sign peer response after an early announcer's good/bad news over subsequent days; possible overreaction must be tested separately.

## 26. VERIFIED — Hameed, Morck, Shen & Yeung (2015), “Information, Analysts, and Stock Return Comovement,” *Review of Financial Studies* 28(11), 3153–3187. [Published DOI](https://doi.org/10.1093/rfs/hhv042) | [opened NBER paper](https://www.nber.org/papers/w15833)
- **Claim / mechanism:** Information about prominent, followed firms can be impounded in same-industry neglected firms that share fundamentals; the empirical spillover is mainly prominent-to-neglected.
- **Data / horizon:** US stocks and analyst coverage; working paper abstract documents stock-specific price fluctuations and forecast revisions in same-industry firms. The NBER version is dated March 2010; journal publication is 2015.
- **Magnitude:** Accessible abstract establishes direction and analyst-coverage heterogeneity, but not an effect size; no figure is invented.
- **Large caps / costs / decay:** Neglected firms are central to the mechanism, limiting transfer to 30 large-cap Dow names. Not a strategy-cost study.
- **Relevance 3/3; feasibility 2/3.** Supports directional peer information flow; SIC/common owner links are available, analyst prominence data are not required for a first design.
- **Prediction:** Positive (negative) prominent-firm information shock predicts same-sign response in connected neglected peers, likely concentrated in short event windows.

## 27. VERIFIED — Thomas & Zhang (2008), “Overreaction to Intra-industry Information Transfers?”, *Journal of Accounting Research* 46(4), 909–940. [DOI / opened Wiley abstract](https://doi.org/10.1111/j.1475-679X.2008.00294.x)
- **Claim / mechanism:** Early-announcer earnings news may be over-extrapolated to late announcers; the induced price response is corrected when the later firm reports its own earnings.
- **Data / horizon:** Early and late industry earnings announcers; late-firm response on early firms' announcement days compared with later response to own earnings news.
- **Magnitude:** Publisher abstract gives the negative relation between peer-day response and subsequent own-announcement response, without a headline effect size.
- **Large caps / costs / decay:** This is direct counterevidence to monotonic peer continuation, not an after-cost result.
- **Relevance 3/3; feasibility 3/3.** A fixed counter-hypothesis and reversal check can be preregistered with SEC event dates and daily prices.
- **Prediction:** Peer reaction can overshoot and reverse by the target's own announcement; omit a peer with a near-term own announcement or report that event separately.

## 28. VERIFIED — Das, King & Pandit (2026), “Are Delayed Earnings Announcements Informative for Peer Firms?”, *Journal of Business Finance & Accounting* 53(1), 435–464. [DOI / open-access article](https://doi.org/10.1111/jbfa.70022)
- **Claim / mechanism:** Late earnings releases transmit less information to peers than timely first releases; leakage and lower industry relevance can explain some attenuation.
- **Data / horizon:** Announcing firms and matched non-announcing peers; three-day peer CAR centered on an earnings release. The opened abstract and methods describe delayed announcements relative to same-quarter prior-year timing.
- **Magnitude:** Abstract reports a 24% attenuation for delayed announcements conditional on still being among the industry's first. The article also reports attenuation is stronger in competitive industries.
- **Large caps / costs / decay:** Peer-event evidence, no net strategy-cost result. Delay classification and industry taxonomy differ from our simple SIC setup.
- **Relevance 3/3; feasibility 3/3.** Confirms event timing and leakage are material design threats.
- **Prediction:** Timely, informative first releases should cause stronger same-sign peer responses than delayed ones; do not pool delayed events without a prespecified indicator.

## 29. VERIFIED — Lou, Polk & Skouras (2019), “A Tug of War: Overnight versus Intraday Expected Returns,” *Journal of Financial Economics* 134(1), 192–213. [DOI / opened author PDF](https://doi.org/10.1016/j.jfineco.2019.03.011) | [PDF](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf)
- **Claim / mechanism:** Overnight and intraday return components proxy different investor clienteles; same-period continuation and cross-period reversal are consistent with persistent demand and opposing trading.
- **Data / horizon:** Broad US stock cross-section and 14 strategies; monthly overnight/intraday components, with persistent patterns extending across signal lags.
- **Magnitude:** Author PDF reports overnight-winner decile three-factor overnight alpha 3.47% monthly (t=16.83) and intraday alpha −3.02% (t=−9.74); intraday winners' results have the opposite session pattern. The authors warn costs reduce implementability.
- **Large caps / costs / decay:** Robust to excluding small stocks and alternative open/close definitions in the paper; trading costs remain a concern. Not a network-spillover test.
- **Relevance 3/3; feasibility 3/3.** OHLCV open/close can form the timing split; applying it along common-owner edges is novel.
- **Prediction:** Overnight pressure continues in subsequent overnight returns and is offset by intraday returns; peer-network version remains a hypothesis.

## 30. VERIFIED — SEC, Form 8-K and EDGAR API documentation. [Form 8-K](https://www.sec.gov/forms/form8-k.pdf) | [EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- **Claim / data definition:** Item 2.02 covers public releases of material results information for a completed quarter or year and requires the release date and text as an exhibit. The submissions API provides free filing histories, updated as filings are disseminated; archive documents allow item verification.
- **Data / horizon:** Official regulatory and infrastructure documentation; no return sample or prediction horizon.
- **Magnitude:** Not applicable.
- **Limitations:** Item 2.02 does not cover every oral-only release; filing acceptance, release timestamp, and first complete tradable session must be aligned conservatively.
- **Relevance 3/3; feasibility 3/3.** SEC metadata and filing text are a free source for dated event construction in both periods.
- **Prediction:** No market prediction; it supports only event identity and public-availability timing.

