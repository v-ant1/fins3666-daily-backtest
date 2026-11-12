# R6 Idea Screen AP — DTC short-squeeze pressure

**Status: SCREEN ONLY — STOP — FAIL.** A high days-to-cover (DTC) measure could identify positions that are mechanically difficult to close, but the strongest directly relevant evidence says high DTC predicts *lower*, not higher, subsequent returns. The opposite-sign long-high-DTC “squeeze” thesis also reuses the same FINRA DTC input and monthly horizon already screened in L, while the sealed 2010–2020 holdout has a stated short-interest-history gap from 2010 through 2017-11. No outcome, price, return, signal-predictive statistic, or holdout value was calculated or inspected.

## Identity and immutable-path preflight

- **Proposed name and mechanism:** AP — high DTC identifies a short position that would require a larger share of usual volume to cover; if covering pressure dominates the negative information in short interest, crowded names might rebound over the following month.
- **Exact new output:** `r6_ideas/AP_dtc_squeeze.md`.
- **Path preflight:** the exact target was absent before this file was created. The target name is distinct from the existing screens.
- **Development interval:** 2020-11-27 through 2026-10-30; earliest permissible worker-path date is 2020-11-27.
- **Input paths:** `r6_data/finra_si/finra_si_dev.parquet` was read only with a PyArrow dataset predicate on `settlement_date` bounded to 2020-11-27–2026-10-30. `r6_ideas/L.md`, `r6_ideas/D.md`, `r6_ideas/AN_rule201.md`, `r6_ideas/AA_event_concentrated.md`, and `specs/r6_prereg/D1.md` were consulted for overlap/design only. No sealed folder or pre-cutoff data rows were opened. R5 outcome files and decision-log outcome lines were not read.
- **Name/registry check:** a path and text search across `r6_ideas/*.md` found DTC/short-interest overlap described below; no exact `AP_dtc_squeeze.md` existed. I did not inspect the outcome registry.

## 1. Overlap with prior work

The nearest prior direction is **L — FINRA short interest and days to cover** (`r6_ideas/L.md`). L defines DTC from short interest divided by average daily volume, ranks by **negative** DTC, and hypothesizes that lower-DTC stocks outperform over the next month. AP would use the *same FINRA stock-level DTC observation, same point-in-time release rule, same broad S&P mechanism universe and same monthly horizon*, but invert the sign and call the high-DTC tail a squeeze. That is a different story about covering, but it is not a sufficiently distinct measure or identification design; it is an ex-post-looking sign inversion of the already screened DTC hypothesis. Further, the directly relevant literature predicts the opposite sign.

**D1** is a distinct input: five-session FINRA daily Reg SHO short-sale *transaction volume* (an activity flow) rather than bi-monthly reported open short positions (a position stock / DTC). It is adjacent short-pressure work but is not the reason AP fails novelty. `D` also considers Reg SHO flow, `AN_rule201` studies short-sale constraints, and `AA_event_concentrated` surveys event-pressure overlap; none turns outstanding DTC into a separate input family.

- **Verdict: FAIL.** AP repeats L's underlying series and horizon with the opposite sign. It would be a duplicate strategy variant, not a fresh mechanism.

## 2. Exact pressure measure and dated source

If this were reconsidered, the one fixed signal would be the FINRA consolidated `days_to_cover` field, in trading days, for each point-in-time S&P 500 issuer and Dow constituent. It represents current reported short interest scaled by average daily share volume; the raw ratio is mechanically `currentShortPositionQuantity / averageDailyVolumeQuantity` when the denominator is positive. The candidate score is **positive DTC** (highest is presumed most squeeze-prone), not a buy/sell transaction imbalance. Missing records remain missing; zero is not imputed. The FINRA report is a snapshot, not a continuous measure of when a short position was opened or covered.

Formation would be the last trading-day close of each calendar month. Use the latest settlement record whose **public dissemination date** is no later than that close; the settlement date alone is not the information-availability date. FINRA Notice 21-19 says FINRA disseminates OTC short-interest seven business days after settlement, but exchange-listed positions are sent to the listing exchange for processing/publication; a future implementation must establish the historical release date for each exchange and fail closed when it cannot. The target mechanism panel would rank the PIT S&P 500; the proposed long-only portfolio universe would be PIT Dow 30. The illustrative prediction horizon is the next 21 trading sessions after formation. A fixed placebo, only if a later screen passed, would permute scores within date and SIC2 (500 draws, seed `20261111`).

FINRA’s official [Consolidated Short Interest dataset](https://developer.finra.org/catalog), its [January 2023 release note](https://developer.finra.org/release-notes/january-2023-release-notes), [Rule 4560](https://www.finra.org/rules-guidance/rulebooks/finra-rules/4560) and [Regulatory Notice 21-19](https://www.finra.org/rules-guidance/notices/21-19) describe the source and reporting regime. The [FINRA short-interest explanation](https://www.finra.org/investors/insights/short-interest) distinguishes the twice-monthly position snapshot from daily short-sale volume. The staged panel has settlement dates, but no publication-timestamp field; its input coverage alone does not prove when each row became tradable information.

This screen performed only input coverage counts. It did **not** calculate DTC ranks, future returns, ICs, portfolio returns, or any other outcome statistic.

- **Verdict: PASS for measurable modern inputs, conditional on a frozen public-release-date reconstruction; no outcome evidence is asserted.**

## 3. Point-in-time coverage and independent breadth

The parquet read applied the date predicate at read time (`settlement_date >= 2020-11-27 AND settlement_date <= 2026-10-30`). Input-only coverage was:

| Development-only coverage item | Count |
|---|---:|
| Rows across all included settlement snapshots | 70,669 |
| Distinct settlement dates | 142 |
| Settlement-date span | 2020-11-30 to 2026-10-15 |
| Distinct symbols in the staged PIT-tagged panel | 613 |
| Rows with a nonmissing DTC field and positive average daily volume | 70,669 / 70,669 |
| S&P-tagged rows per settlement date | 493–503 |
| Cumulative distinct S&P-tagged symbols | 613 |
| Dow-tagged rows per settlement date | 30–33 |
| Cumulative distinct Dow-tagged symbols | 33 |
| 2024-only sample after a separate read-time date filter | 11,984 rows; 24 dates; 517 symbols |

The 2024 slice ran from 2024-01-12 through 2024-12-31 and had 11,984 nonmissing DTC entries, each with positive ADV. The 30–33 Dow-tagged rows and 33 cumulative symbols indicate symbol/member transitions that need an explicit roster-lineage join; these raw flags are not a claim of exactly 30 unique valid securities on every test date. No publication timestamp is carried in the panel, so the counts cannot establish an as-of information set by themselves. A future mechanism test would need to join canonical issuer lineage and PIT rosters and reconstruct public availability, with missing records excluded.

For breadth, the proposed cross-section has at most 500 S&P names, 142 raw semi-monthly snapshots (or roughly 72 monthly formations after selecting the most recently public record), and about 54 SIC2 groups using the development roster count documented in the earlier L/D1 screens. SIC2 count is not the number of independent observations: shared industry shocks and overlapping 21-session outcomes reduce effective breadth. FINRA rows have no issuer/news/covering-event identifier, so a DTC snapshot is not an independent squeeze event. Broad S&P survival of an older relation does not establish a positive effect in a concentrated Dow mega-cap subset.

Survivorship and measurement caveats: the panel is assembled from historical security symbols and PIT flags, not a signal-ready canonical issuer series. Symbol changes, mergers, delistings, the mismatch between data flags and canonical roster count, reporting delay, changing exchange coverage, and missing positions can all create selection. The source’s “days” use a volume denominator; it does not measure actual days until the short closes or identify a short seller’s intent.

- **Verdict: FAIL for a confirmatory squeeze test.** Modern input coverage is ample to describe a panel, but public-time alignment, canonical lineage, and truly independent squeeze breadth are not demonstrated, and the best evidence is for the contrary sign.

## 4. Effective breadth and power at a sourced plausible effect

The direct DTC evidence does not supply a positive squeeze effect. Hong, Li, Ni, Scheinkman and Yan’s NBER working paper uses monthly cross-sectional sorts and Fama–MacBeth regressions over NYSE/AMEX/Nasdaq stocks from January 1988 through December 2012. The lowest-minus-highest DTC decile spread is **+1.19% per month equal-weighted** (long low DTC, short high DTC; t=6.67), and **+0.67% value-weighted** (t=2.24), so high DTC predicts lower returns. Their comparison remains informative after excluding the bottom market-cap decile, but the incremental DTC-vs-short-ratio advantage attenuates: 0.29% monthly with t=1.76; after dropping the bottom quintile it is 0.25%. That is not evidence that high-DTC mega-caps squeeze upward. Boehmer, Huszár and Jordan (2010) similarly find high short interest predicts negative abnormal returns in NYSE/AMEX/Nasdaq stocks over 1988–2005, but describe the effect as potentially transient and of debatable economic significance. Rapach, Ringgenberg and Zhou (2016) study aggregate market returns, not single-name squeeze returns. None provides a positive, post-2020 Dow rank-IC for high DTC.

References:

- Hong et al. (2015), [“Days to Cover and Stock Returns,” NBER Working Paper 21166](https://www.nber.org/papers/w21166), https://doi.org/10.3386/w21166. This is a 2015 working paper, not a 2016 peer-reviewed journal publication. Sample and estimator details above are from the paper’s own abstract and empirical tables.
- Boehmer, Huszár and Jordan (2010), [“The Good News in Short Interest,” *Journal of Financial Economics* 96(1), 80–97](https://doi.org/10.1016/j.jfineco.2009.12.002). The authors’ [institutional record](https://ink.library.smu.edu.sg/lkcsb_research/4664/) identifies the journal, issue, pages, and abstract.
- Rapach, Ringgenberg and Zhou (2016), [“Short Interest and Aggregate Stock Returns,” *Journal of Financial Economics* 121(1), 46–65](https://doi.org/10.1016/j.jfineco.2016.03.004). It is aggregate-market predictive evidence and is not used as a single-name effect estimate.

**Synthetic power check (not an effect estimate):** `r4_harness/power_sim.py` was run with a 500-name mechanism cross-section, 72 monthly formation dates over the six-year development span, 21-session horizon (NW lag 20), AR(1) IC dependence `rho=0.5`, assumed cluster-stressed IC SD 0.20538, 20,000 simulations. The SD is an assumption-based stress value carried from the earlier SIC2 design (about 54 groups, within-group correlation 0.15), not estimated from project returns or from the FINRA signal.

| Planted mean rank IC | Power for one-sided NW t ≥ 2 | 80%-power MDE |
|---:|---:|---:|
| 0.0183 (generic R6 planning comparison, not a DTC effect) | 16.0% (MC SE 0.26 pp) | 0.1153 |
| 0.1200 (sensitivity only) | 88.3% (MC SE 0.23 pp) | 0.1153 |

The published monthly long-short return spread cannot be translated into Spearman rank IC without matching cross-sectional return dispersion, portfolio construction, and the same universe. Thus the above power rows are sensitivity checks, not “power at the literature effect.” The 0.120 sensitivity is not supplied by either cited paper and is only a reference point near the separate monthly RankTopHalf planning bound. No plausible positive high-DTC squeeze IC is sourced; by contrast, the sourced expected sign is negative.

- **Verdict: FAIL.** Power at the generic comparison effect is only about 16%; the 80% MDE is 0.1153, and no sourced positive DTC effect exists to power. The relevant literature points the other way.

## 5. Criterion-4 portfolio feasibility first

If the coordinator wanted a squeeze implementation despite the fail-gate, the single ex-ante candidate would be a monthly rank-weighted long-only top half of PIT Dow names by positive DTC, benchmarked to point-in-time EW30. This shape has **55% active share** in the synthetic planning note. Use the latest FINRA snapshot already public by formation, a 21-session holding period, and 0.05% per-side costs. The prior synthetic shape audit estimates monthly RankTopHalf’s IC hurdle at **0.160** for `rho=0.5` (80%-power, first-step Holm planning approximation), with 91% expected total-notional turnover and costs about 4.2% of gross active edge *if* gross edge existed at that hurdle. Those turnover/cost figures are planning assumptions, not measured trading characteristics; 91% exceeds the 50% turnover cap, so the design would have to rely on the alternative “costs below one quarter of gross edge” condition, and that cannot be verified absent any gross edge.

The older paper’s 1.19% equal-weight monthly decile long-short result is a **low-DTC minus high-DTC** spread on a broad 1988–2012 universe. It neither supports the proposed high-DTC-long direction nor maps to the RankTopHalf Dow book, 2020s regime, 0.05% per-side costs, six-year sample, block bootstrap or current Holm family. Consequently I cannot responsibly claim that its effect could clear the fixed net-excess-return / Sharpe / Holm-adjusted block-bootstrap goal. No portfolio outcomes were calculated.

- **Verdict: FAIL — criterion-4 feasibility is unsupported.** A return spread with the contrary sign cannot justify a high-DTC squeeze portfolio; the IC threshold also has no literature-matched positive effect to compare against.

## 6. Holdout availability and protocol

No holdout-specific input was needed or read. The task’s disclosed availability fact is that the consolidated short-interest history starts at **2017-12**; therefore the sealed 2010-01 to 2020-10 Dow holdout has an unavoidable 2010–2017-11 short-interest gap. I did not open, count, or otherwise inspect any pre-2020-11-27 FINRA rows or any holdout files. FINRA’s 2023 note describes the consolidated feed as having five years of history and all-exchange data only from June 2022, which reinforces that source changes over time and does not establish a free complete 2010 panel. No substitution is proposed. Under the coordinator-controlled criterion-5 rule, any later one-shot test must use the frozen design and only proceed if a valid holdout source is approved; this screen cannot meet that requirement with the stated gap.

- **Verdict: FAIL for criterion-5 availability.** The 2010–2017-11 portion lacks this short-interest series. The gap is disclosed; no holdout test is permitted or requested here.

## Final screen decision

**Overall: STOP — FAIL. Do not freeze a preregistration, register a variant, or start a runner.** The apparent squeeze mechanism is not supported by the directly relevant DTC evidence, duplicates L’s same source/horizon under the opposite sign, is not powered at a sourced plausible positive effect, has no demonstrated criterion-4 portfolio case, and cannot span the sealed holdout.

Evidence that could change this decision would require an independent, pre-specified squeeze measure (not the sign-reversed L DTC ranking), peer-reviewed or otherwise verified post-2020 large-cap evidence for positive post-disclosure squeeze returns, and a point-in-time history covering the full approved holdout. A narrower test using the modern development panel alone would still fail the current goal’s holdout rule and would require coordinator/user approval of a substitute before any outcome test.

**Reviewer/date:** dispatched worker screen, 2026-11-11.

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
