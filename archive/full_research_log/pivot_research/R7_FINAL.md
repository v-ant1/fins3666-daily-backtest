# R7 Final Report

**As of 2026-11-11, about 21:00 AEDT. Result: 0 validated strategies.** No strategy passed all five criteria in R6, and no new R7 experiment was run. A promising but failed candidate (J1) is reported as failed, not as validated.

Workflow: `R6_WORKFLOW_REVIEW_BRIEF.md` (the user-revised R7 workflow). Decision logs: `specs/r6_decisions.md` (items 1–222) and `specs/r7_decisions.md`.

## 1. Pass/fail table

All seven strategies were frozen (dated and hashed) before any result was seen, and each was run once. Trading universe: Dow 30, 2020-11 to 2026-10, benchmark EW30.

| Strategy | Idea | Signal test (IC, NW t) | Placebo p | Portfolio vs EW30 (after 0.05%/side) | Holdout | Verdict |
|---|---|---|---|---|---|---|
| J1 | Weekly industry-relative reversal | 0.0148, t 2.08 (passed) | 0.002 (passed) | Net excess +1.03%; Sharpe 0.82 vs 0.90; p 0.45 | Not opened | **Failed** (criterion 4) |
| D1 | Daily FINRA short-volume pressure | 0.0094, t 1.91 | 0.002 | Not run | Not opened | **Failed** (t < 2; near-miss) |
| E1 | Monthly industry-peer close-location pressure | −0.0045, t −0.24 | 0.81 | Not run | Not opened | Failed |
| R1 | Dividend-month premium | t 0.73 | 0.23 | Not run | Not opened | Failed |
| P1 | Overnight-return momentum | −0.0147, t −0.75 | 1.0 | Not run | Not opened | Failed |
| K1 | Earnings-announcement drift | 0.0003, t 0.03 | 0.77 | Not run | Not opened | Failed |
| G1 | High-volume return premium | 0.0018, t 0.19 | 0.71 | Not run | Not opened | Failed |

- **Multiple testing:** the R6 Holm family has 21 tests. After adjustment, J1's signal test has p = 0.36 and D1's has p = 0.51. The only adjusted p-values below 0.05 are the two placebo checks (D1, J1).
- **Validated:** none.
- **Preliminary evidence:** J1's weekly reversal signal is real in development data but too small to survive costs. D1's short-volume signal points the right way but misses t ≥ 2.
- **Failed hypotheses:** E1, R1, P1, K1, G1, plus about 70 idea families rejected at the screening stage (`specs/r6_screened_index.md`).

## 2. Why candidates failed

The binding constraint is criterion 4, the portfolio test against EW30 after costs and Holm correction.

- For a long-only Dow portfolio to have 80% power, the signal needs a rank IC of about **0.16 monthly, 0.10 weekly or 0.08 daily** (top 5). Even the cheapest shape (rank-weighted top half) needs about **0.07**.
- Published large-cap pressure effects are about **0.01–0.03** (`specs/r7_effect_sizes.md`).
- J1 shows the gap in practice. Its signal earned about +14.9% gross over EW30, but weekly trading cost about 10.4%, leaving +1.0% and a lower Sharpe than simply holding EW30.

Sources: `report_drafts/CRITERION4_BOUND_VERIFY.md`, `report_drafts/CRITERION4_BOUND_BY_SHAPE.md`.

## 3. Dow 30 vs S&P 500 (R7 universe check)

R7 tested on paper whether a larger trading universe makes a pass reachable (`report_drafts/R7_POWER_GATE.md`, `R7_POWER_GATE_STRESS.md`, `report_drafts/R7_UNIVERSE_COMPARISON.md`).

| | Dow 30 | S&P 500 (point-in-time, vs equal-weight S&P) |
|---|---|---|
| Cheapest qualifying shape | Rank-weighted top half | Weekly rank-weighted top half, turnover capped |
| IC needed for 80% power | ~0.07 | ~0.028 (only if the signal is slow, weekly persistence ≈ 0.8) |
| Power at IC 0.020 / 0.025 / 0.030 | very low | 27% / 63% / 89% |
| Gate verdict | NO-GO | Narrow conditional GO |
| Tested? | Yes (R6) | **No** |

**Why the S&P route was not tested:**
- **Time:** a full cycle (shortlist, papers, red-team, freeze, input build, runner, run, reproduction) took about 4 hours in R6. Under 2 hours remained before the no-new-experiments cut-off.
- **No sealed S&P holdout exists:** `R7_DATA_MANIFEST.md` finds no comparable sealed pre-2020-11 S&P holdout among the staged files. Brief §4 item 4 therefore fails, so an S&P result could never have reached criterion 5. This alone blocks the route.
- **Data audit late:** the R7 data manifest was finished only after the stop decision. It confirmed the decision rather than changing it.
- **Effect size:** the route needs a true weekly large-cap IC of 0.025 or more, above typical published effects.

Running it rushed would have risked the process errors this workflow exists to prevent (`specs/r7_decisions.md` item 19).

## 4. Protocol changes, tests and limitations

**Protocol changes (all prospective, none applied to a frozen strategy after its result):**
- R6 to R7: the Dow idea loop was stopped; the S&P universe check was added; the power gate now runs before any idea screen.
- A shared governance-first runner template with end-to-end tests using the real statistics helpers (`r4_harness/runner_template.py`).
- An idea-screen template that checks the cost bar first (`specs/IDEA_SCREEN_TEMPLATE.md`).
- An S&P runner adapter and pre-run checklist script, both built and tested but unused (`r4_harness/r7_sp500_adapter.py`, `r4_harness/r7_prerun_check.py`).
- The R7 Holm family carries all 21 R6 tests forward (`specs/r7_holm_family.json`).

**Disclosed process issues:**
- **Runner retries:** K1 needed 4 execution attempts and G1 needed 2, because of bookkeeping bugs. Every crash happened before any result was printed or written.
- **Data-boundary slips:** workers loaded date labels from June–November 2020 development staging files before filtering (4 occasions; no prices or results used).
- **Coordinator brief error:** one brief pointed at the sealed pre-2020 window. The worker refused, and no data was read.
- **Overwritten file:** an older idea file was overwritten; its verdict is preserved in the decision log.
- **Clock error:** R7 log entries 1–17 used a wrong clock; corrected at entry 18.
- **J1 reproduction (resolved):** the earlier −2.66% figure had no saved code or series and is retired (`report_drafts/J1_RECONCILE.md`). A new independent replay written only from the frozen pre-registration gives **+0.94 pp** net cumulative excess against the official **+1.03 pp**, a 0.09 pp difference, and both fail on Sharpe (`report_drafts/J1_REPLAY.md`, code `report_drafts/repro/j1_portfolio_replay.py`). One limitation remains: the compounded return *levels* of both portfolios differ by about 5 pp in each implementation. That's a shared return-path convention which cancels in the excess, and the saved results lack position-level detail to isolate it.

**Limitations:**
- **Short window:** the development window is about 6 years.
- **Data gaps:** the S&P roster lacks 51 names. Alpaca history starts in 2016, and FINRA short-interest holdout data only starts in Dec 2017.
- **Holdout never opened:** no strategy reached criterion 5.
- **DSR helper bug (found in R9):** `r4_harness/phase3.py:385-397` compares a daily Sharpe with an unscaled expected maximum, so it returns about zero for any input (J1 reported 5.2e-209). No R6 verdict changes: J1, the only strategy to reach the portfolio stage, had already failed on net Sharpe (0.82 vs 0.90) and bootstrap p (0.45), and no other strategy reached the DSR gate. Corrected in R9 (`r9/R9_ENGINE_AUDIT.md`); the frozen R6 file is left unchanged.

## 5. Data and reproducibility

- **Data inventory:** `R7_DATA_MANIFEST.md`, which separates downloaded, cleaned, used-in-a-frozen-test and unused data.
- **Rerun commands, frozen specs and hashes:** `R7_REPRO_INDEX.md`.
- **Full R6 detail:** `R6_FINAL.md`.

## 6. Conclusion

A pre-registered, holdout-protected search found **no buying-pressure strategy that beats an equal-weight Dow 30 portfolio after costs**. The one real signal (J1, weekly industry-relative reversal) was too small to survive weekly trading costs in a 30-stock portfolio.

The evidence says the obstacle is structural: published large-cap effects are 3–7 times smaller than a 30-stock portfolio needs. A larger universe (S&P 500) brings the required effect close to the published range on paper, but that route was not tested and remains a hypothesis for future work.
