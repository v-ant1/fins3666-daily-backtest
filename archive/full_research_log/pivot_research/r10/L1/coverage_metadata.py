import re, time, datetime, urllib.parse
import pandas as pd
import requests

START=datetime.date(2010,1,4); END=datetime.date(2015,12,31)
WIKI='https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500'
HEAD={'User-Agent':'Mozilla/5.0 (compatible; L1MetadataAudit/1.0)'}
tables=pd.read_html(WIKI,storage_options=HEAD)
def norm(c):
    return [' '.join(str(x) for x in z if str(x)!='nan').strip().lower() if isinstance(z,tuple) else str(z).strip().lower() for z in c]
hist=next(t for t in tables if norm(t.columns)[:5]==['effective date effective date','added ticker','added security','removed ticker','removed security'])
changes=[]
for _,row in hist.iterrows():
    try: d=pd.to_datetime(row.iloc[0]).date()
    except Exception: continue
    changes.append((d,str(row.iloc[1]).strip(),str(row.iloc[3]).strip()))
ct=pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies',storage_options=HEAD)
current=next(t for t in ct if 'Symbol' in t.columns and 'Security' in t.columns)
active=set(str(x).strip() for x in current['Symbol'] if str(x).strip())
# reverse newer changes to establish point-in-time members at 2010-01-03
for d,added,removed in sorted(changes,reverse=True):
    if d > START:
        active.discard(added); active.add(removed)
# forward replay in target period, counting weekday membership-days as session proxy
window_changes=[x for x in changes if START <= x[0] <= END]
bydate={}
for d,a,r in window_changes: bydate.setdefault(d,[]).append((a,r))
identities=set(active)
member_days=0
session_proxy=0
curdate=START
while curdate<=END:
    if curdate.weekday()<5:
        for a,r in bydate.get(curdate,[]):
            active.discard(r); active.add(a); identities.update((a,r))
        member_days+=len(active); session_proxy+=1
    curdate+=datetime.timedelta(days=1)
# counts of market-data timestamps only; never load/print OHLCV numeric arrays
p1=int(datetime.datetime(START.year,START.month,START.day,tzinfo=datetime.timezone.utc).timestamp())
p2=int(datetime.datetime(END.year,END.month,END.day,23,59,tzinfo=datetime.timezone.utc).timestamp())
s=requests.Session(); s.headers.update(HEAD)
with_bars=0; adjusted_array=0; queried=0; failed=0
for sym in sorted(identities):
    yahoo=sym.replace('.','-').replace('^','-')
    url=f'https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(yahoo,safe="-")}'
    try:
        r=s.get(url,params={'period1':p1,'period2':p2,'interval':'1d','events':'div,splits','includeAdjustedClose':'true'},timeout=15)
        queried+=1
        if not r.ok: failed+=1
        else:
            obj=r.json().get('chart',{}).get('result') or []
            if obj:
                item=obj[0]; stamps=item.get('timestamp') or []
                if stamps: with_bars+=1
                inds=item.get('indicators',{})
                ac=inds.get('adjclose') or []
                if ac and ac[0].get('adjclose') is not None: adjusted_array+=1
    except Exception: failed+=1
    time.sleep(.12)
print('UNIQUE_IDENTITIES',len(identities))
print('WEEKDAY_SESSION_PROXY',session_proxy)
print('MEMBER_DAYS_WEEKDAY_PROXY',member_days)
print('IDENTITIES_WITH_ANY_BAR',with_bars)
print('IDENTITY_BAR_COVERAGE_PCT',round(100*with_bars/len(identities),2))
print('IDENTITIES_WITH_ADJ_CLOSE_ARRAY',adjusted_array)
print('QUERIED',queried)
print('FAILED_OR_NON200',failed)
