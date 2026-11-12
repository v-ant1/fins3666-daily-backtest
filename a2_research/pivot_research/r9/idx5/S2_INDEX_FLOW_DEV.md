# S&P Index Flow — L-IDX5 retry report

**Status: S2 exhausted under the one-retry rule.** This bounded retry of the crashed L-IDX4 trial was registered before price access. Metadata was built and frozen, but the measurement runner stopped at its single-process preflight; no Alpaca endpoint was called, no prices were observed, and no per-event result rows exist.

## Frozen metadata

The frozen event file is `r9/idx5/event_list_frozen.csv`, SHA-256 `aea1e01b79c5a552728f78ca4eda2bd7628a4e1a7c24131d18d32b97b2c582d2`. Development events are the unchanged L-IDX4 set: 105 S&P 500 and 234 S&P 400 additions.

| Holdout metadata count | S&P 500 | S&P 400 | Total |
|---|---:|---:|---:|
| Candidate rows | 125 | 245 | 370 |
| Announcement date found | 100 | 179 | 279 |
| Missing announcement date | 25 | 66 | 91 |
| Frozen dated events | 99 | 156 | 255 |

The press archive was searched by company name with “Set to Join,” then checked for ticker, index, and an announcement before the effective date within 60 days. Company names for 121 of 125 S&P 500 ticker/date candidates were matched from the public Wikipedia historical changes table; the public table supplied company names for the S&P 400 events. Twenty-two S&P 500-to-400 migrations and two dated events outside the matching holdout window were excluded. The allowlisted holdout roster was read for ticker and effective-date fields only. No sealed NPZ or other sealed file was opened.

## Measurement launch and decision

The price runner was designed for one event at a time, per-event exception handling, immediate CSV flushes, ticker error logging, and counts-only holdout bar checks. On launch, its process guard treated transient launcher PID 60832 as another active measurement process and exited before any API request. A follow-up process inspection found no active idx5 measurement instance. The coordinator ruling says the one retry exhausts S2 if it fails, so no second launch was made.

Development N, mean, SD, median, confidence interval, index split, and net-cost means were not measured. Holdout bar coverage by index, N_holdout, missing percentage, and MDE are unavailable. Since there is no measured primary net mean or MDE comparison, no preregistration was drafted; S2 is recorded exhausted under the bounded-retry rule.

## Artifacts

- `r9/idx5/build_metadata.py` — metadata source search and event-list freeze.
- `r9/idx5/run_measurement.py` — checkpointing runner; stopped before requests by the false-positive process guard.
- `r9/idx5/event_list_frozen.csv` — frozen metadata event list.
- `r9/idx5/metadata_search_all_candidates.csv` and `r9/idx5/metadata_candidates_missing_announcement.csv` — metadata audit counts.
