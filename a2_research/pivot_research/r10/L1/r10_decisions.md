# R10 decisions — L1

- 2026-11-12 [L1] Scope accepted: only metadata/count-only source feasibility for a fresh S&P 500 2010-01-04..2015-12-31 candidate; no pre-2020-11-27 prices/returns or sealed data access. All new artifacts remain under r10/L1 because the dispatch forbids editing existing files; this file is the L1-scoped decision-log copy.
- 2026-11-12 [L1] Pre-logged trial L1-COV-2010-2015 in r10/L1/r10_trial_log.md before executing any coverage computation.
- 2026-11-12 [L1] Pre-logged separate Tiingo metadata feasibility check L1-TIINGO-AVAIL-2010-2015; no tokens will be displayed and no price endpoint will be queried.
- 2026-11-12 [L1] L1-COV-2010-2015 returned 619 reconstructed identities, 1,564 weekday session proxies, 800,261 weekday member-days, and Yahoo any-bar presence for 419 (67.69%); 197 requests failed/non-200 and 3 successful responses had no timestamps. Decision: NO-GO for Yahoo; <=3% missing is not plausible on verified coverage.
- 2026-11-12 [L1] Tiingo is a conditional candidate only: docs cover adjusted EOD and limited non-recycled delisted symbols, but free plan caps 500 unique symbols/month and current workspace has no token. No Tiingo coverage result claimed.
- 2026-11-12 [L1] SEC EDGAR filing-header ASSIGNED-SIC supports as-of SIC2 by filing date/CIK. `sealed_holdout_dow` was inspected only via file metadata and existing R6_READINESS.md; this dispatch did not access its data files. Historical use by all prior workers cannot be certified from metadata alone.
