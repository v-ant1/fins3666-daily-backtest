# S&P 500 2010–2020 holdout feasibility and build plan

**Prepared:** 2026-11-11 (AEDT)  
**Tag:** L-SP  
**Decision:** **NO-GO with staged/free inputs currently available. No sealed panel was built and no outcome data was opened.**

## Feasibility finding

The required point-in-time daily S&P panel cannot be assembled cleanly from the staged files. `r6_data/sp500_pit_roster.csv` contains 623 intervals for 622 ticker identities, but its coverage starts on 2020-06-01. The staged S&P OHLCV panel also starts on 2020-06-01, covers 571 identities, and leaves 51 roster identities without any usable bars. The staged daily file has raw OHLC, adjusted close and volume; adjusted open can be derived from raw open and close ratios only where bars exist. It contains no 2010–2020 observations.

The separate `sealed_holdout/` price folder is an ETF basket, including SPY, rather than constituent-level S&P history. Its runner uses a 2020-11-27–2026-10-30 development interval. `sealed_holdout_dow/` is Dow-specific and cannot supply the remaining S&P members. Staged Alpaca partitions start in 2020-11 and are not a pre-2020 S&P history source. I did not open any price, return or volume observations.

The staged SIC panel is based on SEC 10-K headers from 2019-01-01 onward, so it does not provide the requested 2010–2018 as-of SIC2 history. SEC EDGAR is a plausible free source for reconstructing filing-date SIC history, but it does not supply prices or the missing PIT membership and delisted-security price histories. The repository contains no UNSW FactSet extract or evidence that an authorized FactSet feed with inactive constituents, adjusted OHLC and effective-dated SIC is available. A free Yahoo Finance rebuild would still leave survivorship and history gaps: the staged QA already records 51 unresolved symbols and warns not to substitute an acquirer’s history.

The 51 unresolved names are `ABMD, ALXN, ANSS, ATVI, AVB, CDAY, CERN, CMA, CTLT, CTRA, CTXS, CXO, DAY, DFS, DISCA, DISCK, DISH, DRE, EA, ETFC, FLIR, FRC, GPS, HBI, HES, HFC, HOLX, INFO, IPG, JNPR, JWN, K, KSU, KVUE, LEG, MRO, MXIM, NBL, NLSN, PBCT, PXD, QRVO, SBNY, SEE, SIVB, TIF, TWTR, VAR, WBA, WBD, XLNX`. This is the later staged roster’s unresolved set, not a complete list of missing 2010–2020 constituents; the historical holdout roster itself is absent.

## Prior-computation and overlap check

No S&P 2010–2020 holdout panel or return-result artifact appears in repository filenames. The D7 build under `sealed_holdout_dow/D7` is an event/link/SIC metadata builder, and its runner is explicitly restricted to 2020-11-27–2026-10-30 development data. Repository text-log searches for the 2010–2020 S&P holdout window found no matching run log. This supports “no evidence of a prior S&P holdout return computation in the checked repository artifacts”; it is not a claim about logs outside this workspace. No staged holdout prices were opened.

S&P membership includes Dow constituents, so a full-universe S&P holdout would share names and dates with J2’s Dow holdout. The cleanest future design is to exclude, before either holdout is opened, every issuer that was a Dow member at any point in the holdout, and to use a correspondingly defined equal-weight S&P-ex-Dow benchmark. That removes security overlap, though both tests still share calendar and market shocks. If the full S&P universe is used instead, report the overlap and put both tests in the same Holm family; do not describe them as independent confirmations.

## Conditional build plan

1. Obtain a permitted, auditable history source that explicitly covers all S&P membership intervals from 2010-01-01 through 2020-10-30, including inactive and delisted issuers, adjusted open/close, corporate-action lineage and effective-dated SIC. Prefer a UNSW FactSet extract if its access and fields are confirmed. Use SEC EDGAR filing headers for as-of SIC2 only if the historical source does not provide a suitable classification history.
2. Build the point-in-time roster from the source’s dated membership history; do not backfill the current roster or use surviving names only. Preserve CIK/security lineage across ticker changes. Reject any member-date lacking its own valid adjusted bars; never replace it with an acquirer’s bars.
3. Derive adjusted open using the documented adjustment factor and verify adjusted close/open and corporate-action lineage. Carry SIC2 forward only from its first US trading session strictly after the SEC filing/acceptance date, within the applicable issuer lineage. A missing SIC2 makes that name ineligible for SIC2 peer calculations on that date, as J1 already specifies: known SIC2 and at least one other eligible same-SIC2 peer are required; no broadening, imputation or retroactive current SIC.
4. Produce a deterministic NPZ on the XNYS calendar with the J2 development key names and dtypes: date and asset arrays, membership and SIC2 matrices, and adjusted open/close matrices. If the J2 holdout runner needs the Dow portfolio arrays as well, derive the Dow subset from the same sealed PIT source and preserve the corresponding Dow keys. Save only the panel and metadata QA outputs; do not compute signals or returns during the build.
5. Before access by strategy code, write a build report containing source coverage, row counts, missing-name lists and file hashes; hash the exact panel bytes with SHA-256; record the hash in `specs/r9_sp500_holdout_seal.md`; set read access through a runner gate that refuses mismatched hashes and disallows raw panel access to strategy-development code. The runner should allow only the frozen-spec hash, approved strategy entrypoint, one-shot marker and aggregate result output. Any build repair invalidates the seal and requires a new review before access.

## Time estimate and gate

With an available FactSet extract that already includes historical constituents, adjusted daily bars and effective-dated classifications, allow about 4–8 hours for mapping, deterministic assembly, metadata QA and sealing. If only public/free sources are allowed, historical roster reconstruction, delisted-price recovery and SIC backfill would likely take multiple days and still may not resolve every member; that route is not a reasonable basis for a clean confirmatory holdout without a complete licensed or archival source.

**Current gate: NO-GO.** Do not create `sealed_holdout_sp500/` until a complete source is identified and its inactive-security coverage is established from metadata. The J2 development NPZ schema was inspected by keys, shapes and dtypes only. J1’s preregistration covers unavailable SIC2 mechanically: only known same-SIC2 peers qualify, and a target needs at least one other eligible peer. No strategy spec idea is included here because the coordinator reassigned that work.
