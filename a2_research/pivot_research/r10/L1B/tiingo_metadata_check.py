import datetime as dt
import time
import urllib.parse
import requests
import pandas as pd
from dotenv import dotenv_values

START = dt.date(2010, 1, 4)
END = dt.date(2015, 12, 31)
ENV_PATH = r'C:/Users/musta/Desktop/UNSW/SSI/FINS3666/A2/.env'

def normcols(cols):
    return [' '.join(str(x) for x in c if str(x) != 'nan').strip().lower() if isinstance(c, tuple) else str(c).strip().lower() for c in cols]

hurl = 'https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500'
cururl = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
headers = {'User-Agent': 'Mozilla/5.0 (compatible; R10L1BTiingoMetadata/1.0)'}
hist_tables = pd.read_html(hurl, storage_options=headers)
hist = next(t for t in hist_tables if normcols(t.columns)[:5] == ['effective date effective date', 'added ticker', 'added security', 'removed ticker', 'removed security'])
changes = []
for _, row in hist.iterrows():
    try:
        d = pd.to_datetime(row.iloc[0]).date()
    except Exception:
        continue
    changes.append((d, str(row.iloc[1]).strip(), str(row.iloc[2]).strip(), str(row.iloc[3]).strip(), str(row.iloc[4]).strip()))
current_tables = pd.read_html(cururl, storage_options=headers)
current = next(t for t in current_tables if 'Symbol' in t.columns and 'Security' in t.columns)
active = {str(r['Symbol']).strip() for _, r in current.iterrows() if str(r['Symbol']).strip()}
current_symbols = set(active)
for d, added, added_name, removed, removed_name in sorted(changes, reverse=True):
    if d > START:
        active.discard(added)
        active.add(removed)
identities = set(active)
for d, added, added_name, removed, removed_name in changes:
    if START <= d <= END and d.weekday() < 5:
        active.discard(removed)
        active.add(added)
        identities.update((added, removed))
if len(identities) != 619:
    raise RuntimeError(f'Roster identity count differs from pre-registered L1 roster: {len(identities)}')
# Removed/delisted hard cases first; tie-break by original ticker for reproducibility.
removed = sorted(identities - current_symbols)
retained = sorted(identities & current_symbols)
priority = removed + retained
selected = priority[:50]
values = dotenv_values(ENV_PATH)
token = values.get('KEY')
if not token:
    raise RuntimeError('Configured dotenv key KEY is unavailable')

session = requests.Session()
results = []
start_clock = time.monotonic()
for i, ticker in enumerate(selected):
    if i:
        delay = 72.5 - (time.monotonic() - last_call_start)
        if delay > 0:
            time.sleep(delay)
    tiingo = ticker.replace('.', '-')
    url = 'https://api.tiingo.com/tiingo/daily/' + urllib.parse.quote(tiingo, safe='-')
    last_call_start = time.monotonic()
    try:
        resp = session.get(url, params={'token': token}, timeout=25)
        item = {'source_ticker': ticker, 'request_ticker': tiingo, 'status': resp.status_code}
        if resp.status_code == 200:
            obj = resp.json()
            item.update({'name': obj.get('name'), 'returned_ticker': obj.get('ticker'), 'startDate': obj.get('startDate'), 'endDate': obj.get('endDate')})
        results.append(item)
    except Exception as exc:
        results.append({'source_ticker': ticker, 'request_ticker': tiingo, 'status': 'transport_error', 'error_type': type(exc).__name__})

# Emit metadata-only aggregates; no response bodies or secrets are printed/saved.
covered = []
missing = []
ambiguous = []
status_counts = {}
for x in results:
    status_counts[str(x['status'])] = status_counts.get(str(x['status']), 0) + 1
    if x['status'] != 200:
        continue
    sd = x.get('startDate')
    ed = x.get('endDate')
    if not sd or not ed:
        missing.append(x['source_ticker'])
    elif sd <= START.isoformat() and ed >= END.isoformat():
        covered.append(x['source_ticker'])
    else:
        missing.append(x['source_ticker'])
    if x.get('returned_ticker') and x['returned_ticker'].upper() != x['request_ticker'].upper():
        ambiguous.append(x['source_ticker'])
print('ROSTER_COUNT', len(identities))
print('REMOVED_IDENTITIES', len(removed))
print('RETAINED_IDENTITIES', len(retained))
print('QUERIED', len(results))
print('STATUS_COUNTS', status_counts)
print('COVERED_FULL_TARGET_INTERVAL', len(covered))
print('UNCOVERED_OR_NO_METADATA', len(missing))
print('UNCOVERED_TICKERS', ','.join(missing))
print('AMBIGUOUS_TICKERS', ','.join(ambiguous))
print('REMOVED_QUERIED', sum(x in set(removed) for x in selected))
print('ELAPSED_SECONDS', int(time.monotonic() - start_clock))
