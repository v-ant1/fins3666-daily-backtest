# R10 S6 — Post-hoc reverse-direction follow-up of S5

**Status: INDETERMINATE; no GO decision can be made.** Two reverse-side hypotheses were preregistered as new counted trials explicitly labelled **POST-HOC DIRECTION FROM S5**. Synthetic-only validation passed (70 cohorts per selector). The single real `--run-dev` invocation terminated without captured stdout and without creating `DEV_RESULT.json`; its outcome cannot be recovered, and it was not rerun. The GO list is empty because neither hypothesis has a verifiable result, not because a statistical NO-GO was measured.

| Idea | N | Net excess / NW lag-3 t | 2010–15 projected N / MDE | Haircut pass probability | Decision |
|---|---:|---|---|---:|---|
| S6-01 POST-HOC DIRECTION FROM S5: lowest short-volume-ratio quintile, long-only | unavailable | unavailable | unavailable | unavailable | INDETERMINATE |
| S6-02 POST-HOC DIRECTION FROM S5: low-minus-high quintile spread, both legs charged | unavailable | unavailable | unavailable | unavailable | INDETERMINATE |

## Frozen evaluation conventions

Both trials were registered before the real run. They use calendar month-end formation/exit, a five-session mean short-volume ratio, at least 100 eligible PIT names, equal-weight quintiles and stable ticker tie-breaks. S6-01 is long the lowest quintile versus gross EW PIT S&P 500; S6-02 is long low and short high, with the matched EW PIT benchmark shown as context and cancelling from the spread. Both charge 10 bp one-way on the absolute weight change, with 5/20 bp sensitivities; S6-02 charges both legs. NW t uses lag 3. The preregistered GO rule is net excess >0, NW t≥2, and 2010–2015 projected haircut pass probability≥30%.

The synthetic fixture passed before real data loading. The one real execution used the dev-only NPZ date window (2020-11-27..2026-10-30) and filename-filtered staged FINRA raw files; however, because the result artifact and stdout are absent, successful completion and cohort values cannot be attested. No outcome rerun was made. No `sealed_holdout*` file was opened and no pre-boundary price/return values were intentionally accessed. FINRA short-volume ratio remains a transaction-flow proxy, not short interest or a direct buyer-initiated measure.

## Part B — 2010–2015 FINRA daily-file feasibility (metadata only)

HEAD checks targeted the consolidated daily filenames `CNMSshvolYYYYMMDD.txt` at the official [FINRA CDN daily directory](https://cdn.finra.org/equity/regsho/daily/), for every Monday–Friday date in 2010–2015. No file body was requested or read. All HEAD requests returned 403 and no `Content-Length`; therefore **zero dates were confirmed accessible**. Weekday candidate counts include exchange holidays and are only a transparent count of attempted filenames, not trading-session counts.

| Year | Weekday filenames checked | HEAD 200 files | Available-date coverage confirmed | Other statuses |
|---:|---:|---:|---|---|
| 2010 | 261 | 0 | None | 261 × 403 |
| 2011 | 260 | 0 | None | 260 × 403 |
| 2012 | 261 | 0 | None | 261 × 403 |
| 2013 | 261 | 0 | None | 261 × 403 |
| 2014 | 261 | 0 | None | 261 × 403 |
| 2015 | 261 | 0 | None | 261 × 403 |

The directory endpoint itself returned 403. A request to the legacy `regsho.finra.org` path redirected to FINRA's catalog page rather than confirming individual historical files. These checks establish endpoint accessibility only; a 403 does not prove that no archival copy exists elsewhere. Metadata records are in [FINRA_HEAD_2010_2015.csv](FINRA_HEAD_2010_2015.csv). No 2010–2015 contents or values were accessed.

## GO list

None; both trials are indeterminate because the sole real-run result is unavailable.
