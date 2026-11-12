# Evaluation of results

> **Completion rule:** Replace every bracketed field from the frozen preregistration, trial log, and recorded analysis output. Do not omit a failed, null, infeasible, or unavailable test. Use the complete goal-wide Holm family, show raw and adjusted values, and state when a result is descriptive rather than inferential. Do not change gates after viewing outcomes.

## Direction summary

Complete one block for each tested direction: **D4**, **D5**, and **[fallback ID and name]**. Begin with the question the design tested, the frozen prediction, the decision at each preregistered gate, and the evidence supporting that decision. State whether the input-only feasibility gate passed before outcomes were examined. If it failed, mark the direction infeasible and leave later outcome fields as not run; do not imply that the missing result is a negative test.

| Direction | Mechanism prediction and horizon | Input feasibility | Mechanism estimate and gate | Placebo conclusion | Portfolio gate | Holdout gate | Overall status |
|---|---|---|---|---|---|---|---|
| D4 | [frozen prediction] | [pass/fail; input evidence] | [estimate; uncertainty; pass/fail] | [summary] | [pass/fail/not run] | [pass/fail/not run] | [advance/fail/infeasible] |
| D5 | [frozen prediction] | [pass/fail; input evidence] | [estimate; uncertainty; pass/fail] | [summary] | [pass/fail/not run] | [pass/fail/not run] | [advance/fail/infeasible] |
| [Fallback] | [frozen prediction] | [pass/fail; input evidence] | [estimate; uncertainty; pass/fail] | [summary] | [pass/fail/not run] | [pass/fail/not run] | [advance/fail/infeasible] |

## Mechanism and placebo evidence

For each primary mechanism endpoint, report its preregistered sign and horizon, sample coverage, estimate, Newey–West statistic and raw p-value, then compare each result directly with its frozen gate. Include every registered sensitivity endpoint and identify which variant alone could advance. Summarize each placebo separately, including the placebo construction, estimate, uncertainty or randomization comparison, and its preregistered criterion. A non-significant placebo is not proof of no effect; describe it as compatible or incompatible with the control criterion and avoid claiming that it establishes causality. If placebo results are mixed, say so plainly.

| Direction / endpoint | Estimate and horizon | NW statistic / raw p or randomization result | Frozen criterion | Pass, fail, or descriptive |
|---|---|---|---|---|
| [ID / primary mechanism] | [value; horizon] | [value] | [registered gate] | [status] |
| [ID / placebo] | [value; construction] | [value] | [registered criterion] | [status] |
| [ID / sensitivity] | [value; horizon] | [value] | [registered rule] | [status] |

## Portfolio and multiplicity

Only report a portfolio as tested when its preregistered mechanism gate passed. Compare gross and net strategy returns with EW30 over the same eligible dates; state the cost model and report annualized return, Sharpe, maximum drawdown, and turnover using the frozen conventions. Include active share or long-short exposure and whether turnover/cost constraints passed. Show realized costs and whether net excess return and Sharpe satisfy the registered advancement rule. Report every goal endpoint's raw and Holm-adjusted p-value using the complete family. Give the deflated Sharpe ratio together with the full registered trial count used; do not substitute only the variants that reached portfolio testing.

| Direction / portfolio | Gross return vs EW30 | Net return vs EW30 | Sharpe vs EW30 | Max drawdown | Turnover / costs | Active share or exposure | Bootstrap p, raw / Holm | DSR; trial count | Gate |
|---|---|---|---|---|---|---|---|---|---|
| [ID] | [value] | [value] | [value] | [value] | [value] | [value] | [value / value] | [value / count] | [pass/fail/not run] |

| Goal-wide endpoint | Direction / variant | Raw p-value | Holm-adjusted p-value | Registered interpretation | Result |
|---|---|---|---|---|---|
| [endpoint] | [ID] | [value] | [value] | [criterion] | [status] |

## Sealed holdout and deviations

Report the coordinator's single holdout run on the frozen specification, its available-name benchmark, coverage gaps, and each registered pass condition. For Dow directions, show the full holdout result and the required result excluding the DWDP membership window; explain whether removing that window changes the decision. For a non-Dow fallback, mark the DWDP comparison not applicable and report its preregistered holdout universe and coverage instead. Do not describe an incomplete universe as a complete Dow test.

**Disclosed deviations.** The SIC audit found that the DD and pre-separation DOW issuer lineage needs correction, but the recorded decision treats those errors as confined to holdout years; D5's development test stands because DD is outside the development roster and DOW uses Dow Inc. L4 must repair and audit the lineage before the coordinator runs the holdout. The SIC panel records filing dates rather than EDGAR acceptance timestamps, so the D5 cutoff is implemented conservatively as usable on the first NYSE session strictly after the filing date; state this deviation and its no-look-ahead rationale wherever D5 results are summarized.

## Plain-English interpretation

End with a short account of what the evidence supports and what it does not. Separate evidence that pressure predicts returns from evidence that it spreads through the proposed network, and separate both from evidence that a feasible portfolio survives costs and the holdout. If any gate fails, name it, report the failed estimate and controls, and say that the direction did not meet its preregistered advancement rule; do not rescue it with a sensitivity, a different horizon, or a post hoc explanation. If results disagree across development, placebo, portfolio, and holdout stages, describe the disagreement and its practical implication. Report infeasibility, missing coverage, and deviations as limitations, not as favorable evidence. State the number of variants used against the goal budget and whether the final conclusion is positive, negative, or inconclusive.


