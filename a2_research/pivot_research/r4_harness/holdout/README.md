# D4/D5 portfolio runners and coordinator holdout adapter

These files provide the post-mechanism portfolio stage and a one-shot holdout
entry point. Nothing here has run on holdout data. Synthetic tests create all
prices and networks in memory and use temporary lock/prereg files.

## Development portfolio runners

Run from the project root only after the approach is frozen, its mechanism
runner has emitted a passing `MECHANISM_PASS.json`, and the coordinator has
written the full frozen round-wide Holm family JSON:

```powershell
python r4_harness/runs/D4/run_portfolio.py --holm-family specs/r5_holm_pvalues.json
python r4_harness/runs/D5/run_portfolio.py --holm-family specs/r5_holm_pvalues.json
```

Both runners refuse before opening input arrays unless the frozen date/hash and
matching mechanism-pass artifact verify. D4 also refuses its provisional input
bundle when the point-in-time 13F manager roster was unavailable at build time.
A sibling `MECHANISM_FAIL.json` blocks both portfolio and holdout runs.
The Holm file is JSON with `manifest` (the complete, ordered endpoint-name
array, including `D4_v1_portfolio_net_excess` and/or
`D5_v1_portfolio_net_excess` when those portfolio tests are registered),
`manifest_sha256` (SHA-256 of the
UTF-8 endpoint names joined by newlines with a final newline), and `p_values`
(raw p-values for every manifest endpoint except the current runner's portfolio
endpoint, which it calculates). The runner reads the DSR trial budget from
`specs/r4_trials.md`.

D4 reads `D4_INPUTS.npz`; its outcome-blind builder must save `adjusted_open`
and `adjusted_close` in addition to the frozen NCP/roster inputs. D5 reads
`D5_INPUTS.npz`, forms the registered 5-session mean CLV from the stored OHLC,
and aggregates incoming leader pressure over the 20-session SIC graph. The
portfolio fill is the next session's open after each eligible fifth-session
formation. Both runners buy five names, use an equal-weight point-in-time Dow
benchmark, cap total strategy trades at 0.50 NAV per rebalance (D4 measures
benchmark-relative turnover; D5 measures absolute traded notional), charge
0.05% per traded dollar on actual buys and sells, use 5,000 circular 10-session
bootstrap draws with seed 20261110, report active share/turnover/costs/gross
edge/net Sharpe, and apply Holm to the supplied full family.

## Coordinator holdout adapter

Only the coordinator should invoke this CLI after a single frozen D4 or D5
mechanism pass. Supply a point-in-time network bundle and a separate holdout
price folder; no path is chosen by default:

```powershell
$env:ORCA_HOLDOUT_AUTH = 'COORDINATOR_ONLY'
python r4_harness/holdout/run_holdout.py `
  --approach D4 `
  --prereg specs/r4_prereg/D4.md `
  --prices C:\data\holdout_dow_prices `
  --network-inputs C:\data\frozen_D4_holdout_network.npz `
  --mechanism-pass r4_harness/runs/D4/MECHANISM_PASS.json `
  --coordinator-only
```

Both price and network-input paths must explicitly contain `holdout` and are
rejected if any component identifies a development folder (`repo`,
`w1_engine`, `oos3`, or `prices-daily*`). The script verifies the preregistration and matching
mechanism-pass hash, then atomically creates
`r4_harness/holdout/HOLDOUT_RUN_LOCK.json` before opening either network inputs
or prices. That lock is intentionally permanent: a second attempt refuses.
The price loader reads only 2010-01-01 through 2020-10-31 rows and filters the
date before parsing OHLC values. It uses adjusted open/close when supplied, or
adjusts raw open/high/low with the adjusted-close factor. It does not impute
KFT, DWDP, or WBA; UTX uses the disclosed RTX lineage proxy. Results include
primary 5-session IC/NW evidence, reverse and circular 20-session network
checks, and the capped top-five/EW portfolio bootstrap, both with and without
the 2017-09 through 2019-04 DWDP membership window. Since DWDP's price lineage
is unavailable, the exclusion scenario records that its return effect is
necessarily zero rather than imputing it.

The network `.npz` contract is `assets`, `dates`, `adjacency` with shape
`(dates, assets, assets)`, and `roster_mask` with shape `(assets, dates)`.
Optional `network_age_days`, `network_stale_gt_2q`, and `dwdp_membership`
(one boolean per date) are included in the QA report. D4 adjacency is the
dated common-owner cosine graph; D5 adjacency is the directed leader-to-
follower star. The dates must be unique and lie entirely inside the sealed
window. Price files are `{ticker}.csv` with `date`, `open`, `high`, `low`,
`close`, and `adjclose` columns; `adj_open` is optional.

## Synthetic verification

From the project root:

```powershell
python -m unittest r4_harness.holdout.test_holdout_synthetic -v
```

The tests exercise D4/D5 mechanism and portfolio calculations on generated
arrays, verify actual-trade cost reconciliation and the turnover cap, verify
the freeze/hash-to-mechanism-pass gate, reject development paths, and prove
that a second synthetic lock acquisition is refused. They do not open any
holdout path, price file, or real holdout network input.
