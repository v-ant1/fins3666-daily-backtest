# R3 implementer results - cycle 2

## Outcome

**SKEW63_a08 is the only direction that meets development criteria 1, 2, 3 and 5, but it fails the pooled significance requirement (criterion 4).** Its net Sharpe exceeded EW30 in three of four test periods and its pooled return was positive, but the 10-session block-bootstrap p-value was 0.218. ILLIQ63_a08 and DOWNBETA63_Q25_a08 also fail the pooled significance criterion and miss criterion 2. No sealed-holdout data was accessed; the coordinator must perform that one-time evaluation for any direction under consideration.

## Selection and frozen choices

The choices below used only 2020-11-27 through 2022-12-30 in the Dow and cross-asset universes. Within each family, variants above 50% average turnover in either selection universe or with an invalid signal were ineligible; the remaining candidate with the highest mean of the two net Sharpe ratios was frozen. All six variants passed signal validity and turnover screens.

| Family / variant | Dow Sharpe | Dow turnover | Cross-asset Sharpe | Cross-asset turnover | Mean Sharpe | Decision |
|---|---:|---:|---:|---:|---:|---|
| ILLIQ21_a08 | 0.46 | 14.97% | 0.23 | 6.46% | 0.35 | Eligible, not selected |
| ILLIQ63_a08 | 0.50 | 7.99% | 0.23 | 4.50% | 0.36 | Frozen |
| SKEW42_a08 | 0.54 | 38.90% | 0.02 | 36.97% | 0.28 | Eligible, not selected |
| SKEW63_a08 | 0.51 | 29.94% | 0.12 | 31.69% | 0.32 | Frozen |
| DOWNBETA63_NEG_a08 | 0.60 | 27.34% | -0.21 | 18.09% | 0.20 | Eligible, not selected |
| DOWNBETA63_Q25_a08 | 0.64 | 33.16% | -0.09 | 22.01% | 0.28 | Frozen |

Frozen variants: **ILLIQ63_a08**, **SKEW63_a08**, **DOWNBETA63_Q25_a08**. The prior approximate cumulative count was 82 after cycle 1; adding six unique cycle 2 variants gives **88** for DSR reporting.

## Frozen development test results

Net return is the candidate portfolio total return after modeled fees; EW30 uses the same dates, fills and 5 bp per-side cost model. Turnover is mean actual traded notional / pre-trade NAV per rebalance (initial purchase excluded from the rebalance average).

| Frozen variant | Period | Net return | EW30 return | Excess | Sharpe / EW30 Sharpe | Max DD | TE vs EW30 | IR | Turnover |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ILLIQ63_a08 | DOW_OOS1 | 13.64% | 16.77% | -3.14% | 1.04 / 1.38 | -9.83% | 2.38% | -1.01 | 8.20% |
| ILLIQ63_a08 | DOW_OOS2 | 18.47% | 16.28% | 2.19% | 1.11 / 1.02 | -14.79% | 2.79% | 0.72 | 8.08% |
| ILLIQ63_a08 | DOW_OOS3 | 9.36% | 11.35% | -1.99% | 0.93 / 1.24 | -9.42% | 3.08% | -0.66 | 8.87% |
| ILLIQ63_a08 | XASSET_OOS | 25.56% | 29.34% | -3.78% | 0.77 / 0.89 | -7.30% | 1.22% | -0.63 | 4.06% |
| SKEW63_a08 | DOW_OOS1 | 14.00% | 16.77% | -2.77% | 1.16 / 1.38 | -8.71% | 1.98% | -1.14 | 30.61% |
| SKEW63_a08 | DOW_OOS2 | 18.51% | 16.28% | 2.23% | 1.11 / 1.02 | -13.73% | 2.75% | 0.74 | 34.15% |
| SKEW63_a08 | DOW_OOS3 | 13.89% | 11.35% | 2.54% | 1.46 / 1.24 | -9.13% | 3.38% | 0.83 | 29.36% |
| SKEW63_a08 | XASSET_OOS | 36.21% | 29.34% | 6.87% | 0.95 / 0.89 | -7.39% | 2.38% | 0.62 | 33.25% |
| DOWNBETA63_Q25_a08 | DOW_OOS1 | 15.57% | 16.77% | -1.20% | 1.33 / 1.38 | -7.92% | 2.20% | -0.46 | 37.68% |
| DOWNBETA63_Q25_a08 | DOW_OOS2 | 12.58% | 16.28% | -3.71% | 0.89 / 1.02 | -12.42% | 3.86% | -0.92 | 29.10% |
| DOWNBETA63_Q25_a08 | DOW_OOS3 | 14.39% | 11.35% | 3.04% | 1.60 / 1.24 | -7.84% | 3.15% | 1.04 | 33.94% |
| DOWNBETA63_Q25_a08 | XASSET_OOS | 23.03% | 29.34% | -6.31% | 0.90 / 0.89 | -5.57% | 3.18% | -0.46 | 22.76% |

Pooled excess compounds candidate returns and EW30 returns across the four test streams in their reported order, then subtracts the two compounded totals. The bootstrap is a two-sided circular 10-session block test of pooled daily excess over zero, with 5,000 draws and seed 3666. DSR uses Bailey and Lopez de Prado independent-trial approximation at 88 trials; correlations among variants are not estimated.

| Idea | Sharpe > EW30 | Pooled excess | Mean daily excess | Bootstrap p | DSR (88 trials) | Test-average turnover | Mean active share | Criteria 1-5 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| ILLIQ (ILLIQ63_a08) | 1/4 | -10.70% | -0.0031% | 0.308 | 0.415 | 7.30% | 20.69% | 1 pass; 2 fail; 3 pass; 4 fail; 5 pass |
| SKEW (SKEW63_a08) | 3/4 | 14.04% | 0.0045% | 0.218 | 0.588 | 31.84% | 20.69% | 1 pass; 2 pass; 3 pass; 4 fail; 5 pass |
| DOWNBETA (DOWNBETA63_Q25_a08) | 2/4 | -12.46% | -0.0044% | 0.343 | 0.558 | 30.87% | 20.69% | 1 pass; 2 fail; 3 pass; 4 fail; 5 pass |

## Plain-English verdict and research feedback

- **ILLIQ63_a08:** Average turnover was only 7.3% per rebalance, but Sharpe beat EW30 in just one of four tests and pooled excess was -10.7% with p=0.308. Low modeled turnover did not rescue a weak payoff; the illiquidity premium may not transfer to large-cap Dow names or broad ETFs, and flat costs cannot validate the premium.

- **SKEW63_a08:** This is the most promising development result: Sharpe beat EW30 in three tests, pooled excess was +14.0%, and turnover averaged 31.8%. However, p=0.218 and DSR=0.588 do not support a reliable edge after the wider search. The signal measures univariate realized skew, not Harvey and Siddique conditional/systematic skewness; it is also related to cycle 1 MAX and is not independent evidence.

- **DOWNBETA63_Q25_a08:** Q25 was selected over NEG on selection Sharpe and passed the turnover screen. In tests it beat EW30 Sharpe in only two periods, pooled excess was -12.5%, and p=0.343. Low downside beta helped the 2026 Dow slice but lagged in the other Dow and cross-asset windows, consistent with losing upside participation and overlap with ordinary low-beta exposure.

## Validation and reproduction

The cycle 2 brief mixes rank instructions with the common weight formula: applying ordinary ascending ranks directly to raw skew or beta would give the lower score a lower weight. Before results, the preregistration resolved this by applying ascending ranks to negative skew and negative downside beta, so the explicitly stated low-skew/low-downside-beta portfolio directions receive more weight. Amihud illiquidity is ranked so higher illiquidity receives higher weight as the brief specifies. This sign choice is documented as a handoff ambiguity, not a post-test adjustment.

The cycle 2 harness imports the cycle 1 adjusted-OHLCV loader, engine copy, rank-weight utility, actual-cost solve, EW benchmark and bootstrap/DSR helpers. Future-truncation signal/weight checks passed: 18 comparisons for the earlier Dow roster, 12 for the recent Dow roster, and 18 for cross-assets. Each candidate was checked at every selection and frozen-test rebalance for complete lookback, positive dollar volume where needed, and downside sample count. The independent ledger reconciliation also passed on a representative selection run; the three generic-folder frozen functions matched the array harness terminal wealth exactly on the Dow selection sample.

EW30 from the cycle 1 harness matched the validated engine copy `run("ew")` on the selection window to substantially better than 0.01 percentage point: Dow 14.141439% vs 14.141439%, and cross-assets 0.785780% vs 0.785780% (527 marks in each comparison).

From the workspace root, reproduce the selection, freeze, and one-time test run with:

```powershell
py -3 A2\pivot_research\r3_impl\code\cycle2_harness.py
```

The harness writes `outputs_cycle2/metrics.csv`, `significance.json`, frozen-choice metadata, daily equity series and three PNG charts. The reusable generic-folder entry point is `run_frozen_cycle2_price_folder(price_folder, tickers_30, frozen_variant, period)` in `code/cycle2_harness.py`; `frozen_variant` is one of `ILLIQ63_a08`, `SKEW63_a08` or `DOWNBETA63_Q25_a08`. It accepts a flat directory or engine-style price root and fails on missing sessions or invalid volume. The caller supplies the 30-name roster; this worker did not access the sealed basket.

## Research references

Amihud, Y. (2002), "Illiquidity and stock returns: cross-section and time-series effects," *Journal of Financial Markets*, 5(1), 31-56, doi:10.1016/S1386-4181(01)00024-6. Harvey, C. R. and Siddique, A. (2000), "Conditional Skewness in Asset Pricing Tests," *The Journal of Finance*, 55(3), 1263-1295, doi:10.1111/0022-1082.00247. Ang, A., Chen, J. and Xing, Y. (2006), "Downside Risk," *The Review of Financial Studies*, 19(4), 1191-1239, doi:10.1093/rfs/hhj035.



