# R5 Red-Team Audit: D4 and D6 Inputs

**Scope.** Compared the frozen `specs/r4_prereg/D4.md` and `D6.md` with `r4_harness/runs/D4/build_inputs.py`, D4's `INPUT_QA.md`, the input-only D4 `D4_INPUTS.npz` structure and `quarter_coverage.csv`, and D6's `INPUT_QA.md`. I did not read holdout data, load forward returns, or calculate return outcomes or ICs. Structural checks of D4 arrays were limited to the graph adjacency and row weights.

## BLOCKER

### D4's complete 28-name support is likely a position-panel coverage or mapping defect, not proof that broad managers hold every Dow name

From 2020-09 onward, `quarter_coverage.csv` reports 378 positive undirected links out of 435 possible, 28 connected names out of 30, and density 0.869 in every quarterly snapshot. Since 378 = 28×27/2, this is a complete graph among the 28 names with positive mapped positions; the remaining two are isolates. The quarterly input panel has exactly 28 positive-position tickers for every one of its 25 quarters. In the 2020-09 snapshot, those two absent names are **AAPL and TRV**; AAPL remains absent in every quarter of the development position panel. The D4 input bundle likewise has 30 active names but only 28 valid NCP names on 2020-11-27, with AAPL and TRV isolates. A 50-filer cohort with no mapped AAPL position in every quarter is not credible evidence that all large broad-index managers hold a complete Dow basket; it is a strong source-mapping/extraction/coverage anomaly to resolve. It is not explained by binarization: `build_inputs.py` retains positive cosine magnitudes, and the NPZ edge values are continuous and vary. Nor is quarterly `quarter_coverage.csv` produced by simply carrying one graph forward: `panel_edges` recomputes each report-quarter snapshot from that quarter's positions. Daily graphs are carried between filing events as preregistered, but that cannot explain why AAPL has no mapped row in all quarter snapshots.

**Required before treating D4's network as valid:** reconcile the canonical panel against original SEC information tables for selected manager accessions, starting with AAPL CUSIP `037833100`, and audit the ticker/CUSIP mapping and `mapped_dow_position_rows` for AAPL and TRV. Demonstrate whether the absent rows mean true non-ownership, an unmapped or excluded position, or a panel construction omission. Do not assume absent panel rows are zero holdings until this is established; if the panel must be rebuilt, rerun input QA and hash/freeze checks before any outcome access. The existing QA's “50 parsed managers” count is not a resolution: parsed filing count is not the same as per-security mapping coverage.

## SHOULD-FIX

### The near-complete network makes the NCP a broad cross-sectional CLV composite, not a clearly identified peer-transmission measure

For each of 28 connected nodes, `NCP(i,t)` is a normalized weighted average of the other connected names' five-session CLV; there are no absent links within that component to create meaningful sparsity. This is not mathematically identical to the equal-weight market-average CLV because cosine weights differ across pairs and rows. However, with 87% of the possible 30-name links positive and a complete component covering all 28 signal-bearing names, the score can largely act like a leave-one-out broad-market CLV average. A positive mechanism result would not by itself establish that pressure spreads along distinctive common-owner ties; similarly dense rewired/random-link placebos could also approximate a market-wide average.

Before interpreting any D4 mechanism result, report an input-only topology diagnostic: connected components and isolates by roster date, row-wise effective neighbor count/weight concentration, and the signal-only similarity of NCP to the equal-weight leave-one-out CLV5 average. Keep the preregistered tests unchanged unless the coordinator reopens and refreezes the design before outcome access. If network weights do not distinguish NCP materially from the market-average proxy, describe D4 as a broad CLV composite test rather than evidence of network propagation.

### Missing/security-level coverage is not reported at the granularity D4 requires

The frozen D4 specification says not to silently fill missing manager/security holdings with zero and to report manager count and missing coverage for each graph. In `filing_time_network`, `manager_weights` constructs a sparse mapping, then the ticker-by-manager vectors use `.get(ticker, 0.0)`, so an absent position row becomes zero. Parsed filings with zero mapped Dow rows can consequently be included as all-zero manager coordinates, indistinguishable in the graph calculation from a genuine non-holding. The QA reports 50/50 managers with usable filings, but does not show per-date counts for managers with parsed zero-row filings, per-name unmapped/missing coverage, or the age distribution of the 50 managers' latest incorporated positions. This matters particularly given the AAPL support anomaly above.

Add coverage summaries from the existing filing coverage table: current-roster count, managers with usable parsed filing, managers whose latest filing has zero mapped Dow rows, managers with mapped rows, and each manager's filing age (at minimum min/median/max and stale-count). Distinguish confirmed non-holdings from missing/unmapped positions; do not silently convert the latter to zeros. The point-in-time next-session cutoff itself is implemented using `bisect_right` on the filed/availability date, consistent with D4's strict “next trading day” rule. CLV5 is explicitly raw CLV over `t-4:t`, matching the frozen signal window.

## NOTE

### D4 graph mechanics and the central density question

Structural checks on `D4_INPUTS.npz` pass: adjacency has zero diagonal, is symmetric, and every nonzero row in `row_normalized_weights` sums to one within floating-point tolerance; zero rows remain zero. The stored network therefore is not a binary adjacency disguised as continuous input, and row normalization is correct. The fixed support could partly reflect genuine common ownership among very large issuers, but the exact 28-name clique plus the repeated AAPL/TRV omissions means the present files cannot distinguish true density from panel selection/mapping defects. The strongest supported conclusion is “continuous, near-complete common-owner weights on 28 mapped names, with unexplained systematic omissions,” not “50 broad index managers hold every Dow name.”

### D6 development input QA is broadly consistent with the frozen specification

The listed five ETFs, date coverage (2020-06-01 to 2026-10-30), common dates, positive finite OHLC and adjusted-close values, adjusted-open formula, and target/formation month availability align with D6's frozen development design. The QA does not inspect or certify holdout coverage, and correctly leaves that coordinator-only check open. Its description of a “preregistered six-month warm-up” is inaccurate: the frozen primary uses 12-minus-1 trends and 12-month trailing volatility, and the earliest target month is Aug 2021; the available June 2020 start supplies the needed return warm-up. Replace that phrase with “12-month trend and volatility warm-up” (or “13 months of daily price history including the prior-month close”). The QA appropriately caveats that no corporate-action ledger is present, so internal adjustment arithmetic is checked but source adjustment correctness is not independently verified.

## Evidence inspected

- `r4_harness/runs/D4/INPUT_QA.md` and `quarter_coverage.csv`: 25 report-quarter cohorts; repeated 378/435 support and 28 connected names.
- `r4_harness/runs/D4/build_inputs.py`: sparse vector `.get(..., 0.0)` construction, continuous cosine adjacency, row normalization, filing-date next-session index, CLV5 window, and daily carry-forward behavior.
- `r4_harness/runs/D4/D4_INPUTS.npz`: adjacency and row-weight arrays only for structural checks; 30-name roster and 28-name support confirmed on sampled dates.
- `r4_harness/runs/D6/INPUT_QA.md` compared to frozen `specs/r4_prereg/D6.md`; no D6 NPZ returns/signals or holdout data accessed.
