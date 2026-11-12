from __future__ import annotations
import csv, re, datetime as dt
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE = Path(__file__).resolve().parents[2]  # pivot_research
OUT = Path(__file__).resolve().parent
WIKI = 'https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_400'
UA = {'User-Agent': 'Mozilla/5.0 (compatible; research event-list builder/1.0)'}
WINDOWS = {
    'holdout': (dt.date(2016,1,4), dt.date(2020,10,30)),
    'dev': (dt.date(2020,11,27), dt.date(2026,10,30)),
}

def press_date(url: str) -> dt.date | None:
    # The S&P DJI announcement URL encodes its publication date.
    m = re.search(r'(?<!\d)(20\d{2})[-/]?(\d{2})[-/]?(\d{2})(?!\d)', url)
    if not m:
        return None
    try: return dt.date(*map(int, m.groups()))
    except ValueError: return None

def inside_pair(ann: dt.date, eff: dt.date):
    for name, (lo, hi) in WINDOWS.items():
        if lo <= ann <= hi and lo <= eff <= hi:
            return name
    return None

# S&P 500 additions: a dated announcement source marks actual additions, while
# baseline rows reversed from the current roster have no announcement date.
sp5_path = BASE / 'r9' / 'data' / 'sp500_pit_roster_with_announcements.csv'
sp5 = pd.read_csv(sp5_path, dtype=str).fillna('')
rows = []
candidate_rows = []
for x in sp5.to_dict('records'):
    if not x['announcement_date'] or not x['announcement_source_url']:
        continue
    try:
        eff = dt.date.fromisoformat(x['effective_from'])
        ann = dt.date.fromisoformat(x['announcement_date'])
    except Exception:
        continue
    win = inside_pair(ann, eff)
    if win:
        rows.append(dict(window=win,index='S&P 500',ticker=x['ticker'],announcement_date=ann.isoformat(),effective_date=eff.isoformat(),announcement_url=x['announcement_source_url'],event_source='provided S&P 500 PIT roster',status='eligible',drop_reason=''))

# S&P 400 additions from the historical components table. Source footnotes
# link to official S&P DJI releases; only dated official S&P URLs qualify.
html = requests.get(WIKI, headers=UA, timeout=60).text
soup = BeautifulSoup(html, 'html.parser')
table = soup.select_one('table.wikitable')
if table is None: raise RuntimeError('S&P 400 historical components wikitable not found')
added = 0; no_press = 0; undated = 0; outwindow = 0; source_rows = 0
for tr in table.select('tr')[2:]:
    cells = tr.find_all(['th','td'], recursive=False)
    if len(cells) < 5: continue
    date_text = cells[0].get_text(' ',strip=True)
    try: eff = dt.datetime.strptime(date_text, '%B %d, %Y').date()
    except ValueError: continue
    ticker = cells[1].get_text(' ',strip=True).replace('\xa0',' ').strip()
    if not ticker: continue
    source_rows += 1
    eff_window = next((name for name,(lo,hi) in WINDOWS.items() if lo <= eff <= hi), None)
    refs=[]
    for a in cells[-1].find_all('a', href=True):
        href=a['href']
        if href.startswith('#cite_note'):
            ref=soup.find(id=href[1:])
            if ref:
                for ra in ref.find_all('a',href=True):
                    u=ra['href']
                    if ('spglobal.com' in u.lower() or 'press.spglobal.com' in u.lower()) and '/wiki/' not in u:
                        refs.append(u)
    refs=list(dict.fromkeys(refs))
    official=[u for u in refs if press_date(u)]
    if not official:
        if refs: undated += 1
        else: no_press += 1
        if eff_window:
            candidate_rows.append(dict(window=eff_window,index='S&P 400',ticker=ticker,announcement_date='',effective_date=eff.isoformat(),announcement_url='',event_source='Wikipedia historical components',status='dropped',drop_reason='no linked/findable dated S&P DJI press release'))
        continue
    url=official[0]
    ann=press_date(url)
    win=inside_pair(ann,eff)
    if not win:
        outwindow += 1
        if eff_window:
            candidate_rows.append(dict(window=eff_window,index='S&P 400',ticker=ticker,announcement_date=ann.isoformat(),effective_date=eff.isoformat(),announcement_url=url,event_source='Wikipedia historical components + linked S&P DJI release',status='dropped',drop_reason='announcement and effective date are not both inside the same window'))
        continue
    rows.append(dict(window=win,index='S&P 400',ticker=ticker,announcement_date=ann.isoformat(),effective_date=eff.isoformat(),announcement_url=url,event_source='Wikipedia historical components + linked S&P DJI release',status='eligible',drop_reason=''))
    added += 1

# Mark 400 constituents that leave the provided S&P 500 roster on the same
# effective date as non-additions. This is possible for the overlapping roster period.
sp5_ends={(r['ticker'],r['effective_to_exclusive']) for r in sp5.to_dict('records') if r['effective_to_exclusive']}
for r in rows:
    r['overlap_500_exit_same_date'] = int(r['index']=='S&P 400' and (r['ticker'], (dt.date.fromisoformat(r['effective_date'])+dt.timedelta(days=1)).isoformat()) in sp5_ends)
# effective_to_exclusive is first date outside index; index effective date is preceding session
# not necessarily prior calendar day, so use same date and one-day-before comparisons as metadata flags.
for r in rows:
    if r['index']=='S&P 400':
        e=dt.date.fromisoformat(r['effective_date'])
        r['overlap_500_exit_same_date'] = int(any(t==r['ticker'] and d in {e.isoformat(),(e+dt.timedelta(days=1)).isoformat()} for t,d in sp5_ends))
        if r['overlap_500_exit_same_date']:
            r['status']='dropped'; r['drop_reason']='identified S&P 500 to S&P 400 migration; not an addition'
            candidate_rows.append(r.copy())

cols=['window','index','ticker','announcement_date','effective_date','announcement_url','event_source','status','drop_reason','overlap_500_exit_same_date']
rows.sort(key=lambda r:(r['window'],r['effective_date'],r['index'],r['ticker']))
with (OUT/'event_list_metadata.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(r for r in rows if r['status']=='eligible')
with (OUT/'event_candidates_and_drops.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(candidate_rows)
summary={}
for w in WINDOWS:
    summary[w]={idx:sum(1 for r in rows if r['window']==w and r['index']==idx) for idx in ['S&P 500','S&P 400']}
drop_counts={name:{why:sum(1 for r in candidate_rows if r['window']==name and r['drop_reason']==why) for why in sorted({r['drop_reason'] for r in candidate_rows if r['window']==name})} for name in WINDOWS}
eligible_counts={name:{idx:sum(1 for r in rows if r['window']==name and r['index']==idx and r['status']=='eligible') for idx in ['S&P 500','S&P 400']} for name in WINDOWS}
print({'wiki_source_rows':source_rows,'s400_missing_press_link_all_periods':no_press,'s400_link_without_dated_url_all_periods':undated,'s400_outside_windows_all_periods':outwindow,'eligible_before_500to400_exclusion':summary,'eligible_after_exclusions':eligible_counts,'drop_counts_by_window':drop_counts})
