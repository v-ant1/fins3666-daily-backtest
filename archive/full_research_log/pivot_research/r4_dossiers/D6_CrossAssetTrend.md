# Dossier 6 — Asset-appropriate equity–Treasury trend transmission

## Pitch and thesis fit

Test the specific monthly equity–bond lead-lag documented in cross-asset time-series momentum, using bond and equity ETFs from the pre-registered 30-ETF cross-asset basket. This is a weaker fit to Advik’s buying-pressure thesis than D4/D5: it uses lagged asset returns as a slow pressure/information proxy, not observed flows or order imbalance, and makes a directional link between unlike instruments rather than a general graph. It is included as a distinct, falsifiable comparison—not as permission to call all cross-asset momentum “network propagation.”

## L1 root causes this addresses

L1’s Dow pressure blend had five-day close-to-close IC +0.0034 (NW t=0.34), while heat was −0.0015 (t=−0.12); same-window symmetric correlation did not identify a transmitting asset. Component CLV briefly showed next-open-to-close IC +0.0142 (t=2.34) at one day, but this does not establish cross-asset or monthly persistence. D6 avoids treating bonds, commodities, currencies and equities as homogeneous nodes and tests only a literature-grounded equity–bond relation. It does not repair the Dow blend or prove short-horizon buying pressure. L1’s top-five cost/turnover failure (161.2% weekly notional, 8.06 bp cost, net Sharpe 0.64 versus EW30 0.92) remains a separate warning if a portfolio is ever considered.

## Mechanism and verified evidence

Pitkäjärvi, Suominen and Vaittinen (2020) find international bond and equity trends carry cross-asset predictive information: bond past returns predict equity returns positively, and equity past returns predict bond returns negatively. Their tests are monthly and based on international indexes, not flows or this project’s ETFs. Moskowitz, Ooi and Pedersen (2012) document own time-series momentum over 1–12 months across futures in equities, bonds, commodities and currencies. Neither paper implies daily ETF pressure diffusion or a common network across every asset class.

- Pitkäjärvi, Suominen & Vaittinen (2020), “Cross-Asset Signals and Time Series Momentum,” *Journal of Financial Economics*: [DOI](https://doi.org/10.1016/j.jfineco.2019.02.011), L3 Card 20. The opened author PDF’s Table 3 reports monthly XTSMOM alpha 0.54% (t=4.32) versus passive bond/equity exposures and 0.25% (t=3.16) controlling for corresponding TSMOM plus Fama–French–Carhart factors; those are gross historical results, not project expectations.
- Moskowitz, Ooi & Pedersen (2012), “Time Series Momentum,” *Journal of Financial Economics*: [DOI](https://doi.org/10.1016/j.jfineco.2011.11.003), L3 Card 13. The paper covers 58 futures/forwards; own trend is documented at 1–12 months, with longer-horizon partial reversal.
- Cross-asset limitation: Greenwood & Vayanos (2014), L3 Card 14, shows maturity-specific bond-supply effects; this is not a generic ETF-flow proxy. D6 does not introduce duration/curve variables absent confirmed data.

## Exact signal and network

Use the pre-registered xasset ETF basket, with TLT as the U.S. Treasury bond source and IWM as the U.S. equity recipient (both are within the listed basket). At each month-end, calculate each ETF’s trailing 12-to-1-month total return using only adjusted data known at that date; no daily signal or rebalance. Primary transmission predictor: TLT’s prior 12-month return, skipping the most recent month, forecasts IWM’s next-month return **positively**. The reverse cross-asset prediction is predeclared separately: IWM’s prior 12-month return forecasts TLT’s next-month return **negatively**, matching the paper’s equity-to-bond sign. Include each target’s own prior trend and broad market/rate controls available in the same ETF panel. The network is a two-node directed relation, TLT→IWM and IWM→TLT with opposite predicted coefficients—not a learned correlation graph. This is return-based trend, not a direct measure of investor pressure; ETF total returns do not recover Treasury duration supply, commodity roll yield or FX carry.

Before future returns are inspected, confirm the xasset files use consistent split/distribution-adjusted total-return conventions and that TLT/IWM monthly histories overlap all required formation dates. L4’s latest `NETWORK_DATA.md` does not inventory the xasset return panel or confirm its adjusted-price convention. It confirms that SEC N-PORT ETF holdings begin 2019-10, which is insufficient to build full 2010–20 holdings links. D6 does not require holdings if kept as the fixed two-index return-lead-lag, but it does require comparable point-in-time ETF return history.

## Prediction and mechanism test

**Prediction:** positive lagged TLT trend predicts positive IWM next-month return; positive lagged IWM trend predicts negative TLT next-month return. These are monthly paper-based signs, not daily. Use the monthly predictive slopes and NW inference appropriate to non-overlapping monthly observations (lag 0 for one-month outcomes), with each target’s own trend in the regression. Require the signs and NW t≥2 for a predeclared primary direction and no comparable cross-lag placebo. Report both asset directions even if one fails.

**Placebos:** (1) reverse the asset-pair direction while keeping the same signal and outcome timing, (2) shuffle TLT/IWM month alignment in blocks while preserving each series’ autocorrelation, (3) compare cross-asset trends against each target’s own trend-only baseline. A similar coefficient for shuffled/reversed links falsifies transmission. No parameter search over additional ETF pairs, lookbacks or holding periods.

## Portfolio design after the mechanism gate

Only after a mechanism pass, use a fixed monthly two-ETF long-only allocation: hold 50% IWM when lagged TLT trend is positive, and 50% TLT when lagged IWM trend is negative; hold the remainder as cash. These positions follow only the paper-grounded positive conditional-return directions and do not extend the relation to unrelated FX/commodity ETFs. Against EW30 over the same 30 ETFs, the two-name allocation has active share above 50%; report the exact holdings-based active share before any portfolio result. Rebalance monthly at the first session after the signal is public; cap total traded notional at 50% per rebalance or stop unless actual costs stay below one quarter of gross edge. The portfolio is secondary; it cannot rescue a failed cross-asset mechanism test.

## Variants and selection rule

Maximum three predeclared tests, not a sweep:

1. **Primary:** TLT 12-to-1-month return → IWM next-month return, positive.
2. IWM 12-to-1-month return → TLT next-month return, negative.
3. Target own-trend-only model as the comparison baseline; it cannot count as support for a cross-asset network effect.

The primary D6 conclusion requires variant 1’s sign/inference and a null block-shuffled alignment placebo; variant 2 is reported as its own prespecified secondary direction, never used to replace a failed primary, and variant 3 only measures incremental predictive contribution. No other ETFs, frequencies or windows may be substituted after observing results.

## Strongest objection and falsifier

The evidence is monthly index-level/futures evidence, while these are ETFs with duration, tracking, distribution and ETF-specific effects; TLT/IWM is not the same-country broad index pair in the source sample. Trends could proxy inflation/risk regimes rather than transmitted buying pressure. Data history and total-return adjustments for the exact basket are not confirmed by L4. The weakest evidence is the extrapolation from international index trends to a two-ETF relationship as a pressure-spread thesis. Falsify if TLT’s lagged trend does not add positive next-month IWM prediction after IWM’s own trend/common controls, or if block-shuffled alignment is comparable. A return-trend result alone cannot be reported as proof of order-flow pressure.

## Feasibility, effort and risk

Scores: 1=low, 5=high; effort and risk worsen as scores rise. **Development feasibility 2/5:** files for the xasset project corpus exist, but L4 has not confirmed their full adjusted-price coverage or conventions, and this design is monthly rather than daily Dow pressure. **Holdout feasibility 1/5:** no full 2010–20 cross-asset ETF total-return panel is confirmed in L4; the ETF holdings route cannot supply it, and this dossier must not use sealed country-ETF holdout tickers. **Effort 2/5; risk 4/5.** The user must confirm xasset ticker-history, adjusted-return convention and allowed instruments before any development test. D6 is not recommended for the current two-period requirement unless a compliant complete history is documented.

