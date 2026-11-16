#!/usr/bin/env python3
"""Development-only replay of the pre-logged R9 J2 portfolio variants.

Portfolio mechanics are adapted from report_drafts/repro/j1_portfolio_replay.py.
The fixed J1 score is not recomputed or changed. This runner loads only the
staged J1 development price panel and score bundle, filters formation rows to
the registered development window, and never reads any holdout path.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, norm, skew

FIRST_FORMATION = "2020-11-27"
LAST_FORMATION = "2026-10-30"
COST_RATE = 0.0005
BOOTSTRAP_DRAWS = 5000
BOOTSTRAP_SEED = 20261111
BLOCK_LENGTH = 10
R6_TRIAL_COUNT = 3  # frozen J1_RESULTS.json portfolio.trial_count
R9_VARIANT_COUNT = 12
FULL_TRIAL_COUNT = R6_TRIAL_COUNT + R9_VARIANT_COUNT


VARIANTS = [
    {"id": "R9-V0", "kind": "j1_cap", "k": 5},
    {"id": "R9-V1", "kind": "band", "k": 5, "band": 0.02},
    {"id": "R9-V2", "kind": "buffer", "k": 5, "buffer": 8},
    {"id": "R9-V3", "kind": "smooth", "k": 5, "window": 2},
    {"id": "R9-V4", "kind": "smooth", "k": 5, "window": 3},
    {"id": "R9-V5", "kind": "smooth", "k": 5, "window": 4},
    {"id": "R9-V6", "kind": "biweekly", "k": 5},
    {"id": "R9-V7", "kind": "equal", "k": 8},
    {"id": "R9-V8", "kind": "equal", "k": 10},
    {"id": "R9-V9", "kind": "inverse_vol", "k": 5},
    {"id": "R9-V10", "kind": "partial", "k": 5, "fraction": 0.50},
    {"id": "R9-V11", "kind": "partial", "k": 5, "fraction": 0.75},
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def dsr(returns: np.ndarray, trial_count: int) -> float:
    x = np.asarray(returns, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 3:
        return float("nan")
    sr = float(x.mean() / x.std(ddof=1)) if x.std(ddof=1) else 0.0
    if trial_count == 1:
        sr_star = 0.0
    else:
        euler = 0.5772156649015329
        sr_star = ((1 - euler) * norm.ppf(1 - 1 / trial_count)
                   + euler * norm.ppf(1 - 1 / (trial_count * math.e)))
    sk = float(skew(x, bias=False))
    ku = float(kurtosis(x, fisher=False, bias=False))
    denom = math.sqrt(max(1 - sk * sr + (ku - 1) * sr * sr / 4, 1e-12))
    return float(norm.cdf((sr - sr_star) * math.sqrt(n - 1) / denom))


def bootstrap_p(strategy: np.ndarray, benchmark: np.ndarray) -> float:
    d = np.asarray(strategy, float) - np.asarray(benchmark, float)
    d = d[np.isfinite(d)]
    observed = float(d.mean())
    null = d - observed
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    n = len(null)
    blocks = int(math.ceil(n / BLOCK_LENGTH))
    offsets = np.arange(BLOCK_LENGTH)
    draws = np.empty(BOOTSTRAP_DRAWS)
    for j in range(BOOTSTRAP_DRAWS):
        starts = rng.integers(0, n, size=blocks)
        ix = ((starts[:, None] + offsets) % n).ravel()[:n]
        draws[j] = null[ix].mean()
    return float((1 + np.sum(draws >= observed)) / (BOOTSTRAP_DRAWS + 1))


def target_for(variant, form_date, form_i, eligible, scores_by_date, tickers,
               ticker_to_i, closes, history_dates, old_weights, old_names):
    k = variant["k"]
    score_rows = scores_by_date[form_date]
    eligible_rows = []
    for ticker, row in score_rows.items():
        if ticker not in tickers:
            continue
        j = ticker_to_i[ticker]
        score = row.get("relative_return")
        if (not bool(row.get("relative_return_mask")) or pd.isna(score)
                or not np.isfinite(float(score)) or not eligible[j]):
            continue
        value = float(score)
        if variant["kind"] == "smooth":
            window = variant["window"]
            pos = history_dates.index(form_date)
            if pos + 1 < window:
                continue
            vals = []
            valid = True
            for prev_date in history_dates[pos + 1 - window:pos + 1]:
                prev = scores_by_date.get(prev_date, {}).get(ticker)
                if (prev is None or not bool(prev.get("relative_return_mask"))
                        or pd.isna(prev.get("relative_return"))
                        or not np.isfinite(float(prev.get("relative_return")))):
                    valid = False
                    break
                vals.append(float(prev["relative_return"]))
            if not valid:
                continue
            value = float(np.mean(vals))
        eligible_rows.append((value, ticker, j))
    eligible_rows.sort(key=lambda x: (x[0], x[1]))
    if len(eligible_rows) < k:
        return None, old_names

    if variant["kind"] == "buffer":
        rank = {j: n + 1 for n, (_, _, j) in enumerate(eligible_rows)}
        kept = [j for j in np.flatnonzero(old_names) if rank.get(int(j), 10**9) <= variant["buffer"]]
        picks = kept[:k]
        for _, _, j in eligible_rows:
            if len(picks) >= k:
                break
            if j not in picks:
                picks.append(j)
    else:
        picks = [j for _, _, j in eligible_rows[:k]]

    target = np.zeros_like(old_weights)
    if variant["kind"] == "inverse_vol":
        inv = []
        for j in picks:
            px = closes[j, max(0, form_i - 20):form_i + 1]
            valid_px = px[np.isfinite(px) & (px > 0)]
            if len(valid_px) < 21:
                continue
            ret = valid_px[1:] / valid_px[:-1] - 1
            vol = float(np.std(ret, ddof=1)) if len(ret) >= 2 else float("nan")
            if not np.isfinite(vol) or vol <= 0:
                continue
            inv.append((j, 1.0 / vol))
        if len(inv) < k:
            return None, old_names
        weights = {j: v / sum(val for _, val in inv) for j, v in inv}
        capped = set()
        while True:
            over = [j for j, v in weights.items() if j not in capped and v > 0.40]
            if not over:
                break
            for j in over:
                weights[j] = 0.40
                capped.add(j)
            remaining = 1.0 - sum(weights[j] for j in capped)
            free = [j for j in weights if j not in capped]
            denom = sum(1.0 / next(v for jj, v in inv if jj == j) for j in free)
            for j in free:
                raw = next(v for jj, v in inv if jj == j)
                weights[j] = remaining * raw / sum(next(v for jj, v in inv if jj == q) for q in free)
            if not free or denom == 0:
                break
        for j, weight in weights.items():
            target[j] = weight
    else:
        target[picks] = 1.0 / k

    if variant["kind"] == "band":
        held = [j for j in picks if abs(target[j] - old_weights[j]) < variant["band"]]
        for j in held:
            target[j] = old_weights[j]
        fill = [j for j in picks if j not in held]
        remaining = 1.0 - float(target.sum())
        if fill:
            for j in fill:
                target[j] = remaining / len(fill)
    return target, np.isfinite(target) & (target > 1e-12)


def simulate(variant, dates, tickers, ticker_to_i, roster, opens, closes,
             scores_by_date, history_dates, common_start_date):
    date_to_i = {str(d): i for i, d in enumerate(dates)}
    forms = sorted((date_to_i[d], d) for d in scores_by_date
                   if d in date_to_i and FIRST_FORMATION <= d <= LAST_FORMATION)
    if not forms:
        raise ValueError("No development formations available")
    first_i, _ = forms[0]
    # Only development-period columns are used in all portfolio calculations.
    dev_first = next((i for i, d in enumerate(dates) if str(d) >= FIRST_FORMATION), None)
    if dev_first is None:
        raise ValueError("Development start date absent from price panel")
    forms = [(i, d) for i, d in forms if d >= common_start_date
             and i >= dev_first and i + 1 < len(dates)]
    if not forms:
        raise ValueError("No eligible development formations")
    first_i, _ = forms[0]
    member = roster[:, first_i] & np.isfinite(closes[:, first_i]) & (closes[:, first_i] > 0)
    if not member.any():
        raise ValueError("No PIT Dow names for initial EW30 book")
    w = np.zeros(len(tickers), float)
    w[member] = 1.0 / int(member.sum())
    active_names = member.copy()
    last_close = closes[:, first_i].copy()
    last_close[~(np.isfinite(last_close) & (last_close > 0))] = np.nan
    last_nav = 1.0
    nav = 1.0
    daily = []
    turnovers, active_shares, cost_values = [], [], []
    form_map = {i: d for i, d in forms}
    rebalance_count = 0
    for day in range(first_i + 1, len(dates)):
        open_px = opens[:, day]
        valid_open = np.isfinite(open_px) & (open_px > 0)
        overnight_ret = np.zeros(len(tickers), float)
        can_mark = valid_open & np.isfinite(last_close)
        overnight_ret[can_mark] = open_px[can_mark] / last_close[can_mark] - 1
        overnight = float(np.dot(w, overnight_ret))
        nav_open = nav * (1 + overnight)
        w_open = w * (1 + overnight_ret)
        if w_open.sum() > 0:
            w_open /= w_open.sum()
        cost_fraction = 0.0
        turnover = 0.0
        form_i = day - 1
        form_date = form_map.get(form_i)
        should_trade = form_date is not None
        if should_trade and variant["kind"] == "biweekly":
            should_trade = rebalance_count % 2 == 0
        if form_date is not None:
            rebalance_count += 1
        if should_trade:
            eligible = roster[:, form_i] & valid_open
            if variant["kind"] == "benchmark":
                target = np.zeros_like(w_open)
                if eligible.any():
                    target[eligible] = 1.0 / int(eligible.sum())
                target_names = eligible.copy()
            else:
                target, target_names = target_for(
                    variant, form_date, form_i, eligible, scores_by_date, tickers,
                    ticker_to_i, closes, history_dates, w_open, active_names)
            if target is not None:
                if variant["kind"] == "j1_cap":
                    requested = float(np.abs(target - w_open).sum())
                    if requested > 0.50:
                        target = w_open + (0.50 / requested) * (target - w_open)
                if variant["kind"] == "partial":
                    fraction = variant["fraction"]
                    target = w_open + fraction * (target - w_open)
                delta = target - w_open
                turnover = float(np.abs(delta).sum())
                cost_fraction = turnover * COST_RATE
                w_open = target
                active_names = target_names
            else:
                target_names = active_names.copy()
            # Active share relative to the same-date PIT EW30 cohort.
            cohort = roster[:, form_i] & valid_open
            bench_w = np.zeros(len(tickers), float)
            if cohort.any():
                bench_w[cohort] = 1.0 / int(cohort.sum())
            active_shares.append(0.5 * float(np.abs(w_open - bench_w).sum()))
            turnovers.append(turnover)
            cost_values.append(nav_open * cost_fraction)
        close_px = closes[:, day]
        valid_close = np.isfinite(close_px) & (close_px > 0)
        intraday = np.zeros(len(tickers), float)
        can_intraday = valid_close & valid_open
        intraday[can_intraday] = close_px[can_intraday] / open_px[can_intraday] - 1
        gross_return = (1 + overnight) * (1 + float(np.dot(w_open, intraday))) - 1
        net_return = ((1 + overnight) - cost_fraction) * (1 + float(np.dot(w_open, intraday))) - 1
        daily.append({"date": str(dates[day]), "gross": gross_return, "net": net_return,
                      "turnover": turnover, "cost_fraction": cost_fraction})
        nav *= 1 + net_return
        last_nav = nav
        last_close[valid_close] = close_px[valid_close]
        w = w_open * (1 + intraday)
        if w.sum() > 0:
            w /= w.sum()
    return daily, {"turnover": turnovers, "active_share": active_shares,
                   "cost_values": cost_values}


def summary(daily):
    net = np.asarray([x["net"] for x in daily], float)
    gross = np.asarray([x["gross"] for x in daily], float)
    return {"net": net, "gross": gross,
            "net_cumulative": float(np.prod(1 + net) - 1),
            "gross_cumulative": float(np.prod(1 + gross) - 1),
            "net_sharpe": float(np.sqrt(252) * net.mean() / net.std(ddof=1)),
            "dsr": dsr(net, FULL_TRIAL_COUNT)}


def main():
    root = Path(__file__).resolve().parents[1]
    data = root / "r6_J1"
    npz_path = root / "r9" / "data" / "J2_DEV_FROM_20201127.npz"
    bundle_path = data / "signal_bundle.parquet"
    result_path = data / "J1_RESULTS.json"
    # Confirm the pre-registered R6 count from the saved result before any run.
    j1_results = json.loads(result_path.read_text(encoding="utf-8"))
    r6_trials = int(j1_results["portfolio"]["trial_count"])
    if r6_trials != R6_TRIAL_COUNT:
        raise ValueError(f"R6 trial count changed: expected {R6_TRIAL_COUNT}, got {r6_trials}")
    z = np.load(npz_path, allow_pickle=False)
    dates = z["dow_dates"].astype(str)
    if dates[0] != FIRST_FORMATION or dates[-1] != LAST_FORMATION:
        raise ValueError(f"Trimmed development input bounds mismatch: {dates[0]}..{dates[-1]}")
    tickers = z["dow_assets"].astype(str).tolist()
    ticker_to_i = {ticker: i for i, ticker in enumerate(tickers)}
    roster = z["dow_roster"]
    opens = z["dow_adjusted_open"]
    closes = z["dow_adjusted_close"]
    frame = pd.read_parquet(bundle_path)
    frame = frame[(frame["universe"] == "dow")
                  & (frame["formation_date"].astype(str) >= FIRST_FORMATION)
                  & (frame["formation_date"].astype(str) <= LAST_FORMATION)]
    score_rows = {}
    for d, group in frame.groupby(frame["formation_date"].astype(str), sort=True):
        score_rows[d] = {str(r.ticker): {
            "relative_return": r.relative_return,
            "relative_return_mask": r.relative_return_mask,
        } for r in group.itertuples(index=False)}
    history_dates = sorted(score_rows)
    # Input-only scan: choose the first formation where all variants have
    # complete registered lookback and enough eligible names for their target.
    common_start_date = None
    zeros = np.zeros(len(tickers), float)
    no_names = np.zeros(len(tickers), bool)
    for d in history_dates:
        form_i = int(np.flatnonzero(dates == d)[0]) if np.any(dates == d) else -1
        if form_i < 0 or form_i + 1 >= len(dates):
            continue
        valid_open = np.isfinite(opens[:, form_i + 1]) & (opens[:, form_i + 1] > 0)
        eligible = roster[:, form_i] & valid_open
        all_valid = True
        for variant in VARIANTS:
            target, _ = target_for(variant, d, form_i, eligible, score_rows,
                                   tickers, ticker_to_i, closes, history_dates,
                                   zeros, no_names)
            if target is None:
                all_valid = False
                break
        if all_valid:
            common_start_date = d
            break
    if common_start_date is None:
        raise ValueError("No common formation date with complete targets for all variants")
    benchmark_daily, benchmark_meta = simulate(
        {"id": "PIT-EW30", "kind": "benchmark", "k": len(tickers)},
        dates, tickers, ticker_to_i, roster, opens, closes, score_rows,
        history_dates, common_start_date)
    benchmark = summary(benchmark_daily)
    rows = []
    for variant in VARIANTS:
        daily, meta = simulate(variant, dates, tickers, ticker_to_i, roster,
                               opens, closes, score_rows, history_dates,
                               common_start_date)
        if [x["date"] for x in daily] != [x["date"] for x in benchmark_daily]:
            raise AssertionError(f"Date alignment failure for {variant['id']}")
        s = summary(daily)
        net_excess = s["net_cumulative"] - benchmark["net_cumulative"]
        gross_edge = s["gross_cumulative"] - benchmark["gross_cumulative"]
        total_cost = float(sum(meta["cost_values"]))
        ratio = total_cost / gross_edge if gross_edge > 0 else None
        sharpe_difference = s["net_sharpe"] - benchmark["net_sharpe"]
        rows.append({
            "id": variant["id"], "rules": variant,
            "net_excess_return": net_excess,
            "strategy_net_cumulative_return": s["net_cumulative"],
            "ew30_net_cumulative_return": benchmark["net_cumulative"],
            "strategy_net_sharpe": s["net_sharpe"],
            "ew30_net_sharpe": benchmark["net_sharpe"],
            "sharpe_difference_vs_ew30": sharpe_difference,
            "mean_turnover": float(np.mean(meta["turnover"])) if meta["turnover"] else 0.0,
            "max_turnover": float(np.max(meta["turnover"])) if meta["turnover"] else 0.0,
            "cost_to_gross_edge": ratio,
            "total_strategy_cost": total_cost,
            "gross_edge": gross_edge,
            "average_active_share": float(np.mean(meta["active_share"])) if meta["active_share"] else 0.0,
            "bootstrap_p": bootstrap_p(s["net"], benchmark["net"]),
            "dsr": s["dsr"],
            "trial_count": FULL_TRIAL_COUNT,
            "eligible_for_selection": bool(
                np.mean(meta["active_share"]) >= 0.50 and ratio is not None and ratio < 0.50),
        })
    eligible_rows = [r for r in rows if r["eligible_for_selection"]]
    selected = None
    if eligible_rows:
        selected = sorted(eligible_rows,
                          key=lambda r: (-r["sharpe_difference_vs_ew30"], r["mean_turnover"]))[0]["id"]
    out = {
        "scope": "development only; no sealed holdout or pre-2020-11-27 portfolio data",
        "period": {"start": FIRST_FORMATION, "end": LAST_FORMATION},
        "common_first_formation": common_start_date,
        "r6_trial_count": r6_trials,
        "r9_variant_count": len(VARIANTS),
        "full_dsr_trial_count": FULL_TRIAL_COUNT,
        "cost_rate_per_traded_dollar": COST_RATE,
        "bootstrap": {"draws": BOOTSTRAP_DRAWS, "seed": BOOTSTRAP_SEED,
                      "block_sessions": BLOCK_LENGTH},
        "input_sha256": {"prices": sha256(npz_path), "scores": sha256(bundle_path),
                         "r9_variant_log": sha256(root / "specs" / "r9_variant_log.md")},
        "benchmark": {"net_cumulative_return": benchmark["net_cumulative"],
                      "gross_cumulative_return": benchmark["gross_cumulative"],
                      "net_sharpe": benchmark["net_sharpe"],
                      "mean_turnover": float(np.mean(benchmark_meta["turnover"]))},
        "selection_rule": "Highest dev-period net Sharpe among variants with active share >=50% and cost/gross edge <50%; ties go to lower turnover.",
        "selected_candidate": selected,
        "variants": rows,
    }
    out_path = root / "r9" / "R9_VARIANTS.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"selected_candidate": selected,
                      "full_dsr_trial_count": FULL_TRIAL_COUNT,
                      "variant_results": rows}, indent=2))
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
