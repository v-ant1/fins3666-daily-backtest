# R3 implementer cycle 4 results

## Summary

Four preregistered definitions were implemented. The high-dollar-volume family froze to EW30 because both candidates failed selection validity; `WEEKDAY63_SHR10` and `MONTHPHASE63_SHR10` were selected from the selection windows, but neither beat EW30 on the pooled development tests or achieved a significant pooled result. No cycle 4 direction passed criteria 1-5, and no sealed-holdout data was accessed.

## Preregistration and selection

`PREREG_cycle4.md` was saved before cycle 4 test runs. It specified the 2020-11-27 through 2022-12-30 selection windows, exact candidate formulas, full-strength long-only rank weights (a=1), 21-session anchor schedule, 1% trade band, 5 bp per-side actual-trade cost, test periods, and freeze/tie rule. The three frozen outcomes were saved before any complete test run.

| Family | Candidate | Dow selection result | Cross-asset selection result | Selection decision |
|---|---|---|---|---|
| High volume | `HVOL21_K15` | Invalid: 104-row signal history unavailable at first scheduled fill. | Invalid: first signal had only 4 qualifying events for one asset. | Excluded; freeze EW30 fallback |
| High volume | `HVOL21_K20` | Invalid: 104-row signal history unavailable at first scheduled fill. | Invalid: first signal had only 3 qualifying events for one asset. | Excluded; freeze EW30 fallback |
| WEEKDAY | `WEEKDAY63_SHR10` | Sharpe 0.552, turnover 33.24% | Sharpe 0.315, turnover 33.06% | Frozen |
| MONTHPHASE | `MONTHPHASE63_SHR10` | Sharpe 0.555, turnover 33.72% | Sharpe 0.296, turnover 32.87% | Frozen |

Both one-definition families were valid in the two selection universes and below the 50% turnover cap. Selection means were 0.433 for weekday and 0.426 for month-phase, but these are selection-only comparisons and do not establish test performance.

## Frozen test results


### HVOL: `EW30 fallback`

| Test period | Net return | EW30 return | Sharpe | EW30 Sharpe | Max drawdown | TE | IR | Turnover | Active share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dow 2023-01-03 to 2024-02-23 | 16.77% | 16.77% | 1.380 | 1.380 | -8.92% | 0.00% | 0.000 | 0.00% | 0.00% |
| Dow 2024-12-06 to 2025-12-31 | 16.28% | 16.28% | 1.025 | 1.025 | -15.16% | 0.00% | 0.000 | 0.00% | 0.00% |
| Dow 2026-01-02 to 2026-10-30 | 11.35% | 11.35% | 1.240 | 1.240 | -8.51% | 0.00% | 0.000 | 0.00% | 0.00% |
| Cross-asset 2023-01-03 to 2026-10-30 | 29.34% | 29.34% | 0.889 | 0.889 | -6.93% | 0.00% | 0.000 | 0.00% | 0.00% |

Pooled excess return: **0.00%**; bootstrap p-value versus EW30: **1.000**; DSR at 98 trials: **0.533**.

### WEEKDAY: `WEEKDAY63_SHR10`

| Test period | Net return | EW30 return | Sharpe | EW30 Sharpe | Max drawdown | TE | IR | Turnover | Active share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dow 2023-01-03 to 2024-02-23 | 11.68% | 16.77% | 0.974 | 1.380 | -8.94% | 3.30% | -1.259 | 35.62% | 25.86% |
| Dow 2024-12-06 to 2025-12-31 | 7.59% | 16.28% | 0.567 | 1.025 | -18.50% | 5.40% | -1.498 | 33.91% | 25.86% |
| Dow 2026-01-02 to 2026-10-30 | 12.88% | 11.35% | 1.377 | 1.240 | -7.74% | 4.55% | 0.375 | 31.97% | 25.86% |
| Cross-asset 2023-01-03 to 2026-10-30 | 22.80% | 29.34% | 0.614 | 0.889 | -10.45% | 3.97% | -0.314 | 37.55% | 25.86% |

Pooled compounded excess versus EW30: **-28.99%**; one-sided 10-session circular block-bootstrap p-value (10,000 draws): **0.951**; DSR at cumulative trial count 98: **0.278**.

### MONTHPHASE: `MONTHPHASE63_SHR10`

| Test period | Net return | EW30 return | Sharpe | EW30 Sharpe | Max drawdown | TE | IR | Turnover | Active share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dow 2023-01-03 to 2024-02-23 | 11.30% | 16.77% | 0.946 | 1.380 | -9.02% | 3.30% | -1.358 | 36.14% | 25.86% |
| Dow 2024-12-06 to 2025-12-31 | 7.15% | 16.28% | 0.537 | 1.025 | -19.16% | 5.46% | -1.555 | 34.79% | 25.86% |
| Dow 2026-01-02 to 2026-10-30 | 11.95% | 11.35% | 1.291 | 1.240 | -7.74% | 4.47% | 0.152 | 32.78% | 25.86% |
| Cross-asset 2023-01-03 to 2026-10-30 | 20.39% | 29.34% | 0.560 | 0.889 | -10.42% | 4.00% | -0.444 | 37.76% | 25.86% |

Pooled compounded excess versus EW30: **-34.82%**; one-sided 10-session circular block-bootstrap p-value (10,000 draws): **0.976**; DSR at cumulative trial count 98: **0.238**.

## Criteria 1-5

| Family / frozen choice | 1. Selection-only freeze | 2. Sharpe > EW in >=3/4 and pooled excess >0 | 3. TE >=3% or active share >=20% | 4. Bootstrap p <0.10; DSR reported | 5. Mean turnover <=50% |
|---|---|---|---|---|---|
| HVOL / EW30 fallback | PASS: fallback chosen after selection invalidity | FAIL: 0/4 Sharpe wins; pooled excess 0% | FAIL: active share 0%; TE 0% | FAIL: p=1.000; DSR=0.533 | PASS: 0% |
| WEEKDAY / `WEEKDAY63_SHR10` | PASS: frozen using selection only | FAIL: 1/4 Sharpe wins; pooled -28.99% | PASS: TE windows 3.30%, 5.40%, 4.55%, 3.97%; active share 25.86% | FAIL: p=0.951; DSR=0.278 | PASS: max test turnover 37.55% |
| MONTHPHASE / `MONTHPHASE63_SHR10` | PASS: frozen using selection only | FAIL: 1/4 Sharpe wins; pooled -34.82% | PASS: TE windows 3.30%, 5.46%, 4.47%, 4.00%; active share 25.86% | FAIL: p=0.976; DSR=0.238 | PASS: max test turnover 37.76% |

## Verdict and researcher feedback

**High dollar volume:** Neither variant could be evaluated as a valid selection portfolio. Dow has only 64 rows through the first signal close, short of the 104-row warmup, and cross-asset starts with only four or three qualifying events in one asset where five are mandatory. This is a data-window/minimum-event failure, not evidence for or against the event-return hypothesis; the preregistered fallback was EW30.

**Weekday relative-return seasonality:** It beat EW30 Sharpe in only one of four development periods and compounded to 29.0 percentage points less pooled wealth than EW30; the pooled p-value was 0.951. Turnover stayed under 50% and realized TE exceeded 3% in every window, so it is distinct, but activity did not translate into useful performance. The 63-session weekday averages were noisy despite shrinkage.

**Month-phase relative-return seasonality:** It beat EW30 Sharpe in one of four windows, had -34.8 percentage points pooled excess, and p=0.976. It had adequate realized TE and turnover, but the early/late month estimates did not transfer across Dow and cross-asset tests; the short sample and shrinkage were not enough to stabilize the rank order. Neither seasonal direction meets the development goal.

## Signal validation and execution

- Cost self-test from the copied validated harness passed. Candidate portfolios use next-open fills, actual trade notional costs, the 1% L1 band, initial buy cost, final liquidation cost, and a share-ledger reconciliation on each completed run. EW30 selection parity remains inherited from the cycle 2 check: Dow 14.141439% and cross-asset 0.785780%, matching the validated engine to six decimal places.
- Future-truncation: signal weights matched with all price/volume arrays cut at the signal close and the known session-date calendar retained. Valid data comparisons: 24/24 across first/middle/last eligible selection signal dates for K15, weekday and month-phase. K20 had no valid selection date in the supplied data; a controlled synthetic panel with at least five events verified both HVOL formulas, and synthetic checks also passed weekday and month-phase (4/4).
- The high-volume candidates have no valid selection weights at the selection-series start due insufficient history/minimum event counts, so they were excluded before testing. This follows the proposal's invalidation behavior.
- The flat-folder adapter was compared with the array harness on the selection window for both frozen cycle 4 strategies; maximum absolute wealth differences were below 3e-15.
- The supplied Dow and cross-asset files only were used. The sealed single-country holdout roster and prices were not read or downloaded.

## Coordinator-facing folder functions

Cycle 4 exposes `run_frozen_price_folder(price_folder, tickers, variant, period)` and named wrappers `run_hvol21_k15(...)`, `run_hvol21_k20(...)`, `run_weekday63_shr10(...)`, and `run_monthphase63_shr10(...)` in `code/cycle4_harness.py`. The frozen choices are EW30 for HVOL, `WEEKDAY63_SHR10`, and `MONTHPHASE63_SHR10`; neither active choice passed criteria 1-5, so no cycle 4 passer is proposed for holdout evaluation. Cycle 3 retains `run_idioskew63_a08(...)` in `code/cycle3_harness.py` for the prior development passer.

Example from a Python script, where `flat_folder` contains `TICKER.csv` for each of your 30 supplied names plus `SPY.csv`, with columns `date,open,high,low,close,adjclose,volume` and sufficient history before the evaluation start:

```python
import sys
sys.path.insert(0, r"C:\path\to\pivot_research\r3_impl\code")
from cycle3_harness import run_idioskew63_a08
from cycle4_harness import run_weekday63_shr10, run_monthphase63_shr10
tickers = [...]  # caller supplies exactly 30 unique symbols
flat_folder = r"C:\path\to\flat_prices"
period = ("2020-11-27", "2026-10-30")
idio = run_idioskew63_a08(flat_folder, tickers, period)
weekday = run_weekday63_shr10(flat_folder, tickers, period)
monthphase = run_monthphase63_shr10(flat_folder, tickers, period)
```

Use only coordinator-authorized holdout symbols when making sealed-holdout calls. Flat-folder wrappers take a folder path, 30 ticker names, and an inclusive `(start_date, end_date)` tuple; they read `SPY.csv` as the session calendar and do not embed a roster.

## Reproduction

Run the registered analysis at the project root with:

```powershell
py -3 A2\pivot_research\r3_impl\code\cycle4_harness.py
```

`outputs_cycle4/` contains frozen choices, metrics, daily wealth CSVs, significance estimates, charts and run inventory. `PREREG_cycle4.md` contains the rule fixed before tests.

## Run accounting and cumulative trial count

Cycle 3 ended at approximate count 94. Cycle 4 added four unique definitions, so final cumulative DSR input is **98**. Final registered run set: eight selection candidate-universe attempts (four candidates x two universes; four weekday/month-phase series valid and four high-volume attempts invalid), and eight frozen active candidate test series (two active families x four periods); the high-volume fallback uses the already-computed EW30 benchmarks. Flat-folder parity checks added two selection-window verification reruns.

Technical attempts are disclosed: an initial run stopped during raw-close loading before any portfolio series; a subsequent run completed selection and the four weekday test windows, then stopped on a missing future calendar tail for month-phase; after adding known-session dates, the final complete run produced all metrics above. The four weekday tests and first partial month-phase test were exact technical reruns, with no tuning or choice changes. The month-phase calendar tail uses exchange-closure rules to supply future session dates only beyond the provided price history; no synthetic future prices were used. All four formulas passed synthetic future-truncation checks.

