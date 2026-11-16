"""Cycle 4 event/calendar strategies on the reusable validated backtest harness."""
from __future__ import annotations
import csv, json, math
from pathlib import Path
from datetime import date
import numpy as np
import matplotlib.pyplot as plt
import research_harness as base
import cycle3_harness as c3

HERE=Path(__file__).resolve().parent.parent
COST=base.COST; ANCHOR=base.ANCHOR; TRIALS=98
VARIANTS={'HVOL21_K15':('HVOL',1.5),'HVOL21_K20':('HVOL',2.0),
          'WEEKDAY63_SHR10':('WEEKDAY',1.0),'MONTHPHASE63_SHR10':('MONTHPHASE',1.0)}
FAMILY={'HVOL21_K15':'HVOL','HVOL21_K20':'HVOL','WEEKDAY63_SHR10':'WEEKDAY','MONTHPHASE63_SHR10':'MONTHPHASE'}
DATA_ROOTS=c3.DATA_ROOTS
PERIODS={'selection':('2020-11-27','2022-12-30'),'DOW_OOS1':('2023-01-03','2024-02-23'),
'DOW_OOS2':('2024-12-06','2025-12-31'),'DOW_OOS3':('2026-01-02','2026-10-30'),'XASSET_OOS':('2023-01-03','2026-10-30')}

def easter_sunday(year):
    a=year%19; b=year//100; c=year%100; d=b//4; e=b%4; f=(b+8)//25; g=(b-f+1)//3
    h=(19*a+b-d-g+15)%30; i=c//4; k=c%4; ell=(32+2*e+2*i-h-k)%7; m=(a+11*h+22*ell)//451
    month=(h+ell-7*m+114)//31; day=((h+ell-7*m+114)%31)+1
    return date(year,month,day)

def observed(d):
    if d.weekday()==5: return d.replace(day=d.day-1)
    if d.weekday()==6: return d.replace(day=d.day+1)
    return d

def market_holidays(year):
    from datetime import timedelta
    def nth_weekday(month,w,n):
        first=date(year,month,1); return first+timedelta(days=(w-first.weekday())%7+7*(n-1))
    def last_weekday(month,w):
        import calendar as calmod
        last=date(year,month,calmod.monthrange(year,month)[1]); return last-timedelta(days=(last.weekday()-w)%7)
    fixed={observed(date(year,1,1)),observed(date(year,7,4)),observed(date(year,12,25))}
    if year>=2022: fixed.add(observed(date(year,6,19)))
    return fixed|{nth_weekday(1,0,3),nth_weekday(2,0,3),easter_sunday(year)-timedelta(days=2),last_weekday(5,0),nth_weekday(9,0,1),nth_weekday(11,3,4)}

def extend_known_sessions(dates,needed=24):
    from datetime import timedelta
    out=list(dates); d=date.fromisoformat(out[-1]); holidays=set()
    while len(out)<len(dates)+needed:
        d+=timedelta(days=1); holidays.update(market_holidays(d.year))
        if d.weekday()<5 and d not in holidays: out.append(d.isoformat())
    return out

def load_calendar(ctx,universe):
    dates=ctx[0]; root=DATA_ROOTS['dow_recent'] if universe=='dow' else DATA_ROOTS[universe]; allcal=set()
    for folder in ('prices-daily-lookback','prices-daily'):
        p=root/folder/'SPY.csv'
        if p.exists():
            with p.open(newline='',encoding='utf-8-sig') as f: allcal.update(r['date'][:10] for r in csv.DictReader(f) if r.get('date'))
    later=sorted(d for d in allcal if d>dates[-1])
    return extend_known_sessions(list(dates)+later)

def load_raw_close(ctx,universe):
    dates=ctx[0]; assets=base.UNIVERSE_ASSETS[universe]; root=DATA_ROOTS[universe]; data={t:{} for t in assets}
    for t in assets:
        for folder in ('prices-daily-lookback','prices-daily','prices-daily-delisted'):
            p=root/folder/f'{t}.csv'
            if p.exists():
                with p.open(newline='',encoding='utf-8-sig') as f:
                    for row in csv.DictReader(f):
                        try: data[t][row['date'][:10]]=float(row['close'])
                        except (KeyError,ValueError,TypeError): pass
    if any(any(d not in data[t] for d in dates) for t in assets): raise AssertionError('raw close missing in supplied inputs')
    P=np.array([[data[t][d] for d in dates] for t in assets],float)
    if not np.isfinite(P).all() or np.any(P<=0): raise AssertionError('invalid raw close matrix')
    return P

def score(name,i,C,P,V,dates):
    if name not in VARIANTS: raise ValueError(name)
    kind,param=VARIANTS[name]; n=C.shape[0]
    if n!=30 or C.shape!=P.shape or C.shape!=V.shape or C.shape[1]>len(dates): raise AssertionError('unaligned 30-asset signal matrices')
    if kind=='HVOL':
        if i<103: raise AssertionError(f'{name}: 104-row event history unavailable')
        dollar=P*V
        if not np.isfinite(dollar[:,i-103:i+1]).all() or np.any(dollar[:,i-103:i+1]<=0): raise AssertionError(f'{name}: invalid dollar-volume history')
        out=np.empty(n)
        for a in range(n):
            labels=[]
            for d in range(i-83,i-20):
                baseline=float(np.median(dollar[a,d-20:d]))
                if baseline<=0 or not np.isfinite(baseline): raise AssertionError(f'{name}: invalid shock baseline')
                shock=dollar[a,d]/baseline
                if shock>=param:
                    labels.append(C[a,d+21]/C[a,d]-1.)
            if len(labels)<5: raise AssertionError(f'{name}: only {len(labels)} qualifying events for asset index {a} at {dates[i]}')
            out[a]=float(np.mean(labels))
        return out
    if i<63: raise AssertionError(f'{name}: 63-return history unavailable')
    rets=C[:,1:]/C[:,:-1]-1.; x=rets[:,i-63:i]
    if x.shape[1]!=63 or not np.isfinite(x).all(): raise AssertionError(f'{name}: incomplete return history')
    # Return columns i-63..i-1 correspond to session dates i-62..i.
    sample_dates=dates[i-62:i+1]
    if len(sample_dates)!=63: raise AssertionError(f'{name}: insufficient date labels')
    market=x.mean(axis=0); resid=x-market[None,:]
    if kind=='WEEKDAY':
        wd=np.array([date.fromisoformat(d).weekday() for d in sample_dates]); scores=np.empty(n)
        for a in range(n):
            shrunk=[]
            for w in range(5):
                z=resid[a,wd==w]; count=len(z)
                if count<8: raise AssertionError(f'{name}: weekday {w} has only {count} observations')
                shrunk.append((count/(count+10.))*float(np.mean(z)))
            scores[a]=float(np.mean(shrunk))
        return scores
    if kind=='MONTHPHASE':
        day=np.array([date.fromisoformat(d).day for d in sample_dates]); scores=np.empty(n)
        if i+22>len(dates): raise AssertionError(f'{name}: 21 future session dates unavailable')
        futday=[date.fromisoformat(d).day for d in dates[i+1:i+22]]
        nf=sum(d<=15 for d in futday); nl=21-nf
        for a in range(n):
            first=resid[a,day<=15]; last=resid[a,day>15]
            if len(first)<15 or len(last)<15: raise AssertionError(f'{name}: phase counts {len(first)}/{len(last)} below 15')
            sf=(len(first)/(len(first)+10.))*float(first.mean()); sl=(len(last)/(len(last)+10.))*float(last.mean())
            scores[a]=(nf*sf+nl*sl)/21.
        return scores
    raise ValueError(kind)

def weights(name,i,C,P,V,dates): return base.rank_weights(score(name,i,C,P,V,dates),1.0)

def check_invariance(ctx,universe,P,calendar):
    dates,ho,hc,C,V,H,L,spy=ctx; grid=[j for j,d in enumerate(dates) if d>=ANCHOR][::21]
    # Use selection-period signal dates only, so these technical checks do not guide test-period selection.
    candidates=[i-1 for i in grid if PERIODS['selection'][0]<=dates[i]<=PERIODS['selection'][1] and i>0]
    checks={}; invalid={}
    for name in VARIANTS:
        valid=[]; failures=[]
        req=103 if VARIANTS[name][0]=='HVOL' else 63
        for i in candidates:
            if i<req or i+22>len(calendar): continue
            try: score(name,i,C,P,V,calendar)
            except AssertionError as e: failures.append((dates[i],str(e))); continue
            valid.append(i)
        if not valid:
            checks[name]=0; invalid[name]=failures[:3]
            print(f'[invariance-c4] {universe}/{name}: no valid selection signal date; candidate validation will determine eligibility')
            continue
        samples=sorted(set([valid[0],valid[len(valid)//2],valid[-1]])); count=0
        for i in samples:
            full=weights(name,i,C,P,V,calendar)
            # Keep known calendar dates for phase counts; truncate all prices/volumes at the signal close.
            trunc=weights(name,i,C[:,:i+1],P[:,:i+1],V[:,:i+1],calendar)
            if not np.allclose(full,trunc,rtol=0,atol=1e-12): raise AssertionError(f'{universe}/{name} future-price truncation mismatch at {dates[i]}')
            count+=1
        checks[name]=count
        if failures: invalid[name]=failures[:3]
        print(f'[invariance-c4] {universe}/{name}: {count} comparisons PASS at {[dates[i] for i in samples]}')
    return {'checks':checks,'invalid_signal_samples':invalid}

def backtest_arrays(dates,assets,ho,hc,C,P,V,period,variant=None,calendar=None):
    if calendar is None: calendar=dates
    lo,hi=period; dmap={d:i for i,d in enumerate(dates)}
    grid=[j for j,d in enumerate(dates) if d>=ANCHOR][::21]; fills=[j for j in grid if lo<=dates[j]<=hi]
    if not fills: raise AssertionError(f'no scheduled fills in {period}')
    sigs=[fi-1 for fi in fills]; req=103 if variant and VARIANTS[variant][0]=='HVOL' else 63
    if variant and min(sigs)<req: raise AssertionError(f'{variant}: history unavailable at first fill')
    daily=[]; turns=[]; active=[]; shares=None; prior_nav=None
    for k,(si,fi) in enumerate(zip(sigs,fills)):
        fill=dates[fi]; end=fills[k+1] if k+1<len(fills) else dmap[hi]; final=k+1==len(fills)
        target=np.full(30,1/30) if variant is None else weights(variant,si,C,P,V,calendar)
        if shares is None: w=target; nav=1/(1+COST); turn=0.
        else:
            old={t:shares[t]*ho[t][fill] for t in assets}; gross=sum(old.values()); drift=np.array([old[t]/gross for t in assets])
            if np.abs(target-drift).sum()<.01: w=drift; nav=gross; notional=0.
            else:
                nav=gross
                for _ in range(500):
                    nxt=gross-COST*sum(abs(nav*target[j]-old[t]) for j,t in enumerate(assets))
                    if abs(nxt-nav)<1e-15*max(1.,gross): nav=nxt; break
                    nav=nxt
                notional=sum(abs(nav*target[j]-old[t]) for j,t in enumerate(assets)); assert abs(gross-nav-COST*notional)<1e-9*max(1.,gross); w=target
            turn=notional/gross if gross else 0.
        if np.any(w< -1e-14) or abs(w.sum()-1)>1e-12: raise AssertionError('invalid weights')
        turns.append(turn); active.append(.5*np.abs(w-1/30).sum()); shares={t:nav*w[j]/ho[t][fill] for j,t in enumerate(assets)}; prior_nav=nav
        for j in range(fi,end+1):
            if j==end and not final: continue
            value=sum(shares[t]*hc[t][dates[j]] for t in assets)
            if final and j==end: value*=1-COST
            daily.append((dates[j],value))
    terminal=sum(shares[t]*hc[t][hi] for t in assets)*(1-COST)
    wealth=np.array([v for _,v in daily]); outdates=[d for d,_ in daily]
    if not daily or len(outdates)!=len(set(outdates)) or np.any(wealth<=0) or abs(terminal-wealth[-1])>1e-6*max(1.,abs(terminal)): raise AssertionError('share-ledger reconciliation failed')
    return {'dates':outdates,'wealth':wealth,'turnover':turns,'active_share':active}

def backtest(ctx,universe,period,variant=None,P=None,calendar=None):
    dates,ho,hc,C,V,H,L,spy=ctx; return backtest_arrays(dates,base.UNIVERSE_ASSETS[universe],ho,hc,C,P,V,period,variant,calendar)

def run_frozen_price_folder(price_folder,tickers,variant,period,anchor=ANCHOR,rebalance_every=21):
    """Generic cycle-4 function for a flat or engine-style folder, with caller's 30 tickers and SPY calendar."""
    if len(tickers)!=30 or len(set(tickers))!=30: raise ValueError('exactly 30 unique tickers required')
    if variant not in VARIANTS: raise ValueError(f'variant must be one of {list(VARIANTS)}')
    root=Path(price_folder); dirs=[root/'prices-daily-lookback',root/'prices-daily',root/'prices-daily-delisted',root]
    data={t:{} for t in tickers}
    for t in tickers:
        for folder in dirs:
            p=folder/f'{t}.csv'
            if p.exists():
                with p.open(newline='',encoding='utf-8-sig') as f:
                    for row in csv.DictReader(f):
                        try:
                            d=row['date'][:10]; raw=float(row['close']); adj=float(row['adjclose']); op=float(row['open']); vol=float(row['volume'])
                            if raw>0 and adj>0: data[t][d]={'raw':raw,'adj':adj,'open':op*adj/raw,'volume':vol}
                        except (KeyError,ValueError,TypeError): pass
    if any(not data[t] for t in tickers): raise AssertionError('missing ticker price CSV')
    calendar=set()
    for folder in dirs:
        p=folder/'SPY.csv'
        if p.exists():
            with p.open(newline='',encoding='utf-8-sig') as f: calendar.update(r['date'][:10] for r in csv.DictReader(f) if r.get('date'))
    if not calendar: calendar=set.union(*(set(data[t]) for t in tickers))
    start=max(min(data[t]) for t in tickers); all_calendar=sorted(d for d in calendar if d>=start); dates=[d for d in all_calendar if d<=period[1]]; all_sessions=extend_known_sessions(all_calendar)
    for t in tickers:
        missing=[d for d in dates if d not in data[t]]
        if missing: raise AssertionError(f'FAIL-FAST {t} missing sessions {missing[:3]}')
    C=np.array([[data[t][d]['adj'] for d in dates] for t in tickers]); P=np.array([[data[t][d]['raw'] for d in dates] for t in tickers]); V=np.array([[data[t][d]['volume'] for d in dates] for t in tickers])
    ho={t:{d:data[t][d]['open'] for d in dates} for t in tickers}; hc={t:{d:data[t][d]['adj'] for d in dates} for t in tickers}
    lo,hi=period; grid=[j for j,d in enumerate(dates) if d>=anchor][::rebalance_every]; fills=[j for j in grid if lo<=dates[j]<=hi]
    if not fills: raise AssertionError('no scheduled fills in caller folder')
    # generic call uses requested anchor/schedule via shared defaults; non-default schedule is intentionally rejected.
    if anchor!=ANCHOR or rebalance_every!=21: raise ValueError('cycle-4 schedule is fixed at the registered anchor and 21 sessions')
    return backtest_arrays(dates,tickers,ho,hc,C,P,V,period,variant,all_sessions)

def run_hvol21_k15(price_folder,tickers,period,anchor=ANCHOR,rebalance_every=21): return run_frozen_price_folder(price_folder,tickers,'HVOL21_K15',period,anchor,rebalance_every)
def run_hvol21_k20(price_folder,tickers,period,anchor=ANCHOR,rebalance_every=21): return run_frozen_price_folder(price_folder,tickers,'HVOL21_K20',period,anchor,rebalance_every)
def run_weekday63_shr10(price_folder,tickers,period,anchor=ANCHOR,rebalance_every=21): return run_frozen_price_folder(price_folder,tickers,'WEEKDAY63_SHR10',period,anchor,rebalance_every)
def run_monthphase63_shr10(price_folder,tickers,period,anchor=ANCHOR,rebalance_every=21): return run_frozen_price_folder(price_folder,tickers,'MONTHPHASE63_SHR10',period,anchor,rebalance_every)

def one_sided_bootstrap_p(series,draws=10000,block=10,seed=3666):
    x=np.asarray(series); obs=float(np.mean(x)); z=x-obs; rng=np.random.default_rng(seed); n=len(x); nb=math.ceil(n/block); off=np.arange(block); count=0
    for _ in range(draws):
        starts=rng.integers(0,n,size=nb); sample=np.concatenate([z[(s+off)%n] for s in starts])[:n]; count += np.mean(sample)>=obs
    return (count+1)/(draws+1)

def synthetic_invariance():
    from datetime import timedelta
    rng=np.random.default_rng(44); nday=260; ds=[]; d=date(2020,1,1)
    while len(ds)<nday:
        if d.weekday()<5: ds.append(d.isoformat())
        d+=timedelta(days=1)
    rets=rng.normal(.0002,.01,(30,nday)); C=100*np.cumprod(1+rets,axis=1); P=C.copy(); V=np.full((30,nday),10000.)
    i=160
    for day in range(i-83,i-20,7): V[:,day]=V[:,day-20:day].mean(axis=1)*25
    out={}
    for name in VARIANTS:
        full=weights(name,i,C,P,V,ds); trunc=weights(name,i,C[:,:i+1],P[:,:i+1],V[:,:i+1],ds)
        if not np.allclose(full,trunc,rtol=0,atol=1e-12): raise AssertionError(f'synthetic future-truncation mismatch: {name}')
        out[name]=True
    print('[invariance-c4-synthetic] all four formula checks PASS')
    return out

def run_all():
    out=HERE/'outputs_cycle4'; out.mkdir(exist_ok=True); synthetic=synthetic_invariance()
    contexts={u:base.load_context(u) for u in ('dow','dow_recent','xasset')}; P={u:load_raw_close(contexts[u],u) for u in contexts}; calendars={u:load_calendar(contexts[u],u) for u in contexts}
    invariance={u:check_invariance(contexts[u],u,P[u],calendars[u]) for u in contexts}
    selection={}; rows=[]; records={}; invalid={}; runs=[]
    for u in ('dow','xasset'):
        ctx=contexts[u]; ew=base.backtest(ctx,u,PERIODS['selection'])
        for name in VARIANTS:
            runs.append((u,'selection',name))
            try:
                res=backtest(ctx,u,PERIODS['selection'],name,P[u],calendars[u]); m=base.metrics(res,ew); selection[(u,name)]=m; records[(u,'selection',name)]=(res,ew,m); rows.append({'universe':u,'period':'selection','variant':name,**m})
            except (AssertionError,ValueError,KeyError) as e: invalid[(u,name)]=str(e); print('[invalid-selection]',u,name,str(e))
    frozen={}
    for fam in ('HVOL','WEEKDAY','MONTHPHASE'):
        names=[n for n in VARIANTS if FAMILY[n]==fam]; eligible=[n for n in names if all((u,n) in selection and selection[(u,n)]['turnover']<=.5 for u in ('dow','xasset'))]
        frozen[fam]=max(eligible,key=lambda n:(np.mean([selection[(u,n)]['sharpe'] for u in ('dow','xasset')]),-np.mean([selection[(u,n)]['turnover'] for u in ('dow','xasset')]),-names.index(n))) if eligible else 'EW30'
    (out/'frozen_choices.txt').write_text('\n'.join(f'{f}={n}' for f,n in frozen.items())+'\n',encoding='utf-8')
    # The choices are persisted before any development test series is computed.
    for fam,name in frozen.items():
        if name=='EW30': continue
        for p in ('DOW_OOS1','DOW_OOS2','DOW_OOS3','XASSET_OOS'):
            u='xasset' if p=='XASSET_OOS' else ('dow' if p=='DOW_OOS1' else 'dow_recent'); runs.append((u,p,name))
            ew=base.backtest(contexts[u],u,PERIODS[p]); res=backtest(contexts[u],u,PERIODS[p],name,P[u],calendars[u]); m=base.metrics(res,ew); records[(u,p,name)]=(res,ew,m); rows.append({'universe':u,'period':p,'variant':name,**m})
    with (out/'metrics.csv').open('w',newline='',encoding='utf-8') as f: w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for (u,p,n),(res,ew,m) in records.items():
        with (out/f'{u}_{p}_{n}.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f); w.writerow(['date',n,'ew']); w.writerows((d,f'{v:.10f}',f'{e:.10f}') for d,v,e in zip(res['dates'],res['wealth'],ew['wealth']))
    sig={}
    for fam,name in frozen.items():
        if name=='EW30': continue
        diffs=[]; sr=[]; ewrs=[]
        for p in ('DOW_OOS1','DOW_OOS2','DOW_OOS3','XASSET_OOS'):
            u='xasset' if p=='XASSET_OOS' else ('dow' if p=='DOW_OOS1' else 'dow_recent'); res,ew,_=records[(u,p,name)]
            rr=np.diff(np.r_[1.,res['wealth']])/np.r_[1.,res['wealth']][:-1]; er=np.diff(np.r_[1.,ew['wealth']])/np.r_[1.,ew['wealth']][:-1]; diffs.extend(rr-er); sr.extend(rr); ewrs.extend(er)
        sig[fam]={'bootstrap_p':one_sided_bootstrap_p(diffs),'dsr':base.dsr(sr,TRIALS),'pooled_excess_return':float(np.prod(1+np.array(sr))-np.prod(1+np.array(ewrs))),'n_daily':len(sr)}
    (out/'significance.json').write_text(json.dumps(sig,indent=2),encoding='utf-8')
    for fam,name in frozen.items():
        if name=='EW30': continue
        fig,axs=plt.subplots(2,2,figsize=(11,7)); axs=axs.ravel()
        for ax,p in zip(axs,('DOW_OOS1','DOW_OOS2','DOW_OOS3','XASSET_OOS')):
            u='xasset' if p=='XASSET_OOS' else ('dow' if p=='DOW_OOS1' else 'dow_recent'); r,e,_=records[(u,p,name)]; ax.plot(r['wealth']/r['wealth'][0],label=name); ax.plot(e['wealth']/e['wealth'][0],label='EW30'); ax.set_title(p); ax.grid(alpha=.25); ax.legend(fontsize=8)
        fig.suptitle(f'Cycle 4 {fam}: {name} vs EW30'); fig.tight_layout(); fig.savefig(out/f'{fam}_frozen_tests.png',dpi=160); plt.close(fig)
    (out/'run_inventory.json').write_text(json.dumps({'candidate_series':runs,'invalid':{str(k):v for k,v in invalid.items()},'invariance_checks':invariance,'synthetic_invariance':synthetic,'frozen':frozen},indent=2),encoding='utf-8')
    print('FROZEN',frozen); print('INVALID',invalid); print('SELECTION')
    for fam,name in frozen.items():
        if name=='EW30': continue
        for u in ('dow','xasset'): print(fam,name,u,selection[(u,name)])
    print('TESTS')
    for k,v in records.items():
        if k[1]!='selection': print(k,v[2])
    print('SIGNIFICANCE',sig); print('RUNS',len(runs)); print('OUT',out)

if __name__=='__main__': run_all()


