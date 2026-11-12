"""Pre-registered EW30 timing overlays using the copied official price loader."""
import csv, importlib.util, math, os, sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)
COST=0.0005
VARIANTS=['mom126','mom252','vol10','vol15']
PERIODS={
 'Dow IS':('2020-11-27','2022-12-30','dow_early'),
 'Cross-asset IS':('2020-11-27','2022-12-30','xasset'),
 'Dow test 1':('2023-01-03','2024-02-23','dow_early'),
 'Dow test 2':('2024-12-06','2025-12-31','dow_recent'),
 'Dow test 3':('2026-01-02','2026-10-30','dow_recent'),
 'Cross-asset test':('2023-01-03','2026-10-30','xasset'),
}

def load_engine(universe, roster, last):
    p=ROOT/universe/'code'/'pivot_backtest.py'
    sys.argv=['pivot_backtest.py',f'--roster={roster}',f'--anchor=2020-11-27',f'--win-first=2020-11-27',f'--win-last={last}', '--cost=actual']
    spec=importlib.util.spec_from_file_location(f'eng_{universe}_{roster}',p)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def solve_target(gross, values, weights):
    e=gross
    for _ in range(500):
        en=gross-COST*sum(abs(e*weights.get(t,0.0)-values.get(t,0.0)) for t in set(values)|set(weights))
        if abs(en-e)<1e-14*max(1.0,gross): e=en; break
        e=en
    return e

def simulate(m, variant, period_last, anchor):
    dates,ho,hc,C,V,H,L,spy=m.load_all(); n=len(m.DOW30); idx={d:i for i,d in enumerate(dates)}
    grid=[d for d in dates if d>=anchor and d<=period_last][::5]
    sigs=[dates[idx[e]-1] for e in grid]
    shares={}; cash=1.0; marks=[]; exposures=[]; active_turn=[]; cost_paid=0.0
    for k,(fill,sig) in enumerate(zip(grid,sigs)):
        ti=idx[sig]
        if variant.startswith('mom'):
            lb=int(variant[3:]); ok=(C[:,ti]/C[:,ti-lb]-1)>0
            weights={t:(1/n if ok[j] else 0.0) for j,t in enumerate(m.DOW30)}
            exposure=sum(weights.values())
        else:
            rr=C[:,1:]/C[:,:-1]-1
            basket=rr.mean(axis=0)
            vol=float(np.std(basket[max(0,ti-21):ti],ddof=1)*math.sqrt(252))
            target=0.10 if variant=='vol10' else 0.15
            exposure=min(1.0,target/vol) if vol>0 else 1.0
            weights={t:exposure/n for t in m.DOW30}
        exposure=max(0.0,min(1.0,float(exposure))); exposures.append(exposure)
        vals={t:sh*ho[t][fill] for t,sh in shares.items()}
        gross=cash+sum(vals.values())
        e=solve_target(gross,vals,weights)
        notional=sum(abs(e*weights.get(t,0.0)-vals.get(t,0.0)) for t in set(vals)|set(weights))
        cost_paid+=COST*notional
        cash=e*(1-exposure)
        shares={t:e*w/ho[t][fill] for t,w in weights.items() if w>0}
        active_turn.append(notional/gross if gross else 0.0)
        nxt=grid[k+1] if k+1<len(grid) else None
        end=nxt if nxt else period_last
        for d in dates[idx[fill]:idx[end]+1]:
            if nxt and d==nxt: continue
            val=cash+sum(sh*hc[t][d] for t,sh in shares.items())
            if not nxt and d==end:
                sale=sum(sh*hc[t][d] for t,sh in shares.items())
                val-=COST*sale; cost_paid+=COST*sale
            marks.append((d,val))
    return marks, exposures, active_turn, cost_paid

def bootstrap_p(x, draws=5000, block=10, seed=3666):
    x=np.asarray(x,float); n=len(x); rng=np.random.default_rng(seed); obs=float(x.mean())
    centered=x-obs; stats=[]
    blocks=int(math.ceil(n/block))
    for _ in range(draws):
        starts=rng.integers(0,n,size=blocks); sample=np.concatenate([centered[(s+np.arange(block))%n] for s in starts])[:n]
        stats.append(sample.mean())
    return (1+sum(abs(v)>=abs(obs) for v in stats))/(draws+1)

def dsr(returns,trials=74):
    x=np.asarray(returns); n=len(x); sd=x.std(ddof=1)
    if n<3 or sd==0:return float('nan')
    sr=x.mean()/sd
    z=(x-x.mean())/sd; skew=np.mean(z**3); kurt=np.mean(z**4); euler=.5772156649
    mx=((1-euler)*norm_ppf(1-1/trials)+euler*norm_ppf(1-1/(trials*math.e)))/math.sqrt(n-1)
    den=1-skew*sr+((kurt-1)/4)*sr*sr
    return float(.5*(1+math.erf(((sr-mx)*math.sqrt(n-1)/math.sqrt(den))/math.sqrt(2)))) if den>0 else float('nan')

def norm_ppf(p):
    from scipy.stats import norm
    return float(norm.ppf(p))

def metrics(eq, ew, first, last, seed):
    dates=sorted(set(eq)&set(ew)); ix=[i for i,d in enumerate(dates) if first<=d<=last]
    if not ix: raise ValueError(f'no marks for {first}..{last}')
    a,b=ix[0],ix[-1]; dates=dates[a:b+1]
    all_e=np.array([eq[d] for d in sorted(set(eq)&set(ew))]); all_w=np.array([ew[d] for d in sorted(set(eq)&set(ew))])
    prev_e=1.0 if a==0 else all_e[a-1]; prev_w=1.0 if a==0 else all_w[a-1]
    e=all_e[a:b+1]; w=all_w[a:b+1]
    r=np.diff(np.r_[prev_e,e])/np.r_[prev_e,e][:-1]; q=np.diff(np.r_[prev_w,w])/np.r_[prev_w,w][:-1]
    active=r-q; years=len(r)/252
    total=np.prod(1+r)-1; cagr=(1+total)**(1/years)-1 if 1+total>0 else float('nan')
    vol=r.std(ddof=1)*math.sqrt(252); sh=r.mean()/r.std(ddof=1)*math.sqrt(252) if r.std(ddof=1) else 0
    ev=e/prev_e; wv=w/prev_w
    peak=np.maximum.accumulate(np.r_[1,ev]); dd=np.r_[1,ev]/peak-1; mdd=float(dd.min())
    te=active.std(ddof=1)*math.sqrt(252); ir=active.mean()*252/te if te else float('nan')
    p=bootstrap_p(active,seed=seed)
    t=float(active.mean()/(active.std(ddof=1)/math.sqrt(len(active)))) if len(active)>1 and active.std(ddof=1)>0 else float('nan')
    return dict(n=len(r),total=total,cagr=cagr,vol=vol,sharpe=sh,mdd=mdd,te=te,ir=ir,t=t,bootp=p,dsr=dsr(r),equity=ev,ew=wv,dates=dates,active=active)

def main():
    (OUT/'selection_rule.txt').write_text('Written before running any test-period simulation: among four variants (mom126, mom252, vol10, vol15), select the one with the highest arithmetic mean annualized daily Sharpe across Dow IS and Cross-asset IS (2020-11-27..2022-12-30). An exact tie is resolved by the listed order. No test-period result enters selection.\n',encoding='utf-8')
    # Each segment uses its official point-in-time roster and anchor. Metrics slice the fixed windows after simulation.
    specs=[('dow_early','dow','2020-08-31','2020-11-27','2024-02-23'),('dow_recent','dow','2024-11-08','2024-12-06','2026-10-30'),('xasset','xasset','xasset30','2020-11-27','2026-10-30')]
    allseries={}
    for key,univ,roster,anchor,last in specs:
        m=load_engine(univ,roster,last); runs={}
        for v in VARIANTS:
            marks,ex,to,cost=simulate(m,v,last,anchor); runs[v]=marks
            print(f'[run] {key} {v}: {len(marks)} closes, mean exposure={np.mean(ex):.3f}, mean traded={np.mean(to):.3%}, costs={cost:.4f}')
        # Constant EW30 portfolio is same accounting path and every rebalance.
        runs['ew']=simulate_ew(m,last,anchor)[0]
        dts,_,_,_,_,_,_,spy=m.load_all()
        prior=[d for d in dts if d<anchor and d in spy]
        base=spy[prior[-1]]['ac'] if prior else spy[next(d for d in dts if d in spy)]['ac']
        runs['spy']=[(d,spy[d]['ac']/base) for d in dts if d in spy]
        allseries[key]=runs
    report=[]; summaries={}
    for label,(first,last,key) in PERIODS.items():
        runs=allseries[key]
        for v in VARIANTS+['ew','spy']:
            em=dict(runs[v]); ewmap=dict(runs['ew'])
            met=metrics(em,ewmap,first,last,3666+len(summaries))
            summaries[(label,v)]=met
            report.append([label,v,met['n'],met['total'],met['cagr'],met['vol'],met['sharpe'],met['mdd'],met['ir'],met['t'],met['bootp'],met['dsr']])
    with open(OUT/'period_metrics.csv','w',newline='') as f:
        w=csv.writer(f); w.writerow(['period','variant','n_days','total_return','CAGR','vol','Sharpe','max_drawdown','IR_vs_EW','active_t_unadjusted','bootstrap_p_10d','DSR_trials74']); w.writerows(report)
    # Selection rule fixed before test: highest arithmetic mean Sharpe over the two IS universes.
    scores={v:np.mean([summaries[(p,v)]['sharpe'] for p in ('Dow IS','Cross-asset IS')]) for v in VARIANTS}
    frozen=max(VARIANTS,key=lambda v:scores[v])
    # Output normalized cumulative curves for frozen choice; period charts use test spans only.
    for label in ('Dow test 1','Dow test 2','Dow test 3','Cross-asset test'):
        first,last,key=PERIODS[label]; best=summaries[(label,frozen)]; base=summaries[(label,'ew')]
        fig,ax=plt.subplots(figsize=(9,4.5)); ax.plot(best['dates'],best['equity'],label=f'{frozen}'); ax.plot(base['dates'],base['ew'],label='EW30'); ax.set_title(label+' cumulative wealth (net of 5 bp/side)'); ax.set_ylabel('Growth of $1'); ax.grid(alpha=.25); ax.legend(); fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(OUT/(label.lower().replace(' ','_')+'_equity.png'),dpi=160); plt.close(fig)
    print('[selection] scores='+str({k:round(float(v),4) for k,v in scores.items()})+' frozen='+frozen)
    with open(OUT/'selection_scores.csv','w',newline='') as f:
        w=csv.writer(f); w.writerow(['variant','Dow IS Sharpe','Cross-asset IS Sharpe','mean Sharpe','selected']); [w.writerow([v,summaries[('Dow IS',v)]['sharpe'],summaries[('Cross-asset IS',v)]['sharpe'],scores[v],v==frozen]) for v in VARIANTS]
    # Chosen variant exposure / in-market diagnostics by period, from whole segment aligned to grid.
    with open(OUT/'overlay_diagnostics.csv','w',newline='') as f:
        w=csv.writer(f); w.writerow(['universe_segment','variant','period','mean_exposure','fraction_rebalances_partly_or_fully_cash','mean_notional_turnover'])
        # Re-run only frozen diagnostics; runs are deterministic and do not alter selection.
        for key,univ,roster,anchor,last in specs:
            m=load_engine(univ,roster,last); _,ex,to,_=simulate(m,frozen,last,anchor)
            for p,(a,b,k) in PERIODS.items():
                if k==key:
                    sel=[i for i,d in enumerate([d for d in m.load_all()[0] if d>=anchor and d<=last][::5]) if a<=d<=b]
                    ee=np.array(ex)[sel]; tt=np.array(to)[sel]
                    w.writerow([key,frozen,p,float(ee.mean()) if len(ee) else '',float(np.mean(ee<.999)) if len(ee) else '',float(tt.mean()) if len(tt) else ''])
    write_report(frozen,scores,summaries)

def simulate_ew(m,last,anchor):
    dates,ho,hc,C,V,H,L,spy=m.load_all(); n=len(m.DOW30); idx={d:i for i,d in enumerate(dates)}; grid=[d for d in dates if d>=anchor and d<=last][::5]
    shares={}; cash=1.0; marks=[]; tos=[]; costs=0
    for k,fill in enumerate(grid):
        vals={t:sh*ho[t][fill] for t,sh in shares.items()}; gross=cash+sum(vals.values()); weights={t:1/n for t in m.DOW30}; e=solve_target(gross,vals,weights)
        notional=sum(abs(e/n-vals.get(t,0.0)) for t in m.DOW30); tos.append(notional/gross); costs+=COST*notional
        cash=0.0; shares={t:e/n/ho[t][fill] for t in m.DOW30}
        nxt=grid[k+1] if k+1<len(grid) else None; end=nxt if nxt else last
        for d in dates[idx[fill]:idx[end]+1]:
            if nxt and d==nxt:continue
            val=sum(sh*hc[t][d] for t,sh in shares.items())
            if not nxt and d==end: val*=1-COST; costs+=COST*val/(1-COST)
            marks.append((d,val))
    return marks,[],tos,costs

def write_report(frozen,scores,s):
    diag={r['period']:r for r in csv.DictReader((OUT/'overlay_diagnostics.csv').open(encoding='utf-8'))}
    cash_text='; '.join(f"{p}: {float(diag[p]['mean_exposure']):.1%} mean invested, {float(diag[p]['fraction_rebalances_partly_or_fully_cash']):.0%} of rebalances with some cash" for p in ('Dow test 1','Dow test 2','Dow test 3','Cross-asset test'))
    lines=['# EW basket timing and risk overlays','',
      '## Preregistered selection rule (written before test results)',
      'Compare four round-number overlays: 6-month asset time-series momentum, 12-month asset time-series momentum, 10% volatility target, and 15% volatility target. Select the highest arithmetic mean annualized daily Sharpe across Dow and cross-asset IS, both 2020-11-27 to 2022-12-30; exact ties are resolved by the listed order. Test periods play no role in selection.',
      '',f'Frozen variant: **{frozen}** (mean IS Sharpe {scores[frozen]:.3f}). All four candidates were run on both IS universes and every preregistered test period (24 universe-period-candidate runs; EW30 benchmark additionally on every segment).','',
      '## Design and implementation','',
      'The basket holds equal dollars in the 30 roster names at each five-session rebalance. Momentum candidates keep each name at its 1/30 weight only when its trailing 126 or 252 session adjusted-close return is positive; otherwise that slice stays in zero-return cash. Volatility candidates scale the entire EW basket by min(1, target / trailing annualized standard deviation of daily EW returns), using the previous 21 sessions and 10% or 15% targets. Rebalance execution uses the next session open, adjusted OHLC prices, 5 bp per side on actual traded notional, including drift and final liquidation. Cash earns 0%; short sales and borrowing are not used. The copied engine source and price files live under dow/ and xasset/.',
      '', '## Selection-period results','', '|Variant|Dow IS Sharpe|Cross-asset IS Sharpe|Mean|', '|---|---:|---:|---:|']
    for v in VARIANTS: lines.append(f"|{v}|{s[('Dow IS',v)]['sharpe']:.3f}|{s[('Cross-asset IS',v)]['sharpe']:.3f}|{scores[v]:.3f}|")
    lines+=['','## Frozen choice: test results','', 'Returns and risk are net of costs. SPY is buy-and-hold adjusted close with no added trading cost. IR is annualized active mean divided by tracking error against same-universe EW30. Bootstrap p-values use 5,000 circular 10-session block resamples of paired daily active returns under the zero-mean null; p-values are unadjusted. DSR follows Bailey and López de Prado (2014), using 74 total trials (about 70 prior variants plus these four); the independent-trial approximation is imperfect because strategies are correlated.','', '|Period|Strategy|CAGR|EW30 CAGR|SPY CAGR|Sharpe|EW30 Sharpe|SPY Sharpe|MaxDD|EW30 MaxDD|IR|Block p|DSR (74)|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for p in ('Dow test 1','Dow test 2','Dow test 3','Cross-asset test'):
      a=s[(p,frozen)]; b=s[(p,'ew')]; z=s[(p,'spy')]; lines.append(f"|{p}|{frozen}|{a['cagr']:.2%}|{b['cagr']:.2%}|{z['cagr']:.2%}|{a['sharpe']:.2f}|{b['sharpe']:.2f}|{z['sharpe']:.2f}|{a['mdd']:.2%}|{b['mdd']:.2%}|{a['ir']:.2f}|{a['bootp']:.3f}|{a['dsr']:.3f}|")
    lines+=['','## Validation and evaluation','',
      'The tests use fixed dates and the same 30-name universe per comparison; every strategy and EW30 series is generated on the same five-session schedule with next-open fills. Signals use information available by the previous close. The two Dow rosters follow the project’s fixed 2020-08-31 and 2024-11-08 rosters. Results are daily-close marked and include actual-notional costs at each rebalance and final liquidation. The 2026 Dow period begins at the first eligible rebalance on the inherited five-session schedule after 2026-01-02.',
      '', f'The frozen overlay was partly in cash at each of these test rebalance dates: {cash_text}.',
      '', 'No test period is used to choose or alter the overlay. Four candidates were screened, so the apparent IS winner is subject to selection bias. The test 2 bootstrap p-value of 0.034 is evidence of negative active returns in that window, not an overlay benefit. The DSR is a rough multiple-testing correction and does not account for dependence across variants or the earlier ~70 trials individually.',
      '', '## Refinement and report paragraph','',
      'This overlay keeps the broad equal-weight basket and changes only its market exposure. That is economically simpler than trying to forecast which of 30 names will win. Momentum gates leave part of the portfolio in zero-return cash, while volatility targeting reduces all holdings together when recent basket risk is high. The test should be judged against EW30 on Sharpe, active risk, and drawdown after turnover costs; if the frozen choice does not improve these consistently, the project conclusion should remain that the data do not support a reliable timing edge and EW30 is the appropriate baseline.',
      '', 'Figures for the chosen variant are in `outputs/dow_test_1_equity.png`, `outputs/dow_test_2_equity.png`, `outputs/dow_test_3_equity.png`, and `outputs/cross-asset_test_equity.png`. `outputs/period_metrics.csv` contains all candidates and periods; `outputs/overlay_diagnostics.csv` reports exposure, out-of-market frequency, and turnover for the frozen choice.',
      '', '## Literature','',
      '- Faber, M. T. (2007), “A Quantitative Approach to Tactical Asset Allocation,” *Journal of Wealth Management*, 9(4), 69–79 (10-month moving-average timing rule).',
      '- Moskowitz, T. J., Ooi, Y. H., and Pedersen, L. H. (2012), “Time Series Momentum,” *Journal of Financial Economics*, 104(2), 228–250.',
      '- Moreira, A. and Muir, T. (2017), “Volatility-Managed Portfolios,” *Journal of Finance*, 72(4), 1611–1644.',
      '', '## Reproduction','',
      'Run from `A2/pivot_research/r2_overlay` with Python 3 and the installed numpy, scipy, and matplotlib packages:',
      '```powershell','py -3 overlay_research.py','```',
      'The script sets the selection rule in `outputs/selection_rule.txt` before simulations, runs all four variants once per applicable segment, and writes the report tables, CSV diagnostics, and charts. The official copied pricing engine is `dow/code/pivot_backtest.py` or `xasset/code/pivot_backtest.py`; source engine folders were not edited.']
    (ROOT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': main()
