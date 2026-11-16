"""Build point-in-time S&P 500 SEC Item 2.02 filing clock; metadata only."""
import csv
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
import requests

ROOT=Path(__file__).resolve().parent
START=date(2020,6,1)
END_EXCLUSIVE=date(2026,11,1)  # through October 2026
UA='FINS3666 SEC metadata research project contact research@example.edu'
BASE='https://data.sec.gov'
s=requests.Session()
s.headers.update({'User-Agent':UA,'Accept-Encoding':'gzip, deflate','Host':'data.sec.gov'})
_last=[0.0]

def get_json(url):
    # 0.20 s minimum start-to-start spacing: five requests/second.
    wait=0.20-(time.monotonic()-_last[0])
    if wait>0: time.sleep(wait)
    r=s.get(url,timeout=90)
    _last[0]=time.monotonic()
    r.raise_for_status()
    return r.json()

def parse_date(v):
    return date.fromisoformat(str(v)[:10])

def accepted_et(raw):
    if not raw:return None
    try:return datetime.fromisoformat(str(raw).replace('Z','+00:00')).astimezone(ZoneInfo('America/New_York'))
    except (ValueError, TypeError):return None

def filing_records(cik):
    url=f'{BASE}/submissions/CIK{cik}.json'
    sub=get_json(url)
    filings=sub.get('filings',{})
    blocks=[filings.get('recent',{})]
    archive_names=[]
    for desc in filings.get('files',[]):
        lo=str(desc.get('filingFrom',''))
        hi=str(desc.get('filingTo',''))
        if hi>='2020-06-01' and lo<='2026-10-31':
            archive_names.append(desc['name'])
    for name in archive_names:
        blocks.append(get_json(f'{BASE}/submissions/{name}'))
    seen=set()
    cols=['accessionNumber','filingDate','reportDate','acceptanceDateTime','form','items','primaryDocument']
    for block in blocks:
        arrays={k:block.get(k,[]) for k in cols}
        for i,acc in enumerate(arrays['accessionNumber']):
            if not acc or acc in seen:continue
            seen.add(acc)
            yield {k:(arrays[k][i] if i<len(arrays[k]) else '') for k in cols}

def active_on(intervals, day):
    return any(lo<=day<hi for lo,hi in intervals)

def clipped_days(intervals, year):
    year_lo=date(year,1,1); year_hi=date(year+1,1,1)
    lo=max(START,year_lo); hi=min(END_EXCLUSIVE,year_hi)
    total=0
    for a,b in intervals:
        aa=max(a,lo); bb=min(b,hi)
        if aa<bb: total+=(bb-aa).days
    return total

roster=pd.read_csv(ROOT/'sp500_pit_roster.csv',dtype={'ticker':str})
sic=pd.read_csv(ROOT/'sp500_sic_panel.csv',dtype={'ticker':str,'cik':str})
sic['cik']=sic['cik'].str.replace(r'\.0$','',regex=True).str.zfill(10)
# Each roster ticker has one CIK in the historical SEC SIC panel. Company name and
# membership intervals remain tied to the point-in-time S&P roster.
cik_map=sic.groupby('ticker')['cik'].agg(lambda x:sorted(set(x))[-1]).to_dict()
missing=sorted(set(roster['ticker'])-set(cik_map))
if missing: raise RuntimeError(f'No SIC-panel CIK mapping for roster tickers: {missing}')
issuers={}
for ticker,part in roster.groupby('ticker',sort=True):
    cik=cik_map[ticker]
    intervals=[]
    names=[]
    for row in part.itertuples(index=False):
        lo=max(START,parse_date(row.effective_from))
        hi=min(END_EXCLUSIVE,parse_date(row.effective_to_exclusive))
        if lo<hi: intervals.append((lo,hi))
        names.append(str(row.company))
    if intervals:
        issuers.setdefault(cik,{'ticker':ticker,'name':names[0],'tickers':set(),'names':set(),'intervals':[],'ticker_intervals':defaultdict(list)})
        issuers[cik]['tickers'].add(ticker);issuers[cik]['names'].update(names);issuers[cik]['intervals'].extend(intervals);issuers[cik]['ticker_intervals'][ticker].extend(intervals)
# Merge duplicate/adjacent membership intervals per issuer.
for c in issuers.values():
    merged=[]
    for lo,hi in sorted(c['intervals']):
        if merged and lo<=merged[-1][1]: merged[-1]=(merged[-1][0],max(hi,merged[-1][1]))
        else: merged.append((lo,hi))
    c['intervals']=merged
    c['ticker']=sorted(c['tickers'])[0]
    c['name']=sorted(c['names'])[0]

print(f'Point-in-time roster: {len(roster)} membership intervals, {roster.ticker.nunique()} ticker identities, {len(issuers)} CIKs.',flush=True)
events=[]; fetch_status=[]
for n,(cik,company) in enumerate(sorted(issuers.items()),1):
    try:
        all_records=list(filing_records(cik))
        examined=0
        for rec in all_records:
            form=str(rec.get('form','')).strip().upper()
            if form not in {'8-K','8-K/A'}: continue
            items={x.strip() for x in str(rec.get('items') or '').split(',')}
            if '2.02' not in items: continue
            accepted=accepted_et(rec.get('acceptanceDateTime'))
            if accepted is None or not START<=accepted.date()<END_EXCLUSIVE: continue
            if not active_on(company['intervals'],accepted.date()): continue
            examined+=1
            t=accepted.timetz().replace(tzinfo=None)
            cls=('BMO' if t<datetime.strptime('09:30','%H:%M').time() else
                 'AMC' if t>=datetime.strptime('16:00','%H:%M').time() else 'intraday')
            acc=str(rec.get('accessionNumber',''))
            doc=str(rec.get('primaryDocument') or '').strip()
            archive_cik=str(int(cik))
            source=f"https://www.sec.gov/Archives/edgar/data/{archive_cik}/{acc.replace('-','')}/{doc or acc+'.txt'}"
            ticker=next((tkr for tkr in sorted(company['tickers']) if active_on(company['ticker_intervals'][tkr],accepted.date())),company['ticker'])
            events.append({'ticker':ticker,'cik':cik,'company_name':company['name'],'acceptance_timestamp_et':accepted.isoformat(timespec='seconds'),'acceptance_timestamp_utc':str(rec.get('acceptanceDateTime','')),'classification':cls,'form':form,'items':str(rec.get('items') or ''),'filing_date':str(rec.get('filingDate') or ''),'report_date':str(rec.get('reportDate') or ''),'accession_number':acc,'membership_on_acceptance_date':'true','source_url':source})
        fetch_status.append({'ticker':company['ticker'],'cik':cik,'status':'ok','filing_records':len(all_records),'qualifying_events':examined,'error':''})
    except Exception as e:
        fetch_status.append({'ticker':company['ticker'],'cik':cik,'status':'error','filing_records':0,'qualifying_events':0,'error':repr(e)})
    if n%25==0 or n==len(issuers): print(f'{n}/{len(issuers)} issuers; events={len(events)}',flush=True)

events.sort(key=lambda r:(r['acceptance_timestamp_utc'],r['cik'],r['accession_number']))
columns=['ticker','cik','company_name','acceptance_timestamp_et','acceptance_timestamp_utc','classification','form','items','filing_date','report_date','accession_number','membership_on_acceptance_date','source_url']
with (ROOT/'earnings_clock_sp500.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=columns); w.writeheader(); w.writerows(events)

counts=defaultdict(lambda:defaultdict(lambda:defaultdict(int)))
for e in events:
    y=int(e['acceptance_timestamp_et'][:4]); q=counts[e['cik']][y]
    q['events']+=1; q[e['classification']]+=1
status_by_cik={r['cik']:r for r in fetch_status}
coverage=[]
for cik,part in roster.assign(cik=roster.ticker.map(cik_map)).groupby('cik',sort=True):
    intervals=[]; active_tickers={}
    for row in part.itertuples(index=False):
        lo=max(START,parse_date(row.effective_from)); hi=min(END_EXCLUSIVE,parse_date(row.effective_to_exclusive))
        if lo<hi:
            intervals.append((lo,hi))
            active_tickers.setdefault(row.ticker,[]).append((lo,hi))
    status=status_by_cik.get(cik,{'status':'missing','filing_records':0,'error':'No filing query record'})
    for year in range(2020,2027):
        days=clipped_days(intervals,year)
        if not days:continue
        q=counts[cik][year]
        tickers=';'.join(t for t,spans in sorted(active_tickers.items()) if clipped_days(spans,year)>0)
        coverage.append({'cik':cik,'issuer_tickers_active_this_year':tickers,'company_name':str(part.iloc[0].company),'year':year,'membership_calendar_days':days,'item_2_02_events':q['events'],'BMO':q['BMO'],'intraday':q['intraday'],'AMC':q['AMC'],'submissions_status':status['status'],'filing_records_indexed':status['filing_records']})
pd.DataFrame(coverage).to_csv(ROOT/'earnings_clock_sp500_coverage.csv',index=False)
pd.DataFrame(fetch_status).to_csv(ROOT/'earnings_clock_sp500_fetch_status.csv',index=False)

classcounts={k:sum(e['classification']==k for e in events) for k in ('BMO','intraday','AMC')}
status_counts=pd.Series([x['status'] for x in fetch_status]).value_counts().to_dict()
byyear=defaultdict(lambda:defaultdict(int))
for e in events: byyear[int(e['acceptance_timestamp_et'][:4])][e['classification']]+=1
rows=['| Year | Item 2.02 filings | BMO | Intraday | AMC |']
rows.append('|---:|---:|---:|---:|---:|')
for y in range(2020,2027):
    z=byyear[y]; rows.append(f"| {y} | {sum(z.values())} | {z['BMO']} | {z['intraday']} | {z['AMC']} |")
qa=f'''# S&P 500 earnings clock QA

Prepared 2026-11-11. The event file contains SEC filing metadata only; no prices, returns, or price-derived fields were accessed.

## Scope and method

`earnings_clock_sp500.csv` covers point-in-time S&P 500 membership from 2020-06-01 through 2026-10-30. It includes Form 8-K and 8-K/A filings whose SEC submissions metadata lists Item 2.02 and whose EDGAR acceptance date falls inside the issuer's S&P membership interval. The roster is `r6_data/sp500_pit_roster.csv` (623 membership intervals, 622 unique ticker identities); CIKs come from the dated SEC SIC panel, `r6_data/sp500_sic_panel.csv`, which has one CIK per roster ticker. A filing from a company before entry or after removal is excluded.

Acceptance times are SEC submission timestamps converted to `America/New_York` with daylight-saving rules. Classification is mechanical: before 09:30 ET = BMO; 09:30 to before 16:00 ET = intraday; 16:00 ET or later = AMC. The classification describes filing acceptance time, not the actual earnings release schedule. SEC's `items` index field is split into comma-separated codes and matched to `2.02`; filing bodies were not downloaded or searched. The CSV links each event to the SEC primary filing document (falling back to the filing text URL if the primary document is absent).

## Coverage

There are {len(events)} qualifying filings across {roster.ticker.nunique()} point-in-time ticker identities and {len(issuers)} CIKs. Classifications: {classcounts['BMO']} BMO, {classcounts['intraday']} intraday, and {classcounts['AMC']} AMC. EDGAR submission queries succeeded for {status_counts.get('ok',0)} CIKs and failed for {status_counts.get('error',0)}; any query failure is listed in `earnings_clock_sp500_fetch_status.csv` and reduces coverage for those issuers. `earnings_clock_sp500_coverage.csv` gives per-issuer, per-year counts and membership calendar days; 2020 starts June 1, and membership extends through October 30 in 2026.

| Year | Item 2.02 filings | BMO | Intraday | AMC |
|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

A zero event count means the SEC submissions index query succeeded and no qualifying Item 2.02 filing was observed during that issuer's membership days. This counts filing-index metadata, not all issuer earnings announcements regardless of form/item coding.

## Sources and fair access

The roster and SEC SIC-derived CIK mapping are project inputs. Filing timestamps and Item 2.02 codes are from the [SEC EDGAR submissions API](https://www.sec.gov/edgar/sec-api-documentation); issuer CIK references resolve under `https://data.sec.gov/submissions/CIK{{cik}}.json`. The builder identifies as `FINS3666 SEC metadata research project contact research@example.edu` and spaces SEC requests at 0.20 seconds (five requests per second, below the 10 requests/second limit).

## Rebuild

Run from `A2/pivot_research`:

```powershell
python r6_data/build_earnings_clock_sp500.py
```

This writes the event CSV, per-ticker/year coverage, issuer fetch status, and this report. No price data is opened.
'''
(ROOT/'earnings_clock_sp500_QA.md').write_text(qa,encoding='utf-8')
print(f'DONE events={len(events)} issuers={len(issuers)} status={status_counts} classes={classcounts}',flush=True)

