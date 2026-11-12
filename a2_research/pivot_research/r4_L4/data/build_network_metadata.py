"""Add PIT availability to the 13F edge panel and status manifests for unbuilt sources."""
import csv
from pathlib import Path
P=Path('A2/pivot_research/r4_L4/data')
with (P/'13f_filing_coverage.csv').open(encoding='utf-8-sig',newline='') as f:
    coverage=list(csv.DictReader(f))
dates={}
for r in coverage:
    if r['status'].startswith('parsed_') and r['availability_filing_date']:
        dates.setdefault(r['report_date'],[]).append(r['availability_filing_date'])
ep=P/'13f_cosine_overlap_edges.csv'
with ep.open(encoding='utf-8-sig',newline='') as f:
    edges=list(csv.DictReader(f))
for r in edges:
    ds=dates.get(r['report_date'],[])
    r['panel_availability_date']=max(ds) if ds else ''
with ep.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(edges[0].keys())); w.writeheader(); w.writerows(edges)

etfs=['SPY','DIA','QQQ','XLB','XLC','XLE','XLF','XLI','XLK','XLP','XLRE','XLU','XLV','XLY','IWD','IWF','IVE','IVW','IWB','IWM']
with (P/'etf_history_status.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f); w.writerow(['etf_ticker','holdings_link_rows_built','free_source','source_coverage','holdout_same_construction','status'])
    for t in etfs: w.writerow([t,'no','SEC Form N-PORT public data sets','public quarter-end reports begin 2019-10; quarterly bulk ZIP; filing/publication dates provide availability','partly: 2019-10 onward only; no 2010-2019 N-PORT','source identified; fund/series-level extraction and CUSIP mapping not completed in this dispatch'])
with (P/'customer_supplier_status.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f); w.writerow(['dataset','rows_built','availability_date_rule','coverage','status','reason']); w.writerow(['SEC 10-K major-customer relationships','0','10-K filing date','Dow issuer 10-Ks 2020-06 to 2026-10 not systematically coded','not feasible in this build','disclosures may anonymize customers (e.g. Customer A), may omit names below materiality thresholds, and require manual filing-by-filing entity resolution'])
