# L1B — Tiingo historical coverage check

**Date:** 2026-11-12  
**Decision: PARTIAL.** The metadata pass queried 50 of 619 reconstructed roster tickers, prioritizing names removed from the current S&P 500 roster. This is not enough to establish the <=3% missing threshold.

## Scope and method

The pre-registered trial `L1B-TIINGO-500` is recorded in `specs/r10_trial_log.md`. The 619-ticker roster follows the prior L1 historical-components reconstruction. Of those 619, 271 are absent from the current constituent list; the first 50 queried were selected from that removed set. No `sealed_holdout*` file was opened, and no prices endpoint or price/return/volume values were requested or inspected.

The script called only `GET /tiingo/daily/<ticker>` after loading `KEY` through `python-dotenv` from the specified A2 `.env`. It converted periods to Tiingo hyphens. Calls were spaced by at least 72.5 seconds, with no retries. Credential values were never printed. The helper is `r10/L1B/tiingo_metadata_check.py`.

## Partial results

| Measure | Result |
|---|---:|
| Reconstructed roster | 619 tickers |
| Removed from current roster (hard-case priority pool) | 271 |
| Queried | 50, all from the removed pool |
| HTTP 200 | 45 |
| Full 2010-01-04 through 2015-12-31 date span reported by metadata | 25 / 50 (50%) |
| Successful responses not meeting that full-span check | 20 / 50 (40%) |
| Transport errors | 4 / 50 (8%) |
| HTTP 404 | 1 / 50 (2%) |

The 20 tickers that did not meet the full-span check were: **AA, ALTR, ANR, APC, APOL, AYE, BBBY, BEAM, BIG, BJS, BMC, BRCM, BTU, BXLT, CA, CAM, CBE, CCE, CEPH, CFN**. These are not confirmed membership-window misses: the executed comparison required metadata dates to span the entire six-year target interval, which is stricter than checking each ticker's actual PIT membership interval. Therefore 25/50 is a confirmed full-target-span count, while the requested membership-window coverage and roster-wide missing percentage remain undetermined. The four transport-error tickers and the 404 ticker were not retained individually in the emitted summary and are unresolved.

No response ticker differed from its request ticker, so the script flagged zero ticker-string mismatches. This is not a complete recycled-symbol audit: the response metadata's issuer name was not retained for historical-name matching, and Tiingo documents that delisted support applies to tickers that have not been recycled. Accordingly, no recycled-ticker ambiguity was cleared; the 50 removed names remain subject to identity review. This limitation prevents a GO or NO-GO conclusion.

## Quota and next run

The current Starter tier documentation lists 500 unique symbols per month, 50 requests per hour and 1,000 per day. This pass used 50 unique symbols, leaving room for at most 450 additional unique symbols under the current monthly allowance; those can be checked after the rolling hourly limit permits, paced at the same rate. The remaining 119 roster tickers beyond the 500-symbol monthly allowance can first be checked on **2026-12-01**, assuming the documented monthly quota resets at the start of the calendar month. Complete the remaining removed/delisted names before current constituents.

## Source notes

Tiingo describes `/tiingo/daily/<ticker>` as the metadata endpoint, with `startDate` and `endDate` indicating the earliest and latest available price dates. Its documentation maps dot share-class symbols to hyphen form and says delisted data is supported only where the ticker has not been recycled. Pricing currently lists the Starter caps above. Sources: [EOD API documentation](https://www.tiingo.com/documentation/end-of-day), [Tiingo symbology](https://www.tiingo.com/documentation/appendix/symbology), [Tiingo pricing](https://www.tiingo.com/about/pricing).

**Conclusion:** **PARTIAL** — the check did not establish membership-window coverage for the full roster, and no <=3% missingness claim is supportable from the sampled full-span results.
