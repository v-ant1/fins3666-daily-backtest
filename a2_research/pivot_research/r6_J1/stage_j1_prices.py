"""Stage development-only point-in-time daily prices for the J1 runner.

Reads price rows only with date filters that begin on 2020-06-01. It computes
adjusted open/close input matrices and PIT roster/SIC2 masks only; it does not
form signals, forward returns, ICs, or portfolio outcomes.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(__file__).resolve().parent
DATA = ROOT / "r6_data"
START = pd.Timestamp("2020-06-01")
END_EXCLUSIVE = pd.Timestamp("2026-10-31")
END_DATE = "2026-10-30"


def _read_filtered(path: Path, columns: list[str]) -> pd.DataFrame:
    df = pd.read_parquet(path, columns=columns,
                         filters=[("date", ">=", START), ("date", "<", END_EXCLUSIVE)])
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    # Fail closed if source partition filtering did not honor the sealed boundary.
    if len(df) and (df["date"].min() < START or df["date"].max() > pd.Timestamp(END_DATE)):
        raise ValueError(f"out-of-window row returned from {path}")
    if df.duplicated(["date", "ticker"]).any():
        raise ValueError(f"duplicate date/ticker rows in {path}")
    df["ticker"] = df["ticker"].astype(str)
    return df


def _adjusted_open(raw_open, raw_close, adj_close):
    o = np.asarray(raw_open, float)
    c = np.asarray(raw_close, float)
    a = np.asarray(adj_close, float)
    good = np.isfinite(o) & (o > 0) & np.isfinite(c) & (c > 0) & np.isfinite(a) & (a > 0)
    out = np.full(o.shape, np.nan, float)
    out[good] = o[good] * a[good] / c[good]
    return out


def _roster(path: Path, assets: np.ndarray, dates: pd.DatetimeIndex) -> np.ndarray:
    roster = pd.read_csv(path, dtype={"ticker": str})
    roster["effective_from"] = pd.to_datetime(roster["effective_from"])
    roster["effective_to_exclusive"] = pd.to_datetime(roster["effective_to_exclusive"])
    roster = roster.loc[(roster.effective_from < END_EXCLUSIVE) &
                        (roster.effective_to_exclusive > START)]
    asset_ix = {name: i for i, name in enumerate(assets.tolist())}
    mask = np.zeros((len(assets), len(dates)), dtype=bool)
    date_values = dates.to_numpy(dtype="datetime64[ns]")
    for row in roster.itertuples(index=False):
        i = asset_ix.get(str(row.ticker))
        if i is None:
            raise ValueError(f"PIT roster ticker missing from assets: {row.ticker}")
        left = np.datetime64(row.effective_from, "ns")
        right = np.datetime64(row.effective_to_exclusive, "ns")
        mask[i] |= (date_values >= left) & (date_values < right)
    return mask


def _sic2_panel(path: Path, assets: np.ndarray, dates: pd.DatetimeIndex) -> np.ndarray:
    sic = pd.read_csv(path, dtype={"ticker": str, "sic": str}, keep_default_na=False)
    sic["effective_date"] = pd.to_datetime(sic["effective_date"], errors="coerce")
    sic = sic.loc[(sic.effective_date >= START) & (sic.effective_date <= pd.Timestamp(END_DATE))].copy()
    sic["sic2"] = sic["sic"].str.extract(r"^(\d{2})", expand=False)
    sic = sic.dropna(subset=["effective_date", "sic2"]).sort_values(["ticker", "effective_date"])
    out = np.full((len(assets), len(dates)), "", dtype="<U2")
    date_values = dates.to_numpy(dtype="datetime64[ns]")
    for i, asset in enumerate(assets):
        rows = sic.loc[sic.ticker == asset]
        if rows.empty:
            continue
        eff = rows.effective_date.to_numpy(dtype="datetime64[ns]")
        codes = rows.sic2.astype(str).to_numpy(dtype="<U2")
        ix = np.searchsorted(eff, date_values, side="right") - 1
        valid = ix >= 0
        out[i, valid] = codes[ix[valid]]
    return out


def _pivot(prices: pd.DataFrame, assets: np.ndarray, dates: pd.DatetimeIndex):
    close = prices.pivot(index="ticker", columns="date", values="adj_close")
    op = prices.pivot(index="ticker", columns="date", values="adj_open")
    close = close.reindex(index=assets, columns=dates).to_numpy(dtype=float)
    op = op.reindex(index=assets, columns=dates).to_numpy(dtype=float)
    return op, close


def _load_sp500():
    p = _read_filtered(DATA / "sp500_ohlcv_dev_gapfilled.parquet",
                       ["date", "ticker", "open", "close", "adj_close"])
    p["adj_open"] = _adjusted_open(p.open, p.close, p.adj_close)
    return p[["date", "ticker", "adj_open", "adj_close"]]


def _load_dow():
    # The base series is already adjusted and is restricted to the approved
    # development era at the Parquet reader. Missing early Dow history is
    # completed from the r6_data raw-OHLCV gap-fill source.
    base = pd.read_parquet(ROOT / "r6_C1" / "dow_components_dev.parquet",
                           columns=["date", "ticker", "adj_open", "adj_close"],
                           filters=[("date", ">=", START), ("date", "<", END_EXCLUSIVE)])
    base["date"] = pd.to_datetime(base["date"]).dt.normalize()
    base["ticker"] = base["ticker"].astype(str)
    if len(base) and base.date.min() < START:
        raise ValueError("Dow base included data before 2020-06-01")
    gap = _read_filtered(DATA / "dow_dev_gapfill.parquet",
                         ["date", "ticker", "open", "close", "adj_close"])
    gap["adj_open"] = _adjusted_open(gap.open, gap.close, gap.adj_close)
    gap = gap[["date", "ticker", "adj_open", "adj_close"]]
    combined = pd.concat([base, gap], ignore_index=True)
    if combined.duplicated(["date", "ticker"]).any():
        raise ValueError("Dow base and gap-fill overlap; refuse to choose a price silently")
    combined = combined.loc[(combined.date >= START) & (combined.date <= pd.Timestamp(END_DATE))]
    return combined


def _universe(prices: pd.DataFrame, roster_path: Path, dates: pd.DatetimeIndex, sic_path: Path):
    roster = pd.read_csv(roster_path, dtype={"ticker": str})
    roster["effective_from"] = pd.to_datetime(roster.effective_from)
    roster["effective_to_exclusive"] = pd.to_datetime(roster.effective_to_exclusive)
    roster = roster.loc[(roster.effective_from < END_EXCLUSIVE) &
                        (roster.effective_to_exclusive > START)]
    assets = np.asarray(sorted(roster.ticker.astype(str).unique()), dtype=str)
    op, close = _pivot(prices, assets, dates)
    return {
        "assets": assets,
        "roster": _roster(roster_path, assets, dates),
        "sic2": _sic2_panel(sic_path, assets, dates),
        "adjusted_open": op,
        "adjusted_close": close,
    }


def main() -> None:
    sp_prices = _load_sp500()
    dates = pd.DatetimeIndex(sorted(sp_prices.date.unique()))
    if dates[0] != START or dates[-1] != pd.Timestamp(END_DATE):
        raise ValueError(f"unexpected S&P date span: {dates[0]} .. {dates[-1]}")
    sp = _universe(sp_prices, DATA / "sp500_pit_roster.csv", dates, DATA / "sp500_sic_panel.csv")
    dow_prices = _load_dow()
    dow = _universe(dow_prices, ROOT / "r6_D1" / "dow_pit_roster.csv", dates,
                    DATA / "sp500_sic_panel.csv")

    payload = {}
    for name, d, x in (("sp500", dates, sp), ("dow", dates, dow)):
        payload[f"{name}_dates"] = d.strftime("%Y-%m-%d").to_numpy(dtype=str)
        for key in ("assets", "roster", "sic2", "adjusted_open", "adjusted_close"):
            payload[f"{name}_{key}"] = x[key]

    out = OUT_DIR / "J1_PRICES_DEV.npz"
    np.savez_compressed(out, **payload)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    manifest = {
        "output": out.name,
        "sha256": digest,
        "development_window": [str(START.date()), END_DATE],
        "sessions": len(dates),
        "sp500_assets": len(sp["assets"]),
        "sp500_pit_member_days": int(sp["roster"].sum()),
        "sp500_assets_with_any_prices": int(np.isfinite(sp["adjusted_close"]).any(axis=1).sum()),
        "dow_assets": len(dow["assets"]),
        "dow_pit_member_days": int(dow["roster"].sum()),
        "dow_assets_with_any_prices": int(np.isfinite(dow["adjusted_close"]).any(axis=1).sum()),
        "source_files": [
            "r6_data/sp500_ohlcv_dev_gapfilled.parquet",
            "r6_data/sp500_pit_roster.csv",
            "r6_data/sp500_sic_panel.csv",
            "r6_C1/dow_components_dev.parquet",
            "r6_data/dow_dev_gapfill.parquet",
            "r6_D1/dow_pit_roster.csv",
        ],
        "construction": "adjusted_open = raw_open * adj_close / raw_close; adjusted close from adj_close; missing bars are NaN; no returns or outcomes computed",
    }
    (OUT_DIR / "J1_PRICES_DEV_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
