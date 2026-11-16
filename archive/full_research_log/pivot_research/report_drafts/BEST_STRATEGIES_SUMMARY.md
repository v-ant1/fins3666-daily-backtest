# Best strategy attempts: summary of results

Status: research stopped 13 Nov 2026. No strategy passed every test. This document lists the best attempts, what each strategy does, and how it performed.

All numbers are after trading costs. Development data is 27 Nov 2020 to 30 Oct 2026. "Excess" means return above the benchmark.

---

## 1. J2: weekly reversal within industries, smoothed (the only strategy tested on a holdout)

**Strategy**
- Universe: Dow 30 stocks, using the index members on each date.
- Each week, compute each stock's 5-day return minus the average 5-day return of the other S&P 500 stocks in its industry (2-digit SIC code).
- Average that score over the last 4 weeks.
- Buy the 5 stocks with the lowest score (the biggest losers relative to their industry), equal-weighted.
- Trade at the next day's open. Cost: 0.05% per dollar traded.
- Benchmark: equal-weighted Dow 30.

**Theory:** stocks pushed down by temporary selling that is unrelated to the company tend to bounce back. Comparing each stock with its own industry removes industry-wide news, which does not reverse.

**How it was chosen:** J1 (below) had a real signal but high costs. Twelve ways of turning J1 into a portfolio were written down before any were run. A selection rule fixed in advance picked the 4-week smoothing version (V5).

**Development results (2021-03 to 2026-10)**

| Measure | J2 | Benchmark |
|---|---:|---:|
| Net excess return | +40.1% | — |
| Net Sharpe ratio | 0.92 | 0.88 |
| Average turnover per rebalance | 69.7% | — |
| Costs as a share of gross edge | 22.5% | — |
| Bootstrap p-value | 0.19 | — |

**Holdout results (Jan 2016 to Oct 2020, run once, with approval)**

| Measure | J2 | Benchmark | Required to pass |
|---|---:|---:|---|
| Total net return | +72.5% | +77.8% | Above benchmark |
| Net Sharpe ratio | 0.61 | 0.73 | Above benchmark |
| Bootstrap p-value | 0.478 | — | Below 0.05 |
| Deflated Sharpe ratio | 0.84 | — | Above 0.95 |

**Verdict: FAIL** on all four checks. An audit confirmed the run was clean, so the result stands.

---

## 2. J1: weekly reversal within industries (the parent of J2)

**Strategy:** the same signal as J2, using only the latest week with no 4-week smoothing. Hold the 5 lowest-scoring Dow stocks and rebalance weekly.

**Results (development)**

| Measure | Result |
|---|---:|
| Signal predictive power (average rank correlation) | 0.0148, t = 2.08 (passed) |
| Placebo test p-value | 0.002 (passed) |
| Net excess return | +5.15% |
| Net Sharpe ratio | 0.84 (benchmark 0.88) |
| Costs as a share of gross edge | 53% |

**Verdict:** the signal predicted returns, but trading costs ate the profit. J2 was the attempt to fix this.

---

## 3. Industry momentum (S3-01): best average return in the R10 screens

**Strategy**
- Universe: S&P 500, using the index members on each date.
- Each month, group stocks by industry (2-digit SIC code) and rank industries by their 12-month return, skipping the latest month.
- Buy all stocks in the top fifth of industries, equal-weighted, and hold for one month.
- Cost: 0.10% per trade. Benchmark: equal-weighted S&P 500.

**Theory:** buying pressure spreads across related stocks, so money flowing into a sector keeps lifting the group.

**Results (58 months)**

| Measure | Result |
|---|---:|
| Net excess return | +0.41% per month (about 5% a year) |
| t-statistic (Newey-West) | 1.22 (needed 2.0) |
| Net Sharpe of excess return | 0.53 |
| Average turnover | 35% per month |
| Costs as a share of gross edge | 7.9% |
| Years positive | 5 of 6 |
| Estimated chance of passing a 2010–2015 test | 14% |

**Verdict: NO-GO.** Positive and cheap to trade, but too noisy to tell apart from luck.

---

## 4. Residual momentum (S4-06): most consistent in the R10 screens

**Strategy**
- Universe: S&P 500, using the index members on each date.
- Each month, measure each stock's past-year return after removing the part explained by the overall market.
- Buy the top fifth, equal-weighted, and hold for one month.
- Cost: 0.10% per trade. Benchmark: equal-weighted S&P 500.

**Theory:** this isolates buying pressure that is specific to the stock and keeps going, separate from market moves.

**Results (58 months)**

| Measure | Result |
|---|---:|
| Net excess return | +0.34% per month (about 4% a year) |
| t-statistic (Newey-West) | 1.49 (needed 2.0) |
| Net excess at 0.05% / 0.10% / 0.20% cost | +0.36% / +0.34% / +0.29% per month |
| Years positive | 5 of 6 |
| Estimated chance of passing a 2010–2015 test | 15% |

**Verdict: NO-GO.** It overlaps heavily with industry momentum, so the two are not independent.

---

## 5. S&P 500 index additions

**Strategy:** buy stocks newly added to the S&P 500, which index funds are forced to buy. Hold over the inclusion window.

**Results**
- Early test (L-ADDS): +1.09% net per event, below the 2.35% the sample could reliably detect.
- Final pooled test (L-IDX5C): −0.63% net per event.

**Verdict: NO-GO.** The effect has largely been traded away since it became well known.

---

## Overall

- No strategy met every requirement: frozen in advance, beating the benchmark after costs, significant after counting every trial, and confirmed on a holdout.
- Number of trials counted across all rounds: about 75. The more trials, the stronger a result has to be to count as significant.
- **Best real evidence:** J1's signal predicts returns, but the profit does not survive costs, and J2 failed its holdout.
- **Best untested leads:** industry momentum and residual momentum. Each has about a 15% chance of passing, and there is no clean 2010–2015 test set to confirm them on.
- **Hourly (intraday) work, R11:** stopped before any testing.
  - Published research suggests hourly effects are about 1.5–2 bp per trade after allowing for the winner's curse, well below trading costs.
  - The 1-hour bar download was stopped partway. The sealed 2016–2020 file is complete; the 2020–2026 file is partial.

Source files: `r9/HOLDOUT_RESULT.json`, `r9/R9_VARIANTS.md`, `r6_J1/RESULTS.md`, `r10/S3/SCREEN.md`, `r10/S4/SCREEN.md`, `specs/r9_prereg/J2.md`, `r11/ideas/H1_IDEAS.md`.
