#!/usr/bin/env python3
"""Build and exercise a schema-matched synthetic J2 holdout gate fixture."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import exchange_calendars as xcals
import numpy as np


PROJECT = Path(__file__).resolve().parents[2]
READY = Path(__file__).resolve().parent
CASE = READY / "synthetic_case"
SYNTHETIC_PANEL = CASE / "r9" / "j2ready" / "J2_HOLDOUT_SYNTHETIC.npz"
APPROVAL = CASE / "specs" / "r9_HOLDOUT_APPROVED.txt"
ATTEMPT = CASE / "r9" / "HOLDOUT_ATTEMPTED.txt"
RESULT = CASE / "r9" / "HOLDOUT_RESULT.json"
RUNNER = PROJECT / "r9" / "holdout_runner.py"
FROZEN = PROJECT / "specs" / "r9_prereg" / "J2.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_synthetic_panel() -> str:
    CASE.mkdir(parents=True, exist_ok=True)
    (CASE / "r9" / "j2ready").mkdir(parents=True, exist_ok=True)
    (CASE / "specs" / "r9_prereg").mkdir(parents=True, exist_ok=True)
    (CASE / "r9").mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROJECT / "r9" / "j2_frozen.py", CASE / "r9" / "j2_frozen.py")
    shutil.copy2(FROZEN, CASE / "specs" / "r9_prereg" / "J2.md")
    (CASE / "r9" / "j2ready" / "SYNTHETIC_ONLY.txt").write_text(
        "Synthetic random panel fixture. No sealed input is used.\n", encoding="utf-8")

    sessions = xcals.get_calendar("XNYS").sessions_in_range("2016-01-04", "2020-10-30")
    dates = np.asarray([d.strftime("%Y-%m-%d") for d in sessions], dtype="<U10")
    if len(dates) != 1217 or dates[0] != "2016-01-04" or dates[-1] != "2020-10-30":
        raise RuntimeError("installed XNYS calendar does not match the BUILD_REPORT schema bounds/count")

    rng = np.random.default_rng(3666)
    sp_assets = np.asarray([f"S{i:04d}" for i in range(631)], dtype="<U5")
    dow_assets = sp_assets[:41].copy()
    sic_values = np.asarray([f"{10 + i % 12:02d}" for i in range(631)], dtype="<U2")
    sp_sic = np.repeat(sic_values[:, None], len(dates), axis=1).astype("<U2")
    dow_sic = sp_sic[:41].copy()

    def prices(count: int) -> tuple[np.ndarray, np.ndarray]:
        overnight = rng.normal(0.0, 0.003, (count, len(dates)))
        intraday = rng.normal(0.00015, 0.009, (count, len(dates)))
        close = np.empty((count, len(dates)), dtype=np.float64)
        open_ = np.empty_like(close)
        close[:, 0] = rng.uniform(20.0, 180.0, count)
        open_[:, 0] = close[:, 0] * (1.0 + overnight[:, 0])
        for t in range(1, len(dates)):
            open_[:, t] = close[:, t - 1] * (1.0 + overnight[:, t])
            close[:, t] = open_[:, t] * (1.0 + intraday[:, t])
        return open_, close

    sp_open, sp_close = prices(631)
    dow_open, dow_close = sp_open[:41].copy(), sp_close[:41].copy()
    panel = {
        "sp500_dates": dates,
        "sp500_assets": sp_assets,
        "sp500_roster": np.ones((631, len(dates)), dtype=bool),
        "sp500_sic2": sp_sic,
        "sp500_adjusted_open": sp_open.astype(np.float64, copy=False),
        "sp500_adjusted_close": sp_close.astype(np.float64, copy=False),
        "dow_dates": dates.copy(),
        "dow_assets": dow_assets,
        "dow_roster": np.ones((41, len(dates)), dtype=bool),
        "dow_sic2": dow_sic,
        "dow_adjusted_open": dow_open.astype(np.float64, copy=False),
        "dow_adjusted_close": dow_close.astype(np.float64, copy=False),
    }
    np.savez(SYNTHETIC_PANEL, **panel)
    return sha256(SYNTHETIC_PANEL)


def invoke(expected_hash: str | None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(RUNNER), "--root", str(CASE)]
    if expected_hash is not None:
        command.extend(["--synthetic-hash-override", expected_hash])
    return subprocess.run(command, capture_output=True, text=True, check=False)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    digest = build_synthetic_panel()
    if ATTEMPT.exists():
        ATTEMPT.unlink()
    if RESULT.exists():
        RESULT.unlink()
    if APPROVAL.exists():
        APPROVAL.unlink()

    missing_approval = invoke(digest)
    require(missing_approval.returncode == 2, "runner did not refuse missing synthetic approval")
    require(not ATTEMPT.exists(), "missing approval should refuse before claiming a run")

    j2_hash = re.search(
        rb"(?m)^SHA-256 \(content above this line\): ([0-9a-f]{64})\s*$",
        FROZEN.read_bytes()).group(1).decode("ascii")
    APPROVAL.write_text(f"J2.md SHA-256: {j2_hash}\n", encoding="utf-8")
    mismatch = invoke("0" * 64)
    require(mismatch.returncode == 2, "runner did not refuse the synthetic panel digest mismatch")
    require(ATTEMPT.exists() and not RESULT.exists(), "hash mismatch should claim the attempt but write no result")

    # Reset only synthetic-case state so the successful path can be exercised independently.
    ATTEMPT.unlink()
    if RESULT.exists():
        RESULT.unlink()
    first = invoke(digest)
    require(first.returncode == 0, f"synthetic run failed: {first.stderr.strip()}")
    require(ATTEMPT.is_file() and RESULT.is_file(), "successful run must write marker and result")
    summary = json.loads(RESULT.read_text(encoding="utf-8"))
    require("dsr_primary_observed_12_stream_v" in summary
            and "dsr_null_1_over_t_minus_1" in summary,
            "result must report both frozen DSR variants")
    require("pass" in summary and summary["period"]["n_daily"] > 0,
            "result must contain Rule-6 decision and daily period")
    second = invoke(digest)
    require(second.returncode == 2, "runner did not refuse the second synthetic run")
    require("one-shot attempt marker already exists" in second.stderr,
            "second-run refusal was not caused by the one-shot marker")

    report = {
        "synthetic_only": True,
        "npz_sha256": digest,
        "schema": {key: {"dtype": str(value.dtype), "shape": list(value.shape)}
                   for key, value in panel_metadata(SYNTHETIC_PANEL).items()},
        "gates": {
            "missing_approval_refused": missing_approval.returncode == 2,
            "npz_hash_mismatch_refused": mismatch.returncode == 2,
            "first_run_wrote_result": first.returncode == 0,
            "result_reports_both_dsrs": True,
            "second_run_refused": second.returncode == 2,
        },
        "result_path": str(RESULT.relative_to(PROJECT)),
        "note": "Synthetic hash override is accepted only for the marked r9/j2ready/synthetic_case root.",
    }
    (READY / "SYNTHETIC_DRY_RUN.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


def panel_metadata(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


if __name__ == "__main__":
    raise SystemExit(main())
