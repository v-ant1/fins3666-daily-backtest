"""Synthetic future-truncation tests; no outcomes or mechanism tests."""
from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from r4_harness.builders import (
    build_common_owner_network,
    build_dated_industry_network,
    build_peer_pressure,
    build_trailing_clv_pressure,
    degree_preserving_shuffle,
    load_13f_cosine_edges,
    matched_same_industry_nonowners,
    reverse_direction,
    sic_provider_from_records,
)


def assert_prefix_equal(test, full, truncated, cut, time_axis=1):
    idx = [slice(None)] * np.asarray(full).ndim
    idx[time_axis] = slice(0, cut)
    np.testing.assert_allclose(
        np.asarray(full)[tuple(idx)], np.asarray(truncated),
        equal_nan=True, rtol=0, atol=0,
    )


class BuilderInvarianceTests(unittest.TestCase):
    def setUp(self):
        self.dates = [f'2024-01-{d:02d}' for d in range(1, 13)]
        self.assets = ['A', 'B', 'C', 'D', 'E', 'F']
        rng = np.random.default_rng(80)
        n, t = len(self.assets), len(self.dates)
        low = np.full((n, t), 90.0)
        high = np.full((n, t), 110.0)
        clv = rng.uniform(-1, 1, (n, t))
        self.close = 100.0 + 10.0 * clv
        self.low = low
        self.high = high
        self.volume = np.tile(np.array([100000, 50000, 25000, 12000, 6000, 3000],
                                       dtype=float)[:, None], (1, t))
        self.volume *= rng.uniform(0.9, 1.1, (n, t))
        self.records = [
            {'asset': a, 'sic': '1000' if a in 'ABC' else '2000',
             'available_date': self.dates[0]}
            for a in self.assets
        ]

    def test_real_13f_edge_file_respects_panel_availability_and_truncation(self):
        edges = load_13f_cosine_edges()
        names = ['AAPL', 'AXP', 'BA']
        dates = ['2020-08-13', '2020-08-14', '2020-08-17']
        full = build_common_owner_network(names, dates, edges)
        truncated = build_common_owner_network(names, dates[:2], edges)
        self.assertEqual(full[0].sum(), 0.0)
        self.assertGreater(full[1].sum(), 0.0)
        assert_prefix_equal(self, full, truncated, 2, time_axis=0)
        print('PASS 13F edge graph uses latest public panel availability date')

    def test_common_owner_builder_is_future_invariant(self):
        edges = [
            {'report_date': '2024-01-01', 'panel_availability_date': self.dates[1],
             'ticker_i': 'A', 'ticker_j': 'B',
             'cosine_13f_portfolio_value_overlap': '0.7'},
            {'report_date': '2024-01-05', 'panel_availability_date': self.dates[7],
             'ticker_i': 'A', 'ticker_j': 'C',
             'cosine_13f_portfolio_value_overlap': '0.4'},
        ]
        full = build_common_owner_network(self.assets, self.dates, edges)
        short = build_common_owner_network(self.assets, self.dates[:6], edges)
        assert_prefix_equal(self, full, short, 6, time_axis=0)

    def test_clv_builder_is_future_invariant(self):
        cut = 8
        full = build_trailing_clv_pressure(self.high, self.low, self.close,
                                           lookback=5, min_history=3)
        short = build_trailing_clv_pressure(self.high[:, :cut], self.low[:, :cut],
                                            self.close[:, :cut], lookback=5,
                                            min_history=3)
        assert_prefix_equal(self, full, short, cut)
        self.assertTrue(np.isnan(full[:, :3]).all())

    def test_lagged_peer_pressure_is_future_invariant(self):
        scores = build_trailing_clv_pressure(self.high, self.low, self.close,
                                             lookback=5, min_history=2)
        network = build_dated_industry_network(
            self.assets, self.dates, self.close, self.volume,
            sic_provider_from_records(self.records), lookback=4,
        )
        cut = 8
        full = build_peer_pressure(scores, network, lag=1)
        short = build_peer_pressure(scores[:, :cut], network[:cut], lag=1)
        assert_prefix_equal(self, full, short, cut)
        self.assertTrue(np.isnan(full[:, 0]).all())

    def test_sic_provider_does_not_expose_future_filing(self):
        rows = [
            {'asset': 'A', 'sic': '1000', 'available_date': '2024-01-01'},
            {'asset': 'A', 'sic': '2000', 'available_date': '2024-01-10'},
        ]
        provider = sic_provider_from_records(rows)
        short_provider = sic_provider_from_records(rows[:1])
        self.assertEqual(provider('A', '2024-01-09'), '1000')
        self.assertEqual(provider('A', '2024-01-09'), short_provider('A', '2024-01-09'))
        self.assertEqual(provider('A', '2024-01-10'), '2000')

    def test_dated_industry_graph_is_future_invariant(self):
        provider = sic_provider_from_records(self.records)
        cut = 8
        full = build_dated_industry_network(self.assets, self.dates, self.close,
                                             self.volume, provider, lookback=4)
        short = build_dated_industry_network(self.assets, self.dates[:cut],
                                              self.close[:, :cut], self.volume[:, :cut],
                                              provider, lookback=4)
        assert_prefix_equal(self, full, short, cut, time_axis=0)
        self.assertEqual(full[0].sum(), 0.0)
        self.assertEqual(full[5, 0, 1], 1.0)
        self.assertEqual(full[5, 1, 0], 0.0)

    def test_reversed_network_is_future_invariant(self):
        g = np.zeros((len(self.dates), len(self.assets), len(self.assets)))
        g[:, 0, 1] = 1
        cut = 7
        assert_prefix_equal(self, reverse_direction(g), reverse_direction(g[:cut]), cut,
                            time_axis=0)

    def test_degree_shuffle_is_future_invariant_and_degree_preserving(self):
        g = np.zeros((len(self.dates), 6, 6))
        for t in range(len(self.dates)):
            for i, j in [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]:
                g[t, i, j] = g[t, j, i] = 0.5 + 0.1 * i
        full = degree_preserving_shuffle(g, seed=18)
        short = degree_preserving_shuffle(g[:7], seed=18)
        assert_prefix_equal(self, full, short, 7, time_axis=0)
        np.testing.assert_array_equal((full > 0).sum(axis=2), (g > 0).sum(axis=2))

    def test_matched_nonowner_placebo_is_future_invariant(self):
        provider = sic_provider_from_records(self.records)
        g = np.zeros((len(self.dates), len(self.assets), len(self.assets)))
        g[:, 0, 1] = g[:, 1, 0] = 0.8
        g[:, 0, 2] = g[:, 2, 0] = 0.6
        full = matched_same_industry_nonowners(g, self.assets, self.dates,
                                                provider, seed=7)
        short = matched_same_industry_nonowners(g[:7], self.assets, self.dates[:7],
                                                 provider, seed=7)
        assert_prefix_equal(self, full, short, 7, time_axis=0)
        self.assertGreater(float(full[4, 1, 2] + full[4, 2, 1]), 0.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
