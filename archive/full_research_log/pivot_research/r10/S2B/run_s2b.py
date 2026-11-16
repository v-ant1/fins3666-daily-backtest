from __future__ import annotations

import json, math, re, time, threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import dotenv_values

from event_harness import END, START, evaluate

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PANEL = ROOT / "r9" / "data" / "J2_DEV_FROM_20201127.npz"
ROSTER = ROOT / "r9" / "data" / "sp500_pit_roster_with_announcements.csv"
LINEAGE = ROOT / "r6_data" / "historical_ticker_cik_lineage.csv"
ENV = ROOT.parent / ".env"
DEV0, DEV1 = date(2020, 11, 27), date(2026, 10, 30)
SEC_UA = "FINS3666 generic research contact research@example.edu"
SEC_ROOT = "https://data.sec.gov"
ARCHIVE = "https://www.sec.gov/Archives/edgar/data"
ALPACA_ROOT = "https://data.alpaca.markets/v2/stocks"
NY = ZoneInfo("America/New_York")


class ThrottledGet:
    def __init__(self, minimum_gap: float, headers: dict[str, str]):
        self.gap = minimum_gap
        self.last = 0.0
        self.lock = threading.Lock()
        self.local = threading.local()
        self.headers = headers

    def get(self, url: str, **kwargs):
        with self.lock:
            wait = self.gap - (time.monotonic() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.monotonic()
        if not hasattr(self.local, "session"):
            self.local.session = requests.Session()
        response = self.local.session.get(url, headers=self.headers, timeout=60, **kwargs)
        if response.status_code == 429:
            time.sleep(2.0)
            with self.lock:
                wait = self.gap - (time.monotonic() - self.last)
                if wait > 0:
                    time.sleep(wait)
                self.last = time.monotonic()
            response = self.local.session.get(url, headers=self.headers, timeout=60, **kwargs)
        return response


def bounded_filing_texts(sec: ThrottledGet, filings: list[dict[str, str]], workers: int = 8):
    # Keep both request rate and in-flight response memory bounded.
    for start in range(0, len(filings), 100):
        chunk = filings[start:start+100]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            yield from pool.map(lambda filing: filing_text(sec, filing), chunk)


def api_ticker(t: str) -> str:
    return {"BF-B": "BF.B", "BRK-B": "BRK.B"}.get(t.upper(), t.upper())


def first_session_in_month(ds: list[str], year: int, month: int) -> str | None:
    prefix = f"{year:04d}-{month:02d}-"
    return next((x for x in ds if x.startswith(prefix)), None)


def month_after(y: int, m: int) -> tuple[int, int]:
    return (y + 1, 1) if m == 12 else (y, m + 1)


def next_month_session(ds: list[str], d: date, strictly_after: bool = False) -> str | None:
    y, m = d.year, d.month
    if strictly_after:
        y, m = month_after(y, m)
    else:
        s = first_session_in_month(ds, y, m)
        if s and date.fromisoformat(s) > d:
            return s
        y, m = month_after(y, m)
    while date(y, m, 1) <= DEV1:
        s = first_session_in_month(ds, y, m)
        if s:
            return s
        y, m = month_after(y, m)
    return None


def get_dev_panel():
    with np.load(PANEL, allow_pickle=False) as z:
        all_dates = z["sp500_dates"].astype(str)
        keep = (all_dates >= START) & (all_dates <= END)
        dates = all_dates[keep]
        assets = np.array([str(x).upper().replace(".", "-") for x in z["sp500_assets"]])
        roster = z["sp500_roster"][:, keep].astype(bool)
        sic2 = z["sp500_sic2"][:, keep].astype(str)
        op = z["sp500_adjusted_open"][:, keep].astype(float).copy()
        cl = z["sp500_adjusted_close"][:, keep].astype(float).copy()
    return dates, assets, roster, sic2, op, cl


def read_cik_map(sec: ThrottledGet) -> dict[str, str]:
    global SEC_COMPANY_NAMES
    r = sec.get("https://www.sec.gov/files/company_tickers.json")
    r.raise_for_status()
    mapping: dict[str, str] = {}
    SEC_COMPANY_NAMES = {}
    for row in r.json().values():
        ticker = str(row.get("ticker", "")).upper().replace(".", "-")
        if ticker:
            mapping[ticker] = str(row["cik_str"]).zfill(10)
            SEC_COMPANY_NAMES[str(row["cik_str"]).zfill(10)] = str(row.get("title", "")).lower()
    lineage = pd.read_csv(LINEAGE, dtype=str).fillna("")
    for row in lineage.to_dict("records"):
        ticker, cik = row.get("ticker", "").upper().replace(".", "-"), row.get("cik", "")
        if ticker and cik.isdigit():
            mapping.setdefault(ticker, cik.zfill(10))
    return mapping


def fetch_submissions(sec: ThrottledGet, cik: str) -> list[dict[str, str]]:
    r = sec.get(f"{SEC_ROOT}/submissions/CIK{cik}.json")
    if not r.ok:
        return []
    recent = r.json().get("filings", {}).get("recent", {})
    result = []
    keys = ("accessionNumber", "filingDate", "acceptanceDateTime", "form", "items", "primaryDocument")
    for tup in zip(*(recent.get(k, [""] * len(recent.get("form", []))) for k in keys)):
        accession, filing_date, accepted, form, items, primary = tup
        try:
            accepted_day = date.fromisoformat(str(accepted)[:10])
        except Exception:
            continue
        if DEV0 <= accepted_day <= DEV1:
            result.append({"cik": cik, "accession": str(accession), "filed": str(filing_date),
                           "accepted": str(accepted), "accepted_date": accepted_day.isoformat(),
                           "form": str(form), "items": str(items or ""), "primary": str(primary or "")})
    return result


def filing_text(sec: ThrottledGet, filing: dict[str, str]) -> str:
    acc0 = filing["accession"]
    acc = acc0.replace("-", "")
    url = f"{ARCHIVE}/{int(filing['cik'])}/{acc}/{acc0}.txt"
    r = sec.get(url)
    if not r.ok:
        return ""
    return BeautifulSoup(r.content, "html.parser").get_text(" ", strip=True).lower()


def contains_cash_deal(text: str) -> bool:
    return bool(re.search(r"\b(cash|all.cash)\b.{0,100}\b(merger|acquisition|acquire|acquired)\b|\b(merger|acquisition|acquire|acquired)\b.{0,100}\b(cash|all.cash)\b", text))


def recent_dividend_fact(sec: ThrottledGet, cik: str, accepted: date, cache: dict[str, dict]) -> bool:
    if cik not in cache:
        r = sec.get(f"{SEC_ROOT}/api/xbrl/companyfacts/CIK{cik}.json")
        cache[cik] = r.json().get("facts", {}).get("us-gaap", {}) if r.ok else {}
    floor = accepted - timedelta(days=8*92)
    facts = cache[cik]
    for tag, detail in facts.items():
        if "Dividend" not in tag or "PerShare" not in tag or "CommonStock" not in tag:
            continue
        for vals in detail.get("units", {}).values():
            for x in vals:
                # Only development-window reported facts are inspected; prior boundary values remain unread.
                filed = x.get("filed", "")
                end = x.get("end", "")
                if filed and START <= filed < accepted.isoformat() and end and end >= START and end >= floor.isoformat():
                    try:
                        if float(x.get("val", 0)) > 0:
                            return True
                    except (TypeError, ValueError):
                        pass
    return False


def sec_events():
    raise RuntimeError("Full EDGAR filing-body census disabled by coordinator capacity direction.")
    sec = ThrottledGet(0.112, {"User-Agent": SEC_UA, "Accept-Encoding": "gzip, deflate"})
    tickers = read_cik_map(sec)
    dates, assets, roster, sic2, op, cl = get_dev_panel()
    ds = dates.tolist()
    issuer_by_cik = {cik: t for t, cik in tickers.items()}
    name_by_cik: dict[str, str] = {}
    metadata_path = OUT / "sec_dev_filing_metadata.json"
    if metadata_path.exists():
        all_subs = json.load(open(metadata_path, encoding="utf-8"))
        print(f"Reusing {len(all_subs)} cached development-window SEC metadata rows")
    else:
        all_subs = []
        ciks = sorted({tickers[a] for a in assets if a in tickers})
        for n, cik in enumerate(ciks, 1):
            subs = fetch_submissions(sec, cik)
            all_subs.extend(subs)
            if n % 100 == 0:
                print(f"SEC submissions checked: {n}/{len(ciks)}")
        # The issuer list is metadata only; all accepted dates are bounded to dev.
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(all_subs, f)
    assets_ix = {x: i for i, x in enumerate(assets)}
    cik_ix = {tickers[t]: i for i, t in enumerate(assets) if t in tickers}

    filings = defaultdict(list)
    for f in all_subs:
        if f["form"] == "8-K" and set(re.findall(r"\d+\.\d+", f["items"])) & {"8.01", "5.02", "1.01", "2.01"}:
            filings["8K"].append(f)
        elif f["form"] in ("8-K/A",) and set(re.findall(r"\d+\.\d+", f["items"])) & {"8.01", "5.02", "1.01", "2.01"}:
            filings["8K"].append(f)
        elif f["form"] == "424B5":
            filings["424B5"].append(f)
    print("candidate filing docs", {k: len(v) for k, v in filings.items()})

    event_lists = {f"S2-0{i}": [] for i in range(1, 7)}
    seen = {k: set() for k in event_lists}
    filings["8K"].sort(key=lambda f: (f["accepted_date"], f["cik"], f["accession"]))
    filings["424B5"].sort(key=lambda f: (f["accepted_date"], f["cik"], f["accession"]))
    qualifying_buyback_issuer = set()
    div_facts_cache: dict[str, dict] = {}
    roster_names = {}
    for row in pd.read_csv(ROSTER, dtype=str).fillna("").to_dict("records"):
        ticker = row.get("ticker", "").upper().replace(".", "-")
        if ticker in assets_ix and row.get("company"):
            roster_names[ticker] = row["company"].lower()
    for kind in ("8K", "424B5"):
        text_iter = bounded_filing_texts(sec, filings[kind])
        for n, filing in enumerate(filings[kind], 1):
            text = next(text_iter)
            cik, accepted = filing["cik"], date.fromisoformat(filing["accepted_date"])
            issuer = issuer_by_cik.get(cik)
            if not issuer or issuer not in assets_ix:
                continue
            itemset = set(re.findall(r"\d+\.\d+", filing["items"]))
            if kind == "8K" and itemset & {"8.01", "5.02"}:
                rep = bool(re.search(r"repurchase|buyback|buy back", text))
                auth = bool(re.search(r"authoriz\w*|board.{0,40}approv\w*", text))
                historical = bool(re.search(r"completed.{0,50}(repurchase|buyback)|historical.{0,50}(repurchase|buyback)|previously.{0,50}(repurchase|buyback)", text))
                is_amendment = filing["form"] == "8-K/A"
                if rep and auth and not historical and (not is_amendment or cik not in qualifying_buyback_issuer):
                    cohort = next_month_session(ds, accepted)
                    if cohort and not is_amendment and (cik, cohort[:7]) not in seen["S2-01"]:
                        event_lists["S2-01"].append({"event_date": accepted.isoformat(), "cohort_month": cohort, "asset": issuer})
                        seen["S2-01"].add((cik, cohort[:7]))
                        qualifying_buyback_issuer.add(cik)
                div_announce = "dividend" in text and bool(re.search(r"cash dividend|quarterly dividend|regular dividend", text))
                not_special = not bool(re.search(r"special dividend|one.time dividend|stock dividend", text))
                if div_announce and not_special:
                    cohort = next_month_session(ds, accepted)
                    prior_regular = recent_dividend_fact(sec, cik, accepted, div_facts_cache)
                    history_complete = accepted - timedelta(days=8*92) >= DEV0
                    initiation = history_complete and not prior_regular
                    # Explicit rate-change language is usable only if the document states a >=5% increase.
                    increase = bool(re.search(r"(increase|raised|raise).{0,80}(5%|five percent|[6-9]\d?%|\d{2,}%)", text))
                    if cohort and (initiation or increase) and (cik, cohort[:7]) not in seen["S2-03"]:
                        event_lists["S2-03"].append({"event_date": accepted.isoformat(), "cohort_month": cohort, "asset": issuer})
                        seen["S2-03"].add((cik, cohort[:7]))
            elif kind == "8K" and itemset & {"1.01", "2.01"}:
                if contains_cash_deal(text) and not re.search(r"terminated|termination of", text):
                    # EDGAR filing issuer is excluded as named acquirer; target text-to-CIK mapping is not assumed.
                    target = None
                    company_matches = [(name, t) for t, name in roster_names.items()
                                       if tickers.get(t) != cik and len(name) >= 8]
                    company_matches += [(name, issuer_by_cik.get(c)) for c, name in SEC_COMPANY_NAMES.items()
                                        if name and c != cik and issuer_by_cik.get(c) in assets_ix and len(name) >= 8]
                    company_matches.sort(key=lambda x: len(x[0]), reverse=True)
                    for name, t in company_matches:
                        if re.search(rf"\b{re.escape(name)}\b", text):
                            target = t; break
                    if target is None:
                        for t, c in tickers.items():
                            if t in assets_ix and c != cik and re.search(rf"\b{re.escape(t.lower())}\b", text):
                                target = t; break
                    ti = assets_ix.get(target)
                    cohort = next_month_session(ds, accepted)
                    if ti is not None and cohort and (cik, cohort[:7]) not in seen["S2-06"]:
                        s = sic2[ti, np.searchsorted(dates, cohort)]
                        peers = [assets[k] for k in range(len(assets)) if assets[k] != target and assets[k] != issuer
                                 and roster[k, np.searchsorted(dates, cohort)] and sic2[k, np.searchsorted(dates, cohort)] == s]
                        if len(peers) >= 3:
                            event_lists["S2-06"].extend({"event_date": accepted.isoformat(), "cohort_month": cohort, "asset": a} for a in peers)
                            seen["S2-06"].add((cik, cohort[:7]))
            elif kind == "424B5":
                positive = bool(re.search(r"underwritten.{0,100}offering|public offering.{0,100}underwritten|firm.commitment", text))
                primary = bool(re.search(r"newly issued|issue.{0,50}common shares|shares of common stock", text))
                priced = bool(re.search(r"priced at|public offering price|offering price", text))
                excluded = bool(re.search(r"at.the.market|\bATM\b|selling shareholders|convertible|preferred stock|shelf registration", text))
                if positive and primary and priced and not excluded:
                    cohort = next_month_session(ds, accepted)
                    if cohort and (cik, cohort[:7]) not in seen["S2-05"]:
                        event_lists["S2-05"].append({"event_date": accepted.isoformat(), "cohort_month": cohort, "asset": issuer})
                        seen["S2-05"].add((cik, cohort[:7]))
            if n % 200 == 0:
                print(f"SEC filing texts retrieved ({kind}): {n}/{len(filings[kind])}")

    # S2-02 uses first accepted 10-Q/K with a quarter repurchase fact and prior quarter shares.
    # Tag availability and report-period values are later derived from each issuer's companyfacts.
    for i, (t, cik) in enumerate((t, tickers[t]) for t in assets if t in tickers):
        r = sec.get(f"{SEC_ROOT}/api/xbrl/companyfacts/CIK{cik}.json")
        if not r.ok:
            continue
        facts = r.json().get("facts", {}).get("us-gaap", {})
        rep_tags = [k for k in facts if re.search(r"Repurchased.*Shares|Shares.*Repurchased", k, re.I)]
        share_tags = [k for k in facts if re.search(r"CommonStockSharesOutstanding|EntityCommonStockSharesOutstanding", k, re.I)]
        if not rep_tags or not share_tags:
            continue
        rep_vals, shares = [], []
        for tag in rep_tags:
            units = facts[tag].get("units", {})
            rep_vals += [(x, tag) for vals in units.values() for x in vals if x.get("form") in ("10-Q", "10-K")]
        for tag in share_tags:
            units = facts[tag].get("units", {})
            shares += [x for vals in units.values() for x in vals if x.get("form") in ("10-Q", "10-K")]
        rep_vals = sorted((x for x, tag in rep_vals if x.get("filed", "") >= START and x.get("filed", "") <= END), key=lambda x:x.get("filed", ""))
        shares = sorted((x for x in shares if x.get("filed", "") < END), key=lambda x:x.get("filed", ""))
        for x in rep_vals:
            try:
                val = float(x["val"])
                filed = date.fromisoformat(x["filed"])
                prior = [q for q in shares if q.get("filed", "") >= START
                         and q.get("end", "") < x.get("end", "")
                         and q.get("filed", "") < x.get("filed", "")]
                if val <= 0 or not prior:
                    continue
                denom = float(prior[-1]["val"])
                if denom <= 0:
                    continue
                # Group and rank across issuers below, retaining reported fact and filing availability.
                cohort = next_month_session(ds, filed)
                if cohort:
                    event_lists["S2-02"].append({"event_date": filed.isoformat(), "cohort_month": cohort,
                                                 "asset": t, "score": val/denom, "cik": cik, "period_end": x.get("end", "")})
                    break
            except Exception:
                continue
        if i % 100 == 0:
            print(f"SEC companyfacts checked: {i}/{len(assets)}")

    # Rank S2-02 company facts within month at top quintile (minimum five).
    by_month = defaultdict(list)
    for e in event_lists["S2-02"]:
        by_month[e["cohort_month"]].append(e)
    event_lists["S2-02"] = []
    for cohort, rows in by_month.items():
        if len(rows) >= 5:
            rows = sorted(rows, key=lambda e: e["score"], reverse=True)
            event_lists["S2-02"].extend(rows[:max(1, math.ceil(len(rows)*.2))])

    # Dated S&P deletion events from the provided PIT roster metadata, limited to dev exits.
    roster_csv = pd.read_csv(ROSTER, dtype=str).fillna("")
    for row in roster_csv.to_dict("records"):
        t = row["ticker"].upper().replace(".", "-")
        try:
            eff_exclusive = date.fromisoformat(row["effective_to_exclusive"])
        except Exception:
            continue
        eff = eff_exclusive if eff_exclusive <= DEV1 else (date.fromisoformat(ds[-1]) if eff_exclusive == DEV1 + timedelta(days=1) else eff_exclusive)
        if DEV0 <= eff <= DEV1 and t in assets_ix and any(host in row.get("end_source_url", "").lower() for host in ("spglobal.com", "spindices.com")):
            cohort = next_month_session(ds, eff, strictly_after=True)
            if cohort:
                event_lists["S2-04"].append({"event_date": eff.isoformat(), "cohort_month": cohort, "asset": t})

    return event_lists, dates, assets, roster, sic2, op, cl


def fill_alpaca_gaps(dates, assets, roster, sic2, op, cl):
    env = dotenv_values(ENV)
    key, secret = env.get("ALPACA_API_KEY"), env.get("ALPACA_SECRET_KEY")
    if not key or not secret:
        raise RuntimeError("Alpaca credential pair unavailable in configured dotenv file")
    api = ThrottledGet(.125, {"APCA-API-KEY-ID": str(key), "APCA-API-SECRET-KEY": str(secret), "accept": "application/json"})
    needed = [i for i in range(len(assets)) if np.any(roster[i] & (~np.isfinite(op[i]) | ~np.isfinite(cl[i])))]
    filled = 0; failed = 0
    start, end = dates[0], dates[-1]
    for n, i in enumerate(needed, 1):
        ticker = assets[i]
        symbol = quote(api_ticker(ticker), safe=".")
        params = {"timeframe": "1Day", "start": f"{start}T00:00:00Z", "end": f"{end}T23:59:59Z",
                  "feed": "sip", "adjustment": "all", "limit": 1000, "sort": "asc"}
        token = None; bars = {}
        for _ in range(5):
            q = dict(params)
            if token: q["page_token"] = token
            r = api.get(f"{ALPACA_ROOT}/{symbol}/bars", params=q)
            if not r.ok:
                bars = {}; break
            payload = r.json()
            for b in payload.get("bars", []):
                d = datetime.fromisoformat(b["t"].replace("Z", "+00:00")).astimezone(NY).date().isoformat()
                if d in dates.tolist(): bars[d] = (float(b["o"]), float(b["c"]))
            token = payload.get("next_page_token")
            if not token: break
        di = {d: j for j, d in enumerate(dates)}
        for d, (o, c) in bars.items():
            j = di[d]
            if not np.isfinite(op[i, j]): op[i, j] = o; filled += 1
            if not np.isfinite(cl[i, j]): cl[i, j] = c; filled += 1
        if not bars: failed += 1
        if n % 50 == 0: print(f"Alpaca gap symbols: {n}/{len(needed)}")
    np.savez_compressed(OUT / "dev_panel_prices.npz", dates=dates, assets=assets, roster=roster,
                        sic2=sic2, adjusted_open=op, adjusted_close=cl)
    return {"symbols_requested": len(needed), "price_values_filled": filled, "symbols_without_bars": failed,
            "open_gaps_remaining": int((roster & ~np.isfinite(op)).sum()),
            "close_gaps_remaining": int((roster & ~np.isfinite(cl)).sum())}


def clean_json(x):
    if isinstance(x, dict): return {k: clean_json(v) for k, v in x.items()}
    if isinstance(x, list): return [clean_json(v) for v in x]
    if isinstance(x, (float, np.floating)) and not math.isfinite(float(x)): return None
    if isinstance(x, np.integer): return int(x)
    return x


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.prepare_only == args.execute:
        parser.error("choose exactly one of --prepare-only or --execute")
    if args.prepare_only:
        event_lists, dates, assets, roster, sic2, op, cl = sec_events()
        gap_summary = fill_alpaca_gaps(dates, assets, roster, sic2, op, cl)
        with (OUT / "dev_events.json").open("w", encoding="utf-8") as f:
            json.dump(event_lists, f, indent=2)
        with (OUT / "PREPARED.json").open("w", encoding="utf-8") as f:
            json.dump({"gap_fill": gap_summary, "event_counts": {k: len(v) for k,v in event_lists.items()},
                       "outcomes_computed": False}, f, indent=2)
        print(json.dumps({"gap_fill": gap_summary, "n_cohorts": {k: len(v) for k,v in event_lists.items()},
                          "outcomes_computed": False}, indent=2))
        return
    with np.load(OUT / "dev_panel_prices.npz", allow_pickle=False) as z:
        dates, assets, roster, sic2 = z["dates"], z["assets"], z["roster"], z["sic2"]
        op, cl = z["adjusted_open"], z["adjusted_close"]
    event_lists = json.load(open(OUT / "dev_events.json", encoding="utf-8"))
    results = {}
    for idea in [f"S2-0{i}" for i in range(1, 7)]:
        rows = event_lists[idea]
        events = [{"event_date": r["event_date"], "cohort_month": r["cohort_month"], "asset": r["asset"]} for r in rows]
        results[idea] = evaluate(events, dates, assets, roster, sic2, op, cl)
        print(idea, "cohorts", len(events), "usable", results[idea]["n_months"])
    with (OUT / "DEV_RESULTS.json").open("w", encoding="utf-8") as f:
        json.dump(clean_json({"results": results}), f, indent=2, allow_nan=False)
    print(json.dumps(clean_json({"n_cohorts": {k: len(v) for k,v in event_lists.items()},
                                 "n_usable": {k: v["n_months"] for k,v in results.items()}}), indent=2))


if __name__ == "__main__":
    main()
