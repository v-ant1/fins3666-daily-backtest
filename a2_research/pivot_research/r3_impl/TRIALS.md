# R3 implementer cycle 1 trial inventory

Unique active parameterizations added this cycle: **6** (MAX21 at a=0.8/1.0; HIGH63/HIGH126 at a=0.8; IDIO63/IDIO126 at a=0.8). With the coordinator's approximate prior inventory of 76, the DSR trial count used here is **82**. The precise historical count is still approximate, and these related variants are not independent.

## Portfolio evaluations and technical attempts

| Attempt | Completed work | Outcome / accounting |
|---|---|---|
| 1 | Tried to load Dow using the 2020 roster through 2026-10-30 | Stopped at WBA's absent later observations before any candidate portfolio run; zero active variant evaluations. |
| 2 | Split Dow data by point-in-time roster and began selection | Stopped when the full 126-session lookback was unavailable at 2020-11-25; three Dow selection candidate runs (MAX21_a08, MAX21_a10, HIGH63_a08) had run. |
| 3 | Full selection plus frozen tests completed; final console summary hit a results-key error | 8 valid selection candidate-universe series and 12 frozen test-period evaluations completed; four 126-session candidate-universe attempts failed the lookback guard. All result files had been written before the summary error. |
| 4 | Repeated complete selection and test pass after repairing summary lookup | 8 valid selection candidate-universe series and 12 frozen test-period evaluations completed successfully; four 126-session candidate-universe attempts failed the lookback guard. |

Thus, 6 unique candidate definitions were evaluated; 40 valid candidate-series runs were completed across the two complete passes, plus 3 complete partial-selection runs in the aborted attempt. Eight candidate-universe attempts for the two 126-session definitions failed the preregistered history check across the two full passes; they were not silently shortened or counted as valid measured results. The first failed data-load attempt produced no portfolio series. EW30 benchmarks were also rerun alongside each applicable candidate but are not counted as active variants.

The two full passes are exact reruns, not additional parameterizations or tuning. They are disclosed here because the task requires technical and abandoned executions to remain visible.


# Cycle 2 cumulative update (2026-11-10)

Cycle 1 left an approximate cumulative trial count of 82 (prior estimate about 76 plus six cycle 1 variants). Cycle 2 added exactly six unique parameterizations: ILLIQ21_a08, ILLIQ63_a08, SKEW42_a08, SKEW63_a08, DOWNBETA63_NEG_a08 and DOWNBETA63_Q25_a08. The DSR count reported in `RESULTS_cycle2.md` is therefore **88**; candidates across all cycles are correlated and the historical base remains approximate.

| Cycle 2 run set | Count | Status |
|---|---:|---|
| Selection candidate-universe series | 12 (6 variants x 2 universes) | Completed; all six variants valid and below the 50% turnover ceiling in both selection universes. |
| Frozen development test candidate series | 12 (3 frozen variants x 4 periods) | Completed once per frozen variant and period; no retuning. |
| Future-truncation checks | 48 signal/weight comparisons | Passed: 18 earlier Dow, 12 recent Dow, 18 cross-asset. |
| EW30 engine parity checks | 2 benchmark comparisons | Completed on selection window; harness and validated engine return matched to six decimals in percent (Dow 14.141439%; cross-assets 0.785780%; 527 marks each). |
| Failed/abandoned candidate backtests | 0 | None. |

There were no cycle 2 strategy reruns or additional variants. EW30 parity checks and invariance comparisons are validation, not additional active parameterizations.

# Cycle 2 execution inventory

The unique cumulative trial count is approximately **88** (82 inherited after cycle 1 plus six cycle 2 parameterizations). These variants are related, and 88 remains an approximate independent-trial input for DSR.

| Run set | Candidate-series count | Notes |
|---|---:|---|
| Selection | 12 | Six variants x Dow and cross-asset; all valid and at or below 50% turnover. |
| Frozen development tests | 12 | Three choices x four fixed windows, each run once. |
| Ledger verification rerun | 1 | SKEW63 on the Dow selection window, solely to validate the independent share-ledger reconciliation added after the main run; no test window or selection changed. |
| Generic price-folder API parity | 3 | Each frozen variant on the Dow selection window; terminal wealth matched the array harness exactly. This exercised the coordinator-facing input adapter and did not use holdout data. |
| EW30 parity | 2 benchmark checks | Dow and cross-asset selection windows matched the copied validated engine to six decimals in percent. |
| Future-truncation checks | 48 signal/weight comparisons | Passed across eligible sampled dates and universes. |
| Failed/abandoned backtests | 0 | No candidate or data run failed. |

No cycle 2 test-period strategy was rerun. The four extra active series are verification runs on the registered selection window and are disclosed rather than treated as new parameterizations.


# Cycle 3 cumulative update (2026-11-10)

Cycle 2 ended at an approximate cumulative count of 88. Cycle 3 added six unique candidates (IDIOSKEW63_a08, COSKEW63_a08, DIST63_a08, DIST63_a10, GAPVOL63_a08, GAPSHARE63_a08), so the DSR count used is **94**; all are correlated and the inherited count is approximate.

| Cycle 3 run set | Count | Accounting |
|---|---:|---|
| Selection portfolio series | 12 | Six candidates x Dow/cross-asset; all valid. |
| Frozen development test series | 12 | Three frozen choices x four registered test periods, once each. |
| Generic-folder parity reruns | 3 | Frozen skew and distribution on Dow selection, gap-share on cross-asset selection; wealth matched exactly. |
| Future-truncation comparisons | 48 | All passed: 18 Dow early, 12 Dow recent, 18 cross-asset. |
| Cost and ledger validation | 1 engine self-test plus per-run reconciliation | Passed. |
| Failed/abandoned candidate series | 0 | None. |

The three folder-adapter reruns are selection verification, not new parameterizations. No development test was rerun and no sealed-holdout data was accessed. See `RESULTS_cycle3.md` and `outputs_cycle3/run_inventory.json`.


# Cycle 4 cumulative update (2026-11-10)

Cycle 3 ended at approximate count 94. Cycle 4 added four unique definitions (HVOL21_K15, HVOL21_K20, WEEKDAY63_SHR10, MONTHPHASE63_SHR10); cumulative DSR count is **98**. Prior counts are approximate and variants correlated.

| Cycle 4 run set | Count | Accounting |
|---|---:|---|
| Selection candidate-universe attempts | 8 | Four definitions x Dow/cross-asset; weekday and month-phase completed, both high-volume candidates invalid in both universes under the preregistered history/event rules. |
| Frozen active development tests | 8 | Two active frozen families x four periods, completed in final run. |
| EW30 fallback benchmark periods | 4 distinct | Same fixed test benchmarks shared across candidates and the HVOL EW30 fallback. |
| Flat-folder API parity reruns | 2 | Weekday and month-phase on Dow selection; max wealth differences <3e-15. |
| Supplied-data future-truncation comparisons | 24 | First/middle/last eligible selection dates for signals with valid outputs; all passed. |
| Synthetic future-truncation checks | 4 | All formulas passed on controlled data with enough qualifying HVOL events. |
| Failed technical attempts | 1 loader failure + 1 future-calendar failure | First stopped before portfolio runs; second completed weekday tests but aborted during month-phase due missing future calendar dates. Exact test reruns after calendar fix are disclosed in RESULTS_cycle4.md. |

The final cycle 4 result is in `RESULTS_cycle4.md`. No sealed-holdout data was accessed. Existing cycle 3 `run_idioskew63_a08` remains available; cycle 4 wrappers and flat-folder calls are documented in that report.
