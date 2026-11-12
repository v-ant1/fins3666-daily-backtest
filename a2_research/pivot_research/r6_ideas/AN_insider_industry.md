# R6 Idea Screen: Industry insider purchase clusters

**Status:** SCREEN ONLY — no signal outcomes, no return calculations, and no variant is authorized by this document.

## Identity and immutable-path preflight

- **Proposed short name and mechanism:** AN — public insider purchase clusters in one SIC2 industry are an information signal that may transmit to other Dow constituents in that industry.
- **Exact new output path:** `r6_ideas/AN_insider_industry.md`.
- The exact target path was checked before writing and did not exist. No project data, signal outcomes, or returns were read to make this check.
- The name was checked against the existing idea-screen names. This is a new artifact name; the underlying Form 4 source overlaps an existing Round 6 family, as detailed below.
- **Development dates:** development panel starts 2020-11-27; feasibility reads below are restricted to 2024. Earliest permissible worker-path date is **2020-11-27**.
- No holdout path or pre-2020-11-27 rows were used. The only project observations used were time-filtered 2024 filing rows and dated membership/SIC records used for matching those rows.
- No signal outcomes, forward returns, ICs, or portfolio returns were calculated.

## 1. Overlap with prior work

The nearest overlap is the Round 6 Form 4 insider-buying family. Existing screens identify own-firm Form 4 purchase clusters as already covered and flag event-time variations of Form 4 as duplication (see `r6_ideas/AA_event_concentrated.md` and `r6_ideas/N.md`). This proposal changes the recipient mapping: it would exclude the source issuer and map disclosed buying to other firms in the same point-in-time SIC2 group. Its source event and information set are still Form 4 purchases, so the new network aggregation is not enough to establish a genuinely new signal family.

The activist 13D signal in `r6_ideas/AM_activist13d.md` is a different filing and mechanism. R5 summary headings and the decision-log heading were checked for naming context only; no decision-log outcome lines or result sections were used. The overlap with the existing Form 4 family is itself a screen failure under the instruction to avoid repeats.

**Verdict: FAIL.** It reuses the same dated Form 4 purchase source as prior R6 work, with only an industry-recipient transformation.

## 2. Exact pressure measure and dated data source

**Candidate definition, if a coordinator later authorizes a distinct test:** At each Friday close, use only Form 4 filings with filing dates in the most recent five completed trading sessions. Retain non-derivative transaction rows with transaction code `P`, and use reported transaction value in USD. Map each source issuer to its SIC2 industry using the last SIC record effective on or before that filing date. For each target Dow issuer, exclude its own source-issuer purchases; sum the remaining value for distinct source issuers in the target's SIC2. A SIC2-week is active only if at least two distinct source issuers report a `P` transaction. The target score is that five-session dollar sum; rank target Dow names cross-sectionally at the formation close, with ties receiving average ranks and a stable ticker tie-break only for portfolio selection. The hypothesis sign is positive. The predictive test, if separately approved, would be rank IC between formation scores and the next five-session Dow returns in excess of EW30, with a predeclared weekly NW lag of four.

This candidate deliberately does not claim that every `P` row is an open-market purchase: SEC code `P` includes an open-market **or private** purchase. The normalized input table lacks transaction footnotes/10b5-1 indicators, so it cannot reliably isolate open-market purchases or systematically exclude prearranged trading. The candidate score also assigns the same industry score to most firms in a SIC2, creating many tied ranks; it therefore may have little usable cross-sectional breadth.

The source is the SEC's public EDGAR Form 4 filings and its [Insider Transactions Data Sets](https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets). SEC guidance describes Form 4 reporting and Section 16 filing rules; generally, transactions are reported by the end of the second business day, so filing date is the public-information timestamp, not the trade date ([SEC Exchange Act Section 16 interpretations](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-section-16-related-rules-forms)). Use filing date, not transaction date, to avoid look-ahead. Access is free, subject to SEC automated-access policies and request-rate limits. SIC membership comes from the project's dated SIC panel and Dow membership from the dated Dow SIC panel.

The 2024 filing sample was read with a filing-date predicate from 2024-01-01 inclusive to 2025-01-01 exclusive. Its observed filing dates run 2024-01-02 through 2024-12-31. No earlier Form 4 rows were read for this pull. No forward returns, signal IC, or portfolio result was computed.

**Verdict: FAIL.** The code `P` definition and missing footnote/10b5-1 fields do not support the screen's intended open-market, non-prearranged pressure interpretation.

## 3. Point-in-time coverage and independent breadth

The following counts come from input-only 2024 coverage checks. Filing rows were selected at read time by `filing_date`; SIC records were selected at read time by 2024 effective dates and matched only when effective no later than the relevant filing; Dow membership intervals were selected by overlap with 2024.

| Coverage item | Count | Definition |
|---|---:|---|
| Form 4 transaction rows | 22,696 | P and S rows in the date-filtered 2024 filing sample |
| Candidate purchase rows | 800 | Rows with transaction code P |
| Candidate purchase source issuers | 154 | Unique ticker/issuer identifiers among P rows |
| P rows with officer or director flag | 707 | P rows with either role flag; flags may overlap |
| P rows with 10% owner flag | 83 | P rows with the 10% owner flag; may overlap officer/director |
| P rows with a usable pre-filing SIC record | 273 | 83 source issuers, matched from 2024 SIC rows effective by filing date |
| 2024 Dow SIC groups | 19 | SIC2 groups among dated Dow membership intervals overlapping 2024 |
| Possible Dow-industry cluster weeks | 14 | SIC2-week counts with at least two distinct mapped P-source tickers, among 7 SIC2 groups and 13 active weeks |
| Development weeks represented in the sample | 52 | Calendar weeks in 2024; only 13 had at least one mapped active cluster |

These are availability counts, not evidence of predictive effects. SIC mapping covered only 83 of 154 P-source tickers; just 273 of 800 P rows matched. A 2024 Dow issuer ticker list contains membership intervals rather than one fixed constituent set, and SIC coding may change over time. Form 4 filing delays mean the public signal arrives after the reported transaction; later filings, amendments, missing value fields, CIK/ticker changes, non-Dow source firms, and private transactions further reduce breadth. The local normalized table does not include all filing footnotes needed to classify these cases.

Literature does not establish that these input counts translate into 7 independent, predictive SIC2 signals among current mega-caps. The observed candidate event breadth is too sparse for a robust industry-cluster test.

**Verdict: FAIL.** Only 7 SIC2 groups and 14 possible industry-week clusters were available after the 2024 point-in-time join, and SIC coverage is incomplete.

## 4. Effective breadth and power at a sourced plausible effect

The literature supports parts of the mechanism but does not provide a plausible effect size matching this signal, universe, and horizon:

- Alldredge and Blank, “Do Insiders Cluster Trades With Colleagues? Evidence From Daily Insider Trading,” *Journal of Financial Research* 42(2), [DOI: 10.1111/jfir.12172](https://doi.org/10.1111/jfir.12172). They study 52,532 insiders at 8,789 firms over 1986–2014 and report within-firm purchase clustering and subsequent abnormal performance over approximately the next month. This is own-firm clustering, not SIC2 spillover into Dow peers, and it predates the current development period.
- Jagolinzer, Larcker, and Taylor, “Corporate Governance and the Information Content of Insider Trades,” *Journal of Accounting Research* 49, [DOI: 10.1111/j.1475-679X.2011.00424.x](https://doi.org/10.1111/j.1475-679X.2011.00424.x). Their U.S. governance-policy setting concerns the information content of insiders' own trades, not cross-firm industry clusters.
- Ben-David, Birru, and Rossi, “Industry Familiarity and Trading,” *Journal of Financial Economics* 132(1), [DOI: 10.1016/j.jfineco.2018.08.007](https://doi.org/10.1016/j.jfineco.2018.08.007). The study supports industry familiarity in individual trading, particularly outside the mega-cap/high-coverage setting; it does not estimate peer spillover from disclosed insider purchases.
- Deuskar, Khatri, and Sunder, “Insider Trading Restrictions and Informed Trading in Peer Stocks,” *Management Science* 71(3), [DOI: 10.1287/mnsc.2022.02907](https://doi.org/10.1287/mnsc.2022.02907). This provides evidence about insider trading in peer stocks in India, but not an effect estimate for U.S. SEC Form 4 clusters or a Dow weekly rank IC.

Thus the reported effects are not interchangeable with this proposal's weekly rank IC. I do not treat the often-cited next-month abnormal return from own-firm insider clustering as a sourced effect for this peer signal.

For a transparent **synthetic planning sensitivity only**, `r4_harness/power_sim.py` was run with 500 assets, 308 dates, five-session horizon, signal autocorrelation 0.5, event rate 0.25, cluster shape 0.5, planted event effect 0.02, 5,000 simulations, seed 20261111. The event-rate assumption reflects 13 active weeks among 52 in the small 2024 coverage sample. The simulation returned 69.14% probability of NW t ≥ 2 at the planted effect, mean 56.54 event observations, mean effective sample size 25.41, and an unadjusted 80%-power minimum detectable effect of 0.02162. These are simulator units, not rank IC or empirical outcomes. The simulation assumes a 500-name cross-section and does not model the observed concentration in only seven SIC2 groups, so it is optimistic for this candidate.

For orientation, using a conservative 24-test Holm first-step cutoff (one-sided z about 2.87) and a normal-approximation scaling gives an approximate adjusted 80%-power threshold of 0.0282 simulator units. This is not a re-run of the simulator under Holm, and it is not a claim about the current family size; it is a planning sensitivity only. No independent study provides a directly matched SIC2-to-Dow-peer rank-IC effect to compare with it.

**Verdict: FAIL.** There is no sourced, setting-matched effect size, and the sparse cluster structure makes useful power doubtful even before the additional concentration penalty.

## 5. Criterion-4 portfolio feasibility first

If this direction were independently approved despite the overlap failure, the fixed portfolio candidate would be a weekly rank-weighted long-only tilt over the eligible Dow cohort, using the signal ranks at each Friday close and holding through the next five sessions. The portfolio would use the shape in `report_drafts/CRITERION4_BOUND_BY_SHAPE.md`: rank-weighted top half (15 names when the full Dow cohort is available), active share at least 50%, compared with EW30; charge 0.05% per side; apply the exact decision-63 missing-price carry-and-sale rule to both books; and use a block bootstrap against the complete R6 Holm family. Turnover would be constrained at 50% per rebalance, or costs would have to remain below 25% of gross active edge, as allowed by the fixed screen rule. This is only a proposed evaluation shape; no portfolio is authorized.

The synthetic criterion-4 shape analysis reports a weekly rank-IC hurdle of about 0.083 for rank-weighted top-half at signal autocorrelation 0.5. That hurdle is a synthetic planning result, not an empirical effect. The own-firm insider papers' reported monthly abnormal-return findings cannot be converted into a weekly SIC2 peer rank IC without unsupported assumptions. The 2024 coverage pull has only 14 possible active SIC2-week clusters across seven SIC2 groups, making any conversion from a paper's own-firm or non-U.S. results especially speculative. No defensible sourced range can be shown to clear the 0.083 hurdle after costs, six-year sample dependence, and Holm adjustment.

**Verdict: FAIL — criterion-4 infeasible on current evidence.** The documented effect does not match the candidate outcome or universe, and no justified mapping reaches the weekly hurdle.

## 6. Holdout availability and protocol

This screen does not need a holdout input, and no holdout path or sealed value was opened. The candidate fails earlier gates and should not advance to holdout testing. If the coordinator later authorizes an eligible idea, use goal criterion 5: keep the holdout sealed until the preregistration, governance checks, and development results are complete; permit only the specified availability-only roster/row-count check before a coordinator-controlled holdout evaluation. No availability check was needed for this screen.

**Verdict: PASS for screen data handling only; no holdout test is proposed.**

## Final screen decision

**Overall: STOP — FAIL.** The source repeats the existing R6 Form 4 family; SEC code P does not isolate the intended open-market non-prearranged purchases; the input-only 2024 join leaves only seven possible SIC2 groups and fourteen cluster weeks; and research does not provide a matched effect capable of supporting the synthetic weekly criterion-4 hurdle.

Evidence that could change this decision would include an explicitly distinct, coordinator-approved source family; reliable public timing and open-market/non-10b5-1 classification; broader point-in-time SIC coverage and substantially more independent industry clusters; and independent research quantifying this exact U.S. mega-cap peer-pressure mechanism in a rank-IC-comparable metric. Do not run a signal or portfolio test unless all gates are re-reviewed and pass.

**Reviewer/date:** Worker screen / 2026-11-11.

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
