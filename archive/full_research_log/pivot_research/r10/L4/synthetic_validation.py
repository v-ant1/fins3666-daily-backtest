#!/usr/bin/env python3
"""Run the single pre-registered L4-SYNTH-01 fixture suite; never uses real data."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from datetime import date, timedelta
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_module("r10_builder_template", HERE / "build_panel_template.py")
runner = load_module("r10_gated_runner", HERE / "gated_runner_template.py")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synthetic_dates() -> list[str]:
    out, d = [], date(2010, 1, 4)
    end = date(2015, 12, 31)
    while d <= end:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def write_source_csv(path: Path, dates: list[str]) -> None:
    rows = ["universe,date,asset,roster,sic2,adjusted_open,adjusted_close"]
    for group, assets in (("sp500", ("AAA", "BBB")), ("dow", ("AAA",))):
        for ai, asset in enumerate(assets):
            for ti, d in enumerate(dates):
                base = 10.0 + ai * 3.0 + ti * 0.01
                rows.append(f"{group},{d},{asset},true,{10+ai:02d},{base:.6f},{base+0.02:.6f}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def make_fixture(root: Path, *, panel_hash_override: str | None = None,
                 approval: bool = True) -> tuple[Path, Path]:
    data_dir = root / "fixture"
    data_dir.mkdir(parents=True, exist_ok=True)
    dates = synthetic_dates()
    csv_path, panel_path = data_dir / "synthetic.csv", data_dir / "panel.npz"
    write_source_csv(csv_path, dates)
    builder.build(csv_path, panel_path, data_dir / "builder_report.json")
    prereg = data_dir / "frozen.md"
    prereg.write_text("Synthetic frozen strategy; no real observations.\n", encoding="utf-8")
    engine = data_dir / "engine.py"
    engine.write_text(
        "import numpy as np\n"
        "def run_frozen_strategy(prereg_path, panel, start_date, end_date):\n"
        "    dates = panel['sp500_dates'].astype(str).tolist()[1:]\n"
        "    b = np.full(len(dates), 0.0001, dtype=float)\n"
        "    s = b + np.linspace(-0.0002, 0.0003, len(dates))\n"
        "    return {'dates': dates, 'strategy_net': s, 'benchmark_net': b, 'trial_count': 50}\n",
        encoding="utf-8")
    manifest = {
        "strategy_id": "L4-SYNTH-01-fixture",
        "start_date": runner.START, "end_date": runner.END,
        "prereg_path": "fixture/frozen.md", "prereg_sha256": digest(prereg),
        "engine_path": "fixture/engine.py", "engine_sha256": digest(engine),
        "runner_sha256": digest(HERE / "gated_runner_template.py"),
        "panel_path": "fixture/panel.npz",
        "panel_sha256": panel_hash_override or digest(panel_path),
        "approval_path": "fixture/approval.txt",
        "marker_path": "fixture/attempted.txt", "output_path": "fixture/result.json",
        "dsr_trials": 50,
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if approval:
        mh = digest(manifest_path)
        (data_dir / "approval.txt").write_text(runner._expected_approval(mh, manifest), encoding="utf-8")
    return manifest_path, panel_path


def expect_refusal(fn, text: str) -> None:
    try:
        fn()
    except runner.GateError as exc:
        assert text in str(exc), (text, str(exc))
        return
    raise AssertionError(f"expected refusal containing {text!r}")


def run() -> dict:
    with tempfile.TemporaryDirectory(prefix="l4_synth_", dir=HERE) as temp:
        base = Path(temp)

        # Builder contract and metadata-only report.
        dates = synthetic_dates()
        csv_path = base / "builder.csv"
        panel_path = base / "builder.npz"
        report_path = base / "builder_report.json"
        write_source_csv(csv_path, dates)
        report = builder.build(csv_path, panel_path, report_path)
        with np.load(panel_path, allow_pickle=False) as z:
            expected = {f"{g}_{s}" for g in ("sp500", "dow") for s in
                        ("dates", "assets", "roster", "sic2", "adjusted_open", "adjusted_close")}
            assert set(z.files) == expected
            assert z["sp500_dates"].dtype == np.dtype("<U10")
            assert z["sp500_assets"].dtype == np.dtype("<U5")
            assert z["sp500_roster"].dtype == np.dtype(bool)
            assert z["sp500_sic2"].dtype == np.dtype("<U2")
            assert z["sp500_adjusted_open"].dtype == np.dtype(np.float64)
            assert z["sp500_adjusted_close"].shape == (2, len(dates))
            assert z["dow_adjusted_close"].shape == (1, len(dates))
        assert report["price_or_return_values_emitted"] is False
        assert report["session_count"] == len(dates)
        partial_csv = base / "partial.csv"
        partial_panel = base / "partial.npz"
        write_source_csv(partial_csv, dates[:-1])
        try:
            builder.build(partial_csv, partial_panel, base / "partial_report.json")
        except ValueError as exc:
            assert "complete frozen interval" in str(exc)
        else:
            raise AssertionError("builder accepted a partial synthetic panel")

        # Missing approval refuses without claiming the one-shot marker.
        no_approval = base / "no_approval"
        manifest, _ = make_fixture(no_approval, approval=False)
        expect_refusal(lambda: runner.run_once(no_approval, "manifest.json"), "approval file is missing")
        assert not (no_approval / "fixture" / "attempted.txt").exists()

        # Approved hash mismatch consumes the attempt before the panel hash read.
        bad_hash = base / "bad_hash"
        make_fixture(bad_hash, panel_hash_override="0" * 64, approval=True)
        expect_refusal(lambda: runner.run_once(bad_hash, "manifest.json"), "panel SHA-256 mismatch")
        assert (bad_hash / "fixture" / "attempted.txt").is_file()

        # Successful fixture. Instrument the loader to prove marker-before-load.
        success = base / "success"
        make_fixture(success)
        original_load = runner.load_panel

        def marker_checked_load(path: Path):
            assert (success / "fixture" / "attempted.txt").is_file()
            return original_load(path)

        runner.load_panel = marker_checked_load
        summary = runner.run_once(success, "manifest.json")
        runner.load_panel = original_load
        assert summary["dsr_trial_count"] == 50
        assert "dsr_primary_observed_12_stream_v" in summary
        assert "dsr_null_1_over_t_minus_1" in summary
        assert "primary_dsr_above_0_95" in summary["checks"]
        assert summary["period"]["end"] == runner.END
        assert (success / "fixture" / "result.json").is_file()
        expect_refusal(lambda: runner.run_once(success, "manifest.json"), "marker or result output already exists")

        return {
            "status": "PASS",
            "builder_schema": "development NPZ keys, shapes, and dtypes matched",
            "gate_cases": ["missing approval refused before marker", "panel hash mismatch refused after marker",
                           "approved synthetic run reported both DSRs", "marker existed before panel load",
                           "second attempt refused"],
            "real_data_accessed": False,
            "strategy_outcome_claim": False,
        }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
