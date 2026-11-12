"""Build a point-in-time SEC earnings-event clock for Dow members and fallback S&P 500 mega-caps."""
import csv,time
from collections import defaultdict
from datetime import datetime,date,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import requests

OUT=Path('A2/pivot_research/r4_L4/data'); START=date(2020,6,1); END=date(2026,10,31)
UA='FINS3666 earnings clock project contact research@example.edu'
s=requests.Session();s.headers.update({'User-Agent':UA,'Accept-Encoding':'gzip, deflate'}); last=[0.0]
def getj(url):
    wait=.20-(time.monotonic()-last[0])
    if wait>0:time.sleep(wait)
    r=s.get(url,timeout=90);r.raise_for_status();last[0]=time.monotonic();return r.json()
TOP50=['AAPL','NVDA','MSFT','GOOGL','AMZN','META','TSLA','AVGO','BRK-B','LLY','WMT','JPM','V','MU','AMD','XOM','JNJ','MA','ABBV','COST','CVX','KO','PLTR','PG','CSCO','ORCL','MRK','UNH','HD','BAC','GE','PM','INTC','MS','AMAT','NFLX','GS','TMO','PANW','RTX','CAT','TXN','WFC','LRCX','AMGN','LIN','IBM','CRWD','ANET','AXP']
# Half-open [start,end) constituent dates, reconstructed from S&P DJI change releases.
DOW=[
('MMM','0000066740',START,date(2026,11,1)),('AAPL','0000320193',START,date(2026,11,1)),('AXP','0000004962',START,date(2026,11,1)),('BA','0000012927',START,date(2026,11,1)),('CAT','0000018230',START,date(2026,11,1)),('CSCO','0000858877',START,date(2026,11,1)),('CVX','0000093410',START,date(2026,11,1)),('DIS','0001744489',START,date(2026,11,1)),('DOW','0001751788',START,date(2024,11,8)),('GS','0000886982',START,date(2026,11,1)),('HD','0000354950',START,date(2026,11,1)),('IBM','0000051143',START,date(2026,11,1)),('INTC','0000050863',START,date(2024,11,8)),('JNJ','0000200406',START,date(2026,11,1)),('JPM','0000019617',START,date(2026,11,1)),('KO','0000021344',START,date(2026,11,1)),('MCD','0000063908',START,date(2026,11,1)),('MRK','0000310158',START,date(2026,11,1)),('MSFT','0000789019',START,date(2026,11,1)),('NKE','0000320187',START,date(2026,11,1)),('PFE','0000078003',START,date(2020,8,31)),('PG','0000080424',START,date(2026,11,1)),('RTX','0000101829',START,date(2020,8,31)),('TRV','0000086312',START,date(2026,11,1)),('UNH','0000731766',START,date(2026,11,1)),('V','0001403161',START,date(2026,11,1)),('VZ','0000732712',START,date(2026,11,1)),('WBA','0001618921',START,date(2024,2,26)),('WMT','0000104169',START,date(2026,11,1)),('XOM','0000034088',START,date(2020,8,31)),('AMGN','0000318154',date(2020,8,31),date(2026,11,1)),('CRM','0001108524',date(2020,8,31),date(2026,11,1)),('HON','0000773840',date(2020,8,31),date(2026,11,1)),('AMZN','0001018724',date(2024,2,26),date(2026,11,1)),('NVDA','0001045810',date(2024,11,8),date(2026,11,1)),('SHW','0000089800',date(2024,11,8),date(2026,11,1))]
# SEC company_tickers_exchange gives the CIK map; WBA is a historical, now delisted symbol.
ct=getj('https://www.sec.gov/files/company_tickers_exchange.json'); keys=ct['fields']; byticker={str(r[keys.index('ticker')]).upper():dict(zip(keys,r)) for r in ct['data']}
bycik={str(r[keys.index('cik')]).zfill(10):dict(zip(keys,r)) for r in ct['data']}
companies={}
for rank,t in enumerate(TOP50,1):
    rec=byticker[t];cik=str(rec['cik']).zfill(10)
    c=companies.setdefault(cik,{'cik':cik,'ticker':t,'name':rec['name'],'sources':set(),'intervals':[],'top50_rank':rank})
    c['sources'].add('S&P500_top50_market_cap_2026-11-06')
    # ExxonMobil changed reporting CIK; carry the predecessor CIK for its time series.
    if t=='XOM':
        old=bycik.get('0000034088',{'name':'Exxon Mobil Corp.'});oldcik='0000034088'
        alias=companies.setdefault(oldcik,{'cik':oldcik,'ticker':'XOM','name':old['name'],'sources':set(),'intervals':[],'top50_rank':rank})
        alias['sources'].add('S&P500_top50_market_cap_2026-11-06')
for t,cik,lo,hi in DOW:
    rec=bycik.get(cik) or (dict(cik=int(cik),name={'WBA':'Walgreens Boots Alliance, Inc.','XOM':'Exxon Mobil Corp.'}[t],ticker=t,exchange='NYSE') if t in {'WBA','XOM'} else None)
    if rec is None:raise RuntimeError(f'CIK missing for {t}: {cik}')
    c=companies.setdefault(cik,{'cik':cik,'ticker':t,'name':rec['name'],'sources':set(),'intervals':[],'top50_rank':''})
    if 'S&P500_top50_market_cap_2026-11-06' not in c['sources']:c['ticker']=t
    c['sources'].add('Dow_PIT');c['intervals'].append((t,lo,hi))
print(f'Selected {len(companies)} unique issuers: {len(TOP50)} top-50 symbols and {len(DOW)} Dow ticker intervals',flush=True)
def records_for(cik):
    sub=getj(f'https://data.sec.gov/submissions/CIK{cik}.json'); blocks=[sub.get('filings',{}).get('recent',{})]
    for f in sub.get('filings',{}).get('files',[]):
        if f.get('filingTo','')>='2020-06-01' and f.get('filingFrom','')<='2026-10-31':blocks.append(getj('https://data.sec.gov/submissions/'+f['name']))
    seen=set()
    for b in blocks:
        cols=['accessionNumber','filingDate','reportDate','acceptanceDateTime','form','items','primaryDocument']; arr={k:b.get(k,[]) for k in cols}
        for i,acc in enumerate(arr['accessionNumber']):
            if not acc or acc in seen:continue
            seen.add(acc);yield {k:arr[k][i] if i<len(arr[k]) else '' for k in cols}
def accepted_et(raw):
    if not raw:return None
    try:return datetime.fromisoformat(raw.replace('Z','+00:00')).astimezone(ZoneInfo('America/New_York'))
    except ValueError:return None
def member_at(c,day):return any(lo<=day<hi for _,lo,hi in c['intervals'])
events=[]
for n,(cik,c) in enumerate(sorted(companies.items()),1):
    for r in records_for(cik):
        form=str(r['form']).strip().upper()
        if form not in {'8-K','8-K/A'} or '2.02' not in {x.strip() for x in str(r['items'] or '').split(',')}:continue
        dt=accepted_et(r['acceptanceDateTime'])
        if dt is None or not START<=dt.date()<=END:continue
        is_dow=member_at(c,dt.date())
        if 'S&P500_top50_market_cap_2026-11-06' not in c['sources'] and not is_dow:continue
        t=dt.timetz().replace(tzinfo=None)
        cls='BMO' if t<datetime.strptime('09:30','%H:%M').time() else ('AMC' if t>=datetime.strptime('16:00','%H:%M').time() else 'intraday')
        acc=r['accessionNumber'];doc=str(r['primaryDocument'] or '').strip();url=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-','')}/{doc or acc+'.txt'}"
        dowticker=next((tkr for tkr,lo,hi in c['intervals'] if lo<=dt.date()<hi),'')
        events.append({'ticker':dowticker or c['ticker'],'cik':cik,'company_name':c['name'],'acceptance_timestamp_et':dt.isoformat(timespec='seconds'),'acceptance_timestamp_utc':r['acceptanceDateTime'],'classification':cls,'form':form,'items':str(r['items'] or ''),'filing_date':r['filingDate'],'report_date':r['reportDate'],'accession_number':acc,'universe_source':';'.join(sorted(c['sources'])),'dow_member_on_acceptance_date':'true' if is_dow else 'false','source_url':url})
    print(f'{n}/{len(companies)} {c["ticker"]} ({cik}) events={len(events)}',flush=True)
events.sort(key=lambda r:(r['acceptance_timestamp_utc'],r['cik'],r['accession_number']))
columns=['ticker','cik','company_name','acceptance_timestamp_et','acceptance_timestamp_utc','classification','form','items','filing_date','report_date','accession_number','universe_source','dow_member_on_acceptance_date','source_url']
with (OUT/'earnings_clock.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(events)
by_count=defaultdict(lambda:defaultdict(lambda:defaultdict(int)))
for e in events:
    y=int(e['acceptance_timestamp_et'][:4]);q=by_count[e['cik']][y];q['total']+=1;q[e['classification']]+=1
coverage=[]
for cik,c in sorted(companies.items(),key=lambda x:(x[1]['ticker'],x[0])):
    top='S&P500_top50_market_cap_2026-11-06' in c['sources']
    for y in range(2020,2027):
        lo=max(START,date(y,1,1));hi=min(END,date(y,12,31))
        in_scope=top or any(a<=hi and b>lo for _,a,b in c['intervals'])
        if not in_scope:continue
        ylo=date(y,1,1);yhi=date(y,12,31)
        days=sum(max(0,(min(hi,b-timedelta(days=1))-max(lo,a)).days+1) for _,a,b in c['intervals'])
        q=by_count[cik][y]
        coverage.append({'ticker':c['ticker'],'cik':cik,'name':c['name'],'scope':'+'.join(sorted(c['sources'])),'year':y,'events':q['total'],'BMO':q['BMO'],'intraday':q['intraday'],'AMC':q['AMC'],'dow_member_days':days})
# Build a firm-by-year matrix in QA. '-' means out of Dow window and not in fallback top 50.
firm_rows=[]
for cik,c in sorted(companies.items(),key=lambda x:(x[1]['ticker'],x[0])):
    counts={str(r['year']):r['events'] for r in coverage if r['cik']==cik}
    if not counts:continue
    firm_rows.append('| '+c['ticker']+' | '+cik+' | '+('+'.join(sorted(c['sources'])))+' | '+' | '.join(str(counts.get(str(y),'-')) for y in range(2020,2027))+' |')
classcounts={k:sum(e['classification']==k for e in events) for k in ['BMO','intraday','AMC']}
report=f'''# SEC earnings clock QA

## Scope and source universe

Collected SEC Form 8-K and 8-K/A filings explicitly tagged with Item 2.02, from acceptance dates 2020-06-01 through 2026-10-31. The requested `r5_D7/LINKS.csv` did not exist in this workspace, so the fallback set is the first 50 S&P 500 companies ranked by market capitalization on 2026-11-06 (the latest published list available when built); ranking and component source: [S&P 500 companies by market value](https://www.sectoralpha.in/sp-500-stocks). SEC CIK and filing metadata came from [company_tickers_exchange.json](https://www.sec.gov/files/company_tickers_exchange.json) and [EDGAR submissions API](https://www.sec.gov/edgar/sec-api-documentation).

Dow membership is point-in-time: 30 components at the window start, with S&P DJI changes applied effective 2020-08-31, 2024-02-26, and 2024-11-08. The 2020 release replaced XOM/PFE/RTX with CRM/AMGN/HON ([S&P DJI](https://press.spglobal.com/2020-08-24-Salesforce-com-Amgen-and-Honeywell-International-Set-to-Join-Dow-Jones-Industrial-Average)); Amazon replaced WBA from 2024-02-26 ([S&P DJI PDF](https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20240220-1470711/1470711_djiadjtawbajblu-feb2024.pdf)); NVDA and SHW replaced INTC and DOW from 2024-11-08 ([S&P DJI](https://press.spglobal.com/2024-11-01-NVIDIA-and-Sherwin-Williams-Set-to-Join-Dow-Jones-Industrial-Average-Vistra-to-Join-Dow-Jones-Utility-Average?asPDF=1)). RTX is the active issuer/ticker during this window, including the predecessor Dow constituent's final months.

The combined universe has {len(companies)} unique CIKs ({len(TOP50)} fallback tickers plus the Dow identities, with overlap collapsed by CIK). For firms selected only as Dow members, filings are included only while that CIK is in the Dow; fallback top-50 firms are retained throughout the full requested window. `dow_member_on_acceptance_date` in the event CSV distinguishes those cases. The extraction reads filing-index metadata only; it does not download or inspect prices or returns.

## Classification and schema

`earnings_clock.csv` contains {len(events)} qualifying event filings: {classcounts['BMO']} BMO, {classcounts['intraday']} intraday, and {classcounts['AMC']} AMC. `acceptance_timestamp_utc` is SEC's timestamp; `acceptance_timestamp_et` is converted with Python `America/New_York` timezone rules, including daylight saving. Classification uses local acceptance time: before 09:30 = BMO; 09:30 to before 16:00 = intraday; 16:00 or later = AMC. This is a mechanical timestamp classification, not a claim about the scheduled earnings-release time.

Columns are `ticker`, `cik`, `company_name`, `acceptance_timestamp_et`, `acceptance_timestamp_utc`, `classification`, `form`, `items`, `filing_date`, `report_date`, `accession_number`, `universe_source`, `dow_member_on_acceptance_date`, and `source_url`. The source URL resolves to the primary EDGAR filing document (or the filing text when the index lacks a primary-document name). Items are taken from the SEC submissions `items` field, split on commas and matched exactly to `2.02`; no document text keyword matching was used. The source for every event is linked in its CSV row.

## Coverage by firm and year

Counts are qualifying Item 2.02 filings. Years 2020 and 2026 are partial (2020 starts June 1; 2026 ends October 31). A dash means the firm was outside the point-in-time Dow membership and outside the fallback top-50 universe that year; zero means in-scope but no qualifying filing was indexed.

| Ticker | CIK | Inclusion source | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(firm_rows)}

## Rebuild

Run from the workspace root: `python A2/pivot_research/r4_L4/data/build_earnings_clock.py`. Requests use a generic project User-Agent and a 0.20-second minimum interval (at most five SEC requests per second). The script reads only SEC ticker/submission metadata and writes the event CSV and this report; no price files are accessed.
'''
(OUT/'EARNINGS_CLOCK_QA.md').write_text(report,encoding='utf-8')
print('DONE events',len(events),'coverage rows',len(coverage),'classes',classcounts,flush=True)
