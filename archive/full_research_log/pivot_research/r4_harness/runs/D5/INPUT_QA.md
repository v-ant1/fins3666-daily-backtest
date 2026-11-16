# D5 development input QA (outcome-blind)

**Gate verdict: PASS.**

Built the D5 point-in-time 2-digit SIC directed graph using only registered development dates. No forward returns, future outcome windows, ICs, event responses, portfolios, or holdout price data were loaded or computed.

## Fixed inputs and timing

- Development session range: 2020-11-27 through 2026-10-30 (1488 sessions); initial formation dates are every fifth session starting at session 5.
- SIC source: `r4_L4/data/sic_panel.csv`; `effective_from` is treated as the filing date and becomes usable on the first development trading session strictly after it. Only the two-character SIC major group is used.
- Dollar volume: raw close × reported volume, exactly the prior 20 completed sessions; the highest mean is the sole leader and ticker ascending breaks ties.
- Harness interface: `build_dated_industry_network` constructs the directed ranked candidate graph; this D5 build retains only the registered leader-to-each-follower star.
- Roster: development point-in-time Dow roster schedule shared with D4 inputs.

## Input coverage

- SIC records in the development filing-date interval: 265 records across 45 assets; historical SIC rows are used only to carry the latest dated code into development dates.
- SIC ticker/date gaps listed by `sic_panel_gaps.csv` within development dates: 0 rows.
- Active-member SIC coverage: 30 to 30 names on eligible formation dates.
- Per-ticker bar and SIC coverage is recorded in `D5_COVERAGE.csv`; per-date counts are in `D5_GRAPH_BY_DATE.csv`.

## Registered minimum-pair gate

- Eligible fifth-session dates with input coverage: 293.
- Requirements: at least 10 directed pairs, 3 distinct leaders, and 3 SIC groups on at least 80% of eligible dates.
- Dates passing all three conditions: 293/293 (100.0%); failing dates: 0 (0.0%).
- Directed pairs per eligible date: min 11, median 11.0, max 11; leaders min/median/max 5/5.0/6; SIC groups min/median/max 5/5.0/6.
- Under D5, failure on more than 20% of dates is infeasible. Observed failure share: 0.0%.

## Files

- `D5_INPUTS.npz`: development-only graph and signal inputs, with no forward-return field.
- `D5_GRAPH_BY_DATE.csv`: pair, leader, SIC, and eligibility counts by development date.
- `D5_COVERAGE.csv`: ticker-level development bar and SIC coverage.
- `sic_panel_gaps.csv` is the development-date-only copy of L4 gap records.
- This input QA was produced before the D5 freeze and before any mechanism outcomes; the later freeze/hash verification and mechanism results are recorded in `MECHANISM_RESULTS.md`.
- The frozen clarification defines a single deterministic 20-session shift, not a 500-draw family.
