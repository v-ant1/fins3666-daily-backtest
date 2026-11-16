"""Synthetic-only tests for K1 timing, inference primitives and guards."""
import unittest
from datetime import date, timedelta
from pathlib import Path
import tempfile
import hashlib
import json
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from r4_harness.r6 import k1_runner as k


class K1RunnerSyntheticTests(unittest.TestCase):
    def test_frozen_hash_and_prereg_diff(self):
        frozen_date, digest = k.validate_frozen_prereg(k.PREREG)
        self.assertEqual(frozen_date, "2026-11-11")
        self.assertEqual(digest, k.EXPECTED_PREREG_SHA256)
        self.assertTrue(k.prereg_diff_payload().matches)

    def test_guard_requires_execute_without_touching_inputs(self):
        with self.assertRaises(PermissionError):
            k.main([])

    def test_bmo_amc_and_intraday_mapping(self):
        ds = np.array([str(date(2021, 1, 4) + timedelta(days=i)) for i in range(8)])
        bmo = k._session_index("2021-01-05T08:00:00-05:00", ds, "BMO")
        amc = k._session_index("2021-01-05T16:05:00-05:00", ds, "AMC")
        self.assertEqual(bmo, 1)
        self.assertEqual(amc, 2)
        with self.assertRaises(ValueError):
            k._session_index("2021-01-05T10:00:00-05:00", ds, "BMO")
        self.assertIsNone(k._session_index("2021-01-05T10:00:00-05:00", ds, "INTRADAY"))

    def test_forward_horizon_and_event_pressure(self):
        self.assertAlmostEqual(k._market_adjusted_event(105, 100, 202, 200), .04)
        stock_close = np.arange(100, 130, dtype=float)
        stock_open = np.arange(100, 130, dtype=float)
        spy_close = np.arange(200, 230, dtype=float)
        spy_open = np.arange(200, 230, dtype=float)
        got = k._forward_abret21(stock_close, stock_open, spy_close, spy_open, 2)
        expected = (stock_close[23] / stock_open[3] - 1) - (spy_close[23] / spy_open[3] - 1)
        self.assertAlmostEqual(got, expected)
        self.assertTrue(np.isnan(k._market_adjusted_event(np.nan, 100, 200, 200)))

    def test_quarterly_mechanism_detects_planted_positive_ic(self):
        rows = []
        for qi in range(8):
            q = f"202{qi // 4}Q{qi % 4 + 1}"
            for j in range(12):
                x = float(j)
                rows.append({"quarter": q, "signal": x, "fwd_abret21": x + (j % 2) * .001,
                             "sic2": f"{j % 3:02d}", "ticker": f"T{j}", "cik": str(qi*100+j)})
        result = k.mechanism(rows)
        self.assertEqual(len(result["quarters"]), 8)
        self.assertGreater(result["mean_ic"], .95)
        self.assertGreaterEqual(result["nw_t"], 2)
        self.assertTrue(result["pass"])

    def test_sic2_shuffle_is_reproducible_and_preserves_finite_mask(self):
        rows = []
        for qn in range(6):
            for j in range(18):
                rows.append({"quarter": f"202{qn//4}Q{qn%4+1}", "signal": float(j),
                             "fwd_abret21": float((j * 7 + qn) % 19), "sic2": f"{j%3:02d}"})
        a = k.sic2_shuffle(rows, draws=20, seed=314)
        b = k.sic2_shuffle(rows, draws=20, seed=314)
        np.testing.assert_array_equal(a["draws"], b["draws"])
        self.assertEqual(len(a["draws"]), 20)
        self.assertTrue(np.isfinite(a["draws"]).all())

    def test_monthly_formations_and_k_cohort(self):
        dates = pd.bdate_range("2020-11-27", periods=120).strftime("%Y-%m-%d").to_numpy()
        forms = k.monthly_formations(dates)
        self.assertGreaterEqual(len(forms), 4)
        self.assertTrue(all(dates[i][:7] != dates[i+1][:7] for i in forms[:-1]))
        score = np.array([9., 8., 7., 6., 5., 4., np.nan])
        roster = np.array([1, 1, 1, 1, 1, 1, 1], bool)
        opens = np.array([10., 10., 10., 10., 10., 10., 10.])
        weights, n, count, selected = k.target_weights(score, roster, opens,
                                                       np.array(["A","B","C","D","E","F","G"]))
        self.assertEqual((n, count, selected), (7, 3, 3))
        self.assertEqual(set(np.flatnonzero(weights)), {0, 1, 2})
        self.assertAlmostEqual(weights.sum(), 1.)

    def test_turnover_cap_and_decision63_price_gap(self):
        weights, turnover, binds = k.cap_turnover(np.array([.5,.5,0.]), np.array([0.,0.,1.]))
        self.assertAlmostEqual(turnover, .5)
        self.assertTrue(binds)
        close = np.array([[100., np.nan, np.nan, 110.], [50., 55., 55., 55.]])
        returns = k.stale_close_returns(close)
        np.testing.assert_allclose(returns[0], [0., 0., 0., .1])
        np.testing.assert_allclose(returns[1], [0., .1, 0., 0.])

    @staticmethod
    def _monthly_synthetic():
        dates = pd.bdate_range("2020-11-27", periods=120).strftime("%Y-%m-%d").to_numpy()
        tickers = np.array(["A", "B", "C", "D", "E", "F"])
        op = np.full((6, len(dates)), 100.)
        close = np.full_like(op, 100.)
        roster = np.ones_like(op, bool)
        forms = k.monthly_formations(dates)
        rows = []
        for q, f in enumerate(forms):
            order = [5, 4, 3, 2, 1, 0] if q == 0 else [0, 1, 2, 3, 4, 5]
            for i, ticker in enumerate(tickers):
                rows.append({"ticker": ticker, "event_index": int(f), "signal": float(order[i])})
        bundle = {"dates": dates, "dow_tickers": tickers, "dow_open": op,
                  "dow_close": close, "dow_roster": roster}
        return bundle, rows, forms

    def test_missing_open_at_rebalance_sells_at_next_valid_open(self):
        bundle, rows, forms = self._monthly_synthetic()
        fill2 = int(forms[1] + 1)
        bundle["dow_open"][0, fill2] = np.nan
        bundle["dow_open"][0, fill2 + 1] = 120.
        bundle["dow_close"][0, fill2 + 1] = 120.
        result = k._simple_monthly_book(bundle, rows)
        sale_day = fill2 + 1
        daily_i = sale_day - int(forms[0] + 1)
        self.assertGreater(result["strategy_returns"][daily_i], .02)
        self.assertGreater(result["strategy_returns"][daily_i], result["ew_returns"][daily_i])

    def test_missing_close_mid_hold_carries_then_catches_up(self):
        bundle, rows, forms = self._monthly_synthetic()
        fill1 = int(forms[0] + 1)
        bundle["dow_close"][0, fill1 + 1:fill1 + 3] = np.nan
        bundle["dow_close"][0, fill1 + 3] = 110.
        result = k._simple_monthly_book(bundle, rows)
        base = int(forms[0] + 1)
        self.assertAlmostEqual(result["strategy_returns"][fill1 + 1 - base], 0., places=12)
        self.assertAlmostEqual(result["strategy_returns"][fill1 + 2 - base], 0., places=12)
        self.assertGreater(result["strategy_returns"][fill1 + 3 - base], .01)

    def test_delisted_name_uses_last_close_terminal_fallback(self):
        bundle, rows, forms = self._monthly_synthetic()
        fill1, fill2 = int(forms[0] + 1), int(forms[1] + 1)
        bundle["dow_close"][0, fill1 + 1:] = np.nan
        bundle["dow_open"][0, fill2:] = np.nan
        result = k._simple_monthly_book(bundle, rows)
        self.assertGreaterEqual(result["terminal_stale_fallback_names"], 1)
        self.assertTrue(np.any(result["costs"] > 0))

    def test_manifest_fails_closed_for_absent_or_tampered_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(k.InputManifestError):
                k.validate_input_manifest(root / "missing.json", root=root)
            paths = {
                "prices": root / "r4_harness" / "r6" / "K1_INPUTS.npz",
                "events": root / "r6_data" / "earnings_clock_sp500.csv",
                "sic": root / "r6_data" / "sp500_sic_panel.csv",
                "sp500_roster": root / "r6_data" / "sp500_pit_roster.csv",
                "dow_roster": root / "r6_data" / "dow_pit_roster.csv",
            }
            files = {}
            for name, path in paths.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(("synthetic placeholder " + name).encode())
                files[name] = {"path": path.relative_to(root).as_posix(), "sha256": k.sha256_file(path)}
            manifest = {"schema": "K1_INPUTS_V1", "development_window": ["2020-11-27", "2026-10-30"],
                        "holdout_loaded": False, "forward_labels_built": False, "files": files}
            mp = root / "manifest.json"
            import json
            mp.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(k.validate_input_manifest(mp, root=root)["schema"], "K1_INPUTS_V1")
            paths["prices"].write_bytes(b"tampered")
            with self.assertRaisesRegex(k.InputManifestError, "SHA-256 mismatch"):
                k.validate_input_manifest(mp, root=root)

    def test_holm_manifest_uses_json_digest_and_null_slots_are_unrun(self):
        h15 = [f"R6-H{i}" for i in range(1, 16)]
        self.assertEqual(hashlib.sha256(json.dumps(h15).encode()).hexdigest(),
                         "42e24dc6bed8ec2c46755bc3a45d4fce3d5aa96513d44225b7a643432c313911")
        manifest = [f"R6-H{i}" for i in range(1, 22)]
        p_values = {e: .02 for e in manifest[:15]}
        p_values.update({e: None for e in manifest[15:]})
        payload = {"manifest": manifest, "manifest_sha256": hashlib.sha256(
                   json.dumps(manifest).encode()).hexdigest(), "p_values": p_values}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "holm.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            adjusted = k._read_holm(path, {"R6-H16": .01, "R6-H17": .03, "R6-H18": None})
            self.assertIn("R6-H21", adjusted)
            for endpoint in ("R6-H18", "R6-H19", "R6-H20", "R6-H21"):
                self.assertEqual(adjusted[endpoint]["holm_p"], 1.0)
            payload["manifest_sha256"] = "0" * 64
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manifest/hash"):
                k._read_holm(path, {})

    def test_variant_count_is_unique_and_registry_driven(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trials.md"
            path.write_text("""# Prior rounds\nX9-V1\n\n## R6 Holm family\n- R6 variant 1: D1-V1\n- R6 variant 2: E1-V1\n- R6 variant 3: J1-V1\n- R6 variant 4: R1-V1\n- R6 variant 5: P1-V1\n- K1-V1 FROZEN\n- G1-V1 FROZEN\n- duplicate mention: D1-V1\n""", encoding="utf-8")
            self.assertEqual(k._r6_variant_count(path), 7)
            path.write_text(path.read_text(encoding="utf-8") + "- R6 variant 8: Z9-V1\n", encoding="utf-8")
            self.assertEqual(k._r6_variant_count(path), 8)

    def test_governance_preflight_precedes_event_forward_computation(self):
        synthetic_manifest = {"files": {
            "events": {"path": k.EVENTS.relative_to(k.ROOT).as_posix()},
            "prices": {"path": k.INPUTS.relative_to(k.ROOT).as_posix()},
        }}
        with tempfile.TemporaryDirectory() as tmp:
            bad_holm = Path(tmp) / "bad_holm.json"
            bad_holm.write_text(json.dumps({"manifest": [], "p_values": {},
                                            "manifest_sha256": "bad"}), encoding="utf-8")
            with patch.object(k, "validate_frozen_prereg", return_value=("2026-11-11", "hash")), \
                 patch.object(k, "EXPECTED_PREREG_SHA256", "hash"), \
                 patch.object(k, "prereg_diff_payload", return_value=MagicMock()), \
                 patch.object(k, "validate_input_manifest", return_value=synthetic_manifest), \
                 patch.object(k, "_r6_variant_count", return_value=7), \
                 patch.object(k, "make_event_rows", side_effect=AssertionError("outcome path reached")):
                with self.assertRaisesRegex(ValueError, "Holm manifest"):
                    k.analyze(holm_path=bad_holm)

    def test_invalid_manifest_stops_before_event_forward_computation(self):
        with patch.object(k, "validate_frozen_prereg", return_value=("2026-11-11", "hash")), \
             patch.object(k, "EXPECTED_PREREG_SHA256", "hash"), \
             patch.object(k, "prereg_diff_payload", return_value=MagicMock()), \
             patch.object(k, "validate_input_manifest", side_effect=k.InputManifestError("synthetic manifest error")), \
             patch.object(k, "make_event_rows", side_effect=AssertionError("outcome path reached")):
            with self.assertRaisesRegex(k.InputManifestError, "synthetic manifest error"):
                k.analyze()

    def test_missing_k1_trial_registration_stops_before_event_forward_computation(self):
        synthetic_manifest = {"files": {
            "events": {"path": k.EVENTS.relative_to(k.ROOT).as_posix()},
            "prices": {"path": k.INPUTS.relative_to(k.ROOT).as_posix()},
        }}
        with tempfile.TemporaryDirectory() as tmp:
            trials = Path(tmp) / "trials.md"
            trials.write_text("## R6 Holm family\nD1-V1\nG1-V1\n", encoding="utf-8")
            with patch.object(k, "validate_frozen_prereg", return_value=("2026-11-11", "hash")), \
                 patch.object(k, "EXPECTED_PREREG_SHA256", "hash"), \
                 patch.object(k, "prereg_diff_payload", return_value=MagicMock()), \
                 patch.object(k, "validate_input_manifest", return_value=synthetic_manifest), \
                 patch.object(k, "make_event_rows", side_effect=AssertionError("outcome path reached")):
                with self.assertRaisesRegex(ValueError, "K1-V1 must be registered"):
                    k.analyze(trial_log=trials)

    def test_end_to_end_synthetic_execute_runs_guard_analyze_write_and_append(self):
        """Exercise the guarded runner end to end with synthetic-only outcomes."""
        with tempfile.TemporaryDirectory(dir=k.HERE, prefix="_k1_synthetic_") as tmp:
            root = Path(tmp)
            bundle_path = root / "K1_INPUTS.npz"
            events_path = root / "events.csv"
            manifest_path = root / "manifest.json"
            results_path = root / "results.json"
            endpoints_path = root / "endpoints.csv"
            trial_log = root / "trials.md"
            trial_log.write_text(
                "## R6 Holm family\nD1-V1 E1-V1 J1-V1 R1-V1 P1-V1 K1-V1 G1-V1\n\n"
                "## Holdout integrity log\n", encoding="utf-8")
            dates = pd.bdate_range("2020-11-27", "2026-10-30").strftime("%Y-%m-%d").to_numpy(dtype="U10")
            tickers = np.asarray([f"T{i:02d}" for i in range(30)])
            opens = np.full((30, len(dates)), 100.0)
            closes = np.full_like(opens, 100.0)
            spy_open = np.full(len(dates), 100.0)
            spy_close = np.full(len(dates), 100.0)
            roster = np.ones((30, len(dates)), dtype=bool)
            sic2 = np.full((30, len(dates)), "20", dtype="U2")
            events = []
            event_dates = ["2021-03-31", "2021-06-30", "2021-09-30",
                           "2021-12-31", "2022-03-31", "2022-06-30"]
            rng = np.random.default_rng(481)
            for qi, day in enumerate(event_dates):
                e = int(np.flatnonzero(dates == day)[0])
                noise = rng.normal(0.0, .45 + .18 * qi, size=30)
                outcome_rank = np.argsort(np.argsort(np.arange(30) + noise))
                for i, ticker in enumerate(tickers):
                    closes[i, e - 1] = 100.0
                    closes[i, e] = 100.0 * (1 + i * .001)
                    closes[i, e + 21] = 100.0 * (1 + outcome_rank[i] * .0005)
                    events.append({"ticker": ticker, "cik": f"{i+1:010d}",
                        "report_date": day, "acceptance_timestamp_et": f"{day}T08:00:00-05:00",
                        "classification": "BMO"})
            np.savez_compressed(bundle_path,
                dates=dates, sp500_tickers=tickers, sp500_open=opens, sp500_close=closes,
                sp500_roster=roster, sp500_sic2=sic2,
                dow_tickers=tickers, dow_open=opens.copy(), dow_close=closes.copy(),
                dow_roster=roster.copy(), dow_sic2=sic2.copy(), spy_open=spy_open,
                spy_close=spy_close)
            pd.DataFrame(events).to_csv(events_path, index=False)
            source_files = {
                "sic": root / "sic.csv", "sp500_roster": root / "sp_roster.csv",
                "dow_roster": root / "dow_roster.csv"}
            for p in source_files.values():
                p.write_text("synthetic metadata only\n", encoding="utf-8")
            files = {
                "prices": bundle_path, "events": events_path, **source_files}
            manifest = {"schema": "K1_INPUTS_V1",
                "development_window": ["2020-11-27", "2026-10-30"],
                "holdout_loaded": False, "forward_labels_built": False,
                "files": {name: {"path": p.relative_to(k.ROOT).as_posix(),
                                 "sha256": k.sha256_file(p)} for name,p in files.items()}}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with patch.object(k, "INPUTS", bundle_path), patch.object(k, "EVENTS", events_path), \
                 patch.object(k, "RESULTS", results_path), patch.object(k, "ENDPOINT_LOG", endpoints_path):
                output = StringIO()
                with redirect_stdout(output):
                    result = k._execute(execute=True, prereg_path=k.PREREG,
                        run_dir=root / "guard", output_dir=root / "run",
                        prereg_dir=k.PREREG.parent, trial_log=trial_log,
                        analysis_kwargs={"events_path":events_path,"inputs_path":bundle_path,
                            "manifest_path":manifest_path,"holm_path":k.HOLM_CONFIG,
                            "trial_log":trial_log})
            self.assertTrue(results_path.is_file())
            written = json.loads(results_path.read_text(encoding="utf-8"))
            self.assertEqual(written["trial_count"] if "trial_count" in written else
                             written["portfolio"]["trial_count"], 7)
            self.assertEqual(len(written["holm"]), 21)
            self.assertEqual(written["holm"]["R6-H16"]["raw_p"], result["holm"]["R6-H16"]["raw_p"])
            self.assertIn("R6-H21", written["holm"])
            if result["portfolio"] is None:
                self.assertEqual(written["holm_status"]["R6-H21"], "not run")
                self.assertEqual(written["holm"]["R6-H21"]["holm_p"], 1.0)
            else:
                self.assertEqual(written["holm_status"]["R6-H21"], "computed")
            self.assertTrue(endpoints_path.is_file())
            run_result = root / "run" / "K1_RESULTS.json"
            self.assertTrue(run_result.is_file())
            self.assertEqual(json.loads(run_result.read_text(encoding="utf-8"))["status"], result["status"])
            self.assertTrue((root / "guard" / ".k1-run.lock").is_file())
            self.assertIn("| 1 | K1 | K1-V1 |", trial_log.read_text(encoding="utf-8"))
            self.assertIn("result=" + str(run_result), output.getvalue())


if __name__ == "__main__":
    unittest.main()
