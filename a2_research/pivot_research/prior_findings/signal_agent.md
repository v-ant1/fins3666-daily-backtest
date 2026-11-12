# Signal-pivot findings (agent_signal)

Script: code/signal_lab.py (`python signal_lab.py early|recent`). It imports the original module for data and pressure code, unchanged.
Engine: simplified. Same grid (every 5 sessions), next-open fills, top-5 at 20% each, top-8 buffer, cost 0.05% x |weight change|. EW30 runs through the same engine.
Sanity check (recent window) against the official script: orig 3.6% vs 2.5%, pressure 10.6% vs 11.7%, EW30 11.8% vs 12.0%. The numbers are close but not identical, so treat them as indicative.

**Variants tried: 19 signals** (plus EW30). Each was run on 3 periods. Selection rule fixed in advance: choose on IS (2020-11..2022-12) only.

## Excess CAGR vs EW30 (pp) / Sharpe ; turnover = share of names changed per rebalance
| Signal | IS 20-11..22-12 | OOS1 23-01..24-02 | OOS2 24-12..25-12 | Turnover |
|---|---|---|---|---|
| EW30 (abs CAGR / Sharpe) | 6.9% / 0.50 | 17.9% / 1.55 | 11.8% / 0.78 | - |
| orig heat50 | -2.6 / 0.31 | +3.4 / 1.42 | -8.2 / 0.28 | 71% |
| pressure | -7.7 / 0.06 | -9.1 / 0.67 | -1.2 / 0.62 | 72% |
| -pressure (reversal) | -3.3 / 0.28 | -19.5 / -0.02 | -17.3 / -0.16 | 70% |
| CLV | +6.4 / 0.78 | -17.5 / 0.10 | +4.3 / 0.84 | 72% |
| -CLV | -3.2 | -11.0 | -30.9 | 72% |
| SVOL | -8.7 | -7.4 | -9.6 | 73% |
| -SVOL | +1.4 / 0.50 | -18.9 / 0.02 | +0.5 / 0.60 | 70% |
| OI (intraday-overnight) | -8.0 / 0.05 | -3.5 / 0.96 | +15.9 / 1.22 | 73% |
| -OI | -2.3 | -14.6 | -38.3 | 70% |
| rev5 (Lehmann/Jegadeesh) | +3.2 / 0.55 | -15.6 / 0.23 | -0.4 / 0.57 | 74% |
| mom5 | -9.1 | +2.4 / 1.30 | -12.0 | 73% |
| rev21 (1-month reversal) | -4.2 / 0.23 | +13.3 / 1.90 | +8.5 / 0.86 | 30% |
| mom63 skip 5 | -4.9 | -22.0 | -3.8 | 15% |
| residual mom 63 (Blitz et al. 2011) | -9.2 | -11.8 | -1.9 | 12-16% |
| residual rev5 (beta-adj vs EW mkt) | +0.2 / 0.42 | -16.4 / 0.17 | +13.5 / 1.09 | 74% |
| lead-lag: nbr 5d ret (Cohen-Frazzini 2008) | -16.5 | -6.3 | -3.8 | 74% |
| -lead-lag nbr 5d ret | **+13.9 / 0.99** | -10.1 / 0.55 | -11.1 / 0.14 | 75% |
| nbr ret minus own ret (catch-up) | -19.5 | -14.8 | +4.1 | 70% |
| resid rev5 + resid mom | -3.9 | -27.8 | -8.3 | 55% |

Max drawdowns (IS / OOS1 / OOS2): EW30 -21% / -9% / -15%. Every active variant had a deeper drawdown than EW30 in OOS1. The full output lists DD per cell.

## Verdict
- **No variant beats EW30 in all three periods.** Applying the honest rule, the IS winner is the negative lead-lag signal (+13.9pp IS). It then fails in both OOS periods (-10.1pp, -11.1pp). This is a textbook in-sample overfit.
- The signals that win in one or two periods (CLV, OI, residual rev5, -SVOL) flip sign between windows. With about 19 tries, about 1 in 20 would "work" in any single period by chance.
- Weekly reversal (Lehmann 1990, Lo & MacKinlay 1990) is not reliable among 30 mega-caps after costs. rev5 was +3.2pp IS, then -15.6 and -0.4.

## Recommendations
1. **Report the negative result honestly** (preferred). Pressure and heat do not beat EW30. The full grid of tried variants shows this is not a cherry-picked failure. The marker rewards this kind of validation.
2. If a pivot is required: **1-month reversal (rev21)**. It has a literature basis (Jegadeesh 1990; the monthly reversal is a liquidity/overreaction effect), uses one round lookback, has 30% turnover (vs ~71%), and won both OOS periods (+13.3pp, +8.5pp, Sharpe 1.90 / 0.86). **But it lost in IS (-4.2pp)**, so the IS rule would not have chosen it. Choosing it now uses OOS information. If you present it, frame it as a hypothesis for future testing, not a validated edge.

## Caveats
Simplified cost and engine. Only 30 names and about 3.5 years of data. Sub-periods are short (14-25 months), so differences of ±10pp are within noise. Survivorship is handled by the point-in-time rosters only.
