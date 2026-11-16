#!/usr/bin/env python3
"""One-pass R10 S6 post-hoc reverse-direction FINRA screen."""
import csv, json, math
from pathlib import Path
from statistics import NormalDist
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
START, END = "2020-11-27", "2026-10-30"
COSTS = (0.0005, 0.001, 0.002)
IDS = ("S6-01 low-ratio long-only", "S6-02 low-minus-high quintile spread")

def nw(x, lag=3):
    x = np.asarray(x, float); n = len(x)
    if n < 3: return {"mean": float(x.mean()) if n else None, "sd": float(x.std(ddof=1)) if n > 1 else None, "se": None, "t": None}
    u = x - x.mean(); v = np.dot(u, u) / n
    for k in range(1, min(lag, n - 1) + 1): v += 2 * (1-k/(lag+1)) * np.dot(u[k:], u[:-k]) / n
    se = math.sqrt(max(v, 0) / n)
    return {"mean": float(x.mean()), "sd": float(x.std(ddof=1)), "se": se, "t": float(x.mean()/se) if se else None}

def norm_symbol(x): return "".join(ch for ch in str(x).upper() if ch.isalnum())

def evaluate(panel):
    dates, close, roster, assets = panel["dates"], panel["close"], panel["roster"], panel["assets"]
    ratio = panel["short_ratio"]
    per = pd.PeriodIndex(dates, freq="D").asfreq("M")
    ends = pd.Series(np.arange(len(dates))).groupby(per).max().to_dict()
    forms = [int(ends[x]) for x in sorted(ends)]
    records = {key: [] for key in IDS}; prev = {key: {} for key in IDS}
    bench_cov, eligible_cov, source_cov = [], [], []
    for i, j in zip(forms[:-1], forms[1:]):
        if dates[i] < START or dates[j] > END: continue
        live = np.flatnonzero(roster[:, i])
        bidx = live[np.isfinite(close[live, i]) & np.isfinite(close[live, j]) & (close[live, i] > 0) & (close[live, j] > 0)]
        if not len(bidx): continue
        bench = float(np.mean(close[bidx,j] / close[bidx,i] - 1)); bench_cov.append(len(bidx)/max(int(roster[:,i].sum()),1))
        if i < 4: continue
        elig = live[np.isfinite(ratio[:,i-4:i+1]).all(axis=1)]
        eligible_cov.append(len(elig)/max(int(roster[:,i].sum()),1))
        source_cov.append(float(np.isfinite(ratio[:,i-4:i+1]).all(axis=1).sum()/max(int(roster[:,i].sum()),1)))
        if len(elig) < 100: continue
        ordered = sorted(elig.tolist(), key=lambda q:(float(np.mean(ratio[q,i-4:i+1])), str(assets[q])))
        k = max(1, math.ceil(.2*len(ordered))); low, high = ordered[:k], ordered[-k:]
        px = lambda q: np.isfinite(close[q,i]) and np.isfinite(close[q,j]) and close[q,i] > 0 and close[q,j] > 0
        lowp, highp = [q for q in low if px(q)], [q for q in high if px(q)]
        if not lowp or not highp: continue
        lowret = float(np.mean(close[lowp,j]/close[lowp,i]-1)); highret = float(np.mean(close[highp,j]/close[highp,i]-1))
        for key in IDS:
            old = prev[key]
            if key == IDS[0]:
                names = [str(assets[q]) for q in lowp]; w = {str(assets[q]):1/len(lowp) for q in lowp}
                gross, gross_excess = lowret, lowret-bench
            else:
                names = [str(assets[q]) for q in lowp+highp]
                w = {str(assets[q]):1/len(lowp) for q in lowp}
                w.update({str(assets[q]):-1/len(highp) for q in highp})
                gross, gross_excess = lowret-highret, lowret-highret
            abschange = sum(abs(w.get(a,0)-old.get(a,0)) for a in set(w)|set(old))
            turnover = .5*abschange
            sens = {str(c):gross_excess-c*abschange for c in COSTS}
            records[key].append({"formation_date":str(dates[i]),"exit_date":str(dates[j]),"gross_portfolio_return":gross,
                "ew_pit_benchmark":bench,"gross_excess":gross_excess,"one_way_turnover":turnover,
                "absolute_weight_change":abschange,"eligible":len(elig),"low_priced":len(lowp),"high_priced":len(highp),"net_excess_by_cost":sens})
            prev[key] = w
    out = {"period":{"start":START,"end":END},"ew_pit_benchmark_coverage_mean":float(np.mean(bench_cov)) if bench_cov else None,
           "eligibility_fraction_mean":float(np.mean(eligible_cov)) if eligible_cov else None,"source_ratio_fraction_mean":float(np.mean(source_cov)) if source_cov else None,"ideas":{}}
    nd,z=NormalDist(),1.6448536269514722
    for key, rows in records.items():
        x=np.array([r["net_excess_by_cost"]["0.001"] for r in rows]); g=np.array([r["gross_excess"] for r in rows]); st=nw(x)
        years={}
        for y in sorted({r["formation_date"][:4] for r in rows}):
            a=[r["net_excess_by_cost"]["0.001"] for r in rows if r["formation_date"].startswith(y)]
            years[y]={"n":len(a),"mean_net_excess":float(np.mean(a)),"positive":bool(np.mean(a)>0)}
        nh=max(1,round(len(x)/max(1,len(years))*6)); sd=st["sd"]; se=sd/math.sqrt(nh) if sd is not None else None
        pp=nd.cdf(.5*st["mean"]/se-z) if se and st["mean"] is not None else None
        out["ideas"][key]={"n_months":len(x),"gross_excess_mean":float(g.mean()) if len(g) else None,"net_excess_mean":st["mean"],
            "nw_lag3_t":st["t"],"nw_se":st["se"],"sample_sd_net_excess":sd,"yearly":years,
            "positive_years":sum(v["positive"] for v in years.values()),"observed_years":len(years),
            "mean_one_way_turnover":float(np.mean([r["one_way_turnover"] for r in rows])) if rows else None,
            "mean_cost_bps":float(np.mean([r["absolute_weight_change"]*.001 for r in rows])*10000) if rows else None,
            "net_excess_cost_sensitivity":{str(c):float(np.mean([r["net_excess_by_cost"][str(c)] for r in rows])) for c in COSTS} if rows else {},
            "holdout_2010_2015":{"N_projected":nh,"family":1,"one_sided_alpha":.05,"power":.8,"MDE":2.4865*se if se else None,"haircut_pass_probability":pp},
            "go":bool(st["mean"] is not None and st["mean"]>0 and st["t"] is not None and st["t"]>=2 and pp is not None and pp>=.3),"cohorts":rows}
    return out

def synthetic_panel():
    dates=pd.bdate_range(START,periods=1550).strftime("%Y-%m-%d").to_numpy(); n=650; rng=np.random.default_rng(20261112)
    ret=rng.normal(.0003,.012,(n,len(dates))); close=np.empty_like(ret); close[:,0]=np.linspace(20,80,n)
    for i in range(1,len(dates)): close[:,i]=close[:,i-1]*(1+ret[:,i])
    ratio=np.clip(.5+rng.normal(0,.08,(n,len(dates))),.01,.99); roster=np.ones_like(close,dtype=bool)
    return {"dates":dates,"close":close,"roster":roster,"assets":np.array([f"T{i:03d}" for i in range(n)]),"short_ratio":ratio}

def load_dev_prices():
    with np.load(ROOT/"r9/data/J2_DEV_FROM_20201127.npz",allow_pickle=False) as z:
        d0=z["sp500_dates"].astype(str); keep=(d0>=START)&(d0<=END); dates=d0[keep]
        close=z["sp500_adjusted_close"][:,keep].astype(float); roster=z["sp500_roster"][:,keep].astype(bool); assets=z["sp500_assets"].astype(str)
    if not len(dates) or dates[0]<START or dates[-1]>END: raise ValueError("dev date guard failed")
    return dates,close,roster,assets

def load_finra(dates,assets,roster):
    raw=ROOT/"r6_data/finra_regsho/raw"
    files=sorted(p for p in raw.glob("CNMSshvol????????.txt") if START.replace("-","")<=p.stem[-8:]<=END.replace("-",""))
    aliases=pd.read_csv(ROOT/"r6_data/finra_regsho/ticker_aliases.csv",dtype=str).fillna("")
    asset_index={norm_symbol(x):i for i,x in enumerate(assets)}; alias_index={}
    for row in aliases.itertuples(index=False): alias_index.setdefault(norm_symbol(row.FINRA_symbol),[]).append((row.from_inclusive,row.to_exclusive,norm_symbol(row.roster_ticker)))
    date_index={str(d):i for i,d in enumerate(dates)}; ratio=np.full((len(assets),len(dates)),np.nan); matched=set(); opened=0
    for path in files:
        ds=path.stem[-8:]; d=f"{ds[:4]}-{ds[4:6]}-{ds[6:]}"
        if d not in date_index: continue
        k=date_index[d]; agg={}
        with path.open("r",encoding="utf-8-sig",newline="") as f:
            for row in csv.DictReader(f,delimiter="|"):
                sym=norm_symbol(row["Symbol"]); ticker=sym
                for lo,hi,mapped in alias_index.get(sym,[]):
                    if lo<=d<hi: ticker=mapped; break
                ai=asset_index.get(ticker)
                if ai is None or not roster[ai,k]: continue
                s=float(row["ShortVolume"] or 0); t=float(row["TotalVolume"] or 0); a,b=agg.get(ai,(0.,0.)); agg[ai]=(a+s,b+t)
        opened+=1
        for ai,(s,t) in agg.items():
            if t>0: ratio[ai,k]=s/t
        if agg: matched.add(d)
    return ratio,{"restricted_start":START,"restricted_end":END,"daily_source_files":len(files),"opened_dev_files":opened,"matched_source_dates":len(matched)}

def main():
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("--synthetic-only",action="store_true"); p.add_argument("--run-dev",action="store_true"); a=p.parse_args()
    if a.synthetic_only:
        r=evaluate(synthetic_panel()); assert set(r["ideas"])==set(IDS) and all(v["n_months"]>0 for v in r["ideas"].values())
        print(json.dumps({"status":"PASS","synthetic_only":True,"ideas":len(IDS),"observations":{k:v["n_months"] for k,v in r["ideas"].items()},"outcomes_created":False},indent=2)); return
    if not a.run_dev: raise SystemExit("choose --synthetic-only or the single --run-dev execution")
    dates,close,roster,assets=load_dev_prices(); ratio,src=load_finra(dates,assets,roster)
    result=evaluate({"dates":dates,"close":close,"roster":roster,"assets":assets,"short_ratio":ratio}); result["finra_source"]=src
    (ROOT/"r10/S6/DEV_RESULT.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"source":src,"coverage":{k:result[k] for k in ("ew_pit_benchmark_coverage_mean","eligibility_fraction_mean","source_ratio_fraction_mean")},"ideas":{k:{q:v for q,v in z.items() if q!="cohorts"} for k,z in result["ideas"].items()}},indent=2))
if __name__=="__main__": main()
