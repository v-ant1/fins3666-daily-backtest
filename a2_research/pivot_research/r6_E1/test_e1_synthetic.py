"""Synthetic tests for E1 runner; no project outcomes or holdout are read."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from r4_harness.runner_guard import validate_frozen_prereg
from r6_E1.run_e1 import (
    ACTIVE_SHARE_MIN, BOOTSTRAP_DRAWS, COST_RATE, HORIZON, MIN_IC, NW_LAG,
    R6_ENDPOINTS, SEED, SHUFFLE_DRAWS, TURNOVER_CAP, _capped_step,
    _endpoint_rows, coverage_gate, forward_returns, monthly_portfolio,
    prereg_diff_payload, run_e1, shuffle_sic2_labels, validate_bundle,
    _r6_trial_count,
)


def synthetic_bundle(n_sp=300, n_dow=30, dates=None):
    if dates is None:
        dates = np.asarray(["2020-11-30", "2020-12-31", "2021-01-29"])
    dates = np.asarray(dates).astype(str)

    def market(n, prefix):
        tickers = np.asarray([f"{prefix}{i:03d}" for i in range(n)])
        pressure = np.tile(np.linspace(-.9, .9, n), (len(dates), 1))
        labels = np.tile(np.asarray([f"{i % 10:02d}" for i in range(n)]), (len(dates), 1))
        peer = np.empty_like(pressure)
        for t in range(len(dates)):
            for i in range(n):
                peers = [j for j in range(n) if j != i and labels[t, j] == labels[t, i]]
                peer[t, i] = np.mean(pressure[t, peers]) if len(peers) >= 2 else np.nan
        roster = np.ones((len(dates), n), bool)
        pactive = np.isfinite(pressure)
        sactive = np.ones((len(dates), n), bool)
        peeractive = np.isfinite(peer)
        return {
            f"{prefix}_tickers": tickers,
            f"{prefix}_formation_dates": dates,
            f"{prefix}_stock_pressure": pressure,
            f"{prefix}_peer_pressure": peer,
            f"{prefix}_active_roster": roster,
            f"{prefix}_active_pressure": pactive,
            f"{prefix}_active_sic2": sactive,
            f"{prefix}_active_peer_score": peeractive,
            f"{prefix}_sic2": labels,
            f"{prefix}_industry_group_size": np.full((len(dates), n), n // 10),
            f"{prefix}_valid_peer_count": np.full((len(dates), n), n // 10 - 1),
        }

    out = market(n_sp, "sp500")
    # The bundle uses the `dow` prefix, while the helper above uses the same key naming.
    out.update(market(n_dow, "dow"))
    return out


class FrozenDesignTests(unittest.TestCase):
    def test_frozen_hash_and_prereg_diff_are_clean(self):
        root = Path(__file__).resolve().parents[1]
        frozen_date, digest = validate_frozen_prereg(root / "specs" / "r6_prereg" / "E1.md")
        self.assertEqual(frozen_date, "2026-11-11")
        self.assertEqual(len(digest), 64)
        diff = prereg_diff_payload()
        self.assertTrue(diff["matches"], diff["differences"])
        self.assertEqual(diff["differences"], [])
        self.assertEqual(R6_ENDPOINTS, ("R6-H4", "R6-H5", "R6-H6"))
        self.assertEqual((HORIZON, NW_LAG, SHUFFLE_DRAWS, BOOTSTRAP_DRAWS, SEED),
                         (21, 20, 500, 5000, 20261111))
        self.assertEqual(_r6_trial_count(), 2)

    def test_runner_requires_execute_before_input_access(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(PermissionError):
                run_e1(Path(td) / "missing.npz", Path(td) / "missing.json",
                       run_dir=Path(td) / "run")
            self.assertFalse((Path(td) / "run" / ".runner.lock").exists())

    def test_bundle_schema_and_development_dates(self):
        data = synthetic_bundle()
        checked = validate_bundle(data)
        self.assertEqual(checked["sp500"]["stock_pressure"].shape, (3, 300))
        data["sp500_formation_dates"][0] = "2019-12-31"
        with self.assertRaises(ValueError):
            validate_bundle(data)


class InputGateTests(unittest.TestCase):
    def test_current_gate_values_pass_and_missing_coverage_fails(self):
        manifest = {
            "development_only": True,
            "forward_returns_computed": False,
            "ics_computed": False,
            "daily_member_day_coverage": {
                "SP500": {"ohlcv_and_sic_coverage_pct": 95.085},
                "Dow30": {"ohlcv_and_sic_coverage_pct": 98.44},
            },
            "universes": {"SP500": {"eligible_dates_fraction_at_250_names": 1.0,
                                      "min_peer_score_eligible": 430}},
        }
        self.assertTrue(coverage_gate(manifest)["passed"])
        manifest["daily_member_day_coverage"]["SP500"]["ohlcv_and_sic_coverage_pct"] = 89.9
        self.assertFalse(coverage_gate(manifest)["passed"])


class SignalAndPortfolioTests(unittest.TestCase):
    def test_forward_return_uses_next_open_through_horizon_close_and_masks_tail(self):
        dates = np.asarray([str(x) for x in np.busday_offset(np.datetime64("2021-01-04"), np.arange(24))])
        op = np.arange(100, 124, dtype=float)[None, :]
        close = op * 1.01
        r, eligible = forward_returns(dates, op, close, np.asarray([dates[0], dates[-1]]))
        self.assertAlmostEqual(r[0, 0], close[0, 21] / op[0, 1] - 1)
        self.assertTrue(eligible[0])
        self.assertFalse(eligible[1])
        self.assertTrue(np.isnan(r[0, 1]))

    def test_within_date_shuffle_preserves_sic2_group_sizes_and_seed(self):
        labels = np.asarray(["01", "01", "01", "02", "02", "", "03"])
        eligible = np.asarray([1, 1, 1, 1, 1, 1, 1], bool)
        a = shuffle_sic2_labels(labels, eligible, np.random.default_rng(SEED))
        b = shuffle_sic2_labels(labels, eligible, np.random.default_rng(SEED))
        np.testing.assert_array_equal(a, b)
        for code in ("01", "02", "03"):
            self.assertEqual(np.count_nonzero(a == code), np.count_nonzero(labels == code))
        self.assertEqual(a[5], "")

    def test_pro_rata_turnover_cap_and_cost_rate(self):
        current = np.ones(30) / 30
        target = np.zeros(30)
        target[:5] = .2
        updated, turnover = _capped_step(current, target, TURNOVER_CAP)
        self.assertAlmostEqual(turnover, TURNOVER_CAP)
        self.assertLessEqual(np.abs(updated - current).sum(), TURNOVER_CAP + 1e-10)
        self.assertAlmostEqual(COST_RATE, .0005)

    def test_monthly_portfolio_caps_turnover_and_emits_metrics(self):
        names = np.asarray([f"T{i:02d}" for i in range(30)])
        dates = np.asarray([str(x) for x in np.busday_offset(np.datetime64("2021-01-04"), np.arange(45))])
        close = np.asarray([100 * np.cumprod(np.full(45, 1 + .0002 * ((i % 5) - 2))) for i in range(30)])
        op = close / 1.0001
        form_ix = [5, 15, 25, 35]
        formation_dates = dates[form_ix]
        scores = np.tile(np.arange(30, dtype=float), (len(form_ix), 1))
        roster = np.ones_like(scores, bool)
        result = monthly_portfolio(scores, roster, op, close, dates, formation_dates, names)
        self.assertLessEqual(result["max_turnover"], TURNOVER_CAP + 1e-9)
        self.assertTrue(np.all(result["turnovers"] <= TURNOVER_CAP + 1e-9))
        self.assertAlmostEqual(result["turnovers"][0], TURNOVER_CAP, places=7)
        self.assertTrue(np.isfinite(result["sharpe"]))
        self.assertTrue(np.isfinite(result["benchmark_sharpe"]))
        self.assertGreaterEqual(result["active_share"], 0)
        self.assertIn("cumulative_gross_return", result)
        self.assertIn("max_drawdown", result)
        self.assertEqual(len(result["eligible_name_counts"]), len(formation_dates))
        self.assertIn("selection_failure_dates", result)

    def test_endpoint_log_has_one_row_per_frozen_holm_endpoint(self):
        rows = _endpoint_rows({"estimate": .01, "statistic": 2.1, "raw_p": .02, "holm_p": .08, "pass": True},
                              {"estimate": .01, "statistic": .005, "raw_p": .01, "holm_p": .04, "pass": True},
                              None)
        self.assertEqual([r["endpoint_id"] for r in rows], list(R6_ENDPOINTS))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[-1]["status"], "not run")
        self.assertIsNone(rows[-1]["raw_p"])


if __name__ == "__main__":
    unittest.main()
