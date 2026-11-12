# Round 4 direction decision brief

**v1 snapshot:** the original comparison below reflects the data status before L4 published `NETWORK_DATA.md`; see v2 for the current recommendation.

**Status:** L1 postmortem, L2 synthesis/audit/red-team, L3 synthesis/cards/citation audit/red-team and L4 reports were present; none was marked draft. Optional `r4_L4\NETWORK_DATA.md` is absent. L3’s audit corrected the published Antón–Polk Table V estimate to 76 bp/month (t=4.96), clarified ETF evidence version boundaries, and downgraded L3 card 7; this brief does not rely on card 7. L3’s red-team confirms that daily ETF-flow history and a full holdout graph are not established, and that reversal is not a universal ETF-flow prediction. All three dossiers stay in U.S. equities; no cross-asset method is proposed. No outcome data were used here.

## Comparison and pick

| Dossier | Thesis path | Main evidence / reason | Data and holdout obstacle | Scores¹ | Recommendation |
|---|---|---|---|---|---|
| [D1 — Retail flow](D1_RetailFlow.md) | Direct signed-pressure persistence | Boehmer et al. measure marketable retail flow; clean contrast to candle proxies | No TAQ coverage verified in either period; recent large-cap evidence is adverse | F 1 / E 4 / R 5 | **Conditional second pick:** investigate only if TAQ is confirmed for both periods. |
| [D2 — ETF flow network](D2_ETFFlowNetwork.md) | ETF demand spreads through holdings | Strongest direct event and constituent-network design; current issuer holding sample exists | Daily historical holdings, signed ETF flow, NAV and holdout sources unverified; N-PORT is monthly/lagged | F 1 / E 5 / R 5 | **Primary pick for a data-access gate**, then preregister only if both eras are covered. |
| [D3 — Active common-owner flow](D3_CommonOwnerFlow.md) | Fund-flow pressure through shared holders | SEC filings and Lou/Coval–Stafford/Antón–Polk support a distinct, slower channel | 13F has positions, not flows; fund-flow/TNA access and full holdout history unverified | F 2 / E 5 / R 5 | **Backup:** consider if licensed fund-flow history is confirmed; otherwise drop. |

¹ Feasibility, effort, risk are each 1–5; higher effort/risk is worse. **Pick D2** as the main conditional study because it replaces L1’s nondirectional correlation smoother with dated flow and holdings links. **Pick D1 as a distinct persistence comparison only if TAQ is available.** D3 is a slower alternative to D2; do not test both without a specific user choice. None is ready for outcome testing today.

The L3 supplier-to-customer direction is dropped: its verified evidence primarily concerns monthly fundamental-news diffusion, not direct buying pressure; L4 says public customer links are too sparse for a full 30-stock network and FactSet Revere access is unconfirmed. Daily CLV or `sign(return)×volume` is not a substitute: L1 found five-day blend IC +0.0037 (NW t=0.38), heat IC −0.0017 (t=−0.14), and conflicting component signs.

## Holdout choice required before any outcomes

L4 found timestamp/schema availability for **37 of 40 Dow security/lineage windows**. KFT, DWDP and WBA lack Yahoo legacy-symbol rows; UTX is represented by an RTX lineage proxy. L4 also disclosed that a DWDP page rendered historical rows during its availability search; coordinator instruction is to report any later result both with and without the DWDP window. This worker did not inspect holdout values.

Choose one route before the coordinator opens any holdout outcomes:

1. **Full Dow (preferred if obtainable):** obtain and audit archived KFT, DWDP, WBA and UTX history (L4 names Kibot as a possible paid source, not sampled), then freeze the roster; report DWDP with/without its exposed interval.
2. **Dow with explicit gaps:** no silent fills; disclose the changed EW30 benchmark and reduced breadth. This is not equivalent to the registered 30-name holdout and needs user approval.
3. **Approved substitute:** e.g. a point-in-time S&P 100, with fresh roster audit and user approval.

These price gaps are separate from the dossiers’ missing historical TAQ, ETF flows/holdings or mutual-fund flow/TNA data. L4 did not verify those alternative sources over the full holdout.

## L1 constraints and trial budget

L1 found the original top-five portfolio traded **161.5%** of NAV per weekly rebalance versus **2.4%** for EW30, costing **8.07 bp** versus **0.12 bp**; net Sharpe was **0.60 vs 0.98**. Five-day pressure IC was +0.0037 (t=0.38), heat IC −0.0017 (t=−0.14), and an IC around **0.0196** would be needed for |t|=2 at observed HAC uncertainty. L1’s report gives weekly cost break-even IC ≈**0.0127**, but `cost_analysis.csv` gives **0.00605**; reconcile before portfolio decisions and use 0.0127 as a conservative warning meanwhile. Candidate turnover is unknown; each portfolio design caps total traded notional at 50% per rebalance or requires costs below one quarter of gross edge. A five-long/five-short dollar-neutral portfolio is materially different from EW30; a long-only top-five version has about 83% active share.

Allocate at most **3 variants per dossier**: D1=3, D2=3, D3=3 (9 candidate slots). Keep the remaining **21/30 unspent** as reserve; they are not permission for sweeps or post-result rescue. Any reserve use requires a new user/coordinator decision and a pre-registration logged in `specs/r4_trials.md`. Mechanism/event tests with Newey–West t≥2 and null shuffled-link/timing placebos come first; Holm correction applies across registered tests. Only then can a frozen portfolio test proceed.

**Next gate:** user selects 2–3 dossiers and the holdout route; confirm data access; reconcile L1’s cost break-even discrepancy; then preregister before outcome access.

## v2 — six-dossier decision (updated for L4 NETWORK_DATA.md)

**Current status.** This section supersedes the earlier v1 snapshot where it differs: L4 has now built a dated, partial common-ownership panel. No mechanism tests or outcome data are included in these dossiers. The new panel improves D4’s development readiness but does not clear any candidate for a complete both-period holdout: L4’s full Dow holdout price history still lacks KFT, DWDP and WBA and has the UTX→RTX lineage proxy; no sealed outcomes were opened.

### Ranked comparison by readiness before 20 Nov 2026

Scores use the existing 1–5 scale: feasibility higher is better; effort and risk higher are worse. “Both-period status” concerns development and 2010–20 holdout separately; it is not permission to inspect holdout outcomes.

| Rank | Dossier | Development readiness | 2010–20 holdout readiness | Evidence and thesis fit | Scores (F/E/R) | Decision |
|---:|---|---|---|---|---|---|
| 1 | [D4 — Common-owner CLV](D4_CommonOwnerCLV.md) | **Partial, best of six:** daily Dow OHLCV plus a public-filing-dated L4 13F overlap panel for 10 managers, 2020Q2–2026Q2. Incomplete filer universe and late-2026 edge staleness remain. | **Possible in principle, not ready:** SEC filings extend earlier and L4 says sampled 13F construction can be rebuilt for 2010–20; filings/CUSIP mapping are not built for that era, and OHLCV security history is incomplete. | Strong historical shared-owner evidence; direct thesis fit. But daily CLV propagation in 30 contemporary mega-caps is unproven. | 3/3/4 | **Pick 1, conditional primary.** First choice for a development mechanism test after user accepts the 10-filer graph and L4 confirms a feasible holdout source/route. |
| 2 | [D5 — Industry leader-follower](D5_IndustryLeaderFollower.md) | **Partial/conditional:** OHLCV exists; historical 10-K-header SIC time series must be built from public filings. L4 has only current SIC snapshot. | **Possible in principle, not ready:** historical 10-K headers can cover both eras, but PIT SIC/identifier history and full Dow prices are unbuilt/incomplete. | Hou/Menzly–Ozbas provide directional old-sample evidence; thesis fit good, but effect is known to be weaker in large, well-followed firms and Dow links may be sparse. | 2/4/5 | **Pick 2, conditional backup.** Run only if PIT industry labels and enough pre-specified directed pairs can be established without broadening after outcomes. |
| 3 | [D3 — Common-owner fund flow](D3_CommonOwnerFlow.md) | **Partial network, missing core signal:** L4’s 13F panel exists, but standardized mutual-fund TNA/flow history required by D3 is unconfirmed. | **Not ready:** historical 13F is possible, but 2010–12 requires archive extraction and fund-flow/TNA plus full security history are unconfirmed. | Strong flow mechanism and thesis fit; actual fund demand rather than OHLCV proxy. | 1/5/5 | Reserve only if user confirms a point-in-time mutual-fund flow/TNA source for both periods. |
| 4 | [D1 — Retail flow](D1_RetailFlow.md) | **Not ready:** no historical TAQ/retail classification data source confirmed. | **Not ready:** no holdout TAQ source and price gaps remain. | Direct measure and good persistence thesis fit, but modern large-cap critique and cost evidence are adverse. | 1/4/5 | Do not select unless user confirms full trades/quotes and retail classifier coverage in both periods. |
| 5 | [D2 — ETF flow network](D2_ETFFlowNetwork.md) | **Not ready for primary test:** current holdings and monthly delayed N-PORT exist, but ETF signed flow, NAV/imbalance decomposition and daily historical weights are not built. | **Fails full-period coverage as specified:** N-PORT begins 2019-10, and daily historical holdings/flows for 2010–19 are unconfirmed. | Network mechanism is plausible, but mixed informative/temporary flows make the sign ambiguous; thesis fit high. | 1/5/5 | Do not select for this deadline absent verified daily flow + dated holdings across both eras. |
| 6 | [D6 — Cross-asset trend](D6_CrossAssetTrend.md) | **Unconfirmed for an approved test:** xasset files exist, but L4 has not confirmed total-return conventions and exact full-period coverage for the chosen pair. | **Not confirmed:** no compliant full 2010–20 cross-asset panel documented. | Monthly bond/equity evidence is real, but return trends are a weak buying-pressure proxy and the cross-asset evidence is not a daily Dow network result. | 1/2/4 | Not a current pick; reconsider only after both-period ETF return availability is documented. |

### Recommendation and data the user must confirm

**Recommended picks: D4 and D5**, with D4 first. These are the only two new directions that retain a stock-to-stock propagation question and have a plausible free-data path in both eras. “Possible in principle” is not confirmed buildability: neither may proceed to predictive outcomes until its inputs and the holdout route are approved. The user should confirm:

- **For D4:** whether the fixed 10-reporting-entity L4 13F sample is acceptable despite not being the full institutional universe; whether the team can parse filing-dated positions and CUSIP/security lineage for 2010–20 from EDGAR; and which complete Dow-price route will resolve KFT, DWDP, WBA and UTX/RTX. For development, confirm how to treat dates after the last public 2026Q2 network panel (carry forward and report age, or stop at last usable panel).
- **For D5:** whether the team can build point-in-time SIC from historical 10-K headers for every roster constituent and map issuer changes; verify before outcomes that the two-digit SIC rule creates enough directed leader-follower links. Confirm the same complete Dow-price route as D4. If too few links exist under the frozen rule, record infeasibility rather than changing industry granularity after seeing returns.

Do not select D1–D3 or D6 without confirming the specific missing feeds listed in the table and dossier. L4’s newer report states: sampled 13F is **yes in principle** for the holdout; historical SIC is **possible with annual filings**; ETF N-PORT is **not** a full-period source; named customer-supplier links remain manual and sparse. These facts supersede earlier L3 statements that the 13F/SIC historical route was not confirmed, but they do not fill the holdout price gaps.

### Holdout route options

1. **Full registered Dow (preferred):** source the missing KFT, DWDP, WBA and point-in-time UTX history from an approved archive/vendor; freeze lineage and report the exposed DWDP window both with and without it. L4 named Kibot as a possible paid source but did not sample or purchase it. User must confirm funding/access.
2. **Dow with explicit gaps:** keep the registered Dow universe and disclose missing windows, reduced breadth and the altered EW30 benchmark; no silent fills. User must approve that this is an acceptable, non-equivalent holdout before any result is opened.
3. **Approved substitute universe:** have L4 reconstruct an alternative point-in-time roster with complete history, document availability only, and obtain user approval before the coordinator accesses outcomes. Do not substitute the sealed country-ETF basket.

D4 also requires a point-in-time 13F rebuild; D5 requires historical SEC 10-K headers. A price route alone is insufficient for either. If none of the options is accepted, holdout validation is infeasible and must be reported as such.

### Trial budget v2

For the recommended D4 and D5 only, reserve **3 variants each** (six candidate slots total) in `specs/r4_trials.md` once the user selects and preregistration is approved. Keep the overall hard cap at **30 variants**; the other **24 remain unspent reserve**, not permission for sweeps or after-result replacements. Dossiers D1–D6 each describe at most three fixed comparisons, but they do not consume trial slots until selected and registered. No variant has been tested or added to the trial log by this update.


