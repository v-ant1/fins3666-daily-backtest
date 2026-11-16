# Preregistration draft index

All six files are **DRAFT - NOT FROZEN**. None has a FROZEN date or SHA256 line; only the coordinator may freeze after the user selects directions. No outcome data were accessed in preparing these drafts. D1–D5 use the point-in-time Dow universe. D6 is the only cross-asset direction and currently has no confirmed holdout history.

| Draft | Direction | Primary mechanism test | Data readiness | Holdout status |
|---|---|---|---|---|
| [D1](D1_DRAFT.md) | Retail marketable-order pressure | 5-session retail-flow rank IC | TAQ team entitlement and fields unverified | Full holdout blocked by pre-June rule and incomplete lineage |
| [D2](D2_DRAFT.md) | ETF creation demand through holdings | +1:+5 event CAR after demand shock | Daily flow, signed trades and point-in-time holdings unverified | No daily 2010–20 history confirmed |
| [D3](D3_DRAFT.md) | Mutual-fund expected flow through common owners | Next-month NFP rank IC | CRSP source listed; student access and linked holdings extraction unconfirmed | Flow/holdings history and permitted full interval unresolved |
| [D4](D4_DRAFT.md) | 13F common-owner network with daily CLV | 5-session network-pressure rank IC | Dow OHLCV confirmed; parsed historical graph absent | 2010–12 graph and price gaps unresolved |
| [D5](D5_DRAFT.md) | Directed SIC leader-to-follower CLV | 5-session peer-pressure rank IC | Dow OHLCV confirmed; historical PIT SIC absent | PIT network/price gaps and pre-June restriction |
| [D6](D6_DRAFT.md) | Monthly SPY–Treasury ETF trend network | Sign-adjusted next-month rank IC | Five development series date/row metadata available; no outcome values read | No 2010–20 series confirmed |

## Fixed inference and governance

- Portfolio cost: 0.0005 per dollar traded per side; total traded notional cap 0.50 NAV per rebalance.
- Common D1–D5 rank-IC reference hurdle: 0.005481 using r4_harness L1 break-even helper, L1 five-session dispersion 0.0300751, top fraction 5/30 and turnover in excess of EW30 0.0241638. It is a calibration reference, not a forecast or portable alpha estimate. D6 instead has a 2.5 bp/NAV maximum cost at the turnover cap; its five-asset monthly trend is outside the rank-IC helper's Dow assumptions.
- Portfolio inference: 5,000 one-sided circular block-bootstrap draws, seed 20261110, block length 10 observations (daily sessions for D1–D5; monthly observations for D6); Holm over 24 fixed endpoints (18 mechanism variants plus six portfolio endpoints); DSR trial_count=30 for each reported portfolio.
- Budget: 3 variants per dossier = 18 planned variants; 12 slots remain unallocated within the goal-wide 30-variant ceiling. No sweeps. Unused slots stay unused unless the coordinator obtains a new user decision and preregisters them.
- Holdout: full goal interval is 2010-01-01–2020-10-31, but shared data rules prohibit pre-2020-06 Dow return/signal calculations. Current drafts therefore prohibit a full-period holdout pass unless governance resolves the rule conflict; a permitted June–October 2020 subset is explicitly diagnostic only. Coordinator-only one-shot procedure; mandated DWDP include/exclude disclosure remains.

