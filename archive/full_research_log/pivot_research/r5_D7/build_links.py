"""Build an outcome-blind named major-customer link panel from SEC 10-Ks.

Only SEC filing metadata/text, the D7 development earnings clock, a public
company name/ticker index, and the point-in-time Dow calendar are read. No
price, return, signal, or holdout file is opened.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from bisect import bisect_right
from collections import defaultdict
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from exchange_calendars import get_calendar

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
DATA = ROOT / 'r4_L4' / 'data'
EARNINGS = DATA / 'earnings_clock.csv'
SIC = DATA / 'sic_panel.csv'
DEV_START = '2020-11-27'
DEV_END = '2026-10-30'
FILINGS_START = '2019-01-01'
FILINGS_END = DEV_END
USER_AGENT = 'FINS3666 student research contact research@example.com'
SEC_TICKERS_URL = 'https://www.sec.gov/files/company_tickers_exchange.json'
SUBMISSIONS_URL = 'https://data.sec.gov/submissions/CIK{cik}.json'
ARCHIVE_URL = 'https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}'
REQUEST_PAUSE = 0.22
XNYS = get_calendar('XNYS')
XNYS_SESSIONS = [str(x.date()) for x in XNYS.sessions_in_range('2019-01-01', '2026-12-31')]

# Effective membership schedule, sourced in the L4 earnings-clock QA from the
# official S&P Dow Jones Indices change notices. The first roster is the
# post-August-2020 development roster.
ROSTERS = [
    ('2020-11-27', ['AAPL','AMGN','AXP','BA','CAT','CRM','CSCO','CVX','DIS','DOW','GS','HD','HON','IBM','INTC','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','PG','TRV','UNH','V','VZ','WBA','WMT']),
    ('2024-02-26', ['AAPL','AMGN','AXP','AMZN','BA','CAT','CRM','CSCO','CVX','DIS','DOW','GS','HD','HON','IBM','INTC','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','PG','TRV','UNH','V','VZ','WMT']),
    ('2024-11-08', ['AAPL','AMGN','AXP','AMZN','BA','CAT','CRM','CSCO','CVX','DIS','GS','HD','HON','IBM','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','NVDA','PG','SHW','TRV','UNH','V','VZ','WMT']),
]
DEV_TICKERS = set().union(*(set(x[1]) for x in ROSTERS))
CIK_OVERRIDES = {'WBA': '0001618921'}

PCT_RE = re.compile(r'(?<!\d)(1[0-9](?:\.\d+)?|[2-9][0-9](?:\.\d+)?|100(?:\.0+)?)\s*(?:%|percent)', re.I)
MAJOR_RE = re.compile(r'customer|customers|client|clients|sales to|net sales to|revenue from|accounts receivable', re.I)
ANON_RE = re.compile(r'\b(?:customer|client|retailer|distributor)\s+[A-Z0-9]{1,3}\b|\b(?:one|two|three|several)\s+(?:of our )?(?:largest )?customers\b', re.I)
CAPTURE_RE = re.compile(
    r'(?:sales|net sales|revenue|receivables)\s+(?:to|from)\s+(?P<a>[A-Z][A-Za-z0-9&.,’\'()\- ]{2,70}?)\s+(?:accounted|represented|comprised|were|was)|'
    r'(?P<b>[A-Z][A-Za-z0-9&.,’\'()\- ]{2,60}?)\s+(?:accounted for|represented|comprised)\s+(?:approximately\s+|more than\s+)?(?:1[0-9]|[2-9][0-9])(?:\.\d+)?\s*(?:%|percent)', re.I)
CLAIM_PATTERNS = [re.compile(
    r'\b(?:net\s+)?(?:sales|revenues?|accounts receivable)\s+(?:to|from)\s+'
    r'(?P<name>[A-Z][^.;]{1,110}?)\s+(?:accounted for|represented|comprised|made up)\s+'
    r'(?:approximately\s+|more than\s+|at least\s+)?(?:1[0-9]|[2-9][0-9])(?:\.\d+)?\s*(?:%|percent)', re.I),
    re.compile(r'\b(?:customer|client)\s+(?:named\s+)?(?P<name>[A-Z][A-Za-z0-9&.,’\'()\- ]{2,80}?)\s+'
               r'(?:accounted for|represented|comprised)\s+(?:approximately\s+|more than\s+)?'
               r'(?:1[0-9]|[2-9][0-9])(?:\.\d+)?\s*(?:%|percent)', re.I)]
LEGAL = {'inc','incorporated','corporation','corp','company','co','limited','ltd','plc','llc','lp','l p','the'}


def _norm(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', str(s).lower())


def _name_aliases(name: str) -> set[str]:
    tokens = re.findall(r'[A-Za-z0-9]+', str(name).lower())
    while tokens and tokens[-1] in LEGAL:
        tokens.pop()
    base = ''.join(tokens)
    aliases = {_norm(name)}
    if len(base) >= 4:
        aliases.add(base)
    return {x for x in aliases if len(x) >= 5}


def dow_roster(day: str) -> set[str]:
    roster = set(ROSTERS[0][1])
    for effective, members in ROSTERS[1:]:
        if day >= effective:
            roster = set(members)
    return roster


def dow_intervals(ticker: str):
    ranges = []
    start = DEV_START
    previous = set(ROSTERS[0][1])
    for effective, members in ROSTERS[1:]:
        current = set(members)
        if ticker in previous and ticker not in current:
            ranges.append((start, effective))
        elif ticker not in previous and ticker in current:
            start = effective
        previous = current
    if ticker in previous:
        ranges.append((start, DEV_END))
    return ranges


def next_session(filing_date: str) -> str:
    # XNYS calendar dates only; this does not inspect or derive a return.
    i = bisect_right(XNYS_SESSIONS, filing_date)
    if i == len(XNYS_SESSIONS):
        raise ValueError(f'No NYSE session after filing date {filing_date}')
    return XNYS_SESSIONS[i]


def npdate(value: str) -> date:
    y, m, d = map(int, value[:10].split('-'))
    return date(y, m, d)


def _json_get(session, url, cache_path=None):
    if cache_path and cache_path.is_file():
        return json.loads(cache_path.read_text(encoding='utf-8'))
    response = session.get(url, timeout=60)
    response.raise_for_status()
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(response.text, encoding='utf-8')
    time.sleep(REQUEST_PAUSE)
    return response.json()


def _text_get(session, url, cache_path):
    if cache_path.is_file():
        return cache_path.read_bytes()
    response = session.get(url, timeout=90)
    response.raise_for_status()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(response.content)
    time.sleep(REQUEST_PAUSE)
    return response.content


def _load_earnings():
    with EARNINGS.open('r', encoding='utf-8-sig', newline='') as f:
        rows = [row for row in csv.DictReader(f)
                if DEV_START <= str(row.get('filing_date') or '')[:10] <= DEV_END]
    return rows


def _issuer_index(session, cache_dir):
    obj = _json_get(session, SEC_TICKERS_URL, cache_dir / 'company_tickers_exchange.json')
    by_ticker = {}
    by_cik = {}
    for cik, name, ticker, _exchange in obj.get('data', []):
        ticker = str(ticker or '').upper()
        cik = str(cik).zfill(10)
        record = {'cik': cik, 'name': str(name), 'ticker': ticker}
        if ticker:
            by_ticker[ticker] = record
        by_cik[cik.lstrip('0')] = record
    # Historical WBA is missing from the current ticker directory; the L4
    # earnings-clock CIK is the dated issuer mapping for the D7 sample.
    by_ticker['WBA'] = {'cik': CIK_OVERRIDES['WBA'], 'name': 'Walgreens Boots Alliance, Inc.', 'ticker': 'WBA'}
    return by_ticker, by_cik


def _listed_customer_map(earnings_rows, by_ticker, by_cik):
    records = {}
    for row in earnings_rows:
        cik = str(row.get('cik', '')).lstrip('0')
        ticker = str(row.get('ticker', '')).upper()
        if not cik or not ticker:
            continue
        rec = records.setdefault(cik, {'cik': cik.zfill(10), 'ticker': ticker,
                                       'names': set(), 'clock_tickers': set()})
        if row.get('company_name'):
            rec['names'].add(row['company_name'])
        rec['clock_tickers'].add(ticker)
    for rec in by_cik.values():
        cik = rec['cik'].lstrip('0')
        if cik in records:
            records[cik]['names'].add(rec['name'])
    aliases = defaultdict(list)
    for cik, rec in records.items():
        for name in rec['names']:
            for alias in _name_aliases(name):
                aliases[alias].append(cik)
    return records, aliases


def _sentences(text):
    # Filing HTML tables often lack punctuation; retain larger disclosure
    # windows around percentage mentions rather than splitting aggressively.
    for m in PCT_RE.finditer(text):
        start = max(text.rfind('.', 0, m.start()), text.rfind(';', 0, m.start()),
                    text.rfind('\n', 0, m.start())) + 1
        stops = [x for x in (text.find('.', m.end()), text.find(';', m.end()),
                             text.find('\n', m.end())) if x >= 0]
        end = min(stops) if stops else min(len(text), m.end() + 250)
        start = max(start, m.start() - 350)
        end = min(end, m.end() + 350)
        yield m, text[start:end].strip()


def _match_customers(window, aliases):
    tokens = re.findall(r'[A-Za-z0-9]+', window.lower())
    hits = set()
    # Probe a compact list of text n-grams against the alias dictionary rather
    # than scanning the whole 10k-company index for every percentage mention.
    for i in range(len(tokens)):
        for j in range(i + 1, min(i + 9, len(tokens) + 1)):
            alias = ''.join(tokens[i:j])
            if len(alias) >= 5 and alias in aliases:
                hits.update(aliases[alias])
    return hits


def extract_disclosures(html_bytes, aliases, issuer_by_cik):
    soup = BeautifulSoup(html_bytes, 'html.parser')
    text = re.sub(r'\s+', ' ', soup.get_text(' ', strip=True))
    found = []
    # Many ASC 280 disclosures put the named customer on one table row and
    # its percentage of revenue on the following row. Preserve that explicit
    # row relationship rather than searching a broad window for company names.
    for table in soup.find_all('table'):
        rows = []
        for tr in table.find_all('tr'):
            cells = [' '.join(cell.stripped_strings) for cell in tr.find_all(['th', 'td'])]
            if cells:
                rows.append(cells)
        if not any('total' in ' '.join(c).lower() and 'revenue' in ' '.join(c).lower() for c in rows):
            continue
        for i, cells in enumerate(rows):
            label = re.sub(r'\s+', ' ', ' '.join(cells)).strip()
            if not label or re.search(r'\b(?:%|percent|sales|revenue|years ended|customer|customers)\b', label, re.I):
                continue
            ciks = _match_customers(label, aliases)
            # A table entity label must resolve uniquely; no fuzzy inference.
            if len(ciks) != 1:
                continue
            pct = None
            for next_cells in rows[i + 1:i + 4]:
                metric = ' '.join(next_cells)
                if re.search(r'%\s*of\s*(?:total\s*)?(?:gross\s*)?(?:net\s*)?revenues?', metric, re.I):
                    vals = [float(x) for x in re.findall(r'(?<!\d)(100|[1-9]?\d)(?:\.\d+)?\s*%', metric)]
                    if vals:
                        # SEC tables list the current fiscal year first; use
                        # that row's first percentage, not a prior-year max.
                        pct = vals[0]
                    else:
                        nums = re.findall(r'(?<!\d)(100|[1-9]?\d)(?:\.\d+)?(?!\d)', metric)
                        pct = float(nums[0]) if nums else None
                    break
            if pct is not None and pct >= 10:
                cik = next(iter(ciks))
                entity = issuer_by_cik.get(cik, {})
                found.append({'customer_name': label.rstrip(':').strip(),
                              'customer_cik': entity.get('cik') or cik.zfill(10),
                              'customer_ticker': entity.get('ticker') or '',
                              'identity_status': 'listed_name_matched',
                              'disclosed_percent': pct,
                              'evidence_snippet': 'TABLE: ' + label + ' | ' + ' | '.join(' '.join(x) for x in rows[i + 1:i + 4])})
    for pct_match, window in _sentences(text):
        # Generic negative statements such as “no single customer ... 10%”
        # are not named-customer disclosures.
        if re.search(r'\b(?:no|not|none|no single)\s+(?:one\s+)?(?:single\s+)?customer', window, re.I):
            continue
        percent = float(pct_match.group(1))
        if percent < 10:
            continue
        if ANON_RE.search(window):
            continue
        name_candidates = []
        for pattern in CLAIM_PATTERNS:
            name_candidates.extend(m.group('name').strip(' ,.;:') for m in pattern.finditer(window))
        # Only link an issuer name when the filing text explicitly places it
        # in a sales-to/customer claim adjacent to the >=10% disclosure.
        matching = []
        for name in name_candidates:
            ciks = _match_customers(name, aliases)
            if len(ciks) == 1:
                matching.append((name, next(iter(ciks))))
        matched_ciks = {cik for _name, cik in matching}
        if len(matched_ciks) == 1:
            cik = next(iter(matched_ciks))
            entity = issuer_by_cik.get(cik, {})
            found.append({'customer_name': entity.get('name') or '',
                          'customer_cik': entity.get('cik') or cik.zfill(10),
                          'customer_ticker': entity.get('ticker') or '',
                          'identity_status': 'listed_name_matched',
                          'disclosed_percent': percent,
                          'evidence_snippet': window[:800]})
            continue
        # Extract one explicitly capitalized name when a listed name was not
        # resolved. These rows are documented but not eligible for D7 links.
        cap = CAPTURE_RE.search(window)
        if cap or name_candidates:
            name = re.sub(r'\s+', ' ', (cap.group('a') or cap.group('b') if cap else name_candidates[0])).strip(' ,.;:')
            if name and not ANON_RE.search(name) and len(name.split()) <= 10:
                found.append({'customer_name': name, 'customer_cik': '',
                              'customer_ticker': '', 'identity_status': 'named_unmatched',
                              'disclosed_percent': percent,
                              'evidence_snippet': window[:800]})
        elif len(matched_ciks) > 1:
            found.append({'customer_name': '[ambiguous listed-entity match]',
                          'customer_cik': '', 'customer_ticker': '',
                          'identity_status': 'ambiguous', 'disclosed_percent': percent,
                          'evidence_snippet': window[:800]})
    # One disclosure pair is enough per filing, even if repeated in the note.
    unique = {}
    for item in found:
        key = (item['customer_cik'], item['customer_name'].lower(), item['identity_status'])
        unique.setdefault(key, item)
    return list(unique.values())


def _get_filings(session, cache_dir, cik):
    cache_path = cache_dir / 'submissions' / f'CIK{cik}.json'
    obj = _json_get(session, SUBMISSIONS_URL.format(cik=cik), cache_path)
    recent = obj.get('filings', {}).get('recent', {})
    keys = ['form', 'filingDate', 'reportDate', 'accessionNumber', 'primaryDocument']
    n = min((len(recent.get(k, [])) for k in keys), default=0)
    out = []
    for i in range(n):
        form = recent['form'][i]
        filing_date = recent['filingDate'][i]
        if form not in ('10-K', '10-K/A') or not FILINGS_START <= filing_date <= FILINGS_END:
            continue
        out.append({'form': form, 'filing_date': filing_date,
                    'report_date': recent['reportDate'][i],
                    'accession': recent['accessionNumber'][i],
                    'document': recent['primaryDocument'][i]})
    return out


def _load_sic_coverage():
    if not SIC.is_file():
        return {}
    coverage = defaultdict(set)
    with SIC.open('r', encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            available = str(row.get('effective_from') or row.get('available_date') or row.get('filing_date') or '')[:10]
            # The date guard precedes reading issuer or code, keeping all
            # roster/SIC use within development dates.
            if not '2020-06-01' <= available <= DEV_END:
                continue
            ticker = str(row.get('ticker') or row.get('asset') or '').upper()
            sic = str(row.get('sic') or '').strip()
            if ticker and sic:
                coverage[ticker].add((available, sic))
    return coverage


def _asof_sic(ticker, day, sic_panel):
    available = sorted((d, sic) for d, sic in sic_panel.get(ticker, set()) if d <= day)
    return available[-1][1][:2] if available else ''


def _event_input_coverage(earnings_rows, links, sic_panel):
    linked_by_cik = defaultdict(list)
    for link in links:
        linked_by_cik[link['customer_cik'].lstrip('0')].append(link)
    dedup = {}
    for row in earnings_rows:
        cik = str(row.get('cik') or '').lstrip('0')
        filing_day = str(row.get('filing_date') or '')[:10]
        if cik not in linked_by_cik or not DEV_START <= filing_day <= DEV_END:
            continue
        if '2.02' not in [x.strip() for x in str(row.get('items') or '').split(',')]:
            continue
        response_day = next_session(filing_day)  # prereg's unknown-release-time rule
        ticker = str(row.get('ticker') or '').upper()
        if response_day > DEV_END or ticker not in dow_roster(response_day):
            continue
        key = (cik, filing_day)
        old = dedup.get(key)
        if old is None or (str(old.get('form','')).endswith('/A') and not str(row.get('form','')).endswith('/A')):
            dedup[key] = {**row, '_response_date': response_day}
    by_date = defaultdict(list)
    for row in dedup.values():
        by_date[row['_response_date']].append(row)

    coverage = []
    for response_day, events in sorted(by_date.items()):
        customers = sorted({str(e['ticker']).upper() for e in events})
        recipient_set = set()
        shuffle_ok = True
        missing_sic = set()
        for event in events:
            customer = str(event['ticker']).upper()
            cik = str(event['cik']).lstrip('0')
            suppliers = sorted({link['supplier_ticker'] for link in linked_by_cik[cik]
                if link['first_usable_session'] <= response_day
                and link['supplier_ticker'] != customer
                and link['supplier_ticker'] in dow_roster(response_day)})
            recipient_set.update(suppliers)
            groups = defaultdict(set)
            for supplier in suppliers:
                code = _asof_sic(supplier, response_day, sic_panel)
                if not code:
                    missing_sic.add(supplier)
                else:
                    groups[code].add(supplier)
            if not suppliers or any(not _asof_sic(s, response_day, sic_panel) for s in suppliers):
                shuffle_ok = False
            for code, observed in groups.items():
                pool = {ticker for ticker in dow_roster(response_day)
                        if _asof_sic(ticker, response_day, sic_panel) == code}
                alternates = pool - observed - {customer}
                if len(alternates) < len(observed):
                    shuffle_ok = False
        if len(recipient_set) >= 3:
            coverage.append({'response_date': response_day, 'event_customers': len(customers),
                'active_dow_supplier_recipients': len(recipient_set),
                'passes_30date_recipient_rule': True, 'missing_sic_supplier_count': len(missing_sic),
                'all_customer_sic_groups_shuffleable': shuffle_ok,
                'event_ids': ';'.join(sorted(str(e.get('accession_number') or '') for e in events))})
    return coverage, len(dedup)


def _write_csv(path, rows, fields):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def build(download=True):
    cache_dir = OUT / 'sec_cache'
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT, 'Accept-Encoding': 'gzip, deflate'})
    earnings_rows = _load_earnings()
    by_ticker, by_cik = _issuer_index(session, cache_dir)
    customers, aliases = _listed_customer_map(earnings_rows, by_ticker, by_cik)
    issuer_by_cik = {cik: {**rec, 'name': next(iter(rec['names']), '')}
                     for cik, rec in customers.items()}
    # Add SEC ticker-directory legal names for listed issuers outside the
    # supplied event clock; they can be recorded but are not tradable here.
    for ticker, rec in by_ticker.items():
        issuer_by_cik.setdefault(rec['cik'].lstrip('0'), rec)
        for alias in _name_aliases(rec['name']):
            aliases[alias].append(rec['cik'].lstrip('0'))

    supplier_tickers = sorted(DEV_TICKERS)
    suppliers = {}
    for ticker in supplier_tickers:
        record = by_ticker.get(ticker)
        if not record:
            cik = CIK_OVERRIDES.get(ticker)
            if cik:
                record = {'cik': cik, 'name': 'Walgreens Boots Alliance, Inc.', 'ticker': ticker}
        if not record:
            # Use the historical L4 SEC CIK mapping when no current ticker row
            # exists (e.g., delisted point-in-time Dow names).
            rows = [r for r in earnings_rows if r['ticker'].upper() == ticker]
            if rows:
                record = {'cik': rows[-1]['cik'].zfill(10), 'name': rows[-1]['company_name'], 'ticker': ticker}
        if record:
            suppliers[ticker] = record

    candidate_rows = []
    failures = []
    total = sum(1 for _ in suppliers)
    for sn, (ticker, supplier) in enumerate(suppliers.items(), 1):
        cik = str(supplier['cik']).zfill(10)
        try:
            filings = _get_filings(session, cache_dir, cik)
        except Exception as exc:
            failures.append({'supplier_ticker': ticker, 'supplier_cik': cik,
                             'error': f'submissions: {type(exc).__name__}: {exc}'})
            continue
        for filing in filings:
            accession_compact = filing['accession'].replace('-', '')
            doc_path = cache_dir / 'filings' / accession_compact / Path(filing['document']).name
            url = ARCHIVE_URL.format(cik=str(int(cik)), accession=accession_compact,
                                     document=filing['document'])
            try:
                if not download and not doc_path.is_file():
                    failures.append({'supplier_ticker': ticker, 'supplier_cik': cik,
                                     'error': f'cache missing filing {filing["accession"]}'})
                    continue
                raw = _text_get(session, url, doc_path)
                disclosures = extract_disclosures(raw, aliases, issuer_by_cik)
            except Exception as exc:
                failures.append({'supplier_ticker': ticker, 'supplier_cik': cik,
                                 'accession': filing['accession'],
                                 'error': f'{type(exc).__name__}: {exc}'})
                continue
            for disclosure in disclosures:
                candidate_rows.append({
                    **disclosure, 'supplier_ticker': ticker, 'supplier_cik': cik,
                    'source_form': filing['form'], 'source_accession': filing['accession'],
                    'report_date': filing['report_date'], 'filing_date': filing['filing_date'],
                    'source_url': url,
                })
        print(f'[{sn}/{total}] {ticker}: {len(filings)} 10-K filings; candidates so far {len(candidate_rows)}')

    sessions = next_session
    clock_by_cik = defaultdict(list)
    for event in earnings_rows:
        cik = str(event['cik']).lstrip('0')
        if DEV_START <= event.get('filing_date', '') <= DEV_END and '2.02' in event.get('items', '').split(','):
            clock_by_cik[cik].append(event)

    links = []
    pair_keys = set()
    for row in candidate_rows:
        if row['identity_status'] != 'listed_name_matched' or not row['customer_cik']:
            continue
        if row['customer_cik'].lstrip('0') == row['supplier_cik'].lstrip('0'):
            continue
        # Only suppliers that appear in the D7 point-in-time Dow universe are
        # retained. The filing may predate sample start; link use is bounded by
        # the subsequent first-session availability and carried forward.
        if row['supplier_ticker'] not in DEV_TICKERS:
            continue
        first = sessions(row['filing_date'])
        memberships = dow_intervals(row['supplier_ticker'])
        overlap = [(max(a, DEV_START), min(b, DEV_END)) for a, b in memberships
                   if max(a, DEV_START) <= min(b, DEV_END)]
        if not overlap:
            continue
        event_rows = clock_by_cik.get(row['customer_cik'].lstrip('0'), [])
        pair = (row['customer_cik'].lstrip('0'), row['supplier_cik'].lstrip('0'))
        pair_keys.add(pair)
        links.append({
            'customer_cik': row['customer_cik'].zfill(10),
            'customer_ticker': row['customer_ticker'],
            'customer_name': row['customer_name'],
            'supplier_cik': row['supplier_cik'].zfill(10),
            'supplier_ticker': row['supplier_ticker'],
            'source_form': row['source_form'], 'source_accession': row['source_accession'],
            'report_date': row['report_date'], 'filing_date': row['filing_date'],
            'first_usable_session': first, 'valid_from': first, 'valid_to': '',
            'supplier_dow_valid_from': overlap[0][0], 'supplier_dow_valid_to': overlap[-1][1],
            'source_url': row['source_url'], 'disclosed_customer_share_percent': row['disclosed_percent'],
            'identity_status': row['identity_status'],
            'earnings_clock_filings_development': len(event_rows),
            'customer_has_earnings_clock': bool(event_rows),
            'valid_for_development': bool(first <= DEV_END),
            'explicit_termination_disclosure': False,
        })

    # Event counts are metadata only. With no explicit release timestamp from
    # a reviewed 8-K exhibit, apply the preregistered next-session fallback.
    linked_ciks = {x['customer_cik'].lstrip('0') for x in links}
    event_counts = defaultdict(set)
    dow_event_counts = defaultdict(set)
    for row in earnings_rows:
        cik = str(row['cik']).lstrip('0')
        day = str(row.get('filing_date') or '')[:10]
        if cik not in linked_ciks or not DEV_START <= day <= DEV_END:
            continue
        if '2.02' not in [x.strip() for x in row.get('items', '').split(',')]:
            continue
        response_day = next_session(day)
        event_key = (cik, day)
        event_counts[day[:4]].add(event_key)
        if response_day <= DEV_END and row['ticker'].upper() in dow_roster(response_day):
            dow_event_counts[day[:4]].add(event_key)

    tradable_pairs = {(x['customer_cik'], x['supplier_cik']) for x in links if x['customer_has_earnings_clock']}
    distinct_pairs = {(x['customer_cik'], x['supplier_cik']) for x in links}
    dow_pairs = set()
    for x in links:
        customer, supplier = x['customer_ticker'], x['supplier_ticker']
        public_from = max(DEV_START, x['first_usable_session'])
        for ca, cb in dow_intervals(customer):
            for sa, sb in dow_intervals(supplier):
                if max(public_from, ca, sa) <= min(DEV_END, cb, sb):
                    dow_pairs.add((x['customer_cik'], x['supplier_cik']))
                    break
            if (x['customer_cik'], x['supplier_cik']) in dow_pairs:
                break
    matched_event_customers = {x['customer_cik'] for x in links if x['customer_has_earnings_clock']}
    sic_panel = _load_sic_coverage()
    event_coverage, dedup_event_count = _event_input_coverage(earnings_rows, links, sic_panel)
    event_dates = {x['response_date'] for x in event_coverage}
    dated_events = sum(len(v) for v in dow_event_counts.values())
    shuffleable_dates = sum(x['all_customer_sic_groups_shuffleable'] for x in event_coverage)

    # Count years of Item 2.02 clock filings from matched named customers.
    years = [str(y) for y in range(2020, 2027)]
    events_by_year = [{'year': y, 'linked_listed_customer_events': len(event_counts[y]),
                       'linked_Dow_customer_events': len(dow_event_counts[y])} for y in years]
    _write_csv(OUT / 'LINKS.csv', links, [
        'customer_cik','customer_ticker','customer_name','supplier_cik','supplier_ticker',
        'source_form','source_accession','report_date','filing_date','first_usable_session',
        'valid_from','valid_to','source_url','disclosed_customer_share_percent','identity_status',
        'earnings_clock_filings_development','customer_has_earnings_clock','valid_for_development',
        'explicit_termination_disclosure','supplier_dow_valid_from','supplier_dow_valid_to'])
    _write_csv(OUT / 'LINK_CANDIDATES.csv', candidate_rows,
               ['customer_cik','customer_ticker','customer_name','identity_status','disclosed_percent',
                'evidence_snippet','supplier_cik','supplier_ticker','source_form','source_accession',
                'report_date','filing_date','source_url'])
    _write_csv(OUT / 'SEC_FETCH_ERRORS.csv', failures, ['supplier_ticker','supplier_cik','accession','error'])
    _write_csv(OUT / 'EVENT_COVERAGE.csv', event_coverage,
               ['response_date','event_customers','active_dow_supplier_recipients',
                'passes_30date_recipient_rule','missing_sic_supplier_count',
                'all_customer_sic_groups_shuffleable','event_ids'])

    with (OUT / 'LINK_QA.md').open('w', encoding='utf-8') as f:
        f.write('# D7 SEC customer-link input QA\n\n')
        f.write(f'Sample: SEC 10-K filings from {FILINGS_START} through {FILINGS_END}; link-use window {DEV_START} through {DEV_END}. This is an input-only build: no prices, returns, outcomes, or holdout data were read. SEC document bytes were downloaded from the public EDGAR Archives; company CIK/ticker references use the SEC company ticker directory and the supplied earnings clock.\n\n')
        f.write('## Extraction rules and limitations\n\n')
        f.write('The builder reads 10-K/10-K/A primary filing documents from SEC EDGAR. It accepts an explicitly named entity in either (a) a customer/sales sentence with an adjacent ≥10% claim or (b) a table where a uniquely matched company-name row is followed by an explicit percent-of-revenue row; for tables the first value is the current fiscal year. Anonymized labels and generic statements about “these customers” are not link identities. Unmatched or ambiguous candidates remain in `LINK_CANDIDATES.csv` for audit and are excluded from `LINKS.csv`; no SIC or industry relationship is inferred. Filing disclosures are usable from the first XNYS session strictly after the filing date. A later omission does not terminate a relationship; `valid_to` remains open because no explicit termination disclosure was machine-confirmed. Each link row retains its source accession, filing date and direct SEC URL. This conservative text parser is not a legal/accounting determination; source snippets need coordinator review before freeze.\n\n')
        f.write('## Counts\n\n')
        f.write(f'- Extracted disclosure candidates (including unmatched/ambiguous audit rows): {len(candidate_rows):,}.\n')
        f.write(f'- Eligible listed-name link rows in `LINKS.csv`: {len(links):,}.\n')
        f.write(f'- Distinct named listed-customer/supplier pairs in `LINKS.csv`: {len(distinct_pairs):,}.\n')
        f.write(f'- Distinct pairs where both customer and supplier are point-in-time Dow members on an overlapping development date, with the link already public: {len(dow_pairs):,}.\n')
        f.write(f'- Distinct directed pairs whose listed customer has at least one development earnings-clock filing: {len(tradable_pairs):,}.\n')
        f.write(f'- Unique matched linked customers with a clock: {len(matched_event_customers):,}.\n')
        f.write(f'- Matched, issuer-day-deduplicated 8-K Item 2.02 filings: {dedup_event_count:,}; response dates under the preregistered unknown-time fallback with at least three active linked Dow recipients: {len(event_coverage):,}; shuffleable dates: {shuffleable_dates}/{len(event_coverage)}. The clock has no explicit earnings-release timestamp, so filing date is used only for the preregistered next-session fallback; the linked 8-K exhibits remain unaudited.\n')
        f.write(f'- SEC fetch/parse errors: {len(failures):,}.\n\n')
        f.write('| Year | Linked listed-customer Item 2.02 filings | Linked Dow-customer Item 2.02 filings |\n|---:|---:|---:|\n')
        for row in events_by_year:
            f.write(f"| {row['year']} | {row['linked_listed_customer_events']} | {row['linked_Dow_customer_events']} |\n")
        f.write('\n## Frozen feasibility thresholds and verdict\n\n')
        f.write('| Gate | Required | Observed | Status |\n|---|---:|---:|---|\n')
        f.write(f"| Distinct event-response dates with ≥3 active linked Dow recipients | 30 | {len(event_coverage)} | {'PASS' if len(event_coverage) >= 30 else 'FAIL'} |\n")
        f.write(f"| Distinct directed Dow customer-supplier pairs | 10 | {len(dow_pairs)} | {'PASS' if len(dow_pairs) >= 10 else 'FAIL'} |\n")
        f.write(f"| Eligible alternate suppliers within PIT two-digit SIC for every qualifying date | 100% | {shuffleable_dates}/{len(event_coverage)} | {'PASS' if event_coverage and shuffleable_dates == len(event_coverage) else 'FAIL'} |\n\n")
        failed = len(event_coverage) < 30 or len(dow_pairs) < 10 or not event_coverage or shuffleable_dates != len(event_coverage)
        f.write('Feasibility verdict: **' + ('INFEASIBLE — fixed metadata gate failed' if failed else 'INPUT GATE PASSED; coordinator must audit sampled source filings before freeze') + '**. No outcomes, returns, or placebo draws were calculated.\n\n')
        f.write('## Audit files\n\n')
        f.write('- `LINKS.csv`: source rows with listed customer identity matches.\n- `LINK_CANDIDATES.csv`: all parser candidates with snippet evidence, including unresolved names for manual audit.\n- `EVENT_COVERAGE.csv`: metadata-only event-date, Dow-recipient, and SIC-shuffle feasibility counts.\n- `SEC_FETCH_ERRORS.csv`: missing metadata/document downloads.\n- `sec_cache/`: downloaded SEC submissions and filing documents, retained for reproducibility.\n')
    print(f'Wrote {len(links)} eligible link rows, {len(distinct_pairs)} directed pairs, {len(tradable_pairs)} tradable pairs, {dated_events} linked Dow events; errors={len(failures)}')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--offline', action='store_true', help='rebuild only from the existing SEC cache')
    args = ap.parse_args(argv)
    build(download=not args.offline)


if __name__ == '__main__':
    main()
