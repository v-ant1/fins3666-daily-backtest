# L-BREADTH — Bounded survivorship coverage check

**Decision: NO-GO.** Estimated coverage of delisted names in the liquidity-screened top-1,500 is approximately **62%** by the conservative, annual-capped benchmark method below, with a conditional 95% binomial interval of about **53–71%**. The observed record is too inconsistent by year to support a ≥97% coverage claim, and key systematic uncertainties are not captured by that interval.

## Builder and output boundary

The mechanical builder queried Alpaca's GET asset and daily-bars endpoints only. It loaded API credentials with `python-dotenv` from `A2/.env`; it made no order requests. Daily SIP bars were requested for 2015-01-01 through 2020-10-30. The builder used close × volume in memory only to rank trailing 60-session median dollar volume; it did not print, log, summarize, or plot prices, returns, or dollar volume. API-response caches are confined to `sealed_holdout_broad/build/cache/`.

The asset filter selected `us_equity` records on NYSE, NASDAQ, AMEX, ARCA, and BATS, across active and inactive status. It excluded names containing ETF, ETN, fund, trust, warrant, preferred, depositary, debenture, note, bond, or unit terms; symbols with warrant, unit, rights, or preferred suffix patterns; and symbols longer than eight characters. This is a best-effort common-stock rule; asset names and symbols do not fully identify share classes or corporate actions.

Of 16,089 major-exchange asset records, 7,180 unique symbols remained after that filter. Bars were returned for 4,709 (65.6%); 2,471 returned no bars; 32 single-symbol requests failed. The earliest returned bar date was 2016-01-04, despite the 2015 request start, and the latest was 2020-10-30. Consequently the requested 2015 warm-up is absent and only 58 month-end screens had a full 60-session history.

The counts-only record at `sealed_holdout_broad/build/symbol_bar_coverage.csv` contains first bar date, last bar date, and bar count only (no symbol identifiers). `annual_delist_counts.csv` contains annual counts only. These are bar-availability records; a last bar before the cutoff is a **delisting proxy**, not proof of an exchange delisting.

## Annual comparison

The external reference is a CRSP-based study of U.S. public firms, which reports 28, 40, 32, and 43 delistings in 2016–2019, respectively, with annual sample rates of 1.23%, 1.76%, 1.42%, and 1.90%. It reports no matching 2020 count in that table. Expected top-1,500 counts below apply each reference rate to 1,500 names; 2020 is imputed using the 2016–2019 mean rate and prorated to ten months. “Alpaca top-1,500 proxy” counts names whose last bar precedes 2020-10-30 and that ranked in the top 1,500 at a month-end within the 12 months preceding their own last bar.

| Year | Alpaca last-bar proxy, all filtered symbols | CRSP-based reference delists | Expected top-1,500 delists | Alpaca top-1,500 proxy |
|---:|---:|---:|---:|---:|
| 2016 | 6 | 28 (1.23%) | 18.5 | 0 |
| 2017 | 6 | 40 (1.76%) | 26.4 | 2 |
| 2018 | 140 | 32 (1.42%) | 21.3 | 29 |
| 2019 | 310 | 43 (1.90%) | 28.5 | 72 |
| 2020 through Oct 30 | 168 | No directly comparable table count | 19.7 (imputed) | 48 |

The reference rates come from a CRSP study whose sample declines from 2,273 firms in 2016 to 2,260 in 2019; it is a broad-market benchmark, not an exact risk rate for the more liquid top-1,500. See [Brogaard et al., *Does Shareholder Litigation Risk Cause Public Firms to Delist?*](https://doi.org/10.1017/S0022109023000571), Table 2. The broader CRSP listing-gap literature also identifies mergers and for-cause removals as major delisting channels; see [Doidge, Karolyi, and Stulz, *The U.S. Listing Gap*](https://www.nber.org/papers/w21181).

## Top-1,500 coverage estimate and uncertainty

For each year, the estimated captured count is the smaller of the Alpaca top-1,500 proxy count and the expected top-1,500 count. This prevents the very large 2018–2020 excess counts—which likely include stale histories, symbol changes, or other availability gaps—from offsetting the 2016–2017 shortfall. The capped captured count is about 71.5 names versus 114.4 expected, or **62.5%**. A Wilson interval treating those expected delistings as a binomial reference gives approximately **53–71%**. That interval is conditional on the CRSP reference rates and does not include uncertainty from differing sample definitions, size-specific delist risk, symbol lineage, the 2,471 no-bar records, or the 32 failed requests; those systematic uncertainties are material. Applying a broad-market rate to a liquid universe may itself overstate expected top-1,500 delistings, so this estimate is a screening diagnostic rather than a verified capture fraction.

The annual mismatch is decisive for the gate: the builder observed no top-1,500 dropouts in 2016 and only two in 2017, versus roughly 18 and 26 expected. The later excess cannot establish historical-name coverage because the bar endpoint does not distinguish an actual delisting from a stale or discontinuous symbol history.

## FINRA short-interest history for DTC

**Not verified end-to-end for January 2016–October 2020 from free FINRA sources for this major-exchange common-stock universe.** FINRA's developer center points to an “equity short interest archive,” but the public archive is explicitly under OTC equities; it does not establish listed-stock short-interest coverage for this universe. The repository's staged consolidated short-interest metadata begins 2017-12-29, leaving the 2016–2017 period unverified. This does not clear DTC's historical-input gate. See FINRA's [data API resources](https://developer.finra.org/node/2681) and [Equity Short Interest archives](https://otce.finra.org/otce/EquityShortInterest/archives).

## Reproducibility hashes

- Builder SHA-256: `42984e9a55077f9a0edc339653411eee1fa47aec5a617300498e46aabaf6c203`
- Counts-only bar coverage CSV SHA-256: `4bdce7ab6793567313d2c83ce8d1fbfe5f135853f22278640efe932249f0e09e`
- Annual proxy counts CSV SHA-256: `3d8aca8a4bb3233cd4f3c359803265369921d2c2d6509be740cb48c1f80df277`
- Summary JSON SHA-256: `fa2ee1503504e81c7ab4d6a58de7d8a7d9c7964907a770295a99f72315fde7ce`

## Decision

**COVERAGE < 97% (NO-GO)**
