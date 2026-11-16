import json
import tempfile
import unittest
from pathlib import Path
import numpy as np

from r4_harness.phase3 import (
    append_trial, assert_future_truncation_invariant, config_digest,
    break_even_rank_ic, circular_block_bootstrap_pvalue, cross_sectional_ic, event_study, holm_correction, network_placebos,
    portfolio_engine, prereg_digest, run_holdout, run_registered_trial,
    signal_matrix, _degree_preserving_cube,
)


class MechanismTests(unittest.TestCase):
    def test_break_even_rank_ic_matches_l1_reconciliation(self):
        # L1 mean incremental total-notional turnover vs EW and weekly return dispersion.
        hurdle=break_even_rank_ic(1.5875067664083777,0.03007510102898867,
                                  cost_per_side=0.0005,top_fraction=5/30)
        self.assertAlmostEqual(hurdle,0.01828517466410752,places=12)
        print(f'PASS cost break-even helper matches L1 reconciliation (IC={hurdle:.5f})')

    def test_planted_rank_effect_is_detected_and_null_is_not(self):
        rng=np.random.default_rng(44); n,t=30,650
        r=rng.normal(0,.01,(n,t)); close=np.cumprod(np.c_[np.ones(n),1+r],axis=1)
        planted=r+.01*rng.normal(size=(n,t)); null=rng.normal(size=(n,t))
        planted_scores=np.c_[planted,np.full(n,np.nan)]; null_scores=np.c_[null,np.full(n,np.nan)]
        p=cross_sectional_ic(planted_scores,close,[1])[0]
        z=cross_sectional_ic(null_scores,close,[1])[0]
        self.assertGreater(p.mean_ic,.2); self.assertGreater(p.nw_t,5)
        self.assertLess(abs(z.nw_t),2.0)
        print(f'PASS planted IC detected (mean={p.mean_ic:.3f}, NW t={p.nw_t:.2f}); null not detected (t={z.nw_t:.2f})')

    def test_event_study_detects_linked_neighbour_response(self):
        rng=np.random.default_rng(55); n,t=20,420
        r=rng.normal(0,.005,(n,t)); net=np.zeros((t+1,n,n)); events=[]
        for ti in range(10,t-5,15):
            src=(ti//15)%n; events.append({'source':src,'date':ti})
            for peer in ((src+1)%n,(src+2)%n):
                net[ti,src,peer]=1
                r[peer,ti:ti+3]+=.012
        close=np.cumprod(np.c_[np.ones(n),1+r],axis=1)
        result=event_study(events,net,close,[3])[0]
        self.assertGreater(result.mean_car,.02); self.assertGreater(result.nw_t,2)
        print(f'PASS planted event response detected (CAR={result.mean_car:.3f}, NW t={result.nw_t:.2f})')

    def test_placebos_preserve_degrees_and_return_all_families(self):
        rng=np.random.default_rng(2); n,t=12,30; net=np.zeros((t,n,n))
        for d in range(t):
            for i in range(n):
                j=(i+1)%n; net[d,i,j]=net[d,j,i]=1
        rewired=_degree_preserving_cube(net,np.random.default_rng(4))
        self.assertTrue(np.array_equal(np.sum(net>0,axis=2),np.sum(rewired>0,axis=2)))
        def edge_stat(g): return float(np.mean(np.sum(g>0,axis=2)))
        out=network_placebos(net,edge_stat,n_draws=25,seed=10)
        self.assertEqual(set(out),{'degree_preserving','random_links','time_shifted'})
        self.assertEqual(out['degree_preserving'].draws,25)
        print('PASS network placebo engine (degree-preserving, random-link and time-shifted families)')

    def test_costed_long_only_and_long_short_portfolios(self):
        rng=np.random.default_rng(9); n,t=20,100
        r=rng.normal(0,.01,(n,t)); scores=r+.01*rng.normal(size=(n,t))
        close=np.cumprod(np.c_[np.ones(n),1+r],axis=1); op=close.copy(); scores=np.c_[scores,np.full(n,np.nan)]
        fills=list(range(2,t-2,5))
        for design in ('long_only','long_short'):
            result=portfolio_engine(scores,op,close,fills,design=design,n_long=4,n_short=4,bootstrap_draws=100,seed=3,trial_count=30)
            self.assertLess(result.strategy_net['cumulative_return'],result.strategy_gross['cumulative_return'])
            self.assertGreaterEqual(result.strategy_net['turnover'],0)
            self.assertGreaterEqual(result.deflated_sharpe,0); self.assertLessEqual(result.deflated_sharpe,1)
        print('PASS long-only and dollar-neutral portfolio engines with actual-trade costs')


class GovernanceTests(unittest.TestCase):
    def test_centered_block_bootstrap_effect_and_null(self):
        rng=np.random.default_rng(97); zero=np.zeros(1200)
        effect=.002+rng.normal(0,.005,1200); null=rng.normal(0,.005,1200); null-=null.mean()
        p_effect,_=circular_block_bootstrap_pvalue(effect,zero,n_draws=500,seed=1)
        p_null,_=circular_block_bootstrap_pvalue(null,zero,n_draws=500,seed=1)
        self.assertLess(p_effect,.05); self.assertGreater(p_null,.05)
        print(f'PASS centered 10-day block bootstrap detects planted edge (p={p_effect:.3f}) and retains null (p={p_null:.3f})')

    def test_trial_gate_frozen_hash_and_future_truncation(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root,prefix='.test_') as td:
            base=Path(td); preregs=base/'specs'/'r4_prereg'; preregs.mkdir(parents=True)
            p=preregs/'toy.md'; content='# prereg\nFROZEN: 2026-11-10\nSHA256: placeholder\n'
            content=content.replace('placeholder',prereg_digest(content))
            p.write_text(content,encoding='utf-8')
            log=base/'r4_trials.md'; log.write_text('# trials\n| # | Approach | Variant | Pre-reg file | Date | Result |\n|---|---|---|---|---|---|\n\n## Holdout integrity log\n',encoding='utf-8')
            value=run_registered_trial('toy','v1',lambda:17,prereg_dir=preregs,trial_log=log,trial_date='2026-11-10')
            self.assertEqual(value,17); self.assertIn('| 1 | toy | v1 |',log.read_text(encoding='utf-8'))
            called=[]
            with self.assertRaises(FileNotFoundError):
                run_registered_trial('missing','v1',lambda:called.append(True),prereg_dir=preregs,trial_log=log)
            self.assertFalse(called)
            p.write_text(content.replace('# prereg','# tampered'),encoding='utf-8')
            with self.assertRaises(ValueError):
                run_registered_trial('toy','v2',lambda:called.append(True),prereg_dir=preregs,trial_log=log)
            self.assertFalse(called)
            data=np.arange(24).reshape(2,12)
            fn=lambda d,i:d[:,:i+1].sum(axis=1)
            trunc=lambda d,i:np.c_[d[:,:i+1],np.full((d.shape[0],d.shape[1]-i-1),np.nan)]
            assert_future_truncation_invariant(fn,data,5,trunc)
        print('PASS frozen prereg hash required before run, in-folder trial log fixture, and future-truncation check')

    def test_holdout_runner_rejects_development_and_non_coordinator(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); preregs=root/'specs'/'r4_prereg'; preregs.mkdir(parents=True)
            body='FROZEN: 2026-11-10\nSHA256: placeholder\n'; (preregs/'toy.md').write_text(body.replace('placeholder',prereg_digest(body)),encoding='utf-8')
            config={'approach':'toy','prereg_dir':str(preregs),'frozen_date':'2026-11-10'}; config['sha256']=config_digest(config)
            cfg=root/'config.json'; cfg.write_text(json.dumps(config),encoding='utf-8')
            with self.assertRaises(PermissionError): run_holdout(cfg,root/'repo'/'dev',lambda c,p:1,caller_role='coordinator')
            with self.assertRaises(PermissionError): run_holdout(cfg,root/'fake_holdout',lambda c,p:1,caller_role='worker')
        print('PASS holdout entry point rejects development folders and non-coordinator calls')

    def test_holm_adjustment(self):
        h=holm_correction({'a':.01,'b':.04,'c':.03})
        self.assertAlmostEqual(h['a']['holm_p'],.03)
        self.assertAlmostEqual(h['b']['holm_p'],.06)
        self.assertAlmostEqual(h['c']['holm_p'],.06)

    def test_signal_function_adapter(self):
        a=['A','B']; d=[0,1,2]; data={'A':[1,2,3],'B':[4,5,6]}
        m=signal_matrix(lambda asset,day,x:x[asset][day],a,d,data)
        np.testing.assert_array_equal(m,[[1,2,3],[4,5,6]])


if __name__=='__main__': unittest.main(verbosity=2)
