# R6 Idea Screen AK — sector ETF primary-market creation pressure

**Verdict: STOP — FAIL. Do not register a variant or start a runner.** Daily sector-SPDR creations could force authorised participants to acquire underlying stocks, creating a direct buying-pressure channel. The date-filtered development inputs contain all 11 ETFs' prices and volumes, but no verified daily share-outstanding history or point-in-time holdings-weight panel; the literature supports ETF-level predictability and constituent liquidity/volatility effects, not a post-2020 Dow weekly rank IC. Power is acceptable only under the implausible assumption that all 11 sector shocks are independent, and the published effect sizes cannot be translated to the fixed Dow portfolio hurdle.

This is a screen only. I did not calculate signals, forward returns, ICs, portfolio returns, or other project outcomes, and did not inspect holdout data or `specs/r6_holm_family.json`.

## Identity and immutable-path preflight

- **Proposed short name / mechanism:** AK, primary-market sector rotation pressure. A net creation in one of the 11 Select Sector SPDRs may induce basket purchases by an authorised participant; map the creation dollars through each stock's last-known sector-fund weight to measure constituent-level buying pressure.
- **Exact new output path:** `r6_ideas/AK_sector_rotation.md`.
- **Target preflight:** the exact target path did not exist before this screen; no file was overwritten.
- **Prior-name check:** AK is assigned to this sector-rotation flow concept in the decision registry; the exact artifact name is new.
- **Development date range / earliest allowed worker-path date:** 2020-11-27 through 2026-10-30; earliest permissible date is **2020-11-27**.
- **Path/data safety:** the only project-data read was a PyArrow dataset query with `date >= '2020-11-27'`, restricted to the 11 ETF ticker and `date`,`ticker` columns. No earlier rows were materialized; no project return fields or holdout path were read. The listed date range is the allowed development window only.
- **Verdict:** PASS for output-path and date-bound preflight.

## 1. Overlap with prior work

The closest screen is **Round H, Direction 1**: it used a trailing close-location-value × volume-surprise measure on the 11 sector SPDRs and gave sector constituents common scores. H failed because inference depended on treating as many as 11 sector shocks as independent, the large-cap evidence was weak, and staged data had neither actual creations/redemptions nor a point-in-time sector-to-fund mapping. H's Direction 2 used DIA, a single source series, and did not produce a stock ranking. `R5_FINAL.md` also reports that the earlier ETF-flow proposal could not verify daily shares histories beyond SPY and DIA and had only quarterly N-PORT holdings for its broader constituent map.

AK changes the input mechanism: it proposes **actual primary-market share creation/redemption** rather than secondary-market ETF OHLCV as a flow proxy, and weights each stock by its lagged, pre-formation sector-SPDR portfolio weight. That is a genuine signal-definition change, not just a renamed H signal. But AK remains closely related to H and the R5 ETF-flow screen: it has the same 11 sector-level source shocks, needs a historical constituent map, and cannot claim 30 independent signals because it maps a small set of fund flows to many stocks. The distinction would only matter if the proposed issuer data and point-in-time holdings were actually available.

- **Verdict:** PASS for a distinct mechanism; substantial shared cluster and data-identification limitations remain.

## 2. Exact pressure measure and dated data source

### Candidate signal (one design only)

For each sector fund `s` and session `d`, define estimated dollar creation/redemption as:

`flow_dollars[s,d] = (shares_outstanding[s,d] - shares_outstanding[s,d-1]) * NAV[s,d-1]`.

An increase is positive creation pressure and a decrease is negative redemption pressure. For point-in-time Dow issuer `i` at a Friday close, define its score as the sum of the last five **available** complete daily fund flows, allocated by the stock's most recently public sector-SPDR portfolio weight strictly before each flow date, and scaled by the stock's trailing 20-session dollar ADV ending before that flow window:

`pressure[i,t] = Σ_s Σ_{d=t-5..t-1} flow_dollars[s,d] * weight[i,s,d-1] / ADV20[i,d-1]`.

This score has units of recent fund-created dollar demand per dollar of the stock's typical daily trading value. The ex-ante sign is **positive**: larger inflow pressure is hypothesized to predict positive next-week stock returns. The first formation requires enough in-window history for a 20-session ADV and the five-day flow window. Form at Friday close using only values demonstrably public by then; enter at the next valid session open and define the prediction horizon as the next five sessions. If an issuer's daily share count or holdings weight has not been published before formation, delay/exclude it under one frozen rule rather than backfill a later value. Flow changes caused by share splits, data corrections, or other non-flow adjustments must be identified from issuer notices and removed or corrected before scoring.

The free issuer source is State Street's Select Sector SPDR product documentation and NAV history. State Street's [fund page](https://www.ssga.com/us/en/individual/etfs/fund-finder) displays fund NAV/AUM and shares outstanding and links NAV history and daily holdings. The page confirms the field exists for current reporting; it does **not** by itself verify a downloadable, date-filterable historical daily shares file for all 11 ETFs, its revision/publication history, or point-in-time creation-basket weights. Fund holdings at a later date are not an acceptable substitute for weights available before the flow date. ETF share-count differences estimate net primary-market activity; they do not identify which AP or investor acted, and a raw dollar change is not necessarily the basket's exact same-day cash-equivalent purchase.

Xu, “Are the Flows of Exchange-Traded Funds Informative?” *Financial Management* (2022), uses daily ETF shares-outstanding changes to estimate flows, but its sample of 366 US passive equity ETFs / 1,013,078 ETF-days is from February 2001–December 2016 and uses Bloomberg data. It finds that flow decomposition matters: unexpected flows predict ETF returns, while demand- and arbitrage-related components have different signs and the apparent return reversal evidence is concentrated in some flow components. Its estimator and outcome are ETF-level, not Dow constituent rank IC ([DOI](https://doi.org/10.1111/fima.12396)).

Brown, Davies & Ringgenberg, “ETF Arbitrage, Non-Fundamental Demand, and Return Predictability,” *Review of Finance* (2021), report an ETF-level long-short return spread of roughly 1.1–2.0% per month using primary-market flow signals. That result supports the non-fundamental-demand mechanism, but it is not a constituent-level flow transmission effect or a large-cap stock rank IC ([DOI](https://doi.org/10.1093/rof/rfaa027)).

Comerton-Forde & Marta, “ETF effects: The role of primary versus secondary market activities,” *Journal of Financial Markets* (2025), find that primary-market activity is associated with higher volatility and illiquidity in overweighted ETF constituent stocks; their public abstract describes a Japan quasi-natural experiment and says primary-market activity is infrequent and limited. This is a direct constituent-transmission mechanism, but the published summary does not provide a post-2020 US mega-cap return effect or the rank IC needed here ([DOI](https://doi.org/10.1016/j.finmar.2025.100983)).

Counter-evidence: Box et al., “Intraday arbitrage between ETFs and their underlying portfolios,” *Journal of Financial Economics* (2021), find little evidence that ETF trading leads constituent returns, including in daily-frequency tests ([DOI](https://doi.org/10.1016/j.jfineco.2021.04.023)).

- **No-outcomes confirmation:** these are external published results only; no project signal or return calculation was made.
- **Verdict:** FAIL for verified historical input timing and weights; concept is defined, but the required dated signal cannot yet be built without risking look-ahead.

## 3. Point-in-time coverage and independent breadth

The only local input check used a **predicate-filtered** read of `r6_data/etf/etf_ohlcv_dev.parquet`: PyArrow applied `date >= '2020-11-27'` and restricted the projection to `date` and `ticker`, then kept the 11 sector-SPDR symbols. It returned 16,368 metadata/bar rows: 1,488 dates, 2020-11-27 through 2026-10-30, with 1,488 rows per ETF for XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, and XLY. This confirms only that the 11 ETF market-data series have common development-date coverage; it does not verify the shares or holdings inputs.

| Input-only coverage item | Count / result | Method and limitation |
|---|---:|---|
| Select Sector SPDR names | 11 | Fixed task list; all present in the filtered OHLCV input |
| Common eligible ETF sessions | 1,488 | PyArrow predicate at read time; 2020-11-27..2026-10-30 |
| ETF OHLCV metadata rows | 16,368 | 11 × 1,488; not flow observations |
| Daily shares-outstanding rows verified in staged data | 0 | The staged ETF parquet has no shares-outstanding/NAV-history columns |
| Nonmissing daily dollar-flow signals | 0 verified | No historical issuer share-count series was staged or date-filtered into the workspace |
| Point-in-time Dow name-to-fund holdings weights | 0 verified | The available mapping QA describes latest sector labels, not dated historical fund weights |
| Eligible daily flow events | Not established | Cannot infer creation/redemption events from ETF OHLCV volume |
| Independent source clusters | At most 11; effective count unknown | Same sector fund shocks can co-move; constituent rows do not increase source breadth |
| Usable weekly formations / nonmissing stock scores | Not established | Requires historical share counts, publication times, historical weights, and PIT roster join |

The staged [`ETF_QA.md`](../r6_data/etf/ETF_QA.md) describes 11 sector ETF bars but no daily shares-outstanding, creation/redemption flow, NAV premium/discount, or historical ETF holdings weights. Its sector map uses a latest (2026) GICS snapshot, not point-in-time historical classifications. Applying that current classification backward would create look-ahead. A fund's published daily holdings list is not evidence that its historical weight series is available; the daily creation basket may also differ from full portfolio holdings. CIK/ticker changes, Dow entry/removal, sector reclassifications, and flow publication delays all need dated treatment.

At best, one daily observation carries 11 source-fund shocks; cross-sector correlation and the market-wide component reduce the effective number. The expected signal has tied or mechanically related scores for companies in the same sector, so nominal Dow cross-section breadth is not independent. The fixed proposal uses the 11 funds and no post-hoc broader universe.

- **Verdict:** FAIL. ETF bar coverage passes, but the required flow and point-in-time mapping coverage does not.

## 4. Effective breadth and power at a sourced plausible effect

No cited paper reports a weekly rank IC for daily sector-SPDR creation dollars mapped through historical constituent weights into Dow returns. Xu's 1,013,078 ETF-day sample and Brown et al.'s monthly ETF long-short spread concern ETF-level outcomes; Comerton-Forde–Marta report constituent volatility and illiquidity effects, not return rank predictability. Their magnitudes cannot be translated to this stock score without unsupported assumptions. There is no independently sourced effect size matched to this universe and horizon, so the power run below is a **scenario check**, not power at a sourced effect.

I used `r4_harness/power_sim.py` with 297 weekly formations (an optimistic six-year ceiling), five-session horizon/NW lag 4, date-level score autocorrelation 0.2, 5,000 seeded simulations, and 3, 5, or 11 effective sector-shock clusters per date. The harness's rank-IC noise approximation is `1/sqrt(K−1)`, with `K` equal to the assumed independent sector clusters; this is only a rough cluster-breadth sensitivity and does not implement a two-way sector/date bootstrap. `IC=.0183` is retained only as a comparison scenario used in earlier Round H planning, not a finding or literature estimate. `IC=.074` is the cheapest weekly rank-weighted-top-half planning threshold in `CRITERION4_BOUND_BY_SHAPE.md` at rho=.2, not an expected effect.

| Assumed independent source clusters | Power at scenario IC .0183 | Power at planning IC .074 | 80%-power MDE | Effective date N |
|---:|---:|---:|---:|---:|
| 11 (optimistic upper bound) | 15.0% | 91.5% | .0611 | 216.0 |
| 5 | 9.1% | 57.3% | .0967 | 216.0 |
| 3 | 7.0% | 34.3% | .1367 | 216.0 |

All power numbers are for the simple one-sided Newey–West `t >= 2` screen, **not** for block-bootstrap `p < .05` after Holm. Thus even a hypothetical IC at the portfolio planning hurdle reaches high power only if all 11 fund flows are independent; the more realistic 3–5 cluster sensitivities fail. Current/growing Holm-family adjustment and the goal's bootstrap can only make the criterion stricter. No evidence supports the scenario ICs as likely magnitudes.

- **Verdict:** FAIL. The effect is not sourced for the proposed signal, and effective source breadth is too uncertain to claim useful power.

## 5. Criterion-4 portfolio feasibility first

Conditional design only: weekly rank-weighted top-half long-only Dow book, top 15 positions with ranks 1–15 weights, active share 55%, next-session-open implementation, EW30 benchmark, and 0.05% per-side costs. For the proposal to form a genuine cross-sectional ranking, use the 11 fund flow shocks multiplied by lagged stock weights and divided by lagged ADV; names with equal resulting scores remain tied under a fixed deterministic ticker rule. This active-share property is a design target and is not verified from the unavailable weight panel.

The synthetic shape study sets the weekly 80%-power IC hurdle at .074 for rho=.2 and .083 for rho=.5. At rho=.2 it models 116% total-notional turnover and annual costs equal to 24.1% of gross edge at the .074 hurdle; at rho=.5 it models 91% turnover and 16.7% cost/gross edge at .083. Those are score-transition planning assumptions, not turnover observed for sector flows. The turnover cap branch is not satisfied under either scenario, and the alternative cost branch passes only at a gross edge near the strong synthetic hurdle. A scenario IC of .0183 would imply roughly 97% cost/gross edge under the same rho=.2 linear cost assumptions, which fails both portfolio cost conditions; it is not an empirical estimate.

ETF-level returns of 1.1–2.0% monthly cannot be presented as the expected stock-level portfolio return: ETF flow decomposition, premium/discount, stock weights, and flow timing all matter, and the papers do not provide the matched Dow rank IC. No defensible portfolio excess-return or Sharpe range can be generated. The criterion remains positive net excess return, Sharpe above EW30, one-sided block-bootstrap p < .05 after Holm across the current family, and the turnover/cost condition, with DSR at the cumulative variant count. The family was not queried from the prohibited Holm manifest.

- **Verdict:** FAIL — criterion-4 feasibility is unsupported. Do not commission an outcome run.

## 6. Holdout availability and protocol

No holdout-specific input is needed for this screen; no holdout data were accessed and availability remains unverified. Any future holdout must follow goal criterion 5, after the development gates, user decision, and a frozen specification; only the coordinator may perform the once-only holdout execution and any permitted availability-only check. This screen does not authorize that step.

- **Verdict:** PASS for not accessing holdout data; availability is not established.

## Final screen decision

**Overall: STOP — FAIL.** The idea is mechanistically distinguishable from Round H's CLV/volume proxy, and filtered ETF bars cover the full development window. The binding failures are the absence of verified daily issuer share counts and historical sector-fund weights in the date-bounded inputs, the same small and correlated source-cluster structure that limited H, and no matched literature effect capable of meeting the weekly portfolio hurdle. No runner or variant is authorized.

What could change the decision: a reproducible, free issuer source that supports reading only 2020-11-27 onward and yields all 11 funds' daily shares outstanding/NAV with publication/revision timing; a historical point-in-time holdings or creation-basket mapping to Dow members; and independent post-2020 evidence of a stock-level effect with scale and event breadth sufficient for the fixed Holm-adjusted criterion.

**Reviewer/date:** dispatched worker screen, 2026-11-11.

## Sources

- State Street, [Select Sector SPDR fund family](https://www.ssga.com/us/en/individual/capabilities/equities/sector-investing/select-sector-etfs).
- State Street, [SPY fund page showing NAV, shares outstanding, and NAV-history link](https://www.ssga.com/se/en_gb/intermediary/etfs/state-street-spdr-sp-500-etf-trust-spy); cited only as an illustration of the issuer's published fields, not as sector-flow coverage.
- Xu (2022), [“Are the Flows of Exchange-Traded Funds Informative?”](https://doi.org/10.1111/fima.12396).
- Brown, Davies & Ringgenberg (2021), [“ETF Arbitrage, Non-Fundamental Demand, and Return Predictability”](https://doi.org/10.1093/rof/rfaa027).
- Comerton-Forde & Marta (2025), [“ETF effects: The role of primary versus secondary market activities”](https://doi.org/10.1016/j.finmar.2025.100983).
- Box et al. (2021), [“Intraday arbitrage between ETFs and their underlying portfolios”](https://doi.org/10.1016/j.jfinec.2021.04.023).
- Synthetic planning comparison: [`CRITERION4_BOUND_BY_SHAPE.md`](../report_drafts/CRITERION4_BOUND_BY_SHAPE.md); [`power_sim.py`](../r4_harness/power_sim.py).

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
