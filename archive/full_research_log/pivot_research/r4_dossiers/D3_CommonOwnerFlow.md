# Dossier 3 — Mutual-fund demand through common ownership

## Pitch and thesis fit

Estimate when mutual funds are likely to buy or sell existing holdings because of investor flows, then test whether that pressure is concentrated in the same stocks and transmitted across stocks sharing those fund owners. The primary hypothesis is that expected flow-induced buying predicts positive returns while it is being deployed; a separate forced-fire-sale event is expected to fall during the selling and recover later. This preserves pressure plus a common-owner network, but uses a slow monthly/quarterly signal rather than pretending 13F holdings are daily trading records.

## L1 root causes this addresses

L1 found a mixed-sign pressure blend (five-day IC +0.0037, t=0.38; signed-volume components often reverse), and an undirected co-movement graph with heat IC −0.0017 (t=−0.14). D3 directly measures institutional flow demand and builds shared-holder links, addressing root causes 1–2. The pre-portfolio event/predictive test addresses root cause 3. Quarterly flows and slower rebalancing may help with root cause 4, but actual turnover is unknown. The narrow 30-name sample and small effective breadth remain root cause 5. L1’s baseline was 161.5% turnover and 8.07 bp cost per weekly rebalance vs EW30’s 2.4% and 0.12 bp; its postmortem estimates ~0.0127 weekly IC to cover incremental cost, while the CSV says 0.00605. Reconcile these before any cost-based selection; neither is a universal threshold for D3.

## Mechanism and evidence

Coval and Stafford show forced fund-flow sales in shared holdings can create temporary price pressure; Lou shows expected flow-induced trading predicts returns during deployment and reverses over longer subsequent horizons. Antón and Polk show shared active ownership links stocks through excess comovement and cross-stock reversal; Greenwood and Thesmar supply a fragility mechanism for correlated fund-liquidity shocks. These studies motivate distinct stage-specific predictions rather than one blended pressure sign.

- Coval & Stafford (2007), “Asset Fire Sales (and Purchases) in Equity Markets,” *Journal of Financial Economics*: [DOI](https://doi.org/10.1016/j.jfineco.2006.09.007). **Verified/corrected in L2 card 4 and citation audit**: forced-sale stocks fell 7.90% in the event quarter and rebounded 6.13% over the next 12 months (Table 4); only 18 quarterly event groups supported conservative grouped inference.
- Lou (2012), “A Flow-Based Explanation for Return Predictability,” *Review of Financial Studies*: [DOI](https://doi.org/10.1093/rfs/hhs103). **Verified/corrected in L2 card 5 and citation audit**: expected-FIT deciles gained 5.28% (t=2.63) in the following year and lost 5.67% (t=−2.17) over the next two years.
- Antón & Polk (2014), “Connected Stocks,” *Journal of Finance*: [DOI](https://doi.org/10.1111/jofi.12149). **Verified L3 card 3 and citation audit.** The L3 audit corrects the published Table V result to 76 bp/month (t=4.96); this dossier does not assume that broad-universe portfolio result carries over to Dow stocks.
- Greenwood & Thesmar (2011), “Stock Price Fragility,” *Journal of Financial Economics*: [DOI](https://doi.org/10.1016/j.jfineco.2011.06.003). **Verified L3 card 4.**

## Exact signal and network

Use fund net flows and point-in-time fund holdings. For fund `f`, define monthly flow rate from total net assets and fund return as `g_f,m = [TNA_f,m − TNA_f,m−1 × (1+r_f,m)] / TNA_f,m−1`. Before month `m`, estimate the expected flow rate `ĝ_f,m` from an expanding fund-panel regression of past monthly `g` on lagged 12-month fund excess return, requiring 36 prior monthly observations; this is a single fixed Lou-style performance-chasing specification, not a parameter sweep. At the date the inputs are actually public, compute expected dollar demand for stock `i` as `EFIT_i,m = Σ_f [TNA_f,m−1 × ĝ_f,m × h_f,i,m−1] / MktCap_i,m−1`, where `h` is the latest disclosed stock portfolio weight. Actual realized `FIT_i,m` uses `g_f,m` instead of `ĝ_f,m` and serves as a baseline/event measure. Timestamp each flow and holdings record; when either input is not public, do not use it.

Build common-owner stock edges as `A_i,j,m = Σ_f [TNA_f,m−1 × h_f,i,m−1 × h_f,j,m−1]` for i≠j and row-normalize to `W`. The primary network-pressure signal is `NFP_i,m = Σ_j W_i,j,m−1 × EFIT_j,m`; also retain own `EFIT_i,m` so network spillover must add predictive information beyond direct expected demand. This is a shared-holder exposure network, not a directional causal edge; direction is tested through lagged source expected flow and recipient return. No same-quarter holdings that became public later are backfilled.

L4 found [SEC 13F](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets) data are free and public, quarterly and filed up to 45 days after quarter-end; structured datasets start 2013 Q1, with earlier filings requiring separate archive scraping. L4 pulled one development-period filing (Jan 2026) but did not parse holdings. 13F omits shorts and some positions and does **not** contain the needed fund flow/TNA series. Standardized mutual-fund flows likely require FactSet/Morningstar access, not confirmed for the team; [UNSW lists FactSet](https://www.unsw.edu.au/business/our-research/research-environment/databases), but entitlement to this module is unconfirmed. Thus development data availability is **partial and unproven for the combined signal**.

**Holdout replicability:** Structured 13F begins in 2013, leaving 2010–12 dependent on separate historical-filing scraping; point-in-time flow/TNA panel and identifier mapping were not verified. Dow returns for KFT, DWDP and WBA are unresolved from Yahoo; RTX is a proxy for UTX. Complete holdout replication requires both flow/holdings coverage and resolution/approval of those security windows. The L4 exposure of DWDP rows requires any later holdout result be reported with and without that window; this dossier’s author has not accessed holdout values.

## Prediction, tests and portfolio

Primary prediction: positive expected `NFP` predicts positive recipient returns over the next month while forecast flows are being deployed; negative expected pressure predicts lower returns. As demand dissipates, the medium-term prediction turns negative; Lou’s result motivates a prespecified 12–24-month unwind, not a claim that this long-horizon effect is short-term. Test monthly rank IC of `NFP` versus next-month residual returns, controlling for own `EFIT`, market and industry returns, and direct holdings exposure. Report 1- and 3-month horizons as prespecified secondary horizons; use Newey–West with lag 2 for the 3-month overlapping series and Holm across all registered horizons/variants. The event-stage corroboration is that extreme realized forced selling predicts a negative contemporaneous return and positive post-event 12-month recovery, consistent with Coval–Stafford; do not select sign/horizon after results.

**Placebos:** Shuffle fund holdings among stocks within sector/size bins while preserving portfolio sizes and fund flow series; shift flow dates forward one quarter; randomize common-owner links preserving node degree. If shuffled or future links predict similarly, the network mechanism fails.

**Portfolio after mechanism gate:** At each public monthly/quarterly update, long top five and short bottom five stocks by frozen `NFP`, equal-weight, dollar-neutral; do not rebalance between disclosures unless a new flow/holding update is public. This is a distinct long-short portfolio. A five-stock long-only alternative has approximately 83% active share vs EW30. Expected turnover is unknown; the low-frequency signal suggests fewer trades but does not guarantee turnover ≤50%. Set that as a hard cap; if turnover exceeds it, require actual trading costs below one quarter of the gross edge or stop. L1’s 7.95 bp incremental weekly cost and ~0.0127 break-even IC are stress benchmarks only, not a conversion for a quarterly fund-flow signal; reconcile the `cost_analysis.csv` 0.00605 discrepancy before translating break-even.

## Variants and selection rule

1. Realized published mutual-fund flow `FIT` × latest disclosed holdings (baseline/event measure).
2. Lou-style expected flow-induced trading `EFIT` from lagged fund excess return, using only data available before formation.
3. Primary thesis test: shared-owner network signal `NFP` from neighboring `EFIT`, tested incrementally above own `EFIT`.

Variant 3 is the thesis test; variant 1 is its realized-flow baseline and variant 2 its direct expected-flow predictor. All three must use fixed filing timestamps and no backfilled holdings. They are not ranked by portfolio return. Select only the predeclared primary network definition if its incremental predictive coefficient has the predicted sign, NW t≥2 after Holm, and shuffled-link/timing placebos are null; otherwise stop. If fund flow history cannot be sourced before outcome access, mark the dossier infeasible rather than substituting 13F holdings changes for fund flows.

## Strongest objection and falsifier

The strongest objection is data and horizon mismatch: 13F is delayed quarterly holdings, not daily trades or fund flows, while Lou’s strongest result unfolds over annual and multi-year horizons. Coval–Stafford’s 12-month rebound is based on a small set of extreme event quarters, not a daily Dow effect; a later Chilean pension-flow experiment reports the recovery only after four to six months, not immediately. These estimates are not proof of a short-horizon edge after 5 bp/side costs. Falsify D3 if reported flow shocks do not have the predicted sign after publication, if neighbor flow adds nothing beyond own flow, or if shuffled holdings/future flow reproduce the result. The tradable version fails if turnover costs erase its edge.

## Feasibility, effort and risk

Scale: 1=low, 5=high. **Feasibility 2/5** (SEC holdings source exists, but unparsed and fund-flow series/holdout panel unconfirmed); **effort 5/5** (point-in-time filings, fund identifier/security mapping and flow data); **risk 5/5** (sparse extreme events, slow data and uncertain short-horizon effect). Recommendation: retain as a conditional comparison only if licensed flow data is confirmed before preregistration.
