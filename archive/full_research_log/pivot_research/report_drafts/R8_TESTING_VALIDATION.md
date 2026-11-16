# 4. Testing and validation

<!-- DRAFT for the team to edit. The "src:" comments are for checking only and are not counted; delete them before submission. -->

We first backtested the Section 3 strategy as written; it did not beat an equal-weight Dow portfolio after costs (Section 5.1). We then tested seven new strategies on the same idea: buying pressure persists, spreads to related stocks, or reverses. All faced the same tests and pass rules, so a good result could not come from trying many versions and keeping the best.
<!-- src: r4_L1/POSTMORTEM.md (baseline backtest); R7_FINAL.md §1; specs/r6_decisions.md -->

## 4.1 Data split

- **Development (in-sample):** Dow 30 daily data, 27 November 2020 to 30 October 2026. All seven strategies were tested here.
- **Holdout (out-of-sample):** Dow 30 daily data, January 2010 to October 2020. These files were sealed. Only a strategy passing every development test could use them, once. None did, so this report has no out-of-sample result.

Dow membership was point-in-time, so stocks that left the index stay in the sample. Some signals were estimated on the wider S&P 500 for statistical power, but every portfolio traded only Dow stocks.
<!-- src: R7_DATA_MANIFEST.md; R6_FINAL.md (holdout definition); specs/r6_goal.md -->

## 4.2 Pre-registration

Before any result was seen, each strategy's rules were frozen: signal, predicted direction, holding period, portfolio rules and pass thresholds. Each frozen file was dated and fingerprinted, so later changes would be detectable. We tested one version of each idea, and a failed idea was dropped, with no reversed signs or rescue versions.
<!-- src: specs/r6_prereg/*.md (FROZEN lines + SHA256); specs/r4_trials.md; R7_REPRO_INDEX.md -->

## 4.3 Three tests in order

Each strategy faced up to three tests in order; a failure stopped it.

1. **Signal test.** On each date we measured the rank correlation between the signal and later returns (the information coefficient, IC). The average had to have the predicted sign and a Newey–West t-statistic of at least 2.
2. **Placebo test.** We shuffled the signal 500 times among stocks in the same industry and re-ran the test (E1 shuffled the industry labels instead). The real signal had to beat 95% of the shuffles.
3. **Portfolio test.** A long-only Dow portfolio had to beat an equal-weight Dow 30 portfolio (EW30) on return and Sharpe ratio after a 0.05% cost on every trade. It also had to differ from EW30 in at least half its holdings, keep turnover at or below 50% per rebalance (or costs below a quarter of its gross gain), and pass a block-bootstrap significance test. We also report the deflated Sharpe ratio, which adjusts for the number of strategies tried.
<!-- src: specs/r6_prereg/J1.md (test order, 500 draws, 0.05%, 50% cap); R6_FINAL.md -->

## 4.4 Correcting for multiple tests

We registered three tests per strategy, 21 in total; tests never run were counted with p = 1. A Holm correction then adjusted each p-value for the number of tests.
<!-- src: specs/r6_holm_family.json (H1–H21) -->

## 4.5 Independent checks

D1's signal and placebo results were checked with separate code. J1's portfolio was rebuilt from its frozen rules alone: cumulative excess return +0.94 percentage points, against +1.03 officially, and a lower Sharpe ratio than EW30 in both.
<!-- src: report_drafts/REPRO_D1.md; report_drafts/J1_REPLAY.md; report_drafts/J1_RECONCILE.md -->

## 4.6 Process errors

Two runs (K1 and G1) crashed several times from bookkeeping bugs in the test code. Each crash came before any result was shown or saved, so no rule changed after seeing a result. A few early checks read date labels from outside the development period; nothing was calculated from them.
<!-- src: specs/r6_decisions.md items 116–127, 152, 169; R7_FINAL.md §4 -->
