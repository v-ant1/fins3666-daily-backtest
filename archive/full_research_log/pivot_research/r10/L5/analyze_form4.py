from __future__ import annotations
import json, math, os, time
from collections import Counter
from datetime import date, datetime, time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
from dotenv import dotenv_values
from scipy.stats import t as student_t, norm

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DATA = ROOT / 'r6_data' / 'insider' / 'form4_dev.parquet'
PANEL = ROOT / 'r9' / 'data' / 'J2_DEV_FROM_20201127.npz'
ENV = ROOT.parent / '.env'
DEV_START, DEV_END = date(2020, 11, 27), date(2026, 10, 30)
NY, UTC = ZoneInfo('America/New_York'), ZoneInfo('UTC')
SEC_UA = 'FINS3666 SEC metadata research contact research@example.edu'
ALPACA_ROOT = 'https://data.alpaca.markets/v2/stocks'


def owners(value):
    try: return json.loads(value) if value else []
    except Exception: return []


def get_acceptance(records):
    # One public SEC submissions JSON GET per issuer CIK, at 5 requests/sec.
    cik_list = sorted(records.issuer_cik.astype(str).str.zfill(10).unique())
    ses = requests.Session()
    ses.headers.update({'User-Agent': SEC_UA, 'Accept-Encoding': 'gzip, deflate'})
    lookup = {}
    failures = Counter()
    for i, cik in enumerate(cik_list, 1):
        url = f'https://data.sec.gov/submissions/CIK{cik}.json'
        try:
            r = ses.get(url, timeout=45)
            if r.status_code != 200:
                failures[f'HTTP_{r.status_code}'] += 1
                time.sleep(.2); continue
            js = r.json().get('filings', {}).get('recent', {})
            accs = js.get('accessionNumber', [])
            times = js.get('acceptanceDateTime', [])
            forms = js.get('form', [])
            for acc, stamp, form in zip(accs, times, forms):
                if form in ('4', '4/A') and stamp:
                    lookup[(cik, acc)] = stamp
        except Exception as exc:
            failures[type(exc).__name__] += 1
        time.sleep(.2)
        if i % 100 == 0:
            print(f'SEC metadata CIKs fetched: {i}/{len(cik_list)}')
    return lookup, failures


def alpaca_headers():
    vals = dotenv_values(ENV)
    key, secret = vals.get('ALPACA_API_KEY'), vals.get('ALPACA_SECRET_KEY')
    if not key or not secret:
        return None
    return {'APCA-API-KEY-ID': str(key), 'APCA-API-SECRET-KEY': str(secret), 'Accept': 'application/json'}


def fetch_missing(ticker, start, end, headers, session):
    aliases = {'BF-B':'BF.B', 'BRK-B':'BRK.B'}
    symbol = aliases.get(ticker.upper(), ticker.upper())
    params = {'timeframe':'1Day', 'start':f'{start.isoformat()}T00:00:00Z',
              'end':f'{end.isoformat()}T23:59:59Z', 'feed':'sip',
              'adjustment':'all', 'limit':1000, 'sort':'asc'}
    bars, token = {}, None
    for _ in range(20):
        q = dict(params)
        if token: q['page_token'] = token
        r = session.get(f'{ALPACA_ROOT}/{symbol}/bars', params=q, headers=headers, timeout=60)
        if r.status_code == 429:
            time.sleep(2); continue
        if not r.ok:
            return {}, f'HTTP_{r.status_code}'
        payload = r.json()
        for b in payload.get('bars', []):
            d = datetime.fromisoformat(b['t'].replace('Z', '+00:00')).astimezone(NY).date()
            if DEV_START <= d <= DEV_END:
                bars[d] = (float(b['o']), float(b['c']))
        token = payload.get('next_page_token')
        if not token: return bars, None
    return {}, 'pagination_limit'


def main():
    # Predicate pushdown keeps pre-development filing/transaction rows unread.
    df = pd.read_parquet(DATA, filters=[
        ('transaction_date', '>=', pd.Timestamp(DEV_START)),
        ('transaction_date', '<=', pd.Timestamp(DEV_END)),
        ('filing_date', '>=', pd.Timestamp(DEV_START)),
        ('filing_date', '<=', pd.Timestamp(DEV_END)),
    ])
    df['transaction_date'] = pd.to_datetime(df.transaction_date).dt.date
    df['filing_date'] = pd.to_datetime(df.filing_date).dt.date
    df = df[df.transaction_date.between(DEV_START, DEV_END) & df.filing_date.between(DEV_START, DEV_END)].copy()
    df = df[df.transaction_code.isin(['P','S'])].copy()
    df['owners'] = df.reporting_owners_json.map(owners)
    df['officer_director_owners'] = df.owners.map(lambda xs: [str(x.get('owner_cik','')).zfill(10) for x in xs if x.get('owner_cik') and ('officer' in str(x.get('role','')).lower() or 'director' in str(x.get('role','')).lower())])
    df = df[df.officer_director_owners.map(bool)].copy()
    # History from non-derivative purchases/sales observed for S&P PIT issuers only.
    # All three prior calendar years must be fully represented; hence trade date >= 2024-01-01.
    history = set()
    for row in df.itertuples():
        for owner in set(row.officer_director_owners):
            history.add((owner, row.transaction_date.year, row.transaction_date.month))
    p = df[(df.transaction_code == 'P') & (df.transaction_date >= date(2024,1,1))].copy()
    p['eligible_owner_ciks'] = p.apply(lambda r: [o for o in set(r.officer_director_owners)
        if not all((o, r.transaction_date.year-y, r.transaction_date.month) in history for y in (1,2,3))], axis=1)
    p = p[p.eligible_owner_ciks.map(bool)].copy()

    acceptance, sec_failures = get_acceptance(p)
    p['acceptance_utc'] = [acceptance.get((str(r.issuer_cik).zfill(10), str(r.accession_number)), '') for r in p.itertuples()]
    p = p[p.acceptance_utc.ne('')].copy()
    p['acceptance_et'] = pd.to_datetime(p.acceptance_utc, utc=True).dt.tz_convert('America/New_York')
    p['after_close'] = p.acceptance_et.map(lambda x: x.time() > dtime(16,0))
    p['acceptance_day'] = p.acceptance_et.dt.date
    p['issuer_day'] = p.issuer_cik.astype(str).str.zfill(10) + ':' + p.acceptance_day.astype(str)
    # Store unique eligible issuer-day events; multiple transactions/accessions aggregate to one event.
    ev = p.sort_values(['acceptance_et','accession_number']).groupby('issuer_day', as_index=False).agg(
        issuer_cik=('issuer_cik','first'), ticker=('ticker','first'), transaction_date=('transaction_date','first'),
        acceptance_et=('acceptance_et','min'),
        transactions=('transaction_id','nunique'), owners=('eligible_owner_ciks', lambda s: sorted(set(o for xs in s for o in xs))))
    ev['after_close'] = ev.acceptance_et.map(lambda x: x.time() > dtime(16,0))

    with np.load(PANEL, allow_pickle=False) as z:
        dates = [date.fromisoformat(x) for x in z['sp500_dates'].tolist()]
        assets = [str(x) for x in z['sp500_assets'].tolist()]
        roster = z['sp500_roster'].astype(bool)
        ao, ac = z['sp500_adjusted_open'], z['sp500_adjusted_close']
    d2i = {d:i for i,d in enumerate(dates)}
    caldates = [d for d in dates if DEV_START <= d <= DEV_END]
    # Backfill missing NPZ prices only through Alpaca SIP GET adjustment=all.
    missing_symbols = [assets[i] for i in range(len(assets)) if np.any(roster[i] & (~np.isfinite(ao[i]) | ~np.isfinite(ac[i])))]
    extra = {}
    extra_errors = {}
    headers = alpaca_headers()
    if missing_symbols and headers:
        sess = requests.Session()
        for j, ticker in enumerate(missing_symbols, 1):
            bars, err = fetch_missing(ticker, DEV_START, DEV_END, headers, sess)
            if err: extra_errors[ticker] = err
            else: extra[ticker] = bars
            time.sleep(.34)
            if j % 10 == 0: print(f'Alpaca missing-symbol GETs: {j}/{len(missing_symbols)}')
    elif missing_symbols:
        extra_errors = {x:'dotenv credential pair unavailable' for x in missing_symbols}

    # Build aligned prices; NPZ prices are the project SIP adjustment=all panel.
    ticker_i = {t:i for i,t in enumerate(assets)}
    for ticker, bars in extra.items():
        if ticker not in ticker_i: continue
        i = ticker_i[ticker]
        for d,(o,c) in bars.items():
            if d in d2i:
                j = d2i[d]
                if not np.isfinite(ao[i,j]): ao[i,j] = o
                if not np.isfinite(ac[i,j]): ac[i,j] = c

    results, exclusions = [], Counter()
    for r in ev.itertuples():
        accept = r.acceptance_et.to_pydatetime()
        # Entry is first panel session strictly after acceptance date, with one extra session after 16:00 ET.
        entry_candidates = [d for d in caldates if d > accept.date()]
        if r.after_close:
            entry_candidates = entry_candidates[1:]
        if not entry_candidates:
            exclusions['no_entry_session'] += 1; continue
        entry = entry_candidates[0]
        i0 = d2i[entry]; i1 = i0 + 19
        if i1 >= len(dates) or dates[i1] > DEV_END:
            exclusions['incomplete_20_session_window'] += 1; continue
        if i0 < d2i[DEV_START]:
            exclusions['entry_before_boundary'] += 1; continue
        si = ticker_i.get(str(r.ticker))
        acceptance_i = d2i.get(accept.date())
        if si is None or acceptance_i is None or not roster[si,acceptance_i] or not (roster[si,i0] and np.isfinite(ao[si,i0]) and ao[si,i0] > 0 and np.isfinite(ac[si,i1])):
            exclusions['missing_stock_price_or_not_PIT_member'] += 1; continue
        stock_ret = float(ac[si,i1] / ao[si,i0] - 1)
        daily_ew, bad = [], False
        for j in range(i0, i1+1):
            if j == i0:
                valid = roster[:,j] & np.isfinite(ao[:,j]) & np.isfinite(ac[:,j]) & (ao[:,j] > 0)
                vals = ac[valid,j] / ao[valid,j] - 1
            else:
                valid = roster[:,j-1] & roster[:,j] & np.isfinite(ac[:,j-1]) & np.isfinite(ac[:,j]) & (ac[:,j-1] > 0)
                vals = ac[valid,j] / ac[valid,j-1] - 1
            vals = vals[np.isfinite(vals)]
            if not len(vals): bad=True; break
            daily_ew.append(float(vals.mean()))
        if bad:
            exclusions['missing_benchmark_session'] += 1; continue
        benchmark_ret = float(np.prod(1+np.asarray(daily_ew)) - 1)
        gross = stock_ret - benchmark_ret
        results.append({'issuer_day':r.issuer_day,'issuer_cik':r.issuer_cik,'ticker':r.ticker,
            'transaction_date':r.transaction_date.isoformat(),'acceptance_et':accept.isoformat(),
            'entry_date':entry.isoformat(),'exit_date':dates[i1].isoformat(),'transactions':int(r.transactions),
            'stock_return':stock_ret,'benchmark_return':benchmark_ret,'gross_car':gross,
            'net_5bp':gross-.001,'net_10bp':gross-.002,'net_20bp':gross-.004})
    out = pd.DataFrame(results)
    out.to_csv(OUT/'event_results.csv', index=False)
    pd.DataFrame([{'ticker':k,'reason':v} for k,v in extra_errors.items()]).to_csv(OUT/'missing_price_get_errors.csv',index=False)

    def summary(col):
        x = out[col].to_numpy(float)
        n=len(x)
        mean=float(x.mean()) if n else math.nan
        sd=float(x.std(ddof=1)) if n>1 else math.nan
        med=float(np.median(x)) if n else math.nan
        if n>1:
            half=float(student_t.ppf(.975,n-1)*sd/math.sqrt(n)); ci=(mean-half,mean+half)
        else: ci=(math.nan,math.nan)
        return {'N':n,'mean':mean,'sd':sd,'median':med,'ci95':ci}
    primary=summary('net_10bp')
    annual = out.assign(year=pd.to_datetime(out.entry_date).dt.year).groupby('year').agg(
        N=('net_10bp','size'), mean_net_car=('net_10bp','mean'), sd_net_car=('net_10bp','std'), median_net_car=('net_10bp','median')).reset_index()
    annual.to_csv(OUT/'annual_results.csv',index=False)
    clusters = out.groupby('entry_date').size() if len(out) else pd.Series(dtype=int)
    n_holdout=int(round(len(out) / ((DEV_END-DEV_START).days/365.2425) * 6))
    if n_holdout > 0 and primary['sd'] > 0:
        mde=2.4865*primary['sd']/math.sqrt(n_holdout)
        ppass=float(norm.cdf((.5*primary['mean'])/(primary['sd']/math.sqrt(n_holdout))-1.6449))
    else: mde,ppass=math.nan,math.nan
    # SEC holdout archive volume uses only HEAD metadata already in the QA manifest.
    avail=pd.read_csv(ROOT/'r6_data'/'insider'/'archive_availability.csv')
    hold=avail[avail.quarter.astype(str).str.match(r'^(2010|2011|2012|2013|2014|2015)Q[1-4]$')]
    report = {
      'source_rows_in_dev_window':int(len(df)), 'purchases_officer_director':int(len(p)),
      'eligible_issuer_days_before_acceptance_match':int(len(set(p.issuer_day))),
      'accepted_transactions_matched':int(len(p)), 'event_count_pricing_eligible':int(len(out)),
      'acceptance_timestamp_match_rate':float(p.acceptance_et.notna().mean()) if len(p) else 0,
      'sec_metadata_cik_count':int(p.issuer_cik.nunique()), 'sec_metadata_errors':dict(sec_failures),
      'routine_fallback_excluded_early_history':int((df.transaction_date < date(2024,1,1)).sum()),
      'exclusions':dict(exclusions), 'missing_price_symbols':missing_symbols,
      'missing_price_errors':extra_errors, 'primary_net_10bp':primary,
      'sensitivity_5bp':summary('net_5bp'), 'sensitivity_20bp':summary('net_20bp'),
      'annual':annual.to_dict(orient='records'), 'event_entry_dates':int(len(clusters)),
      'events_per_entry_date_mean':float(clusters.mean()) if len(clusters) else math.nan,
      'events_per_entry_date_median':float(clusters.median()) if len(clusters) else math.nan,
      'max_events_per_entry_date':int(clusters.max()) if len(clusters) else 0,
      'entry_dates_with_multiple_events':int((clusters>1).sum()),
      'dev_years_calendar':(DEV_END-DEV_START).days/365.2425, 'projected_2010_2015_N':n_holdout,
      'mde':mde, 'pass_probability_50pct_haircut':ppass,
      'holdout_sec_archives':int(len(hold)), 'holdout_sec_zip_total_bytes':int(hold.content_length_bytes.sum()),
      'holdout_sec_avg_zip_bytes':float(hold.content_length_bytes.mean()) if len(hold) else math.nan,
    }
    (OUT/'analysis_summary.json').write_text(json.dumps(report,indent=2,default=str),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('missing_price_symbols','annual','sec_metadata_errors','missing_price_errors')},indent=2,default=str))

if __name__=='__main__': main()

