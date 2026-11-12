# D4 pre-freeze audit

**Scope.** Independent review of `specs/r4_prereg/D4.md` against the round rules and `specs/r5_decisions.md`. I did not inspect, calculate, or use D4 outcome data. For the named 13F files, I checked existence and CSV headers only.

## BLOCKER — fixed Q2 2026 manager selection leaks future information into the 2010–2020 holdout

D4 says to use the 50-manager roster in `13f_manager_rank_q2_2026.csv` for both development and holdout. Those managers were selected by a 2026 filing-period rank; applying that future-selected roster to 2010–2020 makes the historical network depend on information unavailable in the holdout period. The stock roster is point-in-time as required by the binding holdout decision, but the manager roster is not. Resolve this before freeze and before any outcome test. A coherent point-in-time rule changes the network input construction and must be applied identically in development and holdout.

**Proposed exact replacement for the manager-roster sentences in “Universe, inputs, timing, and network”:**

> At each signal date, define the eligible manager universe from original Form 13F-HR filings accepted by the SEC before the signal cutoff. For each manager, use only its latest original report whose filing was accepted by that cutoff; omit managers with no then-public report and do not treat absent filings as zero holdings. Rank eligible managers by the reported total value in that latest public filing, descending, breaking ties by CIK ascending; retain the first 50, or all eligible managers if fewer than 50 exist. Apply this same date-specific rule in development and holdout. The Q2 2026 rank file may validate the development-period ranking only; it must not define historical holdout membership.

If the coordinator elects to keep the fixed Q2 2026 cohort instead, the holdout cannot be described as point-in-time and D4 does not satisfy the preregistered holdout criterion.

## BLOCKER — filing availability is date-only, but the rule permits same-day after-close look-ahead

D4 requires filings to be “public by the close of t,” while the checked `13f_holder_by_dow_stock.csv`, `13f_filing_coverage.csv`, and manager-rank schema expose `availability_filing_date`/`filing_date`, not acceptance timestamps. A filing accepted later on signal date t would not have been usable at that close. The prose is not implementable safely from the stated date-only fields unless the build has an unmentioned timestamp source.

**Proposed exact replacement for “Use positions only once their actual SEC filing acceptance/public date is reached” and the same-day graph clauses:**

> Use the SEC filing acceptance timestamp when available and include a position only if the timestamp is strictly earlier than the signal close timestamp. If the input provides only a filing date and no acceptance time, treat the filing as available at the next trading session's open; do not use it for a signal dated on the filing date. Apply the same cutoff to manager eligibility, position updates, and every network edge. Record the source timestamp or date and effective signal date for each incorporated update.

## SHOULD-FIX — the placebo criteria cannot establish “no effect”

The conditions that random-link and time-shifted placebo series have `|NW t| < 2` are failures to reject a zero mean, not evidence that the placebo effect is negligible. The degree-preserving placebo is only required to fall below the observed IC's 95th percentile; it has no null-effect criterion. Thus “a placebo version … must show no such effect” is not tested as written. The harness randomization p-values also test the observed statistic against a placebo distribution; they do not by themselves establish that placebo ICs are practically zero.

**Proposed exact replacement for the placebo pass conditions:**

> For each of the three placebo families, report the placebo mean IC and its two-sided 90% Newey–West confidence interval using Bartlett lag 4. Treat “no material placebo effect” as established only when that entire interval lies within [−0.00577, +0.00577], where 0.00577 is the frozen cost-only reference IC defined below. For the observed-versus-placebo tests, use the harness finite-sample upper-tail randomization p-value `(1 + count(placebo_statistic >= observed_statistic))/(500 + 1)` and require p < 0.05 for each family. These requirements are separate: placebo equivalence does not replace observed-versus-placebo superiority, and neither replaces the primary IC t-statistic gate. Report all intervals and p-values.

Before using this text, make sure the placebo statistic's randomization and the confidence interval are computed on the same date-wise IC statistic, not a portfolio return.

## SHOULD-FIX — cost-only IC hurdle is valid for the 50% cap, but not conservative against the L1 reconciliation

D4's 0.00577 follows the stated harness formula with turnover 0.50, dispersion 0.030, and top fraction 5/30. It is internally consistent with a hard 50% benchmark-relative turnover cap and is not a calculation error. However, L1's reconciled top-five weekly cost-only hurdle is 0.0183 using 1.58751 incremental turnover versus EW30 and 0.030075 dispersion; 0.00577 is about 31.5% of that value. D4 should not present 0.00577 as the conservative hurdle. The different turnover assumptions must remain visible: 0.0183 is the stronger pre-result hurdle, while the actual cost engine and the 0.50 cap determine realized D4 costs.

**Proposed exact replacement for the cost-hurdle paragraph:**

> Report both fixed planning references. The cap-based cost-only floor is `break_even_rank_ic(turnover=0.50, return_dispersion=0.030, cost_per_side=0.0005, top_fraction=5/30) = 0.00577`. The conservative L1-reconciled reference is 0.0183, using L1's 1.58751 incremental weekly turnover versus EW30 and 0.030075 cross-sectional return dispersion; it is a conservative advance hurdle, not a D4 estimate. Require D4's primary mean IC to be at least 0.0183 as well as NW t ≥ 2.00 before portfolio testing. Independently enforce the 0.50 turnover cap, calculate actual share-level costs, and retain all net-return and Sharpe pass conditions. Do not substitute one reference for the other after results are observed.

If the coordinator decides not to add the 0.0183 conservative gate, change “conservative” language wherever it appears to “cap-based cost-only floor” and state explicitly that D4 may advance at an IC below the L1-reconciled hurdle.

## SHOULD-FIX — the round-wide Holm family is asserted but not frozen or fully enumerated

D4 lists five endpoints (primary IC, three placebo comparisons, and portfolio net excess), then delegates the complete family to `specs/r4_trials.md`. At audit time that file contains only the blank variant-log header; no endpoint family is recorded there. D4's alternative edge-weight variant is described as a mechanism diagnostic but is omitted from the five endpoints. D5/D6 and later direction endpoint counts also need to be included before any outcomes. Without an endpoint manifest, it is not possible to verify whether every reported inferential test is corrected.

**Proposed exact replacement for the “Registered endpoints and multiplicity” section:**

> Before any D4–D6 outcome is computed, the coordinator records a named endpoint manifest in `specs/r4_trials.md`. Include every preregistered statistic for which a p-value or inferential confidence claim will be reported: each primary and registered sensitivity/diagnostic mechanism test, every observed-versus-placebo randomization test, and each portfolio bootstrap excess-return test across all directions in this goal. In particular include the D4 alternative edge-weight IC if its inferential p-value or confidence interval is reported. Freeze the manifest before outcomes; apply Holm once across the full manifest and report raw and adjusted p-values for every endpoint, including failed or infeasible directions where a test was run. Do not count diagnostics without inferential claims as endpoints, and do not add or remove endpoints after seeing results. The DSR trial count remains 30 and is separate from this Holm family.

The five current D4 endpoints may remain the D4 subset only if variant 2 is explicitly descriptive (no p-value, confidence interval, or inferential claim) and the manifest includes all D5/D6 endpoints before testing.

## SHOULD-FIX — several timing and network implementation choices are not fully fixed

The primary CLV and return windows are correctly ordered: CLV uses sessions t−4 through t; the return starts at the next session's open and ends at t+5's close; no future price enters the signal. The main filing-date issue is covered above. Additional exact choices should be frozen to avoid implementation divergence: the first weekly formation date, whether stale scores remain eligible, minimum cross-sectional breadth, and whether the precomputed quarter-level edge file or the per-manager holdings feed determines the graph between filings. The prose says both “use” `13f_cosine_overlap_edges.csv` and rebuild after each manager filing. The edge-file schema is quarter-level (`report_date`, `parsed_manager_count`, `panel_availability_date`), while the holder and coverage files support per-manager filing dates.

**Proposed exact replacement for the graph-refresh, staleness, and weekly formation sentences:**

> At each signal close, rebuild the graph from each eligible manager's latest then-public holdings under the filing cutoff above; a missing manager report contributes no vector, not a zero vector. Do not use a synchronized-quarter edge row until its `panel_availability_date` is at or before the signal cutoff. Carry forward the last usable graph between filings. Define graph age as calendar days since the latest incorporated acceptance date; define quarter age by calendar-quarter difference between the signal date and that acceptance date. Stale means strictly more than two calendar quarters (equivalently, more than six calendar months); keep stale observations in the primary test, flag them, and report their count and manager coverage without selecting a freshness threshold after results. Calculate an IC only on dates with at least three finite score-return pairs, consistent with the harness Spearman implementation; require at least five finite scores to form the top-five portfolio. Otherwise record the relevant date as unavailable. Start the weekly formation schedule on the first date in the development period with a valid primary score and then form every fifth trading session on the fixed Dow market calendar; do not reset the schedule when names or graph coverage change.

This replacement resolves timing definitions but still requires the data builder to demonstrate that the graph can be reconstructed from the named per-manager holdings without using future filings.

## Consistency with `specs/r5_decisions.md`

- **Matches:** one coordinator-only holdout over 2010-01-01–2020-10-31; disclose missing KFT, DWDP, WBA and the UTX→RTX proxy; equal-weight benchmark over available names; DWDP window with and without; workers do not access holdout prices/returns/signals. The D4 development cutoff also respects the worker prohibition on pre-2020-06 Dow outcomes.
- **Matches with clarification:** carry the 13F network forward after the last public filing and flag observations more than two quarters stale. D4 includes the age/staleness requirement but should define the exact quarter-age calculation and whether stale observations remain in the primary test (replacement above).
- **Mismatch / possible look-ahead:** fixed Q2 2026 manager rank roster used for earlier holdout dates is not point-in-time; see BLOCKER 1. The binding decision permits L4 to build holdout link inputs, so the date-specific roster/positions can be prepared without opening holdout prices.

## Named 13F file existence and schema spot-check

All six files named in D4 exist. Only their header rows were read.

| File | Header/schema observed | Audit result |
|---|---|---|
| `13f_holder_by_dow_stock.csv` | `report_date, availability_filing_date, manager_cik, manager_name, accession_number, ticker, cusip, reported_issuer, share_class, value_usd_thousands, shares_or_principal_amount, amount_type` | Exists; has manager/security/value and date fields, but only a filing date is exposed in the header. |
| `13f_cosine_overlap_edges.csv` | `report_date, parsed_manager_count, panel_availability_date, ticker_i, ticker_j, cosine_13f_portfolio_value_overlap` | Exists; synchronized report-date edges and latest panel availability date; does not itself expose per-manager update timestamps. |
| `13f_filing_coverage.csv` | `manager_cik, manager_name, report_date, availability_filing_date, status, accession_or_error` | Exists; date-only availability field in schema. |
| `13f_manager_rank_q2_2026.csv` | `rank, manager_cik, manager_name, table_value_usd_thousands, accession_number, filing_date, report_date` | Exists; explicitly Q2 2026 ranked roster. |
| `13f_top50_holdout_filing_metadata.csv` | `q2_2026_rank, manager_cik, manager_name, report_period, earliest_filing_date, accession_number, edgar_filing_found, check_status` | Exists; metadata-only coverage schema, keyed to Q2 2026 rank. |
| `13f_top50_holdout_manager_summary.csv` | `q2_2026_rank, manager_cik, manager_name, quarterly_reports_found, quarters_checked, first_report_period, last_report_period` | Exists; coverage summary schema, keyed to Q2 2026 rank. |

## NIT — minor exactness

The statement “the 50-manager roster” should say whether the roster can contain fewer than 50 managers on early dates; the point-in-time replacement above makes that explicit. The dossier contains claims about SEC filing-data coverage, but this audit did not verify citations or source correctness because the assigned scope was pre-freeze design and schema review.

**Proposed exact replacement for “Use the roster of 50 managers in the rank file for the panel”:**

> Use up to 50 managers selected by the point-in-time ranking rule above; if fewer than 50 managers have a qualifying public filing at a signal date, use all qualifying managers and report their count.
