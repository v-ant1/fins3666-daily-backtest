from pathlib import Path
from dotenv import dotenv_values
import numpy as np, pandas as pd, requests, time
root=Path.cwd(); env=dotenv_values(root.parent/'.env')
headers={'APCA-API-KEY-ID':str(env['ALPACA_API_KEY']),'APCA-API-SECRET-KEY':str(env['ALPACA_SECRET_KEY']),'Accept':'application/json'}
z=np.load(root/'r9/data/J2_DEV_FROM_20201127.npz',allow_pickle=False)
dates=pd.to_datetime(z['sp500_dates']); assets=np.array([str(x).upper().replace('.','-') for x in z['sp500_assets']]); roster=z['sp500_roster'].astype(bool); op=z['sp500_adjusted_open'];cl=z['sp500_adjusted_close']
qs=pd.to_datetime(pd.read_csv(root/'r10/L3B/quarterly_outcomes.csv').cutoff_session)
need={}
for x in qs:
 i=int(np.searchsorted(dates.values,x.to_datetime64())); en=i+1; ex=en+19
 for ai in np.flatnonzero(roster[:,en]):
  for idx,arr in ((en,op),(ex,cl)):
   if not np.isfinite(arr[ai,idx]): need.setdefault(assets[ai],set()).add(str(dates[idx].date()))
path=root/'r10/L3B/alpaca_gap_bars.csv'; existing={}
if path.exists():
 old=pd.read_csv(path)
 existing={t:set(g.date.astype(str)) for t,g in old.groupby('ticker')}
base='https://data.alpaca.markets/v2/stocks'; out=[]; errors=[]; sess=requests.Session()
for ticker, ds in sorted(need.items()):
 if ds.issubset(existing.get(ticker,set())): continue
 symbol={'BF-B':'BF.B','BRK-B':'BRK.B'}.get(ticker,ticker)
 params={'timeframe':'1Day','start':min(ds)+'T00:00:00Z','end':(pd.Timestamp(max(ds))+pd.Timedelta(days=1)).strftime('%Y-%m-%dT23:59:59Z'),'feed':'sip','adjustment':'all','limit':10000,'sort':'asc'}
 token=None; found={}; error=None
 for page in range(10):
  q=dict(params)
  if token:q['page_token']=token
  try: resp=sess.get(f'{base}/{symbol}/bars',params=q,headers=headers,timeout=(10,35))
  except Exception as e: error=type(e).__name__;break
  if resp.status_code==429: time.sleep(3);continue
  if not resp.ok:error=f'HTTP_{resp.status_code}';break
  js=resp.json()
  for b in (js.get('bars') or []):
   day=pd.Timestamp(b['t']).date().isoformat()
   if day in ds: found[day]=(float(b['o']),float(b['c']))
  token=js.get('next_page_token')
  if not token:break
  time.sleep(.2)
 if error: errors.append((ticker,error))
 if found:
  chunk=pd.DataFrame([{'ticker':ticker,'date':day,'open':v[0],'close':v[1]} for day,v in found.items()])
  chunk.to_csv(path,index=False,mode='a',header=not path.exists())
  out.extend(found)
 time.sleep(.2)
old=pd.read_csv(path) if path.exists() else pd.DataFrame(columns=['ticker','date'])
print('requested_tickers',len(need),'requested_endpoint_pairs',sum(map(len,need.values())),'filled_pairs',len(old),'remaining_unfilled',sum(len(ds-existing.get(t,set())-set(old.loc[old.ticker.eq(t),'date'].astype(str))) for t,ds in need.items()),'errors',len(errors))
if errors: print('error_statuses',errors[:20])
