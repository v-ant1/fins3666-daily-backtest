import json, numpy as np, math
rng=np.random.default_rng(0)
E=json.load(open('netres_earlier.json')); R=json.load(open('netres_recent.json'))
P={'IS 2020-11..2022-12':(E,'2020','2022-12-31'),'OOS1 2023-01..2024-02':(E,'2023-01-01','2024-12'),'OOS2 2024-12..2025-12':(R,'2024','2026')}
keys=list(E['ic'])
print('### IC (mean, t, n) by period; also by calendar year')
for k in keys:
    row=[]
    for p,(D,a,b) in P.items():
        x=np.array([v for d,v in D['ic'][k] if a<=d<b and v==v]); row.append(f"{x.mean():+.3f} (t {x.mean()/x.std(ddof=1)*math.sqrt(len(x)):+.2f}, n{len(x)})")
    yrs=[]
    for y in ['2021','2022','2023','2025']:
        D=R if y=='2025' else E
        x=np.array([v for d,v in D['ic'][k] if d.startswith(y) and v==v]); yrs.append(f"{y}:{x.mean():+.3f}")
    print(f"| {k} | "+" | ".join(row)+" | "+" ".join(yrs)+" |")
def bb(x,L=10,B=5000):
    n=len(x); m=[]
    for _ in range(B):
        idx=np.concatenate([np.arange(s,s+L)%n for s in rng.integers(0,n,n//L+1)])[:n]; m.append(x[idx].mean())
    m=np.array(m); return (m<=0).mean()
print('\n### backtest: ann ret / Sharpe / excess vs EW ann / t / bootstrap p(one-sided) / turnover')
for k in ['ew','pressure']+keys[1:]:
    row=[]
    for p,(D,a,b) in P.items():
        d=np.array(D['bt'][k][0]); r=np.array(D['bt'][k][1]); m=(d>=a)&(d<b)
        ew=np.array(D['bt']['ew'][1])[m]; r=r[m]; ex=r-ew
        ann=np.prod(1+r)**(252/len(r))-1; sh=r.mean()/r.std()*math.sqrt(252)
        t=ex.mean()/ex.std(ddof=1)*math.sqrt(len(ex)) if k!='ew' else 0
        p_=bb(ex) if k!='ew' else float('nan')
        row.append(f"{ann*100:+.1f}%/{sh:.2f}/{ex.mean()*25200:+.1f}%/t{t:+.2f}/p{p_:.2f}")
    print(f"| {k} | "+" | ".join(row)+f" | to {D['bt'][k][2]*100:.0f}% |")
