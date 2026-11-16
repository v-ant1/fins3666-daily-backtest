# D7 freeze-readiness review

## Verdict: NOT READY

I reviewed the revised `specs/r4_prereg/D7.md` against the BLOCKER and SHOULD-FIX findings in `report_drafts/D7_PREFREEZE_AUDIT.md`, checked the existing D4–D6 endpoint family and variant budget, and read only the header row of `r4_L4/data/earnings_clock.csv`. I did not inspect `r5_D7/LINKS.csv`, any outcome data, or any D7 results.

## Audit findings

| Audit finding | Status | Evidence and exact fix needed |
|---|---|---|
| **BLOCKER — executable event clock** | **Unresolved** | D7 currently says a release before 09:30 ET uses that session and a release at/after 09:30 ET uses the next session; unknown time uses the first session after the filing date. It does not combine the release timestamp with the filing-date cutoff, so the selected session can precede the next session after the 8-K filing date. Replace the clock rule with: “Normalize EDGAR acceptance and explicitly stated release timestamps to America/New_York. Let `a` be the first NYSE session whose 09:30 ET open is strictly later than the later known timestamp; a timestamp exactly at 09:30 ET is treated as not earlier than that open, so use the following session. Let `f` be the first NYSE session strictly after the filing date. The response session `d` is the later of `a` and `f`. If no explicit release timestamp is available, treat the filing-date anchor as date-only and set `d=f`. If an explicit release time is during regular trading, use the next session. Record the normalized timestamps, `f`, `a`, and final `d` for every event. Compute the customer shock only on `d` after that entire session has completed.” |
| **BLOCKER — benchmark source and definition** | **Resolved** | D7 now fixes the sole benchmark as same-session EW30 open-to-close return from the authorized point-in-time Dow price panel, expressly excluding SPY and any beta-adjusted label. It also gives a missing-price exclusion rule. |
| **BLOCKER — pre-inspection feasibility chronology** | **Unresolved / unverified** | D7 states that thresholds were fixed at `2026-11-10T13:27:54Z` and asserts that no link contents or coverage summaries had been seen. The audit requires a dated, content-hashed D7 text and the L1 handoff date recorded before L1 provides the file or any coverage summary; those two pieces of chronology are absent from D7. Add the dated content hash and L1 handoff date to the freeze record before any link data or counts are provided. If the claim cannot be substantiated, disclose that and do not describe the gate as pre-inspection; keep D7 infeasible unless an independently dated rule supports the same thresholds. This cannot be verified by opening the prohibited link file. |
| **SHOULD-FIX — placebo inference and common sample** | **Resolved** | D7 now requires all eligible event dates in every draw, fails the input gate if a complete shuffle is impossible, specifies 500 complete draws and the seed, and replaces the `|t|<2` null claim with TOST equivalence checks and 90% intervals for both the shuffled-series and timing placebo. The timing placebo freezes the original response-date link set. |
| **SHOULD-FIX — Holm endpoints** | **Unresolved count discrepancy** | D7 enumerates five endpoints and states 21 + 5 = 26. This covers a primary test, observed-versus-shuffle test, shuffled-series equivalence, timing-placebo equivalence, and portfolio test. The audit's proposed replacement calls for six D7 endpoints and a 27-endpoint family, including an additional inferential endpoint. Reconcile the audit and preregistration before freeze: either name and define the sixth inferential endpoint and set the family to 27, or document that no sixth test is being added, update the audit ruling to five D7 endpoints/26 total, and confirm the shuffled-series equivalence endpoint includes the mean-series inference that the audit identified. Do not leave an open-ended “any other endpoint” in the frozen family. |
| **SHOULD-FIX — literature horizon** | **Resolved** | D7 now calls five sessions a project-specific short-horizon extrapolation and says the cited monthly studies do not establish this event horizon. |
| **SHOULD-FIX — thesis fit** | **Resolved** | D7 describes itself as an adjacent information-diffusion test and explicitly says it does not directly measure buying pressure, order flow, or causal transmission. |
| **NOTE — preserve one variant** | **Resolved** | D7 registers one primary variant and disallows alternative benchmarks, event categories, links, or horizons as rescues. |

## Endpoint-family and budget checks

The interim family has 21 endpoints: D4 has 9, D5 has 6, and D6 has 6. The D7 draft adds five named endpoints, so its arithmetic of 26 is internally correct, but it does not match the audit's requested six / 27 count. That discrepancy is a freeze blocker until the audit ruling and endpoint manifest agree.

The D7 variant budget fits. The preregistrations identify 7 active D4–D6 variants (2 + 2 + 3); duplicate D6 outcome rows are not extra variants. D7 adds one variant, giving 8 of the 30-variant ceiling and leaving 22 slots. The five D7 endpoints/placebo calculations are not additional strategy variants. The variant count is separate from the unresolved Holm endpoint count.

## Earnings-clock schema check

I read only the CSV header. `earnings_clock.csv` has these fields:

`ticker, cik, company_name, acceptance_timestamp_et, acceptance_timestamp_utc, classification, form, items, filing_date, report_date, accession_number, universe_source, dow_member_on_acceptance_date, source_url`

This schema supports the filing identity, Item/form, filing date, accession, EDGAR acceptance time in ET and UTC, and source URL required for the audit trail. It has no earnings-release timestamp or derived response-session field. D7 says to obtain an explicit release timestamp from the furnished exhibit and to record the associated response session, so the schema can feed the D7 event table, but the event table must add `release_timestamp_et` when the exhibit supplies one and a derived `response_session`; `acceptance_timestamp_et` must remain an audit timestamp and must not be used as a substitute for an unknown release time. The clock boundary issue above still prevents freeze.

## Freeze actions

1. Replace the event-date rule with the combined release-time / filing-date clock stated above.
2. Record the dated content hash and L1 handoff date before any link file or coverage data is delivered; otherwise disclose the chronology limitation and do not pass the gate as pre-inspection.
3. Resolve whether D7 contributes five or six endpoints. Make the named D7 list, total family count, audit ruling, and coordinator manifest agree before any D7 outcome.
4. At freeze, log D7's one variant within the remaining 22 slots and keep all already registered D4–D6 endpoints in the family.

