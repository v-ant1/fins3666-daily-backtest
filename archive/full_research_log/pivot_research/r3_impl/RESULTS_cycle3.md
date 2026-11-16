# R3 implementer cycle 3 results

## Summary

Cycle 3 tested six preregistered variants: idiosyncratic and systematic skew, a realized distribution contribution proxy at two tilt strengths, and two overnight-gap risk measures. Selection froze `IDIOSKEW63_a08`, `DIST63_a08`, and `GAPSHARE63_a08`; only idiosyncratic skew met all five development criteria, and no sealed-holdout data was accessed. The cycle-3 harness uses the copied validated engine data and cost assumptions, and its frozen-variant folder adapter matched the array harness on selection-window checks.

## Selection record

Rule was saved in `PREREG_cycle3.md` before tests: within each idea family, reject a candidate if either selection-universe signal failed or average actual turnover exceeded 50%; among remaining variants choose the highest unweighted mean of Dow and cross-asset net annualized daily Sharpe, ties by lower mean turnover then listing order. Selection periods were 2020-11-27 through 2022-12-30 only. The selected file was written before the first test-period evaluation.

| Family | Variant | Dow Sharpe | Dow turnover | Cross-asset Sharpe | Cross-asset turnover | Mean Sharpe | Frozen |
|---|---|---:|---:|---:|---:|---:|:---:|
| SKEW | `IDIOSKEW63_a08` | 0.546 | 29.03% | 0.182 | 29.96% | 0.364 | Yes |
| SKEW | `COSKEW63_a08` | 0.523 | 32.04% | 0.127 | 28.96% | 0.325 | No |
| DIST | `DIST63_a08` | 0.652 | 9.84% | -0.099 | 19.12% | 0.276 | Yes |
| DIST | `DIST63_a10` | 0.695 | 11.92% | -0.145 | 23.66% | 0.275 | No |
| GAP | `GAPVOL63_a08` | 0.498 | 15.13% | -0.372 | 6.14% | 0.063 | No |
| GAP | `GAPSHARE63_a08` | 0.407 | 22.71% | -0.019 | 15.79% | 0.194 | Yes |

All 12 candidate-universe selection series were valid and under the turnover cap. Choices: `SKEW=IDIOSKEW63_a08`, `DIST=DIST63_a08`, `GAP=GAPSHARE63_a08`. The DIST variants were close under the preregistered tie hierarchy: mean Sharpe selected a08.

## Frozen test-period results

Net returns include the stated actual-trade costs. Sharpe and drawdown are strategy versus EW30; tracking error and information ratio are relative to EW30.

### SKEW: `IDIOSKEW63_a08`

| Test period | Net return | EW30 return | Sharpe | EW30 Sharpe | Max drawdown | TE | IR | Turnover/rebalance | Active share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dow 2023-01-03 to 2024-02-23 | 16.21% | 16.77% | 1.318 | 1.380 | -8.67% | 1.79% | -0.244 | 28.92% | 20.69% |
| Dow 2024-12-06 to 2025-12-31 | 17.64% | 16.28% | 1.073 | 1.025 | -14.38% | 2.31% | 0.544 | 30.32% | 20.69% |
| Dow 2026-01-02 to 2026-10-30 | 15.37% | 11.35% | 1.579 | 1.240 | -9.15% | 3.39% | 1.306 | 27.49% | 20.69% |
| Cross-asset 2023-01-03 to 2026-10-30 | 39.22% | 29.34% | 1.052 | 0.889 | -7.13% | 1.99% | 1.018 | 33.59% | 20.69% |

Pooled excess return (compounded net strategy wealth minus EW30 wealth): **24.01%**. One-sided circular block-bootstrap p-value (10-session blocks, 10,000 draws): **0.019**. Deflated Sharpe at approximate cumulative trial count 94: **0.658**. Sharpe exceeded EW30 in **3/4** tests.

### DIST: `DIST63_a08`

| Test period | Net return | EW30 return | Sharpe | EW30 Sharpe | Max drawdown | TE | IR | Turnover/rebalance | Active share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dow 2023-01-03 to 2024-02-23 | 13.40% | 16.77% | 1.097 | 1.380 | -8.87% | 2.46% | -1.106 | 8.07% | 20.69% |
| Dow 2024-12-06 to 2025-12-31 | 16.32% | 16.28% | 1.110 | 1.025 | -13.09% | 3.97% | -0.046 | 13.12% | 20.69% |
| Dow 2026-01-02 to 2026-10-30 | 15.53% | 11.35% | 1.623 | 1.240 | -6.88% | 3.87% | 1.182 | 13.38% | 20.69% |
| Cross-asset 2023-01-03 to 2026-10-30 | 23.58% | 29.34% | 0.807 | 0.889 | -8.58% | 2.51% | -0.510 | 18.77% | 20.69% |

Pooled excess return (compounded net strategy wealth minus EW30 wealth): **-7.23%**. One-sided circular block-bootstrap p-value (10-session blocks, 10,000 draws): **0.714**. Deflated Sharpe at approximate cumulative trial count 94: **0.532**. Sharpe exceeded EW30 in **2/4** tests.

### GAP: `GAPSHARE63_a08`

| Test period | Net return | EW30 return | Sharpe | EW30 Sharpe | Max drawdown | TE | IR | Turnover/rebalance | Active share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dow 2023-01-03 to 2024-02-23 | 16.64% | 16.77% | 1.390 | 1.380 | -8.11% | 2.21% | -0.058 | 22.24% | 20.69% |
| Dow 2024-12-06 to 2025-12-31 | 16.21% | 16.28% | 1.029 | 1.025 | -15.19% | 2.58% | -0.031 | 24.36% | 20.69% |
| Dow 2026-01-02 to 2026-10-30 | 11.12% | 11.35% | 1.161 | 1.240 | -8.34% | 2.78% | -0.066 | 22.10% | 20.69% |
| Cross-asset 2023-01-03 to 2026-10-30 | 27.93% | 29.34% | 0.889 | 0.889 | -6.92% | 2.18% | -0.148 | 17.40% | 20.69% |

Pooled excess return (compounded net strategy wealth minus EW30 wealth): **-2.87%**. One-sided circular block-bootstrap p-value (10-session blocks, 10,000 draws): **0.621**. Deflated Sharpe at approximate cumulative trial count 94: **0.529**. Sharpe exceeded EW30 in **3/4** tests.

## Criteria 1-5

| Frozen idea | 1. Selection-only freeze | 2. Sharpe > EW in >=3/4 and pooled excess >0 | 3. TE >=3% or active share >=20% | 4. Bootstrap p <0.10; DSR reported | 5. Mean turnover <=50% |
|---|---|---|---|---|---|
| `SKEW` / `IDIOSKEW63_a08` | PASS: selection rule only | PASS: 3/4 Sharpe wins; pooled 24.01% | PASS: all test active shares ~20.69% (TE: 1.79%, 2.31%, 3.39%, 1.99%) | PASS: p=0.019; DSR=0.658 | PASS: max test mean 33.59% |
| `DIST` / `DIST63_a08` | PASS: selection rule only | FAIL: 2/4 Sharpe wins; pooled -7.23% | PASS: all test active shares ~20.69% (TE: 2.46%, 3.97%, 3.87%, 2.51%) | FAIL: p=0.714; DSR=0.532 | PASS: max test mean 18.77% |
| `GAP` / `GAPSHARE63_a08` | PASS: selection rule only | FAIL: 3/4 Sharpe wins; pooled -2.87% | PASS: all test active shares ~20.69% (TE: 2.21%, 2.58%, 2.78%, 2.18%) | FAIL: p=0.621; DSR=0.529 | PASS: max test mean 24.36% |

### Plain-English verdict and researcher feedback

**Idiosyncratic skew (`IDIOSKEW63_a08`) passes criteria 1-5 on the four development tests.** It beat EW30 on Sharpe in three windows, compounded to 24.01 percentage points more pooled wealth than EW30, had 20.69% active share, stayed below the 50% turnover limit, and produced a one-sided block-bootstrap p-value of 0.019. The deflated Sharpe is 0.658 at 94 trials, so the bootstrap evidence should be read alongside substantial selection history; the historical trial count is approximate. This is a development result only, not a sealed-holdout pass.

**Distribution contribution (`DIST63_a08`) fails criterion 2 and 4.** It beat EW30 Sharpe in two of four windows, had -7.23 percentage points pooled excess, and p=0.714; its low turnover does not repair the weak cross-asset result. The proxy is a realized payout contribution, not forward yield or futures carry, and the six-month window can be dominated by ex-distribution timing.

**Overnight gap share (`GAPSHARE63_a08`) fails criterion 2 and 4.** It beat EW30 Sharpe in three windows but pooled excess was -2.87 percentage points and p=0.621; it is economically distinct and below the turnover cap but does not show pooled value. This risk allocation may sacrifice compensation for overnight risk and does not reduce total volatility by construction. Systematic co-skew and gap-volatility were not selected by the registered rule; their selection Sharpe did not top their family.

## Signal and implementation validation

- Future-truncation: 48/48 signal-weight comparisons passed (18 Dow early, 12 Dow recent, 18 cross-asset; each valid sampled candidate at first, middle and last eligible dates). Signals use only completed bars through signal close.
- Cost self-test in the copied engine passed (no-drift and full-replacement cases, plus stayer/leaver trade accounting). The backtest records next-open fills, solves costs on actual traded notional, applies the 1% whole-rebalance band, and reconciles the share ledger to final wealth.
- The frozen-folder API matched the array harness exactly (maximum absolute wealth difference 0.0) for the three frozen functions on selection periods: Dow `IDIOSKEW63_a08`, Dow `DIST63_a08`, and cross-asset `GAPSHARE63_a08`. These are disclosed selection verification reruns; no test period was rerun.
- EW30 and the copied engine remain parity-validated by cycle 2 on selection windows: 14.141439% Dow and 0.785780% cross-asset return, matching to six decimals.
- Only the provided Dow and cross-asset files were used. No sealed holdout basket or symbols were read, downloaded, or tested.

## Frozen functions and reproduction

`code/cycle3_harness.py` exposes `run_frozen_price_folder(price_folder, tickers, variant, period, anchor=ANCHOR, rebalance_every=21)` and wrappers `run_idioskew63_a08(...)`, `run_dist63_a08(...)`, and `run_gapshare63_a08(...)`. Supply exactly 30 caller-provided ticker names and a folder of standard OHLCV CSV files (flat or engine-style with daily/lookback/delisted subfolders). The adapter derives adjusted open from `open * adjclose / close`, retains both close fields for the distribution formula, and does not embed any holdout roster.

Reproduce the registered run from the project root with:

```powershell
py -3 A2\pivot_research\r3_impl\code\cycle3_harness.py
```

The preregistration is `PREREG_cycle3.md`; machine-readable series, metrics, frozen choices, significance and charts are in `outputs_cycle3/`.

## Accounting and limitations

Unique cumulative trial count reported: approximately **94** (88 inherited plus six unique cycle 3 parameterizations). Cycle 3 completed 12 selection candidate-universe runs and 12 frozen candidate test-period runs. The generic-folder parity checks added three selection verification runs. The 48 invariance comparisons and cost/ledger checks are validations, not new variants; no candidate series failed. The 94 count inherits approximate historical accounting and correlated variants, so the deflated-Sharpe calculation is an adjustment, not a guarantee of generalization.
