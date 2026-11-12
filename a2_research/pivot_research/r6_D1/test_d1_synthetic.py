"""Synthetic-only tests for the guarded D1 runner; no project outcomes loaded."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from r4_harness.phase3 import circular_block_bootstrap_pvalue
from r4_harness.runner_guard import validate_frozen_prereg
from r6_D1.run_d1 import (
    CoverageFailure,
    BOOTSTRAP_DRAWS,
    SHUFFLE_DRAWS,
    _endpoint_rows,
    _forward_returns,
    _signals,
    _stratified_shuffle,
    _wealth_path,
    analyze_bundle,
    joint_coverage_gate,
    prereg_diff_payload,
    run_d1,
    run_coverage_first,
    coverage_manifest_gate,
    validate_bundle,
)


def synthetic_bundle():
    dates = np.busday_offset(np.datetime64("2020-06-01"), np.arange(1614))
    dates = dates.astype("datetime64[D]").astype(str)
    rng = np.random.default_rng(17)

    def universe(n, prefix):
        ratio = rng.uniform(.2, .8, (n, len(dates)))
        roster = np.ones((n, len(dates)), dtype=bool)
        daily = rng.normal(.0002, .009, (n, len(dates)))
        close = 100 * np.cumprod(1 + daily, axis=1)
        op = close / (1 + daily)
        names = np.asarray([f"{prefix}{i:03d}" for i in range(n)])
        sic = np.tile(np.asarray([f"{i:02d}" for i in range(10)]),
                      int(np.ceil(n / 10)))[:n]
        sic = np.broadcast_to(sic[:, None], (n, len(dates))).copy()
        return {
            f"{prefix}_names": names,
            f"{prefix}_roster": roster,
            f"{prefix}_ratio": ratio,
            f"{prefix}_adjusted_open": op,
            f"{prefix}_adjusted_close": close,
            f"{prefix}_sic2": sic,
        }

    data = {"dates": dates}
    data.update(universe(300, "sp500"))
    data.update(universe(30, "dow"))
    return data


class FrozenGuardTests(unittest.TestCase):
    def test_frozen_hash_and_normalized_prereg_diff_are_clean(self):
        date, digest = validate_frozen_prereg(
            Path(__file__).resolve().parents[1] / "specs" / "r6_prereg" / "D1.md")
        self.assertEqual(date, "2026-11-11")
        self.assertEqual(len(digest), 64)
        diff = prereg_diff_payload()
        self.assertTrue(diff["matches"], diff["differences"])
        self.assertEqual(diff["differences"], [])
        self.assertEqual(SHUFFLE_DRAWS, 500)
        self.assertEqual(BOOTSTRAP_DRAWS, 5000)

    def test_execution_guard_refuses_without_execute_before_loading_input(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(PermissionError):
                run_d1(Path(td) / "nonexistent.npz", run_dir=Path(td) / "run")
            self.assertFalse((Path(td) / "run" / ".runner.lock").exists())


class InputGateTests(unittest.TestCase):
    def test_synthetic_presence_only_manifest_passes(self):
        manifest = {
            "development_only": True,
            "price_values_loaded": False,
            "price_returns_computed": False,
            "forward_returns_loaded_or_computed": False,
            "ics_computed": False,
            "formation_rule": "every fifth NYSE session beginning 2020-11-27",
            "formation_price_windows": {
                "signal": "t-4 through t, bar presence only",
                "forward": "t+2 through t+6, bar presence only",
            },
            "first_formation": "2020-11-27",
            "last_formation": "2026-10-28",
            "sp500_unresolved_price_gap_count": 1,
            "sp500_unresolved_price_gap_symbols": ["GAP"],
            "overall_gate": "PASS",
            "universes": {
                "SP500": {"development_daily_sessions": 1488,
                          "formation_joint_member_day_coverage_pct": 94.8,
                          "formation_dates_pct_ge_250": 99.0,
                          "formation_dates_ge_250_eligible": 99,
                          "scheduled_formation_dates": 100},
                "DOW30": {"development_daily_sessions": 1488,
                          "formation_joint_member_day_coverage_pct": 97.0,
                          "scheduled_formation_dates": 100},
            },
        }
        manifest["universes"]["SP500"]["scheduled_formation_dates"] = 298
        manifest["universes"]["SP500"]["formation_dates_ge_250_eligible"] = 297
        manifest["universes"]["SP500"]["formation_dates_pct_ge_250"] = 297 / 298 * 100
        result = coverage_manifest_gate(manifest)
        self.assertTrue(result["passed"])
        self.assertEqual(result["sp500_price_gap_count"], 1)

    def test_synthetic_joint_coverage_passes(self):
        report = joint_coverage_gate(validate_bundle(synthetic_bundle()))
        self.assertTrue(report["passed"])
        self.assertEqual(report["universes"]["dow"]["joint_coverage"], 1.0)
        self.assertGreaterEqual(report["wide_dates_fraction"], .80)

    def test_failed_input_gate_stops_before_signals_and_returns(self):
        data = synthetic_bundle()
        # A 15% joint price gap forces the input-only member-day threshold to fail.
        data["sp500_adjusted_open"][:50, data["dates"] >= "2020-11-27"] = np.nan
        with tempfile.TemporaryDirectory() as td, \
             patch("r6_D1.run_d1._signals", side_effect=AssertionError("signal computed before gate")), \
             patch("r6_D1.run_d1._forward_returns", side_effect=AssertionError("return computed before gate")):
            result = analyze_bundle(data, output_dir=Path(td))
            self.assertEqual(result["status"], "stopped at input-only coverage gate")
            self.assertEqual([r["endpoint_id"] for r in result["endpoint_rows"]],
                             ["R6-H1", "R6-H2", "R6-H3"])
            self.assertTrue((Path(td) / "D1_ENDPOINTS.csv").is_file())
            self.assertIsNone(result["endpoint_rows"][0]["raw_p"])

    def test_manifest_failure_stops_before_bundle_loader(self):
        manifest = {
            "development_only": True,
            "price_values_loaded": False,
            "price_returns_computed": False,
            "forward_returns_loaded_or_computed": False,
            "ics_computed": False,
            "formation_rule": "every fifth NYSE session beginning 2020-11-27",
            "formation_price_windows": {
                "signal": "t-4 through t, bar presence only",
                "forward": "t+2 through t+6, bar presence only",
            },
            "sp500_unresolved_price_gap_count": 51,
            "universes": {
                "SP500": {"formation_joint_member_day_coverage_pct": 89.9,
                          "formation_dates_pct_ge_250": 99.0,
                          "formation_dates_ge_250_eligible": 99,
                          "scheduled_formation_dates": 100},
                "DOW30": {"formation_joint_member_day_coverage_pct": 97.0,
                          "scheduled_formation_dates": 100},
            },
            "overall_gate": "FAIL",
        }
        loader_called = []
        result = run_coverage_first(manifest,
                                    lambda: loader_called.append(True),
                                    output_dir=None)
        self.assertEqual(result["status"], "stopped at input-only coverage gate")
        self.assertFalse(loader_called)
        self.assertEqual([r["endpoint_id"] for r in result["endpoint_rows"]],
                         ["R6-H1", "R6-H2", "R6-H3"])


class SignalAndMechanismHelpersTests(unittest.TestCase):
    def test_five_session_signal_and_t_plus_two_to_t_plus_six_return(self):
        ratios = np.arange(1, 13, dtype=float)[None, :] / 100
        signal = _signals(ratios)
        self.assertAlmostEqual(signal[0, 4], -np.mean(ratios[0, :5]))
        op = np.arange(10, 22, dtype=float)[None, :]
        close = (np.arange(10, 22, dtype=float) * 2)[None, :]
        forward = _forward_returns({"open": op, "close": close})
        self.assertAlmostEqual(forward[0, 0], close[0, 6] / op[0, 2] - 1)

    def test_shuffle_stays_inside_sic2_and_leaves_singletons_fixed(self):
        scores = np.asarray([[1.], [2.], [3.], [10.], [20.]])
        sic = np.asarray([["01"], ["01"], ["01"], ["02"], ["03"]])
        mask = np.ones_like(scores, dtype=bool)
        shuffled = _stratified_shuffle(scores, sic, mask, np.random.default_rng(2))
        self.assertEqual(sorted(shuffled[:3, 0]), [1., 2., 3.])
        self.assertEqual(shuffled[3, 0], 10.)
        self.assertEqual(shuffled[4, 0], 20.)

    def test_portfolio_starts_at_ew_and_enforces_total_turnover_cap(self):
        rng = np.random.default_rng(4)
        n, t = 30, 16
        returns = rng.normal(.0005, .01, (n, t))
        close = 100 * np.cumprod(1 + returns, axis=1)
        op = close / (1 + returns)
        scores = np.zeros((n, t))
        scores[:5, :] = 1.0
        roster = np.ones((n, t), bool)
        result = _wealth_path(scores, op, close, roster,
                              np.asarray([f"T{i:02d}" for i in range(n)]),
                              fills=[4, 9], equal_weight=False)
        self.assertLessEqual(result["max_turnover"], .50 + 1e-8)
        self.assertAlmostEqual(result["turnovers"][0], .50, places=7)
        self.assertGreater(result["active_share"], 0)
        self.assertTrue(np.isfinite(result["cumulative_return"]))

    def test_bootstrap_is_deterministic_and_endpoint_slots_are_fixed(self):
        x = np.asarray([.01, -.01, .02, 0., .005])
        p1, draw1 = circular_block_bootstrap_pvalue(x, np.zeros_like(x),
                                                    block_length=10, n_draws=100,
                                                    seed=20261111)
        p2, draw2 = circular_block_bootstrap_pvalue(x, np.zeros_like(x),
                                                    block_length=10, n_draws=100,
                                                    seed=20261111)
        self.assertEqual(p1, p2)
        np.testing.assert_array_equal(draw1, draw2)
        rows = _endpoint_rows({"raw_p": .02}, {"raw_p": .03}, None)
        self.assertEqual([r["endpoint_id"] for r in rows],
                         ["R6-H1", "R6-H2", "R6-H3"])
        self.assertIsNone(rows[2]["raw_p"])


if __name__ == "__main__":
    unittest.main()
