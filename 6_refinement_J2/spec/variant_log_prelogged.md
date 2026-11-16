# R9 J2 development variant log

Worker tag: L-A
Created: 2026-11-11T12:00:25Z (updated before any variant run)
Scope: J1 portfolio construction only. The signal remains fixed at the five-session SIC2-relative return signal, with the registered sign and timing. All variants use the development-only `r9/data/J2_DEV_FROM_20201127.npz` price panel, the staged J1 score bundle filtered to 2020-11-27 through 2026-10-30, R6 cost of 0.05% per dollar of buys-plus-sells traded notional, and PIT EW30. No holdout or pre-2020-11-27 data is authorized.

For a fair comparison, the benchmark and all 12 variants start on the first scheduled formation date when every variant has the minimum history and eligible names required by its logged target. Each variant uses daily marking, the registered next-session-open trade, and price drift between trades. A target is held unchanged when fewer than its required number of eligible names are available, matching the fixed availability behavior in J1.

| ID | Timestamp (UTC; logged before any variant run) | Exact portfolio-construction rules |
|---|---|---|
| R9-V0 | 2026-11-11T12:00:25Z | J1 as written: each fifth-session formation, select the five lowest eligible fixed J1 scores and set equal 20% target weights. Start from PIT EW30. On the next open, move pro rata toward target by the largest step keeping total traded notional (buys plus sells divided by NAV) at or below 50% per rebalance, including the initial transition. Hold and drift between formations. |
| R9-V1 | 2026-11-11T12:00:25Z | Five lowest signal names, equal 20% target weights. No-trade band: at a weekly rebalance, if a name's absolute target-weight change is under 2% of NAV, keep its drifted weight; redistribute the remaining target NAV equally across the other selected names, and trade fully to that adjusted target. |
| R9-V2 | 2026-11-11T12:00:25Z | Hold buffer: retain current holdings whose signal rank remains among the eight lowest eligible names; fill remaining slots in ascending score order, then assign equal 20% weights to the five resulting names and trade fully to target weekly. |
| R9-V3 | 2026-11-11T12:00:25Z | Smooth each eligible name's signal as the arithmetic mean of its current and prior one weekly formation signal (2 observations); rank ascending and hold the five lowest with equal 20% targets, trading fully weekly. Exclude a name until both scores are available. |
| R9-V4 | 2026-11-11T12:00:25Z | Smooth each eligible name's signal as the arithmetic mean of its current and prior two weekly formation signals (3 observations); rank ascending and hold the five lowest with equal 20% targets, trading fully weekly. Exclude a name until all three scores are available. |
| R9-V5 | 2026-11-11T12:00:25Z | Smooth each eligible name's signal as the arithmetic mean of its current and prior three weekly formation signals (4 observations); rank ascending and hold the five lowest with equal 20% targets, trading fully weekly. Exclude a name until all four scores are available. |
| R9-V6 | 2026-11-11T12:00:25Z | Keep the five-lowest-signal equal-weight target. Rebalance every second scheduled weekly formation (10-session/biweekly cadence), beginning at the common comparison start; hold and drift between those dates. |
| R9-V7 | 2026-11-11T12:00:25Z | Eight lowest signal names, equal 12.5% target weights; rank and trade fully at every weekly formation. |
| R9-V8 | 2026-11-11T12:00:25Z | Ten lowest signal names, equal 10% target weights; rank and trade fully at every weekly formation. |
| R9-V9 | 2026-11-11T12:00:25Z | Five lowest signal names, inverse-volatility target weights: weight proportional to the inverse of each name's sample standard deviation of its trailing 20 daily adjusted-close returns ending at formation close; cap each weight at 40%, then redistribute the residual pro rata by inverse volatility among uncapped names until weights sum to 100%. Exclude names lacking 20 valid returns; trade fully weekly. |
| R9-V10 | 2026-11-11T12:00:25Z | Five lowest signal names, equal 20% target weights; at each weekly formation move 50% of the way from current drifted weights toward target, leaving the rest invested in current holdings. |
| R9-V11 | 2026-11-11T12:00:25Z | Five lowest signal names, equal 20% target weights; at each weekly formation move 75% of the way from current drifted weights toward target, leaving the rest invested in current holdings. |

## Precommitted selection rule

Choose ONE final variant (J2) by a rule written down before any variant is run: highest dev-period net Sharpe among variants with active share ≥50% and cost/gross edge <50%. Ties → lower turnover. Freeze J2 (rules file + SHA-256) before step 6.

No other variants or parameter values may be run under this log. Every attempted run, including failures, counts toward the 12-variant budget.
