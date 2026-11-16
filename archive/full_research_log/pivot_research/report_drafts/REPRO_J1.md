# Independent J1 development reproduction

## Scope and inputs

This reproduction used only the J1 development inputs. It did not read or calculate on the sealed holdout, write the R6 trial log, add a variant, or alter the official runner or input bundles.

The verified input hashes were:

| Input | SHA-256 |
|---|---|
| `r6_J1/J1_PRICES_DEV.npz` | `517f85becd0a07fa094a0492e5fe7b3f36170109082b249d5c8a3149d88f5584` |
| `r6_J1/signal_bundle.parquet` | `490acf5f8ef0df5c85ee25180ed0b49816dab2cf4cb00398b1a329e0eec30b4c` |

`RESULTS.md` records the preregistration hash but not these two input hashes; I checked them against the input manifest and QA record instead. The price bundle spans 2020-06-01 to 2026-10-30, with 2020-11-27 as the first J1 formation date. I independently rebuilt the five-session close-to-close leave-one-out SIC2 signal and next-open-to-day-five-close peer-relative forward returns, then passed the date-by-ticker panels to `report_drafts/repro/j1_reference.py` for its lag-4 Newey–West and 500-draw SIC2 shuffle calculations (seed 20261111). The rebuilt signal masks and finite signal values match the feature bundle for all 150,043 S&P feature rows; maximum absolute signal difference was `5.55e-17`.

## Mechanism comparison

| Statistic | `r6_J1/RESULTS.md` | Independent reproduction | To 3 significant figures |
|---|---:|---:|---:|
| Direction-adjusted mean IC | 0.01478633328 | 0.01478633328 | 0.0148 / 0.0148 |
| Direction-adjusted NW t, lag 4 | 2.077041551 | 2.077041551 | 2.08 / 2.08 |
| SIC2 shuffle 95th percentile | 0.005605976313 | 0.005739692428 | 0.00561 / 0.00574 |
| One-sided shuffle p | 0.001996008 | 0.001996008 | 0.00200 / 0.00200 |

The observed IC, Newey–West statistic, and randomization p-value reproduce. The placebo 95th percentile differs by `0.000133716` (about 2.4%). The independent reference helper visits SIC2 groups in sorted-label order, while the frozen runner's helper visits groups in first-ticker-encounter order; with a fixed pseudorandom seed, that changes which permutation draws are assigned to each group. Both 500-draw distributions still put the observed statistic above the 95th percentile, and both p-values imply zero null draws at least as extreme as observed. This is a finite-simulation difference, not a change in the input mask, statistic, draw count, or seed.

## Dow portfolio check

I separately replayed the Dow top-five strategy and EW30 from the same development price arrays using the frozen five-session signal, weekly formation, next-open execution, 50% traded-notional cap, and 0.05% traded-notional cost. The independently replayed annualized net Sharpe was **0.815** for J1 and **0.902** for EW30, a difference of **−0.0871**. Both are below the EW30 benchmark, confirming that J1 fails the required Sharpe comparison.

The independent replay's cumulative net excess was −2.66%, whereas `RESULTS.md` reports +1.03%. This portfolio-level discrepancy means the replay confirms the Sharpe failure but does not fully reconcile the official portfolio path; execution handling of sparse bars/held-name availability should be compared before describing the portfolio replay as an exact replication. The official H9 p-value remains 0.449 (Holm adjusted 1.000), so H9 fails independently of the adverse Sharpe comparison. No holdout result is reported here.

## Conclusion

J1's primary development mechanism and placebo p-value reproduce at three significant figures; the placebo percentile has the disclosed finite-shuffle ordering discrepancy. An independent portfolio replay also finds a lower net Sharpe than EW30, consistent with the official Sharpe failure, although its cumulative excess return does not reconcile with the official output. The full H9 portfolio path is therefore a **NOT passing** result, not a success; the net-return path discrepancy should be resolved if an exact portfolio reproduction is required.
