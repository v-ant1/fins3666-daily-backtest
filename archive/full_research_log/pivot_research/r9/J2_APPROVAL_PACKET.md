# J2 holdout approval packet (HELD until L-IDX5 decides S2)

**Status:** DRAFT, not yet sent to the user. No holdout data has been opened.

## What you would approve
One run, once, of the frozen strategy J2 on the sealed S&P 500 / Dow holdout, 4 Jan 2016 to 30 Oct 2020 (1,217 trading days). The result is final: a fail is reported, not fixed.

| Item | Value |
|---|---|
| Strategy file | `specs/r9_prereg/J2.md`, SHA-256 `ed8998e8...c8ef39b` (content hash `23968857...cf80`) |
| Holdout file | `sealed_holdout_sp500/J2_HOLDOUT.npz`, SHA-256 `7b405c9b...c589db` (re-verified by coordinator) |
| Code | `r9/j2_frozen.py` SHA-256 `85e643e9...4020`; `r9/holdout_runner.py` SHA-256 `52c9c06b...9a02` (`r9/j2ready/J2_CODE_HASHES.md`). Synthetic end-to-end dry run passed (refuses without approval, refuses on hash mismatch, runs once, refuses a second run); dev V5 still reproduces 40.1251% / Sharpe 0.9239 |
| Holdout start | First weekly formation with four valid J1 scores (mechanical, `j2_frozen.py:217-224`); no chosen start date |
| DSR variance | Frozen: primary V = 0.0000841539 decides; null 1/(T-1) reported alongside (`specs/r9_dsr_variance_freeze.md`) |
| Holdout family | **J2 alone** (S2 exhausted on evidence: final index-flow run, pooled dev net -0.63% vs MDE 1.36%; holdout missing 5.88% > 3%. Full search history disclosed) |

## J2 in one paragraph
Each week, rank Dow stocks by their 5-day return relative to same-industry (SIC2) peers, averaged over the last four weeks; hold the five biggest losers equally weighted, trading at the next open with 0.05% cost per dollar traded, against an equal-weight Dow benchmark. It is J1 (weekly industry-relative reversal) with signal smoothing, picked mechanically from 12 pre-logged variants.

## Pass rule (all must hold)
Net cumulative return above EW Dow; net Sharpe above EW Dow; one-sided block-bootstrap p < 0.05 (Holm-adjusted if S2 joins); primary DSR > 0.95 with 15 trials.

## Honest odds
About **10-17%** chance of passing all gates (planning simulation on 1,215 days; 17.4% if the 2020-2026 effect is real at full size, 13.0% at the V3-V5 average, 9.6% at half). Under the null-variance sensitivity: 3-6%.

## Disclosed limitations
- 39 of 631 holdout S&P identities have no SEC industry code and are ineligible on those dates (dev comparison: 11 of 614).
- 2 of 631 identities lack prices (SNDK, STI).
- A worker accidentally displayed raw 2018-2019 Dow FINRA short-sale rows; no prices or returns; J2 is price-only and unaffected.
- J2 was refined after seeing J1's 2020-2026 results; only the holdout result is confirmatory.
- Full search history: R6 7 frozen strategies + ~71 paper screens; R7 power work; R9 12 J2 variants, D1 diagnosis (5 runs), S2 rounds 1-3 (all dropped pre-outcome), breadth check (NO-GO), dev evidence tests (7 attempts), index-add tests (L-ADDS, L-IDX4 crash x2, L-IDX5).
- Implementation corrections before the run: DSR scaling bug, V1 empty-book bug, run_frozen_j2 added, roster in-place edit restored.

## To approve
Reply "approve J2 holdout run" (with the family filled in). The coordinator then creates `specs/r9_HOLDOUT_APPROVED.txt`, runs once, and sends the result to the supervisor for sign-off.





