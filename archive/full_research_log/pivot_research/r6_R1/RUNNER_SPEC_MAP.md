# R1 runner map

`run_r1.py` implements the frozen `specs/r6_prereg/R1.md` R1-V1. It is protected by `r4_harness.runner_guard.guarded_runner`; outcome inputs are not loaded unless explicitly invoked with `--execute`. This worker did not use `--execute` and computed no forward return, mechanism statistic, placebo outcome, portfolio result, or bootstrap.

## Input build and coverage-first order

`build_inputs.py` reads only the staged development dividend panel, S&P OHLCV, Dow development OHLCV, PIT rosters, and dated SIC panel. It emits `R1_INPUTS.npz`, `formation_coverage.csv`, `R1_DIVIDEND_PROVENANCE.csv`, and `build_manifest.json`; the builder does not divide prices into returns. Dividend history uses Yahoo's positive dividend-event rows and their `ex_date` field as the frozen schedule proxy; manifest statuses `ok` and `no_dividend_events` indicate complete responses. Failed/missing histories remain missing. The provenance file joins ticker symbols to the staged ticker/CIK lineage and preserves event date, source response/status and SHA-256 links. The upstream dividend package omitted its source-query timestamp; `source_pull_timestamp_utc` is explicitly blank and local manifest mtime is reported separately, not represented as the query time. No sealed dividend folder or pre-2020-06 Dow price data is read.

The runner first reads the row-count-only coverage CSV and requires 64 monthly S&P formations with at least 250 names each having a valid dividend response, SIC2, and both next-month endpoint bars. A failure writes all H10-H12 as not run and stops before loading the NPZ. Only after this gate does it open price-valued inputs and divide the registered next-month adjusted close by adjusted open.

## Frozen settings and implementation

| Preregistered item | Code location |
|---|---|
| Formation 2021-06 through 2026-09; next calendar month | `build_inputs.py` forms the final S&P session per month, creates 64 formations, and records the first and last next-month sessions. |
| Prior 12-month event history, strict-before formation; recurrence at +3/+6/+9/+12 months, month-end clamp | `recurrence_signal`; count of projected events is only the Dow tie-breaker. |
| SIC2-stratified payer-minus-nonpayer return spread, NW Bartlett lag 3, positive and t >= 2 | `mechanism`, using `r4_harness.phase3.newey_west_t`. |
| Within-date, within-SIC2 payer-flag shuffle, 500 draws, seed 20261111 | `shuffle_placebo`; it preserves each eligible SIC2 payer count and saves every draw to `run/R1_PLACEBO_DRAWS.csv`. |
| Dow `min(15, floor(n/2))`, where `n` is the same-date EW30 opening-available PIT count; fewer payers means all qualifying payers; no payers means cash; event-count/ticker ordering | `target_weights` uses PIT membership and opening-price availability only; it never consults same-session close to form an opening target. Portfolio daily rebalance trades toward target with total absolute notional <=50% per rebalance. |
| Active share >=50%, cost 0.05% per traded side/notional; same-available-name EW30 | `portfolio`; reports turnover and realized active share each rebalance, daily gross/net strategy and EW returns. |
| Decision 63 stale-close handling | Both books carry missing closes at their last valid close (flat daily mark), catch up from that mark when a close resumes, retain untradeable names through a rebalance, sell at the next valid rebalance open, and liquidate still-missing terminal positions at the last valid close. Strategy terminal fallback costs are included. |
| 10-session circular bootstrap, 5,000 draws, seed 20261111 | `r4_harness.phase3.circular_block_bootstrap_pvalue`; run only after H10 and H11 raw gates pass. |
| Holm family H1-H12, prior R6 H1-H6 config plus H7-H9 from `r6_J1/J1_RESULTS.json`, then H10-H12 | `_holm`; blocked endpoints use p=1 for Holm only and are labeled not run. Exactly one endpoint row is written for each H10-H12. |
| DSR at cumulative R6 strategy count | `_trial_count` requires R1-V1 in `specs/r4_trials.md`; the DSR uses daily net returns and counts unique logged strategies only. |
| Holdout firewall | No holdout paths are referenced. The input manifest certifies development-only inputs; holdout is reserved for coordinator criterion 5. |

## Outputs after authorized execution

An authorized run writes `run/R1_RESULTS.json`, `run/R1_ENDPOINTS.csv`, and the complete 500-row placebo file when the mechanism executes. A normal invocation without `--execute` is refused before input loading. The coordinator resolved the former draft/frozen front-matter contradiction through decision 102, metadata only, and refreshed the frozen SHA-256; the current digest and clean numeric specification check are recorded in `PREREG_DIFF.txt`.
