# D6 draft — monthly equity–Treasury cross-asset trend

STATUS: DRAFT — NEXT FALLBACK; NOT FROZEN. No D6 outcome data have been computed.

D6 tests a literature-grounded monthly bond/equity lead–lag with asset-class-appropriate total-return trends. Trend is a slow price-pressure/information proxy, not observed investor flows or signed order flow. The cross-asset link is fixed in advance and cannot be generalized to a broad network.

## Literature basis and limits

Pitkäjärvi, Suominen and Vaittinen document positive bond-trend prediction of equity returns and negative equity-trend prediction of bond returns at monthly frequency in international bond and equity markets ([Journal of Financial Economics, 2020](https://doi.org/10.1016/j.jfineco.2019.02.011)). Moskowitz, Ooi and Pedersen document 1–12 month time-series momentum in futures including equity-index and bond contracts ([Journal of Financial Economics, 2012](https://doi.org/10.1016/j.jfineco.2011.11.003)). These findings motivate the horizon and signs; neither establishes this ETF implementation or proves buying-pressure transmission.

## Fixed universe, timing and signals

- **Assets:** SPY (U.S. equity), TLT (long Treasury), IEF (intermediate Treasury), SHY (short Treasury), and TIP (Treasury inflation-protected securities), from `oos3/xasset/prices-daily`. Do not add or substitute assets. Development availability-only check found all five files with 1,614 daily rows from 2020-06-01 to 2026-10-30 and adjusted-close fields; no returns or signals were calculated in that check.
- **Monthly data:** use each ETF's split- and distribution-adjusted month-end close. Form a signal only after the month-end close is available. For asset `a` and month `m`, define the 12-minus-1-month trend `T[a,m] = adjusted_close[a,m−1] / adjusted_close[a,m−12] − 1`.
- **Cross-class link:** fixed directed links from each of TLT, IEF, SHY and TIP to SPY, and from SPY to each of the four Treasury ETFs. No within-class links. For bond-to-equity, `B[m]` is the equal-weight mean of the four bond trends and predicts SPY's next calendar-month total return, with positive sign. For equity-to-bond, SPY trend predicts the next month's equal-weight mean total return of the four bonds, with negative sign. Each regression includes the target class's own matching trend (SPY trend in the equity target regression; equal-weight bond trend in the bond target regression) so the cross-lag tests incremental direction.
- **Returns and dates:** target return is adjusted month-end close at `m+1` divided by adjusted month-end close at `m`, minus one. Signals use data through `m−1` as specified above, leaving the most recent month out. Do not compute daily or overlapping short-horizon outcomes.

## Primary mechanism test and placebos

Estimate the two predeclared monthly regressions: `SPY_return[m+1] = alpha + beta_BE × B[m] + gamma_E × SPY_trend[m] + error`; and `mean_bond_return[m+1] = alpha + beta_EB × SPY_trend[m] + gamma_B × B[m] + error`. Primary direction is `beta_BE > 0`; secondary is `beta_EB < 0`. Report coefficient, standard error, Newey–West t-statistic with Bartlett lag 11 (the signals use overlapping 12-month histories), sample dates and observations. Primary mechanism pass requires the positive primary coefficient and NW t ≥ 2.0. Report secondary in full, but it cannot rescue a failed primary.

Use 500 placebo draws with seed `20261110`, circularly shifting the cross-class signal/target month alignment by random offsets of at least 12 months while leaving each time series' internal order intact. Also report (a) reversed-link coefficient signs and (b) target-own-trend-only regressions. The primary cross-lag must exceed the 95th percentile of the one-sided block-shift placebo distribution; report all results. If the cross-lag does not add the registered direction beyond the own-trend model, or its randomized alignment is comparable, the transmission hypothesis fails and no portfolio follows.

## Variants and selection rule

1. **Primary:** 12-minus-1-month bond-basket trend → next-month SPY return, positive.
2. **Predeclared secondary direction:** 12-minus-1-month SPY trend → next-month equal-weight bond return, negative.
3. **Fixed sensitivity:** repeat the two regressions with six-minus-one-month trends; this is sensitivity only and cannot replace the primary.

Variant 1 alone determines advancement. Variant 2 and 3 are reported regardless of result. No other ETF, frequency, formation rule or lookback may be selected after outcomes.

## Portfolio and inference, only after mechanism pass

For a secondary portfolio description, at each month-end score the five ETFs by sign-adjusted cross-class signal: SPY receives `B[m]`, each bond ETF receives `−SPY_trend[m]`. Invest 100% in the highest score at the next month's first available open, equal-weight EW5 is the benchmark, rebalance monthly, and break ties by ticker ascending. Formation active share is 80%. Cap total traded notional/NAV at 50% per rebalance and charge 0.05% per traded dollar. Require actual gross active edge at least four times realized costs, positive net excess and higher net Sharpe than EW5.

Use the harness actual-trade engine and one-sided circular block bootstrap with 5,000 draws, 10-month blocks and seed `20261110`; report raw and Holm-adjusted p-values and DSR at full goal trial count 30. Holm applies to the complete family of all preregistered mechanism, placebo-comparison and portfolio endpoints across D4–D6, including sensitivities; enumerate the family before outcomes and do not use a fixed 24-test family. Portfolio pass requires adjusted p < 0.05. D6's portfolio cannot rescue a failed mechanism test.

## Holdout coverage and limitations

The development check found no 2010–2020 rows for these five ETFs in the inspected project corpus. Therefore full-period holdout coverage is **not confirmed**, and D6 is not currently eligible for a holdout pass. Before any outcome testing, a permitted same-asset full 2010-01-01 to 2020-10-31 adjusted-price archive and consistent total-return convention would have to be documented; report exact ticker/date coverage. The sealed country-ETF basket is prohibited and cannot be used as a substitute. Only the coordinator may run a holdout, once, on frozen code and an approved data route. If complete coverage cannot be established, report holdout infeasibility; do not imply that development performance passes the holdout criterion.

## Freeze gate

D6 remains a draft until the five development series' adjusted-close conventions are verified from source metadata, target-month alignment and distribution adjustment are documented, exact full-period holdout coverage is confirmed or D6 is marked infeasible under the goal rule, and the complete D4–D6 Holm family is enumerated before outcome access. Freeze only with `FROZEN: YYYY-MM-DD` and a matching SHA256 after inputs are checked and before any D6 return, signal or test statistic is computed.
