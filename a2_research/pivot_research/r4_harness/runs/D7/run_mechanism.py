"""D7 frozen-spec mechanism runner.

The input is a development-only NPZ produced by the coordinator's input builder.
No input is opened unless the D7 preregistration is hash-valid and --execute is
explicitly supplied.  This module deliberately does not read LINKS.csv.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from scipy.stats import norm, rankdata

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from r4_harness.phase3 import (  # noqa: E402
    append_trial, authorize_trial, circular_block_bootstrap_pvalue,
    deflated_sharpe_ratio, prereg_digest, require_frozen_prereg,
)

OUT = Path(__file__).resolve().parent
PREREG_DIR = ROOT / 'specs' / 'r4_prereg'
TRIAL_LOG = ROOT / 'specs' / 'r4_trials.md'
START, END = '2020-11-27', '2026-10-30'
IC_FLOOR = .0183
NW_LAG = 4
SHUFFLES = 500
SEED = 20261110
SHIFT = 20

def _text(x):
    return np.asarray(x).astype(str)

def _date(value):
    return dt.date.fromisoformat(str(value)[:10])

def _et_datetime(value):
    """Parse timestamps as ET; date-only values are not valid timestamps."""
    s = str(value).strip()
    if not s:
        return None
    v = s.replace('Z', '+00:00')
    try:
        parsed = dt.datetime.fromisoformat(v)
    except ValueError as exc:
        raise ValueError(f'invalid ISO timestamp: {s}') from exc
    et = ZoneInfo('America/New_York')
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=et)
    return parsed.astimezone(et)

def derive_response_session(filing_date, release_timestamp_et, acceptance_timestamp_et, dates):
    """Apply D7's combined f/a clock; unknown release time uses f only."""
    calendar = [_date(v) for v in dates]
    filing = _date(filing_date)
    f = next((i for i, d in enumerate(calendar) if d > filing), None)
    if f is None:
        return None
    release = _et_datetime(release_timestamp_et)
    if release is None:
        return f
    acceptance = _et_datetime(acceptance_timestamp_et)
    latest = max(x for x in (release, acceptance) if x is not None)
    opening = dt.time(9, 30)
    a = next((i for i, day in enumerate(calendar)
              if dt.datetime.combine(day, opening, tzinfo=ZoneInfo('America/New_York')) > latest), None)
    if a is None:
        return None
    return max(a, f)

def _nw(y, lag=NW_LAG):
    y = np.asarray(y, float)
    y = y[np.isfinite(y)]
    if len(y) < 3:
        raise ValueError('Newey-West inference needs at least three finite dates')
    mu = float(y.mean()); u = y - mu; n = len(y)
    l = min(int(lag), n - 1)
    var = float(u @ u / n)
    for k in range(1, l + 1):
        var += 2.0 * (1.0 - k / (l + 1.0)) * float(u[k:] @ u[:-k]) / n
    se = math.sqrt(max(var / n, 0.0))
    t = mu / se if se else math.copysign(math.inf, mu) if mu else 0.0
    return {'n': n, 'mean': mu, 'se': se, 't': t, 'lag': l}

def _spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    if int(ok.sum()) < 3:
        return float('nan')
    a, b = rankdata(x[ok]), rankdata(y[ok])
    if np.std(a) == 0 or np.std(b) == 0:
        return float('nan')
    return float(np.corrcoef(a, b)[0, 1])

def _p_one_sided(t, side):
    return float(norm.sf(t) if side == 'positive' else norm.cdf(t))

def _tost(series, margin=IC_FLOOR):
    nw = _nw(series)
    zlo = (nw['mean'] + margin) / nw['se'] if nw['se'] else math.inf
    zhi = (nw['mean'] - margin) / nw['se'] if nw['se'] else -math.inf
    p_lower = float(norm.sf(zlo))  # reject mean <= -margin
    p_upper = float(norm.cdf(zhi)) # reject mean >= +margin
    return {**nw, 'ci90': [nw['mean'] - 1.6448536269514722 * nw['se'],
                           nw['mean'] + 1.6448536269514722 * nw['se']],
            'p_lower': p_lower, 'p_upper': p_upper,
            'p_tost': max(p_lower, p_upper),
            'equivalent': bool(p_lower < .05 and p_upper < .05)}

def _load_bundle(path, price_path=None):
    required = {
        'dates','assets','roster_mask','sic2',
        'event_customer_idx','event_customer_cik','event_filing_date','event_form','event_items',
        'event_release_timestamp_et','event_acceptance_timestamp_et','event_acceptance_timestamp_utc',
        'event_accession_number','event_source_url','event_response_session',
        'link_customer_idx','link_supplier_idx','link_customer_cik','link_supplier_cik',
        'link_source_form','link_source_accession','link_filing_date','link_source_url',
        'link_first_usable_session','link_valid_to',
    }
    with np.load(path, allow_pickle=False) as z:
        missing = required - set(z.files)
        if missing:
            raise ValueError(f'input bundle missing fields: {sorted(missing)}')
        a = {k: z[k].copy() for k in z.files}
    dates = _text(a['dates']).tolist(); assets = _text(a['assets']).tolist()
    if not dates or dates != sorted(dates) or len(set(dates)) != len(dates):
        raise ValueError('dates must be unique and chronological')
    if dates[0] < START or dates[-1] > END:
        raise ValueError('bundle contains dates outside the D7 development period')
    n, t = len(assets), len(dates)
    for k in ('roster_mask','sic2'):
        if np.asarray(a[k]).shape != (n, t):
            raise ValueError(f'{k} must have assets x dates shape {(n,t)}')
    if len(set(assets)) != n or n < 30:
        raise ValueError('D7 requires at least 30 unique assets in the point-in-time panel')
    if not np.all(np.asarray(a['roster_mask'],bool).sum(axis=0)==30):
        raise ValueError('the point-in-time roster must contain exactly 30 Dow names each session')
    e = len(a['event_customer_idx'])
    event_fields = ('event_customer_cik','event_filing_date','event_form','event_items',
                    'event_release_timestamp_et','event_acceptance_timestamp_et','event_acceptance_timestamp_utc',
                    'event_accession_number','event_source_url','event_response_session')
    if any(len(a[k]) != e for k in event_fields):
        raise ValueError('event columns must have identical lengths')
    if len(set(_text(a['event_accession_number']).tolist())) != e:
        raise ValueError('duplicate event accession: deduplicate releases before runner input')
    m = len(a['link_customer_idx'])
    if any(len(a[k]) != m for k in ('link_supplier_idx','link_first_usable_session','link_valid_to')):
        raise ValueError('link columns must have identical lengths')
    if np.any(np.asarray(a['event_customer_idx'], int) < 0) or np.any(np.asarray(a['event_customer_idx'], int) >= n):
        raise ValueError('event customer index out of range')
    if np.any(np.asarray(a['link_customer_idx'], int) < 0) or np.any(np.asarray(a['link_customer_idx'], int) >= n) or np.any(np.asarray(a['link_supplier_idx'], int) < 0) or np.any(np.asarray(a['link_supplier_idx'], int) >= n):
        raise ValueError('link endpoint index out of range')
    lookup = {d:i for i,d in enumerate(dates)}
    event_ix=[]
    for k in range(e):
        if str(a['event_form'][k]).upper() not in ('8-K','8K') or '2.02' not in str(a['event_items'][k]):
            raise ValueError(f'event row {k} is not a verified Form 8-K Item 2.02 event')
        derived = derive_response_session(a['event_filing_date'][k], a['event_release_timestamp_et'][k], a['event_acceptance_timestamp_et'][k], dates)
        declared = str(a['event_response_session'][k])
        if derived is None or dates[derived] != declared:
            raise ValueError(f'event response_session does not match the frozen combined clock at row {k}')
        event_ix.append(derived)
        if not str(a['event_customer_cik'][k]).strip() or not str(a['event_accession_number'][k]).strip() or not str(a['event_source_url'][k]).strip():
            raise ValueError(f'event row {k} lacks exhibit source_url')
    link_start=[]; link_end=[]
    link_keys=[]
    for k, start in enumerate(_text(a['link_first_usable_session'])):
        key=(int(a['link_customer_idx'][k]),int(a['link_supplier_idx'][k]),str(start))
        if key in link_keys: raise ValueError(f'duplicate link row: {key}')
        link_keys.append(key)
        filing=_date(a['link_filing_date'][k])
        filed_ix=next((i for i,d in enumerate(map(_date,dates)) if d>filing),None)
        if filed_ix is None or dates[filed_ix] != str(start):
            raise ValueError(f'link first_usable_session does not equal first NYSE session after filing date at row {k}')
        if start not in lookup:
            # A link already public before development is available from index zero.
            if _date(start) < _date(dates[0]): link_start.append(0)
            else: raise ValueError(f'link first_usable_session outside calendar: {start}')
        else: link_start.append(lookup[start])
        end = str(a['link_valid_to'][k]).strip()
        if not end: link_end.append(t-1)
        elif _date(end) < _date(dates[0]): link_end.append(-1)
        elif _date(end) > _date(dates[-1]): link_end.append(t-1)
        elif end in lookup: link_end.append(lookup[end])
        else: raise ValueError(f'link_valid_to outside calendar: {end}')
        if not str(a['link_customer_cik'][k]).strip() or not str(a['link_supplier_cik'][k]).strip() or not str(a['link_source_accession'][k]).strip() or not str(a['link_source_url'][k]).strip():
            raise ValueError(f'link row {k} lacks source or CIK identity metadata')
        if str(a['link_source_form'][k]).upper() not in ('10-K','10-Q'):
            raise ValueError(f'link row {k} is not based on a 10-K or 10-Q')
    a['_dates'], a['_assets'], a['_event_ix'] = dates, assets, np.asarray(event_ix, int)
    a['_link_start'], a['_link_end'] = np.asarray(link_start), np.asarray(link_end)
    # The metadata bundle can be gated without opening any OHLC inputs.
    if price_path is not None:
        with np.load(price_path, allow_pickle=False) as z:
            if not {'dates','assets','adjusted_open','adjusted_close'} <= set(z.files):
                raise ValueError('price bundle requires dates, assets, adjusted_open, adjusted_close')
            pd=_text(z['dates']).tolist(); pa=_text(z['assets']).tolist()
            if pd != dates or pa != assets:
                raise ValueError('price bundle calendar or asset order differs from metadata bundle')
            for k in ('adjusted_open','adjusted_close'):
                if z[k].shape != (n,t): raise ValueError(f'{k} must have assets x dates shape {(n,t)}')
                a[k]=z[k].copy()
    return a

def _event_shocks(a):
    n,t = a['adjusted_open'].shape
    op=np.asarray(a['adjusted_open'],float); cl=np.asarray(a['adjusted_close'],float)
    roster=np.asarray(a['roster_mask'],bool); cix=np.asarray(a['event_customer_idx'],int)
    dates=a['_dates']; eix=a['_event_ix']; shocks=[]
    for k,d in enumerate(eix):
        if not roster[cix[k],d]:
            raise ValueError(f'event customer is not active on response date {dates[d]}')
        valid=roster[:,d] & np.isfinite(op[:,d]) & np.isfinite(cl[:,d]) & (op[:,d]>0)
        if valid.sum()!=30:
            raise ValueError(f'event date {dates[d]} lacks complete EW30 open/close coverage')
        ew=float(np.mean(cl[valid,d]/op[valid,d]-1))
        shocks.append(float(cl[cix[k],d]/op[cix[k],d]-1-ew))
    return np.asarray(shocks,float)

def _date_scores(a, shocks, event_ix=None, shuffled=None):
    """Return event-date supplier score vectors and event index sets."""
    n,t=a['adjusted_open'].shape; dates=a['_dates']; roster=np.asarray(a['roster_mask'],bool)
    cix=np.asarray(a['event_customer_idx'],int); eix=a['_event_ix'] if event_ix is None else np.asarray(event_ix,int)
    own_by_date={d:set(cix[eix==d].tolist()) for d in set(eix.tolist())}
    result={}
    for d in sorted(set(eix.tolist())):
        ev=np.flatnonzero(eix==d); per_supplier={}
        for k in ev:
            customer=int(cix[k])
            if shuffled is None:
                edges=[q for q,(cc,ss) in enumerate(zip(a['link_customer_idx'],a['link_supplier_idx']))
                       if int(cc)==customer and a['_link_start'][q]<=d<=a['_link_end'][q]]
                targets=[int(a['link_supplier_idx'][q]) for q in edges]
            else:
                targets=shuffled[d].get(customer,[])
            for supplier in targets:
                if supplier==customer or supplier in own_by_date[d] or not roster[supplier,d]:
                    continue
                per_supplier.setdefault(supplier,[]).append(float(shocks[k]))
        score=np.full(n,np.nan)
        for j,vals in per_supplier.items(): score[j]=float(np.mean(vals))
        result[d]=score
    return result,own_by_date

def _forward(a, d):
    op=np.asarray(a['adjusted_open'],float); cl=np.asarray(a['adjusted_close'],float)
    j=d+1; k=d+5
    if k>=op.shape[1]: return np.full(op.shape[0],np.nan)
    out=np.full(op.shape[0],np.nan); ok=np.isfinite(op[:,j])&(op[:,j]>0)&np.isfinite(cl[:,k])
    out[ok]=cl[ok,k]/op[ok,j]-1
    return out

def _ic_series(a, score_map, dates=None):
    vals=[]; used=[]
    allowed=sorted(score_map) if dates is None else list(dates)
    for d in allowed:
        y=_forward(a,d); act=np.asarray(a['roster_mask'],bool)[:,d]
        ic=_spearman(score_map[d][act],y[act])
        if np.isfinite(ic): vals.append(ic); used.append(d)
    return np.asarray(vals,float), used

def _feasibility(a):
    """Outcome-free D7 gates: breadth, directed pairs and shuffle pools."""
    eix=a['_event_ix']; cix=np.asarray(a['event_customer_idx'],int); n=len(a['_assets'])
    active=np.asarray(a['roster_mask'],bool); sic=_text(a['sic2'])
    pairset=set(); eligible_dates=[]; fail=[]
    for d in sorted(set(eix.tolist())):
        event_customers=set(cix[eix==d].tolist())
        edges=[q for q,(c,s) in enumerate(zip(a['link_customer_idx'],a['link_supplier_idx']))
               if a['_link_start'][q]<=d<=a['_link_end'][q] and int(c) in event_customers
               and int(s)!=int(c) and int(s) not in event_customers and active[int(s),d] and active[int(c),d]]
        recipients=set(int(a['link_supplier_idx'][q]) for q in edges)
        pairset.update((int(a['link_customer_idx'][q]),int(a['link_supplier_idx'][q])) for q in edges)
        if len(recipients)>=3:
            eligible_dates.append(d)
            # Every observed SIC bucket must have enough active alternatives to assign each customer's slots.
            by_customer={}
            for q in edges:
                c,s=int(a['link_customer_idx'][q]),int(a['link_supplier_idx'][q])
                group=str(sic[s,d])
                if not group: fail.append((d,c,'MISSING_SIC',1,0))
                by_customer.setdefault(c,[]).append(group)
            for c,groups in by_customer.items():
                for g in set(groups)-{''}:
                    need=groups.count(g)
                    observed={int(a['link_supplier_idx'][q]) for q in edges
                              if int(a['link_customer_idx'][q])==c and str(sic[int(a['link_supplier_idx'][q]),d])==g}
                    pool=[j for j in range(n) if active[j,d] and str(sic[j,d])==g and j not in event_customers and j not in observed]
                    if len(pool)<need: fail.append((d,c,g,need,len(pool)))
    counts={'eligible_event_dates':len(eligible_dates),'directed_dow_pairs':len(pairset),
            'shuffle_coverage_dates':len(eligible_dates),'total_event_dates':len(set(eix.tolist())),
            'shuffle_failures':fail}
    counts['passed']=counts['eligible_event_dates']>=30 and counts['directed_dow_pairs']>=10 and counts['shuffle_coverage_dates']==counts['eligible_event_dates'] and not fail
    if not counts['passed']:
        raise RuntimeError('D7 infeasible before outcomes: '+json.dumps(counts))
    return counts

def _shuffle_for_date(a,d,rng):
    cix=np.asarray(a['event_customer_idx'],int); eix=a['_event_ix']; active=np.asarray(a['roster_mask'],bool); sic=_text(a['sic2']); n=len(a['_assets'])
    by_customer={}; event_customers=set(cix[eix==d].tolist())
    for q,(c,s) in enumerate(zip(a['link_customer_idx'],a['link_supplier_idx'])):
        c,s=int(c),int(s)
        if a['_link_start'][q]<=d<=a['_link_end'][q] and c in event_customers and s!=c and s not in event_customers and active[c,d] and active[s,d]:
            by_customer.setdefault(c,{}).setdefault(str(sic[s,d]),[])
            by_customer[c][str(sic[s,d])].append(s)
    draw={}
    for c,groups in by_customer.items():
        targets=[]
        for group,observed in sorted(groups.items()):
            pool=np.asarray([j for j in range(n) if active[j,d] and str(sic[j,d])==group and j not in event_customers and j not in observed],int)
            if len(pool)<len(observed): raise RuntimeError(f'incomplete SIC shuffle pool at {a["_dates"][d]} customer={c} SIC={group}')
            targets.extend(rng.choice(pool,size=len(observed),replace=False).tolist())
        if len(targets)!=len(set(targets)): raise RuntimeError('duplicate supplier endpoint in customer shuffle')
        draw[c]=targets
    return draw

def _portfolio(a, shocks):
    """Registered long-five weekly portfolio, actual-trade cap and costs."""
    n,t=a['adjusted_open'].shape; op=np.asarray(a['adjusted_open'],float); cl=np.asarray(a['adjusted_close'],float); roster=np.asarray(a['roster_mask'],bool)
    cix=np.asarray(a['event_customer_idx'],int); eix=a['_event_ix']; scores=np.full((n,t),np.nan)
    # At close t, include only event shocks in response sessions t-4..t and links public by each response close.
    for t0 in range(t):
        vals={}
        for k,d in enumerate(eix):
            if t0-4<=d<=t0:
                for q,(cc,ss) in enumerate(zip(a['link_customer_idx'],a['link_supplier_idx'])):
                    cc,ss=int(cc),int(ss)
                    if cc==cix[k] and a['_link_start'][q]<=d<=a['_link_end'][q] and ss!=cc:
                        vals.setdefault(ss,[]).append(shocks[k])
        for j,x in vals.items(): scores[j,t0]=float(np.mean(x))
    formations=[f for f in range(0,t-1,5) if np.isfinite(scores[:,f]).any()]
    if len(formations)<2: raise ValueError('portfolio needs at least two weekly formations')
    # Actual trading is at next-session open.  Apply the harness's total buy+sell
    # notional cap and per-dollar cost, then mark each session to its close.
    strat=np.zeros(t-1); gross_strat=np.zeros(t-1); ew=np.zeros(t-1); ew_gross=np.zeros(t-1)
    weights=np.zeros(n); ew_weights=np.zeros(n); turnovers=[]; requested_turnovers=[]; costs=[]; ew_costs=[]; active_shares=[]; cap_binds=0
    form_to_fill={f:f+1 for f in formations}
    for day in range(1,t):
        if day in form_to_fill.values():
            f=day-1; active=roster[:,day]&np.isfinite(op[:,day])&(op[:,day]>0)
            if np.isfinite(scores[:,f]).sum()<5:
                target=np.zeros(n); target[active]=1/max(1,int(active.sum()))
            else:
                eligible=np.flatnonzero(active & np.isfinite(scores[:,f]))
                picked=sorted(eligible.tolist(),key=lambda j:(-scores[j,f],a['_assets'][j]))[:5]
                target=np.zeros(n); target[picked]=.2
            requested=float(np.abs(target-weights).sum())
            requested_turnovers.append(requested)
            scale=min(1.0,.50/requested) if requested>.50 else 1.0
            if scale<1: cap_binds+=1
            target=weights+scale*(target-weights)
            turnover=float(np.abs(target-weights).sum()); cost=.0005*turnover
            turnovers.append(turnover); costs.append(cost)
            ewtarget=np.zeros(n); ewtarget[active]=1/max(1,int(active.sum()))
            ewturn=float(np.abs(ewtarget-ew_weights).sum()); ewcost=.0005*ewturn
            ew_costs.append(ewcost)
            active_shares.append(.5*float(np.abs(target-ewtarget).sum()))
            weights=target; ew_weights=ewtarget
        else:
            cost=ewcost=0.0
        if day==1:
            asset_ret=np.divide(cl[:,day],op[:,day],out=np.full(n,np.nan),where=np.isfinite(op[:,day])&(op[:,day]>0))-1
        else:
            asset_ret=np.divide(cl[:,day],cl[:,day-1],out=np.full(n,np.nan),where=np.isfinite(cl[:,day-1])&(cl[:,day-1]>0))-1
        good=np.isfinite(asset_ret)
        sr=float(np.nansum(weights*asset_ret)-cost)
        er=float(np.nansum(ew_weights*asset_ret)-ewcost)
        strat[day-1]=sr; gross_strat[day-1]=sr+cost; ew[day-1]=er; ew_gross[day-1]=er+ewcost
    # The terminal liquidation is charged at the last observed close.
    final_cost=.0005*float(np.abs(weights).sum()); strat[-1]-=final_cost; costs.append(final_cost)
    p,_=circular_block_bootstrap_pvalue(strat,ew,10,5000,SEED)
    def cum(x): return float(np.prod(1+np.nan_to_num(x,nan=0.0))-1)
    def sharpe(x):
        sd=float(np.std(x,ddof=0)); return float(np.mean(x)/sd*math.sqrt(252)) if sd else 0.0
    def max_dd(x):
        curve=np.r_[1.0,np.cumprod(1+np.nan_to_num(x,nan=0.0))]
        return float(np.min(curve/np.maximum.accumulate(curve)-1.0))
    annual=lambda x: float((1+cum(x))**(252/max(1,len(x)))-1) if cum(x)>-1 else -1.0
    gross_edge=cum(gross_strat)-cum(ew_gross); excess=cum(strat)-cum(ew)
    inc_cost=max(0.0,float(sum(costs)-sum(ew_costs)))
    turn=float(np.mean(turnovers)) if turnovers else 0.0
    raw_criteria=bool(excess>0 and sharpe(strat)>sharpe(ew) and gross_edge>=4*float(sum(costs)) and turn<=.50 and (np.mean(active_shares) if active_shares else 0)>=.50 and p<.05)
    return {'status':'run','net_excess':excess,'gross_active_edge':gross_edge,'strategy_sharpe':sharpe(strat),'ew30_sharpe':sharpe(ew),
            'strategy_annualized_return':annual(strat),'ew30_annualized_return':annual(ew),
            'strategy_max_drawdown':max_dd(strat),'ew30_max_drawdown':max_dd(ew),
            'strategy_turnover_executed_mean':turn,'strategy_turnover_requested_mean':float(np.mean(requested_turnovers)) if requested_turnovers else 0.0,
            'active_share':float(np.mean(active_shares)) if active_shares else 0.0,'strategy_cost':float(sum(costs)),
            'ew30_cost':float(sum(ew_costs)),'incremental_cost':inc_cost,'cap_binding_dates':cap_binds,
            'bootstrap_p':p,'holm_p':'pending complete 27-endpoint family','dsr':deflated_sharpe_ratio(strat,30),'trial_count':30,
            'raw_criteria_pass_before_holm':raw_criteria,'pass':'pending complete 27-endpoint Holm adjustment' if raw_criteria else False}

def calculate(a):
    feasibility=_feasibility(a)
    if 'adjusted_open' not in a or 'adjusted_close' not in a:
        raise ValueError('prices are not attached; pass the separately gated price bundle')
    shocks=_event_shocks(a)
    primary_map,own=_date_scores(a,shocks)
    primary,used=_ic_series(a,primary_map)
    if len(primary)<30: raise RuntimeError('D7 infeasible: fewer than 30 usable event-date ICs')
    primary_nw=_nw(primary)
    rng=np.random.default_rng(SEED)
    shuffled_series=[]; shuffled_means=[]
    for _ in range(SHUFFLES):
        smap={d:_shuffle_for_date(a,d,rng) for d in sorted(primary_map)}
        scores,_=_date_scores(a,shocks,shuffled=smap)
        series,_=_ic_series(a,scores,dates=used)
        if len(series)!=len(used) or not np.isfinite(series).all():
            raise RuntimeError('within-industry shuffle could not preserve every primary event date')
        shuffled_series.append(series); shuffled_means.append(float(series.mean()))
    shuffled_series=np.asarray(shuffled_series); shuffled_means=np.asarray(shuffled_means)
    p2=float((1+np.count_nonzero(shuffled_means>=primary_nw['mean']))/(SHUFFLES+1))
    placebo_avg=shuffled_series.mean(axis=0)
    nw3=_nw(placebo_avg); p3=float(2*norm.sf(abs(nw3['t'])))
    tost4=_tost(placebo_avg)
    # Freeze the original response-date link set and shock, then test the
    # identical score vector against the supplier cross-section 20 sessions on.
    shifted_map={int(d+SHIFT): primary_map[int(d)] for d in primary_map
                 if int(d+SHIFT)+5 < len(a['_dates'])}
    shift_series,shift_dates=_ic_series(a,shifted_map)
    tost5=_tost(shift_series)
    primary_gate=bool(primary_nw['mean']>=IC_FLOOR and primary_nw['t']>=2 and primary_nw['mean']>0)
    shuffle_gate=bool(primary_nw['mean']>np.quantile(shuffled_means,.95) and p2<.05)
    portfolio={'status':'not_run','reason':'primary and both placebo gates must pass before portfolio stage'}
    if primary_gate and shuffle_gate and tost4['equivalent'] and tost5['equivalent']:
        portfolio=_portfolio(a,shocks)
    endpoints={
        'D7-1 primary event-date rank IC':{**primary_nw,'one_sided_p':_p_one_sided(primary_nw['t'],'positive'),'gate':primary_gate,'dates':[a['_dates'][d] for d in used]},
        'D7-2 observed vs within-industry shuffle':{'observed_mean':primary_nw['mean'],'shuffle_p95':float(np.quantile(shuffled_means,.95)),'randomization_p':p2,'gate':shuffle_gate},
        'D7-3 averaged shuffle series vs zero':{**nw3,'two_sided_p':p3},
        'D7-4 averaged shuffle series TOST':tost4,
        'D7-5 fixed +20-session timing placebo TOST':{**tost5,'shifted_dates':[a['_dates'][d] for d in shift_dates],
            'excluded_events':int(sum(int(d+SHIFT)+5>=len(a['_dates']) for d in a['_event_ix']))},
        'D7-6 portfolio net excess vs EW30':portfolio,
    }
    all_gate=bool(primary_gate and shuffle_gate and tost4['equivalent'] and tost5['equivalent'])
    return {'approach':'D7','passed':all_gate,'prereg_sha256':prereg_digest((PREREG_DIR/'D7.md').read_text(encoding='utf-8')),
            'input_only_feasibility':feasibility,'endpoints':endpoints,
            'shuffle_distribution':{'draws':SHUFFLES,'seed':SEED,'min':float(shuffled_means.min()),'q05':float(np.quantile(shuffled_means,.05)),'median':float(np.median(shuffled_means)),'q95':float(np.quantile(shuffled_means,.95)),'max':float(shuffled_means.max()),'means':shuffled_means.tolist()},
            'portfolio_gate_pass':all_gate}

def _require_log_capacity(trial_log, rows=6):
    text=Path(trial_log).read_text(encoding='utf-8')
    used=sum(bool(re.match(r'^\|\s*\d+\s*\|',line)) for line in text.splitlines())
    if used+rows>30: raise RuntimeError(f'D7 needs {rows} endpoint log rows but only {30-used} budget rows remain')

def run(metadata_path=OUT/'D7_METADATA.npz', price_path=OUT/'D7_PRICES.npz', prereg_dir=PREREG_DIR, trial_log=TRIAL_LOG, out_dir=OUT, *, execute=False):
    if not execute: raise PermissionError('explicit execute=True / CLI --execute is required')
    prereg=require_frozen_prereg('D7',prereg_dir=prereg_dir)
    authorize_trial('D7',prereg_dir=prereg_dir,trial_log=trial_log)
    _require_log_capacity(trial_log,6)
    # Only point-in-time roster/link/event/SIC metadata are opened before the
    # input-only gate. OHLC prices remain unopened unless that gate passes.
    metadata=_load_bundle(metadata_path)
    feasibility=_feasibility(metadata)
    a=_load_bundle(metadata_path,price_path)
    result=calculate(a)
    result['prereg_sha256']=prereg_digest(prereg.read_text(encoding='utf-8'))
    od=Path(out_dir); od.mkdir(parents=True,exist_ok=True)
    (od/'D7_MECHANISM_RESULTS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    lines=['# D7 mechanism and placebo results','',f"**Mechanism gate: {'PASS' if result['passed'] else 'FAIL'}.** Preregistration SHA-256: `{result['prereg_sha256']}`.",'','| Endpoint | Estimate / p-value | Result |','|---|---|---|']
    for name,value in result['endpoints'].items():
        lines.append(f"| {name} | `{json.dumps(value,sort_keys=True)}` | {'not run' if value.get('status')=='not_run' else 'reported'} |")
    lines += ['', 'All six registered endpoints are retained. Holm-adjusted p-values require the complete goal-wide 27-endpoint family and are not calculated here.', '']
    (od/'MECHANISM_RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    log_rows=[]
    for name,value in result['endpoints'].items():
        log_rows.append((name,json.dumps(value,sort_keys=True)))
    for name,detail in log_rows:
        append_trial('D7',name,detail,prereg_dir=prereg_dir,trial_log=trial_log)
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(description='D7 frozen development mechanism runner')
    parser.add_argument('--execute',action='store_true',help='explicitly authorize input opening and calculation')
    parser.add_argument('--metadata',type=Path,default=OUT/'D7_METADATA.npz')
    parser.add_argument('--prices',type=Path,default=OUT/'D7_PRICES.npz')
    parser.add_argument('--prereg-dir',type=Path,default=PREREG_DIR)
    parser.add_argument('--trial-log',type=Path,default=TRIAL_LOG)
    parser.add_argument('--out-dir',type=Path,default=OUT)
    args=parser.parse_args(argv)
    if not args.execute:
        print('REFUSED: pass --execute to authorize D7 input access',file=sys.stderr); return 2
    try:
        require_frozen_prereg('D7',prereg_dir=args.prereg_dir)
        result=run(args.metadata,args.prices,args.prereg_dir,args.trial_log,args.out_dir,execute=True)
    except Exception as exc:
        print(f'REFUSED/FAILED: {type(exc).__name__}: {exc}',file=sys.stderr); return 2
    print(json.dumps({'passed':result['passed'],'prereg_sha256':result['prereg_sha256']},indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
