"""Shared, single-pass monthly event cohort return and power harness for S2.

The harness accepts already-classified event books (idea, event_date, asset,
cohort_month, sic2). It deliberately has no event classifier or threshold
selection logic: those are frozen in specs/r10_trial_log.md. The public runner
limits the price panel to the permitted development dates before reading any
price fields.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np

START = "2020-11-27"
END = "2026-10-30"
HOLD_SESSIONS = 20
COST_ONE_WAY = 0.001
NW_LAG = 3


def _nw_t(values: np.ndarray, lag: int = NW_LAG) -> float:
    x = np.asarray(values, dtype=float)
    n = len(x)
    if n < 2:
        return float("nan")
    e = x - x.mean()
    gamma0 = float(e @ e / n)
    long_run = gamma0
    for k in range(1, min(lag, n - 1) + 1):
        gamma = float(e[k:] @ e[:-k] / n)
        long_run += 2.0 * (1.0 - k / (lag + 1.0)) * gamma
    se = math.sqrt(max(long_run, 0.0) / n)
    return float(x.mean() / se) if se > 0 else float("nan")


def _norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _month(date: str) -> str:
    return date[:7]


def evaluate(events: list[dict[str, str]], dates: np.ndarray,
             assets: np.ndarray, roster: np.ndarray, sic2: np.ndarray,
             adjusted_open: np.ndarray, adjusted_close: np.ndarray) -> dict[str, Any]:
    """Evaluate one idea once. Incomplete selected books are omitted as frozen."""
    ds = np.asarray(dates).astype(str)
    if len(ds) < HOLD_SESSIONS + 1 or ds[0] < START or ds[-1] > END:
        raise ValueError("price axis must be a development-only session subset")
    if len(set(ds.tolist())) != len(ds) or not np.all(ds[:-1] < ds[1:]):
        raise ValueError("price dates must be unique and increasing")
    names = np.asarray(assets).astype(str)
    aix = {name: i for i, name in enumerate(names)}
    dix = {date: i for i, date in enumerate(ds)}
    cohort_members: dict[str, set[str]] = defaultdict(set)
    for event in events:
        date = str(event["event_date"])
        cohort = str(event.get("cohort_month", _month(date)))
        asset = str(event["asset"])
        if not (START <= date <= END) or asset not in aix:
            continue
        # Event-month availability: events are assigned to the first session
        # of the month after their acceptance month by the panel builder.
        if cohort in ds:
            cohort_members[cohort].add(asset)
    months = sorted(cohort_members)
    records: list[dict[str, Any]] = []
    weights_by_month: dict[str, dict[str, float]] = {}
    for formation in months:
        j = dix.get(formation)
        if j is None or j + HOLD_SESSIONS - 1 >= len(ds):
            continue
        end_j = j + HOLD_SESSIONS - 1
        members = sorted(a for a in cohort_members[formation]
                         if roster[aix[a], j] and np.isfinite(adjusted_open[aix[a], j])
                         and np.isfinite(adjusted_close[aix[a], end_j])
                         and adjusted_open[aix[a], j] > 0)
        if not members:
            continue
        # Frozen completeness rule: all signal members must have prices and
        # PIT eligibility; never silently drop a selected name.
        if len(members) != len(cohort_members[formation]):
            continue
        bench = roster[:, j:end_j + 1].astype(bool)
        pxok = np.isfinite(adjusted_open[:, j]) & np.isfinite(adjusted_close[:, end_j])
        bench_ix = np.flatnonzero(bench[:, 0] & pxok & (adjusted_open[:, j] > 0))
        if len(bench_ix) == 0:
            continue
        # Benchmark weights are daily point-in-time equal weights. Compound
        # daily closes over the same 20 sessions, with entry at first open.
        b_daily = []
        for k in range(j, end_j + 1):
            eligible = np.flatnonzero(roster[:, k] & np.isfinite(adjusted_close[:, k])
                                       & (np.isfinite(adjusted_open[:, k]) if k == j else True))
            if len(eligible) == 0:
                b_daily.append(float("nan")); continue
            if k == j:
                r = adjusted_close[eligible, k] / adjusted_open[eligible, k] - 1.0
            else:
                prev = adjusted_close[eligible, k - 1]
                ok = np.isfinite(prev) & (prev > 0)
                eligible, prev = eligible[ok], prev[ok]
                if len(eligible) == 0:
                    b_daily.append(float("nan")); continue
                r = adjusted_close[eligible, k] / prev - 1.0
            b_daily.append(float(np.mean(r)))
        if not np.all(np.isfinite(b_daily)):
            continue
        long_returns = np.array([adjusted_close[aix[a], end_j] /
                                 adjusted_open[aix[a], j] - 1.0 for a in members])
        gross_long = float(np.mean(long_returns))
        gross_bench = float(np.prod(1.0 + np.asarray(b_daily)) - 1.0)
        net_long = gross_long - 2.0 * COST_ONE_WAY
        records.append({"formation": formation, "year": formation[:4],
                        "n_names": len(members), "gross_long": gross_long,
                        "gross_benchmark": gross_bench, "net_excess": net_long-gross_bench,
                        "gross_excess": gross_long-gross_bench,
                        "net_long": net_long})
        weights_by_month[formation] = {a: 1.0 / len(members) for a in members}
    excess = np.array([r["net_excess"] for r in records], dtype=float)
    gross_excess = np.array([r["gross_excess"] for r in records], dtype=float)
    sd = float(np.std(excess, ddof=1)) if len(excess) > 1 else float("nan")
    mean = float(np.mean(excess)) if len(excess) else float("nan")
    turnovers = []
    prior: dict[str, float] = {}
    for formation in sorted(weights_by_month):
        cur = weights_by_month[formation]
        universe = set(prior) | set(cur)
        turnovers.append(0.5 * sum(abs(cur.get(a, 0.0)-prior.get(a, 0.0)) for a in universe))
        prior = cur
    turnover = float(np.mean(turnovers)) if turnovers else float("nan")
    annual = {}
    for year in sorted({r["year"] for r in records}):
        vals = [r["net_excess"] for r in records if r["year"] == year]
        annual[year] = {"n": len(vals), "mean_net_excess": float(np.mean(vals)),
                        "positive": bool(np.mean(vals) > 0)}
    years_positive = sum(v["positive"] for v in annual.values())
    yearly_consistency = years_positive / len(annual) if annual else float("nan")
    n_holdout = min(72, int(round((len(records) / max(1, len(annual))) * 6)))
    if len(records) < 2 or not np.isfinite(sd) or n_holdout < 2:
        mde, power = float("nan"), 0.0
    else:
        se_holdout = sd / math.sqrt(n_holdout)
        mde = 2.4865 * se_holdout
        power = _norm_cdf((0.5 * mean) / se_holdout - 1.6449)
    avg_cost = 2.0 * COST_ONE_WAY if records else float("nan")
    cost_share = (avg_cost / abs(float(np.mean(gross_excess)))
                  if records and abs(float(np.mean(gross_excess))) > 0 else float("nan"))
    return {"n_months": len(records), "n_eligible_months": len(records),
            "mean_net_excess": mean, "nw_t_lag3": _nw_t(excess),
            "net_sharpe_vs_benchmark": (mean/sd*math.sqrt(12)
                                        if len(excess) > 1 and sd > 0 else float("nan")),
            "mean_signal_turnover_half_l1": turnover,
            "entry_exit_notional_turnover": 2.0 if records else float("nan"),
            "cost_share_abs_gross_excess": cost_share,
            "gross_excess_mean": float(np.mean(gross_excess)) if records else float("nan"),
            "annual": annual, "year_sign_consistency": yearly_consistency,
            "n_holdout_projected": n_holdout, "holdout_mde": mde,
            "haircut_pass_probability": power,
            "observations": records}


def synthetic_validation() -> dict[str, Any]:
    """Small deterministic fixture: known positive edge, event mapping and cost."""
    dates = np.array([f"2021-{m:02d}-{d:02d}" for m in range(1, 7)
                      for d in range(1, 22)], dtype="<U10")
    n, t = 4, len(dates)
    assets = np.array(["AAA", "BBB", "CCC", "DDD"], dtype="<U5")
    roster = np.ones((n, t), dtype=bool)
    sic2 = np.full((n, t), "35", dtype="<U2")
    op = np.full((n, t), 100.0)
    cl = np.full((n, t), 100.0)
    # Synthetic asset AAA gains exactly 2% over each held 20-session window.
    for month_ix in range(6):
        start = month_ix*21
        cl[0, start:start+20] = np.linspace(100.0, 102.0, 20)
    events = [{"event_date": ("2020-12-15" if m == 1 else f"2021-{m-1:02d}-15"),
               "cohort_month": f"2021-{m:02d}-01", "asset": "AAA"}
              for m in range(1, 7)]
    out = evaluate(events, dates, assets, roster, sic2, op, cl)
    assert out["n_months"] == 6
    assert np.isfinite(out["nw_t_lag3"])
    assert out["entry_exit_notional_turnover"] == 2.0
    assert abs(out["observations"][0]["gross_long"] - .02) < 1e-9
    assert abs(out["observations"][0]["net_long"] - .018) < 1e-9
    return {"passed": True, "synthetic_months": out["n_months"],
            "first_gross_long": out["observations"][0]["gross_long"],
            "first_net_long": out["observations"][0]["net_long"],
            "primary_cost_round_trip": 2* COST_ONE_WAY,
            "strategy_outcomes_read": False}
