"""Small, self-contained daily OHLCV candidate screen for FINS3666.

Reads the supplied repo price files but writes only beneath w2_candidates.
Six new variants, fixed before looking at their OOS results, share a common
weekly top-five, top-eight hold-buffer, next-open, actual-cost simulator.
"""
import csv
import math
from pathlib import Path

import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
DATA_DIRS = [ROOT / "repo" / x for x in ("prices-daily-lookback", "prices-daily", "prices-daily-delisted")]
OUT = Path(__file__).resolve().parent
COST = 0.0005
TOP = 5
BUFFER = 8
STEP = 5
IS_ROSTER = ["AAPL","AMGN","AXP","BA","CAT","CRM","CSCO","CVX","DIS","DOW","GS","HD","HON","IBM","INTC","JNJ","JPM","KO","MCD","MMM","MRK","MSFT","NKE","PG","TRV","UNH","V","VZ","WBA","WMT"]
RECENT_ROSTER = ["AAPL","AMGN","AXP","AMZN","BA","CAT","CRM","CSCO","CVX","DIS","GS","HD","HON","IBM","JNJ","JPM","KO","MCD","MMM","MRK","MSFT","NKE","NVDA","PG","SHW","TRV","UNH","V","VZ","WMT"]
PERIODS = {
    "IS": ("2020-11-27", "2022-12-30", IS_ROSTER, "2020-11-27"),
    "OOS1": ("2023-01-03", "2024-02-23", IS_ROSTER, "2020-11-27"),
    "OOS2": ("2024-12-06", "2025-12-31", RECENT_ROSTER, "2024-12-06"),
}


def read_data(ticker):
    rows = {}
    for folder in DATA_DIRS:
        p = folder / f"{ticker}.csv"
        if not p.exists():
            continue
        with p.open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                date = row["date"][:10]
                try:
                    o, h, l, c, adj, vol = (float(row[k]) for k in ("open", "high", "low", "close", "adjclose", "volume"))
                    factor = adj / c if c else 1.0
                except (ValueError, TypeError, KeyError):
                    continue
                rows[date] = (o * factor, h * factor, l * factor, adj, vol)
    return rows


def load(roster, end):
    raw = {t: read_data(t) for t in sorted(set(IS_ROSTER + RECENT_ROSTER + ["SPY"]))}
    dates = sorted(d for d in raw["SPY"] if d <= end)
    # The daily files have a common exchange calendar. Fail visibly if an input is incomplete.
    names = sorted(set(IS_ROSTER + RECENT_ROSTER))
    matrices = {}
    for key, col in (("open",0),("high",1),("low",2),("close",3),("volume",4)):
        a = np.full((len(names), len(dates)), np.nan)
        for i, t in enumerate(names):
            for j, d in enumerate(dates):
                if d in raw[t]:
                    a[i,j] = raw[t][d][col]
        matrices[key] = a
    return dates, names, matrices


def pct_rank(x):
    # Stable average ranks in [0,1], supporting ties.
    n = len(x); order = np.argsort(x, kind="mergesort"); out = np.empty(n, float)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and x[order[j+1]] == x[order[i]]:
            j += 1
        out[order[i:j+1]] = ((i+j)/2)/(n-1) if n > 1 else .5
        i = j + 1
    return out


def score_for(kind, i, ix, ret, close, vol, market_ret):
    # All features use observations no later than signal close i. Returns here
    # are close-to-close adjusted returns; all portfolio fills are next open.
    r5 = np.prod(1 + ret[:, i-4:i+1], axis=1) - 1
    r21 = np.prod(1 + ret[:, i-20:i+1], axis=1) - 1
    vol63 = np.std(ret[:, i-62:i+1], axis=1, ddof=1) * math.sqrt(252)
    if kind == "low_vol_63":
        return -pct_rank(vol63)
    if kind == "low_beta_63":
        x = market_ret[i-62:i+1]
        xc = x - x.mean()
        beta = np.sum((ret[:,i-62:i+1] - ret[:,i-62:i+1].mean(axis=1,keepdims=True))*xc,axis=1) / max(np.sum(xc*xc),1e-12)
        return -pct_rank(beta)
    if kind == "vol_scaled_resrev5":
        market5 = np.prod(1+market_ret[i-4:i+1])-1
        resid = r5 - market5
        return pct_rank(-resid / np.maximum(vol63 / math.sqrt(252) * math.sqrt(5), 1e-5))
    if kind == "low_volume_reversal":
        vshort = np.mean(vol[:,i-4:i+1],axis=1)
        vbase = np.mean(vol[:,i-24:i+1],axis=1)
        low = np.clip(1-vshort/np.maximum(vbase,1),0,1)
        return pct_rank((-r5) * low)
    if kind == "resrev_lowvol":
        market5 = np.prod(1+market_ret[i-4:i+1])-1
        resid = r5 - market5
        return .5*pct_rank(-resid) + .5*pct_rank(-vol63)
    if kind == "vol_timing_ew":
        # Common portfolio exposure, not a cross-sectional score. Handled in simulator.
        return np.zeros(len(ix))
    raise ValueError(kind)


def simulate(kind, period, dates, names, m):
    start, end, roster, anchor = PERIODS[period]
    ix = np.array([names.index(t) for t in roster])
    pos = {d:j for j,d in enumerate(dates)}
    close, opn, vol = m["close"][ix], m["open"][ix], m["volume"][ix]
    feature_start = max(0, pos[start]-63)
    feature_end = pos[end]+1
    if np.isnan(close[:,feature_start:feature_end]).any() or np.isnan(opn[:,feature_start:feature_end]).any():
        raise RuntimeError(f"Missing OHLC in used {period} data; no names or dates were silently dropped")
    # Data indices must be contiguous exchange sessions; official periods are fixed.
    ret = close[:,1:] / close[:,:-1] - 1
    market_ret = np.r_[0.0, np.mean(ret,axis=0)]
    ret = np.column_stack([np.zeros(len(ix)), ret])
    fills = [d for d in dates if anchor <= d <= end][::STEP]
    if not fills:
        raise RuntimeError(f"No fills in {period}")
    i0 = pos[fills[0]]
    if i0 < 63:
        raise RuntimeError(f"Insufficient feature history at {fills[0]}")
    weights = None
    shares = None
    equity_marks = []
    turnovers = []
    turnover_dates = []
    equity = 1.0
    cash = 0.0
    for k, fill in enumerate(fills):
        i = pos[fill]
        nxt = fills[k+1] if k+1 < len(fills) else end
        ni = pos[nxt]
        if weights is None or i >= i0:
            if kind == "vol_timing_ew":
                # Use only lagged 21-session EW30 volatility, cap gross at one.
                lagged = market_ret[i-21:i]
                sigma = np.std(lagged, ddof=1)*math.sqrt(252)
                gross_target = min(1.0, .15/max(sigma, .01))
                target = np.full(len(ix), gross_target/len(ix))
            else:
                s = score_for(kind, i, ix, ret, close, vol, market_ret)
                order = np.lexsort((np.array(roster), -s))
                ranked = [roster[z] for z in order]
                held = set() if weights is None else {roster[j] for j,w in enumerate(weights) if w > 0}
                keep = [t for t in ranked if t in held and ranked.index(t)+1 <= BUFFER][:TOP]
                chosen = keep + [t for t in ranked if t not in keep and t not in held][:TOP-len(keep)]
                # If held names beyond buffer remain, they are sold; entrants are next best.
                target = np.zeros(len(ix))
                for t in chosen:
                    target[roster.index(t)] = 1/TOP
            px = opn[:,i]
            if shares is None:
                # Solve initial buy-side fee against invested notional; residual stays in cash.
                equity = 1.0/(1.0+COST*float(np.sum(target)))
                shares = equity * target / px
                cash = equity*(1.0-float(np.sum(target)))
                turnovers.append(float(np.sum(target)))
                turnover_dates.append(fill)
            else:
                values = shares * px
                gross = float(values.sum()+cash)
                new_equity = gross
                for _ in range(500):
                    updated = gross-COST*np.sum(np.abs(target*new_equity-values))
                    if abs(updated-new_equity) < 1e-14*max(1,gross):
                        new_equity=updated; break
                    new_equity=updated
                traded = float(np.sum(np.abs(target*new_equity-values)))
                equity = new_equity
                shares = equity*target/px
                cash = equity*(1.0-float(np.sum(target)))
                turnovers.append(traded/max(gross,1e-12))
                turnover_dates.append(fill)
            weights = target
        # Close marks on [fill, next fill); next-open rebalancing is handled before that day's mark.
        first = i
        stop = ni if k + 1 < len(fills) else ni + 1
        for j in range(first, stop):
            if dates[j] > end:
                continue
            equity_marks.append((dates[j],float(np.sum(shares*close[:,j])+cash)))
    # Final liquidation at the last close (the official engine also charges final sell side).
    if equity_marks:
        d, v = equity_marks[-1]
        equity_marks[-1] = (d, v-COST*float(np.sum(shares*close[:,pos[d]])))
    mark_dates=[d for d,_ in equity_marks]
    vals = np.array([v for _,v in equity_marks])
    if len(vals) < 2:
        raise RuntimeError(f"Too few daily marks for {period}")
    first=next(j for j,d in enumerate(mark_dates) if d>=start)
    base=1.0 if first==0 else vals[first-1]
    period_vals=vals[first:]
    daily=np.r_[period_vals[0]/base-1,period_vals[1:]/period_vals[:-1]-1]
    years = max(len(daily)/252, 1/252)
    total = period_vals[-1]/base-1
    ann = (period_vals[-1]/base)**(1/years)-1
    sharpe = daily.mean()/daily.std(ddof=0)*math.sqrt(252) if daily.std(ddof=0)>0 else 0
    period_turnover=[x for x,d in zip(turnovers,turnover_dates) if d>=start]
    return {"ann":ann,"sharpe":sharpe,"turnover":float(np.mean(period_turnover)),"daily":daily,"marks":equity_marks}


def main():
    dates,names,m=load(RECENT_ROSTER,"2025-12-31")
    variants=["low_vol_63","low_beta_63","vol_scaled_resrev5","low_volume_reversal","resrev_lowvol","vol_timing_ew"]
    results={}
    for p in PERIODS:
        # Benchmark uses same open-fill calendar and cost mechanics, fully invested equal weights.
        results[("EW30",p)] = simulate_ew(p,dates,names,m)
        for v in variants:
            results[(v,p)] = simulate(v,p,dates,names,m)
    with (OUT/"candidate_results.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["variant","period","annualized_excess_vs_EW30_pp","sharpe_0rf","mean_traded_equity_per_rebalance_pct","active_HAC10_t","active_HAC10_p_two_sided"])
        for v in variants:
            for p in PERIODS:
                x=results[(v,p)]; ew=results[("EW30",p)]
                tstat,pval=hac_test(x["daily"]-ew["daily"],10)
                w.writerow([v,p,f"{100*(x['ann']-ew['ann']):.4f}",f"{x['sharpe']:.4f}",f"{100*x['turnover']:.2f}",f"{tstat:.3f}",f"{pval:.4f}"])
    print("variant,period,excess_ann_pp,sharpe,turnover_pct,HAC10_t,HAC10_p")
    for v in variants:
        for p in PERIODS:
            x=results[(v,p)]; ew=results[("EW30",p)]
            tstat,pval=hac_test(x["daily"]-ew["daily"],10)
            print(f"{v},{p},{100*(x['ann']-ew['ann']):.3f},{x['sharpe']:.3f},{100*x['turnover']:.2f},{tstat:.3f},{pval:.4f}")
    print("IS winner:",max(variants,key=lambda v:results[(v,"IS")]["ann"]-results[("EW30","IS")]["ann"]))


def hac_test(x, lag=10):
    """Newey-West t test of mean paired daily active return, Bartlett weights."""
    x=np.asarray(x,float); n=len(x); mu=float(x.mean()); u=x-mu
    lrv=float(np.dot(u,u)/n)
    for k in range(1,min(lag,n-1)+1):
        cov=float(np.dot(u[k:],u[:-k])/n)
        lrv += 2*(1-k/(lag+1))*cov
    se=math.sqrt(max(lrv,0)/n)
    t=mu/se if se else 0.0
    return t,float(2*norm.sf(abs(t)))


def simulate_ew(period, dates, names, m):
    start,end,roster,anchor=PERIODS[period]
    ix=np.array([names.index(t) for t in roster]); pos={d:j for j,d in enumerate(dates)}
    fills=[d for d in dates if anchor<=d<=end][::STEP]
    close,opn=m["close"][ix],m["open"][ix]
    w=np.full(len(ix),1/len(ix)); equity=1.0; shares=None; marks=[]; to=[]
    for k,fill in enumerate(fills):
        i=pos[fill]; nxt=fills[k+1] if k+1<len(fills) else end; ni=pos[nxt]
        if shares is None:
            equity=1/(1+COST)
            shares=equity*w/opn[np.arange(len(ix)),i]
            to.append(1.0)
        else:
            px=opn[np.arange(len(ix)),i]; values=shares*px; gross=values.sum(); E=gross
            for _ in range(500):
                u=gross-COST*np.sum(np.abs(E*w-values))
                if abs(u-E)<1e-14*max(1,gross): E=u; break
                E=u
            to.append(float(np.sum(np.abs(E*w-values))/gross)); equity=E; shares=equity*w/px
        first=i
        stop=ni if k+1<len(fills) else ni+1
        for j in range(first,stop):
            if dates[j]<=end: marks.append((dates[j],float(np.sum(shares*close[np.arange(len(ix)),j]))))
    if marks:
        d,v=marks[-1]; marks[-1]=(d,v*(1-COST))
    mark_dates=[d for d,_ in marks]; vals=np.array([v for _,v in marks]); first=next(j for j,d in enumerate(mark_dates) if d>=start); base=1.0 if first==0 else vals[first-1]; pv=vals[first:]; daily=np.r_[pv[0]/base-1,pv[1:]/pv[:-1]-1]; years=max(len(daily)/252,1/252)
    period_fills=[(v,d) for v,d in zip(to,fills) if d>=start]
    return {"ann":(pv[-1]/base)**(1/years)-1,"sharpe":daily.mean()/daily.std(ddof=0)*math.sqrt(252),"turnover":float(np.mean([v for v,d in period_fills])),"daily":daily,"marks":marks}


if __name__ == "__main__":
    main()
