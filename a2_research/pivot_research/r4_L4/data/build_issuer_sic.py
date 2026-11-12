"""Build a dated SEC issuer-SIC snapshot for Dow names in the network panel."""
import csv, json, time
from pathlib import Path
import requests

OUT=Path('A2/pivot_research/r4_L4/data')
UA='FINS3666 network data project contact research@example.edu'
s=requests.Session(); s.headers.update({'User-Agent':UA,'Accept-Encoding':'gzip, deflate'})
r=s.get('https://www.sec.gov/files/company_tickers_exchange.json',timeout=60); r.raise_for_status()
items=r.json()['data']; headers=r.json()['fields']; rows=[dict(zip(headers,x)) for x in items]
targets=set('AAPL AMGN AMZN AXP BA CAT CRM CSCO CVX DOW DIS GS HD HON IBM INTC JNJ JPM KO MCD MMM MRK MSFT NKE NVDA PG RTX SHW TRV UNH V VZ WBA WMT XOM PFE'.split())
out=[]
for ticker in sorted(targets):
    matches=[x for x in rows if str(x.get('ticker','')).upper()==ticker]
    if not matches:
        out.append([ticker,'','','','','2026-11-10','not_found_in_SEC_ticker_file']); continue
    cik=str(matches[0]['cik']).zfill(10)
    time.sleep(.2)
    q=s.get(f'https://data.sec.gov/submissions/CIK{cik}.json',timeout=60); q.raise_for_status(); data=q.json()
    sic=data.get('sic',''); desc=data.get('sicDescription','')
    rec=data.get('filings',{}).get('recent',{})
    filed=''
    for i,form in enumerate(rec.get('form',[])):
        if form=='10-K': filed=rec.get('filingDate',[''])[i]; break
    out.append([ticker,cik,matches[0].get('name',''),sic,desc,filed,'current_submissions_SIC; filing date is latest available 10-K in recent block'])
with (OUT/'issuer_sic_snapshot.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['ticker','cik','issuer_name','sic','sic_description','latest_10k_filing_date','availability_note']); w.writerows(out)
