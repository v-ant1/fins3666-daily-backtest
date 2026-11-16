"""Outcome-blind D7 event/link/SIC feasibility builder.

This script reads metadata only. It never opens daily prices and never computes
an event shock, forward return, IC, regression, or portfolio statistic.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
DATA = ROOT / 'r4_L4' / 'data'
LINKS_DEFAULT = ROOT / 'r5_D7' / 'LINKS.csv'
EARNINGS_DEFAULT = DATA / 'earnings_clock.csv'
SIC_DEFAULT = DATA / 'sic_panel.csv'
START, END = '2020-11-27', '2026-10-30'
SIC_METADATA_START='2020-06-01'
ET = ZoneInfo('America/New_York')

# The same point-in-time Dow roster schedule used by the D7 link builder.
DOW_ROSTERS = [
    ('2020-11-27', 'AAPL AMGN AXP BA CAT CRM CSCO CVX DIS DOW GS HD HON IBM INTC JNJ JPM KO MCD MMM MRK MSFT NKE PG TRV UNH V VZ WBA WMT'.split()),
    ('2024-02-26', 'AAPL AMGN AXP AMZN BA CAT CRM CSCO CVX DIS DOW GS HD HON IBM INTC JNJ JPM KO MCD MMM MRK MSFT NKE PG TRV UNH V VZ WMT'.split()),
    ('2024-11-08', 'AAPL AMGN AXP AMZN BA CAT CRM CSCO CVX DIS GS HD HON IBM JNJ JPM KO MCD MMM MRK MSFT NKE NVDA PG SHW TRV UNH V VZ WMT'.split()),
]
ROSTER_MEMBERS = {d: set(xs) for d, xs in DOW_ROSTERS}
EVENT_FIELDS = ['customer_cik','accession_number','filing_date','acceptance_timestamp_et',
                'acceptance_timestamp_utc','release_timestamp_et','exhibit_source_url',
                'filing_source_url','normalized_release_timestamp_et',
                'normalized_acceptance_timestamp_et','f','a','response_session']

def _read_csv(path):
    with Path(path).open('r',encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def _write_csv(path, rows, fields):
    with Path(path).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader(); w.writerows(rows)

def _date(value):
    try: return dt.date.fromisoformat(str(value)[:10])
    except Exception as exc: raise ValueError(f'invalid ISO date: {value!r}') from exc

def _timestamp(value):
    s=str(value or '').strip()
    if not s: return None
    parsed=dt.datetime.fromisoformat(s.replace('Z','+00:00'))
    if parsed.tzinfo is None: parsed=parsed.replace(tzinfo=ET)
    return parsed.astimezone(ET)

def _iso_et(value): return value.isoformat(timespec='seconds') if value else ''
def _iso_utc(value): return value.astimezone(dt.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z') if value else ''
def _cik(value):
    digits=re.sub(r'\D','',str(value or ''))
    return digits.zfill(10) if digits else ''

def roster_at(day):
    members=set()
    for effective, tickers in DOW_ROSTERS:
        if str(day)>=effective: members=set(tickers)
    return members

def default_sessions():
    """Return XNYS session dates; calendar metadata only, no market observations."""
    import pandas as pd
    from exchange_calendars import get_calendar
    cal=get_calendar('XNYS')
    return [str(x.date()) for x in cal.sessions_in_range(pd.Timestamp('2019-01-01'),pd.Timestamp('2026-12-31'))]

def _next_session_after(day,sessions):
    return next((s for s in sessions if s>str(day)),None)

def _session_after_timestamp(stamp,sessions):
    if stamp is None:return None
    for s in sessions:
        opening=dt.datetime.combine(_date(s),dt.time(9,30),tzinfo=ET)
        if opening>stamp:return s
    return None

def event_clock_row(row, sessions, release_annotation=None):
    filing=str(row.get('filing_date',''))[:10]
    if not filing: raise ValueError('earnings event lacks filing_date')
    f=_next_session_after(filing,sessions)
    ann=release_annotation or {}
    release_raw=str(ann.get('release_timestamp_et') or row.get('release_timestamp_et') or '').strip()
    release=_timestamp(release_raw)
    acceptance=_timestamp(row.get('acceptance_timestamp_et') or row.get('acceptance_timestamp_utc'))
    latest=max((x for x in (release,acceptance) if x is not None),default=None)
    a=_session_after_timestamp(latest,sessions)
    # Frozen exception: unknown exhibit release time means d=f; acceptance is
    # retained for audit but is not substituted for the release timestamp.
    d=(max(a,f) if a and f else f) if release is not None else f
    return {
        'customer_cik':_cik(row.get('cik')),
        'accession_number':str(row.get('accession_number','')).strip(),
        'filing_date':filing,
        'acceptance_timestamp_et':_iso_et(acceptance),
        'acceptance_timestamp_utc':str(row.get('acceptance_timestamp_utc','')).strip() or _iso_utc(acceptance),
        'release_timestamp_et':_iso_et(release),
        'exhibit_source_url':str(ann.get('exhibit_source_url') or row.get('exhibit_source_url') or '').strip(),
        'filing_source_url':str(row.get('source_url','')).strip(),
        'normalized_release_timestamp_et':_iso_et(release),
        'normalized_acceptance_timestamp_et':_iso_et(acceptance),
        'f':f or '', 'a':a or '', 'response_session':d or '',
        'ticker':str(row.get('ticker','')).upper(),
        'event_form':str(row.get('form','')).upper(),
        'event_items':str(row.get('items','')),
        'company_name':str(row.get('company_name','')),
        'report_date':str(row.get('report_date',''))[:10],
    }

def _is_item_202(row):
    return str(row.get('form','')).upper() in {'8-K','8-K/A'} and '2.02' in {x.strip() for x in str(row.get('items','')).split(',')}

def deduplicate_events(rows, sessions, release_map=None):
    """Dedup issuer/report-period amendments; keep original filing if present."""
    release_map=release_map or {}
    eligible=[]; seen_source=0
    for row in rows:
        if not _is_item_202(row): continue
        filing=str(row.get('filing_date',''))[:10]
        if not filing or filing>END: continue
        cik=_cik(row.get('cik')); accession=str(row.get('accession_number','')).strip()
        if not cik or not accession or not row.get('source_url'): continue
        if filing<'2020-06-01': continue
        seen_source+=1
        ann=release_map.get((cik,accession),release_map.get(accession,{}))
        event=event_clock_row(row,sessions,ann)
        if not event['response_session'] or not START<=event['response_session']<=END: continue
        if event['ticker'] not in roster_at(event['response_session']): continue
        eligible.append(event)
    by_release={}
    for e in eligible:
        key=(e['customer_cik'],e['report_date'] or e['filing_date'])
        prior=by_release.get(key)
        # Prefer the non-amended 8-K; for ties, the earliest acceptance is the release anchor.
        score=(e['event_form'].endswith('/A'),e['acceptance_timestamp_utc'] or '',e['accession_number'])
        if prior is None or score<(prior['_score']):
            e['_score']=score; by_release[key]=e
    out=[]
    for e in by_release.values(): e.pop('_score',None); out.append(e)
    out.sort(key=lambda x:(x['response_session'],x['customer_cik'],x['accession_number']))
    return out, seen_source-len(out)

def _load_sic(path):
    """As-of 2-digit SIC values using only rows effective within development."""
    codes=defaultdict(list); scanned=0
    for row in _read_csv(path):
        effective=str(row.get('effective_from') or row.get('available_date') or '')[:10]
        # The pre-2020-06 Dow holdout remains sealed. Later SIC filings may
        # provide the latest public code available for early development dates.
        if not effective or effective<SIC_METADATA_START or effective>END: continue
        scanned+=1
        ticker=str(row.get('ticker') or row.get('asset') or '').upper()
        raw=re.sub(r'\D','',str(row.get('sic') or ''))
        if ticker and len(raw)>=2: codes[ticker].append((effective,raw[:2]))
    for ticker in codes: codes[ticker].sort()
    return codes,scanned

def _asof_sic(codes,ticker,day):
    vals=[sic for effective,sic in codes.get(ticker,[]) if effective<=day]
    return vals[-1] if vals else ''

def _load_release_map(path):
    if not path or not Path(path).is_file():return {}
    out={}
    for row in _read_csv(path):
        accession=str(row.get('accession_number','')).strip(); cik=_cik(row.get('customer_cik') or row.get('cik'))
        if accession: out[(cik,accession)]={k:row.get(k,'') for k in ('release_timestamp_et','exhibit_source_url')}
    return out

def build_metadata(links_rows, events, sic_codes, sessions):
    dev_dates=[s for s in sessions if START<=s<=END]
    if not dev_dates or dev_dates[0]!=START or dev_dates[-1]!=END:
        raise ValueError('NYSE development calendar must begin 2020-11-27 and end 2026-10-30')
    assets=sorted(set().union(*(set(xs) for _,xs in DOW_ROSTERS)))
    ix={ticker:i for i,ticker in enumerate(assets)}; dx={d:i for i,d in enumerate(dev_dates)}
    roster=np.zeros((len(assets),len(dev_dates)),bool); sic=np.full((len(assets),len(dev_dates)),'',dtype='U2')
    for j,ticker in enumerate(assets):
        for k,d in enumerate(dev_dates):
            roster[j,k]=ticker in roster_at(d)
            sic[j,k]=_asof_sic(sic_codes,ticker,d)
    if not np.all(roster.sum(axis=0)==30): raise ValueError('point-in-time roster does not contain exactly 30 names on every development session')

    links=[]; bad_links=0; seen_link=set()
    for row in links_rows:
        if str(row.get('valid_for_development','true')).lower() not in {'true','1','yes'}: continue
        form=str(row.get('source_form','')).upper()
        if form not in {'10-K','10-K/A','10-Q','10-Q/A'}: bad_links+=1; continue
        cci, sci=_cik(row.get('customer_cik')),_cik(row.get('supplier_cik'))
        ct,st=str(row.get('customer_ticker','')).upper(),str(row.get('supplier_ticker','')).upper()
        filing=str(row.get('filing_date',''))[:10]; first=str(row.get('first_usable_session',''))[:10]
        if not all([cci,sci,ct,st,filing,first,row.get('source_accession'),row.get('source_url')]): bad_links+=1; continue
        if ct not in ix or st not in ix: continue
        expected=_next_session_after(filing,sessions)
        if expected!=first: bad_links+=1; continue
        start=max(first,START); end=str(row.get('valid_to','')).strip()[:10] or END
        if end<START or start>END or end<start: continue
        key=(cci,sci,first,end)
        if key in seen_link: continue
        seen_link.add(key)
        links.append({'customer_cik':cci,'customer_ticker':ct,'supplier_cik':sci,'supplier_ticker':st,
                      'source_form':form,'source_accession':str(row['source_accession']),
                      'filing_date':filing,'first_usable_session':first,'valid_from':start,
                      'valid_to':end if str(row.get('valid_to','')).strip() else '',
                      'source_url':str(row['source_url'])})
    # Repeated disclosures preserve one point-in-time economic edge. Keep its
    # earliest public start; an open-ended row keeps the relationship open.
    collapsed={}
    for link in links:
        key=(link['customer_cik'],link['supplier_cik'])
        old=collapsed.get(key)
        if old is None:
            collapsed[key]=link.copy(); continue
        valid_to='' if (not old['valid_to'] or not link['valid_to']) else max(old['valid_to'],link['valid_to'])
        if link['first_usable_session']<old['first_usable_session']:
            collapsed[key]=link.copy()
        collapsed[key]['valid_to']=valid_to
    links=list(collapsed.values())

    event_customers=[]; event_customer_ciks=[]; event_release=[]; event_accept_et=[]; event_accept_utc=[]; event_accessions=[]; event_sources=[]; event_filing=[]; event_forms=[]; event_items=[]; event_response=[]; event_rows=[]
    for e in events:
        d=e['response_session']; dayidx=dx.get(d)
        if dayidx is None: continue
        ticker=e['ticker']; cci=e['customer_cik']
        if ticker not in ix or not roster[ix[ticker],dayidx]: continue
        event_customers.append(ix[ticker]); event_customer_ciks.append(cci); event_release.append(e['release_timestamp_et']); event_accept_et.append(e['acceptance_timestamp_et']); event_accept_utc.append(e['acceptance_timestamp_utc'])
        event_accessions.append(e['accession_number']); event_sources.append(e['exhibit_source_url'] or e['filing_source_url']); event_filing.append(e['filing_date']); event_forms.append(e['event_form']); event_items.append(e['event_items']); event_response.append(d)
        event_rows.append({k:e.get(k,'') for k in EVENT_FIELDS}|{'event_form':e['event_form'],'event_items':e['event_items'],'ticker':ticker,'company_name':e['company_name']})

    counts=[]; pairset=set(); event_recipient_counts={}; dated_pairs=defaultdict(set)
    for d in sorted(set(event_response)):
        di=dx[d]; event_idx=[k for k,x in enumerate(event_response) if x==d]
        event_tickers={assets[event_customers[k]] for k in event_idx}
        event_ciks={events[k]['customer_cik'] for k in event_idx}
        recipients=set(); customer_groups=defaultdict(lambda:defaultdict(set)); pairset_date=set(); missing_sic_tickers=set()
        for eidx in event_idx:
            c=event_customers[eidx]; customer_cik=str(events[eidx]['customer_cik'])
            for link in links:
                if link['customer_cik']!=customer_cik or link['first_usable_session']>d or (link['valid_to'] and link['valid_to']<d):continue
                ct,st=link['customer_ticker'],link['supplier_ticker']
                if ct not in roster_at(d) or st not in roster_at(d) or st==ct or st in event_tickers or link['supplier_cik'] in event_ciks: continue
                supplier=ix[st]; group=sic[supplier,di]
                recipients.add(st); pairset_date.add((customer_cik,link['supplier_cik']))
                if not group: missing_sic_tickers.add(st); continue
                customer_groups[customer_cik][str(group)].add(st)
        pairset.update(pairset_date); dated_pairs[d]=pairset_date
        qualifying=len(recipients)>=3
        missing_sic=len(missing_sic_tickers)
        shuffle_ok=qualifying and not missing_sic_tickers
        if qualifying:
            for customer_cik,groups in customer_groups.items():
                customer_ticker=next((events[k]['ticker'] for k in event_idx if events[k]['customer_cik']==customer_cik),'')
                for group,observed in groups.items():
                    pool={t for t in roster_at(d) if _asof_sic(sic_codes,t,d)==group and t not in event_tickers and t!=customer_ticker}
                    alternates=pool-observed
                    if len(alternates)<len(observed): shuffle_ok=False
        event_recipient_counts[d]=len(recipients)
        counts.append({'response_date':d,'distinct_event_customers':len(event_tickers),
                       'active_dow_supplier_recipients':len(recipients),'directed_pairs_usable_to_date':len(pairset),
                       'date_directed_pairs':len(pairset_date),'sic_missing_recipients':missing_sic,
                       'qualifies_30_date_gate':qualifying,'shuffleable':bool(shuffle_ok)})
    qualifying_dates=[r for r in counts if r['qualifies_30_date_gate']]
    shuffle_good=sum(r['shuffleable'] for r in qualifying_dates)
    gate1=len(qualifying_dates)>=30; gate2=len(pairset)>=10; gate3=bool(qualifying_dates) and shuffle_good==len(qualifying_dates)
    gate={'distinct_eligible_event_dates':len(qualifying_dates),'min_required_event_dates':30,
          'distinct_directed_dow_pairs':len(pairset),'min_required_pairs':10,
          'shuffleable_dates':shuffle_good,'eligible_dates_for_shuffle':len(qualifying_dates),
          'shuffle_coverage':(shuffle_good/len(qualifying_dates) if qualifying_dates else 0.0),
          'gate_1_pass':gate1,'gate_2_pass':gate2,'gate_3_pass':gate3,'pass':bool(gate1 and gate2 and gate3),
          'status':'PASS' if gate1 and gate2 and gate3 else 'FAIL - D7 INFEASIBLE per pre-registration'}
    link_idx_c=[]; link_idx_s=[]; link_first=[]; link_end=[]; link_c_cik=[]; link_s_cik=[]; link_forms=[]; link_acc=[]; link_filings=[]; link_urls=[]; link_valid_to=[]
    for l in links:
        link_idx_c.append(ix[l['customer_ticker']]); link_idx_s.append(ix[l['supplier_ticker']]); link_first.append(l['first_usable_session']); link_end.append(l['valid_to'])
        link_c_cik.append(l['customer_cik']);link_s_cik.append(l['supplier_cik']);link_forms.append(l['source_form']);link_acc.append(l['source_accession']);link_filings.append(l['filing_date']);link_urls.append(l['source_url']);link_valid_to.append(l['valid_to'])
    arrays={'dates':np.asarray(dev_dates),'assets':np.asarray(assets),'roster_mask':roster,'sic2':sic,
        'event_customer_idx':np.asarray(event_customers,dtype=int),'event_customer_cik':np.asarray(event_customer_ciks),
        'event_filing_date':np.asarray(event_filing),'event_form':np.asarray(event_forms),'event_items':np.asarray(event_items),
        'event_release_timestamp_et':np.asarray(event_release),'event_acceptance_timestamp_et':np.asarray(event_accept_et),'event_acceptance_timestamp_utc':np.asarray(event_accept_utc),
        'event_accession_number':np.asarray(event_accessions),'event_source_url':np.asarray(event_sources),'event_response_session':np.asarray(event_response),
        'link_customer_idx':np.asarray(link_idx_c,dtype=int),'link_supplier_idx':np.asarray(link_idx_s,dtype=int),
        'link_customer_cik':np.asarray(link_c_cik),'link_supplier_cik':np.asarray(link_s_cik),'link_source_form':np.asarray(link_forms),
        'link_source_accession':np.asarray(link_acc),'link_filing_date':np.asarray(link_filings),'link_source_url':np.asarray(link_urls),
        'link_first_usable_session':np.asarray(link_first),'link_valid_to':np.asarray(link_valid_to)}
    return arrays,event_rows,counts,gate,{'link_rows_used':len(links),'invalid_or_unusable_link_rows':bad_links,
        'deduplicated_events':len(event_rows),'event_rows_without_exhibit_annotation':sum(not bool(e['release_timestamp_et']) or not bool(e['exhibit_source_url']) for e in event_rows),
        'sic_rows_development_only':sum(len(v) for v in sic_codes.values()),'active_assets_union':len(assets)}

def write_qa(path,meta,gate,counts,events,qa_rows):
    text=(Path(__file__).resolve().parent/'INPUT_QA_TEMPLATE.md').read_text(encoding='utf-8')
    text=text.replace('{{GATE_STATUS}}',gate['status']).replace('{{EVENT_DATES}}',str(gate['distinct_eligible_event_dates']))
    text=text.replace('{{PAIR_COUNT}}',str(gate['distinct_directed_dow_pairs'])).replace('{{SHUFFLE_COVERAGE}}',f"{gate['shuffleable_dates']}/{gate['eligible_dates_for_shuffle']} ({gate['shuffle_coverage']:.1%})")
    text=text.replace('{{GATE1_STATUS}}','PASS' if gate['gate_1_pass'] else 'FAIL')
    text=text.replace('{{GATE2_STATUS}}','PASS' if gate['gate_2_pass'] else 'FAIL')
    text=text.replace('{{GATE3_STATUS}}','PASS' if gate['gate_3_pass'] else 'FAIL')
    text=text.replace('{{GATE_JSON}}',json.dumps(gate,indent=2)).replace('{{QA_JSON}}',json.dumps(qa_rows,indent=2))
    text=text.replace('{{EVENT_EXCERPT}}',json.dumps(events[:5],indent=2,ensure_ascii=False))
    text=text.replace('{{DATE_COVERAGE}}','\n'.join(f"| {r['response_date']} | {r['distinct_event_customers']} | {r['active_dow_supplier_recipients']} | {r['directed_pairs_usable_to_date']} | {r['sic_missing_recipients']} | {'PASS' if r['shuffleable'] else 'FAIL'} |" for r in counts) or '| — | 0 | 0 | 0 | 0 | no qualifying dates |')
    Path(path).write_text(text,encoding='utf-8')

def build(links_path=LINKS_DEFAULT, earnings_path=EARNINGS_DEFAULT, sic_path=SIC_DEFAULT,
          out_dir=OUT, sessions=None, release_map_path=None):
    sessions=sessions or default_sessions()
    sessions=sorted(set(map(str,sessions)))
    links_rows=_read_csv(links_path); earnings_rows=_read_csv(earnings_path)
    sic_codes,sic_count=_load_sic(sic_path); release_map=_load_release_map(release_map_path)
    events,dedup_count=deduplicate_events(earnings_rows,sessions,release_map)
    arrays,event_table,coverage,gate,qa=build_metadata(links_rows,events,sic_codes,sessions)
    qa['candidate_earnings_rows']=sum(_is_item_202(r) for r in earnings_rows)
    qa['deduplicated_or_excluded_events']=dedup_count
    qa['sic_rows_development_only']=sic_count
    od=Path(out_dir);od.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(od/'D7_METADATA.npz',**arrays)
    _write_csv(od/'D7_EVENT_TABLE.csv',event_table,EVENT_FIELDS+['event_form','event_items','ticker','company_name'])
    _write_csv(od/'D7_EVENT_COVERAGE.csv',coverage,list(coverage[0]) if coverage else ['response_date','distinct_event_customers','active_dow_supplier_recipients','directed_pairs_usable_to_date','date_directed_pairs','sic_missing_recipients','qualifies_30_date_gate','shuffleable'])
    write_qa(od/'INPUT_QA.md',arrays,gate,coverage,event_table,qa)
    return {'metadata':str(od/'D7_METADATA.npz'),'event_table':str(od/'D7_EVENT_TABLE.csv'),
            'coverage':str(od/'D7_EVENT_COVERAGE.csv'),'gate':gate,'qa':qa}

def main(argv=None):
    p=argparse.ArgumentParser(description='Outcome-blind D7 metadata and feasibility gate builder')
    p.add_argument('--links',type=Path,default=LINKS_DEFAULT);p.add_argument('--earnings',type=Path,default=EARNINGS_DEFAULT)
    p.add_argument('--sic-panel',type=Path,default=SIC_DEFAULT);p.add_argument('--release-map',type=Path,default=None)
    p.add_argument('--out-dir',type=Path,default=OUT);args=p.parse_args(argv)
    if not args.links.is_file() or not args.earnings.is_file() or not args.sic_panel.is_file():
        p.error('required metadata input missing; no input bundle was opened')
    result=build(args.links,args.earnings,args.sic_panel,args.out_dir,release_map_path=args.release_map)
    print(json.dumps({'gate':result['gate'],'qa':result['qa'],'outputs':{k:v for k,v in result.items() if k in {'metadata','event_table','coverage'}}},indent=2))
    return 0 if result['gate']['pass'] else 1

if __name__=='__main__': raise SystemExit(main())
