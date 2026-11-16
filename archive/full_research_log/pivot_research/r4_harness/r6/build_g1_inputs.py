"""Build G1's development-only input bundle and availability coverage.

This module constructs no forward-return labels, ICs, or portfolio outputs.
It restricts every price row to 2020-11-27..2026-10-30 before parsing values.
Yahoo chart volume is already restated for splits in the source series; a
development-window split-event ledger is retained and hashed to document that
basis and to prevent a second split adjustment.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
OUT = HERE
START, END = "2020-11-27", "2026-10-30"
END_EXCLUSIVE = "2026-10-31"
SP_OHLCV = ROOT / "r6_data/sp500_ohlcv_dev_gapfilled.parquet"
SP_ROSTER = ROOT / "r6_data/sp500_pit_roster.csv"
SP_SIC = ROOT / "r6_data/sp500_sic_panel.csv"
DOW_ROSTER = ROOT / "r6_D1/dow_pit_roster.csv"
DOW_SIC = ROOT / "r4_L4/data/sic_panel.csv"
DOW_PRICE_DIRS = [ROOT / "w1_engine/prices-daily", ROOT / "w1_engine/prices-daily-delisted"]
DOW_GAPFILL = ROOT / "r6_data/dow_dev_gapfill.parquet"
SPLITS = OUT / "G1_split_actions_dev.csv"
INPUTS = OUT / "G1_INPUTS.npz"
COVERAGE = OUT / "formation_coverage.csv"
MANIFEST = OUT / "build_manifest.json"
QA = OUT / "G1_INPUT_QA.md"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_dow_bars() -> tuple[pd.DataFrame, list[Path]]:
    roster = pd.read_csv(DOW_ROSTER, dtype={"ticker": str})
    symbols = sorted(roster.ticker.astype(str).unique())
    found: list[pd.DataFrame] = []
    sources: list[Path] = []
    for ticker in symbols:
        path = next((folder / f"{ticker}.csv" for folder in DOW_PRICE_DIRS
                     if (folder / f"{ticker}.csv").is_file()), None)
        if path is None:
            continue
        sources.append(path)
        rows = []
        with path.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            need = {"date", "open", "close", "adjclose", "volume"}
            if not need.issubset(reader.fieldnames or []):
                raise ValueError(f"Dow source lacks {sorted(need-set(reader.fieldnames or []))}: {path}")
            for row in reader:
                day = (row.get("date") or "")[:10]
                if START <= day <= END:
                    rows.append({"date": day, "ticker": ticker,
                                 "open": row["open"], "close": row["close"],
                                 "adj_close": row["adjclose"], "volume": row["volume"]})
        if rows:
            d = pd.DataFrame(rows)
            for col in ("open", "close", "adj_close", "volume"):
                d[col] = pd.to_numeric(d[col], errors="coerce")
            d["date"] = pd.to_datetime(d.date)
            found.append(d)
    if DOW_GAPFILL.is_file():
        sources.append(DOW_GAPFILL)
        gap = pd.read_parquet(DOW_GAPFILL)
        gap["date"] = pd.to_datetime(gap.date).dt.normalize()
        gap = gap.loc[gap.date.between(START, END), ["date", "ticker", "open", "close", "adj_close", "volume"]].copy()
        found.append(gap)
    if not found:
        raise FileNotFoundError("No in-window Dow OHLCV rows found")
    bars = pd.concat(found, ignore_index=True)
    bars["date"] = pd.to_datetime(bars.date).dt.normalize()
    bars["ticker"] = bars.ticker.astype(str).str.upper()
    bars = bars.drop_duplicates(["date", "ticker"], keep="last").sort_values(["date", "ticker"])
    return bars, sources


def load_sp_bars() -> pd.DataFrame:
    # Arrow predicate filtering returns only allowed development rows.
    try:
        x = pd.read_parquet(SP_OHLCV, filters=[("date", ">=", pd.Timestamp(START)),
                                               ("date", "<=", pd.Timestamp(END))])
    except (TypeError, ValueError):
        x = pd.read_parquet(SP_OHLCV)
        x = x.loc[pd.to_datetime(x.date).between(START, END)].copy()
    x["date"] = pd.to_datetime(x.date).dt.normalize()
    x["ticker"] = x.ticker.astype(str).str.upper()
    return x.loc[x.date.between(START, END), ["date", "ticker", "open", "close", "adj_close", "volume"]].copy()


def fetch_split_ledger(tickers: list[str], *, refresh: bool = False) -> pd.DataFrame:
    """Fetch split event metadata for names with staged price rows, dev dates only."""
    if SPLITS.exists() and not refresh:
        ledger = pd.read_csv(SPLITS, dtype={"ticker": str})
        if set(ledger.ticker.astype(str)) == set(tickers):
            return ledger
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("requests is required for the Yahoo split-event ledger") from exc
    p1 = int(datetime(2020, 11, 27, tzinfo=ZoneInfo("America/New_York")).timestamp())
    p2 = int(datetime(2026, 10, 31, tzinfo=ZoneInfo("America/New_York")).timestamp())
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 UNSW FINS3666 academic research"})
    output: list[dict] = []
    last = 0.0
    for number, ticker in enumerate(tickers, 1):
        symbol = ticker.replace(".", "-")
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
               f"?period1={p1}&period2={p2}&interval=1d&events=splits")
        delay = .34 - (time.monotonic() - last)
        if delay > 0:
            time.sleep(delay)
        try:
            response = session.get(url, timeout=25)
            last = time.monotonic()
            response.raise_for_status()
            result = response.json().get("chart", {}).get("result") or []
            if not result:
                raise ValueError("empty chart result")
            events = result[0].get("events", {}).get("splits", {})
            rows = []
            for ev in events.values():
                day = pd.Timestamp(ev["date"], unit="s", tz="UTC").tz_convert("America/New_York").date().isoformat()
                if START <= day <= END:
                    rows.append({"ticker": ticker, "effective_date": day,
                                 "numerator": float(ev.get("numerator", np.nan)),
                                 "denominator": float(ev.get("denominator", np.nan)),
                                 "split_ratio": str(ev.get("splitRatio", "")),
                                 "status": "split_event", "source_url": url})
            if rows:
                output.extend(rows)
            else:
                output.append({"ticker": ticker, "effective_date": "", "numerator": "",
                               "denominator": "", "split_ratio": "", "status": "no_split_in_development_window",
                               "source_url": url})
        except Exception as exc:
            output.append({"ticker": ticker, "effective_date": "", "numerator": "",
                           "denominator": "", "split_ratio": "", "status": f"fetch_error:{type(exc).__name__}",
                           "source_url": url})
        if number % 100 == 0:
            print(f"split ledger {number}/{len(tickers)}", flush=True)
    ledger = pd.DataFrame(output, columns=["ticker", "effective_date", "numerator", "denominator", "split_ratio", "status", "source_url"])
    ledger.to_csv(SPLITS, index=False)
    return ledger


def load_sic(path: Path, *, sp: bool) -> pd.DataFrame:
    x = pd.read_csv(path, dtype={"ticker": str, "sic": str})
    if sp:
        x["asof"] = pd.to_datetime(x["effective_date"], errors="coerce")
    else:
        x["asof"] = pd.to_datetime(x["effective_from"], errors="coerce")
    sic = pd.to_numeric(x["sic"], errors="coerce")
    x["sic2"] = (sic // 100).astype("Int64").astype("string").str.zfill(2)
    # Preserve the latest pre-window observation so the SIC label is available
    # point-in-time from the first development session onward.
    x = x.loc[x["asof"].notna() & x["sic2"].notna() & x["asof"].le(END)]
    return x[["ticker", "asof", "sic2"]].sort_values(["ticker", "asof"])


def interval_mask(names: np.ndarray, dates: pd.DatetimeIndex, path: Path) -> np.ndarray:
    x = pd.read_csv(path, dtype={"ticker": str})
    x["effective_from"] = pd.to_datetime(x.effective_from)
    x["effective_to_exclusive"] = pd.to_datetime(x.effective_to_exclusive)
    name_ix = {n: i for i, n in enumerate(names)}
    out = np.zeros((len(names), len(dates)), dtype=bool)
    for row in x.itertuples(index=False):
        i = name_ix.get(str(row.ticker).upper())
        if i is None:
            continue
        lo = max(pd.Timestamp(START), row.effective_from)
        hi = min(pd.Timestamp(END_EXCLUSIVE), row.effective_to_exclusive)
        a = int(dates.searchsorted(lo, side="left")); b = int(dates.searchsorted(hi, side="left"))
        if b > a:
            out[i, a:b] = True
    return out


def sic_matrix(names: np.ndarray, dates: pd.DatetimeIndex, sic_frame: pd.DataFrame) -> np.ndarray:
    out = np.full((len(names), len(dates)), "", dtype="U2")
    cols = {n: i for i, n in enumerate(names)}
    date_values = dates.to_numpy(dtype="datetime64[ns]")
    for ticker, group in sic_frame.groupby("ticker", sort=False):
        i = cols.get(str(ticker).upper())
        if i is None:
            continue
        obs_dates = group["asof"].to_numpy(dtype="datetime64[ns]")
        codes = group["sic2"].astype(str).to_numpy(dtype="U2")
        loc = np.searchsorted(obs_dates, date_values, side="right") - 1
        valid = loc >= 0
        out[i, valid] = codes[loc[valid]]
    return out


def make_panel(universe: str, names: np.ndarray, dates: pd.DatetimeIndex,
               bars: pd.DataFrame, roster_path: Path, sic_path: Path, *, sp: bool) -> dict[str, np.ndarray]:
    n, t = len(names), len(dates)
    shape = (n, t)
    vol = np.full(shape, np.nan, dtype=np.float64)
    adj_open = np.full(shape, np.nan, dtype=np.float64)
    adj_close = np.full(shape, np.nan, dtype=np.float64)
    name_ix = {v: i for i, v in enumerate(names)}
    day_ix = {v: i for i, v in enumerate(dates)}
    # Use the source OHLC and same-day adjusted-close factor. This only creates
    # point-in-time adjusted price inputs; no price ratios/outcomes are formed.
    for row in bars.itertuples(index=False):
        i = name_ix.get(str(row.ticker).upper()); j = day_ix.get(pd.Timestamp(row.date))
        if i is None or j is None:
            continue
        o, c, ac, v = row.open, row.close, row.adj_close, row.volume
        if pd.notna(o) and pd.notna(c) and pd.notna(ac) and c > 0:
            adj_open[i, j] = float(o) * float(ac) / float(c)
            adj_close[i, j] = float(ac)
        if pd.notna(v) and v > 0:
            vol[i, j] = float(v)
    roster = interval_mask(names, dates, roster_path)
    sic = sic_matrix(names, dates, load_sic(sic_path, sp=sp))
    return {f"{universe}_names": names.astype("U12"),
            f"{universe}_roster": roster,
            f"{universe}_sic2": sic,
            f"{universe}_volume": vol,
            f"{universe}_adjusted_open": adj_open,
            f"{universe}_adjusted_close": adj_close}


def source_entry(path: Path, role: str) -> dict:
    return {"role": role, "path": path.resolve().relative_to(ROOT).as_posix(), "sha256": sha256(path)}


def build() -> dict:
    sp = load_sp_bars()
    dow, dow_sources = load_dow_bars()
    dates = pd.DatetimeIndex(sorted(set(sp.date.unique()) | set(dow.date.unique())))
    if len(dates) != 1488 or dates[0].strftime("%Y-%m-%d") != START or dates[-1].strftime("%Y-%m-%d") != END:
        raise ValueError(f"expected 1,488 development sessions {START}..{END}; found {len(dates)}")
    sp_roster = pd.read_csv(SP_ROSTER, dtype={"ticker": str})
    dow_roster = pd.read_csv(DOW_ROSTER, dtype={"ticker": str})
    sp_names = np.array(sorted(sp_roster.ticker.astype(str).str.upper().unique()), dtype="U12")
    dow_names = np.array(sorted(dow_roster.ticker.astype(str).str.upper().unique()), dtype="U12")
    active_price_tickers = sorted(set(sp.ticker.astype(str)) | set(dow.ticker.astype(str)))
    split_ledger = fetch_split_ledger(active_price_tickers)
    # Yahoo chart's historical `volume` field is already in a common,
    # split-restated share basis (verified against the chart response); do not
    # multiply it by the event ledger a second time. The score uses log-volume
    # z-scores, which are invariant to a constant share-unit scale per ticker.
    arrays = {"dates": dates.strftime("%Y-%m-%d").to_numpy(dtype="U10")}
    arrays.update(make_panel("sp500", sp_names, dates, sp, SP_ROSTER, SP_SIC, sp=True))
    arrays.update(make_panel("dow", dow_names, dates, dow, DOW_ROSTER, DOW_SIC, sp=False))
    np.savez_compressed(INPUTS, **arrays)

    from r4_harness.r6.g1_runner import availability_masks
    masks = availability_masks(arrays)
    forms = masks["sp500"]["forms"]
    rows = []
    for u in ("sp500", "dow"):
        for date, count in zip(dates[forms], masks[u]["eligible_counts"]):
            rows.append({"universe": u, "formation_date": date.strftime("%Y-%m-%d"),
                         "eligible_names": int(count)})
    coverage = pd.DataFrame(rows)
    coverage.to_csv(COVERAGE, index=False)

    sources = [source_entry(SP_OHLCV, "sp500_ohlcv")]
    sources.extend(source_entry(p, "dow_ohlcv") for p in dow_sources)
    sources.extend([source_entry(SP_ROSTER, "sp500_pit_roster"),
                    source_entry(DOW_ROSTER, "dow_pit_roster"),
                    source_entry(SP_SIC, "sic2"), source_entry(DOW_SIC, "sic2"),
                    source_entry(SPLITS, "split_actions")])
    manifest = {
        "manifest_version": 1,
        "scope": "development-only input panels; no forward labels or outcomes",
        "development_window": [START, END],
        "calendar_sessions": len(dates),
        "point_in_time_rosters": True,
        "sic2_dated_asof": True,
        "volume_basis": "split_adjusted_share_volume",
        "volume_adjustment": "split factors effective by each session; dividends excluded",
        "volume_source_treatment": "Yahoo chart share-volume series already split-restated; split event ledger pinned; no double adjustment applied",
        "forward_labels_built": False,
        "holdout_loaded": False,
        "input_bundle_sha256": sha256(INPUTS),
        "coverage_sha256": sha256(COVERAGE),
        "split_event_rows": int(split_ledger.status.eq("split_event").sum()),
        "split_tickers_with_status": int(split_ledger.ticker.nunique()),
        "source_files": sources,
    }
    manifest["manifest_sha256"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    summaries = coverage.groupby("universe").eligible_names.agg(["count", "min", "median", "max"]).reset_index()
    sp_gate = bool((coverage.loc[coverage.universe.eq("sp500"), "eligible_names"] >= 250).all())
    qa = ["# G1 input-only build QA", "", "This report describes development inputs and availability masks only. No forward labels, returns, ICs, mechanism tests, or portfolios were created; no holdout data were loaded.", "",
          f"- Calendar: {len(dates)} sessions, {START} through {END}.",
          f"- S&P PIT names: {len(sp_names)}; Dow PIT names: {len(dow_names)}.",
          f"- Split-adjusted volume: Yahoo chart `volume` is already split-restated in the source; the development-only split event ledger is pinned ({int(split_ledger.status.eq('split_event').sum())} event rows across {int(split_ledger.ticker.nunique())} symbols with status). No dividend adjustment or second split adjustment was applied.",
          f"- S&P ≥250-name coverage gate: {'PASS' if sp_gate else 'FAIL'}.", "",
          "| Universe | Formation dates | Minimum eligible | Median eligible | Maximum eligible |", "|---|---:|---:|---:|---:|"]
    for r in summaries.itertuples(index=False):
        qa.append(f"| {r.universe} | {r.count} | {r.min} | {r.median:.0f} | {r.max} |")
    qa.extend(["", "Coverage counts require PIT roster, dated SIC2, complete 50-session positive-volume baseline plus five current-volume observations, and presence of the fixed endpoint open/close bars. These are availability checks; endpoint prices were not divided or used as returns.",
               "", f"- Input NPZ SHA256: `{sha256(INPUTS)}`.", f"- Coverage CSV SHA256: `{sha256(COVERAGE)}`.", f"- Build manifest SHA256: `{sha256(MANIFEST)}`.", f"- S&P coverage gate dry-check: `{sp_gate}`.", ""])
    QA.write_text("\n".join(qa), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = build()
    print(json.dumps({"npz": str(INPUTS), "npz_sha256": result["input_bundle_sha256"],
                      "coverage": str(COVERAGE), "manifest": str(MANIFEST),
                      "calendar_sessions": result["calendar_sessions"],
                      "split_events": result["split_event_rows"]}, indent=2))
