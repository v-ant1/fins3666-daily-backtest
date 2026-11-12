"""Metadata-only Tiingo coverage against PIT S&P membership windows."""
import csv, datetime as dt, difflib, json, time, urllib.parse
from pathlib import Path
import pandas as pd
import requests
from dotenv import dotenv_values

START=dt.date(2010,1,4); END=dt.date(2015,12,31); ENDX=END+dt.timedelta(days=1)
ENV=Path(r'C:/Users/musta/Desktop/UNSW/SSI/FINS3666/A2/.env')
OUT=Path(__file__).resolve().parent; ROWS=OUT/'coverage_rows.csv'; ROSTER=OUT/'pit_membership_windows.csv'; MANIFEST=OUT/'run_manifest.json'
HEAD={'User-Agent':'Mozilla/5.0 (compatible; R10L1CTiingoMetadata/1.0)'}
FIELDS=['source_ticker','request_ticker','expected_issuer','window_start','window_end_exclusive','status','returned_ticker','name','name_status','startDate','endDate','error_type','checked_at_utc']

def normcols(cols):
 return [' '.join(str(x) for x in c if str(x)!='nan').strip().lower() if isinstance(c,tuple) else str(c).strip().lower() for c in cols]

def build_roster():
 hurl='https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500'; curl='https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
 hist=next(t for t in pd.read_html(hurl,storage_options=HEAD) if normcols(t.columns)[:5]==['effective date effective date','added ticker','added security','removed ticker','removed security'])
 changes=[]
 for _,r in hist.iterrows():
  try:d=pd.to_datetime(r.iloc[0]).date()
  except Exception:continue
  changes.append((d,str(r.iloc[1]).split('|')[0].strip(),str(r.iloc[2]).strip(),str(r.iloc[3]).split('|')[0].strip(),str(r.iloc[4]).strip()))
 cur=next(t for t in pd.read_html(curl,storage_options=HEAD) if 'Symbol' in t.columns and 'Security' in t.columns)
 active={str(r['Symbol']).strip():str(r['Security']).strip() for _,r in cur.iterrows() if str(r['Symbol']).strip()}; current=set(active)
 for d,a,an,rm,rn in sorted(changes,reverse=True):
  if d>START:active.pop(a,None);active[rm]=rn
 opened={t:(START,n) for t,n in active.items()}; identities=set(opened); windows=[]
 for d,a,an,rm,rn in sorted((x for x in changes if START<=x[0]<ENDX and x[0].weekday()<5),key=lambda x:x[0]):
  identities.update((a,rm))
  if rm in opened:
   begin,issuer=opened.pop(rm)
   if begin<d:windows.append({'ticker':rm,'issuer_name':issuer,'window_start':begin.isoformat(),'window_end_exclusive':d.isoformat()})
  opened[a]=(d,an)
 for t,(begin,issuer) in opened.items():windows.append({'ticker':t,'issuer_name':issuer,'window_start':begin.isoformat(),'window_end_exclusive':ENDX.isoformat()})
 if len(identities)!=619:raise RuntimeError(f'L1 roster identity mismatch: {len(identities)}')
 by={}
 for w in windows:by.setdefault(w['ticker'],[]).append(w)
 if len(by)!=618:raise RuntimeError(f'L1 endpoint-symbol mismatch: expected 618 (one recycled symbol among 619 PIT identities), got {len(by)}')
 with ROSTER.open('w',newline='',encoding='utf-8') as f:
  wr=csv.DictWriter(f,fieldnames=['ticker','issuer_name','window_start','window_end_exclusive']);wr.writeheader();wr.writerows(windows)
 return by,current

def name_match(expected,returned):
 if not returned:return 'name_missing'
 clean=lambda s:''.join(c.lower() for c in s if c.isalnum());a,b=clean(expected),clean(returned)
 if a==b or a in b or b in a:return 'match'
 return 'match_fuzzy' if difflib.SequenceMatcher(None,a,b).ratio()>=.82 else 'recycled_ambiguous'

def main():
 by,current=build_roster();removed=sorted(set(by)-current);ordered=removed+sorted(set(by)&current)
 selected=ordered[50:499] # 449 roster symbols; one L1C slot was spent on a malformed source ticker
 vals=dotenv_values(ENV)
 if not vals.get('KEY'):raise RuntimeError('Configured dotenv key KEY is unavailable')
 existing={}
 if ROWS.exists():
  with ROWS.open(newline='',encoding='utf-8') as f:existing={r['source_ticker']:r for r in csv.DictReader(f)}
 pending=[t for t in selected if t not in existing]
 if len(existing)+len(pending)>450:raise RuntimeError('L1C unique-symbol monthly budget exceeded')
 first=not ROWS.exists();session=requests.Session();last=None
 if existing:
  recent=max(dt.datetime.fromisoformat(r['checked_at_utc']) for r in existing.values())
  elapsed=max(0,(dt.datetime.now(dt.timezone.utc)-recent).total_seconds())
  last=time.monotonic()-elapsed
 for i,t in enumerate(pending,1):
  if last is not None:
   delay=75-(time.monotonic()-last)
   if delay>0:time.sleep(delay)
  entries=by[t];names=sorted({e['issuer_name'] for e in entries})
  begin=min(dt.date.fromisoformat(e['window_start']) for e in entries);end=max(dt.date.fromisoformat(e['window_end_exclusive']) for e in entries)
  sym=t.replace('.','-');url='https://api.tiingo.com/tiingo/daily/'+urllib.parse.quote(sym,safe='-')
  row=dict(source_ticker=t,request_ticker=sym,expected_issuer=' | '.join(names),window_start=begin.isoformat(),window_end_exclusive=end.isoformat(),status='transport_error',returned_ticker='',name='',name_status='',startDate='',endDate='',error_type='',checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
  last=time.monotonic()
  try:
   resp=session.get(url,params={'token':vals['KEY']},timeout=25);row['status']=str(resp.status_code)
   if resp.status_code==200:
    obj=resp.json();row.update(returned_ticker=obj.get('ticker',''),name=obj.get('name',''),startDate=obj.get('startDate',''),endDate=obj.get('endDate',''))
    states=[name_match(n,row['name']) for n in names];row['name_status']='recycled_ambiguous' if 'recycled_ambiguous' in states or len(entries)>1 else (states[0] if states else 'name_missing')
  except Exception as exc:row['error_type']=type(exc).__name__
  with ROWS.open('a',newline='',encoding='utf-8') as f:
   wr=csv.DictWriter(f,fieldnames=FIELDS)
   if first:wr.writeheader();first=False
   wr.writerow(row)
  print(json.dumps({'completed_this_run':i,'total_target':len(pending),'ticker':t,'status':row['status']}),flush=True)
 total=len(existing)+len(pending);roster_checked=len(set(existing)&set(by))+len(pending);manifest={'roster_identities':619,'unique_endpoint_symbols':len(by),'removed_pool':len(removed),'previously_used_symbols':50,'new_symbol_monthly_cap':450,'new_symbols_checkpointed':total,'nonroster_requests':sum(t not in by for t in existing),'roster_symbols_checked_this_month':50+roster_checked,'remaining_roster_symbols':max(0,len(by)-50-roster_checked),'remaining_first_check_date':'2026-12-01','result_rows':str(ROWS),'roster_windows':str(ROSTER)}
 MANIFEST.write_text(json.dumps(manifest,indent=2),encoding='utf-8');print('RUN_COMPLETE',json.dumps(manifest),flush=True)

if __name__=='__main__':main()
