# R10 execution readiness — L4

**Status: READY FOR A FROZEN R10 STRATEGY AND A SEPARATELY APPROVED ONE-SHOT RUN.** This deliverable supplies a generic panel builder and an approval-gated runner for the candidate S&P 2010-01-04 through 2015-12-31 period. No real pre-2020-11-27 price/return values, sealed data files, credentials, or strategy outcomes were read or computed by L4; the candidate panel has not been built or opened.

## Artifacts

- `build_panel_template.py` accepts a normalized long CSV (`universe,date,asset,roster,sic2,adjusted_open,adjusted_close`) and writes both S&P 500 and Dow arrays using the development NPZ schema. It requires the exact frozen interval endpoints, shared date axes, <=5-character ticker labels, SIC2 strings, unique rows, and emits a report with schema, counts, coverage, source/panel hashes only. It was validated on synthetic CSV input; it was not used on real historical data.
- `gated_runner_template.py` is strategy-agnostic. A frozen engine exposes `run_frozen_strategy(prereg_path, panel, start_date, end_date)` and returns aligned dates, net strategy returns, net benchmark returns, and the predeclared DSR trial count. The engine receives the loaded panel in memory after the gate and must be pinned before approval.
- `synthetic_validation.py` and `SYNTHETIC_VALIDATION.json` document the synthetic-only gate validation. Trial registrations and outcomes are in `r10_trial_log.md`.
- Cumulative search history and multiplicity guidance are in `TRIAL_LEDGER.md`; L4's scoped decision log is `r10_decisions.md`.

## Gate sequence

The runner validates the run manifest's date bounds and trial count; confirms the exact approval file; verifies preregistration, engine, and runner SHA-256 pins; and confirms the panel path exists. The approval file binds the manifest digest and all pinned preregistration, engine, runner, and panel hashes. It then atomically creates a persistent one-shot marker with exclusive creation **before hashing or loading panel bytes**. A panel hash mismatch after marker claim consumes the attempt. On a matching digest, the runner loads with pickle disabled, validates all 12 development-schema keys/shapes/dtypes and shared date axis, imports the frozen engine, checks its output dates and trial count, computes the one-sided 10-session circular bootstrap and both DSR variants, and writes one result file atomically. A marker or result file blocks a second run.

For R10 the frozen DSR variance is primary `V=0.00008415393784762033`; null sensitivity `V=1/(T−1)` is also reported. The primary DSR alone decides the `>0.95` gate. The bootstrap is 5,000 circular draws with 10-session blocks and seed `20261111`. Each candidate's signed preregistration must freeze the pass criteria and Holm family before any outcome calculation; L4 does not authorize a real run.

## Trial accounting

The cumulative historical ledger is **50** by the task's requested convention. R6's actual Holm family is 21 unique H1–H21 endpoints. J2's historical holdout stored DSR trial count 15; R10 uses 50 as a conservative cumulative search-history count before adding newly pre-registered trials, without claiming 50 independent return streams. The detailed mapping and proper distinction between endpoint families and execution attempts are in `TRIAL_LEDGER.md`.

The requested shared paths `specs/r10_decisions.md` and `specs/r10_trial_log.md` did not exist. Since the same dispatch says all new files must remain under `r10/L4/`, L4 kept its tagged logs in this directory and asked the coordinator to resolve the path conflict; no shared file outside the assigned directory was created or edited.

## Synthetic validation

`L4-SYNTH-01` passed schema, approval refusal, panel-hash mismatch, both-DSR output, marker-before-load, and one-shot checks. `L4-SYNTH-02` passed partial-window refusal and full-period endpoint checks. Both used generated synthetic data only. No live candidate or holdout output exists.

## Code SHA-256 pins

| File | SHA-256 |
|---|---|
| `build_panel_template.py` | `53d2955e5794689399386fc29c3a972a3824eeb1f5110a946e109d4bcfbd232b` |
| `gated_runner_template.py` | `47d2c8fbc55d5035888392c6138baddbc26b6572962914a5bd9dbd990a19e536` |
| `synthetic_validation.py` | `1f11291976e63c87ed327529706cd92e0520794e5717fd2d003ebb3302fc583f` |
