"""Rank Q2 2026 filing managers by the SEC's reported table value total."""
import csv, io, zipfile
from pathlib import Path
import requests

OUT=Path('A2/pivot_research/r4_L4/data')
URL='https://www.sec.gov/files/datastandardsinnovation/data/form-13f-data-sets/01jun2026-31aug2026_form13f.zip'
S=requests.Session(); S.headers.update({'User-Agent':'FINS3666 network data project contact research@example.edu'})
z=zipfile.ZipFile(io.BytesIO(S.get(URL,timeout=180).content))
def tsv(name): return list(csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig')),delimiter='\t'))
sub={r['ACCESSION_NUMBER']:r for r in tsv('SUBMISSION.tsv') if r['SUBMISSIONTYPE']=='13F-HR' and r['PERIODOFREPORT']=='30-JUN-2026'}
summary={r['ACCESSION_NUMBER']:r for r in tsv('SUMMARYPAGE.tsv')}
cover={r['ACCESSION_NUMBER']:r for r in tsv('COVERPAGE.tsv')}
best={}
for acc,s in sub.items():
    c=cover.get(acc,{})
    if c.get('ISAMENDMENT','').upper()=='Y': continue
    try: value=int(summary[acc]['TABLEVALUETOTAL'])
    except (KeyError,ValueError): continue
    cik=s['CIK'].lstrip('0') or '0'
    row=(value,c.get('FILINGMANAGER_NAME',''),acc,s['FILING_DATE'])
    if cik not in best or value>best[cik][0]: best[cik]=row
rows=sorted(((cik,*v) for cik,v in best.items()),key=lambda x:x[1],reverse=True)[:50]
with (OUT/'13f_manager_rank_q2_2026.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['rank','manager_cik','manager_name','table_value_usd_thousands','accession_number','filing_date','report_date']);
    for n,(cik,val,name,acc,filed) in enumerate(rows,1): w.writerow([n,cik,name,val,acc,filed,'2026-06-30'])
print(f'wrote {len(rows)} ranked managers')
