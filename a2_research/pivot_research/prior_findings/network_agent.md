# Network agent findings (round 1, transcribed by coordinator)

Harness swaps only the 50% heat term; keeps original fills, actual costs 0.05%/side, top-8 buffer.
Periods: IS 2020-11-27..2022-12 | OOS1 2023-01..2024-02-23 | OOS2 2024-12..2025-12 (recent roster).
Code: network_agent_code/network_research.py (arg `recent` or `earlier`), analyse.py, netres_*.json.

## Mean Spearman IC vs next-5-session return (IS / OOS1 / OOS2)
- Heat (tau 1): -0.030 (t -0.92) / +0.041 (t +0.99) / +0.020 (t +0.48); 2022 -0.053, 2023 +0.055 -> sign flip
- Nbr-avg ~ heat; tau 0.5/2 ~ tau 1
- Pressure: -0.001 / +0.023 / +0.039, all |t|<1.3
- Heat on 5-day returns: -0.072 (t -2.34) IS, ~0 OOS

## Excess annualised return vs EW30 (IS / OOS1 / OOS2)
| Variant | IS | OOS1 | OOS2 |
|---|---|---|---|
| Current heat tau 1 | -0.6% | +3.8% | -7.8% (p .73) |
| tau 0.5 | +3.3% | +11.8% | -8.2% |
| Nbr-avg | -4.6% | +9.8% | -11.8% |
| Lead-lag graph, leaders' pressure | +3.1% | +6.3% | +15.0% (p .09) |
| Residual reversal (peer ret minus own) | +3.5% | +1.6% | +12.1% (p .10) |

Lead-lag and residual reversal are positive in all three periods but OOS2 IC negative -> fragile. 11 variants; Bonferroni p<0.0045; nothing close.

## Proposed validation design
Pre-registered rule: best IS excess Sharpe vs EW30, freeze, report OOS1/OOS2 once. Daily excess t-stat + circular block bootstrap (10-day blocks, 5000 draws). Disclose trial count; Harvey-Liu-Zhu 2016; deflated Sharpe (Bailey & Lopez de Prado 2014).

## Known conflict with signal agent
Signal agent's "neighbour lead-lag" (-16.5/-6.3/-3.8pp) and "5-day residual reversal" (+0.2/-16.4/+13.5pp) disagree with the above. Different constructions (this agent keeps 50% pressure; different graph) and different simplified engines. Must be reconciled in the official engine.
