"""L1D continuation: Tiingo metadata and adjusted-price date coverage only."""
import csv, datetime as dt, difflib, json, time, urllib.parse
from pathlib import Path
import pandas_market_calendars as mcal
import requests
from dotenv import dotenv_values

BASE = Path(__file__).resolve().parent
L1C = BASE.parent / 'L1C'
WINDOWS = L1C / 'pit_membership_windows.csv'
L1C_ROWS = L1C / 'coverage_rows.csv'
ROWS = BASE / 'coverage_rows_cont.csv'
ENV = Path(r'C:/Users/musta/Desktop/UNSW/SSI/FINS3666/A2/.env')
TARGET_START = dt.date(2010, 1, 1)
TARGET_END_EXCLUSIVE = dt.date(2016, 1, 1)
MIN_GAP = 72.5
REQUEST_BUDGET = 146  # 73 metadata + 73 prices calls; <=50 requests/hour when spaced.
ELAPSED_BUDGET = 2 * 60 * 60 + 58 * 60
FIELDS = ['source_ticker','request_ticker','window_start','window_end_exclusive','expected_sessions','covered_sessions','missing_sessions','metadata_status','name_status','startDate','endDate','prices_status','date_rows','error_type','checked_at_utc']


def norm(s):
    return ''.join(c.lower() for c in (s or '') if c.isalnum())

def name_match(expected, actual):
    a, b = norm(expected), norm(actual)
    return bool(b) and (a == b or a in b or b in a or difflib.SequenceMatcher(None, a, b).ratio() >= .82)

def sessions_for(start, end_exclusive, sessions):
    a, b = dt.date.fromisoformat(start), dt.date.fromisoformat(end_exclusive)
    return {d for d in sessions if a <= d < b}

def existing_symbols(path):
    if not path.exists(): return set()
    with path.open(newline='', encoding='utf-8-sig') as f:
        return {r['source_ticker'] for r in csv.DictReader(f) if r.get('source_ticker')}

def main():
    vals = dotenv_values(ENV)
    if not vals.get('KEY'):
        raise RuntimeError('Configured dotenv key KEY is unavailable')
    with WINDOWS.open(newline='', encoding='utf-8-sig') as f:
        windows = list(csv.DictReader(f))
    by = {}
    for w in windows: by.setdefault(w['ticker'], []).append(w)
    already = existing_symbols(L1C_ROWS) | existing_symbols(ROWS)
    # Respect the L1C roster universe; malformed checkpoint-only symbols consume quota but are not retried.
    pending = [t for t in sorted(by) if t not in already]
    request_limit = min(len(pending), REQUEST_BUDGET // 2)
    pending = pending[:request_limit]
    calendar = mcal.get_calendar('NYSE')
    schedule = calendar.schedule(start_date=TARGET_START.isoformat(), end_date=(TARGET_END_EXCLUSIVE-dt.timedelta(days=1)).isoformat())
    market_sessions = {x.date() for x in schedule.index}
    session = requests.Session()
    last_call = None
    call_count = 0
    started = time.monotonic()
    is_new = not ROWS.exists()
    for ticker in pending:
        if call_count + 2 > REQUEST_BUDGET or time.monotonic() - started >= ELAPSED_BUDGET: break
        request_ticker = ticker.replace('.', '-')
        urlbase = 'https://api.tiingo.com/tiingo/daily/' + urllib.parse.quote(request_ticker, safe='-')
        meta = {'status':'not_requested'}
        price_dates = set()
        prices_status = 'not_requested'
        errors = []
        for kind in ('metadata','prices'):
            if call_count >= REQUEST_BUDGET or time.monotonic() - started >= ELAPSED_BUDGET: break
            if last_call is not None:
                wait = MIN_GAP - (time.monotonic() - last_call)
                if wait > 0: time.sleep(wait)
            url = urlbase if kind == 'metadata' else urlbase + '/prices'
            params = {'token': vals['KEY']} if kind == 'metadata' else {'token': vals['KEY'], 'startDate':TARGET_START.isoformat(), 'endDate':TARGET_END_EXCLUSIVE.isoformat()}
            if kind == 'prices': params['resampleFreq'] = 'daily'
            last_call = time.monotonic()
            call_count += 1
            try:
                resp = session.get(url, params=params, timeout=40)
                if kind == 'metadata':
                    meta = {'status':str(resp.status_code)}
                    if resp.status_code == 200:
                        obj = resp.json()
                        meta.update({'name':obj.get('name') or '', 'startDate':obj.get('startDate') or '', 'endDate':obj.get('endDate') or ''})
                else:
                    prices_status = str(resp.status_code)
                    if resp.status_code == 200:
                        data = resp.json()
                        # Inspect date fields only; no price, return, volume, or adjustment values are read or retained.
                        price_dates = {dt.date.fromisoformat(str(row['date'])[:10]) for row in data if isinstance(row, dict) and row.get('date')}
                if resp.status_code not in (200,): errors.append('http_'+str(resp.status_code))
            except Exception as exc:
                if kind == 'metadata': meta = {'status':'transport_error'}
                else: prices_status = 'transport_error'
                errors.append(type(exc).__name__)
        meta_name_ok = meta.get('status') == '200' and bool(meta.get('name')) and all(name_match(w['issuer_name'], meta['name']) for w in by[ticker])
        # A single current ticker mapping cannot disambiguate recycled identities; count these windows as unverified.
        recycled = len(by[ticker]) > 1
        out_rows = []
        for w in by[ticker]:
            expected = sessions_for(w['window_start'], w['window_end_exclusive'], market_sessions)
            covered = len(expected & price_dates) if meta_name_ok and not recycled and prices_status == '200' else 0
            out_rows.append({'source_ticker':ticker,'request_ticker':request_ticker,'window_start':w['window_start'],'window_end_exclusive':w['window_end_exclusive'],'expected_sessions':len(expected),'covered_sessions':covered,'missing_sessions':len(expected)-covered,'metadata_status':meta.get('status','not_requested'),'name_status':'match' if meta_name_ok else ('recycled_ambiguous' if recycled else ('name_missing' if meta.get('status')=='200' and not meta.get('name') else 'unverified')),'startDate':meta.get('startDate',''),'endDate':meta.get('endDate',''),'prices_status':prices_status,'date_rows':len(price_dates),'error_type':';'.join(errors),'checked_at_utc':dt.datetime.now(dt.timezone.utc).isoformat()})
        with ROWS.open('a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            if is_new: writer.writeheader(); is_new = False
            writer.writerows(out_rows)
            f.flush()
        print(json.dumps({'symbols_completed':len(existing_symbols(ROWS)),'symbols_target':request_limit,'requests_used':call_count,'metadata_status':meta.get('status'),'prices_status':prices_status,'date_rows':len(price_dates)}, separators=(',',':')), flush=True)
    print(json.dumps({'run_complete':False,'symbols_checkpointed':len(existing_symbols(ROWS)),'requests_this_run':call_count,'elapsed_seconds':int(time.monotonic()-started),'pending_symbols':len(pending),'monthly_quota_prior_unique':120,'monthly_quota_new_cap':380,'rows_file':str(ROWS)}, separators=(',',':')), flush=True)

if __name__ == '__main__': main()
