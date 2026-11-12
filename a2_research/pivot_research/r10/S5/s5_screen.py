#!/usr/bin/env python3
"""One-pass R10 S5 screen using dev-only daily FINRA Reg SHO files."""
import argparse
import csv
import json
import math
from datetime import date
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
START, END = "2020-11-27", "2026-10-30"
COSTS = (0.0005, 0.001, 0.002)
IDS = (
    "S5-01 five-session short-volume-ratio pressure",
    "S5-02 short-volume-ratio acceleration",
    "S5-03 high short-volume flow with volume confirmation",
    "S5-04 extreme-pressure reversal",
)


def nw(x, lag=3):
    x = np.asarray(x, float)
    n = len(x)
    if n < 3:
        return {"mean": float(x.mean()) if n else None,
                "sd": float(x.std(ddof=1)) if n > 1 else None, "se": None, "t": None}
    u = x - x.mean()
    v = np.dot(u, u) / n
    for k in range(1, min(lag, n - 1) + 1):
        v += 2 * (1 - k / (lag + 1)) * np.dot(u[k:], u[:-k]) / n
    se = math.sqrt(max(v, 0) / n)
    return {"mean": float(x.mean()), "sd": float(x.std(ddof=1)), "se": se,
            "t": float(x.mean() / se) if se else None}


def norm_symbol(x):
    return "".join(ch for ch in str(x).upper() if ch.isalnum())


def signal_scores(i, ratio, volume, total, roster):
    """Return four scores for current PIT members; indices are S&P sessions."""
    n = len(roster)
    out = [np.full(n, np.nan) for _ in IDS]
    live = roster[:, i]
    if i < 69:
        return out
    recent5 = slice(i - 4, i + 1)
    prior5 = slice(i - 9, i - 4)
    prior60 = slice(i - 69, i - 9)
    r5 = ratio[:, recent5]
    p5 = ratio[:, prior5]
    v5 = total[:, recent5]
    v60 = total[:, prior60]
    p60 = ratio[:, prior60]
    full5 = np.isfinite(r5).all(axis=1)
    full10 = full5 & np.isfinite(p5).all(axis=1)
    out[0][full5] = np.mean(r5[full5], axis=1)
    out[1][full10] = np.mean(r5[full10], axis=1) - np.mean(p5[full10], axis=1)
    valid60 = full5 & np.isfinite(v5).all(axis=1) & np.isfinite(v60).all(axis=1) & (np.nanmedian(v60, axis=1) > 0)
    out[2][valid60] = np.mean(r5[valid60], axis=1) * (
        np.mean(v5[valid60], axis=1) / np.median(v60[valid60], axis=1))
    validrev = full10 & np.isfinite(p60).all(axis=1)
    for a in np.flatnonzero(validrev):
        if np.mean(p5[a]) >= np.quantile(p60[a], .8):
            out[3][a] = np.mean(p5[a]) - np.mean(r5[a])
    for x in out:
        x[~live] = np.nan
    return out


def evaluate(panel):
    dates, close, roster, assets = panel["dates"], panel["close"], panel["roster"], panel["assets"]
    ratio, volume, total = panel["short_ratio"], panel["short_volume"], panel["total_volume"]
    per = pd.PeriodIndex(dates, freq="D").asfreq("M")
    ends = pd.Series(np.arange(len(dates))).groupby(per).max().to_dict()
    forms = [int(ends[x]) for x in sorted(ends)]
    rec = {x: [] for x in IDS}
    prior = {x: {} for x in IDS}
    coverage = []
    signal_coverage = {x: [] for x in IDS}
    for i, j in zip(forms[:-1], forms[1:]):
        if dates[i] < START or dates[j] > END:
            continue
        live = np.flatnonzero(roster[:, i])
        priced_bench = live[np.isfinite(close[live, i]) & np.isfinite(close[live, j]) &
                            (close[live, i] > 0) & (close[live, j] > 0)]
        if not len(priced_bench):
            continue
        bench = float(np.mean(close[priced_bench, j] / close[priced_bench, i] - 1))
        coverage.append(len(priced_bench) / max(int(roster[:, i].sum()), 1))
        scores = signal_scores(i, ratio, volume, total, roster)
        for z, name in enumerate(IDS):
            eligible = np.flatnonzero(np.isfinite(scores[z]) & roster[:, i])
            signal_coverage[name].append(len(eligible) / max(int(roster[:, i].sum()), 1))
            if len(eligible) < 100:
                continue
            ordered = sorted(eligible.tolist(), key=lambda q: (-float(scores[z][q]), str(assets[q])))
            chosen = ordered[:max(1, math.ceil(.2 * len(ordered)))]
            priced = [q for q in chosen if np.isfinite(close[q, i]) and np.isfinite(close[q, j]) and
                      close[q, i] > 0 and close[q, j] > 0]
            if not priced:
                continue
            gross = float(np.mean(close[priced, j] / close[priced, i] - 1))
            w = {str(assets[q]): 1 / len(priced) for q in priced}
            old = prior[name]
            turnover = .5 * sum(abs(w.get(x, 0) - old.get(x, 0)) for x in set(w) | set(old))
            if not old:
                turnover = 1.
            abs_traded = sum(abs(w.get(x, 0) - old.get(x, 0)) for x in set(w) | set(old))
            gross_excess = gross - bench
            rec[name].append({
                "formation_date": str(dates[i]), "exit_date": str(dates[j]),
                "gross": gross, "benchmark": bench, "gross_excess": gross_excess,
                "one_way_turnover": turnover, "absolute_weight_change": abs_traded,
                "eligible": len(eligible), "selected": len(chosen), "priced": len(priced),
                "net_excess_by_cost": {str(c): gross_excess - c * abs_traded for c in COSTS},
            })
            prior[name] = w

    out = {"period": {"start": START, "end": END},
           "benchmark_coverage_mean": float(np.mean(coverage)) if coverage else None,
           "signal_coverage_mean": {k: float(np.mean(v)) if v else None for k, v in signal_coverage.items()},
           "ideas": {}}
    nd, z = NormalDist(), 1.6448536269514722
    for name in IDS:
        rows = rec[name]
        x = np.array([q["net_excess_by_cost"]["0.001"] for q in rows])
        grossx = np.array([q["gross_excess"] for q in rows])
        st = nw(x)
        years = {}
        for y in sorted({q["formation_date"][:4] for q in rows}):
            vals = [q["net_excess_by_cost"]["0.001"] for q in rows if q["formation_date"].startswith(y)]
            years[y] = {"n": len(vals), "mean_net_excess": float(np.mean(vals)), "positive": bool(np.mean(vals) > 0)}
        ny = len(years)
        nh = max(1, round(len(x) / max(1, ny) * 6))
        sd = st["sd"]
        plan_se = sd / math.sqrt(nh) if sd is not None else None
        mde = 2.4865 * plan_se if plan_se is not None else None
        pp = nd.cdf(.5 * st["mean"] / plan_se - z) if plan_se and st["mean"] is not None else None
        out["ideas"][name] = {
            "n_months": len(x), "gross_excess_mean": float(grossx.mean()) if len(x) else None,
            "net_excess_mean": st["mean"], "nw_lag3_t": st["t"], "nw_se": st["se"],
            "sample_sd_net_excess": sd, "mean_one_way_turnover": float(np.mean([q["one_way_turnover"] for q in rows])) if rows else None,
            "mean_cost_bps": float(np.mean([q["absolute_weight_change"] * .001 for q in rows]) * 10000) if rows else None,
            "cost_share_abs_gross_excess": abs(float(np.mean([q["absolute_weight_change"] * .001 for q in rows])) / float(grossx.mean())) if rows and grossx.mean() != 0 else None,
            "yearly": years, "positive_years": sum(v["positive"] for v in years.values()), "observed_years": ny,
            "holdout_2010_2015": {"N_projected": nh, "family": 1, "one_sided_alpha": .05, "power": .8,
                                   "MDE": mde, "haircut_pass_probability": pp},
            "net_excess_cost_sensitivity": {str(c): float(np.mean([q["net_excess_by_cost"][str(c)] for q in rows])) for c in COSTS} if rows else {},
            "mean_signal_eligible": float(np.mean([q["eligible"] for q in rows])) if rows else None,
            "mean_selected": float(np.mean([q["selected"] for q in rows])) if rows else None,
            "mean_priced": float(np.mean([q["priced"] for q in rows])) if rows else None,
            "go": bool(st["mean"] is not None and st["mean"] > 0 and st["t"] is not None and st["t"] >= 2 and pp is not None and pp >= .3),
            "cohorts": rows,
        }
    return out


def synthetic_panel():
    d = pd.bdate_range(START, periods=1550).strftime("%Y-%m-%d").to_numpy()
    n = 650
    rng = np.random.default_rng(20261112)
    market = rng.normal(.0003, .008, len(d))
    ret = market[None, :] + rng.normal(.0001, .012, (n, len(d)))
    close = np.empty_like(ret)
    close[:, 0] = np.linspace(20, 80, n)
    for k in range(1, len(d)):
        close[:, k] = close[:, k - 1] * (1 + ret[:, k])
    trend = np.linspace(.20, .78, len(d))[None, :]
    short_ratio = np.clip(trend + rng.normal(0, .06, (n, len(d))), .05, .95)
    total = rng.lognormal(13, .6, (n, len(d)))
    short_volume = short_ratio * total
    roster = np.ones_like(close, dtype=bool)
    return {"dates": d, "close": close, "roster": roster,
            "assets": np.array([f"T{k:03d}" for k in range(n)]),
            "short_ratio": short_ratio, "short_volume": short_volume, "total_volume": total}


def load_dev_prices():
    # Filter the date axis first and only then slice the authorized price/roster fields.
    with np.load(ROOT / "r9/data/J2_DEV_FROM_20201127.npz", allow_pickle=False) as z:
        d0 = z["sp500_dates"].astype(str)
        keep = (d0 >= START) & (d0 <= END)
        dates = d0[keep]
        close = z["sp500_adjusted_close"][:, keep].astype(float)
        roster = z["sp500_roster"][:, keep].astype(bool)
        assets = z["sp500_assets"].astype(str)
    if not len(dates) or dates[0] < START or dates[-1] > END:
        raise ValueError("development date guard failed")
    return dates, close, roster, assets


def load_dev_finra(dates, assets, roster):
    # Select raw daily files by filename date before opening any contents. This avoids
    # touching even pre-boundary FINRA signal values.
    raw = ROOT / "r6_data/finra_regsho/raw"
    files = sorted(p for p in raw.glob("CNMSshvol????????.txt")
                   if START.replace("-", "") <= p.stem[-8:] <= END.replace("-", ""))
    if not files:
        raise ValueError("no staged FINRA development files")
    aliases = pd.read_csv(ROOT / "r6_data/finra_regsho/ticker_aliases.csv", dtype=str).fillna("")
    asset_index = {norm_symbol(x): i for i, x in enumerate(assets)}
    alias_index = {}
    for row in aliases.itertuples(index=False):
        alias_index.setdefault(norm_symbol(row.FINRA_symbol), []).append(
            (row.from_inclusive, row.to_exclusive, norm_symbol(row.roster_ticker)))
    date_index = {str(d): i for i, d in enumerate(dates)}
    shape = (len(assets), len(dates))
    short = np.full(shape, np.nan)
    total = np.full(shape, np.nan)
    matched_dates = set()
    for path in files:
        d = f"{path.stem[-8:-4]}-{path.stem[-4:-2]}-{path.stem[-2:]}"
        if d not in date_index:
            continue
        k = date_index[d]
        agg = {}
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter="|")
            for row in reader:
                sym = norm_symbol(row["Symbol"])
                ticker = sym
                for lo, hi, mapped in alias_index.get(sym, []):
                    if lo <= d < hi:
                        ticker = mapped
                        break
                ai = asset_index.get(ticker)
                if ai is None or not roster[ai, k]:
                    continue
                s = float(row["ShortVolume"] or 0)
                t = float(row["TotalVolume"] or 0)
                old_s, old_t = agg.get(ai, (0, 0))
                agg[ai] = (old_s + s, old_t + t)
        for ai, (s, t) in agg.items():
            if t > 0:
                short[ai, k] = s
                total[ai, k] = t
        if agg:
            matched_dates.add(d)
    ratio = np.divide(short, total, out=np.full(shape, np.nan), where=np.isfinite(total) & (total > 0))
    return {"short_ratio": ratio, "short_volume": short, "total_volume": total,
            "source_files": len(files), "matched_source_dates": len(matched_dates)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic-only", action="store_true")
    ap.add_argument("--run-dev", action="store_true")
    args = ap.parse_args()
    if args.synthetic_only:
        result = evaluate(synthetic_panel())
        assert set(result["ideas"]) == set(IDS)
        assert all(len(v["cohorts"]) == v["n_months"] for v in result["ideas"].values())
        assert all(result["ideas"][k]["n_months"] > 0 for k in IDS[:3])
        assert result["ideas"][IDS[3]]["n_months"] == 0  # sparse frozen extreme filter is handled explicitly
        assert all(v["holdout_2010_2015"]["N_projected"] > 0 for v in result["ideas"].values())
        print(json.dumps({"status": "PASS", "synthetic_only": True, "ideas": len(IDS),
                          "observations": {k: v["n_months"] for k, v in result["ideas"].items()},
                          "outcomes_created": False}, indent=2))
        return
    if not args.run_dev:
        raise SystemExit("choose --synthetic-only or the single --run-dev execution")
    dates, close, roster, assets = load_dev_prices()
    finra = load_dev_finra(dates, assets, roster)
    panel = {"dates": dates, "close": close, "roster": roster, "assets": assets, **finra}
    result = evaluate(panel)
    result["finra_source"] = {"restricted_start": START, "restricted_end": END,
                              "daily_source_files": finra["source_files"],
                              "matched_source_dates": finra["matched_source_dates"]}
    dest = ROOT / "r10/S5/DEV_RESULT.json"
    dest.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"source": result["finra_source"],
                      "ideas": {k: {q: v for q, v in r.items() if q != "cohorts"}
                                for k, r in result["ideas"].items()}}, indent=2))


if __name__ == "__main__":
    main()
