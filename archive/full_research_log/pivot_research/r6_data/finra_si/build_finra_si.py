"""Download FINRA consolidated equity short-interest settlement files.
Development files are parsed only for PIT S&P 500/Dow membership fields.
Holdout files stay raw; the manifest scanner reads row count and symbol only.
"""
import csv, time, calendar
from datetime import date, timedelta
from pathlib import Path
from collections import defaultdict
import pandas as pd
import requests

ROOT=Path(__file__).resolve().parent
DEV_DIR=ROOT/'raw'
PROJECT=ROOT.parent
WORKSPACE=PROJECT.parent
HOLD_DIR=WORKSPACE/'sealed_holdout_dow'/'finra_si'/'raw'
HOLD_DIR.mkdir(parents=True,exist_ok=True); DEV_DIR.mkdir(parents=True,exist_ok=True)
START=date(2020,6,1); END=date(2026,10,31)
HOLD_START=date(2009,11,1); HOLD_END=date(2020,10,31)
FIRST_ALL_MARKET_FILE=date(2017,12,29)
BASE='https://cdn.finra.org/equity/otcmarket/biweekly/shrt{:%Y%m%d}.csv'
UA='FINS3666 FINRA short-interest research project contact research@example.edu'
s=requests.Session(); s.headers.update({'User-Agent':UA,'Accept':'text/csv,*/*'})
_last=[0.0]
def pace():
    wait=.25-(time.monotonic()-_last[0])
    if wait>0: time.sleep(wait)
def request_file(d,dest):
    """Try settlement date, then earlier candidate dates for weekends/holidays."""
    candidates=[d-timedelta(days=i) for i in range(0,6)]
    for cand in candidates:
        if cand.weekday()>=5: continue
        url=BASE.format(cand); source_dest=dest.parent/f'shrt{cand:%Y%m%d}.csv'
        if source_dest.exists(): return cand,url,source_dest
        pace()
        try:
            r=s.get(url,timeout=90,stream=True); _last[0]=time.monotonic()
            if r.status_code==200:
                with source_dest.open('wb') as f:
                    for chunk in r.iter_content(1024*1024):
                        if chunk:f.write(chunk)
                r.close(); return cand,url,source_dest
            code=r.status_code; r.close()
        except Exception as e:
            code=type(e).__name__
        if cand==d and code not in (403,404, 'HTTPError'):
            print(f'HTTP/request {code} for {cand}',flush=True)
    return None,None,None

def base_dates(lo,hi):
    cur=date(lo.year,lo.month,1)
    while cur<=hi:
        y,m=cur.year,cur.month
        mid=date(y,m,15)
        month_end=date(y,m,calendar.monthrange(y,m)[1])
        for d in (mid,month_end):
            if lo<=d<=hi: yield d
        if m==12:cur=date(y+1,1,1)
        else:cur=date(y,m+1,1)

def norm_symbol(x):
    return ''.join(c for c in str(x).upper() if c.isalnum())

def add_interval(dct,ticker,lo,hi,flag):
    lo=max(lo,START); hi=min(hi,date(2026,10,31))
    if lo<hi: dct.setdefault(ticker,[]).append((lo,hi,flag))

# Point-in-time S&P roster from the existing Round 6 data build.
sp=pd.read_csv(PROJECT/'sp500_pit_roster.csv',dtype={'ticker':str})
sp_int=defaultdict(list)
for x in sp.itertuples(index=False):
    lo=max(START,date.fromisoformat(str(x.effective_from)[:10])); hi=min(date(2026,11,1),date.fromisoformat(str(x.effective_to_exclusive)[:10]))
    if lo<hi:sp_int[x.ticker].append((lo,hi,True))
# Dow PIT SIC membership starts on 2020-11-27; add the pre-2020-11-27 roster and its Aug-2020 rebalance.
dow_int=defaultdict(list)
dow_start=['MMM','AAPL','AXP','BA','CAT','CSCO','CVX','DIS','DOW','GS','HD','IBM','INTC','JNJ','JPM','KO','MCD','MRK','MSFT','NKE','PFE','PG','TRV','UNH','V','VZ','WBA','WMT','XOM','RTX']
# Aug 2020 change effective before the open on Aug 31.
changes=[(date(2020,8,31),['CRM','AMGN','HON'],['XOM','PFE','RTX'])]
for t in dow_start:
    end=date(2026,10,31)
    for dt,adds,dels in changes:
        if t in dels:end=dt
    add_interval(dow_int,t,START,end,True)
for dt,adds,dels in changes:
    for t in adds:add_interval(dow_int,t,dt,date(2026,10,31),True)
dow=pd.read_csv(PROJECT.parent/'r6_C1'/'dow_sic_membership.csv',dtype={'ticker':str})
for x in dow.itertuples(index=False):
    lo=max(date(2020,11,27),date.fromisoformat(str(x.effective_from)[:10])); hi=min(date(2026,10,31),date.fromisoformat(str(x.effective_to_exclusive)[:10]))
    if lo<hi:add_interval(dow_int,x.ticker,lo,hi,True)

# Historical Dow roster for the sealed availability manifest. This is kept
# separate from the development roster and exists only for ticker-presence
# checks; no price or FINRA quantity fields are accessed for these dates.
hold_dow_int=defaultdict(list)
hold_initial=['MMM','AA','AXP','T','BAC','BA','CAT','CSCO','CVX','KO','DIS','DD','XOM','GE','HPQ','HD','IBM','INTC','JNJ','JPM','KFT','MCD','MRK','MSFT','PFE','PG','TRV','UTX','VZ','WMT']
hold_changes=[
    (date(2012,9,24),['UNH'],['KFT']),
    (date(2013,9,23),['GS','V','NKE'],['BAC','AA','HPQ']),
    (date(2015,3,19),['AAPL'],['T']),
    (date(2017,9,1),['DWDP'],['DD']),
    (date(2018,6,26),['WBA'],['GE']),
    (date(2019,4,2),['DOW'],['DWDP']),
    (date(2020,4,3),['RTX'],['UTX']),
    (date(2020,8,31),['CRM','AMGN','HON'],['XOM','PFE','RTX']),
]
hold_end=date(2020,11,27)
for t in hold_initial:
    end=hold_end
    for dt,adds,dels in hold_changes:
        if t in dels:end=dt
    hold_dow_int[t].append((HOLD_START,end,True))
for dt,adds,dels in hold_changes:
    for t in adds:
        end=next((when for when,a,d in hold_changes if when>dt and t in d),hold_end)
        hold_dow_int[t].append((dt,end,True))

def members_on(intervals,day):
    return {norm_symbol(t) for t,spans in intervals.items() if any(lo<=day<hi for lo,hi,*_ in spans)}

# Fetch development raw settlement files and build the per-settlement PIT membership index.
dev_files=[]; dev_gaps=[]
for base_date in base_dates(START,END):
    name=f'shrt{base_date:%Y%m%d}.csv'; dest=DEV_DIR/name
    actual,url,source_path=request_file(base_date,dest)
    if actual is None:
        dev_gaps.append((base_date,name,'not_found'))
        print('MISSING development file',base_date,flush=True); continue
    dev_files.append((actual,source_path,url))
    print(f'dev file {actual} {source_path.stat().st_size} bytes',flush=True)

# Download only available historical full-market consolidated files. The public full-market
# endpoint starts at 2017-12-29; earlier dates are not represented as raw holdout files.
hold_files=[]
for base_date in base_dates(FIRST_ALL_MARKET_FILE,HOLD_END):
    dest=HOLD_DIR/f'shrt{base_date:%Y%m%d}.csv'
    actual,url,source_path=request_file(base_date,dest)
    if actual is None:
        continue
    hold_files.append((actual,source_path,url))
    print(f'holdout raw {actual} {source_path.stat().st_size} bytes',flush=True)

# Remove only old query-anchor copies from this build where the canonical
# source-date-named file is now present; preserve every file referenced above.
for raw_dir,files in [(DEV_DIR,dev_files),(HOLD_DIR,hold_files)]:
    keep={p.resolve() for _,p,_ in files}
    for old in raw_dir.glob('shrt*.csv'):
        if old.resolve() not in keep: old.unlink()

# Create the sealed manifest. Only file row counts and presence/absence by active Dow ticker are read.
hold_rows=[]
all_dow=sorted(hold_dow_int)
for d,path,url in hold_files:
    nrows=0; present=set()
    with path.open('r',encoding='utf-8-sig',errors='replace',newline='') as f:
        for line_no,line in enumerate(f):
            if line_no==0:continue # header only; no data value read
            if not line.strip():continue
            nrows+=1
            parts=line.rstrip('\r\n').split('|',2)
            if len(parts)>1:
                sym=parts[1].strip().strip('"')
            if norm_symbol(sym) in members_on(hold_dow_int,d):present.add(norm_symbol(sym))
    active={norm_symbol(t):t for t in all_dow if norm_symbol(t) in members_on(hold_dow_int,d)}
    for sym,ticker in sorted(active.items(),key=lambda x:x[1]):
        hold_rows.append({'settlement_date':d.isoformat(),'file_name':path.name,'row_count':nrows,'dow_ticker':ticker,'present':str(sym in present).lower()})
with (HOLD_DIR.parent/'MANIFEST.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['settlement_date','file_name','row_count','dow_ticker','present']);w.writeheader()
    for row in hold_rows:
        w.writerow(row)

# Parse development files, retaining only the requested SI/ADV/DTC fields for point-in-time members.
rows=[]; parse_errors=[]; schema_seen=set()
for d,path,url in dev_files:
    sp_active=members_on(sp_int,d); dow_active=members_on(dow_int,d)
    try:
        with path.open('r',encoding='utf-8-sig',errors='replace',newline='') as f:
            reader=csv.DictReader(f,delimiter='|')
            for raw in reader:
                raw={str(k).strip().strip('"'): (v.strip().strip('"') if isinstance(v,str) else v) for k,v in raw.items() if k is not None}
                schema_seen.update(raw.keys())
                symbol=raw.get('symbolCode','')
                n=norm_symbol(symbol)
                in_sp=n in sp_active; in_dow=n in dow_active
                if not(in_sp or in_dow):continue
                rows.append({'ticker':symbol,'symbol':symbol,'settlement_date':raw.get('settlementDate',d.isoformat()),'short_interest':raw.get('currentShortPositionQuantity',''),'average_daily_volume':raw.get('averageDailyVolumeQuantity',''),'days_to_cover':raw.get('daysToCoverQuantity',''),'market_class_code':raw.get('marketClassCode',''),'issue_name':raw.get('issueName',''),'sp500_member':in_sp,'dow_member':in_dow,'source_file':path.name,'source_url':url})
    except Exception as e:parse_errors.append({'file':path.name,'error':repr(e)})
    print(f'parsed development {d}: cumulative matched rows {len(rows)}',flush=True)

df=pd.DataFrame(rows)
if not df.empty:
    for col in ['short_interest','average_daily_volume','days_to_cover']:
        df[col]=pd.to_numeric(df[col].replace({'':'','N/A':None,'NA':None}),errors='coerce')
    df['settlement_date']=pd.to_datetime(df['settlement_date'],errors='coerce').dt.date.astype('string')
    df.sort_values(['settlement_date','ticker','market_class_code'],inplace=True)
    df.to_parquet(ROOT/'finra_si_dev.parquet',index=False)
else:
    pd.DataFrame(columns=['ticker','symbol','settlement_date','short_interest','average_daily_volume','days_to_cover','market_class_code','issue_name','sp500_member','dow_member','source_file','source_url']).to_parquet(ROOT/'finra_si_dev.parquet',index=False)
pd.DataFrame(dev_gaps,columns=['settlement_date','file_name','status']).to_csv(ROOT/'dev_download_gaps.csv',index=False)
pd.DataFrame(parse_errors,columns=['file','error']).to_csv(ROOT/'dev_parse_errors.csv',index=False)

# Holdout manifest markdown contains no numeric short-interest fields.
manifest=pd.DataFrame(hold_rows)
file_summary=manifest.drop_duplicates(['settlement_date','file_name','row_count']).sort_values('settlement_date') if not manifest.empty else pd.DataFrame()
if len(file_summary):
    lines=['| Settlement date | Raw file | Row count | Active Dow tickers present |','|---|---|---:|---|']
    for rec in file_summary.itertuples(index=False):
        present='; '.join(manifest[(manifest.file_name==rec.file_name)&(manifest.present=='true')].dow_ticker.tolist())
        lines.append(f'| {rec.settlement_date} | {rec.file_name} | {rec.row_count} | {present} |')
    table='\n'.join(lines)
else:table='No holdout files were downloadable.'
missing_pre=f'{(date(2017,12,29)-HOLD_START).days} calendar days'
(HOLD_DIR.parent/'MANIFEST.md').write_text(f'''# Sealed FINRA short-interest availability manifest

The raw files under `raw/` are held sealed. This manifest contains only file row counts and whether each point-in-time Dow ticker appears; no short-interest, average-volume, days-to-cover, or other numeric field values were read or saved here. Settlement dates are taken from the date in the FINRA source-file URL; the settlement-date field inside holdout files was not inspected.

The requested holdout availability window is 2009-11 through 2020-10. The public consolidated full-market file path is available here from 2017-12-29. For earlier dates, the official FINRA archive page describes archive files from 2014 as **OTC equities only**, which do not provide the requested exchange-listed consolidated panel. Representative pre-cutoff consolidated-file requests returned unavailable. Thus no raw files are present for 2009-11 through 2017-11; this gap is explicit rather than filled with a different universe. The first accessible settlement was 2017-12-29, and the last requested settlement is 2020-10-30.

`MANIFEST.csv` is long format: one row per file and active Dow ticker, with only settlement date, raw filename, total data-row count, ticker, and boolean presence. Availability is the set of downloaded files below.

{table}

Sources: FINRA [Equity Short Interest Files](https://www.finra.org/finra-data/browse-catalog/equity-short-interest/files) links the current consolidated settlement files and notes that its static archives cover OTC equities only. The directly downloadable settlement files follow `https://cdn.finra.org/equity/otcmarket/biweekly/shrtYYYYMMDD.csv`. Ticker windows use the point-in-time Dow roster and citations in [`r4_L4/HOLDOUT_FEASIBILITY.md`](../../r4_L4/HOLDOUT_FEASIBILITY.md), including the UTX-to-RTX security lineage. The user-agent identifies the project and requests are rate-limited to at most four per second.
''',encoding='utf-8')

# Coverage-only QA. Dev summaries are data availability/row counts, not return statistics.
if not df.empty:
    devsum=df.groupby(df.settlement_date.str[:4]).agg(panel_rows=('ticker','size'),settlements=('settlement_date','nunique')).reset_index(names='year')
    dev_table='\n'.join([f'| {x.year} | {x.panel_rows} | {x.settlements} |' for x in devsum.itertuples(index=False)])
    st=pd.read_parquet(ROOT/'finra_si_dev.parquet')
    tic=st.groupby('ticker').agg(rows=('settlement_date','size'),first=('settlement_date','min'),last=('settlement_date','max')).reset_index()
    tic.to_csv(ROOT/'dev_ticker_coverage.csv',index=False)
else: dev_table='No development rows.'
(ROOT/'QA.md').write_text(f'''# FINRA equity short-interest data QA

Prepared 2026-11-11. This package is data-only; no prices, returns, signals, or backtests were accessed.

## Development data

`finra_si_dev.parquet` is a point-in-time panel of securities present in the S&P 500 roster or the Dow roster on each settlement date, covering 2020-06 through 2026-10. It retains FINRA's `symbolCode` as `symbol`/`ticker`, `settlementDate`, `currentShortPositionQuantity` as `short_interest`, `averageDailyVolumeQuantity` as `average_daily_volume`, and `daysToCoverQuantity` as `days_to_cover`; `market_class_code`, `issue_name`, universe-membership flags, source filename and URL are also retained. Values are reported by FINRA and are not recomputed or imputed. The full source settlement files are stored in `raw/`.

| Year | Matched panel rows | Settlement files |
|---:|---:|---:|
{dev_table}

`dev_ticker_coverage.csv` gives row coverage by matched ticker. `dev_download_gaps.csv` and `dev_parse_errors.csv` report any missing source file or parse issue. Empty/nonreported securities are absent from FINRA files and are not zero-filled.

## Sealed holdout

Raw files for the available portion of 2009-11 to 2020-10 are under `sealed_holdout_dow/finra_si/raw/`. The row-count and ticker-presence-only manifest is at `sealed_holdout_dow/finra_si/MANIFEST.md` and `.csv`; its fields are settlement date from the source URL, filename, row count, Dow ticker, and presence. Files from 2009-11 through 2017-11 are not available through the public consolidated full-market file path: FINRA's linked older static archives are OTC-only. Therefore holdout coverage is partial; do not interpret the unavailable years as zero short interest. The manifest scan reads only a line count and the symbol column, and does not access short-interest, average daily volume, or days-to-cover values.

## Availability and timing

FINRA settlement files are semi-monthly, typically the 15th (or prior settlement day) and the final settlement day of a month. A settlement is a snapshot, not a daily series. The files were retrieved from FINRA's public file path `https://cdn.finra.org/equity/otcmarket/biweekly/shrtYYYYMMDD.csv`. The source directory is labelled `otcmarket` despite the portal's **current** file feed describing consolidated exchange-listed and OTC equity short interest; FINRA's static archive files are explicitly OTC-only. Field quoting changed in the latest years, so parsing uses the pipe delimiter and CSV quoting rules.

## Rebuild

Run from `A2/pivot_research`:

```powershell
python r6_data/finra_si/build_finra_si.py
```

The script downloads development files and available holdout raw files, writes the parsed development panel, and creates the holdout manifest using presence-only scanning.
''',encoding='utf-8')
print('DEV files',len(dev_files),'gaps',len(dev_gaps),'panel rows',len(df),'holdout files',len(file_summary),'manifest rows',len(hold_rows),'holdout raw dir',HOLD_DIR,flush=True)


