# R9 D-family exploratory trial log

Worker tag: L-D1
Created: 2026-11-11 (before any new D1 dev-data computation)
Scope: diagnosis of the already-run D1 signal; no strategy selection, rescue, portfolio run, or holdout use is authorized. The source must be the saved D1 development input bundle, restricted to dates on or after 2020-11-27, plus existing saved J1/J2 development outputs. Never access pre-2020-11-27 price, return, or volume values.

## Trial tally

| ID | Status | Precommitted analysis | Data | Purpose |
|---|---|---|---|---|
| L-D1-E01 | Completed on attempt 5; five attempts counted | One diagnostic suite: recompute the frozen D1 negative five-session FINRA ratio score's date-wise Spearman IC on the existing five-session forward-return definition, summarize those saved/derived date ICs by calendar year, then compute same-sign IC summaries for horizons 1, 2, 10 and 20 sessions as sensitivity only; report eligible-name counts and missing-score/return coverage by year and horizon. No sign selection, horizon selection, portfolio simulation, or inferential pass claim. | Development only, formations >=2020-11-27 and outcomes wholly <=2026-10-30; 2020-06 warm-up rows may not be read as values. | Exploratory near-miss diagnosis. Counts as one trial bundle; no variants beyond the named horizons. |

## Trial-free descriptive check

The planned D1-vs-J1/J2 signal/rank correlation on overlapping development formation dates and ticker identities is a descriptive dependence check, not a candidate test or trial. D1 is ranked in its registered orientation (higher negative-pressure score = lower raw FINRA ratio); J1/J2 use the registered J1 signal orientation. Report pairwise date-wise rank correlations and pooled rank correlation, state the shared mask, and do not use results to change any signal or registration.

No outputs exist under this log yet. Every computation above is restricted to the named analyses; no additional horizons or specifications may be added after results.

## Attempt ledger update

- L-D1-E01 attempt 1 ran and failed before any IC or signal-correlation result was produced: the post-cutoff FINRA reader's date-boundary assertion rejected its parsed date range. Count this failed attempt in the tally. A single corrective attempt is now pre-registered as L-D1-E02: inspect only post-cutoff source date labels/universe labels to identify the parser mismatch, correct the reader, then rerun exactly the E01 analyses without changing the dates, variables, masks, or horizons. No further retry is authorized by this log.

| ID | Status | Precommitted analysis | Data | Purpose |
|---|---|---|---|---|
| L-D1-E02 | Logged; not yet run | One parser-correction retry of E01, after checking only post-cutoff date/universe labels; exactly the same E01 outputs and no extra analyses. | Same post-cutoff development-only sources. | Correct failed exploratory attempt; counts as a second attempt. |
- L-D1-E02 attempt 1 (corrective retry) ran and failed before any IC or correlation statistic: the runtime's pandas version does not accept `axis` in `DataFrame.rolling`. Count this failed retry. One final mechanical compatibility retry is now pre-registered as L-D1-E03: transpose before rolling to preserve the same five-session trailing arithmetic mean; then run exactly E01's registered diagnostics once. No more reruns are allowed.

| ID | Status | Precommitted analysis | Data | Purpose |
|---|---|---|---|---|
| L-D1-E03 | Logged; not yet run | Mechanical pandas compatibility correction only (transpose rolling operation); exact E01 analyses and masks/horizons unchanged. | Same post-cutoff development-only sources. | Final corrective attempt; counts as third attempt. |
- L-D1-E03 attempt 1 failed before producing any IC/correlation estimate because the staged PIT roster is under `r6_data/`, not `r6_D1/`. Count this failed attempt. A final path-only correction is registered as L-D1-E04: point to `r6_data/sp500_pit_roster.csv` and run the exact E01 analysis once. This exhausts the logged diagnostic retry budget; no further run is authorized.

| ID | Status | Precommitted analysis | Data | Purpose |
|---|---|---|---|---|
| L-D1-E04 | Logged; not yet run | Path correction only; exact E01 analyses, date limits, masks, and horizons unchanged. | Same post-cutoff development-only sources. | Final attempt, counts as fourth attempt. |
- L-D1-E04 attempt 1 reached the registered calculation but failed in the descriptive-correlation assembly: the tuple included a source J1 value and the four-field tuple was unpacked as three fields. No report output was written. Count this attempt. One final mechanical tuple-unpacking correction is logged as L-D1-E05; run the same registered E01 analysis once, with no specification changes. This is the final attempt.

| ID | Status | Precommitted analysis | Data | Purpose |
|---|---|---|---|---|
| L-D1-E05 | Logged; not yet run | Tuple-unpacking correction only; exact E01 analyses, dates, masks, and horizons unchanged. | Same post-cutoff development-only sources. | Final attempt, counts as fifth attempt. |

## Final status

L-D1-E01 completed on the fifth counted attempt (E05) and wrote `report_drafts/repro/D1_DIAGNOSTIC_OUTPUT.json`; attempts E01-E04 failed before producing statistics. The date-wise and horizon outputs are exploratory. The trial-free rank comparison was completed descriptively. No further computation, portfolio test, holdout access, or D2 registration was performed.

