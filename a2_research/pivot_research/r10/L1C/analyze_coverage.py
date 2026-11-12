"""Summarize L1C metadata rows at PIT identity-window level."""
import csv, datetime as dt, difflib, json
from pathlib import Path

BASE=Path(__file__).resolve().parent
def clean(s):return ''.join(c.lower() for c in s if c.isalnum())
def matches(expected,actual):
 a,b=clean(expected),clean(actual or '')
 return bool(b) and (a==b or a in b or b in a or difflib.SequenceMatcher(None,a,b).ratio()>=.82)

with (BASE/'pit_membership_windows.csv').open(newline='',encoding='utf-8') as f: windows=list(csv.DictReader(f))
with (BASE/'coverage_rows.csv').open(newline='',encoding='utf-8') as f: results={r['source_ticker']:r for r in csv.DictReader(f)}
by={}
for w in windows:by.setdefault(w['ticker'],[]).append(w)
counts={'covered':0,'missing':0,'recycled_ambiguous':0,'not_queried':0}
details=[]
for ticker,entries in by.items():
 r=results.get(ticker)
 if r is None:
  counts['not_queried']+=len(entries);continue
 for w in entries:
  status='missing';reason='unusable_or_non200'
  if r['status']=='200' and r['name'] and r['startDate'] and r['endDate']:
   if not matches(w['issuer_name'],r['name']):status='recycled_ambiguous';reason='issuer_name_mismatch'
   else:
    last_day=(dt.date.fromisoformat(w['window_end_exclusive'])-dt.timedelta(days=1)).isoformat()
    if r['startDate']<=w['window_start'] and r['endDate']>=last_day:status='covered';reason='metadata_spans_identity_window'
    else:status='missing';reason='metadata_dates_do_not_span_identity_window'
  elif r['status']=='200':reason='metadata_fields_not_captured'
  counts[status]+=1
  details.append({'ticker':ticker,'issuer_name':w['issuer_name'],'window_start':w['window_start'],'window_end_exclusive':w['window_end_exclusive'],'status':status,'reason':reason,'http_status':r['status'],'name':r['name'],'startDate':r['startDate'],'endDate':r['endDate']})
sample_n=sum(counts[k] for k in ('covered','missing','recycled_ambiguous'))
usable=counts['covered']+counts['missing']+counts['recycled_ambiguous']
summary={'roster_identities':len(windows),'queried_endpoint_symbols':len(results),'queried_identities':usable,'covered':counts['covered'],'covered_pct_of_queried_identities':round(100*counts['covered']/usable,2) if usable else None,'missing':counts['missing'],'missing_pct_of_queried_identities':round(100*counts['missing']/usable,2) if usable else None,'recycled_ambiguous':counts['recycled_ambiguous'],'recycled_ambiguous_pct_of_queried_identities':round(100*counts['recycled_ambiguous']/usable,2) if usable else None,'unqueried_identities':counts['not_queried'],'unqueried_pct_roster':round(100*counts['not_queried']/len(windows),2) if windows else None,'http_status_counts':{s:sum(1 for r in results.values() if r['status']==s) for s in sorted({r['status'] for r in results.values()})},'metadata_capture_failures':sum(1 for r in results.values() if r['status']=='200' and not (r['name'] and r['startDate'] and r['endDate']))}
(BASE/'coverage_identity_results.csv').write_text('ticker,issuer_name,window_start,window_end_exclusive,status,reason,http_status,name,startDate,endDate\n'+'\n'.join(','.join('"'+str(d[k]).replace('"','""')+'"' for k in ['ticker','issuer_name','window_start','window_end_exclusive','status','reason','http_status','name','startDate','endDate']) for d in details)+'\n',encoding='utf-8')
(BASE/'coverage_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
