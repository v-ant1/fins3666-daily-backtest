"""Synthetic-only tests for the one-shot coordinator holdout adapter."""
import json
import csv
import tempfile
import unittest
import hashlib
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from r4_harness.holdout.frozen_utils import load_holm_family, require_mechanism_pass, trial_budget
from r4_harness.holdout.portfolio_core import portfolio_report
from r4_harness.holdout.run_holdout import (
    acquire_one_run_lock, analyze_arrays, load_holdout_prices,
    validate_network_path, validate_price_path,
)
from r4_harness.phase3 import prereg_digest


class SyntheticHoldoutTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(49021)
        self.n, self.t = 8, 80
        start = date(2010, 1, 4)
        days = []
        d = start
        while len(days) < self.t:
            if d.weekday() < 5:
                days.append(d.isoformat())
            d += timedelta(days=1)
        self.dates = days
        self.assets = [f'S{i:02d}' for i in range(self.n)]
        ret = rng.normal(.0003, .01, (self.n, self.t))
        close = 100 * np.cumprod(1 + ret, axis=1)
        op = close / (1 + rng.normal(0, .002, (self.n, self.t)))
        spread = rng.uniform(.3, 2.0, (self.n, self.t))
        high = np.maximum(op, close) + spread / 2
        low = np.minimum(op, close) - spread / 2
        self.op, self.close, self.high, self.low = op, close, high, low
        self.roster = np.ones((self.n, self.t), bool)
        self.adj = np.zeros((self.t, self.n, self.n))
        for k in range(self.t):
            self.adj[k] = np.ones((self.n, self.n)) - np.eye(self.n)
        self.dwdp = np.zeros(self.t, bool)
        self.dwdp[30:34] = True

    def test_synthetic_D4_D5_runs_both_DWDP_scenarios(self):
        for approach in ('D4', 'D5'):
            result = analyze_arrays(approach, self.assets, self.dates,
                                    self.adj, self.roster, self.op, self.high,
                                    self.low, self.close, self.dwdp,
                                    trial_count=30, bootstrap_draws=25)
            self.assertEqual(result['approach'], approach)
            self.assertEqual(result['dwdp_included']['dwdp_window_dates'], 4)
            self.assertEqual(result['dwdp_excluded']['dwdp_window_dates_removed'], 0)
            self.assertIn('primary_mechanism', result['dwdp_included'])
            self.assertIn('portfolio', result['dwdp_included'])

    def test_actual_trade_cost_and_turnover_cap(self):
        scores = np.tile(np.arange(self.n, dtype=float)[:, None], (1, self.t))
        fill = np.arange(10, self.t - 1, 5)
        report = portfolio_report(scores, self.op, self.close, self.roster,
                                   fill, trial_count=30, bootstrap_draws=25,
                                   turnover_cap=.50)
        self.assertLessEqual(report['strategy_net']['turnover'], .50000001)
        self.assertGreater(report['realized_strategy_cost'], 0)
        self.assertGreater(report['realized_benchmark_cost'], 0)
        relative = portfolio_report(scores, self.op, self.close, self.roster,
                                    fill, trial_count=30, bootstrap_draws=25,
                                    turnover_cap=.50,
                                    turnover_cap_basis='benchmark_relative')
        self.assertLessEqual(relative['benchmark_relative_turnover'], .50000001)

    def test_holdout_path_rejects_development_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(validate_price_path(root / 'holdout_prices').name,
                             'holdout_prices')
            with self.assertRaises(PermissionError):
                validate_price_path(root / 'holdout' / 'repo' / 'prices-daily')
            with self.assertRaises(PermissionError):
                validate_price_path(root / 'repo' / 'prices-daily')
            self.assertEqual(validate_network_path(root / 'holdout' / 'network.npz').name,
                             'network.npz')
            with self.assertRaises(PermissionError):
                validate_network_path(root / 'w1_engine' / 'network.npz')

    def test_atomic_one_run_lock_refuses_second_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / 'once.lock'
            acquire_one_run_lock(lock, {'synthetic': True})
            with self.assertRaises(PermissionError):
                acquire_one_run_lock(lock, {'synthetic': True})

    def test_frozen_hash_and_mechanism_pass_linkage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = '# Synthetic prereg\nFROZEN: 2026-11-10\n'
            digest = prereg_digest(body)
            prereg = root / 'D4.md'
            prereg.write_text(body + f'SHA256: {digest}\n', encoding='utf-8')
            pass_file = root / 'MECHANISM_PASS.json'
            pass_file.write_text(json.dumps({'approach': 'D4', 'passed': True,
                                             'prereg_sha256': digest,
                                             'mean_ic': .02, 'nw_t_lag4': 2.1}), encoding='utf-8')
            self.assertTrue(require_mechanism_pass('D4', prereg, pass_file)['passed'])
            proof = json.loads(pass_file.read_text(encoding='utf-8'))
            proof['prereg_sha256'] = '0' * 64
            pass_file.write_text(json.dumps(proof), encoding='utf-8')
            with self.assertRaises(PermissionError):
                require_mechanism_pass('D4', prereg, pass_file)
            pass_file.write_text(json.dumps({'approach': 'D4', 'passed': True,
                                             'prereg_sha256': digest,
                                             'mean_ic': .02, 'nw_t_lag4': 2.1}), encoding='utf-8')
            (root / 'MECHANISM_FAIL.json').write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(PermissionError, 'mechanism gate failed'):
                require_mechanism_pass('D4', prereg, pass_file)

    def test_trial_count_is_read_from_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / 'trials.md'
            log.write_text('# Trial log (budget: 30 variants)\n', encoding='utf-8')
            self.assertEqual(trial_budget(log), 30)

    def test_holm_family_is_complete_and_includes_both_directions(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'holm.json'
            manifest = ['D4.primary_ic', 'D4_v1_portfolio_net_excess',
                        'D5.primary_ic', 'D5_v1_portfolio_net_excess']
            digest = hashlib.sha256(('\n'.join(manifest) + '\n').encode()).hexdigest()
            p.write_text(json.dumps({'manifest': manifest, 'manifest_sha256': digest,
                                     'p_values': {'D4.primary_ic': .03,
                                                  'D5.primary_ic': .04,
                                                  'D5_v1_portfolio_net_excess': .02}}),
                         encoding='utf-8')
            family = load_holm_family(p, 'D4_v1_portfolio_net_excess')
            self.assertEqual(set(family), {'D4.primary_ic', 'D5.primary_ic',
                                           'D5_v1_portfolio_net_excess'})

    def test_synthetic_price_loader_filters_before_numeric_parsing_and_maps_UTX(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'holdout_prices'
            folder.mkdir()
            with (folder / 'AAA.csv').open('w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['date', 'open', 'high', 'low', 'close', 'adjclose'])
                w.writerow(['2009-12-31', 'not-a-number', '', '', '', ''])
                w.writerow(['2010-01-04', '10', '11', '9', '10', '5'])
                w.writerow(['2020-11-02', 'also-bad', '', '', '', ''])
            with (folder / 'RTX.csv').open('w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['date', 'open', 'high', 'low', 'close', 'adjclose'])
                w.writerow(['2010-01-04', '20', '22', '19', '20', '10'])
            op, hi, lo, close, coverage = load_holdout_prices(
                folder, ['AAA', 'UTX', 'KFT', 'DWDP', 'WBA'], ['2010-01-04'])
            self.assertAlmostEqual(op[0, 0], 5.0)
            self.assertAlmostEqual(close[1, 0], 10.0)
            self.assertEqual(coverage['UTX']['source'], 'RTX')
            self.assertEqual(coverage['KFT']['rows'], 0)
            self.assertTrue(np.isfinite(hi[0, 0]))


if __name__ == '__main__':
    unittest.main(verbosity=2)
