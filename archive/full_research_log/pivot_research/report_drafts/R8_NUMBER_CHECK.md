# R8 number check

**FAIL count: 3** (one incorrect numerical explanation; one unsourced chart claim; one numeric claim not supported by its nearby cited source). I checked the values in both drafts against the files named in their nearby `src:` comments. No holdout data files were opened. PASS means the reported value is supported at its shown precision; table/section identifiers are treated as labels, not empirical values.

| Number(s) in draft | Where it appears | Source file(s) checked | Source value / rounding check | Result |
|---|---|---|---|---|
| 7; Section 3 | Testing section 4 intro | `R6_FINAL.md`; `specs/r6_decisions.md` | Seven R6 strategies are listed and tested; same R6 gates are described. -Section 3- is a cross-reference label. | PASS |
| 2020-11-27-2026-10-30; 30; 7 | Testing section 4.1 development bullet | `R7_DATA_MANIFEST.md`; `R6_FINAL.md` | Manifest gives development bars 2020-11-27-2026-10-30; Dow universe is 30 names; R6 ran seven approaches. | PASS |
| January 2010-October 2020 | Testing section 4.1 holdout bullet | `R6_FINAL.md` (definition only) | R6_FINAL defines the sealed Dow holdout as 2010-01 to 2020-10. I did not inspect holdout observations. | PASS |
| S&P 500; Dow 30 | Testing section 4.1 final sentence | `R6_FINAL.md`; `R7_DATA_MANIFEST.md` | R6 used S&P signal panels for some tests and Dow portfolios; the manifest confirms universe coverage. | PASS |
| SHA-256 (256) | Testing section 4.2 | `specs/r6_prereg/*.md`; `R7_REPRO_INDEX.md` | Frozen preregistrations carry SHA256 digests. -256- is the hash standard-s label, not a result; one-version claim is consistent with seven R6 trial rows. | PASS |
| 2 | Testing section 4.3 signal threshold | `specs/r6_prereg/*.md`; `R6_FINAL.md` | Registered signal gate is NW t >= 2. | PASS |
| 500; 95% | Testing section 4.3 placebo | `specs/r6_prereg/*.md` | Frozen placebo designs use 500 permutations and the registered 5% one-sided criterion (equivalent to the stated 95% tail wording). | PASS |
| 30; 0.05%; 50% | Testing section 4.3 portfolio | `specs/r6_prereg/*.md`; `R6_FINAL.md` | Dow benchmark has 30 names; 0.05% traded-notional cost and a 50% turnover cap are in the R6 goal and frozen designs. The sentence compresses strategy-specific implementations but does not alter these values. | PASS |
| 3 | Testing section 4.3 heading/list | `R6_FINAL.md`; preregistrations | The draft lists signal, placebo, and portfolio gates. | PASS |
| 21; 7 | Testing section 4.4 | `specs/r6_holm_family.json`; `r4_harness/phase3.py` | Family has 21 endpoints; Holm helper includes blocked/unrun endpoints with p=1 per family note. | PASS |
| 2; +0.94 pp; +1.03 pp | Testing section 4.5 | `report_drafts/J1_REPLAY.md`; `report_drafts/J1_RECONCILE.md`; `R6_FINAL.md` | Independent replay is +0.9360 pp (rounds +0.94); official excess +1.0276019 pp (rounds +1.03). J1 and D1 are the two independently rebuilt results. | PASS |
| 4 (K1); 2 (G1) | Testing section 4.6 | `specs/r6_decisions.md` items 116-127; `R6_FINAL.md` | K1 took four attempts and G1 two; failures preceded saved/printed outcomes. | PASS |
| 2020 (development boundary) | Testing section 4.6 | `specs/r6_decisions.md` items 152 and 169; `R7_FINAL.md` | The two incidents involved staged development date labels from June-November 2020; no prices/results were read. The wording -early checks- is imprecise because one incident was later. | PASS (wording note) |
| 7; 30; 0 | Evaluation opening | `R7_FINAL.md`; `R6_FINAL.md` | Seven R6 strategies, none passed; no holdout run. | PASS |
| 30; Nov 2020-Oct 2026 | Evaluation Table 5.1 heading | `R6_FINAL.md`; `R7_DATA_MANIFEST.md` | R6 Dow sample and development window match. | PASS |
| J1: 0.015, 2.08, 0.002, 0.82, 0.90 | Evaluation Table 5.1 J1 row | `R7_FINAL.md` section 1; `r6_J1/J1_RESULTS.json` | IC 0.0147863 rounds to 0.015; NW t 2.0770 rounds to 2.08; placebo 0.001996 rounds to 0.002; net Sharpe 0.8229 rounds to 0.82 and EW30 0.9020 rounds to 0.90. | PASS |
| D1: 0.009, 1.91, 0.002 | Evaluation Table 5.1 D1 row | `R7_FINAL.md` section 1; `report_drafts/REPRO_D1.md` | IC 0.0093742 rounds to 0.009; NW t 1.9080 rounds to 1.91; placebo p 0.001996 rounds to 0.002. | PASS |
| E1: -0.005, -0.24, 0.81 | Evaluation Table 5.1 E1 row | `R7_FINAL.md` section 1; `R6_FINAL.md` | IC -0.0045 - -0.005; t -0.24; placebo p 0.81. | PASS |
| R1: 0.73, 0.23 | Evaluation Table 5.1 R1 row | `R7_FINAL.md` section 1; `R6_FINAL.md` | R1 t=0.73 and placebo p=0.23. | PASS |
| P1: -0.015, -0.75, 1.00 | Evaluation Table 5.1 P1 row | `R7_FINAL.md` section 1; `R6_FINAL.md` | IC -0.0147 - -0.015; t -0.75; p=1.0 rounds to 1.00. | PASS |
| K1: 0.000, 0.03, 0.77 | Evaluation Table 5.1 K1 row | `R7_FINAL.md` section 1; `specs/r6_decisions.md` item 128 | IC 0.0003 rounds to 0.000 at 3 decimals; t=0.03; placebo p=0.77. | PASS |
| G1: 0.002, 0.19, 0.71 | Evaluation Table 5.1 G1 row | `R7_FINAL.md` section 1; `specs/r6_decisions.md` item 126 | IC 0.0018 rounds to 0.002; t=0.19; placebo p=0.71. | PASS |
| 21; 0.36; 0.51 | Evaluation section 5.1 Holm paragraph | `specs/r6_holm_family.json`; `r4_harness/phase3.py` | Recomputed directly with `phase3.holm_correction`: 21 p-values; H7/J1 Holm p=0.359078378 - 0.36; H1/D1 Holm p=0.507510 - 0.51. Both correct. | PASS |
| Figure 5.1; 14.9%; 10.4%; 1.0% | Evaluation section 5.2 opening | `r6_J1/J1_RESULTS.json`; `J1_REPLAY.md`; `figures/R8_J1_METRICS.json` | Official gross excess is 14.9105% rounds to 14.9%; strategy costs are 10.3567% rounds to 10.4%; official net excess is 1.0276% rounds to 1.0%. However, saying the 10.4 pp strategy cost -cut- gross excess to net excess is arithmetically unsupported: benchmark costs and compounding mean gross excess minus strategy cost does not equal net excess. The exact reported net excess is independently corroborated, but the causal subtraction is wrong. | **FAIL** |
| Figure 5.1 claim -ahead - for most of the period- | Evaluation section 5.2 opening | `figures/R8_J1_METRICS.json` (named nearby); no chart series/source in comment | Metrics JSON contains summary statistics, not the cumulative path or a duration count. The figure path itself is not a named source in the nearby `src:` comment. | **FAIL** |
| 30 Nov 2020-30 Oct 2026; Table 5.2 | Evaluation Table 5.2 heading | `figures/R8_J1_METRICS.json` | Sample first/last day are 2020-11-30 and 2026-10-30. | PASS |
| 12.1%, 12.0% | Evaluation Table 5.2 annualised return | `figures/R8_J1_METRICS.json` | J1 net 12.1008% - 12.1%; EW30 net 12.0011% - 12.0%. | PASS |
| 15.3%, 13.6% | Evaluation Table 5.2 annualised volatility | Same | J1 15.3064% - 15.3%; EW30 13.5912% - 13.6%. | PASS |
| 0.82, 0.90 | Evaluation Table 5.2 Sharpe | Same | J1 0.8229 rounds to 0.82; EW30 0.9020 rounds to 0.90. | PASS |
| 1.20, 1.29 | Evaluation Table 5.2 Sortino | Same | J1 1.2045 - 1.20; EW30 1.2856 - 1.29. | PASS |
| -21.9%, -21.4% | Evaluation Table 5.2 max drawdown | Same | J1 -21.8961% - -21.9%; EW30 -21.3654% - -21.4%. | PASS |
| 0.06 | Evaluation Table 5.2 information ratio | Same | 0.05629 - 0.06. | PASS |
| 48% | Evaluation Table 5.2 turnover | Same | 0.481737 - 48.2%, rounds to whole percent 48%. | PASS |
| 66%; 25%; p=0.45 | Evaluation section 5.2 final paragraph | `r6_J1/J1_RESULTS.json`; J1 prereg | Cost/gross edge=0.661742 - 66%; bootstrap p=0.449110 - 0.45. But -above our 25% limit- is incomplete: the R6 rule is turnover -50% **or** cost/gross edge <25%; J1-s 48.17% turnover satisfies the first branch. It is above the cost-share branch threshold, not an unconditional strategy limit. | PASS (threshold framing needs correction) |
| 30; Table 5.3 | Evaluation section 5.3 opening/table title | `R6_FINAL.md`; `R7_DATA_MANIFEST.md` | Dow universe has 30 names; -Table 5.3- is a label. | PASS |
| 80%; 0.099 | Evaluation Table 5.3 Dow top-five weekly | `report_drafts/CRITERION4_BOUND_VERIFY.md` | Long-only weekly IC 80%-power hurdle is 0.099. | PASS |
| 0.07 | Evaluation Table 5.3 Dow best shape | `report_drafts/CRITERION4_BOUND_BY_SHAPE.md`; `specs/r6_decisions.md` item 166 | Lowest qualifying listed daily top-15 hurdle is 0.070; weekly rank-weighted top half is 0.074. -About 0.07- is reasonable, though the shape/horizon should be named to avoid implying a unique universal minimum. | PASS (rounded) |
| S&P 500; 0.028 | Evaluation Table 5.3 S&P row | `report_drafts/R7_POWER_GATE_STRESS.md` | Weekly rank-weighted top-half at -=0.8 is calibrated near 0.028 for 80% power. Value is conditional on assumptions; the draft omits the -=0.8 qualifier. | PASS (qualifier omitted) |
| 0.01-0.03 | Evaluation Table 5.3 published effects | `specs/r7_effect_sizes.md` | Literature review gives pseudo-IC estimates in this broad range, while explicitly cautioning these are not matched ICs. | PASS (must retain pseudo-IC caveat) |
| 3-7; 0.015 | Evaluation section 5.3 after table | `CRITERION4_BOUND_VERIFY.md`; `CRITERION4_BOUND_BY_SHAPE.md`; `specs/r7_effect_sizes.md`; `r6_J1/J1_RESULTS.json` | Ratio of the displayed hurdle range (about 0.07-0.099) to 0.01-0.03 is roughly 2.3-9.9 depending endpoints; the narrower -3-7- comparison is not uniquely defined. J1 IC 0.014786 rounds to 0.015. | **PASS only as loose illustrative range; specify matched endpoints** |
| 6 years; about 300 weekly rebalances | Evaluation section 5.4 | `R8_J1_METRICS.json`; `R7_DATA_MANIFEST.md` | Sample duration 5.9008 years - about six; 298 rebalances - about 300. | PASS |
| 51; December 2017; 2016 | Evaluation section 5.4 data gaps | `R7_DATA_MANIFEST.md`; `r6_data/alpaca/ALPACA_AUDIT.md`; `R8_J1_METRICS.json` | 51 names without staged price history and Alpaca history from 2016 are supported. The nearby named sources do not support December 2017; `R7_FINAL.md` does, for FINRA short-interest *holdout* availability, but it is not named in the draft comment and ?holdout? is omitted. | **FAIL** |
| 298 | Evaluation section 5.4 final bullet | `figures/R8_J1_METRICS.json` | Rebalances=298. | PASS |
| 0.028; S&P 500 | Evaluation section 5.5 | `R7_FINAL.md` -3; `R7_POWER_GATE_STRESS.md`; `R7_DATA_MANIFEST.md` | 0.028 is the conditional weekly S&P hurdle; no sealed S&P holdout is reported. | PASS (conditional) |
| 20 Nov 2026 | Report context/date if read as a deadline | No nearby source comment in either draft | Deadline is stated in the task context, not sourced in the drafts; it is not a claim made by either draft. | N/A |

## Source-less or overstated claims to resolve

- The chart assertion that J1 was ahead of EW30 -for most of the period- needs the cumulative chart/underlying series named in the nearby source comment.
- The nearby named sources do not support December 2017; `R7_FINAL.md` supports it only for holdout short-interest availability. Add that source and clarify the series/sample.
- The 25% cost-share number is one branch of the turnover-or-cost condition; say J1 exceeded the cost-share branch while meeting the -50% turnover branch.
- Table 5.3 should identify the particular assumed design behind each IC hurdle and label literature values as pseudo-ICs.

## Holm recomputation

Loaded the 21 entries from `specs/r6_holm_family.json` and called `r4_harness.phase3.holm_correction` unchanged. H7/J1 = 0.359078378 (reported 0.36); H1/D1 = 0.507510 (reported 0.51); neither rejects at -=0.05.

## Re-check

**FAIL count: 0** (all requested numeric claims pass at the precision shown; section labels are not empirical values).

| Number(s) | Draft location | Source checked | Source value and rounding | Result |
|---|---|---|---|---|
| 80% | `R8_EVALUATION.md` section 5.2, paragraph 1: ahead of EW30 after costs | `report_drafts/figures/R8_J1_METRICS.json`, `net_vs_ew30.share_of_days_ahead_net` | 0.799596503, or 79.9597% of days; rounds to 80%. | PASS |
| 0.5% | Same paragraph: EW30 total cost | `report_drafts/figures/R8_J1_METRICS.json`, `net_vs_ew30.ew30_total_cost` | 0.004897266 of capital, or 0.4897%; rounds to 0.5%. | PASS |
| 10.4%; 14.9%; 1.0 percentage point | Same paragraph: J1 costs, gross lead and net lead | `report_drafts/figures/R8_J1_METRICS.json`, `official.total_strategy_cost`, `official.gross_excess_return`, `official.net_excess_return` | 0.103566512 -> 10.4%; 0.149105418 -> 14.9%; 0.010276019 -> 1.0 percentage point. The reported values match. These fields support the outcomes but do not independently decompose the stated compounding explanation. | PASS |
| 0.003; t = 0.34 | `R8_EVALUATION.md` section 5.1, “Section 3 strategy” paragraph | `r4_L1/POSTMORTEM.md`, line 74 | Observed five-day pressure IC 0.0034, NW t 0.34; IC rounds to 0.003. | PASS |
| +133.2%; +102.6% | Same paragraph: gross returns | `r4_L1/POSTMORTEM.md`, lines 80-83 | Heat50 top-five gross return +133.2%; EW30 gross return +102.6%. Exact displayed values. | PASS |
| 161% | Same paragraph: traded per rebalance | `r4_L1/POSTMORTEM.md`, lines 80-83 | Mean total traded notional 161.2%; rounds to 161% at whole-percent precision. | PASS |
| +83.3%; +101.7% | Same paragraph: net returns | `r4_L1/POSTMORTEM.md`, lines 80-83 | Heat50 +83.3%; EW30 +101.7%. Exact displayed values. | PASS |
| 0.64; 0.92 | Same paragraph: Sharpe ratios | `r4_L1/POSTMORTEM.md`, lines 80-83 | Heat50 net Sharpe 0.64; EW30 net Sharpe 0.92. Exact displayed values. | PASS |
| 7 | `R8_TESTING_VALIDATION.md`, opening paragraph: seven new strategies | `R7_FINAL.md` section 1; `R6_FINAL.md` | Seven R6 strategies were run. The count matches. | PASS |
| December 2017 (2017-12-29); 2020-10-30; 69; 2,070 | `R8_EVALUATION.md` section 5.4, data-gaps bullet | `R7_DATA_MANIFEST.md`, line 92 | Holdout FINRA short-interest manifest begins 2017-12-29 and ends 2020-10-30; it has 69 consolidated files and 2,070 file/ticker rows. December 2017 is an accurate month-level summary. The revised draft now specifies the holdout period and cites this manifest line. | PASS |

**Non-numeric scope note:** The opening paragraph says the seven strategies were each “tested the same way.” The cited summaries support a common staged gate and preregistration process, while strategy-specific signals, horizons and execution rules varied; interpret “same way” as shared evaluation gates, not identical test specifications.


## Final pass

**FAIL count: 0.** I re-checked every numeric claim in the current versions of both drafts against the cited development sources. Section and table numbers are editorial labels; no holdout observations were accessed.

| Draft location | Number(s) checked | Source values and rounding | Result |
|---|---|---|---|
| Testing opening paragraph | 3 and 5.1 are section labels; seven strategies | `R7_FINAL.md` section 1 lists/runs seven new strategies; `r4_L1/POSTMORTEM.md` records the baseline. ?Same tests and pass rules? means shared gates; individual signals and horizons differ. | PASS |
| Testing section 4.1 | Dow 30; 2020-11-27 to 2026-10-30; seven; holdout Jan 2010 to Oct 2020; once; zero holdout results | `R7_DATA_MANIFEST.md` gives development window and Dow universe; `R6_FINAL.md` defines holdout and says it was not opened; seven R6 strategies, none passed. | PASS |
| Testing section 4.2 | One version per idea | `specs/r6_prereg/*.md`, `specs/r4_trials.md`, `R7_REPRO_INDEX.md`: seven R6 ideas each have a frozen single variant. | PASS |
| Testing section 4.3 signal gate | Three tests; t >= 2 | `specs/r6_goal.md` and `specs/r6_prereg/J1.md`: mechanism Newey-West threshold is 2.0; signal, placebo, and portfolio gates are in order, with later tests blocked after failure. | PASS |
| Testing section 4.3 placebo gate | 500 shuffles; 95% | `specs/r6_prereg/J1.md` specifies 500 draws and p < 0.05; other R6 preregistrations use their registered 500-draw placebo. E1 shuffles industry labels as the draft says. | PASS |
| Testing section 4.3 portfolio gate | Dow 30; 0.05%; 50%; 25% | `specs/r6_goal.md` and J1 prereg: 0.05% cost per traded-notional dollar; long-only active share >= 50%; average turnover <= 50% or cost/gross edge < 25%. The draft's half-holdings wording is an informal description of active share; the formal threshold is average active share. | PASS |
| Testing section 4.4 | Three endpoints per strategy; seven strategies; 21 endpoints; unrun p = 1 | `specs/r6_holm_family.json` has H1-H21; its note assigns p=1 to unrun endpoints for Holm only. Three endpoints x seven strategies = 21. | PASS |
| Testing section 4.5 | Two independent checks; +0.94 pp; +1.03 pp | `report_drafts/REPRO_D1.md`, `J1_REPLAY.md`, `J1_RECONCILE.md`: D1 and J1 were reproduced; J1 replay excess +0.9360 pp rounds +0.94; official +1.0276 pp rounds +1.03. Both Sharpe comparisons are lower for J1 than EW30. | PASS |
| Testing section 4.6 | Two runs; K1 four attempts; G1 two attempts; two cited boundary incidents | `R7_FINAL.md` section 4 and `specs/r6_decisions.md` items 116-127, 152, 169: counts and pre-outcome crashes match; the date-label incidents did not use prices/results. | PASS |
| Evaluation opening | Zero passing strategies; one closest candidate (J1) | `R7_FINAL.md` section 1: no validated strategy; J1 passed mechanism/placebo but failed criterion 4. | PASS |
| Evaluation section 5.1, Section 3 strategy | Five-day; IC 0.003; t 0.34; top five; gross +133.2% vs +102.6%; turnover 161%; net +83.3% vs +101.7%; Sharpe 0.64 vs 0.92 | `r4_L1/POSTMORTEM.md` lines 74, 80-85: IC 0.0034 rounds to 0.003; t, gross/net returns and Sharpes match; 161.2% mean turnover rounds to 161%. | PASS |
| Evaluation section 5.1, Table 5.1 header | Dow 30; Nov 2020-Oct 2026; Table 5.1 | `R6_FINAL.md` and `R7_DATA_MANIFEST.md`: universe and period match; table number is a label. | PASS |
| Evaluation Table 5.1, J1 | IC 0.015; t 2.08; placebo p 0.002; Sharpes 0.82 and 0.90 | `R7_FINAL.md` section 1 and `r6_J1/J1_RESULTS.json`: IC 0.014786 -> 0.015; t 2.0770 -> 2.08; p 0.001996 -> 0.002; net Sharpe 0.8232 -> 0.82 vs EW30 0.9023 -> 0.90. | PASS |
| Evaluation Table 5.1, D1 | IC 0.009; t 1.91; p 0.002 | `R7_FINAL.md` section 1 and `report_drafts/REPRO_D1.md`: 0.009374 -> 0.009; 1.9080 -> 1.91; 0.001996 -> 0.002. | PASS |
| Evaluation Table 5.1, E1 | IC -0.005; t -0.24; p 0.81 | `R7_FINAL.md` section 1; `R6_FINAL.md`: -0.0045 rounds -0.005; t and p match. | PASS |
| Evaluation Table 5.1, R1 | t 0.73; p 0.23 | `R7_FINAL.md` section 1; `R6_FINAL.md`: both match. | PASS |
| Evaluation Table 5.1, P1 | IC -0.015; t -0.75; p 1.00 | `R7_FINAL.md` section 1; `R6_FINAL.md`: -0.0147 rounds -0.015; t and p match. | PASS |
| Evaluation Table 5.1, K1 | IC 0.000; t 0.03; p 0.77 | `R7_FINAL.md` section 1; `specs/r6_decisions.md` item 128: 0.0003 rounds 0.000 at three decimals; t and p match. | PASS |
| Evaluation Table 5.1, G1 | IC 0.002; t 0.19; p 0.71 | `R7_FINAL.md` section 1; `specs/r6_decisions.md` item 126: 0.0018 rounds 0.002; t and p match. | PASS |
| Evaluation Table 5.1 strategy count | Seven pre-registered strategies | `R6_FINAL.md`: D1, E1, J1, R1, P1, K1, G1; count 7. | PASS |
| Evaluation Holm paragraph | 21; J1 0.36; D1 0.51 | `specs/r6_holm_family.json` recomputed with `r4_harness.phase3.holm_correction`: family size 21; H7 = 0.359078 -> 0.36; H1 = 0.507510 -> 0.51. | PASS |
| Evaluation section 5.2 lead paragraph | 14.9 pp gross; 10.4% J1 cost; 0.5% EW30 cost; 1.0 pp net; 80% of days ahead | `figures/R8_J1_METRICS.json`: gross excess 0.149105 -> 14.9 pp; strategy cost 0.103567 -> 10.4%; EW cost 0.004897 -> 0.5%; net excess 0.010276 -> +1.0 pp; share ahead net 0.799597 -> 80%. | PASS |
| Evaluation Table 5.2 header | 30 Nov 2020-30 Oct 2026; Table 5.2 | Metrics JSON sample dates are 2020-11-30 and 2026-10-30; table number is a label. | PASS |
| Evaluation Table 5.2 annualized return | J1 12.1%; EW30 12.0% | Metrics JSON: 12.1008% -> 12.1%; 12.0011% -> 12.0%. | PASS |
| Evaluation Table 5.2 annualized volatility | J1 15.3%; EW30 13.6% | Metrics JSON: 15.3064% -> 15.3%; 13.5912% -> 13.6%. | PASS |
| Evaluation Table 5.2 Sharpe | J1 0.82; EW30 0.90 | Metrics JSON: 0.8229 -> 0.82; 0.9020 -> 0.90. | PASS |
| Evaluation Table 5.2 Sortino | J1 1.20; EW30 1.29 | Metrics JSON: 1.2045 -> 1.20; 1.2856 -> 1.29. | PASS |
| Evaluation Table 5.2 max drawdown | J1 -21.9%; EW30 -21.4% | Metrics JSON: -21.8961% -> -21.9%; -21.3654% -> -21.4%. | PASS |
| Evaluation Table 5.2 information ratio and mean turnover | 0.06; 48% | Metrics JSON: information ratio 0.05629 -> 0.06; mean turnover 0.481737 -> 48%. | PASS |
| Evaluation Table 5.2 new rows | Net excess +1.0 pp; active share 55%; block-bootstrap p 0.45 | `r6_J1/J1_RESULTS.json`: net excess 0.010276 -> +1.0 pp; average active share 0.547681 -> 55%; bootstrap p 0.449110 -> 0.45. | PASS |
| Evaluation costs/cap sentence | 66%; 50%; p 0.45 | `r6_J1/J1_RESULTS.json`: cost/gross-edge ratio 0.661742 -> 66%; `turnover_cap_pass` is true and maximum turnover is 0.500000000001 (50% plus 1e-12 floating-point residue); bootstrap p 0.449110 -> 0.45. The result passes the registered cap check, with the tiny machine-precision overshoot disclosed. | PASS |
| Evaluation section 5.3 design hurdle | 30 names; 80%; IC 0.099; about 0.07; about 0.028; effects 0.01-0.03 | `CRITERION4_BOUND_VERIFY.md`: top-five weekly hurdle 0.099; `CRITERION4_BOUND_BY_SHAPE.md`: qualifying shapes near 0.070-0.074; `R7_POWER_GATE_STRESS.md`: conditional weekly S&P hurdle around 0.028; `specs/r7_effect_sizes.md`: literature pseudo-IC range 0.01-0.03. The draft describes these as simulation/planning values and a rough literature guide. | PASS |
| Evaluation section 5.3 comparison | About 3-7 times; J1 IC 0.015 | Sources above: paired endpoint comparisons 0.099/0.03 = 3.3 and 0.07/0.01 = 7.0; J1 IC 0.014786 -> 0.015. ?About? and the following caveat appropriately signal a rough comparison, not the full Cartesian ratio range. | PASS |
| Evaluation section 5.4 short window | Six years; about 300 weekly rebalances | Metrics JSON: 5.9008 years -> about six; 298 rebalances -> about 300. | PASS |
| Evaluation section 5.4 universe and data gaps | 30 stocks; 51 missing S&P names; December 2017; 2016; no holdout; no stability test | `R7_DATA_MANIFEST.md` supports 51; line 92 records holdout FINRA SI from 2017-12-29 to 2020-10-30; `ALPACA_AUDIT.md` supports 2016; R6_FINAL confirms no holdout run. Qualitative no-stability statement is consistent with the reported tests. | PASS |
| Evaluation section 5.5 | S&P 500; IC 0.028 | `R7_FINAL.md` section 3; `R7_POWER_GATE_STRESS.md`: conditional weekly S&P design hurdle around 0.028; the draft says this was not tested and notes no sealed S&P holdout. | PASS |

