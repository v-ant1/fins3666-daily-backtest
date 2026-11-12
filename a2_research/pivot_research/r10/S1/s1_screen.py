#!/usr/bin/env python3
"""R10 S1 single-pass monthly price/volume screen; filters inputs to dev dates."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from statistics import NormalDist
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
START, END = "2020-11-27", "2026-10-30"
COSTS = (0.0005, 0.0010, 0.0020)
IDS = ("S1-01 signed abnormal-volume pressure", "S1-02 volume-weighted close-location pressure",
       "S1-03 overnight-return persistence", "S1-04 volume/return alignment")


def nw_stats(x, lag=3):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    n = len(x)
    if n < 3: return {"n": n, "mean": float(np.mean(x)) if n else None, "se": None, "t": None}
    u = x - x.mean(); gamma0 = np.dot(u, u) / n
    lrv = gamma0
    for k in range(1, min(lag, n-1)+1):
        g = np.dot(u[k:], u[:-k]) / n
        lrv += 2.0 * (1.0 - k/(lag+1.0)) * g
    se = math.sqrt(max(lrv, 0.0) / n)
    return {"n": n, "mean": float(x.mean()), "se": se, "t": float(x.mean()/se) if se else None}


def score_at(k, idx, close, adj_open, raw_close, high, low, volume, roster):
    n_assets = close.shape[0]
    if idx < 61: return [np.full(n_assets, np.nan) for _ in range(4)]
    # q[d] is current log volume relative to the preceding 60 sessions.
    q = np.full((n_assets, 20), np.nan)
    r = np.full((n_assets, 20), np.nan)
    clv = np.full((n_assets, 20), np.nan)
    vratio = np.full((n_assets, 20), np.nan)
    overnight = np.full((n_assets, 20), np.nan)
    for z, d in enumerate(range(idx-19, idx+1)):
        vv = volume[:, d]
        hist = volume[:, max(0,d-60):d]
        med = np.nanmedian(hist, axis=1)
        validhist = np.sum(np.isfinite(hist), axis=1) >= 40
        ok = validhist & np.isfinite(vv) & (vv >= 0) & np.isfinite(med) & (med >= 0)
        q[ok,z] = np.log((vv[ok]+1.0)/(med[ok]+1.0))
        if d > 0:
            a = close[:, d]; b = close[:, d-1]
            good = np.isfinite(a) & np.isfinite(b) & (a>0) & (b>0)
            r[good,z] = a[good]/b[good]-1.0
            oa = adj_open[:,d]
            prev = close[:,d-1]
            good = np.isfinite(oa) & np.isfinite(prev) & (oa>0) & (prev>0)
            overnight[good,z] = oa[good]/prev[good]-1.0
        h, l, c = high[:,d], low[:,d], raw_close[:,d]
        good = np.isfinite(h) & np.isfinite(l) & np.isfinite(c)
        clv[good,z] = np.where(h[good] == l[good], 0.0,
                               (2*c[good]-h[good]-l[good]) / np.where(h[good] == l[good],1.0,h[good]-l[good]))
        goodw = np.isfinite(vv) & np.isfinite(med) & (med > 0)
        vratio[goodw,z] = vv[goodw]/med[goodw]
    # Scores require valid full 20-session windows except S1-01's 18 valid pairs.
    s1 = np.full(n_assets,np.nan); s2=s1.copy(); s3=s1.copy(); s4=s1.copy()
    qcount=np.sum(np.isfinite(q),axis=1); rcount=np.sum(np.isfinite(r),axis=1)
    x=np.sign(r)*q
    ok=(qcount>=18)&(np.sum(np.isfinite(x),axis=1)>=18)
    for a in np.flatnonzero(ok):
        sd=np.nanstd(q[a],ddof=1)
        if sd>0: s1[a]=np.nanmean(x[a])/sd
    w=vratio
    ok2=(np.sum(np.isfinite(clv),axis=1)==20)&(np.sum(np.isfinite(w),axis=1)==20)
    denom=np.nansum(w,axis=1)
    valid=ok2&(denom>0)
    s2[valid]=np.nansum(w[valid]*clv[valid],axis=1)/denom[valid]
    ok3=np.sum(np.isfinite(overnight),axis=1)==20
    s3[ok3]=np.nanmean(overnight[ok3],axis=1)
    ok4=(qcount==20)&(rcount==20)
    for a in np.flatnonzero(ok4):
        if np.std(q[a])>0 and np.std(r[a])>0: s4[a]=np.corrcoef(q[a],r[a])[0,1]
    for s in (s1,s2,s3,s4): s[~roster]=np.nan
    return [s1,s2,s3,s4]


def evaluate(panel, synthetic=False):
    dates=panel["dates"]; close=panel["close"]; roster=panel["roster"]
    assets=panel["assets"]; volume=panel["volume"]; high=panel["high"]; low=panel["low"]
    raw_close=panel["raw_close"]; adj_open=panel["adj_open"]
    months=pd.Series(np.arange(len(dates)),index=pd.PeriodIndex(dates,freq="D")).groupby(lambda p:p.asfreq("M")).max().to_numpy()
    # Ensure month-end rebalances have a following calendar month endpoint.
    records={name:[] for name in IDS}; prev={name:{} for name in IDS}
    benchmark_coverage=[]; eligible_coverage=[]
    for m, idx in enumerate(months[:-1]):
        nxt=months[m+1]
        if dates[idx] < START or dates[nxt] > END: continue
        sigs=score_at(m,idx,close,adj_open,raw_close,high,low,volume,roster[:,idx])
        bench_idx=np.flatnonzero(roster[:,idx] & np.isfinite(close[:,idx]) & np.isfinite(close[:,nxt]) & (close[:,idx]>0))
        if bench_idx.size==0: continue
        bret=close[bench_idx,nxt]/close[bench_idx,idx]-1.0
        bench=float(np.mean(bret))
        benchmark_coverage.append(bench_idx.size / max(int(roster[:,idx].sum()),1))
        for j,name in enumerate(IDS):
            sig=sigs[j]
            elig=np.flatnonzero(np.isfinite(sig) & roster[:,idx] & np.isfinite(close[:,idx]) & (close[:,idx]>0))
            eligible_coverage.append(elig.size/max(int(roster[:,idx].sum()),1))
            if elig.size<100: continue
            k=max(1,int(math.ceil(.20*elig.size)))
            chosen=elig[np.argsort(sig[elig],kind="mergesort")[-k:]]
            if not np.all(np.isfinite(close[chosen,nxt]) & (close[chosen,nxt]>0)):
                continue
            gross=float(np.mean(close[chosen,nxt]/close[chosen,idx]-1.0))
            weights={str(assets[a]):1.0/len(chosen) for a in chosen}
            old=prev[name]
            turnover=.5*sum(abs(weights.get(x,0.0)-old.get(x,0.0)) for x in set(weights)|set(old))
            # Initial cash-to-book gets 100% one-way turnover; cost is 10bp × total abs notional change.
            if not old: turnover=1.0
            one_way=float(turnover)
            abs_notional=1.0 if not old else 2.0*one_way
            gross_excess=gross-bench
            rec={"formation_date":str(dates[idx]),"exit_date":str(dates[nxt]),"gross":gross,"benchmark":bench,
                 "gross_excess":gross_excess,"turnover_one_way":one_way,"abs_notional":abs_notional,
                 "net_by_cost":{str(c):gross - (abs_notional*c) for c in COSTS},"net_excess_by_cost":{str(c):gross_excess-(abs_notional*c) for c in COSTS},"book_n":len(chosen)}
            records[name].append(rec); prev[name]=weights
    out={"period":{"start":START,"end":END},"benchmark_coverage_mean":float(np.mean(benchmark_coverage)) if benchmark_coverage else None,
         "eligible_coverage_mean":float(np.mean(eligible_coverage)) if eligible_coverage else None,"ideas":{}}
    crit=1.6448536269514722
    z80=NormalDist().inv_cdf(.80)
    for name in IDS:
        rows=records[name]
        gross=np.array([x["gross"] for x in rows]); bench=np.array([x["benchmark"] for x in rows]); gx=np.array([x["gross_excess"] for x in rows])
        net=np.array([x["net_by_cost"][str(.001)] for x in rows]); nx=np.array([x["net_excess_by_cost"][str(.001)] for x in rows])
        st=nw_stats(nx,3); ann=sorted(set(x["formation_date"][:4] for x in rows)); years={}
        for y in ann:
            yx=np.array([x["net_excess_by_cost"][str(.001)] for x in rows if x["formation_date"].startswith(y)])
            years[y]={"n":len(yx),"mean_net_excess":float(yx.mean()) if len(yx) else None}
        ndev=len(nx); projected_se=(st["se"]*math.sqrt(ndev/72.0)) if ndev and st["se"] is not None else None
        mde=(crit+z80)*projected_se if projected_se is not None else None
        passprob=(1-NormalDist().cdf(max(crit,2.0)-(0.5*st["mean"])/projected_se)) if projected_se and st["mean"] is not None else None
        grossmean=float(gx.mean()) if len(gx) else None
        costmean=float(np.mean([x["abs_notional"]*.001 for x in rows])) if rows else None
        sharpe=lambda x: float(np.mean(x)/np.std(x,ddof=1)*math.sqrt(12)) if len(x)>1 and np.std(x,ddof=1)>0 else None
        out["ideas"][name]={"n_months":ndev,"gross_excess_mean":grossmean,"net_excess_mean":st["mean"],"nw_lag3_t":st["t"],"nw_se":st["se"],
            "mean_strategy_net":float(net.mean()) if len(net) else None,"mean_benchmark_gross":float(bench.mean()) if len(bench) else None,
            "net_sharpe":sharpe(net),"benchmark_sharpe":sharpe(bench),"net_excess_sharpe":sharpe(nx),
            "mean_one_way_turnover":float(np.mean([x["turnover_one_way"] for x in rows])) if rows else None,
            "mean_abs_notional_turnover":float(np.mean([x["abs_notional"] for x in rows])) if rows else None,
            "mean_cost_return":costmean,"cost_share_abs_gross_excess":abs(costmean/grossmean) if grossmean not in (None,0) and costmean is not None else None,
            "yearly":years,"positive_year_fraction":sum(v["mean_net_excess"]>0 for v in years.values())/len(years) if years else None,
            "net_excess_cost_sensitivity":{str(c):float(np.mean([x["net_excess_by_cost"][str(c)] for x in rows])) for c in COSTS} if rows else {},
            "holdout_2010_2015":{"N":72,"family":1,"one_sided_alpha":.05,"power":.80,"MDE":mde,"haircut_pass_probability":passprob},
            "go": bool(st["mean"] is not None and st["mean"]>0 and st["t"] is not None and st["t"]>=2 and passprob is not None and passprob>=.30),
            "cohorts":rows}
    return out


def synthetic_panel():
    dates=pd.bdate_range(START,periods=130).strftime("%Y-%m-%d").to_numpy(); n=120
    base=np.arange(n)[:,None]+20.; drift=np.arange(130)[None,:]
    close=base*np.exp(.0002*drift+0.002*np.sin(drift/3+np.arange(n)[:,None]))
    rng=np.random.default_rng(42); volume=rng.integers(1000,10000,size=(n,130)).astype(float)
    high=close*1.01; low=close*.99; raw_close=close.copy(); adj_open=close*.999
    roster=np.ones((n,130),bool); assets=np.array([f"T{i:03d}" for i in range(n)])
    return {"dates":dates,"close":close,"roster":roster,"assets":assets,"volume":volume,"high":high,"low":low,"raw_close":raw_close,"adj_open":adj_open}


def load_dev():
    p=ROOT/"r9/data/J2_DEV_FROM_20201127.npz"
    with np.load(p,allow_pickle=False) as z:
        dates=z["sp500_dates"].astype(str)
        keep=(dates>=START)&(dates<=END)
        dates=dates[keep]
        assets=z["sp500_assets"].astype(str)
        close=z["sp500_adjusted_close"][:,keep].astype(float)
        roster=z["sp500_roster"][:,keep].astype(bool)
    # Predicate-push the staged OHLCV scan to the permitted interval before reading bar values.
    bars=pd.read_parquet(ROOT/"r6_data/sp500_ohlcv_dev_gapfilled.parquet",columns=["date","ticker","open","high","low","close","volume"],
                         filters=[("date",">=",pd.Timestamp(START)),("date","<=",pd.Timestamp(END))])
    bars["date"]=pd.to_datetime(bars["date"]).dt.strftime("%Y-%m-%d")
    dateix={d:i for i,d in enumerate(dates)}; assetix={a:i for i,a in enumerate(assets)}
    shape=(len(assets),len(dates)); vol=np.full(shape,np.nan); hi=vol.copy(); lo=vol.copy(); raw=vol.copy(); op=vol.copy()
    for col,arr in (("volume",vol),("high",hi),("low",lo),("close",raw),("open",op)):
        for row in bars[["date","ticker",col]].itertuples(index=False,name=None):
            d,t,v=row
            i=dateix.get(d); a=assetix.get(t)
            if i is not None and a is not None: arr[a,i]=float(v)
    adj_open=op*(close/raw)
    return {"dates":dates,"close":close,"roster":roster,"assets":assets,"volume":vol,"high":hi,"low":lo,"raw_close":raw,"adj_open":adj_open}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--synthetic-only",action="store_true"); ap.add_argument("--run-dev",action="store_true"); args=ap.parse_args()
    if args.synthetic_only:
        out=evaluate(synthetic_panel(),True)
        assert set(out["ideas"])==set(IDS)
        assert all(v["n_months"]>0 and len(v["cohorts"])==v["n_months"] for v in out["ideas"].values())
        print(json.dumps({"status":"PASS","synthetic_only":True,"ideas":len(out["ideas"]),"outcomes_created":False},indent=2)); return
    if not args.run_dev: raise SystemExit("choose --synthetic-only or the single --run-dev execution")
    out=evaluate(load_dev())
    dest=ROOT/"r10/S1/DEV_RESULT.json"; dest.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:{x:y for x,y in v.items() if x!="cohorts"} for k,v in out["ideas"].items()},indent=2))

if __name__=="__main__": main()


