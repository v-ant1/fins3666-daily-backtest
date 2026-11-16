"""Cycle 1 OHLCV signal and portfolio harness, using a local copy of the validated engine."""
from __future__ import annotations
import csv, importlib.util, math, os, sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent.parent
ENGINE_PATH = HERE / "code" / "validated_engine_copy.py"
spec = importlib.util.spec_from_file_location("validated_engine_copy", ENGINE_PATH)
eng = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eng)
COST = 0.0005
ANCHOR = "2020-11-27"
VARIANTS = {
    "MAX21_a08": ("MAX21", 21, .8), "MAX21_a10": ("MAX21", 21, 1.0),
    "HIGH63_a08": ("HIGH", 63, .8), "HIGH126_a08": ("HIGH", 126, .8),
    "IDIO63_a08": ("IDIO", 63, .8), "IDIO126_a08": ("IDIO", 126, .8),
}
UNIVERSE_ASSETS = {}
FAMILY = {"MAX21_a08":"MAX21", "MAX21_a10":"MAX21", "HIGH63_a08":"HIGH",
          "HIGH126_a08":"HIGH", "IDIO63_a08":"IDIO", "IDIO126_a08":"IDIO"}

def load_context(universe: str):
    """Load either supplied universe using the copied engine's adjusted OHLCV reader."""
    if universe in ("dow", "dow_recent"):
        eng.BASE = str(HERE.parent / "w1_engine")
        eng.ROSTER_KEY = "2020-08-31" if universe == "dow" else "2024-11-08"
        eng.DOW30 = eng.ROSTERS[eng.ROSTER_KEY]
    elif universe == "xasset":
        eng.BASE = str(HERE.parent / "oos3" / "xasset")
        eng.ROSTER_KEY = "xasset30"
        eng.DOW30 = eng.ROSTERS[eng.ROSTER_KEY]
    else:
        raise ValueError(universe)
    eng.WIN_LAST = "2024-02-23" if universe == "dow" else "2026-10-30"
    ctx = eng.load_all()
    dates, ho, hc, C, V, H, L, spy = ctx
    if len(eng.DOW30) != 30:
        raise AssertionError("exactly 30 assets are required")
    UNIVERSE_ASSETS[universe] = list(eng.DOW30)
    if np.any(C <= 0) or np.isnan(C).any() or np.isnan(H).any():
        raise AssertionError("invalid adjusted price matrix")
    return ctx

def raw_signal(kind: str, lookback: int, i: int, C: np.ndarray, H: np.ndarray):
    """Per-asset raw signal at close i; lower lottery/idio risk or closer to high ranks higher."""
    if kind == "MAX21":
        rets = C[:, 1:] / C[:, :-1] - 1.0
        return -np.max(rets[:, i-21:i], axis=1)
    if kind == "HIGH":
        return C[:, i] / np.max(H[:, i-lookback+1:i+1], axis=1)
    if kind == "IDIO":
        rets = C[:, 1:] / C[:, :-1] - 1.0
        x = rets[:, i-lookback:i]
        market = x.mean(axis=0)
        if np.var(market, ddof=1) <= 0:
            raise AssertionError("market proxy has zero variance")
        residuals = np.empty_like(x)
        for j in range(x.shape[0]):
            beta = np.cov(x[j], market, ddof=1)[0,1] / np.var(market, ddof=1)
            intercept = x[j].mean() - beta * market.mean()
            residuals[j] = x[j] - intercept - beta * market
        # Annualization does not change cross-sectional ranks, but preserve the specified signal.
        return -residuals.std(axis=1, ddof=1) * math.sqrt(252)
    raise ValueError(kind)

def rank_weights(score: np.ndarray, a: float):
    vals = {str(i): float(x) for i, x in enumerate(score)}
    ranks = eng.pct_ranks(vals)
    return np.array([(1/30)*(1+a*(2*ranks[str(i)]-1)) for i in range(30)])

def signal_for(name: str, i: int, C: np.ndarray, H: np.ndarray):
    kind, lb, a = VARIANTS[name]
    return rank_weights(raw_signal(kind, lb, i, C, H), a)

def test_invariance(ctx, universe):
    dates, ho, hc, C, V, H, L, spy = ctx
    eligible = [j for j,d in enumerate(dates) if d >= ANCHOR]
    grid = eligible[::21]
    sampled = sorted(set([grid[0], grid[len(grid)//2], grid[-1]]))
    checks=0
    for i in sampled:
        if i < 126: continue
        for name, (kind,lb,a) in VARIANTS.items():
            now=signal_for(name,i,C,H)
            # Future observations are replaced/removed; the function gets only the prefix.
            c_prefix=C[:,:i+1].copy(); h_prefix=H[:,:i+1].copy()
            then=signal_for(name,i,c_prefix,h_prefix)
            if not np.allclose(now,then,rtol=0,atol=1e-12):
                raise AssertionError(f"{universe} {name} future-truncation mismatch at {dates[i]}")
            checks+=1
    print(f"[invariance] {universe}: {checks} signal/weight checks across 3 sampled dates PASS")

def backtest(ctx, universe, period, variant=None):
    """Run EW30 or one rank-tilt. Actual trade costs, next-open fills, 21-session grid and 1% band."""
    eng.DOW30 = UNIVERSE_ASSETS[universe]
    dates, ho, hc, C, V, H, L, spy = ctx
    lo,hi=period
    dmap={d:i for i,d in enumerate(dates)}
    eligible=[j for j,d in enumerate(dates) if d>=ANCHOR]
    grid=eligible[::21]
    fills=[j for j in grid if lo<=dates[j]<=hi]
    if not fills: raise AssertionError(f"no scheduled fills for {universe} {period}")
    sigs=[j-1 for j in fills]
    required=126 if variant and variant.startswith(("HIGH126","IDIO126")) else 63
    if min(sigs)<required:
        raise AssertionError(f"insufficient history before first signal: {dates[min(sigs)]}")
    # Complete session close series across the tested range, mark at daily close.
    daily=[]; schedule_turn=[]; records=[]; active_shares=[]
    equity=1.0; shares=None; last_fill_ix=None
    for k,(si,fi) in enumerate(zip(sigs,fills)):
        fill_date=dates[fi]
        end_ix=fills[k+1] if k+1<len(fills) else dmap[hi]
        final=(k+1==len(fills))
        oldvals={}
        if shares is not None:
            for t,sh in shares.items():
                if fill_date not in ho[t]: raise AssertionError(f"no open {t} {fill_date}")
                oldvals[t]=sh*ho[t][fill_date]
            gross=sum(oldvals.values())
            if variant is None:
                target=np.full(30,1/30)
            else:
                target=signal_for(variant,si,C,H)
            current=np.array([oldvals.get(t,0.0)/gross for t in eng.DOW30])
            if np.abs(target-current).sum() < .01:
                newvals=oldvals.copy(); after=gross; notional=0.0; paid=0.0; traded=False
                weights=np.array([oldvals.get(t,0.0)/gross for t in eng.DOW30])
            else:
                E=gross
                for _ in range(500):
                    E2=gross-COST*sum(abs(E*target[i]-oldvals.get(t,0.0)) for i,t in enumerate(eng.DOW30))
                    if abs(E2-E)<1e-15*max(1.0,gross): E=E2; break
                    E=E2
                notional=sum(abs(E*target[i]-oldvals.get(t,0.0)) for i,t in enumerate(eng.DOW30))
                paid=gross-E
                px={t:ho[t][fill_date] for t in eng.DOW30}
                chk=sum(abs(E*target[i]-oldvals.get(t,0.0)) for i,t in enumerate(eng.DOW30))
                assert abs(notional-chk)<1e-10*max(1,gross) and abs(paid-COST*notional)<1e-9*max(1,gross)
                after=E; traded=True; weights=target
            turnover=notional/gross if gross else 0.0
            schedule_turn.append(turnover)
            active_shares.append(.5*np.abs(weights-1/30).sum())
            equity=after
        else:
            # First purchase from cash incurs buy-side cost only, as in the validated engine.
            target=np.full(30,1/30) if variant is None else signal_for(variant,si,C,H)
            equity=1/(1+COST)
            weights=target; turnover=0.; traded=True
            active_shares.append(.5*np.abs(weights-1/30).sum())
        # The validated engine uses next-open execution and actual traded-notional cost accounting.
        entry={t:ho[t][fill_date] for t in eng.DOW30}
        shares={t:equity*weights[i]/entry[t] for i,t in enumerate(eng.DOW30)}
        records.append((fill_date,turnover,turnover>0,active_shares[-1]))
        # Do not double-count close on a rebalance date: mark through prior session then fill at open.
        start=fi
        # Segment return from fill open to each close; next scheduled fill's open valuation belongs to trade solve.
        for j in range(start,end_ix+1):
            d=dates[j]
            if j==end_ix and not final:
                continue
            v=sum(shares[t]*hc[t][d] for t in eng.DOW30)
            if final and j==end_ix:
                v*=1-COST
            daily.append((d,v))
        last_fill_ix=end_ix
    if not daily: raise AssertionError("no daily equity marks")
    # Validate no duplicate marks, positive wealth, and daily returns.
    md=[x[0] for x in daily]
    if len(md)!=len(set(md)) or any(v<=0 for _,v in daily): raise AssertionError("invalid equity marks")
    return {"dates":md,"wealth":np.array([v for _,v in daily]),"turnover":schedule_turn,
            "active_share":active_shares,"records":records}

def metrics(result, ew):
    r=np.diff(np.r_[1.0,result["wealth"]])/np.r_[1.0,result["wealth"]][:-1]
    er=np.diff(np.r_[1.0,ew["wealth"]])/np.r_[1.0,ew["wealth"]][:-1]
    n=len(r); sd=r.std(ddof=1); esd=(r-er).std(ddof=1)
    e_sd=er.std(ddof=1)
    growth=np.prod(1+r); cagr=growth**(252/n)-1 if growth>0 else -1
    peak=np.maximum.accumulate(np.r_[1,np.cumprod(1+r)])
    mdd=float(np.min(np.r_[1,np.cumprod(1+r)]/peak-1))
    ew_growth=np.prod(1+er)
    return {"cagr":cagr,"return":growth-1,"ew_return":ew_growth-1,
            "excess_return":growth-ew_growth,"sharpe":r.mean()/sd*math.sqrt(252) if sd else 0,
            "ew_sharpe":er.mean()/e_sd*math.sqrt(252) if e_sd else 0,
            "sharpe_above_ew":bool((r.mean()/sd if sd else 0)>(er.mean()/e_sd if e_sd else 0)),
            "mdd":mdd,"te":esd*math.sqrt(252) if esd else 0,
            "ir":(r-er).mean()/esd*math.sqrt(252) if esd else 0,
            "turnover":float(np.mean(result["turnover"])) if result["turnover"] else 0,
            "active_share":float(np.mean(result["active_share"]))}

def circular_bootstrap_p(series, draws=5000, block=10, seed=3666):
    rng=np.random.default_rng(seed); obs=abs(np.mean(series)); z=series-np.mean(series)
    n=len(z); nb=math.ceil(n/block); off=np.arange(block); count=0
    for _ in range(draws):
        starts=rng.integers(0,n,size=nb)
        sample=np.concatenate([z[(s+off)%n] for s in starts])[:n]
        count+=abs(np.mean(sample))>=obs
    return (count+1)/(draws+1)

def dsr(daily_returns, trials=82):
    # Bailey-López de Prado probabilistic/deflated Sharpe approximation.
    from scipy.special import ndtr
    from scipy.stats import norm
    x=np.asarray(daily_returns); n=len(x); sd=x.std(ddof=1)
    if n<3 or sd==0:return float("nan")
    sr=x.mean()/sd; z=(x-x.mean())/sd; skew=np.mean(z**3); kurt=np.mean(z**4)
    euler=.5772156649
    expected_max_z=((1-euler)*norm.ppf(1-1/trials)+euler*norm.ppf(1-1/(trials*math.e)))
    sr_max=expected_max_z/math.sqrt(n-1)
    denom=math.sqrt(max(1e-18,1-skew*sr+((kurt-1)/4)*sr*sr))
    return float(ndtr((sr-sr_max)*math.sqrt(n-1)/denom))

def run_frozen_price_folder(price_folder, tickers, family, period,
                            lookback=None, a=None, anchor=ANCHOR, rebalance_every=21):
    """Run a frozen cycle-1 tilt on any folder of 30 adjusted OHLCV CSVs.

    `price_folder` may be a flat directory of TICKER.csv files or an engine-style
    root containing prices-daily and optional lookback/delisted subdirectories.
    Returns date/wealth pairs and actual turnover. The caller supplies its
    30-name roster; this function does not know or inspect any holdout basket.
    """
    if len(tickers)!=30 or len(set(tickers))!=30:
        raise ValueError("exactly 30 unique tickers are required")
    fam=family.upper()
    frozen={"MAX21":("MAX21",21,.8),"HIGH":("HIGH",63,.8),"IDIO":("IDIO",63,.8)}
    if fam not in frozen: raise ValueError("family must be MAX21, HIGH, or IDIO")
    kind,default_lb,default_a=frozen[fam]
    lb=default_lb if lookback is None else int(lookback); strength=default_a if a is None else float(a)
    if kind=="MAX21" and lb!=21: raise ValueError("MAX21 lookback is fixed at 21")
    root=Path(price_folder); dirs=[root/"prices-daily-lookback",root/"prices-daily",root/"prices-daily-delisted",root]
    data={t:{} for t in tickers}
    for t in tickers:
        for folder in dirs:
            p=folder/f"{t}.csv"
            if not p.exists(): continue
            with p.open(newline="",encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    try:
                        d=row["date"][:10]; c=float(row["adjclose"]); raw=float(row["close"])
                        factor=c/raw if raw else 1.; o=float(row["open"])*factor; h=float(row["high"])*factor
                    except (KeyError,TypeError,ValueError): continue
                    data[t][d]={"open":o,"high":h,"close":c}
    if any(not data[t] for t in tickers): raise AssertionError("missing one or more ticker CSVs")
    spy_dates=set()
    for folder in dirs:
        p=folder/"SPY.csv"
        if p.exists():
            with p.open(newline="",encoding="utf-8-sig") as f:
                spy_dates.update(row["date"][:10] for row in csv.DictReader(f) if row.get("date"))
    calendar=spy_dates if spy_dates else set.union(*(set(data[t]) for t in tickers))
    data_start=max(min(data[t]) for t in tickers)
    dates=sorted(d for d in calendar if data_start<=d<=period[1])
    for t in tickers:
        missing=[d for d in dates if d not in data[t]]
        if missing: raise AssertionError(f"FAIL-FAST: {t} misses sessions such as {missing[:3]}")
    dmap={d:i for i,d in enumerate(dates)}
    C=np.array([[data[t][d]["close"] for d in dates] for t in tickers]); H=np.array([[data[t][d]["high"] for d in dates] for t in tickers])
    lo,hi=period
    eligible=[j for j,d in enumerate(dates) if d>=anchor]; fills=eligible[::rebalance_every]
    fills=[j for j in fills if lo<=dates[j]<=hi]
    if not fills: raise AssertionError("no scheduled fills in requested period")
    if fills[0]-1<lb: raise AssertionError("full signal lookback is not available")
    wealth=[]; outdates=[]; turnovers=[]; shares=None
    for k,fi in enumerate(fills):
        si=fi-1; end_ix=fills[k+1] if k+1<len(fills) else dmap.get(hi)
        if end_ix is None: raise AssertionError("period end date missing from common trading calendar")
        final=k+1==len(fills); target=rank_weights(raw_signal(kind,lb,si,C,H),strength)
        fill=dates[fi]
        if shares is None:
            nav=1/(1+COST); to=0.
        else:
            old={t:shares[t]*data[t][fill]["open"] for t in tickers}; gross=sum(old.values())
            drift=np.array([old[t]/gross for t in tickers])
            if np.abs(target-drift).sum()<.01:
                target=drift; nav=gross; notional=0.
            else:
                nav=gross
                for _ in range(500):
                    n2=gross-COST*sum(abs(nav*target[i]-old.get(t,0.)) for i,t in enumerate(tickers))
                    if abs(n2-nav)<1e-15*max(1.,gross):nav=n2;break
                    nav=n2
                notional=sum(abs(nav*target[i]-old.get(t,0.)) for i,t in enumerate(tickers))
                assert abs((gross-nav)-COST*notional)<1e-9*max(1.,gross)
            to=notional/gross if gross else 0.
        turnovers.append(to)
        shares={t:nav*target[i]/data[t][fill]["open"] for i,t in enumerate(tickers)}
        for j in range(fi,end_ix+1):
            if j==end_ix and not final: continue
            d=dates[j]; value=sum(shares[t]*data[t][d]["close"] for t in tickers)
            if final and j==end_ix:value*=1-COST
            outdates.append(d);wealth.append(value)
    return {"dates":outdates,"wealth":wealth,"turnover":turnovers,"variant":fam,"lookback":lb,"a":strength}

def write_outputs():
    out=HERE/"outputs_cycle1"; out.mkdir(exist_ok=True)
    periods={"selection":("2020-11-27","2022-12-30"),"DOW_OOS1":("2023-01-03","2024-02-23"),
             "DOW_OOS2":("2024-12-06","2025-12-31"),"DOW_OOS3":("2026-01-02","2026-10-30"),
             "XASSET_OOS":("2023-01-03","2026-10-30")}
    contexts={u:load_context(u) for u in ("dow","dow_recent","xasset")}
    for u,ctx in contexts.items(): test_invariance(ctx,u)
    rows=[]; results={}; selection={}; unavailable={}
    # Selection jobs only in this first pass.
    for u in ("dow","xasset"):
        ctx=contexts[u]; ew=backtest(ctx,u,periods["selection"])
        for name in VARIANTS:
            try:
                res=backtest(ctx,u,periods["selection"],name)
            except AssertionError as exc:
                if "insufficient history" not in str(exc): raise
                unavailable[(u,name)]=str(exc)
                print(f"[unavailable] {u} {name}: {exc}")
                continue
            m=metrics(res,ew)
            results[(u,"selection",name)]=(res,ew,m)
            selection[(u,name)]=m
            rows.append({"universe":u,"period":"selection","variant":name,**m})
    frozen={}
    for fam in ("MAX21","HIGH","IDIO"):
        cands=[n for n in VARIANTS if FAMILY[n]==fam]
        eligible=[n for n in cands if all((u,n) in selection and selection[(u,n)]["turnover"]<=.5 for u in ("dow","xasset"))]
        frozen[fam]=max(eligible,key=lambda n:(np.mean([selection[(u,n)]["sharpe"] for u in ("dow","xasset")]),
                       -np.mean([selection[(u,n)]["turnover"] for u in ("dow","xasset")]),
                       -VARIANTS[n][1],-VARIANTS[n][2])) if eligible else "EW30"
    (out/"frozen_choices.txt").write_text("\n".join(f"{k}={v}" for k,v in frozen.items())+"\n",encoding="utf-8")
    # Frozen test jobs, exactly once per idea-period.
    for fam,name in frozen.items():
        if name=="EW30": continue
        for period_name in ("DOW_OOS1","DOW_OOS2","DOW_OOS3","XASSET_OOS"):
            u="xasset" if period_name=="XASSET_OOS" else ("dow" if period_name=="DOW_OOS1" else "dow_recent")
            ctx=contexts[u]; bounds=periods[period_name]
            ew=backtest(ctx,u,bounds); res=backtest(ctx,u,bounds,name); m=metrics(res,ew)
            results[(u,period_name,name)]=(res,ew,m)
            rows.append({"universe":u,"period":period_name,"variant":name,**m})
    with (out/"metrics.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    # Store daily wealth series, one file per series evaluation.
    for key,(res,ew,m) in results.items():
        u,p,n=key; name=n or "EW30"
        with (out/f"{u}_{p}_{name}.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(["date",name,"ew"])
            for d,v,ev in zip(res["dates"],res["wealth"],ew["wealth"]):w.writerow([d,f"{v:.10f}",f"{ev:.10f}"])
    # Selected family chart for the four frozen test-period evaluations.
    for fam,name in frozen.items():
        if name=="EW30":continue
        fig,axes=plt.subplots(2,2,figsize=(11,7)); axes=axes.ravel()
        for ax,pname in zip(axes,("DOW_OOS1","DOW_OOS2","DOW_OOS3","XASSET_OOS")):
            u="xasset" if pname=="XASSET_OOS" else ("dow" if pname=="DOW_OOS1" else "dow_recent")
            res,ew,_=results[(u,pname,name)]
            ax.plot(np.arange(len(res["wealth"])),res["wealth"]/res["wealth"][0],label=name)
            ax.plot(np.arange(len(ew["wealth"])),ew["wealth"]/ew["wealth"][0],label="EW30",alpha=.8)
            ax.set_title(pname);ax.set_ylabel("wealth (rebased to first close)");ax.legend(fontsize=8);ax.grid(alpha=.25)
        fig.suptitle(f"{fam}: frozen choice vs EW30, after costs")
        fig.tight_layout();fig.savefig(out/f"{fam}_frozen_tests.png",dpi=160);plt.close(fig)
    # Per-family pooled tests: concatenate the four frozen-test excess daily returns.
    significance={}
    for fam,name in frozen.items():
        if name=="EW30":continue
        streams=[]; strategies=[]; bench=[]
        for pname in ("DOW_OOS1","DOW_OOS2","DOW_OOS3","XASSET_OOS"):
            u="xasset" if pname=="XASSET_OOS" else ("dow" if pname=="DOW_OOS1" else "dow_recent")
            res,ew,_=results[(u,pname,name)]
            sr=np.diff(np.r_[1.0,res["wealth"]])/np.r_[1.0,res["wealth"]][:-1]
            er=np.diff(np.r_[1.0,ew["wealth"]])/np.r_[1.0,ew["wealth"]][:-1]
            streams.extend(sr-er);strategies.extend(sr);bench.extend(er)
        significance[fam]={"p":circular_bootstrap_p(np.array(streams)),"dsr":dsr(np.array(strategies),82),
                           "pooled_excess":float(np.prod(1+np.array(strategies))-np.prod(1+np.array(bench))),
                           "mean_excess_daily":float(np.mean(streams))}
    (out/"significance.json").write_text(__import__('json').dumps(significance,indent=2),encoding="utf-8")
    print("[frozen]",frozen)
    print("[selection]")
    for fam,name in frozen.items():
        print(f" {fam} {name}")
        for u in ("dow","xasset"):
            if name!="EW30": print(f"  {u}: {selection[(u,name)]}")
    print("[tests]")
    for fam,name in frozen.items():
        if name=="EW30":continue
        for pname in ("DOW_OOS1","DOW_OOS2","DOW_OOS3","XASSET_OOS"):
            u="xasset" if pname=="XASSET_OOS" else ("dow" if pname=="DOW_OOS1" else "dow_recent")
            m=results[(u,pname,name)][2]
            print(f" {fam} {pname} {m}")
        print(" ",significance[fam])
    print(f"[outputs] {out}")

if __name__=="__main__": write_outputs()
