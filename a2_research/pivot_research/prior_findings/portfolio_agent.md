# Portfolio construction / turnover / risk pivots — findings

Harness: `code/construct.py` (imports the original signal code unchanged; generic weight simulator with next-open fills, 0.05%/side cost on actual notional traded incl. drift, final liquidation cost). It reproduces the current strategy (recent window 2.5%, same 142% traded/rebalance). EW30 is rebalanced every 5 sessions as in the original script. Sharpe at 0 rf; IR = annualised mean active daily return / tracking error vs EW30. Signal = existing 50% pressure + 50% heat blend unless marked PRESSURE-only.

**Variants tried: 14 (+ EW benchmark), all shown below — no hidden runs.** Selection rule fixed in advance: choose on IS (2020-11..2022-12) only; 2023-01..2024-02 and Dec24..Dec25 are OOS.


### IS 2020-11..2022-12
| variant | ret | ann | vol | Sharpe | excess vs EW | TE | IR | maxDD | traded/reb | ann. cost drag |
|---|---|---|---|---|---|---|---|---|---|---|
| EW30 (benchmark) | 14.7% | 6.8% | 16.2% | 0.48 | +0.0pp | 0.0% | nan | -21.4% | 2% | 0.07% |
| Top5 buf8 reb5 (current) | 11.6% | 5.4% | 20.1% | 0.36 | -3.1pp | 12.2% | -0.05 | -29.4% | 142% | 3.59% |
| Top5 buf8 reb10 | 14.0% | 6.5% | 20.0% | 0.41 | -0.7pp | 11.8% | 0.03 | -29.9% | 147% | 1.85% |
| Top5 buf8 reb21 | -14.2% | -7.0% | 22.2% | -0.22 | -28.9pp | 12.8% | -1.00 | -37.0% | 148% | 0.89% |
| Top10 buf15 reb5 | 2.0% | 0.9% | 18.1% | 0.14 | -12.7pp | 9.0% | -0.59 | -31.0% | 99% | 2.49% |
| Top15 buf20 reb5 | 8.4% | 3.9% | 16.9% | 0.31 | -6.3pp | 6.3% | -0.41 | -24.9% | 65% | 1.64% |
| Top10 buf15 reb21 | -8.1% | -4.0% | 19.0% | -0.12 | -22.8pp | 8.2% | -1.23 | -29.6% | 105% | 0.63% |
| Tilt a=0.5 reb5 | 9.6% | 4.5% | 16.2% | 0.35 | -5.1pp | 2.2% | -1.00 | -23.1% | 33% | 0.85% |
| Tilt a=1.0 reb5 | 4.4% | 2.1% | 16.5% | 0.21 | -10.3pp | 4.4% | -1.02 | -25.2% | 67% | 1.70% |
| Tilt a=1.0 reb21 | 1.3% | 0.6% | 16.9% | 0.12 | -13.4pp | 4.0% | -1.45 | -25.1% | 69% | 0.42% |
| Top10 inv-vol reb5 | 2.6% | 1.2% | 17.5% | 0.16 | -12.1pp | 8.7% | -0.59 | -29.1% | 103% | 2.59% |
| Top5 vol-target->EW reb5 | 14.5% | 6.7% | 15.0% | 0.51 | -0.2pp | 9.7% | -0.03 | -20.0% | 114% | 2.87% |
| EW + 20% L/S overlay reb5 | 6.4% | 3.0% | 16.5% | 0.26 | -8.3pp | 4.4% | -0.80 | -24.5% | 65% | 1.65% |
| EW + 20% L/S overlay reb21 | 5.3% | 2.5% | 16.8% | 0.23 | -9.4pp | 4.1% | -0.97 | -23.6% | 70% | 0.43% |
| Tilt a=1.0 reb5 PRESSURE-only | 6.8% | 3.2% | 16.2% | 0.27 | -7.9pp | 3.5% | -0.97 | -23.7% | 67% | 1.69% |

### OOS 2023-01..2024-02
| variant | ret | ann | vol | Sharpe | excess vs EW | TE | IR | maxDD | traded/reb | ann. cost drag |
|---|---|---|---|---|---|---|---|---|---|---|
| EW30 (benchmark) | 20.6% | 17.9% | 11.3% | 1.51 | +0.0pp | 0.0% | nan | -8.9% | 2% | 0.07% |
| Top5 buf8 reb5 (current) | 25.3% | 21.9% | 15.0% | 1.39 | +4.7pp | 9.8% | 0.39 | -15.7% | 142% | 3.59% |
| Top5 buf8 reb10 | 18.4% | 16.0% | 16.3% | 1.00 | -2.2pp | 10.4% | -0.09 | -14.1% | 147% | 1.85% |
| Top5 buf8 reb21 | 4.8% | 4.2% | 15.2% | 0.35 | -15.8pp | 10.0% | -1.18 | -16.5% | 148% | 0.89% |
| Top10 buf15 reb5 | 22.4% | 19.4% | 12.9% | 1.44 | +1.8pp | 6.5% | 0.23 | -9.3% | 99% | 2.49% |
| Top15 buf20 reb5 | 21.3% | 18.5% | 11.9% | 1.49 | +0.7pp | 5.0% | 0.11 | -8.8% | 65% | 1.64% |
| Top10 buf15 reb21 | 14.0% | 12.2% | 13.5% | 0.92 | -6.6pp | 6.8% | -0.68 | -13.7% | 105% | 0.63% |
| Tilt a=0.5 reb5 | 22.9% | 19.9% | 11.2% | 1.67 | +2.3pp | 1.6% | 1.07 | -8.1% | 33% | 0.85% |
| Tilt a=1.0 reb5 | 25.2% | 21.8% | 11.4% | 1.79 | +4.5pp | 3.1% | 1.05 | -7.5% | 67% | 1.70% |
| Tilt a=1.0 reb21 | 14.7% | 12.8% | 11.8% | 1.08 | -5.9pp | 3.4% | -1.30 | -11.6% | 69% | 0.42% |
| Top10 inv-vol reb5 | 20.4% | 17.7% | 12.3% | 1.39 | -0.2pp | 6.3% | -0.01 | -9.8% | 103% | 2.59% |
| Top5 vol-target->EW reb5 | 19.7% | 17.1% | 10.9% | 1.50 | -0.9pp | 7.6% | -0.09 | -10.8% | 114% | 2.87% |
| EW + 20% L/S overlay reb5 | 26.1% | 22.6% | 11.5% | 1.83 | +5.5pp | 3.3% | 1.18 | -7.7% | 65% | 1.65% |
| EW + 20% L/S overlay reb21 | 11.5% | 10.1% | 11.4% | 0.90 | -9.1pp | 3.4% | -2.03 | -11.9% | 70% | 0.43% |
| Tilt a=1.0 reb5 PRESSURE-only | 22.1% | 19.2% | 11.4% | 1.59 | +1.5pp | 2.7% | 0.40 | -8.3% | 67% | 1.69% |

### OOS Dec24..Dec25
| variant | ret | ann | vol | Sharpe | excess vs EW | TE | IR | maxDD | traded/reb | ann. cost drag |
|---|---|---|---|---|---|---|---|---|---|---|
| EW30 (benchmark) | 12.0% | 11.3% | 15.9% | 0.75 | +0.0pp | 0.0% | nan | -15.3% | 3% | 0.11% |
| Top5 buf8 reb5 (current) | 2.5% | 2.3% | 19.1% | 0.22 | -9.5pp | 12.4% | -0.63 | -15.5% | 142% | 3.60% |
| Top5 buf8 reb10 | -4.3% | -4.1% | 19.5% | -0.11 | -16.3pp | 11.9% | -1.20 | -16.5% | 160% | 2.01% |
| Top5 buf8 reb21 | 41.8% | 39.1% | 19.0% | 1.83 | +29.9pp | 13.6% | 1.69 | -14.4% | 151% | 0.90% |
| Top10 buf15 reb5 | 25.9% | 24.3% | 18.4% | 1.27 | +14.0pp | 9.2% | 1.26 | -12.9% | 93% | 2.38% |
| Top15 buf20 reb5 | 19.8% | 18.6% | 18.0% | 1.04 | +7.9pp | 6.5% | 1.04 | -12.6% | 65% | 1.67% |
| Top10 buf15 reb21 | 24.7% | 23.2% | 17.3% | 1.29 | +12.8pp | 9.2% | 1.13 | -17.0% | 106% | 0.65% |
| Tilt a=0.5 reb5 | 14.1% | 13.2% | 16.2% | 0.85 | +2.1pp | 2.1% | 0.85 | -14.4% | 32% | 0.85% |
| Tilt a=1.0 reb5 | 16.1% | 15.1% | 16.7% | 0.92 | +4.1pp | 4.3% | 0.83 | -13.6% | 65% | 1.67% |
| Tilt a=1.0 reb21 | 18.4% | 17.2% | 15.3% | 1.12 | +6.4pp | 4.7% | 1.10 | -15.9% | 72% | 0.45% |
| Top10 inv-vol reb5 | 26.7% | 25.0% | 17.9% | 1.34 | +14.7pp | 8.8% | 1.36 | -12.7% | 96% | 2.45% |
| Top5 vol-target->EW reb5 | 2.8% | 2.6% | 13.8% | 0.26 | -9.2pp | 10.0% | -0.84 | -11.6% | 101% | 2.54% |
| EW + 20% L/S overlay reb5 | 12.5% | 11.8% | 16.4% | 0.76 | +0.6pp | 4.1% | 0.14 | -14.6% | 67% | 1.71% |
| EW + 20% L/S overlay reb21 | 19.7% | 18.5% | 15.3% | 1.18 | +7.7pp | 4.3% | 1.44 | -15.2% | 69% | 0.44% |
| Tilt a=1.0 reb5 PRESSURE-only | 15.2% | 14.3% | 15.7% | 0.93 | +3.2pp | 3.4% | 0.79 | -13.2% | 67% | 1.71% |

## What the table says

1. **Nothing beats EW30 in-sample.** Every one of 14 variants has negative excess return vs EW over 2020-11..2022-12. Best IS: vol-targeted top-5 (-0.2pp, Sharpe 0.51 vs 0.48) and top-5 rebalanced every 10 (-0.7pp). Following the pre-committed rule, those would be picked — and both lose to EW in BOTH OOS windows (vol-target -0.9pp / -9.2pp; reb10 -2.2pp / -16.3pp). Construction cannot manufacture an edge the signal does not have (Grinold & Kahn: IR ≈ IC × √breadth, net of costs).
2. **Window-specific wins — do not report as findings:** Top-5 reb21 is +29.9pp in Dec24–Dec25 but -28.9pp IS and -15.8pp in 2023; Top-10 variants +13–15pp in 2025 but -12pp IS. The sign flips across windows → noise/luck of a concentrated 5–10 name book (TE 9–13%).
3. **Turnover is a real, mechanical drag.** The current book pays ~3.6%/yr in costs (142% traded per weekly rebalance). Tilts at a=0.5 cut that to ~0.85%/yr; reb21 cuts any scheme to ~0.4–0.9%/yr (Novy-Marx & Velikov 2016). But slowing a 5-day signal also decays it (reb21 hurts IS and 2023), so lower cost ≠ higher net return here.
4. **Tilting/overlays bound the damage.** EW ± rank tilt keeps TE at 2–4% and Sharpe/maxDD close to EW in every window; the dollar-neutral 20% L/S overlay behaves similarly. They do not reliably add value (IS IR ≈ -0.8 to -1.0; OOS IR +0.1 to +1.2), consistent with a near-zero-IC signal. DeMiguel et al. (2009): 1/N is hard to beat out-of-sample, and that is what we see.
5. **Vol management (Moreira & Muir 2017)** lowered vol/maxDD (IS maxDD -20% vs -29%) but not returns relative to EW; inverse-vol weighting did not help IS.

## Recommendations
1. **Adopt an EW ± rank tilt (a = 0.5, weekly; weights 1/60..3/60, long-only)** as the construction, framed as "controlled active risk": TE ~2%, cost drag ~0.85%/yr (vs 3.6%), vol/maxDD ≈ EW. Results: IS -5.1pp (IR -1.0), OOS 2023 +2.3pp (IR 1.07), OOS 2025 +2.1pp (IR 0.85). Honest summary: it roughly tracks EW and does not demonstrably beat it; it is chosen because it limits downside from a weak signal, not because it won IS.
2. **Pair it with whatever signal change the other agent finds**, and re-run this harness — the tilt is where a modest-IC signal can show up without being eaten by 140%/week turnover. If the new signal beats EW only when concentrated in 5 names, treat that as suspect.

## Caveats
- Short samples (~2.1y IS, ~1.1y and ~1.1y OOS); IR standard errors are ~1/√years ≈ 0.7–1.0, so none of these IRs is statistically distinguishable from zero.
- 14 variants tried; the best OOS number among them is selection-biased.
- Shorting cost/borrow ignored for the L/S overlay; cash earns 0 in vol-target; costs are flat 5bp/side (no impact).
- Dow 30 roster changes handled only via the two fixed rosters of the original script.
