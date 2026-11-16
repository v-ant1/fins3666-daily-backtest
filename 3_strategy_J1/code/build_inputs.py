"""Build J1 trailing-return/SIC2 peer features from development inputs only.

No forward returns are computed. All price rows are restricted to dates on or
after 2020-06-01 before any return features are formed.
"""
from __future__ import annotations

import json
from bisect import bisect_right
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "r6_J1"
DATA = ROOT / "r6_data"
START = pd.Timestamp("2020-06-01")
FIRST_FORMATION = pd.Timestamp("2020-11-27")
LAST_DATE = pd.Timestamp("2026-10-30")
MIN_SP500_GATE = 250


def read_price(path: Path, *, ticker_col: str = "ticker") -> pd.DataFrame:
    df = pd.read_parquet(path, columns=["date", ticker_col, "adj_close"])
    df = df.rename(columns={ticker_col: "ticker"})
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df = df.loc[(df.date >= START) & (df.date <= LAST_DATE), ["date", "ticker", "adj_close"]]
    if (df.date < START).any():
        raise ValueError(f"pre-2020-06 prices found in {path}")
    if df.duplicated(["date", "ticker"]).any():
        raise ValueError(f"duplicate date/ticker rows in {path}")
    return df


def build_sic_lookup(path: Path) -> dict[str, tuple[list[pd.Timestamp], list[str]]]:
    sic = pd.read_csv(path, dtype={"ticker": str, "sic": str}, keep_default_na=False)
    sic["effective_date"] = pd.to_datetime(sic["effective_date"], errors="coerce")
    sic = sic.loc[(sic.effective_date >= START) & (sic.effective_date <= LAST_DATE)].copy()
    sic["sic2"] = sic["sic"].str.extract(r"^(\d{2})", expand=False)
    sic = sic.dropna(subset=["effective_date", "sic2"]).sort_values(["ticker", "effective_date"])
    result = {}
    for ticker, rows in sic.groupby("ticker", sort=False):
        rows = rows.drop_duplicates("effective_date", keep="last")
        result[str(ticker)] = (rows.effective_date.tolist(), rows.sic2.astype(str).tolist())
    return result


def sic_asof(lookup, ticker: str, date: pd.Timestamp) -> str | None:
    item = lookup.get(ticker)
    if item is None:
        return None
    dates, values = item
    ix = bisect_right(dates, date) - 1
    return values[ix] if ix >= 0 else None


def load_roster(path: Path) -> pd.DataFrame:
    r = pd.read_csv(path, dtype=str)
    r["effective_from"] = pd.to_datetime(r["effective_from"])
    r["effective_to_exclusive"] = pd.to_datetime(r["effective_to_exclusive"])
    return r


def make_universe(universe: str, prices: pd.DataFrame, roster: pd.DataFrame,
                  formations: list[pd.Timestamp], sic_lookup,
                  all_sessions: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Build adjusted-close lookup from development dates only.
    close = prices.pivot(index="ticker", columns="date", values="adj_close")
    close = close.reindex(columns=all_sessions)
    # Five session returns need the formation close and the close five sessions
    # earlier; all six observations are required so gaps are never bridged.
    r5 = pd.DataFrame(np.nan, index=close.index, columns=all_sessions)
    valid5 = pd.DataFrame(False, index=close.index, columns=all_sessions)
    for j in range(5, len(all_sessions)):
        w = close.iloc[:, j - 5:j + 1]
        ok = np.isfinite(w.to_numpy()).all(axis=1) & (w.to_numpy() > 0).all(axis=1)
        end = close.iloc[:, j].to_numpy(dtype=float)
        start = close.iloc[:, j - 5].to_numpy(dtype=float)
        vals = np.full(len(close), np.nan)
        vals[ok] = end[ok] / start[ok] - 1.0
        r5.iloc[:, j] = vals
        valid5.iloc[:, j] = ok

    records = []
    coverage = []
    r_by = roster
    for date in formations:
        active = r_by.loc[(r_by.effective_from <= date) & (date < r_by.effective_to_exclusive), "ticker"].astype(str).tolist()
        own = r5[date].reindex(active)
        own_ok = own.notna()
        sic2 = {ticker: sic_asof(sic_lookup, ticker, date) for ticker in active}
        valid_group_values: dict[str, list[float]] = {}
        for ticker in active:
            group = sic2[ticker]
            if group is not None and bool(own_ok.get(ticker, False)):
                valid_group_values.setdefault(group, []).append(float(own[ticker]))

        own_n = int(own_ok.sum())
        sic_n = sum(s is not None for s in sic2.values())
        peer_n = relative_n = 0
        for ticker in active:
            group = sic2[ticker]
            own_valid = bool(own_ok.get(ticker, False))
            vals = valid_group_values.get(group, []) if group is not None else []
            n_valid_group = len(vals)
            n_others = n_valid_group - int(own_valid)
            peer_count = max(0, n_others)
            peer_valid = peer_count > 0
            peer_mean = np.nan
            if peer_valid:
                peer_mean = (sum(vals) - (float(own[ticker]) if own_valid else 0.0)) / peer_count
                peer_n += 1
            own_value = float(own[ticker]) if own_valid else np.nan
            relative_valid = own_valid and peer_valid
            relative = own_value - peer_mean if relative_valid else np.nan
            relative_n += int(relative_valid)
            records.append({
                "universe": universe,
                "formation_date": date,
                "ticker": ticker,
                "sic2": group,
                "trailing_5session_total_return": own_value,
                "own_return_mask": own_valid,
                "peer_count": peer_count,
                "peer_mean_return": peer_mean,
                "peer_return_mask": peer_valid,
                "relative_return": relative,
                "relative_return_mask": relative_valid,
            })
        coverage.append({
            "universe": universe,
            "formation_date": date,
            "pit_members": len(active),
            "own_return_names": own_n,
            "sic2_names": sic_n,
            "peer_return_names": peer_n,
            "relative_return_names": relative_n,
            "sp500_250_name_gate": (relative_n >= MIN_SP500_GATE) if universe == "sp500" else pd.NA,
        })
    return pd.DataFrame.from_records(records), pd.DataFrame.from_records(coverage)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    sp_prices = read_price(DATA / "sp500_ohlcv_dev_gapfilled.parquet")
    dow_gap = read_price(DATA / "dow_dev_gapfill.parquet")
    # C1's Dow component parquet is development-only (starts 2020-11-27) and
    # supplies the base adjusted closes after the explicit r6_data gap-fill.
    dow_base = pd.read_parquet(ROOT / "r6_C1" / "dow_components_dev.parquet",
                               columns=["date", "ticker", "adj_close"])
    dow_base["date"] = pd.to_datetime(dow_base.date).dt.normalize()
    dow_base = dow_base.loc[(dow_base.date >= FIRST_FORMATION) & (dow_base.date <= LAST_DATE)]
    dow_base = dow_base[["date", "ticker", "adj_close"]]
    dow_prices = pd.concat([dow_base, dow_gap], ignore_index=True)
    # The gap-fill deliberately excludes the already-present WBA observations;
    # fail loudly if any unexpected duplicate remains.
    if dow_prices.duplicated(["date", "ticker"]).any():
        dup = dow_prices.loc[dow_prices.duplicated(["date", "ticker"], keep=False), ["date", "ticker"]]
        raise ValueError(f"duplicate Dow base/gap-fill rows: {dup.head().to_dict('records')}")

    if sp_prices.date.min() < START or dow_prices.date.min() < START:
        raise ValueError("source has prices before 2020-06-01")
    if dow_prices.date.min() < FIRST_FORMATION:
        raise ValueError("Dow source predates the approved formation window")

    # S&P's staged daily file supplies the common NYSE session calendar.
    all_sessions = pd.DatetimeIndex(sorted(sp_prices.loc[sp_prices.date >= START, "date"].unique()))
    form_ix = np.flatnonzero((all_sessions >= FIRST_FORMATION) & (all_sessions <= LAST_DATE))[::5]
    formations = list(all_sessions[form_ix])
    if not formations or formations[0] != FIRST_FORMATION:
        raise ValueError("formation calendar must begin on 2020-11-27")

    sic_lookup = build_sic_lookup(DATA / "sp500_sic_panel.csv")
    sp_roster = load_roster(DATA / "sp500_pit_roster.csv")
    dow_roster = load_roster(ROOT / "r6_D1" / "dow_pit_roster.csv")

    sp_panel, sp_cov = make_universe("sp500", sp_prices, sp_roster, formations, sic_lookup, all_sessions)
    dow_panel, dow_cov = make_universe("dow", dow_prices, dow_roster, formations, sic_lookup, all_sessions)
    panel = pd.concat([sp_panel, dow_panel], ignore_index=True)
    coverage = pd.concat([sp_cov, dow_cov], ignore_index=True)
    panel.to_parquet(OUT / "signal_bundle.parquet", index=False)
    coverage.to_csv(OUT / "formation_coverage.csv", index=False)

    sp = coverage.loc[coverage.universe == "sp500"]
    dow = coverage.loc[coverage.universe == "dow"]
    manifest = {
        "scope": "trailing signal inputs only; no forward returns or outcomes",
        "price_boundary": {"start": "2020-06-01", "end": "2026-10-30"},
        "formation_rule": "every fifth S&P development session beginning 2020-11-27",
        "formation_count": len(formations),
        "trailing_total_return": "adjusted_close[t] / adjusted_close[t-5] - 1; all six consecutive session prices required",
        "peer_definition": "leave-one-out equal-weight mean of valid trailing returns among active same-SIC2 PIT constituents",
        "sic_timing": "latest SIC observation effective on or before formation date, restricted to effective dates >= 2020-06-01",
        "sp500": {
            "formation_dates_ge_250_relative_names": int(sp.sp500_250_name_gate.fillna(False).sum()),
            "formation_dates": int(len(sp)),
            "minimum_relative_names": int(sp.relative_return_names.min()),
            "median_relative_names": float(sp.relative_return_names.median()),
            "minimum_own_return_names": int(sp.own_return_names.min()),
            "minimum_pit_members": int(sp.pit_members.min()),
        },
        "dow": {
            "formation_dates": int(len(dow)),
            "minimum_relative_names": int(dow.relative_return_names.min()),
            "median_relative_names": float(dow.relative_return_names.median()),
            "minimum_own_return_names": int(dow.own_return_names.min()),
            "minimum_pit_members": int(dow.pit_members.min()),
            "250_name_gate": "not applicable to a 30-name universe",
        },
        "input_files": [
            "r6_data/sp500_ohlcv_dev_gapfilled.parquet",
            "r6_data/sp500_pit_roster.csv",
            "r6_data/sp500_sic_panel.csv",
            "r6_data/dow_dev_gapfill.parquet",
            "r6_C1/dow_components_dev.parquet (development-only base Dow closes)",
            "r6_D1/dow_pit_roster.csv",
        ],
        "outputs": ["signal_bundle.parquet", "formation_coverage.csv"],
    }
    (OUT / "build_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
