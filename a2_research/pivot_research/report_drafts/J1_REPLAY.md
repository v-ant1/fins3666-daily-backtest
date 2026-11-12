# J1 portfolio replay

## Result

I replayed the frozen Dow portfolio from the preregistered J1 rules, the staged development price panel, and the frozen signal bundle. The script is standalone: it does not import the official runner or any holdout helper. No holdout data or new signals were accessed.

| Measure | Independent replay | Frozen `J1_RESULTS.json` | Difference (replay minus official) |
|---|---:|---:|---:|
| Strategy net cumulative return | +101.285% | +96.214% | +5.071 pp |
| EW30 net cumulative return | +100.349% | +95.187% | +5.162 pp |
| Strategy less EW30 net cumulative return | +0.9360 pp | +1.0276 pp | −0.0916 pp |
| Strategy annualized net Sharpe | 0.8381 | 0.8232 | +0.0150 |
| EW30 annualized net Sharpe | 0.9093 | 0.9023 | +0.0070 |

The frozen run's **+1.0276 pp (reported +1.03%)** is the correct number to cite as the official J1 result. The independent replay gives +0.9360 pp, within the requested 0.1 pp tolerance for net cumulative excess; both versions show lower strategy Sharpe than EW30, so the portfolio still fails the Sharpe gate.

## Return-path comparison and limits

All 1,487 daily observations align on date indices 127–1613. The strategy daily net-return correlation is 0.99941 and EW30's is 0.99900. Mean absolute daily differences are 0.0155 pp for the strategy and 0.0196 pp for EW30, with maximum differences of 0.5732 pp and 0.8604 pp, respectively. Thus the headline excess nearly reproduces because the two books' wealth-level differences mostly cancel; the individual compounded return levels do not reproduce within 0.1 pp.

This is not a simple compounding convention error: the official stored daily net series compound exactly to the cumulative values in `J1_RESULTS.json`, and the replay uses the same aligned dates and compounds its own daily returns the same way. The common-mode level gap in both strategy and EW30, alongside the small excess gap, indicates a portfolio return-path convention difference (most plausibly the treatment of open execution and the EW30 rebalance/available-name basis), rather than a signal-ranking difference. The preregistration specifies next-session-open execution and a point-in-time EW30 available-name benchmark, but the saved result alone does not encode enough position-level state to identify which of those conventions accounts for the remaining 5 pp level gaps. Therefore this audit reconciles the requested **net excess** to within tolerance, but does not claim an exact daily portfolio-path reproduction.

## Replay implementation and inputs

The independent code builds the weekly formation calendar from the frozen signal rows, selects the five lowest valid peer-relative scores, starts from PIT EW30, applies the 50% total traded-notional step cap, charges 0.05% on turnover, and records daily net returns for the strategy and benchmark. The first ten dates with fewer than five eligible names are held without substitution, matching the fixed availability behavior recorded in the official result. The full daily replay and comparison vectors are saved at `report_drafts/repro/J1_PORTFOLIO_REPLAY.json`.

Input hashes: prices `517f85becd0a07fa094a0492e5fe7b3f36170109082b249d5c8a3149d88f5584`; signal bundle `490acf5f8ef0df5c85ee25180ed0b49816dab2cf4cb00398b1a329e0eec30b4c`; preregistration `996b971090be395fffb1e11dff1430bbf581b338637250716607bf6b51cb7698`.

