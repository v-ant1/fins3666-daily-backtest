# L-D1 — D1 near-miss diagnosis

**Verdict: do not register D2 as a rescue of D1.** D1 missed its required signal t-statistic (1.91 versus 2.00), and its year-by-year pattern is uneven. The placebo passed, but the Holm-adjusted primary p-value was 0.056 and no portfolio test was run. Under the R9 rules D1 is not eligible for refinement. A new study could be considered only as a separately registered hypothesis with a clean future or otherwise untouched holdout; it must not be presented as a continuation that repairs D1.

## What the saved D1 result says

The frozen development run used 297 eligible weekly formation dates and reported mean negative-FINRA-pressure IC 0.009374, Newey–West t(4) 1.908, raw one-sided p 0.0282, and R6-family Holm p 0.0564. It passed its SIC2 shuffle placebo (p 0.0020), but missed the preregistered t ≥ 2 gate. The portfolio endpoint was consequently not run. Its returns, costs, turnover, active share, Sharpe, and portfolio pass probability are unknown.

## Stability and horizon diagnosis

I ran the pre-logged exploratory suite on development observations dated 2020-11-27 or later. To comply with the date boundary without using warm-up values, the newly formed five-session D1 score starts on 2020-12-04, after five fully post-cutoff FINRA sessions. Formation outcomes use t+2 open and the listed horizon's closing price; all rows are within the development window. These exploratory figures therefore omit the first frozen D1 formation, which had a pre-cutoff signal warm-up, and are not a reproduction of the frozen 297-date statistic.

| Return horizon from t+2 open | Formation dates | Mean date-wise IC | Share of dates with positive IC |
|---|---:|---:|---:|
| 1 session | 297 | −0.0098 | 47.1% |
| 2 sessions | 296 | −0.0029 | 49.3% |
| 5 sessions (registered) | 296 | 0.0095 | 54.1% |
| 10 sessions | 295 | 0.0111 | 55.6% |
| 20 sessions | 293 | 0.0184 | 57.3% |

The horizon sensitivity is descriptive only. It suggests little short-lag continuation and a somewhat stronger positive association over longer windows, but those horizons were not registered and cannot replace the failed five-session test.

At the registered five-session horizon, annual mean date-wise ICs were:

| Year | Dates | Mean IC | Positive-IC dates | Mean eligible names/date | Minimum names/date |
|---|---:|---:|---:|---:|---:|
| 2020* | 4 | 0.0124 | 75.0% | 459.5 | 459 |
| 2021 | 51 | −0.0070 | 45.1% | 464.0 | 458 |
| 2022 | 50 | 0.0081 | 56.0% | 472.0 | 467 |
| 2023 | 50 | 0.0009 | 50.0% | 478.7 | 476 |
| 2024 | 50 | 0.0191 | 64.0% | 481.8 | 479 |
| 2025 | 50 | 0.0271 | 60.0% | 488.1 | 482 |
| 2026** | 41 | 0.0085 | 46.3% | 495.6 | 490 |

* December only; the first four usable formations after the cutoff. **Through October 30. The rounded per-year means are not significance tests. The pattern is not stable: 2021 was negative, 2023 was essentially flat, 2024–25 were stronger, and less than half of 2026 dates were positive.

## Coverage, source quality, sign, and overlap with J1/J2

Coverage does not look like the main explanation for the miss. The frozen joint formation coverage was 94.84% for the S&P mechanism panel and 97.49% for the Dow, with 297/298 scheduled S&P dates above 250 eligible names. FINRA paired-ratio input coverage in the R7 manifest was 99.91% for S&P and 100% for Dow before joining to prices; the D1 joint-coverage report shows the lower combined figures after price availability is required. In this strictly post-cutoff diagnostic, eligible S&P names averaged about 460–496 per formation and increased over time. Missing names and bars remain a limitation, but do not explain a t-statistic just below its gate.

The signal is correctly oriented in the registered direction: higher D1 score means lower FINRA facility short-volume ratio, and the positive five-session mean IC has the predicted sign. No sign flip is supported as a rescue. The signal is a noisy proxy: FINRA Reg SHO short volume records short-sale transactions reported by specific facilities, not net short positions or investor intent. Short sales may be covered the same day or reflect liquidity provision; the denominator is facility-reported volume rather than consolidated market volume. FINRA publication times are absent from the staged panel, which is why D1 used a conservative t+2 entry. High row coverage does not remove these measurement limitations.

The trial-free shared-date rank comparison finds D1 modestly distinct from J1/J2. After orienting J1/J2 as the registered reversal portfolio score (the negative of raw SIC2-relative return, with J2's four-formation smoothing), pooled rank correlations with D1 are about **+0.120 for J1** and **+0.126 for J2**; average date-level correlations are about +0.121 and +0.125. The common mask has 296 dates/133,767 ticker-date pairs for J1 and 293 dates/132,106 pairs for J2. This low correlation is consistent with different inputs, though both signals operate on the same equity universe and short horizon. It is not evidence that combining them improves returns.

## Holdout feasibility and partial-view notice

The D1 preregistration says FINRA daily files have been available since 2009. The staged Dow holdout manifest covers 2010-01-04 through 2020-10-30, but has 720 expected source files missing or unavailable, concentrated in 2013–2016; it uses older facility files before CNMS became available in 2018. The coordinator has now reported that raw rows from the 2018–2019 `finra_si` archive were accidentally displayed. Treat the Dow FINRA short-data holdout as **partly viewed**: D2 cannot claim the 2018–2019 segment as never viewed. I did not open any holdout files.

Possible clean alternatives are limited:

- A pre-2018 Dow segment may remain untouched, but its usable sessions and ticker coverage need coordinator verification from manifests only, and the 2013–2016 file gaps make its power materially weaker. It would be a new, shorter holdout, not the full 2010–2020 test.
- A different universe is viable only if it has a separate untouched holdout source and point-in-time membership/data; the staged manifest says there is no sealed S&P holdout now.
- A forward period after a fresh preregistration could be clean, but it requires waiting for new observations and should be treated as a new study.

None of these alternatives makes D1 eligible under the current R9 refinement rules.

## Pass probability and decision

For planning only, I apply an explicit 50% winner's-curse haircut to the observed t of 1.91, yielding an assumed true t near 0.95. Under a simple normal approximation, that gives roughly a **15%** chance of clearing the unadjusted t ≥ 2 signal gate on a comparable independent sample. The actual full-study probability is lower and not estimable from the saved artifacts: D1's R6-family adjusted primary p was already 0.056, the signal varies sharply by year, and no Dow portfolio outcome exists. My rough estimate for passing all gates is **below 10%**, with substantial uncertainty. This is not a power calculation or a calibrated forecast.

The logged suite required five execution attempts: four setup/code failures before the fifth produced the registered diagnostic output. All attempts are counted in `specs/r9_variant_log_D.md`; the successful figures above are exploratory and do not alter D1's frozen verdict. D1's rank comparison to J1/J2 is logged as descriptive and trial-free. No holdout was opened, no portfolio was run, and no D2 or holdout was frozen.

## Reproduction artifacts

- Saved diagnostic output: `report_drafts/repro/D1_DIAGNOSTIC_OUTPUT.json`
- Logged diagnostic script: `report_drafts/repro/d1_diagnostic.py`
- Trial and retry ledger: `specs/r9_variant_log_D.md`
- Decision record: `specs/r9_decisions.md`
