"""R7 S&P point-in-time portfolio adapter; accepts arrays, never loads data.

All input matrices are asset x session. ``roster[:, d]`` is membership known
at the execution open on d; scores are formed at the preceding close. Missing
closes are carried at the last valid close, and stale positions remain until a
scheduled rebalance can trade them. The caller owns data loading/provenance.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from r4_harness import phase3

SHAPES = ("top_decile", "top_quintile", "rank_weighted_top_half")
TURNOVER_CAP = 0.50
COST_PER_SIDE = 0.0005
R6_ENDPOINTS = tuple(f"R6-H{i}" for i in range(1, 22))
R7_ENDPOINTS = ("R7-H1", "R7-H2", "R7-H3")
R7_ENDPOINT_LABELS = {
    "R7-H1": "registered signal/mechanism endpoint",
    "R7-H2": "registered placebo endpoint",
    "R7-H3": "registered portfolio net excess endpoint",
}


def build_holm_family(path: str | Path, r7_endpoints: Sequence[str] = R7_ENDPOINTS) -> dict:
    """Create a prospective R6+R7 family with null p slots and json.dumps hash."""
    endpoints = [*R6_ENDPOINTS, *r7_endpoints]
    if len(set(endpoints)) != len(endpoints) or any(not isinstance(x, str) for x in endpoints):
        raise ValueError("endpoint IDs must be unique strings")
    payload = {"manifest": endpoints,
               "manifest_sha256": hashlib.sha256(json.dumps(endpoints).encode("utf-8")).hexdigest(),
               "p_values": {key: None for key in endpoints},
               "note": "Prospective family scaffold: coordinator must populate preserved R6 p-values before an authorized R7 run; R7 slots remain null until tested.",
               "labels": {**{key: "preserved R6 endpoint slot" for key in R6_ENDPOINTS},
                          **{key: R7_ENDPOINT_LABELS.get(key, "registered R7 endpoint") for key in r7_endpoints}}}
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def validate_holm_family(path: str | Path, *, r7_endpoints: Sequence[str] = R7_ENDPOINTS,
                         require_r6_populated: bool = False) -> dict:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    manifest = obj.get("manifest")
    expected = [*R6_ENDPOINTS, *r7_endpoints]
    digest = hashlib.sha256(json.dumps(manifest).encode("utf-8")).hexdigest()
    if manifest != expected or obj.get("manifest_sha256") != digest:
        raise ValueError("R7 Holm family must preserve R6-H1..H21 then append the frozen R7 endpoints")
    p_values = obj.get("p_values")
    if not isinstance(p_values, dict) or set(p_values) != set(expected):
        raise ValueError("Holm p_values must contain every family slot")
    if any(v is not None and not (0 <= float(v) <= 1) for v in p_values.values()):
        raise ValueError("Holm p-values must be null or in [0,1]")
    if require_r6_populated and any(p_values[key] is None for key in R6_ENDPOINTS):
        raise ValueError("coordinator must populate preserved R6 endpoint p-values before R7 execution")
    labels = obj.get("labels")
    if not isinstance(labels, dict) or set(labels) != set(expected) or any(not str(v).strip() for v in labels.values()):
        raise ValueError("family labels must cover every endpoint with a nonempty description")
    return obj


def cumulative_trial_count(*, prior_trials: int, r7_registered_trials: int,
                           budget: int = 30) -> int:
    """Validate, do not infer, cumulative count from a frozen trial ledger."""
    values = (prior_trials, r7_registered_trials, budget)
    if any(isinstance(x, bool) or not isinstance(x, int) for x in values):
        raise ValueError("trial counts and budget must be integers")
    total = prior_trials + r7_registered_trials
    if prior_trials < 1 or r7_registered_trials < 1 or budget < 1 or total > budget:
        raise ValueError("cumulative trial count is invalid or exceeds the shared budget")
    return total


def _target_weights(scores: np.ndarray, eligible: np.ndarray, shape: str,
                    names: Sequence[str]) -> np.ndarray:
    if shape not in SHAPES:
        raise ValueError(f"shape must be one of {', '.join(SHAPES)}")
    ids = np.flatnonzero(eligible & np.isfinite(scores))
    target = np.zeros(len(scores), dtype=float)
    if not len(ids):
        return target
    labels = np.asarray(names).astype(str)
    order = sorted(ids.tolist(), key=lambda i: (-float(scores[i]), labels[i]))
    count = {"top_decile": max(1, math.ceil(len(ids) * .10)),
             "top_quintile": max(1, math.ceil(len(ids) * .20)),
             "rank_weighted_top_half": max(1, math.ceil(len(ids) * .50))}[shape]
    selected = order[:count]
    if shape == "rank_weighted_top_half":
        weights = np.arange(count, 0, -1, dtype=float)
        target[selected] = weights / weights.sum()
    else:
        target[selected] = 1.0 / count
    return target


def _cap_trade(old: np.ndarray, target: np.ndarray, open_ok: np.ndarray,
               cap: float) -> tuple[np.ndarray, float, bool]:
    """Move toward target pro rata, freezing holdings without an open."""
    frozen = (~open_ok) & (old > 1e-12)
    desired = target.copy()
    desired[frozen] = old[frozen]
    tradable = open_ok.copy()
    remaining = max(0.0, 1.0 - float(desired[frozen].sum()))
    mass = float(desired[tradable].sum())
    if mass > 0:
        desired[tradable] *= remaining / mass
    else:
        desired[tradable] = 0.0
    delta = desired - old
    total = float(np.abs(delta[tradable]).sum())
    scale = min(1.0, cap / total) if total > 0 else 1.0
    new = old.copy()
    new[tradable] = old[tradable] + scale * delta[tradable]
    turnover = float(np.abs(new - old).sum())
    return new, turnover, total > cap + 1e-12


def _apply_returns(weights: np.ndarray, returns: np.ndarray) -> tuple[np.ndarray, float]:
    # Uninvested weight is cash, which earns zero and stays in the book. This
    # matters when a turnover-capped transition leaves part of NAV uninvested.
    cash = max(0.0, 1.0 - float(weights.sum()))
    raw = weights * (1.0 + np.nan_to_num(returns, nan=0.0))
    gross = cash + float(raw.sum())
    if gross <= 0:
        raise ArithmeticError("portfolio NAV reached zero or below")
    return raw / gross, gross - 1.0


def run_portfolio(scores, open_prices, close_prices, membership, fill_indices,
                  names: Sequence[str], *, shape: str = "top_decile",
                  turnover_cap: float = TURNOVER_CAP, cost_rate: float = COST_PER_SIDE,
                  trial_count: int, holm_family: Mapping[str, float | None] | None = None,
                  bootstrap_draws: int = 5000, seed: int = 20261111) -> dict:
    """Run strategy against PIT EW S&P using next-open formation and decision 63.

    At each fill, both cohorts require PIT membership and an available positive
    execution open. Strategy names additionally require a finite prior-close
    score. Daily missing closes are stale-marked; the last valid close is used
    when prices resume. Nontradable old positions are frozen until a later
    scheduled/open opportunity. Turnover is total buys+sells divided by NAV.
    """
    s, op, cl, roster = (np.asarray(x, dtype=float) for x in
                         (scores, open_prices, close_prices, membership))
    if s.ndim != 2 or op.shape != s.shape or cl.shape != s.shape or roster.shape != s.shape:
        raise ValueError("scores, opens, closes and membership must share (assets, dates) shape")
    n, t = s.shape
    if len(names) != n or len(set(map(str, names))) != n:
        raise ValueError("names must uniquely label every asset row")
    if not np.isfinite(roster).all() or not np.isin(roster, (0.0, 1.0)).all():
        raise ValueError("membership must contain only finite 0/1 point-in-time flags")
    if shape not in SHAPES:
        raise ValueError(f"shape must be one of {', '.join(SHAPES)}")
    if not 0 <= turnover_cap <= 0.5:
        raise ValueError("turnover cap must be in [0, 0.50]")
    if (not 0 <= cost_rate < 1 or isinstance(trial_count, bool) or
            not isinstance(trial_count, int) or not 1 <= trial_count <= 30 or bootstrap_draws < 1):
        raise ValueError("invalid cost, trial count or bootstrap draw count")
    fills = sorted(set(int(x) for x in fill_indices))
    if len(fills) < 2 or any(i <= 0 or i >= t for i in fills):
        raise ValueError("at least two valid open fill indices are required")
    expected_prior_p = set(R6_ENDPOINTS) | set(R7_ENDPOINTS[:2])
    if holm_family is None or set(holm_family) != expected_prior_p:
        raise ValueError("portfolio requires every frozen R6 and preceding R7 Holm p-value slot")
    if any(v is None or not 0 <= float(v) <= 1 for v in holm_family.values()):
        raise ValueError("prior Holm endpoints must have computed p-values before portfolio stage")

    first = fills[0]
    last_close = np.full(n, np.nan)
    for i in range(n):
        prior = np.flatnonzero(np.isfinite(cl[i, :first]) & (cl[i, :first] > 0))
        if len(prior):
            last_close[i] = cl[i, prior[-1]]
    strategy = np.zeros(n)
    benchmark = np.zeros(n)
    sret, bret, turns, costs, active = [], [], [], [], []
    formation_records = []
    cap_binds = 0
    fill_set = set(fills)

    for d in range(first, t):
        open_ok = np.isfinite(op[:, d]) & (op[:, d] > 0)
        close_ok = np.isfinite(cl[:, d]) & (cl[:, d] > 0)
        if d == first:
            initial = roster[:, d].astype(bool) & open_ok
            if initial.any():
                strategy[initial] = 1.0 / int(initial.sum())
                benchmark[initial] = strategy[initial]
        # Existing holdings receive prior-close to open returns. With no open,
        # keep the stale mark flat until a valid open resumes.
        overnight = np.zeros(n)
        can_overnight = open_ok & np.isfinite(last_close) & (last_close > 0)
        if d != first:
            overnight[can_overnight] = op[can_overnight, d] / last_close[can_overnight] - 1.0
        strategy, so = _apply_returns(strategy, overnight)
        benchmark, bo = _apply_returns(benchmark, overnight)
        total_cost = 0.0

        if d in fill_set:
            cohort = roster[:, d].astype(bool) & open_ok
            target = _target_weights(s[:, d - 1], cohort, shape, names)
            ew_target = np.zeros(n)
            if cohort.any():
                ew_target[cohort] = 1.0 / int(cohort.sum())
            if d == first:
                # Initialize both books at the identical available-name EW.
                strategy = ew_target.copy()
                benchmark = ew_target.copy()
            strategy, traded, binds = _cap_trade(strategy, target, open_ok, turnover_cap)
            benchmark, btraded, _ = _cap_trade(benchmark, ew_target, open_ok, 2.0)
            selected = np.flatnonzero(target > 0)
            formation_records.append({
                "fill_index": d,
                "strategy_target_names": [str(names[i]) for i in selected],
                "benchmark_cohort_names": [str(names[i]) for i in np.flatnonzero(cohort)],
            })
            turns.append(traded)
            cap_binds += int(binds)
            active.append(float(.5 * np.abs(strategy - ew_target).sum()))
            total_cost = cost_rate * traded
            # Benchmark follows its exact available-name EW target; costs use
            # its own realized buys+sells under the same rate.
            total_bench_cost = cost_rate * btraded
        else:
            total_bench_cost = 0.0

        # If today's open is unavailable but a close is available, value from
        # last valid close here. Otherwise mark open-to-close; a missing close
        # is carried flat and does not erase the last valid mark.
        intraday = np.zeros(n)
        normal = open_ok & close_ok
        intraday[normal] = cl[normal, d] / op[normal, d] - 1.0
        resumed = (~open_ok) & close_ok & np.isfinite(last_close) & (last_close > 0)
        intraday[resumed] = cl[resumed, d] / last_close[resumed] - 1.0
        strategy, si = _apply_returns(strategy, intraday)
        benchmark, bi = _apply_returns(benchmark, intraday)
        sret.append((1.0 + so) * (1.0 - total_cost) * (1.0 + si) - 1.0)
        bret.append((1.0 + bo) * (1.0 - total_bench_cost) * (1.0 + bi) - 1.0)
        costs.extend([total_cost, total_bench_cost])
        last_close[close_ok] = cl[close_ok, d]

    # Terminal stale books are liquidated at their last valid close, charging
    # one side on the final session just like a normal exit.
    if sret:
        missing_final = ~np.isfinite(cl[:, -1]) | (cl[:, -1] <= 0)
        stale_s = (strategy > 0) & missing_final
        stale_b = (benchmark > 0) & missing_final
        sc = cost_rate * float(strategy[stale_s].sum()) if stale_s.any() else 0.0
        bc = cost_rate * float(benchmark[stale_b].sum()) if stale_b.any() else 0.0
        sret[-1] = (1 + sret[-1]) * (1 - sc) - 1
        bret[-1] = (1 + bret[-1]) * (1 - bc) - 1
        costs.extend([sc, bc])
    sr, br = np.asarray(sret), np.asarray(bret)
    boot_p, boot_draws = phase3.circular_block_bootstrap_pvalue(
        sr, br, block_length=10, n_draws=bootstrap_draws, seed=seed)
    adjusted = phase3.holm_correction({**{k: float(v) for k, v in holm_family.items()},
                                       "R7-H3": boot_p})["R7-H3"]["holm_p"]
    sharpe = lambda x: float(x.mean() / x.std(ddof=1) * math.sqrt(252)) if len(x) > 1 and x.std(ddof=1) > 0 else 0.0
    return {
        "shape": shape, "strategy_daily_net": sr, "benchmark_daily_net": br,
        "net_excess_cumulative": float(np.prod(1 + sr) - np.prod(1 + br)),
        "strategy_net_sharpe": sharpe(sr), "benchmark_net_sharpe": sharpe(br),
        "bootstrap_p_raw": boot_p, "bootstrap_p_holm": adjusted,
        "bootstrap_draws": boot_draws,
        "strategy_mean_nw_t": phase3.newey_west_t(sr, lag=10),
        "benchmark_mean_nw_t": phase3.newey_west_t(br, lag=10),
        "deflated_sharpe": phase3.deflated_sharpe_ratio(sr, trial_count=trial_count),
        "trial_count": trial_count, "turnover": np.asarray(turns),
        "turnover_mean": float(np.mean(turns)) if turns else 0.0,
        "turnover_max": float(max(turns, default=0.0)), "turnover_cap_bind_count": cap_binds,
        "active_share_mean": float(np.mean(active)) if active else 0.0,
        "formation_records": formation_records,
        "cost_total_and_terminal": float(sum(costs)),
        "decision63_terminal_stale_strategy_names": int(stale_s.sum()) if sret else 0,
        "decision63_terminal_stale_benchmark_names": int(stale_b.sum()) if sret else 0,
    }

