"""Build the top-50 quarterly Dow common-ownership panel from SEC bulk files.

The ranking is fixed using SEC Q2 2026 reported 13F value totals. This builder
downloads quarterly public SEC data sets, filters rows in memory, and saves only
Dow constituent positions. No price data or pre-2020 positions are accessed.
"""
import calendar,csv,io,math,re,time,zipfile
from collections import defaultdict
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
import requests

OUT=Path('A2/pivot_research/r4_L4/data')
UA='FINS3666 network data project contact research@example.edu'
S=requests.Session();S.headers.update({'User-Agent':UA,'Accept-Encoding':'gzip, deflate'})
PAUSE=.2
BASE='https://www.sec.gov'

class Links(HTMLParser):
    def __init__(self): super().__init__();self.in_a=False;self.href='';self.text='';self.links=[]
    def handle_starttag(self,t,a):
        if t=='a': self.in_a=True;self.href=dict(a).get('href','');self.text=''
    def handle_data(self,d):
        if self.in_a:self.text+=d
    def handle_endtag(self,t):
        if t=='a':self.links.append((self.text.strip(),self.href));self.in_a=False

def get(url):
    for n in range(4):
        try:
            r=S.get(url,timeout=180)
            if r.status_code==200:
                time.sleep(PAUSE);return r
            if r.status_code not in (403,429,500,502,503):r.raise_for_status()
        except Exception:
            if n==3:raise
        time.sleep(1.5*(n+1))
    raise RuntimeError(url)

def quarter_end(y,q):
    m=q*3
    return f'{y}-{m:02d}-{calendar.monthrange(y,m)[1]:02d}'

def report_date_from_label(label):
    m=re.match(r'^(\d{4}) Q([1-4]) 13F$',label)
    if m:
        y=int(m.group(1));q=int(m.group(2))-1
        if q==0:y-=1;q=4
        return quarter_end(y,q)
    m=re.match(r'^(\d{4}) (January|February|March|April|May|June|July|August|September|October|November|December)',label)
    if not m:return None
    y=int(m.group(1));month=datetime.strptime(m.group(2),'%B').month
    # Datasets are grouped by filing months: Jan/Feb carry the prior Q4; all
    # other group starts correspond to the preceding quarter-end month.
    if month==1: y-=1; q=4
    else:q=((month-1)//3)+1
    return quarter_end(y,q)

ranked=list(csv.DictReader((OUT/'13f_manager_rank_q2_2026.csv').open(encoding='utf-8-sig',newline='')))
MANAGERS={r['manager_cik']:r['manager_name'] for r in ranked}
cusip_to_ticker={}
with (OUT/'build_13f_panel.py').open(encoding='utf-8') as f: source=f.read()
match=re.search(r'CUSIP_TO_TICKER\s*=\s*\{(.*?)\n\}',source,re.S)
if not match:raise RuntimeError('Could not load Dow CUSIP map')
for c,t in re.findall(r"'([A-Z0-9]{9})':'([A-Z]+)'",match.group(1)):cusip_to_ticker[c]=t

roster_initial=set('MMM AXP AAPL BA CAT CSCO CVX DIS DOW GS HD IBM INTC JNJ JPM KO MCD MRK MSFT NKE PFE PG RTX TRV VZ WBA WMT XOM'.split())
def roster_for(d):
    r=set(roster_initial)
    if d>='2020-09-30':r-={'PFE','XOM','RTX'};r|={'AMGN','CRM','HON'}
    if d>='2024-03-31':r-={'WBA'};r|={'AMZN'}
    if d>='2024-12-31':r-={'DOW','INTC'};r|={'NVDA','SHW'}
    return r

page=get('https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets').text
p=Links();p.feed(page)
archives={report:BASE+href for label,href in p.links if href.lower().endswith('.zip') and (report:=report_date_from_label(label))}
REPORT_DATES=[quarter_end(y,q) for y in range(2020,2027) for q in range(1,5) if '2020-06-30'<=quarter_end(y,q)<='2026-09-30']
raw=[];coverage=[]
for report in REPORT_DATES:
    url=archives.get(report)
    if not url:
        for cik,name in MANAGERS.items():coverage.append([cik,name,report,'','not_yet_available_in_SEC_bulk_dataset',''])
        continue
    print(f'Processing SEC bulk panel for {report}',flush=True)
    z=zipfile.ZipFile(io.BytesIO(get(url).content))
    files={n.rsplit('/',1)[-1]:n for n in z.namelist() if n.lower().endswith('.tsv')}
    def table(name):return list(csv.DictReader(io.TextIOWrapper(z.open(files[name]),encoding='utf-8-sig',newline=''),delimiter='\t'))
    submissions=table('SUBMISSION.tsv')
    cover=table('COVERPAGE.tsv')
    cover_by={x['ACCESSION_NUMBER']:x for x in cover}
    candidates=defaultdict(list)
    for s in submissions:
        if s['SUBMISSIONTYPE'] not in ('13F-HR','13F-HR/A') or s['PERIODOFREPORT']!=datetime.strptime(report,'%Y-%m-%d').strftime('%d-%b-%Y').upper():continue
        cik=s['CIK'].lstrip('0') or '0'
        if cik not in MANAGERS:continue
        c=cover_by.get(s['ACCESSION_NUMBER'],{})
        if c.get('ISAMENDMENT','').strip().upper()=='Y':continue
        try:filed=datetime.strptime(s['FILING_DATE'],'%d-%b-%Y').strftime('%Y-%m-%d')
        except ValueError:filed=s['FILING_DATE']
        candidates[cik].append((filed,s['ACCESSION_NUMBER']))
    selected={cik:sorted(v)[0] for cik,v in candidates.items()}
    row_count=defaultdict(int)
    accessions=set(x[1] for x in selected.values())
    for r in csv.DictReader(io.TextIOWrapper(z.open(files['INFOTABLE.tsv']),encoding='utf-8-sig',newline=''),delimiter='\t'):
        acc=r['ACCESSION_NUMBER']
        if acc not in accessions:continue
        cusip=re.sub(r'\s+','',r.get('CUSIP','')).upper(); ticker=cusip_to_ticker.get(cusip)
        if not ticker:continue
        cik=next(k for k,v in selected.items() if v[1]==acc)
        filed=selected[cik][0]
        raw.append([report,filed,cik,MANAGERS[cik],acc,ticker,cusip,r.get('NAMEOFISSUER',''),r.get('TITLEOFCLASS',''),r.get('VALUE',''),r.get('SSHPRNAMT',''),r.get('SSHPRNAMTTYPE','')])
        row_count[cik]+=1
    for cik,name in MANAGERS.items():
        if cik in selected:coverage.append([cik,name,report,selected[cik][0],f'parsed_{row_count[cik]}_Dow_rows',selected[cik][1]])
        else:coverage.append([cik,name,report,'','no_original_13F_HR_found_in_bulk_window',''])

def write(name,header,rows):
    with (OUT/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(header);w.writerows(rows)
write('13f_holder_by_dow_stock.csv',['report_date','availability_filing_date','manager_cik','manager_name','accession_number','ticker','cusip','reported_issuer','share_class','value_usd_thousands','shares_or_principal_amount','amount_type'],raw)
write('13f_filing_coverage.csv',['manager_cik','manager_name','report_date','availability_filing_date','status','accession_or_error'],coverage)
byq=defaultdict(lambda:defaultdict(lambda:defaultdict(float)))
for r in raw:
    try:byq[r[0]][r[5]][r[2]]+=float(r[9] or 0)
    except ValueError:pass
filers=defaultdict(set);dates=defaultdict(list)
for c in coverage:
    if c[4].startswith('parsed_'):
        filers[c[2]].add(c[0]);dates[c[2]].append(c[3])
edges=[]
for report in REPORT_DATES:
    members=sorted(roster_for(report));managers=sorted(filers[report])
    vec={t:[byq[report][t].get(m,0.) for m in managers] for t in members}
    norm={t:math.sqrt(sum(x*x for x in v)) for t,v in vec.items()}
    avail=max(dates[report]) if dates[report] else ''
    for i,a in enumerate(members):
        for b in members[i+1:]:
            den=norm[a]*norm[b];cos=sum(x*y for x,y in zip(vec[a],vec[b]))/den if den else 0.
            edges.append([report,len(managers),avail,a,b,f'{cos:.12g}'])
write('13f_cosine_overlap_edges.csv',['report_date','parsed_manager_count','panel_availability_date','ticker_i','ticker_j','cosine_13f_portfolio_value_overlap'],edges)
print(f'wrote {len(raw)} positions, {len(coverage)} coverage rows, {len(edges)} edges',flush=True)
