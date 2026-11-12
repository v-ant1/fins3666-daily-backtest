# J1 Runner Review

**Verdict: FIX.** The current runner implements most frozen choices and the synthetic suite passes, but one peer-cohort mismatch affects the registered outcome and the embedded diff test can pass with incorrect numeric declarations. The published normalized prereg diff is clean; the review below identifies the remaining fixes before the runner is ready.

## Scope and checks

I reviewed `r6_J1/run_j1.py` against the frozen `specs/r6_prereg/J1.md`, plus its synthetic tests, runner map, and saved prereg-diff artifacts. I ran only synthetic tests and the prereg-diff check; I did not pass `--execute`, load the staged price bundle, calculate project outcomes, or access holdout data.

- `python -m unittest r6_J1.test_j1_synthetic -v` — **9 tests passed**.
- `python -m r4_harness.prereg_diff r6_J1/J1_PREREG_DIFF_SOURCE.md r6_J1/prereg_diff_config.json` — **matches; no differences**.
- The frozen-date/hash test passes, and the guarded entry point refuses without `--execute` before reading input files or taking a lock.

## Frozen choices that match

| Requirement | Runner evidence | Review |
|---|---|---|
| Formation cadence and signal | `run_j1.py:150-187, 536-545`; starts at 2020-11-27, forms every fifth session, computes adjusted-close `t-5` to `t`, and subtracts the leave-one-out SIC2 mean | Matches. |
| Timing and registered direction | `run_j1.py:189-208`; forward leg is adjusted open at `t+1` to adjusted close at `t+5`; `_direction_ic` negates the raw score | Matches the negative raw-signal prediction and positive direction-adjusted test. |
| NW inference | `run_j1.py:49-50, 545-550`; uses the shared masked IC engine with lag 4 and a one-sided normal tail on the direction-adjusted NW t | Matches. |
| SIC2 placebo | `run_j1.py:261-287, 634-637`; permutes scores within each date/SIC2 group, uses 500 draws and seed 20261111, calculates the +1 tail p-value, and serializes every draw | Matches. The unchanged outcomes and eligible mask are used across draws. |
| Dow selection and execution | `run_j1.py:290-298, 317-379, 585-609`; descending sort of the negated score selects the five lowest raw scores; trades at the next open and moves pro rata from EW30 | Matches the direction, K=5, and next-open execution. |
| Turnover, costs, and portfolio diagnostics | `run_j1.py:344-379, 481-515`; caps total buys-plus-sells/NAV at 0.50 including initial transition, charges 0.0005 per traded dollar, and reports turnover, active share, costs, EW30, excess returns, Sharpe comparison, drawdown, and cost/gross-edge ratio | Matches. The code retains cap-bind flags and actual turnover values. |
| Bootstrap, DSR, and endpoint slots | `run_j1.py:481-515, 518-549, 610-644`; 10-session circular bootstrap, 5,000 draws, seed 20261111; cumulative R6 trial count; writes H7-H9 rows and reports raw/Holm p-values | Matches the registered settings. H9 is not computed unless the raw mechanism and placebo gates pass; a blocked H9 slot is assigned p=1 only for Holm accounting. |
| Run guard | `run_j1.py:697-715`; `@guarded_runner` wraps the registered-trial callback | Matches frozen/hash validation, explicit `--execute`, lock, and existing mechanism-artifact checks. |

The loader also limits the accepted calendar to 2020-06-01 through 2026-10-30 (`run_j1.py:109-132`). No holdout path is used.

## Required fixes

1. **Use the same eligible peer cohort for the forward peer mean.** In `build_j1_panels`, the signal cohort at lines 178-187 requires a valid trailing five-session return. The forward cohort at lines 191-199 groups by SIC2 and forward-bar availability only. A peer can therefore enter `peer_fwd5` despite lacking the trailing bars required to be an eligible peer at formation. Build the forward groups using the formation-date eligible set as well, for example by passing `active[:, d] & np.isfinite(trailing)` as the roster mask to `_groups` together with `fwd[:, d]`. Add a synthetic missing-trailing-bar case that verifies this peer is excluded from every target's forward peer mean.

2. **Make the embedded diff test exercise the documented clean diff.** The external command above compares the normalized frozen copy and the JSON config correctly. However `run_j1.py:69-89` still defines a stale `DIFF_CONFIG` (`turnover_cap: 0.40`, `top_fraction: 5.0`, and `draws: [500, 0]`), and `test_j1_synthetic.py` calls `prereg_diff(j1.PREREG, j1.DIFF_CONFIG)`. That raw parser/test pair reports a false match by treating the 0.40 cost-hurdle reference as the turnover cap, the numerator 5 as the fraction, and a date token as a draw count. Update the synthetic test to load/use `prereg_diff_config.json` against `J1_PREREG_DIFF_SOURCE.md`, or otherwise assert the runtime values directly: cap **0.50**, cost-hurdle reference turnover **0.40**, top fraction **5/30**, and draws **500 / 5,000**. The dated normalized CLI result can remain the saved diff artifact.

3. **Fail closed on the published input-only coverage gate before calculating forward labels.** `INPUT_QA.md` and `formation_coverage.csv` document coverage, but `_analyze` does not read a frozen coverage manifest or compare its hashes/counts. Further, `validate_feature_bundle` calls `build_j1_panels` at lines 229-231, which also constructs forward returns at lines 189-199 while this input-feature validation is in progress. Separate a signal-only/input-QA validator from forward-panel construction; verify the expected staged-input and coverage manifest first, then calculate the forward panel only after the gate passes. This must preserve the documented handling of the 12 early S&P dates below 250 names; the review is not asking to drop or impute them.

4. **Label raw gates separately from Holm decisions.** In `_analyze` at lines 574-585, H7/H8 `status` is set from raw t/floor and placebo criteria; after Holm adjustment, only H9's `tested` status is replaced using `reject` (`run_j1.py:616-620`). The raw and adjusted p-values are present, but H7/H8 status does not say whether it is a raw gate result or a family-adjusted endpoint decision. Keep the registered raw gates for deciding whether to proceed if that is the intended rule, but label them explicitly as raw gate status and report Holm rejection separately for all three slots. If “H7/H8 pass” is intended to mean family-adjusted rejection, use that decision consistently before allowing H9 to run.

## Final assessment

The exact timing, direction, NW lag, shuffle setup, lowest-five portfolio, turnover cap, costs, bootstrap, Holm family membership, and fail-closed execute guard are otherwise represented. Because item 1 changes the measured peer-relative forward outcome and item 2 invalidates the embedded regression check, do not treat this runner as ready until those fixes and corresponding synthetic assertions are in place; item 3 should also be resolved or explicitly attested by the coordinator as an external pre-run gate.
