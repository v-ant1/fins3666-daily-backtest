# Round 3 outcome (2026-11-10)

Stop rule reached: 4 research-and-test cycles completed. 1 direction passes all six criteria; the target was 2-3.

## Passing direction: IDIOSKEW63_a08 (idiosyncratic-skewness avoidance tilt)
Hold all 30 assets. Every 21 sessions, rank assets by the skewness of their 63-day returns after removing the market move (idiosyncratic skewness). Tilt toward low-skew (non-"lottery") assets: w = (1/30)(1 + 0.8(2r - 1)). Next-open fills, 0.05%/side actual-trade costs, no-trade band of 1% total weight change.
Code: r3_impl/code/cycle3_harness.py (run_idioskew63_a08). Literature: Boyer, Mitton and Vorkink (2010); Bali, Cakici and Whitelaw (2011); see r3_research/IDEAS_cycle3.md.

| Criterion | Result |
|---|---|
| 1 Selection-only choice | PASS (r3_impl/PREREG_cycle3.md) |
| 2 Sharpe > EW in >=3/4 tests, pooled excess > 0 | PASS: 3/4 (lost Dow 2023-24: 1.32 vs 1.38); pooled +24.0% |
| 3 TE >=3% or active share >=20% | PASS on active share (20.69%), but this is mechanical for any a=0.8 tilt; TE is only 1.8-3.4% |
| 4 Pooled block p < 0.10, DSR reported | PASS: p = 0.019; DSR 0.658 at 94 trials |
| 5 Turnover <= 50% | PASS: 27-34% per rebalance |
| 6 Sealed holdout (30 country ETFs, 2020-11-27..2026-10-30, run once) | PASS (directional): +84.4% vs EW30 +73.7%; Sharpe 0.73 vs 0.67; max DD -26.1% vs -26.0%; TE 1.5%. Not significant within holdout sub-periods (block p 0.96 / 0.064 / 0.52). |

Holdout files: sealed_holdout/result/ (equity CSV, evaluation report, charts). Script: sealed_holdout/run_holdout.py. EW30 uses the same engine with tilt a=0.

## Failed directions in round 3 (all disclosed)
Inverse heat optimisation (low15_inv); MAX avoidance; 52-week-high proximity; idiosyncratic-vol avoidance; Amihud illiquidity; total skewness (SKEW63, p=0.22); downside beta; co-skewness (not selected); distribution-income proxy; overnight-gap share; high-volume event returns; weekday seasonality; month-phase returns.

## Trial count
About 100 variants across the whole project (round 1 ~44, round 2 ~29, round 3 ~27; r3_impl/TRIALS.md logs about 98).

## Honest reading
One low-turnover tilt (avoid assets with lottery-like idiosyncratic skew) held up out of sample on two universes and on a sealed third universe. Its edge is small (tracking error ~2%), and it is only significant on the pooled development tests, not within the holdout. Present it as a modest, plausible refinement, not a strong alpha source.
