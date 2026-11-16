"""Synthetic-only P1 runner regression tests; never loads project outcomes."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from r4_harness.prereg_diff import prereg_diff
from r4_harness.phase3 import prereg_digest
from r4_harness.runner_guard import guarded_runner
from r6_P1 import build_inputs
from r6_P1 import run_p1 as p1


class P1SyntheticTests(unittest.TestCase):
    def test_numeric_prereg_diff_is_clean_and_runtime_is_fixed(self):
        cfg = json.loads((p1.HERE / "prereg_diff_config.json").read_text(encoding="utf-8"))
        result = prereg_diff(p1.DIFF_SOURCE, cfg)
        self.assertTrue(result.matches, result.differences)
        runtime_result = p1.prereg_diff_payload()
        self.assertTrue(runtime_result.matches, runtime_result.differences)
        self.assertEqual(p1.LOOKBACK, 21)
        self.assertEqual(p1.NW_LAG, 1)
        self.assertEqual(p1.PLACEBO_DRAWS, 500)
        self.assertEqual(p1.BOOTSTRAP_DRAWS, 5000)
        self.assertEqual(p1.BOOTSTRAP_BLOCK, 10)
        self.assertEqual(p1.SEED, 20261111)
        self.assertEqual(p1.TURNOVER_CAP, 0.50)
        self.assertEqual(p1.COST_PER_SIDE, 0.0005)
        self.assertEqual(p1.IC_FLOOR, 0.0017320508)
        self.assertEqual(p1.FORMATION_COUNT, 70)

    def test_shared_formation_calendar_starts_at_december_2020(self):
        calendar = pd.bdate_range("2020-11-27", "2020-12-31")
        dates = build_inputs.make_formation_dates(calendar)
        self.assertEqual(dates, [pd.Timestamp("2020-12-31")])

    def test_refuses_execution_without_explicit_execute(self):
        with tempfile.TemporaryDirectory() as tmp:
            prereg = Path(tmp) / "synthetic.md"
            run_dir = Path(tmp) / "run"
            prereg.write_text("DRAFT only\n", encoding="utf-8")

            @guarded_runner(prereg_path=prereg, run_dir=run_dir)
            def sample():
                self.fail("guarded function must not run")

            with self.assertRaises(PermissionError):
                sample()
            self.assertFalse(run_dir.exists())

    def test_guard_refuses_unfrozen_prereg_even_if_function_is_authorized(self):
        with tempfile.TemporaryDirectory() as tmp:
            prereg = Path(tmp) / "synthetic.md"
            run_dir = Path(tmp) / "run"
            prereg.write_text("DRAFT only\n", encoding="utf-8")

            @guarded_runner(prereg_path=prereg, run_dir=run_dir)
            def sample():
                self.fail("unfrozen prereg must block before runner body")

            with self.assertRaisesRegex(ValueError, "FROZEN"):
                sample(execute=True)
            self.assertFalse((run_dir / ".runner.lock").exists())

    def test_manifest_gate_precedes_parquet_reads_and_forward_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = [root / x for x in ("manifest.json", "signals.parquet", "prices.parquet", "coverage.csv")]
            for path in files:
                path.write_text("synthetic placeholder", encoding="utf-8")
            order = []

            def verifier(*args, **kwargs):
                order.append("verified")
                return {"verified": True}

            def precheck():
                order.append("pre-label-check")

            def labels_builder(signals, prices):
                order.append("labels-built")
                return pd.DataFrame()

            def parquet_reader(path):
                order.append("read:" + Path(path).name)
                return pd.DataFrame({"x": [1]})

            with patch.object(pd, "read_parquet", side_effect=parquet_reader):
                p1.verified_forward_labels(
                    *files, verifier=verifier, label_builder=labels_builder,
                    pre_label_check=precheck,
                )
            self.assertEqual(order, ["verified", "pre-label-check", "read:signals.parquet",
                                     "read:prices.parquet", "labels-built"])

            order.clear()

            def fail_verifier(*args, **kwargs):
                order.append("rejected")
                raise p1.InputGateError("synthetic bad input hash")

            with patch.object(pd, "read_parquet") as reader:
                with self.assertRaises(p1.InputGateError):
                    p1.verified_forward_labels(*files, verifier=fail_verifier,
                                               label_builder=labels_builder)
                reader.assert_not_called()
            self.assertEqual(order, ["rejected"])

    def test_missing_trailing_signal_is_excluded_from_forward_cohort(self):
        formation = pd.Timestamp("2020-11-30")
        signals = pd.DataFrame([
            {"universe": "SP500", "formation_date": formation, "ticker": "AAA", "member": True,
             "overnight_momentum_21s": 0.02, "signal_valid": True, "sic2": "35", "sic_valid": True},
            {"universe": "SP500", "formation_date": formation, "ticker": "BBB", "member": True,
             "overnight_momentum_21s": 0.01, "signal_valid": True, "sic2": "35", "sic_valid": True},
            {"universe": "SP500", "formation_date": formation, "ticker": "CCC", "member": True,
             "overnight_momentum_21s": np.nan, "signal_valid": False, "sic2": "35", "sic_valid": True},
        ])
        dates = pd.to_datetime(["2020-12-01", "2020-12-31"])
        prices = pd.DataFrame([
            {"universe": "SP500", "date": d, "ticker": ticker, "member": True,
             "adjusted_open": 100.0, "adjusted_close": close}
            for d, close in zip(dates, [101.0, 102.0])
            for ticker in ("AAA", "BBB", "CCC")
        ])
        result = p1.build_forward_labels(signals, prices)
        self.assertEqual(set(result.ticker), {"AAA", "BBB"})
        self.assertNotIn("CCC", set(result.ticker))

    def test_open_selection_uses_same_benchmark_cohort_and_no_close(self):
        target, info = p1.select_weights(
            {"A": 0.3},
            {"A": True, "B": True, "C": True, "D": True},
            {"A": 10.0, "B": 20.0, "C": 30.0, "D": 40.0},
        )
        self.assertEqual(info["benchmark_n"], 4)
        self.assertEqual(info["k"], 2)
        self.assertEqual(info["selected"], ["A"])
        self.assertEqual(info["benchmark_names"], ["A", "B", "C", "D"])
        self.assertAlmostEqual(info["active_share"], 0.75)
        self.assertNotIn("close", p1.select_weights.__code__.co_varnames)

    def test_sic2_shuffle_saves_all_seeded_draws(self):
        rows = []
        for d in range(4):
            for i in range(8):
                rows.append({"universe": "SP500", "formation_date": pd.Timestamp("2021-01-31") + pd.offsets.MonthEnd(d),
                             "ticker": f"T{i}", "score": float(i), "forward_return": float((i + d) % 8),
                             "sic2": "35" if i < 4 else "36", "eligible": True})
        labels = pd.DataFrame(rows)
        a = p1.sic2_shuffle_placebo(labels)
        b = p1.sic2_shuffle_placebo(labels)
        self.assertEqual(a["draw_count"], 500)
        self.assertEqual(len(a["draws"]), 500)
        np.testing.assert_array_equal(a["draws"], b["draws"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "placebo.csv"
            p1.write_placebo_draws(path, a["draws"])
            saved = pd.read_csv(path)
            self.assertEqual(len(saved), 500)
            self.assertEqual(saved.draw.iloc[0], 1)
            self.assertEqual(saved.draw.iloc[-1], 500)

    def test_decision63_carries_then_catches_up_for_both_books(self):
        last, valid = p1.stale_close_marks(np.array([10.0, 20.0]), np.array([np.nan, 20.0]))
        np.testing.assert_array_equal(valid, [False, True])
        np.testing.assert_allclose(last, [10.0, 20.0])
        dates = ["2021-01-29", "2021-02-01", "2021-02-02"]
        names = ["A", "B"]
        open_px = np.array([[10.0, 10.0, 15.0], [20.0, 20.0, 20.0]])
        close_px = np.array([[10.0, np.nan, 15.0], [20.0, 20.0, 20.0]])
        roster = np.ones((2, 3), dtype=bool)
        fills = {1: {"A": 1.0}}
        for equal_weight in (False, True):
            book = p1.simulate_book(dates, names, open_px, close_px, roster, fills,
                                    equal_weight=equal_weight, cost_per_side=0.0)
            self.assertAlmostEqual(book["returns"][0], 0.0, places=12)
        # Initial move starts from EW30 and is turnover-capped at 50%, so the
        # strategy holds 75% A; EW30 catches up on half the missing-name gap.
        self.assertAlmostEqual(book["returns"][1], 0.375 if not equal_weight else 0.25, places=12)

    def test_decision63_terminal_missing_price_uses_last_close_fallback(self):
        dates = ["2021-01-29", "2021-02-01", "2021-02-02"]
        open_px = np.array([[10.0, 10.0, np.nan], [20.0, 20.0, 20.0]])
        close_px = np.array([[10.0, np.nan, np.nan], [20.0, 20.0, 20.0]])
        roster = np.ones((2, 3), dtype=bool)
        for equal_weight in (False, True):
            book = p1.simulate_book(dates, ["A", "B"], open_px, close_px, roster,
                                    {1: {"A": 1.0}}, equal_weight=equal_weight,
                                    cost_per_side=0.0005)
            self.assertGreaterEqual(book["terminal_stale_fallback_names"], 1)
            self.assertTrue(np.all(np.isfinite(book["returns"])))

    def test_holm_requires_complete_family_and_reports_raw_separately(self):
        self.assertFalse(p1.holm_reject_strict(0.05))
        self.assertTrue(p1.holm_reject_strict(0.049999))
        self.assertEqual(len(p1.validate_holm_family()["manifest"]), 15)
        with tempfile.TemporaryDirectory() as tmp:
            family = [f"R6-H{i}" for i in range(1, 16)]
            digest = hashlib.sha256(json.dumps(family).encode()).hexdigest()
            p_values = {key: (0.10 if key in family[:12] else None) for key in family}
            cfg = {"manifest": family, "manifest_sha256": digest,
                   "p_values": p_values, "endpoints": p_values.copy()}
            path = Path(tmp) / "holm.json"
            path.write_text(json.dumps(cfg), encoding="utf-8")
            adjusted = p1.holm_results({"R6-H13": 0.01, "R6-H14": 0.20, "R6-H15": None}, path)
            rows = p1.endpoint_rows(
                {"R6-H13": 0.01, "R6-H14": 0.20, "R6-H15": None},
                {"R6-H13": "pass", "R6-H14": "fail", "R6-H15": "not run"},
                adjusted, {"R6-H13": "raw gate pass", "R6-H14": "raw gate fail", "R6-H15": "not run"},
            )
            self.assertEqual(len(adjusted), 15)
            self.assertEqual(rows[0]["raw_gate_status"], "pass")
            self.assertEqual(rows[0]["holm_adjusted_p"], adjusted["R6-H13"]["holm_adjusted_p"])
            self.assertEqual(adjusted["R6-H15"]["holm_accounting_p"], 1.0)
            self.assertEqual(adjusted["R6-H15"]["status"], "not run")

    def test_results_markdown_contains_all_placebo_draws(self):
        rows = [{"endpoint": f"R6-H{i}", "raw_p": None, "raw_gate_status": "not run",
                 "holm_adjusted_p": 1.0, "holm_reject": False, "endpoint_status": "not run"}
                for i in (13, 14, 15)]
        report = p1.render_results_markdown({
            "prereg_sha256": "synthetic", "input_manifest_sha256": "synthetic",
            "mechanism": {"raw_gate_status": "fail", "mean_ic": 0.0, "nw_t": 0.0,
                          "raw_one_sided_p": 0.5, "nw_lag_months": 1,
                          "ic_floor_diagnostic": p1.IC_FLOOR,
                          "mean_ic_above_cost_floor_diagnostic": False,
                          "dates": ["2021-01-31"], "eligible_names_by_date": [4],
                          "ic_by_date": [0.0]},
            "placebo": {"raw_gate_status": "fail", "observed_mean_ic": 0.0,
                        "null_p95": 0.2, "raw_one_sided_p": 0.5,
                        "draw_count": 500, "seed": p1.SEED},
            "placebo_draws": np.zeros(500), "endpoints": rows,
            "portfolio": None,
            "holm_family": {"R6-H15": {"holm_adjusted_p": 1.0}},
        })
        self.assertEqual(report.count("| 1 | 0 |"), 1)
        self.assertIn("| 500 | 0 |", report)
        self.assertIn("H15 has no raw outcome p-value", report)


if __name__ == "__main__":
    unittest.main()
