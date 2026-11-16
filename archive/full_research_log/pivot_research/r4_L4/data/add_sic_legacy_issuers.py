"""Fill legacy issuer CIK history missing from the current-ticker directory."""
import csv,re,time
from collections import defaultdict
from pathlib import Path
import requests
P=Path('A2/pivot_research/r4_L4/data');s=requests.Session();s.headers.update({'User-Agent':'FINS3666 network data project contact research@example.edu','Accept-Encoding':'gzip, deflate'})
def get(u):
 r=s.get(u,timeout=90);r.raise_for_status();time.sleep(.18);return r
rows=list(csv.DictReader((P/'sic_panel.csv').open(encoding='utf-8-sig',newline='')))
# DIS was reported under legacy CIK 1001039 through 2018 before the current Walt Disney CIK.
cik='0001001039';d=get(f'https://data.sec.gov/submissions/CIK{cik}.json').json();blocks=[d.get('filings',{}).get('recent',{})]
for f in d.get('filings',{}).get('files',[]):
 if f.get('filingFrom','')<='2018-12-31' and f.get('filingTo','')>='2010-01-01':blocks.append(get('https://data.sec.gov/submissions/'+f['name']).json())
filings=[]
for b in blocks:
 for form,day,acc in zip(b.get('form',[]),b.get('filingDate',[]),b.get('accessionNumber',[])):
  if form=='10-K' and '2010-01-01'<=day<='2018-12-31':filings.append((day,acc))
yearly={}
for day,acc in sorted(filings):yearly.setdefault(day[:4],(day,acc))
for year,(day,acc) in sorted(yearly.items()):
 if any(r['ticker']=='DIS' and r['effective_from'][:4]==year for r in rows):continue
 u=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-','')}/{acc}.hdr.sgml";txt=get(u).text;m=re.search(r'<ASSIGNED-SIC>\s*(\d{4})',txt,re.I);rows.append({'ticker':'DIS','cik':cik,'sic':m.group(1) if m else '', 'effective_from':day,'source_url':u})
# SEC's historical 2009 annual 10-K filings provide the SIC at the start of 2010 for T and VZ.
for ticker,cik,acc,day in [('T','0000732717','0000732717-09-000007','2009-02-25'),('VZ','0000732712','0001193125-09-036349','2009-02-24')]:
 if any(r['ticker']==ticker and r['effective_from']<='2010-01-01' for r in rows):continue
 u=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-','')}/{acc}.hdr.sgml";txt=get(u).text;m=re.search(r'<ASSIGNED-SIC>\s*(\d{4})',txt,re.I);rows.append({'ticker':ticker,'cik':cik,'sic':m.group(1) if m else '', 'effective_from':day,'source_url':u})
unique={}
for r in rows:unique.setdefault((r['ticker'],r['effective_from']),r)
rows=sorted(unique.values(),key=lambda r:(r['ticker'],r['effective_from']))
with (P/'sic_panel.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=['ticker','cik','sic','effective_from','source_url']);w.writeheader();w.writerows(rows)
by=defaultdict(list)
for r in rows:by[r['ticker']].append(r)
with (P/'sic_panel_coverage.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['ticker','cik','dated_sic_rows','first_effective_from','last_effective_from','missing_sic_rows'])
 for t,rs in sorted(by.items()):w.writerow([t,rs[0]['cik'],len(rs),min(r['effective_from'] for r in rs),max(r['effective_from'] for r in rs),sum(not r['sic'] for r in rs)])
gapfile=P/'sic_panel_seed_gaps.csv'
gaps=list(csv.DictReader(gapfile.open(encoding='utf-8-sig',newline=''))) if gapfile.exists() else []
gaps=[g for g in gaps if g['ticker'] not in {'DIS','T','VZ'}]
with (P/'sic_panel_seed_gaps.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=['ticker','cik','date','status','source_or_accession']);w.writeheader();w.writerows(gaps)
print('rows',len(rows),'tickers',len(by),'missing SIC',sum(not r['sic'] for r in rows),'DIS rows',len(by['DIS']),'range',min(r['effective_from'] for r in rows),max(r['effective_from'] for r in rows),'seed gaps',sorted(set(g['ticker'] for g in gaps)),flush=True)
