"""Synthetic end-to-end coverage for the governance-first runner template."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from r4_harness import phase3, runner_template


def _fixture(tmp_path: Path):
    root = tmp_path / "project"
    prereg_dir = root / "specs" / "r6_prereg"
    specs_dir = root / "specs"
    prereg_dir.mkdir(parents=True)
    frozen_body = "Synthetic test specification.\nFROZEN: 2026-11-11\n"
    digest = phase3.prereg_digest(frozen_body)
    prereg = prereg_dir / "T1.md"
    prereg.write_text(frozen_body + f"SHA256: {digest}\n", encoding="utf-8")

    input_file = root / "synthetic_prices.bin"
    input_file.write_bytes(b"synthetic development input only")
    manifest = {
        "schema": "RUNNER_INPUTS_V1",
        "development_window": ["2020-11-27", "2026-10-30"],
        "input_date_min": "2020-11-27",
        "input_date_max": "2026-10-30",
        "holdout_loaded": False,
        "files": [{"path": "synthetic_prices.bin",
                    "sha256": hashlib.sha256(input_file.read_bytes()).hexdigest()}],
    }
    manifest_path = specs_dir / "T1_INPUT_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    endpoints = ["H1", "H2", "H3"]
    holm = {"manifest": endpoints,
            "manifest_sha256": hashlib.sha256(json.dumps(endpoints).encode()).hexdigest(),
            "p_values": {"H1": 0.04, "H2": None, "H3": None}}
    holm_path = specs_dir / "r6_holm_family.json"
    holm_path.write_text(json.dumps(holm), encoding="utf-8")

    # Three registered R6 variants including this synthetic T1-V1 slot.
    trial_log = specs_dir / "r4_trials.md"
    trial_log.write_text(
        "# Temporary trial registry\n## R6 Holm family\n"
        "- D1-V1\n- E1-V1\n- T1-V1\n## Holdout integrity log\n",
        encoding="utf-8")
    return {"root": root, "prereg_dir": prereg_dir, "prereg": prereg,
            "digest": digest, "manifest": manifest_path, "holm": holm_path,
            "trial_log": trial_log, "run_dir": root / "runs" / "T1",
            "result": root / "results" / "T1_result.json"}


def _kwargs(f):
    return dict(approach="T1", variant="T1-V1", prereg_path=f["prereg"],
                expected_prereg_sha256=f["digest"], prereg_dir=f["prereg_dir"],
                input_manifest_path=f["manifest"], holm_path=f["holm"],
                trial_log=f["trial_log"], project_root=f["root"],
                run_dir=f["run_dir"], result_path=f["result"],
                trial_date="2026-11-11")


def test_full_template_runs_governance_then_real_helpers_and_persists_before_log(tmp_path, monkeypatch):
    f = _fixture(tmp_path)
    sequence = []

    def analyze(governance):
        sequence.append("analyze")
        assert governance["trial_count"] == 3
        assert (f["run_dir"] / ".runner.lock").is_file()
        synthetic_returns = np.array([.01, -.004, .007, .002, -.003, .009,
                                      .001, .005, -.002, .006, .004, -.001])
        benchmark = np.zeros_like(synthetic_returns)
        nw_t = phase3.newey_west_t(synthetic_returns, lag=2)
        p_value, draws = phase3.circular_block_bootstrap_pvalue(
            synthetic_returns, benchmark, block_length=3, n_draws=250, seed=17)
        dsr = phase3.deflated_sharpe_ratio(synthetic_returns,
                                           trial_count=governance["trial_count"])
        assert draws.shape == (250,)
        return {"synthetic_nw_t": nw_t, "synthetic_bootstrap_p": p_value,
                "synthetic_bootstrap_draws": draws,
                "synthetic_dsr": dsr,
                "current_p_values": {"H2": p_value}}

    real_append = phase3.append_trial

    def append_after_result(*args, **kwargs):
        sequence.append("append_trial")
        assert f["result"].is_file(), "result must be durable before trial log append"
        saved = json.loads(f["result"].read_text(encoding="utf-8"))
        assert saved["trial_count"] == 3
        return real_append(*args, **kwargs)

    monkeypatch.setattr(runner_template, "append_trial", append_after_result)
    result = runner_template.run_template(**_kwargs(f), analyze=analyze, execute=True)

    assert sequence == ["analyze", "append_trial"]
    assert (f["run_dir"] / ".runner.lock").is_file()
    saved = json.loads(f["result"].read_text(encoding="utf-8"))
    assert saved["variant"] == "T1-V1"
    assert saved["holm"]["raw_p_values"]["H3"] is None
    assert saved["holm"]["status"]["H3"] == "not run"
    assert saved["holm"]["holm"]["H3"]["holm_p"] == 1.0
    assert np.isfinite(saved["synthetic_nw_t"])
    assert len(result["synthetic_bootstrap_draws"]) == 250
    assert "| T1 | T1-V1 |" in f["trial_log"].read_text(encoding="utf-8")


def test_governance_rejects_pre_window_before_analyze(tmp_path):
    f = _fixture(tmp_path)
    manifest = json.loads(f["manifest"].read_text(encoding="utf-8"))
    manifest["input_date_min"] = "2020-11-26"
    f["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    calls = []
    with pytest.raises(runner_template.GovernanceError, match="before 2020-11-27"):
        runner_template.run_template(**_kwargs(f), analyze=lambda _: calls.append(True), execute=True)
    assert calls == []
    assert not f["run_dir"].exists(), "governance must pass before the lock directory is created"


def test_input_path_date_guard_checks_parent_directories(tmp_path):
    f = _fixture(tmp_path)
    dated_dir = f["root"] / "inputs_2019-12-31"
    dated_dir.mkdir()
    source = f["root"] / "synthetic_prices.bin"
    nested = dated_dir / source.name
    nested.write_bytes(source.read_bytes())
    manifest = json.loads(f["manifest"].read_text(encoding="utf-8"))
    manifest["files"][0] = {"path": "inputs_2019-12-31/synthetic_prices.bin",
                             "sha256": hashlib.sha256(nested.read_bytes()).hexdigest()}
    f["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(runner_template.GovernanceError, match="worker path names pre-window"):
        runner_template.governance_preflight(
            approach="T1", variant="T1-V1", prereg_path=f["prereg"],
            expected_prereg_sha256=f["digest"], prereg_dir=f["prereg_dir"],
            input_manifest_path=f["manifest"], holm_path=f["holm"],
            trial_log=f["trial_log"], project_root=f["root"])


def test_runner_requires_execute_and_immutable_output(tmp_path):
    f = _fixture(tmp_path)
    with pytest.raises(PermissionError, match="--execute"):
        runner_template.run_template(**_kwargs(f), analyze=lambda _: {}, execute=False)
    assert not f["run_dir"].exists()

    f["result"].parent.mkdir(parents=True)
    f["result"].write_text("prior", encoding="utf-8")
    with pytest.raises(FileExistsError, match="immutable"):
        runner_template.write_result_atomic(f["result"], {"value": 1})
