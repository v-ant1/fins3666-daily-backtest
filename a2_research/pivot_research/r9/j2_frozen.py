#!/usr/bin/env python3
"""Frozen J2 implementation, isolated from the one-shot gate wrapper.

The panel contract is the development archive's aligned S&P and Dow arrays:
dates, assets, PIT roster, dated SIC2, adjusted open, and adjusted close.
Signals are reconstructed from the fixed J1 five-session SIC2-relative return.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Mapping

import numpy as np

COST_RATE = 0.0005
SMOOTHING_FORMATIONS = 4
TOP_K = 5
DEV_COMMON_START = "2021-03-04"
DEV_CUTOFF = "2020-11-27"
FULL_TRIAL_COUNT = 15
SEALED_PANEL_SHA256 = "7b405c9b8348c5c9db794a85480e6c0228901ab96b32d7af4c763ae758c589db"
SEALED_START_DATE = "2016-01-04"
SEALED_END_DATE = "2020-10-30"
SEALED_SESSION_COUNT = 1217


def _file_sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _arr(panel: Mapping[str, np.ndarray], key: str) -> np.ndarray:
    if key not in panel:
        raise ValueError(f"panel missing required field: {key}")
    return np.asarray(panel[key])


def _validate_panel(panel: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    out = {key: _arr(panel, key) for key in (
        "sp500_dates", "sp500_assets", "sp500_roster", "sp500_sic2",
        "sp500_adjusted_open", "sp500_adjusted_close", "dow_dates",
        "dow_assets", "dow_roster", "dow_sic2", "dow_adjusted_open",
        "dow_adjusted_close")}
    dates = out["dow_dates"].astype(str)
    if not np.array_equal(dates, out["sp500_dates"].astype(str)):
        raise ValueError("S&P and Dow date axes must be identical and aligned")
    n_date = len(dates)
    for prefix in ("sp500", "dow"):
        n_asset = len(out[f"{prefix}_assets"])
        for suffix in ("roster", "sic2", "adjusted_open", "adjusted_close"):
            value = out[f"{prefix}_{suffix}"]
            if value.shape != (n_asset, n_date):
                raise ValueError(f"{prefix}_{suffix} shape does not match asset/date axes")
    if n_date < 7 or not np.all(dates[:-1] < dates[1:]):
        raise ValueError("panel requires at least seven strictly increasing sessions")
    return out


def _validate_sealed_panel(panel: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Enforce the sealed archive contract using BUILD_REPORT's schema table."""
    required = {
        f"{prefix}_{suffix}"
        for prefix in ("sp500", "dow")
        for suffix in ("dates", "assets", "roster", "sic2", "adjusted_open", "adjusted_close")
    }
    if set(panel) != required:
        raise ValueError("sealed panel keys do not match the frozen S&P/Dow schema")
    out = _validate_panel(panel)
    expected_assets = {"sp500": 631, "dow": 41}
    expected_dtypes = {
        "dates": np.dtype("<U10"), "assets": np.dtype("<U5"),
        "roster": np.dtype(bool), "sic2": np.dtype("<U2"),
        "adjusted_open": np.dtype(np.float64), "adjusted_close": np.dtype(np.float64),
    }
    for prefix, n_asset in expected_assets.items():
        for suffix, dtype in expected_dtypes.items():
            value = out[f"{prefix}_{suffix}"]
            expected_shape = ((SEALED_SESSION_COUNT,) if suffix == "dates"
                              else (n_asset,) if suffix == "assets"
                              else (n_asset, SEALED_SESSION_COUNT))
            if value.dtype != dtype:
                raise ValueError(f"sealed {prefix}_{suffix} dtype must be {dtype}")
            if value.shape != expected_shape:
                raise ValueError(f"sealed {prefix}_{suffix} shape must be {expected_shape}")
    dates = out["sp500_dates"].astype(str)
    if dates[0] != SEALED_START_DATE or dates[-1] != SEALED_END_DATE:
        raise ValueError("sealed date axis must span 2016-01-04 through 2020-10-30")
    return out


def _valid_prices(values: np.ndarray) -> np.ndarray:
    return np.isfinite(values) & (values > 0)


def build_j1_scores(panel: Mapping[str, np.ndarray], formation_indices: list[int]
                    ) -> dict[str, dict[str, float]]:
    """Build Dow J1 scores using leave-one-out PIT S&P same-SIC2 peers.

    A target is unavailable when its own SIC2/price history is missing, or
    when no other valid PIT S&P peer in that SIC2 has a complete five-session
    return. Missing classifications are never broadened or imputed.
    """
    p = _validate_panel(panel)
    dates = p["dow_dates"].astype(str)
    sp_assets = p["sp500_assets"].astype(str)
    dow_assets = p["dow_assets"].astype(str)
    sp_ix = {ticker: i for i, ticker in enumerate(sp_assets)}
    sp_close = p["sp500_adjusted_close"].astype(float)
    dow_close = p["dow_adjusted_close"].astype(float)
    sp_roster = p["sp500_roster"].astype(bool)
    dow_roster = p["dow_roster"].astype(bool)
    sp_sic = p["sp500_sic2"].astype(str)
    dow_sic = p["dow_sic2"].astype(str)
    result: dict[str, dict[str, float]] = {}
    for t in formation_indices:
        if t < 5 or t >= len(dates):
            continue
        sp_before, sp_now = sp_close[:, t - 5], sp_close[:, t]
        sp_window = sp_close[:, t - 5:t + 1]
        sp_valid = (sp_roster[:, t] & np.all(_valid_prices(sp_window), axis=1))
        sp_r5 = np.full(len(sp_assets), np.nan, dtype=float)
        sp_r5[sp_valid] = sp_now[sp_valid] / sp_before[sp_valid] - 1.0
        daily: dict[str, float] = {}
        for j, ticker in enumerate(dow_assets):
            # The target's frozen J1 trailing return is its Dow-panel return;
            # its same-SIC2 peer mean uses all eligible PIT S&P peers.
            sic = dow_sic[j, t].strip()
            d_window = dow_close[j, t - 5:t + 1]
            if (not dow_roster[j, t] or len(sic) != 2 or not sic.isdigit()
                    or not np.all(_valid_prices(d_window))):
                continue
            target_return = float(d_window[-1] / d_window[0] - 1.0)
            peer_mask = sp_valid & (sp_sic[:, t] == sic)
            own = sp_ix.get(ticker)
            if own is not None:
                peer_mask[own] = False
            peers = sp_r5[peer_mask]
            if peers.size == 0:
                continue
            daily[ticker] = float(target_return - np.mean(peers))
        result[dates[t]] = daily
    return result


def _development_signal_rows(root: Path) -> dict[str, dict[str, float]]:
    """Read only post-cutoff, metadata-verified J1 development score groups."""
    from r9.check_j2 import read_development_scores

    raw = read_development_scores(root / "r6_J1" / "signal_bundle.parquet")
    out: dict[str, dict[str, float]] = {}
    for date, rows in raw.items():
        out[date] = {
            ticker: float(row["score"])
            for ticker, row in rows.items()
            if row["valid"] and row["score"] is not None
            and np.isfinite(float(row["score"]))
        }
    return out


def _smooth_targets(scores: dict[str, dict[str, float]], formations: list[str],
                    assets: list[str], eligible: np.ndarray,
                    old_weights: np.ndarray) -> np.ndarray | None:
    history = formations[-SMOOTHING_FORMATIONS:]
    if len(history) != SMOOTHING_FORMATIONS:
        return None
    rows = []
    for j, ticker in enumerate(assets):
        if not eligible[j]:
            continue
        values = [scores.get(d, {}).get(ticker) for d in history]
        if any(v is None or not np.isfinite(v) for v in values):
            continue
        rows.append((float(np.mean(values)), ticker, j))
    rows.sort(key=lambda row: (row[0], row[1]))
    if len(rows) < TOP_K:
        return None
    target = np.zeros_like(old_weights)
    target[[row[2] for row in rows[:TOP_K]]] = 1.0 / TOP_K
    return target


def simulate_j2(panel: Mapping[str, np.ndarray], start_date: str, end_date: str,
                *, comparison_start: str | None = None,
                signal_rows: dict[str, dict[str, float]] | None = None) -> dict:
    """Run frozen J2 and aligned PIT EW30 over the requested window."""
    p = _validate_panel(panel)
    dates = p["dow_dates"].astype(str)
    if start_date > end_date:
        raise ValueError("start_date must not follow end_date")
    requested = np.flatnonzero((dates >= start_date) & (dates <= end_date))
    if requested.size == 0:
        raise ValueError("requested date range does not overlap the panel")
    last_requested = int(requested[-1])
    # Fifth-session schedule anchored to the first session in the panel. This
    # preserves the same trading-calendar phase for the trimmed dev and sealed
    # holdout panels.
    form_indices = list(range(0, len(dates), 5))
    scores = signal_rows if signal_rows is not None else build_j1_scores(p, form_indices)
    # Require a full four-formation history before choosing the common book.
    panel_dates = set(dates.tolist())
    signal_dates = sorted(d for d in scores if d in panel_dates)
    valid_forms = []
    for pos, d in enumerate(signal_dates):
        i = int(np.searchsorted(dates, d))
        if (d < start_date or d > end_date or pos < 3 or i + 1 >= len(dates)):
            continue
        valid_forms.append((i, d, signal_dates[:pos + 1]))
    if not valid_forms:
        raise ValueError("no formation has four valid scheduled J1 score dates")
    if comparison_start is not None:
        start_i = int(np.searchsorted(dates, comparison_start))
        candidates = [x for x in valid_forms if x[0] >= start_i]
        if not candidates:
            raise ValueError("no valid formation at or after comparison_start")
        first_i, first_form, _ = candidates[0]
    else:
        first_i, first_form, _ = valid_forms[0]
    sim_dates = [(i, d, hist) for i, d, hist in valid_forms if i >= first_i]
    form_by_index = {i: (d, hist) for i, d, hist in sim_dates}
    dow_assets = p["dow_assets"].astype(str).tolist()
    roster = p["dow_roster"].astype(bool)
    opens = p["dow_adjusted_open"].astype(float)
    closes = p["dow_adjusted_close"].astype(float)
    initial_member = roster[:, first_i] & _valid_prices(closes[:, first_i])
    if not np.any(initial_member):
        raise ValueError("no PIT Dow constituents for the initial EW30 book")
    weights = np.zeros(len(dow_assets), dtype=float)
    weights[initial_member] = 1.0 / int(initial_member.sum())
    last_close = closes[:, first_i].copy()
    last_close[~_valid_prices(last_close)] = np.nan
    strategy, benchmark = [], []
    # Benchmark has its own EW30 weights, initialized on the same PIT cohort.
    bench_weights = weights.copy()
    bench_last_close = last_close.copy()
    for day in range(first_i + 1, last_requested + 1):
        open_px, close_px = opens[:, day], closes[:, day]
        valid_open, valid_close = _valid_prices(open_px), _valid_prices(close_px)
        overnight_ret = np.zeros(len(dow_assets), dtype=float)
        can_mark = valid_open & np.isfinite(last_close)
        overnight_ret[can_mark] = open_px[can_mark] / last_close[can_mark] - 1.0
        overnight = float(np.dot(weights, overnight_ret))
        w_open = weights * (1.0 + overnight_ret)
        if w_open.sum() > 0:
            w_open /= w_open.sum()
        cost_fraction = 0.0
        form = form_by_index.get(day - 1)
        if form is not None:
            form_date, history = form
            eligible = roster[:, day - 1] & valid_open
            target = _smooth_targets(scores, history, dow_assets, eligible, w_open)
            if target is not None:
                cost_fraction = float(np.abs(target - w_open).sum()) * COST_RATE
                w_open = target
        intraday = np.zeros(len(dow_assets), dtype=float)
        pair = valid_close & valid_open
        intraday[pair] = close_px[pair] / open_px[pair] - 1.0
        net = ((1.0 + overnight) - cost_fraction) * (1.0 + float(np.dot(w_open, intraday))) - 1.0
        strategy.append((str(dates[day]), net))
        last_close[valid_close] = close_px[valid_close]
        weights = w_open * (1.0 + intraday)
        if weights.sum() > 0:
            weights /= weights.sum()

        # PIT EW30 benchmark reconstituted each scheduled formation and held
        # with drift between formations, using the same available-name rule.
        bo_ret = np.zeros(len(dow_assets), dtype=float)
        bmark = valid_open & np.isfinite(bench_last_close)
        bo_ret[bmark] = open_px[bmark] / bench_last_close[bmark] - 1.0
        b_overnight = float(np.dot(bench_weights, bo_ret))
        bw_open = bench_weights * (1.0 + bo_ret)
        if bw_open.sum() > 0:
            bw_open /= bw_open.sum()
        b_cost = 0.0
        if form is not None:
            cohort = roster[:, day - 1] & valid_open
            target_b = np.zeros_like(bw_open)
            if cohort.any():
                target_b[cohort] = 1.0 / int(cohort.sum())
            b_cost = float(np.abs(target_b - bw_open).sum()) * COST_RATE
            bw_open = target_b
        b_intraday = float(np.dot(bw_open, intraday))
        b_net = ((1.0 + b_overnight) - b_cost) * (1.0 + b_intraday) - 1.0
        benchmark.append((str(dates[day]), b_net))
        bench_last_close[valid_close] = close_px[valid_close]
        bench_weights = bw_open * (1.0 + intraday)
        if bench_weights.sum() > 0:
            bench_weights /= bench_weights.sum()

    if not strategy or [d for d, _ in strategy] != [d for d, _ in benchmark]:
        raise ValueError("strategy and benchmark return dates are not aligned")
    return {
        "dates": [d for d, _ in strategy],
        "strategy_net": [v for _, v in strategy],
        "ew30_net": [v for _, v in benchmark],
        "trial_count": FULL_TRIAL_COUNT,
        "first_formation": first_form,
    }


def run_frozen_j2(prereg_path: Path, start_date: str, end_date: str,
                  *, synthetic_hash_override: str | None = None) -> dict:
    """Load the approved-window panel and run the unchanged frozen J2 rules."""
    root = Path(prereg_path).resolve().parents[2]
    if start_date >= DEV_CUTOFF:
        panel_path = root / "r9" / "data" / "J2_DEV_FROM_20201127.npz"
        expected_hash = None
    else:
        if synthetic_hash_override is not None:
            # This override is confined to the synthetic fixture tree under r9/j2ready.
            if (root.name != "synthetic_case" or root.parent.name != "j2ready"
                    or root.parent.parent.name != "r9"
                    or not (root / "r9" / "j2ready" / "SYNTHETIC_ONLY.txt").is_file()):
                raise ValueError("synthetic hash override is unavailable outside r9/j2ready/synthetic_case")
            panel_path = root / "r9" / "j2ready" / "J2_HOLDOUT_SYNTHETIC.npz"
            expected_hash = synthetic_hash_override
        else:
            # The sealed artifact is verified by digest before np.load can read it.
            panel_path = root / "sealed_holdout_sp500" / "J2_HOLDOUT.npz"
            expected_hash = SEALED_PANEL_SHA256
    if not panel_path.is_file():
        raise FileNotFoundError(f"required J2 panel is missing: {panel_path}")
    if expected_hash is not None and _file_sha256(panel_path) != expected_hash:
        raise ValueError("J2 panel SHA-256 does not match the required sealed/synthetic digest")
    with np.load(panel_path, allow_pickle=False) as z:
        panel = {key: z[key] for key in z.files}
    if start_date < DEV_CUTOFF:
        panel = _validate_sealed_panel(panel)
    signal_rows = None
    if start_date >= DEV_CUTOFF:
        signal_rows = _development_signal_rows(root)
    return simulate_j2(panel, start_date, end_date,
                       comparison_start=DEV_COMMON_START if start_date >= DEV_CUTOFF else None,
                       signal_rows=signal_rows)


def synthetic_eligibility_check() -> None:
    """Synthetic SIC2 checks for valid peer, missing SIC2, and no-peer cases."""
    dates = np.array([f"2021-01-{day:02d}" for day in range(1, 13)])
    sp_close = np.array([
        np.linspace(10.0, 11.1, 12),
        np.linspace(20.0, 22.2, 12),
        np.linspace(30.0, 29.0, 12),
    ])
    dow_close = np.vstack((sp_close[0], sp_close[1], sp_close[2]))
    sp_sic = np.array([["10"] * 12, ["10"] * 12, ["20"] * 12])
    dow_sic = np.array([["10"] * 12, ["10"] * 12, ["30"] * 12])
    dow_sic[1, 6] = ""  # missing SIC2 makes the target ineligible at that date
    panel = {
        "sp500_dates": dates, "dow_dates": dates,
        "sp500_assets": np.array(["AAA", "BBB", "CCC"]),
        "dow_assets": np.array(["AAA", "BBB", "DDD"]),
        "sp500_roster": np.ones((3, 12), dtype=bool),
        "dow_roster": np.ones((3, 12), dtype=bool),
        "sp500_sic2": sp_sic, "dow_sic2": dow_sic,
        "sp500_adjusted_open": sp_close, "sp500_adjusted_close": sp_close,
        "dow_adjusted_open": dow_close, "dow_adjusted_close": dow_close,
    }
    rows = build_j1_scores(panel, [6, 7])
    assert "AAA" in rows[dates[6]]  # BBB is its valid same-SIC2 peer
    assert "BBB" not in rows[dates[6]]  # missing SIC2
    assert "DDD" not in rows[dates[6]]  # SIC2 30 has no eligible S&P peer
    assert "BBB" in rows[dates[7]]  # SIC2 is known again and AAA is a peer

