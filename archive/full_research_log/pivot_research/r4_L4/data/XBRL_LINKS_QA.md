# SEC XBRL customer concentration links: QA

## What was built

`xbrl_customer_links.csv` contains SEC-filed `ConcentrationRiskPercentage*` facts whose context includes a customer-related axis/member for the point-in-time Dow issuer roster. It records the supplier ticker and CIK, original member QName, a readable customer name and matched ticker when the member identifies one company, percentage, fact period, SEC filing date, form, accession and the original SEC document URL. No price, return or market-data files were accessed.

SEC's `companyfacts` and `frames` products do not preserve the dimensional customer-member detail needed here. The builder therefore reads original SEC inline XBRL filings and, for older filings, the standalone XBRL instance XML from the filing archive. It used SEC submissions metadata to find eligible 10-K and 10-K/A filings, then retained only fact periods ending while that issuer was a Dow member. Each result becomes available on its filing date; its period end is the accounting period, not the signal availability date. Only filings dated through 2026-10-30 are included.

The SEC requests identify the client as `FINS3666 XBRL data research contact research@example.edu` and are spaced at least 0.20 seconds apart (five requests per second). Sources: [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), [SEC submissions API documentation](https://www.sec.gov/edgar/sec-api-documentation), and the [Intel example filing](https://www.sec.gov/Archives/edgar/data/50863/000005086320000011/a12282019q4-10kdocument.htm), which visibly contains dimensioned Dell, HP and Lenovo concentration facts.

## Coverage

The builder scanned **504** point-in-time eligible annual filings (10-K/10-K/A) across **45 CIKs**; 96 documents yielded customer-axis facts. The final CSV has **542 distinct fact rows** after duplicate suppression.

| Period class | Fact rows | Named listed-customer fact rows | Unique matched listed-company customer tickers |
|---|---:|---:|---:|
| Holdout, period end 2009-01-01–2020-10-31 and filing date through 2020-10-31 | 264 | 76 | **6**: AAL, DELL, HA, HPQ, LNVGY, UAL |
| Transition, periods between the defined holdout and development windows | 35 | 9 | 3: DELL, HPQ, LNVGY |
| Development, period end 2020-11-27–2026-10-30 and filing date through 2026-10-30 | 243 | 51 | **8**: ABC, CAH, COR, DELL, HPQ, LNVGY, MCK, WMT |

The customer counts are distinct matched ticker labels, not fact-row counts. Three facts use a single combined McKesson/AmerisourceBergen/Cardinal Health member; these rows are labeled `named_group`, left without a ticker and excluded from the unique-ticker counts because the filing does not provide a separate percentage for each company. `named_unmatched` means the member is named but could not be safely mapped to a listed ticker; `generic` identifies anonymous labels such as `CustomerOne`. For ticker aliases, historical members such as Hewlett-Packard Company, Lenovo Group Limited and United Continental Airlines are explicitly mapped to HPQ, LNVGY and UAL; AmerisourceBergen is mapped to its historical ABC symbol, while Cencora is COR.

Fact rows by accounting-period year:

| Class | Year: fact rows |
|---|---|
| Holdout | 2011: 4; 2012: 13; 2013: 25; 2014: 30; 2015: 40; 2016: 38; 2017: 57; 2018: 36; 2019: 18; 2020: 3 |
| Transition | 2018: 7; 2019: 18; 2020: 10 |
| Development | 2020: 19; 2021: 48; 2022: 48; 2023: 56; 2024: 33; 2025: 30; 2026: 9 |

There are no qualifying output facts with 2009 or 2010 period ends. The scan includes early 10-K XML instance documents, but absence here means no qualifying customer-axis fact was recovered under this tag/axis rule, not that the firms had no customer concentration disclosures. The 2009–2010 period gap should be treated as a dataset coverage gap.

## Spot-check examples

The URLs below are the exact source documents recorded in the CSV. They show filing-date availability, distinct from the accounting period end.

| Class | Supplier | Customer | Percentage | Period end | Filing date | Source |
|---|---|---|---:|---|---|---|
| Holdout | BA (CIK 12927) | American Airlines (AAL) | 12% | 2012-12-31 | 2013-02-11 | [SEC XBRL instance](https://www.sec.gov/Archives/edgar/data/12927/000001292713000014/ba-20121231.xml) |
| Holdout | INTC (CIK 50863) | Dell (DELL) | 15% | 2011-12-31 | 2014-02-14 | [SEC XBRL instance](https://www.sec.gov/Archives/edgar/data/50863/000005086314000020/intc-20131228.xml) |
| Development | MRK (CIK 310158) | Cencora (COR) | 20% | 2023-12-31 | 2024-02-26 | [SEC inline XBRL filing](https://www.sec.gov/Archives/edgar/data/310158/000162828024006850/mrk-20231231.htm) |

## Field and calculation notes

- `percentage` is the displayed XBRL numeric value transformed with the inline XBRL `scale` and `sign` attributes into percentage units. For example, a numeric fact of 0.12 is reported as `12.00`.
- `customer_member_name` keeps the full namespace-qualified member, preserving the issuer taxonomy's member label. `customer_display_name` is normalized for readability. Empty `customer_ticker` values are intentional where the customer is generic, unmatched or a combined group.
- `period_start` and `period_end` are taken from the dimensioned context; `filing_date` is the SEC submission filing date (not a reconstructed intraday acceptance timestamp). `source_url` points to the fact-bearing original document, which may be an instance XML for older reports.
- The SEC submissions archive can contain amendments and comparative contexts. Filing-date versions are retained; exact duplicate facts within the same accession and period are collapsed. A later amendment is a later available version, not an earlier-known fact.
- SEC taxonomy/customer-member labels differ across years. A named member without a reliable exact alias or company-name match remains `named_unmatched`; no fuzzy prefix match is used. The ticker match represents the identified company's conventional symbol and may be a historical symbol (for example ABC).

## Rebuild

From `A2\pivot_research` (Python dependencies: `requests`, `beautifulsoup4`, `lxml`):

```powershell
python r4_L4\data\build_xbrl_customer_links.py
```

The script rebuilds the CSV from SEC submissions and filing documents, applies the point-in-time Dow membership and filing-date rules above, and uses a generic project User-Agent with a request interval below the SEC's 10-requests-per-second ceiling.
