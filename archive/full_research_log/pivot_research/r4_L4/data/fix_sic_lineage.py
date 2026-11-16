"""Repair the Dow / DuPont issuer and ticker lineage in sic_panel.csv.

SIC effective_from remains the SEC 10-K filing date (availability date).
Ticker identity boundaries are documented separately in NETWORK_DATA.md / FIX_QA.md.
"""
import csv, json, re, time
from collections import defaultdict
from pathlib import Path
import requests
P=Path('A2/pivot_research/r4_L4/data')
UA='FINS3666 network data project contact research@example.edu'
s=requests.Session(); s.headers.update({'User-Agent':UA,'Accept-Encoding':'gzip, deflate'})
def get(url):
    r=s.get(url,timeout=90); r.raise_for_status(); time.sleep(.2); return r

def filing_rows(cik, ticker, from_date='2010-01-01', through='2026-10-31', ticker_stop=None):
    submission=get(f'https://data.sec.gov/submissions/CIK{cik}.json').json()
    blocks=[submission.get('filings',{}).get('recent',{})]
    for f in submission.get('filings',{}).get('files',[]):
        if f.get('filingTo','')>=from_date and f.get('filingFrom','')<=through:
            blocks.append(get('https://data.sec.gov/submissions/'+f['name']).json())
    filings=[]
    for b in blocks:
        for form,day,acc in zip(b.get('form',[]),b.get('filingDate',[]),b.get('accessionNumber',[])):
            if form=='10-K' and from_date<=day<=through and (ticker_stop is None or day<ticker_stop):
                filings.append((day,acc))
    # One row per filing year, using the earliest annual 10-K filing of that year.
    yearly={}
    for day,acc in sorted(filings): yearly.setdefault(day[:4],(day,acc))
    out=[]
    for day,acc in yearly.values():
        url=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-','')}/{acc}.hdr.sgml"
        txt=get(url).text
        m=re.search(r'<ASSIGNED-SIC>\s*(\d{4})',txt,re.I)
        out.append({'ticker':ticker,'cik':cik,'sic':m.group(1) if m else '', 'effective_from':day,'source_url':url})
    return out

file=P/'sic_panel.csv'
base=list(csv.DictReader(file.open(encoding='utf-8-sig',newline='')))
# Keep unrelated issuers and old pre-window seed rows; replace all in-window rows for the affected symbols.
rows=[r for r in base if r['ticker'] not in {'DD','DWDP'} and not (r['ticker']=='DOW' and r['cik']=='0000029915')]
rows += [r for r in base if r['ticker']=='DD' and r['effective_from']<'2010-01-01']
# Legacy DuPont ticker DD ended with the 2017 merger. It must never appear under CIK 30554 later.
rows += filing_rows('0000030554','DD',through='2017-08-31')
# Old Dow Chemical ticker DOW ended with the 2017 merger; DowDuPont filed under CIK 1666700 thereafter.
rows += filing_rows('0000029915','DOW',through='2017-08-31')
# DowDuPont used DWDP until the ticker change to DD on 2019-06-03; SIC is available only as of filing.
for r in filing_rows('0001666700','DWDP',from_date='2017-09-01'):
    r['ticker']='DWDP' if r['effective_from']<'2019-06-03' else 'DD'
    rows.append(r)
# Keep current Dow Inc. (CIK 1751788) dated header rows, beginning when filings became available.
uniq={}
for r in rows:
    uniq[(r['ticker'],r['cik'],r['effective_from'])]=r
rows=sorted(uniq.values(),key=lambda r:(r['ticker'],r['effective_from'],r['cik']))
with file.open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['ticker','cik','sic','effective_from','source_url']);w.writeheader();w.writerows(rows)
by=defaultdict(list)
for r in rows:by[r['ticker']].append(r)
with (P/'sic_panel_coverage.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['ticker','ciks','dated_sic_rows','first_effective_from','last_effective_from','missing_sic_rows'])
    for t,rs in sorted(by.items()):
        w.writerow([t,';'.join(sorted(set(r['cik'] for r in rs))),len(rs),min(r['effective_from'] for r in rs),max(r['effective_from'] for r in rs),sum(not r['sic'] for r in rs)])
print('rows',len(rows),'tickers',len(by),'missing SIC',sum(not r['sic'] for r in rows))
for t in ['DOW','DWDP','DD']:
    print(t,[(r['cik'],r['effective_from'],r['sic']) for r in rows if r['ticker']==t])
