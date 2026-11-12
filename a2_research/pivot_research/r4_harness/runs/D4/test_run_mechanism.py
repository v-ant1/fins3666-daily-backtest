import unittest
from collections import defaultdict

import numpy as np

from r4_harness.runs.D4.build_inputs import filing_time_network
from r4_harness.runs.D4.run_mechanism import (
    _directed_degree_rewire,
    _endpoint_log_rows,
    _equivalence_result,
    _ncp,
    _random_directed_links,
    _shift_graphs,
)


class D4RunnerSyntheticTests(unittest.TestCase):
    def test_directed_swap_preserves_in_out_degrees_and_row_sums(self):
        graph = np.zeros((5, 5), float)
        graph[0, 1] = graph[0, 2] = 1.0
        graph[1, 3] = 1.0
        graph[2, 4] = 1.0
        graph[3, 0] = graph[4, 0] = 1.0
        result = _directed_degree_rewire(graph, np.random.default_rng(19))
        np.testing.assert_array_equal((result > 0).sum(axis=0), (graph > 0).sum(axis=0))
        np.testing.assert_array_equal((result > 0).sum(axis=1), (graph > 0).sum(axis=1))
        self.assertFalse(np.diag(result).any())
        np.testing.assert_allclose(result.sum(axis=1), (graph > 0).any(axis=1).astype(float))

    def test_random_links_preserves_count_and_zero_rows(self):
        graph = np.zeros((5, 5), float)
        graph[0, 1] = graph[0, 2] = 0.2
        graph[1, 2] = 0.3
        graph[2, 0] = 0.4
        graph[3, 0] = 0.5
        result = _random_directed_links(graph, np.random.default_rng(22))
        self.assertEqual(int((result > 0).sum()), int((graph > 0).sum()))
        self.assertFalse((result[4] > 0).any())
        self.assertFalse(np.diag(result).any())
        np.testing.assert_allclose(result.sum(axis=1)[:4], np.ones(4))

    def test_shift_is_exact_circular_twenty_session_alignment(self):
        cube = np.arange(5 * 2 * 2).reshape(5, 2, 2)
        shifted = _shift_graphs(cube, shift=2)
        np.testing.assert_array_equal(shifted[2], cube[0])
        np.testing.assert_array_equal(shifted[0], cube[3])

    def test_peer_score_does_not_require_target_own_clv(self):
        graph = np.zeros((1, 3, 3), float)
        graph[0, 0, 1] = graph[0, 0, 2] = 1.0
        clv = np.array([[np.nan], [.2], [.6]])
        roster = np.ones((3, 1), bool)
        score = _ncp(clv, graph, roster, np.array([1.0]))
        self.assertFalse(np.isnan(score[0, 0]))
        self.assertAlmostEqual(score[0, 0], .4)

    def test_equivalence_requires_ci_and_draw_tail_inside_margin(self):
        rng = np.random.default_rng(41)
        series = rng.normal(0, .0004, size=400)
        draws = rng.normal(0, .0005, size=500)
        result = _equivalence_result(series, draws, margin=.00577)
        self.assertTrue(result['passed'])
        self.assertLess(result['ci90_lower'], result['ci90_upper'])
        self.assertLess(result['equivalence_p'], .05)
        self.assertLess(result['p95_abs_draw_mean_ic'], .00577)

    def test_endpoint_logger_handles_equivalence_rows_without_t_stat(self):
        endpoints = {
            'D4-1 primary IC': {'mean_ic': .01, 'nw_t': 2.1, 'raw_p': .02, 'passed': True},
            'D4-2 degree-preserving comparison': {'mean_ic': .01, 'nw_t': 2.1, 'raw_p': .03, 'placebo_p95': .005, 'passed': True},
            'D4-3 random-link comparison': {'mean_ic': .01, 'nw_t': 2.1, 'raw_p': .03, 'placebo_p95': .006, 'passed': True},
            'D4-4 fixed 20-session shift comparison': {'difference_mean_ic': .004, 'difference_nw_t': 2.1, 'raw_p': .02, 'passed': True},
        }
        for i, family in ((5, 'degree'), (6, 'random'), (7, 'shift')):
            endpoints[f'D4-{i} {family} placebo equivalence'] = {
                'mean_ic': 0.0, 'raw_p': .01, 'ci90_lower': -.001,
                'ci90_upper': .001, 'p95_abs_draw_mean_ic': .002,
            }
        endpoints['D4-8 variant-2 IC'] = {'mean_ic': .002, 'nw_t': .4, 'raw_p': .3}
        rows = _endpoint_log_rows({'endpoints': endpoints})
        self.assertEqual(len(rows), 8)
        self.assertTrue(all('None' not in detail for _, detail in rows))

    def test_variant_two_uses_sum_of_manager_minimum_weights(self):
        report = '2020-06-30'
        coverage = {report: [{
            'status': 'parsed_ok', 'availability_filing_date': '2020-09-10',
            'manager_cik': '1',
        }]}
        positions = {report: {('1', 'AAPL'): 70.0, ('1', 'TRV'): 30.0}}
        fixed = {'1'}
        pit = {report: ({'1'}, '2020-09-10')}
        dates = ['2020-09-10', '2020-09-11']
        active = np.ones((2, 2), dtype=bool)
        result, *_ = filing_time_network(
            ['AAPL', 'TRV'], dates, active, coverage, positions, fixed, pit,
            edge_method='sum_min',
        )
        self.assertEqual(result[0].sum(), 0.0)
        self.assertAlmostEqual(result[1, 0, 1], .3)
        self.assertAlmostEqual(result[1, 1, 0], .3)


if __name__ == '__main__':
    unittest.main()
