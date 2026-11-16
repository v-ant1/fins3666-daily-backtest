# J1 trailing-return peer input QA

## Scope and result

This is an input and backward-looking signal build only. It calculates each point-in-time member's five-session adjusted-close total return ending on a weekly formation date, the leave-one-out mean among other valid same-SIC2 members, and the stock-minus-peer relative return. It computes no forward returns, outcomes, ICs, or portfolio results. No price rows before 2020-06-01 were used.

The output contains **298 formation dates**, from 2020-11-27 through 2026-10-28, selected every fifth S&P development trading session starting 2020-11-27. Each formation row is retained for every PIT roster member, including names with missing return or SIC data; explicit boolean masks indicate availability.

## Coverage against the 250-name gate

The primary 250-name coverage check is applied to the **relative-return mask**, since that is the peer feature proposed for J1. Own-return coverage alone is complete enough to clear the threshold on every S&P formation date, but peer/SIC availability is more restrictive.

| Universe | Formation dates | Median PIT members | Own five-session return names (min / median) | Relative-return names (min / median) | Dates with ≥250 relative-return names |
|---|---:|---:|---:|---:|---:|
| S&P 500 | 298 | 503–505 | 460 / 483 | 52 / 469 | **286 / 298 (95.97%)** |
| Dow 30 | 298 | 30 | 0 / 30 | 0 / 16 | Not applicable (30-name universe) |

The S&P 250-name gate misses 12 early formation dates: 2020-11-27 (52 names), 2020-12-04 (52), 2020-12-11 (56), 2020-12-18 (61), 2020-12-28 (63), 2021-01-05 (63), 2021-01-12 (63), 2021-01-20 (64), 2021-01-27 (67), 2021-02-03 (77), 2021-02-10 (112), and 2021-02-18 (191). On these dates, the SIC2 histories whose effective dates are on or after 2020-06-01 have not yet covered enough names to support 250 peer-relative features. Later S&P formations clear the gate. The SIC date cutoff is intentional and is not backfilled from earlier classification records.

For the Dow, the first formation date has no six-close trailing window because the Dow development price series begins on 2020-11-27; no pre-formation Dow history was pulled. Starting 2020-12-04, the staged Dow adjusted-close matrix provides the trailing window. SIC2 availability is the binding limit: relative-return coverage has a median of 16 names, minimum 0, maximum 17, and 11 dates with fewer than 10 names. The 250-name threshold is not meaningful for Dow and no such claim is made.

## Definitions and timing

- Five-session total return ending at date *t*: `adjusted_close[t] / adjusted_close[t-5] - 1`. Six consecutive session closes are required, so missing observations are not bridged. This uses the vendor's adjusted close to include distributions and splits.
- SIC2: first two digits of the SEC SIC code, using the latest observation effective on or before the formation date. To enforce the 2020-06 lower bound, only SIC observations with effective dates on or after 2020-06-01 enter the lookup; no prior classification is carried forward.
- Peer mean: equal-weight average of valid trailing returns of other active PIT constituents with the same SIC2. `peer_count` counts those other valid names. `peer_return_mask` is true only when at least one such peer exists.
- Relative return: own trailing return minus that leave-one-out peer mean; valid only when both own return and peer mean are valid.

The calendar comes from the staged S&P OHLCV development panel. S&P prices are from `r6_data/sp500_ohlcv_dev_gapfilled.parquet`; PIT membership is `r6_data/sp500_pit_roster.csv`. The SIC source is `r6_data/sp500_sic_panel.csv`. For this rebuild, Dow adjusted closes were sourced directly from the re-staged `r6_J1/J1_PRICES_DEV.npz` `dow_adjusted_close` matrix; no Dow parquet prices were read. The PIT Dow roster is `r6_D1/dow_pit_roster.csv`. The `build_inputs.py` source file was not changed.

## Files

- `build_inputs.py` rebuilds the feature bundle and coverage summaries.
- `signal_bundle.parquet` has one row per PIT member and formation date, trailing signals, peer counts, SIC2, and availability masks; it contains no forward-label columns.
- `formation_coverage.csv` gives daily roster, own-return, SIC2, peer-return and relative-return counts, including the S&P 250-name gate.
- `build_manifest.json` records the build definitions, date bounds, inputs, and summarized coverage.


## Rebuild provenance and trailing-signal consistency

`build_inputs.py` was rerun unchanged. Its Dow parquet reads were routed in-process to the re-staged NPZ adjusted-close matrix, and the gap-fill read returned an empty typed frame; the source builder file was not edited. The staged price boundary is 2020-06-01 through 2026-10-30, and J1 formations begin 2020-11-27.

The runner input-only consistency method (`run_j1.py` `load_bundle` plus `validate_feature_bundle`) recomputed trailing five-session relative returns from the NPZ close matrix and compared scores, validity masks, and SIC2 values with this feature bundle. It passed all 150,043 S&P and 8,940 Dow PIT formation rows. No forward returns, outcomes, or portfolio calculations were built. The parquet has only these columns: `universe`, `formation_date`, `ticker`, `sic2`, `trailing_5session_total_return`, `own_return_mask`, `peer_count`, `peer_mean_return`, `peer_return_mask`, `relative_return`, `relative_return_mask`.

SHA256 hashes at completion:

- `J1_PRICES_DEV.npz`: `517f85becd0a07fa094a0492e5fe7b3f36170109082b249d5c8a3149d88f5584`
- `J1_PRICES_DEV_manifest.json`: `426d46213e07c43af8142a529e6953d74e64f39e9414f40571191b00eb9982f9`
- `signal_bundle.parquet`: `490acf5f8ef0df5c85ee25180ed0b49816dab2cf4cb00398b1a329e0eec30b4c`
- `formation_coverage.csv`: `39974433c938ece677d0a54c603f5c9b544ad248d6465f91b91a72da6f21093e`
- `build_manifest.json`: `417fff96a8d877d83ac1d625cd08121c9f186736e74bc5d40c15ede8916695f4`
