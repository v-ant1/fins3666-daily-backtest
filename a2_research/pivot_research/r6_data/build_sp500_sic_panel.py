"""Fetch dated 10-K header SIC classifications for S&P 500 PIT tickers.

SEC requests are sequential and throttled; responses are cached for reproducible
restarts. Only SEC filing metadata dated 2019-01-01 through 2026-10-30 is used.
No prices, returns, or outcomes are touched.
"""
from __future__ import annotations
import json, re, time
from pathlib import Path
from datetime import date
from urllib.parse import quote
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
ROSTER = OUT / "sp500_pit_roster.csv"
LEGACY = ROOT / "r4_L4" / "data" / "sic_panel.csv"
LEGACY_C1 = ROOT / "r6_C1" / "sp500_sic_membership_from_L4.csv"
START = "2019-01-01"
END = "2026-10-30"
CACHE = OUT / "sec_sic_cache"
MAP_CACHE = CACHE / "company_tickers.json"
SUB_CACHE = CACHE / "submissions"
HDR_CACHE = CACHE / "headers"
USER_AGENT = "UNSW FINS3666 student research contact: research@example.edu"
DELAY = 0.15  # <= 6.7 requests/second, below the SEC's stated 10 req/s ceiling.
HISTORICAL_CIK_OVERRIDES = {
    "ADS": ("0001101215", "BREAD FINANCIAL HOLDINGS, INC."),
    "CDAY": ("0001725057", "Dayforce, Inc."),
    "CERN": ("0000804753", "CERNER Corp"),
    "CTLT": ("0001596783", "Catalent, Inc."),
    "DRE": ("0000783280", "DUKE REALTY CORP"),
    "ETFC": ("0001015780", "E TRADE FINANCIAL CORP"),
    "FRC": ("0001132979", "FIRST REPUBLIC BANK"),
    "GPS": ("0000039911", "GAP INC"),
    "HBI": ("0001359841", "Hanesbrands Inc."),
    "HES": ("0000004447", "HESS CORP"),
    "HOLX": ("0000859737", "HOLOGIC INC"),
    "JNPR": ("0001043604", "JUNIPER NETWORKS INC"),
    "JWN": ("0000072333", "NORDSTROM INC"),
    "KSU": ("0000054480", "KANSAS CITY SOUTHERN"),
    "SBNY": ("0001288784", "Signature Bank Corp"),
    "SEE": ("0001012100", "SEALED AIR CORP/DE"),
}


def ticker_key(x: str) -> str:
    return str(x).strip().upper().replace(".", "-")


def sec_get(url: str, session: requests.Session, cache_path: Path | None = None) -> requests.Response:
    if cache_path is not None and cache_path.exists():
        class Cached:
            status_code = 200
            def __init__(self, path: Path): self._path = path
            @property
            def content(self): return self._path.read_bytes()
            @property
            def text(self): return self.content.decode("utf-8", errors="replace")
            def json(self): return json.loads(self.text)
        return Cached(cache_path)  # type: ignore[return-value]
    last = None
    for attempt in range(6):
        time.sleep(DELAY)
        try:
            r = session.get(url, timeout=60)
            if r.status_code == 200:
                if cache_path is not None:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    cache_path.write_bytes(r.content)
                return r
            if r.status_code not in (403, 408, 429, 500, 502, 503, 504):
                r.raise_for_status()
            last = RuntimeError(f"HTTP {r.status_code} {url}")
        except Exception as exc:
            last = exc
        time.sleep(min(30.0, 2.0 ** attempt))
    raise RuntimeError(f"SEC request failed after retries: {url}: {last}")


def read_roster_tickers() -> list[str]:
    r = pd.read_csv(ROSTER, dtype={"ticker": str})
    return sorted({ticker_key(x) for x in r.ticker.dropna()})


def read_roster_company_names() -> dict[str, str]:
    r = pd.read_csv(ROSTER, dtype={"ticker": str, "company": str})
    r["ticker"] = r.ticker.map(ticker_key)
    r = r.dropna(subset=["company"]).drop_duplicates("ticker", keep="last")
    return dict(zip(r.ticker, r.company.astype(str)))


def lineage_map(tickers: set[str]) -> dict[str, str]:
    """Recover historical ticker-to-CIK links from dated project SEC SIC records."""
    found: dict[str, str] = {}
    if LEGACY.exists():
        # Stream the legacy file and retain only the requested 2019-2026 SEC rows.
        for chunk in pd.read_csv(LEGACY, dtype={"ticker": str, "cik": str, "sic": str},
                                 usecols=["ticker", "cik", "effective_from"], chunksize=50000):
            chunk["effective_from"] = pd.to_datetime(chunk.effective_from, errors="coerce")
            chunk = chunk.loc[chunk.effective_from.between(pd.Timestamp(START), pd.Timestamp(END))]
            chunk["ticker"] = chunk.ticker.map(ticker_key)
            chunk["cik"] = chunk.cik.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(10)
            chunk = chunk.loc[chunk.ticker.isin(tickers) & chunk.cik.str.fullmatch(r"\d{10}")]
            # Repeated rows for the same symbol and issuer are fine; differing CIKs
            # are resolved by the most recent dated relationship, then audited below.
            for ticker, g in chunk.sort_values("effective_from").groupby("ticker"):
                found[ticker] = str(g.iloc[-1].cik)
    if LEGACY_C1.exists():
        x = pd.read_csv(LEGACY_C1, dtype={"ticker": str, "cik": str})
        x["ticker"] = x.ticker.map(ticker_key)
        x["cik"] = x.cik.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(10)
        for row in x.itertuples(index=False):
            if row.ticker in tickers and row.cik.isdigit() and row.ticker not in found:
                found[row.ticker] = row.cik
    return found


def load_ticker_map(session: requests.Session) -> dict[str, str]:
    response = sec_get("https://www.sec.gov/files/company_tickers.json", session, MAP_CACHE)
    data = response.json()
    result = {}
    for row in data.values():
        ticker = ticker_key(row.get("ticker", ""))
        cik = str(row.get("cik_str", "")).zfill(10)
        if ticker and cik.isdigit(): result[ticker] = cik
    return result


def company_name_search_cik(ticker: str, company: str, session: requests.Session) -> tuple[str | None, str]:
    """Resolve inactive historical symbols using their PIT issuer name in EDGAR."""
    cache = CACHE / "company_search" / f"{ticker}.html"
    url = "https://www.sec.gov/cgi-bin/browse-edgar?company=" + quote(company) + "&owner=exclude&action=getcompany&type=10-K&count=40"
    response = sec_get(url, session, cache)
    match = re.search(r'<span class="companyName">\s*([^<]+?)\s*<acronym[^>]*>CIK</acronym>\s*#:\s*<a[^>]*>\s*(\d{10})\s*\(see all company filings\)', response.text, re.I | re.S)
    if not match:
        return None, ""
    result_name, cik = match.group(1).strip(), match.group(2)
    clean = lambda x: re.sub(r"[^A-Z0-9]+", " ", x.upper()).strip()
    left, right = set(clean(company).split()), set(clean(result_name).split())
    stop = {"INC", "INCORPORATED", "CORP", "CORPORATION", "CO", "COMPANY", "LTD", "LIMITED", "PLC", "LLC", "THE"}
    left -= stop
    right -= stop
    if not left or not right or not (left & right):
        return None, result_name
    return cik, result_name


def submissions(cik: str, session: requests.Session) -> dict:
    path = SUB_CACHE / f"CIK{cik}.json"
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    return sec_get(url, session, path).json()


def filing_rows(sub: dict) -> list[tuple[str, str]]:
    filing = sub.get("filings", {})
    blocks = [filing.get("recent", {})]
    for old in filing.get("files", []):
        if old.get("filingTo", "") >= START and old.get("filingFrom", "") <= END:
            blocks.append({"__archive_name__": old.get("name", "")})
    rows: dict[str, str] = {}
    # Caller expands archived submissions blocks because they require an HTTP read.
    for block in blocks:
        if "__archive_name__" in block: continue
        for form, day, accession in zip(block.get("form", []), block.get("filingDate", []), block.get("accessionNumber", [])):
            if form == "10-K" and START <= day <= END:
                rows[accession] = day
    return [(acc, day) for acc, day in sorted(rows.items(), key=lambda p: (p[1], p[0]))]


def all_filings(sub: dict, cik: str, session: requests.Session) -> list[tuple[str, str]]:
    filing = sub.get("filings", {})
    rows = dict(filing_rows(sub))
    for old in filing.get("files", []):
        if old.get("filingTo", "") < START or old.get("filingFrom", "") > END:
            continue
        name = old.get("name", "")
        if not name: continue
        url = "https://data.sec.gov/submissions/" + name
        try:
            block = sec_get(url, session, SUB_CACHE / ("archive_" + Path(name).name)).json()
        except Exception as exc:
            print(f"ARCHIVE_FAIL CIK{cik} {name}: {exc}", flush=True)
            continue
        for form, day, accession in zip(block.get("form", []), block.get("filingDate", []), block.get("accessionNumber", [])):
            if form == "10-K" and START <= day <= END:
                rows[accession] = day
    return [(acc, day) for acc, day in sorted(rows.items(), key=lambda p: (p[1], p[0]))]


def next_trading_day_lookup() -> dict[str, str]:
    import exchange_calendars as xcals
    sessions = xcals.get_calendar("XNYS").sessions_in_range(pd.Timestamp("2019-01-01"), pd.Timestamp("2026-12-31"))
    # XNYS sessions are UTC midnight; effective date is the first session strictly
    # after the filing calendar date, including when filing date itself is a session.
    days = pd.DatetimeIndex(sessions).tz_localize(None).normalize()
    lookup = {}
    for date_text in pd.date_range("2019-01-01", "2026-10-30", freq="D").strftime("%Y-%m-%d"):
        day = pd.Timestamp(date_text)
        i = days.searchsorted(day, side="right")
        if i < len(days): lookup[date_text] = days[i].strftime("%Y-%m-%d")
    return lookup


def header_sic(cik: str, accession: str, session: requests.Session) -> tuple[str | None, str]:
    dashed = accession
    folder = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{folder}/{dashed}.hdr.sgml"
    cache = HDR_CACHE / f"{cik}_{accession}.hdr.sgml"
    response = sec_get(url, session, cache)
    match = re.search(r"<ASSIGNED-SIC>\s*(\d{4})", response.text, re.I)
    return (match.group(1) if match else None), url


def main() -> None:
    for p in (CACHE, SUB_CACHE, HDR_CACHE): p.mkdir(parents=True, exist_ok=True)
    tickers = read_roster_tickers()
    ticker_set = set(tickers)
    company_names = read_roster_company_names()
    legacy = lineage_map(ticker_set)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"})
    ticker_map = load_ticker_map(session)
    # Current SEC symbol mapping has precedence; the 2019-2026 dated SEC lineage
    # map fills delisted/historical ticker labels that no longer appear in it.
    ciks = {t: ticker_map.get(t) or legacy.get(t) or HISTORICAL_CIK_OVERRIDES.get(t, (None, ""))[0] for t in tickers}
    name_search_map: dict[str, str] = {}
    name_search_names: dict[str, str] = {}
    for ticker in tickers:
        if ciks[ticker]:
            continue
        cik, result_name = company_name_search_cik(ticker, company_names.get(ticker, ticker), session)
        if cik:
            ciks[ticker] = cik
            name_search_map[ticker] = cik
            name_search_names[ticker] = result_name
    mapped_by_current = sum(t in ticker_map for t in tickers)
    mapped_by_lineage = sum(t not in ticker_map and t in legacy for t in tickers)
    mapped_by_override = sum(t not in ticker_map and t not in legacy and t in HISTORICAL_CIK_OVERRIDES for t in tickers)
    lookup = next_trading_day_lookup()
    output, errors = [], []
    cik_cache: dict[str, dict] = {}
    lineage_rows = []
    for n, ticker in enumerate(tickers, 1):
        cik = ciks[ticker]
        if not cik:
            output.append({"ticker": ticker, "cik": "", "sic": "", "filing_date": "", "effective_date": "",
                           "source": "unmapped", "source_url": "", "flag": "no_CIK_mapping"})
            errors.append({"ticker": ticker, "cik": "", "stage": "mapping", "error": "no_current_or_historical_CIK"})
            continue
        try:
            if cik not in cik_cache: cik_cache[cik] = submissions(cik, session)
            sub = cik_cache[cik]
            if ticker not in ticker_map:
                if ticker in HISTORICAL_CIK_OVERRIDES:
                    expected_name = HISTORICAL_CIK_OVERRIDES[ticker][1]
                    if str(sub.get("name", "")).casefold() != expected_name.casefold():
                        errors.append({"ticker": ticker, "cik": cik, "stage": "lineage_verify", "error": f"expected_{expected_name}_got_{sub.get('name', '')}"})
                    else:
                        basis = "explicit historical ticker/company alias; issuer verified against SEC submissions JSON"
                        mapping_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
                elif ticker in name_search_map:
                    expected_name = name_search_names[ticker]
                    basis = "SEC EDGAR company-name search; CIK verified against submissions JSON"
                    mapping_url = "https://www.sec.gov/cgi-bin/browse-edgar?company=" + quote(company_names.get(ticker, ticker)) + "&owner=exclude&action=getcompany&type=10-K&count=40"
                else:
                    basis = "dated historical ticker/CIK relationship from existing L4 SIC panel"
                    mapping_url = str(LEGACY)
                if ticker not in HISTORICAL_CIK_OVERRIDES or str(sub.get("name", "")).casefold() == HISTORICAL_CIK_OVERRIDES[ticker][1].casefold():
                    lineage_rows.append({"ticker": ticker, "roster_company": company_names.get(ticker, ""), "cik": cik,
                                         "SEC_submission_name": sub.get("name", ""),
                                         "source_url": mapping_url,
                                         "CIK_verification_url": f"https://data.sec.gov/submissions/CIK{cik}.json",
                                         "mapping_basis": basis})
            filings = all_filings(sub, cik, session)
            ticker_rows = []
            for accession, filing_date in filings:
                try:
                    sic, url = header_sic(cik, accession, session)
                    if sic is None:
                        errors.append({"ticker": ticker, "cik": cik, "stage": "header_parse", "error": f"no_ASSIGNED-SIC_{filing_date}_{accession}"})
                        continue
                    eff = lookup.get(filing_date)
                    if not eff:
                        errors.append({"ticker": ticker, "cik": cik, "stage": "calendar", "error": f"no_next_session_{filing_date}"})
                        continue
                    ticker_rows.append({"ticker": ticker, "cik": cik, "sic": sic, "filing_date": filing_date,
                                        "effective_date": eff, "source": "10-K_header_ASSIGNED-SIC",
                                        "source_url": url, "flag": ""})
                except Exception as exc:
                    errors.append({"ticker": ticker, "cik": cik, "stage": "header_fetch", "error": f"{filing_date}_{accession}_{type(exc).__name__}_{exc}"})
            if ticker_rows:
                output.extend(ticker_rows)
            else:
                current_sic = str(sub.get("sic", ""))
                if re.fullmatch(r"\d{4}", current_sic):
                    output.append({"ticker": ticker, "cik": cik, "sic": current_sic, "filing_date": "",
                                   "effective_date": "2019-01-01", "source": "current_submission_SIC_fallback",
                                   "source_url": f"https://data.sec.gov/submissions/CIK{cik}.json",
                                   "flag": "current_SIC_carried_back_no_usable_10-K_header"})
                else:
                    output.append({"ticker": ticker, "cik": cik, "sic": "", "filing_date": "", "effective_date": "",
                                   "source": "no_10-K_SIC", "source_url": "", "flag": "no_header_or_current_SIC"})
                    errors.append({"ticker": ticker, "cik": cik, "stage": "sic", "error": "no_usable_10-K_or_current_SIC"})
        except Exception as exc:
            sub = cik_cache.get(cik, {})
            current_sic = str(sub.get("sic", ""))
            if re.fullmatch(r"\d{4}", current_sic):
                output.append({"ticker": ticker, "cik": cik, "sic": current_sic, "filing_date": "",
                               "effective_date": "2019-01-01", "source": "current_submission_SIC_fallback",
                               "source_url": f"https://data.sec.gov/submissions/CIK{cik}.json",
                               "flag": "current_SIC_carried_back_submissions_failure"})
            else:
                output.append({"ticker": ticker, "cik": cik, "sic": "", "filing_date": "", "effective_date": "",
                               "source": "submissions_failure", "source_url": "", "flag": type(exc).__name__})
            errors.append({"ticker": ticker, "cik": cik, "stage": "submissions", "error": f"{type(exc).__name__}_{exc}"})
        if n % 10 == 0 or n == len(tickers):
            print(f"processed {n}/{len(tickers)} tickers; SIC records={len(output)} errors={len(errors)}", flush=True)
    panel = pd.DataFrame(output, columns=["ticker", "cik", "sic", "filing_date", "effective_date", "source", "source_url", "flag"])
    panel = panel.sort_values(["ticker", "effective_date", "filing_date"], na_position="last")
    panel.to_csv(OUT / "sp500_sic_panel.csv", index=False)
    pd.DataFrame(errors, columns=["ticker", "cik", "stage", "error"]).to_csv(OUT / "sp500_sic_errors.csv", index=False)
    pd.DataFrame(lineage_rows, columns=["ticker", "roster_company", "cik", "SEC_submission_name", "source_url", "CIK_verification_url", "mapping_basis"]).to_csv(OUT / "historical_ticker_cik_lineage.csv", index=False)
    mapped = panel.loc[panel.sic.astype(str).str.fullmatch(r"\d{4}")]
    fallback = int(mapped.source.str.contains("fallback", na=False).sum())
    summary = {
        "scope": "SEC filing metadata only; 2019-01-01 through 2026-10-30; no price or outcome data",
        "roster_unique_tickers": len(tickers), "current_company_ticker_map_matches": mapped_by_current,
        "historical_SEC_lineage_map_only_matches": mapped_by_lineage,
        "manual_historical_lineage_overrides_verified": mapped_by_override,
        "historical_SEC_company_name_search_matches": len(name_search_map),
        "historical_company_search_names": name_search_names,
        "historical_company_search_ciks": name_search_map,
        "historical_noncurrent_lineage_rows_saved": len(lineage_rows),
        "CIK_mapped_tickers": sum(bool(v) for v in ciks.values()),
        "tickers_with_any_usable_SIC": int(mapped.ticker.nunique()),
        "tickers_missing_SIC": sorted(set(tickers) - set(mapped.ticker)),
        "panel_rows": int(len(panel)), "10-K_header_rows": int((panel.source == "10-K_header_ASSIGNED-SIC").sum()),
        "current_SIC_fallback_rows": fallback, "fallback_tickers": sorted(mapped.loc[mapped.source.str.contains("fallback", na=False), "ticker"].unique()),
        "rows_without_SIC": int(panel.sic.astype(str).str.fullmatch(r"\d{4}").eq(False).sum()),
        "error_rows": int(len(errors)), "panel_csv": "sp500_sic_panel.csv", "errors_csv": "sp500_sic_errors.csv",
        "NYSE_effective_date_rule": "effective_date is first XNYS session strictly after SEC filingDate",
        "rate_limit": "sequential requests with 0.15s minimum delay; cached; retry backoff on 403/429/5xx",
    }
    (OUT / "sic_build_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_qa(summary, panel, errors)


def write_qa(summary: dict, panel: pd.DataFrame, errors: list[dict]) -> None:
    lines = ["# S&P 500 point-in-time SIC panel QA", "",
             "This file documents SEC issuer SIC retrieval and mapping only. It contains no price data, returns, forward outcomes, or ICs. SIC filings requested span 2019-01-01 through 2026-10-30; effective dates use the first NYSE session strictly after each filing date.", "",
             "## Coverage", "",
             f"- PIT roster symbols processed: {summary['roster_unique_tickers']}.",
             f"- Direct current SEC company_tickers.json matches: {summary['current_company_ticker_map_matches']}.",
             f"- Additional historical ticker/CIK lineage matches from the existing dated SEC panel: {summary['historical_SEC_lineage_map_only_matches']}.",
             f"- Historical ticker/CIK lineage overrides verified against SEC submissions names: {summary['manual_historical_lineage_overrides_verified']}.",
             f"- Additional historical CIKs resolved by SEC company-name search against PIT issuer names: {summary['historical_SEC_company_name_search_matches']}.",
             f"- Non-current/historical ticker-to-CIK lineage rows saved for audit: {summary['historical_noncurrent_lineage_rows_saved']}.",
             f"- Symbols mapped to a CIK: {summary['CIK_mapped_tickers']}.",
             f"- Symbols with at least one usable 4-digit SIC: {summary['tickers_with_any_usable_SIC']}; symbols without one: {summary['rows_without_SIC']} ticker-status rows.",
             f"- Unresolved SIC ticker(s): `{summary['tickers_missing_SIC']}`.",
             f"- Dated 10-K header records: {summary['10-K_header_rows']}.",
             f"- Current SIC fallback rows: {summary['current_SIC_fallback_rows']}; fallback symbols: `{summary['fallback_tickers']}`.",
             f"- SEC retrieval/parse error rows: {summary['error_rows']}; see `sp500_sic_errors.csv`.", "",
             "The fallback is explicitly flagged because the current issuer SIC may not represent the point-in-time historical class. It is used only when no usable 10-K header row was obtained for that symbol; it must be treated as weaker coverage in E1 feasibility QA.", "",
             "## Construction and lineage", "",
             "Each roster ticker is mapped first through the SEC company_tickers.json symbol/CIK table, then through dated SEC SIC ticker/CIK lineage already held in the L4 SEC panel and the C1 L4 seed. All non-current/delisted symbol mappings are recorded in `historical_ticker_cik_lineage.csv` with their CIK, SEC submission issuer name, mapping source URL, and CIK verification URL. Remaining aliases use explicit historical ticker/CIK rows, verified against the issuer name returned by SEC submissions JSON; SEC company-name search is also used where the historical label is absent from current SEC symbol maps. For each mapped CIK, SEC submissions JSON supplies all 10-K accession numbers with filing dates in 2019-2026; archived submissions files are fetched where needed. Header files are parsed for `<ASSIGNED-SIC>`. A usable SIC is effective on the first NYSE session strictly after its filing date, and stays current until the next dated 10-K SIC row for that ticker. No later filing is backfilled before its effective date.", "",
             "Requests use one sequential SEC session with a 0.15-second minimum spacing, a generic research User-Agent, local response caching and exponential retries for transient or rate-limit responses. The build can be restarted from cache using `python r6_data/build_sp500_sic_panel.py`.", "",
             "## Files", "",
             "- `sp500_sic_panel.csv`: ticker, CIK, SIC, filing date, effective date, source, filing URL, and fallback flag.",
             "- `sp500_sic_errors.csv`: issuer mapping, archived submissions, header fetch and parse failures.",
             "- `historical_ticker_cik_lineage.csv`: every explicit historical alias/CIK bridge and verified SEC source.",
             "- `sic_build_manifest.json`: machine-readable coverage summary.",
             "- `sec_sic_cache/`: downloaded submissions JSON and SEC header responses for restart and audit.", ""]
    (OUT / "SIC_QA.md").write_text("\n".join(lines), encoding="utf-8")

if __name__ == "__main__":
    main()
