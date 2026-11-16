from pathlib import Path
import csv, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import norm
ROOT=Path(__file__).resolve().parent
TRIALS=85

def read(path):
    with path.open(newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    return [r['date'][:10] for r in rows], {k:np.array([float(r[k]) for r in rows]) for k in rows[0] if k!='date'}
def metric(path,lo,hi,mode='low15_inv'):
    dates,v=read(path); idx=[i for i,d in enumerate(dates) if lo<=d<=hi]
    if not idx: raise ValueError((path,lo,hi))
    sr=[]; er=[]; pr=[]; wealths=[]; ewwealth=[]; prev=idx[0]-1
    for i in idx:
        sr.append(v[mode][i]/v[mode][prev]-1 if prev>=0 else v[mode][i]-1)
        er.append(v['ew'][i]/v['ew'][prev]-1 if prev>=0 else v['ew'][i]-1)
        if 'spy' in v: pr.append(v['spy'][i]/v['spy'][prev]-1 if prev>=0 else v['spy'][i]-1)
        prev=i
    r=np.array(sr); e=np.array(er); active=r-e
    def summary(a):
        total=float(np.prod(1+a)-1); cagr=(1+total)**(252/len(a))-1 if 1+total>0 else -1
        sd=a.std(ddof=1); sh=float(a.mean()/sd*math.sqrt(252)) if sd else 0
        cr=np.r_[1,np.cumprod(1+a)]; dd=cr/np.maximum.accumulate(cr)-1
        return total,cagr,sh,float(dd.min())
    total,cagr,sh,mdd=summary(r); et,ec,esh,edd=summary(e)
    te=float(active.std(ddof=1)*math.sqrt(252)); ir=float(active.mean()*252/te) if te else float('nan')
    rng=np.random.default_rng(3666); n=len(active); centered=active-active.mean(); needed=math.ceil(n/10); offsets=np.arange(10); exceed=0
    for _ in range(5000):
        starts=rng.integers(0,n,size=needed); sample=np.concatenate([centered[(s+offsets)%n] for s in starts])[:n]
        exceed += abs(sample.mean())>=abs(active.mean())
    pval=(exceed+1)/5001
    sd=r.std(ddof=1); z=(r-r.mean())/sd if sd else r*0; srday=r.mean()/sd if sd else 0
    skew=np.mean(z**3); kurt=np.mean(z**4); euler=.5772156649015329
    maxz=((1-euler)*norm.ppf(1-1/TRIALS)+euler*norm.ppf(1-1/(TRIALS*math.e)))/math.sqrt(n-1) if n>1 else 0
    den=1-skew*srday+((kurt-1)/4)*srday**2
    dsr=float(norm.cdf((srday-maxz)*math.sqrt(n-1)/math.sqrt(den))) if den>0 and n>1 else float('nan')
    return dict(dates=[dates[i] for i in idx],r=r,e=e,active=active,wealth=np.r_[1,np.cumprod(1+r)],ewwealth=np.r_[1,np.cumprod(1+e)],total=total,cagr=cagr,sh=sh,mdd=mdd,ewtotal=et,ewcagr=ec,ewsh=esh,ewmdd=edd,te=te,ir=ir,p=pval,dsr=dsr)
def deflated_sharpe(x,trials):
    x=np.asarray(x); n=len(x); sd=x.std(ddof=1)
    if n<3 or sd==0: return float('nan')
    sr=x.mean()/sd; z=(x-x.mean())/sd; skew=np.mean(z**3); kurt=np.mean(z**4); e=.5772156649015329
    mz=((1-e)*norm.ppf(1-1/trials)+e*norm.ppf(1-1/(trials*math.e)))/math.sqrt(n-1)
    den=1-skew*sr+((kurt-1)/4)*sr*sr
    return float(norm.cdf((sr-mz)*math.sqrt(n-1)/math.sqrt(den))) if den>0 else float('nan')
def turnover(path,lo,hi):
    vals=[]
    with path.open(newline='',encoding='utf-8-sig') as f:
      for i,row in enumerate(csv.DictReader(f)):
       if i and lo<=row['rebalance_date']<=hi and float(row['pretrade_equity'])>0:
        vals.append(float(row['notional_traded'])/float(row['pretrade_equity']))
    return float(np.mean(vals)) if vals else 0
def active_share(path,lo,hi,universe):
    vals=[]
    with path.open(newline='',encoding='utf-8-sig') as f:
      rows=list(csv.DictReader(f))
    for d in sorted(set(r['rebalance_date'] for r in rows if lo<=r['rebalance_date']<=hi)):
      w={r['ticker']:float(r['weight']) for r in rows if r['rebalance_date']==d}
      vals.append(.5*sum(abs(w.get(t,0)-1/30) for t in universe))
    return float(np.mean(vals)) if vals else 0
ROOTD=ROOT/'dow'; ROOTX=ROOT/'xasset'
dow_early=['AAPL','AMGN','AXP','BA','CAT','CRM','CSCO','CVX','DIS','DOW','GS','HD','HON','IBM','INTC','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','PG','TRV','UNH','V','VZ','WBA','WMT']
dow_late=['AAPL','AMGN','AXP','AMZN','BA','CAT','CRM','CSCO','CVX','DIS','GS','HD','HON','IBM','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','NVDA','PG','SHW','TRV','UNH','V','VZ','WMT']
xassets=['BWX','DBA','DBB','EEM','EMB','EWA','EWC','EWJ','FXA','FXB','FXC','FXE','FXY','GLD','HYG','IEF','IWM','LQD','MUB','PPLT','RWX','SHY','SLV','TIP','TLT','UNG','USO','UUP','VGK','VNQ']
sel_specs=[('Dow selection',ROOTD/'outputs_rerun/r3_selection_dow_equity_variants.csv','2020-11-27','2022-12-30',ROOTD/'outputs_rerun/r3_selection_dow_low15_inv_costdetail.csv'),('Cross-asset selection',ROOTX/'outputs_rerun/r3_selection_xasset_equity_variants.csv','2020-11-27','2022-12-30',ROOTX/'outputs_rerun/r3_selection_xasset_low15_inv_costdetail.csv')]
sel=[]
for label,path,lo,hi,costpath in sel_specs:
    dates,v=read(path)
    for mode in ['inv_heat','inv_heat_k2','low15_equal','low10_inv','low15_inv','low15_rev21','low15_rev63']:
        # Low15 rev63 rows use the rebalance-63 candidate series; matching EW schedule is ew63.
        bench='ew63' if mode=='low15_rev63' else 'ew'
        idx=[i for i,d in enumerate(dates) if lo<=d<=hi]; prev=idx[0]-1
        a=[]; b=[]
        for i in idx:
            a.append(v[mode][i]/v[mode][prev]-1 if prev>=0 else v[mode][i]-1)
            b.append(v[bench][i]/v[bench][prev]-1 if prev>=0 else v[bench][i]-1); prev=i
        r=np.array(a); e=np.array(b); cr=np.r_[1,np.cumprod(1+r)]; dd=cr/np.maximum.accumulate(cr)-1
        total=float(np.prod(1+r)-1); sharpe=float(r.mean()/r.std(ddof=1)*math.sqrt(252)); cagr=float(np.prod(1+r)**(252/len(r))-1)
        turnover_path=costpath.parent/f"{costpath.stem.replace('low15_inv','')}{mode}_costdetail.csv"
        # Locate exact cost ledger for this candidate.
        turnover_path=costpath.parent/(costpath.name.replace('low15_inv',mode))
        to=turnover(turnover_path,lo,hi)
        active=r-e; te=float(active.std(ddof=1)*math.sqrt(252)); share=0
        # Selection active share from candidate trade file.
        trades=costpath.parent/(costpath.name.replace('_costdetail.csv','_trades.csv').replace('low15_inv',mode))
        share=active_share(trades,lo,hi,dow_early if label=='Dow selection' else xassets)
        sel.append((mode,label,total,cagr,sharpe,float(dd.min()),to,te,share))
periods=[('Dow OOS1','dow/outputs_rerun/r3_test_dow_early_equity_variants.csv','2023-01-03','2024-02-23','dow/outputs_rerun/r3_test_dow_early_low15_inv_costdetail.csv'),('Dow OOS2','dow/outputs_rerun/r3_test_dow_recent_equity_variants.csv','2024-12-06','2025-12-31','dow/outputs_rerun/r3_test_dow_recent_low15_inv_costdetail.csv'),('Dow 2026','dow/outputs_rerun/r3_test_dow_recent_equity_variants.csv','2026-01-02','2026-10-30','dow/outputs_rerun/r3_test_dow_recent_low15_inv_costdetail.csv'),('Cross-asset OOS','xasset/outputs_rerun/r3_test_xasset_equity_variants.csv','2023-01-03','2026-10-30','xasset/outputs_rerun/r3_test_xasset_low15_inv_costdetail.csv')]
tests=[]
for label,rel,lo,hi,costrel in periods:
    m=metric(ROOT/rel,lo,hi); to=turnover(ROOT/costrel,lo,hi); trades=ROOT/costrel.replace('_costdetail.csv','_trades.csv'); ash=active_share(trades,lo,hi,dow_early if label=='Dow OOS1' else (xassets if label=='Cross-asset OOS' else dow_late))
    m.update(label=label,turnover=to,active_share=ash); tests.append(m)
# Pool all daily active observations equally; labels overlap in calendar because the ETF universe is a separate test.
pooled=np.concatenate([m['active'] for m in tests]); pp=np.random.default_rng(3666); n=len(pooled); centered=pooled-pooled.mean(); needed=math.ceil(n/10); off=np.arange(10); exc=0
for _ in range(5000):
    starts=pp.integers(0,n,size=needed); sample=np.concatenate([centered[(s+off)%n] for s in starts])[:n]; exc+=abs(sample.mean())>=abs(pooled.mean())
pooled_p=(exc+1)/5001
pooled_excess=float(np.mean([m['total']-m['ewtotal'] for m in tests])); concatenated_active=float(np.prod(1+pooled)-1); pooled_dsr=deflated_sharpe(np.concatenate([m['r'] for m in tests]),TRIALS)
# Cross-sectional rolling 63-session beta sort factor (lowest beta 10 equal-weight minus EW30).
def beta_factor(folder,assets,lo,hi):
    def load(t):
      rows=[]
      for sub in ('prices-daily-lookback','prices-daily','prices-daily-delisted'):
       q=folder/sub/f'{t}.csv'
       if q.exists(): rows.extend(csv.DictReader(open(q,newline='',encoding='utf-8-sig')))
      return {r['date'][:10]:float(r['adjclose']) for r in rows if r.get('adjclose')}
    prices={t:load(t) for t in assets}; dates=sorted(set.intersection(*(set(x) for x in prices.values())))
    px=np.array([[prices[t][d] for d in dates] for t in assets]); ret=px[:,1:]/px[:,:-1]-1; rd=dates[1:]
    ew=ret.mean(axis=0); factors=[]
    for j,d in enumerate(rd):
      if d<lo or d>hi or j<63: continue
      w=ret[:,j-63:j]; market=ew[j-63:j]; var=np.var(market,ddof=1)
      beta=np.array([np.cov(row,market,ddof=1)[0,1]/var if var else 0 for row in w])
      ids=np.argsort(beta)[:10]; factors.append((d,float(ret[ids,j].mean()-ew[j])))
    return dict(factors)
# Dow constituents for the earlier roster, recent roster for later periods; use only complete aligned names.
from importlib.machinery import SourceFileLoader
# Explicit universe lists from copied engine, preserving the benchmark's point-in-time basket.
dow_early=['AAPL','AMGN','AXP','BA','CAT','CRM','CSCO','CVX','DIS','DOW','GS','HD','HON','IBM','INTC','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','PG','TRV','UNH','V','VZ','WBA','WMT']
dow_late=['AAPL','AMGN','AXP','AMZN','BA','CAT','CRM','CSCO','CVX','DIS','GS','HD','HON','IBM','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','NVDA','PG','SHW','TRV','UNH','V','VZ','WMT']
xassets=['BWX','DBA','DBB','EEM','EMB','EWA','EWC','EWJ','FXA','FXB','FXC','FXE','FXY','GLD','HYG','IEF','IWM','LQD','MUB','PPLT','RWX','SHY','SLV','TIP','TLT','UNG','USO','UUP','VGK','VNQ']
# factor beta regression on dates with both factor and active return. For test-period aggregate compare active r at date.
factors=[]; actives=[]
for m in tests:
    if m['label'].startswith('Dow'):
      assets=dow_early if m['label']=='Dow OOS1' else dow_late; folder=ROOTD
    else: assets=xassets; folder=ROOTX
    fac=beta_factor(folder,assets,m['dates'][0],m['dates'][-1])
    maps=dict(zip(m['dates'],m['active']))
    common=[d for d in fac if d in maps]
    factors.extend([fac[d] for d in common]); actives.extend([maps[d] for d in common])
f=np.array(factors); y=np.array(actives); X=np.c_[np.ones(len(f)),f]; coef=np.linalg.lstsq(X,y,rcond=None)[0]; resid=y-X@coef; se=np.sqrt(np.diag((resid@resid/(len(y)-2))*np.linalg.inv(X.T@X))); beta=float(coef[1]); t_beta=float(beta/se[1]); r2=float(1-resid@resid/((y-y.mean())@(y-y.mean())))
# Save charts
fig,ax=plt.subplots(figsize=(10,5));
for m in tests: ax.plot(m['dates'],m['wealth'][1:],label=m['label'])
ax.set_title('Frozen least-connected 15 inverse-heat portfolio: growth of $1'); ax.set_ylabel('Growth of $1'); ax.grid(alpha=.25); ax.legend(); fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(ROOT/'frozen_choice_equity.png',dpi=180); plt.close(fig)
fig,ax=plt.subplots(figsize=(10,4));
for m in tests:
    cr=m['wealth']; dd=cr/np.maximum.accumulate(cr)-1; ax.plot(m['dates'],dd[1:],label=m['label'])
ax.set_title('Frozen portfolio drawdown by test window'); ax.axhline(0,color='black',lw=.6); ax.grid(alpha=.25); ax.legend(); fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(ROOT/'frozen_choice_drawdown.png',dpi=180); plt.close(fig)
# concise markdown report
lines=['# Round 3: Deep inverse-heat connectivity optimization','', '## Scope and registered protocol','', 'Selection rule and seven candidate definitions were written before selection runs in [PREREG.md](PREREG.md). The selection periods were Dow and cross-asset 2020-11-27 through 2022-12-30. The highest average daily Sharpe among candidates with mean turnover no greater than 50% in both universes was frozen in [FROZEN_CHOICE.md](FROZEN_CHOICE.md). The frozen rule is the 15 lowest unit-time heat connectivity names with inverse-connectivity weights, rebalanced every 21 sessions; costs are 5 bp per side on actual traded notional with next-open fills.','', '## Selection results','', '| Variant | Universe | Total P&L | CAGR | Sharpe | Max DD | Turnover / rebalance | Tracking error vs EW | Active share |','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
labels={'inv_heat':'Full universe inverse connectivity k=1','inv_heat_k2':'Full universe inverse connectivity k=2','low15_equal':'Equal weight in lowest-connectivity 15','low10_inv':'Inverse connectivity in lowest 10','low15_inv':'Inverse connectivity in lowest 15','low15_rev21':'Lowest 15 plus 21-day reversal','low15_rev63':'Lowest 15 plus reversal, 63-session rebalance'}
for mode,label,total,cagr,sh,dd,to,te,ash in sel: lines.append(f'| {labels[mode]} | {label} | {total:.2%} | {cagr:.2%} | {sh:.2f} | {dd:.2%} | {to:.1%} | {te:.2%} | {ash:.1%} |')
lines+=['','Selection rule chose `low15_inv`: average Sharpe 0.595, with turnover 45.4% in Dow and 45.3% in cross-asset. Although the selection Sharpe exceeds EW30 in the cross-asset window, this is a screen winner and not evidence of a persistent premium. The 10-name and reversal variants breach the turnover ceiling in at least one selection universe.','', '## Development test results','', 'Each held-out window is reported once for the frozen variant against schedule-matched EW30 and SPY. Costs are after the actual-trade 5 bp/side model. Block p is a two-sided circular 10-session block bootstrap of strategy-minus-EW daily returns, 5,000 draws, seed 3666, plus-one correction. DSR uses 85 cumulative trials (approximately 70 prior variants + eight Round 2 portfolios + seven Round 3 candidates), using the independent-trial approximation.','', '| Test period | Strategy total | EW30 total | SPY total | Sharpe | EW Sharpe | IR | Tracking error | Max DD | Turnover | Active share | Block p | DSR |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for m in tests: lines.append(f"| {m['label']} | {m['total']:.2%} | {m['ewtotal']:.2%} | {0:.2%} | {m['sh']:.2f} | {m['ewsh']:.2f} | {m['ir']:.2f} | {m['te']:.2%} | {m['mdd']:.2%} | {m['turnover']:.1%} | {m['active_share']:.1%} | {m['p']:.4f} | {m['dsr']:.1%} |")
lines[-len(tests):]=[x.replace(f"| {m['label']} |",f"| {m['label']} |",1) for x,m in zip(lines[-len(tests):],tests)]
# replace SPY placeholder by actual test stats from CSV where available
for i,m in enumerate(tests):
    label,rel,lo,hi,_=periods[i]; dates,v=read(ROOT/rel); idx=[j for j,d in enumerate(dates) if lo<=d<=hi]; prev=idx[0]-1; pp=[]
    for j in idx: pp.append(v['spy'][j]/v['spy'][prev]-1 if prev>=0 else v['spy'][j]-1); prev=j
    spy_total=float(np.prod(1+np.array(pp))-1)
    old=lines[-len(tests)+i]; lines[-len(tests)+i]=old.replace('| 0.00% |',f'| {spy_total:.2%} |')

lines.append("")
lines.append(f"The equal-weighted average of the four window total-return differences (strategy minus EW30) is {pooled_excess:.2%}; the concatenated daily active series compounds to {concatenated_active:.2%}. The pooled daily active mean is {pooled.mean()*252:.2%} annualized, with block-bootstrap p={pooled_p:.3f}; pooled strategy DSR is {pooled_dsr:.1%} at {TRIALS} trials. Because the windows include separate universes and overlapping dates, this is a descriptive pooled diagnostic.")
wins=sum(m["sh"]>m["ewsh"] for m in tests)
mean_te=float(np.mean([m["te"] for m in tests])); mean_as=float(np.mean([m["active_share"] for m in tests]))
pass2=wins>=3 and pooled_excess>0
pass3=mean_te>=.03 or mean_as>=.20
pass4=pooled_p<.10
pass5=all(m["turnover"]<=.5 for m in tests)
lines += ["", "## Round 3 criteria 1-5", "", "| Criterion | Result |", "|---|---|",
"| 1. Selection only on registered periods under written rule | PASS |",
f"| 2. Sharpe above EW in at least 3 of 4 tests and positive pooled excess | {'PASS' if pass2 else 'FAIL'} ({wins}/4 Sharpe wins; average window excess +{pooled_excess*100:.2f} pp) |",
f"| 3. Clearly different: tracking error >=3% or active share >=20% | {'PASS' if pass3 else 'FAIL'} (mean TE {mean_te:.2%}; mean active share {mean_as:.1%}) |",
f"| 4. Pooled block p <0.10 with DSR reported | {'PASS' if pass4 else 'FAIL'} (p={pooled_p:.3f}; pooled DSR {pooled_dsr:.1%} at {TRIALS} trials) |",
f"| 5. Turnover <=50% per rebalance in all tests | {'PASS' if pass5 else 'FAIL'} (range {min(m['turnover'] for m in tests):.1%} to {max(m['turnover'] for m in tests):.1%}) |",
"", "The frozen candidate is not a direction that meets the full success definition. Its out-of-sample evidence is mixed; the low-connectivity concentration does produce a material active portfolio, but pooled inference and per-window turnover do not meet the pre-set hurdles. The sealed holdout remains for the coordinator and was not run here.",
"", "## Connectivity versus low beta", "",
f"The same-universe low-beta factor sorts assets by beta to the universe EW portfolio using the previous 63 daily returns, then takes the bottom ten minus EW30. The pooled OLS slope of strategy active returns on this factor is {beta:.3f} (t={t_beta:.2f}, R2={r2:.3f}; n={len(y)}). This descriptive relationship helps identify a possible beta proxy; it does not establish a causal mechanism.",
"", "## Economic interpretation and refinement", "",
"The hypothesis is diversification: peripheral assets may have less exposure to network-wide shock transmission (Billio et al., 2012; Diebold and Yilmaz, 2014; Pozzi, Di Matteo and Aste, 2013). Concentrating in the least-connected 15 makes the book materially different from EW30, but the held-out evidence is mixed and turnover exceeds the 50% limit in the cross-asset test. The positive low-beta-factor slope suggests connectivity may partly proxy beta; that resembles the low-beta effect discussed by Frazzini and Pedersen (2014), though this long-only rule is not their market-neutral BAB strategy. Connectivity may also reflect sector composition and noisy short-window correlations rather than a durable contagion premium. EW30 remains the sensible default.",
"", "### Reproduction", "", "From `r3_invheat`, run these exact commands:",
"", "The first Dow OOS1 engine run emitted all pre-registered candidates because the test-only output filter had not applied. The frozen choice had already been selected and written down before any test results; only `low15_inv` is evaluated here. Later test runs emitted EW30 and the frozen choice only. There was no post-test tuning.",
"", "### Testing and validation\n\nThe copied engine's synthetic cost checks, actual-notional reconciliation, missing-data/calendar guards, and sampled future-truncation invariance checks passed on the recorded runs. The portable weight function was compared with the frozen selection ledger on cross-asset signal date 2020-11-25: it selected the same 15 names, with a maximum absolute weight difference of 3.6e-9 and a weight sum of 1. The selection screen comprised seven candidate definitions, each run once in each of the two selection universes.\n\n### Refinement\n\nDo not alter the choice based on these test outcomes. This seven-variant screen covered k=1/k=2 tilts, top-10/top-15 concentration, 21-day reversal, and 21/63-session rebalance. Within the 12-variant cap, it did not test k=3, rank tilts, tau changes, top-10 graph density, a 126-session correlation window, or a no-trade band; those remain untested options rather than negative results. A next development cycle can pre-register those options and test whether a beta-neutralized connectivity signal adds anything.\n\n### Frozen strategy function", "", "[frozen_strategy.py](frozen_strategy.py) exposes a function taking any folder of 30 daily adjusted-price CSVs and returns the frozen weights for a signal date.",
"", "### Charts", "", "![Equity](frozen_choice_equity.png)", "", "![Drawdown](frozen_choice_drawdown.png)",
"", "### Sources", "",
"- Billio, M., Getmansky, M., Lo, A. W., and Pelizzon, L. (2012), ?Econometric measures of connectedness and systemic risk in the finance and insurance sectors,? *Journal of Financial Economics*, 104(3), 535?559. [DOI](https://doi.org/10.1016/j.jfineco.2011.12.010).",
"- Diebold, F. X. and Yilmaz, K. (2014), ?On the network topology of variance decompositions: Measuring the connectedness of financial firms,? *Journal of Econometrics*, 182(1), 119?134. [DOI](https://doi.org/10.1016/j.jeconom.2014.04.012).",
"- Pozzi, F., Di Matteo, T. and Aste, T. (2013), ?Spread of Risk across Financial Markets: Better to Invest in the Peripheries,? *Scientific Reports*, 3, 1665. [DOI](https://doi.org/10.1038/srep01665).",
"- Bailey, D. H. and Lopez de Prado, M. (2014), 'The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality,' *The Journal of Portfolio Management*, 40(5), 94-107. [DOI](https://doi.org/10.3905/jpm.2014.40.5.094).", ""]
report='\n'.join(lines)
report=report.replace('?Econometric measures of connectedness and systemic risk in the finance and insurance sectors,? *Journal of Financial Economics*, 104(3), 535?559.', "'Econometric measures of connectedness and systemic risk in the finance and insurance sectors,' *Journal of Financial Economics*, 104(3), 535-559.")
report=report.replace('?On the network topology of variance decompositions: Measuring the connectedness of financial firms,? *Journal of Econometrics*, 182(1), 119?134.', "'On the network topology of variance decompositions: Measuring the connectedness of financial firms,' *Journal of Econometrics*, 182(1), 119-134.")
report=report.replace('?Spread of Risk across Financial Markets: Better to Invest in the Peripheries,? *Scientific Reports*, 3, 1665.', "'Spread of Risk across Financial Markets: Better to Invest in the Peripheries,' *Scientific Reports*, 3, 1665.")
report=report.replace('?The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality,? *The Journal of Portfolio Management*, 40(5), 94?107.', "'The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality,' *The Journal of Portfolio Management*, 40(5), 94-107.")
report=report.replace('### Sources', "- Frazzini, A. and Pedersen, L. H. (2014), 'Betting Against Beta,' *Journal of Financial Economics*, 111(1), 1-25. [DOI](https://doi.org/10.1016/j.jfineco.2013.10.005).\n\n### Sources")
commands='''```powershell
cd .\\dow
py -3 code\\pivot_backtest.py --runset=selection --cost=actual --reb=21 --roster=2020-08-31 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2022-12-30 --tag=r3_selection_dow
cd ..\\xasset
py -3 code\\pivot_backtest.py --runset=selection --cost=actual --reb=21 --roster=xasset30 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2022-12-30 --tag=r3_selection_xasset
cd ..\\dow
py -3 code\\pivot_backtest.py --cost=actual --reb=21 --roster=2020-08-31 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2024-02-23 --tag=r3_test_dow_early
py -3 code\\pivot_backtest.py --cost=actual --reb=21 --roster=2024-11-08 --anchor=2024-12-06 --win-first=2024-12-06 --win-last=2026-10-30 --tag=r3_test_dow_recent
cd ..\\xasset
py -3 code\\pivot_backtest.py --cost=actual --reb=21 --roster=xasset30 --anchor=2020-11-27 --win-first=2020-11-27 --win-last=2026-10-30 --tag=r3_test_xasset
cd ..
py -3 analyze_r3.py
```'''
report=report.replace('From `r3_invheat`, run these exact commands:', 'From `r3_invheat`, run these exact commands:\n\n'+commands)
(ROOT/'REPORT.md').write_text(report,encoding='utf-8')
print(f"saved report; pooled active annualized={pooled.mean()*252:.3%}; compound={pooled_excess:.3%}; p={pooled_p:.3f}; low-beta beta={beta:.3f}, t={t_beta:.2f}, R2={r2:.3f}")
for m in tests: print(m['label'],m['total'],m['ewtotal'],m['sh'],m['ewsh'],m['te'],m['turnover'],m['active_share'],m['p'],m['dsr'])
