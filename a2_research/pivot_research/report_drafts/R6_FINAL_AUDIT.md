# R6 Final Report Audit

**Scope and method.** I audited every numerical claim in `R6_FINAL.md` against the available run result bundles and result reports, `specs/r6_holm_family.json`, `specs/r4_trials.md`, frozen preregistration SHA footers and run hashes, `specs/r6_decisions.md`, and the current criterion-4 audits. I recomputed the final family with the real `r4_harness.phase3.holm_correction` helper. I did not read or calculate any sealed-holdout returns, signals, or outcomes; this is an audit of existing development results only.

## Corrections required

| `R6_FINAL.md` location | Reported value | Correct value / treatment | Source and reason |
|---|---|---|---|
| Lines 3, 39, 182–188: report status and decision-log span | “updated after rounds S–U”; full log items 1–138; round overview ends at U | Update the status to include through round AA and log items **1–173**. The content already includes later material through AA; the header and overview are stale. | `specs/r6_decisions.md`, items 145–173 (file currently ends at item 173). |
| Lines 81–82, 109–110, 123–124, 129–130: H1, H2, H7, H8 Holm-adjusted p | H1 **0.169170**, H2 **0.017964**, H7 **0.132292**, H8 **0.017964** | For the final 21-slot R6 family: H1 **0.507510**, H2 **0.041916**, H7 **0.359078378**, H8 **0.041916**. Replace every repeated interim value in the detailed tables. | Recomputed `phase3.holm_correction` on the 21 raw p-values in `specs/r6_holm_family.json`. The old numbers belong to an earlier, smaller family. The top-line H1–H21 table at lines 25–35 is already correct to its shown precision. |
| Lines 43 and 169: criterion-4 top-five requirement | Long-only top-5 IC about **0.085**; line 169 says long-short about **0.31** | Replace with the current 80%-power synthetic hurdle by cadence: top-5 long-only **0.157 monthly / 0.099 weekly / 0.077 daily**; long-short **0.490 monthly / 0.283 weekly / 0.197 daily**. Thus J1's weekly IC ≈0.0148 is about **6.7×** below the weekly top-5 bound, not “6× below 0.085.” | `report_drafts/CRITERION4_BOUND_VERIFY.md`, table “Estimated IC hurdle”; decision-log item 163 gives rounded versions. The 0.085 / 0.31 numbers are from the superseded `CRITERION4_BOUND_AUDIT.md`. These are design estimates, not realized outcomes. |
| Line 184: Alpaca auction sample size | **323k** auction rows | **330k auction events**, 0 failed requests, and **43 missing close-cross dates** after the end-bound fix. | `specs/r6_decisions.md`, item 170. Item 161 records the earlier pre-fix 323k count; final report should use the corrected count and disclose the remaining missing dates. The 17.3M bar count is consistent with the decision log's 17.27M (rounded). |
| Line 188: casualty-screen count and source attribution | “Across **40** idea screens” attributed to `specs/r6_c4_only_casualties.md` | Separate the evidence: the casualty audit covers **38** earlier screens and found none failing only criterion 4; the later AA literature and event screens (items 171–172) both also failed. The combined **40** is derivable as 38 + 2, but is not the count reported by the casualty audit itself. | `specs/r6_c4_only_casualties.md` / decision-log item 167, plus items 171–172. Keep “40” only if described as this combined count, not as a direct citation to the 38-screen audit. |

## Holm recomputation

The manifest contains 21 slots. Only H2 and H8 remain below 0.05 after Holm adjustment; this agrees with the report's sentence at line 37. The full recomputed adjusted values are:

| Endpoint(s) | Raw p | Final Holm p |
|---|---:|---:|
| H1 | 0.028195 | 0.507510 |
| H2 | 0.001996 | 0.041916 |
| H3, H6, H12, H14, H15, H18, H21 (not run / placeholder) | 1.000000 | 1.000000 |
| H4 | 0.595093 | 1.000000 |
| H5 | 0.812375 | 1.000000 |
| H7 | 0.018898862 | 0.359078378 |
| H8 | 0.001996008 | 0.041916 |
| H9 | 0.449110178 | 1.000000 |
| H10 | 0.234995 | 1.000000 |
| H11 | 0.227545 | 1.000000 |
| H13 | 0.771461473 | 1.000000 |
| H16 | 0.489807071 | 1.000000 |
| H17 | 0.768463074 | 1.000000 |
| H19 | 0.423747331 | 1.000000 |
| H20 | 0.710578842 | 1.000000 |

The helper's `reject` flag is true only for H2 and H8. The run-local D1/E1/J1/R1/P1 Holm figures are not interchangeable with the coordinator's final manifest-wide adjustment.

## Checks that agree with the source

- **Headline mechanism and placebo values (lines 11–17):** D1's mean IC 0.0093742, NW t 1.9080 and placebo p 0.001996; E1's −0.00454295, −0.2407 and 0.812375; J1's direction-adjusted mean IC 0.014786333, t 2.077042 and placebo p 0.001996008; R1's spread 0.000933 per month, t 0.726883 and placebo p 0.227545; P1's mean IC −0.014713818, t −0.747875 and placebo p 1; K1's rounded 0.0003 / 0.03 / 0.77; and G1's rounded 0.0018 / 0.19 / 0.71 all agree with their result reports or decision-log entries at the precision shown. The p≈0.42 for G1 and p≈0.49 for K1 are also consistent with decision items 126 and 128.
- **J1 portfolio (lines 111–115):** the JSON reports net excess 1.0276%, gross excess 14.9105%, strategy cost 10.3567%, net Sharpe 0.823179 vs EW30 0.902267, average turnover 48.1737%, maximum turnover 50%, active share 54.7681%, bootstrap p 0.449110 and DSR 5.23316e−209 using trial count 3. The report's rounded values agree. The independent replay mismatch (−2.66% cumulative net excess vs official +1.03%) is explicitly disclosed at line 115 and is correctly marked unreconciled.
- **Updated criterion-4 figures (line 186):** 0.16 monthly / 0.10 weekly / 0.08 daily correctly round the verification report's 0.157 / 0.099 / 0.077. Line 187's “about 0.07” lowest weekly/daily hurdle is a coarse summary of the shape study (rank-weighted top-half weekly 0.074; top-15 daily 0.070), and “0.17 or more” is consistent with its long-short results. Line 170's zero-pass conclusion is consistent with the current decision log through item 172.
- **Historical gate figures (lines 55–69):** the cited B4 power 41% at IC 0.01; C1 SIC3 power 32% at IC 0.0183; D1 S&P cluster power 63% at IC 0.0183 and realized t=1.908; G-round MDE 0.036; H-round breadth of about 11 clusters; I-round 59 monthly observations; J-round 26.7% power at IC 0.0183 / MDE 0.0392; K-round 11–15% power; N-round below 14% power at IC 0.02 / MDE 0.10–0.14; and O1 Sharpe 0.75 are consistent with the cited decision-log entries (items 12, 31, 27, 39, 44–46, 75 and 78) and the linked idea dossiers. Decision 79 likewise supports the earlier 14-round / three-execution-stage statement at line 139; it is a historical snapshot and should not be presented as the current search status. The line-39 failed-ideas summary stops at U and should be extended through V–AA if intended as a complete current-round inventory.
- **Attempt counts and frozen-variant count:** K1's four attempts and G1's two attempts are recorded in decision items 116–127; 7 frozen R6 variants and the 30-variant cap are recorded in items 112 and 128. However, `specs/r4_trials.md` has 27 numbered rows, includes failed attempts and sensitivity/placebo rows, and does not list the complete R6 frozen set. It therefore cannot independently substantiate a goal-wide “7 of 30” count. Cite the decision log as the source and clarify that this is the R6 count, not a count inferred from the R4 row numbers.

## Frozen hashes and audit limits

The SHA256 footer strings in `specs/r6_prereg/{D1,E1,J1,R1,P1,K1,G1}.md` agree with the prereg digests recorded for the five available execution bundles (D1, E1, J1, R1, P1), and with the coordinator's freeze entries for all seven. The K1 and G1 prereg files and freeze digests exist, but no K1/G1 result JSON or `RESULTS.md` is present in the inspected paths; their reported mechanism values are supported by decision items 126 and 128 rather than a durable result bundle. The report should say so, or add the missing artifacts if they exist elsewhere.

The audit did not find a numerical discrepancy in the high-level 21-slot Holm table, the displayed frozen-run headline estimates, the J1 portfolio figures, or the current zero-pass conclusion. The concrete edits are the stale Holm values in the detailed H1–H9 tables, superseded criterion-4 bounds, stale report/log span, corrected Alpaca auction count, and precise attribution of the 38-versus-40 screen count; the R6 trial count's ledger provenance should also be clarified.

