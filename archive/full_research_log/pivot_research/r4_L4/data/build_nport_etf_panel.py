"""Build Dow holding-weight rows from public ETF Form N-PORT-P filings.

Covered registrants: SPY, DIA, QQQ and the Select Sector SPDR Trust. The script
does not download filings for other iShares/style-fund registrants.
"""
import csv,re,time,xml.etree.ElementTree as ET
from pathlib import Path
import requests

OUT=Path('A2/pivot_research/r4_L4/data')
UA='FINS3666 network data project contact research@example.edu'
S=requests.Session();S.headers.update({'User-Agent':UA,'Accept-Encoding':'gzip, deflate'})
PAUSE=.2
REGISTRANTS={
 '884394':('SPY',None),
 '1041130':('DIA',None),
 '1067839':('QQQ',None),
 '1064641':(None,'SPDR_SECTOR'),
}
SECTOR_MAP=[
 ('Communication Services','XLC'),('Consumer Discretionary','XLY'),('Consumer Staples','XLP'),
 ('Energy','XLE'),('Financial','XLF'),('Health Care','XLV'),('Industrial','XLI'),
 ('Materials','XLB'),('Real Estate','XLRE'),('Technology','XLK'),('Utilities','XLU')]
DEV_START='2019-10-01';DEV_END='2026-10-30'

def get(url):
    last=''
    for attempt in range(4):
        try:
            r=S.get(url,timeout=90)
            if r.status_code==200:
                time.sleep(PAUSE);return r
            last=f'HTTP {r.status_code}'
            if r.status_code not in (403,429,500,502,503):break
        except Exception as e:last=type(e).__name__
        time.sleep(1.5*(attempt+1))
    raise RuntimeError(last)

def tag(t):return t.rsplit('}',1)[-1]
def text_of(node,key):
    return next(((n.text or '').strip() for n in node.iter() if tag(n.tag)==key),'')

def fund_for(cik,root):
    fixed=REGISTRANTS[cik][0]
    if fixed:return fixed
    name=text_of(root,'seriesName').lower()
    if 'premium income' in name:return ''
    for phrase,ticker in SECTOR_MAP:
        if phrase.lower() in name:return ticker
    return ''

# SEC CUSIP to Dow ticker crosswalk used by the 13F panel.
cusip_to_ticker={}
with (OUT/'build_13f_panel.py').open(encoding='utf-8') as f: source=f.read()
m=re.search(r'CUSIP_TO_TICKER\s*=\s*\{(.*?)\n\}',source,re.S)
for cusip,ticker in re.findall(r"'([A-Z0-9]{9})':'([A-Z]+)'",m.group(1)):cusip_to_ticker[cusip]=ticker

filings=[];coverage=[]
for cik in REGISTRANTS:
    data=get(f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json').json()
    blocks=[data.get('filings',{}).get('recent',{})]
    for part in data.get('filings',{}).get('files',[]):
        if part.get('filingTo','')>=DEV_START and part.get('filingFrom','')<=DEV_END:
            blocks.append(get('https://data.sec.gov/submissions/'+part['name']).json())
    seen=set()
    for block in blocks:
        for i,form in enumerate(block.get('form',[])):
            if form!='NPORT-P':continue
            rpt=block.get('reportDate',[''])[i] or ''; filed=block.get('filingDate',[''])[i] or ''
            if not (DEV_START<=rpt<=DEV_END and filed<=DEV_END):continue
            acc=block['accessionNumber'][i]
            if acc in seen:continue
            seen.add(acc)
            filings.append((cik,rpt,filed,acc))

weights=[]
for n,(cik,report,filed,acc) in enumerate(sorted(filings,key=lambda x:(x[1],x[0],x[3])),1):
    try:
        xml=get(f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace("-","")}/primary_doc.xml').content
        root=ET.fromstring(xml)
        etf=fund_for(cik,root)
        if not etf:
            coverage.append([cik,acc,report,filed,'series_not_mapped',text_of(root,'seriesName')]);continue
        matches=0
        for node in root.iter():
            if tag(node.tag)!='invstOrSec':continue
            cusip=re.sub(r'\s+','',text_of(node,'cusip')).upper(); ticker=cusip_to_ticker.get(cusip)
            if not ticker:continue
            pct=text_of(node,'pctVal')
            weights.append([etf,report,filed,ticker,cusip,text_of(node,'name'),pct,acc])
            matches+=1
        coverage.append([cik,acc,report,filed,f'parsed_{matches}_Dow_holdings',text_of(root,'seriesName')])
    except Exception as e:
        coverage.append([cik,acc,report,filed,'filing_parse_failed_'+type(e).__name__,''])
    if n%100==0:print(f'Parsed {n}/{len(filings)} N-PORT filings',flush=True)

with (OUT/'etf_dow_comembership.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['etf_ticker','report_date','availability_filing_date','dow_ticker','cusip','reported_issuer','weight_percent','accession_number']);w.writerows(weights)
with (OUT/'etf_nport_filing_coverage.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['registrant_cik','accession_number','report_date','availability_filing_date','status','series_name']);w.writerows(coverage)
all_etfs=['SPY','DIA','QQQ']+[t for _,t in SECTOR_MAP]+['IWB','IWD','IWF','IWM','IUSG','IUSV']
by_name={}
for phrase,ticker in SECTOR_MAP:by_name[phrase.lower()]=ticker
def status_ticker(cik,name):
    if cik in REGISTRANTS and REGISTRANTS[cik][0]:return REGISTRANTS[cik][0]
    lower=(name or '').lower()
    if 'premium income' in lower:return ''
    for phrase,ticker in SECTOR_MAP:
        if phrase.lower() in lower:return ticker
    return ''
filings_by={}
for row in coverage:
    ticker=status_ticker(row[0],row[5])
    if ticker:filings_by.setdefault(ticker,[]).append(row)
with (OUT/'etf_history_status.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['etf_ticker','nport_filings_parsed','dow_weight_rows','first_report_date','last_report_date','development_coverage','holdout_replicability','notes'])
    for ticker in all_etfs:
        filings=filings_by.get(ticker,[]); rowweights=[r for r in weights if r[0]==ticker]
        reports=[r[2] for r in filings]
        if filings:w.writerow([ticker,len(filings),len(rowweights),min(reports),max(reports),'SEC Form N-PORT-P panel available for observed filing periods','not full 2010-2020; SEC public data starts 2019-10','No matching Dow position rows' if not rowweights else 'Weights are SEC N-PORT pctVal fields; filing date is availability'])
        else:w.writerow([ticker,0,0,'','','not extracted','not replicated','iShares/style series not extracted in this build; N-PORT registrant CIK contains many fund series'])
target_filings=sum(1 for row in coverage if row[4]!='series_not_mapped')
print(f'wrote {len(weights)} Dow ETF holdings rows from {target_filings} target fund filings; checked {len(coverage)} candidate filings',flush=True)
