# 5. Evaluation of results

<!-- DRAFT for the team to edit. The "src:" comments are for checking only and are not counted; delete them before submission. -->

No strategy passed all tests, so none was run on the holdout. The closest, J1, passed its signal and placebo tests but did not beat simply holding the Dow after trading costs.
<!-- src: R7_FINAL.md §1 -->

## 5.1 Results

**Section 3 strategy.** The pressure-plus-heat signal had almost no predictive power (five-day IC 0.003, t = 0.34). Its top-five portfolio beat EW30 before costs (+133.2% against +102.6%), but it traded about 161% of its value each rebalance, so after costs it returned +83.3% against +101.7%. Its net Sharpe ratio was 0.64, against 0.92 for EW30.
<!-- src: r4_L1/POSTMORTEM.md lines 74, 80-85 (IC 0.0034 t 0.34; gross 133.2/102.6; net 83.3/101.7; Sharpe 0.64/0.92; 161.2% traded notional) -->

**New strategies.** Table 5.1 shows the seven pre-registered strategies.

**Table 5.1: Development results (Dow 30, Nov 2020 – Oct 2026)**

| Strategy | Signal | Signal test (IC, t) | Placebo p (raw) | Portfolio test | Result |
|---|---|---|---|---|---|
| J1 | Weekly reversal relative to industry peers | 0.015, t = 2.08 | 0.002 | Failed (Sharpe 0.82 vs 0.90) | Not passing |
| D1 | Daily short-selling volume | 0.009, t = 1.91 | 0.002 | Not run | Not passing (near-miss) |
| E1 | Peer close-location pressure | −0.005, t = −0.24 | 0.81 | Not run | Failed |
| R1 | Dividend-month premium | t = 0.73 | 0.23 | Not run | Failed |
| P1 | Overnight-return momentum | −0.015, t = −0.75 | 1.00 | Not run | Failed |
| K1 | Earnings-announcement drift | 0.000, t = 0.03 | 0.77 | Not run | Failed |
| G1 | High-volume premium | 0.002, t = 0.19 | 0.71 | Not run | Failed |
<!-- src: R7_FINAL.md §1 table; r6_J1/J1_RESULTS.json; specs/r6_decisions.md items 109, 126, 128 -->

After the Holm correction for all 21 registered tests, neither J1's signal (adjusted p = 0.36) nor D1's (0.51) is significant.
<!-- src: specs/r6_holm_family.json recomputed with phase3.holm_correction (H7 0.359, H1 0.508) -->

## 5.2 J1: a signal that did not survive costs

Each week J1 bought the Dow stocks that had fallen most against their industry peers, expecting a rebound. Before costs it beat EW30 by 14.9 percentage points. But its costs came to 10.4% of capital, against 0.5% for EW30, leaving a final lead of 1.0 point, although after costs it was ahead on 80% of trading days (Figure 5.1).
<!-- src: report_drafts/figures/R8_J1_METRICS.json (share_of_days_ahead_net 0.800, ew30_total_cost 0.0049, official.total_strategy_cost 0.1036, gross_excess 0.149, net_excess 0.0103); figure from make_r8_j1_figure.py -->

**Figure 5.1:** `figures/r8_j1_excess.png`: cumulative return of J1 minus EW30, before and after costs.

**Table 5.2: J1 vs EW30 after costs (30 Nov 2020 – 30 Oct 2026)**

| Metric | J1 | EW30 |
|---|---|---|
| Annualised return | 12.1% | 12.0% |
| Annualised volatility | 15.3% | 13.6% |
| Sharpe ratio | 0.82 | 0.90 |
| Sortino ratio | 1.20 | 1.29 |
| Maximum drawdown | −21.9% | −21.4% |
| Information ratio vs EW30 | 0.06 | – |
| Average turnover per weekly rebalance | 48% | – |
| Cumulative excess return vs EW30 | +1.0 pp | – |
| Active share | 55% | – |
| Block-bootstrap p-value | 0.45 | – |
<!-- src: report_drafts/figures/R8_J1_METRICS.json (from r6_J1/J1_RESULTS.json via make_r8_j1_figure.py) -->

J1 earned about the same return as EW30 but took more risk, so its Sharpe ratio was lower. Its turnover stayed within the 50% cap, but costs used up 66% of its gross excess return. The bootstrap test found no significant difference (p = 0.45).
<!-- src: r6_J1/J1_RESULTS.json (cost_to_gross_edge_ratio 0.662, bootstrap p 0.449) -->

## 5.3 Why nothing passed

The biggest hurdle is portfolio size. With only 30 stocks, a strategy needs a very strong signal to beat EW30 after costs and the multiple-test correction. We estimated how strong by simulation (Table 5.3), under stated assumptions about costs, turnover and return spread.

**Table 5.3: Signal strength (IC) needed for an 80% chance of passing**

| Universe and portfolio | IC needed |
|---|---|
| Dow 30, top 5 stocks, weekly | 0.099 |
| Dow 30, best portfolio shape | about 0.07 |
| S&P 500, best shape, slow signal | about 0.028 |
| Published effects in large US stocks | 0.01 – 0.03 |
<!-- src: report_drafts/CRITERION4_BOUND_VERIFY.md; CRITERION4_BOUND_BY_SHAPE.md; R7_POWER_GATE_STRESS.md; specs/r7_effect_sizes.md -->

On the Dow, the IC needed is about three to seven times larger than published effects. J1's IC of 0.015 is in line with those effects, which helps explain why it could not pass. The published range is only a rough guide.

## 5.4 Limitations

- **Short window.** Development covers only six years, about 300 weekly rebalances.
- **Small universe.** Thirty stocks limit how much a signal can be spread across names.
- **Data gaps.** The S&P 500 price data is missing 51 names, short-interest data for the holdout period starts only in December 2017, and minute data from Alpaca starts in 2016.
- **No holdout result.** Because nothing passed, we have no out-of-sample evidence.
- **No stability test.** We did not test whether J1's result held across sub-periods.
<!-- src: R7_DATA_MANIFEST.md (51 names; line 92: holdout FINRA short interest 2017-12-29 to 2020-10-30); r6_data/alpaca/ALPACA_AUDIT.md (2016); R8_J1_METRICS.json (298 rebalances) -->

## 5.5 What would change the outcome

A larger universe may help. On the S&P 500 the required IC falls to about 0.028, inside the published range. We did not test this, because no sealed S&P holdout was available and there was not enough time to build one properly. A future test would need point-in-time S&P data with a separate, untouched holdout period.
<!-- src: R7_FINAL.md §3; R7_DATA_MANIFEST.md; specs/r7_decisions.md items 19, 23 -->
