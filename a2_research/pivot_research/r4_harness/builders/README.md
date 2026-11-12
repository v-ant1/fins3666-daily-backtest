# Phase 3 candidate builders

These outcome-blind builders prepare the two network-pressure candidates in
`r4_L3/BUILDABLE.md`. They construct features only: there is no forward-return
input, mechanism test, portfolio, or holdout runner here. Functions do not
mutate input arrays or write files; seeded random builders are reproducible.

## Inputs and outputs

Import with `from r4_harness.builders import ...`.

| Builder | Inputs | Output |
|---|---|---|
| `build_common_owner_network` | asset names, sorted dates, L4 cosine edge rows (or default `r4_L4/data/13f_cosine_overlap_edges.csv`) | `dates × sources × targets` symmetric weighted cosine graph |
| `build_trailing_clv_pressure` | high, low, close matrices (`assets × dates`); default 63-day window and 20 prior observations | `assets × dates` CLV z-scores; normalization for date *t* uses only observations before *t* |
| `build_peer_pressure` | CLV scores and a dated network; default one-day lag | `assets × dates` weighted incoming peer pressure; for target *t*, source scores and network are both from *t−1* |
| `build_dated_industry_network` | assets, sorted dates, close and volume (`assets × dates`), `industry_at(asset,date)` provider | `dates × sources × targets` directed graph, higher trailing dollar volume to lower within the same SIC; uses only volume through the prior date |
| `degree_preserving_shuffle` | symmetric network cube, fixed seed | shuffled symmetric graph with per-date node degrees and edge-weight multiset preserved |
| `reverse_direction` | directed network cube | transposed edge direction per date |
| `matched_same_industry_nonowners` | common-owner network, assets/dates and dated industry provider | sampled non-owner pairs matched to the owner-edge count within each industry/date |

The common-owner builder consumes L4's already computed 13F portfolio-value
cosine table. `panel_availability_date` is the latest filing date among the
parsed manager filings for that panel. The builder activates each report
quarter only on that date, then carries the most recent available quarter
forward until the next panel is public. It does not use `report_date` as an
availability date. L4 stores filing/publication dates at calendar-day
resolution, not SEC acceptance timestamps; the builder honors the recorded
date as its as-of threshold. A preregistration should conservatively lag a
filing-date observation by one session if within-day acceptance time is
unavailable. For example:

```python
from r4_harness.builders import build_common_owner_network, load_13f_cosine_edges

edges = load_13f_cosine_edges()  # L4 13F links only; no price/outcome fields
network = build_common_owner_network(tickers, dates, edges)
```

For daily pressure and lagged neighbor pressure:

```python
from r4_harness.builders import build_trailing_clv_pressure, build_peer_pressure

clv = build_trailing_clv_pressure(high, low, close)
peer_clv = build_peer_pressure(clv, common_owner_network, lag=1)
```

## Dated SIC data gap

L4 has only `r4_L4/data/issuer_sic_snapshot.csv`, which is current SIC
metadata. It is not a point-in-time history and this builder deliberately
does not load it. Candidate 2 requires a caller-supplied historical sequence
with at least `asset`, `sic`, and `available_date` fields (the date the SEC
filing made that classification public). `sic_provider_from_records` creates
an `industry_at(asset, date)` lookup that returns the newest visible SIC only
after its filing date. Example:

```python
from r4_harness.builders import sic_provider_from_records, build_dated_industry_network

industry_at = sic_provider_from_records(dated_sic_rows)
directed = build_dated_industry_network(
    tickers, dates, close, volume, industry_at, lookback=63,
)
```

Until L4 or the coordinator supplies that dated panel, Candidate 2 cannot
produce a real PIT graph. No fallback to current SIC or retrospective industry
labels is permitted. The leader rank uses trailing average dollar volume
(`close × volume`) through *t−1*, as the specified OHLCV attention/liquidity
proxy; this is not direct investor attention or market capitalization. The
graph connects all strictly ranked same-industry pairs, with unit edge weights
and no edge for volume ties.

## Placebo builders and timing

The degree shuffle rewires each undirected date slice independently using
double-edge swaps and a fixed seed. It preserves degree and the date slice's
weights, while breaking the observed counterparty identities. The reversed
placebo swaps source and target. The matched non-owner placebo samples
same-industry pairs with no common-owner edge at that date, matching the
number of owner edges per SIC where candidate pairs are available. It returns
fewer placebo edges where the industry has insufficient non-owners. Pass the
network snapshot visible at the signal date; these utilities never infer a
future network.

## Validation

From the project root run:

```powershell
python r4_harness/builders/run_tests.py
```

The synthetic tests check future-truncation invariance for each dated builder,
signal, peer aggregator, and placebo generator. One additional data-only check
reads the existing L4 13F edge table to verify that the network remains empty
before the panel filing date and becomes available on that date. It reads no
prices, returns, event outcomes, or holdout observations. Full output is saved
to `r4_harness/builders/TEST_OUTPUT.txt`.
