# D4 runner repair log

The pre-registration `specs/r4_prereg/D4.md` was not changed. The repaired runner is guarded by its frozen date and content SHA-256, and refuses to run if any `MECHANISM_*` artifact already exists. It authorizes the eight mechanism endpoints before opening development price files, then appends one trial-log row for each endpoint. The portfolio endpoint (D4-9) remains outside this runner.

| Runner change | Frozen text implemented |
|---|---|
| D4-1 primary mean rank IC, Newey–West Bartlett lag 4, one-sided raw p-value, and positive/t≥2/0.0183 advancement rule | `D4.md` lines 28, 52 |
| D4-2 degree-preserving placebo: 500 draws, one `default_rng(20261110)` stream, 10×E directed double-edge swap attempts, reject self/duplicate edges, shuffle the original weight multiset, then row-normalize | `D4.md` line 30, family (1) |
| D4-3 random-link placebo: 500 draws from the same RNG stream after the degree family; sample the same directed non-self edge count without replacement, retain originally zero rows, permute weights, and row-normalize | `D4.md` line 30, family (2) |
| D4-4 fixed 20-session graph alignment wraps the dated graph sequence and compares primary and shifted date-wise ICs on matched dates | `D4.md` lines 30, 32, 38; interpretation detail is recorded below |
| D4-5 to D4-7 calculate averaged date-wise IC, Bartlett-lag-4 90% NW interval, both one-sided equivalence p-values and their maximum, and linear p95 of absolute draw mean ICs against ±0.00577 | `D4.md` line 32 |
| D4-8 rebuilds the point-in-time network with pair weight `sum_m min(w_i,m, w_j,m)`, then computes five-session NCP mean rank IC, lag-4 NW t and one-sided p; it cannot advance | `D4.md` lines 38, 42–46 |
| Removes a stale runner check requiring target-own CLV5 to be finite before accepting peer pressure; the rebuilt bundle retains a score when peers have valid CLV but target-own CLV is missing | `D4.md` line 22, NCP formula |
| Writes date-level ICs, all 500 draw-level statistics for each randomized family, complete endpoint table, and one PASS or FAIL JSON | `D4.md` lines 30, 32 |

## Fixed-shift interpretation

The frozen text names the 20-session control in the randomized-test family and asks for a randomization p-value, but it defines only one deterministic alignment: graph `t−20`, with circular wrapping. There is no registered distribution of alternative shift offsets. To avoid inventing offsets or duplicating one value 500 times and calling it a randomization distribution, D4-4 uses the one-sided paired NW test of primary-minus-shift IC on the same dates. The separate D4-7 equivalence test reports the shifted series against the frozen margin. This interpretation is fixed before the outcome run and disclosed in the results.

## Synthetic checks

`test_run_mechanism.py` uses toy graphs/series only. It checks in/out-degree preservation, random-link edge count and zero rows, exact circular alignment, the equivalence gate, endpoint-log formatting, the variant-2 sum-of-minimum weight, and peer scores when a target's own CLV5 is missing. All seven synthetic tests passed before the valid D4 endpoint run.

Before the outcome run, one guarded invocation stopped at the saved-NCP consistency check because the runner incorrectly censored a score when the target's own CLV5 was missing. No endpoint statistic or trial-log row was produced by that preflight. The stale check was removed and tested. The registered endpoint computation then ran once and produced D4-1 through D4-8; a post-computation formatting error prevented trial rows and Markdown from being written. `--finalize-logs` was added to write the eight rows and Markdown from the already-saved JSON, validating its frozen hash and refusing duplicate D4 rows; this did not recompute any outcome. The outcome gate is FAIL. No portfolio or holdout data were used.
