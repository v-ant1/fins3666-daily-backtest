# G1 runner-to-preregistration map

`g1_runner.py` implements the single frozen G1-V1 design in `specs/r6_prereg/G1.md`. The `@guarded_runner` wrapper verifies the frozen date and SHA-256, requires explicit `--execute`, takes a one-shot lock, and refuses an existing `MECHANISM_*` artifact. This implementation task did not use `--execute`, load project input panels, calculate outcome labels, or access holdout data.

## Frozen design mapping

| Frozen requirement | Implementation |
|---|---|
| 50 preceding valid volume sessions; log-volume z-score; five-session mean ending at formation | `high_volume_signal`; current session is excluded from its baseline and all 50 prior observations plus nonzero sample SD are required. |
| Fixed development calendar, 68 formations, first index 54 and 21-session cadence | `formation_indices`; requires the full 1,488-session 2020-11-27–2026-10-30 development calendar. Portfolio and outcomes stop at final registered endpoint index 1,482. |
| Point-in-time roster, SIC2 and next-21-session open-to-close label | `availability_masks` constructs signal/SIC/endpoint masks without divisions. `check_coverage` runs first; `_forward_returns` is only called after that gate and post-load mask/calendar agreement. |
| S&P coverage gate: at least 250 eligible observations on every formation | `check_coverage`, then exact recomputation of both S&P and Dow availability counts before `_forward_returns`. No date deletion or imputation is performed. |
| S&P date-wise Spearman IC, positive sign, NW lag 1 and t≥2 | `mechanism`; H19 raw gate requires positive mean IC and NW t≥2. The cost floor is a reported numeric diagnostic, never a gate. |
| Within-date/SIC2 score shuffle, 500 draws, seed 20261111; save every draw | `sic2_shuffle`, preserving group score distributions and eligible masks; `G1_PLACEBO_DRAWS.csv` receives all 500 mean-IC draws. H20 also requires positive observed mean, above-null 95th percentile, and p<.05. |
| Dow opening cohort, K=min(5,floor(n/2)), top scores, ≤50% turnover and 0.05% per traded dollar | `target_weights`, `_trade`, and `portfolio`; n is the open-available PIT roster count, signal eligibility is intersected at the next open, ticker-ascending tie-break, and initial transition starts from EW30. |
| Decision 63 applied to both books | `portfolio` carries last valid closes, marks missing-close days flat, catches up on resumed closes, trades stale names only at a scheduled rebalance when an open is available, and charges terminal last-close fallback liquidation cost. |
| 10-session circular block bootstrap, 5,000 draws, seed 20261111; DSR at cumulative strategy count | `portfolio`, `deflated_sharpe_ratio`, and `_trial_count`. G1 must already appear in `specs/r4_trials.md`; only unique R6 variant log entries count. |
| H19-H21 in full R6 Holm H1-H21 family | `validate_holm_family` checks the ordered manifest and digest, requires all slots and H19-H21 null before execution; `holm` preserves prior slots and fills current outcomes. Raw H19/H20 gates control portfolio progression, while adjusted decisions are separately reported. |
| Coverage/input lineage and development-only boundaries | `verify_inputs` and `check_coverage` require a self-digested input manifest, hashed bundle and availability table, pinned source file hashes/roles, split-adjusted volume and explicit no-forward-label/no-holdout attestations. Required NPZ keys and axes are validated before signal/outcome work. |

## Input bundle contract

The data owner stages `G1_INPUTS.npz`, `formation_coverage.csv`, and `build_manifest.json` next to this runner. The NPZ stores a shared `dates` axis (exactly 1,488 sessions, 2020-11-27 through 2026-10-30) and, for each of `sp500` and `dow`, `{universe}_names`, `{universe}_roster`, `{universe}_sic2`, `{universe}_volume`, `{universe}_adjusted_open`, and `{universe}_adjusted_close`. Every panel is assets × dates; no forward returns or derived outcome columns are accepted or needed. The input-only manifest records SHA-256 for the bundle, coverage CSV, and all source files, with roles `sp500_ohlcv`, `dow_ohlcv`, `sp500_pit_roster`, `dow_pit_roster`, `sic2`, and `split_actions`; volume must be in split-adjusted share units using actions effective by each session, with dividends excluded. Coverage rows contain `universe`, fixed `formation_date`, and `eligible_names`; those counts are recomputed from bundle availability masks before any forward-return division.

The current worktree did not contain the G1 input bundle, coverage table, or build manifest when this runner was built, so the runner has not been executed. It also fails closed until the coordinator-owned `specs/r6_holm_family.json` contains H1-H21, including reserved nulls for H16-H21, and G1-V1 is logged in `specs/r4_trials.md`; those shared files are outside this worker's write scope.

## Synthetic checks and clean prereg diff

Run from `A2/pivot_research`:

```powershell
python -m unittest r4_harness.r6.test_g1_runner -v
python -m r4_harness.prereg_diff r4_harness/r6/G1_PREREG_DIFF_SOURCE.md r4_harness/r6/prereg_diff_config.json
```

`G1_PREREG_DIFF_SOURCE.md` is a numeric-only normalized copy of the frozen registered choices for the harness parser. The canonical `specs/r6_prereg/G1.md` remains unchanged and its content hash is asserted by the synthetic test.
