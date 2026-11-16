# J2 Holdout Audit

**Audit: PASS. Holdout outcome: FAIL.** The holdout was not rerun; the NPZ was hashed only and its contents were not loaded or printed.

| Check | Status | Evidence |
|---|---|---|
| Frozen artifact hashes | PASS | Current SHA-256: `specs/r9_prereg/J2.md` `ed8998e871044b27c4cc9fe3b7b637f10083429503941a30c4ebb3d34c8ef39b`; content above footer `23968857b7ebd15502274400e9c0335583656051999626acd6e44de839a9cf80`; `sealed_holdout_sp500/J2_HOLDOUT.npz` `7b405c9b8348c5c9db794a85480e6c0228901ab96b32d7af4c763ae758c589db`; `r9/j2_frozen.py` `85e643e9e6ad796e9ee1537fdf749c572c1c716e4ea98573465dac9832cf4020`; `r9/holdout_runner.py` `52c9c06ba7b3d916d6358bbf213119fbd9daec6bef57df80191a9c837c959a02`. All match the frozen references in the approval, seal, and readiness records. |
| Approval hash | PASS | `specs/r9_HOLDOUT_APPROVED.txt` contains the matching content hash exactly once. `frozen_prerequisites` also requires exactly one preregistration content-hash footer. |
| Refusal precedes attempt and data access | PASS | In `run_once`, `frozen_prerequisites` runs before the attempt-marker check/write and before `_load_engine`; the engine is the code path that calls `np.load`. The decision log records the first invocation refused because the approval used the full-file hash. That invocation could not have imported the J2 engine or read the NPZ. |
| Result consistency | PASS | Excess is exactly `0.7254405801209578 - 0.7781364356386009 = -0.05269585551764311`. All four checks are false and `pass` is false. The deciding DSR is `primary_observed_12_stream_v` with frozen variance `8.415393784762033e-05`; trial count is 15. |
| Other attempt/result traces | PASS, with fixture note | The production tree has only `r9/HOLDOUT_ATTEMPTED.txt` and `r9/HOLDOUT_RESULT.json`. The only additional matching marker/result pair is under `r9/j2ready/synthetic_case/`; its `SYNTHETIC_ONLY.txt` says it uses a synthetic random panel and no sealed input. |

The recorded run fails all four Rule 6 gates. The audit found no second production holdout attempt.
