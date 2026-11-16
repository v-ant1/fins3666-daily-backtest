"""Build input-only, development-window R1 bundle; never computes returns."""
from __future__ import annotations

import hashlib
import json
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
START, END = pd.Timestamp("2020-06-01"), pd.Timestamp("2026-10-30")
FIRST_FORM, LAST_FORM = pd.Timestamp("2021-06-01"), pd.Timestamp("2026-09-30")


def month_add_clamped(day: pd.Timestamp, months: int) -> pd.Timestamp:
    return day + pd.DateOffset(months=months)


def recurrence_signal(events: pd.Series, formation: pd.Timestamp) -> int:
    """Return count of prior-year 3/6/9/12-month projections into next month."""
    lo = formation - pd.DateOffset(months=12)
    next_month = formation + pd.offsets.MonthEnd(0) + pd.Timedelta(days=1)
    after_next = next_month + pd.offsets.MonthEnd(0) + pd.Timedelta(days=1)
    count = 0
    for event in pd.to_datetime(events).dropna():
        event = pd.Timestamp(event).normalize()
        if not (lo <= event < formation):
            continue
        for offset in (3, 6, 9, 12):
            projected = month_add_clamped(event, offset)
            if next_month <= projected < after_next:
                count += 1
    return count


def load_roster(path: Path) -> pd.DataFrame:
    r = pd.read_csv(path, dtype=str)
    r["effective_from"] = pd.to_datetime(r.effective_from).dt.normalize()
    r["effective_to_exclusive"] = pd.to_datetime(r.effective_to_exclusive).dt.normalize()
    return r


def build_sic(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path, dtype={"ticker": str, "sic": str})
    d["effective_date"] = pd.to_datetime(d.effective_date, errors="coerce").dt.normalize()
    d = d.loc[d.effective_date.between(START, END)].copy()
    d["sic2"] = d.sic.str.extract(r"^(\d{2})", expand=False)
    return d.dropna(subset=["ticker", "effective_date", "sic2"])


def make_sic_lookup(sic: pd.DataFrame):
    out = {}
    for ticker, rows in sic.sort_values("effective_date").groupby("ticker", sort=False):
        rows = rows.drop_duplicates("effective_date", keep="last")
        out[str(ticker)] = (rows.effective_date.tolist(), rows.sic2.astype(str).tolist())
    return out


def asof_sic(lookup, ticker: str, formation: pd.Timestamp) -> str:
    item = lookup.get(ticker)
    if item is None:
        return ""
    ix = bisect_right(item[0], formation) - 1
    return item[1][ix] if ix >= 0 else ""


def read_prices() -> tuple[pd.DataFrame, pd.DataFrame]:
    sp = pd.read_parquet(ROOT / "r6_data/sp500_ohlcv_dev_gapfilled.parquet",
                         columns=["date", "ticker", "open", "close", "adj_close"])
    sp.date = pd.to_datetime(sp.date).dt.normalize()
    sp = sp.loc[sp.date.between(START, END)].copy()
    # Convert unadjusted open to adjusted open using the day's adjustment factor.
    sp["adj_open"] = sp.open * sp.adj_close / sp.close
    sp = sp[["date", "ticker", "adj_open", "adj_close"]]
    c1 = pd.read_parquet(ROOT / "r6_C1/dow_components_dev.parquet",
                         columns=["date", "ticker", "adj_open", "adj_close"])
    c1.date = pd.to_datetime(c1.date).dt.normalize()
    c1 = c1.loc[c1.date.between(START, END)].copy()
    gap = pd.read_parquet(ROOT / "r6_data/dow_dev_gapfill.parquet",
                          columns=["date", "ticker", "open", "close", "adj_close"])
    gap.date = pd.to_datetime(gap.date).dt.normalize()
    gap = gap.loc[gap.date.between(START, END)].copy()
    gap["adj_open"] = gap.open * gap.adj_close / gap.close
    gap = gap[["date", "ticker", "adj_open", "adj_close"]]
    dow = pd.concat([c1, gap], ignore_index=True)
    if dow.duplicated(["date", "ticker"]).any():
        raise ValueError("duplicate Dow OHLCV rows in staged base plus gap-fill")
    for frame in (sp, dow):
        if frame.date.min() < START or frame.date.max() > END:
            raise ValueError("price frame exceeds the development boundary")
    return sp, dow


def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    div_path = ROOT / "r6_data/dividends/dividends_dev.parquet"
    div = pd.read_parquet(div_path, columns=["ticker", "ex_date", "amount_per_share", "data_source"])
    div.ex_date = pd.to_datetime(div.ex_date).dt.normalize()
    div = div.loc[div.ex_date.between(START, END) & (div.amount_per_share > 0)].copy()
    if div.ex_date.min() < START or div.ex_date.max() > END:
        raise ValueError("dividend panel exceeds permitted development boundary")
    manifest = pd.read_csv(ROOT / "r6_data/dividends/manifest.csv", dtype=str).fillna("")
    status = dict(zip(manifest.ticker.astype(str), manifest.yahoo_status.astype(str)))
    lineage_path = ROOT / "r6_data/historical_ticker_cik_lineage.csv"
    lineage = pd.read_csv(lineage_path, dtype=str).fillna("")
    lineage = lineage.drop_duplicates("ticker", keep="last")
    lineage_lookup = dict(zip(lineage.ticker.astype(str), lineage.cik.astype(str)))
    # Retain ticker/security/event/source-response provenance. The upstream
    # dividend package omitted its actual API pull timestamp; keep that field
    # explicitly empty and record file metadata time separately, never relabel it.
    prov_events = div.rename(columns={"ex_date": "event_date", "amount_per_share": "event_amount"})[
        ["ticker", "event_date", "event_amount", "data_source"]]
    provenance = manifest[["ticker", "yahoo_status", "yahoo_rows", "yahoo_error"]].merge(
        prov_events, on="ticker", how="left")
    provenance["cik"] = provenance.ticker.map(lineage_lookup).fillna("")
    provenance["source_pull_timestamp_utc"] = ""
    provenance["source_pull_timestamp_note"] = "not recorded in staged upstream dividend package"
    provenance["manifest_file_mtime_utc"] = datetime.fromtimestamp(
        (ROOT / "r6_data/dividends/manifest.csv").stat().st_mtime, timezone.utc).isoformat()
    provenance["panel_file_sha256"] = hashlib.sha256(div_path.read_bytes()).hexdigest()
    provenance["status_manifest_sha256"] = hashlib.sha256(
        (ROOT / "r6_data/dividends/manifest.csv").read_bytes()).hexdigest()
    provenance["lineage_table_sha256"] = hashlib.sha256(lineage_path.read_bytes()).hexdigest()
    provenance.to_csv(OUT / "R1_DIVIDEND_PROVENANCE.csv", index=False)
    sp_roster = load_roster(ROOT / "r6_data/sp500_pit_roster.csv")
    dow_roster = load_roster(ROOT / "r6_D1/dow_pit_roster.csv")
    sic = make_sic_lookup(build_sic(ROOT / "r6_data/sp500_sic_panel.csv"))
    sp_px, dow_px = read_prices()
    sessions = pd.DatetimeIndex(sorted(sp_px.date.unique()))
    sessions_in_range = sessions[(sessions >= FIRST_FORM) & (sessions <= LAST_FORM)]
    formations = pd.DatetimeIndex(sessions_in_range.to_series().groupby(
        [sessions_in_range.year, sessions_in_range.month]).max().to_numpy())
    if len(formations) != 64:
        raise ValueError(f"expected 64 month-end formations, got {len(formations)}")
    next_first, next_last = [], []
    for f in formations:
        next_month_start = f + pd.offsets.MonthEnd(0) + pd.Timedelta(days=1)
        next_month_dates = sessions[(sessions.year == next_month_start.year) &
                                     (sessions.month == next_month_start.month)]
        if not len(next_month_dates):
            raise ValueError(f"missing next-month price calendar after {f.date()}")
        next_first.append(next_month_dates[0]); next_last.append(next_month_dates[-1])
    names = {"sp500": np.asarray(sorted(sp_roster.ticker.unique()), dtype=str),
             "dow": np.asarray(sorted(dow_roster.ticker.unique()), dtype=str)}
    all_div = {t: g.ex_date.tolist() for t, g in div.groupby("ticker")}
    arrays = {"formations": formations.strftime("%Y-%m-%d").to_numpy(dtype="U10"),
              "next_first": pd.DatetimeIndex(next_first).strftime("%Y-%m-%d").to_numpy(dtype="U10"),
              "next_last": pd.DatetimeIndex(next_last).strftime("%Y-%m-%d").to_numpy(dtype="U10"),
              "sessions": sessions.strftime("%Y-%m-%d").to_numpy(dtype="U10")}
    coverage_rows = []
    for universe, roster, prices in (("sp500", sp_roster, sp_px), ("dow", dow_roster, dow_px)):
        n, m = len(names[universe]), len(formations)
        payer = np.zeros((n, m), dtype=np.int8)
        count = np.zeros((n, m), dtype=np.int16)
        member = np.zeros((n, m), dtype=bool)
        daily_member = np.zeros((n, len(sessions)), dtype=bool)
        sicmat = np.full((n, m), "", dtype="U2")
        statusmat = np.zeros((n, m), dtype=bool)
        fwd_open = np.full((n, m), np.nan)
        fwd_close = np.full((n, m), np.nan)
        opmat = np.full((n, len(sessions)), np.nan)
        clmat = np.full_like(opmat, np.nan)
        ni = {t: i for i, t in enumerate(names[universe])}
        di = {d: i for i, d in enumerate(sessions)}
        for row in roster.itertuples(index=False):
            if row.ticker not in ni:
                continue
            lo = max(START, row.effective_from)
            hi = min(END + pd.Timedelta(days=1), row.effective_to_exclusive)
            i0, i1 = np.searchsorted(sessions, lo), np.searchsorted(sessions, hi)
            if i1 > i0:
                daily_member[ni[row.ticker], i0:i1] = True
        piv_op = prices.pivot(index="ticker", columns="date", values="adj_open")
        piv_cl = prices.pivot(index="ticker", columns="date", values="adj_close")
        piv_op = piv_op.reindex(index=names[universe], columns=sessions)
        piv_cl = piv_cl.reindex(index=names[universe], columns=sessions)
        opmat[:] = piv_op.to_numpy(dtype=float)
        clmat[:] = piv_cl.to_numpy(dtype=float)
        for j, f in enumerate(formations):
            active = set(roster.loc[(roster.effective_from <= f) & (f < roster.effective_to_exclusive), "ticker"])
            for t in active:
                i = ni[t]; member[i, j] = True
                statusmat[i, j] = status.get(t, "") in {"ok", "no_dividend_events"}
                sicmat[i, j] = asof_sic(sic, t, f)
                count[i, j] = recurrence_signal(pd.Series(all_div.get(t, [])), f)
                payer[i, j] = int(count[i, j] > 0)
                fi, li = di[pd.Timestamp(next_first[j])], di[pd.Timestamp(next_last[j])]
                if np.isfinite(opmat[i, fi]) and opmat[i, fi] > 0:
                    fwd_open[i, j] = opmat[i, fi]
                if np.isfinite(clmat[i, li]) and clmat[i, li] > 0:
                    fwd_close[i, j] = clmat[i, li]
            valid = member[:, j] & statusmat[:, j] & (sicmat[:, j] != "") & np.isfinite(fwd_open[:, j]) & np.isfinite(fwd_close[:, j])
            coverage_rows.append({"universe": universe, "formation_date": f.strftime("%Y-%m-%d"),
                                  "pit_members": int(member[:, j].sum()),
                                  "successful_dividend_status": int((member[:, j] & statusmat[:, j]).sum()),
                                  "sic2_members": int((member[:, j] & (sicmat[:, j] != "")).sum()),
                                  "valid_flag_sic_next_month_bars": int(valid.sum()),
                                  "payers": int((valid & (payer[:, j] == 1)).sum()),
                                  "nonpayers": int((valid & (payer[:, j] == 0)).sum())})
        arrays[f"{universe}_names"] = names[universe]
        arrays[f"{universe}_payer"] = payer
        arrays[f"{universe}_recurrence_count"] = count
        arrays[f"{universe}_member"] = member
        arrays[f"{universe}_daily_member"] = daily_member
        arrays[f"{universe}_sic2"] = sicmat
        arrays[f"{universe}_dividend_status_ok"] = statusmat
        arrays[f"{universe}_fwd_open"] = fwd_open
        arrays[f"{universe}_fwd_close"] = fwd_close
        arrays[f"{universe}_adj_open"] = opmat
        arrays[f"{universe}_adj_close"] = clmat
    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(OUT / "formation_coverage.csv", index=False)
    np.savez_compressed(OUT / "R1_INPUTS.npz", **arrays)
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    meta = {"development_only": True, "price_boundary": ["2020-06-01", "2026-10-30"],
            "dividend_boundary": ["2020-06-01", "2026-10-30"], "formation_count": len(formations),
            "minimum_sp500_complete_names": int(coverage.loc[coverage.universe == "sp500", "valid_flag_sic_next_month_bars"].min()),
            "sp500_formation_dates_ge_250": int((coverage.loc[coverage.universe == "sp500", "valid_flag_sic_next_month_bars"] >= 250).sum()),
            "dow_formation_dates": int((coverage.universe == "dow").sum()),
            "outcomes_computed": False, "forward_returns_computed": False,
            "forward_price_values_staged_but_not_divided": True,
            "dividend_source": "staged Yahoo Finance dividend event ex_date panel; only positive amount_per_share rows",
            "dividend_status_source": "staged yahoo_status manifest; ok/no_dividend_events count as complete response",
            "holdout_loaded": False, "price_sha256": hashlib.sha256((ROOT / "r6_data/sp500_ohlcv_dev_gapfilled.parquet").read_bytes()).hexdigest(),
            "dividend_sha256": sha(div_path),
            "sic_sha256": sha(ROOT / "r6_data/sp500_sic_panel.csv"),
            "sp500_roster_sha256": sha(ROOT / "r6_data/sp500_pit_roster.csv"),
            "dow_roster_sha256": sha(ROOT / "r6_D1/dow_pit_roster.csv"),
            "lineage_sha256": sha(lineage_path),
            "dividend_provenance_sha256": sha(OUT / "R1_DIVIDEND_PROVENANCE.csv"),
            "upstream_pull_timestamp_available": False,
            "coverage_sha256": sha(OUT / "formation_coverage.csv"),
            "input_bundle_sha256": sha(OUT / "R1_INPUTS.npz")}
    (OUT / "build_manifest.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
