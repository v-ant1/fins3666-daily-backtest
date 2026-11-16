# P1 runner implementation map

This map records alignment to the **FROZEN** `specs/r6_prereg/P1.md` (SHA256 `939e8272c4487b7728e1e4993ce62acee9e71134b5cabbe7417e16a2e9e3e3bc`). The only authorized outcome run is decision 108; preflight and synthetic tests are completed before that invocation.

## Specification map

| Registered requirement | Implementation | Synthetic coverage |
|---|---|---|
| First formation 2020-12-31 through 2026-09-30, 70 dates; Dow and S&P calendars aligned | `build_inputs.py` derives the formation schedule from the permitted Dow panel, applies the same dates to both universes, and fails if a date is absent | Formation schedule and exact runtime parameters checked |
| Compounded trailing 21-session adjusted overnight signal | `build_inputs.py`; `run_p1.py::build_forward_labels` | Missing-trailing-bar names excluded |
| Manifest and coverage verified before forward labels are read or built | `verify_input_manifest`, `verified_forward_labels`, and runner preflight | Ordering test verifies manifest before data reads/labels; failed gate blocks reads |
| S&P 500 mechanism: date-wise Spearman IC; positive sign and NW lag 1 t≥2; cost floor diagnostic only | `mechanism` and H13 raw-gate logic | H13 gate and diagnostic fields checked |
| SIC2-preserving 500-draw signal shuffle, seed 20261111, save every draw | `sic2_shuffle_placebo`; emits all 500 values to `P1_PLACEBO_DRAWS.csv` | Deterministic count/seed and retained draws checked |
| Dow strategy and EW30 use the same point-in-time next-open eligible cohort; K=min(5,floor(n/2)); no same-session close in selection | `select_weights` and `portfolio` | Cohort/K behavior and selector input isolation tested |
| 50% total buys-plus-sells turnover cap, 0.05% per traded dollar, EW30 benchmark and active share | `simulate_book` and `portfolio` | Synthetic transition, cap, costs, and active-share calculations tested |
| Decision 63 stale-price carry and scheduled-sale/terminal liquidation rule in both books | `stale_close_marks` and `simulate_book` | Strategy and EW tests cover stale marks, resumed prices, and final-close fallback |
| 10-session circular block bootstrap (5,000, seed 20261111); DSR with current registered trial count | `portfolio`; `_trial_count` | Runtime values asserted; no project portfolio is calculated in tests |
| All Holm family slots H1–H15; raw statuses separate from adjusted decisions; blocked slots account as p=1 | `endpoint_rows`, `holm_results`, `validate_holm_family` | Full-family fixture checks raw/Holm separation and strict H15 adjusted p<0.05 |
| Freeze/hash, explicit `--execute`, lock and existing mechanism-artifact guard | `@guarded_runner` | Refusal without execute and frozen prerequisites tested |

## Input pin and preconditions

`run_p1.py` pins `INPUT_MANIFEST.json` SHA256 `ebe1ee185f77aa3aac12e4eeac631c28c0cdcde4a7187a6755c37b303230a799`. Its preflight verifies the manifest bytes, bundle hashes, development-only bounds, 70 formation dates from December 2020 to September 2026, and the registered S&P coverage gate before any forward labels are built. The point-in-time Dow roster and execution opens define the same available-name cohort for the strategy and EW30. `specs/r6_holm_family.json` is validated as the full H1–H15 family using manifest digest `42e24dc6bed8ec2c46755bc3a45d4fce3d5aa96513d44225b7a643432c313911`; H13–H15 are unrun before execution.

`P1_PREREG_DIFF_SOURCE.md` is the normalized numeric excerpt used by `r4_harness.prereg_diff`; `prereg_diff_config.json` and the live `RUNNER_SPEC_CONFIG` are checked against it. It includes the formation count and all registered settings, including the H13 cost-floor diagnostic rather than a cost-floor gate.

## Validation status

The synthetic suite and preregistration diff are required to pass immediately before the sole authorized `--execute` invocation. No holdout inputs are permitted. The runner writes `RESULTS.md`, the endpoint table and all placebo draws; H15 is not run unless raw H13 and H14 pass.

## One authorized run

Decision 108's sole `python r6_P1/run_p1.py --execute` invocation completed successfully. H13 failed (mean IC -0.01471381774, NW t -0.74787486, raw one-sided p 0.77146147); H14 failed (observed mean IC -0.01471381774, SIC2 placebo p 1.0). Accordingly H15 was not run, its raw p is recorded as not run, and p=1 is used only for Holm accounting; no portfolio outcomes were generated. The complete report, including all 500 placebo draws and endpoint rows H13–H15, is `RESULTS.md` and `run/P1_ENDPOINTS.csv`; no `MECHANISM_PASS.json` was written.
