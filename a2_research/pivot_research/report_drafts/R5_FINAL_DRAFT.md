# R5 Final Report Draft

## Executive summary

This project tested whether short-horizon buying pressure persists or spreads through the registered Dow and cross-asset networks. None of the completed directions passed its pre-registered mechanism gate: D4 produced a significant result in the opposite direction (reversal), D5 and D6 failed, and the index-change and ETF-flow proposals failed their input-feasibility gates before outcomes. D7, the customer–supplier earnings direction, remains pending; no final holdout result is included here because the coordinator alone is authorized to run that one-shot test.

The development evidence therefore does not support a tradable network-propagation strategy at the tested horizons. This is a bounded conclusion about these definitions, data and gates; it is not proof that buying pressure never persists or diffuses in other settings. The main empirical lesson is that common-owner peer pressure at the tested weekly horizon moved opposite to the forecast, while the other tested mechanisms did not clear their registered tests.

**Terms used below:** CLV is close-location value (where the close sits between that day's high and low); an IC is the correlation between signal values and later returns, and a rank IC compares their cross-sectional ranks. NCP is the pressure score averaged across connected stocks by the specified network. A common-owner link means two stocks are held by the same disclosed institutional manager; Form 13F is the quarterly filing that reports certain managers' holdings. SIC is the industry classification code. A Newey–West t-statistic uses standard errors adjusted for serial dependence. EW30/EW5 are equal-weight benchmarks over 30 Dow stocks/five ETFs. A placebo deliberately breaks a link or timing. Holm adjustment controls false positives across the registered test family; DSR (deflated Sharpe ratio) adjusts a Sharpe for selection among multiple strategies.

**More terms:** point-in-time means using only information publicly available by the date being tested. N-PORT is the SEC form reporting fund portfolio holdings. A 12-minus-1 trend is the past 12-month return excluding the most recent month; six-minus-one is the analogous six-month measure. A raw p-value is for one test before correcting for the other registered tests; the Holm-adjusted p-value is its family-wide corrected counterpart. A bootstrap estimates uncertainty by resampling observations; a circular block bootstrap resamples short runs of adjacent dates. Active share measures how different a portfolio's weights are from its benchmark. A turnover cap limits the value traded relative to portfolio value.

## 1. Directions and status

| Direction | Registered idea | Status | What the evidence permits us to say |
|---|---|---|---|
| D1 | Retail marketable-order pressure | Not selected or tested | Earlier dossier did not establish the required free-data inputs; no outcome claim. |
| D2 | ETF creation demand through holdings | Not selected or tested in this cycle | Input access was uncertain; do not describe as failed. The later Cycle-3 ETF-flow proposal is separately marked infeasible below. |
| D3 | Mutual-fund expected flow through common owners | Not selected or tested | Data access unresolved; no outcome claim. |
| D4 | Common-owner CLV/NCP on the point-in-time 13F graph | **Failed; killed** | Primary five-session rank IC was significantly negative, opposite the registered positive prediction. No portfolio or holdout was run. |
| D5 | SIC leader-to-follower CLV | **Failed; killed** | Primary effect and within-SIC randomized comparison missed their gates. No portfolio or holdout was run. |
| D6 | Monthly 12-minus-1 Treasury-basket trend to SPY | **Failed; killed** | Primary beta was positive but weak and did not clear either the NW t or placebo percentile gate. No portfolio or holdout was run. |
| F1–F3 | Draft fallback directions | Drafts only; not frozen or tested | No outcome claims. |
| D7 / R5-N1 | Customer–supplier earnings pressure | **Pending; not ready for freeze** | Input/link gate and any eventual preregistered outcome remain pending while gate chronology and endpoint count are unresolved. The holdout-source check found zero verified edges among 373 10-Ks (`specs/r5_decisions.md`, item 30); this is a warning, not the development-gate verdict. Keep the result block below open. |
| R5-N2 | Dow index-change pressure through common-owner peers | **Infeasible before outcomes** | Three independent DJIA announcement dates were available against the fixed minimum of 20. Zero variants used. |
| Cycle 3 ETF flow | Creation/redemption pressure through ETF holdings | **Infeasible before outcomes** | Only SPY and DIA had verified daily shares histories; quarterly N-PORT holdings did not satisfy the fixed daily coverage gate. Zero variants used. |

D4–D6 exhaust the completed mechanism tests. Index-change and ETF-flow are data-feasibility failures, not negative return tests. D1–D3 and F1–F3 were not selected. No direction is represented as successful.

## 2. D4 — common-owner pressure: significant reversal

D4 used the frozen point-in-time common-owner network and asked whether five-session network close-location pressure ranked subsequent five-session Dow returns positively. On the 2020-11-27 to 2026-10-30 development sample, the primary mean rank IC was **−0.018074**, with Newey–West *t* = **−2.4195** at Bartlett lag 4 across 1,479 valid dates. This is a statistically significant result in the direction opposite to the preregistered positive persistence/propagation prediction. The registered positive-direction raw *p* is 0.992229; that one-sided value is not evidence for a positive effect. The independent reproduction matched the primary IC and *t* exactly at stored precision.

The registered graph comparisons and equivalence tests also failed their gates: degree-preserving and random-link null 95th percentiles were 0.006460 and 0.009216, respectively, both above the negative observed IC; the fixed 20-session-shift comparison was not significant; none of the three equivalence checks met its required criterion. Variant 2 was diagnostic only (IC −0.006837, NW *t* −0.7882) and cannot rescue variant 1. The graph was nearly complete among 30 names in 24 of 25 quarters, so NCP was close to a weighted market-average CLV. That density limits a literal “network transmission” interpretation; it does not turn the negative result into evidence of propagation.

D4 stopped before portfolio testing. Gross/net returns, EW30 comparison, Sharpe, drawdown, turnover, costs, active share, portfolio bootstrap and DSR are **not run**, not zero-valued results. The holdout is also not run by this worker. Decision 16 records the AAPL/TRV mapping defect and pre-outcome hold; decisions 22–26 document the corrected inputs, runner repair, negative result and independent reproduction. The coordinator should report holdout feasibility and the required with/without-DWDP comparison separately.

## 3. D5 — SIC leader-to-follower pressure: failed

D5 asked whether five-session CLV at the top 20-session dollar-volume leader in a two-digit-SIC group predicted same-sign five-session follower returns. Its input gate passed: 293/293 eligible dates had the required 11 directed pairs per date. The primary mean rank IC was **0.007455**, Newey–West *t* = **0.5644** at lag 4, one-sided raw *p* = 0.286249. It missed both the pre-registered mean-IC hurdle of 0.0183 and *t* ≥ 2.

The within-SIC permutation test also failed: the observed effect was at the 69.4th percentile, below the required 95th percentile (randomization *p* = 0.307385; null 95th percentile 0.015677). The reverse-edge and fixed 20-session-shift controls were near zero and met their control thresholds, but those controls do not establish equivalence or validate the proposed network. The 60-session sensitivity IC was 0.003702 (NW *t* = 0.2675); it was not eligible to replace the primary. D5 was killed before portfolio or holdout testing. Its net/gross performance, Sharpe, drawdown, turnover, costs, active share and DSR are not run.

Decision 9 discloses a conservative timing deviation: the SIC file has filing dates rather than EDGAR acceptance timestamps, so observations became usable on the first NYSE session strictly after the filing date. Decision 8’s DD/pre-2019 DOW lineage repair was holdout-only under the recorded ruling and did not alter the development D5 result.

## 4. D6 — cross-asset monthly trend: failed

D6 tested whether the 12-minus-1 Treasury-basket trend predicted SPY’s next monthly return after controlling for SPY’s own trend. The primary coefficient was **0.076921**, Newey–West SE 0.100374, *t* = **0.7663** at lag 11, one-sided raw *p* = 0.221736, using 62 monthly targets from August 2021 through September 2026. It failed the registered positive-coefficient/*t* gate. The observed coefficient ranked at the 94.6th percentile of the circular-shift placebo distribution, below the required 95th percentile (randomization *p* = 0.055888).

The reversed-direction primary-horizon coefficient was 0.001569 (*t* = 0.0763) and did not support the registered negative prediction. A six-minus-one sensitivity produced a positive coefficient 0.337990 (*t* = 2.6232, raw *p* = 0.004355), but this was explicitly sensitivity-only and cannot replace the failed 12-minus-1 primary. The six-minus-one reverse direction did not pass. D6 therefore stopped before its EW5 portfolio endpoint; no portfolio or holdout result exists.

Decision 12 records the adjusted-high/low scaling clarification; the signal does not rely on those fields, so the decision calls it immaterial. Decision 17 discloses that L1 accidentally ran the registered D6 tests after freeze; the official guarded L2 run matched exactly. Both log blocks are disclosed and counted once per endpoint in Holm; there was no result-selection rerun.

## 5. Infeasible directions and pending D7

**Index change.** The fixed feasibility rule required at least 20 independent DJIA announcement dates. The official-release review found three dates in the window (2024-02-20, 2024-11-01 and 2026-06-23; `r5_L3/INDEX_CHANGE_FEASIBILITY.md`). D4 graph support supplied peers for incumbent names, but entry names were not yet in the roster; graph density cannot compensate for event scarcity. The direction was ruled infeasible before outcome analysis, with zero variants used.

**Cycle-3 ETF flow.** The fixed six-fund gate required daily shares/NAV/AUM histories on at least 1,000 common sessions and point-in-time holdings on at least 80% of sessions. Only SPY and DIA had verified daily share histories (1,488 rows each, 2020-11-27 to 2026-10-30); daily histories for IVV, VOO, QQQ and IWM were not verified. SEC N-PORT provided quarterly public holdings snapshots, not the required daily historical holdings panel. The direction was ruled infeasible before outcomes; no thresholds or universe were broadened and zero variants were used (`r5_L3/CYCLE3_DATA_CHECK.md`).

**D7 — pending block for coordinator.** D7 is the customer–supplier earnings-pressure proposal. Its outcome is not supplied in the materials used for this draft, and must not be inferred from the holdout source check. Insert the dated input-gate verdict, frozen specification/hash and any authorized mechanism/placebo results here only after the coordinator confirms the gate chronology and the final endpoint manifest. If the gate fails, say “infeasible before outcomes” and report zero variants; if it passes, report every registered endpoint and the stop/advance rule. No D7 portfolio or holdout result is asserted here.

## 6. Complete Holm family: 21 endpoints

The interim correction uses the frozen 21-endpoint family: nine D4, six D5 and six D6 endpoints. It applies Holm step-down to all 21 raw values, assigning **p=1 only as an interim bookkeeping value** to the three unrun portfolio endpoints. Those p=1 entries are not observed p-values. D6’s accidental and official duplicate log rows count once per registered endpoint. No endpoint is dropped because it failed, was a sensitivity, or was not run.

| Endpoint | Test | Raw p / status | Interim Holm p |
|---|---|---:|---:|
| D4-1 | V1 primary NCP rank IC, positive | 0.99222889 | 1.00000000 |
| D4-2 | Degree-preserving comparison | 0.95608782 | 1.00000000 |
| D4-3 | Random-link comparison | 0.97804391 | 1.00000000 |
| D4-4 | Fixed 20-session-shift comparison | 0.73387050 | 1.00000000 |
| D4-5 | Degree-placebo equivalence | 0.48573705 | 1.00000000 |
| D4-6 | Random-link-placebo equivalence | 0.17794169 | 1.00000000 |
| D4-7 | Shifted-placebo equivalence | 0.91798249 | 1.00000000 |
| D4-8 | V2 mean rank IC, positive | 0.78471021 | 1.00000000 |
| D4-9 | V1 net excess vs EW30, block bootstrap | Not run; p=1 assigned for interim correction | 1.00000000 |
| D5-1 | V1 follower mean rank IC, positive | 0.28624857 | 1.00000000 |
| D5-2 | Reverse-edge mean IC | 0.93947879 | 1.00000000 |
| D5-3 | Within-SIC permutation comparison | 0.30738523 | 1.00000000 |
| D5-4 | Fixed 20-session-shifted graph | 0.76020789 | 1.00000000 |
| D5-5 | V2 60-session sensitivity mean IC | 0.39452692 | 1.00000000 |
| D5-6 | V1 net excess vs EW30, block bootstrap | Not run; p=1 assigned for interim correction | 1.00000000 |
| D6-1 | 12–1 Treasury to SPY beta, positive | 0.22173578 | 1.00000000 |
| D6-2 | 12–1 SPY to Treasury beta, negative | 0.53039291 | 1.00000000 |
| D6-3 | Primary vs circular-shift placebo | 0.055888224 | 1.00000000 |
| D6-4 | 6–1 Treasury to SPY sensitivity | 0.0043550034 | 0.09145507 |
| D6-5 | 6–1 SPY to Treasury sensitivity | 0.87945218 | 1.00000000 |
| D6-6 | Net excess vs EW5 | Not run; p=1 assigned for interim correction | 1.00000000 |

No endpoint has interim Holm-adjusted *p* < 0.05. The smallest is D6-4 at 0.09145507; it is a sensitivity, not a primary pass, and does not change D6’s failure. These values are the interim family table; the coordinator owns any final update if the authorized endpoint manifest changes. DSR’s fixed trial count is a separate quantity and is not the Holm endpoint count.

## 7. Trial and variant accounting

The goal-wide budget and DSR setting are fixed at **30 variants/trials** (`specs/r4_trials.md`, heading and trial log). The log has **23 numbered entries**: D5 rows 1–5, D6 rows 6–15, and D4 rows 16–23. D6 rows 6–10 and 11–15 are duplicate accidental/official records of the same five endpoints. Thus, the log documents 18 distinct computed endpoint/test entries after that duplicate block is counted once; it does **not** itself provide a unique strategy-variant tally because it mixes primaries, placebo/control tests, and sensitivity tests. Do not equate 23 log rows or 21 Holm endpoints with 23 or 21 variants. The separately stated 7 (or hypothetical 8 including D7) candidate-variant count is not traceable to a unique-variant field in `specs/r4_trials.md`, so it is omitted here pending an authoritative row-to-variant reconciliation. The log explicitly records zero variants for the infeasible index-change and ETF-flow proposals (decisions 27 and 31 in `specs/r5_decisions.md`). The DSR input remains 30, not the observed row or endpoint count.

## 8. Reproduction checks

Independent reproduction scripts read development inputs only and did not access holdout data. D4’s independent reconstruction exactly matched the saved primary IC (−0.0180739987) and Newey–West *t* (−2.4194916), over 1,479 finite IC dates. D5’s independent mean IC (0.007455133611) and lag-4 *t* (0.5643776624) matched the runner; D6’s independent primary beta (0.07692125109) and lag-11 *t* (0.7663441562) also matched. D5 and D6 freeze hashes were verified; the D4 report records its verified frozen hash. D5/D6 runner settings checked against their frozen specifications matched the reported horizons, lag lengths and placebo settings.

The D4 record discloses that a preflight stopped before endpoint statistics at an old NCP check, then the corrected run generated D4-1 through D4-8 once; a later formatting error was fixed from saved JSON without recomputing outcomes. The independent D4 review found those eight rows logged once, with D4-9 not run. The D5/D6 reproduction notes stale introductory status lines in the frozen files; hashes and freeze checks were nevertheless valid. Preserve these procedural facts in the audit trail rather than implying the reproduction independently proves the input panel is error-free.

## 9. Decisions and disclosed deviations (items 8–31)

| Decision | Disclosure carried into the report |
|---:|---|
| 8 | SIC issuer/ticker lineage errors for DD and pre-2019 DOW affect holdout construction only under the recorded ruling; L4 must repair/audit CIK and ticker intervals before holdout. The D5 development universe/result is unchanged. |
| 9 | SIC panel has filing dates but no acceptance timestamps; use the first NYSE session strictly after filing date. This is later and conservative; disclose as a timing deviation. |
| 10 | D4 was not to be frozen before the complete point-in-time top-50 roster and rebuilt inputs/QA. Later freeze and input-defect decisions supersede the earlier hold. |
| 11 | D5 primary failed (mean IC about 0.00746, NW *t* about 0.56; below 0.0183 and *t*≥2); permutation comparison failed; kill D5 without rescue. Activate D6 as pre-ordered fallback. |
| 12 | D6 adjusted high/low are scaled by the daily adjusted-close/close factor to match adjusted-open convention. Recorded as an immaterial clarification because the signal does not use those fields. |
| 13 | D6 frozen after input QA; endpoints 1–6 entered the Holm manifest. |
| 14 | D4 frozen after roster/input QA; 9 endpoints completed the 21-endpoint Holm family. Dense 378-link counts were first accepted as diagnostic; subsequent input defect ruling supersedes that interpretation until repair. |
| 15 | D4/D6 SHA-256 values were initially computed on paths, not file contents. Coordinator recomputed content digests on unchanged specs before outcomes; no analysis rule changed. |
| 16 | Red-team found AAPL and TRV lacked mapped 13F positions; D4 was put on hold with no result until L4 repaired mappings and L1 rebuilt inputs. The eventual frozen-spec run followed; disclose the pre-outcome input correction. |
| 17 | L1 accidentally ran frozen D6 registered tests. Results were preserved; official guarded L2 run matched exactly. Both log blocks stay visible but count once for Holm; no result-selecting rerun. |
| 18 | Cycle 2 proposal D7 is customer–supplier earnings pressure; L1 owns the input-only Dow/customer-supplier link coverage gate. |
| 19 | Accidental D6 rows remain in the trial log beside official rows; duplicate endpoints count once in Holm. |
| 20 | Official D6 replicated the accidental run and failed; D5 and D6 killed, D4 initially held for mapping correction, D7 in preparation. Later decisions update D4 status. |
| 21 | Independent D5/D6 reproduction confirmed the primary statistics; see reproduction section. |
| 22 | Corrected D4 graph was complete among 30 names in 24/25 quarters, making NCP close to weighted market CLV; disclosed as design weakness. L2 assigned mechanism test. |
| 23 | D4 runner initially omitted endpoints 5–8, used 3×E rather than 10×E swaps, and had seed handling mismatch. L2 repaired to frozen spec, added synthetic checks and documented diff before outcome; no spec change. |
| 24 | L4 corrected post-2023 13F value units; D4 bundle rebuilt before its single mechanism run. |
| 25 | D4 primary mean IC −0.01807, NW *t* −2.42: significant reversal opposite registered positive sign. D4 killed; no sign flip/rescue; cycle 1 had zero passes. |
| 26 | Independent D4 reproduction matched (IC −0.01807, *t* −2.42); D4 endpoint rows 1–8 appear once. |
| 27 | Index-change direction infeasible: 3 independent announcement dates versus minimum 20; no outcome test and zero variants. D7 link task was re-dispatched. |
| 28 | D7 gate chronology anchor recorded at 2026-11-10T14:18:48Z before LINKS.csv existed; later readiness audit found unresolved chronology/hash and endpoint-count issues. Do not claim D7 frozen or gate-passed absent coordinator resolution. |
| 29 | Cycle-3 ETF creation/redemption proposal is used only if D7 fails; estimated success chance was 5%; its input-only data check found it infeasible. |
| 30 | Holdout-source D7 check found zero verified customer–supplier edges among 373 10-Ks; L4 was to check XBRL concentration-risk tags as a second free source. This is a warning and not a substitute for the development gate. |
| 31 | ETF-flow direction failed its input gate: daily share history only for SPY and DIA; N-PORT quarterly. No outcomes or variants. If D7 also fails/is infeasible, stop rule applies; all three cycles are exhausted and final report should state the stop. |

The separate accidental DWDP exposure incident in `specs/r4_trials.md` remains disclosed: L4 saw rendered historical DWDP OHLCV rows during an availability check but computed or used no values; L4 was excluded from later hypothesis, preregistration and implementation work. The coordinator must still report the prescribed holdout comparison with and without the DWDP membership window.

## 10. Holdout and portfolio reporting

No worker-side holdout result is included. The coordinator has the single authorized run on Dow 2010-01 to 2020-10, must disclose all coverage gaps (including KFT, DWDP, WBA and UTX→RTX lineage), use the available-name equal-weight benchmark, and report the required DWDP-window inclusion/exclusion sensitivity. D5 and D6 did not advance to holdout; D4’s corrected development mechanism failed. Do not imply a holdout confirmation or generalization result where none exists.

| Direction | Development portfolio | Holdout |
|---|---|---|
| D4 | Not run after mechanism gate failed | Coordinator-only; report authorized status/result and gaps |
| D5 | Not run after mechanism gate failed | Not run after development failure |
| D6 | Not run after mechanism gate failed | Not run after development failure |
| D7 | Pending authorization and gate | Coordinator-only if eventually preregistered and advanced |
| Index-change / Cycle-3 ETF flow | Not run; infeasible inputs | Not run |

No portfolio return, Sharpe, drawdown, turnover, realized cost, active share, bootstrap performance inference or DSR estimate is available for D4–D6 because their mechanism gates failed before portfolio formation. The DSR trial-count input is fixed at 30; this is not a reported DSR statistic.

## 11. Conclusion

The tested approaches did not establish a positive, tradable network-pressure effect. D4 is especially informative: at the registered weekly horizon its primary association was significantly negative, consistent with short-term reversal in this sample rather than persistence or network propagation. D5’s industry-leader signal did not clear the effect, t-statistic or randomized-link criteria, and D6’s monthly cross-asset primary did not clear its coefficient and placebo gates. The index-change and ETF-flow proposals could not be tested under their precommitted input requirements.

These findings do not refute Advik’s broad idea that buying pressure can persist or spread under some conditions. They show that the tested proxies and networks did not provide the required evidence in the Dow development sample, and the common-owner network result went the other way. The report should state **zero completed approaches passed**, keep D7 explicitly pending until its gate and endpoint issues are resolved, and avoid turning sensitivities, feasibility failures, or unrun portfolio endpoints into evidence of success. Any holdout statement belongs to the coordinator’s one-shot analysis and must be reported with its gaps and DWDP sensitivity.
