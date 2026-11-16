from pathlib import Path
import pandas as pd

base = set('MMM AXP AMGN AAPL BA CAT CVX CSCO KO DIS DOW GS HD HON IBM INTC JNJ JPM MCD MRK MSFT NKE PG CRM TRV UNH VZ V WBA WMT'.split())
changes = [
    ('2020-08-31', 'AMGN', 'PFE'), ('2020-08-31', 'CRM', 'XOM'), ('2020-08-31', 'HON', 'RTX'),
    ('2024-02-26', 'AMZN', 'WBA'),
    ('2024-11-08', 'NVDA', 'INTC'), ('2024-11-08', 'SHW', 'DOW'),
    ('2026-06-29', 'GOOGL', 'VZ'),
]
# Reverse the August 2020 changes to recover the June-start constituents.
active=set(base)
for dt, added, removed in changes:
    if dt == '2020-08-31':
        active.remove(added); active.add(removed)
rows=[]
start=pd.Timestamp('2020-06-01')
for dt in sorted(set(x[0] for x in changes)):
    end=pd.Timestamp(dt)
    rows.extend((t,start.date().isoformat(),end.date().isoformat()) for t in sorted(active))
    for when, added, removed in changes:
        if when == dt:
            active.discard(removed); active.add(added)
    start=end
rows.extend((t,start.date().isoformat(),'2026-10-31') for t in sorted(active))
out=Path(__file__).resolve().parents[1]/'r6_D1'/'dow_pit_roster.csv'
df=pd.DataFrame(rows,columns=['ticker','effective_from','effective_to_exclusive'])
# Merge uninterrupted memberships and keep positive-length intervals only.
df['effective_from']=pd.to_datetime(df.effective_from)
df['effective_to_exclusive']=pd.to_datetime(df.effective_to_exclusive)
merged=[]
for t,g in df.groupby('ticker'):
    intervals=[]
    for r in g.sort_values('effective_from').itertuples():
        if r.effective_to_exclusive <= r.effective_from: continue
        if intervals and intervals[-1][1] == r.effective_from: intervals[-1]=(intervals[-1][0],r.effective_to_exclusive)
        else: intervals.append((r.effective_from,r.effective_to_exclusive))
    merged.extend((t,a.date().isoformat(),b.date().isoformat()) for a,b in intervals)
pd.DataFrame(merged,columns=['ticker','effective_from','effective_to_exclusive']).sort_values(['ticker','effective_from']).to_csv(out,index=False)
print(f'wrote {len(merged)} non-overlapping ticker intervals')
