# Consistency audit: R5 and evaluation drafts

**Scope.** Cross-checked the D4–D6 figures in `R5_FINAL_DRAFT.md`, `EVALUATION_DRAFT.md`, `TESTING_VALIDATION_DRAFT.md`, and `HOLM_INTERIM.md` against `r4_harness/runs/D4/MECHANISM_RESULTS.md`, the corresponding D5/D6 result files, `REPRO_D4.md`, `REPRO_D5_D6.md`, and `specs/r4_trials.md`. Drafts were not edited. This is a document-level audit; no outcomes were recalculated.

## BLOCKER

### EVALUATION_DRAFT misstates the index-change status

In its direction table, EVALUATION_DRAFT says the index-change proposal was “Not selected, preregistered, or tested.” That is incomplete and misleading: the direction received an input-only feasibility assessment, was ruled **infeasible before outcome testing** at three independent announcement dates against a fixed minimum of 20, and used zero variants (decision 27; feasibility report). It was not an outcome test, but the pre-outcome feasibility work did occur.

**Suggested replacement:** “Index-change peer-pressure proposal | Infeasible before outcomes | The input-only review found 3 independent DJIA announcement dates, below the fixed minimum of 20; no outcome test was run and zero variants were used.”

## SHOULD-FIX

### 1. Original pressure-plus-heat outcome numbers are not supported by the source set named for this audit

EVALUATION_DRAFT reports the original design’s pressure and heat ICs/t-statistics, cumulative portfolio returns, Sharpe ratios, and turnover: 0.0034, −0.0015, 0.34, −0.12, +133.2%, +102.6%, +83.3%, +101.7%, 0.64, 0.92, and 161.2%. Those figures do not appear in the D4–D6 mechanism result files, the D4/D5/D6 reproduction reports, or `specs/r4_trials.md`; they therefore cannot be verified from the source set requested here. This is a provenance gap, not evidence that the values are wrong.

**Suggested fix:** cite the exact prior result artifact/table supporting each baseline figure (including the sample, cost convention, and whether return figures are cumulative), or remove the figures until that source is supplied. “Some individual components showed short-lived one-day continuation” also needs a source citation or should be removed.

### 2. R5_FINAL_DRAFT’s strategy-variant tally is not auditable from the trial log

R5_FINAL_DRAFT says D4–D6 comprise 7 active strategy variants (2+2+3), and that D7 would make 8/30 with 22 remaining. `specs/r4_trials.md` explicitly fixes a 30-variant budget, but its 23 numbered rows are outcome/test entries: controls and sensitivity tests are mixed with primaries, and D6’s five entries are duplicated for accidental and official runs. The log does not contain a direct unique-strategy-variant tally that substantiates 7 or 8. The 21 unique Holm endpoints are a separate, correctly identified count; they must not be used as the variant count either.

**Suggested fix:** cite the versioned variant roster that defines the 2+2+3 count, and mark D7’s addition as conditional on authorization. If no such roster is authoritative, state only the fixed 30-trial DSR input and the 23 logged rows / 21 unique Holm endpoints, explicitly saying these do not establish the number of unique variants.

### 3. Testing-validation holdout wording should disclose the accidental DWDP exposure

TESTING_VALIDATION_DRAFT says “Workers did not use holdout prices, returns, or signals.” `specs/r4_trials.md` records that L4 accidentally saw rendered historical DWDP OHLCV rows during an availability check, though no values were computed or used and L4 was excluded from later research work. The current sentence may be technically accurate about use, but it hides the exposure incident that the report is required to disclose.

**Suggested replacement:** “No worker computed or used holdout prices, returns, or signals. During an availability check, L4 accidentally saw rendered DWDP historical OHLCV rows; no values were computed or used, and L4 was excluded from later hypothesis, preregistration, and implementation work.”

### 4. D4 significance and raw p-value need one plain explanation

The D4 estimate, IC date count, NW t-statistic, and registered positive-direction raw p-value agree across EVALUATION_DRAFT, TESTING_VALIDATION_DRAFT, R5_FINAL_DRAFT, the D4 result file, and `REPRO_D4.md`. However, the reader is told both that the result is “significantly negative” and that the registered positive-direction raw p is 0.992 (or 0.992229), without explaining that these refer to different directional questions. The result file’s raw p is for the preregistered positive alternative; the negative t-statistic supports the opposite direction. Avoid letting the large registered one-sided p look like a contradiction or silently relabeling it as a two-sided p.

**Suggested addition:** “The registered p-value tests the predicted positive effect, so it is near one when the estimate is negative. The negative t-statistic instead points opposite to that prediction; we report the reversal as a wrong-sign finding and do not use it to advance or trade the signal.” If the final report wants a two-sided p-value, source it from a documented output rather than deriving it in prose.

### 5. D7 placeholder/status should reflect the unresolved freeze-readiness issues

The D7 placeholders in EVALUATION_DRAFT and TESTING_VALIDATION_DRAFT are appropriate because no D7 outcome is available in the audited result set. EVALUATION_DRAFT’s table says “Pre-registration in draft; not frozen or tested,” which is directionally accurate; its closing sentence says D7 is untested. For the final version, call it **pending / not ready for freeze**, and retain the placeholder until the gate chronology and Holm endpoint-count discrepancy are resolved. Do not state a D7 gate pass based on the holdout-source check alone; decision 30 calls that a warning, not the development-gate verdict.

## NOTE — checks with no numerical mismatch found

### D4

The following reported figures match `MECHANISM_RESULTS.md`, `REPRO_D4.md`, and the trial log: primary mean IC −0.018073999 (rounded −0.0181), NW *t* −2.4194916 (rounded −2.42), lag 4, and 1,479 valid IC dates. Variant 2 is −0.00683667 with *t* −0.7882. The D4 comparison values and equivalence-test raw p-values in the R5/Holm tables match the result file and rows 17–23 of the trial log. D4-9 was not run. The descriptions of all placebo gates failing and the opposite-sign reversal are consistent with the source. The 1,488-session input sample also matches the source files.

### D5

The reported primary mean IC 0.007455, NW *t* 0.5644 at lag 4, one-sided raw *p* 0.286249, 293/293 input-gate dates, 11 directed pairs per date, null 95th percentile 0.015677, observed percentile 69.4%, and randomization *p* 0.307385 match D5’s result file and `specs/r4_trials.md`. The reverse-edge and shifted-control ICs/p-values, 60-session sensitivity 0.003702 / *t* 0.2675, and independent primary reproduction match. The 1,463 daily IC observations and 293 formation dates in the evaluation discussion match `REPRO_D5_D6.md`; that report also notes only 292 formation dates have a complete five-session forward return, which is distinct from the 293-date input gate. D5’s portfolio endpoint was not run.

### D6

The reported primary beta 0.0769213, NW SE 0.100374, *t* 0.766344, lag 11, raw *p* 0.221736, 62 targets, 94.6th percentile, placebo 95th percentile 0.0949808, and randomization *p* 0.0558882 match the D6 result file and duplicated trial rows. The reverse-direction primary-horizon beta 0.00156874 / *t* 0.0762576 and the six-minus-one sensitivity beta 0.33799 / *t* 2.62323 / raw *p* 0.004355 also match; the sensitivity is correctly described as unable to rescue the primary. D6’s independent reproduction matches the primary beta and t-statistic. D6-6 was not run.

### Holm table and ledger

All 21 raw and interim Holm-adjusted p-values in `HOLM_INTERIM.md` match the values copied from the trial log/result artifacts; the smallest adjusted value, 0.09145507 for D6-4, is correctly identified as a non-primary sensitivity. The family composition (9 D4 + 6 D5 + 6 D6) and three p=1 interim assignments for unrun portfolios are disclosed. The D6 duplicate rows are correctly counted once per endpoint, not as extra Holm tests. The `specs/r4_trials.md` budget of 30 is correctly distinguished from both 21 unique Holm endpoints and 23 numbered log rows in R5_FINAL_DRAFT.

## Jargon likely to need a short definition

For a third-year finance marker, define these once at first use or add a short glossary: **CLV** (where the close falls within the day’s high–low range), **IC / rank IC** (the cross-sectional correlation between the signal ranks and subsequent-return ranks), **NCP** (the network-propagated pressure score), **SIC** (the industry classification used to group firms), **13F** (quarterly institutional holdings disclosure), **Newey–West / NW t** (a standard error adjustment for serial dependence), **Holm correction** (a multiple-testing adjustment controlling the chance of any false positive in a family), **DSR** (deflated Sharpe ratio, adjusting for strategy selection), **placebo** (a comparison after deliberately breaking the proposed link/timing), and **EW30/EW5** (equal-weight benchmarks over 30 Dow names or five ETFs). Also explain “20-session shift,” “six-minus-one / 12-minus-1,” “circular block bootstrap,” “active share,” and “point-in-time” the first time they appear. `HOLM_INTERIM.md` explains the mechanics of Holm but not why the family is adjusted; one short plain-English sentence would make the table easier to interpret.

## Overclaim and precision watchlist

- EVALUATION_DRAFT says the “true links did not beat the randomized-link comparison.” The numbers support failure to outperform the registered null at the required cutoff; phrase it as “did not exceed the registered randomized-link threshold,” not as proof of no effect.
- EVALUATION_DRAFT says the graph “captured co-movement and smoothed pressure.” This may be a design description, but the listed mechanism results do not establish that interpretation; support it with the original graph diagnostics or phrase it as what the construction was intended to do.
- R5_FINAL_DRAFT’s conclusion that D4 is “consistent with short-term reversal” is appropriately bounded to the tested sample. Keep “consistent with” and avoid generalizing reversal to all Dow stocks, all periods, or all network pressure.
- TESTING_VALIDATION_DRAFT’s methodological statements about the 10-session, 5,000-draw bootstrap, 0.05%-per-side costs, positive net excess, and higher net Sharpe are not verifiable from the mechanism-result/reproduction/trial sources in this audit. They may be correct frozen portfolio rules, but cite the relevant frozen specs. State clearly that none was applied to D4–D6 because no portfolio advanced.
- The holdout roster gaps, event feasibility counts, ETF daily-history counts, and D7 373-filing check in R5_FINAL_DRAFT are not established by the D4–D6 results/reproduction/trial sources audited here. They should retain citations to their specific availability/feasibility reports; they are not numerical mismatches found in the requested source set.

**Overall:** no D4–D6 primary statistic or Holm-table numerical mismatch was found. The index-change status in EVALUATION_DRAFT needs correction; the original baseline values and unique variant tally need clearer provenance; and the drafts should explain key terms and disclose the DWDP exposure incident without implying that an outcome was computed from it.
