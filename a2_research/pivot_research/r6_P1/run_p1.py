"""Guarded, one-variant P1 runner. Synthetic helpers are safe to import."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from r4_harness.ic_engine import cross_sectional_ic
from r4_harness.phase3 import (
    break_even_rank_ic, circular_block_bootstrap_pvalue,
    deflated_sharpe_ratio, holm_correction, newey_west_t, prereg_digest,
)
from r4_harness.prereg_diff import prereg_diff
from r4_harness.runner_guard import guarded_runner, validate_frozen_prereg
from r6_P1.build_inputs import LOOKBACK_SESSIONS

PREREG = ROOT / "specs" / "r6_prereg" / "P1.md"
TRIAL_LOG = ROOT / "specs" / "r4_trials.md"
HOLM_CONFIG = ROOT / "specs" / "r6_holm_family.json"
SIGNALS = HERE / "P1_signal_inputs.parquet"
DAILY_PRICES = HERE / "P1_daily_prices.parquet"
COVERAGE = HERE / "coverage_by_formation.csv"
INPUT_MANIFEST = HERE / "INPUT_MANIFEST.json"
DIFF_SOURCE = HERE / "P1_PREREG_DIFF_SOURCE.md"
DIFF_CONFIG_PATH = HERE / "prereg_diff_config.json"
RUN_DIR = HERE / "run"

LOOKBACK = 21
HORIZON_MONTHS = 1
NW_LAG = 1
PLACEBO_DRAWS = 500
BOOTSTRAP_DRAWS = 5000
BOOTSTRAP_BLOCK = 10
SEED = 20261111
TURNOVER_CAP = 0.50
COST_PER_SIDE = 0.0005
ACTIVE_SHARE_MIN = 0.50
TOP_N = 5
MIN_SP500_NAMES = 250
RETURN_DISPERSION = 0.10
TOP_FRACTION = TOP_N / 30.0
# The preregistered hurdle is published to ten decimal places; compare against
# that declared value rather than a hidden higher-precision helper result.
IC_FLOOR = float(f"{break_even_rank_ic(TURNOVER_CAP, RETURN_DISPERSION, COST_PER_SIDE, TOP_FRACTION):.10f}")
ENDPOINTS = ("R6-H13", "R6-H14", "R6-H15")
FORMATION_COUNT = 70
EXPECTED_INPUT_MANIFEST_SHA256 = "ebe1ee185f77aa3aac12e4eeac631c28c0cdcde4a7187a6755c37b303230a799"

RUNNER_SPEC_CONFIG = {
    "window": LOOKBACK,
    "formation_count": FORMATION_COUNT,
    "horizon": 1,
    "nw_lag": NW_LAG,
    "draws": [PLACEBO_DRAWS, BOOTSTRAP_DRAWS],
    "block_length": BOOTSTRAP_BLOCK,
    "seed": SEED,
    "turnover_limit": TURNOVER_CAP,
    "cost_per_side": COST_PER_SIDE,
    "top_n": TOP_N,
    "top_fraction": TOP_FRACTION,
    "return_dispersion": RETURN_DISPERSION,
    "cost_floor_diagnostic": IC_FLOOR,
    "min_t": 2,
    "active_share_min": ACTIVE_SHARE_MIN,
    "alpha": 0.05,
    "percentile": 95,
    "endpoint_ids": [1, 2, 3],
    "endpoint_count": 3,
}


class InputGateError(RuntimeError):
    """Input provenance or signal-coverage gate failed."""


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prereg_diff_payload():
    """Compare normalized registered settings with the code declarations."""
    return prereg_diff(DIFF_SOURCE, RUNNER_SPEC_CONFIG)


def verify_input_manifest(manifest_path=INPUT_MANIFEST, *, signal_path=SIGNALS,
                          daily_path=DAILY_PRICES, coverage_path=COVERAGE,
                          expected_manifest_sha=EXPECTED_INPUT_MANIFEST_SHA256,
                          minimum_names=MIN_SP500_NAMES) -> dict:
    """Fail closed on pinned input bytes and coverage before label creation."""
    required = (manifest_path, signal_path, daily_path, coverage_path)
    if any(not Path(p).is_file() for p in required):
        raise FileNotFoundError("P1 signal, daily-price, coverage, and manifest inputs must all exist")
    manifest_hash = _sha256(manifest_path)
    if manifest_hash != expected_manifest_sha:
        raise InputGateError("P1 input manifest does not match the runner's reviewed SHA256")
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("scope") != "input-only adjusted daily bars and trailing signals; no forward labels or outcomes":
        raise InputGateError("manifest is not the required input-only build")
    if manifest.get("development_window") != ["2020-06-01", "2026-10-30"]:
        raise InputGateError("manifest has an invalid development-only boundary")
    if manifest.get("formation_window") != ["2020-12", "2026-09"] or manifest.get("formation_count") != FORMATION_COUNT:
        raise InputGateError("manifest formation range differs from P1")
    if manifest.get("forward_labels_built") is not False or manifest.get("holdout_loaded") is not False:
        raise InputGateError("input manifest must attest that no labels or holdout data were built")
    for key, path in (("signal_bundle", signal_path), ("daily_price_bundle", daily_path), ("coverage_table", coverage_path)):
        entry = manifest.get(key, {})
        if entry.get("sha256") != _sha256(path):
            raise InputGateError(f"{key} SHA256 differs from input manifest")

    coverage = pd.read_csv(coverage_path)
    expected_cols = {"universe", "formation_date", "pit_members", "valid_21_session_signals", "gate_250_names"}
    if not expected_cols.issubset(coverage.columns):
        raise InputGateError(f"coverage table missing required fields: {sorted(expected_cols - set(coverage.columns))}")
    for universe in ("SP500", "DOW"):
        subset = coverage.loc[coverage.universe.eq(universe)]
        if len(subset) != FORMATION_COUNT or subset.formation_date.nunique() != FORMATION_COUNT:
            raise InputGateError(f"{universe} coverage must contain {FORMATION_COUNT} unique monthly formations")
    sp = coverage.loc[coverage.universe.eq("SP500")]
    expected_gate = sp.valid_21_session_signals.astype(int).ge(minimum_names)
    if not np.array_equal(expected_gate.to_numpy(), sp.gate_250_names.astype(bool).to_numpy()):
        raise InputGateError("S&P 500 250-name flags disagree with valid-signal counts")
    gate_dates = int(expected_gate.sum())
    if gate_dates < math.ceil(0.80 * len(sp)):
        raise InputGateError("S&P 500 signal coverage misses the preregistered 250-name date gate")
    return {
        "verified": True,
        "manifest_sha256": manifest_hash,
        "formations": FORMATION_COUNT,
        "sp500_dates_ge_250": gate_dates,
        "sp500_coverage_fraction": gate_dates / len(sp),
        "minimum_sp500_signal_names": int(sp.valid_21_session_signals.min()),
        "forward_labels_built": False,
    }


def build_forward_labels(signal_frame: pd.DataFrame, daily_frame: pd.DataFrame) -> pd.DataFrame:
    """Construct next-calendar-month open-to-close labels for eligible rows.

    The caller must verify the input manifest first. The returned cohort is
    fixed by PIT formation membership, a complete signal, SIC2, and both
    endpoint bars; signal-ineligible peers cannot enter the benchmark cohort.
    """
    required_signal = {"universe", "formation_date", "ticker", "member", "overnight_momentum_21s", "signal_valid", "sic2", "sic_valid"}
    required_daily = {"universe", "date", "ticker", "member", "adjusted_open", "adjusted_close"}
    if not required_signal.issubset(signal_frame.columns) or not required_daily.issubset(daily_frame.columns):
        raise ValueError("P1 input tables do not match their documented schemas")
    signal = signal_frame.copy()
    daily = daily_frame.copy()
    signal["formation_date"] = pd.to_datetime(signal.formation_date).dt.normalize()
    daily["date"] = pd.to_datetime(daily.date).dt.normalize()
    if daily.date.min() < pd.Timestamp("2020-06-01") or daily.date.max() > pd.Timestamp("2026-10-30"):
        raise ValueError("daily price panel must remain inside the development date window")
    rows = []
    for (universe, formation), cohort in signal.groupby(["universe", "formation_date"], sort=True):
        next_month = formation.to_period("M") + 1
        month = daily.loc[
            daily.universe.eq(universe) & daily.date.dt.to_period("M").eq(next_month)
        ]
        sessions = np.sort(month.date.unique())
        if len(sessions) == 0:
            continue
        first, last = pd.Timestamp(sessions[0]), pd.Timestamp(sessions[-1])
        first_open = month.loc[month.date.eq(first), ["ticker", "member", "adjusted_open"]].set_index("ticker")
        last_close = month.loc[month.date.eq(last), ["ticker", "member", "adjusted_close"]].set_index("ticker")
        for row in cohort.itertuples(index=False):
            if not bool(row.member) or not bool(row.signal_valid) or not bool(row.sic_valid):
                continue
            ticker = str(row.ticker)
            if ticker not in first_open.index or ticker not in last_close.index:
                continue
            fo = first_open.loc[ticker]
            lc = last_close.loc[ticker]
            if not bool(fo.member) or not bool(lc.member):
                continue
            op, close = float(fo.adjusted_open), float(lc.adjusted_close)
            if not (np.isfinite(op) and op > 0 and np.isfinite(close) and close > 0):
                continue
            rows.append({
                "universe": universe, "formation_date": formation, "ticker": ticker,
                "sic2": str(row.sic2), "score": float(row.overnight_momentum_21s),
                "forward_return": close / op - 1.0,
                "first_session": first, "last_session": last,
                "eligible": True,
            })
    return pd.DataFrame(rows)


def verified_forward_labels(manifest_path=INPUT_MANIFEST, signal_path=SIGNALS,
                            daily_path=DAILY_PRICES, coverage_path=COVERAGE,
                            *, verifier=verify_input_manifest,
                            label_builder=build_forward_labels,
                            pre_label_check=None) -> tuple[dict, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Open staged inputs and build labels only after the input gate succeeds."""
    gate = verifier(manifest_path, signal_path=signal_path,
                    daily_path=daily_path, coverage_path=coverage_path)
    if pre_label_check is not None:
        pre_label_check()
    signal_frame = pd.read_parquet(signal_path)
    daily_frame = pd.read_parquet(daily_path)
    labels = label_builder(signal_frame, daily_frame)
    return gate, signal_frame, daily_frame, labels


def _cross_section_matrices(labels: pd.DataFrame, universe: str, formation_dates=None):
    frame = labels.loc[labels.universe.eq(universe)].copy()
    dates = (sorted(pd.to_datetime(frame.formation_date).unique()) if formation_dates is None
             else sorted(pd.to_datetime(formation_dates).unique()))
    names = sorted(frame.ticker.astype(str).unique())
    score = np.full((len(names), len(dates)), np.nan)
    forward = np.full_like(score, np.nan)
    sic = np.full(score.shape, "", dtype=object)
    mask = np.zeros(score.shape, dtype=bool)
    ni, di = {x: i for i, x in enumerate(names)}, {x: i for i, x in enumerate(dates)}
    for row in frame.itertuples(index=False):
        i, j = ni[str(row.ticker)], di[pd.Timestamp(row.formation_date)]
        score[i, j], forward[i, j] = float(row.score), float(row.forward_return)
        sic[i, j], mask[i, j] = str(row.sic2), True
    return names, dates, score, forward, sic, mask


def mechanism(labels: pd.DataFrame, formation_dates=None) -> dict:
    names, dates, score, forward, _, mask = _cross_section_matrices(labels, "SP500", formation_dates)
    result = cross_sectional_ic(score, forward, mask, nw_lag=NW_LAG)
    finite = result.ic_by_date[np.isfinite(result.ic_by_date)]
    p = float(student_t.sf(result.nw_t, max(len(finite) - 1, 1)))
    passed = bool(len(finite) >= 2 and result.mean_ic > 0 and result.nw_t >= 2.0)
    return {
        "dates": [pd.Timestamp(d).strftime("%Y-%m-%d") for d in dates],
        "eligible_names_by_date": result.n_assets_by_date.tolist(),
        "ic_by_date": result.ic_by_date.tolist(), "mean_ic": result.mean_ic,
        "nw_lag_months": NW_LAG, "nw_t": result.nw_t, "raw_one_sided_p": p,
        "ic_floor_diagnostic": IC_FLOOR,
        "mean_ic_above_cost_floor_diagnostic": bool(result.mean_ic >= IC_FLOOR),
        "raw_gate_status": "pass" if passed else "fail",
        "raw_gate_pass": passed,
    }


def sic2_shuffle_placebo(labels: pd.DataFrame, *, draws=PLACEBO_DRAWS, seed=SEED,
                         formation_dates=None) -> dict:
    names, dates, score, forward, sic, mask = _cross_section_matrices(labels, "SP500", formation_dates)
    observed = cross_sectional_ic(score, forward, mask).mean_ic
    if not np.isfinite(observed):
        raise ValueError("no finite observed S&P 500 IC for placebo")
    rng = np.random.default_rng(seed)
    null = np.empty(draws)
    for b in range(draws):
        shuffled = score.copy()
        for j in range(score.shape[1]):
            for code in sorted(set(sic[:, j][mask[:, j]]) - {"", "nan", "None"}):
                ix = np.flatnonzero(mask[:, j] & (sic[:, j] == code))
                if len(ix) > 1:
                    shuffled[ix, j] = rng.permutation(score[ix, j])
        ic = cross_sectional_ic(shuffled, forward, mask).mean_ic
        null[b] = ic
    p = (1 + int(np.sum(null >= observed))) / (draws + 1)
    p95 = float(np.quantile(null, 0.95))
    passed = bool(observed > p95 and p < 0.05)
    return {
        "observed_mean_ic": float(observed), "draws": null,
        "draw_count": int(draws), "seed": int(seed), "null_p95": p95,
        "raw_one_sided_p": float(p), "raw_gate_status": "pass" if passed else "fail",
        "raw_gate_pass": passed,
    }


def _price_ok(values):
    values = np.asarray(values, float)
    return np.isfinite(values) & (values > 0)


def stale_close_marks(last_close: np.ndarray, current_close: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Carry last valid close; subsequent valid closes catch up from that mark."""
    last = np.asarray(last_close, float).copy()
    close = np.asarray(current_close, float)
    valid = _price_ok(close)
    last[valid] = close[valid]
    return last, valid


def select_weights(signal_by_name: dict[str, float], daily_members: dict[str, bool],
                   open_by_name: dict[str, float], *, top_n=TOP_N) -> tuple[dict[str, float], dict]:
    """Select at the open from the benchmark's open-available PIT cohort only."""
    benchmark_names = sorted(
        name for name, member in daily_members.items()
        if member and np.isfinite(open_by_name.get(name, np.nan)) and open_by_name[name] > 0
    )
    n = len(benchmark_names)
    k = min(int(top_n), n // 2)
    candidates = [name for name in benchmark_names if np.isfinite(signal_by_name.get(name, np.nan))]
    selected = sorted(candidates, key=lambda name: (-float(signal_by_name[name]), name))[:k]
    target = {name: 0.0 for name in daily_members}
    if selected:
        for name in selected:
            target[name] = 1.0 / len(selected)
    benchmark = {name: 0.0 for name in daily_members}
    if n:
        for name in benchmark_names:
            benchmark[name] = 1.0 / n
    active_share = 0.5 * sum(abs(target.get(name, 0.0) - benchmark.get(name, 0.0)) for name in daily_members)
    return target, {"benchmark_names": benchmark_names, "benchmark_n": n, "k": k,
                    "selected": selected, "benchmark_weights": benchmark,
                    "active_share": active_share}


def simulate_book(dates, names, open_px, close_px, roster, scores_by_fill,
                  *, equal_weight=False, cost_per_side=COST_PER_SIDE,
                  turnover_cap=TURNOVER_CAP) -> dict:
    """Daily marked portfolio with next-open trades and stale-price liquidation.

    ``scores_by_fill`` maps an execution date index to the preceding formation's
    signal dictionary. Selection uses current roster and open bars only.
    """
    dates = np.asarray(dates).astype(str)
    names = list(map(str, names))
    op, close, roster = np.asarray(open_px, float), np.asarray(close_px, float), np.asarray(roster, bool)
    n, t = op.shape
    if close.shape != op.shape or roster.shape != op.shape or len(names) != n or len(dates) != t:
        raise ValueError("portfolio arrays must align as names × sessions")
    if not scores_by_fill:
        raise ValueError("at least one next-open formation is required")
    first_fill = min(scores_by_fill)
    if first_fill <= 0 or first_fill >= t:
        raise ValueError("fill must have a prior close and be within the calendar")
    last_close = close[:, first_fill - 1].copy()
    last_close[~_price_ok(last_close)] = np.nan
    start_available = roster[:, first_fill - 1] & _price_ok(last_close)
    weights = np.zeros(n)
    if start_available.any():
        weights[start_available] = 1.0 / int(start_available.sum())
    cash_weight = 1.0 - float(weights.sum())
    pending = np.zeros(n, bool)
    nav = 1.0
    returns, turnovers, costs, active_shares, bind_flags = [], [], [], [], []
    daily_dates, benchmark_weights, selected_names = [], [], []
    terminal_fallback = 0

    for d in range(first_fill, t):
        open_ok = _price_ok(op[:, d])
        open_mark = np.where(open_ok, op[:, d], np.where(_price_ok(last_close), last_close, 0.0))
        prior_marks = np.where(_price_ok(last_close), last_close, open_mark)
        gap_factor = np.ones(n)
        can_gap = (weights > 0) & _price_ok(open_mark) & _price_ok(prior_marks)
        gap_factor[can_gap] = open_mark[can_gap] / prior_marks[can_gap]
        overnight_growth = float(cash_weight + np.sum(weights * gap_factor))
        if not np.isfinite(overnight_growth) or overnight_growth <= 0:
            raise ValueError("portfolio NAV became nonpositive at open")
        nav_open = nav * overnight_growth
        open_weights = np.divide(weights * gap_factor, overnight_growth,
                                  out=np.zeros_like(weights), where=overnight_growth > 0)
        cash_open = cash_weight / overnight_growth

        # Decision 63: sell a stale holding at its next valid open; unavailable
        # names remain locked and marked until a later valid open.
        forced = pending & open_ok & (open_weights > 1e-14)
        forced_turnover = float(open_weights[forced].sum())
        if forced_turnover:
            cash_open += forced_turnover * (1.0 - cost_per_side)
            open_weights[forced] = 0.0
        pending[forced] = False

        month_signal = scores_by_fill.get(d)
        traded_turnover = 0.0
        day_active_share = np.nan
        day_benchmark = np.zeros(n)
        day_selected = []
        if month_signal is not None:
            daily_members = {name: bool(roster[i, d]) for i, name in enumerate(names)}
            open_by_name = {name: float(op[i, d]) for i, name in enumerate(names)}
            if equal_weight:
                target_by_name, info = select_weights({}, daily_members, open_by_name, top_n=TOP_N)
                # Benchmark is EW over the entire opening-price-available cohort.
                target_by_name = info["benchmark_weights"]
                day_active_share = 0.0
            else:
                target_by_name, info = select_weights(month_signal, daily_members, open_by_name, top_n=TOP_N)
                day_active_share = float(info["active_share"])
                day_selected = info["selected"]
            target = np.array([target_by_name.get(name, 0.0) for name in names], float)
            if equal_weight:
                day_benchmark = target.copy()
            else:
                day_benchmark = np.array([info["benchmark_weights"].get(name, 0.0) for name in names], float)
            locked = (open_weights > 1e-14) & ~open_ok
            target[locked] = open_weights[locked]
            free = open_ok
            remaining = max(0.0, 1.0 - float(target[locked].sum()))
            target_mass = float(target[free].sum())
            if target_mass > 0:
                target[free] *= remaining / target_mass
            else:
                target[free] = 0.0
                cash_open = max(0.0, 1.0 - float(open_weights[locked].sum()))
            delta = target - open_weights
            delta[~open_ok] = 0.0
            full = float(np.abs(delta).sum()) + forced_turnover
            scale = min(1.0, max(0.0, (turnover_cap - forced_turnover) / float(np.abs(delta).sum()))) if np.abs(delta).sum() else 1.0
            new_weights = open_weights + scale * delta
            traded_turnover = float(np.abs(new_weights - open_weights).sum())
            total_turn = traded_turnover + forced_turnover
            fee = cost_per_side * total_turn
            if total_turn > turnover_cap + 1e-9:
                raise ArithmeticError("portfolio turnover cap exceeded")
            if fee:
                nav_open *= 1.0 - fee
            # Costs are charged to NAV; normalize position weights back to the
            # post-cost NAV and keep any uninvested residual in cash.
            weights = new_weights.copy()
            cash_weight = max(0.0, 1.0 - float(weights.sum()))
            denom = float(weights.sum() + cash_weight)
            weights /= denom
            cash_weight /= denom
            traded_turnover = total_turn
            turnovers.append(total_turn)
            costs.append(fee * nav)
            active_shares.append(day_active_share)
            bind_flags.append(bool(total_turn >= turnover_cap - 1e-8))
            selected_names.append(day_selected)
        else:
            weights = open_weights
            cash_weight = cash_open
            fee = cost_per_side * forced_turnover
            if forced_turnover:
                nav_open *= 1.0 - fee
                turnovers.append(forced_turnover)
                costs.append(fee * nav)
                active_shares.append(np.nan)
                bind_flags.append(False)
                selected_names.append([])

        # Mark close with last-valid-close carry; a resumed close catches up
        # from the stale mark because close/open return is measured vs that mark.
        close_mark, close_valid = stale_close_marks(last_close, close[:, d])
        close_ratio = np.ones(n)
        intraday_ok = _price_ok(open_mark) & _price_ok(close_mark)
        close_ratio[intraday_ok] = close_mark[intraday_ok] / open_mark[intraday_ok]
        close_growth = float(cash_weight + np.sum(weights * close_ratio))
        day_nav = nav_open * close_growth
        if not np.isfinite(day_nav) or day_nav <= 0:
            raise ValueError("portfolio NAV became nonpositive at close")
        returns.append(day_nav / nav - 1.0)
        daily_dates.append(dates[d])
        pending |= (weights > 1e-14) & ~close_valid
        close_value = weights * close_ratio
        close_total = float(cash_weight + close_value.sum())
        if close_total > 0:
            weights = close_value / close_total
            cash_weight /= close_total
        last_close = close_mark
        nav = day_nav

    # If no later valid open occurs, settle any stale holding at its last valid
    # close and charge the exit cost on the final observation.
    terminal = pending & (weights > 1e-14)
    terminal_fallback = int(terminal.sum())
    terminal_turnover = float(weights[terminal].sum())
    if terminal_turnover and returns:
        terminal_fee = cost_per_side * terminal_turnover
        returns[-1] = (1.0 + returns[-1]) * (1.0 - terminal_fee) - 1.0
        costs.append(terminal_fee * nav)
        turnovers.append(terminal_turnover)
    arr = np.asarray(returns, float)
    return {
        "returns": arr, "dates": daily_dates, "turnovers": np.asarray(turnovers),
        "costs": np.asarray(costs), "active_shares": np.asarray(active_shares),
        "cap_bind_flags": np.asarray(bind_flags), "selected_names": selected_names,
        "terminal_stale_fallback_names": terminal_fallback,
        "cumulative_return": float(np.prod(1.0 + arr) - 1.0),
        "sharpe": float(np.mean(arr) / np.std(arr, ddof=1) * np.sqrt(252)) if len(arr) > 1 and np.std(arr, ddof=1) else 0.0,
        "mean_turnover": float(np.mean(turnovers)) if turnovers else 0.0,
        "max_turnover": float(np.max(turnovers)) if turnovers else 0.0,
        "mean_active_share": float(np.nanmean(active_shares)) if np.isfinite(active_shares).any() else 0.0,
        "total_cost": float(np.sum(costs)),
    }


def _daily_arrays(daily: pd.DataFrame, universe="DOW"):
    frame = daily.loc[daily.universe.eq(universe)].copy()
    dates = sorted(pd.to_datetime(frame.date).dt.normalize().unique())
    names = sorted(frame.ticker.astype(str).unique())
    name_ix, date_ix = {x: i for i, x in enumerate(names)}, {pd.Timestamp(x): i for i, x in enumerate(dates)}
    op = np.full((len(names), len(dates)), np.nan)
    close = np.full_like(op, np.nan)
    roster = np.zeros(op.shape, dtype=bool)
    for row in frame.itertuples(index=False):
        i, j = name_ix[str(row.ticker)], date_ix[pd.Timestamp(row.date).normalize()]
        op[i, j], close[i, j], roster[i, j] = row.adjusted_open, row.adjusted_close, bool(row.member)
    return names, np.asarray(dates, dtype="datetime64[ns]").astype(str), op, close, roster


def portfolio(signal_frame: pd.DataFrame, daily: pd.DataFrame, trial_count: int) -> dict:
    names, dates, op, close, roster = _daily_arrays(daily, "DOW")
    date_ix = {x: i for i, x in enumerate(dates)}
    # Use final observed session each month as formation and first session of
    # the following month as the next-open execution date.
    calendar = pd.to_datetime(dates)
    dow_signals = signal_frame.loc[
        signal_frame.universe.eq("DOW") & signal_frame.signal_valid.astype(bool)
        & signal_frame.member.astype(bool)
    ].copy()
    scores_by_fill = {}
    for formation, rows in dow_signals.groupby("formation_date", sort=True):
        form = pd.Timestamp(formation).strftime("%Y-%m-%d")
        if form not in date_ix:
            continue
        next_period = pd.Timestamp(formation).to_period("M") + 1
        first_next = next((str(d) for d in dates if pd.Period(d[:7], freq="M") == next_period), None)
        if first_next is None:
            continue
        fill_ix = date_ix[first_next]
        scores_by_fill[fill_ix] = {str(r.ticker): float(r.score) for r in rows.itertuples(index=False)}
    if not scores_by_fill:
        raise ValueError("no complete Dow formation-to-next-month fills")
    strategy = simulate_book(dates, names, op, close, roster, scores_by_fill, equal_weight=False)
    benchmark = simulate_book(dates, names, op, close, roster, scores_by_fill, equal_weight=True, turnover_cap=1.0)
    if strategy["dates"] != benchmark["dates"]:
        raise ValueError("strategy and EW30 daily calendars differ")
    p, boot = circular_block_bootstrap_pvalue(
        strategy["returns"], benchmark["returns"], block_length=BOOTSTRAP_BLOCK,
        n_draws=BOOTSTRAP_DRAWS, seed=SEED,
    )
    gross_strategy = simulate_book(dates, names, op, close, roster, scores_by_fill,
                                    equal_weight=False, cost_per_side=0.0)
    gross_benchmark = simulate_book(dates, names, op, close, roster, scores_by_fill,
                                    equal_weight=True, cost_per_side=0.0, turnover_cap=1.0)
    net_excess = strategy["cumulative_return"] - benchmark["cumulative_return"]
    gross_excess = gross_strategy["cumulative_return"] - gross_benchmark["cumulative_return"]
    active = strategy["mean_active_share"]
    nav_path = np.cumprod(1.0 + strategy["returns"])
    peaks = np.maximum.accumulate(np.r_[1.0, nav_path])[1:]
    drawdown = float(np.min(nav_path / peaks - 1.0)) if len(nav_path) else 0.0
    return {
        "strategy_net_cumulative": strategy["cumulative_return"],
        "benchmark_net_cumulative": benchmark["cumulative_return"],
        "strategy_gross_cumulative": gross_strategy["cumulative_return"],
        "benchmark_gross_cumulative": gross_benchmark["cumulative_return"],
        "net_excess_cumulative": net_excess, "gross_excess_cumulative": gross_excess,
        "strategy_net_sharpe": strategy["sharpe"], "benchmark_net_sharpe": benchmark["sharpe"],
        "strategy_net_max_drawdown": drawdown,
        "bootstrap_p_raw": p, "bootstrap_draws": boot,
        "turnover_mean": strategy["mean_turnover"], "turnover_max": strategy["max_turnover"],
        "turnover_cap_bind_count": int(strategy["cap_bind_flags"].sum()),
        "turnover_cap": TURNOVER_CAP, "turnover_cap_pass": strategy["max_turnover"] <= TURNOVER_CAP + 1e-8,
        "active_share_mean": active, "active_share_pass": active >= ACTIVE_SHARE_MIN,
        "cost_total": strategy["total_cost"], "benchmark_cost_total": benchmark["total_cost"],
        "cost_gross_edge_ratio": strategy["total_cost"] / gross_excess if gross_excess > 0 else None,
        "terminal_stale_fallback_names_strategy": strategy["terminal_stale_fallback_names"],
        "terminal_stale_fallback_names_benchmark": benchmark["terminal_stale_fallback_names"],
        "dsr": deflated_sharpe_ratio(strategy["returns"], trial_count),
        "trial_count": int(trial_count),
        "daily_returns_strategy": strategy["returns"], "daily_returns_benchmark": benchmark["returns"],
        "daily_dates": strategy["dates"],
    }


def _trial_count(path=TRIAL_LOG) -> int:
    text = Path(path).read_text(encoding="utf-8")
    variants = set(re.findall(r"^\s*-\s*R6\s+variant\s+\d+\s*:\s*([A-Za-z0-9_-]+)\s*$", text, re.M | re.I))
    if "P1-V1" not in variants:
        raise ValueError("P1-V1 must be logged in specs/r4_trials.md before execution")
    return len(variants)


def holm_results(current_p: dict[str, float | None], config_path=HOLM_CONFIG) -> dict:
    """Adjust raw p-values across all 15 R6 slots, preserving not-run slots."""
    cfg = validate_holm_family(config_path)
    expected = {f"R6-H{i}" for i in range(1, 16)}
    source_p = cfg["p_values"]
    raw_family = {k: (1.0 if v is None else float(v)) for k, v in source_p.items()}
    for endpoint in ENDPOINTS:
        raw_family[endpoint] = 1.0 if current_p.get(endpoint) is None else float(current_p[endpoint])
    adjusted = holm_correction(raw_family)
    out = {}
    for endpoint in sorted(expected, key=lambda x: int(x.split("H")[1])):
        raw = current_p.get(endpoint) if endpoint in ENDPOINTS else source_p[endpoint]
        out[endpoint] = {
            "raw_p": raw,
            "holm_accounting_p": raw_family[endpoint],
            "holm_adjusted_p": adjusted[endpoint]["holm_p"],
            "holm_reject": holm_reject_strict(adjusted[endpoint]["holm_p"]),
            "status": "prior/fixed family" if endpoint not in ENDPOINTS else ("not run" if raw is None else "tested"),
        }
        if endpoint in ENDPOINTS and raw is None:
            out[endpoint]["holm_reject"] = False
    return out


def validate_holm_family(config_path=HOLM_CONFIG) -> dict:
    """Require the coordinator's complete H1-H15 family before labels exist."""
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
    p_values = cfg.get("p_values", {})
    endpoint_values = cfg.get("endpoints", {})
    expected = {f"R6-H{i}" for i in range(1, 16)}
    ordered = sorted(expected, key=lambda x: int(x.split("H")[1]))
    manifest = cfg.get("manifest")
    if manifest != ordered or set(p_values) != expected or set(endpoint_values) != expected:
        raise InputGateError("specs/r6_holm_family.json must be extended and frozen for all R6-H1 through R6-H15 slots")
    # The coordinator's frozen family manifest hash uses canonical Python
    # JSON list serialization (no whitespace normalization beyond defaults).
    digest = hashlib.sha256(json.dumps(ordered).encode("utf-8")).hexdigest()
    if cfg.get("manifest_sha256", "").lower() != digest:
        raise InputGateError("R6 Holm endpoint manifest SHA256 does not match H1-H15")
    try:
        parsed = {key: (None if value is None else float(value)) for key, value in p_values.items()}
    except (TypeError, ValueError) as exc:
        raise InputGateError("R6 Holm family p-values must be numeric or null") from exc
    if any(value is not None and not 0 <= value <= 1 for value in parsed.values()):
        raise InputGateError("R6 Holm family p-values must lie in [0,1]")
    if any(parsed[key] is None for key in sorted(expected - set(ENDPOINTS))):
        raise InputGateError("R6 Holm family must already contain raw p-values for H1-H12")
    if any(parsed[key] is not None for key in ENDPOINTS):
        raise InputGateError("P1 H13-H15 slots must be null before the authorized one-shot run")
    if endpoint_values != p_values:
        raise InputGateError("R6 Holm endpoint and p-value maps disagree")
    return cfg


def holm_reject_strict(adjusted_p: float | None, alpha: float = 0.05) -> bool:
    """The P1 Holm gate is strict: equality with alpha does not pass."""
    return adjusted_p is not None and float(adjusted_p) < alpha


def endpoint_rows(current_p, raw_gate, adjusted, statuses):
    return [{
        "endpoint": endpoint,
        "raw_p": current_p.get(endpoint),
        "raw_gate_status": raw_gate.get(endpoint, "not run"),
        "holm_adjusted_p": adjusted[endpoint]["holm_adjusted_p"],
        "holm_reject": adjusted[endpoint]["holm_reject"],
        "endpoint_status": statuses.get(endpoint, "not run"),
    } for endpoint in ENDPOINTS]


def write_placebo_draws(path: str | Path, draws) -> None:
    """Persist each preregistered SIC2 placebo draw without truncation."""
    values = np.asarray(draws, dtype=float)
    if values.shape != (PLACEBO_DRAWS,) or not np.isfinite(values).all():
        raise ValueError("P1 placebo output must contain exactly 500 finite draws")
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["draw", "mean_ic"])
        writer.writerows(enumerate(values, 1))


def render_results_markdown(results: dict) -> str:
    """Create the required durable one-run report, including the full null."""
    mech = results["mechanism"]
    placebo = results["placebo"]
    draws = results["placebo_draws"]
    lines = [
        "# P1 development results", "",
        "One authorized development run. No holdout data were loaded or tested.", "",
        f"- Frozen P1 SHA256: `{results['prereg_sha256']}`",
        f"- Input manifest SHA256: `{results['input_manifest_sha256']}`",
        f"- H13 raw gate: **{mech['raw_gate_status']}** (positive mean IC and NW t ≥ 2)",
        f"- H14 raw gate: **{placebo['raw_gate_status']}**",
        "", "## H13: monthly S&P 500 mechanism", "",
        f"Mean IC: {mech['mean_ic']:.10g}; NW t: {mech['nw_t']:.8g}; one-sided raw p: {mech['raw_one_sided_p']:.8g}; lag: {mech['nw_lag_months']} month.",
        f"The cost-only rank-IC floor `{mech['ic_floor_diagnostic']:.10g}` is diagnostic only; mean IC above floor: `{mech['mean_ic_above_cost_floor_diagnostic']}`.",
        "", "| Formation date | Eligible names | Spearman IC |", "|---|---:|---:|",
    ]
    for date, count, ic in zip(mech["dates"], mech["eligible_names_by_date"], mech["ic_by_date"]):
        ic_text = "NA" if ic is None or not np.isfinite(ic) else f"{ic:.10g}"
        lines.append(f"| {date} | {count} | {ic_text} |")
    lines.extend([
        "", "## H14: SIC2 signal-shuffle placebo", "",
        f"Observed mean IC: {placebo['observed_mean_ic']:.10g}; null 95th percentile: {placebo['null_p95']:.10g}; raw one-sided randomization p: {placebo['raw_one_sided_p']:.8g}; draws: {placebo['draw_count']}; seed: {placebo['seed']}.",
        "", "All 500 placebo mean-IC draws:", "", "| Draw | Mean IC |", "|---:|---:|",
    ])
    lines.extend(f"| {i} | {float(value):.12g} |" for i, value in enumerate(draws, 1))
    lines.extend(["", "## Holm endpoint decisions", "", "| Endpoint | Raw p | Raw gate | Holm adjusted p | Holm reject | Status |", "|---|---:|---|---:|---|---|"])
    for row in results["endpoints"]:
        raw = "not run" if row["raw_p"] is None else f"{row['raw_p']:.8g}"
        lines.append(f"| {row['endpoint']} | {raw} | {row['raw_gate_status']} | {row['holm_adjusted_p']:.8g} | {row['holm_reject']} | {row['endpoint_status']} |")
    port = results["portfolio"]
    lines.extend(["", "## H15: Dow portfolio", ""])
    if port is None:
        lines.append("Not run because one or both raw H13/H14 gates failed. H15 has no raw outcome p-value; p=1 is used only for Holm family accounting.")
    else:
        lines.extend([
            f"Net cumulative return: strategy {port['strategy_net_cumulative']:.8g}; EW30 {port['benchmark_net_cumulative']:.8g}; excess {port['net_excess_cumulative']:.8g}.",
            f"Gross cumulative return: strategy {port['strategy_gross_cumulative']:.8g}; EW30 {port['benchmark_gross_cumulative']:.8g}; excess {port['gross_excess_cumulative']:.8g}.",
            f"Annualized net Sharpe: strategy {port['strategy_net_sharpe']:.8g}; EW30 {port['benchmark_net_sharpe']:.8g}; strategy max drawdown {port['strategy_net_max_drawdown']:.8g}.",
            f"Turnover mean/max: {port['turnover_mean']:.8g}/{port['turnover_max']:.8g}; cap-bind count: {port['turnover_cap_bind_count']}; active share mean: {port['active_share_mean']:.8g}.",
            f"Transaction costs: strategy {port['cost_total']:.8g}; EW30 {port['benchmark_cost_total']:.8g}; strategy cost/gross-edge ratio {port['cost_gross_edge_ratio']}.",
            f"Daily 10-session block-bootstrap p (raw): {port['bootstrap_p_raw']:.8g}; DSR: {port['dsr']:.8g} at trial count {port['trial_count']}.",
            f"Holm-adjusted H15 p: {results['holm_family']['R6-H15']['holm_adjusted_p']:.8g}.",
        ])
    lines.extend(["", "## Reproducibility", "", "The complete machine-readable output is `run/P1_RESULTS.json`; all placebo draws are also saved in `run/P1_PLACEBO_DRAWS.csv`.", ""])
    return "\n".join(lines)


def _json_safe(value):
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


@guarded_runner(prereg_path=PREREG, run_dir=RUN_DIR)
def run_p1(*, manifest_path=INPUT_MANIFEST, signal_path=SIGNALS,
           daily_path=DAILY_PRICES, coverage_path=COVERAGE,
           output_dir=RUN_DIR, holm_path=HOLM_CONFIG, trial_log=TRIAL_LOG):
    """Verify manifest first, then construct labels, run gates, and persist outputs."""
    diff = prereg_diff_payload()
    validate_holm_family(holm_path)
    # No daily bars or forward labels are loaded before the manifest and the
    # signal-only 250-name coverage gate pass.
    coverage_gate, signal_frame, daily_frame, labels = verified_forward_labels(
        manifest_path, signal_path, daily_path, coverage_path,
        pre_label_check=diff.require_match,
    )
    if labels.empty:
        raise InputGateError("no eligible P1 forward label observations were constructed")
    sp_formations = signal_frame.loc[signal_frame.universe.eq("SP500"), "formation_date"].drop_duplicates().sort_values()
    mech = mechanism(labels, formation_dates=sp_formations)
    placebo = sic2_shuffle_placebo(labels, formation_dates=sp_formations)
    current_p = {
        "R6-H13": float(mech["raw_one_sided_p"]),
        "R6-H14": float(placebo["raw_one_sided_p"]),
        "R6-H15": None,
    }
    raw_gate = {
        "R6-H13": mech["raw_gate_status"],
        "R6-H14": placebo["raw_gate_status"],
        "R6-H15": "not run",
    }
    statuses = {"R6-H13": mech["raw_gate_status"], "R6-H14": placebo["raw_gate_status"], "R6-H15": "not run; H13/H14 raw gates pending"}
    results = {
        "approach": "P1", "variant": "P1-V1",
        "prereg_sha256": validate_frozen_prereg(PREREG)[1],
        "input_manifest_sha256": coverage_gate["manifest_sha256"],
        "coverage_gate": coverage_gate,
        "mechanism": mech,
        "placebo": {k: v for k, v in placebo.items() if k != "draws"},
        "placebo_draws": placebo["draws"],
        "portfolio": None,
    }
    if mech["raw_gate_pass"] and placebo["raw_gate_pass"]:
        trial_count = _trial_count(trial_log)
        port = portfolio(signal_frame, daily_frame, trial_count)
        current_p["R6-H15"] = float(port["bootstrap_p_raw"])
        raw_gate["R6-H15"] = (
            "pass" if port["net_excess_cumulative"] > 0 and
            port["strategy_net_sharpe"] > port["benchmark_net_sharpe"] and
            port["turnover_cap_pass"] and port["active_share_pass"] and
            port["bootstrap_p_raw"] < 0.05 else "fail"
        )
        statuses["R6-H15"] = "tested"
        results["portfolio"] = port
        results["portfolio"]["criterion4_raw_gates"] = raw_gate["R6-H15"]
    else:
        statuses["R6-H15"] = "not run; H13/H14 raw gates did not both pass"
    adjusted = holm_results(current_p, holm_path)
    if results["portfolio"] is not None:
        results["portfolio"]["bootstrap_p_holm"] = adjusted["R6-H15"]["holm_adjusted_p"]
    if current_p["R6-H15"] is not None:
        h15_ok = (raw_gate["R6-H15"] == "pass" and
                  holm_reject_strict(adjusted["R6-H15"]["holm_adjusted_p"]))
        statuses["R6-H15"] = "pass" if h15_ok else ("raw gates passed; Holm failed" if raw_gate["R6-H15"] == "pass" else "raw gates failed")
    results["endpoints"] = endpoint_rows(current_p, raw_gate, adjusted, statuses)
    results["holm_family"] = adjusted
    results["settings"] = {
        "lookback_sessions": LOOKBACK, "horizon_months": HORIZON_MONTHS,
        "nw_lag_months": NW_LAG, "placebo_draws": PLACEBO_DRAWS,
        "bootstrap_block_sessions": BOOTSTRAP_BLOCK, "bootstrap_draws": BOOTSTRAP_DRAWS,
        "seed": SEED, "turnover_cap": TURNOVER_CAP, "cost_per_side": COST_PER_SIDE,
        "active_share_min": ACTIVE_SHARE_MIN, "ic_floor": IC_FLOOR,
    }
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "P1_RESULTS.json").write_text(json.dumps(_json_safe(results), indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with (out / "P1_ENDPOINTS.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results["endpoints"][0]))
        writer.writeheader()
        for row in results["endpoints"]:
            writer.writerow(row)
    write_placebo_draws(out / "P1_PLACEBO_DRAWS.csv", placebo["draws"])
    (HERE / "RESULTS.md").write_text(render_results_markdown(_json_safe(results)), encoding="utf-8")
    if mech["raw_gate_pass"] and placebo["raw_gate_pass"]:
        (HERE / "MECHANISM_PASS.json").write_text(json.dumps({
            "approach": "P1", "variant": "P1-V1", "passed": True,
            "prereg_sha256": results["prereg_sha256"],
            "R6-H13_raw_gate": mech["raw_gate_status"],
            "R6-H14_raw_gate": placebo["raw_gate_status"],
        }, indent=2) + "\n", encoding="utf-8")
    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="explicit outcome-execution authorization")
    parser.add_argument("--manifest", type=Path, default=INPUT_MANIFEST)
    parser.add_argument("--signals", type=Path, default=SIGNALS)
    parser.add_argument("--daily-prices", type=Path, default=DAILY_PRICES)
    parser.add_argument("--coverage", type=Path, default=COVERAGE)
    parser.add_argument("--output-dir", type=Path, default=RUN_DIR)
    args = parser.parse_args(argv)
    try:
        run_p1(manifest_path=args.manifest, signal_path=args.signals,
               daily_path=args.daily_prices, coverage_path=args.coverage,
               output_dir=args.output_dir, execute=args.execute)
        return 0
    except Exception as exc:
        print(f"P1 refused/failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
