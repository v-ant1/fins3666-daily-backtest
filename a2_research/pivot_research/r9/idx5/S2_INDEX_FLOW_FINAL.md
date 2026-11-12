# S&P Index Flow — L-IDX5B final report

**Decision: S2 exhausted under supervisor ruling B.** One invocation of the existing runner was made after the minimal PID guard edit. Its guard raised `RuntimeError: Another idx5 measurement process is active (pid=32000)` before the data-loading and fetch loop; no request or event result was produced. No relaunch was made. Development statistics, holdout coverage, and MDE are therefore unavailable, and no preregistration was drafted.

## Frozen inputs and execution record

- Frozen event list SHA-256: `aea1e01b79c5a552728f78ca4eda2bd7628a4e1a7c24131d18d32b97b2c582d2` (verified immediately before the invocation; unchanged afterward).
- Fixed runner SHA-256: `0238f38c2653353eFC118C8618F5186792E887F9760C976BE61E1285AFB9EB68` (see `RUNNER_HASH.md`). The only runner change was the single-process guard, recorded in `PID_GUARD_FIX.diff`.
- The run stopped at `claim_single_process()` before reading prices or making any Alpaca request. No `event_results.csv` or `results.json` was created.

## Required measurements

| Development set | N | Mean CAR | Sample SD | Median | 95% CI |
|---|---:|---:|---:|---:|---:|
| S&P 500 | unavailable | unavailable | unavailable | unavailable | unavailable |
| S&P 400 | unavailable | unavailable | unavailable | unavailable | unavailable |
| Pooled | unavailable | unavailable | unavailable | unavailable | unavailable |

Net mean CAR after 5/10/20 bp one-way costs: unavailable for all three sets. The primary pooled 10 bp net mean and `2.970 × SD_pooled / sqrt(N_holdout_covered)` MDE cannot be computed.

Holdout coverage is also unavailable: covered N by index and missing percentage were not measured. Since the runner failed and the decision gate cannot be demonstrated, S2 is exhausted under the ruling; no holdout outcome was opened.

## Missing-announcement candidates by effective year and index

These are metadata counts from `metadata_candidates_missing_announcement.csv` (91 candidates total); year refers to effective date.

| Year | S&P 500 | S&P 400 | Total |
|---|---:|---:|---:|
| 2016 | 8 | 13 | 21 |
| 2017 | 9 | 11 | 20 |
| 2018 | 0 | 8 | 8 |
| 2019 | 6 | 21 | 27 |
| 2020 | 2 | 13 | 15 |
| **Total** | **25** | **66** | **91** |

Missing-announcement candidates skew toward S&P 400 overall (66 vs 25) and are most numerous in 2019 (27); the year mix varies across indices. This comparison is descriptive of candidate counts, not an outcome analysis.
