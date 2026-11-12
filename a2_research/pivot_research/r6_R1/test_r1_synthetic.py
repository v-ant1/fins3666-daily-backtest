"""Synthetic-only regression tests; no staged outcome panel is opened here."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r4_harness.runner_guard import validate_frozen_prereg
from r6_R1 import build_inputs
from r6_R1.run_r1 import (
    CoverageFailure, check_coverage, mechanism, shuffle_placebo, target_weights,
    run_r1, prereg_diff_payload, portfolio, _holm, _h12_allowed, stale_mark_return,
    NW_LAG, SHUFFLE_DRAWS, BOOTSTRAP_DRAWS, SEED,
)
import r6_R1.run_r1 as runner
from unittest.mock import patch


class SignalTests(unittest.TestCase):
    def test_recurrence_projection_uses_preformation_events_and_month_end_clamp(self):
        # Jan 31 + 6 months clamps to Jul 31, which is in the forecast month.
        events = pd.Series([pd.Timestamp("2021-01-31"), pd.Timestamp("2021-07-31")])
        self.assertEqual(build_inputs.recurrence_signal(events, pd.Timestamp("2021-06-30")), 1)
        # Event on formation date is excluded by strict prior-information rule.
        self.assertEqual(build_inputs.recurrence_signal(pd.Series([pd.Timestamp("2021-06-30")]),
                                                        pd.Timestamp("2021-06-30")), 0)

    def test_coverage_gate_is_input_only_and_fails_closed(self):
        frame = pd.DataFrame({"universe": ["sp500"] * 64,
                              "formation_date": pd.date_range("2021-06-30", periods=64, freq="ME").strftime("%Y-%m-%d"),
                              "valid_flag_sic_next_month_bars": [260] * 64})
        self.assertTrue(check_coverage(frame)["passed"])
        frame.loc[5, "valid_flag_sic_next_month_bars"] = 249
        with self.assertRaises(CoverageFailure):
            check_coverage(frame)

    def test_sector_spread_positive_and_newey_west_lag_is_frozen(self):
        payer = np.asarray([[1] * 5, [1] * 5, [0] * 5, [0] * 5])
        sic = np.asarray([["01"] * 5, ["01"] * 5, ["01"] * 5, ["01"] * 5])
        ret = np.asarray([[.02] * 5, [.01] * 5, [0.] * 5, [-.01] * 5])
        mask = np.ones_like(payer, dtype=bool)
        result = mechanism(payer, sic, ret, mask)
        self.assertAlmostEqual(result["mean"], .02)
        self.assertEqual(NW_LAG, 3)
        self.assertTrue(result["pass"])

    def test_placebo_preserves_sector_payer_counts_and_is_deterministic(self):
        payer = np.asarray([[1] * 3, [1] * 3, [0] * 3, [0] * 3, [1] * 3, [0] * 3])
        sic = np.asarray([["01"] * 3, ["01"] * 3, ["01"] * 3, ["01"] * 3,
                          ["02"] * 3, ["02"] * 3])
        ret = np.asarray([[.03] * 3, [.02] * 3, [0.] * 3, [-.01] * 3, [.01] * 3, [0.] * 3])
        mask = np.ones_like(payer, dtype=bool)
        first = shuffle_placebo(payer, sic, ret, mask)
        second = shuffle_placebo(payer, sic, ret, mask)
        self.assertEqual(len(first["draws"]), 500)
        np.testing.assert_array_equal(first["draws"], second["draws"])
        self.assertEqual(first["p"], second["p"])
        self.assertEqual(SEED, 20261111)
        self.assertEqual(SHUFFLE_DRAWS, 500)
        self.assertEqual(BOOTSTRAP_DRAWS, 5000)

    def test_dow_target_holds_few_payers_and_cash_when_none(self):
        names = np.asarray(["A", "B", "C", "D", "E", "F"])
        mem = np.ones((6, 1), dtype=bool); status = mem.copy()
        payer = np.asarray([[1], [0], [1], [0], [0], [0]])
        count = np.asarray([[2], [0], [1], [0], [0], [0]])
        w, active, n, k, chosen, avail = target_weights(
            names, mem, status, payer, count, np.ones(6), np.ones(6, dtype=bool), 0)
        self.assertEqual(n, 6)
        self.assertEqual(k, 3)
        self.assertEqual(chosen, 2)
        self.assertEqual(np.flatnonzero(w).tolist(), [0, 2])
        self.assertAlmostEqual(w.sum(), 1.0)
        self.assertGreaterEqual(active, .5)
        payer[:] = 0
        w, _, _, _, chosen, _ = target_weights(
            names, mem, status, payer, count, np.ones(6), np.ones(6, dtype=bool), 0)
        self.assertEqual(w.sum(), 0.0)
        self.assertEqual(chosen, 0)

    def test_payer_k_uses_benchmark_open_availability_not_candidate_count_or_close(self):
        names = np.asarray([f"T{i}" for i in range(10)])
        formation_member = np.ones((10, 1), dtype=bool)
        status = np.ones((10, 1), dtype=bool)
        payer = np.zeros((10, 1), dtype=np.int8); payer[:3] = 1
        counts = payer.copy()
        # Benchmark has ten opening-price names while only three are valid payers.
        # This API has no close argument, so a same-session close cannot leak into selection.
        w, active, n, k, selected, available = target_weights(
            names, formation_member, status, payer, counts, np.ones(10), np.ones(10, dtype=bool), 0)
        self.assertEqual(n, 10)
        self.assertEqual(k, 5)
        self.assertEqual(selected, 3)  # all eligible payers because fewer than k
        self.assertEqual(int((w > 0).sum()), 3)
        self.assertAlmostEqual(active, .7)
        # If the available-name EW30 cohort shrinks, k changes with that cohort only.
        daily = np.asarray([True] * 8 + [False] * 2)
        w2, _, n2, k2, selected2, _ = target_weights(
            names, formation_member, status, payer, counts, np.ones(10), daily, 0)
        self.assertEqual(n2, 8); self.assertEqual(k2, 4); self.assertEqual(selected2, 3)

    def test_synthetic_monthly_portfolio_enforces_turnover_cap(self):
        dates = pd.bdate_range("2021-06-30", "2021-09-30").strftime("%Y-%m-%d").to_numpy()
        forms = np.asarray(["2021-06-30", "2021-07-30", "2021-08-31"])
        runner.FORMATION_DATES = forms
        n, t = 30, len(dates)
        rng = np.random.default_rng(3)
        daily = rng.normal(.0002, .008, (n, t))
        close = 100 * np.cumprod(1 + daily, axis=1)
        op = close / (1 + daily)
        member = np.ones((n, len(forms)), dtype=bool)
        status = member.copy()
        payer = np.zeros_like(member, dtype=np.int8); payer[:10] = 1
        count = payer * 2
        with patch("r6_R1.run_r1.circular_block_bootstrap_pvalue", return_value=(.2, np.zeros(5000))) as boot:
            out = portfolio(dates, np.asarray([f"T{i:02d}" for i in range(n)]), member, status,
                            payer, count, op, close)
        boot.assert_called_once()
        self.assertEqual(boot.call_args.kwargs, {"block_length": 10, "n_draws": 5000, "seed": 20261111})
        self.assertGreater(len(out["turnover"]), 0)
        self.assertLessEqual(float(np.max(out["turnover"])), .50 + 1e-9)
        self.assertTrue(np.all(np.isfinite(out["strategy_daily_net"])))

    def test_stale_close_mark_is_flat_then_catches_up(self):
        last = 100.0
        self.assertEqual(stale_mark_return(last, np.nan), 0.0)
        self.assertAlmostEqual(stale_mark_return(last, 110.0), .10)

    def test_missing_through_rebalance_carries_until_next_valid_open_then_fallbacks(self):
        dates = pd.bdate_range("2021-06-30", "2021-09-30").strftime("%Y-%m-%d").to_numpy()
        runner.FORMATION_DATES = np.asarray(["2021-06-30", "2021-07-30", "2021-08-31"])
        n, t = 30, len(dates)
        close = np.full((n, t), 100.0); op = close.copy()
        ix = {x: i for i, x in enumerate(dates)}
        # One gap resumes at a valid close and must catch up from its last mark.
        close[0, ix["2021-07-07"]] = np.nan
        close[0, ix["2021-07-08"]] = 110.0; op[0, ix["2021-07-08"]] = 110.0
        # A second held name is unavailable at Aug and Sep rebalances and never resumes.
        op[1, ix["2021-08-02"]:] = np.nan; close[1, ix["2021-08-02"]:] = np.nan
        # This name becomes tradable again at the September rebalance; because it is
        # no longer a payer, it must be sold there after being carried through August.
        op[1, ix["2021-09-01"]:] = 100.0; close[1, ix["2021-09-01"]:] = 100.0
        # Another held name stays missing through terminal close and uses last-close fallback.
        op[2, ix["2021-08-02"]:] = np.nan; close[2, ix["2021-08-02"]:] = np.nan
        # Name 0 is unavailable at August rebalance, then returns at the next valid open in September.
        op[0, ix["2021-08-02"]] = np.nan; close[0, ix["2021-08-02"]] = np.nan
        op[0, ix["2021-09-01"]:] = 110.0; close[0, ix["2021-09-01"]:] = 110.0
        member = np.ones((n, 3), dtype=bool); status = member.copy()
        payer = np.zeros((n, 3), dtype=np.int8); payer[:10, :2] = 1; payer[10:20, 2] = 1
        count = payer.copy(); daily = np.ones((n, t), dtype=bool)
        with patch("r6_R1.run_r1.circular_block_bootstrap_pvalue", return_value=(.5, np.zeros(5000))):
            result = portfolio(dates, np.asarray([f"T{i:02d}" for i in range(n)]), member, status,
                               payer, count, op, close, daily)
        catchup_ix = list(dates).index("2021-07-08") - ix["2021-07-01"]
        self.assertGreater(result["strategy_daily_gross"][catchup_ix], .0049)
        self.assertGreater(result["turnover"][-1], 0.0)  # September rebalance trades again after the August carry
        self.assertGreaterEqual(result["terminal_stale_fallback_names"], 1)
        self.assertGreaterEqual(result["benchmark_terminal_stale_fallback_names"], 1)
        self.assertLessEqual(result["max_turnover"], .50 + 1e-9)

    def test_h12_is_blocked_when_either_mechanism_gate_fails_and_holm_slot_is_kept(self):
        self.assertTrue(_h12_allowed(True, True))
        self.assertFalse(_h12_allowed(False, True))
        self.assertFalse(_h12_allowed(True, False))
        adjusted = _holm({"R6-H10": .01, "R6-H11": .02, "R6-H12": None})
        row = runner._endpoint_rows({"R6-H10": .01, "R6-H11": .02, "R6-H12": None},
                                    {"R6-H10": True, "R6-H11": False, "R6-H12": None},
                                    adjusted, {"R6-H10": "pass", "R6-H11": "fail",
                                               "R6-H12": "not run; H10/H11 did not both pass"})
        self.assertEqual(len(row), 3)
        h12 = next(x for x in row if x["endpoint"] == "R6-H12")
        self.assertEqual(h12["status"], "not run; H10/H11 did not both pass")
        self.assertEqual(h12["raw_p"], "")
        self.assertEqual(h12["holm_p"], 1.0)


class FrozenGuardTests(unittest.TestCase):
    def test_freeze_hash_and_no_execute_refusal_happen_before_input_load(self):
        date, digest = validate_frozen_prereg(ROOT / "specs/r6_prereg/R1.md")
        self.assertEqual(date, "2026-11-11")
        self.assertEqual(digest, "3df293c87ff8eaf446a90d089bfe7672606bf7df7b26701b86b8f98c9c5955b0")
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(PermissionError):
                run_r1(Path(td) / "does-not-exist.npz", Path(td) / "missing.csv",
                       Path(td) / "missing.json", Path(td) / "run")
            self.assertFalse((Path(td) / "run/.runner.lock").exists())

    def test_numeric_prereg_diff_is_clean(self):
        diff = prereg_diff_payload()
        self.assertTrue(diff.matches, diff.differences)
        self.assertEqual(diff.differences, ())

    def test_full_holm_family_appends_prior_j1_values_and_three_r1_slots(self):
        adjusted = _holm({"R6-H10": None, "R6-H11": None, "R6-H12": None})
        self.assertEqual(set(adjusted), {f"R6-H{i}" for i in range(1, 13)})
        self.assertAlmostEqual(adjusted["R6-H7"]["raw_p"], .0188988621812783)
        self.assertAlmostEqual(adjusted["R6-H8"]["raw_p"], .001996007984031936)
        self.assertAlmostEqual(adjusted["R6-H9"]["raw_p"], .4491101779644071)


if __name__ == "__main__":
    unittest.main()
