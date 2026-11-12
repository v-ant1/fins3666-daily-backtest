# Independent red-team: U COT positioning × issuer exposure

**Verdict: KILL.** The futures-positioning literature and free weekly source are real, and an ex-ante issuer map is possible in principle. The proposed stock-level mechanism is not identified by COT: CFTC categories are aggregate futures traders, not the Dow issuers with a hedge or commodity exposure; the proposed power calculation treats a broad stock cross-section as if it supplied hundreds of independent pressure units; and the likely issuer map collapses to a few shared commodity/industry shocks. The economically plausible piece is commodity exposure / earnings sensitivity, which is distinct from evidence that COT buying pressure persists or spreads through a network of related stocks.

I reviewed only the design in `r6_ideas/U_crossasset.md`, its stated development-window COT count (309 report dates, 29 commodity names), source documentation, and SIC/sector concepts. I did not inspect COT position magnitudes, calculate signals, open stock returns, or access holdout data.

## Gate (a): papers verified, but external validity is weak

- De Roon, Nijman and Veld, [“Hedging Pressure Effects in Futures Markets,” *Journal of Finance* 55 (2000), 1437–1469](https://doi.org/10.1111/0022-1082.00253), tests hedging pressure across futures markets and reports relations with futures returns and some underlying-asset returns. It does not test COT-to-Dow-stock continuation.
- Fan, [“Speculative pressure,” *Journal of Futures Markets* 40 (2020), 1373–1399](https://doi.org/10.1002/fut.22085), studies speculative-position premia in commodity, currency, and equity-index futures. It supports futures-market pressure as a construct, not a cross-sectional individual-stock effect.
- Wang, [“Measurement errors in index trader positions data: Is the price pressure hypothesis still invalid?” *Applied Economic Perspectives and Policy* (2022)](https://doi.org/10.1002/aepp.13186), is a relevant counterweight: correcting measurement error does not find significant true index-trader-position effects for the commodities examined.

**Assessment:** the literature gate passes only in the narrow sense that futures positioning can be related to futures prices. It does not establish the proposed equity mechanism or sign. The CFTC says trader categories are based on predominant business purpose reported on Form 40, but positions in a category need not be taken for that purpose; it also does not publish identities or how an individual trader is classified. See the CFTC’s [COT description and FAQ](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm). That prevents attribution of observed aggregate positioning to a Dow company’s actual hedge.

## Gate (b): issuer exposure map can be frozen, but SIC alone is too blunt

An ex-ante map need not peek at outcomes. A defensible process would freeze an issuer-to-commodity table using only information public before each formation: CIK-linked 10-K/10-Q business descriptions, segment disclosures, and explicit commodity sensitivities. Rules would need to be specified before returns are touched, with filing acceptance time as availability; exposures, directions, and reporting-date changes would be coded independently of returns. This could support a descriptive exposure map.

However, simply mapping NAICS/SIC2 to “producer,” “merchant,” or “user” is not a point-in-time company hedge map. It creates broad sector buckets, includes firms with no material commodity exposure, misses conglomerate-specific segment differences, and cannot distinguish whether a firm is a net buyer or seller of futures. Manual filing coding is feasible but requires a documented rulebook, adjudication, explicit “unknown” labels, and a minimum-coverage rule. The proposal does not yet provide those rules or coverage counts for Dow issuers.

More fundamentally, COT itself does not disclose which firms or traders generated the category position. Multiplying a commodity-wide position by a guessed set of issuer exposures produces a common macro exposure shock, not observed pressure transmitted from a source asset through related equities. SIC2 stratification for an S&P mechanism test does not solve this ecological attribution problem.

**Assessment:** potentially buildable as ex-ante issuer *sensitivity* to commodity prices, but not as a verified map from COT trader pressure to issuer-specific buying pressure. No equity outcomes are needed to make that distinction.

## Gate (c): original power assumes too many independent exposure units

The proposal’s stated `power_sim` call uses 500 stocks, 309 weekly dates, horizon 5, serial correlation 0.5, `IC_SD=0.10`, and planted mean IC 0.02. That produces 64.16% simulated probability of NW t ≥ 2, an 80% MDE of 0.0241, and effective time-series sample size about 138.9. These results are internally consistent with the provided assumptions, but 500 is not the relevant independent breadth when a common COT shock is multiplied by a small number of commodity-specific exposures.

The design has 29 named commodity markets in the coverage count, but that is not 29 independent equity-pressure clusters: several markets share commodity complexes and the Dow’s mapped issuer exposure is likely concentrated in a few groups such as energy, materials, industrial inputs, and transport/consumer users. We do not yet know the actual issuer map, so treat effective clusters as a sensitivity, not a measured fact. Using `power_sim.py` with the same 309 dates, horizon 5, autocorrelation 0.5, planted effect 0.02, 5,000 draws and seed 20261111, but treating 10 or 6 independent exposure buckets as the effective cross-section gives:

| Assumed effective independent exposure buckets | IC noise SD (`1/sqrt(K-1)`) | Power for NW t ≥ 2 | 80% MDE |
|---:|---:|---:|---:|
| 10 | 0.333 | 13.64% | 0.0804 |
| 6 | 0.447 | 10.82% | 0.1078 |

Even the six-bucket stress case still treats dates as informative independent shock realizations except for the assumed AR(1) correlation and ignores common commodity-cycle regimes, overlap among issuer maps, repeated/shared market shocks, and estimation error in the hand-coded exposures. The effective cross-section is not 500 independently shocked names. The candidate therefore fails the power gate at the proposed planted effect; the original 64% is too optimistic to rely on.

## Gate (d): release schedule and executable timing

The CFTC’s [release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm) says COT is released at **3:30 p.m. Eastern**, usually Friday, and the report generally describes the previous Tuesday’s positions; holidays can delay publication one or two days. The CFTC’s [report overview](https://www.cftc.gov/MarketReports/CommitmentsofTraders/AbouttheCOTReports/index.htm) confirms weekly Futures-Only and Futures-and-Options-Combined reports are released Friday at 3:30 p.m. ET. Thus the report date is not a tradable timestamp.

For ordinary U.S. equity sessions, 3:30 p.m. ET is only 30 minutes before the 4:00 p.m. cash close. The proposal’s signal must not be dated Tuesday or entered at Tuesday prices, and a Friday-close entry would assume robust parsing, dissemination, and execution in that narrow window. The clean rule is to use the actual publication timestamp and enter at the next regular-session open (normally Monday, subject to market/CFTC holidays), then define the one-week holding horizon from that open. This delays the signal further and weakens the story of anticipating the market response. The stated CFTC data count is an input-availability count only; no position sizes were viewed.

There is also a current timing change to track: on 27 October 2026, the CFTC announced a plan to move some agricultural COT reporting to twice weekly by year-end, with Monday positions published Wednesday and Wednesday positions on Friday. The announcement describes an intended rollout, not a historical schedule change for the six-year development sample; only the CFTC’s eventual market-specific schedule should govern any future timestamps. See [CFTC Release 9316-26](https://www.cftc.gov/PressRoom/PressReleases/9316-26).

**Assessment:** free COT coverage and the standard historical calendar are feasible; a correctly timed live rule is Monday/next-session open, not backdated Tuesday or assumed Friday close. Correct execution timing further attenuates the proposed signal’s timeliness.

## Gate (e): novelty and thesis fit fail

**Novelty:** using CFTC positions rather than ETF holdings is a different source from ETF-flow tests, and it is not the rejected daily short-sale-volume proxy. That is a source distinction, not enough for a new thesis mechanism. The proposed link still takes a common market-wide pressure measure, multiplies it by issuer holdings/exposure, and predicts a cross-section. It is close to the earlier macro-flow / sector-response proposals. Without individual trader identities or issuer-linked futures trades, it cannot establish that buying pressure in one asset spills to a related stock. The proposal’s claim of a network effect is overstated.

**Thesis fit:** commodity futures positions measure outstanding net exposures, not necessarily current signed trades or buying pressure in the stock. Weekly changes may capture hedging, new information, supply expectations, or position reclassification; CFTC category labels do not identify motive. A commodity shock may affect issuer cash flows through costs or revenues, but that is a commodity-beta / earnings-sensitivity mechanism. It is not direct evidence of persistent stock demand or pressure propagating through a network. Because COT position movements can reflect informed commodity views, the predicted equity sign may also vary by shock type and producer-versus-user status; the proposal currently risks choosing those directions after seeing results.

## Decision

**KILL, do not freeze or test.** The cited literature supports pressure in futures, and the exposure panel could be authored without outcome peeking if the rules were frozen first, but COT categories do not identify issuer hedge trades; SIC-only mapping yields a small number of dependent exposure clusters; the candidate fails a conservative power sensitivity; actual release timing requires next-session execution; and the signal is more naturally a macro commodity-exposure factor than Advik’s measurable, spreading buying-pressure thesis. A future redesign would need a prespecified, filing-coded issuer map and a genuinely observable issuer-linked flow source, followed by power based on the resulting exposure clusters. That would be a materially different data design, not a reason to advance this candidate as written.
