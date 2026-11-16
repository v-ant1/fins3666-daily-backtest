"""Build annual point-in-time SIC observations from EDGAR 10-K submission headers."""
import csv,json,re,time
from pathlib import Path
import requests
OUT=Path('A2/pivot_research/r4_L4/data');UA='FINS3666 network data project contact research@example.edu'
s=requests.Session();s.headers.update({'User-Agent':UA,'Accept-Encoding':'gzip, deflate'})
def get(url):
 for n in range(4):
  try:
   r=s.get(url,timeout=90)
   if r.status_code==200:time.sleep(.18);return r
   if r.status_code not in (403,429,500,502,503):r.raise_for_status()
  except Exception:
   if n==3:raise
  time.sleep(1.5*(n+1))
 raise RuntimeError(url)
manual={
'AA':('0000004281','Alcoa Inc'),'BAC':('0000070858','Bank of America Corporation'),'T':('0000732717','AT&T Inc'),
'DD':('0000030554','E. I. du Pont de Nemours and Company'),'DWDP':('0001666700','DowDuPont Inc'),'DOW':('0001751788','Dow Inc'),
'GE':('0000040545','General Electric Company'),'HPQ':('0000047217','HP Inc'),'KFT':('0001103982','Kraft Foods Inc'),
'UTX':('0000101829','United Technologies Corporation'),'RTX':('0000101829','Raytheon Technologies Corporation'),
'WBA':('0001618921','Walgreens Boots Alliance'),'XOM':('0000034088','Exxon Mobil Corporation')}
tickers=set('MMM AA AXP T BAC BA CAT CSCO CVX KO DIS DD DWDP DOW XOM GE HPQ HD IBM INTC JNJ JPM KFT UNH MCD MRK MSFT PFE PG TRV UTX RTX VZ WMT GS V NKE AAPL WBA CRM AMGN HON AMZN NVDA SHW'.split())
company=get('https://www.sec.gov/files/company_tickers_exchange.json').json();fields=company['fields'];records=[dict(zip(fields,r)) for r in company['data']]
for t in sorted(tickers):
 if t not in manual:
  matches=[r for r in records if str(r.get('ticker','')).upper()==t]
  if matches:manual[t]=(str(matches[0]['cik']).zfill(10),matches[0]['name'])
rows=[];gaps=[]
for ticker,(cik,name) in sorted(manual.items()):
 try:
  data=get(f'https://data.sec.gov/submissions/CIK{cik}.json').json();blocks=[data.get('filings',{}).get('recent',{})]
  for f in data.get('filings',{}).get('files',[]):
   if f.get('filingTo','')>='2010-01-01' and f.get('filingFrom','')<='2026-10-31':blocks.append(get('https://data.sec.gov/submissions/'+f['name']).json())
  filings=[]
  for b in blocks:
   for form,day,acc in zip(b.get('form',[]),b.get('filingDate',[]),b.get('accessionNumber',[])):
    if form=='10-K' and '2010-01-01'<=day<='2026-10-31':filings.append((day,acc))
  yearly={}
  for day,acc in sorted(filings):yearly.setdefault(day[:4],(day,acc))
  if not yearly:gaps.append([ticker,cik,'','no_10K_in_window','']);continue
  for year,(day,acc) in sorted(yearly.items()):
   url=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-','')}/{acc}.hdr.sgml"
   try:
    txt=get(url).text;m=re.search(r'<ASSIGNED-SIC>\s*(\d{4})',txt,re.I);sic=m.group(1) if m else ''
    rows.append([ticker,cik,sic,day,url])
    if not sic:gaps.append([ticker,cik,day,'sic_missing_in_filing_header',url])
   except Exception as e:gaps.append([ticker,cik,day,'header_fetch_failed_'+type(e).__name__,url])
  print(ticker,len(yearly),flush=True)
 except Exception as e:gaps.append([ticker,cik,'','submissions_failed_'+type(e).__name__,'']);print('ERROR',ticker,type(e).__name__,flush=True)
with (OUT/'sic_panel.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['ticker','cik','sic','effective_from','source_url']);w.writerows(rows)
with (OUT/'sic_panel_gaps.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['ticker','cik','date','status','source_or_accession']);w.writerows(gaps)
print('wrote',len(rows),'dated rows; SIC values',sum(bool(r[2]) for r in rows),'gaps',len(gaps),flush=True)
