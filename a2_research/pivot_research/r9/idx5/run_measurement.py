from __future__ import annotations
import csv, hashlib, json, math, os, re, sys, time
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
EVENTS = OUT / 'event_list_frozen.csv'
PANEL = ROOT / 'r9' / 'data' / 'J2_DEV_FROM_20201127.npz'
ENV_PATH = Path(r'C:\Users\musta\Desktop\UNSW\SSI\FINS3666\A2\.env')
API_ROOT = 'https://data.alpaca.markets/v2/stocks'
NY = ZoneInfo('America/New_York')
DEV_START, DEV_END = date(2020,11,27), date(2026,10,30)
HOLD_START, HOLD_END = date(2016,1,4), date(2020,10,30)
LOCK = OUT / 'idx5_run.lock'

def release_lock():
    try: LOCK.unlink()
    except FileNotFoundError: pass

def alpaca_symbol(ticker):
    return {'BF-B':'BF.B','BRK-B':'BRK.B'}.get(ticker.upper(), ticker.upper())

def headers_from_dotenv():
    values = dotenv_values(ENV_PATH)
    key, secret = values.get('ALPACA_API_KEY'), values.get('ALPACA_SECRET_KEY')
    if not key or not secret: raise RuntimeError('Alpaca credential pair unavailable at configured dotenv path')
    return {'APCA-API-KEY-ID':str(key), 'APCA-API-SECRET-KEY':str(secret), 'accept':'application/json'}

def fetch_bars(session, headers, ticker, start, end, prices):
    if (start <= DEV_END and end >= DEV_START) and (start < DEV_START or end > DEV_END):
        raise RuntimeError('Refusing request that crosses holdout/development boundary')
    symbol = quote(alpaca_symbol(ticker), safe='.')
    params={'timeframe':'1Day','start':f'{start.isoformat()}T00:00:00Z','end':f'{end.isoformat()}T23:59:59Z',
            'feed':'sip','adjustment':'all','limit':1000,'sort':'asc'}
    bars={}; token=None
    for _ in range(10):
        q=dict(params)
        if token: q['page_token']=token
        resp=session.get(f'{API_ROOT}/{symbol}/bars',params=q,headers=headers,timeout=60)
        if resp.status_code == 429:
            time.sleep(2.0); continue
        if not resp.ok: return None, f'HTTP_{resp.status_code}'
        payload=resp.json()
        for b in payload.get('bars',[]):
            d=datetime.fromisoformat(b['t'].replace('Z','+00:00')).astimezone(NY).date()
            if start <= d <= end:
                if prices:
                    bars[d]=(float(b['o']),float(b['c']))
                else:
                    bars[d]=True
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
    try:
        digest=hashlib.sha256(EVENTS.read_bytes()).hexdigest()
        with EVENTS.open(encoding='utf-8-sig',newline='') as f: events=list(csv.DictReader(f))
        with (OUT/'metadata_search_all_candidates.csv').open(encoding='utf-8-sig',newline='') as f: meta_candidates=list(csv.DictReader(f))
        hold_candidates=[e for e in meta_candidates if e.get('effective_date','') and HOLD_START.isoformat()<=e['effective_date']<=HOLD_END.isoformat() and e.get('index') in ('S&P 500','S&P 400')]
        with (OUT/'metadata_candidates_missing_announcement.csv').open(encoding='utf-8-sig',newline='') as f: meta_missing=list(csv.DictReader(f))
        dev=[e for e in events if e['window']=='dev']
        hold=[e for e in events if e['window']=='holdout']
        with np.load(PANEL,allow_pickle=False) as z:
            dates=[date.fromisoformat(x) for x in z['sp500_dates'].tolist()]
            d2i={d:i for i,d in enumerate(dates)}
            membership=z['sp500_roster']; ao=z['sp500_adjusted_open']; ac=z['sp500_adjusted_close']
            devdates=[d for d in dates if DEV_START<=d<=DEV_END]
            cal=xcals.get_calendar('XNYS')
            sessions=[x.date() for x in cal.sessions_in_range(pd.Timestamp(HOLD_START),pd.Timestamp(HOLD_END))]
            session_set=set(sessions)
            headers=headers_from_dotenv(); sess=requests.Session()
            fields=['window','index','ticker','announcement_date','effective_date','entry_date','status','error','holding_sessions','stock_return','benchmark_return','car']
            result_path=OUT/'event_results.csv'; error_path=OUT/'event_errors.csv'
            with result_path.open('w',encoding='utf-8',newline='') as rf, error_path.open('w',encoding='utf-8',newline='') as ef:
                writer=csv.DictWriter(rf,fieldnames=fields); writer.writeheader(); rf.flush(); os.fsync(rf.fileno())
                ew=csv.DictWriter(ef,fieldnames=['window','index','ticker','announcement_date','effective_date','error']); ew.writeheader(); ef.flush()
                dev_cars=[]; dev_by=Counter(); dev_status=Counter(); hold_cov=Counter(); hold_total=Counter()
                for ix,e in enumerate(dev,1):
                    row={k:e.get(k,'') for k in ['window','index','ticker','announcement_date','effective_date']}
                    row.update(entry_date='',status='',error='',holding_sessions='',stock_return='',benchmark_return='',car='')
                    try:
                        ann=date.fromisoformat(e['announcement_date']); eff=date.fromisoformat(e['effective_date'])
                        entry=next((d for d in devdates if d>ann),None)
                        if entry is None or entry not in d2i or eff not in d2i or entry>eff or not (DEV_START<=entry<=DEV_END and DEV_START<=eff<=DEV_END):
                            raise ValueError('calendar_or_panel_boundary')
                        row['entry_date']=entry.isoformat()
                        bars,err=fetch_bars(sess,headers,e['ticker'],entry,eff,True); time.sleep(.34)
                        if err: raise RuntimeError(err)
                        if entry not in bars or eff not in bars:
                            row['status']='missing_entry_or_effective_bar'; dev_status[(e['index'],row['status'])]+=1
                        else:
                            stock=bars[eff][1]/bars[entry][0]-1.0
                            i0,i1=d2i[entry],d2i[eff]; bd=[]
                            for j in range(i0,i1+1):
                                if j==i0:
                                    valid=membership[:,j]&np.isfinite(ao[:,j])&np.isfinite(ac[:,j])&(ao[:,j]>0)
                                    x=ac[valid,j]/ao[valid,j]-1.0
                                else:
                                    valid=membership[:,j-1]&membership[:,j]&np.isfinite(ac[:,j-1])&np.isfinite(ac[:,j])&(ac[:,j-1]>0)
                                    x=ac[valid,j]/ac[valid,j-1]-1.0
                                x=x[np.isfinite(x)]
                                if not x.size: bd=[]; break
                                bd.append(float(x.mean()))
                            if not bd: row['status']='missing_benchmark_session'; dev_status[(e['index'],row['status'])]+=1
                            else:
                                bench=float(np.prod(1+np.asarray(bd))-1); car=stock-bench
                                row.update(status='ok',holding_sessions=i1-i0+1,stock_return=stock,benchmark_return=bench,car=car)
                                dev_cars.append(car); dev_by[e['index']]+=1; dev_status[(e['index'],'ok')]+=1
                    except Exception as ex:
                        row['status']='error'; row['error']=f'{type(ex).__name__}: {ex}'
                        ew.writerow({k:row[k] for k in ['window','index','ticker','announcement_date','effective_date','error']})
                        ef.flush(); os.fsync(ef.fileno()); dev_status[(e['index'],'error')]+=1
                    writer.writerow(row); rf.flush(); os.fsync(rf.fileno())
                    if ix%25==0: print(f'dev_checkpoint={ix}/{len(dev)}',flush=True)
                for ix,e in enumerate(hold,1):
                    row={k:e.get(k,'') for k in ['window','index','ticker','announcement_date','effective_date']}
                    row.update(entry_date='',status='',error='',holding_sessions='',stock_return='',benchmark_return='',car='')
                    idx=e['index']; hold_total[idx]+=1
                    try:
                        ann=date.fromisoformat(e['announcement_date']); eff=date.fromisoformat(e['effective_date'])
                        entry=next((d for d in sessions if d>ann),None)
                        if entry is None or eff not in session_set or entry>eff: raise ValueError('calendar')
                        row['entry_date']=entry.isoformat()
                        # Presence-only parse: never retain or display holdout OHLC values.
                        bars,err=fetch_bars(sess,headers,e['ticker'],entry,eff,False); time.sleep(.34)
                        if err: raise RuntimeError(err)
                        if entry in bars and eff in bars:
                            row['status']='covered'; hold_cov[(idx,'covered')]+=1
                        else:
                            row['status']='missing_entry_or_effective_bar'; hold_cov[(idx,row['status'])]+=1
                    except Exception as ex:
                        row['status']='request_or_calendar_error'; row['error']=f'{type(ex).__name__}: {ex}'
                        ew.writerow({k:row[k] for k in ['window','index','ticker','announcement_date','effective_date','error']})
                        ef.flush(); os.fsync(ef.fileno()); hold_cov[(idx,'request_or_calendar_error')]+=1
                    writer.writerow(row); rf.flush(); os.fsync(rf.fileno())
                    if ix%25==0: print(f'holdout_checkpoint={ix}/{len(hold)}',flush=True)

        pooled=summarize(dev_cars)
        by={i:summarize([float(r['car']) for r in csv.DictReader((OUT/'event_results.csv').open(encoding='utf-8')) if r['window']=='dev' and r['index']==i and r['status']=='ok']) for i in ['S&P 500','S&P 400']}
        costs={label:{str(b): (s['mean']-2*b/10000 if s['mean'] is not None else None) for b in (5,10,20)} for label,s in [('pooled',pooled),*by.items()]}
        hold_covered=sum(hold_cov[(i,'covered')] for i in ['S&P 500','S&P 400'])
        hold_n=sum(hold_total[i] for i in ['S&P 500','S&P 400'])
        missing_pct=100*(hold_n-hold_covered)/hold_n if hold_n else None
        mde=2.970*pooled['sd']/math.sqrt(hold_covered) if pooled['sd'] is not None and hold_covered else None
        primary=costs['pooled']['10']
        decision='prereg_draft' if primary is not None and mde is not None and primary>mde and missing_pct<=3 else 's2_exhausted'
        output={'tag':'L-IDX5','registered_test':'L-IDX5-01','event_list_sha256':digest,
                'announcement_date_counts':{'frozen_dated_events':len(events),'holdout_candidates':len(hold_candidates),
                  'holdout_candidates_by_index':{i:sum(e['index']==i for e in hold_candidates) for i in ['S&P 500','S&P 400']},
                  'holdout_found_announcement_by_index':{i:sum(e['index']==i and e.get('announcement_found')=='1' for e in hold_candidates) for i in ['S&P 500','S&P 400']},
                  'holdout_missing_announcement_candidates':len(meta_missing),
                  'holdout_missing_by_index':{i:sum(e.get('index')==i for e in meta_missing) for i in ['S&P 500','S&P 400']},
                  'dropped_500_to_400_migrations':sum(e.get('migration_from_sp500')=='1' for e in hold_candidates)},
                'development':{'eligible_events':len(dev),'usable':pooled,'by_index':by,'mean_net_car':costs,
                  'status_counts_by_index_and_status':{f'{i}|{s}':n for (i,s),n in dev_status.items()}},
                'holdout_coverage_counts_only':{'eligible_events':hold_n,'covered_N':hold_covered,'missing_pct':missing_pct,
                  'by_index':{i:{s:int(hold_cov[(i,s)]) for s in ['covered','missing_entry_or_effective_bar','request_or_calendar_error']} for i in ['S&P 500','S&P 400']}},
                'mde':mde,'primary_net_mean_10bp_one_way':primary,'decision':decision}
        with (OUT/'results.json').open('w',encoding='utf-8') as f: json.dump(output,f,indent=2); f.flush(); os.fsync(f.fileno())
        # This summary contains development returns and holdout coverage counts only.
        print(json.dumps(output,indent=2),flush=True)
    finally:
        release_lock()

if __name__=='__main__': main()
