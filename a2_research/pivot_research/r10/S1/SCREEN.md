# R10 S1 — Price/volume buying-pressure screen

**Date:** 2026-11-12 · **Tag:** S1 · **Decision: NO-GO for freezing all four ideas**

## Decision

Four distinct monthly long-only price/volume hypotheses were registered before outcomes and measured once in a shared development-only run. None meets the stated GO rule (net excess > 0, Newey–West t ≥ 2, and 2010–2015 haircut pass probability ≥ 30%). S1-01 through S1-03 have negative primary net excess; S1-04 is slightly positive but has t=0.17 and only 2.8% estimated pass probability.

| Idea | N months | Gross excess / month | Net excess / month | NW t (lag 3) | Strategy net Sharpe / EW benchmark Sharpe | One-way turnover / total abs notional | Cost share of abs gross excess | Positive years | 2010–15 MDE / haircut pass probability | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| S1-01 Signed abnormal-volume pressure | 62 | +0.049% | −0.106% | −0.66 | 1.06 / 1.15 | 78.5% / 155.4% | 314% | 3/6 | 0.371% / 0.9% | NO-GO |
| S1-02 Volume-weighted close-location pressure | 64 | +0.039% | −0.115% | −0.52 | 0.73 / 0.80 | 78.1% / 154.7% | 393% | 3/6 | 0.519% / 1.1% | NO-GO |
| S1-03 Overnight-return persistence | 60 | −0.245% | −0.398% | −1.45 | 0.67 / 1.06 | 77.4% / 153.2% | 63% | 2/6 | 0.624% / 0.3% | NO-GO |
| S1-04 Volume/return alignment | 63 | +0.177% | +0.021% | +0.17 | 0.91 / 0.91 | 79.0% / 156.4% | 88% | 2/6 | 0.288% / 2.8% | NO-GO |

Sharpe is annualized from monthly net portfolio returns; benchmark Sharpe uses the same monthly holding windows and gross EW PIT S&P returns. Net excess is the mean portfolio return after transaction costs less the gross equal-weight benchmark. Costs at 5/10/20 bp one-way, on the same fixed portfolios, were:

| Idea | 5 bp | 10 bp primary | 20 bp |
|---|---:|---:|---:|
| S1-01 | −0.028% | −0.106% | −0.261% |
| S1-02 | −0.038% | −0.115% | −0.270% |
| S1-03 | −0.321% | −0.398% | −0.551% |
| S1-04 | +0.099% | +0.021% | −0.135% |

## Frozen designs and evidence

All four definitions use the S&P 500 point-in-time roster and adjusted close from `r9/data/J2_DEV_FROM_20201127.npz`, matched to staged in-period daily OHLCV for bar volume/high/low. Each month-end signal ranks eligible constituents, buys the top quintile equally weighted, and holds from formation close through the following calendar month-end close. Benchmark is the EW PIT S&P roster on identical dates. Primary cost is 10 bp one-way times total absolute weight change; the initial cash-to-book transition is charged for its 100% entry notional. No shorting, imputation, or alternative signal thresholds were used.

- **S1-01:** 20-session mean signed return × log abnormal volume (volume over prior 60-session median), scaled by the window's abnormal-volume standard deviation; long high scores.
- **S1-02:** 20-session volume-relative weighted close-location value; long high scores.
- **S1-03:** Mean of the latest 20 adjusted overnight returns; long high scores.
- **S1-04:** 20-session correlation between adjusted close-to-close returns and log abnormal volume; long high scores.

Each signal requires the frozen valid-history criteria in `specs/r10_trial_log.md`. Observed by-year net excess means, in order 2021–2026, were S1-01: −0.071%, +0.130%, −0.391%, +0.404%, +0.082%, −1.248%; S1-02: +0.010%, −0.438%, −0.433%, +0.419%, +0.088%, −0.396%; S1-03: −1.048%, −0.888%, −0.536%, −0.063%, +0.208%, +0.229%; S1-04: −0.089%, −0.309%, −0.193%, −0.016%, +0.294%, +0.698%. Each power calculation uses the requested per-idea family=1, one-sided 5% convention, N=72 monthly holdout observations, and an NW-SE-scaled MDE; it is planning evidence only, not a holdout test.

## Data and limitations

The development panel used only dates 2020-11-27 through 2026-10-30. The shared parquet scan predicate-pushed those dates before reading OHLCV fields and returned 717,569 rows across 566 tickers. The staged QA reports 51 historical PIT names without bar rows, raw OHLC/volume (with adjusted close retained separately), and Yahoo source data; mean cross-sectional coverage in this run was 95.5% of roster for benchmark prices and 91.3% for eligible OHLCV signal names. Missing bars were not imputed. The volume signals normalize raw volume against prior history, but this does not remove every corporate-action or split-volume artifact. No Alpaca SIP GET was made and adjusted-volume quality was not verified.

All four concepts are technically buildable for a 2010–2015 holdout using Tiingo or Alpaca split/dividend-adjusted daily OHLCV, a historical point-in-time S&P roster, and SEC/issuer filing-based ticker/security lineage. SEC filing data are needed to verify roster and security mapping, not to form these signals. The availability and completeness of delisted-name prices, PIT membership, and adjusted volume for that window remain unverified. No 2010–2015 price, event, or outcome values were inspected, and no `sealed_holdout*` file was opened.

## Protocol record

All four definitions were appended to `specs/r10_trial_log.md` before outcome access. The shared `s1_screen.py --synthetic-only` harness passed on generated data. The first real-data attempt stopped before any OHLCV rows or outcomes were accessed because its date filter used string bounds against a timestamp column; this pre-outcome crash was logged, fixed to typed bounds, loader-checked on permitted dates, and rerun once. That corrected single joint development run produced `r10/S1/DEV_RESULT.json`; there was no post-outcome rerun or parameter change. No API credentials were printed, and no orders were placed.

## Artifacts

- `r10/S1/s1_screen.py` — shared harness and one-shot development runner.
- `r10/S1/DEV_RESULT.json` — cohort-level results and frozen metric summaries.
- `specs/r10_trial_log.md` — preregistrations, crash record, and outcome record.
- `specs/r10_decisions.md` — appended decision entry.
