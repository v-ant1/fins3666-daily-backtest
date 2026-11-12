# R10 S2 — SEC filing/event pressure screen

**Status: STOPPED before development outcomes. No candidate is GO.** The six ideas below were registered in `specs/r10_trial_log.md` before any outcome access. The shared monthly event harness failed its synthetic validation after its one allowed retry: the synthetic fixture returned zero variance, exposing a divide-by-zero in the power calculation. In accordance with the trial protocol, no candidate outcomes were run after this validation failure.

| ID | Frozen hypothesis | Dev result / metrics | 2010–2015 buildability | Decision |
|---|---|---|---|---|
| S2-01 | 8-K buyback authorization continuation; monthly event cohort, long issuer, 20 sessions | Not measured: shared harness validation failed before outcome access. Net mean, NW t, Sharpe, turnover, cost share, yearly signs, MDE, and pass probability are unavailable. | SEC submissions and filing archives plus Tiingo/Alpaca prices and PIT S&P roster are plausible; completeness not verified. | No GO; untested |
| S2-02 | 10-Q/K disclosed repurchase activity; top quintile of repurchases / prior shares outstanding, monthly, 20 sessions | Not measured: shared harness validation failed before outcome access. Metrics unavailable. | SEC companyfacts/filings plus Tiingo/Alpaca and PIT roster are plausible; tagged-fact coverage not verified. | No GO; untested |
| S2-03 | 8-K dividend initiation or ≥5% regular-rate increase, monthly, 20 sessions | Not measured: shared harness validation failed before outcome access. Metrics unavailable. | SEC filing text/companyfacts plus Tiingo/Alpaca and PIT roster are plausible; taxonomy and prior-rate coverage not verified. | No GO; untested |
| S2-04 | Official S&P 500 deletion post-effective long reversal; monthly, 20 sessions | Not measured: shared harness validation failed before outcome access. Metrics unavailable. | SEC filings alone cannot build the deletion list; a complete dated official S&P index-change source is also required, in addition to Tiingo/Alpaca and PIT roster. | No GO; data source unverified |
| S2-05 | Priced primary common-stock 424B5 offering reversal; monthly, 20 sessions | Not measured: shared harness validation failed before outcome access. Metrics unavailable. | SEC filings plus Tiingo/Alpaca and PIT roster are plausible; event classification/completeness unverified. | No GO; untested |
| S2-06 | Cash M&A target's same-SIC2 PIT peers, long spillover; monthly, 20 sessions | Not measured: shared harness validation failed before outcome access. Metrics unavailable. | SEC archives and dated SIC plus Tiingo/Alpaca and PIT roster are plausible; deal-party extraction and historical coverage unverified. | No GO; untested |

## GO list

None. No development strategy outcome was computed, so none can meet the required net-mean/NW-t/power qualification rule. The holdout power calculations are also unavailable because the harness did not pass synthetic validation; no pre-2020-11-27 values or sealed holdout files were read.

## Validation record

`r10/S2/event_harness.py` is the one shared monthly cohort engine. The first synthetic-only run failed because the fixture placed the January–June events before the development boundary. That was logged before a single corrected synthetic rerun. The corrected rerun then failed when zero synthetic return variance caused a divide-by-zero in the haircut power calculation. This was logged in `specs/r10_trial_log.md`; the one-retry allowance is exhausted, so outcome access was not authorized. See `r10/S2/SYNTHETIC_VALIDATION.json` only if present; it was not written because validation failed.
