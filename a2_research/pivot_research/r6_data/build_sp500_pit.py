"""Build point-in-time S&P 500 member intervals and development daily bars.

Sources: Wikipedia's current components and historical component changes,
cross-checked against the linked S&P Dow Jones Indices releases; Yahoo Finance
daily history via yfinance for OHLCV. No prices before 2020-06-01 are requested.
"""
from __future__ import annotations

import re, time, warnings, io
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import requests
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

OUT = Path(__file__).resolve().parent
WIKI_HEADERS = {"User-Agent": "FINS3666 S&P data research contact research@example.edu"}
WINDOW_START = date(2020, 6, 1)
WINDOW_END = date(2026, 10, 30)
RIGHT_EDGE = date(2026, 10, 31)  # half-open end


def norm_ticker(value: object) -> str:
    s = str(value).strip().upper().replace(".", "-")
    return s


def get_html(url: str) -> str:
    response = requests.get(url, headers=WIKI_HEADERS, timeout=60)
    response.raise_for_status()
    return response.text


def history_source_map(soup: BeautifulSoup) -> dict[str, str]:
    out = {}
    for li in soup.select('li[id^="cite_note-"]'):
        ref = li.get("id", "").removeprefix("cite_note-")
        external = [a.get("href", "") for a in li.select("a[href]")
                    if a.get("href", "").startswith("https://")
                    and "wikipedia.org" not in a.get("href", "")]
        if external:
            out[ref] = external[0]
    return out


def parse_changes(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = next(t for t in soup.find_all("table")
                 if "Effective Date" in t.get_text(" ", strip=True)
                 and "Removed" in t.get_text(" ", strip=True))
    refs = history_source_map(soup)
    changes = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) < 6:
            continue
        text = [c.get_text(" ", strip=True) for c in cells]
        try:
            effective = pd.to_datetime(text[0], errors="raise").date()
        except Exception:
            continue
        added = norm_ticker(text[1])
        add_name = text[2]
        removed = norm_ticker(text[3])
        remove_name = text[4]
        ref_ids = [a.get("href", "").split("cite_note-", 1)[-1]
                   for a in cells[6].select('a[href*="cite_note-"]')] if len(cells) > 6 else []
        urls = [refs[x] for x in ref_ids if x in refs]
        official = next((u for u in urls if "spglobal.com" in u or "spindices.com" in u), "")
        changes.append({"date": effective, "added": added, "add_name": add_name,
                        "removed": removed, "remove_name": remove_name,
                        "reason": text[5], "wiki_refs": ";".join(ref_ids),
                        "source_url": official or (urls[0] if urls else "")})
    # The Wikipedia history table has the March 2026 admission under SATS but
    # does not carry through EchoStar's later symbol change. Preserve the same
    # index constituent across its issuer-confirmed June 24 symbol transition.
    changes.append({"date": date(2026, 6, 24), "added": "ECHO", "add_name": "EchoStar",
                    "removed": "SATS", "remove_name": "EchoStar",
                    "reason": "Ticker change; same issuer/security, confirmed by issuer release",
                    "wiki_refs": "issuer ticker change 2026-06-22",
                    "source_url": "https://ir.echostar.com/news-releases/news-release-details/echostar-changing-stocker-ticker-sats-echo-marking-companys-next"})
    changes.append({"date": date(2026, 8, 18), "added": "VMRK", "add_name": "Vivmark Residential",
                    "removed": "EQR", "remove_name": "Equity Residential",
                    "reason": "Merger/name and ticker change; existing S&P 500 seat continued",
                    "wiki_refs": "issuer ticker change 2026-08-18",
                    "source_url": "https://investors.vivmarkresidential.com/news-events/press-releases/detail/113/vivmark-residential-launches-as-one-of-the-countrys-leading-real-estate-companies"})
    return changes


def current_members() -> tuple[dict[str, str], set[str]]:
    html = get_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    table = pd.read_html(io.StringIO(html))[0]
    current = {norm_ticker(r["Symbol"]): str(r["Security"])
               for _, r in table.iterrows()}
    sp100_html = get_html("https://en.wikipedia.org/wiki/S%26P_100")
    sp100_table = next(t for t in pd.read_html(io.StringIO(sp100_html))
                       if "Symbol" in t.columns and "Name" in t.columns)
    sp100 = {norm_ticker(x) for x in sp100_table["Symbol"].tolist()}
    return current, sp100


def make_intervals(changes: list[dict], current: dict[str, str], sp100: set[str]) -> list[dict]:
    # The current components page is the post-change roster at the cutoff.
    # Reverse 2020-06..cutoff changes to recover the roster at the left edge.
    active = set(current)
    bounded = [e for e in changes if WINDOW_START < e["date"] <= WINDOW_END]
    for e in sorted(bounded, key=lambda x: x["date"], reverse=True):
        if e["added"]:
            active.discard(e["added"])
        if e["removed"]:
            active.add(e["removed"])

    starts = {t: WINDOW_START for t in active}
    names = {t: current.get(t, t) for t in active}
    names.update({"IBM": "International Business Machines Corporation",
                  "MSCI": "MSCI Inc."})
    # For constituents removed after the window's left edge, the change table
    # provides the historical security name missing from today's list.
    for e in bounded:
        if e["removed"] in active and e["remove_name"]:
            names[e["removed"]] = e["remove_name"]
    start_sources = {t: "Wikipedia current components, reversed to 2020-06-01" for t in active}
    intervals = []
    for e in sorted(bounded, key=lambda x: x["date"]):
        d = e["date"]
        if e["removed"] and e["removed"] in starts:
            t = e["removed"]
            intervals.append({"ticker": t, "company": names.get(t, e["remove_name"]),
                              "effective_from": starts.pop(t).isoformat(),
                              "effective_to_exclusive": d.isoformat(),
                              "sp100_member_at_2026_10_30": int(t in sp100),
                              "start_source": start_sources.pop(t, ""),
                              "end_source_url": e["source_url"], "source_refs": e["wiki_refs"]})
        if e["added"]:
            t = e["added"]
            starts[t] = d
            names[t] = e["add_name"] or current.get(t, t)
            start_sources[t] = e["source_url"] or "Wikipedia historical changes table"
    for t, start in starts.items():
        intervals.append({"ticker": t, "company": current.get(t, names.get(t, t)),
                          "effective_from": start.isoformat(),
                          "effective_to_exclusive": RIGHT_EDGE.isoformat(),
                          "sp100_member_at_2026_10_30": int(t in sp100),
                          "start_source": start_sources.get(t, ""),
                          "end_source_url": "", "source_refs": "current components at cutoff"})
    intervals.sort(key=lambda r: (r["ticker"], r["effective_from"]))
    return intervals


def save_roster(intervals: list[dict]) -> None:
    pd.DataFrame(intervals).to_csv(OUT / "sp500_pit_roster.csv", index=False)


def download_ohlcv(intervals: list[dict]) -> tuple[pd.DataFrame, list[dict]]:
    tickers = sorted({r["ticker"] for r in intervals})
    # Use Yahoo's chart endpoint directly, one symbol per request, to avoid
    # yfinance's concurrent bursts; the data are the same daily Yahoo history.
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 FINS3666 research data pull"})
    p1 = int(datetime(2020, 6, 1, tzinfo=ZoneInfo("America/New_York")).timestamp())
    p2 = int(datetime(2026, 10, 31, tzinfo=ZoneInfo("America/New_York")).timestamp())
    output = []
    errors = []
    last_request = 0.0
    response_cache = {}
    history_aliases = {"WLTW": "WTW", "EQR": "VMRK"}
    for i, t in enumerate(tickers, 1):
        symbol = history_aliases.get(t, t).replace(".", "-")
        if symbol in response_cache:
            obj = response_cache[symbol]
        else:
            url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                   f"?period1={p1}&period2={p2}&interval=1d&events=div%2Csplits")
            obj = None
            for attempt in range(3):
                wait = 0.25 - (time.monotonic() - last_request)
                if wait > 0:
                    time.sleep(wait)
                try:
                    response = session.get(url, timeout=25)
                    last_request = time.monotonic()
                    if response.status_code == 429:
                        time.sleep(3 + attempt * 3)
                        continue
                    response.raise_for_status()
                    obj = response.json()
                    response_cache[symbol] = obj
                    break
                except Exception as exc:
                    if attempt == 2:
                        errors.append({"batch": i, "symbols": t, "error": str(exc)})
                        print(f"DOWNLOAD_ERROR {i}/{len(tickers)} {t} via {symbol}: {exc}", flush=True)
                    time.sleep(1 + attempt)
        try:
            result = obj["chart"]["result"][0] if obj else None
            if not result or not result.get("timestamp"):
                error = (obj or {}).get("chart", {}).get("error") if obj else "empty response"
                errors.append({"batch": i, "symbols": t, "error": str(error or "no bars")})
                continue
            quote = result["indicators"]["quote"][0]
            adj = result.get("indicators", {}).get("adjclose", [{}])[0].get("adjclose", [])
            dates = pd.to_datetime(result["timestamp"], unit="s", utc=True).tz_convert("America/New_York").date
            ticker_intervals = [(date.fromisoformat(r["effective_from"]),
                                 date.fromisoformat(r["effective_to_exclusive"]))
                                for r in intervals if r["ticker"] == t]
            for j, day in enumerate(dates):
                if not (WINDOW_START <= day <= WINDOW_END):
                    continue
                if not any(lo <= day < hi for lo, hi in ticker_intervals):
                    continue
                output.append({"date": pd.Timestamp(day), "ticker": t,
                               "open": quote.get("open", [None])[j],
                               "high": quote.get("high", [None])[j],
                               "low": quote.get("low", [None])[j],
                               "close": quote.get("close", [None])[j],
                               "adj_close": adj[j] if j < len(adj) else None,
                               "volume": quote.get("volume", [None])[j]})
        except Exception as exc:
            errors.append({"batch": i, "symbols": t, "error": f"parse: {exc}"})
        if i % 50 == 0 or i == len(tickers):
            print(f"SYMBOLS {i}/{len(tickers)} accumulated_rows={len(output)} errors={len(errors)}", flush=True)
    frame = pd.DataFrame(output)
    expected_columns = ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]
    for col in expected_columns:
        if col not in frame.columns:
            frame[col] = pd.NA
    frame = frame[expected_columns]
    frame = frame.sort_values(["ticker", "date"]).drop_duplicates(["ticker", "date"])
    if not frame.empty:
        frame["date"] = pd.to_datetime(frame["date"]).dt.tz_localize(None)
    frame.to_parquet(OUT / "sp500_ohlcv_dev.parquet", index=False)
    return frame, errors


def main():
    hist_html = get_html("https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500")
    changes = parse_changes(hist_html)
    current, sp100 = current_members()
    intervals = make_intervals(changes, current, sp100)
    save_roster(intervals)
    print(f"ROSTER intervals={len(intervals)} tickers={len({x['ticker'] for x in intervals})} "
          f"base={len(current)} sp100_endpoint={len(sp100)}", flush=True)
    frame, errors = download_ohlcv(intervals)
    by_ticker = frame.groupby("ticker").agg(rows=("date", "size"), first=("date", "min"), last=("date", "max")) if not frame.empty else pd.DataFrame()
    missing = sorted(set(x["ticker"] for x in intervals) - set(by_ticker.index)) if not frame.empty else sorted({x["ticker"] for x in intervals})
    print(f"DATA rows={len(frame)} tickers_with_bars={len(by_ticker)} missing={len(missing)} "
          f"missing_tickers={missing}", flush=True)
    pd.DataFrame(errors).to_csv(OUT / "download_errors.csv", index=False)


if __name__ == "__main__":
    main()
