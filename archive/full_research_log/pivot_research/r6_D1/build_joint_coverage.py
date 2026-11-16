"""Build joint D1 input coverage; never read price values or returns.

Only date/ticker price-bar presence, PIT roster intervals, FINRA ratio validity,
and complete-window masks are used. The FINRA ratio field is read only to mark
finite paired ratios. No forward return is loaded or calculated.
"""
from __future__ import annotations
import json
from pathlib import Path
import math
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
START, END = pd.Timestamp("2020-11-27"), pd.Timestamp("2026-10-30")
DATA_START = pd.Timestamp("2020-06-01")


def load_calendar():
    m = pd.read_csv(ROOT / "r6_data/finra_regsho/download_manifest.csv", usecols=["date"])
    d = pd.DatetimeIndex(pd.to_datetime(m.date).dt.normalize().drop_duplicates().sort_values())
    return d[(d >= DATA_START) & (d <= END)]


def load_paired_finra():
    # Read only date, universe, ticker and the ratio's validity; ratio values are
    # never summarized, reported, or used as signal/outcome statistics here.
    f = pd.read_csv(ROOT / "r6_data/finra_regsho/signal_panel.csv.gz",
                    usecols=["date", "universe", "ticker", "short_volume_ratio"],
                    dtype={"universe": str, "ticker": str})
    f["date"] = pd.to_datetime(f.date).dt.normalize()
    ratio = pd.to_numeric(f.short_volume_ratio, errors="coerce").to_numpy(dtype=float)
    f["valid_pair"] = np.isfinite(ratio)
    f["ticker"] = f.ticker.str.upper()
    f = f.loc[f.date.between(DATA_START, END) & f.valid_pair]
    return {
        "SP500": set(zip(f.loc[f.universe.eq("SP500"), "ticker"],
                         f.loc[f.universe.eq("SP500"), "date"])),
        "DOW30": set(zip(f.loc[f.universe.eq("DOW30"), "ticker"],
                         f.loc[f.universe.eq("DOW30"), "date"])),
    }


def load_sp_price_presence(calendar):
    import pyarrow.parquet as pq
    path = ROOT / "r6_data/sp500_ohlcv_dev_gapfilled.parquet"
    t = pq.read_table(path, columns=["date", "ticker"],
                      filters=[("date", ">=", DATA_START.to_pydatetime()),
                               ("date", "<=", END.to_pydatetime())]).to_pandas()
    t["date"] = pd.to_datetime(t.date).dt.normalize()
    t["ticker"] = t.ticker.astype(str).str.upper()
    t = t.loc[t.date.isin(calendar)]
    return set(zip(t.ticker, t.date))


def load_dow_price_presence(calendar):
    # Source CSVs contain longer histories. Inspect only the date token for
    # rows in the permitted development interval; never parse price columns.
    folders = [ROOT / "repo/prices-daily", ROOT / "repo/prices-daily-delisted"]
    present = set()
    for folder in folders:
        if not folder.exists():
            continue
        for path in folder.glob("*.csv"):
            ticker = path.stem.upper()
            with path.open("r", encoding="utf-8-sig", errors="replace") as fh:
                header = fh.readline().strip().split(",")
                if "date" not in header:
                    continue
                date_idx = header.index("date")
                for line in fh:
                    # Read only the designated date field; do not parse OHLCV.
                    fields = line.split(",", date_idx + 1)
                    if len(fields) <= date_idx:
                        continue
                    raw = fields[date_idx].strip().strip('"')[:10]
                    if len(raw) != 10 or raw < "2020-06-01" or raw > "2026-10-30":
                        continue
                    day = pd.Timestamp(raw)
                    if day in calendar:
                        present.add((ticker, day))
    return present


def load_roster(key):
    if key == "SP500":
        p = ROOT / "r6_data/sp500_pit_roster.csv"
    else:
        p = OUT / "dow_pit_roster.csv"
    r = pd.read_csv(p, usecols=["ticker", "effective_from", "effective_to_exclusive"], dtype={"ticker": str})
    r["ticker"] = r.ticker.str.upper()
    r["effective_from"] = pd.to_datetime(r.effective_from).dt.normalize()
    r["effective_to_exclusive"] = pd.to_datetime(r.effective_to_exclusive).dt.normalize()
    return r


def day_active(roster, date):
    return roster.loc[roster.effective_from.le(date) & roster.effective_to_exclusive.gt(date), "ticker"].drop_duplicates().tolist()


def summarize_daily(universe, roster, cal, ratios, prices):
    rows = []
    for d in cal[(cal >= START) & (cal <= END)]:
        names = day_active(roster, d)
        ratio = sum((n, d) in ratios for n in names)
        bar = sum((n, d) in prices for n in names)
        joint = sum((n, d) in ratios and (n, d) in prices for n in names)
        rows.append((universe, d.date().isoformat(), len(names), ratio, bar, joint))
    return pd.DataFrame(rows, columns=["universe", "date", "scheduled_pit_members", "valid_paired_finra_ratio_members",
                                       "price_bar_presence_members", "same_day_joint_members"])


def summarize_formations(universe, roster, cal, ratios, prices, formations):
    rows = []
    for d in formations:
        ix = cal.get_indexer([d])[0]
        names = day_active(roster, d)
        has_calendar_signal = ix >= 4
        has_calendar_forward = ix >= 0 and ix + 6 < len(cal)
        ratio_today = sum((n, d) in ratios for n in names)
        ratio_complete = signal_bars = forward_bars = eligible = 0
        for n in names:
            ratio5 = has_calendar_signal and all((n, cal[j]) in ratios for j in range(ix - 4, ix + 1))
            signal5 = has_calendar_signal and all((n, cal[j]) in prices for j in range(ix - 4, ix + 1))
            forward5 = has_calendar_forward and all((n, cal[j]) in prices for j in range(ix + 2, ix + 7))
            ratio_complete += int(ratio5)
            signal_bars += int(signal5)
            forward_bars += int(forward5)
            eligible += int(ratio5 and signal5 and forward5)
        rows.append((universe, d.date().isoformat(), len(names), ratio_today, ratio_complete,
                     signal_bars, forward_bars, eligible, has_calendar_signal, has_calendar_forward))
    return pd.DataFrame(rows, columns=["universe", "formation_date", "scheduled_pit_members",
        "valid_paired_finra_ratio_at_t", "complete_five_session_finra_score",
        "complete_five_session_signal_price_bars", "complete_forward_price_bars_t2_to_t6",
        "joint_eligible_names", "signal_calendar_window_available", "forward_calendar_window_available"])


def main():
    cal = load_calendar()
    # Prereg schedule begins on the first stated formation date, then every fifth
    # NYSE session. Last dates remain in the manifest and fail eligibility when
    # the full t+2..t+6 window is outside development data.
    dev_cal = cal[(cal >= START) & (cal <= END)]
    formations = dev_cal[::5]
    finra = load_paired_finra()
    prices = {"SP500": load_sp_price_presence(cal), "DOW30": load_dow_price_presence(cal)}
    rosters = {k: load_roster(k) for k in ("SP500", "DOW30")}

    all_daily, all_form = [], []
    for k in ("SP500", "DOW30"):
        all_daily.append(summarize_daily(k, rosters[k], cal, finra[k], prices[k]))
        all_form.append(summarize_formations(k, rosters[k], cal, finra[k], prices[k], formations))
    daily = pd.concat(all_daily, ignore_index=True)
    form = pd.concat(all_form, ignore_index=True)
    form.to_csv(OUT / "joint_coverage.csv", index=False)
    daily.to_csv(OUT / "joint_daily_coverage.csv", index=False)

    summaries = {}
    for k in ("SP500", "DOW30"):
        d = daily.loc[daily.universe.eq(k)]
        f = form.loc[form.universe.eq(k)]
        daily_den = int(d.scheduled_pit_members.sum())
        daily_joint = int(d.same_day_joint_members.sum())
        form_den = int(f.scheduled_pit_members.sum())
        form_joint = int(f.joint_eligible_names.sum())
        dates_ge250 = int((f.joint_eligible_names >= 250).sum())
        # The member-day gate is evaluated on the stricter formation-date
        # joint mask; same-day daily coverage is reported as a diagnostic.
        summaries[k] = {
            "development_daily_sessions": int(len(d)),
            "daily_scheduled_member_days": daily_den,
            "daily_joint_finra_and_price_member_days": daily_joint,
            "daily_joint_coverage_pct": 100 * daily_joint / daily_den if daily_den else None,
            "scheduled_formation_dates": int(len(f)),
            "formation_member_days": form_den,
            "formation_joint_eligible_member_days": form_joint,
            "formation_joint_member_day_coverage_pct": 100 * form_joint / form_den if form_den else None,
            "formation_dates_ge_250_eligible": dates_ge250,
            "formation_dates_pct_ge_250": 100 * dates_ge250 / len(f) if len(f) else None,
            "median_scheduled_members_per_formation": float(f.scheduled_pit_members.median()),
            "median_complete_ratio_scores": float(f.complete_five_session_finra_score.median()),
            "median_signal_price_complete": float(f.complete_five_session_signal_price_bars.median()),
            "median_forward_price_complete": float(f.complete_forward_price_bars_t2_to_t6.median()),
            "median_joint_eligible_names": float(f.joint_eligible_names.median()),
            "min_joint_eligible_names": int(f.joint_eligible_names.min()),
            "daily_member_day_gate_pass_90pct": daily_joint / daily_den >= .90 if daily_den else False,
            "strict_formation_member_day_gate_pass_90pct": form_joint / form_den >= .90 if form_den else False,
            "formation_date_gate_pass_80pct": (dates_ge250 / len(f) >= .80 if len(f) else False) if k == "SP500" else None,
        }

    gaps = ["ABMD", "ALXN", "ANSS", "ATVI", "AVB", "CDAY", "CERN", "CMA", "CTLT", "CTRA", "CTXS", "CXO", "DAY", "DFS", "DISCA", "DISCK", "DISH", "DRE", "EA", "ETFC", "FLIR", "FRC", "GPS", "HBI", "HES", "HFC", "HOLX", "INFO", "IPG", "JNPR", "JWN", "K", "KSU", "KVUE", "LEG", "MRO", "MXIM", "NBL", "NLSN", "PBCT", "PXD", "QRVO", "SBNY", "SEE", "SIVB", "TIF", "TWTR", "VAR", "WBA", "WBD", "XLNX"]
    overall_pass = (all(summaries[k]["strict_formation_member_day_gate_pass_90pct"] for k in summaries)
                    and bool(summaries["SP500"]["formation_date_gate_pass_80pct"]))
    manifest = {"development_only": True, "price_values_loaded": False, "price_returns_computed": False,
                "forward_returns_loaded_or_computed": False, "ics_computed": False,
                "formation_rule": "every fifth NYSE session beginning 2020-11-27",
                "formation_price_windows": {"signal": "t-4 through t, bar presence only", "forward": "t+2 through t+6, bar presence only"},
                "paired_finra_definition": "finite short_volume_ratio row in existing signal_panel; ratio values not summarized or exported",
                "scheduled_formation_dates": int(len(formations)), "first_formation": str(formations[0].date()),
                "last_formation": str(formations[-1].date()), "sp500_unresolved_price_gap_count": len(gaps),
                "sp500_unresolved_price_gap_symbols": gaps, "universes": summaries,
                "overall_gate": "PASS" if overall_pass else "FAIL",
                "gate_rule": "strict formation joint member-day coverage >=90% for both universes and >=80% of scheduled S&P formation dates with >=250 jointly eligible names; the 250-name threshold applies only to the S&P mechanism universe"}
    (OUT / "joint_coverage_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    lines = ["# D1 joint input coverage (development only)", "",
        "This is an input-only coverage audit under frozen `specs/r6_prereg/D1.md`. It uses point-in-time membership dates, finite paired FINRA ratio availability, and price-bar date/ticker presence only. Price columns and price/return values are not loaded; no forward returns, outcomes, ratios as signals, or ICs are computed.", "",
        "## Date and mask definitions", "",
        "The NYSE schedule is the session calendar from the FINRA development manifest. Formation dates are every fifth session starting 2020-11-27, through the last development session. For formation `t`, the complete FINRA score requires valid paired ratios for the five sessions `t-4` through `t`. Price input availability is presence-only: the five signal-window bars `t-4` through `t`, and the five forward-window bars `t+2` through `t+6`. A jointly eligible name must be a PIT member on `t` and have all three complete masks. The final scheduled dates remain in `joint_coverage.csv`; dates without the full calendar-forward window have no eligible names. Daily member-day same-date coverage is also reported separately.", "",
        "## Gate summary", "",
        "| Universe | Daily joint ratio + bar coverage | Formation joint member-day coverage | Median eligible names/date | Min names/date | Dates with ≥250 S&P names | 90% member-day | 80% S&P-date gate |",
        "|---|---:|---:|---:|---:|---:|---|---|"]
    for k, label in (("SP500", "S&P 500"), ("DOW30", "Dow 30")):
        s = summaries[k]
        gate250 = f"{s['formation_dates_ge_250_eligible']}/{s['scheduled_formation_dates']}" if k == "SP500" else "not applicable"
        lines.append(f"| {label} | {s['daily_joint_coverage_pct']:.3f}% | {s['formation_joint_member_day_coverage_pct']:.3f}% | {s['median_joint_eligible_names']:.0f} | {s['min_joint_eligible_names']} | {gate250} | {'PASS' if s['strict_formation_member_day_gate_pass_90pct'] else 'FAIL'} | {'PASS' if s['formation_date_gate_pass_80pct'] else 'FAIL' if k == 'SP500' else 'not applicable'} |")
    lines += ["", f"**Overall gate: {manifest['overall_gate']}.** The fixed rule is strict formation joint-member-day coverage ≥90% in both universes and at least 80% of all scheduled S&P formation dates with ≥250 jointly eligible names. Daily same-date coverage is shown as a separate diagnostic.", "",
        "## Per-date files and price-data limitation", "",
        "`joint_coverage.csv` has one row per formation date and universe with scheduled PIT members, valid paired ratios at t, complete five-session ratio scores, complete signal-window bar counts, complete forward-window bar counts, jointly eligible names, and whether the calendar windows exist. `joint_daily_coverage.csv` reports daily scheduled members, finite paired ratios, bar presence, and same-date joint counts. Only date and ticker were used for price availability; no price fields or returns were accessed.", "",
        f"The S&P price source retains the documented {len(gaps)} unresolved PIT ticker histories: {', '.join(gaps)}. The fixed gap rule is applied date by date; no missing bar or FINRA pair is imputed, and no issuer is replaced by a survivor. FINRA paired validity is determined by finiteness of the prebuilt paired `short_volume_ratio`; its values are never reported or used in this audit.", "",
        "Rebuild with `python r6_D1/build_joint_coverage.py`. All source inputs are restricted to development dates; this job does not access or inspect holdout data.", ""]
    (OUT / "JOINT_COVERAGE.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"overall_gate": manifest["overall_gate"], "universes": summaries}, indent=2))

if __name__ == "__main__":
    main()
