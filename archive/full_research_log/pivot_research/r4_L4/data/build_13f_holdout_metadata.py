"""Check the top-Q2-2026 13F manager set's historical filing-index coverage only.

No filing documents or information tables are fetched. Output covers 2010Q1-2020Q3.
"""
import calendar,csv,time
from pathlib import Path
import requests

OUT=Path('A2/pivot_research/r4_L4/data')
UA='FINS3666 network data project contact research@example.edu'
S=requests.Session();S.headers.update({'User-Agent':UA,'Accept-Encoding':'gzip, deflate'})
def req(url):
    for n in range(4):
        try:
            r=S.get(url,timeout=60)
            if r.status_code==200:
                time.sleep(.16);return r
            if r.status_code not in (403,429,500,502,503): r.raise_for_status()
        except Exception:
            if n==3: raise
        time.sleep(1.5*(n+1))
    raise RuntimeError(url)
def qdates():
    for y in range(2010,2021):
        for q in range(1,5):
            m=q*3; d=f'{y}-{m:02d}-{calendar.monthrange(y,m)[1]:02d}'
            if '2010-03-31'<=d<='2020-09-30': yield d
def rows_from(block):
    return [
        (form, report, filed, acc)
        for form,report,filed,acc in zip(block.get('form',[]),block.get('reportDate',[]),block.get('filingDate',[]),block.get('accessionNumber',[]))
        if form=='13F-HR' and report and '2010-01-01'<=report<='2020-09-30'
    ]
ranked=list(csv.DictReader((OUT/'13f_manager_rank_q2_2026.csv').open(encoding='utf-8-sig',newline='')))
periods=list(qdates()); out=[]
for m in ranked:
    cik=m['manager_cik']; filings=[]
    try:
        data=req(f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json').json()
        filings.extend(rows_from(data.get('filings',{}).get('recent',{})))
        for part in data.get('filings',{}).get('files',[]):
            if part.get('filingTo','')<'2010-01-01' or part.get('filingFrom','')>'2020-09-30': continue
            filings.extend(rows_from(req('https://data.sec.gov/submissions/'+part['name']).json()))
        status='checked_EDGAR_submission_indexes_only'
    except Exception as e:
        status='metadata_fetch_failed_'+type(e).__name__
    selected={}
    for form,report,filed,acc in sorted(filings,key=lambda x:x[2]): selected.setdefault(report,(filed,acc))
    for p in periods:
        filing=selected.get(p)
        out.append([m['rank'],cik,m['manager_name'],p,filing[0] if filing else '',filing[1] if filing else '',bool(filing),status])
with (OUT/'13f_top50_holdout_filing_metadata.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['q2_2026_rank','manager_cik','manager_name','report_period','earliest_filing_date','accession_number','edgar_filing_found','check_status']);w.writerows(out)
summary=[]
for m in ranked:
    rows=[r for r in out if r[0]==m['rank']]
    found=[r for r in rows if r[6]]
    summary.append([m['rank'],m['manager_cik'],m['manager_name'],len(found),len(periods),min((r[3] for r in found),default=''),max((r[3] for r in found),default='')])
with (OUT/'13f_top50_holdout_manager_summary.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['q2_2026_rank','manager_cik','manager_name','quarterly_reports_found','quarters_checked','first_report_period','last_report_period']);w.writerows(summary)
print(f'wrote {len(out)} manager-quarter metadata rows and {len(summary)} manager summaries; no filing documents retrieved')
