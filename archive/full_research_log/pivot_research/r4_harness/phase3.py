"""Direction-agnostic Phase 3 research and portfolio testing primitives.

All arrays use assets on axis 0 and dates on axis 1, except network which is
date x asset x asset (or asset x asset x date). Scores are known at close T.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence
import hashlib
import math
import re
import numpy as np
from scipy.stats import rankdata, norm, skew, kurtosis


def _arr(x, name, ndim=2):
    a=np.asarray(x,dtype=float)
    if a.ndim!=ndim: raise ValueError(f'{name} must have {ndim} dimensions; got {a.shape}')
    return a


def signal_matrix(signal_fn: Callable, assets: Sequence, dates: Sequence, data,
                  mode: str='asset_date') -> np.ndarray:
    """Evaluate a user signal as an (asset,date) score matrix.

    ``mode='asset_date'`` calls ``signal_fn(asset, date, data)`` for every
    pair. ``mode='cross_section'`` calls ``signal_fn(data, date)`` once per
    date and expects one score per asset. Return NaN for unavailable scores.
    """
    out=np.full((len(assets),len(dates)),np.nan,dtype=float)
    if mode=='asset_date':
        for j,d in enumerate(dates):
            for i,a in enumerate(assets): out[i,j]=signal_fn(a,d,data)
    elif mode=='cross_section':
        for j,d in enumerate(dates):
            values=np.asarray(signal_fn(data,d),dtype=float).reshape(-1)
            if len(values)!=len(assets): raise ValueError(f'signal_fn returned {len(values)} scores for {len(assets)} assets')
            out[:,j]=values
    else: raise ValueError("mode must be 'asset_date' or 'cross_section'")
    return out


def _network_cube(network, n_assets: int, n_dates: int) -> np.ndarray:
    """Normalize a dated adjacency/weight tensor to (date, source, target)."""
    g=np.asarray(network,dtype=float)
    if g.shape==(n_dates,n_assets,n_assets): return g
    if g.shape==(n_assets,n_assets,n_dates): return np.moveaxis(g,2,0)
    raise ValueError(f'network must have shape (T,N,N) or (N,N,T); got {g.shape}')


def newey_west_t(values: Sequence[float], lag: int) -> float:
    """Newey-West t-statistic for a mean, Bartlett weights and finite sample."""
    x=np.asarray(values,dtype=float); x=x[np.isfinite(x)]
    n=len(x)
    if n<2: return float('nan')
    lag=min(max(int(lag),0),n-1); u=x-x.mean()
    longvar=float(u@u/n)
    for k in range(1,lag+1):
        longvar += 2*(1-k/(lag+1))*float(u[k:]@u[:-k])/n
    return float(x.mean()/math.sqrt(max(longvar,0.0)/n)) if longvar>0 else (float('inf') if x.mean()>0 else float('-inf') if x.mean()<0 else 0.0)


def _spearman(x, y) -> float:
    ok=np.isfinite(x)&np.isfinite(y)
    if ok.sum()<3: return float('nan')
    rx=rankdata(np.asarray(x)[ok],method='average'); ry=rankdata(np.asarray(y)[ok],method='average')
    if rx.std()==0 or ry.std()==0: return float('nan')
    return float(np.corrcoef(rx,ry)[0,1])


def break_even_rank_ic(turnover: float, return_dispersion: float,
                       cost_per_side: float = 0.0005,
                       top_fraction: float = 1.0/6.0) -> float:
    """Rank-IC hurdle to cover trading costs for a long-only top-quantile.

    ``turnover`` is total traded notional / NAV per rebalance (buys + sells),
    measured relative to the benchmark when the hurdle is benchmark-relative.
    ``return_dispersion`` is
    the cross-sectional standard deviation of the candidate holding-period
    returns. The mapping assumes a linear relation between standardized
    percentile rank and return: a Spearman IC of rho implies a top-quantile
    active return of rho * dispersion * sqrt(12) * (0.5 - top_fraction/2).
    Costs are cost_per_side times total traded notional; do not double turnover
    again for buys and sells. This is a transparent hurdle, not an empirical
    estimate of alpha or a claim that all strategies use top-quantile weights.
    """
    turnover=float(turnover); dispersion=float(return_dispersion)
    cost=float(cost_per_side); q=float(top_fraction)
    if not math.isfinite(turnover) or turnover < 0: raise ValueError('turnover must be finite and non-negative')
    if not math.isfinite(dispersion) or dispersion <= 0: raise ValueError('return_dispersion must be finite and positive')
    if not math.isfinite(cost) or cost < 0: raise ValueError('cost_per_side must be finite and non-negative')
    if not 0 < q < 1: raise ValueError('top_fraction must be between 0 and 1')
    rank_return_multiplier=math.sqrt(12.0)*(0.5-q/2.0)
    return float(cost*turnover/(dispersion*rank_return_multiplier))


@dataclass
class ICResult:
    return_type: str
    horizon: int
    dates: int
    mean_ic: float
    nw_t: float
    series: np.ndarray


def cross_sectional_ic(scores, close_prices, horizons: Sequence[int],
                       open_prices=None, include_series: bool=True) -> list[ICResult]:
    """Cross-sectional rank ICs for close-close and next-open-close returns.

    A score at date t predicts close[t+h]/close[t]-1. Next-open-close uses
    close[t+h]/open[t+1]-1. Non-finite scores/prices are dropped per date,
    which supports point-in-time membership masks. Newey-West lag is h-1.
    """
    s=_arr(scores,'scores'); c=_arr(close_prices,'close_prices')
    if s.shape!=c.shape: raise ValueError('scores and close_prices must have the same (N,T) shape')
    o=None if open_prices is None else _arr(open_prices,'open_prices')
    if o is not None and o.shape!=s.shape: raise ValueError('open_prices shape must match scores')
    n,t=s.shape; out=[]
    for h in horizons:
        if not isinstance(h,(int,np.integer)) or h<1: raise ValueError('horizons must be positive integers')
        for mode in (['C2C','Next O2C'] if o is not None else ['C2C']):
            vals=[]
            for i in range(t-h):
                if mode=='C2C': y=c[:,i+h]/c[:,i]-1
                else: y=c[:,i+h]/o[:,i+1]-1
                vals.append(_spearman(s[:,i],y))
            a=np.asarray(vals,dtype=float); a=a[np.isfinite(a)]
            out.append(ICResult(mode,int(h),int(len(a)),float(a.mean()) if len(a) else float('nan'),newey_west_t(a,h-1),a if include_series else np.empty(0)))
    return out


@dataclass
class EventStudyResult:
    window: int
    event_count: int
    date_clusters: int
    mean_car: float
    nw_t: float
    date_cluster_series: np.ndarray


def event_study(events: Iterable[Mapping], network, close_prices, windows: Sequence[int],
                asset_names: Sequence[str] | None=None, benchmark_close=None) -> list[EventStudyResult]:
    """CAR of linked neighbours after source shocks, clustered by event date.

    Each event has ``source`` (index or asset name) and ``date`` (integer index).
    Event date is the shock close. For window h, neighbour CAR is the weighted
    average of close[t+h]/close[t]-1 minus the equal-weight market return over
    that window, excluding the source. Pass ``benchmark_close`` to use an
    explicit benchmark instead. Same-date event CARs are averaged into date
    clusters and tested with NW lag h-1.
    """
    c=_arr(close_prices,'close_prices'); n,t=c.shape; g=_network_cube(network,n,t)
    if benchmark_close is None:
        mkt=np.nanmean(c[:,1:]/c[:,:-1]-1,axis=0)
        market_path=np.r_[1.0,np.cumprod(1+np.nan_to_num(mkt))]
    else:
        bc=np.asarray(benchmark_close,dtype=float).reshape(-1)
        if len(bc)!=t: raise ValueError('benchmark_close must have T prices')
        market_path=bc/bc[0]
    names={x:i for i,x in enumerate(asset_names)} if asset_names is not None else {}
    ev=[]
    for e in events:
        src=e['source']; src=names[src] if isinstance(src,str) else int(src); ti=int(e['date'])
        if not (0<=src<n and 0<=ti<t): raise ValueError(f'event index out of range: {e}')
        ev.append((src,ti))
    out=[]
    for h in windows:
        vals=[]; dates=[]
        for src,ti in ev:
            if ti+h>=t: continue
            w=np.asarray(g[ti,src,:],float).copy(); w[src]=0
            ok=(np.abs(w)>0)&np.isfinite(c[:,ti])&np.isfinite(c[:,ti+h])
            if not ok.any(): continue
            w=w[ok]; car=c[ok,ti+h]/c[ok,ti]-1-(market_path[ti+h]/market_path[ti]-1)
            denom=np.sum(np.abs(w))
            vals.append(float(np.sum(w*car)/denom)); dates.append(ti)
        clustered=[]
        for d in sorted(set(dates)):
            clustered.append(float(np.mean([x for x,dd in zip(vals,dates) if dd==d])))
        a=np.asarray(clustered,dtype=float)
        out.append(EventStudyResult(int(h),len(vals),len(a),float(a.mean()) if len(a) else float('nan'),newey_west_t(a,h-1),a))
    return out


@dataclass
class PlaceboResult:
    family: str
    real_statistic: float
    draws: int
    percentile: float
    upper_tail_p: float
    two_sided_p: float
    placebo_statistics: np.ndarray


def _edge_list(a: np.ndarray, undirected: bool):
    n=len(a)
    if undirected: return [(i,j,float(a[i,j])) for i in range(n) for j in range(i+1,n) if abs(a[i,j])>0]
    return [(i,j,float(a[i,j])) for i in range(n) for j in range(n) if i!=j and abs(a[i,j])>0]


def _rewire_undirected(a, rng, swaps_per_edge=10):
    n=len(a); es=_edge_list(a,True); edge={(i,j) for i,j,_ in es}; weights=[w for _,_,w in es]
    if len(es)<2: return a.copy()
    for _ in range(max(1,swaps_per_edge*len(es))):
        if len(edge)<2: break
        e1,e2=rng.choice(len(es),size=2,replace=False); a1,b1,_=es[e1]; a2,b2,_=es[e2]
        if len({a1,b1,a2,b2})<4: continue
        new1=(min(a1,b2),max(a1,b2)); new2=(min(a2,b1),max(a2,b1))
        if new1==new2 or new1 in edge or new2 in edge: continue
        edge.remove((min(a1,b1),max(a1,b1))); edge.remove((min(a2,b2),max(a2,b2)))
        edge.add(new1); edge.add(new2)
        es=list((i,j,0.) for i,j in sorted(edge))
    if not edge: return np.zeros_like(a)
    w=rng.permutation(np.asarray(weights)); out=np.zeros_like(a)
    for (i,j),v in zip(sorted(edge),w): out[i,j]=out[j,i]=v
    return out


def _degree_preserving_cube(cube,rng):
    out=np.zeros_like(cube)
    for d,a in enumerate(cube):
        sym=np.allclose(a,a.T,atol=1e-10,equal_nan=True)
        if sym: out[d]=_rewire_undirected(np.nan_to_num(a),rng)
        else:
            # Directed edge swaps preserve each node's in/out degree.
            es=_edge_list(np.nan_to_num(a),False); edge={(i,j) for i,j,_ in es}; weights=[w for _,_,w in es]
            for _ in range(10*len(es)):
                if len(es)<2: break
                q,r=rng.choice(len(es),2,replace=False); a1,b1,_=es[q]; a2,b2,_=es[r]
                if len({a1,b1,a2,b2})<4: continue
                x,y=(a1,b2),(a2,b1)
                if x in edge or y in edge: continue
                edge.remove((a1,b1)); edge.remove((a2,b2)); edge|={x,y}; es=[(i,j,0.) for i,j in sorted(edge)]
            w=rng.permutation(np.asarray(weights))
            for (i,j),v in zip(sorted(edge),w): out[d,i,j]=v
    return out


def _random_links_cube(cube,rng):
    out=np.zeros_like(cube)
    for d,a in enumerate(cube):
        sym=np.allclose(a,a.T,atol=1e-10,equal_nan=True); es=_edge_list(np.nan_to_num(a),sym)
        n=a.shape[0]
        if not es: continue
        if sym:
            choices=[(i,j) for i in range(n) for j in range(i+1,n)]
            ids=rng.choice(len(choices),size=min(len(es),len(choices)),replace=False)
            for (i,j),(_,_,w) in zip([choices[k] for k in ids],rng.permutation(es)): out[d,i,j]=out[d,j,i]=w
        else:
            choices=[(i,j) for i in range(n) for j in range(n) if i!=j]
            ids=rng.choice(len(choices),size=min(len(es),len(choices)),replace=False)
            for (i,j),(_,_,w) in zip([choices[k] for k in ids],rng.permutation(es)): out[d,i,j]=w
    return out


def network_placebos(real_network, statistic: Callable[[np.ndarray],float], n_draws: int=500,
                     seed: int=20261110, families: Sequence[str]=('degree_preserving','random_links','time_shifted')) -> dict[str,PlaceboResult]:
    """Evaluate a network statistic against 500 seeded network placebos.

    The caller supplies a scalar statistic(network). Percentile is the fraction
    of placebo values <= the real value; p-values use finite-sample +1 counts.
    """
    raw=np.asarray(real_network,dtype=float)
    if raw.ndim!=3: raise ValueError('real_network must be a 3D dated network')
    # Infer time-first or time-last from square axes.
    cube=raw if raw.shape[1]==raw.shape[2] else np.moveaxis(raw,2,0)
    if cube.shape[1]!=cube.shape[2]: raise ValueError('network must be (T,N,N) or (N,N,T)')
    if n_draws<1: raise ValueError('n_draws must be positive')
    real=float(statistic(raw))
    if not np.isfinite(real): raise ValueError('real network statistic must be finite')
    rng=np.random.default_rng(seed); result={}
    for family in families:
        vals=[]
        for _ in range(n_draws):
            if family=='degree_preserving': g=_degree_preserving_cube(cube,rng)
            elif family=='random_links': g=_random_links_cube(cube,rng)
            elif family=='time_shifted':
                if len(cube)<2: raise ValueError('time_shifted placebo needs at least two dates')
                shift=int(rng.integers(1,len(cube))); g=np.roll(cube,shift,axis=0)
            else: raise ValueError(f'unknown placebo family {family}')
            # Return in original layout expected by statistic callback.
            passed=g if raw.shape[0]==cube.shape[0] else np.moveaxis(g,0,2)
            vals.append(float(statistic(passed)))
        a=np.asarray(vals,float); a=a[np.isfinite(a)]
        if not len(a): raise ValueError(f'placebo family {family} produced no finite statistics')
        upper=(1+int(np.sum(a>=real)))/(len(a)+1)
        two=(1+int(np.sum(np.abs(a)>=abs(real))))/(len(a)+1)
        result[family]=PlaceboResult(family,real,len(a),float(np.mean(a<=real)),float(upper),float(two),a)
    return result


def _target_weights(score,active,design,n_long,n_short):
    if design=='equal':
        idx=np.flatnonzero(active)
        if not len(idx): raise ValueError('no active assets for equal-weight benchmark')
        w=np.zeros(len(score),float); w[idx]=1/len(idx); return w
    idx=np.flatnonzero(active & np.isfinite(score))
    if len(idx)<max(n_long,n_short if design=='long_short' else 0): raise ValueError('not enough active scored assets for requested design')
    idx=idx[np.argsort(score[idx],kind='stable')]
    w=np.zeros(len(score),float)
    if design=='long_only': w[idx[-n_long:]]=1/n_long
    elif design=='long_short':
        if n_long+n_short>len(idx): raise ValueError('long and short baskets exceed active assets')
        w[idx[-n_long:]]=0.5/n_long; w[idx[:n_short]]=-0.5/n_short
    else: raise ValueError("design must be 'long_only' or 'long_short'")
    return w


def _simulate_portfolio(scores,open_px,close_px,fill_indices,design,n_long,n_short,cost_rate):
    n,t=scores.shape; sh=np.zeros(n); cash=1.0; marks=[]; trade_costs=[]; turnovers=[]; active_shares=[]
    periods=[]
    for k,fi in enumerate(fill_indices):
        if fi<=0 or fi>=t: raise ValueError(f'fill index {fi} must be in [1,T-1]')
        op=open_px[:,fi]; act=np.isfinite(op)&np.isfinite(close_px[:,fi])
        old=sh.copy(); held=np.abs(old)>1e-14
        if np.any(held&~np.isfinite(op)): raise ValueError('missing next-open price for an existing holding')
        nav_open=cash+float(np.sum(old[held]*op[held]))
        if nav_open<=0: raise ValueError('portfolio NAV reached zero or below')
        target=_target_weights(scores[:,fi-1],act,design,n_long,n_short)
        nav_after=nav_open
        for _ in range(500):
            target_sh=np.divide(nav_after*target,op,out=np.zeros(n),where=np.isfinite(op)&(op!=0))
            notional=float(np.sum(np.abs(target_sh-old)*np.where(np.isfinite(op),op,0)))
            newer=nav_open-cost_rate*notional
            if abs(newer-nav_after)<1e-14*max(1.0,abs(nav_open)): nav_after=newer; break
            nav_after=newer
        target_sh=np.divide(nav_after*target,op,out=np.zeros(n),where=np.isfinite(op)&(op!=0))
        notional=float(np.sum(np.abs(target_sh-old)*np.where(np.isfinite(op),op,0)))
        paid=nav_open-nav_after
        if abs(paid-cost_rate*notional)>1e-9*max(1,abs(nav_open)): raise ArithmeticError('actual-trade cost reconciliation failed')
        trade_costs.append(paid); turnovers.append(notional/nav_open)
        ew=np.zeros(n); ew[act]=1/act.sum()
        active_shares.append(.5*float(np.sum(np.abs(target-ew))))
        sh=target_sh; cash=nav_after-float(np.sum(sh[np.isfinite(op)]*op[np.isfinite(op)]))
        end=fill_indices[k+1] if k+1<len(fill_indices) else t-1
        stop=end+1 if k+1==len(fill_indices) else end
        for j in range(fi,stop):
            cp=close_px[:,j]; ok=np.abs(sh)>1e-14
            if np.any(ok&~np.isfinite(cp)): raise ValueError('missing close price for a held asset')
            nav=cash+float(np.sum(sh[ok]*cp[ok])); marks.append((j,nav))
        periods.append((fi,end))
    # Liquidate the final book at the last close and charge the sell-side cost.
    if marks:
        j,nav_before=marks[-1]; cp=close_px[:,j]; notional=float(np.sum(np.abs(sh[np.abs(sh)>1e-14]*cp[np.abs(sh)>1e-14])))
        exit_cost=cost_rate*notional; marks[-1]=(j,nav_before-exit_cost); trade_costs.append(exit_cost)
    vals=np.asarray([v for _,v in marks],float)
    rr=np.diff(np.r_[1.0,vals])/np.maximum(np.abs(np.r_[1.0,vals[:-1]]),1e-12)
    vol=float(rr.std(ddof=0)); sharpe=float(rr.mean()/vol*math.sqrt(252)) if vol else 0.0
    return {'marks':marks,'returns':rr,'cumulative_return':float(vals[-1]-1) if len(vals) else 0.0,
            'sharpe':sharpe,'total_cost':float(np.sum(trade_costs)),'costs':np.asarray(trade_costs),
            'turnover':float(np.mean(turnovers)) if turnovers else 0.0,
            'active_share':float(np.mean(active_shares)) if active_shares else 0.0}


def circular_block_bootstrap_pvalue(strategy_returns, benchmark_returns, block_length=10,
                                    n_draws=5000, seed=20261110) -> tuple[float,np.ndarray]:
    """One-sided null p-value for positive excess mean using centered circular blocks."""
    s=np.asarray(strategy_returns,float); b=np.asarray(benchmark_returns,float)
    if s.shape!=b.shape or s.ndim!=1: raise ValueError('return series must be same-length 1D arrays')
    d=s-b; d=d[np.isfinite(d)]; n=len(d)
    if not n or block_length<1 or n_draws<1: raise ValueError('nonempty returns, positive block length and positive draws required')
    observed=float(d.mean()); null_d=d-observed
    rng=np.random.default_rng(seed); blocks=int(math.ceil(n/block_length)); boot=np.empty(n_draws)
    offsets=np.arange(block_length)
    for j in range(n_draws):
        starts=rng.integers(0,n,size=blocks); ix=((starts[:,None]+offsets)%n).ravel()[:n]; boot[j]=null_d[ix].mean()
    p=(1+np.sum(boot>=observed))/(n_draws+1)
    return float(p),boot


def holm_correction(p_values: Mapping[str,float], alpha=.05) -> dict[str,dict[str,float|bool]]:
    """Holm step-down adjusted p-values for a supplied family of tests."""
    items=sorted(((str(k),float(v)) for k,v in p_values.items()),key=lambda x:x[1]); m=len(items); adjusted={}; running=0.0
    for rank,(name,p) in enumerate(items):
        adj=min(1.0,(m-rank)*p); running=max(running,adj); adjusted[name]={'raw_p':p,'holm_p':running,'reject':running<=alpha}
    return adjusted


def deflated_sharpe_ratio(returns, trial_count: int) -> float:
    """Approximate DSR probability using expected max Sharpe across trials."""
    x=np.asarray(returns,float); x=x[np.isfinite(x)]; n=len(x)
    if trial_count<1: raise ValueError('trial_count must be positive')
    if n<3: return float('nan')
    sr=float(x.mean()/x.std(ddof=1)) if x.std(ddof=1)>0 else 0.0
    if trial_count==1: sr_star=0.0
    else:
        euler=.5772156649015329
        sr_star=(1-euler)*norm.ppf(1-1/trial_count)+euler*norm.ppf(1-1/(trial_count*math.e))
    sk=float(skew(x,bias=False)); ku=float(kurtosis(x,fisher=False,bias=False))
    denom=math.sqrt(max(1-sk*sr+(ku-1)*sr*sr/4,1e-12))
    return float(norm.cdf((sr-sr_star)*math.sqrt(n-1)/denom))


@dataclass
class PortfolioResult:
    strategy_gross: dict
    strategy_net: dict
    benchmark_gross: dict
    benchmark_net: dict
    excess_return_net: float
    bootstrap_p: float
    holm_adjusted_p: float | None
    deflated_sharpe: float
    cost_to_gross_edge_ratio: float | None


def portfolio_engine(scores, open_prices, close_prices, fill_indices: Sequence[int],
                     design='long_only', n_long=5, n_short=5, cost_rate=.0005,
                     bootstrap_draws=5000, seed=20261110, trial_count=1,
                     p_value_family: Mapping[str,float] | None=None) -> PortfolioResult:
    """Next-open portfolio engine, actual-trade costs, EW benchmark and inference."""
    s=_arr(scores,'scores'); o=_arr(open_prices,'open_prices'); c=_arr(close_prices,'close_prices')
    if s.shape!=o.shape or s.shape!=c.shape: raise ValueError('scores/open/close must share (N,T) shape')
    if cost_rate<0 or cost_rate>=1: raise ValueError('cost_rate must be in [0,1)')
    if n_long<1 or n_short<1: raise ValueError('n_long and n_short must be positive')
    if bootstrap_draws<1: raise ValueError('bootstrap_draws must be positive')
    fills=sorted(set(int(x) for x in fill_indices))
    if len(fills)<2: raise ValueError('at least two fill dates are required')
    strat_g=_simulate_portfolio(s,o,c,fills,design,n_long,n_short,0.0)
    strat_n=_simulate_portfolio(s,o,c,fills,design,n_long,n_short,cost_rate)
    ew_scores=np.zeros_like(s)
    bench_g=_simulate_portfolio(ew_scores,o,c,fills,'equal',len(s),len(s),0.0)
    bench_n=_simulate_portfolio(ew_scores,o,c,fills,'equal',len(s),len(s),cost_rate)
    m=min(len(strat_n['returns']),len(bench_n['returns'])); sr=strat_n['returns'][-m:]; br=bench_n['returns'][-m:]
    p,_=circular_block_bootstrap_pvalue(sr,br,10,bootstrap_draws,seed)
    hp=holm_correction({**(p_value_family or {}),'this_strategy':p})['this_strategy']['holm_p'] if p_value_family is not None else None
    gross_edge=strat_g['cumulative_return']-bench_g['cumulative_return']
    ratio=strat_n['total_cost']/gross_edge if gross_edge>0 else None
    return PortfolioResult(strat_g,strat_n,bench_g,bench_n,strat_n['cumulative_return']-bench_n['cumulative_return'],p,hp,deflated_sharpe_ratio(strat_n['returns'],trial_count),ratio)


def require_frozen_prereg(approach: str, prereg_dir=None) -> Path:
    """Require FROZEN date and canonical SHA256 (hash line excluded)."""
    if not re.fullmatch(r'[A-Za-z0-9_-]+',str(approach)): raise ValueError('approach must be a simple identifier')
    root=Path(__file__).resolve().parents[1]
    folder=Path(prereg_dir) if prereg_dir is not None else root/'specs'/'r4_prereg'
    p=folder/f'{approach}.md'
    if not p.is_file(): raise FileNotFoundError(f'pre-registration not found: {p}')
    content=p.read_text(encoding='utf-8'); frozen=re.search(r'^FROZEN:\s*(\d{4}-\d{2}-\d{2})\s*$',content,re.M)
    hash_match=re.search(r'^SHA256:\s*([0-9a-fA-F]{64})\s*$',content,re.M)
    if not frozen or not hash_match: raise ValueError('pre-registration must contain FROZEN: YYYY-MM-DD and SHA256: <64 hex> lines')
    actual=prereg_digest(content)
    if actual.lower()!=hash_match.group(1).lower(): raise ValueError('pre-registration SHA256 does not match its frozen contents')
    return p


def prereg_digest(content: str) -> str:
    """Canonical SHA256 for a pre-registration (the SHA256 line is excluded)."""
    canonical='\n'.join(line for line in content.splitlines() if not re.match(r'^SHA256:\s*',line))+'\n'
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def config_digest(config: Mapping) -> str:
    """Canonical SHA256 for frozen JSON config (its sha256 key is excluded)."""
    body={k:v for k,v in config.items() if k.lower()!='sha256'}
    raw=__import__('json').dumps(body,sort_keys=True,separators=(',',':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def authorize_trial(approach: str, *, prereg_dir=None, trial_log=None) -> Path:
    """Validate prerequisites and remaining budget before a registered run."""
    p=require_frozen_prereg(approach,prereg_dir)
    root=Path(__file__).resolve().parents[1]
    log=Path(trial_log) if trial_log is not None else root/'specs'/'r4_trials.md'
    if not log.is_file(): raise FileNotFoundError(f'trial log not found: {log}')
    nums=[int(m.group(1)) for line in log.read_text(encoding='utf-8').splitlines() if (m:=re.match(r'^\|\s*(\d+)\s*\|',line))]
    if len(nums)>=30: raise RuntimeError('Round 4 trial budget of 30 is exhausted')
    return p


def append_trial(approach: str, variant: str, result: str, *, prereg_dir=None,
                 trial_log=None, trial_date: str | None=None) -> int:
    """Append a single trial row after validating its frozen pre-registration.

    Default destinations are shared project specs paths. During harness
    development, tests pass fixture paths under r4_harness; no shared log is
    written unless this function is explicitly called later by the coordinator.
    """
    require_frozen_prereg(approach,prereg_dir)
    root=Path(__file__).resolve().parents[1]
    log=Path(trial_log) if trial_log is not None else root/'specs'/'r4_trials.md'
    if not log.is_file(): raise FileNotFoundError(f'trial log not found: {log}')
    text=log.read_text(encoding='utf-8'); lines=text.splitlines(keepends=True)
    nums=[]
    for line in lines:
        m=re.match(r'^\|\s*(\d+)\s*\|',line)
        if m: nums.append(int(m.group(1)))
    if len(nums)>=30: raise RuntimeError('Round 4 trial budget of 30 is exhausted')
    no=max(nums,default=0)+1; d=trial_date or date.today().isoformat(); date.fromisoformat(d)
    safe_variant=' '.join(str(variant).split()).replace('|','/')[:80]
    safe_result=' '.join(str(result).split()).replace('|','/')[:160]
    row=f'| {no} | {approach} | {safe_variant} | specs/r4_prereg/{approach}.md | {d} | {safe_result} |\n'
    # Keep rows in the trial table, before the next section (the holdout log).
    marker='## Holdout integrity log'
    if marker in text:
        head,tail=text.split(marker,1); text=head.rstrip()+'\n'+row+'\n'+marker+tail
    else: text=text.rstrip()+'\n'+row
    log.write_text(text,encoding='utf-8')
    return no


def run_registered_trial(approach: str, variant: str, runner: Callable[[],object], *,
                         prereg_dir=None, trial_log=None, trial_date=None) -> object:
    """Gate a trial before execution, then log both successes and failures."""
    authorize_trial(approach,prereg_dir=prereg_dir,trial_log=trial_log)
    try:
        result=runner()
    except Exception as exc:
        append_trial(approach,variant,f'FAILED: {type(exc).__name__}: {exc}',prereg_dir=prereg_dir,trial_log=trial_log,trial_date=trial_date)
        raise
    append_trial(approach,variant,result,prereg_dir=prereg_dir,trial_log=trial_log,trial_date=trial_date)
    return result


def assert_future_truncation_invariant(signal_fn: Callable, data, signal_index: int,
                                       truncate_fn: Callable) -> None:
    """Raise if signal_fn(data, as_of) changes after future data are removed."""
    full=np.asarray(signal_fn(data,signal_index),dtype=float)
    truncated_data=truncate_fn(data,signal_index)
    cut=np.asarray(signal_fn(truncated_data,signal_index),dtype=float)
    if full.shape!=cut.shape or not np.allclose(full,cut,rtol=0,atol=1e-12,equal_nan=True):
        raise AssertionError('signal changes when post-signal-date data are truncated')


def run_holdout(config_path, price_folder, runner: Callable, *, caller_role: str) -> object:
    """Coordinator-only holdout entry point with an explicit directory guard.

    It does not inspect the price folder. The caller must provide a frozen
    JSON config containing ``approach`` and ``prereg_dir`` fields. A directory
    is accepted only when its path explicitly contains ``holdout`` and does
    not point at known development folders.
    """
    import json
    if caller_role!='coordinator': raise PermissionError('only the coordinator may invoke the sealed holdout runner')
    cfg_path=Path(config_path); folder=Path(price_folder)
    if not cfg_path.is_file(): raise FileNotFoundError(cfg_path)
    cfg=json.loads(cfg_path.read_text(encoding='utf-8'))
    if not cfg.get('approach'): raise ValueError('frozen config needs an approach field')
    if not cfg.get('frozen_date') or not cfg.get('sha256') or config_digest(cfg).lower()!=str(cfg['sha256']).lower():
        raise ValueError('config must contain frozen_date and a matching sha256')
    prereg=require_frozen_prereg(cfg['approach'],cfg.get('prereg_dir'))
    frozen_line=re.search(r'^FROZEN:\s*(\d{4}-\d{2}-\d{2})\s*$',prereg.read_text(encoding='utf-8'),re.M)
    if not frozen_line or cfg['frozen_date']!=frozen_line.group(1): raise ValueError('config frozen_date must match the preregistration')
    resolved=str(folder.resolve()).lower().replace('\\','/')
    if 'holdout' not in resolved: raise PermissionError('price folder path must explicitly identify a holdout directory')
    if any(part in resolved.split('/') for part in ('repo','w1_engine','oos3')):
        raise PermissionError('development folders are not valid holdout inputs')
    return runner(cfg,folder)
