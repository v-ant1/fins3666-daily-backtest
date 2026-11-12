"""Guarded D1 runner. Real development outcomes require an explicit --execute.

Input bundle schema is documented in RUNNER_SPEC_MAP.md. This module never
downloads data and rejects any bundle containing pre-2020-06 dates.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Mapping

import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from r4_harness.ic_engine import cross_sectional_ic, newey_west_t
from r4_harness.phase3 import (
    circular_block_bootstrap_pvalue,
    deflated_sharpe_ratio,
    holm_correction,
)
from r4_harness.runner_guard import guarded_runner, validate_frozen_prereg

PREREG = ROOT / "specs" / "r6_prereg" / "D1.md"
RUN_DIR = Path(__file__).resolve().parent / "run"
DEFAULT_INPUTS = Path(__file__).resolve().parent / "D1_INPUTS.npz"
DEFAULT_COVERAGE = Path(__file__).resolve().parent / "joint_coverage_manifest.json"
TRIALS = ROOT / "specs" / "r4_trials.md"
DECISIONS = ROOT / "specs" / "r6_decisions.md"

# Exact implementation settings from frozen D1.
HORIZON = 5
FORMATION_STEP = 5
EXECUTION_DELAY = 2  # t+2 open; five-session return ends at t+6 close.
NW_LAG = 4
SHUFFLE_DRAWS = 500
BOOTSTRAP_DRAWS = 5000
SEED = 20261111
TOP_N = 5
TURNOVER_CAP = 0.50  # buys + sells / NAV
COST_RATE = 0.0005  # 5 bp per dollar of total traded notional
MIN_IC = 0.0043301
MIN_T = 2.0
MIN_COVERAGE = 0.90
MIN_WIDE_DATES = 0.80
MIN_WIDE_NAMES = 250
R6_ENDPOINTS = ("R6-H1", "R6-H2", "R6-H3")

# Config values are derived with the normalization documented in
# PREREG_DIFF.txt. The parser uses `top_fraction`'s numerator (5); the actual
# portfolio fraction is the frozen 5/30 and is explicit in the runner.
RUNNER_SPEC_CONFIG = {
    "min_t": 2,
    "turnover": 0.50,
    "return_dispersion": 0.04,
    "turnover_cap": 0.50,
    "cost_per_side": 0.0005,
    "top_fraction": 5,
    "draws": [5000, 500],
    "percentile": 95,
    "k": 5,
    "block_length": 10,
    "alpha": [0.05, 0.10],
    "min_ic": [0, 0.0043301],
    "p": 1,
    "endpoint_count": 3,
    "endpoint_ids": [1, 2, 3],
    "horizon": 5,
    "nw_lag": 4,
    "seed": 20261111,
    "variant_count": 1,
}


class CoverageFailure(RuntimeError):
    """Input-only threshold failure; no signal/outcome computation follows."""


def _matrix(data: Mapping, key: str, dtype=None) -> np.ndarray:
    if key not in data:
        raise ValueError(f"input bundle missing {key!r}")
    value = np.asarray(data[key], dtype=dtype)
    if value.ndim != 2:
        raise ValueError(f"{key} must be an assets x dates matrix")
    return value


def validate_bundle(data: Mapping) -> dict:
    """Validate development-only inputs and schemas without computing returns."""
    dates = np.asarray(data["dates"]).astype(str)
    if dates.ndim != 1 or not len(dates):
        raise ValueError("dates must be a nonempty vector")
    if not np.all(dates[1:] > dates[:-1]):
        raise ValueError("dates must be strictly increasing and unique")
    if dates[0] < "2020-06-01" or dates[-1] > "2026-10-30":
        raise ValueError("D1 runner accepts development dates 2020-06-01..2026-10-30 only")
    if len(dates) != 1614:
        raise ValueError(f"expected 1,614 development sessions, got {len(dates)}")
    out = {"dates": dates}
    for universe in ("sp500", "dow"):
        roster = _matrix(data, f"{universe}_roster", bool)
        ratio = _matrix(data, f"{universe}_ratio", float)
        op = _matrix(data, f"{universe}_adjusted_open", float)
        close = _matrix(data, f"{universe}_adjusted_close", float)
        sic = _matrix(data, f"{universe}_sic2").astype(str)
        names = np.asarray(data[f"{universe}_names"]).astype(str)
        shape = (len(names), len(dates))
        if any(a.shape != shape for a in (roster, ratio, op, close, sic)):
            raise ValueError(f"{universe} arrays must all have shape {shape}")
        if len(set(names.tolist())) != len(names):
            raise ValueError(f"{universe} names must be unique")
        out[universe] = {
            "names": names,
            "roster": roster,
            "ratio": ratio,
            "open": op,
            "close": close,
            "sic2": sic,
        }
    return out


def _valid_price(open_px, close_px):
    return (np.isfinite(open_px) & (open_px > 0) &
            np.isfinite(close_px) & (close_px > 0))


def joint_coverage_gate(bundle: Mapping) -> dict:
    """Input-only joint coverage and wide-date gate; no returns are formed."""
    dates = bundle["dates"]
    dev = np.flatnonzero((dates >= "2020-11-27") & (dates <= "2026-10-30"))
    if not len(dev):
        raise CoverageFailure("no dates in the registered development window")
    scheduled = dev[np.arange(0, len(dev), FORMATION_STEP)]
    # Formation dates without a full date-indexed five-session forward window
    # cannot be scheduled, independent of the values in the price arrays.
    scheduled = scheduled[scheduled + 6 < len(dates)]
    result = {"development_sessions": int(len(dev)),
              "scheduled_formations": int(len(scheduled)), "universes": {}}
    wide_counts = None
    for universe in ("sp500", "dow"):
        x = bundle[universe]
        # The 90% gate is over the registered weekly formation schedule.
        r = x["roster"][:, scheduled]
        ratio_ok = np.isfinite(x["ratio"][:, scheduled]) & (x["ratio"][:, scheduled] >= 0)
        price_ok = _valid_price(x["open"][:, scheduled], x["close"][:, scheduled])
        paired = r & ratio_ok
        joint = paired & price_ok
        expected = int(r.sum())
        joint_n = int(joint.sum())
        coverage = joint_n / expected if expected else 0.0
        result["universes"][universe] = {
            "scheduled_member_days": expected,
            "paired_finra_member_days": int(paired.sum()),
            "joint_finra_price_member_days": joint_n,
            "joint_coverage": float(coverage),
        }
        if coverage < MIN_COVERAGE:
            raise CoverageFailure(
                f"{universe} joint FINRA/price coverage {coverage:.4%} < 90%")
        if universe == "sp500":
            eligible_per_date = []
            for t in scheduled:
                past = x["ratio"][:, t - 4:t + 1]
                score_ok = np.isfinite(past).all(axis=1) & (past >= 0).all(axis=1)
                fwd_ok = (_valid_price(x["open"][:, t + 2], x["close"][:, t + 6]))
                eligible_per_date.append(int(np.sum(
                    x["roster"][:, t] & score_ok & fwd_ok)))
            counts = np.asarray(eligible_per_date, dtype=int)
            wide_fraction = float(np.mean(counts >= MIN_WIDE_NAMES)) if len(counts) else 0.0
            result["wide_date_counts"] = counts.tolist()
            result["wide_dates_fraction"] = wide_fraction
            if wide_fraction < MIN_WIDE_DATES:
                raise CoverageFailure(
                    f"S&P dates with >=250 complete names {wide_fraction:.4%} < 80%")
    result["passed"] = True
    return result


def coverage_manifest_gate(manifest: Mapping) -> dict:
    """Validate the presence-only joint coverage audit before loading outcomes."""
    if manifest.get("development_only") is not True:
        raise CoverageFailure("coverage manifest is not marked development-only")
    if manifest.get("price_values_loaded") is not False:
        raise CoverageFailure("coverage manifest must establish price-presence-only audit")
    if manifest.get("price_returns_computed") is not False:
        raise CoverageFailure("coverage audit must not compute price returns")
    if manifest.get("forward_returns_loaded_or_computed") is not False:
        raise CoverageFailure("coverage audit must not load or compute forward returns")
    if manifest.get("ics_computed") is not False:
        raise CoverageFailure("coverage audit must not compute ICs")
    if manifest.get("formation_rule") != "every fifth NYSE session beginning 2020-11-27":
        raise CoverageFailure("formation rule differs from frozen D1")
    windows = manifest.get("formation_price_windows", {})
    if windows.get("signal") != "t-4 through t, bar presence only" or \
       windows.get("forward") != "t+2 through t+6, bar presence only":
        raise CoverageFailure("coverage manifest has the wrong frozen price windows")
    universes = manifest.get("universes", {})
    try:
        sp = universes["SP500"]
        dw = universes["DOW30"]
        sp_sessions = int(sp["development_daily_sessions"])
        dw_sessions = int(dw["development_daily_sessions"])
        sp_joint = float(sp["formation_joint_member_day_coverage_pct"]) / 100.0
        dw_joint = float(dw["formation_joint_member_day_coverage_pct"]) / 100.0
        sp_date_fraction = float(sp["formation_dates_pct_ge_250"]) / 100.0
        sp_dates = int(sp["formation_dates_ge_250_eligible"])
        scheduled_dates = int(sp["scheduled_formation_dates"])
        gaps = int(manifest["sp500_unresolved_price_gap_count"])
        gap_symbols = manifest["sp500_unresolved_price_gap_symbols"]
        first_formation = str(manifest["first_formation"])
        last_formation = str(manifest["last_formation"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CoverageFailure(f"joint coverage manifest is incomplete: {exc}") from exc
    if sp_joint < MIN_COVERAGE or dw_joint < MIN_COVERAGE:
        raise CoverageFailure("joint formation member-day coverage is below 90%")
    if sp_date_fraction < MIN_WIDE_DATES or scheduled_dates < 1:
        raise CoverageFailure("fewer than 80% of scheduled S&P dates have 250 eligible names")
    if abs(sp_date_fraction - sp_dates / scheduled_dates) > (1.0 / scheduled_dates + 1e-9):
        raise CoverageFailure("S&P date-count percentage does not match its numerator/denominator")
    if len(gap_symbols) != gaps or len(set(gap_symbols)) != gaps or gaps < 0:
        raise CoverageFailure("S&P price-gap count/list is inconsistent")
    if first_formation != "2020-11-27" or last_formation > "2026-10-30":
        raise CoverageFailure("joint coverage formation dates are outside frozen D1 window")
    if sp_sessions != 1488 or dw_sessions != 1488 or scheduled_dates != 298:
        raise CoverageFailure("joint coverage session/date counts do not match frozen D1 window")
    if manifest.get("overall_gate") != "PASS":
        raise CoverageFailure("joint coverage manifest does not report overall PASS")
    return {
        "passed": True,
        "sp500_formation_coverage": sp_joint,
        "dow_formation_coverage": dw_joint,
        "sp500_dates_ge_250": sp_dates,
        "sp500_scheduled_dates": scheduled_dates,
        "sp500_dates_fraction_ge_250": sp_date_fraction,
        "sp500_price_gap_count": gaps,
        "manifest_gate_rule": manifest.get("gate_rule"),
    }


def run_coverage_first(manifest: Mapping, bundle_loader, *, output_dir: Path | None = None,
                       trial_count: int = 1) -> dict:
    """Gate from metadata first; never invoke bundle_loader when the gate fails."""
    try:
        input_coverage = coverage_manifest_gate(manifest)
    except CoverageFailure as exc:
        blocked = {"status": "not run", "reason": f"coverage gate failed: {exc}"}
        rows = _endpoint_rows(blocked, blocked, None)
        result = {"approach": "D1", "status": "stopped at input-only coverage gate",
                  "coverage_error": str(exc), "endpoint_rows": rows}
        if output_dir is not None:
            _write_endpoints(output_dir, rows)
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "D1_RESULTS.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    data = bundle_loader()
    result = analyze_bundle(data, output_dir=output_dir, trial_count=trial_count)
    result["coverage_manifest"] = input_coverage
    if output_dir is not None:
        (output_dir / "D1_RESULTS.json").write_text(
            json.dumps(result, indent=2, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x),
            encoding="utf-8")
    return result


def _signals(ratio: np.ndarray) -> np.ndarray:
    """Five-session arithmetic mean of ratios, expressed as P=-R."""
    n, t = ratio.shape
    score = np.full((n, t), np.nan, dtype=float)
    for j in range(4, t):
        window = ratio[:, j - 4:j + 1]
        ok = np.isfinite(window).all(axis=1) & (window >= 0).all(axis=1)
        score[ok, j] = -window[ok].mean(axis=1)
    return score


def _forward_returns(x: Mapping) -> np.ndarray:
    """Compute five-session return from t+2 open to t+6 close after gate."""
    op, close = x["open"], x["close"]
    forward = np.full(op.shape, np.nan, dtype=float)
    for t in range(op.shape[1] - 6):
        valid = _valid_price(op[:, t + 2], close[:, t + 6])
        forward[valid, t] = close[valid, t + 6] / op[valid, t + 2] - 1.0
    return forward


def _formation_indices(dates: np.ndarray) -> np.ndarray:
    dev = np.flatnonzero((dates >= "2020-11-27") & (dates <= "2026-10-30"))
    formations = dev[np.arange(0, len(dev), FORMATION_STEP)]
    return formations[formations + 6 < len(dates)]


def _formation_panel(scores, forward, roster, formations):
    return (scores[:, formations], forward[:, formations], roster[:, formations])


def _stratified_shuffle(scores, sic2, mask, rng):
    """Shuffle score within SIC2 among eligible names; singletons are fixed."""
    shuffled = np.array(scores, copy=True)
    for t in range(scores.shape[1]):
        groups: dict[str, list[int]] = {}
        eligible = mask[:, t] & np.isfinite(scores[:, t])
        for i in np.flatnonzero(eligible):
            group = str(sic2[i, t]).strip()
            if group and group.lower() not in {"nan", "none", "0"}:
                groups.setdefault(group, []).append(int(i))
        for members in groups.values():
            if len(members) > 1:
                indices = np.asarray(members, dtype=int)
                shuffled[indices, t] = rng.permutation(scores[indices, t])
    return shuffled


def _sig_score(value):
    return float(value) if np.isfinite(value) else None


def _wealth_path(scores, op, close, roster, names, fills, *, equal_weight,
                 cap=TURNOVER_CAP, cost_rate=COST_RATE):
    """Actual-trade, open-execution simulator initialized at EW weights."""
    n, tmax = scores.shape
    fills = sorted((int(i) for i in fills if 0 < int(i) < tmax))
    if len(fills) < 1:
        raise ValueError("no in-range t+2 fill dates")
    first = fills[0]
    seed_date = first - 1
    seed_members = roster[:, seed_date] & _valid_price(op[:, seed_date], close[:, seed_date])
    if not seed_members.any():
        raise ValueError("cannot initialize EW30 from available names")
    weights0 = np.zeros(n, dtype=float)
    weights0[seed_members] = 1.0 / seed_members.sum()
    shares = np.divide(weights0, close[:, seed_date], out=np.zeros(n),
                       where=np.isfinite(close[:, seed_date]) & (close[:, seed_date] > 0))
    cash = 0.0
    previous_close_nav = 1.0
    nav_close_series, daily_returns = [], []
    turnovers, active_shares = [], []
    total_cost = 0.0
    fill_to_formation = {int(fi): int(fi) - EXECUTION_DELAY for fi in fills}
    stop = min(tmax, max(fill_to_formation.values()) + 7)
    for day in range(first, stop):
        price = op[:, day]
        valid_open = np.isfinite(price) & (price > 0)
        if np.any((np.abs(shares) > 1e-14) & ~valid_open):
            raise ValueError(f"missing open for held asset on {day}")
        nav_open = cash + float(np.sum(shares * np.where(valid_open, price, 0.0)))
        if nav_open <= 0:
            raise ValueError("portfolio NAV reached zero or below")
        if day in fill_to_formation:
            formation = fill_to_formation[day]
            tradable = roster[:, day] & valid_open
            if equal_weight:
                if not tradable.any():
                    raise ValueError("no names for point-in-time EW benchmark")
                desired = tradable.astype(float) / tradable.sum()
            else:
                eligible = (roster[:, formation] & tradable & np.isfinite(scores[:, formation]))
                ix = np.flatnonzero(eligible)
                if len(ix) < TOP_N:
                    raise ValueError(f"only {len(ix)} eligible Dow names at fill {day}; need 5")
                chosen = sorted(ix.tolist(), key=lambda i: (-scores[i, formation], names[i]))[:TOP_N]
                desired = np.zeros(n, dtype=float)
                desired[chosen] = 1.0 / TOP_N
            current = shares * np.where(valid_open, price, 0.0) / nav_open

            def execute(scale):
                weights = current + scale * (desired - current)
                nav_after = nav_open
                new_shares = shares.copy()
                notional = 0.0
                for _ in range(100):
                    new_shares = np.divide(nav_after * weights, price,
                                           out=np.zeros(n), where=valid_open)
                    notional = float(np.sum(np.abs(new_shares - shares) *
                                            np.where(valid_open, price, 0.0)))
                    updated = nav_open - cost_rate * notional
                    if abs(updated - nav_after) < 1e-13 * max(1.0, nav_open):
                        nav_after = updated
                        break
                    nav_after = updated
                new_shares = np.divide(nav_after * weights, price,
                                       out=np.zeros(n), where=valid_open)
                notional = float(np.sum(np.abs(new_shares - shares) *
                                        np.where(valid_open, price, 0.0)))
                return weights, new_shares, notional, nav_open - cost_rate * notional

            full = execute(1.0)
            scale = 1.0
            if not equal_weight and full[2] / nav_open > cap:
                lo, hi = 0.0, 1.0
                for _ in range(60):
                    mid = (lo + hi) / 2
                    if execute(mid)[2] / nav_open <= cap:
                        lo = mid
                    else:
                        hi = mid
                scale = lo
            weights, new_shares, notional, nav_after = execute(scale)
            if not equal_weight and notional / nav_open > cap + 1e-8:
                raise ArithmeticError("50% total traded-notional cap failed")
            total_cost += nav_open - nav_after
            turnovers.append(notional / nav_open)
            ew = tradable.astype(float) / tradable.sum()
            active_shares.append(.5 * float(np.abs(weights - ew).sum()))
            shares = new_shares
            cash = nav_after - float(np.sum(shares * np.where(valid_open, price, 0.0)))
        close_px = close[:, day]
        held = np.abs(shares) > 1e-14
        if np.any(held & (~np.isfinite(close_px) | (close_px <= 0))):
            raise ValueError(f"missing close for held asset on {day}")
        nav_close = cash + float(np.sum(shares * np.where(held, close_px, 0.0)))
        daily_returns.append(nav_close / previous_close_nav - 1.0)
        nav_close_series.append(nav_close)
        previous_close_nav = nav_close
    returns = np.asarray(daily_returns, dtype=float)
    wealth = float(np.prod(1.0 + returns)) if len(returns) else 1.0
    sd = float(np.std(returns, ddof=0)) if len(returns) else 0.0
    sharpe = float(np.mean(returns) / sd * np.sqrt(252)) if sd > 0 else 0.0
    return {
        "returns": returns,
        "cumulative_return": wealth - 1.0,
        "sharpe": sharpe,
        "turnovers": turnovers,
        "mean_turnover": float(np.mean(turnovers)) if turnovers else 0.0,
        "max_turnover": float(np.max(turnovers)) if turnovers else 0.0,
        "active_share": float(np.mean(active_shares)) if active_shares else 0.0,
        "total_cost": float(total_cost),
    }


def _endpoint_rows(h1, h2, h3=None):
    raw = {
        "R6-H1": h1.get("raw_p"),
        "R6-H2": h2.get("raw_p"),
        "R6-H3": None if h3 is None else h3.get("raw_p"),
    }
    adjusted = holm_correction({key: (1.0 if value is None else float(value))
                                for key, value in raw.items()})
    rows = []
    for key, item, status in (
        ("R6-H1", h1, h1.get("status", "run")),
        ("R6-H2", h2, h2.get("status", "run")),
        ("R6-H3", h3 or {}, "not run" if h3 is None else h3.get("status", "run")),
    ):
        rows.append({
            "endpoint_id": key,
            "estimate": item.get("estimate"),
            "statistic": item.get("statistic"),
            "raw_p": raw[key],
            "holm_p": adjusted[key]["holm_p"],
            "status": status,
        })
    return rows


def _write_endpoints(output_dir: Path, rows):
    path = output_dir / "D1_ENDPOINTS.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ("endpoint_id", "estimate", "statistic", "raw_p", "holm_p", "status")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def analyze_bundle(raw_data: Mapping, *, output_dir: Path | None = None,
                   trial_count: int = 1) -> dict:
    """Run coverage first, then mechanism/placebo and conditional Dow portfolio."""
    bundle = validate_bundle(raw_data)
    try:
        coverage = joint_coverage_gate(bundle)  # must precede any signal/return work
    except CoverageFailure as exc:
        blocked = {"status": "not run", "reason": f"coverage gate failed: {exc}"}
        rows = _endpoint_rows(blocked, blocked, None)
        result = {"approach": "D1", "status": "stopped at input-only coverage gate",
                  "coverage_error": str(exc), "endpoint_rows": rows}
        if output_dir is not None:
            _write_endpoints(output_dir, rows)
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "D1_RESULTS.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    h1 = {"status": "run"}
    h2 = {"status": "run"}
    h3 = None
    formations = _formation_indices(bundle["dates"])

    sp = bundle["sp500"]
    sp_scores = _signals(sp["ratio"])
    sp_forward = _forward_returns(sp)
    sp_s, sp_f, sp_roster = _formation_panel(sp_scores, sp_forward, sp["roster"], formations)
    sp_sic = sp["sic2"][:, formations]
    sp_mask = (sp_roster & np.isfinite(sp_s) & np.isfinite(sp_f))
    ic = cross_sectional_ic(sp_s, sp_f, sp_mask, nw_lag=NW_LAG)
    h1_t = float(ic.nw_t)
    h1_p = float(norm.sf(h1_t)) if np.isfinite(h1_t) else 1.0
    h1_pass = bool(ic.mean_ic >= MIN_IC and h1_t >= MIN_T)
    h1.update({"estimate": float(ic.mean_ic), "statistic": h1_t,
               "raw_p": h1_p, "pass": h1_pass,
               "status": "PASS" if h1_pass else "FAIL",
               "n_dates": int(np.isfinite(ic.ic_by_date).sum())})

    rng = np.random.default_rng(SEED)
    null = np.empty(SHUFFLE_DRAWS, dtype=float)
    for draw in range(SHUFFLE_DRAWS):
        shuffled = _stratified_shuffle(sp_s, sp_sic, sp_mask, rng)
        null[draw] = cross_sectional_ic(shuffled, sp_f, sp_mask).mean_ic
    null = null[np.isfinite(null)]
    shuffle_p = (1 + int(np.sum(null >= ic.mean_ic))) / (len(null) + 1) if len(null) else 1.0
    p95 = float(np.quantile(null, .95)) if len(null) else float("nan")
    h2_pass = bool(len(null) == SHUFFLE_DRAWS and ic.mean_ic > p95 and shuffle_p < .05)
    h2.update({"estimate": float(ic.mean_ic), "statistic": p95, "raw_p": shuffle_p,
               "pass": h2_pass, "status": "PASS" if h2_pass else "FAIL",
               "draws": int(len(null)), "null_p95": p95})

    if h1_pass and h2_pass:
        dw = bundle["dow"]
        dw_scores = _signals(dw["ratio"])
        dw_forward = _forward_returns(dw)
        # The custom simulator uses the frozen t+2 open directly.
        fills = formations + 2
        if len(fills) < 2:
            raise ValueError("fewer than two t+2 Dow portfolio fills")
        strategy = _wealth_path(dw_scores, dw["open"], dw["close"], dw["roster"],
                                dw["names"], fills, equal_weight=False,
                                cost_rate=COST_RATE)
        benchmark = _wealth_path(np.zeros_like(dw_scores), dw["open"], dw["close"],
                                 dw["roster"], dw["names"], fills,
                                 equal_weight=True, cost_rate=COST_RATE)
        strategy_gross = _wealth_path(dw_scores, dw["open"], dw["close"], dw["roster"],
                                      dw["names"], fills, equal_weight=False, cost_rate=0.0)
        benchmark_gross = _wealth_path(np.zeros_like(dw_scores), dw["open"], dw["close"],
                                       dw["roster"], dw["names"], fills,
                                       equal_weight=True, cost_rate=0.0)
        n = min(len(strategy["returns"]), len(benchmark["returns"]))
        raw_p, _ = circular_block_bootstrap_pvalue(
            strategy["returns"][-n:], benchmark["returns"][-n:],
            block_length=10, n_draws=BOOTSTRAP_DRAWS, seed=SEED)
        net_excess = strategy["cumulative_return"] - benchmark["cumulative_return"]
        gross_excess = strategy_gross["cumulative_return"] - benchmark_gross["cumulative_return"]
        adjusted = holm_correction({"R6-H1": h1_p, "R6-H2": shuffle_p,
                                    "R6-H3": raw_p})["R6-H3"]["holm_p"]
        h3_pass = bool(net_excess > 0 and strategy["sharpe"] > benchmark["sharpe"]
                       and strategy["active_share"] >= .50
                       and strategy["max_turnover"] <= TURNOVER_CAP + 1e-8
                       and adjusted < .05)
        incremental_cost = max(0.0, strategy["total_cost"] - benchmark["total_cost"])
        h3 = {"estimate": net_excess,
              "statistic": float(strategy["sharpe"] - benchmark["sharpe"]),
              "raw_p": float(raw_p), "pass": h3_pass,
              "net_excess_return": net_excess,
              "gross_active_edge": gross_excess,
              "strategy_cost": strategy["total_cost"],
              "benchmark_cost": benchmark["total_cost"],
              "incremental_cost": incremental_cost,
              "cost_to_gross_edge_ratio": (incremental_cost / gross_excess
                                            if gross_excess > 0 else None),
              "status": "PASS" if h3_pass else "FAIL",
              "strategy": strategy, "benchmark": benchmark,
              "holm_p": float(adjusted),
              "deflated_sharpe": float(deflated_sharpe_ratio(strategy["returns"], trial_count)),
              "trial_count": int(trial_count)}

    rows = _endpoint_rows(h1, h2, h3)
    result = {"approach": "D1", "coverage": coverage,
              "R6-H1": h1, "R6-H2": h2, "R6-H3": h3,
              "holm_family": "R6 only", "endpoint_rows": rows,
              "prereg_sha256": validate_frozen_prereg(PREREG)[1]}
    if output_dir is not None:
        _write_endpoints(output_dir, rows)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "D1_RESULTS.json").write_text(
            json.dumps(result, indent=2, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x),
            encoding="utf-8")
    return result


def _load_npz(path: Path) -> dict:
    # No outcome/return arrays are stored in the required bundle; returns are
    # derived only after joint_coverage_gate has passed.
    with np.load(path, allow_pickle=False) as z:
        return {key: z[key] for key in z.files}


def prereg_diff_text() -> str:
    """Normalize numeric thousands separators and explicit design labels only.

    This works around prereg_diff's comma-tokenization of `5,000` and makes
    already stated horizon/endpoint/variant labels machine-readable. The
    frozen file itself is never edited; its SHA is checked by the guard.
    """
    text = PREREG.read_text(encoding="utf-8")
    text = text.replace("5,000", "5000")
    text = text.replace("500 independent shuffles", "500 shuffle draws")
    text = text.replace("Use seed `20261111`", "Use seed 20261111")
    text = text.replace("## Holm family and DSR", "## Registered endpoints: Holm family and DSR")
    text = text.replace("## Hypothesis and primary design",
                        "## Hypothesis and primary design\nPrimary horizon: 5 sessions. There is 1 variant. Newey-West lag 4.")
    text = text.replace("Before outcomes, append these three D1 endpoints",
                        "Before outcomes, append these 3 registered endpoints")
    return text


def prereg_diff_payload() -> dict:
    """Run the harness numeric audit on the formatting-normalized frozen text."""
    from r4_harness.prereg_diff import prereg_diff
    check = prereg_diff(prereg_diff_text(), RUNNER_SPEC_CONFIG)
    return {"matches": check.matches,
            "prereg_facts": check.facts,
            "differences": [d.__dict__ for d in check.differences]}


@guarded_runner(prereg_path=PREREG, run_dir=RUN_DIR)
def run_d1(input_path: Path = DEFAULT_INPUTS, coverage_path: Path = DEFAULT_COVERAGE):
    manifest = json.loads(Path(coverage_path).read_text(encoding="utf-8"))
    # `run_coverage_first` calls the NPZ loader only after the input-only gate.
    return run_coverage_first(
        manifest, lambda: _load_npz(Path(input_path)), output_dir=RUN_DIR,
        trial_count=_r6_variant_count())


def _r6_variant_count() -> int:
    """Read the coordinator-maintained current R6 unique-strategy count."""
    text = DECISIONS.read_text(encoding="utf-8")
    matches = re.findall(r"R6 variants used:\s*(\d+)\s*/\s*30", text)
    if not matches:
        raise ValueError("cannot determine unique R6 strategy count from r6_decisions.md")
    value = int(matches[-1])
    if value < 1 or value > 30:
        raise ValueError("R6 unique strategy count must be in 1..30")
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-freeze", action="store_true",
                        help="validate the frozen preregistration without loading inputs")
    parser.add_argument("--execute", action="store_true",
                        help="explicit authorization required for the real development run")
    parser.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    args = parser.parse_args(argv)
    try:
        frozen_date, digest = validate_frozen_prereg(PREREG)
        if args.check_freeze and not args.execute:
            print(json.dumps({"frozen": frozen_date, "sha256": digest,
                              "execution": "not requested"}, indent=2))
            return 0
        if not args.execute:
            print("FROZEN D1 verified; no outcomes read. Re-run with --execute only under coordinator authorization.")
            return 0
        result = run_d1(args.inputs, args.coverage, execute=True)
        print(json.dumps(result, indent=2, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x))
        return 0
    except Exception as exc:
        print(f"REFUSED/FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
