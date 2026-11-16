# D1 pre-freeze red-team review

**Verdict: FIX-THEN-READY. Do not freeze or open outcomes until the fixes below are entered and the input-only price gate is resolved.** The registered hypothesis and one-variant limit are coherent, and the FINRA flow coverage is strong. The current D1 text nevertheless treats facility short-sale volume too much like a consolidated-market pressure measure, assumes a next-open execution without a publication timestamp, and uses a lead-score equivalence placebo that is poorly matched to a persistence hypothesis.

This review used only `specs/r6_prereg/D1.md`, `r6_D1/COVERAGE.md`, `r6_D1/POWER.md`, their input-only summaries, and public documentation/papers. No prices, returns, holdout values, or outcomes were inspected or calculated.

## Findings and exact required fixes

### 1. Timing and tradability — fix before freeze

FINRA says the daily file is posted “within a reasonable amount of time” after regular trading hours; that language does not guarantee it is available before the next session's open. The source is explicitly an after-close file. The historical raw files do not provide per-file publication timestamps, so the draft cannot demonstrate that an order at the next open could have used that day's signal. See [FINRA's 2009 publication notice](https://www.finra.org/sites/default/files/NoticeDocument/p120044.pdf).

**Exact fix:** use a fixed one-session execution delay: form `R[i,t]` after close `t`, submit the first eligible trade at the open of session `t+2`, and define the five-session forward return as adjusted close at `t+6` divided by adjusted open at `t+2`, minus one. Update all timing language, formulas, date eligibility, return-window references, and portfolio start dates consistently. State that this is a conservative delayed-use convention because historical file-posting timestamps are unavailable; do not describe `t+1` open as verified tradable. Keep the signal values anchored at `t` and do not shift or backfill them.

### 2. Numerator, denominator, and interpretation — clarify before freeze

The ratio's matching numerator and denominator rule is sensible: aggregate only over the same valid facility rows/market labels, use `ShortVolume / TotalVolume`, and do not add `ShortExemptVolume` a second time. FINRA's [data guide](https://www.finra.org/sites/default/files/2020-12/short-sale-volume-user-guide.pdf) defines `ShortVolume` as executed short-sale **and short-sale-exempt** volume; `ShortExemptVolume` is the exempt subset. Thus the preregistration must say expressly that short-exempt volume is already included in `ShortVolume`, and is reported separately only for diagnostics. Do not subtract the subset either.

The larger problem is the name. “Consolidated NMS” can be mistaken for the national consolidated tape. FINRA's [2019 notice](https://www.finra.org/sites/default/files/2019-07/information-notice-051019.pdf) says these files cover public-dissemination trades reported to FINRA facilities and are not consolidated with exchange data. `TotalVolume` is therefore the FINRA-facility denominator, not all-market consolidated volume. Replace every description implying a market-wide ratio with **“FINRA CNMS facility short-volume ratio (FINRA-reported public-dissemination volume only)”**. Keep the limitation that this is transaction flow, not net short positioning, and avoid presenting it as direct buying pressure.

**Exact fix:** add under the formula: “FINRA `ShortVolume` already includes short-exempt sales; `ShortExemptVolume` is its subset and is never added or subtracted. `TotalVolume` is volume in the same FINRA-reported facility rows, not consolidated national volume.” Preserve the existing paired-row mask and zero-imputation prohibition.

### 3. Direction and evidence — retain sign but narrow the claim

The sign is internally consistent with the cited evidence: the registered score is `P=-R`, so a positive `P` IC means lower reported short-sale flow is associated with higher subsequent returns; equivalently, a high short-flow ratio predicts lower returns. Wang, Yan and Zheng report that shorting flows remain a significant predictor of negative future returns during 2010–2015, including value-weighted results ([JFE article](https://doi.org/10.1016/j.jfineco.2019.05.018); [article page](https://www.sciencedirect.com/science/article/pii/S0304405X19301436)). Diether, Lee and Werner report predictability in daily short-selling activity but find that transaction costs can erase strategy profits ([RFS article](https://doi.org/10.1093/rfs/hhn047)). These do not validate this exact FINRA facility ratio, its five-day mean, a Dow-only portfolio, or post-2015 persistence; Wang et al. also warn that abnormal short-term flow increases do not predict returns.

**Exact fix:** label this an **inverse FINRA short-sale-flow** hypothesis, not a direct measure of net bearish positions or buying pressure. Keep the single registered negative `R` / positive `P` sign. Keep the cited caveats and do not use the cited papers as evidence that the proposed implementation itself works.

### 4. Placebos — replace the lead-score equivalence gate

The date-wise cross-sectional shuffle is a useful null, but a full-universe shuffle destroys industry structure. A significant result could reflect sector return/flow structure rather than name-specific short-flow information. Make this a **within-date, within-two-digit-SIC-group** shuffle (only groups with at least two eligible names are permuted; singleton scores stay fixed), preserving each group's signal distribution. Declare the number of eligible names/groups and the singleton treatment before outcomes.

The fixed `P[t+5]` versus return-after-`t` placebo is not a clean “no effect” test for a persistence thesis. The measured signal itself is highly persistent: the report gives median name-level ACF1 of 0.5567 (S&P) and 0.6065 (Dow), and universe-mean ACF1 of 0.8535 and 0.6885. A future score can therefore proxy for the current score and predict the same return window even when the true signal is available at `t`; equivalence to zero is not a defensible null. Conversely, if it passes equivalence, that may simply show the score has little persistence. FINRA's volume series is not position data, so the signal persistence alone does not resolve this.

**Exact fix:** replace the cross-sectional shuffle with the SIC2-stratified shuffle above. Remove the five-session future-score equivalence condition as a hard gate and from the Holm family; it may be reported as a clearly labeled descriptive lead diagnostic, without a pass/fail threshold and without being used to rescue the primary. Keep one inferential placebo only: the stratified shuffle with the already stated 500 draws, fixed seed, null distribution, and one-sided randomization p-value. Do not replace the removed test with another arbitrary time shift; with the reported signal persistence, a lead-score near-null requirement is not a suitable falsification test.

### 5. Power, hurdle, and turnover — numbers are reproducible but claims must be narrowed

The coverage report has 1,614 sessions from 2020-06-01 through 2026-10-30, all files present, zero missing dates/download failures, and 8,193–12,462 issue rows per daily file (569,204,908 raw bytes). The development power window is 1,488 sessions (2020-11-27 through 2026-10-30). The SIC2 stress results are: S&P minimum/median groups 53/54, assumed IC SD 0.138675, effective N 376.7, 80% MDE 0.02030, simulated power 0.631 at IC 0.0183 and 0.825 at 0.026; Dow groups 18/19, assumed IC SD 0.242536, effective N 492.5, MDE 0.03106, power 0.412 and 0.619 respectively. These exact figures are in `r6_D1/POWER.md`.

The SIC stress derives SD as `1/sqrt(G−1)` using the minimum number of two-digit SIC groups, which is preferable to treating every ticker as independent. But it is still a scenario, not established conservative power: industry groups have unequal sizes and can be correlated, while the temporal stress uses **signal** ACF rather than autocorrelation of the future date-level IC. The larger S&P power is only around 63% at 0.0183, and Dow power is weak throughout the stated range. Do not call the test “adequately powered” without qualification or treat a non-rejection as evidence that the effect is absent.

The stated `0.0043301` is a cost-only approximate break-even conversion under assumed weekly return dispersion 4%, total buys-plus-sells turnover 50%, 5 bp per dollar traded, and top fraction 5/30. At the cap, assumed cost is `0.50 × 0.0005 = 0.00025` NAV, or 2.5 bp per rebalance. The conversion implies gross active return of about `0.04 × 1.587 × 0.0043301 = 0.000275` NAV, about 2.75 bp; it leaves only about 0.25 bp before costs and is not a 25%-of-gross-cost hurdle. It is therefore a thin, assumption-dependent floor, and a S&P cross-sectional IC is not itself a guarantee that the Dow top-five portfolio earns that gross edge.

**Exact fix:** retain `0.0043301` only as the explicitly named *cost-only planning floor*, not as a proven net-return hurdle or evidence that the top-five implementation has enough edge. State that the economic portfolio gate remains positive net excess return after costs and that realized cost/gross-edge is reported. If the team wants the stronger alternative cost rule `costs < 25% of gross edge`, then under the same 2.5 bp cost assumption gross edge must be at least 10 bp, implying planning IC about `0.010 / (0.04 × 1.587) = 0.01575`; make clear this is a separate sensitivity, not an outcome-selected replacement threshold. Keep the portfolio's transition rule: from current weights, move pro rata toward the top-five target only as far as total buys-plus-sells/NAV is at most 50% at every rebalance. This is a valid ex-ante way to satisfy the turnover-cap route; with EW30 to top-five, the initial unconstrained transition is 166.7% total turnover, so the cap will bind. Report its realized turnover and costs. No high-turnover uncapped version should be added.

### 6. Multiplicity and variant count — mostly sound, one Holm repair

D1-V1 is the only strategy variant; this meets the three-variant maximum. Placebo permutations and bootstrap draws are not variants. The four listed endpoints are all directed in advance, and logging D1-V1 before outcomes is appropriate. The frozen family must remain cumulative across R6, not be reset for D1.

**Exact fix:** after removing the invalid future-score equivalence gate, list only the primary mechanism, the SIC2-shuffle placebo, and the Dow net-excess endpoint in the Holm family. Because later endpoints are conditionally not run, predeclare their fixed family slots and set an unrun slot to conservative `p=1` **for Holm adjustment only**, while reporting it as “not run; no raw p-value.” Otherwise the draft's “complete cumulative family” rule is underspecified when endpoints are blocked. Record the count of unique R6 variants and manifest row mapping for DSR; do not count placebo shuffles as strategy variants.

### 7. Coverage and holdout feasibility — input coverage passes, joint gate does not

Insert these exact FINRA coverage values into the D1 placeholders:

| Placeholder | Value to insert |
|---|---:|
| FINRA date span / expected sessions | 2020-06-01 to 2026-10-30 / 1,614 |
| Files present / missing / failed | 1,614 / 0 / 0 |
| Rows per file / total raw download | 8,193–12,462 / 569,204,908 bytes |
| S&P expected roster member-days / matched paired-ratio member-days | 812,848 / 812,099 |
| S&P total coverage / mean daily coverage | 99.9079% / 99.9078% (report as 99.91%) |
| S&P median daily coverage / full dates | 100.0% / 892 of 1,614 |
| S&P minimum | 501/503 = 99.60%; 722 dates are incomplete |
| Dow expected / matched member-days | 48,420 / 48,420 |
| Dow daily coverage / full dates | 100% / 1,614 of 1,614 |
| S&P / Dow signal ACF stress inputs | 0.853545 / 0.688463 |
| S&P / Dow SIC2 min/median groups | 53/54 / 18/19 |
| S&P / Dow IC SD stress | 0.138675 / 0.242536 |
| S&P / Dow effective N | 376.7 / 492.5 |
| S&P / Dow 80% MDE | 0.02030 / 0.03106 |
| S&P power at IC 0.0183 / 0.026 | 0.631 / 0.825 |
| Dow power at IC 0.0183 / 0.026 | 0.412 / 0.619 |

These coverage figures are FINRA flow matches only. They do **not** clear the joint FINRA-plus-price member-day gate or the price/lineage gate: the current `r6_data/QA.md` still reports 54 S&P ticker histories missing. Do not change that status to pass until L4 provides the hashed OHLCV repair/lineage and a complete input-only joint coverage calculation. If price completeness cannot be repaired, fail the S&P gate before outcomes rather than using a survivor subset.

For the sealed holdout, the prereg's availability-only framing is appropriate, and this review has not inspected any holdout files. Replace the stale implication that the D dossier's single 2010 row-count check is sufficient with the specific L4 status: **L4 is storing the sealed FINRA 2010–2020 files; coordinator may check only the storage manifest, date/file counts, sizes and hashes before freeze, without opening rows or computing ratios/signals.** The coverage report for this task deliberately begins 2020-06-01 and does not establish holdout ticker coverage. The coordinator must still disclose holdout flow availability/manifest status, and after the one authorized run report numerator/denominator coverage or infeasibility. Do not ask workers to read those files.

## Paper and data references

- FINRA, [Daily Short Sale Volume Files](https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files) and [Short Sale Volume Data User Guide](https://www.finra.org/sites/default/files/2020-12/short-sale-volume-user-guide.pdf).
- FINRA, [Information Notice 5/10/19](https://www.finra.org/sites/default/files/2019-07/information-notice-051019.pdf), scope and limitations of short-volume data.
- Diether, Lee & Werner (2009), [Short-Sale Strategies and Return Predictability](https://doi.org/10.1093/rfs/hhn047), *Review of Financial Studies*.
- Wang, Yan & Zheng (2020), [Shorting Flows, Public Disclosure, and Market Efficiency](https://doi.org/10.1016/j.jfineco.2019.05.018), *Journal of Financial Economics*.

## Freeze decision

**FIX-THEN-READY:** apply the execution-delay, ratio-label/subset, sign-language, placebo, and Holm-family fixes above; paste the exact flow coverage and power values; retain the price-coverage gate as pending until L4 resolves it; and update holdout feasibility to cite L4's storage manifest without inspecting sealed rows. Then freeze and hash the corrected file before any outcome access. The design must remain one strategy variant and must report all gates, including failures.
