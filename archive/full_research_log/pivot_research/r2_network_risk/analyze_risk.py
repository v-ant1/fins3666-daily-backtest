from pathlib import Path
import csv, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import norm
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'evaluation'; OUT.mkdir(exist_ok=True)
MODES=['ew','ivol63','low_degree','low_eigen','inv_heat','hrp','degree_ivol','heat_ivol']
LABEL={'ew':'EW30','ivol63':'Inverse volatility','low_degree':'Low degree','low_eigen':'Low eigenvector centrality','inv_heat':'Inverse heat connectivity','hrp':'HRP','degree_ivol':'Low degree × inverse volatility','heat_ivol':'Inverse heat × inverse volatility'}
def read(path):
 with path.open(newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
 return [r['date'][:10] for r in rows], {k:np.array([float(r[k]) for r in rows]) for k in rows[0] if k!='date'}
def bootstrap(x,block=10,draws=5000,seed=3666):
 x=np.asarray(x); n=len(x); obs=abs(x.mean()); z=x-x.mean(); needed=math.ceil(n/block); rng=np.random.default_rng(seed); offsets=np.arange(block); nbetter=0
 for _ in range(draws):
  starts=rng.integers(0,n,size=needed); sample=np.concatenate([z[(s+offsets)%n] for s in starts])[:n]
  nbetter += abs(sample.mean())>=obs
 return (nbetter+1)/(draws+1)
def dsr(x,trials=78):
 x=np.asarray(x); n=len(x); sd=x.std(ddof=1)
 if n<3 or sd==0:return float('nan')
 sr=x.mean()/sd; z=(x-x.mean())/sd; skew=(z**3).mean(); kurt=(z**4).mean(); e=0.5772156649015329
 maxz=((1-e)*norm.ppf(1-1/trials)+e*norm.ppf(1-1/(trials*math.e)))/math.sqrt(n-1)
 den=1-skew*sr+((kurt-1)/4)*sr*sr
 return float(norm.cdf((sr-maxz)*math.sqrt(n-1)/math.sqrt(den))) if den>0 else float('nan')
def metric(path,lo,hi,mode):
 dates,v=read(path); idx=[i for i,d in enumerate(dates) if lo<=d<=hi]
 if not idx: raise ValueError(f'no rows in {path} {lo}..{hi}')
 strat=[]; ew=[]; spy=[]; prev_idx=idx[0]-1
 for i in idx:
  strat.append(v[mode][i]/v[mode][prev_idx]-1 if prev_idx>=0 else v[mode][i]-1)
  ew.append(v['ew'][i]/v['ew'][prev_idx]-1 if prev_idx>=0 else v['ew'][i]-1)
  spy.append(v['spy'][i]/v['spy'][prev_idx]-1 if prev_idx>=0 else v['spy'][i]-1)
  prev_idx=i
 r=np.array(strat); e=np.array(ew); p=np.array(spy); active=r-e
 def calc(a):
  total=float(np.prod(1+a)-1); cagr=(1+total)**(252/len(a))-1 if 1+total>0 else -1
  sd=a.std(ddof=1); sh=float(a.mean()/sd*math.sqrt(252)) if sd else 0
  curve=np.r_[1,np.cumprod(1+a)]; dd=curve/np.maximum.accumulate(curve)-1
  return total,cagr,sh,float(dd.min())
 total,cagr,sh,mdd=calc(r); et,ec,esh,edd=calc(e); _,_,_,_=calc(p)
 te=float(active.std(ddof=1)*math.sqrt(252)); ir=float(active.mean()*252/te) if te else float('nan')
 wealth=np.r_[1,np.cumprod(1+r)]; ddates=[dates[i] for i in idx]
 return {'n':len(r),'total':total,'cagr':cagr,'sharpe':sh,'mdd':mdd,'ew_total':et,'ew_cagr':ec,'ew_sharpe':esh,'ew_mdd':edd,'spy_total':float(np.prod(1+p)-1),'te':te,'ir':ir,'r':r,'e':e,'pseries':p,'wealth':wealth[1:],'drawdown':wealth[1:]/np.maximum.accumulate(wealth)[1:]-1,'dates':ddates,'pval':bootstrap(active) if mode=='inv_heat' else float('nan'),'dsr':dsr(r) if mode=='inv_heat' else float('nan')}
def turnover(path,lo,hi):
 vals=[]
 with path.open(newline='',encoding='utf-8-sig') as f:
  for i,row in enumerate(csv.DictReader(f)):
   if i==0: continue  # initial funded position; not a rebalance trade
   if lo<=row['rebalance_date']<=hi and float(row['pretrade_equity'])>0 and float(row['notional_traded'])>0: vals.append(float(row['notional_traded'])/float(row['pretrade_equity']))
 return float(np.mean(vals)) if vals else 0
selection={}; selection_to={}
for label,u,tag in [('Dow IS','dow','selection_dow'),('ETF IS','xasset','selection_xasset')]:
 for m in MODES:
  selection[label,m]=metric(ROOT/u/'outputs_rerun'/f'{tag}_equity_variants.csv','2020-11-27','2022-12-30',m)
  selection_to[label,m]=turnover(ROOT/u/'outputs_rerun'/f'{tag}_{m}_costdetail.csv','2020-11-27','2022-12-30')
windows=[('Dow OOS1','dow/outputs_rerun/test_dow_earlier_equity_variants.csv','2023-01-03','2024-02-23','dow','test_dow_earlier'),('Dow OOS2','dow/outputs_rerun/test_dow_recent_equity_variants.csv','2024-12-06','2025-12-31','dow','test_dow_recent'),('Dow 2026','dow/outputs_rerun/test_dow_recent_equity_variants.csv','2026-01-02','2026-10-30','dow','test_dow_recent'),('Cross-asset OOS','xasset/outputs_rerun/test_xasset_equity_variants.csv','2023-01-03','2026-10-30','xasset','test_xasset')]
tests={}; test_to={}
for label,path,lo,hi,u,tag in windows:
 for m in MODES:
  tests[label,m]=metric(ROOT/path,lo,hi,m); test_to[label,m]=turnover(ROOT/u/'outputs_rerun'/f'{tag}_{m}_costdetail.csv',lo,hi)
lines=['# Selection-period results','','The selection-period table uses only the registered IS windows. Return and Sharpe are after actual-trade costs; turnover is mean traded notional / pre-trade equity per rebalance. Excess is annualized CAGR minus same-universe EW30 CAGR.','', '| Portfolio | Dow CAGR | Dow excess | Dow Sharpe | Dow maxDD | Dow turnover | ETF CAGR | ETF excess | ETF Sharpe | ETF maxDD | ETF turnover | Avg Sharpe |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for m in MODES:
 a=selection['Dow IS',m]; b=selection['ETF IS',m]
 lines.append(f"| {LABEL[m]} | {a['cagr']:.2%} | {(a['cagr']-a['ew_cagr'])*100:+.2f} pp | {a['sharpe']:.2f} | {a['mdd']:.2%} | {selection_to['Dow IS',m]:.1%} | {b['cagr']:.2%} | {(b['cagr']-b['ew_cagr'])*100:+.2f} pp | {b['sharpe']:.2f} | {b['mdd']:.2%} | {selection_to['ETF IS',m]:.1%} | {(a['sharpe']+b['sharpe'])/2:.2f} |")
lines+=['','## Test-period results: all registered portfolios','','All portfolios are shown descriptively; the frozen choice was not changed after selection.','', '| Period | Portfolio | Total return | CAGR | Sharpe | IR vs EW30 | MaxDD | Turnover |','|---|---|---:|---:|---:|---:|---:|---:|']
for label,*_ in windows:
 for m in MODES:
  a=tests[label,m]; lines.append(f"| {label} | {LABEL[m]} | {a['total']:.2%} | {a['cagr']:.2%} | {a['sharpe']:.2f} | {a['ir']:.2f} | {a['mdd']:.2%} | {test_to[label,m]:.1%} |")
lines+=['','## Frozen inverse-heat choice versus benchmarks','','The p-value is a two-sided circular 10-session block bootstrap on daily active returns, demeaned under the null, 5,000 draws, seed 3666, plus-one correction. DSR is the estimated probability of exceeding the expected best Sharpe among 78 effective cumulative trials.','', '| Period | Strategy return | EW30 return | SPY return | CAGR | Sharpe | EW Sharpe | MaxDD | EW MaxDD | IR | TE | Block p | DSR | Turnover |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for label,*_ in windows:
 a=tests[label,'inv_heat']; lines.append(f"| {label} | {a['total']:.2%} | {a['ew_total']:.2%} | {a['spy_total']:.2%} | {a['cagr']:.2%} | {a['sharpe']:.2f} | {a['ew_sharpe']:.2f} | {a['mdd']:.2%} | {a['ew_mdd']:.2%} | {a['ir']:.2f} | {a['te']:.2%} | {a['pval']:.3f} | {a['dsr']:.1%} | {test_to[label,'inv_heat']:.1%} |")
(OUT/'TABLES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
# Plot frozen choice against same-run EW and SPY.
fig,axes=plt.subplots(2,2,figsize=(12,8)); axes=axes.ravel()
for ax,(label,*_) in zip(axes,windows):
 d=tests[label,'inv_heat']; x=np.arange(len(d['dates'])); ax.plot(x,d['wealth'],label='Frozen inverse heat',lw=1.5); ax.plot(x,np.cumprod(1+d['e']),label='EW30',ls='--',lw=1.3); ax.plot(x,np.cumprod(1+d['pseries']),label='SPY',ls=':',lw=1.1); ticks=np.linspace(0,len(x)-1,min(5,len(x)),dtype=int); ax.set_xticks(ticks); ax.set_xticklabels([d['dates'][i] for i in ticks],rotation=25,ha='right'); ax.set_title(label); ax.set_ylabel('Growth of $1'); ax.grid(alpha=.25)
axes[0].legend(fontsize=8); fig.tight_layout(); fig.savefig(OUT/'frozen_choice_equity.png',dpi=180); plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(12,8)); axes=axes.ravel()
for ax,(label,*_) in zip(axes,windows):
 d=tests[label,'inv_heat']; x=np.arange(len(d['dates'])); ax.plot(x,d['drawdown'],lw=1.3); ticks=np.linspace(0,len(x)-1,min(5,len(x)),dtype=int); ax.set_xticks(ticks); ax.set_xticklabels([d['dates'][i] for i in ticks],rotation=25,ha='right'); ax.axhline(0,color='black',lw=.6); ax.set_title(label+' drawdown'); ax.grid(alpha=.25)
fig.tight_layout(); fig.savefig(OUT/'frozen_choice_drawdown.png',dpi=180); plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(12,8)); axes=axes.ravel()
for ax,(label,*_) in zip(axes,windows):
 d=tests[label,'inv_heat']; active=d['r']-d['e']; rolling=[np.prod(1+active[max(0,i-62):i+1])-1 if i>=62 else np.nan for i in range(len(active))]; x=np.arange(len(d['dates'])); ax.plot(x,rolling,lw=1.2); ticks=np.linspace(0,len(x)-1,min(5,len(x)),dtype=int); ax.set_xticks(ticks); ax.set_xticklabels([d['dates'][i] for i in ticks],rotation=25,ha='right'); ax.axhline(0,color='black',lw=.6); ax.set_title(label+' rolling 63-session active return'); ax.grid(alpha=.25)
fig.tight_layout(); fig.savefig(OUT/'frozen_choice_rolling63.png',dpi=180); plt.close(fig)
print('wrote selection and test tables plus frozen-choice charts')

