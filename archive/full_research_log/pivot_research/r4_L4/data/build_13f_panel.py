"""Build SEC 13F quarterly Dow holdings and cosine-overlap links.

Run from workspace root: python A2/pivot_research/r4_L4/data/build_13f_panel.py
Only SEC public filing data for report periods 2020-06 onward is requested.
Requests are spaced at 0.15 s (below the SEC fair-access ceiling).
"""
import csv
import calendar
import datetime as dt
import math
import re
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import requests

OUT = Path('A2/pivot_research/r4_L4/data')
UA = 'FINS3666 network data project contact research@example.edu'
S = requests.Session()
S.headers.update({'User-Agent': UA, 'Accept-Encoding': 'gzip, deflate'})
PAUSE = 0.15

# Fixed top-50 manager roster ranked by the SEC's 2026 Q2 Form 13F reported values.
# CIKs are reporting persons; affiliated filing entities may appear separately.
with (OUT / '13f_manager_rank_q2_2026.csv').open(encoding='utf-8-sig', newline='') as f:
    MANAGERS = {r['manager_cik']: r['manager_name'] for r in csv.DictReader(f)}

# 13F-reported CUSIPs for Dow constituents in the development interval.
# CUSIP is the join key; ticker names are never inferred from price series.
CUSIP_TO_TICKER = {
    '037833100':'AAPL','031162100':'AMGN','023135106':'AMZN','025816109':'AXP',
    '097023105':'BA','149123101':'CAT','79466L302':'CRM','17275R102':'CSCO',
    '166764100':'CVX','260557103':'DOW','254687106':'DIS','38141G104':'GS',
    '437076102':'HD','438516106':'HON','459200101':'IBM','458140100':'INTC',
    '478160104':'JNJ','46625H100':'JPM','191216100':'KO','580135101':'MCD',
    '88579Y101':'MMM','58933Y105':'MRK','594918104':'MSFT','654106103':'NKE',
    '67066G104':'NVDA','742718109':'PG','75513E101':'RTX','824348106':'SHW',
    '89417E109':'TRV','91324P102':'UNH','92826C839':'V','92343V104':'VZ',
    '931427108':'WBA','931142103':'WMT','30231G102':'XOM','717081103':'PFE',
}

def qdate(year, quarter):
    month = quarter * 3
    return f'{year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}'

REPORT_DATES = []
for y in range(2020, 2027):
    for q in range(1, 5):
        d = qdate(y, q)
        if '2020-06-30' <= d <= '2026-09-30':
            REPORT_DATES.append(d)

def roster_for(report_date):
    d = report_date
    roster = set('MMM AXP AAPL BA CAT CSCO CVX DIS DOW GS HD IBM INTC JNJ JPM KO MCD MRK MSFT NKE PFE PG RTX TRV VZ WBA WMT XOM'.split())
    if d >= '2020-09-30':
        roster -= {'PFE','XOM','RTX'}
        roster |= {'AMGN','CRM','HON'}
    if d >= '2024-03-31':
        roster -= {'WBA'}
        roster |= {'AMZN'}
    if d >= '2024-12-31':
        roster -= {'DOW','INTC'}
        roster |= {'NVDA','SHW'}
    return roster

def request(url):
    last = None
    for attempt in range(4):
        try:
            r = S.get(url, timeout=60)
            if r.status_code == 200:
                time.sleep(PAUSE)
                return r
            last = f'HTTP {r.status_code}'
            if r.status_code not in (403, 429, 500, 502, 503):
                break
        except Exception as e:
            last = type(e).__name__
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f'{url}: {last}')

def localtag(tag):
    return tag.rsplit('}', 1)[-1]

def parse_infotable(xml_bytes):
    root = ET.fromstring(xml_bytes)
    result = []
    for node in root.iter():
        if localtag(node.tag) != 'infoTable':
            continue
        fields = {localtag(c.tag): (c.text or '').strip() for c in node.iter() if c is not node}
        cusip = re.sub(r'\s+', '', fields.get('cusip', '')).upper()
        ticker = CUSIP_TO_TICKER.get(cusip)
        if not ticker:
            continue
        share_node = next((x for x in node.iter() if localtag(x.tag) == 'shrsOrPrnAmt'), None)
        shares = ''
        if share_node is not None:
            shares = next(((c.text or '').strip() for c in share_node if localtag(c.tag) == 'sshPrnamt'), '')
        result.append((ticker, cusip, fields.get('nameOfIssuer',''), fields.get('titleOfClass',''), fields.get('value',''), shares, fields.get('sshPrnamtType','')))
    return result

def load_recent(cik):
    url = f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json'
    data = request(url).json()
    rows = []
    for i, form in enumerate(data.get('filings', {}).get('recent', {}).get('form', [])):
        recent = data['filings']['recent']
        if form != '13F-HR':
            continue
        report = recent.get('reportDate', [''] * len(recent['form']))[i]
        if report in REPORT_DATES:
            filed = recent.get('filingDate', [''] * len(recent['form']))[i]
            if filed <= '2026-10-30':
                rows.append((report, filed, recent['accessionNumber'][i], recent['primaryDocument'][i]))
    # Include an archived submissions page if the recent block did not reach 2020.
    for block in data.get('filings', {}).get('files', []):
        if rows and min(x[0] for x in rows) <= '2020-06-30':
            break
        part = request('https://data.sec.gov/submissions/' + block['name']).json()
        for i, form in enumerate(part.get('form', [])):
            if form != '13F-HR':
                continue
            report = part.get('reportDate', [''] * len(part['form']))[i]
            filed = part.get('filingDate', [''] * len(part['form']))[i]
            if report in REPORT_DATES and filed <= '2026-10-30':
                rows.append((report, filed, part['accessionNumber'][i], part['primaryDocument'][i]))
    # First original filing is the earliest public observation for that period.
    by_report = {}
    for row in sorted(rows, key=lambda x: x[1]):
        by_report.setdefault(row[0], row)
    return by_report

def get_holding_file(cik, accession):
    acc = accession.replace('-', '')
    index = request(f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/index.json').json()
    items = index.get('directory', {}).get('item', [])
    candidates = [x['name'] for x in items if 'info' in x['name'].lower() and x['name'].lower().endswith('.xml')]
    if not candidates:
        # Some filers put holdings in the primary XML document.
        candidates = [x['name'] for x in items if x['name'].lower().endswith('.xml') and 'primary' in x['name'].lower()]
    for filename in candidates:
        xml = request(f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{filename}').content
        rows = parse_infotable(xml)
        if rows:
            return rows
    return []

raw_rows = []
coverage_rows = []
for cik, manager in MANAGERS.items():
    try:
        filings = load_recent(cik)
    except Exception as e:
        coverage_rows.append([cik, manager, '', '', 'submission_fetch_failed', str(e)])
        continue
    for period in REPORT_DATES:
        filing = filings.get(period)
        if not filing:
            coverage_rows.append([cik, manager, period, '', 'no_original_filing_found_by_cutoff', ''])
            continue
        report, filed, accession, primary = filing
        try:
            holdings = get_holding_file(cik, accession)
            coverage_rows.append([cik, manager, report, filed, f'parsed_{len(holdings)}_Dow_rows', accession])
            for ticker, cusip, issuer, share_class, value, shares, amount_type in holdings:
                raw_rows.append([report, filed, cik, manager, accession, ticker, cusip, issuer, share_class, value, shares, amount_type])
        except Exception as e:
            coverage_rows.append([cik, manager, report, filed, 'filing_parse_failed', type(e).__name__])

raw_path = OUT / '13f_holder_by_dow_stock.csv'
with raw_path.open('w', newline='', encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['report_date','availability_filing_date','manager_cik','manager_name','accession_number','ticker','cusip','reported_issuer','share_class','value_usd_thousands','shares_or_principal_amount','amount_type']); w.writerows(raw_rows)

coverage_path = OUT / '13f_filing_coverage.csv'
with coverage_path.open('w', newline='', encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['manager_cik','manager_name','report_date','availability_filing_date','status','accession_or_error']); w.writerows(coverage_rows)

# Complete-case manager panel for each quarter. Missing manager filings are excluded,
# not treated as zero; absent constituent positions within a filed 13F are zero.
by_quarter = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
for r in raw_rows:
    report, filed, cik, manager, accession, ticker, cusip, issuer, share_class, value, shares, amount_type = r
    try: by_quarter[report][ticker][cik] += float(value or 0.0)
    except ValueError: pass
filers_by_quarter = defaultdict(set)
for row in coverage_rows:
    cik, manager, report, filed, status, extra = row
    if status.startswith('parsed_'):
        filers_by_quarter[report].add(cik)

edge_path = OUT / '13f_cosine_overlap_edges.csv'
edge_rows=[]
for report in REPORT_DATES:
    members=sorted(roster_for(report))
    managers=sorted(filers_by_quarter[report])
    # Value vector across all successfully parsed managers for this quarter.
    vectors={t:[by_quarter[report][t].get(m,0.0) for m in managers] for t in members}
    norms={t:math.sqrt(sum(x*x for x in v)) for t,v in vectors.items()}
    for i,a in enumerate(members):
        for b in members[i+1:]:
            denom=norms[a]*norms[b]
            cosine=sum(x*y for x,y in zip(vectors[a],vectors[b]))/denom if denom else 0.0
            edge_rows.append([report, len(managers), a, b, f'{cosine:.12g}'])
with edge_path.open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['report_date','parsed_manager_count','ticker_i','ticker_j','cosine_13f_portfolio_value_overlap']); w.writerows(edge_rows)

print(f'wrote {len(raw_rows)} position rows, {len(edge_rows)} overlap rows, {len(coverage_rows)} filing-status rows')
