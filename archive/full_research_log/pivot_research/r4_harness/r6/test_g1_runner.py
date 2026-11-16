"""Synthetic-only G1 checks; they never open project price inputs."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from r4_harness.phase3 import prereg_digest
from r4_harness.runner_guard import validate_frozen_prereg
from r4_harness.r6 import g1_runner as g1


class G1SyntheticTests(unittest.TestCase):
    def test_frozen_prereg_digest_and_numeric_diff(self):
        date, digest = validate_frozen_prereg(g1.PREREG)
        self.assertEqual(date, "2026-11-11")
        self.assertEqual(digest, "201c2c95137ac3fc0ce139eb539837c823431a74b8959f68a6efd2ddb4bef4e6")
        self.assertTrue(g1.prereg_diff_payload().matches, g1.prereg_diff_payload().differences)
        self.assertEqual(g1.formation_indices(1488).tolist(), list(range(54,1462,21)))
        self.assertEqual(len(g1.formation_indices(1488)), 68)

    def test_fifty_prior_observations_and_five_day_completed_score(self):
        v = np.exp(np.linspace(2.0, 3.0, 60))[None, :]
        hv, valid = g1.high_volume_signal(v)
        self.assertFalse(valid[0,53])
        self.assertTrue(valid[0,54])
        expected_z = []
        for d in range(50,55):
            hist = np.log(v[0,d-50:d])
            expected_z.append((np.log(v[0,d])-hist.mean())/hist.std(ddof=1))
        self.assertAlmostEqual(hv[0,54], float(np.mean(expected_z)), places=12)
        changed = v.copy(); changed[0,54] *= 10
        new_hv, _ = g1.high_volume_signal(changed)
        self.assertGreater(new_hv[0,54], hv[0,54])

    def test_all_nan_baseline_is_ineligible_without_runtime_warning(self):
        v = np.full((2, 60), np.nan)
        v[1] = np.exp(np.linspace(2.0, 3.0, 60))
        with np.errstate(all="raise"):
            hv, valid = g1.high_volume_signal(v)
        self.assertFalse(valid[0].any())
        self.assertTrue(valid[1, 54])
        self.assertTrue(np.isnan(hv[0]).all())

    def test_availability_masks_are_hashed_before_forward_labels(self):
        t=1488; dates=np.array([f"2020-11-{i:02d}" for i in range(t)])
        # Synthetic calendar labels are immaterial here; the runner validates
        # the actual ISO calendar at its input boundary.
        v=np.tile(np.exp(np.linspace(2.,3.,t)),(2,1))
        data={"dates":dates}
        for u in ("sp500","dow"):
            data[f"{u}_roster"]=np.ones((2,t),bool)
            data[f"{u}_volume"]=v.copy()
            data[f"{u}_sic2"]=np.full((2,t),"10",dtype="U2")
            data[f"{u}_adjusted_open"]=np.full((2,t),100.)
            data[f"{u}_adjusted_close"]=np.full((2,t),100.)
        masks=g1.availability_masks(data)
        self.assertTrue(np.all(masks["sp500"]["eligible_counts"]==2))
        self.assertEqual(len(masks["sp500"]["hashes"]["formation_eligibility"]),64)

    def test_coverage_gate_requires_every_fixed_formation_and_250_names(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle, covpath, src = root/"input.npz", root/"coverage.csv", root/"source.bin"
            bundle.write_bytes(b"synthetic input placeholder")
            src.write_bytes(b"synthetic source")
            cov = pd.DataFrame({"universe":["sp500"]*68+["dow"]*68,
              "formation_date":[f"d{i}" for i in range(68)]*2,"eligible_names":[250]*68+[30]*68})
            cov.to_csv(covpath,index=False)
            manifest={"scope":"development-only input panels; no forward labels or outcomes",
              "development_window":["2020-11-27","2026-10-30"],"forward_labels_built":False,
              "holdout_loaded":False,"input_bundle_sha256":g1.sha256(bundle),
              "coverage_sha256":g1.sha256(covpath),"volume_basis":"split_adjusted_share_volume",
              "volume_adjustment":"split factors effective by each session; dividends excluded",
              "source_files":[{"role":role,"path":"specs/r6_prereg/G1.md","sha256":g1.sha256(g1.PREREG)}
                for role in ("sp500_ohlcv","dow_ohlcv","sp500_pit_roster","dow_pit_roster","sic2","split_actions")]}
            manifest["manifest_sha256"] = g1.canonical_manifest_sha256(manifest)
            self.assertTrue(g1.check_coverage(cov,manifest,bundle,covpath)["passed"])
            cov.loc[0,"eligible_names"]=249
            with self.assertRaisesRegex(g1.InputGateError,"coverage gate failed"):
                g1.check_coverage(cov,manifest,bundle,covpath)

    def test_rank_mechanism_and_reproducible_sic2_shuffle(self):
        score=np.tile(np.arange(8,dtype=float)[:,None],(1,6))
        forward=score*.01
        sic=np.array(["10"]*4+["20"]*4)[:,None].repeat(6,axis=1)
        eligible=np.ones_like(score,dtype=bool)
        m=g1.mechanism(score,forward,sic,eligible)
        self.assertGreater(m["mean_ic"],.99)
        self.assertTrue(m["pass"])
        a=g1.sic2_shuffle(score,forward,sic,eligible)
        b=g1.sic2_shuffle(score,forward,sic,eligible)
        self.assertEqual(len(a["draws"]),500)
        np.testing.assert_array_equal(a["draws"],b["draws"])
        self.assertEqual(a["p"],b["p"])

    def test_dow_top_k_uses_available_roster_n_and_only_valid_scores(self):
        score=np.array([5.,4.,3.,2.,1.,0.,-1.,-2.,-3.,-4.])
        roster=np.ones(10,bool); open_ok=np.ones(10,bool)
        valid=np.zeros(10,bool); valid[[1,3,8]]=True
        target,ew,k,selected,active=g1.target_weights(score,valid,roster,open_ok)
        self.assertEqual(k,5)  # n=10 benchmark members, independent of 3 valid signals
        self.assertEqual(selected,3)
        self.assertEqual(set(np.flatnonzero(target)),{1,3,8})
        self.assertAlmostEqual(ew.sum(),1.)
        self.assertGreaterEqual(active,0.)

    def test_turnover_cap_is_total_buys_plus_sells(self):
        old=np.array([1.,0.,0.,0.]); target=np.array([0.,0.,0.,1.])
        new,traded=g1._trade(old,target,np.ones(4,bool))
        self.assertLessEqual(traded,.5+1e-12)
        self.assertAlmostEqual(traded,.5)
        np.testing.assert_allclose(new,[.75,0,0,.25])

    def test_decision63_missing_close_carries_and_catches_up(self):
        t=1488; n=2
        dates=np.array([f"d{i}" for i in range(t)])
        roster=np.ones((n,t),bool); signal=np.vstack([np.ones(t),np.zeros(t)])
        op=np.full((n,t),100.); close=np.full((n,t),100.)
        close[0,60:62]=np.nan; close[0,62]=110.
        result=g1.portfolio(dates,np.array(["A","B"]),roster,signal,op,close)
        start=55
        self.assertAlmostEqual(result["strategy_daily_net"][60-start],0.,places=12)
        self.assertAlmostEqual(result["strategy_daily_net"][61-start],0.,places=12)
        self.assertAlmostEqual(result["strategy_daily_net"][62-start],.075,places=10)

    def test_final_unresolved_stale_position_uses_last_close_fallback(self):
        t=1488; n=2
        dates=np.array([f"d{i}" for i in range(t)])
        roster=np.ones((n,t),bool); signal=np.vstack([np.ones(t),np.zeros(t)])
        op=np.full((n,t),100.); close=np.full((n,t),100.)
        close[0,100:1483]=np.nan
        result=g1.portfolio(dates,np.array(["A","B"]),roster,signal,op,close)
        self.assertEqual(result["terminal_stale_fallback_names"],1)
        self.assertGreater(result["terminal_exit_cost"],0.)

    def test_missing_holm_slots_fail_closed_until_family_is_h1_through_h21(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"holm.json"
            p.write_text(json.dumps({"manifest":["R6-H1"],"p_values":{"R6-H1":.1}}))
            with self.assertRaisesRegex(g1.InputGateError,"H1..H21"):
                g1.holm({"R6-H19":None,"R6-H20":None,"R6-H21":None},p)

    def test_holm_manifest_uses_default_json_list_digest(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"holm.json"
            family=[f"R6-H{i}" for i in range(1,22)]
            digest=hashlib.sha256(json.dumps(family).encode("utf-8")).hexdigest()
            pvals={key:None for key in family}
            p.write_text(json.dumps({"manifest":family,"manifest_sha256":digest,"p_values":pvals}))
            self.assertEqual(g1.validate_holm_family(p)["manifest_sha256"],digest)
            # Confirm the real coordinator-owned family is validated too.
            self.assertEqual(g1.validate_holm_family()["manifest_sha256"],
                             "e3fd2f5bc4baed2bdc6a347839ee05d2c09fa3b35e3bab3fd3a105db8871e230")

    def test_trial_count_reads_both_numbered_and_frozen_variant_rows(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"trials.md"
            p.write_text("- R6 variant 3: J1-V1\n- R6 variant 4: R1-V1\n- G1-V1 FROZEN 2026-11-11 SHA abc (R6-H19..H21)\n- K1-V1 FROZEN 2026-11-11 SHA def (R6-H16..H18)\n")
            self.assertEqual(g1._trial_count(p),4)

    def test_end_to_end_synthetic_analyze_and_report_uses_real_helpers(self):
        """Exercise input gates through result JSON with isolated synthetic data."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            n_dates = 1488
            dates = np.array(["2020-11-27"] + [f"d{i:04d}" for i in range(1,n_dates-1)] + ["2026-10-30"])
            forms = g1.formation_indices(n_dates)

            # Give every row a noisy but stationary baseline, then add a small
            # rank-coded volume impulse at each formation.  Future price drift
            # is also rank-coded so the real mechanism/placebo/portfolio paths
            # all receive finite synthetic outcomes.
            data = {"dates": dates}
            for universe, n in (("sp500", 250), ("dow", 30)):
                ids = np.arange(n)
                t = np.arange(n_dates)
                phase = ids[:, None] * .71
                logv = 5.0 + .05*np.sin(t[None, :]*.13 + phase)
                for f in forms:
                    logv[:, f] += np.linspace(.001, .02, n)
                daily = -0.00015 + ids[:, None] * 0.000012
                price = 100.0 * np.cumprod(1.0 + np.broadcast_to(daily, (n,n_dates)), axis=1)
                for key, value in {
                    "names": np.array([f"{universe}_{i:03d}" for i in ids]),
                    "roster": np.ones((n,n_dates), dtype=bool),
                    # One synthetic SIC2 stratum makes the real shuffle test
                    # destroy the cross-sectional association completely.
                    "sic2": np.full((n,n_dates), "10", dtype="U2"),
                    "volume": np.exp(logv),
                    "adjusted_open": price.copy(),
                    "adjusted_close": price.copy(),
                }.items():
                    data[f"{universe}_{key}"] = value

            inputs = root/"G1_INPUTS.npz"
            np.savez_compressed(inputs, **data)
            masks = g1.availability_masks(data)
            coverage = pd.DataFrame({
                "universe": ["sp500"]*len(forms) + ["dow"]*len(forms),
                "formation_date": list(dates[forms])*2,
                "eligible_names": masks["sp500"]["eligible_counts"].tolist() +
                                  masks["dow"]["eligible_counts"].tolist(),
            })
            coverage_path = root/"formation_coverage.csv"
            coverage.to_csv(coverage_path, index=False)
            manifest_path = root/"build_manifest.json"
            source = g1.PREREG.relative_to(g1.ROOT).as_posix()
            manifest = {
                "manifest_version": 1,
                "scope": "development-only input panels; no forward labels or outcomes",
                "development_window": ["2020-11-27", "2026-10-30"],
                "forward_labels_built": False,
                "holdout_loaded": False,
                "input_bundle_sha256": g1.sha256(inputs),
                "coverage_sha256": g1.sha256(coverage_path),
                "volume_basis": "split_adjusted_share_volume",
                "volume_adjustment": "split factors effective by each session; dividends excluded",
                "source_files": [{"role": role, "path": source, "sha256": g1.sha256(g1.PREREG)}
                    for role in ("sp500_ohlcv", "dow_ohlcv", "sp500_pit_roster", "dow_pit_roster", "sic2", "split_actions")],
            }
            manifest["manifest_sha256"] = g1.canonical_manifest_sha256(manifest)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            family_path = root/"holm.json"
            family = [f"R6-H{i}" for i in range(1,22)]
            pvalues = {key: (.5 if int(key.split("H")[1]) <= 18 else None) for key in family}
            family_path.write_text(json.dumps({"manifest": family,
                "manifest_sha256": hashlib.sha256(json.dumps(family).encode("utf-8")).hexdigest(),
                "p_values": pvalues}), encoding="utf-8")
            trials = root/"trials.md"
            trials.write_text("- G1-V1 FROZEN 2026-11-11 SHA synthetic\n", encoding="utf-8")
            out = root/"run"

            result = g1.analyze_and_report(manifest_path=manifest_path,
                coverage_path=coverage_path, inputs_path=inputs, output_dir=out,
                holm_path=family_path, trial_log=trials)
            result_path = out/"G1_RESULTS.json"
            self.assertTrue(result_path.is_file())
            written = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(written, g1._json_safe(result))
            self.assertEqual(written["variant"], "G1-V1")
            self.assertEqual(len(written["placebo_draws"]), 500)
            self.assertEqual(len(written["holm_family"]), 21)
            self.assertEqual(set(written["holm_family"]["R6-H19"]), {"raw_p", "holm_p", "reject"})
            self.assertEqual(set(written["endpoints"][0]),
                {"endpoint", "raw_p", "raw_gate_pass", "holm_adjusted_p", "holm_reject", "status"})
            self.assertIsNotNone(written["portfolio"],
                f"portfolio gate skipped: mechanism={written['mechanism']['nw_t']}, "
                f"mech_pass={written['mechanism']['pass']}, placebo={written['placebo']}")
            self.assertIn("dsr", written["portfolio"])
            self.assertIn("bootstrap_p_holm", written["portfolio"])
            self.assertTrue((out/"G1_PLACEBO_DRAWS.csv").is_file())
            self.assertTrue((out/"G1_ENDPOINTS.csv").is_file())
            self.assertTrue((out/"MECHANISM_PASS.json").is_file())

    def test_execute_guard_refuses_before_input_or_lock_access(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"run"
            with self.assertRaises(PermissionError):
                g1.run_g1(manifest_path=Path(td)/"missing", coverage_path=Path(td)/"missing2",
                          inputs_path=Path(td)/"missing3", output_dir=out)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
