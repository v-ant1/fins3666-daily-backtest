"""Synthetic-only checks for the J1 coordinator holdout runner."""
from __future__ import annotations

import unittest
from datetime import date, timedelta

import numpy as np

from r4_harness.holdout.run_holdout_j1 import (
    analyze_arrays, build_j1_scores, validate_holdout_path,
)


class J1SyntheticTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(20261111)
        self.n, self.t = 8, 100
        d = date(2017, 8, 1)
        dates = []
        while len(dates) < self.t:
            if d.weekday() < 5:
                dates.append(d.isoformat())
            d += timedelta(days=1)
        self.dates = dates
        self.assets = ["A", "B", "C", "D", "E", "F", "G", "DWDP"]
        ret = rng.normal(0.0002, 0.006, (self.n, self.t))
        self.close = 100 * np.cumprod(1 + ret, axis=1)
        self.open = self.close / (1 + rng.normal(0, 0.001, (self.n, self.t)))
        self.roster = np.ones((self.n, self.t), bool)
        self.sic2 = np.full((self.n, self.t), "35", dtype="U2")

    def test_frozen_signal_shape_and_peer_exclusion(self):
        signal, scheduled = build_j1_scores(self.close, self.roster, self.sic2, self.dates)
        self.assertTrue(np.isnan(signal[:, 0:5]).all())
        self.assertEqual(scheduled[0], 0)
        self.assertTrue(np.isfinite(signal[:, 5]).all())
        # For a shared SIC2 group, peer-relative scores sum to zero (up to FP).
        self.assertAlmostEqual(float(np.nansum(signal[:, 5])), 0.0, places=12)

    def test_both_dwdp_scenarios_and_exact_criterion_fields(self):
        result = analyze_arrays(self.assets, self.dates, self.open, self.close,
                                self.roster, self.sic2,
                                development_net_excess_sign=1,
                                trial_count=3, bootstrap_draws=25)
        self.assertEqual(result["approach"], "J1")
        self.assertGreater(result["dwdp_included"]["dwdp_window_sessions"], 0)
        for key in ("dwdp_included", "dwdp_excluded"):
            scenario = result[key]
            self.assertIn("criterion_5_pass", scenario)
            self.assertIn("same_sign_pass", scenario)
            self.assertIn("net_sharpe_above_EW30_pass", scenario)
            self.assertIn("one_sided_block_bootstrap_p_lt_0_10_pass", scenario)
            self.assertLessEqual(scenario["portfolio"]["strategy_net"]["turnover"], .50000001)
            self.assertEqual(scenario["portfolio"]["trial_count"], 3)

    def test_development_folder_refused(self):
        with self.assertRaises(PermissionError):
            validate_holdout_path("C:/work/repo/sealed_holdout_dow/prices")

    def test_holdout_path_requires_sealed_root(self):
        with self.assertRaises(PermissionError):
            validate_holdout_path("C:/work/ordinary_holdout/prices", must_exist=False)


if __name__ == "__main__":
    unittest.main()
