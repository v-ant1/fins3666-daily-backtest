# D7 runner and specification map

This runner implements the current draft at `specs/r4_prereg/D7.md`; it does not edit that specification and does not open `r5_D7/LINKS.csv`. It is not authorized to run while the preregistration is still a draft. The current D7 text is unfrozen, so a real invocation must refuse.

## Freeze and execution controls

| D7 rule | Runner implementation |
|---|---|
| A content-based `FROZEN` date and matching SHA-256 are required before outcomes. | `main()` and `run()` call `require_frozen_prereg('D7')`; the shared harness validates the date and canonical SHA-256. |
| Input access requires explicit authorization. | `main()` requires `--execute` before it invokes `run()`; without it the process returns 2 without opening inputs. |
| D7 fits the 30-row goal budget. | `authorize_trial()` checks the frozen spec and current ledger; `_require_log_capacity()` reserves all six endpoint rows before any input is opened. |
| Exactly one trial-log row per each of six endpoints. | `run()` calls `append_trial()` once for each of the six named endpoint records after writing the results. |

## Specification line mapping

Line numbers below refer to the current D7 draft headings and endpoint numbering; they may change if the coordinator revises the draft before freeze.

| Specification section / text | Implementation |
|---|---|
| **Universe, inputs, link definition, and point-in-time availability**: adjusted Dow OHLC, point-in-time roster, SIC codes, event records, effective links | Input contract is described below. `_load_bundle()` validates the 30-name asset order, dates, array shapes, event IDs and source URLs, response-session consistency, link indexes and link effective intervals. |
| **Earnings event and signal construction**: normalize release and acceptance to ET; `a` first open strictly after latest known timestamp; `f` first session after filing date; `d=later(a,f)`; unknown release time means `d=f` | `derive_response_session()` implements `f`, `a`, and `d`. `_load_bundle()` recomputes `d` and rejects a response-session field that disagrees. `_event_shocks()` computes adjusted open-to-close customer return less same-session EW30 open-to-close return. |
| **Earnings event and signal construction**: public links only; average event shocks by supplier; exclude customer itself and supplier with own event on `d` | `_date_scores()` uses link first-usable and end dates, aggregates by supplier, and excludes self and all same-date event customers from recipient scores. |
| **Pre-outcome input-only feasibility gate**, item 1: at least 30 response dates and 3 active supplier recipients | `_feasibility()` runs on a metadata-only NPZ before the runner opens the separate price file. It checks response dates, active roster, usable event-customer links, self/own-event exclusions, recipient breadth and then stops on failure. |
| **Pre-outcome input-only feasibility gate**, item 2: at least 10 directed Dow pairs | `_feasibility()` builds the set of event-date-usable directed customer–supplier pairs and stops when the count is below 10. |
| **Pre-outcome input-only feasibility gate**, item 3: complete within-SIC shuffle eligibility for all eligible event dates | `_feasibility()` checks each customer's observed supplier SIC counts against active alternate-supplier pools, excluding same-date event customers. `_shuffle_for_date()` and `calculate()` then require all 500 full draws and all primary dates; any incomplete draw ends the run. |
| **Primary mechanism test and placebos**: date-wise Spearman rank IC, supplier return open `d+1` to close `d+5`, Newey–West Bartlett lag 4 | `_spearman()`, `_forward()`, `_ic_series()`, and `_nw()` implement those definitions. Endpoint 1 reports its series, mean, NW standard error/t-statistic and one-sided normal p-value; the gate uses mean ≥0.0183, positive sign and NW t≥2. |
| **Primary mechanism test and placebos**: 500 within-industry shuffles, one `default_rng(20261110)`, preserve event customers/shocks, per-customer edge counts, date SIC counts and active roster | `calculate()` creates one seeded generator for all draws. `_shuffle_for_date()` samples within each observed two-digit SIC bucket without replacement within customer; `_date_scores()` retains the observed event shocks and date's event customers. It reports the shuffle mean distribution and stops if a complete date series cannot be formed. |
| **Registered endpoints**, endpoint 2: observed mean versus shuffle means, finite-sample one-sided p and 95th percentile | `D7-2` uses `(1 + count(shuffle_mean >= observed_mean))/501`, the observed mean, shuffle 95th percentile and pass flag. |
| **Registered endpoints**, endpoint 3: date-wise average shuffled IC series against zero, two-sided NW lag-4 | `D7-3` averages the 500 IC values by date, computes NW lag 4 and a two-sided normal p-value. It is reported independently from TOST and is not a gate. |
| **Registered endpoints**, endpoint 4: averaged shuffle-series equivalence TOST within ±0.0183 | `_tost()` reports the 90% NW interval, both one-sided component p-values, the larger TOST p-value and equivalence decision. |
| **Primary mechanism test and placebos**, fixed 20-session timing placebo: preserve original response-date links and shock, shift outcome date; exclude shifted dates without a five-session outcome | `calculate()` reuses the original response-date score vectors at `d+20`, then `_ic_series()` evaluates the same five-session return at that date. It reports the TOST and number of excluded events. No later links are added. |
| **Registered endpoints**, endpoint 5: timing-placebo mean IC TOST within ±0.0183, NW lag 4 | `_tost()` applies the frozen equivalence rule and returns both component tests, 90% CI and larger p-value. |
| **Portfolio, cost cap, and inference**: proceed only after primary, shuffle-comparison and both equivalence gates; every fifth session; top-five equal-weight; fallback to EW30 if fewer than five finite scores | `_portfolio()` is called only after all mechanism/placebo gates pass, selects the five highest scores with ticker tie-break and uses EW target when fewer than five signals exist. |
| **Portfolio, cost cap, and inference**: cost 0.05% per dollar traded; 0.50 NAV cap; 5,000 circular block draws of length 10 and seed 20261110; DSR trial count 30 | `_portfolio()` applies the per-side cost to total buy+sell turnover, caps the weight transition at 0.50, calls the shared 10-session circular block bootstrap with 5,000 draws/seed 20261110, and reports DSR with 30 trials. Holm remains pending the coordinator's full 27-endpoint family. |
| **Registered endpoints**, endpoint 6: portfolio net excess versus EW30 | `D7-6` remains present even when not run; when authorized by the gates, it reports net excess, raw bootstrap p and portfolio statistics. Adjusted Holm p is explicitly pending the full family. |
| **Sealed holdout procedure** | No holdout inputs or code path are present in this runner. It accepts only the development date range and refuses dates outside 2020-11-27 through 2026-10-30. |

## Input bundle contract

The coordinator's bundle builder must write two NPZ files so the metadata-only gate runs before any OHLC is opened.

`D7_METADATA.npz` contains:

- `dates` and the union of point-in-time Dow tickers in fixed chronological/ticker order (the active roster mask must contain exactly 30 names on every session);
- `roster_mask`, `sic2` as assets-by-sessions arrays;
- event columns `event_customer_idx`, `event_customer_cik`, `event_filing_date`, `event_form`, `event_items`, `event_release_timestamp_et` (blank if unknown), `event_acceptance_timestamp_et` and `_utc` (blank if unknown), `event_accession_number`, exhibit `event_source_url`, and derived `event_response_session`;
- link columns `link_customer_idx`, `link_supplier_idx`, both CIKs, `link_source_form`, `link_source_accession`, `link_filing_date`, `link_source_url`, `link_first_usable_session`, and `link_valid_to` (blank means still active through the development end; a supplied end date is inclusive).

`D7_PRICES.npz` contains matching `dates`, `assets`, `adjusted_open`, and `adjusted_close`. Prices must use the project's frozen adjusted-open convention. The runner confirms identical dates and asset order before merging the two bundles. It does not calculate a portfolio until all mechanism and placebo gates pass.

## Synthetic verification and current status

`test_d7_synthetic.py` creates fabricated weekday calendars, prices, rosters, events and links in temporary files. It checks the combined event clock, metadata-before-price feasibility ordering, all six endpoint records on a synthetic eligible fixture, and refusal without `--execute`. The tests do not read project input bundles or SEC link contents.

The six-endpoint program is implemented and synthetically checked. It remains **unrun on project data** by design. Since `specs/r4_prereg/D7.md` is currently marked DRAFT, the production runner refuses until the coordinator freezes it with a valid hash and supplies the QA'd split metadata/price bundle.
