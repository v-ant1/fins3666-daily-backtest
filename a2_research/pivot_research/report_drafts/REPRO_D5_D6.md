# D5 and D6 independent reproducibility check

**Scope.** I independently recomputed the D5 primary mean daily rank IC and the D6 primary bond-to-SPY regression coefficient from `D5_INPUTS.npz` and `D6_INPUTS.npz`. The script is `report_drafts/repro/rederive_d5_d6.py`; it imports neither registered runner nor `r4_harness` functions. It reads development inputs only and does not read or compute anything from the sealed holdout. No trial-log rows were added.

## Freeze verification

The independent script recomputed each canonical SHA-256 (excluding the `SHA256:` line), and both values match the preregistration footers:

| Spec | Freeze date | Declared SHA-256 | Check |
|---|---|---|---|
| D5 | 2026-11-10 | `e0b71e497fa049dbeeb7bd9af160f0380bd68960aa3206c09f471a2a2e6496ee` | Valid |
| D6 | 2026-11-10 | `341a406f0de406a989bc3fe6195de08f127592f011e7bd975eb1519bd71949dd` | Valid |

Both registered runners' `--check-freeze` commands also accepted their current preregistration files.

## Independent statistic comparisons

| Primary statistic | Independent result | Logged result | Three-significant-figure comparison | Discrepancy |
|---|---:|---:|---:|---|
| D5 mean five-session follower rank IC | 0.007455133611 | 0.007455133611 | 0.00746 = 0.00746 | None |
| D5 Newey–West t, Bartlett lag 4 | 0.5643776624 | 0.5643776624 | 0.564 = 0.564 | None |
| D6 primary 12-minus-1 bond-to-SPY beta | 0.07692125109 | 0.07692125109 | 0.0769 = 0.0769 | None |
| D6 Newey–West t, Bartlett lag 11 | 0.7663441562 | 0.7663441562 | 0.766 = 0.766 | None |

For D5, the bundle has 1,488 daily sessions from 2020-11-27 through 2026-10-30. The independent reconstruction yields 1,463 valid daily IC observations, matching the runner's reported count. The saved input also contains 293 fifth-session formation indices for the pre-outcome feasibility gate; 292 of those dates have a complete five-session forward return. The frozen text specifies the fifth-session dates for the graph feasibility gate and refers to the mechanism IC on each eligible date; the runner computes the IC series daily, consistent with the five-session forward horizon and NW lag 4 for overlapping observations.

For D6, the bundle spans 2020-06-01 through 2026-10-30, including its development warm-up. The independent calculation uses the 62 registered monthly targets, August 2021 through September 2026, and reproduces the logged primary regression using the equal-weight four-ETF 12-minus-1 Treasury trend and SPY's own 12-minus-1 trend control.

## Runner settings checked against the frozen specifications

| Runner | Frozen setting | Runner/input evidence | Assessment |
|---|---|---|---|
| D5 | 20-session primary dollar-volume leader graph; five-session mean CLV and next-open-to-close outcome | Input builder uses `lookback=20`; runner uses `HORIZON=5` and the saved 20-session graph | Matches |
| D5 | NW Bartlett lag 4 | Runner constant `NW_LAG=4`; independent t uses lag 4 | Matches |
| D5 | 500 within-SIC permutations, seed 20261110 | Runner constants `PLACEBO_DRAWS=500`, `SEED=20261110` | Matches |
| D5 | One fixed 20-session shifted-graph control | Runner constant `GRAPH_SHIFT=20`, one deterministic shift | Matches |
| D6 | 12-minus-1 primary; monthly targets Aug 2021–Sep 2026; first adjusted open in target month to first adjusted open next month | Runner checks target endpoints and uses adjusted-close month-end trends plus adjusted-open target inputs; result has N=62 | Matches |
| D6 | NW Bartlett lag 11 | Runner constant `NW_LAG=11`; independent t uses lag 11 | Matches |
| D6 | 500 circular shifts, seed 20261110; offsets 12 through N−12 | Runner uses `PLACEBO_DRAWS=500`, `SEED=20261110`, and inclusive integer draws 12–50 when N=62 | Matches |

## Discrepancies and documentation note

There is no numerical discrepancy in either primary statistic. Both preregistration files have valid freeze dates and matching hashes, but their introductory status sentences are stale: D5 still says “NOT FROZEN,” and D6 still says “READY FOR COORDINATOR FREEZE,” while both files now end with valid `FROZEN:` and `SHA256:` lines. I did not edit either frozen specification.

The independent script and comparisons are reproducible with:

```powershell
python report_drafts\repro\rederive_d5_d6.py
```
