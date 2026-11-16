# R9 ruleset: refining a promising strategy (J1 → J2)

Written 2026-11-11. Supersedes the R6 "one version, no rescue" rule ONLY for J1. All other R6 rules stand.

## Why the change
J1 passed its signal and placebo tests (IC 0.0148, t 2.08, placebo p 0.002) but failed the portfolio test because of costs (66% of gross edge) and higher volatility. R6 banned rescue versions to stop p-hacking. R9 allows a controlled refinement instead: tweaks are allowed, but every tweak is counted, and the final verdict comes only from data no tweak has seen.

## Rules
1. **Eligibility.** Only a strategy that passed both the signal test and the placebo test may be refined. Currently: J1 only. (D1 is not eligible: t 1.91.)
2. **What may change.** Portfolio construction and trading rules only: no-trade bands / hold buffers, signal smoothing, rebalance frequency, number of names, weighting (incl. inverse-volatility), partial rebalancing toward target. The signal itself (5-session industry-relative return, sign, SIC2 peers) is FIXED. No new data sources.
3. **Variant budget.** At most **12 variants** in total, each listed in `specs/r9_variant_log.md` with its rules and a timestamp BEFORE it is run. Every variant run counts, including failures and crashes after results are seen. No unlogged runs.
4. **Development data.** Variants are evaluated on the development period (27 Nov 2020 – 30 Oct 2026) with the R6 cost model (0.05% per dollar traded, buys+sells counted once) against PIT EW30. Report for every variant: net excess return, Sharpe vs EW30, turnover, cost/gross edge, active share, bootstrap p, and **deflated Sharpe ratio using the full trial count** (R6 trials + all R9 variants).
5. **Selection.** Choose ONE final variant (J2) by a rule written down before any variant is run: highest dev-period net Sharpe among variants with active share ≥50% and cost/gross edge <50%. Ties → lower turnover. Freeze J2 (rules file + SHA-256) before step 6.
6. **Confirmation (the significance test).** J2 is run **once** on the sealed Dow holdout (Jan 2010 – Oct 2020), unchanged. Pass = beats EW30 on net return AND net Sharpe, bootstrap p < 0.05 (one-sided), DSR > 0.95. The holdout is opened only after the user approves the frozen J2 file. One shot: a holdout failure is reported, not fixed.
7. **Multiple testing.** The holdout test is a new pre-registered test with its own family; the development results are reported as exploratory, with their trial count, never as confirmation.
8. **Honesty in the report.** The report states that J2 was refined after seeing J1's development results, how many variants were tried, and that only the holdout result is confirmatory.

## Unchanged R6 rules
No holdout or pre-2020-11-27 data on worker paths until rule 6 is approved; no orders; keys never printed; no edits to frozen R6 files; decisions logged in `specs/r9_decisions.md`.
