"""Guarded, single-variant G1 runner. Synthetic helpers are safe to import.

This runner deliberately consumes an input-only NPZ/coverage bundle staged by
the data owner.  It will not load price values until the frozen preregistration,
input hashes, and availability-only coverage gate have been checked.
"""
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
from scipy.stats import spearmanr, t as student_t

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from r4_harness.phase3 import (break_even_rank_ic, circular_block_bootstrap_pvalue,
    deflated_sharpe_ratio, holm_correction, newey_west_t, prereg_digest)
from r4_harness.prereg_diff import prereg_diff
from r4_harness.runner_guard import guarded_runner, validate_frozen_prereg

PREREG = ROOT / "specs/r6_prereg/G1.md"
INPUTS = HERE / "G1_INPUTS.npz"
COVERAGE = HERE / "formation_coverage.csv"
MANIFEST = HERE / "build_manifest.json"
DIFF_SOURCE = HERE / "G1_PREREG_DIFF_SOURCE.md"
DIFF_CONFIG = HERE / "prereg_diff_config.json"
HOLM = ROOT / "specs/r6_holm_family.json"
TRIALS = ROOT / "specs/r4_trials.md"
J1_RESULTS = ROOT / "r6_J1/RESULTS.md"
RUN_DIR = HERE / "run"

FIRST_FORMATION, LAST_FORMATION, STEP, FORMATION_COUNT = 54, 1461, 21, 68
NW_LAG, PLACEBO_DRAWS, BOOTSTRAP_DRAWS, BOOTSTRAP_BLOCK, SEED = 1, 500, 5000, 10, 20261111
MIN_SP500_NAMES, TOP_N, TURNOVER_CAP, COST_PER_SIDE, ACTIVE_SHARE_MIN = 250, 5, .50, .0005, .50
RETURN_DISPERSION, TOP_FRACTION = .06, 5 / 30
IC_FLOOR = float(f"{break_even_rank_ic(TURNOVER_CAP, RETURN_DISPERSION, COST_PER_SIDE, TOP_FRACTION):.10f}")
ENDPOINTS = ("R6-H19", "R6-H20", "R6-H21")
RUNNER_SPEC_CONFIG = {
    "window": 50, "formation_count": FORMATION_COUNT, "horizon": 21,
    "nw_lag": NW_LAG, "draws": [PLACEBO_DRAWS, BOOTSTRAP_DRAWS],
    "block_length": BOOTSTRAP_BLOCK, "seed": SEED, "turnover_limit": TURNOVER_CAP,
    "cost_per_side": COST_PER_SIDE, "top_n": TOP_N, "top_fraction": TOP_FRACTION,
    "return_dispersion": RETURN_DISPERSION, "cost_floor_diagnostic": IC_FLOOR,
    "min_t": 2, "active_share_min": ACTIVE_SHARE_MIN, "alpha": .05,
    "percentile": 95, "endpoint_count": 3,
}


class InputGateError(RuntimeError):
    """Input provenance or availability gate failed."""


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canonical_manifest_sha256(manifest: dict) -> str:
    payload = {k:v for k,v in manifest.items() if k != "manifest_sha256"}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def prereg_diff_payload():
    # The normalized copy exists only to make the parser's numeric comparison
    # explicit; the frozen canonical G1.md is never modified.
    return prereg_diff(DIFF_SOURCE, json.loads(DIFF_CONFIG.read_text(encoding="utf-8")))


def formation_indices(n_dates: int) -> np.ndarray:
    ix = np.arange(FIRST_FORMATION, LAST_FORMATION + 1, STEP, dtype=int)
    if len(ix) != FORMATION_COUNT or n_dates <= LAST_FORMATION + STEP:
        raise ValueError("G1 requires 1,488 development sessions and the frozen 68-date schedule")
    return ix


def _array_sha256(array) -> str:
    a = np.ascontiguousarray(np.asarray(array))
    h = hashlib.sha256()
    h.update(str(a.dtype).encode("ascii")); h.update(repr(a.shape).encode("ascii")); h.update(a.tobytes())
    return h.hexdigest()


def high_volume_signal(volume: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """HV5 = five completed daily log-volume z-scores; trailing 50 exclude d."""
    v = np.asarray(volume, dtype=float)
    if v.ndim != 2:
        raise ValueError("volume must have assets x sessions shape")
    n, t = v.shape
    z = np.full((n, t), np.nan)
    for d in range(50, t):
        cur = v[:, d]
        hist = v[:, d-50:d]
        good = np.isfinite(hist) & (hist > 0)
        count = good.sum(axis=1)
        logs = np.log(np.where(good, hist, 1.0))
        # Rows with missing/invalid baseline observations are ineligible.  Use
        # masked sums so an all-NaN row does not trigger nanmean/nanstd warnings.
        mu = np.full(n, np.nan)
        sd = np.full(n, np.nan)
        complete = count == 50
        mu[complete] = logs[complete].mean(axis=1)
        centered = np.where(good, logs - mu[:, None], 0.0)
        sd[complete] = np.sqrt(np.square(centered[complete]).sum(axis=1) / 49.0)
        ok = (count == 50) & np.isfinite(cur) & (cur > 0) & np.isfinite(sd) & (sd > 0)
        z[ok, d] = (np.log(cur[ok]) - mu[ok]) / sd[ok]
    hv = np.full_like(z, np.nan)
    for d in range(54, t):
        window = z[:, d-4:d+1]
        ok = np.isfinite(window).all(axis=1)
        hv[ok, d] = window[ok].mean(axis=1)
    return hv, np.isfinite(hv)


def availability_masks(data: dict) -> dict:
    """Build masks only; do not divide or otherwise calculate forward returns."""
    forms = formation_indices(len(data["dates"]))
    masks = {}
    for u in ("sp500", "dow"):
        roster = np.asarray(data[f"{u}_roster"], dtype=bool)
        volume = np.asarray(data[f"{u}_volume"], dtype=float)
        sic = np.asarray(data[f"{u}_sic2"]).astype(str)
        op = np.asarray(data[f"{u}_adjusted_open"], dtype=float)
        close = np.asarray(data[f"{u}_adjusted_close"], dtype=float)
        if any(x.shape != volume.shape for x in (roster, sic, op, close)):
            raise InputGateError(f"{u} panels do not share assets x sessions dimensions")
        hv, hv_ok = high_volume_signal(volume)
        eligible_by_date, hm, signal_bars, endpoint_bars = [], [], [], []
        for t in forms:
            end = t + 21
            start = t + 1
            signal_ok = np.isfinite(volume[:, t-54:t+1]) & (volume[:, t-54:t+1] > 0)
            signal_bars.append(signal_ok.all(axis=1))
            endpoint = (np.isfinite(op[:, start]) & (op[:, start] > 0) &
                        np.isfinite(close[:, end]) & (close[:, end] > 0))
            endpoint_bars.append(endpoint)
            known_sic = np.char.str_len(np.char.strip(sic[:, t])) > 0
            elig = roster[:, t] & hv_ok[:, t] & known_sic & endpoint
            eligible_by_date.append(int(elig.sum()))
            hm.append(elig)
        masks[u] = {"forms": forms, "signal": hv, "eligible": np.column_stack(hm),
                    "eligible_counts": np.asarray(eligible_by_date, dtype=int),
                    "hashes": {
                        "pit_roster": _array_sha256(roster),
                        "sic2": _array_sha256(sic[:,forms]),
                        "signal_bars": _array_sha256(np.column_stack(signal_bars)),
                        "signal_valid": _array_sha256(hv_ok[:,forms]),
                        "endpoint_bars": _array_sha256(np.column_stack(endpoint_bars)),
                        "formation_eligibility": _array_sha256(np.column_stack(hm)),
                    }}
    return masks


def check_coverage(frame: pd.DataFrame, manifest: dict, inputs_path: Path, coverage_path: Path) -> dict:
    """Verify build claims and full fixed-calendar S&P gate before labels."""
    if manifest.get("scope") != "development-only input panels; no forward labels or outcomes":
        raise InputGateError("manifest scope is not the approved input-only build")
    if manifest.get("development_window") != ["2020-11-27", "2026-10-30"]:
        raise InputGateError("manifest development boundary differs from frozen G1")
    if manifest.get("forward_labels_built") is not False or manifest.get("holdout_loaded") is not False:
        raise InputGateError("manifest must attest no forward labels and no holdout load")
    if manifest.get("manifest_sha256", "").lower() != canonical_manifest_sha256(manifest):
        raise InputGateError("G1 input manifest self-digest mismatch")
    if manifest.get("volume_basis") != "split_adjusted_share_volume" or manifest.get("volume_adjustment") != "split factors effective by each session; dividends excluded":
        raise InputGateError("manifest does not certify the frozen split-basis share-volume treatment")
    if manifest.get("input_bundle_sha256") != sha256(inputs_path):
        raise InputGateError("G1 input bundle differs from build manifest")
    if manifest.get("coverage_sha256") != sha256(coverage_path):
        raise InputGateError("G1 coverage table differs from build manifest")
    sources = manifest.get("source_files")
    if not isinstance(sources, list) or not sources:
        raise InputGateError("manifest must pin the staged development source files")
    roles = set()
    for entry in sources:
        if not isinstance(entry, dict) or not {"role", "path", "sha256"} <= set(entry):
            raise InputGateError("each source_files entry needs role, path, and sha256")
        roles.add(entry["role"])
        source_path = (ROOT / entry["path"]).resolve()
        if ROOT.resolve() not in source_path.parents:
            raise InputGateError("manifest source path escapes the project")
        if not source_path.is_file() or sha256(source_path) != str(entry["sha256"]).lower():
            raise InputGateError(f"pinned source file missing or changed: {entry['path']}")
    required_roles = {"sp500_ohlcv", "dow_ohlcv", "sp500_pit_roster", "dow_pit_roster", "sic2", "split_actions"}
    if not required_roles <= roles:
        raise InputGateError(f"manifest omits required input roles: {sorted(required_roles-roles)}")
    required = {"universe", "formation_date", "eligible_names"}
    if not required <= set(frame.columns):
        raise InputGateError(f"coverage table lacks columns {sorted(required-set(frame.columns))}")
    sp = frame.loc[frame.universe.eq("sp500")].sort_values("formation_date")
    if len(sp) != FORMATION_COUNT or sp.formation_date.nunique() != FORMATION_COUNT:
        raise InputGateError("coverage must contain all 68 fixed S&P formations")
    dow = frame.loc[frame.universe.eq("dow")].sort_values("formation_date")
    if len(dow) != FORMATION_COUNT or dow.formation_date.nunique() != FORMATION_COUNT:
        raise InputGateError("coverage must contain all 68 fixed Dow formations")
    counts = sp.eligible_names.astype(int).to_numpy()
    if np.any(counts < MIN_SP500_NAMES):
        raise InputGateError(f"coverage gate failed: minimum S&P names {counts.min()} < 250")
    return {"passed": True, "formation_count": len(sp), "minimum_sp500_names": int(counts.min()),
            "eligible_names": counts.tolist(), "manifest_sha256": manifest["manifest_sha256"]}


def _forward_returns(data: dict, mask: np.ndarray, universe: str) -> np.ndarray:
    forms = formation_indices(len(data["dates"]))
    op = np.asarray(data[f"{universe}_adjusted_open"], float)
    close = np.asarray(data[f"{universe}_adjusted_close"], float)
    out = np.full(mask.shape, np.nan)
    for j, t in enumerate(forms):
        ok = mask[:, j]
        out[ok, j] = close[ok, t+21] / op[ok, t+1] - 1.0
    return out


def mechanism(score, forward, sic2, eligible) -> dict:
    score, forward, sic2, eligible = map(np.asarray, (score, forward, sic2, eligible))
    ic, sectors, counts = [], [], []
    for j in range(score.shape[1]):
        ok = eligible[:, j] & np.isfinite(score[:, j]) & np.isfinite(forward[:, j])
        ic.append(float(spearmanr(score[ok, j], forward[ok, j]).statistic) if ok.sum() >= 3 else np.nan)
        sectors.append(int(len(set(sic2[ok, j].tolist()) - {""})))
        counts.append(int(ok.sum()))
    vals = np.asarray(ic, float); finite = np.isfinite(vals)
    x = vals[finite]
    tw = newey_west_t(x, NW_LAG)
    rawp = float(student_t.sf(tw, max(1, len(x)-1)))
    return {"ic_by_formation": vals, "eligible_names": np.asarray(counts),
            "sic2_counts": np.asarray(sectors), "mean_ic": float(x.mean()) if len(x) else np.nan,
            "nw_lag": NW_LAG, "nw_t": float(tw), "raw_p": rawp,
            "pass": bool(len(x) >= 2 and x.mean() > 0 and tw >= 2.0)}


def sic2_shuffle(score, forward, sic2, eligible, *, draws=PLACEBO_DRAWS, seed=SEED) -> dict:
    observed = mechanism(score, forward, sic2, eligible)["mean_ic"]
    rng = np.random.default_rng(seed)
    null = np.full(draws, np.nan)
    for b in range(draws):
        fake = np.asarray(score, float).copy()
        for j in range(fake.shape[1]):
            for sector in sorted(set(np.asarray(sic2)[:, j][eligible[:, j]].tolist()) - {""}):
                ix = np.flatnonzero(eligible[:, j] & (np.asarray(sic2)[:, j] == sector))
                if len(ix) > 1:
                    fake[ix, j] = rng.permutation(fake[ix, j])
        null[b] = mechanism(fake, forward, sic2, eligible)["mean_ic"]
    p = float((1 + np.sum(null >= observed)) / (draws + 1))
    p95 = float(np.nanquantile(null, .95))
    return {"observed_mean_ic": float(observed), "draws": null, "p95": p95, "p": p,
            "pass": bool(observed > 0 and observed > p95 and p < .05)}


def target_weights(score, signal_valid, roster_at_open, open_available, names=None):
    """Frozen top-K Dow selection; n is the available roster, not signal cohort."""
    n_avail = np.asarray(roster_at_open, bool) & np.asarray(open_available, bool)
    ids = np.flatnonzero(n_avail)
    k = min(TOP_N, len(ids) // 2)
    eligible = ids[np.asarray(signal_valid, bool)[ids] & np.isfinite(np.asarray(score)[ids])]
    labels = np.asarray(names).astype(str) if names is not None else np.arange(len(score)).astype(str)
    eligible = sorted(eligible.tolist(), key=lambda i: (-float(score[i]), labels[i]))
    selected = eligible[:k]
    target = np.zeros(len(score), float)
    if selected:
        target[selected] = 1 / len(selected)
    ew = np.zeros(len(score), float)
    if len(ids):
        ew[ids] = 1 / len(ids)
    active_share = .5 * np.abs(target-ew).sum()
    return target, ew, k, len(selected), float(active_share)


def _trade(old, target, can_trade, cap=TURNOVER_CAP):
    old, target, can_trade = map(np.asarray, (old, target, can_trade))
    frozen = (~can_trade) & (old > 1e-12)
    desired = target.astype(float).copy()
    desired[frozen] = old[frozen]
    tradable = ~frozen & can_trade
    mass = desired[tradable].sum()
    if mass:
        desired[tradable] *= max(0, 1-float(old[frozen].sum())) / mass
    delta = desired-old
    traded = float(np.abs(delta[tradable]).sum())
    scale = min(1.0, cap/traded) if traded else 1.0
    new = old.copy(); new[tradable] = old[tradable] + scale*delta[tradable]
    return new, float(np.abs(new-old).sum())


def portfolio(dates, names, roster, signal, op, close):
    """Daily long-only portfolio; stale closes carry, then catch up on resumption."""
    dates, names = np.asarray(dates).astype(str), np.asarray(names).astype(str)
    roster, signal, op, close = map(np.asarray, (roster, signal, op, close))
    n, full_t = op.shape
    forms = formation_indices(full_t)
    # The final daily return is exactly the last registered t+21 close (index
    # 1482); extra calendar rows cannot leak into the six-year portfolio.
    tmax = min(full_t, int(forms[-1] + 22))
    start_map = {int(f+1): int(f) for f in forms}
    first = forms[0]+1
    last_close = np.full(n, np.nan)
    # Values before first fill are used only to initialize stale marks.
    for i in range(n):
        prior = np.flatnonzero(np.isfinite(close[i, :first]) & (close[i, :first] > 0))
        if len(prior): last_close[i] = close[i, prior[-1]]
    own = np.zeros(n); ew = np.zeros(n)
    sret, bret, sret_gross, turns, active, costs = [], [], [], [], [], []
    stale_strategy, stale_benchmark = set(), set()
    for d in range(first, tmax):
        open_ok = np.isfinite(op[:, d]) & (op[:, d] > 0)
        close_ok = np.isfinite(close[:, d]) & (close[:, d] > 0)
        cost, overnight_s, overnight_b = 0.0, 0.0, 0.0
        # Existing holdings first experience the close-to-open return. New
        # positions are bought only after this mark, at today's open.
        if d in start_map:
            overnight = np.zeros(n)
            can_mark = open_ok & np.isfinite(last_close) & (last_close > 0)
            overnight[can_mark] = op[can_mark,d]/last_close[can_mark]-1
            overnight_s = float(own @ overnight)
            overnight_b = float(ew @ overnight)
            if 1+overnight_s > 0: own = own*(1+overnight)/(1+overnight_s)
            if 1+overnight_b > 0: ew = ew*(1+overnight)/(1+overnight_b)
        if d in start_map:
            f = start_map[d]
            target, ew_target, _, _, _ = target_weights(
                signal[:, f], np.isfinite(signal[:, f]), roster[:, d], open_ok, names)
            if d == first:
                # The registered initial trade starts from this date's EW30
                # opening weights, then moves toward the signal target.
                own = ew_target.copy()
                ew = ew_target.copy()
            # Membership determines the new target, but a removed constituent
            # remains tradable at an available open so it can be exited.
            own, traded = _trade(own, target, open_ok)
            turns.append(traded); cost = traded*COST_PER_SIDE; costs.append(cost)
            ew, _ = _trade(ew, ew_target, open_ok, cap=1.0)
            active.append(float(.5*np.abs(own-ew_target).sum()))
        sr, br = np.zeros(n), np.zeros(n)
        for i in range(n):
            if close_ok[i]:
                if d in start_map and open_ok[i]:
                    sr[i] = br[i] = close[i,d]/op[i,d]-1
                elif np.isfinite(last_close[i]) and last_close[i] > 0:
                    sr[i] = br[i] = close[i,d]/last_close[i]-1
        gs, gb = float(own@sr), float(ew@br)
        daily_gross = (1+overnight_s)*(1+gs)-1
        daily_net = (1+overnight_s)*(1-cost)*(1+gs)-1
        daily_bench = (1+overnight_b)*(1+gb)-1
        sret_gross.append(daily_gross); sret.append(daily_net); bret.append(daily_bench)
        if 1+gs: own = own*(1+sr)/(1+gs)
        if 1+gb: ew = ew*(1+br)/(1+gb)
        stale_strategy.update(np.flatnonzero((own > 0) & ~close_ok).tolist())
        stale_benchmark.update(np.flatnonzero((ew > 0) & ~close_ok).tolist())
        last_close[close_ok] = close[close_ok,d]
    # Decision 63: if the final mark is still stale, liquidate at the last
    # valid close and charge one side of transaction costs; do the same for EW.
    stale_s = [i for i in stale_strategy if own[i] > 0 and not np.isfinite(close[i,tmax-1])]
    stale_b = [i for i in stale_benchmark if ew[i] > 0 and not np.isfinite(close[i,tmax-1])]
    terminal_cost = float(own[stale_s].sum()*COST_PER_SIDE) if stale_s else 0.0
    benchmark_terminal_cost = float(ew[stale_b].sum()*COST_PER_SIDE) if stale_b else 0.0
    if sret and terminal_cost:
        sret[-1] = (1+sret[-1])*(1-terminal_cost)-1
        costs.append(terminal_cost)
    if bret and benchmark_terminal_cost:
        bret[-1] = (1+bret[-1])*(1-benchmark_terminal_cost)-1
    s, b, sg = np.asarray(sret), np.asarray(bret), np.asarray(sret_gross)
    p, draws = circular_block_bootstrap_pvalue(s, b, block_length=BOOTSTRAP_BLOCK,
                                                n_draws=BOOTSTRAP_DRAWS, seed=SEED)
    sharpe = lambda x: float(x.mean()/x.std(ddof=1)*math.sqrt(252)) if len(x)>1 and x.std(ddof=1)>0 else 0.0
    gross_edge = float(np.prod(1+sg)-np.prod(1+b))
    net_edge = float(np.prod(1+s)-np.prod(1+b))
    wealth = np.cumprod(1+s)
    peak = np.maximum.accumulate(np.r_[1., wealth])[1:]
    drawdown = float(np.min(wealth/peak-1)) if len(wealth) else 0.0
    return {"strategy_daily_net": s, "benchmark_daily_net": b, "strategy_daily_gross": sg,
            "net_excess_cumulative": net_edge,
            "gross_excess_cumulative": gross_edge,
            "strategy_net_sharpe": sharpe(s), "benchmark_net_sharpe": sharpe(b),
            "bootstrap_p_raw": p, "bootstrap_draws": draws,
            "turnover": np.asarray(turns), "turnover_mean": float(np.mean(turns)) if turns else 0.0,
            "turnover_max": float(max(turns, default=0)),
            "turnover_cap_bind_count": int(np.sum(np.asarray(turns) >= TURNOVER_CAP-1e-10)),
            "active_share": np.asarray(active), "active_share_mean": float(np.mean(active)) if active else 0,
            "costs": np.asarray(costs), "cost_total": float(sum(costs)),
            "cost_gross_edge_ratio": float(sum(costs)/gross_edge) if gross_edge > 0 else None,
            "strategy_net_max_drawdown": drawdown,
            "terminal_stale_fallback_names": len(stale_s),
            "benchmark_terminal_stale_fallback_names": len(stale_b),
            "terminal_exit_cost": terminal_cost,
            "benchmark_terminal_exit_cost": benchmark_terminal_cost,
            "turnover_pass": bool(turns and max(turns) <= TURNOVER_CAP+1e-9),
            "active_share_pass": bool(active and np.mean(active) >= ACTIVE_SHARE_MIN)}


def validate_holm_family(holm_path=HOLM) -> dict:
    cfg = json.loads(Path(holm_path).read_text(encoding="utf-8"))
    family = cfg.get("manifest", [])
    required = [f"R6-H{i}" for i in range(1,22)]
    # The coordinator manifest convention hashes the default JSON encoding of
    # the ordered list (not newline-joined endpoint names).
    digest = hashlib.sha256(json.dumps(family).encode("utf-8")).hexdigest()
    if family != required or cfg.get("manifest_sha256", "").lower() != digest:
        raise InputGateError("Holm family must be the frozen ordered R6-H1..H21 manifest")
    if any(k not in cfg.get("p_values", {}) for k in required):
        raise InputGateError("Holm p-value map is missing a registered endpoint")
    if any(cfg["p_values"].get(k) is not None for k in ENDPOINTS):
        raise InputGateError("G1 Holm slots must be reserved with null p-values before execution")
    return cfg


def holm(current: dict[str, float | None], holm_path=HOLM) -> dict:
    cfg = validate_holm_family(holm_path)
    required = [f"R6-H{i}" for i in range(1,22)]
    pvals = {k: (1.0 if cfg["p_values"][k] is None else float(cfg["p_values"][k])) for k in required}
    # H16-H18 and all previous slots remain immutable in the family file;
    # current G1 slots replace only their null placeholders.
    pvals.update({k: (1.0 if v is None else float(v)) for k,v in current.items()})
    return holm_correction(pvals)


def _trial_count(path=TRIALS) -> int:
    text = Path(path).read_text(encoding="utf-8")
    variants = set(re.findall(r"^\s*-\s*R6\s+variant\s+\d+\s*:\s*([A-Za-z0-9_-]+)\s*$", text, re.M|re.I))
    # Later frozen direction rows record the variant name directly rather
    # than repeating the older numbered R6-variant format.
    variants.update(re.findall(r"^\s*-\s*((?:G1|K1)-V1)\s+FROZEN\b", text, re.M|re.I))
    variants = {v.upper() for v in variants}
    if "G1-V1" not in variants: raise ValueError("G1-V1 must be logged before execution")
    return len(variants)


def _json_safe(x):
    if isinstance(x, dict): return {str(k): _json_safe(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)): return [_json_safe(v) for v in x]
    if isinstance(x, np.ndarray): return _json_safe(x.tolist())
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.floating,float)): return float(x) if np.isfinite(x) else None
    if isinstance(x, (np.bool_,)): return bool(x)
    return x


def verify_inputs(manifest_path=MANIFEST, coverage_path=COVERAGE, inputs_path=INPUTS):
    """Hash/metadata check occurs before NPZ (which contains prices) is opened."""
    for p in (manifest_path, coverage_path, inputs_path):
        if not Path(p).is_file(): raise InputGateError(f"required G1 input artifact missing: {p}")
    m = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if m.get("manifest_version") != 1 or m.get("input_bundle_sha256") != sha256(inputs_path):
        raise InputGateError("G1 input manifest version or bundle digest mismatch")
    cov = pd.read_csv(coverage_path)
    coverage_gate = check_coverage(cov, m, Path(inputs_path), Path(coverage_path))
    return m, coverage_gate


def analyze_and_report(*, manifest_path=MANIFEST, coverage_path=COVERAGE, inputs_path=INPUTS,
                       output_dir=RUN_DIR, holm_path=HOLM, trial_log=TRIALS):
    diff = prereg_diff_payload()
    if not diff.matches: raise InputGateError(f"runner numeric diff is not clean: {diff.differences}")
    manifest, cov = verify_inputs(manifest_path, coverage_path, inputs_path)
    # Governance checks precede loading price-valued arrays or making labels.
    validate_holm_family(holm_path)
    trial_count = _trial_count(trial_log)
    # Coverage file was checked without opening the NPZ; now verify its manifest
    # declaration before reading panels and reconstruct masks for consistency.
    if manifest.get("coverage_sha256") != sha256(coverage_path):
        raise InputGateError("coverage digest mismatch")
    data_npz = np.load(inputs_path, allow_pickle=False)
    data = {k:data_npz[k] for k in data_npz.files}
    dates = np.asarray(data["dates"]).astype(str)
    if len(dates) != 1488 or dates[0] != "2020-11-27" or dates[-1] != "2026-10-30":
        raise InputGateError("bundle calendar does not match the fixed 1,488-session development window")
    for u in ("sp500", "dow"):
        names = np.asarray(data[f"{u}_names"]).astype(str)
        if len(names) != len(set(names.tolist())): raise InputGateError(f"duplicate {u} security identifiers")
        for key in ("roster", "sic2", "volume", "adjusted_open", "adjusted_close"):
            if data[f"{u}_{key}"].shape != (len(names),len(dates)):
                raise InputGateError(f"{u}_{key} has a bad shape")
    masks = availability_masks(data)
    coverage_frame = pd.read_csv(coverage_path)
    forms = masks["sp500"]["forms"]
    expected_forms = dates[forms]
    for u in ("sp500", "dow"):
        subset = coverage_frame.query("universe == @u").sort_values("formation_date")
        if not np.array_equal(subset.formation_date.astype(str).to_numpy(), expected_forms):
            raise InputGateError(f"{u} coverage dates differ from the frozen formation calendar")
        cov_counts = subset.eligible_names.astype(int).to_numpy()
        if not np.array_equal(cov_counts, masks[u]["eligible_counts"]):
            raise InputGateError(f"{u} coverage counts differ from reconstructed availability-only masks")
    forward = _forward_returns(data, masks["sp500"]["eligible"], "sp500")
    sic = np.asarray(data["sp500_sic2"])[:,forms].astype(str)
    score = masks["sp500"]["signal"][:,forms]
    mech = mechanism(score, forward, sic, masks["sp500"]["eligible"])
    placebo = sic2_shuffle(score, forward, sic, masks["sp500"]["eligible"])
    current = {"R6-H19": mech["raw_p"], "R6-H20": placebo["p"], "R6-H21": None}
    raw = {"R6-H19": mech["pass"], "R6-H20": placebo["pass"], "R6-H21": None}
    result = {"variant":"G1-V1", "prereg_sha256":validate_frozen_prereg(PREREG)[1],
              "input_manifest_sha256":sha256(manifest_path), "coverage_gate":cov,
              "availability_mask_hashes":{"calendar":_array_sha256(dates),
                  "sp500":masks["sp500"]["hashes"],"dow":masks["dow"]["hashes"]},
              "mechanism":mech, "placebo":{k:v for k,v in placebo.items() if k!="draws"},
              "placebo_draws":placebo["draws"], "portfolio":None}
    if mech["pass"] and placebo["pass"]:
        di = formation_indices(len(dates)); fwd_indices = di+1
        dscore = masks["dow"]["signal"]
        # Maintain all daily HV5 values; targets consume the formation-date row.
        port = portfolio(dates, data["dow_names"], data["dow_roster"], dscore,
                         data["dow_adjusted_open"], data["dow_adjusted_close"])
        current["R6-H21"] = port["bootstrap_p_raw"]
        raw["R6-H21"] = bool(port["net_excess_cumulative"]>0 and
            port["strategy_net_sharpe"]>port["benchmark_net_sharpe"] and port["turnover_pass"] and
            port["active_share_pass"] and port["bootstrap_p_raw"]<.05)
        port["dsr"] = deflated_sharpe_ratio(port["strategy_daily_net"], trial_count)
        port["trial_count"] = trial_count
        result["portfolio"] = port
    adjusted = holm(current, holm_path)
    if result["portfolio"] is not None:
        result["portfolio"]["bootstrap_p_holm"] = adjusted["R6-H21"]["holm_p"]
    rows=[]
    for k in ENDPOINTS:
        status = "not run" if raw[k] is None else ("pass" if raw[k] else "fail")
        if k == "R6-H21" and raw[k] is not None:
            status = ("pass" if raw[k] and adjusted[k]["reject"] else
                      "raw gates passed; Holm failed" if raw[k] else "raw gates failed")
        rows.append({"endpoint":k,"raw_p":current[k],"raw_gate_pass":raw[k],
          "holm_adjusted_p":adjusted[k]["holm_p"],"holm_reject":adjusted[k]["reject"],
          "status":status})
    result["endpoints"] = rows
    result["holm_family"] = adjusted
    result["settings"] = RUNNER_SPEC_CONFIG
    out = Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    (out/"G1_RESULTS.json").write_text(json.dumps(_json_safe(result),indent=2,allow_nan=False)+"\n",encoding="utf-8")
    with (out/"G1_PLACEBO_DRAWS.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["draw","mean_ic"]); w.writerows(enumerate(placebo["draws"],1))
    with (out/"G1_ENDPOINTS.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(result["endpoints"][0])); w.writeheader(); w.writerows(result["endpoints"])
    if mech["pass"] and placebo["pass"]:
        (out/"MECHANISM_PASS.json").write_text(json.dumps({"variant":"G1-V1","passed":True,
          "prereg_sha256":result["prereg_sha256"]},indent=2)+"\n",encoding="utf-8")
    return result


@guarded_runner(prereg_path=PREREG, run_dir=RUN_DIR)
def run_g1(*, manifest_path=MANIFEST, coverage_path=COVERAGE, inputs_path=INPUTS,
           output_dir=RUN_DIR, holm_path=HOLM, trial_log=TRIALS):
    """Guarded project entry point; synthetic tests call the same analyzer directly."""
    return analyze_and_report(manifest_path=manifest_path, coverage_path=coverage_path,
        inputs_path=inputs_path, output_dir=output_dir, holm_path=holm_path, trial_log=trial_log)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute",action="store_true",help="explicit coordinator authorization for outcomes")
    p.add_argument("--manifest",type=Path,default=MANIFEST)
    p.add_argument("--coverage",type=Path,default=COVERAGE)
    p.add_argument("--inputs",type=Path,default=INPUTS)
    p.add_argument("--output-dir",type=Path,default=RUN_DIR)
    a=p.parse_args(argv)
    try:
        run_g1(manifest_path=a.manifest,coverage_path=a.coverage,inputs_path=a.inputs,
               output_dir=a.output_dir,execute=a.execute)
        return 0
    except Exception as exc:
        print(f"G1 refused/failed: {type(exc).__name__}: {exc}",file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
