# FINRA short-interest sample pull

This folder contains two complete, development-period FINRA Consolidated Short Interest API responses and count-only feasibility metadata. No price or return data were loaded, no outcomes were computed, and no pre-2020 archive records were downloaded or opened.

## Raw responses

- `FINRA_SI_20211215.csv`: FINRA settlement date 2021-12-15; 20,312 rows excluding header.
- `FINRA_SI_20251215.csv`: FINRA settlement date 2025-12-15; 21,107 rows excluding header.
- Both were obtained from `https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest` with a settlement-date equality filter and offset paging through the API's `record-total`; file hashes are in `sample_manifest.json`.
- The 2021-12-15 PIT roster match is 494/505 S&P 500 members and 30/30 Dow names. The 2025-12-15 match is 499/503 S&P 500 members and 30/30 Dow names. Every matched member had a numeric short-position value and positive reported average daily volume. Missing symbols remain missing; they are not interpreted as zero.

## Historical availability only

`archive_availability_counts.json` summarizes FINRA's public OTC archive index metadata without opening any archived security records. It lists 112 file entries from 2014-11-14 through 2019-06-28, and zero entries in 2010. This OTC archive is not a historical all-listed dataset. FINRA's January 2023 release note says consolidated short interest data covers a rolling five-year period and includes all exchanges from June 2022; this does not establish free FINRA-wide listed-security coverage back to the sealed holdout. A 2010 all-listed holdout panel remains unverified.

`sample_coverage.csv` gives the PIT universe and match counts by sample date. `power_sim.json` contains the outcome-free 54-SIC2-cluster power scenario reported in `r6_ideas/L.md`.

## Relevant public documentation

- [FINRA Consolidated Short Interest catalog](https://developer.finra.org/catalog)
- [FINRA January 2023 API release note](https://developer.finra.org/release-notes/january-2023-release-notes)
- [FINRA OTC archive listing](https://otce.finra.org/otce/EquityShortInterest/archives)
- [FINRA Rule 4560](https://www.finra.org/rules-guidance/rulebooks/finra-rules/4560)
- [FINRA short interest vs daily short-sale volume explanation](https://www.finra.org/investors/insights/short-interest)
