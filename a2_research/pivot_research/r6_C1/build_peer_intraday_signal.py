"""Build final C1 SIC3 peer intraday-return signals from development inputs only.

No forward returns, outcomes, or ICs are loaded or calculated. For each date,
compound each asset's adjusted open-to-close returns over the latest five
trading sessions, then average the valid SIC3 peer values excluding the target.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
START, END = pd.Timestamp("2020-11-27"), pd.Timestamp("2026-10-30")
MIN_VALID_PEERS = 2


def build_universe(label: str, components_path: Path, membership_path: Path):
    comp = pd.read_parquet(components_path, columns=["date", "ticker", "intraday_return"])
    comp["date"] = pd.to_datetime(comp.date).dt.normalize()
    comp["ticker"] = comp.ticker.astype(str).str.upper()
    comp["intraday_return"] = pd.to_numeric(comp.intraday_return, errors="coerce")
    comp = comp.loc[comp.date.between(START, END)].sort_values(["ticker", "date"])
    cal = pd.DatetimeIndex(sorted(comp.date.unique()))
    if len(cal) == 0:
        raise ValueError(f"{label}: no development dates")
    # Match by trading-session row. A missing daily return invalidates the full window.
    wide = comp.pivot(index="date", columns="ticker", values="intraday_return").reindex(cal)
    trailing = (1.0 + wide).rolling(5, min_periods=5).apply(np.prod, raw=True) - 1.0
    trailing = trailing.where(np.isfinite(trailing))

    mem = pd.read_csv(membership_path, dtype={"ticker": str, "sic3": str})
    mem["ticker"] = mem.ticker.astype(str).str.upper()
    mem["sic3"] = mem.sic3.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(3)
    mem["effective_from"] = pd.to_datetime(mem.effective_from).dt.normalize()
    mem["effective_to_exclusive"] = pd.to_datetime(mem.effective_to_exclusive).dt.normalize()
    mem = mem.loc[mem.effective_to_exclusive.gt(START) & mem.effective_from.le(END)]

    rows = []
    for date in cal:
        active = mem.loc[mem.effective_from.le(date) & mem.effective_to_exclusive.gt(date), ["ticker", "sic3"]]
        if active.ticker.duplicated().any():
            raise ValueError(f"{label}: duplicate active SIC3 records on {date.date()}")
        vals = trailing.loc[date]
        active = active.copy()
        active["own"] = active.ticker.map(vals)
        valid = active.loc[active.own.notna() & active.sic3.str.fullmatch(r"\d{3}")].copy()
        valid["group_sum"] = valid.groupby("sic3").own.transform("sum")
        valid["group_n"] = valid.groupby("sic3").own.transform("size")
        valid["peer_n"] = valid.group_n - 1
        valid["peer_signal"] = ((valid.group_sum - valid.own) / valid.peer_n.replace(0, np.nan))
        valid.loc[valid.peer_n < MIN_VALID_PEERS, "peer_signal"] = np.nan
        result = active.merge(valid[["ticker", "peer_n", "peer_signal"]], on="ticker", how="left", validate="one_to_one")
        result["peer_n"] = result.peer_n.fillna(0).astype(int)
        for r in result.itertuples(index=False):
            rows.append((date, r.ticker, r.sic3, r.own, r.peer_n, r.peer_signal))
    panel = pd.DataFrame(rows, columns=["date", "ticker", "sic3", "trailing5_intraday_return",
                                        "valid_sic3_peer_count", "peer_intraday_signal"])
    panel["roster_active"] = True
    panel["own_trailing5_available"] = panel.trailing5_intraday_return.notna()
    panel["signal_available"] = panel.peer_intraday_signal.notna()

    by_date = panel.groupby("date", as_index=False).agg(
        roster_names=("ticker", "nunique"),
        sic3_mapped_names=("sic3", lambda x: int(x.astype(str).str.fullmatch(r"\d{3}").sum())),
        names_with_own_5d_return=("own_trailing5_available", "sum"),
        names_with_valid_peer_signal=("signal_available", "sum"),
        median_valid_peer_count=("valid_sic3_peer_count", "median"),
        max_valid_peer_count=("valid_sic3_peer_count", "max"),
    )
    by_date.insert(0, "universe", label)
    denom = by_date.roster_names.replace(0, np.nan)
    by_date["signal_coverage_fraction"] = by_date.names_with_valid_peer_signal / denom

    by_ticker = panel.groupby("ticker", as_index=False).agg(
        component_panel_dates=("date", "nunique"),
        dates_sic3_mapped=("sic3", lambda x: int(x.astype(str).str.fullmatch(r"\d{3}").sum())),
        dates_own_5d_available=("own_trailing5_available", "sum"),
        dates_with_peer_signal=("signal_available", "sum"),
        median_valid_peer_count=("valid_sic3_peer_count", "median"),
        maximum_valid_peer_count=("valid_sic3_peer_count", "max"),
    )
    by_ticker.insert(0, "universe", label)
    by_ticker["signal_coverage_fraction"] = by_ticker.dates_with_peer_signal / by_ticker.component_panel_dates

    # The preregistered schedule is every fifth US trading session, after a complete
    # five-session signal window. This is input-only; no forward-window checks occur.
    weekly_dates = cal[4::5]
    weekly = panel.loc[panel.date.isin(weekly_dates)]
    weekly_stats = {
        "weekly_formation_dates": int(len(weekly_dates)),
        "weekly_dates_with_at_least_250_peer_scores": int((weekly.groupby("date").signal_available.sum() >= 250).sum()),
        "weekly_median_names_with_peer_score": float(weekly.groupby("date").signal_available.sum().median()),
        "weekly_min_names_with_peer_score": int(weekly.groupby("date").signal_available.sum().min()),
        "weekly_median_valid_peer_count": float(weekly.loc[weekly.signal_available, "valid_sic3_peer_count"].median()) if weekly.signal_available.any() else 0.0,
    }
    return panel, by_date, by_ticker, weekly_stats, cal


def main():
    configs = [
        ("S&P 500", OUT / "sp500_components_dev.parquet", OUT / "sp500_sic_membership.csv"),
        ("Dow 30", OUT / "dow_components_dev.parquet", OUT / "dow_sic_membership.csv"),
    ]
    panels, dates, tickers, summaries = [], [], [], {}
    calendars = {}
    for label, cp, mp in configs:
        panel, date_cov, ticker_cov, stats, cal = build_universe(label, cp, mp)
        panel.insert(0, "universe", label)
        panels.append(panel)
        dates.append(date_cov)
        tickers.append(ticker_cov)
        summaries[label] = {**stats,
            "development_dates": len(cal), "first_date": str(cal.min().date()), "last_date": str(cal.max().date()),
            "median_daily_roster": float(date_cov.roster_names.median()),
        "median_daily_peer_scores": float(date_cov.names_with_valid_peer_signal.median()),
        "min_daily_peer_scores": int(date_cov.names_with_valid_peer_signal.min()),
            "median_daily_peer_count_for_scored_names": float(panel.loc[panel.signal_available, "valid_sic3_peer_count"].median()) if panel.signal_available.any() else 0.0,
        }
        calendars[label] = cal
    all_panel = pd.concat(panels, ignore_index=True)
    all_dates = pd.concat(dates, ignore_index=True)
    all_tickers = pd.concat(tickers, ignore_index=True)
    all_panel.to_parquet(OUT / "peer_intraday_signal_dev.parquet", index=False)
    all_dates.to_csv(OUT / "peer_signal_coverage_by_date.csv", index=False)
    all_tickers.to_csv(OUT / "peer_signal_coverage_by_ticker.csv", index=False)
    manifest = {"development_only": True, "forward_returns_loaded": False, "outcomes_loaded": False,
                "ics_computed": False, "start": str(START.date()), "end": str(END.date()),
                "signal": "leave-one-out mean of peer adjusted open-to-close returns compounded over the trailing five trading sessions, among active point-in-time SIC3 peers",
                "minimum_valid_peers": MIN_VALID_PEERS, "point_in_time_rule": "use SIC3 intervals active on signal date; existing membership intervals become usable on the next trading session after SEC filing date",
                "weekly_schedule": "every fifth trading session starting after the first complete five-session signal window",
                "universes": summaries}
    (OUT / "peer_signal_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
