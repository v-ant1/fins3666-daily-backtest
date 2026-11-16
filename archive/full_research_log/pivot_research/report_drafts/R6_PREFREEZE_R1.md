# Hostile pre-freeze review: R1

**Verdict: FIX.** The schedule timing, placebo, statistical hurdles, and holdout rule are otherwise well specified and consistent with the fixed R6 goal. Fix the Dow payer-count rule before freeze because the claimed 50% active share is not guaranteed when the available-name EW30 benchmark has fewer than 30 constituents.

## Scope

Reviewed `specs/r6_prereg/R1.md`, `specs/r6_goal.md`, and the relevant decisions in `specs/r6_decisions.md`, including decisions 27, 76, 94–96. This is a design-only review; I did not access or compute project outcomes, returns, or holdout values.

## Gate-by-gate review

### Timing and sealed-data boundary

The first registered formation is 2021-06-30. Its trailing 12-calendar-month event window begins 2020-06-30, so the signal does not require any event from before the prohibited 2020-06 boundary. The broad yfinance request starts 2020-06-01, but the signal definition must retain only events no more than 12 calendar months old at each formation; for 2021-06-30, events before 2020-06-30 are outside the signal window. The event date must remain strictly earlier than the formation close. Thus the proposed start date is compliant as written; do not move the first formation earlier. The file’s explicit event-date limitation and decision 95 correctly describe this as an ex-date schedule proxy, not a payable-date record.

### Dow payer count and active share — fix required

For an equal-weight portfolio holding `q` names against an equal-weight benchmark of `n` available names that contains the portfolio names, active share is `1 - q/n` when `q ≤ n`. With 30 available names, 15 holdings give exactly 50%; with 29 available benchmark names, 15 holdings give only 48.3%. Therefore the draft’s claim that “at most 15 names” guarantees at least 50% active share against the same-date available-name EW30 benchmark is false when price gaps reduce `n` below 30. The separate realized-average-active-share fail gate is correct, but does not make the target claim true.

**Exact fix:** at each rebalance, let `n` be the number of eligible Dow constituents in the same-date EW benchmark after applying the registered availability rule. Hold the top `min(15, floor(n/2))` predicted payers, or all qualifying payers if fewer; if none qualify, hold cash as registered. Keep tie-breaking and the turnover cap unchanged. Record realized active share against that same available-name benchmark after the turnover cap, and retain the goal’s average active-share ≥50% gate. This makes the target’s mathematical active-share claim valid without changing the dividend signal or adding a result-dependent rule.

The current choice to hold every payer when fewer than the cap qualify is coherent: it avoids inventing non-payers as holdings. A zero-payer month held in cash has 50% active share versus a fully invested EW benchmark, but that fact does not waive the excess-return or Sharpe requirements.

### Placebo validity

The within-date, within-SIC2 permutation keeps each sector’s payer count fixed and tests whether the observed payer/non-payer spread is unusual conditional on those counts. The 500 draws, fixed seed, upper-tail randomization p-value with the plus-one correction, and requirement to exceed the null’s 95th percentile are a valid, conservative registered placebo. The comparison is non-overlapping with future returns in the sense that only prior event dates define payer flags; the labels are shuffled within the cross-section at formation. Keep the eligible-name mask fixed and never treat missing dividend history as a non-payer.

### Hurdle and goal alignment

The mechanism hurdle (positive mean payer-minus-non-payer SIC2-stratified spread and one-sided NW t≥2, lag 3) matches criterion 3. The 250-name threshold is an input-coverage stop, not an outcome threshold. The power section calls out the 53 bp effect as a planning assumption, reports under-80% power at the more conservative 41 bp case, and does not change the registered gate; that is appropriately candid and consistent with decision 94’s instruction to use a plausible effect for the power gate.

The portfolio’s 0.05% per-side costs, 50% turnover cap, positive net excess return, net Sharpe above EW30, active-share requirement, and Holm-adjusted one-sided bootstrap p<0.05 implement criterion 4. The 50% turnover route is permitted by the goal’s “turnover ≤50% or costs <25% of gross edge” language; it is not stricter than the goal. The registered placebo and mechanism gates are the expected criterion-3 progression gates, not added portfolio-pass conditions.

### Holdout rule

The one-shot section states precisely the goal’s criterion 5: same net-excess sign as development, net Sharpe above EW30, and one-sided block-bootstrap p<0.10. It explicitly excludes an extra holdout t-statistic or placebo hurdle and says the holdout cannot rescue a failed development gate. Coordinator-only access and the 2009 warm-up are stated; this matches decisions 95–96. Do not let workers inspect sealed event values.

## Required change before freeze

Apply the available-name payer-count correction above and update the active-share claim. Then the draft is ready for coordinator freeze; no other design or pass-threshold change is required by this review.
