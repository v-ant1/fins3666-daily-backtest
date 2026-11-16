"""Synthetic-only checks for the guarded J1 runner; no project prices loaded."""
from __future__ import annotations

import tempfile
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from r4_harness.prereg_diff import prereg_diff
from r4_harness.runner_guard import guarded_runner, validate_frozen_prereg
from r4_harness.phase3 import break_even_rank_ic
from r6_J1 import run_j1 as j1


class J1SyntheticTests(unittest.TestCase):
    def test_frozen_prereg_and_numeric_diff(self):
        frozen, digest = validate_frozen_prereg(j1.PREREG)
        self.assertEqual(frozen, "2026-11-11")
        self.assertEqual(len(digest), 64)
        result = prereg_diff(j1.DIFF_SOURCE, j1.DIFF_CONFIG)
        self.assertTrue(result.matches, result.differences)
        self.assertEqual(j1.TURNOVER_CAP, .50)
        self.assertEqual(j1.COST_TURNOVER_REFERENCE, .40)
        self.assertEqual(j1.TOP_N / j1.UNIVERSE_N, 5 / 30)
        self.assertEqual(j1.PLACEBO_DRAWS, 500)
        self.assertEqual(j1.BOOTSTRAP_DRAWS, 5000)
        self.assertAlmostEqual(j1.COST_IC_FLOOR,
                               break_even_rank_ic(.40, .04, .0005, 5 / 30),
                               places=10)

    def test_signal_and_forward_alignment_are_exact(self):
        # Five names per SIC2 cluster, deterministic positive price paths.
        n, t = 15, 35
        asset_ix = np.arange(n, dtype=float)[:, None]
        time_ix = np.arange(t, dtype=float)[None, :]
        close = 50 + 0.1 * asset_ix + 0.2 * time_ix + 0.013 * asset_ix * time_ix
        op = close * (1 + 0.0005 * (asset_ix + 1))
        roster = np.ones((n, t), dtype=bool)
        sic = np.tile(np.repeat(["20", "30", "40"], 5)[:, None], (1, t))
        signal, relative_fwd, mask, scheduled = j1.build_j1_panels(
            close, op, roster, sic, formation_start_index=5
        )
        self.assertEqual(np.flatnonzero(scheduled).tolist(), list(range(5, t, 5)))
        d, i = 5, 0
        same_sic = np.arange(0, 5)
        own_r5 = close[i, d] / close[i, d - 5] - 1
        peer_r5 = np.mean([close[q, d] / close[q, d - 5] - 1 for q in same_sic if q != i])
        self.assertAlmostEqual(signal[i, d], own_r5 - peer_r5, places=12)
        own_fwd = close[i, d + 5] / op[i, d + 1] - 1
        peer_fwd = np.mean([close[q, d + 5] / op[q, d + 1] - 1 for q in same_sic if q != i])
        self.assertAlmostEqual(relative_fwd[i, d], own_fwd - peer_fwd, places=12)
        self.assertTrue(mask[i, d])
        self.assertFalse(mask[i, d + 1])

    def test_forward_peer_mean_excludes_peer_without_trailing_bar(self):
        n, t = 4, 20
        close = np.tile(np.linspace(50, 55, t), (n, 1))
        close += np.arange(n, dtype=float)[:, None] * np.linspace(0, .1, t)
        op = close.copy()
        # Name 3 has valid forward prices, but no t-5 trailing close.
        close[3, 0] = np.nan
        close[3, 10] = 200.0
        roster = np.ones((n, t), bool)
        sic = np.full((n, t), "20")
        signal, rel_fwd, mask, _ = j1.build_j1_panels(
            close, op, roster, sic, formation_start_index=5)
        d, target = 5, 0
        peers = [1, 2]
        forward = [close[q, d + 5] / op[q, d + 1] - 1 for q in range(n)]
        expected = forward[target] - np.mean([forward[q] for q in peers])
        contaminated = forward[target] - np.mean([forward[q] for q in (1, 2, 3)])
        self.assertTrue(np.isnan(signal[3, d]))
        self.assertTrue(mask[target, d])
        self.assertAlmostEqual(rel_fwd[target, d], expected, places=12)
        self.assertNotAlmostEqual(rel_fwd[target, d], contaminated, places=6)

    @staticmethod
    def _coverage_fixture(folder: Path, relative_names: int):
        folder.mkdir(parents=True, exist_ok=True)
        input_path = folder / "prices.npz"
        input_path.write_bytes(b"synthetic input bytes")
        price_manifest = {
            "sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
            "development_window": ["2020-06-01", "2026-10-30"],
            "sessions": 1614, "sp500_assets": 622,
        }
        price_manifest_path = folder / "price_manifest.json"
        price_manifest_path.write_text(json.dumps(price_manifest), encoding="utf-8")
        eligible_dates = 298 if relative_names >= 250 else 0
        coverage_manifest = {
            "scope": "trailing signal inputs only; no forward returns or outcomes",
            "price_boundary": {"start": "2020-06-01", "end": "2026-10-30"},
            "formation_count": 298,
            "sp500": {"formation_dates_ge_250_relative_names": eligible_dates,
                      "formation_dates": 298},
        }
        coverage_manifest_path = folder / "coverage.json"
        coverage_manifest_path.write_text(json.dumps(coverage_manifest), encoding="utf-8")
        coverage_csv_path = folder / "coverage.csv"
        rows = ["universe,formation_date,relative_return_names,sp500_250_name_gate"]
        for i in range(298):
            date = f"2021-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}"
            gate = "true" if relative_names >= 250 else "false"
            rows.append(f"sp500,{date},{relative_names},{gate}")
            rows.append(f"dow,{date},16,false")
        coverage_csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        feature_path = folder / "signal_bundle.parquet"
        feature_path.write_bytes(b"synthetic feature bundle placeholder")
        kwargs = {
            "input_path": input_path, "feature_path": feature_path,
            "price_manifest_path": price_manifest_path,
            "coverage_manifest_path": coverage_manifest_path,
            "coverage_csv_path": coverage_csv_path,
            "expected_price_sha": "",
            "expected_price_manifest_sha": "",
            "expected_coverage_manifest_sha": "",
            "expected_coverage_csv_sha": "",
        }
        return kwargs

    def test_coverage_gate_passes_input_only_and_precedes_label_bundle_load(self):
        with tempfile.TemporaryDirectory() as td:
            good = self._coverage_fixture(Path(td) / "good", 250)
            report = j1.verify_input_coverage(**good)
            self.assertTrue(report["verified"])
            self.assertFalse(report["forward_labels_built"])
            self.assertEqual(report["sp500_dates_ge_250"], 298)

            bad = self._coverage_fixture(Path(td) / "bad", 249)
            loaded = []
            with patch.object(j1, "load_bundle", side_effect=lambda *_: loaded.append(True)):
                with self.assertRaisesRegex(ValueError, "coverage gate"):
                    j1._load_verified_bundle(
                        bad["input_path"], bad["feature_path"],
                        **{k: v for k, v in bad.items() if k not in {"input_path", "feature_path"}})
            self.assertEqual(loaded, [], "price/label panel load must wait for coverage approval")

    def test_placebo_is_seeded_and_saves_registered_draw_count(self):
        rng = np.random.default_rng(101)
        n, t = 30, 25
        sic = np.tile(np.repeat(["10", "20", "30", "40", "50", "60"], 5)[:, None], (1, t))
        signal = rng.normal(size=(n, t))
        # Negative relation supports the preregistered direction convention.
        outcome = -0.2 * signal + rng.normal(scale=.5, size=(n, t))
        mask = np.ones((n, t), bool)
        ic = j1._direction_ic(signal, outcome, mask)
        self.assertGreater(ic.mean_ic, 0)
        self.assertGreater(ic.nw_t, 2)
        a = j1._sic2_shuffle(signal, outcome, mask, sic, draws=17, seed=20261111)
        b = j1._sic2_shuffle(signal, outcome, mask, sic, draws=17, seed=20261111)
        self.assertEqual(a["draws"].shape, (17,))
        np.testing.assert_array_equal(a["draws"], b["draws"])
        self.assertEqual(j1.PLACEBO_DRAWS, 500)
        self.assertEqual(j1.PLACEBO_SEED, 20261111)

    def test_no_execute_refuses_before_lock_or_callback(self):
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            called = []
            @guarded_runner(prereg_path=j1.PREREG, run_dir=run_dir)
            def guarded():
                called.append(True)
            with self.assertRaisesRegex(PermissionError, "--execute"):
                guarded()
            self.assertFalse(called)
            self.assertFalse((run_dir / ".runner.lock").exists())

    def test_actual_j1_entry_refuses_before_reading_any_inputs(self):
        with self.assertRaisesRegex(PermissionError, "--execute"):
            j1._guarded_run("does-not-exist.npz", "does-not-exist.parquet",
                            "does-not-exist-holm.json", execute=False)

    def test_cumulative_r6_variant_count(self):
        # Exercise the parser using a synthetic log, never the live run log.
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "trials.md"
            log.write_text(
                "- R6 variant 1: J1-V1\n"
                "- R6 variant 2: D4-V1\n"
                "- R6 variant 3: D5-V1\n",
                encoding="utf-8")
            self.assertEqual(j1._trial_count(log), 3)

    def _flat_synthetic_prices(self, n=6, t=24):
        close = np.full((n, t), 10.0)
        op = np.full((n, t), 10.0)
        roster = np.ones((n, t), dtype=bool)
        names = np.array([f"N{i}" for i in range(n)])
        scores = np.tile(np.arange(n, 0, -1, dtype=float)[:, None], (1, t))
        return scores, op, close, roster, names

    def test_missing_close_is_carried_until_next_valid_close(self):
        scores, op, close, roster, names = self._flat_synthetic_prices()
        close[0, 8] = np.nan
        close[0, 9:] = 12.0
        formations = [5, 10, 15]
        book = j1._simulate_book(scores, op, close, roster, formations, names,
                                 cost_rate=0.0)
        ew = j1._simulate_ew(op, close, roster, formations, cost_rate=0.0)
        loc = {int(d): i for i, d in enumerate(book["return_date_indices"])}
        ew_loc = {int(d): i for i, d in enumerate(ew["return_date_indices"])}
        # A missing close marks the held name at its last close (10), so no
        # artificial one-day loss/NaN is introduced on day 8.
        self.assertAlmostEqual(book["returns"][loc[8]], 0.0, places=12)
        self.assertAlmostEqual(ew["returns"][ew_loc[8]], 0.0, places=12)
        # The next valid close (12) is then recognized: 1/5 and 1/6 weights.
        self.assertAlmostEqual(book["returns"][loc[9]], 0.04, places=12)
        self.assertAlmostEqual(ew["returns"][ew_loc[9]], 1.0 / 30.0, places=12)

    def test_stale_name_sells_at_first_valid_open_and_stays_out(self):
        scores, op, close, roster, names = self._flat_synthetic_prices()
        close[0, 10:] = np.nan
        op[0, 11] = np.nan
        close[0, 11] = np.nan
        op[0, 12] = 20.0
        close[0, 12] = 20.0
        close[0, 13:] = 30.0
        op[0, 13:] = 20.0
        formations = [5, 10, 15]
        book = j1._simulate_book(scores, op, close, roster, formations, names,
                                 cost_rate=0.0)
        ew = j1._simulate_ew(op, close, roster, formations, cost_rate=0.0)
        loc = {int(d): i for i, d in enumerate(book["return_date_indices"])}
        ew_loc = {int(d): i for i, d in enumerate(ew["return_date_indices"])}
        # The carried 10 mark becomes a 20 sale at the first valid open (day
        # 12); day 13's jump to 30 cannot accrue after the forced exit.
        self.assertAlmostEqual(book["returns"][loc[12]], 0.20, places=12)
        self.assertAlmostEqual(ew["returns"][ew_loc[12]], 1.0 / 6.0, places=12)
        self.assertAlmostEqual(book["returns"][loc[13]], 0.0, places=12)
        self.assertAlmostEqual(ew["returns"][ew_loc[13]], 0.0, places=12)
        self.assertTrue(np.all(np.isfinite(book["returns"])))
        self.assertTrue(np.all(np.isfinite(ew["returns"])))

    def test_stale_name_exits_at_rebalance_open_without_same_open_reentry(self):
        scores, op, close, roster, names = self._flat_synthetic_prices()
        close[0, 10] = np.nan
        op[0, 11] = 20.0
        close[0, 11] = 20.0
        op[0, 12:] = 20.0
        close[0, 12:] = 30.0
        formations = [5, 10, 15]
        book = j1._simulate_book(scores, op, close, roster, formations, names,
                                 cost_rate=0.0)
        ew = j1._simulate_ew(op, close, roster, formations, cost_rate=0.0)
        loc = {int(d): i for i, d in enumerate(book["return_date_indices"])}
        ew_loc = {int(d): i for i, d in enumerate(ew["return_date_indices"])}
        # The valid open on the scheduled fill is used to liquidate the stale
        # name and it is not bought again at that same rebalance.
        self.assertAlmostEqual(book["returns"][loc[12]], 0.0, places=12)
        self.assertAlmostEqual(ew["returns"][ew_loc[12]], 0.0, places=12)

    def test_never_trading_again_liquidates_at_last_valid_close(self):
        scores, op, close, roster, names = self._flat_synthetic_prices(n=5)
        close[0, 10:] = np.nan
        op[0, 11:] = np.nan
        close[0, 11:] = np.nan
        formations = [5, 10, 15]
        book = j1._simulate_book(scores, op, close, roster, formations, names,
                                 cost_rate=0.001)
        ew = j1._simulate_ew(op, close, roster, formations, cost_rate=0.001)
        # Initial holdings are already equal-weight. Only the terminal forced
        # sale incurs a cost: 0.1% of the 20% name position.
        self.assertAlmostEqual(float(book["costs"].sum()), 0.0002, places=10)
        self.assertAlmostEqual(float(ew["costs"].sum()), 0.0002, places=10)
        self.assertTrue(np.all(np.isfinite(book["returns"])))
        self.assertTrue(np.all(np.isfinite(ew["returns"])))

    def test_runner_loads_two_universe_schema_and_rejects_old_dates(self):
        dates = np.array(["2020-11-27", "2020-11-30", "2020-12-01"])
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic.npz"
            data = {}
            for u, n in (("sp500", 5), ("dow", 6)):
                shape = (n, len(dates))
                data[f"{u}_dates"] = dates
                data[f"{u}_assets"] = np.array([f"{u}_{i}" for i in range(n)])
                data[f"{u}_roster"] = np.ones(shape, bool)
                data[f"{u}_sic2"] = np.full(shape, "20")
                data[f"{u}_adjusted_open"] = np.full(shape, 10.0)
                data[f"{u}_adjusted_close"] = np.full(shape, 10.0)
            np.savez(path, **data)
            loaded = j1.load_bundle(path)
            self.assertEqual(loaded["sp500"]["adjusted_close"].shape, (5, 3))
            self.assertEqual(loaded["dow"]["adjusted_open"].shape, (6, 3))
            data["sp500_dates"] = np.array(["2019-12-31", "2020-11-30", "2020-12-01"])
            np.savez(path, **data)
            with self.assertRaisesRegex(ValueError, "development window"):
                j1.load_bundle(path)

    def test_portfolio_turnover_cap_on_synthetic_switches(self):
        rng = np.random.default_rng(919)
        n, t = 30, 40
        close = 50 * np.cumprod(1 + rng.normal(0.0002, 0.006, (n, t)), axis=1)
        op = close * (1 + rng.normal(0, .0002, (n, t)))
        scores = np.tile(rng.normal(size=n)[:, None], (1, t))
        for d in (5, 10, 15, 20):
            scores[:, d] = rng.permutation(scores[:, d])
        roster = np.ones((n, t), bool)
        result = j1._simulate_book(scores, op, close, roster, [5, 10, 15, 20],
                                   np.array([f"N{i:02}" for i in range(n)]),
                                   cost_rate=j1.COST_PER_NOTIONAL)
        self.assertLessEqual(float(np.max(result["turnovers"])), .50 + 1e-8)

    def test_runner_constants_match_fixed_spec(self):
        self.assertEqual(j1.NW_LAG, 4)
        self.assertEqual(j1.HORIZON, 5)
        self.assertEqual(j1.FORMATION_STEP, 5)
        self.assertEqual(j1.TOP_N, 5)
        self.assertEqual(j1.TURNOVER_CAP, .50)
        self.assertEqual(j1.COST_TURNOVER_REFERENCE, .40)
        self.assertEqual(j1.TOP_N / j1.UNIVERSE_N, 5 / 30)
        self.assertEqual(j1.ACTIVE_SHARE_MIN, .50)
        self.assertEqual(j1.BOOTSTRAP_BLOCK, 10)
        self.assertEqual(j1.BOOTSTRAP_DRAWS, 5000)
        self.assertEqual(j1.PLACEBO_DRAWS, 500)
        self.assertEqual(j1.ENDPOINTS, ("R6-H7", "R6-H8", "R6-H9"))

    def test_holm_threshold_is_strict_and_distinct_from_raw_gate_status(self):
        self.assertEqual(j1._holm_decision(.049999), "reject")
        self.assertEqual(j1._holm_decision(.05), "retain")
        self.assertEqual(j1._holm_decision(.051), "retain")


if __name__ == "__main__":
    unittest.main(verbosity=2)
