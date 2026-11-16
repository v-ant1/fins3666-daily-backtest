"""Build point-in-time monthly overnight-momentum inputs (signals only).

The formation signal is the compounded overnight return over the last 21
market sessions, ending at each calendar month-end formation date. This module
does not construct forward labels or use outcome data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
START = pd.Timestamp("2020-06-01")
FIRST_FORMATION = pd.Timestamp("2020-12-01")
LAST_FORMATION = pd.Timestamp("2026-09-30")
LOOKBACK_SESSIONS = 21


def load_dow_prices(root: Path) -> pd.DataFrame:
    """Combine development Dow CSV bars and the r6_data early-window gap fill.

    CSV sources are the existing daily and lookback price panels; all rows are
    immediately restricted to 2020-06-01 onward. WBA is read from the delisted
    price folder. The r6_data parquet adds recovered Dow bars for Nov-Dec 2020.
    """
    tickers = pd.read_csv(root / "r6_D1" / "dow_pit_roster.csv")["ticker"].unique()
    candidates = [
        root / "w1_engine" / "prices-daily-lookback",
        root / "w1_engine" / "prices-daily-delisted",
        root / "w1_engine" / "prices-daily",
    ]
    pieces: list[pd.DataFrame] = []
    for ticker in tickers:
        for folder in candidates:
            path = folder / f"{ticker}.csv"
            if not path.exists():
                continue
            # Stream past earlier rows without parsing or retaining price
            # fields before the allowed development cutoff.
            with path.open("r", newline="", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                if not {"date", "open", "close", "adjclose"}.issubset(reader.fieldnames or []):
                    continue
                kept = []
                for row in reader:
                    if (row.get("date") or "")[:10] < START.date().isoformat():
                        continue
                    kept.append({k: row[k] for k in ("date", "open", "close", "adjclose")})
            frame = pd.DataFrame(kept)
            if frame.empty:
                continue
            for col in ("open", "close", "adjclose"):
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
            frame["date"] = pd.to_datetime(frame["date"], utc=True).dt.tz_localize(None).dt.normalize()
            frame["ticker"] = ticker
            pieces.append(frame)

    if not pieces:
        raise FileNotFoundError("No Dow development OHLCV CSV rows were found")
    csv_prices = pd.concat(pieces, ignore_index=True)
    csv_prices = csv_prices.loc[csv_prices["date"].ge(START)].copy()
    csv_prices["open_adj"] = csv_prices["open"] * csv_prices["adjclose"] / csv_prices["close"]
    csv_prices["close_adj"] = csv_prices["adjclose"]
    csv_prices = csv_prices[["date", "ticker", "open_adj", "close_adj"]]

    gap = pd.read_parquet(root / "r6_data" / "dow_dev_gapfill.parquet")
    gap["date"] = pd.to_datetime(gap["date"]).dt.normalize()
    gap = gap.loc[gap["date"].ge(START)].copy()
    gap["open_adj"] = gap["open"] * gap["adj_close"] / gap["close"]
    gap["close_adj"] = gap["adj_close"]
    gap = gap[["date", "ticker", "open_adj", "close_adj"]]

    # Gap-fill rows supersede duplicate ticker/date observations where present.
    combined = pd.concat([csv_prices, gap], ignore_index=True)
    combined = combined.sort_values(["date", "ticker"]).drop_duplicates(["date", "ticker"], keep="last")
    return combined.reset_index(drop=True)


def load_sp500_prices(root: Path) -> pd.DataFrame:
    frame = pd.read_parquet(root / "r6_data" / "sp500_ohlcv_dev_gapfilled.parquet")
    frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()
    frame = frame.loc[frame["date"].ge(START)].copy()
    frame["open_adj"] = frame["open"] * frame["adj_close"] / frame["close"]
    frame["close_adj"] = frame["adj_close"]
    return frame[["date", "ticker", "open_adj", "close_adj"]]


def load_sic(root: Path, universe: str) -> pd.DataFrame:
    if universe == "SP500":
        frame = pd.read_csv(root / "r6_data" / "sp500_sic_panel.csv")
        frame["asof"] = pd.to_datetime(frame["effective_date"])
    else:
        frame = pd.read_csv(root / "r4_L4" / "data" / "sic_panel.csv")
        frame["asof"] = pd.to_datetime(frame["effective_from"])
    frame["sic"] = pd.to_numeric(frame["sic"], errors="coerce")
    frame["sic2"] = frame["sic"].floordiv(100).astype("Int64").astype("string").str.zfill(2)
    return frame[["ticker", "asof", "sic2"]].dropna(subset=["sic2"])


def membership_at(roster: pd.DataFrame, date: pd.Timestamp) -> set[str]:
    start = pd.to_datetime(roster["effective_from"])
    end = pd.to_datetime(roster["effective_to_exclusive"])
    return set(roster.loc[start.le(date) & end.gt(date), "ticker"].astype(str))


def index_sic(sic: pd.DataFrame) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Prepare per-ticker effective-date arrays for fast as-of lookups."""
    result = {}
    for ticker, group in sic.sort_values("asof").groupby("ticker", sort=False):
        result[str(ticker)] = (
            group["asof"].to_numpy(dtype="datetime64[ns]"),
            group["sic2"].astype(str).to_numpy(),
        )
    return result


def sic_at(sic_index: dict[str, tuple[np.ndarray, np.ndarray]],
           ticker: str, date: pd.Timestamp) -> str | None:
    values = sic_index.get(str(ticker))
    if values is None:
        return None
    dates, codes = values
    pos = int(np.searchsorted(dates, np.datetime64(date, "ns"), side="right")) - 1
    return str(codes[pos]) if pos >= 0 else None


def build_daily_panel(prices: pd.DataFrame, roster_path: Path, sic: pd.DataFrame,
                      universe: str) -> pd.DataFrame:
    """Materialize PIT daily open/close inputs, including explicit missing bars."""
    prices = prices.copy()
    prices["date"] = pd.to_datetime(prices["date"]).dt.normalize()
    prices = prices.loc[prices["date"].ge(START)].drop_duplicates(["date", "ticker"], keep="last")
    calendar = pd.DatetimeIndex(sorted(prices["date"].unique()))
    roster = pd.read_csv(roster_path)
    roster["effective_from"] = pd.to_datetime(roster["effective_from"])
    roster["effective_to_exclusive"] = pd.to_datetime(roster["effective_to_exclusive"])
    price_lookup = {
        (date, ticker): (op, close)
        for date, ticker, op, close in zip(
            prices["date"], prices["ticker"], prices["open_adj"], prices["close_adj"]
        )
    }
    sic_index = index_sic(sic)
    rows = []
    for date in calendar:
        names = sorted(membership_at(roster, date))
        for ticker in names:
            op, close = price_lookup.get((date, ticker), (np.nan, np.nan))
            rows.append({
                "universe": universe, "date": date, "ticker": ticker,
                "member": True, "adjusted_open": op, "adjusted_close": close,
                "sic2": sic_at(sic_index, ticker, date),
                "has_open_bar": bool(np.isfinite(op) and op > 0),
                "has_close_bar": bool(np.isfinite(close) and close > 0),
            })
    return pd.DataFrame(rows)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_formation_dates(calendar: pd.DatetimeIndex) -> list[pd.Timestamp]:
    sessions = pd.Series(calendar, index=calendar)
    by_month = sessions.groupby(sessions.index.to_period("M")).max()
    dates = [d for d in by_month.tolist() if FIRST_FORMATION <= d <= LAST_FORMATION]
    return dates


def build_universe(
    prices: pd.DataFrame,
    roster_path: Path,
    sic: pd.DataFrame,
    universe: str,
    formation_dates: list[pd.Timestamp] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    prices = prices.copy()
    prices["date"] = pd.to_datetime(prices["date"]).dt.normalize()
    prices = prices.loc[prices["date"].ge(START)]
    prices = prices.drop_duplicates(["date", "ticker"], keep="last")
    prices = prices.sort_values(["ticker", "date"])
    calendar = pd.DatetimeIndex(sorted(prices["date"].unique()))
    dates = make_formation_dates(calendar) if formation_dates is None else list(formation_dates)
    calendar_dates = set(calendar)
    absent_formations = [date for date in dates if date not in calendar_dates]
    if absent_formations:
        raise ValueError(f"{universe} price calendar is missing shared formation sessions: {absent_formations[:3]}")
    roster = pd.read_csv(roster_path)
    roster["effective_from"] = pd.to_datetime(roster["effective_from"])
    roster["effective_to_exclusive"] = pd.to_datetime(roster["effective_to_exclusive"])

    # Calculate each overnight return against the immediately preceding
    # observed market session. A missing bar on either date makes that return
    # unavailable; no carrying or interpolation is performed for signals.
    prior = pd.Series(calendar, index=calendar).shift(1)
    prior_lookup = prior.to_dict()
    close_lookup = prices.set_index(["ticker", "date"])["close_adj"]
    prices["prior_date"] = prices["date"].map(prior_lookup)
    keys = pd.MultiIndex.from_arrays([prices["ticker"], prices["prior_date"]])
    prices["prior_close_adj"] = close_lookup.reindex(keys).to_numpy()
    prices["overnight_return"] = prices["open_adj"] / prices["prior_close_adj"] - 1.0
    prices.loc[prices["date"].eq(START) | prices["prior_date"].isna(), "overnight_return"] = np.nan

    rows: list[dict] = []
    qa: list[dict] = []
    prices_by_ticker = {t: g.set_index("date") for t, g in prices.groupby("ticker", sort=False)}
    sic_index = index_sic(sic)
    for date in dates:
        members = membership_at(roster, date)
        window_dates = calendar[calendar <= date][-LOOKBACK_SESSIONS:]
        session_count = len(window_dates)
        eligible = 0
        signal_count = 0
        sic_count = 0
        price_bar_count = 0
        for ticker in sorted(members):
            group = prices_by_ticker.get(ticker)
            if group is None:
                vals = pd.Series(dtype=float)
                has_current_bar = False
            else:
                vals = group["overnight_return"].reindex(window_dates)
                has_current_bar = date in group.index and pd.notna(group.at[date, "open_adj"])
            valid_n = int(vals.notna().sum())
            valid_signal = session_count == LOOKBACK_SESSIONS and valid_n == LOOKBACK_SESSIONS
            signal = float((1.0 + vals).prod() - 1.0) if valid_signal else np.nan
            sic2 = sic_at(sic_index, ticker, date)
            has_sic = sic2 is not None
            price_bar_count += int(has_current_bar)
            signal_count += int(valid_signal)
            sic_count += int(has_sic)
            eligible += int(valid_signal and has_sic)
            rows.append({
                "universe": universe,
                "formation_date": date,
                "ticker": ticker,
                "member": True,
                "overnight_momentum_21s": signal,
                "valid_overnight_sessions": valid_n,
                "lookback_sessions_required": LOOKBACK_SESSIONS,
                "has_formation_bar": has_current_bar,
                "sic2": sic2,
                "signal_valid": bool(valid_signal),
                "sic_valid": bool(has_sic),
                "eligible": bool(valid_signal and has_sic),
            })
        qa.append({
            "universe": universe,
            "formation_date": date,
            "pit_members": len(members),
            "formation_bar_names": price_bar_count,
            "valid_21_session_signals": signal_count,
            "sic2_names": sic_count,
            "eligible_signal_and_sic2_names": eligible,
            "eligible_member_coverage": eligible / len(members) if members else np.nan,
            "gate_250_names": signal_count >= 250,
            "formation_session_count": session_count,
        })
    return pd.DataFrame(rows), pd.DataFrame(qa)


def build(root: Path = ROOT, out: Path = OUT) -> tuple[pd.DataFrame, pd.DataFrame]:
    out.mkdir(parents=True, exist_ok=True)
    dow_prices = load_dow_prices(root)
    sp_prices = load_sp500_prices(root)
    sp_sic = load_sic(root, "SP500")
    dow_sic = load_sic(root, "DOW")
    # P1 fixes its formation calendar from the Dow development sessions and
    # requires the S&P mechanism to use exactly those same month-end dates.
    shared_formations = make_formation_dates(pd.DatetimeIndex(sorted(dow_prices["date"].unique())))
    sp = build_universe(
        sp_prices, root / "r6_data" / "sp500_pit_roster.csv", sp_sic, "SP500", shared_formations,
    )
    dow = build_universe(
        dow_prices, root / "r6_D1" / "dow_pit_roster.csv", dow_sic, "DOW", shared_formations,
    )
    bundle = pd.concat([sp[0], dow[0]], ignore_index=True)
    coverage = pd.concat([sp[1], dow[1]], ignore_index=True)
    bundle["formation_date"] = pd.to_datetime(bundle["formation_date"])
    coverage["formation_date"] = pd.to_datetime(coverage["formation_date"])
    bundle.to_parquet(out / "P1_signal_inputs.parquet", index=False)
    coverage.to_csv(out / "coverage_by_formation.csv", index=False, date_format="%Y-%m-%d")
    daily = pd.concat([
        build_daily_panel(sp_prices, root / "r6_data" / "sp500_pit_roster.csv", sp_sic, "SP500"),
        build_daily_panel(dow_prices, root / "r6_D1" / "dow_pit_roster.csv", dow_sic, "DOW"),
    ], ignore_index=True)
    daily.to_parquet(out / "P1_daily_prices.parquet", index=False)
    manifest = {
        "scope": "input-only adjusted daily bars and trailing signals; no forward labels or outcomes",
        "development_window": ["2020-06-01", "2026-10-30"],
        "formation_window": [shared_formations[0].strftime("%Y-%m"), shared_formations[-1].strftime("%Y-%m")],
        "formation_count": int(coverage.formation_date.nunique()),
        "universe_formation_rows": {k: int(v) for k, v in coverage.groupby("universe").size().items()},
        "signal_bundle": {"path": "P1_signal_inputs.parquet", "sha256": _sha256(out / "P1_signal_inputs.parquet")},
        "daily_price_bundle": {"path": "P1_daily_prices.parquet", "sha256": _sha256(out / "P1_daily_prices.parquet")},
        "coverage_table": {"path": "coverage_by_formation.csv", "sha256": _sha256(out / "coverage_by_formation.csv")},
        "forward_labels_built": False,
        "holdout_loaded": False,
    }
    (out / "INPUT_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_qa(coverage, bundle, out / "INPUT_QA.md")
    return bundle, coverage


def write_qa(coverage: pd.DataFrame, bundle: pd.DataFrame, path: Path) -> None:
    lines = [
        "# P1 trailing overnight-momentum input QA",
        "",
        "This is an input-only signal build. It contains no forward returns, ICs, mechanism test, or portfolio outcomes.",
        "",
        "## Fixed construction",
        "",
        "At each calendar month-end, the formation date is the final observed market session in that month. The signal is the compounded overnight return over the 21 observed market sessions ending on formation: `product(open_adj[t] / close_adj[t-1]) - 1`. Adjusted open is reconstructed as raw open × adjusted close / raw close. The input history is clipped at 2020-06-01; a signal is valid only when all 21 overnight observations and their adjacent-session price bars are present. No missing observations are carried or interpolated.",
        "",
        "## Coverage by formation",
        "",
        "`coverage_by_formation.csv` reports PIT membership, current formation-date bars, valid 21-session signals, dated SIC2 labels, and joint eligible names. The 250-name gate is based on PIT members with a valid signal; SIC2 availability and joint signal-plus-SIC2 coverage are reported separately. The Dow's 30-name universe is descriptive and is not expected to meet the S&P-scale threshold.",
        "",
        "| Universe | Formation dates | Min PIT members | Min formation bars | Min valid signals | Min joint signal + SIC2 | Dates ≥250 valid signals | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for universe, group in coverage.groupby("universe", sort=True):
        gate_dates = int(group["gate_250_names"].sum())
        lines.append(
            f"| {universe} | {len(group)} | {int(group.pit_members.min())} | {int(group.formation_bar_names.min())} | "
            f"{int(group.valid_21_session_signals.min())} | {int(group.eligible_signal_and_sic2_names.min())} | {gate_dates}/{len(group)} | "
            f"{'PASS' if universe == 'SP500' and gate_dates == len(group) else ('FAIL' if universe == 'SP500' else 'N/A')} |"
        )
    lines.extend([
        "",
        "## Inputs and limitations",
        "",
        "S&P 500 bars come from `r6_data/sp500_ohlcv_dev_gapfilled.parquet`; the dated constituent intervals are from `r6_data/sp500_pit_roster.csv`. Dow bars are combined from the existing daily/lookback files and `r6_data/dow_dev_gapfill.parquet`; the Dow PIT roster is `r6_D1/dow_pit_roster.csv`. SIC2 is assigned from the latest SEC SIC-panel effective date not after formation (`r6_data/sp500_sic_panel.csv` for S&P 500; `r4_L4/data/sic_panel.csv` for Dow). Historical SIC metadata can predate June 2020 because it establishes the contemporaneous classification at the cutoff; it is not price, return, or outcome data. Price records before 2020-06-01 are discarded before parsing, and no pre-cutoff prices enter return construction.",
        "",
        f"The output has {len(bundle):,} PIT member-formation rows across {coverage.formation_date.nunique()} month-end dates and both universes. The signal parquet is long-form and retains explicit member, bar, signal, SIC2, and eligibility masks for auditability.",
        "",
        "## Rebuild",
        "",
        "Run `python r6_P1/build_inputs.py` from the project root.",
        "The hashed input-only manifest is `INPUT_MANIFEST.json`; it pins the signal bundle, daily price bundle, and per-formation coverage table before the guarded runner may construct forward labels.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    build(args.root, args.out)


if __name__ == "__main__":
    main()
