import csv, datetime as dt
from pathlib import Path
import pandas_market_calendars as mcal

BASE=Path(__file__).resolve().parent
L1C=BASE.parent/'L1C'
windows=list(csv.DictReader((L1C/'pit_membership_windows.csv').open(newline='',encoding='utf-8-sig')))
c_rows=list(csv.DictReader((L1C/'coverage_rows.csv').open(newline='',encoding='utf-8-sig')))
d_path=BASE/'coverage_rows_cont.csv'
d_rows=list(csv.DictReader(d_path.open(newline='',encoding='utf-8-sig'))) if d_path.exists() else []
calendar=mcal.get_calendar('NYSE')
sched=calendar.schedule(start_date='2010-01-01',end_date='2015-12-31')
sessions={x.date() for x in sched.index}

def expected(w):
 a,b=dt.date.fromisoformat(w['window_start']),dt.date.fromisoformat(w['window_end_exclusive'])
 return {d for d in sessions if a<=d<b}
def name_match(a,b):
 norm=lambda s: ''.join(c.lower() for c in (s or '') if c.isalnum())
 x,y=norm(a),norm(b)
 if not y:return False
 return x==y or x in y or y in x

c_by={r.get('source_ticker',''):r for r in c_rows}
d_by={}
for r in d_rows: d_by.setdefault(r.get('source_ticker',''),[]).append(r)
covered_total=expected_total=0
missing=[]
method_counts={'L1C_metadata_range':0,'L1D_daily_date_count':0,'unqueried':0}
for w in windows:
 t=w['ticker']; exp=expected(w); n=len(exp); expected_total+=n; cov=0; reason='unqueried'; method='unqueried'
 if t in d_by:
  row=next((x for x in d_by[t] if x['window_start']==w['window_start'] and x['window_end_exclusive']==w['window_end_exclusive']),None)
  if row:
   cov=int(row.get('covered_sessions') or 0); method='L1D_daily_date_count'; reason=('daily_adjusted_dates_counted' if cov==n else ('partial_daily_adjusted_dates' if cov else 'no_verified_daily_adjusted_dates'))
 elif t in c_by:
  row=c_by[t]; method='L1C_metadata_range'
  if row.get('status')=='200' and row.get('name_status') in ('match','match_fuzzy') and row.get('startDate') and row.get('endDate'):
   lo=dt.date.fromisoformat(row['startDate']); hi=dt.date.fromisoformat(row['endDate'])
   cov=sum(lo<=d<=hi for d in exp); reason=('metadata_span_covers_window' if cov==n else ('metadata_span_partial' if cov else 'metadata_span_absent'))
  else: reason=('recycled_ambiguous' if row.get('name_status')=='recycled_ambiguous' else ('metadata_name_unverified' if row.get('status')=='200' else 'metadata_request_unusable'))
 cov=min(max(cov,0),n); covered_total+=cov; method_counts[method]+=1
 if n-cov:
  missing.append({'ticker':t,'issuer':w['issuer_name'],'window_start':w['window_start'],'window_end_exclusive':w['window_end_exclusive'],'expected_sessions':n,'covered_sessions':cov,'missing_sessions':n-cov,'status':reason,'method':method})
missing_total=expected_total-covered_total
share=100*covered_total/expected_total if expected_total else 0
missing_share=100*missing_total/expected_total if expected_total else 100
d_syms=len({r['source_ticker'] for r in d_rows})
c_syms=len({r['source_ticker'] for r in c_rows})
d_req=2*d_syms
all_requests=50+70+d_req
# Prior documented use: L1B 50; L1C has 70 attempts including its malformed source ticker.
monthly_unique_upper=50+c_syms+d_syms
verdict='GO' if missing_share<=3 else 'NO-GO'
lines=[]
lines += ['# R10 L1D — Tiingo 2010–2015 PIT membership-window coverage','', '**Status:** Partial census; **holdout decision: '+verdict+'.**', '', '## Scope and method', '', 'The check covers daily adjusted-price date availability inside the 2010-01-01 to 2015-12-31 S&P 500 point-in-time membership windows. The denominator is the number of NYSE trading sessions during each identity window (identity-session-days), counted from the NYSE calendar. L1D queried Tiingo daily metadata and prices endpoints using GET requests only; responses were reduced to metadata fields, date strings, and counts. No price or return values were printed, stored, summarized, or analyzed.', '', f'L1C rows were reused without requests. Because L1C used metadata start/end dates rather than daily rows, its contributed session counts are inferred from those endpoint dates and cannot detect internal daily gaps. L1D counts are exact returned date counts within each window. L1C and L1D cover {c_syms} and {d_syms} endpoint symbols respectively; the roster contains {len(windows)} PIT identity windows across {len(set(w["ticker"] for w in windows))} endpoint ticker symbols.', '', '## Coverage', '', '| Measure | Result |', '|---|---:|', f'| Covered identity-session-days | {covered_total:,} / {expected_total:,} ({share:.3f}%) |', f'| Missing or unverified identity-session-days | {missing_total:,} ({missing_share:.3f}%) |', f'| L1C metadata-range identities | {method_counts["L1C_metadata_range"]} |', f'| L1D daily-date-count identities | {method_counts["L1D_daily_date_count"]} |', f'| Unqueried identities | {method_counts["unqueried"]} |', f'| Required maximum missing share for GO | 3.000% |', '', f'**Decision: {verdict}.** The point estimate exceeds the 3% missing-session threshold / remains below the threshold.' if missing_share>3 else f'**Decision: {verdict}.** The measured missing-session share is within the 3% threshold, subject to the L1C internal-gap limitation.', '', '## Missing or unverified identity windows', '', 'Each row lists the unverified sessions for an individual PIT identity window. Unqueried symbols are included as fully missing.', '', '| Ticker | PIT issuer | Window | Covered / expected sessions | Missing | Status |', '|---|---|---|---:|---:|---|']
for r in missing:
 lines.append(f"| {r['ticker']} | {r['issuer'].replace('|','/')} | {r['window_start']} to {r['window_end_exclusive']} | {r['covered_sessions']:,} / {r['expected_sessions']:,} | {r['missing_sessions']:,} | {r['status']} |")
lines += ['', '## Request and quota use', '', '| Phase | GET requests | Unique ticker slots |', '|---|---:|---:|', '| L1B prior metadata pass | 50 | 50 |', '| L1C metadata checkpoint | 70 | 70 (includes one malformed non-roster ticker) |', f'| L1D metadata + daily prices | {d_req} | {d_syms} |', f'| Cumulative | {all_requests} | at most {monthly_unique_upper} of 500 |', '', f'L1D respects a 72.5-second minimum between request starts (under 50 requests/hour), with a maximum 146 requests and a three-hour runtime cap. Monthly unique-symbol use is an upper bound because some L1D symbols may duplicate prior L1B checks. The 500-symbol monthly allowance is not exhausted.', '', '## Limits', '', 'The roster is reconstructed from the supplied L1C PIT windows. Tiingo responses establish availability only for the returned ticker mapping; issuer-name mismatches, ambiguous recycled tickers, failed requests, and unqueried windows receive no coverage credit. L1C metadata start/end dates do not prove daily completeness within their span. This remains a screening coverage check and does not authorize holdout outcome analysis.', '']
report=BASE/'TIINGO_COVERAGE_FINAL.md'
report.write_text('\n'.join(lines),encoding='utf-8')
summary=f"- 2026-11-13 [L1D] Tiingo 2010–2015 PIT membership-window availability: {verdict} to building the holdout under the ≤3% missing identity-session-day gate. Combined L1C metadata-range coverage and L1D daily adjusted-price date counts show {share:.3f}% covered and {missing_share:.3f}% missing/unverified of {expected_total:,} NYSE identity-session-days; {method_counts['unqueried']} identities remain unqueried, and L1C metadata cannot detect internal daily gaps. Cumulative API use: {all_requests} GET requests and at most {monthly_unique_upper}/500 monthly unique ticker slots; details and the full missing-window list are in `r10/L1D/TIINGO_COVERAGE_FINAL.md`."
with (BASE.parent.parent/'specs'/'r10_decisions.md').open('a',encoding='utf-8') as f: f.write('\n'+summary+'\n')
print({'report':str(report),'covered_identity_session_days':covered_total,'expected_identity_session_days':expected_total,'missing_share_pct':round(missing_share,3),'decision':verdict,'missing_windows':len(missing),'L1D_symbols':d_syms})
