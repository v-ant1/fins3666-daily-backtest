"""Assemble top-50 PIT roster, holdout panel, coverage, and cosine link files."""
import csv,math
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
P=Path('A2/pivot_research/r4_L4/data')
def read(n):return list(csv.DictReader((P/n).open(encoding='utf-8-sig',newline='')))
def write(n,head,rows):
 with (P/n).open('w',newline='',encoding='utf-8') as f:w=csv.writer(f);w.writerow(head);w.writerows(rows)
def roster(d):
 r=set('MMM AA AXP T BAC BA CAT CSCO CVX KO DIS DD XOM GE HPQ HD IBM INTC JNJ JPM KFT MCD MRK MSFT PFE PG TRV UTX VZ WMT'.split())
 for cut,drop,add in [('2012-09-30',{'KFT'},{'UNH'}),('2013-09-30',{'BAC','AA','HPQ'},{'GS','V','NKE'}),('2015-03-31',{'T'},{'AAPL'}),('2017-09-30',{'DD'},{'DWDP'}),('2018-06-30',{'GE'},{'WBA'}),('2019-06-30',{'DWDP'},{'DOW'}),('2020-09-30',{'XOM','PFE','UTX'},{'CRM','AMGN','HON'}),('2024-03-31',{'WBA'},{'AMZN'}),('2024-12-31',{'DOW','INTC'},{'NVDA','SHW'})]:
  if d>=cut:r.difference_update(drop);r.update(add)
 return sorted(r)
def panel_date(d):return (date.fromisoformat(d)+timedelta(days=45)).isoformat()
selected_latest=defaultdict(str)
def full_date(d):return max(panel_date(d),selected_latest.get(d,''))
# Merge bulk point-in-time roster and text-parsed pre-2013 fixed-manager fallback.
bulkro=[r for r in read('13f_top50_pit_roster.csv') if r.get('selection_source')=='sec_quarterly_bulk']; metadata=read('13f_top50_holdout_filing_metadata.csv'); rank=read('13f_manager_rank_q2_2026.csv')
rank_by={r['manager_cik']:(r['rank'],r['manager_name']) for r in rank}
rosterrows=[[r['report_date'],r['rank_by_table_value'],r['manager_cik'],r['manager_name'],r['table_value_usd_thousands'],r['accession_number'],r['filing_date'],r['selection_source']] for r in bulkro]
for m in metadata:
 if m['report_period']>'2012-12-31':continue
 rr,default_name=rank_by[m['manager_cik']]
 rosterrows.append([m['report_period'],'',m['manager_cik'],m['manager_name'] or default_name,'',m['accession_number'],m['earliest_filing_date'],'fixed_Q2_2026_top50_fallback_pre2013_not_quarter_ranked'])
rosterrows.sort(key=lambda r:(r[0],int(r[1]) if r[1] else 999,int(r[2])))
for r in rosterrows:
 if r[6] and r[6]>selected_latest[r[0]]:selected_latest[r[0]]=r[6]
write('13f_top50_pit_roster.csv',['report_date','rank_by_table_value','manager_cik','manager_name','table_value_usd_thousands','accession_number','filing_date','selection_source'],rosterrows)
# Combine the development and holdout coverage tables for exact per-period counts.
pre_cov=read('13f_holdout_pre2013_coverage.csv'); bulk_cov=read('13f_pit_bulk_coverage.csv')
cover=[]
for r in pre_cov:
 cover.append([r['report_date'],'fixed_Q2_2026_top50_fallback_pre2013_not_quarter_ranked','',r['manager_cik'],r['manager_name'],r['availability_filing_date'],r['accession_number'],r['status'],r['mapped_dow_position_rows'],full_date(r['report_date'])])
for r in bulk_cov:
 if r['report_date']<='2020-09-30':
  cover.append([r['report_date'],'sec_quarterly_bulk_top50_by_reported_value',r['rank_by_table_value'],r['manager_cik'],r['manager_name'],r['filing_date'],r['accession_number'],r['status'],r['mapped_dow_position_rows'],full_date(r['report_date'])])
cover.sort(key=lambda r:(r[0],int(r[2]) if r[2] else 999,int(r[3])))
write('13f_holdout_coverage.csv',['report_date','selection_source','rank_by_table_value','manager_cik','manager_name','availability_filing_date','accession_number','status','mapped_dow_position_rows','full_roster_available_after'],cover)
# Provide the same quarter-level coverage and conservative roster release date for development quarters.
devcover=[]
for r in bulk_cov:
 if '2020-06-30'<=r['report_date']<='2026-06-30':devcover.append([r['report_date'],r['rank_by_table_value'],r['manager_cik'],r['manager_name'],r['filing_date'],r['accession_number'],r['status'],r['mapped_dow_position_rows'],full_date(r['report_date'])])
write('13f_development_coverage.csv',['report_date','rank_by_table_value','manager_cik','manager_name','availability_filing_date','accession_number','status','mapped_dow_position_rows','full_roster_available_after'],devcover)
byq=defaultdict(list)
for r in bulkro:byq[r['report_date']].append(r)
for r in rosterrows:
 if r[7].startswith('fixed_Q2'):byq[r[0]].append({'filing_date':r[6]})
avail=[]
for q,items in sorted(byq.items()):
 dates=[x.get('filing_date','') for x in items if x.get('filing_date','')]
 avail.append([q,max(dates) if dates else '',full_date(q),len(items)])
write('13f_pit_quarter_availability.csv',['report_date','latest_selected_filing_date','full_roster_available_after','roster_rows'],avail)
# Put only Dow-name rows in the combined holdout positions file.
prepos=read('13f_holdout_pre2013_positions.csv');bulkhold=read('13f_holdout_bulk_pit_positions.csv')
header=['report_date','availability_filing_date','manager_cik','manager_name','accession_number','ticker','cusip','reported_issuer','share_class','value_usd_thousands','shares_or_principal_amount','amount_type']
rows=[]
for r in prepos+bulkhold:
 rows.append([r.get(k,'') for k in header])
rows.sort(key=lambda r:(r[0],r[2],r[5],r[4]))
write('13f_holdout_positions.csv',header,rows)
# The 2020Q2 onward development panel uses the same quarter-specific top-50 selection.
# Retain the existing fixed-rank file as a Round 4 baseline and provide this clearly named PIT panel.
# Calculate common-owner cosine links from manager position values, aggregating duplicate information-table lines.
coverage_by=defaultdict(list)
for r in cover:coverage_by[r[0]].append(r)
bulk_by=defaultdict(list)
for r in bulk_cov:bulk_by[r['report_date']].append(r)
position_by=defaultdict(lambda:defaultdict(lambda:defaultdict(float)))
for r in rows:
 try:position_by[r[0]][r[5]][r[2]]+=float(r[9] or 0)
 except ValueError:pass
# Append development positions to the aggregate input; ensure no holdout price data are accessed.
dev=read('13f_development_pit_positions.csv')
for r in dev:
 try:position_by[r['report_date']][r['ticker']][r['manager_cik']]+=float(r['value_usd_thousands'] or 0)
 except ValueError:pass
quarters=sorted(set(r[0] for r in rosterrows if r[7]=='sec_quarterly_bulk')|set(r[0] for r in rosterrows if r[7].startswith('fixed_Q2')))
edges=[]
for q in quarters:
 if q<'2013-03-31':
  manager_ids=sorted({r[3] for r in coverage_by[q] if r[7].startswith('parsed_legacy_text')})
 else:
  manager_ids=sorted({r['manager_cik'] for r in bulk_by[q]})
 members=roster(q); vectors={t:[position_by[q][t].get(m,0.0) for m in manager_ids] for t in members};norm={t:math.sqrt(sum(x*x for x in vectors[t])) for t in members}
 for i,a in enumerate(members):
  for b in members[i+1:]:
   den=norm[a]*norm[b];cos=sum(x*y for x,y in zip(vectors[a],vectors[b]))/den if den else 0.0
   edges.append([q,len(manager_ids),full_date(q),a,b,f'{cos:.12g}'])
write('13f_pit_cosine_overlap_edges.csv',['report_date','filers_in_overlap','full_roster_available_after','ticker_i','ticker_j','cosine_13f_portfolio_value_overlap'],edges)
# Refresh Round 4 canonical development filenames with the point-in-time manager construction.
write('13f_holder_by_dow_stock.csv',header,[[r.get(k,'') for k in header] for r in dev])
dev_edges=[r for r in edges if '2020-06-30'<=r[0]<='2026-06-30']
write('13f_cosine_overlap_edges.csv',['report_date','parsed_manager_count','panel_availability_date','ticker_i','ticker_j','cosine_13f_portfolio_value_overlap'],[[r[0],r[1],r[2],r[3],r[4],r[5]] for r in dev_edges])
write('13f_filing_coverage.csv',['manager_cik','manager_name','report_date','availability_filing_date','status','accession_or_error'],[[r[2],r[3],r[0],r[4],r[6],r[5]] for r in devcover])
print('roster',len(rosterrows),'holdout rows',len(rows),'coverage',len(cover),'dev rows',len(dev),'edges',len(edges))
