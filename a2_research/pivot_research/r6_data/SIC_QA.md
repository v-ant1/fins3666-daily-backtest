# S&P 500 point-in-time SIC panel QA

This file documents SEC issuer SIC retrieval and mapping only. It contains no price data, returns, forward outcomes, or ICs. SIC filings requested span 2019-01-01 through 2026-10-30; effective dates use the first NYSE session strictly after each filing date.

## Coverage

- PIT roster symbols processed: 622.
- Direct current SEC company_tickers.json matches: 568.
- Additional historical ticker/CIK lineage matches from the existing dated SEC panel: 1.
- Historical ticker/CIK lineage overrides verified against SEC submissions names: 16.
- Additional historical CIKs resolved by SEC company-name search against PIT issuer names: 37.
- Non-current/historical ticker-to-CIK lineage rows saved for audit: 54.
- Symbols mapped to a CIK: 622.
- Symbols with at least one usable 4-digit SIC: 621; symbols without one: 1 ticker-status rows.
- Unresolved SIC ticker(s): `['FRC']`.
- Dated 10-K header records: 4624.
- Current SIC fallback rows: 4; fallback symbols: `['HONA', 'SBNY', 'VYLR', 'XOM']`.
- SEC retrieval/parse error rows: 1; see `sp500_sic_errors.csv`.

The fallback is explicitly flagged because the current issuer SIC may not represent the point-in-time historical class. It is used only when no usable 10-K header row was obtained for that symbol; it must be treated as weaker coverage in E1 feasibility QA.

## Construction and lineage

Each roster ticker is mapped first through the SEC company_tickers.json symbol/CIK table, then through dated SEC SIC ticker/CIK lineage already held in the L4 SEC panel and the C1 L4 seed. All non-current/delisted symbol mappings are recorded in `historical_ticker_cik_lineage.csv` with their CIK, SEC submission issuer name, mapping source URL, and CIK verification URL. Remaining aliases use explicit historical ticker/CIK rows, verified against the issuer name returned by SEC submissions JSON; SEC company-name search is also used where the historical label is absent from current SEC symbol maps. For each mapped CIK, SEC submissions JSON supplies all 10-K accession numbers with filing dates in 2019-2026; archived submissions files are fetched where needed. Header files are parsed for `<ASSIGNED-SIC>`. A usable SIC is effective on the first NYSE session strictly after its filing date, and stays current until the next dated 10-K SIC row for that ticker. No later filing is backfilled before its effective date.

Requests use one sequential SEC session with a 0.15-second minimum spacing, a generic research User-Agent, local response caching and exponential retries for transient or rate-limit responses. The build can be restarted from cache using `python r6_data/build_sp500_sic_panel.py`.

## Files

- `sp500_sic_panel.csv`: ticker, CIK, SIC, filing date, effective date, source, filing URL, and fallback flag.
- `sp500_sic_errors.csv`: issuer mapping, archived submissions, header fetch and parse failures.
- `historical_ticker_cik_lineage.csv`: every explicit historical alias/CIK bridge and verified SEC source.
- `sic_build_manifest.json`: machine-readable coverage summary.
- `sec_sic_cache/`: downloaded submissions JSON and SEC header responses for restart and audit.
