# K1 runner to frozen preregistration map

Runner: `r4_harness/r6/k1_runner.py`  
Preregistration: `specs/r6_prereg/K1.md`  
Canonical frozen digest checked by the guarded entry point: `889a6ffa50fe65864b0c432e1590c2252b7f2a76de6f914bafbdf2578441d3b3`.

| Frozen item | Implementation |
|---|---|
| Explicit one-shot execution and frozen hash | `main` requires `--execute`; `_execute` uses `guarded_runner`, `validate_frozen_prereg`, and exact canonical SHA check before analysis. |
| Input integrity and permitted period | `validate_input_manifest` verifies the K1 manifest and SHA-256 of prices, EDGAR event clock, dated SIC2 and both PIT rosters; price bundle is bounded to 2020-11-27 through 2026-10-30. |
| Acceptance clock and signal | `_session_index`, `make_event_rows`, `_market_adjusted_event`: BMO/AMC only, timestamp-consistent, first regular session opening after acceptance; announcement-session abnormal close-to-close return vs SPY. |
| Forward return / quarterly mechanism | `_forward_abret21`, `quarterly_ic_series`, `mechanism`: next 21-session open-to-close abnormal return, one issuer/event per quarter, quarterly Spearman IC, NW lag 4 and positive mean with t≥2. |
| SIC2 placebo | `sic2_shuffle`: within quarter/SIC2 event-signal permutation, 500 draws, seed 20261111, observed mean above p95 and one-sided p<.05. |
| Monthly Dow cohort and book | `monthly_formations`, `latest_scores`, `target_weights`, `_simple_monthly_book`: fixed month-end set, signal age ≤21 sessions, execution-open PIT roster, K=min(5,floor(n/2)), total-notional turnover cap .50, costs .0005 per traded dollar, and same execution-name roster for EW. |
| Decision-63 carry and delayed sale | `_simple_monthly_book` reuses the reviewed `r6_J1.run_j1` price-validity, close-marking, pending-open sale, and last-close liquidation helpers. Both strategy and EW books carry missing closes, record zero interim movement, catch up on resumed closes, queue a rebalance exit when the execution open is missing, sell at the first later valid open with its close-to-open mark included, and liquidate unresolved pending positions at their last valid close at sample end. |
| Portfolio inference | `circular_block_bootstrap_pvalue` is called with 10-session blocks, 5,000 draws and seed 20261111; output records H18 and DSR at the six-variant cumulative count. |
| Holm endpoints | `_read_holm` requires the frozen family manifest to include H16-H18, validates its digest and requires prior endpoints only in the supplied p-value map. |
| Trial log | `_r6_variant_count` requires D1/E1/J1/R1/P1/K1 single variants before computing DSR; append K1-V1 only after successful run. |
| Numeric prereg diff | `K1_PREREG_DIFF_SOURCE.md` is compared to `k1_prereg_diff_config.json`; `prereg_diff_payload` runs the same check before execution. |

`test_k1_runner.py` uses synthetic arrays/rows only to exercise event timing, abnormal-return arithmetic, planted quarterly IC, reproducible shuffle, cohort sizing, turnover, missing-close marking, manifest/hash failures, frozen digest, and the execution guard. It does not read the project input bundle and contains no real-data outcome checks.

## Review notes

The implementation is guarded, the staged bundle is not currently present, and the CLI is not invoked with `--execute` in this task. Synthetic tests cover a missing open at a rebalance followed by sale at a later valid open, a mid-hold missing-close gap and catch-up, and a delisting resolved at the last valid close with liquidation cost. The guard remains closed until the input manifest, event clock, Holm family and trial log are staged and hash-consistent.
