from __future__ import annotations
import csv, datetime as dt, hashlib, re, time
from pathlib import Path
from urllib.parse import quote_plus
import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
HOLD = (dt.date(2016, 1, 4), dt.date(2020, 10, 30))
DEV = (dt.date(2020, 11, 27), dt.date(2026, 10, 30))
UA = {'User-Agent': 'Mozilla/5.0 (compatible; event metadata research/1.0)'}
PRESS = 'https://press.spglobal.com/index.php'
WIKI = 'https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_400'
WIKI500 = 'https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500'
SESSION = requests.Session()

def win(ann, eff):
    for label, (lo, hi) in [('holdout', HOLD), ('dev', DEV)]:
        if lo <= ann <= hi and lo <= eff <= hi:
            return label
    return None

def url_date(url):
    m = re.search(r'(?<!\d)(20\d{2})[-/]?(\d{2})[-/]?(\d{2})(?!\d)', url)
    if not m: return None
    try: return dt.date(*map(int, m.groups()))
    except ValueError: return None

def norm_ticker(value):
    return re.sub(r'[^A-Z0-9.-]', '', value.upper().strip())

def search_release(query, ticker, index, effective_date, company=''):
    """Search press.spglobal.com by company plus 'Set to Join'; verify page text."""
    params = {'keywords': query + ' Set to Join', 'l': 100, 's': 2429}
    try:
        res = SESSION.get(PRESS, params=params, headers=UA, timeout=35)
        res.raise_for_status()
    except Exception:
        return None, None, False
    soup = BeautifulSoup(res.text, 'html.parser')
    links = []
    for a in soup.select('a[href]'):
        href = a.get('href', '')
        if 'press.spglobal.com/20' in href and href not in links:
            links.append(href)
    for href in links[:20]:
        ad = url_date(href)
        if not ad: continue
        try:
            article = SESSION.get(href, headers=UA, timeout=35)
            article.raise_for_status()
            text = BeautifulSoup(article.text, 'html.parser').get_text(' ', strip=True)
        except Exception:
            continue
        txt = re.sub(r'\s+', ' ', text).lower()
        tk = re.escape(norm_ticker(ticker).lower())
        ticker_match = bool(re.search(r'(?<![A-Z0-9])' + tk + r'(?![A-Z0-9])', text, re.I))
        target = 's&p 500' if index == 'S&P 500' else 's&p midcap 400'
        if (ticker_match and target in txt and ('join' in txt or 'added' in txt or 'replace' in txt)
                and dt.timedelta(0) < effective_date - ad <= dt.timedelta(days=60)):
            from_500 = False
            if index == 'S&P 400' and company:
                for m in re.finditer(r'S&P 500 constituent', text, re.I):
                    if company.lower() in text[m.end():m.end()+180].lower():
                        from_500 = True
                        break
            return ad, href, from_500
    return None, None, False

def wikipedia_500_names():
    res=SESSION.get(WIKI500,headers=UA,timeout=60); res.raise_for_status()
    soup=BeautifulSoup(res.text,'html.parser'); table=soup.select_one('table.wikitable')
    if table is None: raise RuntimeError('S&P 500 historical changes wikitable missing')
    out={}
    for tr in table.select('tr')[2:]:
        cells=tr.find_all(['th','td'],recursive=False)
        if len(cells)<4: continue
        try: eff=dt.datetime.strptime(cells[0].get_text(' ',strip=True),'%B %d, %Y').date()
        except ValueError: continue
        ticker=norm_ticker(cells[1].get_text(' ',strip=True)); company=cells[2].get_text(' ',strip=True)
        if ticker: out[(ticker,eff.isoformat())]=company
    return out

def wikipedia_400():
    res = SESSION.get(WIKI, headers=UA, timeout=60); res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')
    table = soup.select_one('table.wikitable')
    if table is None: raise RuntimeError('S&P 400 historical changes wikitable missing')
    out = []
    for tr in table.select('tr')[2:]:
        cells = tr.find_all(['th', 'td'], recursive=False)
        if len(cells) < 5: continue
        try: eff = dt.datetime.strptime(cells[0].get_text(' ', strip=True), '%B %d, %Y').date()
        except ValueError: continue
        ticker = norm_ticker(cells[1].get_text(' ', strip=True).replace('\xa0', ' '))
        company = cells[2].get_text(' ', strip=True)
        if not ticker: continue
        footnote_urls = []
        for a in cells[-1].find_all('a', href=True):
            href = a['href']
            if not href.startswith('#cite_note'): continue
            ref = soup.find(id=href[1:])
            if ref:
                for ra in ref.find_all('a', href=True):
                    u = ra['href']
                    if 'spglobal.com' in u.lower() and '/wiki/' not in u.lower(): footnote_urls.append(u)
        out.append((eff, ticker, company, list(dict.fromkeys(footnote_urls))) )
    return out

def main():
    # Use only the explicitly permitted two holdout-roster fields.
    roster_path = ROOT / 'sealed_holdout_sp500' / 'sp500_roster.csv'
    sp5 = pd.read_csv(roster_path, usecols=['ticker', 'effective_from'], dtype=str).fillna('')
    sp5_names = wikipedia_500_names()
    candidates = []
    for row in sp5.to_dict('records'):
        try: eff = dt.date.fromisoformat(row['effective_from'])
        except ValueError: continue
        if HOLD[0] < eff <= HOLD[1]:
            ticker=norm_ticker(row['ticker'])
            candidates.append({'window':'holdout','index':'S&P 500','ticker':ticker,
                               'effective_date':eff.isoformat(),'company_search_name':sp5_names.get((ticker,eff.isoformat()),''),
                               'event_source':'allowlisted S&P 500 roster dates/tickers; company name from public Wikipedia changes table'})

    # The development event universe is exactly the already frozen L-IDX4 list.
    with (ROOT / 'r9' / 'idx4' / 'event_list_metadata.csv').open(encoding='utf-8-sig', newline='') as f:
        for e in csv.DictReader(f):
            if e['window'] == 'dev' and e['status'] == 'eligible':
                candidates.append({k:e[k] for k in ['window','index','ticker','announcement_date','effective_date','announcement_url','event_source']})

    # Public Wikipedia changes table supplies the S&P 400 effective date/ticker/company and its citation links.
    wiki_rows = wikipedia_400()
    for eff, ticker, company, refs in wiki_rows:
        if not (HOLD[0] <= eff <= HOLD[1]): continue
        candidates.append({'window':'holdout','index':'S&P 400','ticker':ticker,'effective_date':eff.isoformat(),
                           'company_search_name':company,'wiki_url':WIKI,
                           'wiki_citation_urls':' | '.join(refs),
                           'event_source':'Wikipedia S&P 400 historical changes table'})

    # Search the S&P press archive for each holdout row by company name and "Set to Join".
    records=[]
    for n, e in enumerate(candidates, 1):
        if e.get('window') == 'dev':
            e['announcement_found'] = 1 if e.get('announcement_date') else 0
            records.append(e); continue
        query = e.get('company_search_name') or e['ticker']
        eff_date = dt.date.fromisoformat(e['effective_date'])
        ann, url, from_500 = search_release(query, e['ticker'], e['index'], eff_date, e.get('company_search_name',''))
        time.sleep(.15)
        if not url and e.get('wiki_citation_urls'):
            for u in e['wiki_citation_urls'].split(' | '):
                d = url_date(u)
                if not d or not (dt.timedelta(0) < eff_date - d <= dt.timedelta(days=60)): continue
                # Verify linked citation body names the ticker and the relevant index.
                try:
                    article = SESSION.get(u, headers=UA, timeout=35)
                    if article.ok:
                        text = BeautifulSoup(article.content, 'html.parser').get_text(' ', strip=True)
                        if re.search(r'(?<![A-Z0-9])'+re.escape(e['ticker'])+r'(?![A-Z0-9])', text, re.I) and ('S&P' in text or 'Standard & Poor' in text):
                            ann, url = d, u; break
                except Exception: pass
        e['announcement_date'] = ann.isoformat() if ann else ''
        e['announcement_url'] = url or ''
        e['announcement_found'] = int(bool(ann and url))
        e['migration_from_sp500'] = int(from_500)
        if ann and url:
            try: eff = dt.date.fromisoformat(e['effective_date'])
            except ValueError: eff = None
            e['window'] = win(ann, eff) if eff else None
        records.append(e)
        if n % 25 == 0: print(f'metadata_search_progress={n}/{len(candidates)}', flush=True)

    # Eligible event list includes dated dev rows unchanged and holdout rows with a sourced date
    # within the matching window. Preserve un-dated candidate counts separately.
    final=[]; missing=[]; found_all=[]
    for e in records:
        if e.get('window') == 'holdout': found_all.append(e)
        if e.get('migration_from_sp500'):
            e['drop_reason']='S&P 500 to S&P 400 migration; not an addition'
            continue
        if not e.get('announcement_found'):
            if e.get('effective_date','') and HOLD[0].isoformat() <= e['effective_date'] <= HOLD[1].isoformat(): missing.append(e)
            continue
        if e.get('window') in ('dev','holdout'):
            final.append(e)
    cols=['window','index','ticker','announcement_date','effective_date','announcement_url','event_source','wiki_url','wiki_citation_urls','company_search_name','announcement_found','migration_from_sp500','drop_reason']
    target=OUT/'event_list_frozen.csv'
    with target.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader(); w.writerows(sorted(final,key=lambda e:(e['window'],e['effective_date'],e['index'],e['ticker'])))
        f.flush()
    with (OUT/'metadata_candidates_missing_announcement.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader(); w.writerows(missing); f.flush()
    with (OUT/'metadata_search_all_candidates.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader(); w.writerows(records); f.flush()
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    print({'candidate_rows':len(candidates),'frozen_events':len(final),'missing_announcement_candidates':len(missing),
           'announcement_found_by_window_index':{w:{i:sum(1 for e in final if e['window']==w and e['index']==i) for i in ['S&P 500','S&P 400']} for w in ['holdout','dev']},
           'holdout_candidates_by_index':{i:sum(1 for e in candidates if e.get('effective_date','') and HOLD[0].isoformat() <= e['effective_date'] <= HOLD[1].isoformat() and e.get('index')==i) for i in ['S&P 500','S&P 400']},
           'missing_announcements_by_index':{i:sum(1 for e in missing if e.get('index')==i) for i in ['S&P 500','S&P 400']},
           'event_list_sha256':digest},flush=True)

if __name__=='__main__': main()
