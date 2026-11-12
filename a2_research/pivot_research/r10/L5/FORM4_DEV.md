# L5 — Form 4 opportunistic purchase development evidence

**Tag:** L5 · **Trial:** R10-L5-01 (one counted trial; registered 2026-11-12 13:23 Australia/Sydney, with issuer-day clarification appended before outcomes)  
**Decision: NO-GO for freezing.** The primary 10 bp one-way net mean CAR is negative, its 95% interval includes zero, and the 2010–2015 primary-gate pass probability after a 50% winner’s-curse haircut is 0.9%. The candidate also inherits a strict data-boundary deviation described below, so this result is exploratory and cannot authorize a freeze.

## Frozen specification and implementation

S&P 500 PIT issuers; non-derivative Form 4 transaction code P; officer/director reporting owners; routine insider rule follows Cohen–Malloy–Pomorski. With dev-only history, require three complete prior calendar years and classify an insider as opportunistic only if there was no P/S transaction in the same calendar month in any of those years; exclude earlier trade dates (history begins 2024-01-01). Routine activity is observable only in the S&P PIT issuer panel. Aggregate qualifying transactions by issuer CIK × SEC acceptance date (Eastern), using the earliest qualifying acceptance timestamp that day. Enter next session open after acceptance, or next-next session open after acceptance later than 4 p.m. ET; hold 20 sessions including entry, exit at session-20 close. CAR is stock adjusted open-to-close holding return less compounded daily EW S&P 500 PIT return over the same sessions. Primary cost is 10 bp one way; sensitivities are 5 and 20 bp one way. The full definition and fallback were recorded before outcome access in `specs/r10_trial_log.md`.

SEC public submissions metadata supplied exact acceptance timestamps for all 2,285 eligible P transaction rows from 301 issuer CIKs (100% timestamp match). The run used 49 missing-symbol price GETs from Alpaca SIP with `adjustment=all`; all returned without errors. Twelve issuer-days were excluded for missing stock price or absent PIT membership at acceptance/entry. There were 1,044 priced events. The 2010–2015 SEC archive manifest confirms 24 quarterly archives by HEAD metadata, totaling 266,331,695 compressed bytes; archive bodies were not read, so Form 4 row volume is not verified.

## Development results

Primary values are per-event net CAR; 95% CIs are two-sided Student-t intervals over events (date-cluster robust interval was materially the same: −0.847% to +0.137%).

| Cost, one way | N | Mean net CAR | SD | Median | 95% CI |
|---:|---:|---:|---:|---:|---:|
| 5 bp | 1,044 | −0.255% | 8.098% | −0.029% | [−0.747%, +0.237%] |
| **10 bp** | **1,044** | **−0.355%** | **8.098%** | **−0.129%** | **[−0.847%, +0.137%]** |
| 20 bp | 1,044 | −0.555% | 8.098% | −0.329% | [−1.047%, −0.063%] |

By entry year at the primary cost: 2024 N=252, mean +0.226%; 2025 N=475, −1.091%; 2026 N=317, +0.286%. There were 458 distinct SEC acceptance dates, averaging 2.28 events (median 2, maximum 8); 276 dates had multiple events.

## 2010–2015 power planning

Extrapolating the dev rate over six years gives **N_holdout ≈ 1,058**. With family=1, one-sided α=.05 and 80% power, `MDE = 2.4865 × 8.098% / √1,058 = 0.619%`. Halving the primary net mean for winner’s curse gives −0.177%, for an estimated positive primary-gate pass probability of **0.9%**. The probability is for the event-mean gate only, not full strategy qualification.

## Data and interpretation limits

- **Boundary deviation:** the initial analysis script loaded the complete `form4_dev.parquet` before filtering rows to the dev date window. No pre-boundary price or return values were read, and pre-boundary filing rows were excluded before history construction, signal classification, or outcome calculations; however, their date fields were evaluated by the filter. This violates the strict read boundary. The script has since been changed to use Parquet predicate pushdown, but this single counted trial was not rerun after observing its result. That deviation is an independent reason not to freeze.
- SEC code P includes open-market *or private* purchases; the source does not distinguish the two. The routine test uses reported P/S activity only among observed S&P issuers, not every security an insider may have traded. As-filed amendments are retained upstream.
- The L3 idea brief records material overlap with previous R6 Form 4 screens. The result is development evidence only and does not establish a general absence of insider-purchase predictability.

Reproducibility artifacts: `analyze_form4.py`, `event_results.csv`, `annual_results.csv`, and `analysis_summary.json` under `r10/L5/`. Trial registration and the L5 decision are in `specs/r10_trial_log.md` and `specs/r10_decisions.md`.
