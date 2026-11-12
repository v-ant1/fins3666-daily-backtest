# S&P Index Flow ? L-IDX5C final report

**Decision: S2 exhausted.** The single authorized foreground run completed without an exception. The primary pooled 10 bp one-way net mean was -0.6329%, below the MDE of 1.3581%; holdout missingness was 5.88%, above the 3% gate. No S2 preregistration was drafted, and the sealed holdout outcome was not opened.

## Frozen inputs and execution

- Frozen event list SHA-256: `aea1e01b79c5a552728f78ca4eda2bd7628a4e1a7c24131d18d32b97b2c582d2` (verified before execution; required hash matched).
- Final runner SHA-256: `849a2bd9653442e99da6d764896df2033a399da0de406a88ad156bae4e314b71`; guard removal is recorded in `GUARD_REMOVAL.diff` and `RUNNER_HASH_FINAL.md`.
- Executed `python r9/idx5/run_measurement.py` exactly once in the foreground; exit code 0. Credentials were loaded through python-dotenv from the specified `.env`; requests were GET-only. Holdout use was limited to bar-presence counts; no sealed files or holdout price values were opened or displayed.
- Development summary uses event CARs with sample SD and event-level Student-t 95% confidence intervals. Costs deduct twice the stated one-way rate from each mean.

## Development CAR

| Set | N | Mean | Sample SD | Median | 95% CI |
|---|---:|---:|---:|---:|---:|
| S&P 500 | 93 | 1.1904% | 7.7446% | 0.6141% | [-0.4046%, 2.7854%] |
| S&P 400 | 211 | -1.1484% | 6.6669% | -1.5597% | [-2.0532%, -0.2436%] |
| Pooled | 304 | -0.4329% | 7.0839% | -1.2246% | [-1.2324%, 0.3666%] |

### Mean net CAR by one-way cost tier

| Set | 5 bps | 10 bps (primary) | 20 bps |
|---|---:|---:|---:|
| S&P 500 | 1.0904% | 0.9904% | 0.7904% |
| S&P 400 | -1.2484% | -1.3484% | -1.5484% |
| pooled | -0.5329% | -0.6329% | -0.8329% |

## Holdout coverage ? counts only

| Index | Covered N | Eligible N | Missing N | Missing % |
|---|---:|---:|---:|---:|
| S&P 500 | 90 | 99 | 9 | 9.09% |
| S&P 400 | 150 | 156 | 6 | 3.85% |
| Total | 240 | 255 | 15 | 5.88% |

MDE = `2.970 ? SD_pooled / sqrt(N_holdout_covered)` = `2.970 ? 7.0839% / sqrt(240)` = **1.3581%**. The frozen planning count was N=255; observed covered N was 240. The primary pooled 10 bp net mean (-0.6329%) does not exceed the MDE, and missingness (5.88%) exceeds 3%. Therefore S2 is exhausted.

## Announcement-date exclusions

Metadata-only count: 91 of 370 holdout candidates (24.6%) lacked a dated announcement source: 25 S&P 500 and 66 S&P 400, skewed toward S&P 400. Counts by effective year and index:

| Effective year | S&P 500 | S&P 400 | Total |
|---|---:|---:|---:|
| 2016 | 8 | 13 | 21 |
| 2017 | 9 | 11 | 20 |
| 2018 | 0 | 8 | 8 |
| 2019 | 6 | 21 | 27 |
| 2020 | 2 | 13 | 15 |
| **Total** | **25** | **66** | **91** |

The largest yearly count was 2019. These are source-availability counts, not outcome measurements.
