# Cumulative trial ledger for R10

Tag: L4. Reconciled from the specified R6/R9 records on 2026-11-12. This ledger distinguishes unique hypothesis/endpoints from execution attempts so a retry is not silently counted as a new discovery.

| Source family | Count used in R10 historical ledger | Count type | Sources and interpretation |
|---|---:|---|---|
| R6 Holm family | 21 | Registered endpoints | H1–H21 are the coordinator-owned family; unrun slots were assigned p=1 for that family. Sources: `R6_FINAL.md`, `specs/r6_holm_family.json`, `specs/r6_decisions.md`, `specs/r4_trials.md`. |
| R9 J2 development | 12 | Frozen portfolio variants | R9-V0 through R9-V11. Each counts, irrespective of result. Sources: `specs/r9_variant_log.md`, `r9/R9_VARIANTS.md`, `specs/r9_rules.md`. |
| D1 diagnostic | 5 | Execution attempts for one pre-registered diagnostic bundle | E01–E05; the first four failed before estimates, E05 completed the same registered diagnostic. Do not reinterpret these as five independent signals. Sources: `specs/r9_variant_log_D.md`, `r9/R9_D1_DIAGNOSIS.md`, `specs/r9_decisions.md`. |
| S2 development evidence | 7 | Counted attempts across the registered S2 development tests | Includes incomplete/failed executions as recorded in the execution ledger. Sources: `specs/r9_variant_log_S2.md`, `r9/S2_DEV_EVIDENCE.md`, `specs/r9_decisions.md`. |
| L-ADDS | 1 | Registered test | Direct S&P addition announcement-to-effective CAR test. Source: `specs/r9_variant_log_S2.md`, `r9/S2_INDEX_ADD_DEV.md`, `specs/r9_decisions.md`. |
| L-IDX4 | 2 | Execution attempts | The duplicate/failed measurement executions are counted; no development result was produced. Source: `r9/idx4/S2_INDEX_FLOW_DEV.md`, `specs/r9_decisions.md`. |
| L-IDX5 / L-IDX5B / L-IDX5C | 1 | Shared registered trial | These labels refer to the same frozen event list and one bounded measurement question; count once, including the final run. Sources: `r9/idx5/S2_INDEX_FLOW_DEV.md`, `r9/idx5/S2_INDEX_FLOW_FINAL.md`, `r9/idx5/S2_INDEX_FLOW_RESULT.md`, `specs/r9_decisions.md`. |
| J2 S&P holdout | 1 | Confirmatory holdout trial | One authorized and completed attempt; all four gates failed. Source: `r9/HOLDOUT_RESULT.json`, `r9/COORDINATOR_TO_SUPERVISOR.md` §29, `specs/r9_decisions.md`. |
| **Cumulative history** | **50** | **Counted attempts/endpoints by the requested R10 convention** | **21 + 12 + 5 + 7 + 1 + 2 + 1 + 1 = 50.** |

## How to use the counts

- **DSR:** Use 50 as the conservative cumulative R10 trial count before adding any newly pre-registered R10 trials. The historical J2 holdout recorded DSR `trial_count=15` under its earlier rule (three R6 portfolio Sharpe streams plus 12 J2 variants); that value is preserved in the historical result and is not rewritten. The R10 ledger includes additional diagnostics and failed attempts to avoid understating search history. Its 50 is a conservative search-history count, not a claim that 50 independent return streams were measured.
- **DSR variances:** Follow `specs/r9_dsr_variance_freeze.md`: primary `V=0.00008415393784762033` is decision-making; also report null sensitivity `V=1/(T−1)`. The runner reports both, and only primary DSR decides.
- **Holm:** R6's actual historical Holm family remains the 21 fixed H1–H21 endpoints, not 50 attempts. Holm counts unique registered hypotheses, not implementation retries. R10's coordinator must freeze an explicit R10 Holm manifest before its outcomes; include each distinct R10 primary hypothesis once and assign unrun family members `p=1`. Do not double-count the shared IDX5/5B/5C trial or count the five D1 attempts as five hypotheses.
- **Confirmatory boundary:** J2's 2016–2020 S&P holdout is spent and failed; no R10 strategy may use that period. The candidate 2010–2015 window was not read by L4. This ledger does not certify that other workers or SSI projects have not previously used it.

## R10 synthetic integration trial

`L4-SYNTH-01` is the one pre-registered pipeline test, separate from strategy discovery counts. It passed on synthetic fixtures only; result: `r10/L4/SYNTHETIC_VALIDATION.json`.
