# J1 coordinator-only holdout runner

`run_holdout_j1.py` is an execution adapter for frozen `specs/r6_prereg/J1.md`. It is code-only until the coordinator deliberately runs it. Imports and synthetic tests do not read any sealed price, roster, or availability file.

## Frozen inputs and calculation

- Canonical preregistration: `specs/r6_prereg/J1.md`, approved SHA-256 `996b971090be395fffb1e11dff1430bbf581b338637250716607bf6b51cb7698`.
- Price rows: coordinator-staged CSVs under `sealed_holdout_dow/`, one per historical ticker with `date,open,high,low,close,adjclose` columns (optional `adjopen`). Dates are filtered to 2010-01-01 through 2020-10-31 before numeric fields are parsed. No rows outside that interval enter the calendar or features.
- Historical PIT roster: coordinator-staged `sealed_holdout_dow/dow_pit_roster.csv` with `ticker,effective_from,effective_to_exclusive` columns. The runner requires this dated input; it does not reuse the post-2020 development roster or infer membership from modern Dow constituents.
- SIC2: `r4_L4/data/sic_panel.csv`, using each ticker's last SIC effective by the formation session. The signal is the prior five-session adjusted close-to-close return less the leave-one-out mean for PIT Dow names in the same SIC2 group. Formation is every fifth holdout session; execution is next session open; selection is the five lowest scores.
- Portfolio: the shared portfolio simulator applies the frozen 50% total traded-notional cap including initial transition, 0.05% cost per dollar traded, and a point-in-time EW30 benchmark on the same available-name basis. It reports gross/net, Sharpe, costs, turnover, active share, drawdown, 10-session circular block-bootstrap inference (5,000 draws, seed 20261111), and DSR at the cumulative R6 trial count (currently three unique variants).
- DWDP is evaluated in two runs: include the PIT roster as recorded and remove it only from 2017-09-01 through 2019-04-30. KFT, DWDP, and WBA have known missing price lineage; UTX uses RTX as the disclosed lineage proxy. No missing price is imputed and no successor is substituted. If the coordinator has not staged the PIT roster/price bars, or too few names remain for execution, report infeasibility; do not run on development or substitute another universe.

## Required gates

The CLI requires `--coordinator-only`, `--execute-holdout`, and `ORCA_HOLDOUT_AUTH=COORDINATOR_ONLY`. Before any holdout roster or price values are read, the runner verifies the frozen J1 file and its exact approved hash, the J1 `MECHANISM_PASS.json` artifact and hash linkage, the SIC2 placebo pass and frozen mechanism thresholds, and `J1_RESULTS.json`. The development result must show the development portfolio gate passed and provides its positive net excess-return sign for the same-sign check. A `MECHANISM_FAIL.json` blocks execution. A one-shot lock is created before loading holdout values, so a failed/partial authorized attempt also consumes the single attempt.

The only holdout pass rule is R5/R6 goal criterion 5: (1) net excess-return sign matches the development portfolio sign; (2) net Sharpe exceeds EW30; and (3) the one-sided 10-session circular block-bootstrap p-value is below 0.10. No holdout IC, NW threshold, placebo, or development-only portfolio threshold is added. The development sign input is necessary because the mechanism-pass artifact alone contains no portfolio sign.

Example coordinator command (only after the coordinator has staged and hash-checked the inputs):

```powershell
$env:ORCA_HOLDOUT_AUTH = 'COORDINATOR_ONLY'
python r4_harness/holdout/run_holdout_j1.py `
  --coordinator-only --execute-holdout `
  --prices sealed_holdout_dow/prices `
  --roster sealed_holdout_dow/dow_pit_roster.csv `
  --sic-panel r4_L4/data/sic_panel.csv `
  --mechanism-pass r6_J1/MECHANISM_PASS.json
```

This command is documentation only; it was not run. Do not delete or bypass the lock to retry.

## Synthetic-only verification

Run `python -m unittest r4_harness.holdout.test_holdout_j1_synthetic`. The tests build deterministic synthetic arrays in memory and check signal timing, leave-one-out peer scores, turnover capping, both DWDP-reporting scenarios, and path refusal. They do not call the authorized runner or open any path under `sealed_holdout_dow`.

## Current implementation limits to disclose

The observed workspace path contains availability-only files, not a demonstrated complete historical PIT roster and daily OHLC set. The coordinator must confirm input presence and row coverage using paths/row counts before authorizing the one-shot run. The runner is intentionally fail-closed if there are no eligible OHLC dates, fewer than five eligible signal names at the required formation frequency, a missing/failed mechanism proof, a missing development sign, a changed preregistration hash, or a second execution attempt.
