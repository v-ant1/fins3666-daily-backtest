# J1 Independent Reproduction Plan

## Purpose and boundary

`repro/j1_reference.py` is a small, independent implementation reserved for reproducing the frozen J1 mechanism after the official L1 development run. It has no project-data execution mode and imports no project runner or `r4_harness` statistic. Its only CLI operation is a deterministic synthetic self-test. The implementation has not been run against the signal bundle's forward returns, OHLCV outcomes, or any holdout data.

I inspected the Parquet schema only. `r6_J1/signal_bundle.parquet` is long form with these fields: `universe`, `formation_date`, `ticker`, `sic2`, `trailing_5session_total_return`, `own_return_mask`, `peer_count`, `peer_mean_return`, `relative_return`, and `relative_return_mask`. For a future reproduction, the J1 score is `relative_return`, filtered by `relative_return_mask` and matched by (universe, formation_date, ticker); `sic2` supplies the within-date shuffle strata. No forward-return field exists in the bundle.

## Registered calculations

For a later authorized development reproduction, construct each name's adjusted forward-five-session return using the frozen J1 timing, then subtract the equal-weight forward return of the other eligible same-SIC2 members on that date. The reference helper `relative_forward_returns` implements that leave-one-out transformation from aligned arrays. The returned relative outcome is matched against the frozen peer-relative trailing return signal.

`datewise_spearman` computes one Spearman rank IC per formation date from the signal and peer-relative forward return, requiring at least three finite eligible names. J1 predicts a negative mean IC. The script reports the direction-adjusted mean as `-mean(IC)` and applies an independently coded Bartlett Newey–West mean t-statistic with lag 4 to the direction-adjusted date-wise IC series.

`sic2_signal_shuffle` holds the outcomes, active mask, SIC2 groups, and group sizes fixed. For each of 500 draws, it permutes signal labels only within each formation-date × SIC2 group containing at least two eligible names; singletons stay fixed. It computes the direction-adjusted mean IC for every draw, the 95th percentile, and the one-sided plus-one p-value `(1 + count(null >= observed))/501`. The registered placebo passes only when the observed direction-adjusted mean exceeds the null 95th percentile and the p-value is below 0.05. Defaults are seed `20261111` and 500 shuffles.

The script does not calculate J1's cost-floor comparison, the Dow portfolio endpoint, Holm correction, DSR, or holdout result; those are outside this independent mechanism reference.

## Synthetic validation

Run with:

```powershell
python report_drafts/repro/j1_reference.py --self-test
```

The deterministic synthetic fixture has 72 dates, 120 names, and 12 SIC2 groups of 10. It plants a negative signal/outcome relationship (`relative_forward = -0.8 × signal + Gaussian noise`, noise SD 0.7) and uses seed `20261111` for the 500 shuffles. The self-test passed: mean IC `-0.73248297`, direction-adjusted NW t(4) `139.1741`, placebo 95th percentile `0.08013202`, one-sided placebo p `0.00199601`, and 500 draws. These are synthetic validation values only; they say nothing about J1's empirical performance.

## When it may be used

After the official J1 runner has completed its single authorized development run, a separate reproduction task can load the frozen signal input and the official development outcome panel, align rows and masks, then call these array functions. It should first verify the frozen bundle hash and the official run's date/ticker alignment, and must not alter the specification, seed, or masks. This plan authorizes no project outcome calculation and no holdout access.
