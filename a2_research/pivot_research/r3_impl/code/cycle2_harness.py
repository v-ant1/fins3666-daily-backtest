"""Cycle 2 strategy extension on the reusable cycle 1 engine/data harness."""
from __future__ import annotations
import csv, json, math
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import research_harness as base

HERE=Path(__file__).resolve().parent.parent
COST=base.COST; ANCHOR=base.ANCHOR
TRIALS=88
VARIANTS={
    "ILLIQ21_a08":("ILLIQ",21,.8),"ILLIQ63_a08":("ILLIQ",63,.8),
    "SKEW42_a08":("SKEW",42,.8),"SKEW63_a08":("SKEW",63,.8),
    "DOWNBETA63_NEG_a08":("DOWNBETA_NEG",63,.8),"DOWNBETA63_Q25_a08":("DOWNBETA_Q25",63,.8),
}
FAMILY={"ILLIQ21_a08":"ILLIQ","ILLIQ63_a08":"ILLIQ","SKEW42_a08":"SKEW","SKEW63_a08":"SKEW",
        "DOWNBETA63_NEG_a08":"DOWNBETA","DOWNBETA63_Q25_a08":"DOWNBETA"}

def cycle2_score(name: str, i: int, C: np.ndarray, V: np.ndarray):
    """Compute the preregistered signed rank score at close i, using no future rows."""
    kind,lb,_=VARIANTS[name]
    rets=C[:,1:]/C[:,:-1]-1.0
    x=rets[:,i-lb:i]
    if x.shape[1]!=lb or not np.isfinite(x).all(): raise AssertionError(f"{name}: incomplete return window")
    if kind=="ILLIQ":
        dollar_volume=C[:,i-lb+1:i+1]*V[:,i-lb+1:i+1]
        if dollar_volume.shape[1]!=lb or not np.isfinite(dollar_volume).all() or np.any(dollar_volume<=0):
            raise AssertionError(f"{name}: invalid or missing dollar volume in required window")
        illiq=(np.abs(x)/dollar_volume).mean(axis=1)
        return illiq # greater illiquidity receives greater rank/weight
    if kind=="SKEW":
        centered=x-x.mean(axis=1,keepdims=True)
        m2=np.mean(centered**2,axis=1);m3=np.mean(centered**3,axis=1)
        if np.any(m2<=0) or not np.isfinite(m2).all(): raise AssertionError(f"{name}: zero variance or invalid returns")
        skew=m3/(m2**1.5)
        return -skew # lower realized skewness receives higher rank/weight
    if kind.startswith("DOWNBETA"):
        betas=np.empty(30)
        for j in range(30):
            market=np.delete(x,j,axis=0).mean(axis=0) # leave-one-out equal-weight benchmark
            if kind=="DOWNBETA_NEG": mask=market<0
            else: mask=market<=np.quantile(market,.25)
            xm=market[mask]; yi=x[j,mask]
            if len(xm)<15: raise AssertionError(f"{name}: only {len(xm)} qualifying downside observations for asset {j}")
            var=float(np.var(xm,ddof=1))
            if not np.isfinite(var) or var<=0: raise AssertionError(f"{name}: zero benchmark variance for asset {j}")
            beta=float(np.cov(yi,xm,ddof=1)[0,1]/var)
            if not np.isfinite(beta): raise AssertionError(f"{name}: invalid downside beta for asset {j}")
            betas[j]=beta
        return -betas # lower downside beta receives higher rank/weight
    raise ValueError(kind)

def cycle2_weights(name: str, i: int, C: np.ndarray, V: np.ndarray):
    return base.rank_weights(cycle2_score(name,i,C,V),VARIANTS[name][2])

def test_invariance_cycle2(ctx,universe):
    dates,ho,hc,C,V,H,L,spy=ctx
    eligible=[j for j,d in enumerate(dates) if d>=ANCHOR]; grid=eligible[::21]
    samples=sorted(set([grid[0],grid[len(grid)//2],grid[-1]]));checked=0
    for i in samples:
        if i<63: continue
        for name in VARIANTS:
            full=cycle2_weights(name,i,C,V)
            truncated=cycle2_weights(name,i,C[:,:i+1],V[:,:i+1])
            if not np.allclose(full,truncated,rtol=0,atol=1e-12):
                raise AssertionError(f"{universe} {name} future-truncation mismatch at {dates[i]}")
            checked+=1
    print(f"[invariance-c2] {universe}: {checked} signal/weight checks PASS")

def backtest_cycle2(ctx,universe,period,variant=None):
    """Next-open rank tilt or EW30, actual trade cost, 21-session grid and 1% band."""
    eng=base.eng;eng.DOW30=base.UNIVERSE_ASSETS[universe]
    dates,ho,hc,C,V,H,L,spy=ctx;lo,hi=period;dmap={d:i for i,d in enumerate(dates)}
    eligible=[j for j,d in enumerate(dates) if d>=ANCHOR];grid=eligible[::21]
    fills=[j for j in grid if lo<=dates[j]<=hi]
    if not fills: raise AssertionError(f"no fills for {universe}/{period}")
    sigs=[j-1 for j in fills]
    minlb=VARIANTS[variant][1] if variant else 1
    if min(sigs)<minlb: raise AssertionError(f"insufficient history for {variant} at {dates[min(sigs)]}")
    daily=[];turnovers=[];active=[];shares=None;recon=1.0;prior_nav=None
    for k,(si,fi) in enumerate(zip(sigs,fills)):
        fill=dates[fi];end_ix=fills[k+1] if k+1<len(fills) else dmap[hi];final=k+1==len(fills)
        if shares is None:
            weights=np.full(30,1/30) if variant is None else cycle2_weights(variant,si,C,V)
            nav=1/(1+COST);turn=0.;active.append(.5*np.abs(weights-1/30).sum())
        else:
            old={t:shares[t]*ho[t][fill] for t in eng.DOW30};gross=sum(old.values())
            # Independent share-ledger return through the next fill open.
            recon*=gross/prior_nav
            target=np.full(30,1/30) if variant is None else cycle2_weights(variant,si,C,V)
            drift=np.array([old.get(t,0.)/gross for t in eng.DOW30])
            if np.abs(target-drift).sum()<.01:
                weights=drift;nav=gross;notional=0.
            else:
                nav=gross
                for _ in range(500):
                    nav2=gross-COST*sum(abs(nav*target[j]-old.get(t,0.)) for j,t in enumerate(eng.DOW30))
                    if abs(nav2-nav)<1e-15*max(1.,gross):nav=nav2;break
                    nav=nav2
                notional=sum(abs(nav*target[j]-old.get(t,0.)) for j,t in enumerate(eng.DOW30))
                paid=gross-nav
                assert abs(paid-COST*notional)<1e-9*max(1.,gross),f"{fill}: cost equation does not reconcile"
                weights=target
            turn=notional/gross if gross else 0.;active.append(.5*np.abs(weights-1/30).sum())
            recon*=nav/gross
        if shares is None:
            recon*=nav
            turnovers.append(turn)
        if np.any(weights< -1e-14) or abs(weights.sum()-1)>1e-12:raise AssertionError("invalid portfolio weights")
        shares={t:nav*weights[j]/ho[t][fill] for j,t in enumerate(eng.DOW30)}
        prior_nav=nav
        for j in range(fi,end_ix+1):
            if j==end_ix and not final:continue
            d=dates[j];value=sum(shares[t]*hc[t][d] for t in eng.DOW30)
            if final and j==end_ix:value*=1-COST
            daily.append((d,value))
    dates_out=[d for d,_ in daily];wealth=np.array([v for _,v in daily])
    if len(dates_out)!=len(set(dates_out)) or np.any(wealth<=0):raise AssertionError("duplicate/invalid equity marks")
    terminal_gross=sum(shares[t]*hc[t][hi] for t in eng.DOW30)
    recon*=terminal_gross/prior_nav
    recon*=1-COST
    if abs(recon-wealth[-1])>1e-6*max(1.,abs(wealth[-1])):
        raise AssertionError(f"ledger reconciliation failed: {recon:.10f} vs {wealth[-1]:.10f}")
    return {"dates":dates_out,"wealth":wealth,"turnover":turnovers,"active_share":active}

def run_frozen_cycle2_price_folder(price_folder,tickers,family,period,anchor=ANCHOR,rebalance_every=21):
    """Execute the frozen cycle 2 choice on a caller-supplied 30-name OHLCV folder.

    Accepts a flat ticker CSV directory or a validated-engine root with
    prices-daily and optional lookback/delisted directories. No roster is embedded.
    """
    if len(tickers)!=30 or len(set(tickers))!=30:raise ValueError("exactly 30 unique tickers required")
    if family not in VARIANTS:raise ValueError(f"family must be one of {list(VARIANTS)}")
    root=Path(price_folder);dirs=[root/"prices-daily-lookback",root/"prices-daily",root/"prices-daily-delisted",root]
    data={t:{} for t in tickers}
    for t in tickers:
        for folder in dirs:
            path=folder/f"{t}.csv"
            if not path.exists():continue
            with path.open(newline="",encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    try:
                        d=row["date"][:10];c=float(row["adjclose"]);raw=float(row["close"]);fac=c/raw if raw else 1.
                        data[t][d]={"open":float(row["open"])*fac,"close":c,"volume":float(row["volume"])}
                    except (KeyError,TypeError,ValueError):continue
    if any(not data[t] for t in tickers):raise AssertionError("missing one or more ticker price files")
    cal=set()
    for folder in dirs:
        path=folder/"SPY.csv"
        if path.exists():
            with path.open(newline="",encoding="utf-8-sig") as f:cal.update(r["date"][:10] for r in csv.DictReader(f) if r.get("date"))
    if not cal:cal=set.union(*(set(data[t]) for t in tickers))
    start=max(min(data[t]) for t in tickers);lo,hi=period;dates=sorted(d for d in cal if start<=d<=hi)
    for t in tickers:
        missing=[d for d in dates if d not in data[t]]
        if missing:raise AssertionError(f"FAIL-FAST {t} missing sessions {missing[:3]}")
    C=np.array([[data[t][d]["close"] for d in dates] for t in tickers]);V=np.array([[data[t][d]["volume"] for d in dates] for t in tickers])
    dmap={d:i for i,d in enumerate(dates)};grid=[j for j,d in enumerate(dates) if d>=anchor][::rebalance_every]
    fills=[j for j in grid if lo<=dates[j]<=hi]
    if not fills:raise AssertionError("no eligible rebalance fills")
    if fills[0]-1<VARIANTS[family][1]:raise AssertionError("full lookback unavailable")
    wealth=[];outdates=[];turnovers=[];shares=None;prior_nav=None;recon=1.0;kind,lb,a=VARIANTS[family]
    for k,fi in enumerate(fills):
        si=fi-1;end=fills[k+1] if k+1<len(fills) else dmap.get(hi)
        if end is None:raise AssertionError("period end missing from session calendar")
        final=k+1==len(fills);score=cycle2_score(family,si,C,V);weights=base.rank_weights(score,a);fill=dates[fi]
        if shares is None:nav=1/(1+COST);turn=0.
        else:
            old={t:shares[t]*data[t][fill]["open"] for t in tickers};gross=sum(old.values());recon*=gross/prior_nav;drift=np.array([old[t]/gross for t in tickers])
            if np.abs(weights-drift).sum()<.01:weights=drift;nav=gross;notional=0.
            else:
                nav=gross
                for _ in range(500):
                    n2=gross-COST*sum(abs(nav*weights[j]-old.get(t,0.)) for j,t in enumerate(tickers))
                    if abs(n2-nav)<1e-15*max(1.,gross):nav=n2;break
                    nav=n2
                notional=sum(abs(nav*weights[j]-old.get(t,0.)) for j,t in enumerate(tickers))
                assert abs(gross-nav-COST*notional)<1e-9*max(1.,gross)
            recon*=nav/gross
            turn=notional/gross if gross else 0.
        if shares is None:recon*=nav
        turnovers.append(turn);shares={t:nav*weights[j]/data[t][fill]["open"] for j,t in enumerate(tickers)}
        prior_nav=nav
        for j in range(fi,end+1):
            if j==end and not final:continue
            d=dates[j];value=sum(shares[t]*data[t][d]["close"] for t in tickers)
            if final and j==end:value*=1-COST
            outdates.append(d);wealth.append(value)
    terminal=sum(shares[t]*data[t][hi]["close"] for t in tickers)
    recon*=terminal/prior_nav;recon*=1-COST
    if abs(recon-wealth[-1])>1e-6*max(1.,abs(wealth[-1])):raise AssertionError("generic-folder ledger reconciliation failed")
    return {"dates":outdates,"wealth":wealth,"turnover":turnovers,"variant":family}

def write_outputs_cycle2():
    out=HERE/"outputs_cycle2";out.mkdir(exist_ok=True)
    periods={"selection":("2020-11-27","2022-12-30"),"DOW_OOS1":("2023-01-03","2024-02-23"),
      "DOW_OOS2":("2024-12-06","2025-12-31"),"DOW_OOS3":("2026-01-02","2026-10-30"),"XASSET_OOS":("2023-01-03","2026-10-30")}
    contexts={u:base.load_context(u) for u in ("dow","dow_recent","xasset")}
    for u,ctx in contexts.items():test_invariance_cycle2(ctx,u)
    rows=[];resmap={};sel={};invalid={}
    for u in ("dow","xasset"):
        ctx=contexts[u];ew=base.backtest(ctx,u,periods["selection"])
        for name in VARIANTS:
            try:res=backtest_cycle2(ctx,u,periods["selection"],name)
            except AssertionError as e:
                invalid[(u,name)]=str(e);print(f"[invalid-selection] {u}/{name}: {e}");continue
            m=base.metrics(res,ew);sel[(u,name)]=m;resmap[(u,"selection",name)]=(res,ew,m)
            rows.append({"universe":u,"period":"selection","variant":name,**m})
    frozen={}
    for fam in ("ILLIQ","SKEW","DOWNBETA"):
        names=[n for n in VARIANTS if FAMILY[n]==fam]
        eligible=[n for n in names if all((u,n) in sel and sel[(u,n)]["turnover"]<=.5 for u in ("dow","xasset"))]
        frozen[fam]=max(eligible,key=lambda n:(np.mean([sel[(u,n)]["sharpe"] for u in ("dow","xasset")]),
          -np.mean([sel[(u,n)]["turnover"] for u in ("dow","xasset")]),-VARIANTS[n][1],-names.index(n))) if eligible else "EW30"
    (out/"frozen_choices.txt").write_text("\n".join(f"{f}={n}" for f,n in frozen.items())+"\n",encoding="utf-8")
    # Frozen file is durable before the first test run.
    for fam,name in frozen.items():
        if name=="EW30":continue
        for p in ("DOW_OOS1","DOW_OOS2","DOW_OOS3","XASSET_OOS"):
            u="xasset" if p=="XASSET_OOS" else ("dow" if p=="DOW_OOS1" else "dow_recent")
            ew=base.backtest(contexts[u],u,periods[p]);res=backtest_cycle2(contexts[u],u,periods[p],name);m=base.metrics(res,ew)
            resmap[(u,p,name)]=(res,ew,m);rows.append({"universe":u,"period":p,"variant":name,**m})
    with (out/"metrics.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    for (u,p,n),(res,ew,m) in resmap.items():
        with (out/f"{u}_{p}_{n}.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.writer(f);w.writerow(["date",n,"ew"])
            for d,v,e in zip(res["dates"],res["wealth"],ew["wealth"]):w.writerow([d,f"{v:.10f}",f"{e:.10f}"])
    significance={}
    for fam,name in frozen.items():
        if name=="EW30":continue
        ex=[];sr_all=[];ew_all=[]
        for p in ("DOW_OOS1","DOW_OOS2","DOW_OOS3","XASSET_OOS"):
            u="xasset" if p=="XASSET_OOS" else ("dow" if p=="DOW_OOS1" else "dow_recent")
            res,ew,_=resmap[(u,p,name)]
            sr=np.diff(np.r_[1.,res["wealth"]])/np.r_[1.,res["wealth"]][:-1]
            er=np.diff(np.r_[1.,ew["wealth"]])/np.r_[1.,ew["wealth"]][:-1]
            ex.extend(sr-er);sr_all.extend(sr);ew_all.extend(er)
        significance[fam]={"p":base.circular_bootstrap_p(np.array(ex),draws=5000,block=10,seed=3666),"dsr":base.dsr(np.array(sr_all),TRIALS),
          "pooled_excess":float(np.prod(1+np.array(sr_all))-np.prod(1+np.array(ew_all))),"mean_excess_daily":float(np.mean(ex))}
    (out/"significance.json").write_text(json.dumps(significance,indent=2),encoding="utf-8")
    for fam,name in frozen.items():
        if name=="EW30":continue
        fig,axes=plt.subplots(2,2,figsize=(11,7));axes=axes.ravel()
        for ax,p in zip(axes,("DOW_OOS1","DOW_OOS2","DOW_OOS3","XASSET_OOS")):
            u="xasset" if p=="XASSET_OOS" else ("dow" if p=="DOW_OOS1" else "dow_recent")
            r,e,_=resmap[(u,p,name)];ax.plot(r["wealth"]/r["wealth"][0],label=name);ax.plot(e["wealth"]/e["wealth"][0],label="EW30")
            ax.set_title(p);ax.set_ylabel("wealth (rebased to first close)");ax.grid(alpha=.25);ax.legend(fontsize=8)
        fig.suptitle(f"Cycle 2 {fam}: frozen variant vs EW30, net of costs");fig.tight_layout();fig.savefig(out/f"{fam}_frozen_tests.png",dpi=160);plt.close(fig)
    print("[cycle2-frozen]",frozen)
    for fam,name in frozen.items():
        print(f"[cycle2-selection] {fam} {name}")
        if name!="EW30":
            for u in ("dow","xasset"):print(u,sel[(u,name)])
            for p in ("DOW_OOS1","DOW_OOS2","DOW_OOS3","XASSET_OOS"):
                u="xasset" if p=="XASSET_OOS" else ("dow" if p=="DOW_OOS1" else "dow_recent")
                print(p,resmap[(u,p,name)][2])
            print("pooled",significance[fam])
    print("[cycle2-outputs]",out)

if __name__=="__main__":write_outputs_cycle2()
