# L1 — Holdout source feasibility, S&P 500 2010–2015

**Date:** 2026-11-12  
**Decision:** **NO-GO on currently verified free sources.** Do not freeze 2010–2015 as the clean confirmation holdout yet. The metadata audit does not establish that the underlying outcome series was opened; it only queried ticker/date availability.

## Counts from the pre-registered availability check

Trial `L1-COV-2010-2015` was recorded before the coverage computation in [r10_trial_log.md](r10_trial_log.md). Membership identities were reconstructed by reversing the public Wikipedia historical change table from the current constituent list. The interval was 2010-01-04 through 2015-12-31.

| Measure | Count |
|---|---:|
| Unique ticker/security identities in the reconstructed member roster | 619 |
| Weekdays used as a trading-session proxy | 1,564 |
| Member-days on that weekday proxy | 800,261 |
| Identities with at least one Yahoo Finance chart timestamp | 419 / 619 (67.69%) |
| Requests that returned non-200 or failed | 197 |
| Successful responses without timestamps | 3 |
| Identities with an adjusted-close array | 419 |

The missing/unresolved bar count is 200 identities (32.31%). Because 197 requests failed or returned non-200, this is a conservative confirmed-availability result rather than proof that all 200 names lack history. Still, the evidence does not make ≤3% missing plausible for Yahoo Finance. Adjusted-close availability was present for the 419 identities with bars; this does not validate corporate-action treatment, cash/stock merger proceeds, or delisting returns. The request bodies were parsed only for timestamps and field presence; no OHLCV or return values were inspected or retained.

The weekday member-day count is a proxy, not an exchange-session count. Wikipedia’s effective-date table is suitable for a candidate PIT reconstruction, but it is a secondary source and requires a constituent-by-constituent audit against the linked S&P announcements before freezing. Share-class changes, symbol reuse, mergers, and ambiguous effective-date timing need identity resolution.

## Source assessment

| Source | Free access and relevant coverage | Decision |
|---|---|---|
| Yahoo Finance chart / yfinance | No API token required for the checked GET path. The metadata run confirmed bars for 419/619 identities only; 197 requests failed or returned non-200. Adjusted-close field present for observed identities. No complete delisted or merger payout guarantee established. | **NO-GO** for a <3% missingness claim. The exact coverage among failed requests remains unresolved. |
| Tiingo EOD | API accounts are free Starter accounts, but require an account/token. Official docs state 30+ years of price history and split/dividend-adjusted fields; they also state delisted data is supported only where the ticker has not been recycled, and some reserved/delisted symbols have no price history. Free API limit is 500 unique symbols/month, below this roster’s 619 identities, so a two-month-or-longer staged pull is required. No token was available through `python-dotenv`/environment, so no metadata endpoint checks were made. | Best remaining **candidate**, but not verified complete; recycled/delisted coverage makes ≤3% unproven. [Tiingo EOD docs](https://www.tiingo.com/documentation/end-of-day), [symbology / delisted coverage](https://www.tiingo.com/documentation/appendix/symbology), [pricing limits](https://www.tiingo.com/about/pricing). |
| Alpha Vantage | Official docs expose a historical active/delisted listing-status endpoint. However, the adjusted daily endpoint is marked Premium; the free daily endpoint gives full history only to Premium keys, with free outputsize limited to 100 most recent points. No free adjusted 2010–2015 panel is established. | **NO-GO** as a free adjusted-history source. [Official API docs](https://www.alphavantage.co/documentation/). |
| Stooq | Free historical downloads may be discoverable, but this audit found no authoritative guarantee of complete historical S&P delisted coverage or dividend/split adjusted prices. No coverage count was established. | **Unverified**, cannot support a GO decision. |
| SEC EDGAR | Free filing headers include `ASSIGNED-SIC`; historical filings provide an as-of SIC observation by CIK and filing date. Use the latest header available as of each signal timestamp, then map four-digit SIC to SIC2; do not substitute today’s issuer SIC. Non-filers and issuer/CIK mapping gaps need explicit handling. | **GO for SIC source feasibility**, subject to filing coverage and point-in-time CIK mapping. [SEC header fields](https://www.sec.gov/edgar/searchedgar/edgarzones.htm), [SEC SIC description](https://www.sec.gov/search-filings/standard-industrial-classification-sic-code-list). |

**Source conclusion:** No single currently verified free path demonstrates survivorship-complete adjusted bars for at least 97% of this roster. Tiingo is the strongest low-cost/free-account lead because its docs explicitly describe adjusted EOD data and some delisted support, but access and per-identity availability need to be verified before calling this a viable holdout. A token-available metadata-only run against Tiingo’s `startDate`/`endDate` endpoint would be the next bounded check; never infer coverage for recycled tickers from current-symbol presence.

## `sealed_holdout_dow` status

This dispatch did **not** open any `sealed_holdout*` data files. It inspected only directory/file metadata and read `sealed_holdout_dow/R6_READINESS.md`, an existing metadata-only readiness note. That note reports Yahoo timestamp coverage for 38 of 41 Dow ticker/security windows, with three zero-row cases (KFT, DWDP, WBA) and an RTX lineage proxy for UTX; it says its OHLCV availability counts came from a separate metadata table and that price, volume, returns, signals, and outcomes were not included. The directory contains per-ticker `*_availability.json` metadata files and separate dividends/FINRA directories; no single top-level manifest file was present. The existing note supports “prior metadata inventory exists,” but I cannot certify from filenames or timestamps alone whether any prior worker ever opened the underlying Dow price files. The J2 confirmation spent the S&P 2016-01 through 2020-10 holdout. The records reviewed here do not establish whether any prior worker ever accessed Dow price data or ran an outcome on the Dow holdout, so its never-viewed status cannot be certified from this metadata audit.

## Constraints and audit trail

- No pre-2020-11-27 price, return, or performance values were printed or inspected. Yahoo responses were GET-only and discarded after extracting timestamps and adjusted-field presence.
- No `sealed_holdout*` data files were opened; no `.env` contents or API keys were printed. The Tiingo credential check used `python-dotenv` and returned only a Boolean availability result.
- No orders, crypto, FactSet, or strategy outcomes were involved.
- Decision entries and the pre-registration are in [r10_decisions.md](r10_decisions.md) and [r10_trial_log.md](r10_trial_log.md); the reproducible count scripts are [coverage_metadata.py](coverage_metadata.py) and [inspect_tables.py](inspect_tables.py).

