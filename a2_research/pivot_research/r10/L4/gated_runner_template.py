#!/usr/bin/env python3
"""Approval-gated, hash-pinned, one-shot runner for a frozen R10 strategy.

The runner reads the approved preregistration/engine/runner files to verify
their pins, then creates the persistent one-shot marker before hashing or
loading the panel. A frozen engine exposes
`run_frozen_strategy(prereg_path, panel, start_date, end_date)` and returns
aligned `dates`, `strategy_net`, `benchmark_net`, and `trial_count` fields.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

PRIMARY_V = 0.00008415393784762033
BOOTSTRAP_DRAWS = 5000
BLOCK_LENGTH = 10
BOOTSTRAP_SEED = 20261111
START = "2010-01-04"
END = "2015-12-31"


class GateError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def resolve_inside(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise GateError("all manifest paths must stay within the declared project root") from exc
    return path


def _expected_approval(manifest_hash: str, m: dict[str, Any]) -> str:
    rows = [
        "R10 HOLDOUT APPROVAL",
        f"manifest_sha256={manifest_hash}",
        f"strategy_id={m['strategy_id']}",
        f"prereg_sha256={m['prereg_sha256']}",
        f"engine_sha256={m['engine_sha256']}",
        f"runner_sha256={m['runner_sha256']}",
        f"panel_sha256={m['panel_sha256']}",
    ]
    return "\n".join(rows) + "\n"


def _check_hash(path: Path, expected: str, label: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected)):
        raise GateError(f"refusing: invalid {label} SHA-256 pin")
    if not path.is_file() or sha256(path) != expected:
        raise GateError(f"refusing: {label} SHA-256 mismatch or file missing")


def _claim_marker(path: Path, strategy_id: str, manifest_hash: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (f"R10 one-shot attempt claimed\nstrategy_id={strategy_id}\n"
               f"manifest_sha256={manifest_hash}\nclaimed_utc={datetime.now(timezone.utc).isoformat()}\n")
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise GateError("refusing: one-shot marker already exists") from exc
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())


def _normal_ppf(p: float) -> float:
    if not 0.0 < p < 1.0:
        raise ValueError("normal quantile probability must be between zero and one")
    a = (-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2,
         1.383577518672690e2, -3.066479806614716e1, 2.506628277459239)
    b = (-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2,
         6.680131188771972e1, -1.328068155288572e1)
    c = (-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838,
         -2.549732539343734, 4.374664141464968, 2.938163982698783)
    d = (7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996,
         3.754408661907416)
    plow, phigh = 0.02425, 1.0 - 0.02425
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)
    if p > phigh:
        q = math.sqrt(-2.0 * math.log(1.0-p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)
    q, r = p - 0.5, (p - 0.5) ** 2
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r)+1.0


def expected_max_daily_sharpe(trials: int) -> float:
    if trials <= 1:
        return 0.0
    gamma = 0.5772156649015329
    return ((1.0-gamma) * _normal_ppf(1.0-1.0/trials)
            + gamma * _normal_ppf(1.0-1.0/(trials*math.e)))


def dsr(values: np.ndarray, trials: int, variance: float) -> float:
    n = values.size
    if n < 3 or trials < 1:
        return float("nan")
    centered = values - np.mean(values)
    sd = float(np.std(values, ddof=1))
    if sd <= 0:
        return float("nan")
    sr = float(np.mean(values) / sd)
    skew = float(np.mean(centered**3) / np.mean(centered**2)**1.5)
    kurt = float(np.mean(centered**4) / np.mean(centered**2)**2)
    term = 1.0 - skew*sr + ((kurt-1.0)/4.0)*sr*sr
    if term <= 0:
        return float("nan")
    sr0 = math.sqrt(max(variance, 0.0)) * expected_max_daily_sharpe(trials)
    z = (sr - sr0) * math.sqrt(n-1) / math.sqrt(term)
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def annualized_sharpe(values: np.ndarray) -> float:
    sd = float(np.std(values, ddof=1))
    return math.sqrt(252.0) * float(np.mean(values)) / sd if sd > 0 else float("nan")


def circular_bootstrap_p(excess: np.ndarray) -> float:
    if excess.size < BLOCK_LENGTH:
        raise ValueError("daily series is shorter than the frozen 10-session bootstrap block")
    observed = float(np.mean(excess))
    null = excess - observed
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    nblocks = math.ceil(excess.size / BLOCK_LENGTH)
    offsets = np.arange(BLOCK_LENGTH)
    exceed = 0
    for _ in range(BOOTSTRAP_DRAWS):
        starts = rng.integers(0, excess.size, size=nblocks)
        ix = ((starts[:, None] + offsets[None, :]) % excess.size).ravel()[:excess.size]
        if float(np.mean(null[ix])) >= observed:
            exceed += 1
    return (1 + exceed) / (BOOTSTRAP_DRAWS + 1)


def evaluate(result: dict[str, Any], trials: int) -> dict[str, Any]:
    dates = [str(x)[:10] for x in result["dates"]]
    strategy = np.asarray(result["strategy_net"], dtype=np.float64)
    benchmark = np.asarray(result["benchmark_net"], dtype=np.float64)
    if not dates or len(dates) != strategy.size or strategy.size != benchmark.size:
        raise ValueError("strategy engine returned empty or misaligned series")
    if dates != sorted(dates) or len(set(dates)) != len(dates):
        raise ValueError("strategy engine dates must be unique and sorted")
    if dates[0] < START or dates[-1] != END:
        raise ValueError("strategy engine must cover through the frozen final session 2015-12-31")
    if not np.all(np.isfinite(strategy)) or not np.all(np.isfinite(benchmark)):
        raise ValueError("strategy engine returned non-finite net returns")
    if int(result["trial_count"]) != trials:
        raise ValueError("strategy engine DSR trial count differs from the approved manifest")
    s_total, b_total = float(np.prod(1+strategy)-1), float(np.prod(1+benchmark)-1)
    excess = strategy - benchmark
    p = circular_bootstrap_p(excess)
    primary = dsr(strategy, trials, PRIMARY_V)
    null_v = 1.0/(strategy.size-1)
    null = dsr(strategy, trials, null_v)
    checks = {
        "net_return_beats_benchmark": s_total > b_total,
        "net_sharpe_beats_benchmark": annualized_sharpe(strategy) > annualized_sharpe(benchmark),
        "one_sided_bootstrap_p_below_0_05": p < .05,
        "primary_dsr_above_0_95": primary > .95,
    }
    return {
        "strategy_id": "", "period": {"start": dates[0], "end": dates[-1], "n_daily": int(strategy.size)},
        "strategy_net_cumulative_return": s_total, "benchmark_net_cumulative_return": b_total,
        "net_cumulative_excess": s_total-b_total,
        "strategy_annualized_net_sharpe": annualized_sharpe(strategy),
        "benchmark_annualized_net_sharpe": annualized_sharpe(benchmark),
        "one_sided_10_session_circular_bootstrap_p": p,
        "dsr_primary_observed_12_stream_v": primary, "dsr_null_1_over_t_minus_1": null,
        "dsr_primary_variance": PRIMARY_V, "dsr_null_variance": null_v,
        "dsr_trial_count": trials, "bootstrap": {"draws": BOOTSTRAP_DRAWS,
        "block_length": BLOCK_LENGTH, "seed": BOOTSTRAP_SEED},
        "checks": checks, "pass": all(checks.values()),
    }


def _load_engine(path: Path):
    spec = importlib.util.spec_from_file_location("r10_frozen_strategy_engine", path)
    if spec is None or spec.loader is None:
        raise GateError("cannot load frozen strategy engine")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, "run_frozen_strategy", None)
    if not callable(fn):
        raise GateError("engine must expose run_frozen_strategy(prereg_path, panel, start_date, end_date)")
    return fn


def load_panel(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as data:
        panel = {k: data[k] for k in data.files}
    expected = {f"{g}_{s}" for g in ("sp500", "dow") for s in
                ("dates", "assets", "roster", "sic2", "adjusted_open", "adjusted_close")}
    if set(panel) != expected:
        raise ValueError("panel keys differ from the frozen development NPZ schema")
    dates = panel["sp500_dates"].astype(str)
    if not np.array_equal(dates, panel["dow_dates"].astype(str)):
        raise ValueError("S&P and Dow session axes must be identical")
    if dates.size < 2 or dates[0] < START or dates[-1] > END or not np.all(dates[:-1] < dates[1:]):
        raise ValueError("panel dates must be increasing and inside the frozen candidate interval")
    dtype_by_suffix = {"dates": np.dtype("<U10"), "assets": np.dtype("<U5"),
                       "roster": np.dtype(bool), "sic2": np.dtype("<U2"),
                       "adjusted_open": np.dtype(np.float64), "adjusted_close": np.dtype(np.float64)}
    for group in ("sp500", "dow"):
        n_assets = panel[f"{group}_assets"].size
        if panel[f"{group}_assets"].ndim != 1:
            raise ValueError(f"{group}_assets must be one-dimensional")
        for suffix, expected_dtype in dtype_by_suffix.items():
            arr = panel[f"{group}_{suffix}"]
            if arr.dtype != expected_dtype:
                raise ValueError(f"{group}_{suffix} dtype differs from development schema")
            shape = ((dates.size,) if suffix == "dates" else (n_assets,) if suffix == "assets"
                     else (n_assets, dates.size))
            if arr.shape != shape:
                raise ValueError(f"{group}_{suffix} shape differs from development schema")
    return panel


def run_once(root: Path, manifest_rel: str) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = resolve_inside(root, manifest_rel)
    if not manifest_path.is_file():
        raise GateError("run manifest is missing")
    manifest_bytes = manifest_path.read_bytes()
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    m = json.loads(manifest_bytes)
    if m.get("start_date") != START or m.get("end_date") != END:
        raise GateError("manifest must pin the untouched 2010-01-04 through 2015-12-31 interval")
    if not isinstance(m.get("dsr_trials"), int) or m["dsr_trials"] < 1:
        raise GateError("manifest must pin a positive DSR trial count")
    prereg = resolve_inside(root, m["prereg_path"])
    engine = resolve_inside(root, m["engine_path"])
    approval = resolve_inside(root, m["approval_path"])
    panel_path = resolve_inside(root, m["panel_path"])
    marker = resolve_inside(root, m["marker_path"])
    output = resolve_inside(root, m["output_path"])
    if marker.exists() or output.exists():
        raise GateError("refusing: marker or result output already exists")
    if not approval.is_file():
        raise GateError("refusing: approval file is missing")
    _check_hash(prereg, m.get("prereg_sha256", ""), "frozen preregistration")
    _check_hash(engine, m.get("engine_sha256", ""), "frozen strategy engine")
    _check_hash(Path(__file__).resolve(), m.get("runner_sha256", ""), "one-shot runner")
    if approval.read_text(encoding="utf-8") != _expected_approval(manifest_hash, m):
        raise GateError("refusing: approval file does not exactly pin manifest and code/data hashes")
    if not panel_path.is_file():
        raise GateError("refusing: approved panel file is missing")

    # Claim first. Panel hashing is itself the first panel-byte read.
    _claim_marker(marker, str(m["strategy_id"]), manifest_hash)
    _check_hash(panel_path, m.get("panel_sha256", ""), "approved panel")
    panel = load_panel(panel_path)
    engine_run = _load_engine(engine)
    result = engine_run(prereg, panel, START, END)
    summary = evaluate(result, int(m["dsr_trials"]))
    summary["strategy_id"] = str(m["strategy_id"])
    summary["approved_manifest_sha256"] = manifest_hash
    summary["approved_prereg_sha256"] = m["prereg_sha256"]
    summary["approved_engine_sha256"] = m["engine_sha256"]
    summary["approved_panel_sha256"] = m["panel_sha256"]
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    tmp.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, output)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(run_once(args.root, args.manifest), indent=2))
    except (GateError, KeyError, TypeError, ValueError, OSError) as exc:
        print(f"R10 HOLDOUT RUN REFUSED/FAILED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
