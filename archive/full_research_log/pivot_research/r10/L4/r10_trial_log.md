# R10 trial log — L4

## L4-SYNTH-01 — synthetic pipeline integration (pre-registered 2026-11-12)

Question: Does the generic R10 panel-builder contract and one-shot holdout runner enforce the intended schema, hash, approval, marker, output, and dual-DSR behavior using synthetic data only?

Frozen procedure: run `synthetic_validation.py` once. It builds temporary synthetic panel and strategy fixtures under `r10/L4/`; checks the dev-NPZ-compatible keys/shapes/dtypes; verifies missing approval refusal; exercises a panel hash mismatch in an isolated fixture; executes one approved synthetic run and confirms both primary and null DSRs are present; confirms the marker exists before the panel loader is called; then confirms a second attempt is refused. No real input path is supplied. No real 2010–2015 panel, any `sealed_holdout*` contents, `.env`, prices, returns, or outcomes are read.

Counting: one integration trial regardless of assertion count. A failure or interruption counts; no rerun without a new pre-log entry. A failure is recorded as an implementation result, not strategy evidence.

- 2026-11-12 [L4] Attempt 1 started: ran `python r10/L4/synthetic_validation.py`; counted as one integration trial.
- 2026-11-12 [L4] Attempt 1 completed: PASS. The builder produced the expected development-schema keys/shapes/dtypes; missing approval refused before marker, wrong panel hash refused after marker, the approved synthetic run reported both DSR variants, the marker was present before panel loading, and the second invocation refused. No real panel or strategy data was accessed. See `r10/L4/SYNTHETIC_VALIDATION.json`.

## L4-SYNTH-02 — full-window boundary guard (pre-registered 2026-11-12)

Question: Do the builder and approved runner reject a partial window and accept a complete synthetic 2010-01-04 through 2015-12-31 panel/result?

Frozen procedure: tighten the builder to require exact synthetic axis endpoints `2010-01-04` and `2015-12-31`; require the runner's generated strategy series to end on `2015-12-31`; update `synthetic_validation.py` to build the full synthetic weekday axis, test partial-window builder refusal, and prove a full-window approved synthetic result ends on the frozen last session. No real data path is allowed. This is one additional synthetic integration trial; no rerun if it fails.

- 2026-11-12 [L4] Attempt 1 started: ran the same synthetic-only harness with exact full-window guards; counted as one trial.
- 2026-11-12 [L4] Attempt 1 completed: PASS. The builder refused a partial synthetic source, accepted a full `2010-01-04..2015-12-31` source, and the approved synthetic runner result ended on the frozen final session; all approval/hash/marker/two-DSR/one-shot assertions remained passing. No real data was accessed. See `r10/L4/SYNTHETIC_VALIDATION.json`.
