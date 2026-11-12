import csv,re,time
from pathlib import Path
import requests
OUT=Path('A2/pivot_research/r4_L4/data'); UA='FINS3666 network data project contact research@example.edu'
s=requests.Session();s.headers.update({'User-Agent':UA,'Accept-Encoding':'gzip, deflate'})
rank=list(csv.DictReader((OUT/'13f_manager_rank_q2_2026.csv').open(encoding='utf-8-sig',newline=''))); names={r['manager_cik']:r['manager_name'] for r in rank}
meta=list(csv.DictReader((OUT/'13f_top50_holdout_filing_metadata.csv').open(encoding='utf-8-sig',newline='')))
# 2010-2012 ticker CUSIPs used in their Dow membership; securities in the index by quarter.
cm={'88579Y101':'MMM','013872106':'AA','013817101':'AA','025816109':'AXP','037833100':'AAPL','00206R102':'T','060505104':'BAC','097023105':'BA','149123101':'CAT','17275R102':'CSCO','166764100':'CVX','191216100':'KO','254687106':'DIS','263534109':'DD','260543103':'DD','30231G102':'XOM','369604103':'GE','40434L105':'HPQ','428236103':'HPQ','437076102':'HD','459200101':'IBM','458140100':'INTC','478160104':'JNJ','46625H100':'JPM','50075N104':'KFT','580135101':'MCD','58933Y105':'MRK','594918104':'MSFT','717081103':'PFE','742718109':'PG','89417E109':'TRV','913017109':'UTX','91324P102':'UNH','92343V104':'VZ','931142103':'WMT'}
def roster(d):
 r=set('MMM AA AXP T BAC BA CAT CSCO CVX KO DIS DD XOM GE HPQ HD IBM INTC JNJ JPM KFT MCD MRK MSFT PFE PG TRV UTX VZ WMT'.split())
 if d>='2012-09-30':r.discard('KFT');r.add('UNH')
 return r
periods={'2010-03-31','2010-06-30','2010-09-30','2010-12-31','2011-03-31','2011-06-30','2011-09-30','2011-12-31','2012-03-31','2012-06-30','2012-09-30','2012-12-31'}
positions=[];cov=[]
for rec in meta:
 p=rec['report_period']; c=rec['manager_cik'];acc=rec['accession_number'];date=rec['earliest_filing_date']
 if p not in periods: continue
 if not acc: cov.append([p,c,names[c],'','','no_original_13F_HR_index_entry',0]);continue
 u=f"https://www.sec.gov/Archives/edgar/data/{int(c)}/{acc.replace('-','')}/{acc}.txt"
 try:
  resp=s.get(u,timeout=180);resp.raise_for_status();txt=resp.text;time.sleep(.18)
  # Restrict parsing to the filing's information table; no unrelated document text is interpreted.
  low=txt.lower(); start=low.find('form 13f information table')
  body=txt[start:] if start>=0 else txt
  cnt=0
  for line in body.splitlines():
   for m in re.finditer(r'(?<![A-Z0-9])([A-Z0-9]{9})\s+([\d,]+)\s+([\d,]+)\s+(SH|PRN)\b',line,re.I):
    cusip,ticker=m.group(1).upper(),cm.get(m.group(1).upper())
    if not ticker or ticker not in roster(p):continue
    before=line[:m.start()].strip();issuer=re.sub(r'\s+',' ',before)[:180]
    val=m.group(2).replace(',','');amount=m.group(3).replace(',','')
    positions.append([p,date,c,names[c],acc,ticker,cusip,issuer,'',val,amount,m.group(4).upper()]);cnt+=1
  cov.append([p,c,names[c],date,acc,f'parsed_legacy_text_{cnt}_Dow_rows',cnt])
  if cnt:print(p,cnt,flush=True)
 except Exception as e:cov.append([p,c,names[c],date,acc,'download_or_parse_failed_'+type(e).__name__,0]);print('ERR',p,c,type(e).__name__,flush=True)
# Existing bulk build covers 2013Q1 onward. Keep only old period outputs here; combine after bulk completes.
with (OUT/'13f_holdout_pre2013_positions.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['report_date','availability_filing_date','manager_cik','manager_name','accession_number','ticker','cusip','reported_issuer','share_class','value_usd_thousands','shares_or_principal_amount','amount_type']);w.writerows(positions)
with (OUT/'13f_holdout_pre2013_coverage.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['report_date','manager_cik','manager_name','availability_filing_date','accession_number','status','mapped_dow_position_rows']);w.writerows(cov)
print('WROTE',len(positions),'position rows',len(cov),'manager quarters')
