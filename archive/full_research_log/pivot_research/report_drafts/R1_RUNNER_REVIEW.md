# R1 runner review

**Verdict: FIX.** The synthetic checks pass and the runner has the expected execute guard, but the Dow portfolio does not implement the frozen available-name payer-count rule, uses same-session close availability to make an open-time decision, and omits the required missing-price handling. Do not accept a real run until the fixes below are implemented and covered by synthetic tests.

## Scope and checks

Reviewed `r6_R1/build_inputs.py`, `r6_R1/run_r1.py`, `r6_R1/test_r1_synthetic.py`, `r6_R1/RUNNER_SPEC_MAP.md`, the frozen-hash/diff artifacts, `specs/r6_prereg/R1.md`, and `report_drafts/J1_RUNNER_REVIEW.md`. The runner’s embedded check reports a clean numeric diff against SHA-256 `2681f2e3c67768a795b7489e64e69271239423925d0b4228c2dd7821a70de0b7`; its guard test confirms refusal without `--execute` before input loading. I ran only `python -m unittest r6_R1.test_r1_synthetic -v`: **9 tests passed**. I did not use `--execute`, open the staged R1 NPZ, calculate outcomes, or access holdout values.

## Findings against the frozen specification

### Signal cohort, timing, and forward returns — mostly match

- `build_inputs.py:22-36` includes events on the 12-month lower boundary, excludes any event on or after formation (`lo <= event < formation`), and projects only the fixed +3/+6/+9/+12 month dates. The first built formation is the last S&P-price session in June 2021 (`:111-116`); with the frozen first formation of 2021-06-30, the trailing window begins 2020-06-30, so it does not use pre-2020-06 events. An event exactly on 2020-06-30 may be used; one before it may not. The synthetic strict-before/month-end test passes.
- SIC is selected as of formation with `bisect_right` (`:54-67`). Membership is point-in-time at formation (`:147-168`). `run_r1.py:302-304` uses a common eligible cohort for the payer/non-payer SIC2 spread: member, complete dividend-history status, known SIC2, and both next-month endpoint prices. `monthly_returns` (`:115-119`) matches the registered adjusted-close/adjusted-open formula. The placebo reuses that same eligible mask.
- One input-coverage documentation gap remains: the frozen spec asks for ticker/security lineage and pull timestamp alongside event date and source response/status. The emitted R1 bundle and build manifest do not preserve those fields; the staged dividend manifest inspected by the builder has ticker/status/count/error columns, not lineage or pull timestamp. Keep or link a hash-identified QA artifact containing those provenance fields before an execution.

### Dow target count and formation-time availability — FIX

The frozen rule defines `n` as the count of names in the same-date available-name EW30 benchmark, then sets `k=min(15,floor(n/2))`. `run_r1.py:123-137` instead computes `n=len(ids)` from `member[:,j] & dividend_status & finite(open) & finite(close)` and uses `k=min(15,len(ids)//2)` (`:128-129`). That is a different cohort from the same-date EW benchmark, whose weights are formed separately at `:182-184` from `daily_member` and same-day price availability; it can also differ due to dividend-query gaps and membership changes. Pass the execution-date benchmark availability mask/count into `target_weights`, derive `k` from that benchmark count, and keep the payer candidates limited to signal-valid names. Add synthetic cases where benchmark-available `n` differs from signal-valid candidate count and assert both the registered `k` and realized active-share calculation.

There is also open-time look-ahead. The rebalance executes at the first session’s open, but `target_weights` uses that session’s close in `available` (`:123`) before selecting names. The close is not known at execution. Select from information available at formation plus current opening-price availability (and the registered PIT membership); use the close only for subsequent marking. The benchmark’s same-session close-availability mask (`:182`, `:195`) also needs to be made consistent with the frozen missing-price rule below.

### Decision-63 missing-price handling — FIX

The frozen coordinator rule requires carrying each missing close forward as a stale mark (zero return until a valid price), then selling a still-missing holding at its next valid open at rebalance or at its last valid close if it never trades again; apply the same marking rule to strategy and EW30. The runner does not do this. `portfolio` sets a missing daily return to `NaN` and then `nan_to_num` treats it as zero (`:191-204`), but it does not retain the last valid close. When a close reappears after multiple missing sessions, it compares against the immediately previous close, which is still missing, and again records zero (`:193-194`). It also has no explicit next-rebalance sale/fallback for a holding still missing. Implement the last-valid-close state and the registered sale fallback for both books. Add synthetic tests for one missing close followed by price resumption and for a name that remains missing through rebalance; assert zero interim marking, catch-up return or fallback sale, and matching benchmark treatment.

### Placebo, NW, bootstrap, Holm, and DSR — match with test-coverage caveats

- `shuffle_placebo` (`:82-102`) performs 500 within-date, within-SIC2 payer-flag permutations with seed 20261111, preserves payer counts, uses the +1 upper-tail p-value and requires both p<0.05 and observed > null p95. It stores all draws in the result (`:313`) and writes them to CSV (`:345-348`). This matches the frozen placebo.
- `mechanism` (`:104-113`) uses the shared Newey–West function at lag 3, positive mean and t≥2. The output reports raw p; the `_holm` routine combines the frozen earlier-family values, H7–H9 from J1, and H10–H12 (`:229-255`). A blocked H12 is assigned 1 only for Holm accounting and labeled not run. H10/H11 progression uses the registered raw gate (`:305-309`); Holm decisions are separately emitted.
- `portfolio` calls the circular block bootstrap with 10-session blocks, 5,000 draws, and the registered seed (`:211-212`). DSR uses the unique R6 trial count and requires R1-V1 to exist (`:221-227`, `:323-325`). The test suite covers the family slots and numeric config but does not currently assert bootstrap inputs, the raw-versus-Holm progression labels, or the H12 block after a failed raw gate; add these small synthetic assertions when repairing the runner.

### Guard and freeze metadata

The decorator at `run_r1.py:258-259` is exercised by the synthetic no-execute test and refuses before reading fake inputs. The numeric prereg diff test is clean. However, the prereg file’s opening status still says “DRAFT — NOT FROZEN” while its closing coordinator section says `FROZEN: 2026-11-11` with a digest. The guard accepts the latter. Correct the contradictory status through the coordinator’s freeze process (and update the digest if the file changes) before the one-shot run; do not edit the frozen file in this runner review.

## Exact fixes required

1. Compute payer `k` from the same-date available-name EW30 benchmark count, not from the dividend-valid candidate count, and assert this with a synthetic mismatch case.
2. Remove same-session close availability from the first-session-open selection decision; use current open plus information available by the formation/execution time.
3. Implement decision-63 carry-forward marking and next-rebalance sale/fallback for both the strategy and EW30; add the two missing-price synthetic cases above.
4. Preserve or hash-link the frozen-specified event-lineage and pull-timestamp QA metadata.
5. Resolve the draft/frozen front-matter contradiction through coordinator freeze metadata.
6. Add synthetic assertions for bootstrap parameters and H12 raw-gate blocking/ Holm reporting.

No outcome run is authorized by this review. After these code and QA fixes, rerun the synthetic suite and clean prereg diff; do not pass `--execute` as part of this worker task.
