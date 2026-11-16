from pathlib import Path
import csv, math, json
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import norm, skew, kurtosis

ROOT=Path(__file__).resolve().parent
B=10000
BLOCK=21
TRIALS=73  # about 70 prior reported trials plus the 3 tested candidates
SEED=3666

WINDOWS=[
    ('Dow 2023-01-03 to 2024-02-23','Dow','test_dow_oos1_actualcost'),
    ('Dow 2024-12-06 to 2025-12-31','Dow','test_dow_oos2_actualcost'),
    ('Dow 2026-01-02 to 2026-10-30','Dow','test_dow_2026_actualcost'),
    ('Cross-asset 2023-01-03 to 2026-10-30','xasset','test_xasset_actualcost'),
]

def read_equity(universe,tag):
    path=ROOT/universe/'outputs_rerun'/f'{tag}_equity_variants.csv'
    with path.open(newline='') as f:
        rows=list(csv.DictReader(f))
    keys=['volrev21_a05_tilt','ew','spy']
    dates=[r['date'] for r in rows]
    vals={k:np.array([float(r[k]) for r in rows]) for k in keys}
    return dates,vals

def returns(levels):
    return np.diff(np.r_[1.0,levels])/np.r_[1.0,levels][:-1]

def maxdd(r):
    curve=np.r_[1.0,np.cumprod(1+r)]
    return float(np.min(curve/np.maximum.accumulate(curve)-1))

def metrics(r):
    n=len(r); growth=float(np.prod(1+r)); ann=growth**(252/n)-1 if growth>0 else -1.0
    vol=float(np.std(r,ddof=0)*math.sqrt(252))
    sr=float(np.mean(r)/np.std(r,ddof=0)*math.sqrt(252)) if np.std(r,ddof=0)>0 else 0.0
    return {'n':n,'total_return':growth-1,'cagr':ann,'vol':vol,'sharpe':sr,'maxdd':maxdd(r)}

def bootstrap_p(x,seed):
    x=np.asarray(x,dtype=float); n=len(x); obs=float(x.mean()); centered=x-obs
    rng=np.random.default_rng(seed); nblocks=math.ceil(n/BLOCK); offsets=np.arange(BLOCK)
    ge=0; done=0; batch=250
    while done<B:
        m=min(batch,B-done)
        starts=rng.integers(0,n,size=(m,nblocks))
        ix=((starts[:,:,None]+offsets[None,None,:])%n).reshape(m,-1)[:,:n]
        bm=centered[ix].mean(axis=1)
        ge+=int(np.sum(np.abs(bm)>=abs(obs)))
        done+=m
    return (ge+1)/(B+1),obs

def dsr(r,sr_ann):
    n=len(r); sr_daily=float(np.mean(r)/np.std(r,ddof=0)) if np.std(r,ddof=0)>0 else 0.0
    sk=float(skew(r,bias=False)) if n>2 else 0.0
    ku=float(kurtosis(r,fisher=False,bias=False)) if n>3 else 3.0
    inner=1-sk*sr_daily+((ku-1)/4)*(sr_daily**2)
    se_ann=math.sqrt(252*max(inner,1e-12)/max(n-1,1))
    gamma=0.5772156649015329
    emax=(1-gamma)*norm.ppf(1-1/TRIALS)+gamma*norm.ppf(1-1/(TRIALS*math.e))
    threshold=math.sqrt(252/n)*emax
    prob=float(norm.cdf((sr_ann-threshold)/se_ann)) if se_ann>0 else float(sr_ann>threshold)
    return prob,threshold,se_ann

def trading_stats(universe,tag,suffix):
    p=ROOT/universe/'outputs_rerun'/f'{tag}_{suffix}_costdetail.csv'
    with p.open(newline='') as f: rows=list(csv.DictReader(f))
    factors=np.array([float(z['cost_factor']) for z in rows])
    notionals=np.array([float(z['notional_traded'])/float(z['pretrade_equity']) for z in rows[1:]])
    # Engine charges a final 5 bp liquidation at the terminal close in addition to listed rebalance costs.
    n=len(read_equity(universe,tag)[0])
    drag=1-math.exp((np.log(factors).sum()+math.log(1-0.0005))*252/n)
    return float(notionals.mean()) if len(notionals) else 0.0,float(drag)

results=[]
fig,axes=plt.subplots(2,2,figsize=(14,9),constrained_layout=True)
for j,(label,universe,tag) in enumerate(WINDOWS):
    dates,levels=read_equity(universe,tag)
    xdates=[datetime.strptime(d,'%Y-%m-%d') for d in dates]
    rr={k:returns(v) for k,v in levels.items()}
    stats={k:metrics(v) for k,v in rr.items()}
    active=rr['volrev21_a05_tilt']-rr['ew']
    p,obs=bootstrap_p(active,SEED+j)
    ir=float(active.mean()/active.std(ddof=0)*math.sqrt(252)) if active.std(ddof=0)>0 else 0.0
    dsr_prob,dsr_threshold,dsr_se=dsr(rr['volrev21_a05_tilt'],stats['volrev21_a05_tilt']['sharpe'])
    to_s,cost_s=trading_stats(universe,tag,'volrev21_a05_tilt')
    to_e,cost_e=trading_stats(universe,tag,'ew_tilt')
    row={'period':label,'universe':universe,'tag':tag,'sessions':len(active),
         'strategy':stats['volrev21_a05_tilt'],'ew':stats['ew'],'spy':stats['spy'],
         'information_ratio_vs_ew':ir,'active_mean_daily':obs,'block_bootstrap_p_two_sided':p,
         'block_length_sessions':BLOCK,'bootstrap_replicates':B,'deflated_sharpe_probability':dsr_prob,
         'dsr_expected_max_threshold':dsr_threshold,'dsr_se':dsr_se,'trial_count':TRIALS,
         'strategy_turnover_per_rebalance':to_s,'strategy_annual_cost_drag':cost_s,
         'ew_turnover_per_rebalance':to_e,'ew_annual_cost_drag':cost_e}
    results.append(row)
    ax=axes.flat[j]
    for key,name,color in [('volrev21_a05_tilt','Selected tilt','#1f77b4'),('ew','EW30','#555555'),('spy','SPY','#d17c00')]:
        ax.plot(xdates,levels[key],label=name,color=color,lw=1.5)
    ax.set_title(label); ax.set_ylabel('Growth of $1'); ax.grid(alpha=.25)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4,maxticks=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.tick_params(axis='x',rotation=25)
    if j==0: ax.legend(frameon=False)

fig.suptitle('Frozen volatility-scaled 21-day reversal tilt: net equity after 5 bp per-side costs')
fig.savefig(ROOT/'chosen_variant_test_periods.png',dpi=180)
plt.close(fig)
(ROOT/'test_metrics.json').write_text(json.dumps(results,indent=2))

# Write full tables for direct incorporation in REPORT.md.
lines=['# Held-out test results','',
       'Returns, Sharpe, and drawdowns are computed from daily close-marked net equity and include 5 bp per-side transaction costs. CAGR uses 252 sessions per year. The benchmark EW30 is reset to equal weights on the same 21-session grid. SPY is buy-and-hold on the engine calendar. Information ratio and p-values use paired daily strategy-minus-EW30 returns.',
       '', '| Test window | Tilt CAGR | EW30 CAGR | SPY CAGR | Tilt Sharpe | EW30 Sharpe | SPY Sharpe | Tilt max DD | EW30 max DD | SPY max DD | IR vs EW30 | Block p | DSR prob. |',
       '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for z in results:
    s,e,p=z['strategy'],z['ew'],z['spy']
    lines.append(f"| {z['period']} | {s['cagr']:.1%} | {e['cagr']:.1%} | {p['cagr']:.1%} | {s['sharpe']:.2f} | {e['sharpe']:.2f} | {p['sharpe']:.2f} | {s['maxdd']:.1%} | {e['maxdd']:.1%} | {p['maxdd']:.1%} | {z['information_ratio_vs_ew']:.2f} | {z['block_bootstrap_p_two_sided']:.3f} | {z['deflated_sharpe_probability']:.3f} |")
lines += ['', 'Turnover is average actual traded notional divided by pretrade equity per rebalance, excluding the initial investment. Cost drag is annualized geometric drag from actual-cost factors, including final liquidation.', '', '| Test window | Tilt turnover / rebalance | EW30 turnover / rebalance | Tilt cost drag / yr | EW30 cost drag / yr |', '|---|---:|---:|---:|---:|']
for z in results:
    lines.append(f"| {z['period']} | {z['strategy_turnover_per_rebalance']:.1%} | {z['ew_turnover_per_rebalance']:.1%} | {z['strategy_annual_cost_drag']:.2%} | {z['ew_annual_cost_drag']:.2%} |")
(ROOT/'TEST_TABLES.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
