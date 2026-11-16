"""Stage K1's development-only price bundle and auditable input manifest.

This builder deliberately creates no forward labels, returns, ICs, or outcomes.
All price scans are filtered to 2020-11-27 through 2026-10-30 before values are
materialized. Run from the project root with Python, pandas, NumPy and PyArrow.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
START, END = "2020-11-27", "2026-10-30"
EVENT_START, EVENT_END = "2020-11-30", "2026-09-30"
NY = ZoneInfo("America/New_York")

SP_PRICES = ROOT / "r6_data" / "sp500_ohlcv_dev_gapfilled.parquet"
DOW_PRICES = ROOT / "r6_C1" / "dow_components_dev.parquet"
DOW_GAP = ROOT / "r6_data" / "dow_dev_gapfill.parquet"
SPY_PRICES = ROOT / "r6_data" / "etf" / "etf_ohlcv_dev.parquet"
EVENTS = ROOT / "r6_data" / "earnings_clock_sp500.csv"
SP_ROSTER = ROOT / "r6_data" / "sp500_pit_roster.csv"
DOW_ROSTER = ROOT / "r6_D1" / "dow_pit_roster.csv"
SP_SIC = ROOT / "r6_data" / "sp500_sic_panel.csv"
DOW_SIC = ROOT / "r6_C1" / "dow_sic_membership.csv"
OUT_BUNDLE = HERE / "K1_INPUTS.npz"
OUT_SPY = HERE / "K1_SPY_DEV.csv"
OUT_QA = HERE / "K1_INPUT_COVERAGE.md"
OUT_MANIFEST = HERE / "K1_INPUT_MANIFEST.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_dev_parquet(path: Path, columns: list[str], *, spy_only=False) -> pd.DataFrame:
    dataset = ds.dataset(str(path), format="parquet")
    lo, hi = datetime(2020, 11, 27), datetime(2026, 10, 30)
    # Source schemas vary only in date representation. Filter before table values
    # are materialized; the ETF table uses ISO strings and is restricted to SPY.
    if "string" in str(dataset.schema.field("date").type):
        filt = (ds.field("date") >= START) & (ds.field("date") <= END)
    else:
        filt = (ds.field("date") >= lo) & (ds.field("date") <= hi)
    if spy_only:
        filt = filt & (ds.field("ticker") == "SPY")
    return dataset.to_table(columns=columns, filter=filt).to_pandas()


def intervals_matrix(roster_path: Path, tickers: list[str], dates: list[str]) -> np.ndarray:
    r = pd.read_csv(roster_path, dtype=str).fillna("")
    d = pd.to_datetime(pd.Series(dates))
    ix = {t: i for i, t in enumerate(tickers)}
    mat = np.zeros((len(tickers), len(dates)), dtype=bool)
    for row in r.itertuples(index=False):
        ticker = str(row.ticker)
        if ticker not in ix:
            continue
        lo = pd.Timestamp(row.effective_from)
        hi = pd.Timestamp(row.effective_to_exclusive) if row.effective_to_exclusive else pd.Timestamp.max
        active = (d >= lo) & (d < hi)
        mat[ix[ticker], np.asarray(active)] = True
    return mat


def dated_sic_matrix(sic_path: Path, tickers: list[str], dates: list[str], *, interval: bool) -> np.ndarray:
    s = pd.read_csv(sic_path, dtype=str).fillna("")
    out = np.full((len(tickers), len(dates)), "", dtype="<U2")
    ix = {t: i for i, t in enumerate(tickers)}
    d = pd.to_datetime(pd.Series(dates))
    if interval:
        for row in s.itertuples(index=False):
            ticker = str(row.ticker)
            if ticker not in ix:
                continue
            lo = pd.Timestamp(row.effective_from)
            hi = pd.Timestamp(row.effective_to_exclusive) if row.effective_to_exclusive else pd.Timestamp.max
            sic = str(row.sic2).strip().zfill(2)
            active = (d >= lo) & (d < hi)
            out[ix[ticker], np.asarray(active)] = sic
    else:
        s["effective_date"] = pd.to_datetime(s["effective_date"], errors="coerce")
        s["sic2"] = s["sic"].str.strip().str.zfill(4).str[:2]
        for ticker, group in s.dropna(subset=["effective_date"]).groupby("ticker", sort=False):
            if str(ticker) not in ix:
                continue
            group = group.sort_values("effective_date")
            eff = group["effective_date"].to_numpy(dtype="datetime64[ns]")
            sic = group["sic2"].astype(str).to_numpy(dtype=str)
            pos = np.searchsorted(eff, d.to_numpy(dtype="datetime64[ns]"), side="right") - 1
            valid = pos >= 0
            out[ix[str(ticker)], valid] = np.char.zfill(sic[pos[valid]], 2)
    out[(out == "00") | (out == "0")] = ""
    return out


def matrix_from_long(frame: pd.DataFrame, tickers: list[str], dates: list[str], field: str) -> np.ndarray:
    out = np.full((len(tickers), len(dates)), np.nan, dtype=np.float64)
    tx, dx = {t: i for i, t in enumerate(tickers)}, {d: j for j, d in enumerate(dates)}
    for row in frame[["date", "ticker", field]].itertuples(index=False, name=None):
        day, ticker, value = row
        day = pd.Timestamp(day).strftime("%Y-%m-%d")
        if ticker in tx and day in dx and pd.notna(value):
            out[tx[ticker], dx[day]] = float(value)
    return out


def build_prices():
    sp = read_dev_parquet(SP_PRICES, ["date", "ticker", "open", "close", "adj_close"])
    sp["date"] = pd.to_datetime(sp["date"]).dt.strftime("%Y-%m-%d")
    sp["adj_open"] = sp["open"] * sp["adj_close"] / sp["close"]
    sp["adj_close_input"] = sp["adj_close"]
    dates = sorted(sp.date.unique().tolist())

    dow = read_dev_parquet(DOW_PRICES, ["date", "ticker", "adj_open", "adj_close"])
    gap = read_dev_parquet(DOW_GAP, ["date", "ticker", "open", "close", "adj_close"])
    gap["adj_open"] = gap["open"] * gap["adj_close"] / gap["close"]
    gap["adj_close_input"] = gap["adj_close"]
    base = dow.rename(columns={"adj_close": "adj_close_input"})
    dow = pd.concat([base[["date", "ticker", "adj_open", "adj_close_input"]],
                     gap[["date", "ticker", "adj_open", "adj_close_input"]]], ignore_index=True)
    dow["date"] = pd.to_datetime(dow["date"]).dt.strftime("%Y-%m-%d")
    dow = dow.drop_duplicates(["date", "ticker"], keep="last")

    spy = read_dev_parquet(SPY_PRICES, ["date", "ticker", "open", "close", "adj_close"], spy_only=True)
    spy["date"] = pd.to_datetime(spy["date"]).dt.strftime("%Y-%m-%d")
    spy["adj_open"] = spy["open"] * spy["adj_close"] / spy["close"]
    spy["adj_close_input"] = spy["adj_close"]
    spy = spy[spy.date.isin(dates)]
    if sorted(spy.date.unique().tolist()) != dates:
        missing = sorted(set(dates) - set(spy.date.unique()))
        raise ValueError(f"SPY daily session coverage differs from S&P calendar; missing={missing[:5]}")

    sp_tickers, dow_tickers = sorted(sp.ticker.unique()), sorted(dow.ticker.unique())
    sp_open = matrix_from_long(sp, sp_tickers, dates, "adj_open")
    sp_close = matrix_from_long(sp, sp_tickers, dates, "adj_close_input")
    dow_open = matrix_from_long(dow, dow_tickers, dates, "adj_open")
    dow_close = matrix_from_long(dow, dow_tickers, dates, "adj_close_input")
    so = matrix_from_long(spy, ["SPY"], dates, "adj_open")[0]
    sc = matrix_from_long(spy, ["SPY"], dates, "adj_close_input")[0]
    sp_roster = intervals_matrix(SP_ROSTER, sp_tickers, dates)
    dow_roster = intervals_matrix(DOW_ROSTER, dow_tickers, dates)
    sp_sic = dated_sic_matrix(SP_SIC, sp_tickers, dates, interval=False)
    dow_sic = dated_sic_matrix(DOW_SIC, dow_tickers, dates, interval=True)

    np.savez_compressed(OUT_BUNDLE,
        dates=np.asarray(dates, dtype="U10"),
        sp500_tickers=np.asarray(sp_tickers, dtype="U16"), sp500_open=sp_open,
        sp500_close=sp_close, sp500_roster=sp_roster, sp500_sic2=sp_sic,
        dow_tickers=np.asarray(dow_tickers, dtype="U16"), dow_open=dow_open,
        dow_close=dow_close, dow_roster=dow_roster, dow_sic2=dow_sic,
        spy_open=so, spy_close=sc)
    pd.DataFrame({"date": dates, "spy_adj_open": so, "spy_adj_close": sc}).to_csv(OUT_SPY, index=False)
    return sp, dow, spy, dates, sp_tickers, dow_tickers, sp_roster, dow_roster, sp_sic, dow_sic


def roster_active(tickers, roster, j):
    return {tickers[i] for i in np.flatnonzero(roster[:, j])}


def event_coverage(universe, tickers, close, roster, sic, dates, events):
    date_i = {d: j for j, d in enumerate(dates)}
    ticker_i = {t: i for i, t in enumerate(tickers)}
    # Deduplicate exactly by CIK and report quarter, keeping earliest accepted
    # qualifying BMO/AMC record; no return values are formed or inspected.
    ev = events.copy()
    ev = ev[ev.classification.isin(["BMO", "AMC"])].copy()
    ev["acceptance_timestamp_et"] = pd.to_datetime(ev["acceptance_timestamp_et"], utc=True).dt.tz_convert(NY)
    ev["report_date"] = pd.to_datetime(ev["report_date"], errors="coerce")
    ev = ev.dropna(subset=["report_date"])
    ev["report_quarter"] = ev.report_date.dt.to_period("Q").astype(str)
    ev = ev.sort_values("acceptance_timestamp_et").drop_duplicates(["cik", "report_quarter"], keep="first")
    rows = []
    for _, r in ev.iterrows():
        ts = r.acceptance_timestamp_et.to_pydatetime()
        i = None
        for j, d in enumerate(dates):
            op = datetime.fromisoformat(d).replace(tzinfo=NY, hour=9, minute=30)
            if op > ts:
                i = j
                break
        if i is None or dates[i] < EVENT_START or dates[i] > EVENT_END or i == 0:
            continue
        q = pd.Timestamp(dates[i]).to_period("Q").strftime("%YQ%q")
        ticker = str(r.ticker)
        ti = ticker_i.get(ticker)
        has_asset = ti is not None
        is_member = bool(has_asset and roster[ti, i])
        sic_known = bool(has_asset and sic[ti, i] not in ("", "00"))
        stock_px = bool(has_asset and np.isfinite(close[ti, i]) and close[ti, i] > 0
                        and np.isfinite(close[ti, i-1]) and close[ti, i-1] > 0)
        spy_px = bool(np.isfinite(spy_close_global[i]) and spy_close_global[i] > 0
                      and np.isfinite(spy_close_global[i-1]) and spy_close_global[i-1] > 0)
        rows.append({"quarter": q, "classification": str(r.classification), "mapped_ticker": has_asset,
                     "member": is_member, "sic": sic_known, "stock_closes": stock_px,
                     "spy_closes": spy_px, "input_complete": bool(is_member and sic_known and stock_px and spy_px)})
    df = pd.DataFrame(rows)
    quarters = [f"{y}Q{q}" for y in range(2020, 2027) for q in range(1, 5)]
    result = []
    for q in quarters:
        sub = df[df.quarter == q] if len(df) else pd.DataFrame()
        result.append({"quarter": q, "events_bmo_amc": len(sub),
            "BMO": int((sub.classification == "BMO").sum()) if len(sub) else 0,
            "AMC": int((sub.classification == "AMC").sum()) if len(sub) else 0,
            "ticker_price_panel": int(sub.mapped_ticker.sum()) if len(sub) else 0,
            "PIT_member": int(sub.member.sum()) if len(sub) else 0,
            "SIC2_known": int(sub.sic.sum()) if len(sub) else 0,
            "stock_close_pair": int(sub.stock_closes.sum()) if len(sub) else 0,
            "SPY_close_pair": int(sub.spy_closes.sum()) if len(sub) else 0,
            "all_signal_inputs_available": int(sub.input_complete.sum()) if len(sub) else 0})
    return result


def main():
    global spy_close_global
    (sp, dow, spy, dates, sp_tickers, dow_tickers, sp_roster, dow_roster,
     sp_sic, dow_sic) = build_prices()
    with np.load(OUT_BUNDLE, allow_pickle=False) as z:
        spy_close_global = z["spy_close"].copy()
        sp_close, dow_close = z["sp500_close"].copy(), z["dow_close"].copy()
    events = pd.read_csv(EVENTS, dtype={"cik": str, "ticker": str})
    sp_cov = event_coverage("S&P 500", sp_tickers, sp_close, sp_roster, sp_sic, dates, events)
    dow_cov = event_coverage("Dow 30", dow_tickers, dow_close, dow_roster, dow_sic, dates, events)

    d = pd.to_datetime(pd.Series(dates))
    sp_counts = sp_roster.sum(axis=0)
    dow_counts = dow_roster.sum(axis=0)
    sp_price_names = np.isfinite(sp_close).sum(axis=0)
    dow_price_names = np.isfinite(dow_close).sum(axis=0)
    sp_sic_names = ((sp_sic != "") & sp_roster).sum(axis=0)
    dow_sic_names = ((dow_sic != "") & dow_roster).sum(axis=0)
    lines = [
        "# K1 development input coverage (input-only)", "",
        "Generated from staged data on 2026-11-11. This report counts only input availability; it contains no forward labels, returns, ICs, or portfolio outcomes.", "",
        "## Price panel boundaries and coverage", "",
        f"- Common trading-session calendar: {len(dates):,} dates, {dates[0]} through {dates[-1]}.",
        f"- S&P 500 adjusted-price source after the registered date filter: {len(sp):,} rows across {len(sp_tickers):,} tickers; roster-active names per session range {sp_counts.min()}–{sp_counts.max()}; names with price rows/session range {sp_price_names.min()}–{sp_price_names.max()}; active names with dated SIC2 range {sp_sic_names.min()}–{sp_sic_names.max()}.",
        f"- Dow adjusted-price sources after the registered date filter and initial-window gap overlay: {len(dow):,} rows across {len(dow_tickers):,} tickers; roster-active names/session range {dow_counts.min()}–{dow_counts.max()}; names with price rows/session range {dow_price_names.min()}–{dow_price_names.max()}; active names with dated SIC2 range {dow_sic_names.min()}–{dow_sic_names.max()}.",
        f"- SPY adjusted benchmark: {len(spy):,} daily observations; all {len(dates):,} S&P calendar sessions matched.",
        "- Point-in-time S&P roster: 623 dated intervals and 622 ticker identities; Dow roster and dated SIC2 sources are separately hash-pinned below.",
        "- Dates before 2020-11-27 were excluded by Parquet scan predicates before any price rows were materialized; no sealed-holdout file or pre-2020-11-27 Dow price value was read.", "",
        "## EDGAR event-clock input coverage", "",
        "Counts below deduplicate to the earliest BMO/AMC Item 2.02 filing per CIK/report quarter, map acceptance time to the first session open strictly after acceptance, and check only event-session and preceding-session adjusted-close availability plus PIT roster and dated SIC2. They do not inspect the 21-session forward endpoint or calculate any price change.", "",
        "### S&P 500 mechanism input availability", "",
        "| Event quarter | BMO/AMC events | BMO | AMC | ticker in panel | PIT member | SIC2 known | stock close pair | SPY close pair | all signal inputs available |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in sp_cov:
        if r["events_bmo_amc"]:
            lines.append("| {quarter} | {events_bmo_amc} | {BMO} | {AMC} | {ticker_price_panel} | {PIT_member} | {SIC2_known} | {stock_close_pair} | {SPY_close_pair} | {all_signal_inputs_available} |".format(**r))
    lines += ["", "### Dow portfolio signal input availability", "",
        "| Event quarter | BMO/AMC events | BMO | AMC | ticker in panel | PIT member | SIC2 known | stock close pair | SPY close pair | all signal inputs available |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in dow_cov:
        if r["events_bmo_amc"]:
            lines.append("| {quarter} | {events_bmo_amc} | {BMO} | {AMC} | {ticker_price_panel} | {PIT_member} | {SIC2_known} | {stock_close_pair} | {SPY_close_pair} | {all_signal_inputs_available} |".format(**r))
    lines += ["", "## Hashed files", "", "SHA-256 values are stored in `K1_INPUT_MANIFEST.json`; the input manifest includes the staged bundle, both raw point-in-time price sources, isolated SPY development series, event clock, both rosters, and both dated SIC2 sources.", ""]
    OUT_QA.write_text("\n".join(lines), encoding="utf-8")

    entries = {
        "prices": OUT_BUNDLE,
        "events": EVENTS,
        "sic": SP_SIC,
        "sp500_roster": SP_ROSTER,
        "dow_roster": DOW_ROSTER,
        "sp500_prices": SP_PRICES,
        "dow_prices": DOW_PRICES,
        "dow_gapfill": DOW_GAP,
        "spy_prices": OUT_SPY,
        "dow_sic": DOW_SIC,
        "coverage_report": OUT_QA,
    }
    manifest = {
        "schema": "K1_INPUTS_V1",
        "development_window": [START, END],
        "holdout_loaded": False,
        "forward_labels_built": False,
        "created_utc": datetime.now(tz=ZoneInfo("UTC")).isoformat(),
        "files": {k: {"path": p.relative_to(ROOT).as_posix(), "sha256": sha256(p)} for k, p in entries.items()},
        "notes": "Signal/roster/SIC/prices only. No forward outcomes or sealed holdout values. SP500/Dow/benchmark price arrays are adjusted O/C inputs; source data are filtered to the registered development window before materialization.",
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"dates={len(dates)} sp_tickers={len(sp_tickers)} sp_rows={len(sp)} dow_tickers={len(dow_tickers)} dow_rows={len(dow)} spy_rows={len(spy)}")
    print(f"SP active min/max={sp_counts.min()}/{sp_counts.max()} active SIC min/max={sp_sic_names.min()}/{sp_sic_names.max()}")
    print(f"Dow active min/max={dow_counts.min()}/{dow_counts.max()} active SIC min/max={dow_sic_names.min()}/{dow_sic_names.max()}")
    print(f"S&P eligible close-pair event inputs={sum(x['all_signal_inputs_available'] for x in sp_cov)}")
    print(f"Dow eligible close-pair event inputs={sum(x['all_signal_inputs_available'] for x in dow_cov)}")
    print(f"bundle_sha256={sha256(OUT_BUNDLE)} manifest_sha256={sha256(OUT_MANIFEST)}")


if __name__ == "__main__":
    main()
