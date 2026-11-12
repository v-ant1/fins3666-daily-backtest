"""Logged L-D1-E01 diagnostic; reads only development values dated >= 2020-11-27."""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
CUTOFF = pd.Timestamp("2020-11-27")
END = pd.Timestamp("2026-10-30")
OUT = ROOT / "report_drafts" / "repro" / "D1_DIAGNOSTIC_OUTPUT.json"


def load_post_cutoff_finra():
    path = ROOT / "r6_data" / "finra_regsho" / "signal_panel.csv.gz"
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        header = next(f).rstrip("\n").split(",")
        ix = {name: header.index(name) for name in ("date", "universe", "ticker", "short_volume_ratio")}
        for line in f:
            date_text, sep, rest = line.partition(",")
            if not sep or date_text < "2020-11-27":
                continue
            if date_text > "2026-10-30":
                continue
            fields = (date_text + "," + rest).rstrip("\r\n").split(",")
            if fields[ix["universe"]] != "SP500":
                continue
            ratio = fields[ix["short_volume_ratio"]]
            rows.append((pd.Timestamp(date_text), fields[ix["ticker"]],
                         float(ratio) if ratio and ratio.lower() != "nan" else np.nan))
    df = pd.DataFrame(rows, columns=["date", "ticker", "ratio"])
    if df.empty or df.date.min() < CUTOFF or df.date.max() > END:
        raise RuntimeError("FINRA date boundary check failed")
    if df.duplicated(["date", "ticker"]).any():
        raise RuntimeError("duplicate FINRA date/ticker rows")
    return df


def load_post_cutoff_prices():
    path = ROOT / "r6_data" / "sp500_ohlcv_dev_gapfilled.parquet"
    df = pd.read_parquet(path, columns=["date", "ticker", "open", "close", "adj_close"],
                         filters=[("date", ">=", CUTOFF), ("date", "<=", END)])
    df["date"] = pd.to_datetime(df.date).dt.normalize()
    if len(df) and (df.date.min() < CUTOFF or df.date.max() > END):
        raise RuntimeError("price date boundary check failed")
    op = df.open.to_numpy(float)
    close = df.close.to_numpy(float)
    adj = df.adj_close.to_numpy(float)
    ok = np.isfinite(op) & (op > 0) & np.isfinite(close) & (close > 0) & np.isfinite(adj) & (adj > 0)
    df["adj_open"] = np.where(ok, op * adj / close, np.nan)
    df["adj_close"] = np.where(np.isfinite(adj) & (adj > 0), adj, np.nan)
    return df[["date", "ticker", "adj_open", "adj_close"]]


def yearly_ic(panel, score_col, ret_col, mask_col, group_col="year"):
    out = []
    for y, part in panel.groupby(group_col, sort=True):
        vals = part.loc[part[mask_col], [score_col, ret_col]].dropna()
        ic = spearmanr(vals[score_col], vals[ret_col]).statistic if len(vals) >= 3 else np.nan
        out.append({"year": int(y), "date_count": int(part.date.nunique()),
                    "eligible_name_date_pairs": int(len(vals)), "mean_daily_ic": float(part.loc[part[mask_col], "ic"].mean()) if "ic" in part else None,
                    "pooled_spearman": float(ic) if np.isfinite(ic) else None,
                    "mean_names_per_date": float(part.loc[part[mask_col]].groupby("date").size().mean()) if part[mask_col].any() else 0.0})
    return out


def main():
    finra = load_post_cutoff_finra()
    prices = load_post_cutoff_prices()
    sessions = pd.DatetimeIndex(sorted(finra.date.unique()))
    ratio = finra.pivot(index="ticker", columns="date", values="ratio").reindex(columns=sessions)
    # Form the registered negative five-session mean. The first usable score is
    # after five entirely post-cutoff ratios, so no warm-up value is read.
    scores = -ratio.T.rolling(5, min_periods=5).mean().T
    scores.iloc[:, :4] = np.nan
    pvt = prices.pivot(index="ticker", columns="date", values="adj_close").reindex(columns=sessions)
    opn = prices.pivot(index="ticker", columns="date", values="adj_open").reindex(columns=sessions)
    roster = pd.read_csv(ROOT / "r6_data" / "sp500_pit_roster.csv")
    roster["effective_from"] = pd.to_datetime(roster.effective_from)
    roster["effective_to_exclusive"] = pd.to_datetime(roster.effective_to_exclusive)
    rmask = pd.DataFrame(False, index=scores.index, columns=sessions)
    for r in roster.itertuples(index=False):
        if r.ticker in rmask.index:
            rmask.loc[r.ticker, (sessions >= r.effective_from) & (sessions < r.effective_to_exclusive)] = True
    scheduled = sessions[::5]
    # J1 saved score rows are used as-is; all rows read here are date filtered.
    j1 = pd.read_parquet(ROOT / "r6_J1" / "signal_bundle.parquet",
                         columns=["universe", "formation_date", "ticker", "relative_return"],
                         filters=[("formation_date", ">=", CUTOFF), ("formation_date", "<=", END)])
    j1 = j1[(j1.universe == "sp500") & j1.relative_return.notna()].copy()
    j1["formation_date"] = pd.to_datetime(j1.formation_date).dt.normalize()
    j1 = j1.set_index(["ticker", "formation_date"])["relative_return"]

    horizons = [1, 2, 5, 10, 20]
    yearly = {}
    corr_daily = {"j1": [], "j2": []}
    corr_pairs = {"j1": [], "j2": []}
    for h in horizons:
        records = []
        for d in scheduled:
            ti = sessions.get_loc(d)
            if ti < 4 or ti + h + 1 >= len(sessions):
                continue
            # Entry t+2 open, horizon h sessions through t+h+1 close.
            en, ex = sessions[ti + 2], sessions[ti + h + 1]
            s = scores[d]
            entry = opn[en]
            exitp = pvt[ex]
            ret = exitp / entry - 1.0
            mask = rmask[d] & s.notna() & ret.notna()
            names = mask.index[mask]
            if len(names) < 3:
                continue
            ic = spearmanr(s.loc[names], ret.loc[names]).statistic
            for name in names:
                records.append({"year": int(d.year), "date": d, "ticker": name,
                                "score": float(s.loc[name]), "ret": float(ret.loc[name]), "ic": float(ic)})
        frame = pd.DataFrame(records)
        if frame.empty:
            yearly[str(h)] = []
            continue
        date_summary = frame.groupby(["year", "date"]).agg(ic=("ic", "first"), n=("ticker", "size")).reset_index()
        yearly[str(h)] = [{"year": int(y), "dates": int(len(g)), "mean_date_ic": float(g.ic.mean()),
                           "median_date_ic": float(g.ic.median()), "positive_date_fraction": float((g.ic > 0).mean()),
                           "mean_names": float(g.n.mean()), "min_names": int(g.n.min())}
                          for y, g in date_summary.groupby("year", sort=True)]
        if h == 5:
            j2_vals = []
            for row in frame[["date", "ticker", "score"]].itertuples(index=False):
                jv = j1.get((row.ticker, row.date), np.nan)
                if pd.notna(jv):
                    corr_pairs["j1"].append((row.date, row.ticker, row.score, float(jv)))
                    j2_vals.append((row.date, row.ticker, row.score, float(jv)))
            # J2 signal is the four-formation arithmetic mean of fixed J1 scores.
            bykey = {(d, t): v for d, t, _, v in j2_vals}
            for d, t, s, jv in j2_vals:
                ix = scheduled.get_loc(d)
                prior = [bykey.get((scheduled[k], t), np.nan) for k in range(max(0, ix-3), ix+1)]
                if len(prior) == 4 and np.isfinite(prior).all():
                    corr_pairs["j2"].append((d, t, s, float(np.mean(prior))))

    for key, pairs in corr_pairs.items():
        if not pairs:
            continue
        cp = pd.DataFrame(pairs, columns=["date", "ticker", "d1", key])
        cp["d1_rank"] = cp.groupby("date").d1.rank(pct=True)
        cp["other_rank"] = cp.groupby("date")[key].rank(pct=True)
        daily = cp.groupby("date").apply(lambda x: spearmanr(x.d1, x[key]).statistic, include_groups=False)
        corr_daily[key] = [{"date": d.strftime("%Y-%m-%d"), "rho": float(v)} for d, v in daily.items() if np.isfinite(v)]
        corr_pairs[key] = {"date_count": int(cp.date.nunique()), "pair_count": int(len(cp)),
                           "pooled_rank_correlation": float(spearmanr(cp.d1_rank, cp.other_rank).statistic),
                           "mean_date_rank_correlation": float(np.mean([x["rho"] for x in corr_daily[key]])),
                           "median_date_rank_correlation": float(np.median([x["rho"] for x in corr_daily[key]]))}

    result = {"source": "saved FINRA ratio panel and adjusted price panel; both read only from 2020-11-27 onward",
              "signal_start": "2020-12-04 (five fully post-cutoff ratios required)",
              "finra_dates": [finra.date.min().strftime("%Y-%m-%d"), finra.date.max().strftime("%Y-%m-%d")],
              "price_dates": [prices.date.min().strftime("%Y-%m-%d"), prices.date.max().strftime("%Y-%m-%d")],
              "formations": [d.strftime("%Y-%m-%d") for d in scheduled],
              "horizons_sessions_after_t_plus_2_open": yearly,
              "signal_correlations": corr_pairs}
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "formations"}, indent=2))


if __name__ == "__main__":
    main()
