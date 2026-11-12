"""Fail-closed, read-only R7 pre-run checks; never loads market arrays.

The command validates a frozen JSON config and hashes declared input bytes,
but does not parse prices, calculate outcomes, create locks, or write results.
Filesystem denial of sealed roots must be enforced by the execution host.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from r4_harness import phase3
from r4_harness.r7_sp500_adapter import (
    cumulative_trial_count, validate_holm_family,
)
from r4_harness.runner_guard import validate_frozen_prereg

EXPECTED_WINDOW = ("2020-11-27", "2026-10-30")
SEALED_COMPONENTS = {"holdout", "sealed_holdout", "sealed-holdout"}
DATE_RE = re.compile(r"(?<!\d)(\d{4})[-_]?([01]\d)[-_]?([0-3]\d)(?!\d)")


class PreRunError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _safe_path(path: Path, *, root: Path, reject_pre_window: bool = True) -> None:
    resolved = path.resolve()
    if not _within(resolved, root):
        raise PreRunError(f"path escapes approved root: {path}")
    if any(part.casefold() in SEALED_COMPONENTS for part in resolved.parts):
        raise PreRunError(f"sealed-holdout path is forbidden: {path}")
    if reject_pre_window:
        for part in resolved.parts:
            for m in DATE_RE.finditer(part):
                try:
                    if date(int(m[1]), int(m[2]), int(m[3])) < date.fromisoformat(EXPECTED_WINDOW[0]):
                        raise PreRunError(f"path names pre-window data: {path}")
                except ValueError:
                    continue


def synthetic_helper_check() -> dict:
    """Exercise the exact shared inference helpers on generated arrays only."""
    import numpy as np

    x = np.array([.01, -.002, .004, .006, -.001, .008, .003, -.004, .007, .002, .005, -.003])
    y = np.zeros_like(x)
    nw = phase3.newey_west_t(x, lag=2)
    placebo_net = np.zeros((4, 3, 3), dtype=float)
    placebo_net[:, 0, 1] = 1
    placebo = phase3.network_placebos(
        placebo_net, lambda g: float(np.sum(g[:, 0, 1])), n_draws=3,
        seed=23, families=("time_shifted",))
    boot_p, draws = phase3.circular_block_bootstrap_pvalue(
        x, y, block_length=3, n_draws=25, seed=23)
    holm = phase3.holm_correction({"synthetic-a": .03, "synthetic-b": .10})
    dsr = phase3.deflated_sharpe_ratio(x, trial_count=4)
    prices = np.ones((3, 12), dtype=float)
    opens = prices * (1 + np.arange(12)[None, :] * .0001)
    closes = opens * 1.001
    scores = np.tile(np.arange(3, dtype=float)[:, None], (1, 12))
    portfolio = phase3.portfolio_engine(
        scores, opens, closes, [2, 5, 8, 10], design="long_only", n_long=1,
        cost_rate=.0005, bootstrap_draws=25, trial_count=4)
    if not np.isfinite(nw) or len(placebo["time_shifted"].placebo_statistics) != 3:
        raise PreRunError("synthetic Newey-West/placebo helper contract failed")
    if not 0 <= boot_p <= 1 or len(draws) != 25 or not np.isfinite(dsr):
        raise PreRunError("synthetic bootstrap/DSR helper contract failed")
    if set(holm) != {"synthetic-a", "synthetic-b"} or not np.isfinite(portfolio.deflated_sharpe):
        raise PreRunError("synthetic Holm/portfolio helper contract failed")
    return {"newey_west": "pass", "placebo": "pass", "block_bootstrap": "pass",
            "holm": "pass", "dsr": "pass", "portfolio_engine": "pass"}


def check_config(config_path: str | Path, *, run_synthetic_tests: bool = True) -> dict:
    cfg_path = Path(config_path).resolve()
    if not cfg_path.is_file():
        raise PreRunError(f"config does not exist: {cfg_path}")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    root = Path(cfg["project_root"]).resolve()
    approved_root = Path(cfg.get("approved_root", root)).resolve()
    if root != approved_root:
        raise PreRunError("project_root must equal the explicitly approved_root")
    if tuple(cfg.get("development_window", ())) != EXPECTED_WINDOW:
        raise PreRunError(f"development window must be {EXPECTED_WINDOW}")

    # A declared deny boundary is required. If the sealed roots are present and
    # readable to this process, preflight blocks without opening their contents.
    boundary = cfg.get("sealed_access_boundary", {})
    if boundary.get("mode") != "deny_roots" or not boundary.get("sealed_roots"):
        raise PreRunError("sealed_access_boundary must declare mode=deny_roots and sealed_roots")
    for raw in boundary["sealed_roots"]:
        sealed = Path(raw).resolve()
        if not sealed.exists() or os.access(sealed, os.R_OK):
            raise PreRunError(f"sealed root is missing or readable by this process: {sealed}")

    # Check configuration references for prohibited path/date tokens without
    # opening any referenced data. Input file bytes are read only for hashing.
    for key in ("prereg_path", "manifest_path", "holm_path", "trial_ledger_path",
                "runner_path", "adapter_path", "test_path"):
        p = (root / cfg[key]).resolve()
        _safe_path(p, root=root)
        if not p.is_file():
            raise PreRunError(f"required input file does not exist: {p}")
    prereg = (root / cfg["prereg_path"]).resolve()
    _, digest = validate_frozen_prereg(prereg)
    if digest.lower() != str(cfg.get("expected_prereg_sha256", "")).lower():
        raise PreRunError("pre-registration hash differs from reviewed expected hash")
    if not cfg.get("prereg_file_sha256") or _sha256(prereg) != str(cfg["prereg_file_sha256"]).lower():
        raise PreRunError("pre-registration changed since its reviewed file hash")
    auth_date = date.fromisoformat(cfg.get("authorized_run_date", date.today().isoformat()))
    frozen_date = date.fromisoformat(validate_frozen_prereg(prereg)[0])
    if frozen_date > auth_date:
        raise PreRunError("pre-registration freeze date is later than run authorization date")

    manifest_path = (root / cfg["manifest_path"]).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "RUNNER_INPUTS_V1":
        raise PreRunError("manifest schema must be RUNNER_INPUTS_V1")
    if manifest.get("development_window") != list(EXPECTED_WINDOW):
        raise PreRunError("manifest development window mismatch")
    if manifest.get("holdout_loaded") is not False:
        raise PreRunError("manifest must attest holdout_loaded=false")
    if not manifest.get("universe") or not manifest.get("benchmark"):
        raise PreRunError("manifest must identify the universe and benchmark")
    for attestation in ("source", "provenance", "dimensions", "asset_order",
                        "roster_attestation", "coverage_attestation"):
        if not manifest.get(attestation):
            raise PreRunError(f"manifest must include {attestation}")
    lo = date.fromisoformat(str(manifest.get("input_date_min", "")))
    hi = date.fromisoformat(str(manifest.get("input_date_max", "")))
    if lo < date.fromisoformat(EXPECTED_WINDOW[0]) or hi > date.fromisoformat(EXPECTED_WINDOW[1]) or hi < lo:
        raise PreRunError("manifest date bounds escape the development window")
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise PreRunError("manifest requires a nonempty files list")
    inputs = {manifest_path, prereg}
    seen = set()
    for entry in entries:
        p = (root / str(entry["path"])).resolve()
        _safe_path(p, root=root)
        if p in seen or p in inputs:
            raise PreRunError(f"duplicate or colliding manifest path: {p}")
        seen.add(p)
        if not p.is_file():
            raise PreRunError(f"manifest input does not exist: {p}")
        if _sha256(p).lower() != str(entry.get("sha256", "")).lower():
            raise PreRunError(f"manifest SHA-256 mismatch: {p}")
        inputs.add(p)

    family_path = (root / cfg["holm_path"]).resolve()
    family = validate_holm_family(family_path, require_r6_populated=True)
    if len(family["manifest"]) != 24:
        raise PreRunError("R7 family must preserve 21 R6 slots and append three R7 endpoints")

    ledger_path = (root / cfg["trial_ledger_path"]).resolve()
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    trial_count = cumulative_trial_count(
        prior_trials=ledger.get("prior_trials"),
        r7_registered_trials=ledger.get("r7_registered_trials"),
        budget=ledger.get("budget", 30))
    if trial_count != cfg.get("cumulative_trial_count"):
        raise PreRunError("config DSR trial count does not match the frozen cumulative ledger")
    trial_ids = ledger.get("trial_ids", [])
    if len(trial_ids) != trial_count or len(set(trial_ids)) != trial_count:
        raise PreRunError("trial ledger IDs must uniquely reconcile to the cumulative count")

    # All helper/test paths were checked above; run only the synthetic suite.
    helper_status = synthetic_helper_check() if run_synthetic_tests else {"status": "skipped"}
    if run_synthetic_tests:
        proc = subprocess.run([sys.executable, "-m", "pytest", str(root / cfg["test_path"]), "-q"],
                              cwd=root, capture_output=True, text=True, check=False)
        if proc.returncode:
            raise PreRunError("synthetic adapter e2e tests failed: " + proc.stdout[-1000:] + proc.stderr[-1000:])
    helper_paths = {
        "runner": (root / cfg["runner_path"]).resolve(),
        "adapter": (root / cfg["adapter_path"]).resolve(),
        "phase3": (root / "r4_harness" / "phase3.py").resolve(),
        "runner_guard": (root / "r4_harness" / "runner_guard.py").resolve(),
    }
    helper_status["sha256"] = {key: _sha256(path) for key, path in helper_paths.items()}

    outputs = cfg.get("outputs", {})
    required_outputs = ("run_dir", "result_path", "log_path", "run_registry_path")
    if any(k not in outputs for k in required_outputs):
        raise PreRunError("outputs must declare run_dir, result_path, log_path and run_registry_path")
    resolved_outputs = {}
    for key in required_outputs:
        p = (root / outputs[key]).resolve()
        _safe_path(p, root=root)
        if key == "run_registry_path":
            if not p.is_file():
                raise PreRunError(f"R7 run registry does not exist: {p}")
        elif p.exists():
            raise PreRunError(f"immutable output or lock already exists: {p}")
        if key != "run_registry_path" and (not p.parent.exists() or not p.parent.is_dir()):
            raise PreRunError(f"output parent must already exist and be a directory: {p.parent}")
        resolved_outputs[key] = p
    vals = list(resolved_outputs.values())
    nested_collisions = any(a != b and (_within(a, b) or _within(b, a))
                            for i, a in enumerate(vals) for b in vals[i + 1:])
    if len(set(vals)) != len(vals) or nested_collisions or len(set(inputs) & set(vals)):
        raise PreRunError("output destinations collide with each other or an input")
    if resolved_outputs["result_path"].is_relative_to(resolved_outputs["run_dir"]):
        raise PreRunError("result path must be outside the one-shot run lock directory")
    registry = json.loads(resolved_outputs["run_registry_path"].read_text(encoding="utf-8"))
    registry_hash = _sha256(resolved_outputs["run_registry_path"])
    run_id = str(cfg.get("run_id", ""))
    if (not run_id or run_id in registry.get("run_ids", []) or
            not isinstance(registry.get("output_paths"), list)):
        raise PreRunError("run_id is missing or already used in the R7 run registry")
    registered_outputs = {str((root / Path(p)).resolve()) for p in registry["output_paths"]}
    if any(str(p) in registered_outputs for key, p in resolved_outputs.items() if key != "run_registry_path"):
        raise PreRunError("an output path is already recorded in the R7 run registry")

    # Configuration-level placebo interpretation must be explicit and frozen.
    placebo = cfg.get("placebo", {})
    if not all(placebo.get(k) for k in ("transformation", "preserved_properties", "statistic", "sidedness", "decision_rule", "interpretation")):
        raise PreRunError("placebo transformation, preserved properties, statistic, sidedness and rule are required")
    if placebo.get("upper_tail_formula") != "(1 + count(null >= observed)) / (draws + 1)":
        raise PreRunError("placebo upper-tail finite-sample interpretation is missing or ambiguous")
    if not cfg.get("test_order") == ["signal", "placebo", "portfolio", "stop_on_failure"]:
        raise PreRunError("test order must be signal, placebo, portfolio, stopping on failure")
    if cfg.get("one_shot_authorized") is not True:
        raise PreRunError("one-shot execution authorization is absent")
    if _sha256(prereg) != str(cfg["prereg_file_sha256"]).lower():
        raise PreRunError("pre-registration changed during preflight")
    if _sha256(manifest_path) != str(cfg.get("manifest_sha256", "")).lower():
        raise PreRunError("input manifest changed during preflight or lacks its reviewed hash")
    for entry in entries:
        p = (root / str(entry["path"])).resolve()
        if _sha256(p).lower() != str(entry["sha256"]).lower():
            raise PreRunError(f"manifest input changed during preflight: {p}")
    for key, p in resolved_outputs.items():
        if key != "run_registry_path" and p.exists():
            raise PreRunError(f"output appeared during preflight: {p}")
    if _sha256(resolved_outputs["run_registry_path"]) != registry_hash:
        raise PreRunError("R7 run registry changed during preflight")
    return {"status": "READY", "project_root": str(root), "run_id": run_id,
            "prereg_sha256": digest, "input_count": len(entries),
            "holm_slots": len(family["manifest"]), "trial_count": trial_count,
            "helpers": helper_status, "outputs": {k: str(v) for k, v in resolved_outputs.items()},
            "execution_authorized": True}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="frozen R7 pre-run JSON config")
    args = parser.parse_args(argv)
    try:
        result = check_config(args.config)
        print(json.dumps(result, indent=2))
        return 0
    except (PreRunError, KeyError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
