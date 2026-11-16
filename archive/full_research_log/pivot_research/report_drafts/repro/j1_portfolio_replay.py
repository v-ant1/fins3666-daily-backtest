#!/usr/bin/env python3
"""Independent replay of the frozen J1 Dow portfolio from preregistered rules.

Uses only the staged development price arrays, frozen signal bundle, and saved
J1 result for a path-level comparison. This file intentionally does not import
any project runner or portfolio helper.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

COST = 0.0005
CAP = 0.50
FIRST_FORMATION = "2020-11-27"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def portfolio_path(dates, tickers, roster, opens, closes, signal_rows, kind):
    """Replay one book in daily close-to-close NAV units with next-open trades."""
    n, tmax = closes.shape
    date_to_i = {str(d): i for i, d in enumerate(dates)}
    formations = sorted((date_to_i[d], d) for d in signal_rows)
    first = next(i for i, d in enumerate(dates) if str(d) >= FIRST_FORMATION)
    forms = [(i, d) for i, d in formations if i >= first and i + 1 < tmax]
    if not forms:
        raise ValueError("No scheduled Dow formation dates in the development window")
    # Include the first formation close for the initial EW30 seed. The return
    # series begins at its next-session fill, matching the official date index.
    fi0, _ = forms[0]
    member = roster[:, fi0] & np.isfinite(closes[:, fi0]) & (closes[:, fi0] > 0)
    if not member.any():
        raise ValueError("No valid PIT names for initial EW30 book")
    w = np.zeros(n, dtype=float)
    w[member] = 1.0 / member.sum()
    active_names = member.copy()
    last_close = np.where(np.isfinite(closes[:, fi0]) & (closes[:, fi0] > 0), closes[:, fi0], np.nan)
    last_nav = 1.0
    daily = []
    turns, costs, actives, cap_binds, skipped = [], [], [], [], []
    form_map = {i: d for i, d in forms}
    for day in range(fi0 + 1, tmax):
        # Mark prior-close holdings to today's open; if no open, carry the
        # last valid close (the frozen Dow bundle has no in-window close gaps).
        open_px = opens[:, day]
        valid_open = np.isfinite(open_px) & (open_px > 0)
        open_ret = np.zeros(n, dtype=float)
        can_mark = valid_open & np.isfinite(last_close)
        open_ret[can_mark] = open_px[can_mark] / last_close[can_mark] - 1.0
        # This implementation tracks weights, so apply overnight P&L first.
        overnight = float(np.dot(w, open_ret))
        nav_open = last_nav * (1.0 + overnight)
        w_open = w * (1.0 + open_ret)
        if w_open.sum() > 0:
            w_open /= w_open.sum()
        # Scheduled formation at yesterday's close, fill today at open.
        form_i = day - 1
        trade_cost = 0.0
        turnover = 0.0
        bound = False
        if form_i in form_map:
            form_date = form_map[form_i]
            if kind == "strategy":
                rows = signal_rows[form_date]
                elig = []
                for ticker, row in rows.items():
                    j = tickers.index(ticker)
                    score = row.get("relative_return")
                    if (bool(row.get("relative_return_mask")) and pd.notna(score)
                            and np.isfinite(float(score)) and bool(roster[j, form_i])
                            and valid_open[j]):
                        elig.append((float(score), ticker, j))
                elig.sort(key=lambda x: (x[0], x[1]))
                if len(elig) < 5:
                    skipped.append(form_date)
                    target = w_open.copy()
                    target_names = active_names.copy()
                else:
                    picks = [x[2] for x in elig[:5]]
                    target = np.zeros(n, dtype=float)
                    target[picks] = 0.2
                    target_names = target > 0
            else:
                cohort = roster[:, form_i] & valid_open
                if not cohort.any():
                    target = w_open.copy()
                    target_names = active_names.copy()
                else:
                    target = np.zeros(n, dtype=float)
                    target[cohort] = 1.0 / cohort.sum()
                    target_names = cohort
            delta = target - w_open
            requested = float(np.abs(delta).sum())
            if kind == "strategy" and requested > CAP + 1e-12:
                alpha = CAP / requested
                bound = True
            else:
                alpha = 1.0
            w_trade = w_open + alpha * delta
            turnover = float(np.abs(w_trade - w_open).sum())
            trade_cost = nav_open * turnover * COST
            # Costs are charged against NAV; weights remain the post-trade
            # exposure fractions, so their following market P&L is unchanged.
            w_open = w_trade
            active_names = target_names
            if kind == "strategy":
                actives.append(0.5 * float(np.abs(w_trade - (1.0 / len(tickers))).sum()))
            turns.append(turnover)
            costs.append(trade_cost)
            cap_binds.append(bound)
        # Mark close; missing closes carry last close and produce zero interim
        # return. On resumption, the full close-to-close move is recognized.
        close_px = closes[:, day]
        valid_close = np.isfinite(close_px) & (close_px > 0)
        close_ret = np.zeros(n, dtype=float)
        can_close = valid_close & np.isfinite(last_close)
        close_ret[can_close] = close_px[can_close] / last_close[can_close] - 1.0
        # For names that were validly marked at open, intraday return is close/open.
        # Combining overnight and intraday via shares is equivalent to one close
        # to close return for untraded holdings, and keeps fills at the open.
        intraday_ret = np.zeros(n, dtype=float)
        can_intraday = valid_close & valid_open
        intraday_ret[can_intraday] = close_px[can_intraday] / open_px[can_intraday] - 1.0
        # w_open represents post-trade open weights. Use close/open returns.
        gross_day = (1.0 + overnight) * (1.0 + float(np.dot(w_open, intraday_ret)))
        # Keep cost in daily net return at the fill date; compute nav after
        # open move, transaction cost, then intraday move.
        net_day = ((1.0 + overnight) - (trade_cost / last_nav)) * (1.0 + float(np.dot(w_open, intraday_ret)))
        last_nav *= net_day
        daily.append({"date_index": day, "date": str(dates[day]), "gross": gross_day - 1.0,
                      "net": net_day - 1.0, "turnover": turnover,
                      "cost": trade_cost / max(nav_open, 1e-30), "active_share": actives[-1] if kind == "strategy" and actives else None,
                      "cap_binds": bound})
        # Update prior close levels, preserving last valid observations.
        last_close[valid_close] = close_px[valid_close]
        # Close weights drift from open to close. Normalize; cash is implicitly
        # included as a flat asset if present.
        w = w_open * (1.0 + intraday_ret)
        if w.sum() > 0:
            w /= w.sum()
    return daily, {"turnovers": turns, "costs": costs, "active_shares": actives,
                   "cap_bind_count": int(sum(cap_binds)), "skipped_dates": skipped}


def summarize(series):
    r = np.asarray([x["net"] for x in series], float)
    gross = np.asarray([x["gross"] for x in series], float)
    excess = r
    # Annualization follows 252 daily observations.
    sharpe = float(np.sqrt(252) * r.mean() / r.std(ddof=1)) if r.std(ddof=1) else float("nan")
    return {"net_cumulative_return": float(np.prod(1 + r) - 1),
            "gross_cumulative_return": float(np.prod(1 + gross) - 1),
            "net_sharpe": sharpe,
            "daily_mean_net": float(r.mean()), "daily_sd_net": float(r.std(ddof=1))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()
    root = args.root.resolve()
    data = root / "r6_J1"
    npz_path = data / "J1_PRICES_DEV.npz"
    bundle_path = data / "signal_bundle.parquet"
    result_path = data / "J1_RESULTS.json"
    z = np.load(npz_path, allow_pickle=False)
    dates = z["dow_dates"].astype(str)
    tickers = z["dow_assets"].astype(str).tolist()
    roster, opens, closes = z["dow_roster"], z["dow_adjusted_open"], z["dow_adjusted_close"]
    # Restrict all portfolio operations to the authorized dev window.
    start = int(np.flatnonzero(dates >= FIRST_FORMATION)[0])
    dates, roster, opens, closes = dates, roster, opens, closes
    frame = pd.read_parquet(bundle_path)
    frame = frame[(frame["universe"] == "dow") & (frame["formation_date"].astype(str) >= FIRST_FORMATION)]
    signal_rows = {}
    for d, group in frame.groupby(frame["formation_date"].astype(str), sort=True):
        signal_rows[d] = {str(r.ticker): {"relative_return": r.relative_return,
                          "relative_return_mask": r.relative_return_mask,
                          "peer_count": r.peer_count} for r in group.itertuples(index=False)}
    strategy, s_meta = portfolio_path(dates, tickers, roster, opens, closes, signal_rows, "strategy")
    benchmark, b_meta = portfolio_path(dates, tickers, roster, opens, closes, signal_rows, "benchmark")
    # The books should align exactly by trading date.
    if [x["date_index"] for x in strategy] != [x["date_index"] for x in benchmark]:
        raise AssertionError("Strategy and EW30 dates do not align")
    official = json.loads(result_path.read_text(encoding="utf-8"))["portfolio"]
    off_idx = official["net"]["return_date_indices"]
    off_s = np.asarray(official["net"]["returns"], float)
    off_b = np.asarray(official["ew_net"]["returns"], float)
    dates_idx = np.asarray([x["date_index"] for x in strategy], int)
    if not np.array_equal(dates_idx, np.asarray(off_idx, int)):
        raise AssertionError(f"date indices differ: replay {dates_idx[0]}..{dates_idx[-1]} n={len(dates_idx)}, official {off_idx[0]}..{off_idx[-1]} n={len(off_idx)}")
    s = np.asarray([x["net"] for x in strategy]); b = np.asarray([x["net"] for x in benchmark])
    sg = np.asarray([x["gross"] for x in strategy]); bg = np.asarray([x["gross"] for x in benchmark])
    off_sg = np.asarray(official["gross"]["returns"], float)
    off_bg = np.asarray(official["ew_gross"]["returns"], float)
    ssum, bsum = summarize(strategy), summarize(benchmark)
    # Cumulative net excess means the difference of compounded net wealths.
    excess = ssum["net_cumulative_return"] - bsum["net_cumulative_return"]
    official_excess = float(official["net_cumulative_return"] - official["ew30_net_cumulative_return"])
    out = {"scope": "development replay only; no holdout; no new signal",
           "inputs": {"prices_sha256": sha256(npz_path), "signal_bundle_sha256": sha256(bundle_path),
                      "prereg_sha256": "996b971090be395fffb1e11dff1430bbf581b338637250716607bf6b51cb7698"},
           "strategy": ssum, "ew30": bsum, "net_cumulative_excess_difference": excess,
           "official": {"strategy_net_cumulative_return": official["net_cumulative_return"],
                        "ew30_net_cumulative_return": official["ew30_net_cumulative_return"],
                        "net_cumulative_excess_difference": official_excess,
                        "strategy_net_sharpe": official["net_sharpe"],
                        "ew30_net_sharpe": official["ew30_net_sharpe"]},
           "diff": {"strategy_excess_pp": (excess-official_excess)*100,
                    "strategy_daily_max_abs_pp": float(np.max(np.abs(s-off_s))*100),
                    "strategy_daily_mean_abs_pp": float(np.mean(np.abs(s-off_s))*100),
                    "ew_daily_max_abs_pp": float(np.max(np.abs(b-off_b))*100),
                    "ew_daily_mean_abs_pp": float(np.mean(np.abs(b-off_b))*100),
                    "strategy_gross_daily_mean_abs_pp": float(np.mean(np.abs(sg-off_sg))*100),
                    "ew_gross_daily_mean_abs_pp": float(np.mean(np.abs(bg-off_bg))*100),
                    "strategy_net_return_correlation": float(np.corrcoef(s, off_s)[0, 1]),
                    "ew_net_return_correlation": float(np.corrcoef(b, off_b)[0, 1]),
                    "strategy_sharpe_difference": ssum["net_sharpe"]-official["net_sharpe"],
                    "ew_sharpe_difference": bsum["net_sharpe"]-official["ew30_net_sharpe"]},
           "strategy_turnover": {"mean": float(np.mean(s_meta["turnovers"])),
                                 "max": float(np.max(s_meta["turnovers"])),
                                 "cap_bind_count": s_meta["cap_bind_count"],
                                 "cost_sum": float(np.sum(s_meta["costs"])),
                                 "skipped_dates": s_meta["skipped_dates"]},
           "ew_turnover": {"mean": float(np.mean(b_meta["turnovers"])),
                            "cost_sum": float(np.sum(b_meta["costs"]))},
           "series": {"date_indices": dates_idx.tolist(), "dates": [x["date"] for x in strategy],
                      "strategy_net": s.tolist(), "ew30_net": b.tolist(),
                      "strategy_gross": sg.tolist(), "ew30_gross": bg.tolist(),
                      "official_strategy_net": off_s.tolist(), "official_ew30_net": off_b.tolist()}}
    output = args.output or (root / "report_drafts" / "repro" / "J1_PORTFOLIO_REPLAY.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "series"}, indent=2))
    print(f"Saved daily series: {output}")

if __name__ == "__main__":
    main()
