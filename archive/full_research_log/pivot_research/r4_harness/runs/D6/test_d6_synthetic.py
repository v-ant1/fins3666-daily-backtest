"""Synthetic-only D6 tests; this file never reads any project data files."""
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from r4_harness.runs.D6.d6_core import (ASSETS, build_portfolio_scores,
    newey_west_ols, trend_panel, circular_placebo, portfolio_weights)
from r4_harness.runs.D6.d6_governance import require_d6_mechanism_pass
from r4_harness.runs.D6.run_portfolio import _simulate
from r4_harness.phase3 import prereg_digest


class D6SyntheticTests(unittest.TestCase):
    def test_trend_formula_is_lagged(self):
        close = np.arange(1., 16.)[None, :]
        actual = trend_panel(close, 12)[0, 12]
        self.assertAlmostEqual(actual, 12.0 / 1.0 - 1.0)

    def test_portfolio_score_warmup_and_dimensions_are_synthetic(self):
        months = 20
        rng = np.random.default_rng(53)
        close = np.exp(np.cumsum(rng.normal(.002, .03, size=(5, months)), axis=1))
        scores = build_portfolio_scores([f'2020-{i:02d}' for i in range(1, 13)] +
                                        [f'2021-{i:02d}' for i in range(1, 9)], close)
        self.assertEqual(scores.shape, (5, months))
        self.assertTrue(np.isnan(scores[:, 12]).all())
        self.assertTrue(np.isfinite(scores[:, 13]).all())

    def test_planted_cross_prediction_is_detected(self):
        rng = np.random.default_rng(144)
        n = 260
        bond = rng.normal(size=n)
        own = rng.normal(size=n)
        target = .55 * bond + .15 * own + rng.normal(scale=.35, size=n)
        fit = newey_west_ols(target, np.column_stack([bond, own]), lag=11)
        self.assertGreater(fit['beta'][1], 0)
        self.assertGreater(fit['t'][1], 2)
        placebo = circular_placebo(bond, own, target, draws=150, seed=22)
        self.assertGreater(fit['beta'][1], np.quantile(placebo, .95))

    def test_null_is_not_promoted(self):
        rng = np.random.default_rng(773)
        n = 260
        bond, own, target = rng.normal(size=(3, n))
        fit = newey_west_ols(target, np.column_stack([bond, own]), lag=11)
        self.assertLess(abs(fit['t'][1]), 2.5)
        self.assertGreater(fit['p_positive'][1], .05)

    def test_portfolio_ties_follow_ticker_order_and_costs_are_positive(self):
        scores = np.ones((5, 3))
        w = portfolio_weights(scores)
        self.assertEqual(ASSETS[int(np.argmax(w[:, 0]))], 'IEF')
        opens = np.tile(np.linspace(100, 104, 14), (5, 1))
        varying = np.zeros((5, 14))
        varying[0] = np.arange(14)
        varying[1] = np.arange(14)[::-1]
        varying[2] = 1
        varying[3] = 2
        varying[4] = 3
        sim = _simulate(varying, opens, [1, 2, 3])
        self.assertEqual(len(sim['strategy_net']), 3)
        self.assertGreaterEqual(float(sim['costs'].sum()), 0)
        self.assertTrue(np.isfinite(sim['strategy_net']).all())

    def test_portfolio_gate_refuses_missing_mechanism_proof(self):
        with tempfile.TemporaryDirectory() as td:
            prereg = Path(td) / 'D6.md'
            body = '# Synthetic frozen fixture\nFROZEN: 2026-01-01\n'
            prereg.write_text(body + f'SHA256: {prereg_digest(body)}\n', encoding='utf-8')
            proof = Path(td) / 'MECHANISM_PASS.json'
            with self.assertRaises(PermissionError):
                require_d6_mechanism_pass(prereg_path=prereg, pass_path=proof)

    def test_hash_helper_is_deterministic_on_synthetic_text(self):
        text = '# Frozen fixture\nFROZEN: 2026-01-01\nbody\n'
        self.assertEqual(prereg_digest(text), prereg_digest(text))


if __name__ == '__main__':
    unittest.main(verbosity=2)
