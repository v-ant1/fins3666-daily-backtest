"""Synthetic-only tests for prereg audit, run guard and generic IC engine."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from r4_harness.phase3 import prereg_digest
from r4_harness.prereg_diff import extract_prereg_numbers, prereg_diff
from r4_harness.runner_guard import guarded_runner
from r4_harness.ic_engine import (
    circular_block_bootstrap_test,
    cross_sectional_ic,
    permutation_placebo,
    shift_placebo,
)


class PreregDiffTests(unittest.TestCase):
    def test_extract_and_match_numeric_design(self):
        text = """# Toy protocol
Primary horizon is 5 sessions and Newey-West Bartlett lag 4.
Run 500 placebo draws with seed 20261110.
Use circular block length 10 sessions.
Select the top 5 names; turnover cap is 0.50 NAV.
Charge 0.05% per side; at least 30 distinct event-response dates and at least 3 recipients.
Use the 95th percentile for placebo comparison, p-value < 0.05, and 1 variant.
## Registered endpoints
1. Primary IC at t >= 2.
2. Placebo comparison.
"""
        facts = extract_prereg_numbers(text)
        self.assertEqual(facts["horizon"], (5.0,))
        self.assertEqual(facts["nw_lag"], (4.0,))
        self.assertEqual(facts["seed"], (20261110.0,))
        self.assertEqual(facts["draws"], (500.0,))
        self.assertEqual(facts["block_length"], (10.0,))
        self.assertEqual(facts["endpoint_ids"], (1.0, 2.0))
        self.assertEqual(facts["percentile"], (95.0,))
        self.assertEqual(facts["alpha"], (.05,))
        self.assertEqual(facts["variant_count"], (1.0,))
        self.assertEqual(facts["endpoint_count"], (2.0,))
        declared = {
            "horizon": 5, "newey_west_lag": 4, "rng_seed": 20261110,
            "n_draws": 500, "block_length": 10, "top_n": 5,
            "turnover_cap": .5, "cost_per_side": .0005,
            "min_event_dates": 30, "min_recipients": 3,
            "min_t": 2,
            "percentile": 95, "alpha": .05,
            "variant_count": 1, "endpoint_count": 2,
            "endpoint_ids": [1, 2],
        }
        diff = prereg_diff(text, declared)
        self.assertTrue(diff.matches, diff.differences)
        altered = dict(declared, rng_seed=9)
        self.assertFalse(prereg_diff(text, altered).matches)
        with self.assertRaises(ValueError):
            prereg_diff(text, altered).require_match()


class RunnerGuardTests(unittest.TestCase):
    def _frozen(self, path: Path):
        base = "# Synthetic test\nFROZEN: 2026-11-10\nNumeric window 5 days.\n"
        path.write_text(base + f"SHA256: {prereg_digest(base)}\n", encoding="utf-8")

    def test_execute_freeze_hash_lock_and_mechanism_artifact_gates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prereg = root / "toy.md"
            out = root / "run"
            self._frozen(prereg)
            called = []

            @guarded_runner(prereg_path=prereg, run_dir=out)
            def run(value):
                called.append(value)
                return value * 2

            with self.assertRaises(PermissionError):
                run(3)
            self.assertEqual(called, [])
            self.assertEqual(run(3, execute=True), 6)
            self.assertTrue((out / ".runner.lock").is_file())
            with self.assertRaises(FileExistsError):
                run(4, execute=True)
            self.assertEqual(called, [3])

            other = root / "other"
            other.mkdir()
            (other / "MECHANISM_PASS.json").write_text("{}", encoding="utf-8")

            @guarded_runner(prereg_path=prereg, run_dir=other)
            def artifact_blocked():
                raise AssertionError("must not run")

            with self.assertRaises(FileExistsError):
                artifact_blocked(execute=True)
            prereg.write_text(prereg.read_text(encoding="utf-8").replace("window", "period"), encoding="utf-8")
            third = root / "third"

            @guarded_runner(prereg_path=prereg, run_dir=third)
            def tampered():
                raise AssertionError("must not run")

            with self.assertRaises(ValueError):
                tampered(execute=True)


class GenericICTests(unittest.TestCase):
    def _synthetic(self):
        rng = np.random.default_rng(5)
        n, t = 18, 240
        scores = rng.normal(size=(n, t))
        returns = scores + rng.normal(scale=.45, size=(n, t))
        mask = np.ones((n, t), bool)
        mask[:3, 20::4] = False
        mask[4:8, 1::7] = False
        return scores, returns, mask

    def test_ic_uses_date_specific_universe_and_detects_planted_effect(self):
        scores, returns, mask = self._synthetic()
        result = cross_sectional_ic(scores, returns, mask, nw_lag=4,
                                    bootstrap=True, block_length=10,
                                    n_draws=300, seed=17)
        self.assertEqual(result.n_assets_by_date[20], 15)
        self.assertGreater(result.mean_ic, .7)
        self.assertGreater(result.nw_t, 2)
        self.assertLess(result.bootstrap_p, .05)
        self.assertEqual(len(result.ic_by_date), scores.shape[1])

    def test_null_permutation_and_shift_hooks_are_deterministic(self):
        rng = np.random.default_rng(88)
        scores = rng.normal(size=(16, 220))
        returns = rng.normal(size=(16, 220))
        mask = np.ones_like(scores, dtype=bool)
        mask[0:2, ::5] = False
        placebo_a = permutation_placebo(scores, returns, mask, n_draws=60, seed=4)
        placebo_b = permutation_placebo(scores, returns, mask, n_draws=60, seed=4)
        np.testing.assert_array_equal(placebo_a.placebo_means, placebo_b.placebo_means)
        shifted = shift_placebo(scores, returns, 20, mask)
        self.assertTrue(np.isnan(shifted.ic_by_date[:20]).all())
        self.assertTrue(np.isfinite(shifted.mean_ic))
        p, boot = circular_block_bootstrap_test(shifted.ic_by_date,
                                                block_length=10, n_draws=80,
                                                seed=2, alternative="two-sided")
        self.assertTrue(0 <= p <= 1)
        self.assertEqual(len(boot), 80)
        null = cross_sectional_ic(scores, returns, mask, nw_lag=4)
        self.assertLess(abs(null.nw_t), 2.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)

