# R3 implementer results - cycle 1

## Outcome

None of the three directions meets the development goal. MAX21, HIGH63 and IDIO63 all differ from EW30 by the active-share rule and keep pooled average turnover under 50%, but none has positive pooled excess return after costs. Sharpe exceeds EW30 in only 1/4, 1/4 and 2/4 test periods, respectively; the HIGH63 pooled two-sided bootstrap result is p=0.096, but its measured excess is negative. No sealed holdout was accessed or evaluated.

## Selection results and frozen choices

Selection used only 2020-11-27 through 2022-12-30. For each family I excluded any variant whose average actual notional turnover exceeded 50% in either universe, then selected the remaining variant with the highest average net Sharpe across Dow and cross-asset. Average turnover and Sharpe below are selection-window values. The 126-session candidates were attempted and failed the full-lookback check on the first scheduled selection signal (2020-11-25) in both supplied universes; no shortened windows were substituted.

| Variant | Dow Sharpe | Dow turnover | Cross-asset Sharpe | Cross-asset turnover | Mean Sharpe | Decision |
|---|---:|---:|---:|---:|---:|---|
| MAX21_a08 | 0.60 | 43.6% | -0.37 | 20.1% | 0.11 | Frozen MAX21 |
| MAX21_a10 | 0.63 | 54.1% | -0.53 | 24.8% | 0.05 | Excluded: Dow turnover >50% |
| HIGH63_a08 | 0.52 | 33.1% | -0.11 | 29.7% | 0.21 | Frozen HIGH |
| HIGH126_a08 | n/a | n/a | n/a | n/a | n/a | Failed: full 126-session history unavailable in both selection windows |
| IDIO63_a08 | 0.55 | 17.1% | -0.33 | 7.2% | 0.11 | Frozen IDIO |
| IDIO126_a08 | n/a | n/a | n/a | n/a | n/a | Failed: full 126-session history unavailable in both selection windows |

Frozen choices: **MAX21_a08**, **HIGH63_a08**, and **IDIO63_a08**. The historical trial count is approximately 76; adding six unique active parameterizations gives **82** for the deflated-Sharpe calculation. This count is approximate and the variants are correlated.

## Frozen test-period results

Net returns and costs use actual next-open trades at 5 bp per side. EW30 is run on the same schedule, with the same fill and cost rules. The reported turnover is average traded notional divided by pre-trade NAV at scheduled rebalances; initial buys are charged but omitted from the rebalance average.

| Idea / frozen variant | Period | Net return | EW30 return | Excess | Sharpe / EW30 Sharpe | Max DD | TE vs EW30 | IR | Turnover |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MAX21_a08 | DOW_OOS1 | 14.5% | 16.8% | -2.2% | 1.26 / 1.38 | -8.6% | 2.5% | -0.75 | 44.6% |
| MAX21_a08 | DOW_OOS2 | 14.2% | 16.3% | -2.0% | 0.94 / 1.02 | -14.5% | 2.7% | -0.69 | 49.0% |
| MAX21_a08 | DOW_OOS3 | 11.0% | 11.3% | -0.4% | 1.20 / 1.24 | -7.9% | 2.8% | -0.15 | 51.0% |
| MAX21_a08 | XASSET_OOS | 23.6% | 29.3% | -5.7% | 0.98 / 0.89 | -5.6% | 3.1% | -0.44 | 21.2% |
| HIGH63_a08 | DOW_OOS1 | 15.5% | 16.8% | -1.2% | 1.33 / 1.38 | -8.4% | 2.5% | -0.42 | 34.1% |
| HIGH63_a08 | DOW_OOS2 | 10.1% | 16.3% | -6.2% | 0.74 / 1.02 | -16.8% | 4.2% | -1.37 | 36.8% |
| HIGH63_a08 | DOW_OOS3 | 12.1% | 11.3% | 0.7% | 1.33 / 1.24 | -7.3% | 3.5% | 0.22 | 35.0% |
| HIGH63_a08 | XASSET_OOS | 22.4% | 29.3% | -6.9% | 0.86 / 0.89 | -6.8% | 2.9% | -0.55 | 29.5% |
| IDIO63_a08 | DOW_OOS1 | 15.6% | 16.8% | -1.1% | 1.37 / 1.38 | -8.3% | 2.3% | -0.44 | 17.7% |
| IDIO63_a08 | DOW_OOS2 | 17.7% | 16.3% | 1.4% | 1.12 / 1.02 | -14.3% | 2.7% | 0.44 | 18.9% |
| IDIO63_a08 | DOW_OOS3 | 11.3% | 11.3% | -0.0% | 1.20 / 1.24 | -8.4% | 4.0% | 0.01 | 16.3% |
| IDIO63_a08 | XASSET_OOS | 24.0% | 29.3% | -5.3% | 0.99 / 0.89 | -5.9% | 3.1% | -0.41 | 6.6% |

Pooled significance concatenates the four test-period daily strategy-minus-EW30 returns, uses circular 10-session blocks and 5,000 draws (seed 3666), and reports the two-sided zero-mean p-value. The pooled excess column in the next table is the compounded strategy return minus compounded EW30 return across the concatenated test streams. DSR uses Bailey and Lopez de Prado independent-trial approximation with 82 trials; dependence among candidates is not estimated.

| Idea | Sharpe > EW30 | Pooled excess | Pooled mean daily excess | Bootstrap p | DSR (82 trials) | Test-average turnover | Mean active share | Criteria 1-5 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| MAX21 (MAX21_a08) | 1/4 | -16.1% | -0.0056% | 0.200 | 0.523 | 41.5% | 20.7% | 1 pass; 2 fail; 3 pass; 4 fail: no positive excess finding; 5 pass |
| HIGH (HIGH63_a08) | 1/4 | -21.1% | -0.0073% | 0.096 | 0.479 | 33.9% | 20.7% | 1 pass; 2 fail; 3 pass; 4 fail: no positive excess finding; 5 pass |
| IDIO (IDIO63_a08) | 2/4 | -7.6% | -0.0028% | 0.528 | 0.588 | 14.9% | 20.7% | 1 pass; 2 fail; 3 pass; 4 fail: no positive excess finding; 5 pass |

### Plain-English verdicts and feedback for research

- **MAX21:** The 0.8 tilt beat EW30 on Sharpe only in the cross-asset test, but its excess return was negative in the other periods and it missed the three-of-four threshold. Its average turnover was acceptable overall (about 41%), although the 2026 Dow test was 51.0%. The selection-period Dow gain did not carry through; the MAX statistic may be too noisy over 21 sessions or the effect may not transfer to a diversified ETF basket.

- **HIGH63:** Sharpe beat EW30 only in the 2026 Dow slice. It had the lowest two-sided pooled p-value, 0.096, while pooled excess was -21.1%; this is evidence in the wrong direction for the proposed trade. The 52-week-high effect did not translate into a stable monthly cross-sectional tilt here.

- **IDIO63:** It had the lowest turnover (about 14.7%) and passed the active-share distinction, but Sharpe beat EW30 in only two periods and pooled excess remained negative. A simple equal-weight market proxy and short residual-volatility window did not produce a consistent reward for low residual volatility.

## Validation, implementation and limitations

The local copy `code/validated_engine_copy.py` supplies the validated adjusted OHLCV loader and cost self-test. The harness preserves the 2020 Dow roster for selection/OOS1, switches to the 2024 Dow roster for later periods, and uses the fixed 30-ETF cross-asset roster. It charges initial buy cost, solves actual traded-notional cost at each rebalance, checks the cost budget, applies the 1% total-weight-change no-trade band, and uses the next open after the signal close. All six signal/weight definitions were compared before and after removing future observations on sampled dates with at least their lookback history; these checks passed (12 Dow and 18 cross-asset comparisons).

The harness exposes `run_frozen_price_folder(price_folder, tickers, family, period, ...)` in `code/research_harness.py` for a caller-supplied 30-name adjusted OHLCV directory. The coordinator can pass the sealed basket and its price folder to this function for the one authorized holdout run; this worker did not load, download, or test that basket.

The pooled tests are exploratory, and the data-driven selection across the two universes remains exposed to selection bias. The 2026 Dow turnover of MAX21 slightly exceeds 50% in that individual period, although the four-period average is below the specified cap. Return comparisons with EW30 are the relevant criteria; no conclusion about sealed-holdout performance follows.

## Reproduction

From the workspace root, the full selection and frozen test pass is:

```powershell
py -3 A2\pivot_research\r3_impl\code\research_harness.py
```

The run writes selection/test daily wealth CSVs, `metrics.csv`, `significance.json`, frozen-choice metadata, and the three PNG charts under `outputs_cycle1`. The frozen choices and preregistration are in `outputs_cycle1/frozen_choices.txt` and `PREREG_cycle1.md`.

### Variant-specific function calls

```python
import sys
 sys.path.insert(0, r"A2\pivot_research\r3_impl\code")
 from research_harness import run_frozen_price_folder
run_frozen_price_folder(price_folder, tickers_30, "MAX21", period)
run_frozen_price_folder(price_folder, tickers_30, "HIGH", period)
run_frozen_price_folder(price_folder, tickers_30, "IDIO", period)
```



## Literature cited

The candidate hypotheses came from real studies, but their published stock results do not establish a premium in these ETF portfolios: Bali, Cakici and Whitelaw (2011), *Maxing out: Stocks as lotteries and the cross-section of expected returns*, doi:10.1016/j.jfineco.2010.08.014; George and Hwang (2004), *The 52-Week High and Momentum Investing*, doi:10.1111/j.1540-6261.2004.00695.x; Ang, Hodrick, Xing and Zhang (2006), *The Cross-Section of Volatility and Expected Returns*, doi:10.1111/j.1540-6261.2006.00836.x.

