"""Build the frozen D1 input bundle from development-only source panels.

Price rows are restricted to 2020-06-01..2026-10-30 before parsing numeric
values. Dow CSV lines are date-screened before OHLC fields are parsed.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "D1_INPUTS.npz"
START, END = "2020-06-01", "2026-10-30"


def calendar() -> np.ndarray:
    m = pd.read_csv(ROOT / "r6_data/finra_regsho/download_manifest.csv", usecols=["date"])
    d = pd.DatetimeIndex(pd.to_datetime(m["date"]).dt.normalize().drop_duplicates().sort_values())
    d = d[(d >= START) & (d <= END)]
    dates = d.strftime("%Y-%m-%d").to_numpy(dtype=str)
    if len(dates) != 1614 or dates[0] != START or dates[-1] != END:
        raise ValueError("development calendar does not match frozen 1,614-session window")
    return dates


def load_roster(path: Path, names: np.ndarray, dates: np.ndarray) -> np.ndarray:
    frame = pd.read_csv(path, dtype={"ticker": str})
    required = {"ticker", "effective_from", "effective_to_exclusive"}
    if not required.issubset(frame.columns):
        raise ValueError(f"roster schema missing {required - set(frame.columns)}")
    out = np.zeros((len(names), len(dates)), dtype=bool)
    name_ix = {name: i for i, name in enumerate(names)}
    for row in frame.itertuples(index=False):
        ticker = str(row.ticker).upper()
        if ticker not in name_ix:
            raise ValueError(f"roster ticker absent from symbol union: {ticker}")
        lo = max(START, str(row.effective_from)[:10])
        hi = min("2026-10-31", str(row.effective_to_exclusive)[:10])
        i0, i1 = np.searchsorted(dates, lo), np.searchsorted(dates, hi)
        if i1 > i0:
            out[name_ix[ticker], i0:i1] = True
    return out


def load_sic(path: Path, names: np.ndarray, dates: np.ndarray) -> np.ndarray:
    frame = pd.read_csv(path, dtype={"ticker": str, "sic2": str})
    required = {"ticker", "sic2", "effective_from", "effective_to_exclusive"}
    if not required.issubset(frame.columns):
        raise ValueError(f"SIC schema missing {required - set(frame.columns)}")
    out = np.full((len(names), len(dates)), "", dtype="<U2")
    name_ix = {name: i for i, name in enumerate(names)}
    for row in frame.itertuples(index=False):
        ticker = str(row.ticker).upper()
        if ticker not in name_ix:
            continue
        group = str(row.sic2).strip()
        if group.lower() in {"nan", "none", "0"} or not group.isdigit():
            continue
        group = group.zfill(2)[-2:]
        lo = max(START, str(row.effective_from)[:10])
        hi = min("2026-10-31", str(row.effective_to_exclusive)[:10])
        i0, i1 = np.searchsorted(dates, lo), np.searchsorted(dates, hi)
        if i1 <= i0:
            continue
        target = out[name_ix[ticker], i0:i1]
        conflict = (target != "") & (target != group)
        if conflict.any():
            raise ValueError(f"overlapping SIC2 assignments for {ticker}")
        target[target == ""] = group
    return out


def load_ratio_panel(dates: np.ndarray, name_arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    frame = pd.read_csv(
        ROOT / "r6_data/finra_regsho/signal_panel.csv.gz",
        usecols=["date", "universe", "ticker", "short_volume_ratio"],
        dtype={"universe": str, "ticker": str},
    )
    # Restrict before converting or using ratio values.
    frame["date"] = frame["date"].astype(str).str[:10]
    frame = frame.loc[frame.date.between(START, END)].copy()
    frame["ticker"] = frame["ticker"].str.upper()
    frame["short_volume_ratio"] = pd.to_numeric(frame.short_volume_ratio, errors="coerce")
    date_ix = {d: i for i, d in enumerate(dates)}
    out = {}
    for universe, key in (("SP500", "sp500"), ("DOW30", "dow")):
        names = name_arrays[key]
        name_ix = {name: i for i, name in enumerate(names)}
        mat = np.full((len(names), len(dates)), np.nan, dtype=float)
        rows = frame.loc[frame.universe.eq(universe)]
        seen = set()
        for row in rows.itertuples(index=False):
            ticker, day = row.ticker, row.date
            if ticker not in name_ix or day not in date_ix:
                continue
            key_pair = (ticker, day)
            if key_pair in seen:
                raise ValueError(f"duplicate paired FINRA ratio for {universe} {ticker} {day}")
            seen.add(key_pair)
            value = float(row.short_volume_ratio) if pd.notna(row.short_volume_ratio) else np.nan
            if np.isfinite(value) and value >= 0:
                mat[name_ix[ticker], date_ix[day]] = value
        out[key] = mat
    return out


def load_sp_prices(names: np.ndarray, dates: np.ndarray):
    path = ROOT / "r6_data/sp500_ohlcv_dev_gapfilled.parquet"
    # Metadata confirmed this parquet's date statistics span exactly the
    # allowed development boundary; the predicate is applied at scan time.
    table = pq.read_table(
        path,
        columns=["date", "ticker", "open", "close", "adj_close"],
        filters=[("date", ">=", pd.Timestamp(START)), ("date", "<=", pd.Timestamp(END))],
    )
    frame = table.to_pandas()
    frame["date"] = pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d")
    frame["ticker"] = frame["ticker"].astype(str).str.upper()
    if frame.date.min() < START or frame.date.max() > END:
        raise ValueError("S&P parquet scan returned rows outside development dates")
    return price_matrices(frame, names, dates, adjclose_col="adj_close")


def price_matrices(frame: pd.DataFrame, names: np.ndarray, dates: np.ndarray,
                   *, adjclose_col: str):
    name_ix = {name: i for i, name in enumerate(names)}
    date_ix = {day: i for i, day in enumerate(dates)}
    op = np.full((len(names), len(dates)), np.nan, dtype=float)
    close = np.full_like(op, np.nan)
    seen = set()
    for row in frame.itertuples(index=False):
        ticker, day = str(row.ticker).upper(), str(row.date)[:10]
        if ticker not in name_ix or day not in date_ix:
            continue
        key = (ticker, day)
        if key in seen:
            raise ValueError(f"duplicate OHLCV bar for {ticker} {day}")
        seen.add(key)
        raw_open, raw_close = float(row.open), float(row.close)
        adj_close = float(getattr(row, adjclose_col))
        if all(np.isfinite(x) and x > 0 for x in (raw_open, raw_close, adj_close)):
            i, j = name_ix[ticker], date_ix[day]
            op[i, j] = raw_open * adj_close / raw_close
            close[i, j] = adj_close
    return op, close


def load_dow_prices(names: np.ndarray, dates: np.ndarray):
    folders = (ROOT / "repo/prices-daily", ROOT / "repo/prices-daily-delisted")
    name_ix = {name: i for i, name in enumerate(names)}
    date_ix = {day: i for i, day in enumerate(dates)}
    op = np.full((len(names), len(dates)), np.nan, dtype=float)
    close = np.full_like(op, np.nan)
    seen = set()
    for folder in folders:
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.csv")):
            ticker = path.stem.upper()
            if ticker not in name_ix:
                continue
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                header = handle.readline().rstrip("\r\n").split(",")
                required = {"date", "open", "close", "adjclose"}
                if not required.issubset(header):
                    raise ValueError(f"unexpected Dow CSV schema: {path.name}")
                date_col = header.index("date")
                if date_col != 1:
                    raise ValueError(f"expected date as second CSV column: {path.name}")
                open_col, close_col, adj_col = (header.index(k) for k in ("open", "close", "adjclose"))
                for line in handle:
                    prefix = line.rstrip("\r\n").split(",", 2)
                    if len(prefix) < 2:
                        continue
                    day = prefix[date_col].strip().strip('"')[:10]
                    # Do not split or parse pre-boundary OHLC fields.
                    if day < START or day > END or day not in date_ix:
                        continue
                    fields = line.rstrip("\r\n").split(",")
                    if len(fields) <= max(open_col, close_col, adj_col):
                        continue
                    key = (ticker, day)
                    if key in seen:
                        raise ValueError(f"duplicate Dow OHLCV bar for {ticker} {day}")
                    seen.add(key)
                    try:
                        raw_open = float(fields[open_col])
                        raw_close = float(fields[close_col])
                        adj_close = float(fields[adj_col])
                    except ValueError:
                        continue
                    if all(np.isfinite(x) and x > 0 for x in (raw_open, raw_close, adj_close)):
                        i, j = name_ix[ticker], date_ix[day]
                        op[i, j] = raw_open * adj_close / raw_close
                        close[i, j] = adj_close
    return op, close


def main():
    dates = calendar()
    sp_roster_frame = pd.read_csv(ROOT / "r6_data/sp500_pit_roster.csv", dtype={"ticker": str})
    dw_roster_frame = pd.read_csv(Path(__file__).resolve().parent / "dow_pit_roster.csv", dtype={"ticker": str})
    names = {
        "sp500": np.array(sorted(sp_roster_frame.ticker.str.upper().unique()), dtype=str),
        "dow": np.array(sorted(dw_roster_frame.ticker.str.upper().unique()), dtype=str),
    }
    roster = {
        "sp500": load_roster(ROOT / "r6_data/sp500_pit_roster.csv", names["sp500"], dates),
        "dow": load_roster(Path(__file__).resolve().parent / "dow_pit_roster.csv", names["dow"], dates),
    }
    sic = {
        "sp500": load_sic(ROOT / "r6_C1/sp500_sic_membership.csv", names["sp500"], dates),
        "dow": load_sic(ROOT / "r6_C1/dow_sic_membership.csv", names["dow"], dates),
    }
    ratios = load_ratio_panel(dates, names)
    sp_open, sp_close = load_sp_prices(names["sp500"], dates)
    dow_open, dow_close = load_dow_prices(names["dow"], dates)
    payload = {
        "dates": dates,
        "sp500_names": names["sp500"], "dow_names": names["dow"],
        "sp500_roster": roster["sp500"], "dow_roster": roster["dow"],
        "sp500_ratio": ratios["sp500"], "dow_ratio": ratios["dow"],
        "sp500_adjusted_open": sp_open, "sp500_adjusted_close": sp_close,
        "dow_adjusted_open": dow_open, "dow_adjusted_close": dow_close,
        "sp500_sic2": sic["sp500"], "dow_sic2": sic["dow"],
    }
    np.savez_compressed(OUT, **payload)
    print(f"Wrote development-only D1 input bundle: {OUT} ({OUT.stat().st_size:,} bytes)")
    print(f"sessions={len(dates)} SP500_names={len(names['sp500'])} DOW_names={len(names['dow'])}")


if __name__ == "__main__":
    main()
