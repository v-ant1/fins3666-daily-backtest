# D6 input QA (input-only)

**Gate: PASS for development input coverage and integrity.** The frozen D6 pre-registration hash was verified through the harness before outcome access. All five specified ETF files pass the input checks below. The coordinator separately verifies 2008-11 warm-up and holdout coverage; this worker did not inspect holdout data.

## Scope and source

Inspected only SPY, TLT, IEF, SHY and TIP in `oos3/xasset/prices-daily`. Price fields were read only for 2020-06-01 through 2026-10-30. All five files begin on 2020-06-01 and end on 2026-10-30; the preregistered six-month warm-up for development is included. The bundle `D6_INPUTS.npz` contains raw OHLC, source adjusted close, the daily `adjclose/close` factor, and adjusted OHLC computed with the frozen convention (the same factor applied to open, high, and low).

## Coverage and integrity

| Check | Result |
|---|---|
| Files / assets | 5/5 present: SPY, TLT, IEF, SHY, TIP |
| Daily rows per asset | 1614 each |
| Shared date coverage | 2020-06-01 to 2026-10-30 |
| Duplicate dates / cross-file date mismatch | 0 / none |
| Weekdays absent relative to weekday grid | 61 (market holidays are not separately calendared) |
| Missing, nonfinite, or nonpositive OHLC/adjusted-close values | 0 |
| Raw OHLC range-order violations | 0 |
| Missing/nonpositive adjusted opens from registered formula | 0 |
| Adjusted-close factor | varies across the development window: True; range 0.79142525–1.00000000 |
| Adjusted-open formula max absolute arithmetic discrepancy | 1.14e-13 |

Adjustment check is limited to the provided `adjclose` series, finite positive values, the per-day `adjclose/close` factor, and consistent application of that factor to the registered adjusted-open input. No corporate-action ledger is included, so this check cannot independently certify every split or distribution adjustment against issuer records.

## Formation and target-date availability

The preregistered target range is 2021-08 through 2026-09 (62 monthly targets); corresponding formation months are 2021-07 through 2026-08 (62). Each month has a last available session, and each target month has a first available session: missing formation month-ends = 0; missing target first sessions = 0.

### Formation-date table (date availability only)

| Target month | Formation month-end session | Target first session | Following month first session |
|---|---|---|---|
| 2021-08 | 2021-07-30 | 2021-08-02 | 2021-09-01 |
| 2021-09 | 2021-08-31 | 2021-09-01 | 2021-10-01 |
| 2021-10 | 2021-09-30 | 2021-10-01 | 2021-11-01 |
| 2021-11 | 2021-10-29 | 2021-11-01 | 2021-12-01 |
| 2021-12 | 2021-11-30 | 2021-12-01 | 2022-01-03 |
| 2022-01 | 2021-12-31 | 2022-01-03 | 2022-02-01 |
| 2022-02 | 2022-01-31 | 2022-02-01 | 2022-03-01 |
| 2022-03 | 2022-02-28 | 2022-03-01 | 2022-04-01 |
| 2022-04 | 2022-03-31 | 2022-04-01 | 2022-05-02 |
| 2022-05 | 2022-04-29 | 2022-05-02 | 2022-06-01 |
| 2022-06 | 2022-05-31 | 2022-06-01 | 2022-07-01 |
| 2022-07 | 2022-06-30 | 2022-07-01 | 2022-08-01 |
| 2022-08 | 2022-07-29 | 2022-08-01 | 2022-09-01 |
| 2022-09 | 2022-08-31 | 2022-09-01 | 2022-10-03 |
| 2022-10 | 2022-09-30 | 2022-10-03 | 2022-11-01 |
| 2022-11 | 2022-10-31 | 2022-11-01 | 2022-12-01 |
| 2022-12 | 2022-11-30 | 2022-12-01 | 2023-01-03 |
| 2023-01 | 2022-12-30 | 2023-01-03 | 2023-02-01 |
| 2023-02 | 2023-01-31 | 2023-02-01 | 2023-03-01 |
| 2023-03 | 2023-02-28 | 2023-03-01 | 2023-04-03 |
| 2023-04 | 2023-03-31 | 2023-04-03 | 2023-05-01 |
| 2023-05 | 2023-04-28 | 2023-05-01 | 2023-06-01 |
| 2023-06 | 2023-05-31 | 2023-06-01 | 2023-07-03 |
| 2023-07 | 2023-06-30 | 2023-07-03 | 2023-08-01 |
| 2023-08 | 2023-07-31 | 2023-08-01 | 2023-09-01 |
| 2023-09 | 2023-08-31 | 2023-09-01 | 2023-10-02 |
| 2023-10 | 2023-09-29 | 2023-10-02 | 2023-11-01 |
| 2023-11 | 2023-10-31 | 2023-11-01 | 2023-12-01 |
| 2023-12 | 2023-11-30 | 2023-12-01 | 2024-01-02 |
| 2024-01 | 2023-12-29 | 2024-01-02 | 2024-02-01 |
| 2024-02 | 2024-01-31 | 2024-02-01 | 2024-03-01 |
| 2024-03 | 2024-02-29 | 2024-03-01 | 2024-04-01 |
| 2024-04 | 2024-03-28 | 2024-04-01 | 2024-05-01 |
| 2024-05 | 2024-04-30 | 2024-05-01 | 2024-06-03 |
| 2024-06 | 2024-05-31 | 2024-06-03 | 2024-07-01 |
| 2024-07 | 2024-06-28 | 2024-07-01 | 2024-08-01 |
| 2024-08 | 2024-07-31 | 2024-08-01 | 2024-09-03 |
| 2024-09 | 2024-08-30 | 2024-09-03 | 2024-10-01 |
| 2024-10 | 2024-09-30 | 2024-10-01 | 2024-11-01 |
| 2024-11 | 2024-10-31 | 2024-11-01 | 2024-12-02 |
| 2024-12 | 2024-11-29 | 2024-12-02 | 2025-01-02 |
| 2025-01 | 2024-12-31 | 2025-01-02 | 2025-02-03 |
| 2025-02 | 2025-01-31 | 2025-02-03 | 2025-03-03 |
| 2025-03 | 2025-02-28 | 2025-03-03 | 2025-04-01 |
| 2025-04 | 2025-03-31 | 2025-04-01 | 2025-05-01 |
| 2025-05 | 2025-04-30 | 2025-05-01 | 2025-06-02 |
| 2025-06 | 2025-05-30 | 2025-06-02 | 2025-07-01 |
| 2025-07 | 2025-06-30 | 2025-07-01 | 2025-08-01 |
| 2025-08 | 2025-07-31 | 2025-08-01 | 2025-09-02 |
| 2025-09 | 2025-08-29 | 2025-09-02 | 2025-10-01 |
| 2025-10 | 2025-09-30 | 2025-10-01 | 2025-11-03 |
| 2025-11 | 2025-10-31 | 2025-11-03 | 2025-12-01 |
| 2025-12 | 2025-11-28 | 2025-12-01 | 2026-01-02 |
| 2026-01 | 2025-12-31 | 2026-01-02 | 2026-02-02 |
| 2026-02 | 2026-01-30 | 2026-02-02 | 2026-03-02 |
| 2026-03 | 2026-02-27 | 2026-03-02 | 2026-04-01 |
| 2026-04 | 2026-03-31 | 2026-04-01 | 2026-05-01 |
| 2026-05 | 2026-04-30 | 2026-05-01 | 2026-06-01 |
| 2026-06 | 2026-05-29 | 2026-06-01 | 2026-07-01 |
| 2026-07 | 2026-06-30 | 2026-07-01 | 2026-08-03 |
| 2026-08 | 2026-07-31 | 2026-08-03 | 2026-09-01 |
| 2026-09 | 2026-08-31 | 2026-09-01 | 2026-10-01 |

## Checklist status

- [x] Five named development files exist with adjusted-close fields and common daily coverage.
- [x] Daily open fields exist; adjusted open follows `open × adjclose / close`.
- [x] D6 development input begins 2020-06-01, including the preregistered development warm-up; target/formation month labels and date availability match the preregistered Aug-2021 to Sep-2026 target span.
- [ ] Coordinator confirms 2008-11 warm-up and full 2010-01 to 2020-10 holdout coverage. This worker did not inspect holdout data; that coordinator-only input check remains open.
- [x] Adjusted high/low use the same daily `adjclose/close` factor as adjusted open, per `specs/r5_decisions.md` item 12 and the frozen clarification.
- [x] Six D6 endpoints and the D4?D6 Holm family manifest are recorded in `specs/r4_trials.md` before outcome access.
- [x] Coordinator added `FROZEN: 2026-11-10` and the matching SHA-256 before any outcome access.

## Gate

**PASS for development input QA.** Coordinator holdout checks remain open; no D6 holdout data were accessed.
