"""Add the latest pre-2010 10-K SIC header per ticker as the 2010 PIT seed."""
import csv,re,time
from collections import defaultdict
from pathlib import Path
import requests
P=Path('A2/pivot_research/r4_L4/data');s=requests.Session();s.headers.update({'User-Agent':'FINS3666 network data project contact research@example.edu','Accept-Encoding':'gzip, deflate'})
def get(u):
 r=s.get(u,timeout=90);r.raise_for_status();time.sleep(.18);return r
rows=list(csv.DictReader((P/'sic_panel.csv').open(encoding='utf-8-sig',newline='')))
tickers=defaultdict(set)
for r in rows:tickers[r['ticker']].add(r['cik'])
latest={};errors=[]
for ticker,ciks in sorted(tickers.items()):
 candidates=[]
 for cik in sorted(ciks):
  try:
   d=get(f'https://data.sec.gov/submissions/CIK{cik}.json').json();blocks=[d.get('filings',{}).get('recent',{})]
   for f in d.get('filings',{}).get('files',[]):
    if f.get('filingFrom','')<'2010-01-01':blocks.append(get('https://data.sec.gov/submissions/'+f['name']).json())
   for b in blocks:
    for form,day,acc in zip(b.get('form',[]),b.get('filingDate',[]),b.get('accessionNumber',[])):
     if form.startswith('10-K') and day<'2010-01-01':candidates.append((day,acc,cik))
  except Exception as e:errors.append([ticker,cik,'','seed_metadata_failed_'+type(e).__name__,''])
 if candidates:latest[ticker]=max(candidates)
 else:errors.append([ticker,','.join(sorted(ciks)),'','no_pre2010_10K_seed',''])
added=[]
for ticker,(day,acc,cik) in latest.items():
 url=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-','')}/{acc}.hdr.sgml"
 try:
  txt=get(url).text;m=re.search(r'<ASSIGNED-SIC>\s*(\d{4})',txt,re.I);sic=m.group(1) if m else ''
  added.append({'ticker':ticker,'cik':cik,'sic':sic,'effective_from':day,'source_url':url})
  if not sic:errors.append([ticker,cik,day,'sic_missing_in_seed_header',url])
 except Exception as e:errors.append([ticker,cik,day,'seed_header_failed_'+type(e).__name__,url])
rows=[r for r in rows if not (r['effective_from']<='2010-01-01' and r['ticker'] in latest)]
rows.extend(added);unique={}
for r in rows:unique.setdefault((r['ticker'],r['effective_from']),r)
rows=sorted(unique.values(),key=lambda r:(r['ticker'],r['effective_from']))
with (P/'sic_panel.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=['ticker','cik','sic','effective_from','source_url']);w.writeheader();w.writerows(rows)
by=defaultdict(list)
for r in rows:by[r['ticker']].append(r)
with (P/'sic_panel_coverage.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['ticker','cik','dated_sic_rows','first_effective_from','last_effective_from','missing_sic_rows'])
 for t,rs in sorted(by.items()):w.writerow([t,rs[0]['cik'],len(rs),min(r['effective_from'] for r in rs),max(r['effective_from'] for r in rs),sum(not r['sic'] for r in rs)])
with (P/'sic_panel_seed_gaps.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['ticker','cik','date','status','source_or_accession']);w.writerows(errors)
print('seed rows',len(added),'seed gaps',len(errors),'panel rows',len(rows),'SIC missing',sum(not r['sic'] for r in rows),'names without seed',sorted(set(x[0] for x in errors)),flush=True)
