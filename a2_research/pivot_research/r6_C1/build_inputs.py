"""Build C1's point-in-time return components and dated SIC peer links.

This input-only builder never reads a forward-return column or computes an IC.
The only dates consumed are development dates from 2020-11-27 through
2026-10-30.  SEC SIC observations become usable on the next trading date.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from itertools import combinations
import json
import re
import time
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
START, END = "2020-11-27", "2026-10-30"
DOW_BASE = "MMM AXP AMGN AAPL BA CAT CVX CSCO KO DIS DOW GS HD HON IBM INTC JNJ JPM MCD MRK MSFT NKE PG CRM TRV UNH VZ V WBA WMT".split()
DOW_CHANGES = [("2024-02-26", "AMZN", "WBA"), ("2024-11-08", "NVDA", "INTC"), ("2024-11-08", "SHW", "DOW")]


def dow_roster(dates: pd.DatetimeIndex) -> pd.DataFrame:
    rows = []
    for dt in dates:
        active = set(DOW_BASE)
        for change, added, removed in DOW_CHANGES:
            if dt >= pd.Timestamp(change):
                active.discard(removed)
                active.add(added)
        rows.extend((dt, t) for t in sorted(active))
    return pd.DataFrame(rows, columns=["date", "ticker"])


def dow_roster_intervals() -> pd.DataFrame:
    breaks = [pd.Timestamp(START)] + [pd.Timestamp(x[0]) for x in DOW_CHANGES] + [pd.Timestamp(END) + pd.Timedelta(days=1)]
    rows = []
    for lo, hi in zip(breaks[:-1], breaks[1:]):
        active = set(DOW_BASE)
        for change, added, removed in DOW_CHANGES:
            if lo >= pd.Timestamp(change):
                active.discard(removed)
                active.add(added)
        rows.extend((ticker, lo, hi) for ticker in sorted(active))
    return pd.DataFrame(rows, columns=["ticker", "effective_from", "effective_to_exclusive"])


def _load_dow(folder: Path) -> pd.DataFrame:
    rows = []
    files = list(folder.glob("*.csv"))
    delisted = folder.parent / "prices-daily-delisted"
    if delisted.exists():
        files.extend(delisted.glob("*.csv"))
    for path in files:
        d = pd.read_csv(path, usecols=["date", "open", "close", "adjclose"])
        # Parse/filter dates before deriving any price component.
        d["date"] = pd.to_datetime(d["date"], utc=True).dt.tz_convert(None).dt.normalize()
        d = d.loc[d.date.between(START, END)].copy()
        d["ticker"] = path.stem.upper()
        rows.append(d)
    if not rows:
        raise FileNotFoundError(f"No daily CSVs in {folder}")
    return pd.concat(rows, ignore_index=True).rename(columns={"adjclose": "adj_close"})


def _fetch_sec_sic(tickers: set[str], cache: Path, user_agent: str) -> pd.DataFrame:
    """Fetch dated 10-K SIC headers from SEC submissions for S&P roster tickers."""
    if cache.exists():
        return pd.read_csv(cache, dtype={"ticker": str, "cik": str, "sic": str})
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("Install requests to fetch the SEC SIC extension") from exc
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"})

    def get(url: str):
        for attempt in range(4):
            response = session.get(url, timeout=90)
            if response.status_code == 200:
                time.sleep(.18)
                return response
            if response.status_code not in (403, 429, 500, 502, 503):
                response.raise_for_status()
            time.sleep(1.5 * (attempt + 1))
        response.raise_for_status()

    company = get("https://www.sec.gov/files/company_tickers_exchange.json").json()
    fields = company["fields"]
    ticker_to_cik = {str(row[fields.index("ticker")]).upper(): str(row[fields.index("cik")]).zfill(10)
                     for row in company["data"]}
    records, gaps = [], []
    for number, ticker in enumerate(sorted(tickers), 1):
        cik = ticker_to_cik.get(ticker)
        if not cik:
            gaps.append((ticker, "", "", "ticker_not_in_current_SEC_ticker_map", ""))
            continue
        try:
            data = get(f"https://data.sec.gov/submissions/CIK{cik}.json").json()
            blocks = [data.get("filings", {}).get("recent", {})]
            for f in data.get("filings", {}).get("files", []):
                if f.get("filingTo", "") >= "2020-01-01" and f.get("filingFrom", "") <= END:
                    blocks.append(get("https://data.sec.gov/submissions/" + f["name"]).json())
            filings = []
            for block in blocks:
                for form, day, accession in zip(block.get("form", []), block.get("filingDate", []), block.get("accessionNumber", [])):
                    if form == "10-K" and "2020-01-01" <= day <= END:
                        filings.append((day, accession))
            yearly = {}
            for day, accession in sorted(filings):
                yearly.setdefault(day[:4], (day, accession))
            for day, accession in yearly.values():
                url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{accession}.hdr.sgml"
                try:
                    match = re.search(r"<ASSIGNED-SIC>\s*(\d{4})", get(url).text, re.I)
                    if match:
                        records.append((ticker, cik, match.group(1), day, url))
                    else:
                        gaps.append((ticker, cik, day, "sic_missing_in_filing_header", url))
                except Exception as exc:
                    gaps.append((ticker, cik, day, f"header_fetch_failed_{type(exc).__name__}", url))
            print(f"SEC SIC {ticker}: {len(yearly)} annual filings ({number}/{len(tickers)})", flush=True)
        except Exception as exc:
            gaps.append((ticker, cik, "", f"submissions_failed_{type(exc).__name__}", ""))
    result = pd.DataFrame(records, columns=["ticker", "cik", "sic", "effective_from", "source_url"])
    result.to_csv(cache, index=False)
    pd.DataFrame(gaps, columns=["ticker", "cik", "date", "status", "source_url"]).to_csv(cache.with_name("sp500_sic_gaps.csv"), index=False)
    return result


def _components(bars: pd.DataFrame, roster: pd.DataFrame) -> pd.DataFrame:
    # Compute close-to-open from the prior available close before applying the
    # index-membership mask: a newly added member still has a valid t-1 close.
    x = bars.sort_values(["ticker", "date"]).copy()
    # Adjust open using the day's split/dividend factor; close is already adjusted.
    x["adj_open"] = x["open"] * x["adj_close"] / x["close"]
    x["prev_adj_close"] = x.groupby("ticker")["adj_close"].shift()
    x["overnight_return"] = x["adj_open"] / x["prev_adj_close"] - 1.0
    x["intraday_return"] = x["adj_close"] / x["adj_open"] - 1.0
    # The relative component is an input pressure proxy, not a tested signal.
    x["component_spread"] = x["intraday_return"] - x["overnight_return"]
    x = x.merge(roster, on=["date", "ticker"], how="inner", validate="one_to_one")
    return x[["date", "ticker", "adj_open", "adj_close", "overnight_return", "intraday_return", "component_spread"]]


def _next_trading_day(date: pd.Timestamp, calendar: pd.DatetimeIndex) -> pd.Timestamp | None:
    i = calendar.searchsorted(date, side="right")
    return calendar[i] if i < len(calendar) else None


def _sic_membership(roster: pd.DataFrame, sic: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    s = sic.copy()
    s["ticker"] = s.ticker.str.upper()
    s["effective_from"] = pd.to_datetime(s.effective_from)
    s["usable_from"] = s.effective_from.map(lambda d: _next_trading_day(d, calendar))
    s = s.dropna(subset=["usable_from", "sic"])
    s["sic"] = s.sic.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(4)
    s = s.loc[s.sic.str.fullmatch(r"\d{4}")]
    s["sic2"], s["sic3"] = s.sic.str[:2], s.sic.str[:3]
    # Merge each roster interval with only SEC SIC observations available by date.
    r = roster.copy()
    if "effective_from" not in r:
        r = r.groupby("ticker", as_index=False).date.agg(["min", "max"]).reset_index()
        r = r.rename(columns={"min": "effective_from", "max": "effective_to_exclusive"})
    else:
        r["effective_from"] = pd.to_datetime(r.effective_from)
        r["effective_to_exclusive"] = pd.to_datetime(r.effective_to_exclusive)
    out = []
    for ticker, rrows in r.groupby("ticker"):
        obs = s.loc[s.ticker.eq(ticker)].sort_values("usable_from")
        if obs.empty:
            continue
        for rr in rrows.itertuples(index=False):
            lo = max(pd.Timestamp(rr.effective_from), pd.Timestamp(START))
            hi = min(pd.Timestamp(rr.effective_to_exclusive), pd.Timestamp(END) + pd.Timedelta(days=1))
            if hi <= lo:
                continue
            relevant = obs.loc[(obs.usable_from < hi) & (obs.usable_from >= lo)]
            prior = obs.loc[obs.usable_from < lo]
            if not prior.empty:
                relevant = pd.concat([prior.tail(1), relevant])
            relevant = relevant.drop_duplicates("usable_from", keep="last")
            for j, o in enumerate(relevant.itertuples(index=False)):
                a = max(lo, pd.Timestamp(o.usable_from))
                b = min(hi, pd.Timestamp(relevant.iloc[j + 1].usable_from) if j + 1 < len(relevant) else hi)
                if b > a:
                    out.append((ticker, o.cik, o.sic, o.sic2, o.sic3, a, b, o.source_url))
    return pd.DataFrame(out, columns=["ticker", "cik", "sic", "sic2", "sic3", "effective_from", "effective_to_exclusive", "source_url"])


def _edges(members: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for field in ("sic2", "sic3"):
        for group, g in members.groupby(field, dropna=True):
            by_ticker = {ticker: list(gr.sort_values("effective_from").itertuples(index=False))
                         for ticker, gr in g.groupby("ticker")}
            for u, v in combinations(sorted(by_ticker), 2):
                for x in by_ticker[u]:
                    for y in by_ticker[v]:
                        a = max(pd.Timestamp(x.effective_from), pd.Timestamp(y.effective_from))
                        b = min(pd.Timestamp(x.effective_to_exclusive), pd.Timestamp(y.effective_to_exclusive))
                        if b > a:
                            rows.append((u, v, field, group, a, b))
    return pd.DataFrame(rows, columns=["source", "target", "sic_level", "sic_group", "effective_from", "effective_to_exclusive"])


def _summary(name: str, components: pd.DataFrame, membership: pd.DataFrame) -> dict:
    dates = pd.DatetimeIndex(sorted(components.date.unique()))
    coverage = components.groupby("date").ticker.nunique()
    spread = components.pivot(index="date", columns="ticker", values="component_spread")
    rank = spread.rank(axis=1, pct=True) - 0.5
    per_ticker_acf = [rank[c].autocorr(lag=1) for c in rank.columns if rank[c].notna().sum() > 20]
    acf = float(np.nanmedian(per_ticker_acf)) if per_ticker_acf else float("nan")
    active_groups = []
    for date in dates:
        active = membership.loc[(membership.effective_from <= date) & (membership.effective_to_exclusive > date)]
        active_groups.append(active.sic2.nunique())
    groups = pd.Series(active_groups, index=dates)
    return {"universe": name, "dates": len(dates), "first_date": str(dates.min().date()), "last_date": str(dates.max().date()),
            "ticker_date_rows": len(components), "tickers_seen": int(components.ticker.nunique()),
            "median_names_per_date": float(coverage.median()), "min_names_per_date": int(coverage.min()),
            "component_spread_cross_sectional_sd_median": float(spread.std(axis=1).median()),
            "median_per_name_ranked_spread_acf1_input_only": acf,
            "sic2_tickers_in_membership": int(len(set(membership.ticker) & set(components.ticker))),
            "sic2_group_count_median_on_dates": float(groups.median()) if len(groups) else 0.0,
            "sic2_group_count_min_on_dates": int(groups.min()) if len(groups) else 0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--extend-sp500-sic", action="store_true", help="Fetch point-in-time annual 10-K SIC headers via SEC submissions for S&P roster tickers")
    ap.add_argument("--sec-user-agent", default="FINS3666 network data project contact research@example.edu")
    args = ap.parse_args()
    root = args.root.resolve()
    out = root / "r6_C1"
    out.mkdir(parents=True, exist_ok=True)
    sic = pd.read_csv(root / "r4_L4/data/sic_panel.csv", dtype={"ticker": str, "sic": str, "cik": str})

    dow_bars = _load_dow(root / "repo/prices-daily")
    dow_calendar = pd.DatetimeIndex(sorted(dow_bars.date.unique()))
    d_roster = dow_roster(dow_calendar)
    dow = _components(dow_bars, d_roster)
    dmem = _sic_membership(dow_roster_intervals(), sic, dow_calendar)
    dow.to_parquet(out / "dow_components_dev.parquet", index=False)
    dmem.to_csv(out / "dow_sic_membership.csv", index=False)
    _edges(dmem).to_csv(out / "dow_industry_links.csv", index=False)

    # S&P parquet is development-only; project columns are daily adjusted bars.
    import pyarrow.parquet as pq
    sp_bars = pq.read_table(root / "r6_data/sp500_ohlcv_dev.parquet",
                            columns=["date", "ticker", "open", "close", "adj_close"],
                            filters=[("date", ">=", pd.Timestamp(START)), ("date", "<=", pd.Timestamp(END))]).to_pandas()
    sp_bars["date"] = pd.to_datetime(sp_bars.date).dt.normalize()
    sp_bars = sp_bars.loc[sp_bars.date.between(START, END)].copy()
    sp_roster = pd.read_csv(root / "r6_data/sp500_pit_roster.csv")
    sp_roster["effective_from"] = pd.to_datetime(sp_roster.effective_from)
    sp_roster["effective_to_exclusive"] = pd.to_datetime(sp_roster.effective_to_exclusive)
    sp_cal = pd.DatetimeIndex(sorted(sp_bars.date.unique()))
    sp_sic = sic.copy()
    if args.extend_sp500_sic:
        sec_sic = _fetch_sec_sic(set(sp_roster.ticker.str.upper().unique()), out / "sp500_sic_panel_sec.csv", args.sec_user_agent)
        # SEC's current ticker map omits some retired point-in-time symbols; retain
        # the dated L4 records as a supplemental lineage source for those issuers.
        sp_sic = pd.concat([sec_sic, sic], ignore_index=True).drop_duplicates(
            subset=["ticker", "effective_from"], keep="first")
    # Expand roster membership only onto dates present in development bars.
    sr = sp_roster[["ticker", "effective_from", "effective_to_exclusive"]].copy()
    dates_df = pd.DataFrame({"date": sp_cal})
    sr = sr.merge(dates_df.assign(_k=1), how="cross")
    sr = sr.loc[(sr.date >= sr.effective_from) & (sr.date < sr.effective_to_exclusive), ["date", "ticker"]]
    sp = _components(sp_bars, sr)
    # The full SEC extension supersedes L4's Dow-only panel when requested.
    spmem = _sic_membership(sp_roster, sp_sic, sp_cal)
    sp.to_parquet(out / "sp500_components_dev.parquet", index=False)
    spmem.to_csv(out / "sp500_sic_membership.csv", index=False)
    _edges(spmem).to_csv(out / "sp500_industry_links.csv", index=False)

    sums = [_summary("Dow", dow, dmem), _summary("S&P 500", sp, spmem)]
    payload = {"development_only": True, "start": START, "end": END, "outcome_columns_loaded": False,
               "ic_or_forward_return_computed": False, "summary": sums}
    (out / "input_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
