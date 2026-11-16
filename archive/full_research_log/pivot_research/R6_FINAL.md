# R6 Final Report

**STATUS (2026-11-11, updated after rounds S–AQ): CURRENT FINAL. 0 approaches pass all five criteria. Near-misses are labelled NOT passing. The sealed holdout (Dow, 2010-01 to 2020-10) has not been opened, because no direction passed development plus the portfolio test. This file will be updated if anything changes before the deadline (2026-11-18 23:59 AEST). The full decision log is specs/r6_decisions.md, items 1–221.**

## Executive summary

R6 froze and ran **7 of 30 allowed variants** (D1, E1, J1, R1, P1, K1, G1), each with one variant and a frozen pre-registration (FROZEN date plus content digest) before any outcome was seen. **None passes.**

| Direction | Idea | Mechanism result | Placebo p | Portfolio | Verdict |
|---|---|---|---|---|---|
| D1 | daily FINRA short-volume pressure | IC 0.0094, NW t 1.91 | 0.002 | not run | NOT passing (near-miss, t < 2) |
| E1 | monthly SIC2 peer CLV pressure | IC −0.0045, t −0.24 | 0.81 | not run | Fail |
| J1 | weekly SIC2-relative reversal | IC 0.0148, t 2.08 | 0.002 | net Sharpe 0.823 vs EW30 0.902; p 0.449 | NOT passing (fails criterion 4) |
| R1 | dividend-month premium | spread 0.093%/month, t 0.73 | 0.23 | not run | Fail |
| P1 | overnight-return momentum | IC −0.0147, t −0.75 | 1.0 | not run | Fail |
| K1 | earnings-announcement drift | IC 0.0003, t 0.03 | 0.77 | not run | Fail |
| G1 | high-volume return premium | IC 0.0018, t 0.19 | 0.71 | not run | Fail |

D1 and J1 were reproduced independently (report_drafts/REPRO_D1.md, REPRO_J1.md).

**Final R6 Holm family (H1–H21, raw p / Holm-adjusted p).** The family includes every R6 test; tests that were not run count as p = 1 for Holm only.

| Endpoint | Raw p | Holm p | | Endpoint | Raw p | Holm p |
|---|---|---|---|---|---|---|
| H1 D1 mech | 0.028 | 0.508 | | H12 R1 port | not run | 1 |
| H2 D1 placebo | 0.002 | 0.042 | | H13 P1 mech | 0.772 | 1 |
| H3 D1 port | not run | 1 | | H14 P1 placebo | 1.0 | 1 |
| H4 E1 mech | 0.595 | 1 | | H15 P1 port | not run | 1 |
| H5 E1 placebo | 0.812 | 1 | | H16 K1 mech | 0.490 | 1 |
| H6 E1 port | not run | 1 | | H17 K1 placebo | 0.768 | 1 |
| H7 J1 mech | 0.019 | 0.359 | | H18 K1 port | not run | 1 |
| H8 J1 placebo | 0.002 | 0.042 | | H19 G1 mech | 0.424 | 1 |
| H9 J1 port | 0.449 | 1 | | H20 G1 placebo | 0.711 | 1 |
| H10 R1 mech | 0.235 | 1 | | H21 G1 port | not run | 1 |
| H11 R1 placebo | 0.228 | 1 | | | | |

The only adjusted p-values below 0.05 are placebo checks (H2, H8). No portfolio endpoint comes close.

**Ideas that failed the gate (not built):** rounds A–R (see the idea-gate record below), plus round S (network spread through suppliers, shared owners or SIC4 leaders: overlaps rejected families), round S4–S6 (13F herding, rebalancing, attention: overlaps or underpowered), round T (daily auction/intraday pressure: no free full-window inputs), a D4-reversal re-test (circular: its sign was chosen after D4's result), round U fund flows (free N-PORT covers ETFs, not active funds), and round U cross-asset (COT advanced to a red-team and was killed; it can't identify issuer-level pressure), round V (fails-to-deliver, earnings-calendar cues), W (high-IC literature, event pressure), X (options, co-movement networks), Y (news, seasonal flows), Z (Alpaca signed minute flow, auctions, intraday momentum), AA (IC ≥ 0.06 literature, event-concentrated), AB (Alpaca news), AC (stock-split pressure, Dow price-weighting), AD (tax-loss selling, FOMC drift), AF (peer earnings spillover, 52-week high), AG (index flow-day reversal, closing-auction liquidity), AH (Treasury auctions, foreign-session pressure), AI (quad witching, crypto spillover), AJ (new equity supply, buyback windows), AK (sector rotation, passive weight), AL (Google Trends attention, pre-ex-date run-up), AM (activist 13D, lockup expiry), AN (industry insider clusters, Rule 201 triggers), AO (liquidity shocks, window dressing), AP (days-to-cover squeeze, retail popularity), AQ (commodity roll, funding stress) and AE (analyst ratings from Alpaca news, BJZZ retail order imbalance: Dow trade data is pullable, about 0.6 TB, so the blocker is effect size). All failed the gate.

**Process errors (disclosed):** K1 took four execution attempts and G1 two, because of runner bookkeeping bugs (Holm hash convention, helper key names, prereg path). Each crash happened before any result was printed or written. A worker overwrote the earlier round-F (insider) idea file; its verdict survives in the decision log. A Wikipedia feasibility pull briefly ran past the development end date; it was discarded and rerun.

**Honest conclusion.** With free public data, buying-pressure signals on the post-2020 Dow show either no measurable effect or one that is too small to beat EW30 after costs. The binding constraint is criterion 4: a long-only Dow top-5 portfolio needs an IC of roughly 0.16 monthly / 0.10 weekly / 0.08 daily for 80% power (report_drafts/CRITERION4_BOUND_VERIFY.md; the earlier 0.085 estimate in CRITERION4_BOUND_AUDIT.md is superseded), while documented large-cap effects are 0.01–0.03. The two best results (J1's mechanism and D1's near-miss) are real but small, and are labelled NOT passing.

---
## Earlier detail (D1, E1, J1 sections and addenda kept for the record)

## Idea-gate record

All results below are gate decisions, not investment outcomes unless explicitly stated. **FAIL-GATE**, **FAIL**, **parked**, **deprioritised**, and **NOT passing** are not passes.

| Round | Outcome | Main reason |
|---|---|---|
| A | All four ideas **FAIL-GATE** after red-team. | Common-owner reversal was too close to an earlier result and had dense links, weak directional identification, and inadequate power or data. |
| B | All four **FAIL-GATE**; B4 tested as a feasibility candidate and failed. | Analyst/co-coverage links lacked point-in-time free coverage; GDELT co-mention graph was dense and Dow power was 41% at IC 0.01. |
| C | **FAIL-GATE as written**; C1 conditionally revived then deprioritised. | Initial cluster and SIC inputs were inadequate; corrected SIC3 power was 32% at the planned effect. C2/C3 also lacked power or free historical data. |
| D | Initially **FAIL-GATE**; D1 advanced conditionally and was frozen. | D1 had free Reg SHO coverage and 63% S&P power at the planning effect after cluster stress, but its realized NW t was 1.908, below 2.0. D2/D3 were dropped. |
| E | All initial directions **FAIL-GATE** under the original Dow-only power framing; E1 advanced after decision 17 clarified S&P mechanism estimation. | Monthly costs were lower, but customer-supplier coverage and peer-high evidence did not clear the gates. E1 later failed its mechanism and placebo. |
| F | Form 4 insider buying / peer spread **FAIL-GATE**. | Approximately one matched Dow event per quarter was too sparse for useful power. The SEC panel was retained as data only. |
| G | Volume-shock/visibility idea **parked; did not pass**. | SIC3-cluster MDE was about IC 0.036 and post-2020 large-cap evidence was thin. |
| H | ETF-to-constituent and DIA ideas **FAIL-GATE**. | Effective sector breadth was about 11 clusters; DIA gave only one source shock per date and no valid Dow cross-sectional ranking. |
| I | Seasonal buying pressure **FAIL-GATE**. | A holdout-safe one-year lag left 59 monthly observations and low power. |
| J | J1 allowed one frozen mechanism test despite an explicitly weak power case; idea gate was not a claim of empirical success. | S&P cluster power was 26.7% at IC 0.0183 (80%-power MDE about 0.0392). The registered mechanism passed, but the portfolio failed. |
| K | Both earnings-announcement pressure and peer transfer **FAIL-GATE**. | Season and SIC2 clustering left only 11–15% power at the cost hurdle; the proposed event-return measures were not evidence of buying flow. |
| L | FINRA short-interest / days-to-cover **FAIL-GATE**. | Monthly SIC2 power was low, and the free all-listed 2010–2020 history needed for the holdout was not verified. This is not a D1 rescue: short interest is a bi-monthly stock of outstanding positions, unlike daily Reg SHO short-sale volume. Licensed historical data may be considered only if access and coverage are verified. |
| M | Evidence-targeting survey; no new direction advanced. | No untried free-data pressure effect was found with documented large-cap, post-2010 effect size above the cluster MDE. |
| N | Cybersecurity-breach peer pressure and serial activist campaigns **both FAIL-GATE**. | Synthetic power was below 14% at planted monthly IC 0.02 (80%-power MDE about 0.10–0.14), with event coverage and sign uncertainty unresolved. |
| O1 | Flow/ownership pressure **FAIL-GATE**. | The best cited full-sample Sharpe was 0.75, below the roughly 0.8 criterion-4 feasibility screen even before costs; it did not establish a post-2010 mega-cap effect. |
| O2 | Cross-asset and macro pressure: no viable candidate. | Published ETF-flow evidence was daily and used paid inputs; mutual-fund allocation evidence ended in 2008 and did not establish Dow excess Sharpe. Neither supported the required post-cost portfolio edge. |

The gate record reflects decisions and source dossiers in [the decision log](../specs/r6_decisions.md), [round K](../r6_ideas/K.md), [round L](../r6_ideas/L.md), [round M survey](../r6_ideas/M_SURVEY.md), [round N](../r6_ideas/N.md), [round O1](../r6_ideasO1.md), and [round O2](../r6_ideasO2.md). Earlier rounds A–J are detailed in the idea dossiers linked from the [idea folder](../r6_ideas/).

## Frozen directions and development results

### D1 — daily FINRA Reg SHO short-volume pressure

D1-V1 measured a five-session average of matched facility short-volume ratio, signed as negative pressure, with a five-session forward horizon. The S&P 500 mechanism result had the expected sign and cleared the IC floor, but did not clear the pre-registered NW t threshold. The SIC2 shuffle passed; the sequence therefore stopped before the Dow portfolio.

| Endpoint | Development result | Holm adjusted p | Status |
|---|---|---:|---|
| R6-H1 mechanism | Mean IC 0.0093742; NW t(4) 1.908; IC floor passed, t≥2 failed; raw p=0.028195 | 0.507510 | **FAIL — near-miss, NOT passing** |
| R6-H2 SIC2 shuffle | Observed IC 0.0093742; null p95 0.0042863; raw p=0.001996 | 0.041916 | Placebo passed; does not rescue H1 |
| R6-H3 Dow portfolio | Not evaluated after H1 failed | Not run | **not run** |

The mechanism was independently reproduced (IC 0.00937; t=1.91). The run retained the placebo p95 and p-value but not all 500 shuffle draws; that limitation is disclosed. See [D1 results](../r6_D1/RESULTS.md) and [reproduction](REPRO_D1.md).

### E1 — monthly SIC2 peer CLV pressure

E1-V1 used prior-month CLV pressure among leave-one-out same-SIC2 peers, estimated at a 21-session horizon on the S&P PIT universe, with a monthly top-five Dow portfolio if mechanism gates passed. Input coverage passed: S&P member-day OHLCV-plus-dated-SIC coverage was 95.1%, Dow coverage 98.4%, and all 72 eligible formation dates met the 250-name threshold. The 51-name historical S&P price gap was handled with the predeclared date-wise exclusion. E1's portfolio was not run after the mechanism and placebo failed.

| Endpoint | Development result | Holm adjusted p | Status |
|---|---|---:|---|
| R6-H4 mechanism | Mean IC −0.004543; NW t(20) −0.2407; raw p=0.595093 | 1.000000 | **FAIL** |
| R6-H5 SIC2 shuffle | Observed IC −0.004543; null p95 0.009595; raw p=0.812375 | 1.000000 | **FAIL** |
| R6-H6 Dow portfolio | Blocked by H4/H5; no portfolio outcomes computed | Not run | **not run** |

All 500 E1 shuffle means are retained in the [E1 result bundle](../r6_E1/RESULTS.md). H6 portfolio returns, Sharpe, costs, turnover, active share, bootstrap p, and DSR are **not estimated**, not zero.

### J1 — weekly SIC2-relative return reversal

J1-V1 ranked a stock by its trailing five-session return relative to its leave-one-out SIC2 peer mean, predicting a negative next-five-session peer-relative return. There were 298 Dow formation dates; ten early rebalances were skipped for insufficient signal coverage. In the S&P mechanism input, 286 of 298 dates had at least 250 eligible names. The frozen run was authorized once after two failed pre-analysis attempts; those attempts were errors/input defects, not extra variants:

1. **Run #1:** portfolio-stage crash because a held Dow name lacked a close. No accepted outcome values were saved. Decision 63 fixed missing-close marking and liquidation handling for both strategy and EW30; decision 65 identified the GOOGL in-window gap and required rebuilding the price panel from the same-source S&P bars. This was disclosed as an implementation/input deviation.
2. **Run #2:** stopped before analysis because the signal bundle used the prior Dow price panel and failed the trailing-signal consistency check. No outcomes were computed; decision 67 created the coordinator-owned H1–H9 family record, and decision 68 ordered a signal-only input rebuild. Decision 69 relaunched the input worker after its terminal had exited.
3. **Run #3:** authorized by decision 70 after the input reconciliation passed; the sole official development execution produced complete results. Decisions 64 and 66 required independent H7/H8 reproduction before accepting the portfolio interpretation.

| Endpoint | Official result | Holm adjusted p | Status |
|---|---|---:|---|
| R6-H7 mechanism | Direction-adjusted mean IC 0.0147863; NW t(4)=2.07704; IC floor 0.0034641 passed; raw p=0.0188989 | 0.359078 | Raw mechanism gate **PASS**; family adjusted decision retain |
| R6-H8 SIC2 shuffle | 500 draws, seed 20261111; observed IC 0.0147863 > p95 0.00560598; p=0.00199601 | 0.041916 | Raw placebo gate **PASS**; family adjusted decision reject |
| R6-H9 Dow portfolio | Net cumulative excess +1.028%; gross excess +14.911%; costs 10.357% (66.2% of gross excess); net Sharpe 0.82318 vs EW30 0.90227; turnover 48.174% mean / 50% cap; active share 54.768%; block-bootstrap p=0.449110 | 1.000000 | **FAIL — NOT passing** on Sharpe and bootstrap evidence |

Portfolio diagnostic results: gross return was 110.784% for J1 and 95.874% for EW30; net return was 96.214% and 95.187%. The turnover cap and active-share checks passed, but the Sharpe comparison and overall portfolio criterion did not. DSR used the cumulative trial count of 3 and was 5.23316e−209.

The independent [J1 reproduction](REPRO_J1.md) matched H7 and the randomization p to three significant figures (IC 0.0148; t=2.08; p=0.00200). Its shuffle p95 was 0.00574 versus the official 0.00561 because the reference helper orders SIC2 groups differently before applying the same fixed seed; both distributions place the observation above their 95th percentile. The independent portfolio replay confirmed the Sharpe failure (0.815 vs 0.902), but its cumulative net excess was −2.66%, not the official +1.03%. That cumulative-excess discrepancy remains **unreconciled**; it does not change the NOT passing Sharpe/portfolio conclusion. The official H9 bootstrap p remains 0.449 (Holm 1.000).

## Final R6 Holm family — H1 through H9

This is the coordinator-owned family in `r6_J1/RESULTS.md`; it reports all nine frozen slots. “Not run” means no endpoint statistic was computed. Holm-adjusted values are copied from the saved final family table; this report does not recompute them.

| Endpoint | Direction / test | Raw p | Holm adjusted p | Status |
|---|---|---:|---:|---|
| H1 | D1 S&P mechanism | 0.028195 | 0.507510 | **FAIL — NOT passing** |
| H2 | D1 SIC2 placebo | 0.001996 | 0.041916 | Placebo pass; H1 failed |
| H3 | D1 Dow portfolio | Not run | Not run | **not run** |
| H4 | E1 S&P mechanism | 0.595093 | 1.000000 | **FAIL** |
| H5 | E1 SIC2 placebo | 0.812375 | 1.000000 | **FAIL** |
| H6 | E1 Dow portfolio | Not run | Not run | **not run** |
| H7 | J1 S&P mechanism | 0.018899 | 0.359078 | Raw gate passed; Holm adjusted decision retain |
| H8 | J1 SIC2 placebo | 0.001996 | 0.041916 | Raw gate passed; Holm adjusted decision reject |
| H9 | J1 Dow portfolio | 0.449110 | 1.000000 | **FAIL — NOT passing** |

Holm labels “reject” and “retain” refer to family-wise hypothesis-test decisions; they do not by themselves define whether the strategy passes all criteria. J1's raw mechanism and placebo gates passed, but H7 was not family-significant and the portfolio H9 failed. No absent portfolio endpoint is represented as an observed p-value.

## Feasibility, deviations, and conclusion

Decision 76 states that the binding constraint is criterion 4: a top-five Dow strategy versus EW30 needs one-sided block-bootstrap significance after Holm over roughly six years, which implies expected annualized excess Sharpe around 0.8 or higher after costs at no more than 20% turnover. J1's official portfolio p was 0.449 and its net Sharpe lagged EW30; the published effects screened in O1/O2 do not supply a credible way over this hurdle.

Decision 79 assesses free-data idea generation as saturated after fourteen idea rounds (A–O, with M an evidence survey) and three executed directions: D1 near-miss, E1 null, and J1 mechanism pass/portfolio fail. It records zero full R6 passes. The remaining data paths are licensed: FactSet/I-B-E-S for analyst co-coverage, Revere for supply-chain links, and Compustat or FactSet for historical short interest. Availability and user entitlement must be confirmed through the user's UNSW access; no such licensed input was used in these tests. Changing the fixed criteria is a user decision, not a coordinator or worker decision.

Disclosed deviations and limitations:

- **Variant count:** 3/30 (D1-V1, E1-V1, J1-V1); the two failed J1 attempts were not variants.
- **Price coverage:** unresolved S&P PIT price gaps were excluded date by date under decision 27; the 54-ticker survivorship gap and the J1 Dow roster/bar gap are disclosed. No missing forward outcome was fabricated.
- **J1 missing bars:** decisions 63 and 65 added the fixed held-name close marking rule and rebuilt the GOOGL price history from same-source S&P bars before run #3. The safety rule is an implementation deviation, disclosed above.
- **Placebo reproduction:** official and independent J1 placebo p95 values differ slightly because of SIC2 group iteration order; mean IC, NW t, and p-value match.
- **Portfolio reproduction:** independent J1 cumulative excess does not reconcile with official output; both Sharpe checks show J1 below EW30, and the official bootstrap/Holm values remain as reported.
- **Holdout:** no holdout prices, signals, returns, or results are reported here. Any future holdout execution is coordinator-only and must follow the frozen R5 protocol and criterion 5 exactly.

**Conclusion:** As of this draft, R6 has **0 full passes**. J1 is a mechanism-confirmed near-miss that is **NOT passing** because its after-cost Dow Sharpe and bootstrap result do not beat EW30; D1 is a near-miss at t=1.91 and is also **NOT passing**. E1 failed clearly, and no later idea round supplies a credible free-data route past the criterion-4 feasibility hurdle.

## Source artifacts

- [R6 decision log](../specs/r6_decisions.md), [R6 trial log](../specs/r4_trials.md), and [Holm family manifest](../specs/r6_holm_family.json).
- [D1 preregistration](../specs/r6_prereg/D1.md), [D1 results](../r6_D1/RESULTS.md), and [D1 independent reproduction](REPRO_D1.md).
- [E1 preregistration](../specs/r6_prereg/E1.md) and [E1 results](../r6_E1/RESULTS.md).
- [J1 preregistration](../specs/r6_prereg/J1.md), [J1 results](../r6_J1/RESULTS.md), and [J1 independent reproduction](REPRO_J1.md).
- [Rounds K–N](../r6_ideas/) and [O1](../r6_ideasO1.md) / [O2](../r6_ideasO2.md) screening notes.

*This draft synthesizes saved decisions and results only. It adds no return, IC, power, portfolio, bootstrap, or Holm calculations.*


## Addendum (2026-11-11): rounds P–Q and the criterion-4 feasibility bound

- **P1, overnight-return momentum:** expected Dow excess Sharpe about 0.17. Fail.
- **P2, co-movement pairs:** profits have declined since 2002. Fail.
- **P3, MAX/attention:** expected excess Sharpe about 0.15, p about 0.36. Fail.
- **P4, passive-ownership pressure:** the free data is manager-level, not index-mandate-level. Fail.
- **Q, long-short designs:** to pass criterion 4 (Sharpe above EW30, about 0.9, with Holm p < 0.05 over about 6 years), an independent audit (report_drafts/CRITERION4_BOUND_AUDIT.md) puts the requirement at a rank IC of about **0.085 for a long-only top-5** and about **0.31 for a long-short** (an earlier estimate of 0.29 for long-only was too pessimistic). Documented pressure effects in large caps are about 0.01–0.03, and the best R6 mechanism (J1) measured 0.015, about 6× below the long-only requirement.
- **Conclusion:** under free data and the fixed pass criteria, a pass is not attainable on the Dow. This is a property of the test, not a lack of search. Licensed data (FactSet, I/B/E/S or Compustat via UNSW) could open new mechanisms, but none so far suggests effects near this bound. Status: **0 passes**.

## Addendum (2026-11-11): R1, P1, and directions in progress
| Direction | Test | Result | Verdict |
|---|---|---|---|
| R1 dividend-month premium | H10–H12 | spread 0.093%/month, t 0.73, placebo p 0.23 | Fail (mechanism) |
| P1 overnight-return momentum | H13–H15 | IC −0.0147, NW t −0.75 (p 0.77); placebo p 1.0; H15 not run | Fail (mechanism) |
| K1 earnings-announcement drift | H16–H18 | IC 0.0003, NW t 0.03 (p 0.49); placebo p 0.77; H18 not run | Fail (mechanism) |
| G1 high-volume premium | H19–H21 | IC 0.0018, NW t 0.19 (p 0.42); placebo p 0.71; H21 not run | Fail (mechanism) |

Passes so far: 0. Frozen R6 variants: 7 of 30 (source: specs/r6_decisions.md; r4_trials.md also holds attempt and placebo rows). Process note: K1 needed four execution attempts and G1 two, because of runner bookkeeping bugs (Holm hash convention, helper key names, prereg path). Each crash happened before any result was printed or written, and every attempt is logged in specs/r6_decisions.md items 116–127. The holdout has not been opened.

## Addendum (2026-11-11, afternoon): workflow shift, Alpaca data, rounds S–Z
- **Workflow changes** (specs/R6_WORKFLOW_RETRO.md): a shared governance-first runner template with real-helper end-to-end tests (r4_harness/runner_template.py), and a criterion-4-first idea screen (specs/IDEA_SCREEN_TEMPLATE.md). Both answer the K1/G1 crash loops and the slow gate kills.
- **New data:** Alpaca SIP 1-minute bars and auction records (read-only, development window only). Dow phase: 17.3M bars and 330k auction events (0 failed requests; 43 close-cross dates still missing after an end-bound fix); the S&P phase is in progress. Full tick-level signed flow is infeasible (multi-TB). Alpaca history starts in 2016, so any Alpaca-based direction would have a 2016–2020-10 holdout, with 2010–2015 disclosed as a gap.
- **Rounds S–Z** (about 20 candidate families, including signed minute flow, closing auctions, intraday momentum, options, COT, fund flows, news, seasonal flows): all failed the gate. No new variant was frozen; the trial count stays at 7 of 30.
- **Criterion-4 bound re-derived independently:** a long-only top-5 Dow portfolio needs a rank IC of about 0.16 monthly (0.10 weekly, 0.08 daily) for 80% power, which is higher than the earlier ~0.085 estimate. Documented large-cap pressure effects are 0.01–0.03. This, not data access, is why nothing passes.
- **Portfolio-shape check** (report_drafts/CRITERION4_BOUND_BY_SHAPE.md): broader long-only designs (top 8/10/15, rank-weighted top half, all with active share ≥ 50%) and long-short designs lower the hurdle only to about IC 0.07 (weekly/daily) at best; long-short needs 0.17 or more. The shape of the portfolio is not what blocks a pass.
- **Rounds AA** (only mechanisms with documented large-cap IC ≥ 0.06, and event-concentrated effects): no candidates found. The casualty audit of the 38 earlier screens found none that failed only on criterion 4 (specs/r6_c4_only_casualties.md); the two AA screens also failed, for 40 in total.

- **Accuracy audit:** report_drafts/R6_FINAL_AUDIT.md checked every number against its source; its corrections are applied here. Any remaining 0.085 / 0.31 figures in the older detail sections refer to the superseded first audit.
