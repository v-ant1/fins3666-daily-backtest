#!/usr/bin/env python3
"""
pressure_heat_backtest_daily.py - DAILY-BAR version of the FINS3666
pressure+heat strategy. Robustness/extension test, NOT a replacement for the
hourly assignment test. Derived from pressure_heat_backtest.py v2 with ONLY
the data-frequency layer changed; every signal, portfolio, buffer, cost and
guard rule is identical at session level.

FREQUENCY-CHANGE DISCLOSURES (exactly what differs from the hourly version):
1. Session OHLCV come from the daily CSVs (adjusted via adjclose/close same-
   day factors, total-return consistent) instead of aggregated hourly bars.
2. SVOL volume is CONSOLIDATED daily volume; the hourly version's partial-tape
   volume limitation does not apply here. This is a data-quality difference,
   not a parameter change.
3. Fills are the daily OPEN of T+1 - the same concept as the hourly version's
   first-hourly-bar open of T+1 (same consolidated open print).
4. CLV/OI are computed on daily bars; by construction daily H/L/C equal the
   hourly-aggregated session H/L/C the hourly version used.
No parameter, lookback, blend, buffer or cost changes.

UNIVERSES (point-in-time, known at signal time, S&P DJI primary sources):
- 2024-11-08 roster (default): as the hourly version (release 20241101-1475162).
- 2020-08-31 roster: CRM/AMGN/HON replaced XOM/PFE/RTX effective 2020-08-31
  (S&P DJI release, announced 2020-08-24). The 2024-02-26 AMZN/WBA swap
  (release 20240220-1470711) and the 2024-11-08 NVDA/SHW swap chain this to
  the 2024-11-08 roster, so the 2020-08-31 roster is valid 2020-08-31..
  2024-02-25 and the earlier window ENDS 2024-02-23 (last session before the
  AMZN/WBA effective date). The roster is never used before its effective
  date: signals at T >= 2020-08-31 only.
- Earlier-window first fill is the first session with a complete 63-return
  graph lookback for ALL 30 names (WBA's recovered history starts 2020-08-27,
  which sets the data start; first fill lands ~2020-11-30). No name dropped.

GUARDS (unchanged from hourly version): synthetic cost self-test at import;
future-truncation invariance test on sampled signal dates; fail-fast on ANY
missing open/close/volume for a used session; union actual-cost solve with
independent per-share notional check and budget check; ledger-to-equity
reconciliation (tol 1e-6); session calendar asserted == SPY calendar.
"""
import csv, os, sys, time, math
import numpy as np
from scipy.linalg import expm

ROSTERS={
 'xasset30':'SHY IEF TLT TIP LQD HYG MUB EMB BWX GLD SLV PPLT USO UNG DBA DBB UUP FXE FXY FXB FXA FXC VNQ RWX IWM VGK EWJ EWA EWC EEM'.split(),
 '2024-11-08':['AAPL','AMGN','AXP','AMZN','BA','CAT','CRM','CSCO','CVX','DIS','GS','HD','HON','IBM','JNJ',
               'JPM','KO','MCD','MMM','MRK','MSFT','NKE','NVDA','PG','SHW','TRV','UNH','V','VZ','WMT'],
 '2020-08-31':['AAPL','AMGN','AXP','BA','CAT','CRM','CSCO','CVX','DIS','DOW','GS','HD','HON','IBM','INTC','JNJ',
               'JPM','KO','MCD','MMM','MRK','MSFT','NKE','PG','TRV','UNH','V','VZ','WBA','WMT'],
}
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K=5; TAU=1.0; HEAT_FLOOR=0.05; CORR_LB=63; TOP_N=5; W=1.0/TOP_N

# ---- CLI ----
ROSTER_KEY='2024-11-08'; ANCHOR='2024-12-06'; WIN_FIRST='2024-12-06'; WIN_LAST='2025-12-31'
COST_MODE='full'; BUFFER=None; REB_EVERY=5; TAG='daily_dev'
MODE='legacy'; CONSTRUCT='top5'; TILT_A=0.5
for a in sys.argv:
    if a.startswith('--roster='):  ROSTER_KEY=a.split('=')[1]
    if a.startswith('--anchor='):  ANCHOR=a.split('=')[1]
    if a.startswith('--win-first='): WIN_FIRST=a.split('=')[1]
    if a.startswith('--win-last='):  WIN_LAST=a.split('=')[1]
    if a.startswith('--cost='):    COST_MODE=a.split('=')[1]
    if a.startswith('--buffer='):  BUFFER=int(a.split('=')[1])
    if a.startswith('--reb='):     REB_EVERY=int(a.split('=')[1])
    if a.startswith('--tag='):     TAG=a.split('=')[1]
    if a.startswith('--mode='):    MODE=a.split('=')[1]
    if a.startswith('--construct='): CONSTRUCT=a.split('=')[1]
    if a.startswith('--a='):       TILT_A=float(a.split('=')[1])
DOW30=ROSTERS[ROSTER_KEY]

# ---- data ----
def load_daily_merged(t):
    """Merged adjusted daily series across lookback/main/delisted dirs."""
    out={}
    for d in ['prices-daily-lookback','prices-daily','prices-daily-delisted']:
        p=os.path.join(BASE,d,t+'.csv')
        if not os.path.exists(p): continue
        for r in csv.DictReader(open(p)):
            dt=r['date'][:10]
            try:
                o,h,l,c,a=float(r['open']),float(r['high']),float(r['low']),float(r['close']),float(r['adjclose'])
            except (TypeError,ValueError): continue
            f=a/c if c else 1.0
            out[dt]={'ao':o*f,'ah':h*f,'al':l*f,'ac':a,'v':float(r['volume'] or 0)}
    return out

def load_all():
    data={t:load_daily_merged(t) for t in DOW30}
    spy={}
    for d in ['prices-daily-lookback','prices-daily']:
        p=os.path.join(BASE,d,'SPY.csv')
        if os.path.exists(p):
            for r in csv.DictReader(open(p)):
                spy[r['date'][:10]]={'ao':float(r['open']),'ac':float(r['adjclose'])}
    data_start=max(min(data[t]) for t in DOW30)     # binding constraint printed
    binder=max(DOW30, key=lambda t:min(data[t]))
    dates=[d for d in sorted(spy) if data_start<=d<=WIN_LAST]   # sessions past window end never read (delisted names end there)
    print(f"[audit] roster {ROSTER_KEY}; data start {data_start} (binding: {binder}); sessions available {len(dates)} ({dates[0]}..{dates[-1]})")
    for t in DOW30:
        missing=[d for d in dates if d not in data[t]]
        if missing:
            raise AssertionError(f'FAIL-FAST: {t} missing {len(missing)} sessions (e.g. {missing[:3]}) - no name dropped, run blocked')
    n=len(DOW30)
    C=np.array([[data[t][d]['ac'] for d in dates] for t in DOW30])
    V=np.array([[data[t][d]['v']  for d in dates] for t in DOW30])
    Hh=np.array([[data[t][d]['ah'] for d in dates] for t in DOW30])
    Ll=np.array([[data[t][d]['al'] for d in dates] for t in DOW30])
    ho={t:{d:data[t][d]['ao'] for d in dates} for t in DOW30}
    hc={t:{d:data[t][d]['ac'] for d in dates} for t in DOW30}
    zero_v=int((V==0).sum())
    print(f"[audit] daily bars {C.size}, zero-volume sessions {zero_v}")
    if zero_v or np.isnan(C).any():
        raise AssertionError('FAIL-FAST: zero/NaN cells in used window - run blocked')
    return dates,ho,hc,C,V,Hh,Ll,spy

# ---- signals (identical to hourly version) ----
def pct_ranks(vals):
    items=sorted(vals.items(), key=lambda kv:(kv[1],kv[0])); n=len(items); out={}; i=0
    while i<n:
        j=i
        while j+1<n and items[j+1][1]==items[i][1]: j+=1
        r=(i+j)/2/(n-1) if n>1 else 0.5
        for k in range(i,j+1): out[items[k][0]]=r
        i=j+1
    return out

HhL=None
def pressure_signals(iT, dates, ho, hc, C, V):
    n=len(DOW30)
    ret=C[:,1:]/C[:,:-1]-1.0
    clv5={}; svol={}; oi={}
    for ti,t in enumerate(DOW30):
        clvs=[]
        for i in range(iT-4,iT+1):
            h=HhL[0][ti][i]; l=HhL[1][ti][i]; c=C[ti,i]
            clvs.append(((c-l)-(h-c))/(h-l) if (h is not None and l is not None and h>l) else 0.0)
        clv5[t]=float(np.mean(clvs))
        rets=np.sign(ret[ti,iT-5:iT])
        denom=V[ti,iT-24:iT+1].mean()
        svol[t]=float((rets*V[ti,iT-4:iT+1]).sum()/denom) if denom>0 else 0.0
        intra=0.0; over=0.0
        for i in range(iT-4,iT+1):
            d=dates[i]; dp=dates[i-1]
            fo=ho[t].get(d); lc=hc[t].get(d); plc=hc[t].get(dp)
            if fo and lc: intra+=lc/fo-1.0
            if fo and plc: over+=fo/plc-1.0
        oi[t]=intra-over
    pr_c,pr_s,pr_o=pct_ranks(clv5),pct_ranks(svol),pct_ranks(oi)
    own={t:(pr_c[t]+pr_s[t]+pr_o[t])/3.0 for t in DOW30}
    z=np.array([own[t] for t in DOW30]); z=(z-z.mean())/z.std()
    return own,z,ret

def heat_scores(z, ret_window):
    n=len(DOW30)
    dm=ret_window-ret_window.mean(axis=0,keepdims=True)
    Cm=np.corrcoef(dm)
    Wg=np.zeros((n,n))
    for a in range(n):
        order=np.argsort(-Cm[a])
        keep=[b for b in order if b!=a and Cm[a,b]>0][:K]
        for b in keep: Wg[a,b]=Cm[a,b]; Wg[b,a]=Cm[a,b]
    H=expm(-TAU*(np.diag(Wg.sum(1))-Wg))
    np.fill_diagonal(H,0.0)
    den=H.sum(1)
    heat={t:float((H[ti]@z)/den[ti]) for ti,t in enumerate(DOW30) if den[ti]>HEAT_FLOOR}
    nbr={}
    for ti,t in enumerate(DOW30):
        ws=Wg[ti]; tot=ws.sum()
        if tot>0: nbr[t]=float((ws@z)/tot)
    return pct_ranks(heat), pct_ranks(nbr), int((Wg>0).sum()/2)

def graph_scores(z, ret_window):
    """Auxiliary ranks used by the added research modes; windows end at signal T."""
    n=len(DOW30)
    dm=ret_window-ret_window.mean(axis=0,keepdims=True)
    Cm=np.corrcoef(dm)
    Wg=np.zeros((n,n))
    for a in range(n):
        order=np.argsort(-Cm[a])
        keep=[b for b in order if b!=a and Cm[a,b]>0][:K]
        for b in keep: Wg[a,b]=Cm[a,b]; Wg[b,a]=Cm[a,b]
    # Residual reversal: five-session market-demeaned peer return less own return.
    r5=dm[:,-5:].sum(axis=1)
    peer=np.divide(Wg@r5,Wg.sum(1),out=np.zeros(n),where=Wg.sum(1)>0)
    resrev=pct_ranks({t:float(peer[i]-r5[i]) for i,t in enumerate(DOW30)})
    # Directed leader graph: corr(leader return at t-1, target return at t).
    L=np.zeros((n,n))
    for target in range(n):
        for leader in range(n):
            if target==leader: continue
            x,y=dm[target,1:],dm[leader,:-1]
            if x.std()>0 and y.std()>0: L[target,leader]=float(np.corrcoef(x,y)[0,1])
    lead=np.zeros_like(L)
    for target in range(n):
        keep=[j for j in np.argsort(-L[target]) if j!=target and L[target,j]>0][:K]
        for j in keep: lead[target,j]=L[target,j]
    leader_pressure=np.divide(lead@z,lead.sum(1),out=np.zeros(n),where=lead.sum(1)>0)
    leadlag=pct_ranks({t:float(leader_pressure[i]) for i,t in enumerate(DOW30)})
    return resrev,leadlag

def signal_ranks(mode, sig, dates, ho, hc, C, V, Hh=None, Ll=None):
    """Return cross-sectional rank scores for one mode at one signal date."""
    iT={d:i for i,d in enumerate(dates)}[sig]
    own,z,ret=pressure_signals(iT,dates,ho,hc,C,V)
    pr_own=pct_ranks(own)
    if mode=='pressure': return pr_own
    if mode=='rev21':
        r21=C[:,iT]/C[:,iT-21]-1.0
        return pct_ranks({t:float(-r21[i]) for i,t in enumerate(DOW30)})
    heat,nbr,_=heat_scores(z,ret[:,iT-CORR_LB:iT])
    if mode=='heat50': aux=heat
    elif mode=='nbr50': aux=nbr
    elif mode in ('resrev50','leadlag50'):
        resrev,leadlag=graph_scores(z,ret[:,iT-CORR_LB:iT])
        aux=resrev if mode=='resrev50' else leadlag
    elif mode=='ew': return {t:0.5 for t in DOW30}
    else: raise ValueError(f'unknown mode {mode}')
    out={}
    for t in DOW30:
        if t in aux: out[t]=0.5*pr_own[t]+0.5*aux[t]
        else: out[t]=pr_own[t]
    return out

def construct_weights(ranks, construct='top5', shares=None):
    if construct=='tilt':
        return {t:(1.0/len(DOW30))*(1.0+TILT_A*(2.0*r-1.0)) for t,r in ranks.items()}
    order=sorted(ranks,key=lambda t:(-ranks[t],t))
    if BUFFER is not None and shares is not None:
        pos={t:i+1 for i,t in enumerate(order)}
        keep=[t for t in shares if pos[t]<=BUFFER]
        drop_n=TOP_N-len(keep)
        chall=[t for t in order if t not in shares][:drop_n]
        top=keep+chall
    else: top=order[:TOP_N]
    return {t:W for t in top}

# ---- backtest (identical rules) ----
def run(mode,cost,ctx,construct='top5'):
    dates,ho,hc,C,V,Hh,Ll,spy=ctx
    didx={d:i for i,d in enumerate(dates)}
    grid=[d for d in dates if ANCHOR<=d][::REB_EVERY]
    fills=[d for d in grid if WIN_FIRST<=d<=WIN_LAST]
    sigs=[[d for d in dates if d<e][-1] for e in fills]
    assert didx[sigs[0]]>=CORR_LB, f'first signal {sigs[0]} lacks 63-session graph lookback'
    cal=[d for d in dates if fills[0]<=d<=WIN_LAST]
    spy_cal=[d for d in sorted(spy) if fills[0]<=d<=WIN_LAST]
    assert cal==spy_cal, f'calendar mismatch vs SPY: {len(cal)} vs {len(spy_cal)}'
    equity=1.0; marks=[]; ledger=[]; picks=[]; turnovers=[]
    seg_factors=[]; cost_detail=[]
    floor_trips=[0]
    shares=None; sig_cache={}
    def fill_open(t,d):
        px=ho[t].get(d)
        if px is None:
            raise AssertionError(f'FAIL-FAST: no daily open for {t} on fill session {d} - run blocked')
        return px,d
    for k,(sig,e) in enumerate(zip(sigs,fills)):
        nxt=fills[k+1] if k+1<len(fills) else None
        xd=nxt if nxt else WIN_LAST
        final=(nxt is None)
        if mode=='ew':
            wts={t:1.0/len(DOW30) for t in DOW30}
        else:
            if sig not in sig_cache:
                sig_cache[sig]=signal_ranks(mode,sig,dates,ho,hc,C,V,Hh,Ll)
            ranks=sig_cache[sig]
            if construct=='tilt':
                wts=construct_weights(ranks,'tilt')
            elif construct=='top5':
                wts=construct_weights(ranks,'top5',shares)
            else: raise ValueError(f'unknown construction {construct}')
        if shares is not None:
            vals={}
            for t,sh in shares.items():
                px,_=fill_open(t,e)
                vals[t]=sh*px
            gross=sum(vals.values())
            old_names=set(shares); turnovers.append(len(set(wts)-old_names)/TOP_N)
            if COST_MODE=='actual':
                union=set(vals)|set(wts)
                E=gross
                for _ in range(500):
                    E_new=gross-cost*sum(abs(E*wts.get(t,0.0)-vals.get(t,0.0)) for t in union)
                    if abs(E_new-E)<1e-15*max(1.0,gross): E=E_new; break
                    E=E_new
                notional=sum(abs(E*wts.get(t,0.0)-vals.get(t,0.0)) for t in union)
                cost_paid=gross-E
                assert cost_paid>=-1e-12*gross and E>0, 'actual-cost solve failed'
                px_open={t:fill_open(t,e)[0] for t in union}
                notional_chk=sum(abs(E*wts.get(t,0.0)-shares.get(t,0.0)*px_open[t]) for t in union)
                assert abs(notional_chk-notional)<1e-9*max(1.0,gross), f'{e}: independent notional check {notional_chk:.10f} vs solve {notional:.10f}'
                assert abs(cost_paid-cost*notional)<1e-9*max(1.0,gross), f'{e}: budget check cost {cost_paid:.10f} vs c*notional {cost*notional:.10f}'
                equity=E
            else:
                cost_paid=gross*(1-(1-cost)/(1+cost))
                notional=cost_paid/cost
                equity=gross*(1-cost)/(1+cost)
            seg_factors.append(equity/gross)
            cost_detail.append((e,gross,notional,cost_paid,equity/gross))
        else:
            equity*=1.0/(1+cost)
            seg_factors.append(1.0/(1+cost))
            cost_detail.append((e,1.0,equity,1.0-equity,1.0/(1+cost)))
        entry_px={}; actual_dates={}
        for t in wts:
            px,dd=fill_open(t,e)
            entry_px[t]=px; actual_dates[t]=dd
        shares={t:equity*w/entry_px[t] for t,w in wts.items()}
        picks.append((e,sorted(wts)))
        seg_entry_px=dict(entry_px)
        seg=[d for d in cal if e<=d<=xd]
        for d in seg:
            if d==xd and not final:
                continue
            vals=[]
            for t,sh in shares.items():
                lc=hc[t].get(d)
                if lc is None:
                    raise AssertionError(f'FAIL-FAST: no close mark for {t} on session {d} - run blocked')
                vals.append(sh*lc)
            v=sum(vals)
            if d==xd and final:
                v*=(1-cost); equity=v
            marks.append((d,v))
        for t in wts:
            if final: xp=hc[t].get(xd, seg_entry_px[t])
            else:
                xp,_fd=fill_open(t,xd)
                if xp is None: xp=seg_entry_px[t]
            ledger.append((e,actual_dates[t],xd,t,seg_entry_px[t],xp,wts[t]))
    assert len(marks)==len(cal), f'marks {len(marks)} != sessions {len(cal)}'
    md=[d for d,_ in marks]; assert len(md)==len(set(md)), 'duplicate marks!'
    recon=1.0; segmap={}
    for e,ad,xd,t,pe,px,wt in ledger: segmap.setdefault((e,xd),[]).append((t,pe,px,wt))
    final_key=(fills[-1],WIN_LAST)
    for si,((e,xd),rows) in enumerate(segmap.items()):
        r=sum(wt*(px/pe) for _,pe,px,wt in rows)
        cd_row=[q for q in cost_detail if q[0]==e]
        assert len(cd_row)==1
        g,ntl,pd=cd_row[0][1],cd_row[0][2],cd_row[0][3]
        if si==0:
            fac_chk=1.0/(1+cost); assert abs(pd-(1.0-fac_chk))<1e-9, f'{e}: initial fee {pd} != c/(1+c)'
        else:
            assert abs(pd-cost*ntl)<1e-9*max(1.0,g), f'{e}: ledger budget cost {pd} != c*notional {cost*ntl}'
            fac_chk=1.0-pd/g
        assert abs(fac_chk-seg_factors[si])<1e-9, f'{e}: factor mismatch {fac_chk} vs {seg_factors[si]}'
        recon*=r*fac_chk
        if (e,xd)==final_key: recon*=(1-cost)
    final_mark=marks[-1][1]
    assert abs(recon-final_mark)<1e-6*max(1,abs(final_mark)), f'reconciliation failed: ledger {recon:.8f} vs marks {final_mark:.8f}'
    return equity,marks,ledger,picks,cal,turnovers,floor_trips[0],cost_detail

def metrics(marks):
    eq=[1.0]+[v for _,v in marks]
    r=np.diff(eq)/eq[:-1]
    vol=float(r.std(ddof=0)*math.sqrt(252))
    peak=1.0; mdd=0.0
    for v in eq: peak=max(peak,v); mdd=min(mdd,v/peak-1.0)
    sh=float(r.mean()/r.std(ddof=0)*math.sqrt(252)) if r.std(ddof=0)>0 else 0.0
    return eq[-1]-1.0,vol,mdd,sh

def _selftest_cost():
    def solve(vals,wts,cost):
        gross=sum(vals.values()); union=set(vals)|set(wts); E=gross
        for _ in range(500):
            E_new=gross-cost*sum(abs(E*wts.get(t,0.0)-vals.get(t,0.0)) for t in union)
            if abs(E_new-E)<1e-15*max(1.0,gross): E=E_new; break
            E=E_new
        notional=sum(abs(E*wts.get(t,0.0)-vals.get(t,0.0)) for t in union)
        return E,notional,gross-E
    c=0.0005
    E,n,paid=solve({t:0.2 for t in 'ABCDE'},{t:0.2 for t in 'ABCDE'},c)
    assert abs(n)<1e-12 and abs(paid)<1e-12 and abs(E-1.0)<1e-12, 'selftest1 no-drift failed'
    E,n,paid=solve({t:0.2 for t in 'ABCDE'},{t:0.2 for t in 'FGHIJ'},c)
    assert abs(E-(1-c)/(1+c))<1e-12 and abs(n-(1.0+E))<1e-9, f'selftest2 full-replacement failed: E={E} n={n}'
    E,n,paid=solve({'A':0.4,'B':0.15,'C':0.15,'D':0.15,'E':0.15},{t:0.2 for t in 'ABCDE'},c)
    assert 0.39<n<0.41 and abs(paid-c*n)<1e-12, f'selftest3 stayer-drift failed: n={n}'
    E,n,paid=solve({t:0.2 for t in 'ABCDE'},{**{t:0.2 for t in 'ABCD'},'F':0.2},c)
    assert n>0.39, f'selftest4 leaver-sell-missing: notional {n} (would be ~0.2 if sale free)'
    print('[selftest] actual-cost engine: no-drift=0, full-replacement==(1-c)/(1+c), stayer-drift charged, leaver-sell charged - PASS')

_selftest_cost()

if __name__=='__main__':
    T0=time.perf_counter()
    ctx=load_all()
    dates,ho,hc,C,V,Hh,Ll,spy=ctx
    HhL=(Hh,Ll)
    didx={d:i for i,d in enumerate(dates)}
    grid=[d for d in dates if ANCHOR<=d][::REB_EVERY]
    fills=[d for d in grid if WIN_FIRST<=d<=WIN_LAST]
    sigs=[[d for d in dates if d<e][-1] for e in fills]
    assert didx[sigs[0]]>=CORR_LB, f'first signal {sigs[0]} (idx {didx[sigs[0]]}) lacks 63-session graph lookback - extend data or move WIN_FIRST'
    # FUTURE-TRUNCATION INVARIANCE TEST on 3 sampled grid signal dates
    sample=[sigs[0],sigs[len(sigs)//2],sigs[-1]]
    for sig in sample:
        iT=didx[sig]
        own0,z0,ret0=pressure_signals(iT,dates,ho,hc,C,V)
        rw=ret0[:,iT-CORR_LB:iT]
        h0,n0,_=heat_scores(z0,rw)
        rr0,ll0=graph_scores(z0,rw)
        Cp=C.copy(); Cp[:,iT+1:]=np.nan
        Vp=V.copy(); Vp[:,iT+1:]=np.nan
        hop={t:{d:v for d,v in ho[t].items() if d<=sig} for t in DOW30}
        hcp={t:{d:v for d,v in hc[t].items() if d<=sig} for t in DOW30}
        own1,z1,ret1=pressure_signals(iT,dates,hop,hcp,Cp,Vp)
        assert all(abs(own0[t]-own1[t])<1e-12 for t in DOW30), f'{sig}: pressure signals change when future is removed'
        rw1=ret1[:,iT-CORR_LB:iT]
        h1,n1,_=heat_scores(z1,rw1)
        assert set(h0)==set(h1) and all(abs(h0[t]-h1[t])<1e-12 for t in h0), f'{sig}: heat changes when future is removed'
        rr1,ll1=graph_scores(z1,rw1)
        for label,a,b in [('resrev50',rr0,rr1),('leadlag50',ll0,ll1)]:
            assert set(a)==set(b) and all(abs(a[t]-b[t])<1e-12 for t in a), f'{sig}: {label} changes when future is removed'
        for mode in ('pressure','heat50','nbr50','resrev50','leadlag50','rev21'):
            a=signal_ranks(mode,sig,dates,ho,hc,C,V,Hh,Ll)
            b=signal_ranks(mode,sig,dates,hop,hcp,Cp,Vp,Hh,Ll)
            assert set(a)==set(b) and all(abs(a[t]-b[t])<1e-12 for t in a), f'{sig}: {mode} changes when future is removed'
            for construct in ('top5','tilt'):
                wa=construct_weights(a,construct); wb=construct_weights(b,construct)
                assert set(wa)==set(wb) and all(abs(wa[t]-wb[t])<1e-12 for t in wa), f'{sig}: {mode}/{construct} weights change with future removed'
        print(f"[invariance] {sig}: all six signals and top5/tilt weights identical after future truncation - PASS")
    print(f"[grid] anchor {ANCHOR} every {REB_EVERY} sessions; fills {fills[0]} .. {fills[-1]} ({len(fills)} rebalances); window end {WIN_LAST}")
    tag=TAG
    if COST_MODE!='full': tag+=f'_{COST_MODE}cost'
    if BUFFER is not None: tag+=f'_buf{BUFFER}'
    outdir=os.path.join(BASE,'outputs_rerun')
    os.makedirs(outdir,exist_ok=True)
    legacy_modes=['pressure','heat50','nbr50','ew']
    modes=['pressure','heat50','nbr50','ew','resrev50','leadlag50','rev21']
    constructs=['top5','tilt'] if CONSTRUCT=='both' else [CONSTRUCT]
    if MODE=='legacy': modes=legacy_modes
    elif MODE!='all': modes=[MODE]
    variants=[(m,c) for m in modes for c in constructs]
    equity_series={}; run_details={}; cal=None
    print(f"[accounting] cost={COST_MODE}" + (f' buffer={BUFFER}' if BUFFER is not None else ''))
    for mode,construct in variants:
        key=f'{mode}_{construct}'
        eq,marks,ledger,picks,cal,to,ft,cd=run(mode,0.0005,ctx,construct)
        tr,vol_,mdd,sh=metrics(marks)
        avg_not=np.mean([r[2]/r[1] for r in cd[1:] if r[1]>0]) if len(cd)>1 else 0.0
        print(f"{key:20s} ret {tr*100:7.2f}% vol {vol_*100:5.1f}% maxDD {mdd*100:6.2f}% Sharpe {sh:5.2f} avg-notional {avg_not*100:5.1f}%/reb")
        with open(os.path.join(outdir,f'{tag}_{key}_costdetail.csv'),'w',newline='') as f:
            w=csv.writer(f); w.writerow(['rebalance_date','pretrade_equity','notional_traded','cost_paid','cost_factor'])
            for row in cd: w.writerow([row[0],f'{row[1]:.8f}',f'{row[2]:.8f}',f'{row[3]:.8f}',f'{row[4]:.8f}'])
        with open(os.path.join(outdir,f'{tag}_{key}_trades.csv'),'w',newline='') as f:
            w=csv.writer(f); w.writerow(['rebalance_date','actual_fill_date','exit_date','ticker','entry_px_adj','exit_px_adj','gross_ret','weight','cost_note'])
            for e,ad,xd,t,pe,px,wt in ledger:
                w.writerow([e,ad,xd,t,f'{pe:.4f}',f'{px:.4f}',f'{px/pe-1:.6f}',f'{wt:.8f}',f'DAILY-BAR version; cost={COST_MODE}; construct={construct}; buffer={BUFFER}; final leg +1 sell cost'])
        with open(os.path.join(outdir,f'{tag}_{key}_picks.txt'),'w') as f:
            for e,tk in picks: f.write(f"{e}: {','.join(tk)}\n")
        equity_series[key]=dict(marks)
        run_details[key]={'marks':marks,'turnovers':to,'cost_detail':cd,'picks':picks}
    spyc={d:v['ac'] for d,v in spy.items()}
    line=f"SPY buy-hold same window (close-to-close basis): {(spyc[WIN_LAST]/spyc[cal[0]]-1)*100:.2f}%   (marks {len(cal)} sessions, calendar asserted == SPY)"
    spyo=spy.get(fills[0],{}).get('ao')
    if spyo:
        line+=f"  | SPY open-of-first-fill to final-close basis: {(spyc[WIN_LAST]/spyo-1)*100:.2f}%"
    print(line)
    with open(os.path.join(outdir,f'{tag}_equity_variants.csv'),'w',newline='') as f:
        w=csv.writer(f); w.writerow(['date']+[f'{m}_{c}' for m,c in variants]+['ew','spy'])
        for d in cal:
            w.writerow([d]+[f'{equity_series[f"{m}_{c}"].get(d,float("nan")):.8f}' for m,c in variants]+[f'{spyc[d]/spyc[cal[0]]:.8f}'])
    # Fixed period metrics. Daily returns are computed before slicing, so each
    # period starts with the actual first close-to-close return in that period.
    bounds={'IS':('2020-11-27','2022-12-30'),'OOS1':('2023-01-03','2024-02-23'),'OOS2':('2024-12-06','2025-12-31')}
    periods=[(n,a,b) for n,(a,b) in bounds.items() if any(a<=d<=b for d in cal)]
    result_rows=[]
    def period_stats(key,lo,hi):
        marks=run_details[key]['marks']; dd={d:v for d,v in marks}
        daylist=[d for d in cal if lo<=d<=hi and d in dd]
        if not daylist: return None
        ix=[cal.index(d) for d in daylist]
        prev=1.0 if ix[0]==0 else dict(marks)[cal[ix[0]-1]]
        levels=[prev]+[dd[d] for d in daylist]
        rr=np.diff(levels)/np.array(levels[:-1])
        growth=float(np.prod(1+rr)); years=len(rr)/252.0
        cagr=growth**(1/years)-1 if growth>0 and years>0 else -1.0
        sharpe=float(rr.mean()/rr.std(ddof=0)*math.sqrt(252)) if rr.std(ddof=0)>0 else 0.0
        curve=np.r_[1.0,np.cumprod(1+rr)]; peak=np.maximum.accumulate(curve)
        mdd=float(np.min(curve/peak-1.0))
        cd=run_details[key]['cost_detail']
        costs=[row for row in cd if lo<=row[0]<=hi]
        logfac=sum(math.log(max(row[4],1e-15)) for row in costs)
        if hi==WIN_LAST: logfac+=math.log(1-0.0005)
        cost_drag=1-math.exp(logfac*252/max(1,len(rr)))
        to=[row[2]/row[1] for row in costs[1:] if row[1]>0]
        turnover=float(np.mean(to)) if to else 0.0
        return cagr,sharpe,mdd,turnover,cost_drag,len(rr)
    for pname,lo,hi in periods:
        ew=period_stats('ew_top5',lo,hi)
        for m,c in variants:
            key=f'{m}_{c}'; s=period_stats(key,lo,hi)
            if s is None: continue
            result_rows.append((key,pname,s[0],s[0]-ew[0],s[1],s[2],s[3],s[4],s[5]))
    with open(os.path.join(outdir,f'{tag}_period_results.csv'),'w',newline='') as f:
        w=csv.writer(f); w.writerow(['variant','period','CAGR','excess_CAGR_vs_EW30','Sharpe','maxDD','avg_turnover_notional_per_rebalance','annual_cost_drag','sessions'])
        for row in result_rows: w.writerow([row[0],row[1]]+[f'{x:.8f}' if isinstance(x,float) else x for x in row[2:]])
    print(f"[results] wrote {len(result_rows)} period-by-variant rows; equity CSV has daily benchmark and strategy columns")
    print(f"[{time.perf_counter()-T0:.2f}s] DONE - {tag} run, DAILY bars, same rules, no re-optimisation")
