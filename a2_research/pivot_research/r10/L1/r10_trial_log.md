# R10 trial log — L1

## L1-COV-2010-2015 (pre-registered 2026-11-12)

Question: Can a free public source plausibly provide adjusted daily bars for at least 97% of the unique S&P 500 PIT identities active 2010-01-04 through 2015-12-31, including names later delisted/acquired?

Frozen procedure: derive member identities and effective membership intervals by reversing the public Wikipedia historical-components change table back from its documented current component list; count unique security identities and weekday membership-days within 2010-01-04..2015-12-31 (weekdays are a proxy, not exchange calendar sessions). For each unique ticker lineage, issue Yahoo Finance chart GET metadata/history request for that interval through yfinance, retain only response status, returned timestamp count and whether adjusted-close is present; discard price, return, volume, and adjustment-factor values without printing or inspecting them. Report identity-level any-bars coverage as count only, not raw values. Also record source-level adjustment flags and delisted-coverage limitations from official docs. No strategy signal, return, or performance is computed. This is a single source-availability feasibility trial; no retry after a failed per-symbol request except bounded transport retries inside the HTTP client before any response body is parsed.

Inputs: Wikipedia historical components page; Yahoo Finance chart endpoint queried by ticker. Output: metadata/count summary only in HOLDOUT_SOURCE_2010_2015.md. No sealed_holdout* data files are inputs.

Decision rule: GO only if missing identities <=3% appears plausible and split/dividend-adjusted bars are documented. Delisted/acquisition handling must be separately qualified; ticker presence alone does not establish survivor-free corporate-action continuity.
## L1-TIINGO-AVAIL-2010-2015 (pre-registered 2026-11-12)

Question: Does Tiingo's free EOD metadata endpoint cover at least 97% of the same 619-identity candidate roster with historical price start/end dates overlapping the target interval? Metadata-only `startDate`/`endDate` availability checks; do not request or inspect `/prices`, OHLCV, returns, signals, or outcomes. Use an existing API token only if present in environment or loaded via `python-dotenv` from `.env`; never print token or environment contents. GET requests only. The free plan limit is 50 requests/hour and 500 unique symbols/month; do not exceed either limit. Report counts only, and preserve failed/rate-limited status separately from confirmed no coverage. This source feasibility check is separate from L1-COV-2010-2015.
