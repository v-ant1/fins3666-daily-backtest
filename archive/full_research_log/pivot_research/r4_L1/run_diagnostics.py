#!/usr/bin/env python3
"""Reproduce the Round 4 L1 pressure/heat forensic diagnostics.

Run from any directory: python r4_L1/run_diagnostics.py
Reads only repo/{prices-daily*,prices-daily-delisted} rows dated 2020-06-01+
and writes tables/figures beside this script. No portfolio variants are tested.
"""
from __future__ import annotations
import csv, math
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import rankdata, spearmanr

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
DATA_DIRS = [ROOT / 'repo' / x for x in ('prices-daily-lookback','prices-daily','prices-daily-delisted')]
START, END, SAFE_START = '2020-11-27', '2026-10-30', '2020-06-01'
ROSTERS = {
    'pre2024-02-26': ['AAPL','AMGN','AXP','BA','CAT','CRM','CSCO','CVX','DIS','DOW','GS','HD','HON','IBM','INTC','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','PG','TRV','UNH','V','VZ','WBA','WMT'],
    '2024-02-26': ['AAPL','AMGN','AXP','AMZN','BA','CAT','CRM','CSCO','CVX','DIS','DOW','GS','HD','HON','IBM','INTC','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','PG','TRV','UNH','V','VZ','WMT'],
    '2024-11-08': ['AAPL','AMGN','AXP','AMZN','BA','CAT','CRM','CSCO','CVX','DIS','GS','HD','HON','IBM','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','NVDA','PG','SHW','TRV','UNH','V','VZ','WMT'],
}
SECTORS = {'AAPL':'IT','AMGN':'Health','AXP':'Finance','AMZN':'ConsDisc','BA':'Industrials','CAT':'Industrials','CRM':'IT','CSCO':'IT','CVX':'Energy','DIS':'Comm','DOW':'Materials','GS':'Finance','HD':'ConsDisc','HON':'Industrials','IBM':'IT','INTC':'IT','JNJ':'Health','JPM':'Finance','KO':'Staples','MCD':'ConsDisc','MMM':'Industrials','MRK':'Health','MSFT':'IT','NKE':'ConsDisc','NVDA':'IT','PG':'Staples','SHW':'Materials','TRV':'Finance','UNH':'Health','V':'Finance','VZ':'Comm','WBA':'Staples','WMT':'Staples'}

def load_ticker(t):
    out={}
    for folder in DATA_DIRS:
        p=folder/f'{t}.csv'
        if not p.exists(): continue
        with p.open(newline='') as f:
            for row in csv.DictReader(f):
                d=row['date'][:10]
                # Crucially reject sealed/irrelevant dates before touching price fields.
                if d < SAFE_START or d > END: continue
                try:
                    c=float(row['adjclose']); factor=c/float(row['close'])
                    out[d]={'o':float(row['open'])*factor,'h':float(row['high'])*factor,'l':float(row['low'])*factor,'c':c,'v':float(row['volume'] or 0)}
                except (ValueError, TypeError, ZeroDivisionError): continue
    return out

def pct(x): return rankdata(x, method='average')/(len(x)-1) - 1/(len(x)-1) if len(x)>1 else np.full(len(x),.5)
def ranks(x): return (rankdata(x, method='average')-1)/(len(x)-1) if len(x)>1 else np.full(len(x),.5)
def nw_t(x, lag):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<3: return float('nan')
    m=x.mean(); u=x-m; L=min(lag,n-1)
    longvar=np.dot(u,u)/n
    for k in range(1,L+1): longvar += 2*(1-k/(L+1))*np.dot(u[k:],u[:-k])/n
    return float(m/math.sqrt(max(longvar,1e-20)/n))
def corr(a,b):
    ok=np.isfinite(a)&np.isfinite(b)
    return float(np.corrcoef(a[ok],b[ok])[0,1]) if ok.sum()>2 else float('nan')
def date_roster(d):
    if d < '2024-02-26': return ROSTERS['pre2024-02-26']
    if d < '2024-11-08': return ROSTERS['2024-02-26']
    return ROSTERS['2024-11-08']

def graph(z, ret, names):
    # ret: (names, 63) close returns, identical positive-top-5 symmetrized kNN construction.
    cm=np.corrcoef(ret)
    w=np.zeros_like(cm)
    for i in range(len(names)):
        order=np.argsort(-cm[i]); keep=[j for j in order if j!=i and cm[i,j]>0][:5]
        for j in keep: w[i,j]=cm[i,j]; w[j,i]=cm[i,j]
    L=np.diag(w.sum(1))-w
    vals,vec=np.linalg.eigh(L); filt=np.exp(-vals)
    H=(vec*filt)@vec.T; np.fill_diagonal(H,0)
    den=H.sum(1); heat=(H@z)/np.maximum(den,1e-12)
    nbr=(w@z)/np.maximum(w.sum(1),1e-12)
    return heat,nbr,w,vals,filt

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    tickers=sorted(set(sum(ROSTERS.values(),[])))
    bars={t:load_ticker(t) for t in tickers}
    # Include development warm-up from June only; only START..END observations enter outcomes.
    spy=load_ticker('SPY'); dates=[d for d in sorted(spy) if SAFE_START<=d<=END]
    missing=[]
    for d in dates:
        for t in date_roster(d):
            if d not in bars[t]: missing.append((d,t))
    bad=[x for x in missing if x[0]>=START]
    if bad: raise RuntimeError(f'Missing in outcome window: {bad[:5]} ({len(bad)} total)')
    def values(t,key,default=np.nan): return np.array([bars[t].get(d,{}).get(key,default) for d in dates])
    c={t:values(t,'c') for t in tickers}
    o={t:values(t,'o') for t in tickers}
    h={t:values(t,'h') for t in tickers}
    l={t:values(t,'l') for t in tickers}
    v={t:values(t,'v',0.0) for t in tickers}
    comps={}; pressure={}; heats={}; nbrs={}; graph_cache={}; p_ranks={}; comp_ranks={}
    # Daily cross-sectional signal observations, starting only after 63 prior returns.
    for i,d in enumerate(dates):
        if i < 63 or d < START: continue
        names=date_roster(d)
        clv=[]; svol=[]; oi=[]
        for t in names:
            clv.append(np.mean([((c[t][j]-l[t][j])-(h[t][j]-c[t][j]))/(h[t][j]-l[t][j]) if h[t][j]>l[t][j] else 0 for j in range(i-4,i+1)]))
            r=c[t][1:]/c[t][:-1]-1
            svol.append(np.sum(np.sign(r[i-5:i])*v[t][i-4:i+1])/np.mean(v[t][i-24:i+1]))
            intra=sum(c[t][j]/o[t][j]-1 for j in range(i-4,i+1))
            overnight=sum(o[t][j]/c[t][j-1]-1 for j in range(i-4,i+1))
            oi.append(intra-overnight)
        cr,sr,orr=map(ranks,(np.array(clv),np.array(svol),np.array(oi)))
        blend=(cr+sr+orr)/3
        zr=(blend-blend.mean())/blend.std(ddof=0)
        comp_ranks[d]=dict(zip(names,zip(cr,sr,orr)))
        comps[d]=dict(zip(names,zip(np.array(clv),np.array(svol),np.array(oi))))
        pressure[d]=dict(zip(names,blend)); p_ranks[d]=dict(zip(names,ranks(blend)))
        ret=np.array([c[t][i-63+1:i+1]/c[t][i-63:i]-1 for t in names])
        heat,nbr,w,ev,fw=graph(zr,ret,names)
        heats[d]=dict(zip(names,ranks(heat))); nbrs[d]=dict(zip(names,ranks(nbr)))
        graph_cache[d]=(names,w,ev,fw)
    sig_names=['Pressure','CLV','Signed volume','Intraday minus overnight','Heat','Neighbour avg']
    horizons=[1,2,5,10,20]
    rows=[]; daily_ic={}; daily_by_year={}; sector_ic=[]
    sig_map={'Pressure':p_ranks,'CLV':{},'Signed volume':{},'Intraday minus overnight':{},'Heat':heats,'Neighbour avg':nbrs}
    for d,parts in comp_ranks.items():
        names=list(parts); sig_map['CLV'][d]={t:parts[t][0] for t in names}; sig_map['Signed volume'][d]={t:parts[t][1] for t in names}; sig_map['Intraday minus overnight'][d]={t:parts[t][2] for t in names}
    for sig in sig_names:
        for typ in ('C2C','Next O2C'):
            for hd in horizons:
                vals=[]; vals_dm=[]; ds=[]
                for i,d in enumerate(dates):
                    if d not in sig_map[sig] or i+hd>=len(dates): continue
                    names=date_roster(d)
                    if dates[i+hd] > END: continue
                    x=np.array([sig_map[sig][d][t] for t in names])
                    if typ=='C2C': rr=np.array([c[t][i+hd]/c[t][i]-1 for t in names])
                    else: rr=np.array([c[t][i+hd]/o[t][i+1]-1 for t in names])
                    vals.append(spearmanr(x,rr).statistic)
                    vals_dm.append(spearmanr(x,rr-rr.mean()).statistic)
                    ds.append(d)
                lag=hd-1 if typ=='C2C' else hd-1
                daily_ic[(sig,typ,hd)]=(ds,np.array(vals),np.array(vals_dm))
                rows.append((sig,typ,hd,len(vals),np.nanmean(vals),nw_t(vals,lag),np.nanmean(vals_dm),nw_t(vals_dm,lag)))
    with (OUT/'rank_correlations.csv').open('w',newline='') as f:
        wri=csv.writer(f); wri.writerow(['signal','return','horizon_days','dates','mean_IC','NW_t','mean_IC_market_demeaned','NW_t_market_demeaned']); wri.writerows(rows)
    # Component relation and blend variance attribution.
    comp_names=['CLV','Signed volume','Intraday minus overnight']; component_corr=[]
    for a in range(3):
        for b in range(3):
            xs=[];ys=[]
            for d in comp_ranks:
                names=list(comp_ranks[d]); xs += [comp_ranks[d][t][a] for t in names]; ys += [comp_ranks[d][t][b] for t in names]
            component_corr.append((comp_names[a],comp_names[b],corr(np.array(xs),np.array(ys))))
    with (OUT/'component_correlations.csv').open('w',newline='') as f:
        wr=csv.writer(f); wr.writerow(['component_a','component_b','pooled_pearson_rank_score_correlation']); wr.writerows(component_corr)
    # Weekly graph stability and heat alignments; include only dates with full usable lookback.
    weekly=[d for j,d in enumerate(dates) if j>=64 and (j==64 or dates[j].startswith('2020-11-') or (j>0 and dates[j][:7]!=dates[j-1][:7]))]
    # use each week's last market session as practical weekly snapshot
    weeklast=[]
    for d in dates:
        if d not in graph_cache: continue
        if not weeklast or dates.index(d)//5 != dates.index(weeklast[-1])//5: weeklast.append(d)
        else: weeklast[-1]=d
    overlaps=[]
    for da,db in zip(weeklast,weeklast[1:]):
        na,wa,_,_=graph_cache[da]; nb,wb,_,_=graph_cache[db]
        ea={(na[i],na[j]) for i in range(len(na)) for j in range(i+1,len(na)) if wa[i,j]>0}
        eb={(nb[i],nb[j]) for i in range(len(nb)) for j in range(i+1,len(nb)) if wb[i,j]>0}
        a,b=ea&eb,ea|eb; overlaps.append((da,db,len(a)/len(b) if b else np.nan,len(a),len(b)))
    # pooled heat vs plain neighbour and same-day sector/market pressure averages
    hv=[]; nv=[]; market=[]; sector=[]
    for d in heats:
        names=list(heats[d]); own=p_ranks[d]
        market_mean=np.mean([own[t] for t in names])
        for t in names:
            hv.append(heats[d][t]); nv.append(nbrs[d][t]); market.append(market_mean)
            peers=[s for s in names if SECTORS.get(s)==SECTORS.get(t)]
            sector.append(np.mean([own[s] for s in peers]))
    # market rank-score is constant each date; compare heat map to market-pressure aggregate via time-series levels.
    heat_neighbor_corr=corr(np.array(hv),np.array(nv)); heat_sector_corr=corr(np.array(hv),np.array(sector))
    # Spectral summary at pooled daily graphs and representative graph.
    spec=[]
    for d,(names,w,ev,fw) in graph_cache.items():
        spec.append((d,ev,fw))
    eig_all=np.concatenate([x[1] for x in spec]); filt_all=np.concatenate([x[2] for x in spec])
    # graph modes are eigenmodes; report average fraction of filter trace in eigenvalue bins.
    bins=[(-1e-8,.25),(.25,.5),(.5,1),(1,2),(2,4),(4,100)]
    spectral=[]
    for lo,hi in bins:
        mask=(eig_all>=lo)&(eig_all<hi); spectral.append((f'{"~0" if lo<0 else f"{lo:g}"}-{hi:g}',int(mask.sum()),float(filt_all[mask].sum()/filt_all.sum()) if mask.any() else 0.0,float(np.mean(filt_all[mask])) if mask.any() else np.nan))
    # Graph mean summary and effective rank of filter operator from normalized spectral weights.
    effs=[]; mean_lams=[]
    for _d,_ev,_fw in spec:
        p=_fw/_fw.sum(); effs.append(float(np.exp(-np.sum(p*np.log(np.maximum(p,1e-300)))))); mean_lams.append(float(np.sum(_ev*_fw)/np.sum(_fw)))
    effrank=float(np.mean(effs)); mean_lam=float(np.mean(mean_lams))
    with (OUT/'graph_diagnostics.csv').open('w',newline='') as f:
        wr=csv.writer(f); wr.writerow(['metric','value']); wr.writerow(['weekly edge Jaccard mean',np.mean([r[2] for r in overlaps])]); wr.writerow(['weekly edge Jaccard median',np.median([r[2] for r in overlaps])]); wr.writerow(['heat vs neighbour pooled Pearson',heat_neighbor_corr]); wr.writerow(['heat vs sector-mean own-pressure pooled Pearson',heat_sector_corr]); wr.writerow(['heat vs market mean rank-score correlation','undefined: cross-sectional market mean rank-score is mechanically constant']); wr.writerow(['filter effective spectral rank (mean, per graph)',effrank]); wr.writerow(['filter-weighted mean Laplacian eigenvalue (mean, per graph)',mean_lam]); wr.writerow([]); wr.writerow(['eigenvalue_bin','modes','filter_trace_fraction','mean_exp_minus_lambda']); wr.writerows(spectral)
    with (OUT/'edge_overlap.csv').open('w',newline='') as f:
        wr=csv.writer(f); wr.writerow(['week_start','week_end','Jaccard','common_edges','union_edges']); wr.writerows(overlaps)
    # Year and sector patterns for key horizons (daily ICs, close-to-close).
    for sig in ('Pressure','Heat','Neighbour avg'):
        ds,ic,dm=daily_ic[(sig,'C2C',5)]
        for year in sorted(set(d[:4] for d in ds)):
            vals=[x for d,x in zip(ds,ic) if d[:4]==year]; daily_by_year.setdefault(sig,[]).append((year,len(vals),np.mean(vals),nw_t(vals,4)))
    # Sector IC: for each signal/date/horizon compare only names in sector; small groups excluded <4.
    for sig in ('Pressure','Heat','Neighbour avg'):
        for sec in sorted(set(SECTORS.values())):
            arr=[]
            for d in sig_map[sig]:
                i=dates.index(d); names=[t for t in date_roster(d) if SECTORS.get(t)==sec]
                if len(names)<4 or i+5>=len(dates): continue
                x=[sig_map[sig][d][t] for t in names]; y=[c[t][i+5]/c[t][i]-1 for t in names]
                arr.append(spearmanr(x,y).statistic)
            if arr: sector_ic.append((sig,sec,len(arr),float(np.nanmean(arr)),nw_t(arr,4)))
    with (OUT/'subgroup_diagnostics.csv').open('w',newline='') as f:
        wr=csv.writer(f); wr.writerow(['type','signal','group','dates','mean_IC_5d_C2C','NW_t']);
        for s,ys in daily_by_year.items():
            for y,n,m,t in ys: wr.writerow(['year',s,y,n,m,t])
        for s,sec,n,m,t in sector_ic: wr.writerow(['sector',s,sec,n,m,t])
    # Reproduce the unbuffered weekly top-five heat strategy and EW30 baseline.
    # Entry is next-session open after the first in-window signal; holdings drift between fills.
    fill_idx=[i for i,d in enumerate(dates) if d>START][::5]
    fills=[i for i in fill_idx if dates[i]<=END]
    def portfolio(strategy,cost):
        eq=1.0; shares=None; marks=[]; costs=[]; turnovers=[]; period_gross=[]; period_net=[]
        for k,fi in enumerate(fills):
            d=dates[fi]; sig=dates[fi-1]; names=date_roster(sig)
            if strategy:
                vals={t:.5*p_ranks[sig][t]+.5*heats[sig][t] for t in names}
                chosen=sorted(names,key=lambda t:(-vals[t],t))[:5]; wts={t:.2 for t in chosen}
            else: wts={t:1/30 for t in names}
            if shares is None:
                gross=eq; E=gross/(1+cost); notional=E; paid=gross-E
            else:
                old={t:shares[t]*o[t][fi] for t in shares}; gross=sum(old.values()); E=gross
                for _ in range(500):
                    newer=gross-cost*sum(abs(E*wts.get(t,0)-old.get(t,0)) for t in set(old)|set(wts))
                    if abs(newer-E)<1e-14*max(1,gross): E=newer; break
                    E=newer
                notional=sum(abs(E*wts.get(t,0)-old.get(t,0)) for t in set(old)|set(wts)); paid=gross-E
                turnovers.append(notional/gross if gross else np.nan)
            costs.append((d,gross,notional,paid,paid/max(gross,1e-20)))
            shares={t:E*wts[t]/o[t][fi] for t in wts}; eq=E
            end=fills[k+1] if k+1<len(fills) else len(dates)-1
            # close marks through day before next fill; final close pays sell-side fee.
            for j in range(fi,end if k+1<len(fills) else end+1):
                val=sum(shares[t]*c[t][j] for t in shares)
                if k+1==len(fills) and j==end: val*=1-cost
                marks.append((dates[j],val))
                if k+1==len(fills) and j==end: eq=val
        arr=np.array([x[1] for x in marks]); rr=np.diff(np.r_[1.,arr])/np.r_[1.,arr][:-1]
        sh=float(rr.mean()/rr.std(ddof=0)*math.sqrt(252)) if rr.std()>0 else 0
        return {'return':float(arr[-1]-1),'sharpe':sh,'marks':marks,'costs':costs,'turnovers':turnovers}
    pf={}
    for label,strat in [('Heat50 top5',True),('EW30',False)]:
        pf[(label,'gross')]=portfolio(strat,0.0); pf[(label,'net 0.05%/side')]=portfolio(strat,.0005)
    with (OUT/'cost_analysis.csv').open('w',newline='') as f:
        wr=csv.writer(f); wr.writerow(['portfolio','case','cumulative_return','daily_mark_Sharpe','avg_rebalance_total_notional_pct','avg_rebalance_cost_pct','rebalance_count','break_even_weekly_rank_IC'])
        for (label,case),res in pf.items():
            cc=res['costs'][1:]; wr.writerow([label,case,res['return'],res['sharpe'],100*np.mean([x[2]/x[1] for x in cc]),100*np.mean([x[3]/x[1] for x in cc]),len(res['costs']),''])
    # Empirical IC break-even calibration: weekly active returns regressed on same-date 5d blend IC.
    ds=[]; xs=[]; ys=[]; costs_frac=[]; weekly_dispersion=[]
    for fi in fills[:-1]:
        sig=dates[fi-1]; names=date_roster(sig); ii=dates.index(sig)
        score=np.array([.5*p_ranks[sig][t]+.5*heats[sig][t] for t in names])
        forward=np.array([c[t][min(fi+4,len(dates)-1)]/o[t][fi]-1 for t in names])
        xs.append(spearmanr(score,forward).statistic)
        weekly_dispersion.append(float(np.std(forward,ddof=0)))
    # Realized active return per holding period from gross strategy vs gross EW daily marks.
    s_marks=pf[('Heat50 top5','gross')]['marks']; e_marks=pf[('EW30','gross')]['marks']
    sm={d:v for d,v in s_marks}; em={d:v for d,v in e_marks}
    for k,fi in enumerate(fills[:-1]):
        d=dates[fi]; stop=fills[k+1]-1
        if d in sm and dates[stop] in sm and d in em and dates[stop] in em:
            # paired five-session holding-period close-to-close active return
            ys.append((sm[dates[stop]]/sm[d]-1)-(em[dates[stop]]/em[d]-1))
            sig=dates[fi-1]; names=date_roster(sig); score=np.array([.5*p_ranks[sig][t]+.5*heats[sig][t] for t in names]); forward=np.array([c[t][min(fi+4,len(dates)-1)]/o[t][fi]-1 for t in names]); ds.append(spearmanr(score,forward).statistic)
    slope,intercept=np.polyfit(ds,ys,1); avg_cost=float(np.mean([x[4] for x in pf[('Heat50 top5','net 0.05%/side')]['costs'][1:]])-np.mean([x[4] for x in pf[('EW30','net 0.05%/side')]['costs'][1:]]))
    breakeven=(avg_cost-intercept)/slope if abs(slope)>1e-12 else np.nan
    with (OUT/'power_cost_summary.csv').open('w',newline='') as f:
        rank_multiplier=math.sqrt(12)*(0.5-0.5/6)
        empirical_turnover=avg_cost/.0005
        dispersion=float(np.mean(weekly_dispersion))
        structural_hurdle=avg_cost/(dispersion*rank_multiplier)
        wr=csv.writer(f); wr.writerow(['metric','value']); wr.writerow(['signal dates',len(comp_ranks)]); wr.writerow(['observed pooled 5d pressure IC',next(r[4] for r in rows if r[0]=='Pressure' and r[1]=='C2C' and r[2]==5)]); wr.writerow(['pressure 5d IC NW standard error',next(r[4]/r[5] for r in rows if r[0]=='Pressure' and r[1]=='C2C' and r[2]==5)]); wr.writerow(['IC magnitude for |t|=2, pressure 5d NW SE',2*abs(next(r[4]/r[5] for r in rows if r[0]=='Pressure' and r[1]=='C2C' and r[2]==5))]); wr.writerow(['optimistic IC for annual IR 0.5, breadth=30*52',.5/math.sqrt(30*52)]); wr.writerow(['observed 5d pressure IC / IR0.5 IC',next(r[4] for r in rows if r[0]=='Pressure' and r[1]=='C2C' and r[2]==5)/(.5/math.sqrt(30*52))]); wr.writerow(['observed weekly blend IC mean',float(np.mean(ds))]); wr.writerow(['gross active-return slope per unit IC',slope]); wr.writerow(['gross active-return intercept per week',intercept]); wr.writerow(['incremental mean cost vs EW fraction per rebalance',avg_cost]); wr.writerow(['empirical weekly IC break-even (includes positive intercept)',breakeven]); wr.writerow(['mean cross-sectional weekly O2C return dispersion',dispersion]); wr.writerow(['incremental total-notional turnover vs EW per rebalance',empirical_turnover]); wr.writerow(['linear rank-to-return multiplier, top 5 of 30',rank_multiplier]); wr.writerow(['cost-only weekly IC break-even from turnover and dispersion',structural_hurdle])
    with (OUT/'cost_analysis.csv').open('a',newline='') as f:
        wr=csv.writer(f)
        wr.writerow(['Break-even hurdle','empirical regression with intercept','','',100*empirical_turnover,100*avg_cost, len(fills)-1,breakeven])
        wr.writerow(['Break-even hurdle','cost-only rank/dispersion mapping','','',100*empirical_turnover,100*avg_cost, len(fills)-1,structural_hurdle])
    # Plots.
    fig,ax=plt.subplots(figsize=(9,5))
    for sig in sig_names:
        z=[next(r[4] for r in rows if r[0]==sig and r[1]=='C2C' and r[2]==hd) for hd in horizons]
        ax.plot(horizons,z,marker='o',label=sig)
    ax.axhline(0,color='black',lw=.8); ax.set(xlabel='Forward horizon (trading days)',ylabel='Mean daily cross-sectional Spearman IC',title='Predictive power fades (close-to-close)'); ax.legend(fontsize=8,ncol=2); fig.tight_layout(); fig.savefig(OUT/'ic_by_horizon.png',dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.8)); labels=[x[0] for x in spectral]; vals=[x[2] for x in spectral]; ax.bar(labels,vals); ax.set(xlabel='Laplacian eigenvalue bin',ylabel='Share of filter trace',title='Heat filter spectral mass'); fig.tight_layout(); fig.savefig(OUT/'heat_spectrum.png',dpi=180); plt.close(fig)
    # Print concise output.
    print(f'Observations: {len(dates)} sessions {dates[0]}..{dates[-1]}, signals {len(comp_ranks)}; all prices filtered at {SAFE_START}.')
    for r in rows:
        if r[1]=='C2C' and r[2] in (1,5,20): print(f'{r[0]:26s} C2C {r[2]:2d}d IC={r[4]:+.4f} t={r[5]:+.2f}; demean IC={r[6]:+.4f} t={r[7]:+.2f}')
    print(f'Heat/neighbour pooled r={heat_neighbor_corr:.3f}; heat/sector pressure r={heat_sector_corr:.3f}; weekly Jaccard mean={np.mean([r[2] for r in overlaps]):.3f}; spectral effective rank={effrank:.2f}')
    print('Wrote CSV tables and PNG charts to',OUT)

if __name__=='__main__': main()
