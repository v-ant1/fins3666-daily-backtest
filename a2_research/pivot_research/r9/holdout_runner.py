#!/usr/bin/env python3
"""One-shot J2 holdout gate and Rule 6 evaluator.

This wrapper deliberately imports the holdout engine only after verifying the
frozen preregistration, matching approval hash, and persistent attempt marker.
The engine contract is ``run_frozen_j2(prereg_path, start_date, end_date)`` and
must return aligned ``dates``, ``strategy_net``, ``ew30_net``, and ``trial_count``
fields. No holdout inputs are read by this wrapper before those gates pass.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

START_DATE = "2010-01-01"
END_DATE = "2020-10-31"
FROZEN_J2_FULL_SHA256 = "ed8998e871044b27c4cc9fe3b7b637f10083429503941a30c4ebb3d34c8ef39b"
BOOTSTRAP_DRAWS = 5000
BLOCK_LENGTH = 10
BOOTSTRAP_SEED = 20261111
APPROVAL_PATTERN = re.compile(r"(?im)^\s*J2\.md\s+SHA-256\s*:\s*([0-9a-f]{64})\s*$")
TRIALS_PATTERN = re.compile(r"(?im)\bDSR\s+trial\s+count\s+(?:of|is|:)\s*(\d+)\b")
FROZEN_HASH_PATTERN = re.compile(
    rb"(?m)^SHA-256 \(content above this line\): ([0-9a-f]{64})\s*$"
)


class GateError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def frozen_prerequisites(prereg: Path, approval: Path) -> tuple[str, int]:
    """Validate the exact approved J2 bytes and return their hash and trial count."""
    if not prereg.is_file():
        raise GateError(f"refusing: frozen preregistration is missing: {prereg}")
    if sha256(prereg) != FROZEN_J2_FULL_SHA256:
        raise GateError("refusing: J2.md full-file SHA-256 differs from the frozen approval packet")
    if not approval.is_file():
        raise GateError(f"refusing: holdout approval file is missing: {approval}")
    raw = prereg.read_bytes()
    hash_rows = list(FROZEN_HASH_PATTERN.finditer(raw))
    if len(hash_rows) != 1:
        raise GateError("refusing: J2 preregistration must contain one content-above-footer SHA-256")
    declared_hash = hash_rows[0].group(1).decode("ascii")
    digest = hashlib.sha256(raw[:hash_rows[0].start()]).hexdigest()
    if digest != declared_hash:
        raise GateError("refusing: J2 preregistration content does not match its declared SHA-256")
    approval_text = approval.read_text(encoding="utf-8")
    approved = APPROVAL_PATTERN.findall(approval_text)
    if len(approved) != 1 or approved[0] != digest:
        raise GateError("refusing: approval must contain exactly one matching J2.md SHA-256")
    text = raw.decode("utf-8")
    if not re.search(r"(?im)^\s*\*\*STATUS:\s*FROZEN\b", text):
        raise GateError("refusing: J2 preregistration is not marked frozen")
    trials = TRIALS_PATTERN.findall(text)
    if len(trials) != 1 or int(trials[0]) < 1:
        raise GateError("refusing: J2 preregistration must state one positive full DSR trial count")
    return digest, int(trials[0])


def annualized_sharpe(values: np.ndarray) -> float:
    if values.size < 2:
        return float("nan")
    sd = float(np.std(values, ddof=1))
    return math.sqrt(252.0) * float(np.mean(values)) / sd if sd > 0 else float("nan")


def expected_max_daily_sharpe(trials: int) -> float:
    """Euler approximation to the expected maximum of ``trials`` null Sharpes."""
    if trials <= 1:
        return 0.0
    gamma = 0.5772156649015329
    q1 = 1.0 - 1.0 / trials
    q2 = 1.0 - 1.0 / (trials * math.e)
    return (1.0 - gamma) * _normal_ppf(q1) + gamma * _normal_ppf(q2)


def _normal_ppf(p: float) -> float:
    # Acklam's rational approximation; avoids a SciPy dependency.
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
    plow = 0.02425
    phigh = 1.0 - plow
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)
    if p > phigh:
        q = math.sqrt(-2.0 * math.log(1.0-p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)
    q = p - 0.5
    r = q*q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           ((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1.0


# Cross-trial variance estimated on the corrected common-window R9 dev returns.
# R6 D1/E1 had no portfolio run; see specs/r9_decisions.md for the limitation.
PRIMARY_SHARPE_VARIANCE = 8.415393784762033e-05


def deflated_sharpe_ratio(values: np.ndarray, trials: int,
                          sharpe_variance: float = PRIMARY_SHARPE_VARIANCE) -> float:
    """Probabilistic DSR with SR0 = sqrt(V) * E[max Z], using daily net returns."""
    n = values.size
    if n < 3 or trials < 1:
        return float("nan")
    centered = values - np.mean(values)
    sd = float(np.std(values, ddof=1))
    if sd <= 0:
        return float("nan")
    sr = float(np.mean(values) / sd)
    skew = float(np.mean(centered**3) / (np.mean(centered**2)**1.5))
    kurtosis = float(np.mean(centered**4) / (np.mean(centered**2)**2))
    variance_term = 1.0 - skew*sr + ((kurtosis - 1.0) / 4.0) * sr*sr
    if variance_term <= 0:
        return float("nan")
    sr0 = math.sqrt(max(float(sharpe_variance), 0.0)) * expected_max_daily_sharpe(trials)
    z = (sr - sr0) * math.sqrt(n - 1) / math.sqrt(variance_term)
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def circular_block_bootstrap_p(excess: np.ndarray) -> float:
    """One-sided centered circular block-bootstrap p-value for positive excess."""
    n = excess.size
    if n < BLOCK_LENGTH:
        raise ValueError(f"need at least {BLOCK_LENGTH} daily returns for the registered bootstrap")
    observed = float(np.mean(excess))
    null = excess - observed
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    blocks_needed = math.ceil(n / BLOCK_LENGTH)
    exceed = 0
    offsets = np.arange(BLOCK_LENGTH)
    for _ in range(BOOTSTRAP_DRAWS):
        starts = rng.integers(0, n, size=blocks_needed)
        idx = ((starts[:, None] + offsets[None, :]) % n).ravel()[:n]
        if float(np.mean(null[idx])) >= observed:
            exceed += 1
    return (1 + exceed) / (BOOTSTRAP_DRAWS + 1)


def evaluate_rule6(result: dict[str, Any], expected_trials: int) -> dict[str, Any]:
    dates = [str(d)[:10] for d in result["dates"]]
    strategy = np.asarray(result["strategy_net"], dtype=float)
    benchmark = np.asarray(result["ew30_net"], dtype=float)
    if len(dates) != strategy.size or strategy.size != benchmark.size or strategy.size == 0:
        raise ValueError("holdout engine returned non-aligned or empty daily series")
    if dates != sorted(dates) or len(set(dates)) != len(dates):
        raise ValueError("holdout dates must be unique and sorted")
    if any(d < START_DATE or d > END_DATE for d in dates):
        raise ValueError("holdout engine returned dates outside 2010-01-01 through 2020-10-31")
    if not np.all(np.isfinite(strategy)) or not np.all(np.isfinite(benchmark)):
        raise ValueError("holdout net return series contain missing or non-finite values")
    if int(result["trial_count"]) != expected_trials:
        raise ValueError("holdout engine DSR trial count does not match frozen preregistration")
    strategy_total = float(np.prod(1.0 + strategy) - 1.0)
    benchmark_total = float(np.prod(1.0 + benchmark) - 1.0)
    excess = strategy - benchmark
    sharpe_s = annualized_sharpe(strategy)
    sharpe_b = annualized_sharpe(benchmark)
    bootstrap_p = circular_block_bootstrap_p(excess)
    # Report both preregistered variance choices. The observed 12-stream R9
    # estimate is primary; the null alternative uses V=1/(T-1), where T is
    # the number of daily observations in this holdout series.
    dsr_primary = deflated_sharpe_ratio(
        strategy, expected_trials, PRIMARY_SHARPE_VARIANCE)
    null_variance = 1.0 / (strategy.size - 1) if strategy.size > 1 else float("nan")
    dsr_null = deflated_sharpe_ratio(strategy, expected_trials, null_variance)
    checks = {
        "net_return_beats_ew30": strategy_total > benchmark_total,
        "net_sharpe_beats_ew30": sharpe_s > sharpe_b,
        "one_sided_bootstrap_p_below_0_05": bootstrap_p < 0.05,
        "deflated_sharpe_above_0_95": dsr_primary > 0.95,
    }
    return {
        "period": {"start": dates[0], "end": dates[-1], "n_daily": int(strategy.size)},
        "strategy_net_cumulative_return": strategy_total,
        "ew30_net_cumulative_return": benchmark_total,
        "net_cumulative_excess": strategy_total - benchmark_total,
        "strategy_annualized_net_sharpe": sharpe_s,
        "ew30_annualized_net_sharpe": sharpe_b,
        "one_sided_10_session_circular_bootstrap_p": bootstrap_p,
        "dsr": dsr_primary,
        "dsr_primary_observed_12_stream_v": dsr_primary,
        "dsr_null_1_over_t_minus_1": dsr_null,
        "dsr_primary_variance": PRIMARY_SHARPE_VARIANCE,
        "dsr_null_variance": null_variance,
        "dsr_deciding_choice": "primary_observed_12_stream_v",
        "dsr_trial_count": expected_trials,
        "bootstrap": {"draws": BOOTSTRAP_DRAWS, "block_length": BLOCK_LENGTH,
                      "seed": BOOTSTRAP_SEED},
        "checks": checks,
        "pass": all(checks.values()),
    }


def _load_engine(engine_path: Path):
    spec = importlib.util.spec_from_file_location("r9_frozen_j2_engine", engine_path)
    if spec is None or spec.loader is None:
        raise GateError(f"cannot load frozen J2 engine: {engine_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    run = getattr(module, "run_frozen_j2", None)
    if not callable(run):
        raise GateError("j2_frozen.py must expose run_frozen_j2(prereg_path, start_date, end_date)")
    return run


def run_once(root: Path, synthetic_hash_override: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    if synthetic_hash_override is not None:
        fixture_root = Path(__file__).resolve().parents[1] / "r9" / "j2ready" / "synthetic_case"
        marker = root / "r9" / "j2ready" / "SYNTHETIC_ONLY.txt"
        if (root != fixture_root.resolve() or not marker.is_file()
                or not re.fullmatch(r"[0-9a-f]{64}", synthetic_hash_override)):
            raise GateError("refusing: synthetic hash override is restricted to the marked r9/j2ready fixture path")
    prereg = root / "specs" / "r9_prereg" / "J2.md"
    approval = root / "specs" / "r9_HOLDOUT_APPROVED.txt"
    runner_path = root / "r9" / "j2_frozen.py"
    attempt = root / "r9" / "HOLDOUT_ATTEMPTED.txt"
    output = root / "r9" / "HOLDOUT_RESULT.json"

    prereg_hash, trials = frozen_prerequisites(prereg, approval)
    if not runner_path.is_file():
        raise GateError(f"frozen J2 engine is missing: {runner_path}")
    if attempt.exists():
        raise GateError(f"refusing: one-shot attempt marker already exists: {attempt}")

    # Persist the one-shot claim before importing or invoking code that can read holdout inputs.
    attempt.write_text(
        f"J2 prereg SHA-256: {prereg_hash}\nAttempt claimed UTC: {datetime.now(timezone.utc).isoformat()}\n",
        encoding="utf-8",
    )
    run_frozen_j2 = _load_engine(runner_path)
    result = run_frozen_j2(prereg, START_DATE, END_DATE,
                           synthetic_hash_override=synthetic_hash_override)
    summary = evaluate_rule6(result, trials)
    summary["approved_j2_sha256"] = prereg_hash
    summary["holdout_rule"] = "R9 rule 6"
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def self_test() -> None:
    """Exercise gates and Rule 6 calculations using synthetic-only inputs."""
    import tempfile

    with tempfile.TemporaryDirectory(prefix="r9_synthetic_") as tmp:
        root = Path(tmp)
        prereg = root / "J2.md"
        approval = root / "approval.txt"
        body = "# Synthetic J2\n\n**STATUS: FROZEN CANDIDATE**\n\nDSR trial count of 12.\n\n"
        content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        prereg.write_bytes((body + f"SHA-256 (content above this line): {content_hash}\n").encode("utf-8"))
        approval.write_text(f"J2.md SHA-256: {content_hash}\n", encoding="utf-8")
        digest, trials = frozen_prerequisites(prereg, approval)
        assert digest == content_hash and trials == 12
        try:
            frozen_prerequisites(prereg, root / "missing-approval.txt")
        except GateError:
            pass
        else:
            raise AssertionError("missing approval must fail closed")

    rng = np.random.default_rng(3666)
    n = 420
    dates = np.array([str(np.datetime64("2010-01-01") + np.timedelta64(i, "D")) for i in range(n)])
    benchmark = rng.normal(0.0002, 0.008, n)
    strategy = benchmark + rng.normal(0.0003, 0.006, n)
    result = {"dates": dates.tolist(), "strategy_net": strategy.tolist(),
              "ew30_net": benchmark.tolist(), "trial_count": 12}
    summary = evaluate_rule6(result, 12)
    assert summary["period"]["n_daily"] == n
    assert 0.0 <= summary["one_sided_10_session_circular_bootstrap_p"] <= 1.0
    assert 0.0 <= summary["dsr"] <= 1.0
    print("Synthetic holdout runner self-check passed; no holdout files were opened.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="pivot_research project root")
    parser.add_argument("--self-test", action="store_true",
                        help="run calculations and approval checks on synthetic data only")
    parser.add_argument("--synthetic-hash-override", type=str,
                        help="synthetic-only expected panel digest; accepted only for the marked r9/j2ready fixture")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    try:
        summary = run_once(args.root.resolve(), args.synthetic_hash_override)
    except (GateError, KeyError, TypeError, ValueError, OSError) as exc:
        print(f"HOLDOUT RUN REFUSED/FAILED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
