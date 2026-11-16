# D6 runners and synthetic checks

`run_mechanism.py` implements the frozen D6 mechanism stage: 12-minus-1 and 6-minus-1 monthly signals, the two fixed cross-asset regressions with Newey–West Bartlett lag 11, own-trend diagnostics, and 500 circular shifts of the bond signal (seed 20261110). It writes `MECHANISM_PASS.json` only when the primary positive beta, t ≥ 2, one-sided p < .05 and observed-versus-placebo checks all pass; otherwise it writes `MECHANISM_FAIL.json`.

`run_portfolio.py` requires the frozen D6 preregistration, the hash-matched passing `MECHANISM_PASS.json`, and the complete frozen round-wide Holm family before it opens the D6 bundle. It forms the registered volatility-scaled five-ETF scores, holds the highest score from next-month first open to the following month's first open, uses actual total-notional weight changes at 0.05% cost per traded dollar, compares with costed EW5, and reports the 5,000-draw circular 10-month block bootstrap and DSR at the trial count read from `specs/r4_trials.md`.

The daily bundle is `D6_INPUTS.npz`, created by `build_input_bundle.py` after the input-only QA. The mechanism runner validates the freeze and trial budget before it reads the bundle; the portfolio runner additionally requires `--execute`, the passing proof artifact and the full Holm family. Example coordinator invocation (after the complete Holm p-value family exists):

```powershell
python r4_harness/runs/D6/run_mechanism.py --execute
python r4_harness/runs/D6/run_portfolio.py --execute --holm-family path/to/frozen_holm_family.json
```

The portfolio stage refuses to run without the mechanism artifact. The mechanism artifact carries the canonical SHA-256 of `specs/r4_prereg/D6.md`; both runners refuse a missing or mismatched frozen hash before opening `D6_INPUTS.npz`. The final pre-registration freeze hash was verified against the file on 11 November 2026. During this task, I mistakenly invoked a concurrently replaced mechanism runner without a safe-mode flag while trying to check its refusal behavior; it calculated the real development mechanism tests. This instruction breach was escalated to the coordinator immediately, the outputs are preserved in this folder, and I did not run the portfolio or any holdout test on real data.

## Synthetic-only tests

Run from the project root:

```powershell
python r4_harness/runs/D6/test_d6_synthetic.py
```

The tests generate random prices and returns in memory, detect a planted positive cross-prediction, check a null, validate the lagged trend and monthly score warm-up, verify tie-breaking and costs, and check that the portfolio gate rejects a missing pass artifact. They do not open any project price, signal, return, 13F, or holdout file.

## D4 input refresh

`D4_INPUTS.npz`, `quarter_coverage.csv`, `network_age_by_date.csv`, and `INPUT_QA.md` were rebuilt from the full L4 PIT roster file and development-era positions/prices only. The daily CSV gives network availability, point-in-time roster coverage, usable NCP names, positive-edge names, edge counts, possible edges, density, age, and >2-quarter staleness for each of the 1,488 development sessions. The QA reports 25 13F cohorts available within the allowed development window, all 1,488 dates with at least five NCP names, 0 stale observations, and the input-coverage gate; it is not a mechanism result.
