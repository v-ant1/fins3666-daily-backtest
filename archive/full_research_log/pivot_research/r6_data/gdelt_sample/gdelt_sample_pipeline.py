from __future__ import annotations
import csv, hashlib, io, re, zipfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent
BASE = 'https://data.gdeltproject.org/gkg/'
MONTHS = ('202103', '202503')

ROSTERS = {
 '202103': {
  'AAPL':['Apple','Apple Inc','Apple Computer'], 'AXP':['American Express','American Express Company'],
  'AMGN':['Amgen','Amgen Inc'], 'BA':['Boeing','Boeing Company','Boeing Co'],
  'CAT':['Caterpillar','Caterpillar Inc'], 'CVX':['Chevron','Chevron Corporation','Chevron Corp'],
  'CSCO':['Cisco','Cisco Systems','Cisco Systems Inc'], 'DIS':['Disney','Walt Disney Company','Walt Disney'],
  'DOW':['Dow','Dow Inc'], 'GS':['Goldman Sachs','Goldman Sachs Group'],
  'HD':['Home Depot','The Home Depot','Home Depot Inc'], 'HON':['Honeywell','Honeywell International','Honeywell International Inc'],
  'IBM':['IBM','International Business Machines'], 'INTC':['Intel','Intel Corporation'],
  'JNJ':['Johnson & Johnson','Johnson and Johnson'], 'JPM':['JPMorgan','JPMorgan Chase','JPMorgan Chase & Co'],
  'KO':['Coca-Cola','Coca Cola','Coca-Cola Company'], 'MCD':["McDonald's",'McDonalds',"McDonald's Corporation"],
  'MMM':['3M','3M Company'], 'MRK':['Merck','Merck & Co'], 'MSFT':['Microsoft','Microsoft Corporation'],
  'NKE':['Nike','Nike Inc'], 'PG':['Procter & Gamble','Procter and Gamble','P&G'],
  'CRM':['Salesforce','Salesforce.com','Salesforce Inc'], 'TRV':['Travelers','The Travelers Companies','Travelers Companies'],
  'UNH':['UnitedHealth','UnitedHealth Group'], 'V':['Visa','Visa Inc'],
  'VZ':['Verizon','Verizon Communications'], 'WBA':['Walgreens','Walgreens Boots Alliance'], 'WMT':['Walmart','Walmart Inc']
 },
 '202503': {
  'AAPL':['Apple','Apple Inc','Apple Computer'], 'AXP':['American Express','American Express Company'],
  'AMGN':['Amgen','Amgen Inc'], 'BA':['Boeing','Boeing Company','Boeing Co'],
  'CAT':['Caterpillar','Caterpillar Inc'], 'CVX':['Chevron','Chevron Corporation','Chevron Corp'],
  'CSCO':['Cisco','Cisco Systems','Cisco Systems Inc'], 'DIS':['Disney','Walt Disney Company','Walt Disney'],
  'AMZN':['Amazon','Amazon.com','Amazon.com Inc'], 'GS':['Goldman Sachs','Goldman Sachs Group'],
  'HD':['Home Depot','The Home Depot','Home Depot Inc'], 'HON':['Honeywell','Honeywell International','Honeywell International Inc'],
  'IBM':['IBM','International Business Machines'], 'NVDA':['Nvidia','NVIDIA Corporation','Nvidia Corporation'],
  'JNJ':['Johnson & Johnson','Johnson and Johnson'], 'JPM':['JPMorgan','JPMorgan Chase','JPMorgan Chase & Co'],
  'KO':['Coca-Cola','Coca Cola','Coca-Cola Company'], 'MCD':["McDonald's",'McDonalds',"McDonald's Corporation"],
  'MMM':['3M','3M Company'], 'MRK':['Merck','Merck & Co'], 'MSFT':['Microsoft','Microsoft Corporation'],
  'NKE':['Nike','Nike Inc'], 'PG':['Procter & Gamble','Procter and Gamble','P&G'],
  'CRM':['Salesforce','Salesforce.com','Salesforce Inc'], 'SHW':['Sherwin-Williams','The Sherwin-Williams Company','Sherwin Williams'],
  'TRV':['Travelers','The Travelers Companies','Travelers Companies'], 'UNH':['UnitedHealth','UnitedHealth Group'],
  'V':['Visa','Visa Inc'], 'VZ':['Verizon','Verizon Communications'], 'WMT':['Walmart','Walmart Inc']
 }
}

def norm(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', s.casefold())

def build_matchers(roster):
    out = defaultdict(set)
    for ticker, aliases in roster.items():
        for alias in aliases:
            out[norm(alias)].add(ticker)
    return out

def get_month_files():
    html = requests.get(BASE + 'index.html', timeout=90).text
    matches = re.findall(r'<A HREF="(\d{8}\.gkg\.csv\.zip)"[^>]*>[^<]*</A> \(([^)]*)\)', html)
    all_names = {n for n, _ in matches}
    selected = {}
    for month in MONTHS:
        names = sorted(n for n in all_names if n.startswith(month))
        expected_days = 31
        if len(names) != expected_days:
            raise RuntimeError(f'{month}: expected 31 daily archive files, found {len(names)}')
        selected[month] = names
    return selected

def download_one(name):
    p = ROOT / name[:6] / name
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists() and p.stat().st_size:
        return name, p.stat().st_size, 'cached'
    url = BASE + name
    tmp = p.with_suffix(p.suffix + '.part')
    with requests.get(url, stream=True, timeout=(30, 240)) as resp:
        resp.raise_for_status()
        with tmp.open('wb') as f:
            for chunk in resp.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)
    with zipfile.ZipFile(tmp) as z:
        if z.testzip() is not None:
            raise RuntimeError(f'zip CRC failure: {name}')
        if len(z.namelist()) != 1:
            raise RuntimeError(f'unexpected archive members for {name}: {z.namelist()}')
    tmp.replace(p)
    return name, p.stat().st_size, 'downloaded'

def extract_orgs(row):
    # Official GKG daily-archive schema: DATE, NUMARTS, COUNTS, THEMES,
    # LOCATIONS, PERSONS, ORGANIZATIONS, TONE, CAMEOEVENTIDS, SOURCES, SOURCEURLS.
    fields = row.rstrip('\r\n').split('\t')
    if len(fields) < 11:
        return None
    return fields

def process_month(month, files):
    roster = ROSTERS[month]
    matchers = build_matchers(roster)
    articles = set()
    company_urls = defaultdict(set)
    pair_urls = defaultdict(set)
    rows_seen = 0
    rows_with_orgs = 0
    week = lambda d: (d - __import__('datetime').timedelta(days=d.weekday())).isoformat()
    with (ROOT / f'{month}_daily_audit.csv').open('w', newline='', encoding='utf-8') as audit_f:
        audit = csv.writer(audit_f)
        audit.writerow(['date','source_url','matched_tickers','matched_org_names'])
        for fname in files:
            p = ROOT / month / fname
            with zipfile.ZipFile(p) as z:
                with z.open(z.namelist()[0]) as raw:
                    for bline in raw:
                        rows_seen += 1
                        try:
                            row = extract_orgs(bline.decode('utf-8', 'replace'))
                            if row is None:
                                continue
                            date_s, org_s, url_s = row[0], row[6], row[10]
                            org_names = [x.strip() for x in org_s.split(';') if x.strip()]
                            matched = set()
                            matched_names = []
                            for org in org_names:
                                ts = matchers.get(norm(org), set())
                                if ts:
                                    matched.update(ts)
                                    matched_names.append(org)
                            if not matched:
                                continue
                            rows_with_orgs += 1
                            urls = [u.strip() for u in url_s.split(';') if u.strip()]
                            if not urls:
                                # No URL means there is no stable article key for pair de-duplication.
                                continue
                            from datetime import date
                            w = week(date(int(date_s[:4]), int(date_s[4:6]), int(date_s[6:8])))
                            for url in urls:
                                key = url.strip()
                                articles.add((key, w))
                                for ticker in matched:
                                    company_urls[ticker].add((key, w))
                                ordered = sorted(matched)
                                for i, a in enumerate(ordered):
                                    for b in ordered[i+1:]:
                                        pair_urls[(w,a,b)].add(key)
                                audit.writerow([date_s,key,'|'.join(sorted(matched)),'|'.join(matched_names)])
                        except Exception as e:
                            raise RuntimeError(f'{fname}: parse failure row {rows_seen}: {e}') from e
    company_rows=[]
    for ticker in roster:
        by_week=Counter(w for _,w in company_urls[ticker])
        company_rows.append([month,ticker,len(company_urls[ticker]),sum(v>0 for v in by_week.values())])
    with (ROOT / f'{month}_company_coverage.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['month','ticker','distinct_article_urls','weeks_with_at_least_one_article']); w.writerows(company_rows)
    pair_counts=Counter({k:len(v) for k,v in pair_urls.items()})
    weeks=sorted(set(w for _,w in articles))
    pair_rows=[]
    possible=len(roster)*(len(roster)-1)//2
    for w in weeks:
        active={ (a,b):n for (ww,a,b),n in pair_counts.items() if ww==w and n>0 }
        density=len(active)/possible if possible else 0
        pair_rows.append([month,w,len({u for u,ww in articles if ww==w}),len(active),possible,density])
    with (ROOT / f'{month}_weekly_pairwise.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['month','week_monday','distinct_article_urls_with_any_roster_match','active_pairs_n_articles_ge_1','possible_pairs_30_names','edge_density']); w.writerows(pair_rows)
    with (ROOT / f'{month}_pair_counts.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['month','week_monday','ticker_a','ticker_b','distinct_article_urls']);
        for (ww,a,b),n in sorted(pair_counts.items()): w.writerow([month,ww,a,b,n])
    return {
      'month':month,'gkg_rows':rows_seen,'rows_with_exact_org_match':rows_with_orgs,
      'distinct_urls_with_any_match':len(articles),'companies_covered':sum(bool(company_urls[t]) for t in roster),
      'companies_total':len(roster),'weeks_with_any_roster_match':len(weeks),'possible_pairs':possible,
      'edge_density_mean':sum(r[5] for r in pair_rows)/len(pair_rows) if pair_rows else 0,
      'edge_density_min':min((r[5] for r in pair_rows),default=0),'edge_density_max':max((r[5] for r in pair_rows),default=0),
      'total_positive_week_pair_edges':sum(r[3] for r in pair_rows),
      'sample_weeks':len(pair_rows)
    }

def main():
    selected=get_month_files()
    all_names=[n for m in MONTHS for n in selected[m]]
    print(f'Pulling {len(all_names)} official daily GKG archives (31 days each month).')
    results=[]
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs=[ex.submit(download_one,n) for n in all_names]
        for i,f in enumerate(as_completed(futs),1):
            name,size,status=f.result()
            results.append((name,size,status))
            if i%10==0 or i==len(futs): print(f'downloaded/verified {i}/{len(futs)}; latest {name} {size:,} bytes {status}')
    with (ROOT/'download_manifest.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['archive','bytes','status','url']);
        for name,size,status in sorted(results): w.writerow([name,size,status,BASE+name])
    summaries=[]
    for month in MONTHS:
        print(f'Processing {month}')
        summaries.append(process_month(month,selected[month]))
    with (ROOT/'sample_summary.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(summaries[0])); w.writeheader(); w.writerows(summaries)
    print(summaries)

if __name__=='__main__': main()
