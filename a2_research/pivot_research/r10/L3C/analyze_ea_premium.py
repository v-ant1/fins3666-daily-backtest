from __future__ import annotations
import csv, json, math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo
import time, requests
from dotenv import dotenv_values
import numpy as np
from scipy.stats import norm

ROOT=Path(__file__).resolve().parents[2]
CLOCK=ROOT/'r6_data'/'earnings_clock_sp500.csv'
ROSTER=ROOT/'r6_data'/'sp500_pit_roster.csv'
PANEL=ROOT/'r9'/'data'/'J2_DEV_FROM_20201127.npz'
OUT=Path(__file__).resolve().parent
START=date(2020,11,27); END=date(2026,10,30)
SOURCE_START=START; SOURCE_END=date(2025,10,30)


def anniversary(d: date) -> date:
    try: return d.replace(year=d.year+1)
    except ValueError: return date(d.year+1,2,28)

def read_csv(p):
    with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def fetch_candidate_gaps(tickers):
    env=dotenv_values(Path(r'C:\\Users\\musta\\Desktop\\UNSW\\SSI\\FINS3666\\A2\\.env'))
    key,secret=env.get('ALPACA_API_KEY'),env.get('ALPACA_SECRET_KEY')
    if not key or not secret: return {}, {'status':'credentials_unavailable','tickers_requested':0,'bars':0}
    headers={'APCA-API-KEY-ID':str(key),'APCA-API-SECRET-KEY':str(secret),'accept':'application/json'}
    aliases={'BF-B':'BF.B','BRK-B':'BRK.B'}; bars={}; errors=[]
    sess=requests.Session(); ny=ZoneInfo('America/New_York')
    for ticker in sorted(tickers):
        sym=quote(aliases.get(ticker,ticker),safe='.')
        params={'timeframe':'1Day','start':f'{START.isoformat()}T00:00:00Z','end':f'{END.isoformat()}T23:59:59Z','feed':'sip','adjustment':'all','limit':1000,'sort':'asc'}
        token=None; local={}; err=None
        for page in range(10):
            q=dict(params)
            if token: q['page_token']=token
            try:
                resp=sess.get(f'https://data.alpaca.markets/v2/stocks/{sym}/bars',params=q,headers=headers,timeout=60)
                if not resp.ok: err=f'HTTP_{resp.status_code}'; break
                payload=resp.json()
                for bar in payload.get('bars',[]):
                    stamp=__import__('datetime').datetime.fromisoformat(bar['t'].replace('Z','+00:00'))
                    day=stamp.astimezone(ny).date()
                    if START<=day<=END: local[day]=(float(bar['o']),float(bar['c']))
                token=payload.get('next_page_token')
                if not token: break
            except Exception as e:
                err=type(e).__name__; break
        else: err='pagination_limit'
        if err: errors.append({'ticker':ticker,'error':err})
        else: bars[ticker]=local
        time.sleep(.34)
    return bars, {'status':'completed','tickers_requested':len(tickers),'tickers_ok':len(bars),'bars':sum(map(len,bars.values())),'errors':errors}

def hac_mean_t(x,lag=4):
    x=np.asarray(x,dtype=float); n=len(x)
    if n<2: return None,None
    e=x-x.mean(); g0=float(np.dot(e,e)/n); lrv=g0
    for k in range(1,min(lag,n-1)+1):
        gamma=float(np.dot(e[k:],e[:-k])/n)
        lrv += 2*(1-k/(lag+1))*gamma
    se=math.sqrt(max(lrv,0)/n)
    return (float(x.mean()/se) if se>0 else None),se

def main():
    # Only permitted source-clock rows are materialized; all pre-boundary rows are skipped.
    clock=[]
    with CLOCK.open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            try: d=date.fromisoformat(r['acceptance_timestamp_et'][:10])
            except Exception: continue
            if SOURCE_START <= d <= SOURCE_END and r.get('membership_on_acceptance_date','').lower() in ('true','1','yes'):
                r['_source_date']=d; r['_predicted_date']=anniversary(d); clock.append(r)
    roster=read_csv(ROSTER)
    pit=defaultdict(list)
    for r in roster:
        try:
            a=date.fromisoformat(r['effective_from'][:10]); b=date.fromisoformat(r['effective_to_exclusive'][:10]) if r.get('effective_to_exclusive') else END+timedelta(days=1)
        except Exception: continue
        pit[r['ticker'].strip().upper()].append((a,b))
    with np.load(PANEL,allow_pickle=False) as z:
        dates=[date.fromisoformat(str(x)) for x in z['sp500_dates'].tolist()]
        if dates[0] != START or dates[-1] != END: raise RuntimeError('Dev panel date boundary mismatch')
        # The entire panel starts at the authorized boundary; no older values exist in this file.
        assets=[str(x).upper() for x in z['sp500_assets'].tolist()]
        roster_mask=z['sp500_roster']; op=z['sp500_adjusted_open']; cl=z['sp500_adjusted_close']
        ix={d:i for i,d in enumerate(dates)}; ai={a:i for i,a in enumerate(assets)}
        pred_by_ticker=defaultdict(set)
        for r in clock:
            pd=r['_predicted_date']
            if not (date(2021,11,27)<=pd<=END): continue
            ticker=r['ticker'].strip().upper()
            if any(a<=pd<b for a,b in pit.get(ticker,[])):
                pred_by_ticker[ticker].add(pd)
        # Fetch only eligible candidate long names that have at least one staged missing bar.
        candidates=set(pred_by_ticker)
        to_fetch={t for t in candidates if t in ai and np.any(~np.isfinite(op[ai[t],:]))}
        gapbars,gap_status=fetch_candidate_gaps(to_fetch)
        # Every Friday session is a weekly formation, after close. Forecast horizon is next five sessions.
        formations=[i for i,d in enumerate(dates) if d.weekday()==4 and i+1<len(dates)]
        rows=[]; prev_weights={}; coverage=defaultdict(int); missing_names=defaultdict(int)
        for fi in formations:
            fdate=dates[fi]; upcoming=dates[fi+1:min(fi+6,len(dates))]
            if not upcoming: continue
            upcoming_set=set(upcoming)
            picks={t for t,ps in pred_by_ticker.items() if ps & upcoming_set and t in ai and roster_mask[ai[t],fi+1]}
            entry_i=fi+1
            earliest=min((pd for t in picks for pd in pred_by_ticker[t] if pd in upcoming_set),default=None)
            after_pred=(ix.get(earliest)+1) if earliest in ix else None
            exit_i=min(after_pred if after_pred is not None else entry_i+4,entry_i+4)
            if exit_i>=len(dates) or dates[entry_i]<START or dates[exit_i]>END: continue
            long_returns=[]; used=[]
            for t in sorted(picks):
                j=ai[t]
                o=float(op[j,entry_i]) if np.isfinite(op[j,entry_i]) else None
                c=float(cl[j,exit_i]) if np.isfinite(cl[j,exit_i]) else None
                if t in gapbars:
                    if o is None and dates[entry_i] in gapbars[t]: o=gapbars[t][dates[entry_i]][0]
                    if c is None and dates[exit_i] in gapbars[t]: c=gapbars[t][dates[exit_i]][1]
                if roster_mask[j,entry_i] and roster_mask[j,exit_i] and o is not None and o>0 and c is not None:
                    long_returns.append(float(c/o-1)); used.append(t)
                else: missing_names[t]+=1
            # Exclude incomplete selected books; never silently treat missing securities as cash.
            if picks and len(used)!=len(picks):
                coverage['incomplete_selected_book_excluded']+=1
                prev_weights={t:1/len(picks) for t in picks}
                continue
            elif picks:
                target_weights={t:1/len(used) for t in used}
                long_gross=float(np.mean(long_returns))
                cost=2*10/10000
            else:
                target_weights={}; long_gross=0.0; cost=0.0
            # Same session schedule: first session open through exit close, with daily EW PIT benchmark compounding.
            daily=[]; benchmark_ok=True
            for k in range(entry_i,exit_i+1):
                if k==entry_i:
                    valid=roster_mask[:,k]&np.isfinite(op[:,k])&np.isfinite(cl[:,k])&(op[:,k]>0)
                    vals=cl[valid,k]/op[valid,k]-1
                else:
                    valid=roster_mask[:,k-1]&roster_mask[:,k]&np.isfinite(cl[:,k-1])&np.isfinite(cl[:,k])&(cl[:,k-1]>0)
                    vals=cl[valid,k]/cl[valid,k-1]-1
                vals=vals[np.isfinite(vals)]
                if vals.size==0: benchmark_ok=False; break
                daily.append(float(vals.mean()))
            if not benchmark_ok:
                coverage['missing_benchmark_excluded']+=1; continue
            bench=float(np.prod(1+np.asarray(daily))-1)
            turnover=.5*sum(abs(target_weights.get(t,0)-prev_weights.get(t,0)) for t in set(target_weights)|set(prev_weights))
            prev_weights=target_weights
            gross_excess=long_gross-bench
            net_excess=gross_excess-cost
            rows.append({'formation_date':fdate.isoformat(),'entry_date':dates[entry_i].isoformat(),'exit_date':dates[exit_i].isoformat(),'holding_sessions':exit_i-entry_i+1,'n_signal':len(picks),'n_priced':len(used),'long_gross':long_gross,'benchmark_gross':bench,'gross_excess':gross_excess,'cost':cost,'net_excess':net_excess,'turnover':turnover,'empty_book':not bool(picks)})
            coverage['cohorts']+=1; coverage['empty_book']+=int(not bool(picks)); coverage['invested']+=int(bool(picks))
        if not rows: raise RuntimeError('No eligible cohorts')
        x=np.array([r['net_excess'] for r in rows]); gross=np.array([r['gross_excess'] for r in rows]); costs=np.array([r['cost'] for r in rows]); n=len(x)
        sd=float(x.std(ddof=1)); t,se=hac_mean_t(x,4)
        by_year={}
        for y in sorted({r['entry_date'][:4] for r in rows}):
            yr=[r for r in rows if r['entry_date'][:4]==y]
            by_year[y]={'n':len(yr),'mean_net_excess':float(np.mean([r['net_excess'] for r in yr])),'mean_gross_excess':float(np.mean([r['gross_excess'] for r in yr])),'mean_long_gross':float(np.mean([r['long_gross'] for r in yr])),'mean_benchmark_gross':float(np.mean([r['benchmark_gross'] for r in yr])),'mean_turnover':float(np.mean([r['turnover'] for r in yr]))}
        mde=2.4865*sd/math.sqrt(313)
        passp=float(norm.cdf((.5*float(x.mean()))/(sd/math.sqrt(313))-1.6449)) if sd>0 else None
        # Price-free SEC source coverage summary based only on permitted rows.
        source_by_year=defaultdict(int)
        for r in clock: source_by_year[str(r['_source_date'].year)]+=1
        result={'tag':'L3C','trial':'R10-L3C-01','registered_before_outcomes':True,'dev_boundary':[START.isoformat(),END.isoformat()],'clock_source_boundary':[SOURCE_START.isoformat(),SOURCE_END.isoformat()],'prediction_score_boundary':['2021-11-27',END.isoformat()],'source_clock_rows':len(clock),'price_gap_fill':gap_status,'source_clock_dates':{'first':min(r['_source_date'] for r in clock).isoformat(),'last':max(r['_source_date'] for r in clock).isoformat(),'by_source_year':dict(source_by_year)},'weekly_cohorts':n,'cohort_counts':dict(coverage),'missing_price_name_cohort_exclusions':dict(missing_names),'primary':{'mean_weekly_net_excess':float(x.mean()),'sd':sd,'nw_lag4_t':t,'nw_intercept_se':se,'annualized_sharpe_weekly_net_excess':float(x.mean()/sd*math.sqrt(52)) if sd else None,'mean_gross_excess':float(gross.mean()),'mean_roundtrip_cost':float(costs.mean()),'cost_share_of_abs_mean_gross_excess':float(costs.mean()/abs(gross.mean())) if gross.mean()!=0 else None,'mean_turnover':float(np.mean([r['turnover'] for r in rows])),'mean_invested_entry_exit_notional_turnover':2.0 if any(not r['empty_book'] for r in rows) else 0.0,'mean_holding_sessions':float(np.mean([r['holding_sessions'] for r in rows]))},'cost_sensitivities':{str(bps):float(np.mean([r['gross_excess']-(2*bps/10000 if r['n_priced'] else 0) for r in rows])) for bps in (5,10,20)},'power_2010_2015':{'assumed_weeks':313,'family':1,'one_sided_alpha':0.05,'target_power':0.80,'mde':mde,'pass_probability_50pct_winner_curse_haircut':passp},'annual':by_year,'cohort_rows':rows}
        (OUT/'dev_result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        with (OUT/'weekly_cohorts.csv').open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        print(json.dumps({k:v for k,v in result.items() if k not in ('cohort_rows','annual')},indent=2))
if __name__=='__main__': main()
