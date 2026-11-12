import csv
from pathlib import Path
P=Path('A2/pivot_research/r4_L4/data')
cut='2023-01-03'
def fix(name, date_col, value_col):
    f=P/name
    with f.open(encoding='utf-8-sig',newline='') as src: rows=list(csv.DictReader(src)); fields=list(rows[0])
    changed=0
    target=[r[value_col] for r in rows if r.get(date_col,'')>=cut and r.get(value_col,'')]
    # The one-time conversion writes three decimal places; this guard prevents a second divide.
    if not target or any('.' in v for v in target):
        print(name, 'already normalized or no post-cut rows; skipped')
        return
    for r in rows:
        day=r.get(date_col,'')
        raw=r.get(value_col,'')
        if day>=cut and raw:
            r[value_col]=f'{int(float(raw))/1000:.3f}'
            changed+=1
    with f.open('w',encoding='utf-8',newline='') as dst:
        w=csv.DictWriter(dst,fieldnames=fields);w.writeheader();w.writerows(rows)
    print(name, 'rows converted', changed)
fix('13f_development_pit_positions.csv','availability_filing_date','value_usd_thousands')
fix('13f_holder_by_dow_stock.csv','availability_filing_date','value_usd_thousands')
fix('13f_top50_pit_roster.csv','filing_date','table_value_usd_thousands')
