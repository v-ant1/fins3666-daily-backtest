# L1 task: Phase 0 post-mortem (forensic analyst)

TARGET: the original pressure+heat strategy on Dow 30 development data, 2020-11-27 to 2026-10-30. Folder: r4_L1\ (write only here).

CHANGE: produce a diagnosis of WHY it fails. No new strategies; diagnosis only.
1. Predictive power by horizon:
   - Compute the cross-sectional Spearman rank correlation between each signal (pressure, each of its 3 components, heat, nbr-avg) and forward returns at 1, 2, 5, 10 and 20 days, measured close-to-close and next-open-to-close.
   - Report the mean rank correlation with Newey-West t-stats. Show how the predictive power fades with horizon.
   - Check whether the sign is reversal or continuation. Compare raw returns with market-demeaned returns.
2. Component anatomy: correlations between the components, and how much each contributes to the blend.
3. What the heat term actually is:
   - Break down the graph filter exp(-L) by eigenvalues.
   - Measure how close heat is to (a) a plain neighbour average and (b) the market or sector average.
   - Measure how stable the 63-day graph is from week to week (edge overlap).
4. Power analysis: given 30 names and about 6 years, what rank correlation would be needed for t >= 2 and for a portfolio information ratio of 0.5 (fundamental law)? How far is the observed rank correlation from that?
5. Cost anatomy: gross vs net return, the rank correlation needed to break even at the observed turnover, and what the gross edge is before costs.
6. Regime and sector: is any rank-correlation evidence concentrated in particular years or sectors?

CONSTRAINTS:
- Development data only; never use pre-2020-06 data.
- These diagnostics count as analysis, not trading variants, so they do not use the 30-variant budget. Still list them in r4_L1\DIAGNOSTICS_LOG.md.

OWNERSHIP: r4_L1\ only. You may import from repo\ or w1_engine\code but never edit them.

OBSERVABLE ACCEPTANCE: r4_L1\POSTMORTEM.md containing:
- a table of rank correlations by horizon, with t-stats;
- the spectral breakdown of heat, with numbers;
- the power-analysis numbers;
- the cost break-even;
- a ranked list of 3-5 root causes, each backed by evidence;
- implications: "what a new direction must do differently" (inputs for L2 and L3).
Also include charts as PNGs and code that runs with one command.
