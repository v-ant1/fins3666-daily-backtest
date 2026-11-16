# Dossier 4 — Common-owner peers and daily close-location pressure

## Pitch and thesis fit

Test whether daily pressure at one Dow stock predicts next-session pressure/returns among stocks sharing disclosed institutional owners. This preserves Advik’s network-spread thesis, replaces the same-window return-correlation graph with a filing-dated common-ownership graph, and replaces the mixed pressure blend with close-location value (CLV), the strongest single OHLCV component in L1’s short-horizon diagnostic. It is explicitly a proxy test: OHLCV CLV is not signed order flow, and quarterly holdings do not reveal daily institutional trades.

## L1 root causes this addresses

L1’s five-day pressure blend had close-to-close IC +0.0034 (NW t=0.34); heat had −0.0015 (t=−0.12), and the plain neighbor average −0.0034 (t=−0.29). The blend dilutes components with conflicting signs: signed volume was negative, while CLV and intraday-minus-overnight were positive. CLV’s next-open-to-close IC was +0.0142 (t=2.34) at one day and +0.0142 (t=2.05) at two days; the evidence weakened by five days (+0.0132, t=1.40). D4 tests this brief, component-level signal against a plausible graph and a next-session recipient response, rather than claiming the old heat result worked.

D4 addresses root causes 1–3 (mixed pressure signs, a graph that measures co-movement rather than transmission, and portfolios before mechanism tests). It does not solve the 30-name breadth limitation or prove low turnover. L1’s top-five heat portfolio traded 161.2% of NAV per weekly rebalance, cost 8.06 bp, and ended with net Sharpe 0.64 versus 0.92 for EW30; EW30 turnover/cost were 2.4% / 0.12 bp. A new network signal must pass a mechanism gate first and a strict cost/turnover gate later.

## Mechanism and verified evidence

Antón and Polk find that active mutual-fund common ownership links stocks’ return comovement and reversal, with stronger effects in large stocks than some other network studies. Gao, Moulton and Ng report weekly lead-lag predictability across economically unrelated firms only when they share institutional owners. Coval–Stafford and Lou provide flow-based mechanisms, but their fund-flow measures are not captured by our delayed 13F graph. These are historical, mostly broader-universe results; none establishes daily CLV transmission among current Dow names.

- Antón & Polk (2014), “Connected Stocks,” *Journal of Finance*: [DOI](https://doi.org/10.1111/jofi.12149), L3 Evidence Card 3. Published Table V reports 76 bp/month (t=4.96) for its five-factor alpha specification; its monthly active-mutual-fund strategy is not a daily CLV strategy.
- Gao, Moulton & Ng (2017), “Institutional Ownership and Return Predictability Across Economically Unrelated Stocks,” *Journal of Financial Intermediation*: [DOI](https://doi.org/10.1016/j.jfi.2016.07.004), L3 Evidence Card 19. Cornell’s opened abstract reports over 19 bp/week for an industry-neutral portfolio over 1980–2010; its accessible abstract gives no t-stat.
- Coval & Stafford (2007), “Asset Fire Sales (and Purchases) in Equity Markets,” *Journal of Financial Economics*: [DOI](https://doi.org/10.1016/j.jfineco.2006.09.007), L3 Card 17; Lou (2012), “A Flow-Based Explanation for Return Predictability,” *Review of Financial Studies*: [DOI](https://doi.org/10.1093/rfs/hhs103), L3 Card 18.
- Negative/proxy evidence: Chordia, Roll & Subrahmanyam (2002), “Order Imbalance, Liquidity, and Market Returns,” *Journal of Financial Economics*: [DOI](https://doi.org/10.1016/S0304-405X(02)00136-8), L3 Card 21. Direct signed imbalance requires trades and quotes; daily OHLCV cannot identify aggressor side.

## Exact signal and network

Use the L4-built, public-filing-dated common-owner cosine overlap edges. For each date, use the latest quarterly overlap panel only after its recorded `panel_availability_date` (the latest filing among the contributing managers), and hold that graph until the next usable filing-date panel. Define source pressure `CLV_j,t=(2C_j,t−H_j,t−L_j,t)/(H_j,t−L_j,t)`, set it to zero when `H=L`, and use only daily OHLCV. At the close of day *t*, define recipient network pressure `NP_CLV_i,t = Σ_{j≠i} W_{ij,q(t)} CLV_j,t`, with row-normalized cosine weights and no self-edge. Evaluate the next session’s open-to-close residual return (and next-session CLV as a mechanism outcome) after controlling for recipient own CLV, its own lagged return, broad market return. Add a sector/industry control only if point-in-time classifications are confirmed; current SIC is not a valid historical control. Keep the latest publicly observable graph; never backfill quarter-end holdings to the filing date.

L4’s `NETWORK_DATA.md` confirms 54,739 position rows for 36 Dow tickers, 10 reporting entities, and a quarterly panel from 2020Q2 to 2026Q2, plus 9,450 undirected pair observations. Its ten-filer sample is explicitly not the full institutional ownership universe or a verified top-AUM ranking; coverage varies by quarter. The latest panel does not automatically cover the final 2026 development dates, so carry forward only the last public graph and report its age. L4 did not compute returns/signals in this network build.

## Prediction and mechanism test

**Prediction:** positive peer CLV at day *t* predicts positive recipient residual open-to-close return and/or CLV on day *t+1*. Use that one-session horizon as the primary test because L1’s CLV evidence is brief and fades by five days; do not claim that fund-flow papers establish this specific sign/horizon.

First test the date-level cross-sectional slope/rank-IC from `NP_CLV_t` to next-session recipient outcome, conditional on own pressure and common returns. Use Newey–West lag 0 for the non-overlapping one-session primary series; if the implementation creates overlapping observations, define the overlap rule before testing and use the matching NW lag. Require predicted positive sign and NW t≥2, and require the shuffled-link placebo to be insignificant. Report coverage by filing panel, manager and calendar segment. Mechanism and predictive test precede any portfolio.

**Placebos:** (1) degree-preserving random rewiring of the common-owner network; (2) future filing-panel links as a timing placebo (only where filing timestamps make that comparison valid); (3) own-pressure-only and same-sector peer controls. If random links predict similarly, the ownership topology adds no evidence. A matched sector placebo should be used only if a point-in-time industry label is available; do not use today’s SIC retrospectively.

## Portfolio design after the mechanism gate

If, and only if, the primary mechanism test passes, rank the 30 stocks by the frozen `NP_CLV` and hold the equal-weight top five long, rebalanced weekly at next-session open. Versus EW30 this has approximately 83% active share (well above the 50% floor). Do not use a long-short portfolio as a substitute if the long-only test fails. Cap total traded notional at 50% of NAV per rebalance; if that cannot be met, proceed only if measured costs are below one quarter of gross active edge. No turnover or alpha is claimed before running an authorized test.

## Variants and selection rule

Maximum of three fixed variants, all recorded before joining future returns:

1. **Primary:** L4 cosine-overlap edges × one-day peer CLV.
2. Binary adjacency (at least one common reporter with a nonzero position) × one-day peer CLV, as a network-weighting sensitivity only.
3. L4 cosine-overlap edges × peer intraday-minus-overnight return, as a separate OHLCV pressure proxy.

Variant 1 is the only selection statistic. Variants 2–3 are diagnostic and cannot rescue a failed primary by their relative performance. The same one-session horizon and placebo procedure apply; no parameter sweep.

## Strongest objection and falsifier

The network covers only ten filers, positions rather than trades, and quarterly disclosure lag. The overlap may reflect passive diversification or common factor exposure, and the 30-name subset can have too few independent edges/effective observations. The cited effects are monthly/weekly and largely pre-2020; extrapolation to daily close-location pressure in Dow megacaps is the weakest link. Falsify D4 if the filing-dated cosine peer CLV has no positive incremental one-session predictive association after own/market controls, or if degree-preserving random links are comparable. Also stop if the point-in-time graph is stale/missing for too much of the development sample or the portfolio cannot meet the turnover/cost gate.

## Feasibility, effort and risk

Scores: 1=low, 5=high; effort and risk worsen as scores rise. **Development feasibility 3/5:** L4 confirms OHLCV and an actual dated 13F panel for 2020Q2–2026Q2, but the manager sample is incomplete, position mapping varies, and the latest panel predates the final development dates. **Holdout feasibility 2/5:** L4 says same 13F construction is possible in principle from historical SEC filings, but 2010–20 filing parsing/CUSIP lineage and complete holdout prices have not been built; KFT, DWDP and WBA have zero Yahoo rows, and UTX uses an RTX proxy. **Effort 3/5; risk 4/5.** Before either period is authorized, the user/coordinator must confirm whether the ten-filer universe is acceptable, approve sourcing/constructing 2010–20 filing-dated positions, and resolve the holdout price-lineage route. Report the exposed DWDP window with and without it if any later holdout run is approved.

