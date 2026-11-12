#!/usr/bin/env python3
"""One-pass R10 S4 monthly low-risk and calendar screen."""
import argparse, json, math
from pathlib import Path
from statistics import NormalDist
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
START,END="2020-11-27","2026-10-30"
COSTS=(.0005,.001,.002)
IDS=("S4-01 low realized volatility","S4-02 low market beta","S4-03 turn-of-month seasonality","S4-04 pre-holiday seasonality","S4-05 52-week-high proximity","S4-06 residual momentum")
def nw(x,lag=3):
 x=np.asarray(x,float); n=len(x)
 if n<3:return {"mean":float(x.mean()) if n else None,"sd":float(x.std(ddof=1)) if n>1 else None,"se":None,"t":None}
 u=x-x.mean(); v=np.dot(u,u)/n
 for k in range(1,min(lag,n-1)+1):v+=2*(1-k/(lag+1))*np.dot(u[k:],u[:-k])/n
 se=math.sqrt(max(v,0)/n)
 return {"mean":float(x.mean()),"sd":float(x.std(ddof=1)),"se":se,"t":float(x.mean()/se) if se else None}
def returns(c):
 r=np.full_like(c,np.nan,float); ok=np.isfinite(c[:,1:])&np.isfinite(c[:,:-1])&(c[:,1:]>0)&(c[:,:-1]>0); r[:,1:][ok]=c[:,1:][ok]/c[:,:-1][ok]-1; return r
def scores(i,p,r,b,firsts,holidays):
 d,c,ro,assets=p["dates"],p["close"],p["roster"],p["assets"]; n=len(assets); out=[np.full(n,np.nan) for _ in IDS]; live=ro[:,i]
 a=i-59
 if a>=1:
  x=r[:,a:i+1]; ok=np.isfinite(x).sum(axis=1)==60; out[0][ok]=-np.std(x[ok],axis=1,ddof=1)
  y=b[a:i+1]
  if np.isfinite(y).sum()==60 and np.var(y,ddof=1)>0:
   for j in np.flatnonzero(live):
    z=x[j];
    if np.all(np.isfinite(z)):out[1][j]=-np.cov(z,y,ddof=1)[0,1]/np.var(y,ddof=1)
 # 12 latest completed month-turn episodes: prior month-end close to current month's third session close.
 cur=pd.Period(d[i],freq="M"); eps=[firsts[m] for m in [cur-k for k in range(12)] if m in firsts and firsts[m][1]<=i]
 if len(eps)>=9:
  mat=np.full((n,len(eps)),np.nan)
  for q,(s,e) in enumerate(eps):
   ok=np.isfinite(c[:,s])&np.isfinite(c[:,e])&(c[:,s]>0)&(c[:,e]>0); mat[ok,q]=c[ok,e]/c[ok,s]-1
  ok=np.isfinite(mat).sum(axis=1)>=9; out[2][ok]=np.nanmean(mat[ok],axis=1)
 # Last 24 pre-holiday trading sessions, with >=12 valid returns.
 ev=[k for k in holidays if k<i][-24:]
 if len(ev)>=12:
  mat=r[:,ev]; ok=np.isfinite(mat).sum(axis=1)>=12; out[3][ok]=np.nanmean(mat[ok],axis=1)
 # Current close / 252-session trailing high.
 h=c[:,max(0,i-251):i+1]; count=(np.isfinite(h)&(h>0)).sum(axis=1); peak=np.nanmax(np.where(h>0,h,np.nan),axis=1); ok=np.isfinite(c[:,i])&(c[:,i]>0)&(count>=200)&(peak>0); out[4][ok]=c[ok,i]/peak[ok]
 # 252 daily returns ending 21 sessions before formation.
 lo,hi=i-272,i-20
 if lo>=1 and hi-lo==252:
  y=b[lo:hi]
  for j in np.flatnonzero(live):
   x=r[j,lo:hi]; ok=np.isfinite(x)&np.isfinite(y)
   if ok.sum()>=200 and np.var(y[ok],ddof=1)>0:
    xx,yy=x[ok],y[ok]; beta=np.cov(xx,yy,ddof=1)[0,1]/np.var(yy,ddof=1); out[5][j]=np.sum(xx-beta*yy)
 for x in out:x[~live]=np.nan
 return out
def evaluate(p):
 d,c,ro,assets=p["dates"],p["close"],p["roster"],p["assets"]; r=returns(c); b=np.full(len(d),np.nan)
 for k in range(1,len(d)):
  ix=ro[:,k]&ro[:,k-1]&np.isfinite(r[:,k]);
  if ix.any():b[k]=r[ix,k].mean()
 per=pd.PeriodIndex(d,freq="D").asfreq("M"); ends=pd.Series(np.arange(len(d))).groupby(per).max().to_dict(); forms=[int(ends[x]) for x in sorted(ends)]
 firsts={}
 for m in ends:
  ix=np.flatnonzero(per==m)
  if len(ix)>=3 and m-1 in ends:firsts[m]=(int(ends[m-1]),int(ix[2]))
 holidays=[k for k in range(len(d)-1) if (pd.Timestamp(str(d[k+1]))-pd.Timestamp(str(d[k]))).days>=3]
 rec={x:[] for x in IDS}; prior={x:{} for x in IDS}; cov=[]; eligcov={x:[] for x in IDS}
 for i,j in zip(forms[:-1],forms[1:]):
  if d[i]<START or d[j]>END:continue
  bi=np.flatnonzero(ro[:,i]&np.isfinite(c[:,i])&np.isfinite(c[:,j])&(c[:,i]>0)&(c[:,j]>0))
  if not len(bi):continue
  bm=float(np.mean(c[bi,j]/c[bi,i]-1)); cov.append(len(bi)/max(int(ro[:,i].sum()),1)); ss=scores(i,p,r,b,firsts,holidays)
  for z,name in enumerate(IDS):
   elig=np.flatnonzero(np.isfinite(ss[z])&ro[:,i]&(c[:,i]>0)); eligcov[name].append(len(elig)/max(int(ro[:,i].sum()),1))
   if len(elig)<100:continue
   ordered=sorted(elig.tolist(),key=lambda q:(-float(ss[z][q]),str(assets[q]))); chosen=ordered[:max(1,math.ceil(.2*len(ordered)))]; priced=[q for q in chosen if np.isfinite(c[q,j]) and c[q,j]>0]
   if not priced:continue
   gross=float(np.mean(c[priced,j]/c[priced,i]-1)); w={str(assets[q]):1/len(priced) for q in priced}; old=prior[name]; turn=.5*sum(abs(w.get(x,0)-old.get(x,0)) for x in set(w)|set(old));
   if not old:turn=1.
   absn=1. if not old else 2*turn; gx=gross-bm
   rec[name].append({"formation_date":str(d[i]),"exit_date":str(d[j]),"gross":gross,"benchmark":bm,"gross_excess":gx,"turnover_one_way":turn,"abs_notional":absn,"selected":len(chosen),"priced":len(priced),"net_by_cost":{str(q):gross-absn*q for q in COSTS},"net_excess_by_cost":{str(q):gx-absn*q for q in COSTS}}); prior[name]=w
 out={"period":{"start":START,"end":END},"benchmark_coverage_mean":float(np.mean(cov)) if cov else None,"eligible_coverage_mean":{x:float(np.mean(v)) if v else None for x,v in eligcov.items()},"ideas":{}}
 nd=NormalDist(); z=1.6448536269514722
 for name in IDS:
  rows=rec[name]; x=np.array([q["net_excess_by_cost"]["0.001"] for q in rows]); grossx=np.array([q["gross_excess"] for q in rows]); st=nw(x); years={}
  for y in sorted({q["formation_date"][:4] for q in rows}):
   vals=[q["net_excess_by_cost"]["0.001"] for q in rows if q["formation_date"].startswith(y)]; years[y]={"n":len(vals),"mean_net_excess":float(np.mean(vals)),"positive":bool(np.mean(vals)>0)}
  ny=len(years); nh=max(1,round(len(x)/max(1,ny)*6)); sd=st["sd"]; plan=sd/math.sqrt(nh) if sd is not None else None; mde=2.4865*plan if plan is not None else None; pp=nd.cdf(.5*st["mean"]/plan-z) if plan and st["mean"] is not None else None
  cost=float(np.mean([q["abs_notional"]*.001 for q in rows])) if rows else None; net=np.array([q["net_by_cost"]["0.001"] for q in rows]); sharpe=lambda v:float(np.mean(v)/np.std(v,ddof=1)*math.sqrt(12)) if len(v)>1 and np.std(v,ddof=1)>0 else None
  out["ideas"][name]={"n_months":len(x),"gross_excess_mean":float(grossx.mean()) if len(x) else None,"net_excess_mean":st["mean"],"nw_lag3_t":st["t"],"nw_se":st["se"],"sample_sd_net_excess":sd,"mean_strategy_net":float(net.mean()) if len(net) else None,"mean_benchmark_gross":float(np.mean([q["benchmark"] for q in rows])) if rows else None,"net_sharpe_strategy_annualized":sharpe(net),"net_excess_sharpe_annualized":sharpe(x),"mean_one_way_turnover":float(np.mean([q["turnover_one_way"] for q in rows])) if rows else None,"mean_cost_bps":cost*10000 if cost is not None else None,"cost_share_abs_gross_excess":abs(cost/grossx.mean()) if cost is not None and len(x) and grossx.mean()!=0 else None,"yearly":years,"positive_years":sum(v["positive"] for v in years.values()),"observed_years":ny,"holdout_2010_2015":{"N_projected":nh,"family":1,"one_sided_alpha":.05,"power":.8,"MDE":mde,"haircut_pass_probability":pp},"mean_selected":float(np.mean([q["selected"] for q in rows])) if rows else None,"mean_priced":float(np.mean([q["priced"] for q in rows])) if rows else None,"net_excess_cost_sensitivity":{str(q):float(np.mean([v["net_excess_by_cost"][str(q)] for v in rows])) for q in COSTS} if rows else {},"go":bool(st["mean"] is not None and st["mean"]>0 and st["t"] is not None and st["t"]>=2 and pp is not None and pp>=.3),"cohorts":rows}
 return out
def synthetic_panel():
 d=pd.bdate_range(START,periods=1550).strftime("%Y-%m-%d").to_numpy(); n=140; rng=np.random.default_rng(20261112); f=rng.normal(.0002,.008,len(d)); noise=rng.normal(0,.012,(n,len(d))); beta=np.linspace(.35,1.65,n)[:,None]; rr=beta*f[None,:]+noise+np.linspace(.00008,-.00004,n)[:,None]; c=np.empty_like(rr); c[:,0]=np.linspace(20,70,n)
 for k in range(1,len(d)):c[:,k]=c[:,k-1]*(1+rr[:,k])
 return {"dates":d,"close":c,"roster":np.ones_like(c,bool),"assets":np.array([f"T{k:03d}" for k in range(n)])}
def load_dev():
 with np.load(ROOT/"r9/data/J2_DEV_FROM_20201127.npz",allow_pickle=False) as z:
  d0=z["sp500_dates"].astype(str); keep=(d0>=START)&(d0<=END); d=d0[keep]
  # Slice dates first; only authorized interval is selected from price and roster arrays.
  c=z["sp500_adjusted_close"][:,keep].astype(float); ro=z["sp500_roster"][:,keep].astype(bool); assets=z["sp500_assets"].astype(str)
 if not len(d) or d[0]<START or d[-1]>END:raise ValueError("development date guard failed")
 return {"dates":d,"close":c,"roster":ro,"assets":assets}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--synthetic-only",action="store_true");ap.add_argument("--run-dev",action="store_true");a=ap.parse_args()
 if a.synthetic_only:
  o=evaluate(synthetic_panel()); assert set(o["ideas"])==set(IDS) and all(v["n_months"]>0 and len(v["cohorts"])==v["n_months"] for v in o["ideas"].values());print(json.dumps({"status":"PASS","synthetic_only":True,"ideas":len(IDS),"observations":{k:v["n_months"] for k,v in o["ideas"].items()},"outcomes_created":False},indent=2));return
 if not a.run_dev:raise SystemExit("choose --synthetic-only or the single --run-dev execution")
 o=evaluate(load_dev()); dest=ROOT/"r10/S4/DEV_RESULT.json";dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(o,indent=2,allow_nan=False)+"\n",encoding="utf-8");print(json.dumps({k:{q:v for q,v in r.items() if q!="cohorts"} for k,r in o["ideas"].items()},indent=2))
if __name__=="__main__":main()


