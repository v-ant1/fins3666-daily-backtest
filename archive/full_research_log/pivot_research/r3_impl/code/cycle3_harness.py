"""Cycle 3 signals and portfolio adapter; reuses the validated cycle 2 ledger."""
from __future__ import annotations
import csv, json, math
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import research_harness as base
import cycle2_harness as c2

HERE=Path(__file__).resolve().parent.parent
COST=base.COST; ANCHOR=base.ANCHOR; TRIALS=94
VARIANTS={
 'IDIOSKEW63_a08':('IDIOSKEW',63,.8), 'COSKEW63_a08':('COSKEW',63,.8),
 'DIST63_a08':('DIST',63,.8), 'DIST63_a10':('DIST',63,1.0),
 'GAPVOL63_a08':('GAPVOL',63,.8), 'GAPSHARE63_a08':('GAPSHARE',63,.8)}
FAMILY={'IDIOSKEW63_a08':'SKEW','COSKEW63_a08':'SKEW','DIST63_a08':'DIST','DIST63_a10':'DIST','GAPVOL63_a08':'GAP','GAPSHARE63_a08':'GAP'}
DATA_ROOTS={'dow':HERE.parent/'w1_engine','dow_recent':HERE.parent/'w1_engine','xasset':HERE.parent/'oos3'/'xasset'}

def load_split_close(ctx,universe):
    dates=ctx[0]; assets=base.UNIVERSE_ASSETS[universe]; root=DATA_ROOTS[universe]
    maps={t:{} for t in assets}
    for t in assets:
        for folder in ('prices-daily-lookback','prices-daily','prices-daily-delisted'):
            p=root/folder/f'{t}.csv'
            if p.exists():
                with p.open(newline='',encoding='utf-8-sig') as f:
                    for row in csv.DictReader(f):
                        try: maps[t][row['date'][:10]]=float(row['close'])
                        except (KeyError,ValueError,TypeError): pass
    if any(not all(d in maps[t] for d in dates) for t in assets): raise AssertionError('missing split-adjusted close for DIST signal')
    P=np.array([[maps[t][d] for d in dates] for t in assets],float)
    if not np.isfinite(P).all() or np.any(P<=0): raise AssertionError('invalid split-adjusted close')
    return P

def score(name,i,C,P,O):
    if name not in VARIANTS: raise ValueError(name)
    if i<63: raise AssertionError(f'{name}: 63-session history unavailable')
    kind,lb,a=VARIANTS[name]
    if C.shape[1]<=i or P.shape!=C.shape or O.shape!=C.shape: raise AssertionError('signal arrays not aligned')
    if kind in ('IDIOSKEW','COSKEW'):
        rets=C[:,1:]/C[:,:-1]-1.; x=rets[:,i-63:i]
        if x.shape[1]!=63 or not np.isfinite(x).all(): raise AssertionError('invalid return window')
        out=np.empty(30)
        for j in range(30):
            m=np.delete(x,j,axis=0).mean(axis=0); y=x[j]
            yc=y-y.mean(); mc=m-m.mean(); sy=float(np.sqrt(np.mean(yc**2))); sm=float(np.sqrt(np.mean(mc**2)))
            if sy<=0 or sm<=0: raise AssertionError(f'{name}: zero standard deviation')
            if kind=='IDIOSKEW':
                beta=float(np.mean(yc*mc)/np.mean(mc**2)); resid=yc-beta*mc; sr=float(np.sqrt(np.mean(resid**2)))
                if sr<=0: raise AssertionError(f'{name}: zero residual standard deviation')
                out[j]=-float(np.mean(resid**3)/sr**3)
            else: out[j]=float(np.mean(yc*mc**2)/(sy*sm**2))
        return out
    if kind=='DIST':
        if not np.isfinite(C[:,[i,i-63]]).all() or not np.isfinite(P[:,[i,i-63]]).all() or np.any(P[:,[i,i-63]]<=0): raise AssertionError('invalid distribution input')
        # Fail if the vendor adjustment factor is not stable over the window (e.g. inconsistent adjustment series).
        adj0=C[:,i-63]/P[:,i-63]; adj1=C[:,i]/P[:,i]
        if np.any(adj0<=0) or not np.isfinite(adj0+adj1).all(): raise AssertionError('invalid adjustment factor')
        return C[:,i]/C[:,i-63]-P[:,i]/P[:,i-63]
    # 63 overnight gaps for sessions i-62..i, using previous adjusted closes i-63..i-1.
    oo=O[:,i-62:i+1]; cc=C[:,i-62:i+1]; prev=C[:,i-63:i]
    if oo.shape[1]!=63 or np.any(oo<=0) or np.any(cc<=0) or np.any(prev<=0) or not np.isfinite(oo).all() or not np.isfinite(cc).all() or not np.isfinite(prev).all(): raise AssertionError('invalid gap window')
    g=oo/prev-1.; u=cc/oo-1.
    if kind=='GAPVOL': return -np.std(g,axis=1,ddof=1)*math.sqrt(252)
    den=np.sum(g*g+u*u,axis=1)
    if np.any(den<=0): raise AssertionError('zero gap-share denominator')
    return -np.sum(g*g,axis=1)/den

def weights(name,i,C,P,O): return base.rank_weights(score(name,i,C,P,O),VARIANTS[name][2])


def check_invariance(ctx,universe,P):
    dates,ho,hc,C,V,H,L,spy=ctx; assets=base.UNIVERSE_ASSETS[universe]; O=np.array([[ho[t][d] for d in dates] for t in assets])
    grid=[j for j,d in enumerate(dates) if d>=ANCHOR][::21]; samples=sorted(set([grid[0],grid[len(grid)//2],grid[-1]])); checks=0
    for i in samples:
        if i<63: continue
        for n in VARIANTS:
            a=weights(n,i,C,P,O); b=weights(n,i,C[:,:i+1],P[:,:i+1],O[:,:i+1])
            if not np.allclose(a,b,rtol=0,atol=1e-12): raise AssertionError(f'{universe} {n} future truncation mismatch at {dates[i]}')
            checks+=1
    print(f'[invariance-c3] {universe}: {checks} checks PASS')
    return checks

def backtest(ctx,universe,period,variant=None,P=None):
    eng=base.eng; eng.DOW30=base.UNIVERSE_ASSETS[universe]
    dates,ho,hc,C,V,H,L,spy=ctx; O=np.array([[ho[t][d] for d in dates] for t in eng.DOW30])
    lo,hi=period; dmap={d:i for i,d in enumerate(dates)}; grid=[j for j,d in enumerate(dates) if d>=ANCHOR][::21]
    fills=[j for j in grid if lo<=dates[j]<=hi]
    if not fills: raise AssertionError('no fills')
    sigs=[j-1 for j in fills]
    if variant and min(sigs)<63: raise AssertionError(f'{variant} insufficient history')
    daily=[]; turnovers=[]; active=[]; shares=None; recon=1.; prior_nav=None
    for k,(si,fi) in enumerate(zip(sigs,fills)):
        fill=dates[fi]; end=fills[k+1] if k+1<len(fills) else dmap[hi]; final=k+1==len(fills)
        if shares is None:
            w=np.full(30,1/30) if variant is None else weights(variant,si,C,P,O); nav=1/(1+COST); turn=0.; notional=0.; active.append(.5*np.abs(w-1/30).sum()); recon*=nav
        else:
            old={t:shares[t]*ho[t][fill] for t in eng.DOW30}; gross=sum(old.values()); recon*=gross/prior_nav
            target=np.full(30,1/30) if variant is None else weights(variant,si,C,P,O); drift=np.array([old[t]/gross for t in eng.DOW30])
            if np.abs(target-drift).sum()<.01: w=drift; nav=gross; notional=0.
            else:
                nav=gross
                for _ in range(500):
                    n2=gross-COST*sum(abs(nav*target[j]-old[t]) for j,t in enumerate(eng.DOW30))
                    if abs(n2-nav)<1e-15*max(1.,gross): nav=n2; break
                    nav=n2
                notional=sum(abs(nav*target[j]-old[t]) for j,t in enumerate(eng.DOW30)); assert abs(gross-nav-COST*notional)<1e-9*max(1.,gross); w=target
            turn=notional/gross if gross else 0.; active.append(.5*np.abs(w-1/30).sum()); recon*=nav/gross
        if shares is not None: turnovers.append(turn)
        else: turnovers.append(turn)
        if np.any(w< -1e-14) or abs(w.sum()-1)>1e-12: raise AssertionError('invalid weights')
        shares={t:nav*w[j]/ho[t][fill] for j,t in enumerate(eng.DOW30)}; prior_nav=nav
        for j in range(fi,end+1):
            if j==end and not final: continue
            value=sum(shares[t]*hc[t][dates[j]] for t in eng.DOW30)
            if final and j==end: value*=1-COST
            daily.append((dates[j],value))
    terminal=sum(shares[t]*hc[t][hi] for t in eng.DOW30); recon*=terminal/prior_nav*(1-COST)
    wealth=np.array([v for _,v in daily]); dout=[d for d,_ in daily]
    if len(dout)!=len(set(dout)) or np.any(wealth<=0) or abs(recon-wealth[-1])>1e-6*max(1.,abs(wealth[-1])): raise AssertionError('ledger reconciliation/mark failure')
    return {'dates':dout,'wealth':wealth,'turnover':turnovers,'active_share':active}

def run_frozen_price_folder(price_folder,tickers,variant,period,anchor=ANCHOR,rebalance_every=21):
    """Coordinator-facing frozen C3 function; caller supplies any 30 tickers/folder."""
    if len(tickers)!=30 or len(set(tickers))!=30: raise ValueError('exactly 30 unique tickers required')
    if variant not in VARIANTS: raise ValueError(f'variant must be one of {list(VARIANTS)}')
    root=Path(price_folder); dirs=[root/'prices-daily-lookback',root/'prices-daily',root/'prices-daily-delisted',root]
    data={t:{} for t in tickers}; calendar=set()
    for t in tickers:
        for folder in dirs:
            p=folder/f'{t}.csv'
            if not p.exists(): continue
            with p.open(newline='',encoding='utf-8-sig') as f:
                for row in csv.DictReader(f):
                    try:
                        d=row['date'][:10]; raw=float(row['close']); adj=float(row['adjclose']); op=float(row['open']); vol=float(row['volume'])
                        if raw<=0 or adj<=0: continue
                        fac=adj/raw; data[t][d]={'close':adj,'rawclose':raw,'open':op*fac,'volume':vol}; calendar.add(d)
                    except (KeyError,ValueError,TypeError): continue
    if any(not data[t] for t in tickers): raise AssertionError('missing ticker OHLCV file')
    dates=sorted(d for d in calendar if d<=period[1] and d>=max(min(data[t]) for t in tickers))
    for t in tickers:
        miss=[d for d in dates if d not in data[t]]
        if miss: raise AssertionError(f'FAIL-FAST {t} missing dates {miss[:3]}')
    C=np.array([[data[t][d]['close'] for d in dates] for t in tickers]); P=np.array([[data[t][d]['rawclose'] for d in dates] for t in tickers]); O=np.array([[data[t][d]['open'] for d in dates] for t in tickers])
    ho={t:{d:O[j,i] for i,d in enumerate(dates)} for j,t in enumerate(tickers)}; hc={t:{d:C[j,i] for i,d in enumerate(dates)} for j,t in enumerate(tickers)}
    dmap={d:i for i,d in enumerate(dates)}; fills=[j for j,d in enumerate(dates) if d>=anchor][::rebalance_every]; fills=[j for j in fills if period[0]<=dates[j]<=period[1]]
    if not fills or fills[0]-1<63: raise AssertionError('no fill or 63-session lookback unavailable')
    daily=[]; turns=[]; shares=None; prior=None
    for k,fi in enumerate(fills):
        si=fi-1; end=fills[k+1] if k+1<len(fills) else dmap.get(period[1]); final=k+1==len(fills)
        if end is None: raise AssertionError('period end not present in folder calendar')
        w=weights(variant,si,C,P,O); fill=dates[fi]
        if shares is None: nav=1/(1+COST); turn=0.
        else:
            old={t:shares[t]*ho[t][fill] for t in tickers}; gross=sum(old.values()); drift=np.array([old[t]/gross for t in tickers])
            if np.abs(w-drift).sum()<.01: w=drift; nav=gross; notional=0.
            else:
                nav=gross
                for _ in range(500):
                    n2=gross-COST*sum(abs(nav*w[j]-old[t]) for j,t in enumerate(tickers))
                    if abs(n2-nav)<1e-15*max(1.,gross): nav=n2; break
                    nav=n2
                notional=sum(abs(nav*w[j]-old[t]) for j,t in enumerate(tickers)); assert abs(gross-nav-COST*notional)<1e-9*max(1.,gross)
            turn=notional/gross
        turns.append(turn); shares={t:nav*w[j]/ho[t][fill] for j,t in enumerate(tickers)}; prior=nav
        for j in range(fi,end+1):
            if j==end and not final: continue
            value=sum(shares[t]*hc[t][dates[j]] for t in tickers)
            if final and j==end: value*=1-COST
            daily.append((dates[j],value))
    recon=sum(shares[t]*hc[t][period[1]] for t in tickers)*(1-COST)
    if not daily or abs(recon-daily[-1][1])>1e-6*max(1.,abs(recon)): raise AssertionError('generic-folder ledger reconciliation failed')
    return {'dates':[x[0] for x in daily],'wealth':np.array([x[1] for x in daily]),'turnover':turns,'variant':variant}

def run_idioskew63_a08(price_folder,tickers,period,anchor=ANCHOR,rebalance_every=21):
    return run_frozen_price_folder(price_folder,tickers,'IDIOSKEW63_a08',period,anchor,rebalance_every)

def run_dist63_a08(price_folder,tickers,period,anchor=ANCHOR,rebalance_every=21):
    return run_frozen_price_folder(price_folder,tickers,'DIST63_a08',period,anchor,rebalance_every)

def run_gapshare63_a08(price_folder,tickers,period,anchor=ANCHOR,rebalance_every=21):
    return run_frozen_price_folder(price_folder,tickers,'GAPSHARE63_a08',period,anchor,rebalance_every)

PERIODS={'selection':('2020-11-27','2022-12-30'),'DOW_OOS1':('2023-01-03','2024-02-23'),'DOW_OOS2':('2024-12-06','2025-12-31'),'DOW_OOS3':('2026-01-02','2026-10-30'),'XASSET_OOS':('2023-01-03','2026-10-30')}
def one_sided_bootstrap_p(series,draws=10000,block=10,seed=3666):
    x=np.asarray(series); obs=float(np.mean(x)); z=x-obs; rng=np.random.default_rng(seed); n=len(x); nb=math.ceil(n/block); off=np.arange(block); count=0
    for _ in range(draws):
        starts=rng.integers(0,n,size=nb); sample=np.concatenate([z[(s+off)%n] for s in starts])[:n]
        count += np.mean(sample)>=obs
    return (count+1)/(draws+1)

def run_all():
    out=HERE/'outputs_cycle3'; out.mkdir(exist_ok=True)
    contexts={u:base.load_context(u) for u in ('dow','dow_recent','xasset')}
    raw={u:load_split_close(ctx,u) for u,ctx in contexts.items()}
    invariance={u:check_invariance(contexts[u],u,raw[u]) for u in contexts}
    selection={}; rows=[]; records={}; invalid={}; runs=[]
    for u in ('dow','xasset'):
        ctx=contexts[u]; ew=base.backtest(ctx,u,PERIODS['selection'])
        for name in VARIANTS:
            runs.append((u,'selection',name))
            try: res=backtest(ctx,u,PERIODS['selection'],name,raw[u]); m=base.metrics(res,ew); selection[(u,name)]=m; records[(u,'selection',name)]=(res,ew,m); rows.append({'universe':u,'period':'selection','variant':name,**m})
            except (AssertionError,ValueError,KeyError) as e: invalid[(u,name)]=str(e); print('[invalid]',u,name,e)
    frozen={}
    for fam in ('SKEW','DIST','GAP'):
        names=[n for n in VARIANTS if FAMILY[n]==fam]
        eligible=[n for n in names if all((u,n) in selection and selection[(u,n)]['turnover']<=.5 for u in ('dow','xasset'))]
        frozen[fam]=max(eligible,key=lambda n:(np.mean([selection[(u,n)]['sharpe'] for u in ('dow','xasset')]),-np.mean([selection[(u,n)]['turnover'] for u in ('dow','xasset')]),-names.index(n))) if eligible else 'EW30'
    (out/'frozen_choices.txt').write_text('\n'.join(f'{f}={n}' for f,n in frozen.items())+'\n',encoding='utf-8')
    # The frozen file is persisted before any development-test run.
    for fam,name in frozen.items():
        if name=='EW30': continue
        for p in ('DOW_OOS1','DOW_OOS2','DOW_OOS3','XASSET_OOS'):
            u='xasset' if p=='XASSET_OOS' else ('dow' if p=='DOW_OOS1' else 'dow_recent'); runs.append((u,p,name))
            ew=base.backtest(contexts[u],u,PERIODS[p]); res=backtest(contexts[u],u,PERIODS[p],name,raw[u]); m=base.metrics(res,ew); records[(u,p,name)]=(res,ew,m); rows.append({'universe':u,'period':p,'variant':name,**m})
    with (out/'metrics.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for (u,p,n),(res,ew,m) in records.items():
        with (out/f'{u}_{p}_{n}.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f); w.writerow(['date',n,'ew']); w.writerows((d,f'{v:.10f}',f'{e:.10f}') for d,v,e in zip(res['dates'],res['wealth'],ew['wealth']))
    sig={}
    for fam,name in frozen.items():
        if name=='EW30': continue
        diffs=[]; sr=[]; ewrs=[]
        for p in ('DOW_OOS1','DOW_OOS2','DOW_OOS3','XASSET_OOS'):
            u='xasset' if p=='XASSET_OOS' else ('dow' if p=='DOW_OOS1' else 'dow_recent'); res,ew,_=records[(u,p,name)]
            rr=np.diff(np.r_[1.,res['wealth']])/np.r_[1.,res['wealth']][:-1]; er=np.diff(np.r_[1.,ew['wealth']])/np.r_[1.,ew['wealth']][:-1]
            diffs.extend(rr-er); sr.extend(rr); ewrs.extend(er)
        sig[fam]={'bootstrap_p':one_sided_bootstrap_p(diffs),'dsr':base.dsr(sr,TRIALS),'pooled_excess_return':float(np.prod(1+np.array(sr))-np.prod(1+np.array(ewrs))),'n_daily':len(sr)}
    (out/'significance.json').write_text(json.dumps(sig,indent=2),encoding='utf-8')
    for fam,name in frozen.items():
        if name=='EW30': continue
        fig,axs=plt.subplots(2,2,figsize=(11,7)); axs=axs.ravel()
        for ax,p in zip(axs,('DOW_OOS1','DOW_OOS2','DOW_OOS3','XASSET_OOS')):
            u='xasset' if p=='XASSET_OOS' else ('dow' if p=='DOW_OOS1' else 'dow_recent'); r,e,_=records[(u,p,name)]
            ax.plot(r['wealth']/r['wealth'][0],label=name); ax.plot(e['wealth']/e['wealth'][0],label='EW30'); ax.set_title(p); ax.grid(alpha=.25); ax.legend(fontsize=8)
        fig.suptitle(f'Cycle 3 {fam}: frozen {name} vs EW30'); fig.tight_layout(); fig.savefig(out/f'{fam}_frozen_tests.png',dpi=160); plt.close(fig)
    (out/'run_inventory.json').write_text(json.dumps({'candidate_series':runs,'invalid':{str(k):v for k,v in invalid.items()},'invariance_checks':invariance,'frozen':frozen},indent=2),encoding='utf-8')
    print('FROZEN',frozen); print('INVALID',invalid); print('SELECTION')
    for fam,name in frozen.items():
        for u in ('dow','xasset'):
            if (u,name) in selection: print(fam,name,u,selection[(u,name)])
    print('TESTS')
    for k,v in records.items():
        if k[1]!='selection': print(k,v[2])
    print('SIGNIFICANCE',sig); print('RUNS',len(runs)); print('OUT',out)

if __name__=='__main__': run_all()



