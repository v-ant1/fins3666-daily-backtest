# Round 5 network data update - current files

This section supersedes the Round 4 13F and SIC status below. The files are data-only; no prices, returns, signals, or backtests were accessed.

## Current coverage

| Dataset | Development | Holdout / historical replicability | Availability rule and gaps |
|---|---|---|---|
| Common ownership: quarterly 13F top-50 | `13f_development_pit_positions.csv` and the canonical `13f_holder_by_dow_stock.csv` contain 236,398 Dow-name position rows from 2020Q2 through 2026Q2 (25 quarters; all 36 development-universe names have at least one reported position). The roster is recalculated each quarter from the 50 largest reported `TABLEVALUETOTAL` filings. | `13f_holdout_positions.csv` contains 231,434 rows for 2010Q1-2020Q3 (41 names, with UTX/RTX kept under the point-in-time UTX label during the 2020Q2 report period). For 2013Q1-2020Q3, 50 CIKs are ranked each quarter from SEC bulk data except 2013Q1, where the released archive contains 46 original filings. For 2010Q1-2012Q4, the best feasible fallback is the fixed Q2 2026 top-50 CIK set parsed from individual filings: 441 filings were found and parsed across 600 manager-quarter checks; coverage is 35-38 filings per quarter, 39 managers have any filing, and 33 have all 12. This is not a historical top-50 ranking. | Rows retain SEC filing date in `availability_filing_date`; use a filing from the next trading day. A complete quarter roster is conservatively available after the later of quarter-end + 45 calendar days or the latest selected top-50 filing date (`full_roster_available_after`). Q3 2020 filings extend to 2020-11-19, after the holdout end of 2020-10-31; therefore Q3 2020 cannot be used inside that holdout. Original 13F-HR filings only; amendments excluded. Missing filings and filings with no mapped Dow positions remain distinct in coverage files. |
| Historical SIC from 10-K headers | `sic_panel.csv` has 778 dated SIC observations for 45 Dow ticker/security identities: 736 filing records from 2010-01 through 2026-10 plus 42 pre-2010 seed records, dated 2009-01-30 through 2026-09-02. Every row has a SIC value; `sic_panel_coverage.csv` reports per-name ranges and `sic_panel_gaps.csv` has zero unresolved in-window names. `sic_panel_seed_gaps.csv` lists DOW, DWDP, and WBA, which were not yet the relevant Dow issuers at the start of 2010. | Same filing-header construction covers all names and the holdout years; SIC is the code printed in the 10-K header, effective from that filing date. | Annual filing observations are point-in-time. Carry the latest filed SIC forward only after its `effective_from` date; no current SIC is backdated. `source_url` points to the SEC `.hdr.sgml` for the source 10-K. |
| ETF co-membership (N-PORT-P) | Unchanged from the Round 4 files: SPY, DIA, QQQ and the Select Sector SPDR panel is available from the observed 2019-10 onward. | No 2010-2018 N-PORT history; only the tail of the holdout can be replicated from this source. | See `etf_dow_comembership.csv`, `etf_nport_filing_coverage.csv`, and the source limitations below. |
| Customer-supplier | Not built. | No consistent free historical named-link panel. | 10-K major-customer disclosures are uneven and frequently anonymized; see feasibility note below. |

## 13F files and schemas

- `13f_top50_pit_roster.csv`: one row per selected filer and report quarter, with rank by reported 13F value, CIK, name, accession, filing date, and selection source. It contains 2,696 SEC-bulk roster rows for 2013Q1-2026Q2 plus 600 pre-2013 fallback slots; 2013Q1 has 46, all later bulk quarters have 50.
- `13f_holdout_positions.csv`: the same 12-column schema as the development panel: `report_date`, `availability_filing_date`, `manager_cik`, `manager_name`, `accession_number`, `ticker`, `cusip`, `reported_issuer`, `share_class`, `value_usd_thousands`, `shares_or_principal_amount`, and `amount_type`. It stores Dow-name position rows only.
- `13f_development_pit_positions.csv` and canonical `13f_holder_by_dow_stock.csv`: quarterly point-in-time top-50 development positions, with the same schema.
- `13f_holdout_coverage.csv` and `13f_development_coverage.csv`: filer-quarter status and mapped Dow-row counts. A parsed filing with zero Dow rows is not treated as missing.
- `13f_pit_cosine_overlap_edges.csv`: pairwise cosine overlap of each Dow name's vector of top-50 manager-reported position values, for holdout and development periods. The canonical `13f_cosine_overlap_edges.csv` is refreshed with the point-in-time development edges.
- `13f_pit_quarter_availability.csv`: quarter-level latest selected filing date and conservative full-roster availability date.
- `13f_holdout_pre2013_positions.csv` and `13f_holdout_pre2013_coverage.csv`: raw text-parser outputs for the 2010Q1-2012Q4 fallback set. The combined `13f_holdout_positions.csv` and coverage table include them.

SEC bulk data are used to rank each report quarter by reported table value for 2013Q1 onward. The bulk series begins with the archive for filings reporting 2013Q1; its archive has only 46 distinct original filers in that period. Before then, we used the same 50 CIKs ranked by reported 13F value in Q2 2026, queried their EDGAR submission indexes, and parsed each available original filing's information table text. Of 600 manager-quarter slots, 441 filing documents were available; all 441 were parsed without download or parse errors. The legacy text parser does not populate `share_class`, so that field is blank for these pre-2013 rows. The fixed set is an explicit fallback and must not be described as the historical top 50.

The SEC bulk coverage period used here is 2013Q1-2026Q2. The development extract begins 2020Q2 and ends 2026Q2; Q3 2026 was not in the development cutoff. Filing date is the SEC `FILING_DATE` day, not an intraday timestamp. Per the binding Round 5 decision, a filing is usable only from the next trading day after that date. The full quarterly top-50 identity set is delayed to the `full_roster_available_after` date so the roster is not selected with future filings. Position rows preserve the original accession and reported values; CUSIPs are mapped to the point-in-time Dow membership, with issuer-name overrides for DD/DWDP/DOW lineage and verified legacy aliases for AA, HPQ, AAPL, and TRV.

## SIC construction

`build_sic_panel.py` takes SEC `10-K` filing dates from issuer submissions, selects the first 10-K filed in each calendar year, then reads only the filing's small EDGAR `.hdr.sgml` header and extracts `<ASSIGNED-SIC>`. `add_sic_legacy_issuers.py` supplies DIS history under its earlier CIK (1001039) before the current CIK (1744489), and `add_sic_pre2010_seed.py` adds the latest pre-2010 10-K for issuers that existed at the start of 2010. `effective_from` is the SEC filing date, not fiscal year-end. The ticker list includes every security identity in the reconstructed 2010-2026 Dow roster, including legacy names and the UTX/RTX lineage; `sic_panel_gaps.csv` records missing in-window names or headers. The three absent pre-2010 seed entities are separately listed in `sic_panel_seed_gaps.csv`. Current SEC submissions SIC is not backdated as a historical substitute.

## Rebuild commands

Run from `C:\Users\musta\Desktop\UNSW\SSI\FINS3666` with Python 3 and `requests` installed. SEC requests use the descriptive project User-Agent and a 0.18-second pause.

```powershell
python A2\pivot_research\r4_L4\data\rank_13f_top50.py
python A2\pivot_research\r4_L4\data\build_13f_holdout_metadata.py
python A2\pivot_research\r4_L4\data\build_13f_holdout_pre2013.py
python A2\pivot_research\r4_L4\data\build_13f_pit_bulk.py
python A2\pivot_research\r4_L4\data\assemble_13f_pit.py
python A2\pivot_research\r4_L4\data\build_sic_panel.py
python A2\pivot_research\r4_L4\data\add_sic_legacy_issuers.py
python A2\pivot_research\r4_L4\data\add_sic_pre2010_seed.py
```

The holdout builder requests only SEC 13F filing text and metadata; it never requests price data. Sources: [SEC Form 13F data sets](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets), [SEC EDGAR API documentation](https://www.sec.gov/edgar/sec-api-documentation), and [SEC Form 13F FAQ](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f). The common-owner framing is related to Anton and Polk (2014), "Connected Stocks," DOI [10.1111/jofi.12149](https://doi.org/10.1111/jofi.12149); the CSVs are not a reproduction of that paper's full construction.

---

# Round 4 baseline data coverage (historical snapshot; see the Round 5 update above)

**Status: partial.** The common-ownership panel now uses 50 managers ranked by SEC 13F value, with a filing-index-only check of those same CIKs for 2010Q1-2020Q3. An SEC N-PORT holdings-weight panel is built for SPY, DIA, QQQ, and the 11 Select Sector SPDR funds. The iShares style ETF panel is not built, 2026Q3 13F holdings were not public by the 2026-10-30 development cutoff, and SEC submissions expose only current SIC metadata in this build.

## Dataset coverage

| Dataset | Development coverage | Holdout coverage / replicability | Availability and gap |
|---|---|---|---|
| Common ownership (13F) | 50 managers ranked by Q2 2026 13F table value; 324,137 Dow position rows, all 36 roster tickers, 25 quarter ends from 2020-06-30 through 2026-06-30. `13f_cosine_overlap_edges.csv` has 9,828 pair-quarter rows. | Same 50 CIKs checked against SEC submission-index metadata for 43 quarter ends, 2010-03-31 through 2020-09-30. 1,706 of 2,150 manager-quarter entries have an original 13F-HR filing; 42 managers have at least one old-quarter filing and 31 have a filing for every quarter checked. No holdout position tables were downloaded or parsed. | Position rows use each manager's original 13F-HR filing date. The complete quarter matrix is available only at the latest included manager filing date in `panel_availability_date`. Q3 2026 is recorded as not yet available: quarterly reports are not due until after the 2026-10-30 cutoff. |
| ETF co-membership weights (N-PORT-P) | 2,995 Dow holdings-weight rows from 379 target-fund filings for SPY, DIA, QQQ, and all 11 Select Sector SPDR funds. The build checked 423 candidate filings and excluded 44 other premium-income series. Report dates in the matched-holdings file range from 2019-10-31 to 2026-07-31; filing availability dates range from 2019-12-13 to 2026-09-18. | SEC public N-PORT data starts in 2019-10, so only the last year of the 2010-2020 holdout is in principle available; 2010-2019 cannot be reproduced from this source. | Each row uses the SEC N-PORT `pctVal` field and filing date. Use `etf_nport_filing_coverage.csv` to see all candidate filings; 44 unrelated premium-income series are marked `series_not_mapped`. XLRE and XLU had target fund filings but no matched Dow constituents. These selected funds do not have complete monthly filings in the extracted history; the panel records only observed public filing periods and does not interpolate. |
| iShares style ETFs | Not built for IWB, IWD, IWF, IWM, IUSG, or IUSV; listed in `etf_history_status.csv`. | No holdout panel. N-PORT's 2019-10 public start would prevent a full 2010-2020 replication in any case. | The iShares Trust registrant contains many fund series; targeted historical series resolution and holdings extraction were not completed. |
| SIC classification | `issuer_sic_snapshot.csv` records the current SEC submissions SIC code and description for the available Dow-name CIK crosswalk. | No historical series; same point-in-time construction for 2010-2020 was not completed. | SEC submissions exposes current SIC metadata; this is not a dated SIC history. `latest_10k_filing_date` is only a dating aid and does not make the current code historical. |
| Customer-supplier links | No links built, as instructed. | Not assessed beyond the disclosure-method limitation. | SEC 10-K major-customer disclosure is inconsistent and may anonymize buyers; a defensible named network needs manual entity resolution at each filing date. |

## Common ownership construction

`13f_manager_rank_q2_2026.csv` ranks reporting CIKs by the SEC Form 13F `TABLEVALUETOTAL` field for Q2 2026, using the original filing for each CIK. This is the value reported on Form 13F, not total firm AUM; separate reporting CIKs are ranked separately. The ranking is fixed at the top 50 for the development panel. The SEC quarterly bulk data contain 13F rows as filed; the builder filters to the mapped Dow CUSIPs and retains only position rows, not the bulk ZIPs.

`13f_holder_by_dow_stock.csv` stores `report_date`, `availability_filing_date`, manager CIK/name, accession number, Dow ticker/CUSIP, reported issuer/class, value in USD thousands, shares/principal amount, and amount type. Amendments are excluded; missing manager-quarter filings are not treated as zeros. A successfully parsed filing with no mapped Dow positions is retained as a parsed zero-row observation in `13f_filing_coverage.csv`.

`13f_cosine_overlap_edges.csv` contains the undirected pairwise cosine of each Dow stock's manager vector of reported position values for that quarter. `parsed_manager_count` records the included managers; `panel_availability_date` is the latest original filing date among those managers. A downstream user must not use a full-panel edge before that date. The overlap construction follows the shared-owner framing of Antón and Polk (2014), but it is not a reproduction of their full method.

The 50 manager-quarter historical check uses only `data.sec.gov/submissions` JSON index metadata: form, report date, filing date, accession number, and manager CIK. `13f_top50_holdout_filing_metadata.csv` records each of the 2,150 checks; `13f_top50_holdout_manager_summary.csv` summarizes coverage per CIK. No holdout information tables, positions, prices, returns, or signals were accessed.

## ETF panel and history limits

`etf_dow_comembership.csv` columns are ETF ticker, portfolio report date, filing availability date, Dow ticker/CUSIP, reported issuer, weight percent, and accession number. The file contains positive matched Dow positions; filings with no matched Dow holding appear in `etf_nport_filing_coverage.csv` and `etf_history_status.csv`. The extraction covers the three broad ETFs and the regular Select Sector SPDR series, excluding other similarly named premium-income series.

The SEC says its public Form N-PORT datasets cover October 2019 through September 2026, are updated quarterly, and include information that has been publicly disseminated. N-PORT reports portfolio holdings monthly, but the registrants and periods actually available for these selected funds are uneven; the present file follows the filing periods returned by EDGAR. It has no complete 2010-2019 history, so it cannot reproduce the full sealed holdout. See [SEC Form N-PORT data sets](https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets) and the [N-PORT readme](https://www.sec.gov/files/nport_readme.pdf).

The style ETF list is explicitly marked unbuilt in `etf_history_status.csv`; no row is represented as a zero holding merely because a style series was not extracted. For the four requested iShares Russell/core style funds and two additional large-cap style funds, the registrant has many unrelated series, so a correct PIT build requires resolving the target series and retrieving their reported filings separately.

## SIC and customer-supplier feasibility

The SEC `submissions` endpoint currently exposes SIC and SIC description for issuers but not a historical SIC-by-filing series. This pass therefore records a current classification snapshot only. A historical series would require parsing SIC from each issuer's 10-K filing header and assigning that code from the filing date onward. See [SEC EDGAR API documentation](https://www.sec.gov/edgar/sec-api-documentation).

Customer-supplier disclosure is not a consistent structured data set. Many 10-Ks report that one or more customers account for a material share of sales but anonymize the customer or identify it only as a customer class. Named relationships also require subsidiary-name matching and a filing-date availability rule, so no relationship rows are asserted here.

## Rebuild commands

Run from `C:\Users\musta\Desktop\UNSW\SSI\FINS3666` with Python 3 and `requests` installed:

```powershell
python A2\pivot_research\r4_L4\data\rank_13f_top50.py
python A2\pivot_research\r4_L4\data\build_13f_panel_bulk.py
python A2\pivot_research\r4_L4\data\build_13f_holdout_metadata.py
python A2\pivot_research\r4_L4\data\build_nport_etf_panel.py
python A2\pivot_research\r4_L4\data\build_issuer_sic.py
```

The 13F bulk builder uses quarterly SEC ZIPs for development filings and writes only Dow-matched rows. The holdout check downloads SEC submissions JSON only; do not change it to request filing documents or information tables for 2010-2020. The N-PORT builder requests the selected registrants' NPORT-P XML documents and writes only matched Dow positions plus filing coverage. Scripts use a descriptive project User-Agent and no more than one successful SEC request every 0.15-0.20 seconds.

## References

- SEC, [Form 13F data sets](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets) and [Form 13F FAQ](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f).
- SEC, [Form N-PORT data sets](https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets) and [N-PORT readme](https://www.sec.gov/files/nport_readme.pdf).
- Antón, M. and Polk, C. (2014), “Connected Stocks,” *Journal of Finance*, 69(3), 1099-1127. DOI: [10.1111/jofi.12149](https://doi.org/10.1111/jofi.12149).
