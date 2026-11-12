"""Quarter-specific top-50 13F portfolios from SEC bulk data (2013Q1 onward)."""
import csv,io,re,time,zipfile,calendar,math
from datetime import datetime
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
import requests
OUT=Path('A2/pivot_research/r4_L4/data');UA='FINS3666 network data project contact research@example.edu'
s=requests.Session();s.headers.update({'User-Agent':UA,'Accept-Encoding':'gzip, deflate'})
def get(url):
 for k in range(4):
  try:
   r=s.get(url,timeout=180)
   if r.status_code==200:time.sleep(.18);return r
   if r.status_code not in (403,429,500,502,503):r.raise_for_status()
  except Exception:
   if k==3:raise
  time.sleep(1.5*(k+1))
 raise RuntimeError('could_not_fetch '+url)
class Links(HTMLParser):
 def __init__(self):super().__init__();self.in_a=False;self.href='';self.txt='';self.links=[]
 def handle_starttag(self,t,a):
  if t=='a':self.in_a=True;self.href=dict(a).get('href','');self.txt=''
 def handle_data(self,d):
  if self.in_a:self.txt+=d
 def handle_endtag(self,t):
  if t=='a':self.links.append((self.txt.strip(),self.href));self.in_a=False
def rep(label):
 m=re.match(r'^(\d{4}) Q([1-4]) 13F$',label)
 if m:
  y,q=map(int,m.groups());q-=1
  if q==0:y-=1;q=4
 else:
  m=re.match(r'^(\d{4}) (January|March|June|September|December)\b',label)
  if not m:return None
  y=int(m.group(1));month=m.group(2)
  q={'January':4,'March':1,'June':2,'September':3,'December':4}[month]
  if month=='January':y-=1
 mm=q*3;return f'{y}-{mm:02d}-{calendar.monthrange(y,mm)[1]:02d}'
def roster(d):
 r=set('MMM AA AXP T BAC BA CAT CSCO CVX KO DIS DD XOM GE HPQ HD IBM INTC JNJ JPM KFT MCD MRK MSFT PFE PG TRV UTX VZ WMT'.split())
 for cut,drop,add in [('2012-09-30',{'KFT'},{'UNH'}),('2013-09-30',{'BAC','AA','HPQ'},{'GS','V','NKE'}),('2015-03-31',{'T'},{'AAPL'}),('2017-09-30',{'DD'},{'DWDP'}),('2018-06-30',{'GE'},{'WBA'}),('2019-06-30',{'DWDP'},{'DOW'}),('2020-09-30',{'XOM','PFE','UTX'},{'CRM','AMGN','HON'}),('2024-03-31',{'WBA'},{'AMZN'}),('2024-12-31',{'DOW','INTC'},{'NVDA','SHW'})]:
  if d>=cut:r.difference_update(drop);r.update(add)
 return r
cusip={'88579Y101':'MMM','013872106':'AA','013817101':'AA','025816109':'AXP','037833100':'AAPL','00206R102':'T','060505104':'BAC','097023105':'BA','149123101':'CAT','17275R102':'CSCO','166764100':'CVX','191216100':'KO','254687106':'DIS','263534109':'DD','260543103':'DD','260557103':'DOW','30231G102':'XOM','369604103':'GE','40434L105':'HPQ','428236103':'HPQ','437076102':'HD','459200101':'IBM','458140100':'INTC','478160104':'JNJ','46625H100':'JPM','50075N104':'KFT','580135101':'MCD','58933Y105':'MRK','594918104':'MSFT','654106103':'NKE','717081103':'PFE','742718109':'PG','75513E101':'UTX','89417E109':'TRV','913017109':'UTX','92343V104':'VZ','931142103':'WMT','931427108':'WBA','91324P102':'UNH','38141G104':'GS','92826C839':'V','79466L302':'CRM','031162100':'AMGN','438516106':'HON','023135106':'AMZN','67066G104':'NVDA','824348106':'SHW'}
def ticker_for(c,name):
 n=(name or '').upper()
 if 'DOWDUPONT' in n:return 'DWDP'
 if 'DOW CHEMICAL' in n:return 'DD'
 if re.search(r'\bDOW INC\b',n):return 'DOW'
 return cusip.get(re.sub(r'\s+','',c or '').upper())
page=get('https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets').text;parser=Links();parser.feed(page)
archives={rep(lab):'https://www.sec.gov'+href for lab,href in parser.links if href.lower().endswith('.zip') and rep(lab)}
periods=[]
for y in range(2013,2027):
 for q in range(1,5):
  mm=q*3;d=f'{y}-{mm:02d}-{calendar.monthrange(y,mm)[1]:02d}'
  if '2013-03-31'<=d<='2026-06-30':periods.append(d)
allroster=[];allpos=[];allcoverage=[]
for period in periods:
 url=archives.get(period)
 if not url: print('NO_BULK',period,flush=True);continue
 print('quarter',period,flush=True);z=zipfile.ZipFile(io.BytesIO(get(url).content));files={n.rsplit('/',1)[-1].upper():n for n in z.namelist() if n.lower().endswith('.tsv')}
 def readtab(n):return list(csv.DictReader(io.TextIOWrapper(z.open(files[n]),encoding='utf-8-sig',newline=''),delimiter='\t'))
 sub=readtab('SUBMISSION.TSV');cover=readtab('COVERPAGE.TSV');summ=readtab('SUMMARYPAGE.TSV');info=files['INFOTABLE.TSV']
 cv={r['ACCESSION_NUMBER']:r for r in cover};sm={r['ACCESSION_NUMBER']:r for r in summ};best={}
 for r in sub:
  if r.get('SUBMISSIONTYPE')!='13F-HR' or r.get('PERIODOFREPORT','').upper()!=datetime.strptime(period,'%Y-%m-%d').strftime('%d-%b-%Y').upper():continue
  acc=r['ACCESSION_NUMBER'];c=cv.get(acc,{})
  if c.get('ISAMENDMENT','').strip().upper()=='Y':continue
  try:value=int(re.sub(r'[^0-9]','',sm[acc]['TABLEVALUETOTAL']))
  except (KeyError,ValueError):continue
  cik=r['CIK'].lstrip('0') or '0';name=c.get('FILINGMANAGER_NAME','').strip() or r.get('FILINGMANAGER_NAME','').strip()
  filed_raw=r.get('FILING_DATE','')
  try:filed=datetime.strptime(filed_raw,'%Y-%m-%d').strftime('%Y-%m-%d')
  except ValueError:
   try:filed=datetime.strptime(filed_raw,'%d-%b-%Y').strftime('%Y-%m-%d')
   except ValueError:filed=datetime.strptime(filed_raw,'%d%b%Y').strftime('%Y-%m-%d')
  old=best.get(cik)
  cand=(value,filed,acc,name)
  if old is None or cand[0]>old[0] or (cand[0]==old[0] and cand[1]<old[1]):best[cik]=cand
 ranked=sorted(((cik,*v) for cik,v in best.items()),key=lambda x:(-x[1],x[2],x[0]))[:50]
 selected={r[0]:r for r in ranked};acc_cik={r[3]:r[0] for r in ranked};members=roster(period)
 for rank,(cik,value,filed,acc,name) in enumerate(ranked,1):allroster.append([period,rank,cik,name,value,acc,filed,'sec_quarterly_bulk'])
 counts=defaultdict(int)
 for r in csv.DictReader(io.TextIOWrapper(z.open(info),encoding='utf-8-sig',newline=''),delimiter='\t'):
  acc=r.get('ACCESSION_NUMBER','');cik=acc_cik.get(acc)
  if not cik:continue
  t=ticker_for(r.get('CUSIP',''),r.get('NAMEOFISSUER',''))
  if t not in members:continue
  # Override the obsolete CUSIP alias only when issuer text identifies the Dow lineage.
  rr=selected[cik];filed=rr[2];manager=rr[4]
  allpos.append([period,filed,cik,manager,acc,t,re.sub(r'\s+','',r.get('CUSIP','')).upper(),r.get('NAMEOFISSUER',''),r.get('TITLEOFCLASS',''),r.get('VALUE',''),r.get('SSHPRNAMT',''),r.get('SSHPRNAMTTYPE','')]);counts[cik]+=1
 for rank,(cik,value,filed,acc,name) in enumerate(ranked,1):allcoverage.append([period,rank,cik,name,filed,acc,counts[cik],f'pit_top50_bulk_parsed_{counts[cik]}_Dow_rows'])

def write(file,header,rows):
 with (OUT/file).open('w',newline='',encoding='utf-8') as f:w=csv.writer(f);w.writerow(header);w.writerows(rows)
write('13f_top50_pit_roster.csv',['report_date','rank_by_table_value','manager_cik','manager_name','table_value_usd_thousands','accession_number','filing_date','selection_source'],allroster)
# Development versus holdout split; dates before 2020-11 are holdout/report metadata.
hold=[r for r in allpos if r[0]<='2020-09-30'];dev=[r for r in allpos if r[0]>='2020-06-30']
header=['report_date','availability_filing_date','manager_cik','manager_name','accession_number','ticker','cusip','reported_issuer','share_class','value_usd_thousands','shares_or_principal_amount','amount_type']
write('13f_holdout_bulk_pit_positions.csv',header,hold);write('13f_development_pit_positions.csv',header,dev)
write('13f_pit_bulk_coverage.csv',['report_date','rank_by_table_value','manager_cik','manager_name','filing_date','accession_number','mapped_dow_position_rows','status'],allcoverage)
print('WROTE',len(allroster),'roster rows',len(hold),'holdout pos',len(dev),'development pos',len(allcoverage),'coverage',flush=True)

