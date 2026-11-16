# Frozen candidate choice — R2-2

Frozen after the six preregistered IS-only runs and before any test-period run.

| Candidate | Dow IS Sharpe | Dow turnover / rebalance | Cross-asset IS Sharpe | Cross-asset turnover / rebalance | Mean Sharpe | Eligible? |
|---|---:|---:|---:|---:|---:|---|
| 21-day reversal tilt, a=0.5 | 0.468546 | 38.53% | -0.040743 | 35.16% | 0.213901 | Yes |
| 21-day reversal tilt, a=1.0 | 0.461609 | 73.52% | -0.163158 | 68.08% | 0.149225 | No; breaches 50% cap in both universes |
| Volatility-scaled 21-day reversal tilt, a=0.5 | 0.469501 | 38.97% | -0.015677 | 35.10% | **0.226912** | Yes; selected |

The rule was to exclude candidates above 50% turnover in either selection universe and choose the highest mean Sharpe across the two universes. Thus the frozen choice is **volatility-scaled 21-day reversal tilt, a=0.5**, rebalanced every 21 sessions. No test-period results had been read when this choice was frozen.
The preregistration originally named four candidates. Before the first results, 12-1 momentum was removed because the supplied cross-asset data starts 2020-06-01, leaving fewer than 252 prior sessions at the start of the required selection period. Three candidates were run in each of two universes (six successful selection runs total); the mode-specific engine work was also attempted six times before an invariance check caught and the code corrected two signal-routing issues. Those six aborted invocations produced no performance results. After freezing the selection, the chosen variant was evaluated in the three required Dow test windows and the cross-asset test window. The four exact commands were replayed once to persist EW30 cost-detail files; all inputs, parameters, and reported returns were identical.

