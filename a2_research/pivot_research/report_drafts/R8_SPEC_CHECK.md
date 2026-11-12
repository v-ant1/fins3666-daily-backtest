# R8 review: Step 5 and Step 6 drafts

## Scope and word count

Reviewed exactly `R8_TESTING_VALIDATION.md` and `R8_EVALUATION.md` against the Student Guide's Step 5, Step 6, Appendix A.5 and A.6; the rubric's Analysis & Evaluation criterion; and the available A1b marker-feedback notes. The older `*_DRAFT.md` files were not reviewed. Neither target draft was edited, and I did not run analysis or open holdout files.

Using a word-token count, I excluded Markdown table rows and separators, table/figure caption lines, and all HTML comments. Headings, bullets and ordinary prose remain counted:

- `R8_TESTING_VALIDATION.md`: **566 words**
- `R8_EVALUATION.md`: **476 words**
- Combined: **1,042 words**

Word processors may count hyphenated terms and symbols differently. The report-wide 2,500-word allowance still needs to cover the other sections and any non-exempt text.

## Overall assessment against the course requirements

The drafts provide a clear record of development tests, failures, portfolio costs and risk measures. The Evaluation section has useful evidence: annualised return and volatility, Sharpe and Sortino ratios, drawdown, information ratio and turnover for J1. The baseline also includes gross and net returns, Sharpe and turnover. The text usually distinguishes a failed or unrun test from a successful one.

**Out-of-sample validation remains unperformed.** Step 5 asks for results on a separate unseen dataset and an introductory evaluation of in-sample and out-of-sample results. These drafts explain that the holdout stayed sealed because no strategy passed development gates. That is honest and consistent with the stated stop rule, but the report must say explicitly that the Step 5 out-of-sample requirement was not completed. It cannot describe the holdout as validation or imply that this requirement was met.

The main technical issue is the broad claim that all seven strategies used the same tests. The actual placebo methods differ, and §4.3's one-size-fits-all description says every placebo shuffled signals within industry. The drafts should describe the common decision sequence, then name the registered placebo used by each strategy or put that detail in Table 5.1. Also, 21 Holm slots are registered endpoints, not 21 strategies that were all run; distinguish unrun bookkeeping slots from observed test results.

The rubric's strongest band asks for comprehensive testing, effective use of further metrics and insightful evaluation. These drafts are close in structure, but the conclusion that the main barrier was portfolio size “not the data” is too strong for the mixed feasibility and mechanism results. Clarify that no subperiod stability test is reported. Independent reproduction checks whether saved calculations match; it does not establish that performance is stable over time.

## Specific suggested edits

### `R8_TESTING_VALIDATION.md`

| Location and current wording | Proposed rewrite |
|---|---|
| §4, ¶1: “Each was tested the same way, so that a good result could not come from trying many versions and keeping the best one.” | “Each idea had one frozen version and a pre-set rule for stopping after a failed test. The test details differed by idea, and we report all seven ideas.” This avoids claiming identical test methods. |
| §4.1, ¶1: “We split the data into two periods before any test was run.” | “We set aside the development period and kept the holdout sealed. We used development data for the reported tests.” The original sounds as if both periods were opened or analysed. |
| §4.1, holdout bullet: “Only a strategy that passed every development test could be run on them, once.” | “No strategy passed every development test, so the holdout was not run. The report therefore has no out-of-sample result, although the course guide asks for one.” This states the unmet requirement directly. |
| §4.1, ¶3: “Some signals were estimated on the wider S&P 500 for statistical power, but every portfolio traded only Dow stocks.” | “For some signal tests, we used a larger, point-in-time S&P 500 sample to improve precision. The portfolios still held only Dow stocks.” Define “point-in-time” as the membership known on each date if retained. Add one short reason why a larger signal-test universe is relevant to a Dow portfolio. |
| §4.2: “Each frozen file was dated and given a digital fingerprint (a SHA-256 hash), so any later change would be detectable.” | “We dated each rule file and recorded a file fingerprint, so later changes could be detected.” The algorithm name adds little for a finance report. |
| §4.2: “Each idea got one version only.” | “We tested one registered version of each idea.” “Idea” could mean a direction or a variant; use “version” consistently with the trial log. |
| §4.3, opening: “Each strategy had to pass three tests in order. A failure stopped it.” | “Each strategy faced up to three pre-set tests in order. A failed signal or placebo test stopped its portfolio test.” “Up to” is necessary because portfolio tests were not run for most strategies. |
| §4.3, test 1: “We measured the rank correlation between signal and later return (the information coefficient, IC) on each date.” | “On each date, we checked whether stocks with higher signal ranks also had higher later-return ranks. We call this rank correlation the information coefficient (IC).” Defines the comparison without assuming the reader knows what “across stocks” means. |
| §4.3, test 1: “The average had to have the predicted sign and a Newey–West t-statistic of at least 2.” | “The average had to point in the predicted direction and have a Newey–West t-statistic of at least 2. This statistic adjusts uncertainty for nearby observations being related.” Use this definition once. |
| §4.3, test 2: “We shuffled the signal 500 times among stocks in the same industry and re-ran the test.” | “Each idea used its registered placebo. For the industry-based tests, we shuffled signals among stocks in the same industry 500 times; other tests used their specified network or time-shift comparisons.” Confirm the second clause against the registered specifications before submission and identify the relevant rows in Table 5.1. |
| §4.3, test 3: “A long-only Dow portfolio built from the signal had to beat an equal-weight Dow 30 portfolio (EW30) on both return and Sharpe ratio.” | “If the signal and placebo tests passed, a Dow portfolio had to earn a higher net return and net Sharpe ratio than EW30, an equal-weight Dow portfolio.” The conditional sequence and after-cost comparison should be explicit. |
| §4.3, end of test 3 | **Add:** “The portfolio also had to pass the registered block-bootstrap test and the full portfolio gates, including the active-share and turnover rules.” Include the exact gates that applied; the current paragraph omits them. In particular, do not omit the required DSR reporting at the full trial count from the final portfolio evaluation. |
| §4.4: “We counted every test across all seven strategies: 21 in total, including tests that were blocked and never run.” | “The Holm family contained 21 registered test slots across seven strategies. Some portfolio slots were not run; their bookkeeping values are not observed p-values.” This distinguishes registered endpoints from completed tests. |
| §4.4: “We then applied a Holm correction, which raises each p-value to account for the others.” | “We applied the Holm correction to account for the full set of registered tests.” Not every adjusted p-value must increase, so “raises each” is imprecise. |
| §4.5: “The two best results were rebuilt independently.” | “We independently checked D1's signal and placebo results and replayed J1's portfolio.” “Best” is a vague selection label and may imply these were chosen after comparing outcomes. |
| §4.5: “the rebuild gave +0.94 percentage points of excess return against the official +1.03, and both fail the Sharpe test.” | “The replay's excess return was +0.94 percentage points, compared with +1.03 in the official result. Both results had a lower Sharpe ratio than EW30.” State whether those percentages are cumulative, and retain the separate note that the replay did not reproduce every portfolio metric if applicable. |
| §4.6: “A few early checks also read date labels from outside the development window; no prices or results were used.” | “A few early checks read date labels outside the development period. No prices, returns or signals were calculated from them.” Use the actual scope of the check; “no results were used” is less specific. |

### `R8_EVALUATION.md`

| Location and current wording | Proposed rewrite |
|---|---|
| §5, opening: “One strategy, J1, had a real signal but could not beat simply holding the Dow after trading costs.” | “J1 passed its raw signal and placebo tests, but its Sharpe ratio and bootstrap test did not show that its portfolio beat EW30 after costs. After adjustment for all registered tests, its signal result was not statistically significant.” “Real signal” overstates a raw result that did not survive the family correction. |
| §5.1, baseline: “Its Sharpe ratio was 0.64 against 0.92.” | “Its net Sharpe ratio was 0.64, below EW30's 0.92.” This makes the cost basis and comparison plain. Define Sharpe once as a return-to-risk measure. |
| §5.1, table label `Placebo p` | Change to `Raw placebo p-value` and identify the family-adjusted values in the text or an added column. The nearby paragraph reports adjusted p-values, so the present label can confuse raw and adjusted values. |
| §5.1, after Table 5.1: “After the Holm correction for 21 tests, even J1's signal is no longer significant (adjusted p = 0.36; D1 0.51).” | “After adjustment across all 21 registered test slots, J1's signal p-value was 0.36 and D1's was 0.51; neither met the 0.05 cutoff. Some slots were not run and are included only as bookkeeping entries.” Do not call the 21 slots tests that were all performed. |
| §5.2 heading: “J1: a real signal that costs erased” | “J1: a raw signal result, but no portfolio pass” This reflects the family-adjusted and portfolio evidence. |
| §5.2: “After costs it was ahead of EW30 on 80% of trading days…” | “The cumulative excess-return line was above zero on 80% of dates, even though J1's final net return was only about 1.0 percentage point above EW30.” Only use “cumulative line” if that is what the metric records. This explains why many positive dates do not mean a strong final result. |
| §5.2: “Those costs, and the growth lost on that money, cut its lead to 1.0 percentage point.” | “After costs, J1's excess return was about 1.0 percentage point.” The current causal wording adds a compounding explanation that the sentence does not quantify. |
| §5.2, cost conclusion: “Costs took 66% of its gross edge, above our 25% limit.” | “Trading costs consumed 66% of J1's gross excess return. Its average turnover was 48%, within the 50% cap; its net Sharpe remained below EW30 and the bootstrap p-value was 0.45.” The 25% wording does not match the stated project rule: turnover up to 50% is permitted, otherwise costs must be below one quarter of gross edge. If 25% was a separate frozen gate, cite that preregistered rule. |
| §5.2, Table 5.2 | Add rows for **net cumulative excess return** (+1.03 percentage points), **active share** (54.8%) and **block-bootstrap p-value** (0.45), or place them in the results paragraph. These show the actual portfolio pass/fail gates and prevent the reader inferring success from similar annualised returns. |
| §5.3: “The main barrier is the size of the portfolio, not the data.” | “Limited portfolio breadth was one important hurdle in the tested strategies. Data gaps and failed mechanisms also affected the results.” The original rules out data as a cause without evidence, despite the limitations listed later. |
| §5.3: “We estimated this by simulation (Table 5.3).” | “Under the assumptions in our simulation, the estimated signal strength needed to pass was…” Then name the key assumptions in the caption or a note. These thresholds are design estimates, not universal minimum ICs. |
| §5.3: “On the Dow, the IC needed is about three to seven times larger than published effects. J1's IC of 0.015 is in line with those effects, which explains why it could not pass.” | “Under this simulation, the Dow top-five strategy needed a much larger IC than the 0.015 observed for J1. The published-effect range is only a rough comparison because the studies use different samples and methods.” Cite the specific studies with real links in the report's references; the current draft gives no reader-facing citation for “published effects.” Avoid saying this alone explains failure; J1 also failed portfolio risk and significance tests. |
| §5.4: “Short window…about 300 weekly rebalances.” | “The development period covers about six years and 298 J1 weekly formation dates.” This uses the count in the cited draft source, avoids implying the same number applies to all directions, and uses plain language. |
| §5.5: “A larger universe is the clearest route.” | “A larger universe may improve the test's statistical power, but we did not test that approach.” The current wording presents a possible future direction as a settled conclusion. |
| Figure 5.1 line contains `` `figures/r8_j1_excess.png` `` | Embed the actual figure in the submitted report and use a caption such as “Cumulative return difference between J1 and EW30, before and after costs.” A filename in code formatting will not display a figure in the report. |

## Required elements and evidence to make explicit

- **Step 5 / out-of-sample:** no holdout result exists because no candidate met the pre-set development gates. State that out-of-sample validation was not completed and is an unmet course-guide element. Do not open or use the sealed data in this review.
- **Complete portfolio criteria:** §4.3 currently mentions return, Sharpe, turnover and bootstrap, but not all applicable gates. State the active-share rule and the DSR requirement at the full trial count. The Evaluation section should show J1's net excess return, active share, turnover, Sharpe comparison, costs and bootstrap result together.
- **Holm count:** say “21 registered endpoint slots,” not 21 tests all performed. Mark blocked/unrun slots explicitly; a placeholder p-value is not evidence.
- **Robustness:** the drafts report placebos and independent calculation checks, but no subperiod stability analysis. Say so; replication verifies calculations and does not establish time stability.
- **Original heat baseline:** retain its result. It is an important comparison with the later strategies: weak five-day IC, gross outperformance erased by costs, net return and Sharpe below EW30, and very high turnover.
- **Figure delivery:** replace the literal image path with the actual embedded cumulative-excess chart. Keep axis units, benchmark and cost status visible.
- **Source support:** cite the studies behind the “published effects in large US stocks” range in the final report using working DOI or URLs. A hidden HTML source comment is not a reader-facing citation.
- **Remove production comments:** delete the draft instruction and all `<!-- src: ... -->` comments before submission; they are useful editing notes but are not report content.

## Jargon to define briefly or simplify

| Term in these drafts | Plain-English option |
|---|---|
| In-sample / out-of-sample | Development period / separate holdout period. |
| Point-in-time membership | The list of index members known on each date. |
| Information coefficient (IC), rank correlation | Whether stocks with higher signal ranks also had higher later-return ranks. Define once; use “IC” in tables after that. |
| Newey–West t-statistic | A test statistic whose uncertainty allows nearby observations to be related. |
| Placebo, randomization p-value | A shuffled or shifted comparison used to check whether the result is unusual. Name the actual shuffle or shift. |
| Holm correction / adjusted p-value | A correction for testing many registered results together. |
| Endpoint / family | Registered test result / all registered test results considered together. Avoid “family” in prose. |
| SHA-256 hash | File fingerprint. The exact algorithm is not needed in the main text. |
| EW30 | Equal-weight Dow 30 benchmark. Define at first use. |
| Sharpe / Sortino / information ratio | Return relative to total risk / downside risk / benchmark-relative risk. A short table note can define the ratios together. |
| Maximum drawdown / turnover | Largest peak-to-trough loss / amount traded relative to portfolio value. |
| Long-only / gross edge / notional | Buy-only / excess return before costs / portfolio value traded. |
| Block bootstrap | Repeatedly resampling short runs of adjacent dates to estimate uncertainty. Use only if needed to explain the portfolio p-value. |

The marker-feedback notes favour short, direct sentences and separating measured results from explanations. They caution against adding technical detail for appearance or claiming more than the evidence supports. The edits above keep terminology needed to understand or reproduce the tests while moving secondary implementation detail out of the main prose.

## Materials checked

- `A2/FINS3666 2026 T3 Project Assessment, Group Project Student Guide.pdf`: Step 5, Step 6, Appendix A.5 and A.6.
- `A2/FINS3666 2026 T3 Project Assessment, Group Project Student rubric.pdf`: Analysis & Evaluation (25%).
- `A1b/FINS3666_A1b_marking_feedback (1).md` and `A1b/FINS3666_comprehensive_feedback.md`: prior marker-feedback guidance on clear language, evidence limits and avoiding unnecessary sophistication.
