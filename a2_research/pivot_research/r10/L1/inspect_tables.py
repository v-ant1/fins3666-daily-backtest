import sys, re, time, json, datetime, urllib.parse, urllib.request
import pandas as pd

URL='https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500'
headers={'User-Agent':'Mozilla/5.0 (compatible; L1MetadataAudit/1.0)'}
tables=pd.read_html(URL, storage_options=headers)

def cols(t):
    return [' '.join(str(x) for x in c if str(x)!='nan').strip().lower() if isinstance(c,tuple) else str(c).strip().lower() for c in t.columns]
# Find table with date, added ticker, removed ticker, and a second ticker/name column.
hist=None
for t in tables:
    c=cols(t)
    if any('date' in x for x in c) and sum(('added' in x or 'removed' in x or 'ticker' in x or 'symbol' in x) for x in c)>=2:
        hist=t; break
if hist is None: raise RuntimeError('Historical changes table not located')
print('HIST_COLS',cols(hist))
# Current list is needed as the reversal anchor.
current_tables=pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies',storage_options=headers)
cur=None
for t in current_tables:
    if any('symbol' in x for x in cols(t)) and any('security' in x for x in cols(t)):
        cur=t; break
if cur is None: raise RuntimeError('Current constituents table not located')
print('CURRENT_COLS',cols(cur))
