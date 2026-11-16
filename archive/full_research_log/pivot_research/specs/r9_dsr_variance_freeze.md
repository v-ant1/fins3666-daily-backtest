# R9 DSR variance freeze

Recorded 2026-11-11 under Supervisor Directive 2, before any J2 holdout approval or run.

## Frozen choice

| Role | Variance | How it is used |
|---|---:|---|
| Primary | `V = 0.00008415393784762033` (12-stream observed R9 daily-Sharpe variance; audit rounded value `0.0000841539`) | Decides the Rule-6 DSR gate. The primary DSR must exceed 0.95. |
| Null sensitivity | `V = 1/(T-1)` | Reported alongside the primary. `T` is the number of daily return observations in the evaluated series. |

For a 2,722-session planning path, the null variance is `1/2721 = 0.0003675119441381845`. The two values must both be reported; the null sensitivity cannot replace the frozen primary decision.

## Frozen inputs

| File | SHA-256 |
|---|---|
| `specs/r9_prereg/J2.md` (full file bytes) | `ed8998e871044b27c4cc9fe3b7b637f10083429503941a30c4ebb3d34c8ef39b` |
| J2's declared content-above-footer SHA-256 | `23968857b7ebd15502274400e9c0335583656051999626acd6e44de839a9cf80` |
| `r9/holdout_runner.py` (after the reporting correction) | `edfdfb4678eab791824e8c23a33d5f2b4b5486689357e7eb8fcc7192fcd09c06` |

`r9/holdout_runner.py` now reports both DSRs and the variance used for each. Its Rule-6 `deflated_sharpe_above_0_95` check uses only the primary DSR. This change corrects reporting and does not alter J2 rules.

No approval marker was created and the holdout runner was not run.
