"""Guarded J1 weekly SIC2-relative reversal runner.

The command refuses without a frozen/hash-valid J1 preregistration and an
explicit --execute. Tests call pure array helpers with synthetic arrays only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from r4_harness.ic_engine import cross_sectional_ic
from r4_harness.phase3 import (
    append_trial,
    break_even_rank_ic,
    circular_block_bootstrap_pvalue,
    deflated_sharpe_ratio,
    holm_correction,
    prereg_digest,
    run_registered_trial,
)
from r4_harness.prereg_diff import prereg_diff
from r4_harness.runner_guard import guarded_runner

HERE = Path(__file__).resolve().parent
PREREG = ROOT / "specs" / "r6_prereg" / "J1.md"
TRIAL_LOG = ROOT / "specs" / "r4_trials.md"
INPUTS = HERE / "J1_PRICES_DEV.npz"
FEATURES = HERE / "signal_bundle.parquet"
PRICE_MANIFEST = HERE / "J1_PRICES_DEV_manifest.json"
COVERAGE_MANIFEST = HERE / "build_manifest.json"
COVERAGE_CSV = HERE / "formation_coverage.csv"
OUTPUT = HERE / "J1_RESULTS.json"
ENDPOINT_LOG = HERE / "R6_ENDPOINTS.csv"
MECHANISM_PASS = HERE / "MECHANISM_PASS.json"
MECHANISM_FAIL = HERE / "MECHANISM_FAIL.json"

# The single preregistered design.
LOOKBACK = 5
HORIZON = 5
FORMATION_STEP = 5
NW_LAG = 4
PLACEBO_DRAWS = 500
PLACEBO_SEED = 20261111
BOOTSTRAP_DRAWS = 5000
BOOTSTRAP_BLOCK = 10
BOOTSTRAP_SEED = 20261111
COST_PER_NOTIONAL = 0.0005
TURNOVER_CAP = 0.50
ACTIVE_SHARE_MIN = 0.50
TOP_N = 5
UNIVERSE_N = 30
RETURN_DISPERSION = 0.04
COST_TURNOVER_REFERENCE = 0.40
COST_IC_FLOOR_CALCULATED = break_even_rank_ic(
    COST_TURNOVER_REFERENCE, RETURN_DISPERSION, COST_PER_NOTIONAL, TOP_N / UNIVERSE_N
)
COST_IC_FLOOR = 0.0034641016
ENDPOINTS = ("R6-H7", "R6-H8", "R6-H9")

DIFF_SOURCE = HERE / "J1_PREREG_DIFF_SOURCE.md"
DIFF_CONFIG_PATH = HERE / "prereg_diff_config.json"
DIFF_CONFIG = json.loads(DIFF_CONFIG_PATH.read_text(encoding="utf-8"))

# These digests pin the input-only staging artifacts reviewed before outcome
# construction.  Updating an input bundle requires a new explicit QA review.
EXPECTED_PRICE_NPZ_SHA256 = "517f85becd0a07fa094a0492e5fe7b3f36170109082b249d5c8a3149d88f5584"
EXPECTED_PRICE_MANIFEST_SHA256 = "426d46213e07c43af8142a529e6953d74e64f39e9414f40571191b00eb9982f9"
EXPECTED_COVERAGE_MANIFEST_SHA256 = "417fff96a8d877d83ac1d625cd08121c9f186736e74bc5d40c15ede8916695f4"
EXPECTED_COVERAGE_CSV_SHA256 = "39974433c938ece677d0a54c603f5c9b544ad248d6465f91b91a72da6f21093e"


def _get(z, *keys, required=True):
    for key in keys:
        if key in z.files:
            return z[key]
    if required:
        raise KeyError(f"J1 input bundle is missing all supported keys {keys}")
    return None


def load_bundle(path: str | Path) -> dict:
    """Read normalized S&P and Dow daily price inputs for J1-V1.

    The L3 parquet is a formation-level feature/coverage bundle, not sufficient
    by itself for the registered next-open outcome or daily portfolio. The
    coordinator stages these feature rows plus the underlying development-only
    price panels in this two-universe NPZ schema before an authorized run.
    """
    with np.load(path, allow_pickle=False) as z:
        out = {}
        for universe in ("sp500", "dow"):
            dates = np.asarray(_get(z, f"{universe}_dates", "dates")).astype(str)
            assets = np.asarray(_get(z, f"{universe}_assets", f"{universe}_names", "assets", "tickers")).astype(str)
            roster = np.asarray(_get(z, f"{universe}_roster", f"{universe}_roster_mask", "roster_mask", "roster", "pit_roster"), bool)
            sic2 = np.asarray(_get(z, f"{universe}_sic2", f"{universe}_sic2_codes", "sic2", "sic2_codes", "dated_sic2")).astype(str)
            adjusted_close = np.asarray(_get(z, f"{universe}_adjusted_close", f"{universe}_adj_close", "adjusted_close", "adj_close"), float)
            adjusted_open = np.asarray(_get(z, f"{universe}_adjusted_open", f"{universe}_adj_open", "adjusted_open", "adj_open"), float)
            n, t = adjusted_close.shape
            expected = (n, t)
            if len(assets) != n or len(dates) != t:
                raise ValueError(f"{universe} assets/dates axes do not align with price matrices")
            if roster.shape != expected or sic2.shape != expected or adjusted_open.shape != expected:
                raise ValueError(f"{universe} roster/SIC2/open/close arrays must share the assets x dates shape")
            if len(set(assets.tolist())) != len(assets) or len(set(dates.tolist())) != len(dates):
                raise ValueError(f"{universe} asset and date labels must each be unique")
            if not np.all(dates[1:] > dates[:-1]):
                raise ValueError(f"{universe} dates must be strictly increasing")
            if len(dates) and (dates[0] < "2020-06-01" or dates[-1] > "2026-10-30"):
                raise ValueError(f"{universe} dates must remain within the development window")
            out[universe] = {"assets": assets, "dates": dates, "roster": roster,
                             "sic2": sic2, "adjusted_close": adjusted_close,
                             "adjusted_open": adjusted_open}
    return out


def _valid_sic(code) -> bool:
    s = str(code).strip()
    return len(s) >= 2 and s[:2].isdigit() and s.lower() not in {"nan", "none", "-1", "00"}


def _groups(sic2, roster_column, return_column=None):
    groups: dict[str, list[int]] = {}
    for i in np.flatnonzero(roster_column):
        code = str(sic2[i]).strip()
        if _valid_sic(code) and (return_column is None or np.isfinite(return_column[i])):
            groups.setdefault(code[:2], []).append(int(i))
    return groups


def build_signal_only(adjusted_close, roster, sic2, *, lookback=LOOKBACK,
                      formation_step=FORMATION_STEP, formation_start_index=0):
    """Build trailing signals and the eligible formation cohort, without labels."""
    close = np.asarray(adjusted_close, float)
    active = np.asarray(roster, bool)
    industry = np.asarray(sic2).astype(str)
    if close.ndim != 2 or close.shape != active.shape or close.shape != industry.shape:
        raise ValueError("close/roster/SIC2 must share an assets x dates matrix")
    n, t = close.shape
    signal = np.full((n, t), np.nan)
    if formation_start_index < 0 or formation_start_index >= t:
        raise ValueError("formation_start_index must identify a session on the input calendar")
    scheduled = np.zeros(t, dtype=bool)
    scheduled[formation_start_index::formation_step] = True

    for d in np.flatnonzero(scheduled):
        if d < lookback:
            continue
        trailing = np.full(n, np.nan)
        ok_trailing = (active[:, d] & np.isfinite(close[:, d]) &
                       np.isfinite(close[:, d - lookback]) &
                       (close[:, d] > 0) & (close[:, d - lookback] > 0))
        trailing[ok_trailing] = close[ok_trailing, d] / close[ok_trailing, d - lookback] - 1.0
        for code, members in _groups(industry[:, d], active[:, d], trailing).items():
            idx = np.asarray(members, dtype=int)
            if len(idx) < 2:
                continue
            total = float(trailing[idx].sum())
            signal[idx, d] = trailing[idx] - (total - trailing[idx]) / (len(idx) - 1)
    signal_eligible = np.isfinite(signal) & active
    return signal, signal_eligible, scheduled


def build_j1_panels(adjusted_close, adjusted_open, roster, sic2,
                    *, lookback=LOOKBACK, horizon=HORIZON, formation_step=FORMATION_STEP,
                    formation_start_index=0):
    """Build signals and labels; forward peer means use the signal-eligible cohort."""
    close = np.asarray(adjusted_close, float)
    op = np.asarray(adjusted_open, float)
    active = np.asarray(roster, bool)
    industry = np.asarray(sic2).astype(str)
    if close.ndim != 2 or close.shape != op.shape:
        raise ValueError("close/open must share an assets x dates matrix")
    signal, signal_eligible, scheduled = build_signal_only(
        close, active, industry, lookback=lookback,
        formation_step=formation_step, formation_start_index=formation_start_index)
    n, t = close.shape
    fwd = np.full((n, t), np.nan)
    relative_fwd = np.full((n, t), np.nan)

    for d in np.flatnonzero(scheduled):
        if d < lookback or d + horizon >= t:
            continue
        buy = op[:, d + 1]
        sell = close[:, d + horizon]
        ok_fwd = (active[:, d] & np.isfinite(buy) & np.isfinite(sell) &
                  (buy > 0) & (sell > 0))
        fwd[ok_fwd, d] = sell[ok_fwd] / buy[ok_fwd] - 1.0
        # Only names with a complete trailing signal are eligible peers at t;
        # a forward bar alone cannot add a name to the formation cohort.
        for code, members in _groups(industry[:, d], signal_eligible[:, d], fwd[:, d]).items():
            idx = np.asarray(members, dtype=int)
            if len(idx) < 2:
                continue
            total = float(fwd[idx, d].sum())
            relative_fwd[idx, d] = fwd[idx, d] - (total - fwd[idx, d]) / (len(idx) - 1)

    mask = (signal_eligible & np.isfinite(relative_fwd))
    return signal, relative_fwd, mask, scheduled


def _direction_ic(signal, relative_forward, mask, *, nw_lag=NW_LAG):
    """Use the shared masked IC engine on the registered direction-adjusted score."""
    return cross_sectional_ic(-np.asarray(signal, float), np.asarray(relative_forward, float),
                              np.asarray(mask, bool), nw_lag=nw_lag)


def _sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify_input_coverage(input_path=INPUTS, feature_path=FEATURES, *,
                          price_manifest_path=PRICE_MANIFEST,
                          coverage_manifest_path=COVERAGE_MANIFEST,
                          coverage_csv_path=COVERAGE_CSV,
                          expected_price_sha=EXPECTED_PRICE_NPZ_SHA256,
                          expected_price_manifest_sha=EXPECTED_PRICE_MANIFEST_SHA256,
                          expected_coverage_manifest_sha=EXPECTED_COVERAGE_MANIFEST_SHA256,
                          expected_coverage_csv_sha=EXPECTED_COVERAGE_CSV_SHA256,
                          minimum_coverage=0.80, minimum_names=250):
    """Fail closed on the reviewed staged prices and input-only coverage QA."""
    paths = (input_path, price_manifest_path, coverage_manifest_path, coverage_csv_path)
    if any(not Path(p).is_file() for p in paths):
        raise FileNotFoundError("staged price and input coverage artifacts must all exist")
    if feature_path is not None and not Path(feature_path).is_file():
        raise FileNotFoundError("staged input-only signal bundle is missing")
    if expected_price_manifest_sha and _sha256(price_manifest_path) != expected_price_manifest_sha:
        raise ValueError("staged price manifest differs from the reviewed manifest")
    if expected_coverage_manifest_sha and _sha256(coverage_manifest_path) != expected_coverage_manifest_sha:
        raise ValueError("coverage manifest differs from the reviewed input QA")
    if expected_coverage_csv_sha and _sha256(coverage_csv_path) != expected_coverage_csv_sha:
        raise ValueError("coverage table differs from the reviewed input QA")

    price_manifest = json.loads(Path(price_manifest_path).read_text(encoding="utf-8"))
    coverage = json.loads(Path(coverage_manifest_path).read_text(encoding="utf-8"))
    actual_price_sha = _sha256(input_path)
    declared_price_sha = str(price_manifest.get("sha256", "")).lower()
    if actual_price_sha != declared_price_sha or (expected_price_sha and actual_price_sha != expected_price_sha):
        raise ValueError("staged price bundle SHA256 does not match the reviewed price manifest")
    if price_manifest.get("development_window") != ["2020-06-01", "2026-10-30"]:
        raise ValueError("staged price bundle must use the development-only date boundary")
    if price_manifest.get("sessions") != 1614 or price_manifest.get("sp500_assets") != 622:
        raise ValueError("staged price bundle calendar/universe dimensions differ from reviewed QA")
    if coverage.get("scope") != "trailing signal inputs only; no forward returns or outcomes":
        raise ValueError("coverage manifest is not the reviewed input-only artifact")
    if coverage.get("price_boundary") != {"start": "2020-06-01", "end": "2026-10-30"}:
        raise ValueError("coverage manifest has an invalid development price boundary")
    if coverage.get("formation_count") != 298:
        raise ValueError("coverage manifest formation count differs from frozen input QA")

    with Path(coverage_csv_path).open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    sp_rows = [r for r in rows if r.get("universe", "").lower() == "sp500"]
    dow_rows = [r for r in rows if r.get("universe", "").lower() == "dow"]
    if len(sp_rows) != 298 or len(dow_rows) != 298:
        raise ValueError("coverage table must contain 298 dates for each universe")
    if len({r["formation_date"] for r in sp_rows}) != 298:
        raise ValueError("S&P coverage dates must be unique")
    if len({r["formation_date"] for r in dow_rows}) != 298:
        raise ValueError("Dow coverage dates must be unique")
    sp_eligible = [int(r["relative_return_names"]) for r in sp_rows]
    gate_count = sum(n >= minimum_names for n in sp_eligible)
    declared_flags = [r.get("sp500_250_name_gate", "").strip().lower() == "true" for r in sp_rows]
    if declared_flags != [n >= minimum_names for n in sp_eligible]:
        raise ValueError("S&P per-date coverage flags do not match eligible-name counts")
    declared_sp = coverage.get("sp500", {})
    if (gate_count != declared_sp.get("formation_dates_ge_250_relative_names") or
            len(sp_rows) != declared_sp.get("formation_dates") or
            gate_count / len(sp_rows) < minimum_coverage):
        raise ValueError("S&P input coverage gate does not match the reviewed manifest or misses 80%")
    # These 12 low-coverage early dates are retained; eligibility is date-wise.
    return {"verified": True, "sp500_formation_dates": len(sp_rows),
            "sp500_dates_ge_250": gate_count,
            "sp500_coverage_fraction": gate_count / len(sp_rows),
            "dow_formation_dates": len(dow_rows), "forward_labels_built": False}


def validate_feature_bundle(path: str | Path, bundle: dict) -> dict:
    """Tie the daily execution bundle to L3's formation-level signal artifact."""
    import pandas as pd
    frame = pd.read_parquet(path)
    required = {"universe", "formation_date", "ticker", "sic2", "relative_return", "relative_return_mask"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"L3 signal_bundle.parquet is missing columns: {sorted(missing)}")
    if frame.duplicated(["universe", "formation_date", "ticker"]).any():
        raise ValueError("L3 signal bundle has duplicate universe/date/ticker rows")
    frame = frame.copy()
    frame["formation_date"] = pd.to_datetime(frame["formation_date"]).dt.strftime("%Y-%m-%d")
    verified = {}
    for universe in ("sp500", "dow"):
        x = bundle[universe]
        start = int(np.searchsorted(x["dates"], "2020-11-27"))
        if start >= len(x["dates"]) or x["dates"][start] != "2020-11-27":
            raise ValueError(f"{universe} calendar lacks first registered formation 2020-11-27")
        score, valid, scheduled = build_signal_only(
            x["adjusted_close"], x["roster"], x["sic2"],
            formation_start_index=start)
        subset = frame.loc[frame.universe.astype(str).str.lower() == universe]
        lookup = {(str(r.ticker), str(r.formation_date)): (r.sic2, r.relative_return, bool(r.relative_return_mask))
                  for r in subset.itertuples(index=False)}
        checked = 0
        for d in np.flatnonzero(scheduled):
            date = x["dates"][d]
            for i in np.flatnonzero(x["roster"][:, d]):
                ticker = x["assets"][i]
                key = (str(ticker), str(date))
                if key not in lookup:
                    raise ValueError(f"L3 feature row missing for PIT member at {universe} {date} {ticker}")
                feature_sic, feature_score, feature_mask = lookup[key]
                expected_mask = bool(np.isfinite(score[i, d]) and x["roster"][i, d])
                if feature_mask != expected_mask:
                    raise ValueError(f"L3 signal mask mismatch at {universe} {date} {ticker}")
                if expected_mask and not np.isclose(float(feature_score), score[i, d], rtol=0, atol=1e-10):
                    raise ValueError(f"L3 relative-return signal mismatch at {universe} {date} {ticker}")
                feature_sic = "" if pd.isna(feature_sic) else str(feature_sic).strip()
                daily_sic = str(x["sic2"][i, d]).strip()
                if daily_sic.lower() in {"nan", "none"}:
                    daily_sic = ""
                if feature_sic != daily_sic:
                    raise ValueError(f"L3 SIC2 mismatch at {universe} {date} {ticker}")
                checked += 1
        verified[universe] = {"formation_rows_checked": checked,
                              "feature_rows_present": int(len(subset))}
    return verified


def _sic2_shuffle(signal, relative_forward, mask, sic2, *, draws=PLACEBO_DRAWS,
                  seed=PLACEBO_SEED):
    """Within-date, within-SIC2 label shuffle; retain every draw's mean IC."""
    scores = np.asarray(signal, float)
    outcome = np.asarray(relative_forward, float)
    active = np.asarray(mask, bool)
    industry = np.asarray(sic2).astype(str)
    if scores.shape != outcome.shape or scores.shape != active.shape or scores.shape != industry.shape:
        raise ValueError("placebo arrays must share assets x dates shape")
    observed = _direction_ic(scores, outcome, active, nw_lag=NW_LAG).mean_ic
    if not np.isfinite(observed):
        raise ValueError("observed direction-adjusted IC must be finite")
    rng = np.random.default_rng(seed)
    values = np.empty(draws, float)
    for k in range(draws):
        shuffled = scores.copy()
        for d in range(scores.shape[1]):
            idx_by_group = _groups(industry[:, d], active[:, d], scores[:, d])
            for idx in idx_by_group.values():
                if len(idx) > 1:
                    ids = np.asarray(idx, int)
                    shuffled[ids, d] = rng.permutation(shuffled[ids, d])
        values[k] = _direction_ic(shuffled, outcome, active, nw_lag=NW_LAG).mean_ic
    p = (1 + int(np.sum(values >= observed))) / (draws + 1)
    p95 = float(np.quantile(values, .95, method="linear"))
    return {"observed": float(observed), "draws": values, "p95": p95,
            "one_sided_p": float(p), "passed": bool(observed > p95 and p < .05)}


def _target_weights(score, active, names, top_n=TOP_N):
    ok = np.asarray(active, bool) & np.isfinite(score)
    ids = np.flatnonzero(ok)
    if len(ids) < top_n:
        raise ValueError(f"only {len(ids)} eligible Dow signals; need {top_n}")
    order = sorted(ids.tolist(), key=lambda i: (-float(score[i]), str(names[i])))
    w = np.zeros(len(score), float)
    w[order[:top_n]] = 1.0 / top_n
    return w


def _price_ok(prices):
    return np.isfinite(prices) & (np.asarray(prices) > 0)


def _execute_pending_open(shares, cash, pending, open_prices, cost_rate):
    """Fill forced exits at the first available open, charging actual notional."""
    valid = np.asarray(pending, bool) & _price_ok(open_prices) & (np.asarray(shares) > 1e-14)
    notional = float(np.sum(np.asarray(shares)[valid] * np.asarray(open_prices)[valid]))
    fee = float(cost_rate * notional)
    if np.any(valid):
        shares[valid] = 0.0
        pending[valid] = False
        cash += notional - fee
    return shares, cash, pending, notional, fee


def _execute_pending_close(shares, cash, pending, last_close, cost_rate):
    """At sample end, liquidate never-trading-again holdings at last valid close."""
    valid = np.asarray(pending, bool) & (np.asarray(shares) > 1e-14) & _price_ok(last_close)
    notional = float(np.sum(np.asarray(shares)[valid] * np.asarray(last_close)[valid]))
    fee = float(cost_rate * notional)
    if np.any(valid):
        shares[valid] = 0.0
        pending[valid] = False
        cash += notional - fee
    return shares, cash, pending, notional, fee


def _mark_close(close_column, last_close):
    """Update known closes and carry the last close over missing bars."""
    close_column = np.asarray(close_column, float)
    valid = _price_ok(close_column)
    last_close[valid] = close_column[valid]
    return last_close.copy()


def _finish_forced_liquidation(shares, cash, pending, last_close, cost_rate,
                               returns, turnovers, costs):
    """Close pending names at last valid close and include the terminal fee."""
    before = cash + float(np.sum(shares * np.where(_price_ok(last_close), last_close, 0.0)))
    shares, cash, pending, notional, fee = _execute_pending_close(
        shares, cash, pending, last_close, cost_rate)
    if notional:
        turnovers.append(notional / max(before, 1e-12))
        costs.append(fee)
        after = before - fee
        if returns:
            previous = before / max(1.0 + returns[-1], 1e-12)
            returns[-1] = after / previous - 1.0
    return shares, cash, pending


def _simulate_book(scores, op, close, roster, formation_indices, names, *, cost_rate):
    """Top-five book with carried close marks and delayed forced sale orders."""
    scores = np.asarray(scores, float)
    op = np.asarray(op, float)
    close = np.asarray(close, float)
    roster = np.asarray(roster, bool)
    n, t = scores.shape
    formations = [int(x) for x in formation_indices if 0 <= int(x) < t - HORIZON]
    fills = [x + 1 for x in formations if x + 1 < t]
    if len(fills) < 2:
        raise ValueError("at least two complete weekly formation/fill dates are required")
    first_form = formations[0]
    initial_ok = roster[:, first_form] & _price_ok(close[:, first_form])
    if not np.any(initial_ok):
        raise ValueError("no available Dow holdings for initial EW30 staging")

    start_weights = np.zeros(n, float)
    start_weights[initial_ok] = 1.0 / initial_ok.sum()
    sh = np.divide(start_weights, close[:, first_form], out=np.zeros(n), where=initial_ok)
    cash = 0.0
    last_close = np.full(n, np.nan)
    _mark_close(close[:, first_form], last_close)
    last_mark = first_form
    last_close_nav = 1.0
    returns, dates_ix, turnovers, costs, shares, cap_binds, insufficient_flags = [], [], [], [], [], [], []
    daily_nav = {first_form: 1.0}
    pending = np.zeros(n, bool)

    for k, (form, fi) in enumerate(zip(formations, fills)):
        # A held security still missing at formation close is queued for sale.
        pending |= (sh > 1e-14) & ~_price_ok(close[:, form])
        px = op[:, fi]
        open_valid = _price_ok(px)
        mark_open = np.where(open_valid, px, np.where(_price_ok(last_close), last_close, 0.0))
        nav_before = cash + float(np.sum(sh * mark_open))
        forced_at_fill = pending & open_valid & (sh > 1e-14)
        sh, cash, pending, forced_notional, forced_fee = _execute_pending_open(
            sh, cash, pending, px, cost_rate)
        nav_open = cash + float(np.sum(sh * mark_open))
        if nav_open <= 0:
            raise ValueError("portfolio NAV reached zero")
        current = sh * mark_open / nav_open
        eligible = roster[:, fi] & open_valid & np.isfinite(scores[:, form]) & ~forced_at_fill
        eligible_names = int(eligible.sum())
        insufficient = eligible_names < TOP_N
        insufficient_flags.append(insufficient)
        locked = (sh > 1e-14) & ~open_valid
        if insufficient:
            target = current.copy()
        else:
            selected = sorted(np.flatnonzero(eligible).tolist(),
                              key=lambda i: (-float(scores[i, form]), str(names[i])))[:TOP_N]
            target = np.zeros(n, float)
            target[locked] = current[locked]
            remainder = max(0.0, 1.0 - float(target[locked].sum()))
            target[selected] = remainder / TOP_N

        def candidate(scale):
            weights = current + scale * (target - current)
            new_sh = sh.copy()
            new_sh[open_valid] = nav_open * weights[open_valid] / px[open_valid]
            notional = float(np.sum(np.abs(new_sh[open_valid] - sh[open_valid]) * px[open_valid]))
            nav_after = nav_open - cost_rate * notional
            return weights, new_sh, notional, nav_after

        full_turnover = (forced_notional + candidate(1.0)[2]) / max(nav_before, 1e-12)
        scale = 1.0 if full_turnover <= TURNOVER_CAP + 1e-12 else None
        if scale is None:
            lo, hi = 0.0, 1.0
            for _ in range(60):
                mid = (lo + hi) / 2.0
                if (forced_notional + candidate(mid)[2]) / max(nav_before, 1e-12) <= TURNOVER_CAP + 1e-12:
                    lo = mid
                else:
                    hi = mid
            scale = lo
        weights, new_sh, notional, nav_after = candidate(scale)
        turnover = (forced_notional + notional) / max(nav_before, 1e-12)
        if turnover > TURNOVER_CAP + 1e-8:
            raise ArithmeticError("J1 total traded-notional turnover cap exceeded")
        turnovers.append(turnover)
        costs.append(forced_fee + nav_open - nav_after)
        benchmark = np.zeros(n)
        bench_names = roster[:, fi] & open_valid
        if np.any(bench_names):
            benchmark[bench_names] = 1.0 / int(bench_names.sum())
        shares.append(.5 * float(np.abs(weights - benchmark).sum()))
        cap_binds.append(bool(scale < 1.0 - 1e-10))
        sh = new_sh
        cash = nav_after - float(np.sum(sh * mark_open))
        # If the trade requested at this rebalance cannot execute because its
        # close/open is missing, keep the position marked and queue the sale.
        pending |= (sh > 1e-14) & ~_price_ok(close[:, form])
        next_fill = fills[k + 1] if k + 1 < len(fills) else t
        for d in range(max(last_mark + 1, fi), min(next_fill, t)):
            if d > fi:
                valid_open_d = _price_ok(op[:, d])
                open_mark_d = np.where(valid_open_d, op[:, d],
                                       np.where(_price_ok(last_close), last_close, 0.0))
                nav_before_exit = cash + float(np.sum(sh * open_mark_d))
                sh, cash, pending, delayed_notional, delayed_fee = _execute_pending_open(
                    sh, cash, pending, op[:, d], cost_rate)
                if delayed_notional:
                    turnovers.append(delayed_notional / max(nav_before_exit, 1e-12))
                    costs.append(delayed_fee)
            mark = _mark_close(close[:, d], last_close)
            day_nav = cash + float(np.sum(sh * np.where(_price_ok(mark), mark, 0.0)))
            daily_nav[d] = day_nav
            base = last_close_nav if d == last_mark + 1 else daily_nav[d - 1]
            returns.append(day_nav / base - 1.0)
            dates_ix.append(d)
        if min(next_fill, t) > last_mark:
            last_mark = min(next_fill, t) - 1
            if last_mark in daily_nav:
                last_close_nav = daily_nav[last_mark]

    pending |= (sh > 1e-14) & ~_price_ok(close[:, -1])
    sh, cash, pending = _finish_forced_liquidation(
        sh, cash, pending, last_close, cost_rate, returns, turnovers, costs)
    return {
        "returns": np.asarray(returns, float), "return_date_indices": np.asarray(dates_ix, int),
        "turnovers": np.asarray(turnovers, float), "costs": np.asarray(costs, float),
        "active_shares": np.asarray(shares, float), "cap_binds": np.asarray(cap_binds, bool),
        "insufficient_signal_rebalances": int(sum(insufficient_flags)),
        "cumulative_return": float(np.prod(1.0 + np.asarray(returns, float)) - 1.0),
        "sharpe": (float(np.mean(returns) / np.std(returns, ddof=0) * math.sqrt(252))
                   if len(returns) and np.std(returns, ddof=0) else 0.0),
    }


def _simulate_ew(op, close, roster, formation_indices, *, cost_rate):
    """EW30 benchmark with carried close marks and delayed forced sale orders."""
    op = np.asarray(op, float)
    close = np.asarray(close, float)
    roster = np.asarray(roster, bool)
    n, t = close.shape
    formations = [int(x) for x in formation_indices if 0 <= int(x) < t - HORIZON]
    fills = [x + 1 for x in formations if x + 1 < t]
    if len(fills) < 2:
        raise ValueError("at least two complete weekly formation/fill dates are required")
    first_form = formations[0]
    initial_ok = roster[:, first_form] & _price_ok(close[:, first_form])
    if not np.any(initial_ok):
        raise ValueError("no available Dow holdings for initial EW30 staging")
    w0 = np.zeros(n); w0[initial_ok] = 1.0 / initial_ok.sum()
    sh = np.divide(w0, close[:, first_form], out=np.zeros(n), where=initial_ok)
    cash = 0.0
    last_close = np.full(n, np.nan)
    _mark_close(close[:, first_form], last_close)
    last_mark = first_form
    last_close_nav = 1.0
    daily_nav = {first_form: 1.0}
    returns, date_ids, cost_values, turns = [], [], [], []
    pending = np.zeros(n, bool)

    for k, (form, fi) in enumerate(zip(formations, fills)):
        pending |= (sh > 1e-14) & ~_price_ok(close[:, form])
        px = op[:, fi]
        open_valid = _price_ok(px)
        mark_open = np.where(open_valid, px, np.where(_price_ok(last_close), last_close, 0.0))
        nav_before = cash + float(np.sum(sh * mark_open))
        forced_at_fill = pending & open_valid & (sh > 1e-14)
        sh, cash, pending, forced_notional, forced_fee = _execute_pending_open(
            sh, cash, pending, px, cost_rate)
        nav_open = cash + float(np.sum(sh * mark_open))
        if nav_open <= 0:
            raise ValueError("EW30 NAV reached zero")
        current = sh * mark_open / nav_open
        locked = (sh > 1e-14) & ~open_valid
        target = np.zeros(n)
        target[locked] = current[locked]
        available = roster[:, fi] & open_valid & ~forced_at_fill
        remainder = max(0.0, 1.0 - float(target[locked].sum()))
        if np.any(available):
            target[available] = remainder / int(available.sum())
        nav_after = nav_open
        for _ in range(200):
            new_sh = sh.copy()
            new_sh[open_valid] = nav_after * target[open_valid] / px[open_valid]
            notional = float(np.sum(np.abs(new_sh[open_valid] - sh[open_valid]) * px[open_valid]))
            updated = nav_open - cost_rate * notional
            if abs(updated - nav_after) < 1e-13 * max(1.0, nav_open):
                nav_after = updated
                break
            nav_after = updated
        new_sh = sh.copy()
        new_sh[open_valid] = nav_after * target[open_valid] / px[open_valid]
        notional = float(np.sum(np.abs(new_sh[open_valid] - sh[open_valid]) * px[open_valid]))
        cost_values.append(forced_fee + nav_open - nav_after)
        turns.append((forced_notional + notional) / max(nav_before, 1e-12))
        sh = new_sh
        cash = nav_after - float(np.sum(sh * mark_open))
        next_fill = fills[k + 1] if k + 1 < len(fills) else t
        for d in range(max(last_mark + 1, fi), min(next_fill, t)):
            if d > fi:
                valid_open_d = _price_ok(op[:, d])
                open_mark_d = np.where(valid_open_d, op[:, d],
                                       np.where(_price_ok(last_close), last_close, 0.0))
                nav_before_exit = cash + float(np.sum(sh * open_mark_d))
                sh, cash, pending, delayed_notional, delayed_fee = _execute_pending_open(
                    sh, cash, pending, op[:, d], cost_rate)
                if delayed_notional:
                    turns.append(delayed_notional / max(nav_before_exit, 1e-12))
                    cost_values.append(delayed_fee)
            mark = _mark_close(close[:, d], last_close)
            day_nav = cash + float(np.sum(sh * np.where(_price_ok(mark), mark, 0.0)))
            daily_nav[d] = day_nav
            base = last_close_nav if d == last_mark + 1 else daily_nav[d - 1]
            returns.append(day_nav / base - 1.0)
            date_ids.append(d)
        if min(next_fill, t) > last_mark:
            last_mark = min(next_fill, t) - 1
            if last_mark in daily_nav:
                last_close_nav = daily_nav[last_mark]

    pending |= (sh > 1e-14) & ~_price_ok(close[:, -1])
    sh, cash, pending = _finish_forced_liquidation(
        sh, cash, pending, last_close, cost_rate, returns, turns, cost_values)
    return {"returns": np.asarray(returns, float), "return_date_indices": np.asarray(date_ids, int),
            "costs": np.asarray(cost_values, float), "turnovers": np.asarray(turns, float),
            "cumulative_return": float(np.prod(1.0 + np.asarray(returns, float)) - 1.0),
            "sharpe": (float(np.mean(returns) / np.std(returns, ddof=0) * math.sqrt(252))
                       if len(returns) and np.std(returns, ddof=0) else 0.0)}


def _max_drawdown(returns):
    nav = np.r_[1.0, np.cumprod(1.0 + np.asarray(returns, float))]
    peaks = np.maximum.accumulate(nav)
    return float(np.min(nav / peaks - 1.0)) if len(nav) else 0.0


def _portfolio(scores, open_px, close_px, roster, dates, formation_indices, trial_count,
               *, ew_formations=None, skipped_dates=()):
    gross = _simulate_book(scores, open_px, close_px, roster, formation_indices, dates, cost_rate=0.0)
    net = _simulate_book(scores, open_px, close_px, roster, formation_indices, dates, cost_rate=COST_PER_NOTIONAL)
    ew_formations = formation_indices if ew_formations is None else ew_formations
    # Start the EW path on the same first eligible strategy date; after that it
    # rebalances on each scheduled date even if the signal book had to skip it.
    ew_formations = [int(i) for i in ew_formations if int(i) >= int(formation_indices[0])]
    ew_gross = _simulate_ew(open_px, close_px, roster, ew_formations, cost_rate=0.0)
    ew_net = _simulate_ew(open_px, close_px, roster, ew_formations, cost_rate=COST_PER_NOTIONAL)
    if not (np.array_equal(net["return_date_indices"], ew_net["return_date_indices"]) and
            np.array_equal(net["return_date_indices"], gross["return_date_indices"])):
        raise ValueError("strategy and EW30 daily return calendars differ")
    p, boot = circular_block_bootstrap_pvalue(net["returns"], ew_net["returns"],
                                               block_length=BOOTSTRAP_BLOCK,
                                               n_draws=BOOTSTRAP_DRAWS,
                                               seed=BOOTSTRAP_SEED)
    gross_edge = gross["cumulative_return"] - ew_gross["cumulative_return"]
    net_excess = net["cumulative_return"] - ew_net["cumulative_return"]
    incremental_cost = max(0.0, float(np.sum(net["costs"]) - np.sum(ew_net["costs"])))
    cost_ratio = incremental_cost / gross_edge if gross_edge > 0 else None
    return {
        "gross": gross, "net": net, "ew_gross": ew_gross, "ew_net": ew_net,
        "gross_excess_return": float(gross_edge), "net_excess_return": float(net_excess),
        "gross_cumulative_return": float(gross["cumulative_return"]),
        "net_cumulative_return": float(net["cumulative_return"]),
        "ew30_gross_cumulative_return": float(ew_gross["cumulative_return"]),
        "ew30_net_cumulative_return": float(ew_net["cumulative_return"]),
        "net_sharpe": float(net["sharpe"]),
        "ew30_net_sharpe": float(ew_net["sharpe"]),
        "annualized_net_sharpe_vs_ew30": float(net["sharpe"] - ew_net["sharpe"]),
        "mean_turnover": float(np.mean(net["turnovers"])),
        "max_turnover": float(np.max(net["turnovers"])),
        "total_strategy_cost": float(np.sum(net["costs"])),
        "total_ew30_cost": float(np.sum(ew_net["costs"])),
        "average_active_share": float(np.mean(net["active_shares"])),
        "net_max_drawdown": _max_drawdown(net["returns"]),
        "ew30_net_max_drawdown": _max_drawdown(ew_net["returns"]),
        "bootstrap_p_raw": float(p), "bootstrap_distribution": boot,
        "cost_to_gross_edge_ratio": cost_ratio,
        "dsr": float(deflated_sharpe_ratio(net["returns"], trial_count)),
        "trial_count": int(trial_count),
        "turnover_cap_pass": bool(np.max(net["turnovers"]) <= TURNOVER_CAP + 1e-8),
        "active_share_pass": bool(np.mean(net["active_shares"]) >= ACTIVE_SHARE_MIN),
        "net_return_pass": bool(net_excess > 0),
        "sharpe_pass": bool(net["sharpe"] > ew_net["sharpe"]),
        "insufficient_signal_dates_skipped": list(skipped_dates),
    }


def _read_holm(path: str | Path, current_p: dict[str, float | None]) -> dict:
    """Validate and adjust all registered R6 endpoint slots together."""
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    manifest = obj.get("manifest")
    p_values = obj.get("p_values")
    digest = str(obj.get("manifest_sha256", ""))
    if not isinstance(manifest, list) or not manifest or len(set(manifest)) != len(manifest):
        raise ValueError("Holm file must include a unique complete endpoint manifest")
    actual = hashlib.sha256(("\n".join(manifest) + "\n").encode("utf-8")).hexdigest()
    if actual.lower() != digest.lower():
        raise ValueError("Holm manifest hash mismatch")
    if not set(ENDPOINTS).issubset(set(manifest)):
        raise ValueError("Holm manifest must include R6-H7, R6-H8 and R6-H9")
    if not isinstance(p_values, dict) or set(p_values) != set(manifest) - set(ENDPOINTS):
        raise ValueError("Holm p_values must contain all and only other fixed R6 endpoints")
    values = {str(k): float(v) for k, v in p_values.items()}
    for key in ENDPOINTS:
        # Convention for a gate-blocked endpoint: keep its family slot at p=1,
        # but report raw p as null / not run in the endpoint log.
        value = current_p.get(key)
        values[key] = 1.0 if value is None else float(value)
    if any(not 0 <= p <= 1 for p in values.values()):
        raise ValueError("Holm p-values must lie in [0,1]")
    return holm_correction(values)


def _write_endpoint_log(path, endpoints):
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["endpoint", "raw_p", "raw_gate_pass",
                                               "holm_p", "holm_decision", "status", "statistic"])
        writer.writeheader()
        for row in endpoints:
            writer.writerow(row)


def _holm_decision(p_value, *, alpha=0.05):
    """Use the preregistered strict Holm threshold for all reported slots."""
    return "reject" if float(p_value) < alpha else "retain"


def _analyze(bundle, holm_path, feature_path):
    feature_check = validate_feature_bundle(feature_path, bundle)
    sp = bundle["sp500"]
    dow = bundle["dow"]
    sp_start = int(np.searchsorted(sp["dates"], "2020-11-27"))
    if sp_start >= len(sp["dates"]) or sp["dates"][sp_start] != "2020-11-27":
        raise ValueError("S&P calendar must contain the registered first formation date 2020-11-27")
    scores, relative_fwd, mask, scheduled = build_j1_panels(
        sp["adjusted_close"], sp["adjusted_open"], sp["roster"], sp["sic2"],
        formation_start_index=sp_start
    )
    s_scores = scores.copy(); y = relative_fwd.copy(); active = mask.copy()
    active[:, ~scheduled] = False
    ic = _direction_ic(s_scores, y, active, nw_lag=NW_LAG)
    direction_mean = float(ic.mean_ic)
    t_value = float(ic.nw_t)
    direction_t_p = float(norm.sf(t_value))
    mechanism_pass = bool(direction_mean >= COST_IC_FLOOR and t_value >= 2.0)
    placebo = _sic2_shuffle(s_scores, y, active, sp["sic2"], draws=PLACEBO_DRAWS, seed=PLACEBO_SEED)
    mechanism_pass = bool(mechanism_pass and placebo["passed"])

    # Direction-adjusted output is positive because the engine receives -signal.
    h7_raw_pass = bool(direction_mean >= COST_IC_FLOOR and t_value >= 2.0)
    h8_raw_pass = bool(placebo["passed"])
    endpoint_rows = [
        {"endpoint": "R6-H7", "raw_p": direction_t_p, "raw_gate_pass": h7_raw_pass,
         "holm_p": None, "holm_decision": None, "status": "raw_gate",
         "statistic": f"mean_direction_adjusted_IC={direction_mean:.10g}; NW_t_lag4={t_value:.10g}; floor={COST_IC_FLOOR:.10g}"},
        {"endpoint": "R6-H8", "raw_p": placebo["one_sided_p"], "raw_gate_pass": h8_raw_pass,
         "holm_p": None, "holm_decision": None, "status": "raw_gate",
         "statistic": f"observed={placebo['observed']:.10g}; p95={placebo['p95']:.10g}; draws={PLACEBO_DRAWS}; seed={PLACEBO_SEED}"},
        {"endpoint": "R6-H9", "raw_p": None, "raw_gate_pass": None,
         "holm_p": None, "holm_decision": None,
         "status": "not run; mechanism/placebo gate failed",
         "statistic": ""},
    ]
    current_p = {"R6-H7": direction_t_p, "R6-H8": placebo["one_sided_p"], "R6-H9": None}
    portfolio = None
    if mechanism_pass:
        dates = dow["dates"]
        dow_date_to_index = {d: i for i, d in enumerate(dow["dates"])}
        sp_form_dates = set(sp["dates"][np.flatnonzero(scheduled)].tolist())
        dow_form_indices = [dow_date_to_index[d] for d in sorted(sp_form_dates) if d in dow_date_to_index]
        dow_score, _, dow_mask, _ = build_j1_panels(
            dow["adjusted_close"], dow["adjusted_open"], dow["roster"], dow["sic2"],
            formation_start_index=(dow_form_indices[0] if dow_form_indices else 0)
        )
        ew_formations = [i for i in dow_form_indices
                         if i >= LOOKBACK and i + HORIZON < len(dates)]
        # Restrict the signal matrix to the exact S&P-anchored formation dates,
        # even if the two calendars differ due to a missing session.
        allowed_dates = {dates[i] for i in ew_formations}
        dow_mask[:, np.asarray([d not in allowed_dates for d in dates])] = False
        formation_indices = ew_formations
        skipped_dates = [str(dates[i]) for i in ew_formations
                         if int(np.sum(dow_mask[:, i])) < TOP_N]
        portfolio_scores = np.where(dow_mask, -dow_score, np.nan)
        trial_count = _trial_count(TRIAL_LOG)
        portfolio = _portfolio(portfolio_scores, dow["adjusted_open"], dow["adjusted_close"],
                                dow["roster"], dates, formation_indices, trial_count,
                                ew_formations=ew_formations, skipped_dates=skipped_dates)
        current_p["R6-H9"] = float(portfolio["bootstrap_p_raw"])
        endpoint_rows[2] = {
            "endpoint": "R6-H9", "raw_p": portfolio["bootstrap_p_raw"], "raw_gate_pass": None,
            "holm_p": None, "holm_decision": None,
            "status": "holm_tested", "statistic": f"net_excess={portfolio['net_excess_return']:.10g}; bootstrap_draws={BOOTSTRAP_DRAWS}; seed={BOOTSTRAP_SEED}"
        }

    adjusted = _read_holm(holm_path, current_p)
    for row in endpoint_rows:
        row["holm_p"] = adjusted[row["endpoint"]]["holm_p"]
        # Keep raw H7/H8 progression distinct from the family-wise endpoint
        # decision. H9's registered pass threshold is strictly Holm p < .05.
        row["holm_decision"] = _holm_decision(row["holm_p"])
        if row["endpoint"] == "R6-H9" and row["status"] == "holm_tested":
            row["status"] = "pass" if (row["holm_p"] < 0.05 and portfolio and
                                          portfolio["net_return_pass"] and portfolio["sharpe_pass"] and
                                          portfolio["turnover_cap_pass"] and portfolio["active_share_pass"]) else "fail"
    if portfolio is not None:
        portfolio["holm_p"] = adjusted["R6-H9"]["holm_p"]
        portfolio["pass"] = bool(portfolio["net_return_pass"] and portfolio["sharpe_pass"] and
                                  portfolio["turnover_cap_pass"] and portfolio["active_share_pass"] and
                                  adjusted["R6-H9"]["holm_p"] < 0.05)
    return {
        "approach": "J1", "variant": "J1-V1", "passed": bool(portfolio and portfolio["pass"]),
        "prereg_sha256": prereg_digest(PREREG.read_text(encoding="utf-8")),
        "mechanism": {"passed": mechanism_pass, "mean_direction_adjusted_ic": direction_mean,
                      "mean_raw_ic": -direction_mean, "nw_t_lag4_direction_adjusted": t_value,
                      "one_sided_nw_p_raw": direction_t_p,
                      "ic_floor": COST_IC_FLOOR, "ic_dates": ic.ic_by_date.tolist(),
                      "eligible_names_by_date": ic.n_assets_by_date.tolist()},
        "placebo": {"passed": placebo["passed"], "observed_direction_adjusted_mean_ic": placebo["observed"],
                    "p95": placebo["p95"], "randomization_p_raw": placebo["one_sided_p"],
                    "seed": PLACEBO_SEED, "draws": PLACEBO_DRAWS,
                    "all_draw_means": placebo["draws"].tolist()},
        "portfolio": portfolio,
        "l3_signal_bundle_verification": feature_check,
        "endpoints": endpoint_rows,
        "holm_family": {k: {"raw_p": (None if current_p.get(k) is None else current_p[k]),
                             "holm_input_p": adjusted[k]["raw_p"],
                             "holm_p": adjusted[k]["holm_p"],
                             "holm_decision": _holm_decision(adjusted[k]["holm_p"]),
                             "raw_gate_pass": ({"R6-H7": h7_raw_pass, "R6-H8": h8_raw_pass}.get(k)),
                             "raw_p_reported": (None if current_p.get(k) is None else current_p[k]),
                             "ran": current_p.get(k) is not None}
                        for k in adjusted},
    }


def _trial_count(path):
    import re
    text = Path(path).read_text(encoding="utf-8")
    # The explicit R6 manifest is authoritative. The numbered trial table also
    # contains legacy R4/R5 experiments and must not inflate this count.
    variants = set(re.findall(
        r"^\s*-\s*R6\s+variant\s+\d+\s*:\s*([A-Za-z0-9_-]+)\s*$",
        text, re.M | re.I))
    if "J1-V1" not in variants:
        raise ValueError("R6 trial manifest must include J1-V1 before DSR calculation")
    return len(variants)


def _save_outputs(result, output_path=OUTPUT):
    def clean(value):
        if isinstance(value, dict):
            return {str(k): clean(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [clean(v) for v in value]
        if isinstance(value, np.ndarray):
            return clean(value.tolist())
        if isinstance(value, (np.bool_, bool)):
            return bool(value)
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, (np.floating, float)):
            return float(value) if math.isfinite(float(value)) else None
        return value
    Path(output_path).write_text(json.dumps(clean(result), indent=2, allow_nan=False), encoding="utf-8")
    _write_endpoint_log(ENDPOINT_LOG, result["endpoints"])
    if result["mechanism"]["passed"]:
        MECHANISM_FAIL.unlink(missing_ok=True)
        MECHANISM_PASS.write_text(json.dumps({
            "approach": "J1", "passed": True, "prereg_sha256": result["prereg_sha256"],
            "mean_ic": result["mechanism"]["mean_raw_ic"],
            "nw_t_lag4": -result["mechanism"]["nw_t_lag4_direction_adjusted"],
            "direction_adjusted_mean_ic": result["mechanism"]["mean_direction_adjusted_ic"],
            "ic_floor": result["mechanism"]["ic_floor"],
            "placebo_passed": result["placebo"]["passed"],
        }, indent=2), encoding="utf-8")
    else:
        MECHANISM_PASS.unlink(missing_ok=True)
        MECHANISM_FAIL.write_text(json.dumps({
            "approach": "J1", "passed": False, "prereg_sha256": result["prereg_sha256"],
            "mean_ic": result["mechanism"]["mean_raw_ic"],
            "nw_t_lag4": -result["mechanism"]["nw_t_lag4_direction_adjusted"],
            "reason": "registered direction, cost floor, NW t, or SIC2 shuffle gate failed",
        }, indent=2), encoding="utf-8")


def _load_verified_bundle(input_path, feature_path, **coverage_options):
    """Run input-only QA first, and only then load matrices used for labels."""
    coverage_check = verify_input_coverage(input_path, feature_path, **coverage_options)
    return load_bundle(input_path), coverage_check


@guarded_runner(prereg_path=PREREG, run_dir=HERE)
def _guarded_run(input_path, feature_path, holm_path, output_path=OUTPUT):
    # Verify the published input-only gate before opening/building any forward
    # labels. The verifier reads hashes and count manifests only.
    bundle, coverage_check = _load_verified_bundle(input_path, feature_path)
    result_box = {}

    def callback():
        result = _analyze(bundle, holm_path, feature_path)
        result["input_coverage_verification"] = coverage_check
        _save_outputs(result, output_path)
        result_box["result"] = result
        return (f"J1-V1: mechanism={result['mechanism']['passed']}; "
                f"mean_raw_IC={result['mechanism']['mean_raw_ic']:.10g}; "
                f"direction_adjusted_NW_t={result['mechanism']['nw_t_lag4_direction_adjusted']:.8g}; "
                f"portfolio={bool(result['portfolio'] and result['portfolio']['pass'])}")

    run_registered_trial("J1", "J1-V1 weekly SIC2-relative reversal", callback,
                         prereg_dir=PREREG.parent, trial_log=TRIAL_LOG)
    return result_box["result"]


def _main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="explicit coordinator authorization after freeze and input QA")
    parser.add_argument("--inputs", type=Path, default=INPUTS)
    parser.add_argument("--features", type=Path, default=FEATURES,
                        help="L3 formation-level signal_bundle.parquet for input-feature cross-check")
    parser.add_argument("--holm-family", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = _guarded_run(args.inputs, args.features, args.holm_family, args.output,
                              execute=args.execute)
        print(json.dumps({"approach": "J1", "passed": result["passed"],
                          "mechanism_passed": result["mechanism"]["passed"],
                          "portfolio_run": result["portfolio"] is not None,
                          "endpoints": [r["endpoint"] for r in result["endpoints"]]}, indent=2))
        return 0 if result["passed"] else 1
    except Exception as exc:
        print(f"J1 refused/failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(_main())
