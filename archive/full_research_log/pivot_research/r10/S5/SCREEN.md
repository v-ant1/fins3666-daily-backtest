# R10 S5 — FINRA short-sale flow and pressure reversal

**Decision: NO-GO for all four hypotheses.** None meets the required joint gate (monthly net excess > 0, Newey–West lag-3 t ≥ 2, and 2010–2015 haircut pass probability ≥ 30%). The only positive mean, S5-04, has eight observations, t=0.07, and 5.4% haircut pass probability.

| Idea | N months | Gross excess | Net excess / NW t | 2010–15 projected N / MDE | Haircut pass probability | Net excess at 5 / 10 / 20 bp | Positive years | Mean one-way turnover / cost | Cost / |gross excess| | Decision |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---|
| S5-01 Five-session short-volume-ratio pressure | 67 | −0.120% | −0.233% / −2.08 | 67 / 0.328% | 0.6% | −0.177% / −0.233% / −0.346% | 0/6 | 57.1% / 11.3 bp | 93.5% | NO-GO |
| S5-02 Short-volume-ratio acceleration | 67 | −0.0001% | −0.158% / −2.03 | 67 / 0.241% | 0.7% | −0.079% / −0.158% / −0.317% | 3/6 | 79.8% / 15.8 bp | 116,108% | NO-GO |
| S5-03 High short-volume flow with volume confirmation | 67 | −0.362% | −0.508% / −3.64 | 67 / 0.363% | 0.04% | −0.435% / −0.508% / −0.654% | 0/6 | 73.8% / 14.6 bp | 40.4% | NO-GO |
| S5-04 Extreme-pressure reversal | 8 | +0.243% | +0.064% / +0.07 | 12 / 2.326% | 5.4% | +0.154% / +0.064% / −0.115% | 3/4 observed | 95.7% / 17.9 bp | 73.5% | NO-GO |

## Execution and data

The four hypotheses were registered in `specs/r10_trial_log.md` before development outcome access. The shared runner passed its synthetic-only validation before the successful run; its synthetic fixture also explicitly checks safe handling of a sparse selector that yields zero cohorts. The successful run used 1,488 daily FINRA Reg SHO files dated 2020-11-27 through 2026-10-30, with all 1,488 source dates matched, plus the same-period dates, adjusted closes and PIT roster from `r9/data/J2_DEV_FROM_20201127.npz`. No pre-boundary prices/returns or sealed holdout contents were accessed in the successful run. Mean benchmark price coverage was 95.5%; mean signal eligibility was 94.2%, 94.1%, 93.3%, and 14.0% of the PIT roster for S5-01 through S5-04. S5-04 formed only eight monthly cohorts after its fixed 80th-percentile condition and 100-name minimum; its power estimate therefore projects only 12 observations.

The common formation is each calendar month-end; the portfolio is equal-weight long-only top quintile, held close-to-close through the next month-end against gross EW PIT S&P 500. The primary cost is 10 bp per dollar of absolute weight change at formation, including the initial cash-to-book allocation; 5/20 bp sensitivities use the same weights. The 2010–2015 N is projected from the observed annual cohort rate, with one-sided alpha .05, 80% power and a 50% haircut to the mean for the positive-mean pass probability. These are planning estimates, not historical coverage or holdout results. FINRA short-volume ratio is a short-sale transaction-flow measure, not short interest or a direct buyer-initiated trade measure; its historical all-listed availability and source-definition continuity are unverified.

## Protocol notes

- **Pre-registration source-inspection deviation:** before registering S5, the first lines of `r6_data/finra_regsho/daily_coverage.csv` were opened for schema/coverage inspection. Those lines included 2020-06-01 `mean_name_short_ratio` values, which are pre-2020-11-27 FINRA signal summaries. They were not used to choose signal parameters or in the harness, but this violates the task's no-pre-boundary-values rule and independently bars any freeze/confirmation claim. No pre-boundary price or return values were read.
- Two development attempts stopped before signal scoring or outcome calculation: first, the loader was missing its roster argument; second, parsing failed on decimal volume fields. Both pre-outcome fixes are recorded in the trial log. Synthetic validation passed after the fixes and before the one completed outcome run.
- During the successful run, NumPy emitted an all-NaN median warning for securities with no volume history in the required lookback. Those names fail the fixed eligibility rule; the results were not changed or rerun.
- No outcome reruns or post-outcome changes were made. Annual net-excess means and all row-level cohort outcomes are in `DEV_RESULT.json`.

## GO list

None.
