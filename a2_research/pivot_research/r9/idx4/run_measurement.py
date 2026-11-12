from __future__ import annotations
import csv, json, math, time
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
from dotenv import dotenv_values
from scipy.stats import t as student_t
import exchange_calendars as xcals

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
EVENTS = OUT / 'event_list_metadata.csv'
PANEL = ROOT / 'r9' / 'data' / 'J2_DEV_FROM_20201127.npz'
ENV_PATH = Path(r'C:\Users\musta\Desktop\UNSW\SSI\FINS3666\A2\.env')
API_ROOT = 'https://data.alpaca.markets/v2/stocks'
NY = ZoneInfo('America/New_York')
DEV_START, DEV_END = date(2020,11,27), date(2026,10,30)
HOLD_START, HOLD_END = date(2016,1,4), date(2020,10,30)


def alpaca_symbol(ticker):
    return {'BF-B':'BF.B','BRK-B':'BRK.B'}.get(ticker.upper(),ticker.upper())


def headers_from_dotenv():
    values = dotenv_values(ENV_PATH)
    key, secret = values.get('ALPACA_API_KEY'), values.get('ALPACA_SECRET_KEY')
    if not key or not secret:
        raise RuntimeError('Alpaca credential pair unavailable at configured dotenv path')
    return {'APCA-API-KEY-ID':str(key),'APCA-API-SECRET-KEY':str(secret),'accept':'application/json'}


def fetch_bars(session, headers, ticker, start, end):
    if (start <= DEV_END and end >= DEV_START) and (start < DEV_START or end > DEV_END):
        # A single call may not straddle the holdout/dev boundary.
        raise RuntimeError('Refusing a request that crosses the holdout/development boundary')
    symbol=quote(alpaca_symbol(ticker),safe='.')
    params={'timeframe':'1Day','start':f'{start.isoformat()}T00:00:00Z','end':f'{end.isoformat()}T23:59:59Z',
            'feed':'sip','adjustment':'all','limit':1000,'sort':'asc'}
    bars={}; token=None
    for _ in range(10):
        q=dict(params)
        if token: q['page_token']=token
        resp=session.get(f'{API_ROOT}/{symbol}/bars',params=q,headers=headers,timeout=60)
        if resp.status_code==429:
            time.sleep(2.0); continue
        if not resp.ok:
            return None, f'HTTP_{resp.status_code}'
        payload=resp.json()
        for b in payload.get('bars',[]):
            d=datetime.fromisoformat(b['t'].replace('Z','+00:00')).astimezone(NY).date()
            if start <= d <= end:
                bars[d]=(float(b['o']),float(b['c']))
        token=payload.get('next_page_token')
        if not token: return bars, None
    return None, 'pagination_or_rate_limit'


def summarize(vals):
    vals=np.asarray(vals,dtype=float); n=len(vals)
    if not n: return {'N':0,'mean':None,'sd':None,'median':None,'ci95':[None,None]}
    mean=float(vals.mean()); sd=float(vals.std(ddof=1)) if n>1 else None
    if n>1:
        h=float(student_t.ppf(.975,n-1)*sd/math.sqrt(n)); ci=[mean-h,mean+h]
    else: ci=[None,None]
    return {'N':n,'mean':mean,'sd':sd,'median':float(np.median(vals)),'ci95':ci}


def main():
    with EVENTS.open(encoding='utf-8-sig',newline='') as f:
        all_events=list(csv.DictReader(f))
    dev_events=[e for e in all_events if e['window']=='dev']
    hold_events=[e for e in all_events if e['window']=='holdout']
    with np.load(PANEL,allow_pickle=False) as z:
        dates=[date.fromisoformat(x) for x in z['sp500_dates'].tolist()]
        date_to_i={d:i for i,d in enumerate(dates)}
        membership=z['sp500_roster']; adj_open=z['sp500_adjusted_open']; adj_close=z['sp500_adjusted_close']
        dev_dates=[d for d in dates if DEV_START<=d<=DEV_END]
        dev_dates_set=set(dev_dates)
        cal=xcals.get_calendar('XNYS')
        # calendar-derived sessions are metadata, not prices; Alpaca coverage is still checked below.
        sessions=cal.sessions_in_range(pd.Timestamp(HOLD_START),pd.Timestamp(HOLD_END))
        hold_sessions=[x.date() for x in sessions]
        hold_sessions_set=set(hold_sessions)
        api_headers=headers_from_dotenv(); sess=requests.Session()
        dev_rows=[]; dev_missing=Counter(); dev_errors=Counter(); hold_coverage=Counter()
        for ix,event in enumerate(dev_events,1):
            ann=date.fromisoformat(event['announcement_date']); eff=date.fromisoformat(event['effective_date'])
            entry=next((d for d in dev_dates if d>ann),None)
            if entry is None or eff not in date_to_i or entry not in date_to_i or entry>eff:
                dev_missing[(event['index'],'calendar')]+=1; continue
            if entry not in dev_dates_set or eff not in dev_dates_set:
                dev_missing[(event['index'],'outside_dev_panel')]+=1; continue
            bars,err=fetch_bars(sess,api_headers,event['ticker'],entry,eff)
            time.sleep(.34)
            if err:
                dev_errors[(event['index'],err)]+=1; continue
            if entry not in bars or eff not in bars:
                dev_missing[(event['index'],'missing_entry_or_effective')]+=1; continue
            si=bars[eff][1]/bars[entry][0]-1.0
            i0,i1=date_to_i[entry],date_to_i[eff]
            bd=[]
            for i in range(i0,i1+1):
                if i==i0:
                    valid=membership[:,i]&np.isfinite(adj_open[:,i])&np.isfinite(adj_close[:,i])&(adj_open[:,i]>0)
                    x=adj_close[valid,i]/adj_open[valid,i]-1.0
                else:
                    valid=membership[:,i-1]&membership[:,i]&np.isfinite(adj_close[:,i-1])&np.isfinite(adj_close[:,i])&(adj_close[:,i-1]>0)
                    x=adj_close[valid,i]/adj_close[valid,i-1]-1.0
                x=x[np.isfinite(x)]
                if not x.size: bd=[]; break
                bd.append(float(x.mean()))
            if not bd:
                dev_missing[(event['index'],'benchmark_session')]+=1; continue
            br=float(np.prod(1+np.asarray(bd))-1)
            dev_rows.append({**event,'entry_date':entry.isoformat(),'holding_sessions':i1-i0+1,'stock_return':si,'benchmark_return':br,'car':si-br})
        # Counts only: a holdout event is covered when both daily bars exist on the
        # prescribed entry session (next XNYS session) and its effective date.
        hold_total=len(hold_events)
        for event in hold_events:
            ann=date.fromisoformat(event['announcement_date']); eff=date.fromisoformat(event['effective_date'])
            entry=next((d for d in hold_sessions if d>ann),None)
            if entry is None or eff not in hold_sessions_set or entry>eff:
                hold_coverage[(event['index'],'calendar')]+=1; continue
            bars,err=fetch_bars(sess,api_headers,event['ticker'],entry,eff)
            time.sleep(.34)
            if err:
                hold_coverage[(event['index'],'request_error')]+=1
            elif entry in bars and eff in bars:
                hold_coverage[(event['index'],'covered')]+=1
            else:
                hold_coverage[(event['index'],'missing_entry_or_effective')]+=1

    # All outputs with numeric market results are dev-only; holdout output is aggregate counts only.
    fields=['window','index','ticker','announcement_date','effective_date','announcement_url','event_source','entry_date','holding_sessions','stock_return','benchmark_return','car']
    with (OUT/'dev_event_returns.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(dev_rows)
    pooled=summarize([r['car'] for r in dev_rows])
    sub={}
    for idx in ['S&P 500','S&P 400']:
        vals=[r['car'] for r in dev_rows if r['index']==idx]
        sub[idx]=summarize(vals)
    costs={}
    for label,vals in [('pooled',[r['car'] for r in dev_rows]),('S&P 500',[r['car'] for r in dev_rows if r['index']=='S&P 500']),('S&P 400',[r['car'] for r in dev_rows if r['index']=='S&P 400'])]:
        mu=float(np.mean(vals)) if vals else None
        costs[label]={str(b): (mu-2*b/10000 if mu is not None else None) for b in (5,10,20)}
    covered=int(hold_coverage.get(('S&P 400','covered'),0)+hold_coverage.get(('S&P 500','covered'),0))
    missing_pct=100*(hold_total-covered)/hold_total if hold_total else None
    mde=2.970*pooled['sd']/math.sqrt(covered) if pooled['sd'] is not None and covered else None
    primary=costs['pooled']['10']
    decision='prereg_draft' if primary is not None and mde is not None and primary>mde and missing_pct<=3 else 's2_exhausted'
    output={'tag':'L-IDX4','registered_test':'L-IDX4-01','event_list_sha256':'7a7420cf326d0abd081d9127b9a45694472bd562b265f5a620df9b1b19af2f00',
      'development':{'eligible_events':len(dev_events),'usable':pooled,'by_index':sub,'mean_net_car':costs,'missing_counts_by_index_and_reason':{f'{i}|{r}':n for (i,r),n in dev_missing.items()},'fetch_error_counts_by_index_and_code':{f'{i}|{e}':n for (i,e),n in dev_errors.items()}},
      'holdout_coverage_counts_only':{'eligible_events':hold_total,'covered_N':covered,'missing_pct':missing_pct,'by_index':{i:{r:int(n) for (ii,r),n in hold_coverage.items() if ii==i} for i in ['S&P 500','S&P 400']}},
      'mde':mde,'primary_net_mean_10bp_one_way':primary,'decision':decision}
    with (OUT/'results.json').open('w',encoding='utf-8') as f: json.dump(output,f,indent=2)
    print(json.dumps(output,indent=2))

if __name__=='__main__': main()
