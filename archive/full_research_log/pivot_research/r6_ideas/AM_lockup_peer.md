# R6 Idea Screen AM — lockup-expiry supply pressure and SIC-peer spillover

**Overall: STOP — FAIL. Do not register a variant or start a runner.** Published evidence supports increased trading and a short negative abnormal return around IPO lockup expirations for the issuer, mostly in 1988–1997 IPO samples. It does not show a post-2020 mega-cap effect or a return spillover to Dow SIC peers; ordinary S&P IPO seasoning also means the usual ~180-day lockup often expires before a new IPO can enter the index. A bounded SEC search found filing-text matches, not an eligible event panel, and an optimistic synthetic power check is below 80% even before Holm adjustment.

This is a screen only. I calculated no project signal, forward return, IC, portfolio return, or other signal outcome and did not access holdout values.

## Identity and immutable-path preflight

- **Proposed direction:** AM — when a scheduled lockup expires for an S&P 500 issuer, the newly saleable pre-IPO shares may create temporary negative supply pressure that could transmit to Dow stocks in the issuer’s same SIC2 industry.
- **Exact new output path:** `r6_ideas/AM_lockup_peer.md`.
- **Path check:** the exact target did not exist before this screen; this file is new.
- **Development window:** 2020-11-27 through 2026-10-30; the SEC feasibility query below used 2024-01-01 through 2024-12-31, wholly within the development period. Earliest permissible worker-path date remains 2020-11-27.
- **Input paths:** only public SEC EDGAR filing-search metadata with a server-side date range and existing non-return idea/planning documents. No price, outcome, Holm-family, result, decision-log or holdout path was read.
- **No reused output name:** an `r6_ideas`/R5 text search found no exact lockup-expiry screen. The destination was checked before writing.

## 1. Overlap with prior work

The nearest existing R6 screens are [AJ equity supply](AJ_equity_supply.md), which studies primary shares sold in seasoned equity offerings, and [AJ buyback window](AJ_buyback_window.md), which studies firms resuming repurchases after earnings. Lockup expiry instead releases restricted pre-IPO shares held by insiders, founders, employees, or venture investors; it is neither an issuer sale of newly raised capital nor an issuer repurchase. The shared economic category is dated changes in available share supply, so novelty is partial rather than wholly distinct. The SEC form and event window are not themselves novel.

A targeted text search across the existing idea screens and `R5_FINAL.md` found no lockup-expiry signal with this issuer-to-Dow-peer construction. I did **not** inspect the decision registry, because this task forbids opening decision-log outcome lines; registry-only overlap therefore remains for the coordinator to check without exposing those lines.

- **Verdict: PASS with caveat.** The contractual lockup-release event and cross-company SIC-peer mapping are different from AJ’s offering and buyback measures, but share-supply-event overlap is material.

## 2. Exact pressure measure and dated data source

### Candidate definition, if reconsidered

At each Friday close in the development window, use the then-current point-in-time S&P 500 membership and the public IPO registration statement/prospectus to identify S&P constituents whose contractual lockup expires during the next five trading sessions. For source issuer *i*, define its scheduled release intensity as `locked_shares_i / public_float_i`, using the last prospectus amendment publicly accepted before that Friday close and the pre-release float reported there. Exclude events with no disclosed locked-share amount or contractual expiry, and exclude waivers or early releases unless they were publicly filed by formation. A later amendment may not be used retroactively.

For Dow target *j*, set the weekly pressure score to the negative sum of scheduled release intensities for source issuers with the same SIC2 as *j*: `score_j,t = -Σ_i [same_SIC2(i,j) and expiry_i in next_5_sessions] × locked_shares_i / public_float_i`. Zero means no identified source event in that target’s SIC2. The fixed hypothesis would be that a larger scheduled release predicts a more negative Dow peer return over the next five trading sessions. Formation is at the Friday close, after all included filing acceptance times; the return window begins with the next full session. This is an ex-ante, scheduled supply proxy, not actual insider selling. SIC2 assignment and both rosters must be point-in-time. Event weeks with no eligible peer issuer carry no signal, rather than a zero score.

SEC [EDGAR Full-Text Search](https://www.sec.gov/edgar/search/efts-faq.html) searches filing text and attachments and supports custom start/end dates. Relevant public documents include S-1 registration statements and 424B prospectuses. The SEC [EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) are public and do not require a paid data subscription, but broad text search includes exhibits and is not a clean structured lockup database. Prospectus terms need extraction and human/automated validation; accession and amendment timestamps, contractual dates, share amounts, CIK/ticker lineage, S&P membership and the Dow/SIC peer roster all need point-in-time handling. Later lockup amendments and waivers can make an initial schedule stale.

### External research

- Field and Hanka, “The Expiration of IPO Share Lockups,” *Journal of Finance* 56(2), 471–500 (2001), [DOI 10.1111/0022-1082.00334](https://doi.org/10.1111/0022-1082.00334). In 1,948 U.S. IPO lockup agreements from 1988–1997, the authors report a permanent 40% increase in average trading volume and a statistically prominent −1.5% three-day abnormal return around expiry. Effects were larger for venture-capital-backed firms. This is an issuer event result from an older IPO cohort, not a weekly SIC-peer rank IC.
- Brau, Carter, Christophe and Key, “Market Reaction to the Expiration of IPO Lockup Provisions,” *Managerial Finance* 30(2) (2004), [BYU article record](https://scholarsarchive.byu.edu/facpub/9161/), [DOI 10.1108/03074350410768859](https://doi.org/10.1108/03074350410768859). The authors report statistically significant negative abnormal returns around expiry and relate them to information asymmetry and insider/shareholder incentive alignment. The accessible article record does not establish a post-2020 mega-cap estimate or peer transmission.
- Aggarwal, Krigman and Womack, “Strategic IPO underpricing, information momentum, and lockup expiration selling,” *Journal of Financial Economics* 66(1) (2002), [DOI 10.1016/S0304-405X(02)00152-6](https://doi.org/10.1016/S0304-405X(02)00152-6). Their model and 1990s IPO evidence connect underpricing, information momentum, and insiders’ selling incentives at expiry. It is not evidence that expiry-induced selling spills into mature industry peers.

- **Verdict: PASS for defining a testable schedule; FAIL for a verified, implementation-ready signal.** Contract terms are potentially public before formation, but no staged lockup panel, exact expiry-date panel, or verified shares-under-lockup field is available in the R6 data tree. The query feasibility check below confirms that the free search is a discovery tool, not that an event-level panel is ready.

## 3. Point-in-time coverage and independent breadth

I made one metadata-only SEC EDGAR Full-Text Search request with the query phrase `"lock-up agreement"`, form `S-1`, and explicit server-side dates `2024-01-01` to `2024-12-31`. SEC returned **1,533 matching filing-text documents** (reported total relation `eq`; the API response returned at most 100 document hits). This is within the development window. Per SEC’s FAQ, full text includes attachments; this count is not distinct IPOs, agreements, expirations, eligible S&P events, or independent observations. I did not open any filing body or inspect any stock return.

| Input-only coverage item | Result | Limitation |
|---|---:|---|
| SEC S-1 phrase-search documents, 2024 dates | 1,533 | Filing-text/exhibit documents; cannot be interpreted as events |
| Returned SEC hit records | At most 100 | Search response cap, not a census of agreements |
| Staged lockup/IPO event files in `r6_data` | 0 found by filename search | Does not prove SEC filings lack terms |
| Usable event dates / independent IPOs | Not established; verified count 0 | Requires deduplication, prospectus parsing, contractual-date validation and amendment handling |
| Dow target names | Intended universe 30 per formation | No lockup-linked signal coverage count established |
| Point-in-time S&P source names with expiry in the next week | Not established | No linked PIT S&P/lockup panel was built |
| Independent SIC2 clusters with events | Not established | SEC text hits cannot determine issuer SIC2-to-Dow peer clusters |

This direction is especially sparse by design. IPO lockups usually have one expiry per issuer and are commonly around 180 days, while S&P 500 IPO methodology says ordinary IPOs should have 12 months of trading before index consideration; committee exceptions exist, but the timing mismatch makes a new IPO’s expiry while it is already an S&P constituent unlikely. See the S&P DJI [U.S. Indices methodology](https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-us-indices.pdf). Longer contractual terms and special index additions mean the count is not logically zero, but cannot be assumed broad. The event is one-time, clustered in IPO/technology cycles, potentially shared by multiple issuers in one SIC2, and its universe selection is itself a selected mature-firm subset. SIC2 aggregation reduces, rather than creates, independent breadth.

Public filings are available without cost, but reconstructing historical CIK/ticker identities and prospectus amendments is nontrivial; using present-day names would create survivorship bias. Event-date extraction must distinguish contractual expiry from filing date, and “shares locked” may be reported in different exhibits or not in a readily parseable format. Zero verified eligible events in this screen is a data-coverage finding, not a claim that no such filings exist.

- **Verdict: FAIL.** The searchable document count does not establish usable event breadth, name coverage, or independent SIC2 clusters for the proposed peer design.

## 4. Effective breadth and power at a sourced plausible effect

The strongest external magnitude is Field and Hanka’s −1.5% three-day issuer abnormal return for a 1988–1997 IPO sample. Brau et al. also find negative issuer-window abnormal returns, but neither source estimates Dow peer returns, SIC2 spillover, a weekly cross-sectional rank IC, or a post-2020 large-cap sample. The effect sign for peers is an inference: a source issuer’s selling pressure could depress close substitutes, but investors could also rotate into peers or the source event may be issuer-specific. Therefore **there is no source-matched plausible peer rank-IC range** to claim.

For an explicitly optimistic sensitivity check—not an effect estimate—I ran the synthetic-only `r4_harness/power_sim.py`: 30 Dow targets, 312 weekly dates, five-session horizon/NW lag 4, signal autocorrelation 0.2, event rate 0.10 events per week (about 31 events over six years), negative-binomial cluster shape 0.5, and planted event-date mean rank IC 0.074. The 0.074 value is the lowest weekly `RankTopHalf` 80%-power planning hurdle in `report_drafts/CRITERION4_BOUND_BY_SHAPE.md`, not a published lockup effect. The event frequency is a deliberately transparent assumption, not derived from the SEC’s 1,533 document hits. The tool assumes null-rank-IC noise `1/sqrt(29)` and models clustered event counts; it does not model concentration into SIC2 groups, uncertain schedule coverage, or missing issuer events, so this is favorable to the proposal.

| Synthetic planning result | Value |
|---|---:|
| Mean active event dates | 27.14 of 312 weekly dates |
| Mean source events | 31.19 over six years |
| Mean effective event-date observations | 19.74 |
| Power for one-sided NW t ≥ 2 at planted mean IC 0.074 | 54.4% (Monte Carlo SE 0.0050) |
| Minimum detectable mean IC for 80% power | 0.111 |
| Holm adjustment included? | No; power is for the unadjusted NW t ≥ 2 statistic |

Even under these optimistic assumptions the power is below 80%, and the 0.074 IC is not documented for peer spillover. Holm adjustment and SIC2 concentration would make the actual test less powerful. The full design cannot supply the independent events or sourced effect needed to pass this gate.

- **Verdict: FAIL.** No independently documented effect matches the target and horizon, and the favorable sparse-event simulation has only 54.4% power at a planning benchmark that is itself not a lockup estimate.

## 5. Criterion-4 portfolio feasibility first

The least-concentrated candidate would be the weekly rank-weighted top-half Dow book from the criterion-4 planning note: top 15 names weighted in proportion to ranks 1–15, active share 55%, benchmarked against EW30. Use 0.05% per side (10 bp for a full buy/sell round trip at 100% total-notional turnover), with the fixed goal’s turnover/cost condition and block-bootstrap/Holm criterion unchanged. `CRITERION4_BOUND_BY_SHAPE.md` gives a synthetic weekly 80%-power rank-IC hurdle of **0.074** when signal autocorrelation is 0.2 and **0.083** at 0.5, for a 24-endpoint first-step Holm planning approximation. Its Gaussian-score model estimates 116% average turnover at rho 0.2; a 50% cap would bind and can reduce exposure to event weeks. If the gross active edge existed, that planning case estimates annual trading costs at 24.1% of gross active edge before any attenuation from the cap.

The sourced −1.5% is an issuer three-day event CAR in a 1988–1997 IPO sample. It cannot be translated into an expected return or Sharpe for long-only Dow industry peers: there is no cited peer coefficient, event-frequency estimate, or independent sector breadth. Thus the best defensible peer excess-return/Sharpe range is **not estimable**, rather than positive. Assuming the issuer event coefficient applies to peer stocks would be an unsupported extrapolation and would not satisfy criterion 4. No portfolio is justified merely to discover the missing peer effect. The goal’s criterion-4 bar—positive net excess return and a Sharpe above EW30 with one-sided block-bootstrap evidence after Holm—remains binding.

- **Verdict: FAIL — criterion-4 feasibility is unsupported.** The project has no defensible peer-return effect estimate to clear the 0.074–0.083 weekly rank-IC planning hurdle after costs and Holm adjustment.

## 6. Holdout availability and protocol

This screen required no holdout path and no holdout-specific input; no sealed values were accessed. It does not establish holdout availability. Any later holdout work must follow the coordinator-controlled protocol in goal criterion 5, only after the idea passes development gates and is frozen. I did not inspect, load, or query any pre-2020-11-27 price or return series.

- **Verdict: PASS for this screen’s no-holdout rule; availability remains unverified.**

## Final screen decision

**Overall: STOP — FAIL.** The old IPO literature supports scheduled issuer-level supply pressure, but the proposed effect on Dow SIC peers has no direct evidence, eligible event breadth is not established, the ordinary IPO seasoning interval works against overlap between S&P membership and typical 180-day expiries, and even the favorable event-mode power illustration is underpowered. This screen does not authorize a preregistration, runner, variant, or portfolio test.

Evidence that could change the decision: a deduplicated SEC prospectus/contract panel with point-in-time S&P membership and verified expiry dates, locked-share quantities, and Dow SIC2 links; a sufficiently broad independent-event/cluster count; and independent research showing a compatible post-2020 large-cap peer effect large enough to clear the fixed Holm-adjusted after-cost hurdle.

**Reviewer/date:** dispatched worker screen, 2026-11-11.

## Sources

- Field & Hanka (2001), [“The Expiration of IPO Share Lockups”](https://doi.org/10.1111/0022-1082.00334).
- Brau, Carter, Christophe & Key (2004), [article record](https://scholarsarchive.byu.edu/facpub/9161/), [DOI](https://doi.org/10.1108/03074350410768859).
- Aggarwal, Krigman & Womack (2002), [“Strategic IPO underpricing, information momentum, and lockup expiration selling”](https://doi.org/10.1016/S0304-405X(02)00152-6).
- SEC, [EDGAR Full-Text Search FAQ](https://www.sec.gov/edgar/search/efts-faq.html) and [EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).
- S&P Dow Jones Indices, [U.S. Indices Methodology](https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-us-indices.pdf).
- Project design-only references: [`CRITERION4_BOUND_BY_SHAPE.md`](../report_drafts/CRITERION4_BOUND_BY_SHAPE.md), [`power_sim.py`](../r4_harness/power_sim.py).

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
