"""Build E1 monthly input signals and input-only QA. No outcomes or ICs."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
START = pd.Timestamp("2020-11-27")
DATA_START = pd.Timestamp("2020-06-01")
END = pd.Timestamp("2026-10-30")
PRICE = ROOT / "r6_data" / "sp500_ohlcv_dev_gapfilled.parquet"
PIT = ROOT / "r6_data" / "sp500_pit_roster.csv"
SIC_SP = ROOT / "r6_C1" / "sp500_sic_membership_from_L4.csv"
SIC_DOW = ROOT / "r6_C1" / "dow_sic_membership.csv"
SIC_PANEL = ROOT / "r6_data" / "sp500_sic_panel.csv"
REPO_PRICES = ROOT / "repo" / "prices-daily"
REPO_DELISTED = REPO_PRICES.parent / "prices-daily-delisted"


def load_dow_bars(calendar: pd.DatetimeIndex) -> pd.DataFrame:
    paths = list(REPO_PRICES.glob("*.csv"))
    if REPO_DELISTED.exists():
        paths.extend(REPO_DELISTED.glob("*.csv"))
    rows = []
    cols = ["date", "open", "high", "low", "close", "volume"]
    for path in paths:
        try:
            x = pd.read_csv(path, usecols=cols)
        except (ValueError, FileNotFoundError):
            continue
        x["date"] = pd.to_datetime(x.date, utc=True).dt.tz_convert(None).dt.normalize()
        x = x.loc[x.date.between(DATA_START, END)].copy()
        if x.empty:
            continue
        x["ticker"] = path.stem.upper()
        rows.append(x)
    if not rows:
        raise FileNotFoundError(f"No Dow OHLCV files found in {REPO_PRICES}")
    x = pd.concat(rows, ignore_index=True)
    # Preserve only the same market sessions as the S&P 500 development panel.
    return x.loc[x.date.isin(calendar)].drop_duplicates(["date", "ticker"], keep="last")


def dow_roster(cal: pd.DatetimeIndex) -> pd.DataFrame:
    base = "MMM AXP AMGN AAPL BA CAT CVX CSCO KO DIS DOW GS HD HON IBM INTC JNJ JPM MCD MRK MSFT NKE PG CRM TRV UNH VZ V WBA WMT".split()
    changes = [("2024-02-26", "AMZN", "WBA"), ("2024-11-08", "NVDA", "INTC"), ("2024-11-08", "SHW", "DOW")]
    rows = []
    for d in cal:
        tickers = set(base)
        for day, added, removed in changes:
            if d >= pd.Timestamp(day):
                tickers.discard(removed)
                tickers.add(added)
        rows.extend((d, t) for t in sorted(tickers))
    return pd.DataFrame(rows, columns=["date", "ticker"])


def read_membership(path: Path, level="sic2") -> pd.DataFrame:
    m = pd.read_csv(path, dtype={"ticker": str, "sic2": str, "sic": str})
    if "effective_date" in m.columns:
        # SEC filing SIC is usable on the first NYSE session after filing; panel
        # has already materialized that date. Convert observations to dated
        # half-open intervals and keep missing symbols/classifications missing.
        m["ticker"] = m.ticker.astype(str).str.upper()
        m["effective_from"] = pd.to_datetime(m.effective_date, errors="coerce")
        m["filing_date"] = pd.to_datetime(m.get("filing_date"), errors="coerce")
        m["sic"] = m.sic.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(4)
        m = m.loc[m.effective_from.notna() & m.sic.str.fullmatch(r"\d{4}")].copy()
        m["sic2"] = m.sic.str[:2]
        rows = []
        for ticker, g in m.sort_values(["effective_from", "filing_date"]).groupby("ticker"):
            g = g.drop_duplicates("effective_from", keep="last").reset_index(drop=True)
            for i, row in g.iterrows():
                hi = g.loc[i + 1, "effective_from"] if i + 1 < len(g) else END + pd.Timedelta(days=1)
                if hi > row.effective_from:
                    rows.append({"ticker": ticker, "cik": row.cik, "sic": row.sic, "sic2": row.sic2,
                                 "effective_from": row.effective_from, "effective_to_exclusive": hi,
                                 "source_url": row.source_url, "flag": row.flag})
        m = pd.DataFrame(rows)
        return m
    if level not in m.columns:
        if "sic" in m.columns:
            m[level] = m.sic.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(4).str[:2]
        else:
            raise ValueError(f"{path} lacks {level} classification")
    m["ticker"] = m.ticker.str.upper()
    m[level] = m[level].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(2)
    m["effective_from"] = pd.to_datetime(m.effective_from)
    m["effective_to_exclusive"] = pd.to_datetime(m.effective_to_exclusive)
    # Apply the development-window guard before any joins or calculations.
    m = m.loc[(m.effective_to_exclusive > START) & (m.effective_from <= END)].copy()
    return m


def monthly_pressure(bars: pd.DataFrame, roster: pd.DataFrame, membership: pd.DataFrame,
                     dates: pd.DatetimeIndex, universe: str) -> dict:
    tickers = sorted(set(roster.ticker.astype(str).str.upper()))
    cal = pd.DatetimeIndex(dates)
    # Keep actual OHLCV inputs only, and never calculate from dates before START.
    b = bars.loc[bars.date.between(DATA_START, END) & bars.ticker.isin(tickers)].copy()
    b["ticker"] = b.ticker.str.upper()
    for col in ("high", "low", "close", "volume"):
        b[col] = pd.to_numeric(b[col], errors="coerce")
    b = b.sort_values(["ticker", "date"]).drop_duplicates(["date", "ticker"], keep="last")
    # Last observed US trading session of each calendar month.
    formations = pd.DatetimeIndex(pd.Series(cal, index=cal).groupby(cal.to_period("M")).max().values)
    formations = formations[(formations >= START) & (formations <= END)]
    wide = {c: b.pivot(index="date", columns="ticker", values=c).reindex(index=cal, columns=tickers)
            for c in ("high", "low", "close", "volume")}
    hi, lo, close, vol = (wide[c] for c in ("high", "low", "close", "volume"))
    denom_range = hi - lo
    clv = ((2.0 * close - hi - lo) / denom_range).where(denom_range.ne(0), 0.0)
    clv = clv.where(denom_range.notna())
    dollar = close * vol
    valid_daily = clv.notna() & dollar.notna() & np.isfinite(dollar) & dollar.gt(0)
    pressure = pd.DataFrame(np.nan, index=formations, columns=tickers, dtype=float)
    pressure_valid = pd.DataFrame(False, index=formations, columns=tickers)
    roster_active = pd.DataFrame(False, index=formations, columns=tickers)
    for dt in formations:
        end_idx = cal.get_indexer([dt])[0]
        if end_idx < 20:
            continue
        idx = cal[end_idx-20:end_idx+1]
        daily_ok = valid_daily.loc[idx]
        complete = daily_ok.all(axis=0)
        numerator = (clv.loc[idx] * dollar.loc[idx]).sum(axis=0, min_count=21)
        denominator = dollar.loc[idx].sum(axis=0, min_count=21)
        p = numerator / denominator
        present = set(roster.loc[roster.date.eq(dt), "ticker"].astype(str).str.upper())
        roster_active.loc[dt] = np.asarray([ticker in present for ticker in tickers], dtype=bool)
        # S&P roster is interval data and has already been expanded by caller;
        # Dow roster is likewise expanded by caller.
        pressure.loc[dt] = p.where(complete & roster_active.loc[dt] & denominator.gt(0))
        pressure_valid.loc[dt] = pressure.loc[dt].notna()

    sic = membership.copy()
    # Dated SIC2 assignment active on each formation date; absent/ambiguous rows stay unmapped.
    sic_rows = []
    for dt in formations:
        active = sic.loc[(sic.effective_from <= dt) & (sic.effective_to_exclusive > dt), ["ticker", "sic2"]]
        unambiguous = active.groupby("ticker").sic2.nunique()
        keep = set(unambiguous[unambiguous.eq(1)].index)
        active = active.loc[active.ticker.isin(keep)].drop_duplicates("ticker", keep="last")
        sic_rows.append(active.set_index("ticker").sic2.reindex(tickers))
    sic_at = pd.DataFrame(sic_rows, index=formations, columns=tickers)
    sic_at = sic_at.where(roster_active)
    peer = pd.DataFrame(np.nan, index=formations, columns=tickers, dtype=float)
    sic_active = sic_at.notna()
    group_size = pd.DataFrame(0, index=formations, columns=tickers, dtype=np.int16)
    peer_count = pd.DataFrame(0, index=formations, columns=tickers, dtype=np.int16)
    singleton_groups = []
    group_rows = []
    for dt in formations:
        groups = sic_at.loc[dt].dropna().groupby(sic_at.loc[dt].dropna())
        sizes = {str(g): int(len(members)) for g, members in groups}
        for grp, n in sizes.items():
            group_rows.append({"universe": universe, "formation_date": dt.date().isoformat(), "sic2": grp, "group_size": n})
            if n == 1:
                singleton_groups.append((dt.date().isoformat(), grp))
        for grp, members in groups:
            names = list(members.index)
            group_size.loc[dt, names] = len(names)
            valid_names = [n for n in names if pressure_valid.loc[dt, n]]
            for name in names:
                others = [n for n in valid_names if n != name]
                peer_count.loc[dt, name] = len(others)
                if pressure_valid.loc[dt, name] and len(others) >= 2:
                    peer.loc[dt, name] = pressure.loc[dt, others].mean()

    return {"universe": universe, "tickers": tickers, "dates": formations,
            "pressure": pressure, "peer": peer, "roster_active": roster_active,
            "pressure_valid": pressure_valid, "sic_active": sic_active,
            "peer_active": peer.notna(), "sic2": sic_at, "group_size": group_size,
            "peer_count": peer_count, "group_rows": group_rows,
            "singleton_groups": singleton_groups,
            "daily_rows": int(len(b)), "distinct_bar_tickers": int(b.ticker.nunique()),
            "roster_tickers": len(tickers)}


def expand_roster(pit: pd.DataFrame, cal: pd.DatetimeIndex) -> pd.DataFrame:
    rows = []
    p = pit.copy()
    p["ticker"] = p.ticker.astype(str).str.upper()
    p["effective_from"] = pd.to_datetime(p.effective_from)
    p["effective_to_exclusive"] = pd.to_datetime(p.effective_to_exclusive)
    p = p.loc[(p.effective_to_exclusive > START) & (p.effective_from <= END)]
    for d in cal:
        active = p.loc[(p.effective_from <= d) & (p.effective_to_exclusive > d), "ticker"].drop_duplicates()
        rows.extend((d, t) for t in active)
    return pd.DataFrame(rows, columns=["date", "ticker"])


def daily_member_day_coverage(bars: pd.DataFrame, roster: pd.DataFrame, sic: pd.DataFrame,
                              calendar: pd.DatetimeIndex) -> dict:
    """Input-only PIT member-day coverage for usable OHLCV plus dated SIC lineage."""
    dates = calendar[(calendar >= START) & (calendar <= END)]
    r = roster.loc[roster.date.isin(dates)].copy()
    r["ticker"] = r.ticker.astype(str).str.upper()
    rmap = {d: set(g.ticker) for d, g in r.groupby("date")}
    b = bars.loc[bars.date.isin(dates)].copy()
    b["ticker"] = b.ticker.astype(str).str.upper()
    fields = [c for c in ("high", "low", "close", "volume") if c in b.columns]
    for c in fields:
        b[c] = pd.to_numeric(b[c], errors="coerce")
    valid = b[fields].notna().all(axis=1) & b.close.gt(0) & b.volume.gt(0) & b.high.ge(b.low)
    bmap = {d: set(g.ticker) for d, g in b.loc[valid].groupby("date")}
    expected = ohlcv = full_lineage = 0
    for d in dates:
        members = rmap.get(d, set())
        expected += len(members)
        bar_names = bmap.get(d, set())
        ohlcv += len(members & bar_names)
        dated = sic.loc[(sic.effective_from <= d) & (sic.effective_to_exclusive > d), "ticker"]
        sic_names = set(dated.astype(str).str.upper())
        full_lineage += len(members & bar_names & sic_names)
    return {"scheduled_member_days": int(expected),
            "member_days_with_complete_ohlcv": int(ohlcv),
            "member_days_with_ohlcv_and_dated_sic": int(full_lineage),
            "ohlcv_coverage_pct": 100.0 * ohlcv / expected if expected else 0.0,
            "ohlcv_and_sic_coverage_pct": 100.0 * full_lineage / expected if expected else 0.0,
            "passes_90pct_ohlcv_and_sic_gate": bool(full_lineage / expected >= 0.90) if expected else False}


def main() -> None:
    if not PRICE.exists():
        raise FileNotFoundError(PRICE)
    sp = pd.read_parquet(PRICE, columns=["date", "ticker", "high", "low", "close", "volume"])
    sp["date"] = pd.to_datetime(sp.date).dt.tz_localize(None).dt.normalize()
    sp["ticker"] = sp.ticker.astype(str).str.upper()
    sp = sp.loc[sp.date.between(DATA_START, END)].copy()
    cal = pd.DatetimeIndex(sorted(sp.date.unique()))
    pit = pd.read_csv(PIT, dtype={"ticker": str})
    sp_roster = expand_roster(pit, cal)
    sp_sic = read_membership(SIC_PANEL, "sic2")
    sp_result = monthly_pressure(sp, sp_roster, sp_sic, cal, "SP500")
    sp_member_days = daily_member_day_coverage(sp, sp_roster, sp_sic, cal)

    dow = load_dow_bars(cal)
    dow_roster_frame = dow_roster(cal)
    dow_sic = sp_sic.copy()
    dow_result = monthly_pressure(dow, dow_roster_frame, dow_sic, cal, "Dow30")
    dow_member_days = daily_member_day_coverage(dow, dow_roster_frame, dow_sic, cal)

    sic_panel_raw = pd.read_csv(SIC_PANEL, dtype={"ticker": str, "sic": str, "source": str, "flag": str})
    sic_valid_rows = sic_panel_raw.loc[sic_panel_raw.sic.astype(str).str.fullmatch(r"\d{4}")]
    sic_fallback_rows = sic_valid_rows.loc[sic_valid_rows.source.str.contains("fallback", na=False)]
    sic_panel_summary = {"distinct_tickers_with_usable_sic": int(sic_valid_rows.ticker.nunique()),
                         "usable_10k_header_rows": int((sic_valid_rows.source == "10-K_header_ASSIGNED-SIC").sum()),
                         "current_sic_fallback_rows": int(len(sic_fallback_rows)),
                         "fallback_tickers": sorted(sic_fallback_rows.ticker.unique().tolist()),
                         "rows_without_sic": int(len(sic_panel_raw) - len(sic_valid_rows))}
    out = {}
    qa = {"development_only": True, "outcome_columns_loaded": False,
          "forward_returns_computed": False, "ics_computed": False,
          "date_start": str(START.date()), "lookback_data_start": str(DATA_START.date()), "date_end": str(END.date()),
          "formation_rule": "last observed US trading session each calendar month",
          "pressure_rule": "21-session CLV * raw close * volume weighted mean; zero CLV if high=low; any missing OHLCV among 21 rows makes pressure missing",
          "peer_rule": "equal-weight mean of same active dated SIC2 peer pressures, leave-one-out; at least two other valid peer pressures",
          "sic2_source_SP500": str(SIC_PANEL.relative_to(ROOT)),
          "sic2_source_Dow": str(SIC_PANEL.relative_to(ROOT)),
          "sic_panel_coverage": sic_panel_summary,
          "daily_member_day_coverage": {"SP500": sp_member_days, "Dow30": dow_member_days},
          "gapfill_source": str(PRICE.relative_to(ROOT)), "gapfill_manifest": str((ROOT/'r6_data'/'gapfill_manifest.csv').relative_to(ROOT)),
          "universes": {}}
    for x in (sp_result, dow_result):
        name = x["universe"]
        ids, ds = x["tickers"], x["dates"]
        active = x["roster_active"].to_numpy(dtype=bool)
        pvalid = x["pressure_valid"].to_numpy(dtype=bool)
        sactive = x["sic_active"].to_numpy(dtype=bool)
        peeractive = x["peer_active"].to_numpy(dtype=bool)
        prefix = "sp500" if name == "SP500" else "dow"
        out[f"{prefix}_tickers"] = np.asarray(ids, dtype="U16")
        out[f"{prefix}_formation_dates"] = ds.strftime("%Y-%m-%d").to_numpy(dtype="U10")
        out[f"{prefix}_stock_pressure"] = x["pressure"].to_numpy(dtype=np.float32)
        out[f"{prefix}_peer_pressure"] = x["peer"].to_numpy(dtype=np.float32)
        out[f"{prefix}_active_roster"] = active
        out[f"{prefix}_active_pressure"] = pvalid
        out[f"{prefix}_active_sic2"] = sactive
        out[f"{prefix}_active_peer_score"] = peeractive
        out[f"{prefix}_sic2"] = x["sic2"].fillna("").to_numpy(dtype="U2")
        out[f"{prefix}_industry_group_size"] = x["group_size"].to_numpy(dtype=np.int16)
        out[f"{prefix}_valid_peer_count"] = x["peer_count"].to_numpy(dtype=np.int16)
        expected = x["roster_active"].sum(axis=1)
        pressure_n = x["pressure_valid"].sum(axis=1)
        sic_n = x["sic_active"].sum(axis=1)
        score_n = x["peer_active"].sum(axis=1)
        sizes = pd.Series([r["group_size"] for r in x["group_rows"]], dtype=int)
        qa["universes"][name] = {
            "formations": int(len(ds)), "first_formation": str(ds.min().date()), "last_formation": str(ds.max().date()),
            "ticker_axis_n": len(ids), "distinct_tickers_with_bars": x["distinct_bar_tickers"],
            "daily_bar_rows_in_development_window": x["daily_rows"],
            "median_active_roster": float(expected.median()), "min_active_roster": int(expected.min()),
            "median_complete_21_session_pressure": float(pressure_n.median()), "min_complete_pressure": int(pressure_n.min()),
            "median_sic2_mapped_members": float(sic_n.median()), "min_sic2_mapped_members": int(sic_n.min()),
            "median_peer_score_eligible": float(score_n.median()), "min_peer_score_eligible": int(score_n.min()),
            "sic_group_observations": int(len(sizes)),
            "sic_group_size_distribution": {str(int(k)): int(v) for k, v in sizes.value_counts().sort_index().items()},
            "singleton_industry_observations": int(len(x["singleton_groups"])),
            "singleton_industry_counts_by_sic2": {str(k): int(v) for k, v in pd.Series([g for _, g in x["singleton_groups"]]).value_counts().sort_index().items()},
            "eligible_names_250_gate_passed": bool((score_n >= 250).mean() >= 0.80) if name == "SP500" else None,
            "eligible_dates_fraction_at_250_names": float((score_n >= 250).mean()) if name == "SP500" else None,
            "coverage_issue": "The input QA preserves unresolved OHLCV ticker histories and the one symbol without dated SIC; no missing values are imputed."
        }
        pd.DataFrame(x["group_rows"]).to_csv(OUT / f"{prefix}_sic2_group_sizes.csv", index=False)
    np.savez_compressed(OUT / "E1_INPUTS.npz", **out)
    (OUT / "input_manifest.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    write_qa(qa)
    print(f"Wrote {OUT / 'E1_INPUTS.npz'} and INPUT_QA.md")


def write_qa(qa: dict) -> None:
    lines = ["# E1 monthly CLV-pressure input QA", "",
        "This is an input-only signal build. No forward returns, signal-outcome joins, ICs, or portfolio outcomes were loaded or computed. Price OHLCV was loaded only from 2020-06-01 through 2026-10-30 so the first registered formation has its full 21-session lookback; the registered formation window begins 2020-11-27 and its first month-end observation is 2020-11-30. No price data before 2020-06 or holdout data were read; SIC filing metadata starts in 2019 as preregistered.", "",
        "## Registered construction", "",
        "- Formation: final observed trading session of each calendar month.",
        "- Stock pressure: 21 sessions through formation close; daily CLV is `(2*close-high-low)/(high-low)` with zero for a zero range; pressure is weighted by raw close times volume. Any incomplete 21-session OHLCV window is missing.",
        "- Peer score: equal-weight, leave-one-out mean of same active SIC2 peers with at least two other valid peer-pressure observations.",
        "- Active masks separately identify point-in-time roster membership, pressure availability, SIC2 membership, and usable peer score.", "",
        "## Input coverage", ""]
    for name, u in qa["universes"].items():
        lines += [f"### {name}", "",
            f"- Monthly formations: {u['formations']} ({u['first_formation']} to {u['last_formation']}).",
            f"- Ticker axis: {u['ticker_axis_n']}; tickers with at least one development-window bar: {u['distinct_tickers_with_bars']}; daily OHLCV rows: {u['daily_bar_rows_in_development_window']:,}.",
            f"- Median (minimum) roster size: {u['median_active_roster']:.0f} ({u['min_active_roster']}).",
            f"- Median (minimum) complete 21-session pressure count: {u['median_complete_21_session_pressure']:.0f} ({u['min_complete_pressure']}).",
            f"- Median (minimum) members with dated SIC2: {u['median_sic2_mapped_members']:.0f} ({u['min_sic2_mapped_members']}).",
            f"- Median (minimum) eligible leave-one-out peer scores: {u['median_peer_score_eligible']:.0f} ({u['min_peer_score_eligible']}).",
            f"- SIC2 group-size distribution over formation-date/group observations: `{u['sic_group_size_distribution']}`.",
            f"- Singleton industry observations: {u['singleton_industry_observations']}; counts by SIC2: `{u['singleton_industry_counts_by_sic2']}`.",
            f"- Preregistration 250-name/80%-date input threshold passed: {u['eligible_names_250_gate_passed'] if name == 'SP500' else 'not applicable to Dow'}.",
            "- Input limitation: missing dated SIC classifications and bars are left missing; no peers are invented or substituted.", ""]
    lines += ["## Unchanged E1 input gates", "",
        f"- S&P 500 member-day coverage with complete OHLCV and dated SIC lineage: {qa['daily_member_day_coverage']['SP500']['ohlcv_and_sic_coverage_pct']:.2f}% (registered minimum 90%); gate {'PASS' if qa['daily_member_day_coverage']['SP500']['passes_90pct_ohlcv_and_sic_gate'] else 'FAIL'}.",
        f"- Dow 30 member-day coverage with complete OHLCV and dated SIC lineage: {qa['daily_member_day_coverage']['Dow30']['ohlcv_and_sic_coverage_pct']:.2f}% (registered minimum 90%); gate {'PASS' if qa['daily_member_day_coverage']['Dow30']['passes_90pct_ohlcv_and_sic_gate'] else 'FAIL'}.",
        f"- S&P 500 dates with at least 250 eligible peer scores: {qa['universes']['SP500']['eligible_dates_fraction_at_250_names']*100:.2f}% (registered minimum 80%); gate {'PASS' if qa['universes']['SP500']['eligible_names_250_gate_passed'] else 'FAIL'}.",
        "- These are input-coverage gates only; no signal-outcome statistics were computed.", "",
        "## S&P 500 gap and feasibility caveat", "",
        "The source QA reports 622 distinct PIT tickers across the wider data window and 614 whose PIT intervals overlap this formation window. Original Yahoo OHLCV covered 568 of 622; the documented gap-fill recovered ADS (15 rows), FBHS (644 rows), and SATS (64 rows), leaving 51 ticker histories without rows. The unresolved PIT symbols are ABMD, ALXN, ANSS, ATVI, AVB, CDAY, CERN, CMA, CTLT, CTRA, CTXS, CXO, DAY, DFS, DISCA, DISCK, DISH, DRE, EA, ETFC, FLIR, FRC, GPS, HBI, HES, HFC, HOLX, INFO, IPG, JNPR, JWN, K, KSU, KVUE, LEG, MRO, MXIM, NBL, NLSN, PBCT, PXD, QRVO, SBNY, SEE, SIVB, TIF, TWTR, VAR, WBA, WBD, and XLNX. The gap-fill histories are same-share-line aliases only over their documented PIT membership intervals. This builder preserves the missing-name price-history gap and does not replace issuers with acquirer or current-survivor prices.", "",
        f"The dated SIC source is `r6_data/sp500_sic_panel.csv`, built from SEC 10-K headers and the SEC CIK/ticker lineage. It contains usable SIC for {qa['sic_panel_coverage']['distinct_tickers_with_usable_sic']} unique symbols, including {qa['sic_panel_coverage']['usable_10k_header_rows']} dated 10-K rows and {qa['sic_panel_coverage']['current_sic_fallback_rows']} explicitly flagged current-SIC fallback rows; FRC remains without SIC because no usable 10-K header or current SIC was returned. The same issuer SIC timeline is applied to Dow holdings when a ticker is present in the S&P PIT SIC panel. No missing classification is invented. The numeric coverage above is checked against the unchanged E1 250-name/80%-of-dates gate; failure blocks any outcome work.", "",
        "## Files", "",
        "- `E1_INPUTS.npz`: rectangular arrays, separate axes and dates for S&P500 and Dow; `*_stock_pressure`, `*_peer_pressure`, active masks, SIC2 labels, group sizes, and valid-peer counts.",
        "- `*_sic2_group_sizes.csv`: per-formation-date SIC2 group sizes, including singleton groups.",
        "- `input_manifest.json`: machine-readable input QA and construction provenance.",
        "- `build_inputs.py`: reproducible builder. All output paths are inside `r6_E1/`.", ""]
    (OUT / "INPUT_QA.md").write_text("\n".join(lines), encoding="utf-8")

if __name__ == "__main__":
    main()
