import time, json, csv
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlencode
import requests
import pandas as pd

root=Path('r6_data/etf'); root.mkdir(parents=True, exist_ok=True)
DEV_START=int(pd.Timestamp('2020-06-01',tz='America/New_York').timestamp())
DEV_END=int(pd.Timestamp('2026-11-01',tz='America/New_York').timestamp())
HOLD_START=int(pd.Timestamp('2009-11-01',tz='America/New_York').timestamp())
HOLD_END=int(pd.Timestamp('2020-11-01',tz='America/New_York').timestamp())
TICKERS='XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY SPY DIA QQQ IWM TLT IEF HYG GLD'.split()
s=requests.Session(); s.headers.update({'User-Agent':'FINS3666 Data Research Project contact research@example.edu','Accept':'application/json'})
rows=[]; hold=[]; errs=[]
for ix,t in enumerate(TICKERS):
    url=f'https://query1.finance.yahoo.com/v8/finance/chart/{t}?'+urlencode({'period1':DEV_START,'period2':DEV_END,'interval':'1d','events':'div,splits'})
    try:
        resp=s.get(url,timeout=45); resp.raise_for_status(); j=resp.json()['chart']['result'][0]
        ts=j.get('timestamp') or []; q=j['indicators']['quote'][0]; adj=j.get('indicators',{}).get('adjclose',[{}])[0].get('adjclose',[])
        for n,stamp in enumerate(ts):
            dt=pd.Timestamp(stamp,unit='s',tz='UTC').tz_convert('America/New_York').date().isoformat()
            rows.append({'date':dt,'ticker':t,'open':q['open'][n],'high':q['high'][n],'low':q['low'][n],'close':q['close'][n], 'adj_close':adj[n] if n<len(adj) else None,'volume':q['volume'][n]})
        hold_url=f'https://query1.finance.yahoo.com/v8/finance/chart/{t}?'+urlencode({'period1':HOLD_START,'period2':HOLD_END,'interval':'1d'})
        time.sleep(.25)
        hr=s.get(hold_url,timeout=45); hr.raise_for_status(); hj=hr.json()['chart']['result'][0]
        # Availability only: consume timestamps, discard every market-data field.
        hts=hj.get('timestamp') or []
        hdates=[pd.Timestamp(x,unit='s',tz='UTC').tz_convert('America/New_York').date().isoformat() for x in hts]
        hold.append({'ticker':t,'holdout_rows':len(hts),'first_date':min(hdates) if hdates else '', 'last_date':max(hdates) if hdates else '', 'check_window':'2009-11-01 to 2020-10-31','checked':'timestamps only'})
        print(f'{t}: dev rows {len(ts)}; holdout timestamp rows {len(hts)}',flush=True)
    except Exception as e:
        errs.append({'ticker':t,'error':repr(e)})
        print(f'{t}: ERROR {e}',flush=True)
    time.sleep(.25)
if rows:
    df=pd.DataFrame(rows).sort_values(['ticker','date'])
    df.to_parquet(root/'etf_ohlcv_dev.parquet',index=False)
    print('saved',len(df),'rows')
pd.DataFrame(hold).to_csv(root/'holdout_availability.csv',index=False)
pd.DataFrame(errs,columns=['ticker','error']).to_csv(root/'download_errors.csv',index=False)
