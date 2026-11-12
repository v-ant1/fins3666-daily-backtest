# D5 draft — directed same-industry leader-to-follower pressure

STATUS: DRAFT — NOT FROZEN. No D5 outcome data have been computed.

This is a falsifiable test of whether short-horizon buying pressure at the most actively traded Dow name in a dated SIC industry predicts subsequent returns among its industry peers. It uses point-in-time industry links rather than a correlation graph. Dollar volume ranks leaders; it is not itself interpreted as investor attention or causal transmission.

## Hypothesis, sign and horizon

At a signal close, positive five-session close-location-value (CLV) pressure at a same-industry leader predicts positive next-week returns among its followers. Reversing the directed edges should remove the effect. The only primary horizon is five trading sessions.

## Inputs, industry and directed graph

- **Universe and period:** point-in-time Dow 30 roster and daily OHLCV, development dates 2020-11-27 through 2026-10-30. Use the dated issuer-SIC observations in `r4_L4/data/sic_panel.csv`; this input must be completed and audited before freeze. Never substitute the current SEC SIC snapshot for the dated panel.
- **Industry level:** parse the issuer's four-digit SIC as a four-character code, retaining leading zeroes; the industry key is exactly the first two digits (the SIC major group). Do not use SIC divisions, three-digit groups or four-digit industries. Assign the latest 10-K header SIC publicly accepted by the end of the prior trading session. A code is carried forward until a later accepted 10-K header supplies a new code; no backfilling or later filing look-ahead. Missing or invalid SIC means no edge.
- **Leader ranking:** on signal date `t`, compute each active member's mean daily dollar volume, `close × volume`, over the 20 completed sessions ending at `t−1`. Rank only active names within the same two-digit SIC. Highest mean dollar volume is the sole leader; break exact ties by ticker in ascending ASCII order. Create a directed unit-weight edge from that leader to every other active Dow member in the same SIC. No self-edge, thresholding or within-industry alternative is allowed. A singleton SIC contributes no edge. Ranking inputs are known by the signal date and never use outcomes.
- **Pressure and score:** `CLV_i,t = (2×close_i,t − high_i,t − low_i,t)/(high_i,t − low_i,t)`; set it to zero when high equals low. Leader pressure is the arithmetic mean of its CLV over `t−4:t`. Follower score is the mean pressure of its incoming leaders; in this one-leader-per-industry graph that is the leader's five-session pressure. The graph and score at `t` use only information public by the signal close. No score is assigned to a leader without incoming edges.
- **Pre-outcome graph feasibility gate:** at each fifth-session formation date with valid 20-session dollar-volume and SIC inputs, count the distinct directed source-recipient pairs. D5 is declared **infeasible before any future return, IC, event response or portfolio result is calculated** if there are fewer than 10 directed pairs on at least 20% of eligible formation dates (equivalently, at least 10 pairs must exist on at least 80% of such dates). Do not broaden the industry level, change the window, pool non-Dow assets or lower the threshold. Record the eligible-date count, pair-count distribution and dates below threshold from input coverage only.
- **Known data limitation:** at drafting, the dated SIC panel is still being built and its date/ticker coverage and the above pair-count gate are unverified. This preregistration cannot be frozen until the panel, SIC parsing/date rules and gate are checked without computing outcomes.

## Primary mechanism test and placebos

On each eligible date, calculate cross-sectional Spearman rank IC between the follower score and the follower's next-open-to-close five-session return, `adjusted_close[t+5] / adjusted_open[t+1] − 1`. Report the date-level IC series, its mean and Newey–West t-statistic with Bartlett lag 4. The sole primary prediction is mean IC > 0 and NW t ≥ 2.0. Also report the raw number of eligible observations and effective dates; no alternative horizon can replace a failed primary.

Use 500 draws per randomized placebo family with fixed seed `20261110`: (a) reverse every directed edge, (b) permute leader assignments within each two-digit SIC while preserving the dated roster and industry member counts, and (c) shift the dated graph 20 trading sessions. The observed IC must exceed the 95th percentile of each relevant one-sided randomized distribution; reversed and time-shifted placebo ICs must have absolute NW t < 2. Report every placebo result. A failed primary mechanism test ends D5; no rescue variant or portfolio test follows.

## Variants and selection rule

1. **Primary:** 20-session trailing mean dollar-volume leader; two-digit SIC; five-session mean CLV; five-session next-open-to-close outcome.
2. **Fixed sensitivity:** 60-session trailing mean dollar-volume leader with all other rules unchanged.
3. **Fixed diagnostic/placebo:** reverse edge direction under the 20-session primary construction.

Variant 1 alone determines advancement. Variants 2–3 are reported in full and cannot replace a failed primary or be selected for better returns. The 10-pair feasibility gate applies to the primary graph before outcomes; the 60-session sensitivity does not change that gate.

## Portfolio, costs and inference

Only after a primary mechanism pass, rank eligible followers by score at each fifth-session close and buy the top five equal-weight at the next session's open. Hold through the next weekly formation; score ties break by ticker ascending. Compare with equal-weight among the point-in-time available Dow names. At formation, top-five active share is 83.3% when all 30 names are eligible. Cap total traded notional divided by NAV at 50% per rebalance; charge 0.05% per traded dollar with the harness actual-trade engine. If eligibility changes make the cap or 50% active-share condition impossible, report the condition and do not count the portfolio as a pass.

Cost-only rank-IC hurdle: use `r4_harness.break_even_rank_ic(turnover=0.50, return_dispersion=0.03007510102898867, cost_per_side=0.0005, top_fraction=1/6) = 0.0057591`. The dispersion is the already documented L1 five-session development reference, used solely as a fixed scale assumption; it is not estimated from D5 outcomes. This harness mapping is a planning approximation for a long-only top-sixth score and does not replace actual realized trading costs. Require gross active edge at least four times actual costs, positive net excess return and higher net Sharpe than EW30.

For the portfolio endpoint, use a one-sided circular block bootstrap with 5,000 draws, 10-session blocks and seed `20261110`; report raw and Holm-adjusted p-values and the deflated Sharpe ratio at the full goal trial count of 30. Apply Holm once to the complete family of every preregistered mechanism, placebo-comparison and portfolio endpoint across D4, D5 and D6 in this goal, including sensitivity tests; do not use a fixed 24-test family or correct D5 in isolation. Report the full family, raw p-values, adjusted p-values and all failures. Portfolio pass requires Holm-adjusted p < 0.05.

## Sealed holdout procedure and pass rule

Only the coordinator may run one holdout job, once, after frozen code and this preregistration are verified. Use the point-in-time Dow roster over 2010-01-01 through 2020-10-31, with the gaps disclosed: KFT, DWDP and WBA are unavailable; UTX is proxied by its RTX lineage. Compute the EW benchmark over available names. Report the DWDP membership window both included and excluded. Do not impute missing names or alter this graph, signal, hurdle, horizon or execution rule for the holdout. Workers must not access holdout prices, returns or signals.

Full holdout pass requires the registered positive five-session IC sign, positive net excess return, Sharpe above EW over available names, and one-sided 10-session block-bootstrap p < 0.10; include the required DWDP sensitivity and disclose all gaps. Incomplete coverage is a limitation and cannot be represented as a complete Dow 30 test.

## Ready for freeze checklist

- [ ] `r4_L4/data/sic_panel.csv` exists, has dated 10-K header SIC values and accepted filing dates for the required development roster, and its lineage/coverage has been audited without using outcomes.
- [ ] Two-digit SIC derivation, forward-carry rule, filing-date availability, OHLCV conventions and prior-session 20-session dollar-volume ranking are implemented exactly as written.
- [ ] The pre-outcome gate is computed from inputs only: at least 10 directed pairs on at least 80% of eligible fifth-session formation dates. Record counts and declare D5 infeasible if it fails; do not broaden the design.
- [ ] The coordinator's Dow holdout roster/gap handling is noted in the frozen config; workers still have not opened holdout prices or returns.
- [ ] D4–D6 goal-wide Holm family is enumerated before any outcomes are computed, and the cost hurdle is the stated harness value and fixed L1 dispersion assumption.
- [ ] Add `FROZEN: YYYY-MM-DD` and a SHA256 digest only after all input checks pass and before any D5 outcome is computed. If any specification changes after outcomes, do not freeze this version or continue it as D5.
