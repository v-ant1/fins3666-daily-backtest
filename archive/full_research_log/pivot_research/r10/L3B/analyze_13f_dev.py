from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm, t

ROOT = Path(__file__).resolve().parents[2]
POS = ROOT / 'r4_L4' / 'data' / '13f_development_pit_positions.csv'
PANEL = ROOT / 'r9' / 'data' / 'J2_DEV_FROM_20201127.npz'
OUT = Path(__file__).resolve().parent
START, END = pd.Timestamp('2020-11-27'), pd.Timestamp('2026-10-30')
COST_RT = 0.002
MIN_MANAGERS = 5

def ticker_norm(x):
    return str(x).upper().replace('.', '-').strip()

def main():
    # Every outcome row used below is inside the authorized development range.
    d = pd.read_csv(POS, usecols=['report_date','availability_filing_date','manager_cik','ticker','amount_type','shares_or_principal_amount'])
    d['report_date'] = pd.to_datetime(d.report_date)
    d['availability_filing_date'] = pd.to_datetime(d.availability_filing_date)
    d = d[(d.report_date >= START) & (d.availability_filing_date <= END)].copy()
    d = d[d.amount_type.eq('SH')]
    d['ticker'] = d.ticker.map(ticker_norm)
    d['manager_cik'] = d.manager_cik.astype(str)
    d['shares'] = pd.to_numeric(d.shares_or_principal_amount, errors='coerce').fillna(0)
    # Aggregate duplicate CUSIP/share-class rows to manager × ticker × report quarter.
    d = d.groupby(['report_date','availability_filing_date','manager_cik','ticker'], as_index=False).shares.sum()
    # Snapshot-level availability by manager and quarter; panel contains selected, not comprehensive, managers.
    meta = d.groupby(['report_date','manager_cik'], as_index=False).availability_filing_date.min()
    # Load only the development panel specified in the preregistration.
    z = np.load(PANEL, allow_pickle=False)
    dates = pd.to_datetime(z['sp500_dates'])
    assets = np.array([ticker_norm(x) for x in z['sp500_assets']])
    roster = z['sp500_roster'].astype(bool)
    op = z['sp500_adjusted_open']
    cl = z['sp500_adjusted_close']
    date_idx = {x.normalize(): i for i,x in enumerate(dates)}
    asset_idx = {x:i for i,x in enumerate(assets)}
    rows=[]; quarter_meta=[]
    quarters = sorted(pd.Timestamp(q) for q in d.report_date.unique())
    for q in quarters:
        prev = q - pd.offsets.QuarterEnd(1)
        cutoff = q + pd.Timedelta(days=45)
        # Move cutoff to the next available panel session on/after the statutory 45-day date.
        eligible_dates = [x for x in dates if x >= cutoff]
        if not eligible_dates: continue
        cutoff_session = pd.Timestamp(eligible_dates[0]).normalize()
        if cutoff_session > END: continue
        # Exclude dates outside dev and avoid using any filing that was not public by this cutoff.
        if cutoff_session < START: continue
        di = date_idx.get(cutoff_session)
        if di is None or di+19 >= len(dates) or pd.Timestamp(dates[di+19]).normalize() > END: continue
        # Reports have to be public by cutoff. A complete report filing from a manager establishes
        # that absent listed names are zero positions; only managers filing both quarters qualify.
        current_meta = meta[(meta.report_date.eq(q)) & (meta.availability_filing_date <= cutoff)]
        previous_meta = meta[(meta.report_date.eq(prev)) & (meta.availability_filing_date <= cutoff)]
        managers = set(current_meta.manager_cik) & set(previous_meta.manager_cik)
        if not managers: continue
        cur = d[(d.report_date.eq(q)) & d.manager_cik.isin(managers)].groupby(['manager_cik','ticker']).shares.sum()
        old = d[(d.report_date.eq(prev)) & d.manager_cik.isin(managers)].groupby(['manager_cik','ticker']).shares.sum()
        active = roster[:,di]
        active_assets = {assets[i] for i in np.flatnonzero(active)}
        signals=[]
        for ticker in sorted(active_assets.intersection(asset_idx)):
            buys=sells=0
            for m in managers:
                a=float(cur.get((m,ticker),0.0)); b=float(old.get((m,ticker),0.0))
                if a>b: buys+=1
                elif a<b: sells+=1
            n=buys+sells
            if n >= MIN_MANAGERS:
                signals.append((ticker, (buys-sells)/n, n))
        # Top tercile, stable ticker tie-break; S&P roster exposure is reported separately from 13F data coverage.
        signals.sort(key=lambda x:(-x[1],x[0]))
        k=max(1, math.ceil(len(signals)/3)) if signals else 0
        chosen=signals[:k]
        if not chosen: continue
        # Open on the first session after public cutoff. With cutoff on a session, entry is next session.
        entry_i=di+1
        exit_i=entry_i+19
        if exit_i >= len(dates) or pd.Timestamp(dates[exit_i]).normalize()>END: continue
        # Retain only issuers with valid adjusted open/close prices throughout the single entry/exit measurement.
        chosen_rows=[]
        for ticker,score,n in chosen:
            ai=asset_idx[ticker]
            if not roster[ai,entry_i]: continue
            p0=float(op[ai,entry_i]); p1=float(cl[ai,exit_i])
            if not np.isfinite(p0) or not np.isfinite(p1) or p0<=0: continue
            chosen_rows.append((ticker,score,n,p1/p0-1))
        if not chosen_rows: continue
        # Benchmark is equal-weight buy-and-hold over PIT S&P names on entry day.
        members=np.flatnonzero(roster[:,entry_i])
        br=[]
        for ai in members:
            p0=float(op[ai,entry_i]); p1=float(cl[ai,exit_i])
            if np.isfinite(p0) and np.isfinite(p1) and p0>0: br.append(p1/p0-1)
        if not br: continue
        gross=float(np.mean([x[3] for x in chosen_rows]))
        bench=float(np.mean(br))
        net_excess=gross-bench-COST_RT
        rows.append({'report_date':q.date().isoformat(),'cutoff_session':cutoff_session.date().isoformat(),'n_eligible_stocks':len(signals),'n_managers':len(managers),'n_selected':len(chosen_rows),'gross_portfolio_return':gross,'ew_sp500_benchmark_return':bench,'net_excess_return':net_excess,'selection_signal_mean':float(np.mean([x[1] for x in chosen_rows]))})
        quarter_meta.append({'report_date':q.date().isoformat(),'cutoff':cutoff.date().isoformat(),'available_selected_managers':len(managers),'signals':len(signals),'selected':len(chosen_rows)})
    res=pd.DataFrame(rows)
    if len(res):
        vals=res.net_excess_return.to_numpy(float); n=len(vals); mean=float(vals.mean()); sd=float(vals.std(ddof=1)) if n>1 else 0.0
        ci=(float(mean-t.ppf(.975,n-1)*sd/math.sqrt(n)),float(mean+t.ppf(.975,n-1)*sd/math.sqrt(n))) if n>1 else [None,None]
        byyear=res.assign(year=pd.to_datetime(res.report_date).dt.year).groupby('year').net_excess_return.agg(['count','mean']).reset_index()
        # 24 is the six-year candidate holdout maximum: one event per quarter.
        n_hold=min(24, int(round(n / max(1, (END-START).days/365.2425) * 6)))
        mde=2.4865*sd/math.sqrt(n_hold) if n_hold>0 else None
        passprob=float(norm.cdf((.5*mean)/(sd/math.sqrt(n_hold))-1.6449)) if n_hold>0 and sd>0 else None
        result={'trial':'R10-L3B-01','n_dev_quarters':n,'mean_net_excess':mean,'sd_quarterly_net_excess':sd,'ci95_t':[ci[0],ci[1]],'median_net_excess':float(np.median(vals)),'n_holdout_power':n_hold,'mde_80pct_family1':mde,'pass_probability_after_50pct_haircut':passprob,'cost_one_way_bps':10,'round_trip_cost_return':COST_RT,'annual':byyear.to_dict(orient='records'),'quarters':rows,'quarter_metadata':quarter_meta,'dev_boundary':['2020-11-27','2026-10-30'],'source_position_rows_dev':int(len(d)),'source_tickers_dev':int(d.ticker.nunique()),'selected_panel_instrument_coverage_note':'Input 13F extract has 30 tickers per report quarter in its coverage manifest; not a full S&P 500 13F census.'}
    else:
        result={'trial':'R10-L3B-01','n_dev_quarters':0,'error':'No complete eligible rebalance windows under frozen rules.'}
    (OUT/'dev_result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    res.to_csv(OUT/'quarterly_outcomes.csv',index=False)
    print(json.dumps({k:v for k,v in result.items() if k not in ('quarters','quarter_metadata')},indent=2))
if __name__=='__main__': main()
