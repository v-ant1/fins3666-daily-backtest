"""Network-component research harness. Imports the unchanged strategy module and
swaps only the 'heat' auxiliary score (monkeypatch), so all fills/costs/buffer
rules are identical. Usage: python network_research.py recent|earlier"""
import sys, math, json
WIN = sys.argv[1]
if WIN == 'earlier':
    sys.argv = ['x', '--cost=actual', '--buffer=8', '--roster=2020-08-31', '--anchor=2020-11-27',
                '--win-first=2020-11-27', '--win-last=2024-02-23', '--tag=netres_e']
else:
    sys.argv = ['x', '--cost=actual', '--buffer=8', '--tag=netres_r']
import numpy as np
from scipy.linalg import expm
from scipy.stats import spearmanr
import pressure_heat_backtest_daily as M

SECTOR = {'AAPL':'IT','MSFT':'IT','CSCO':'IT','IBM':'IT','INTC':'IT','CRM':'IT','NVDA':'IT',
          'AXP':'FIN','GS':'FIN','JPM':'FIN','TRV':'FIN','V':'FIN',
          'AMGN':'HC','JNJ':'HC','MRK':'HC','UNH':'HC',
          'KO':'ST','PG':'ST','WMT':'ST','WBA':'ST',
          'HD':'CD','MCD':'CD','NKE':'CD','AMZN':'CD',
          'BA':'IND','CAT':'IND','HON':'IND','MMM':'IND',
          'CVX':'EN','DOW':'MAT','SHW':'MAT','DIS':'COM','VZ':'COM'}
T = M.DOW30; n = len(T)

def topk_graph(Cm, sym=True):
    Wg = np.zeros((n, n))
    for a in range(n):
        order = np.argsort(-Cm[a])
        keep = [b for b in order if b != a and Cm[a, b] > 0][:M.K]
        for b in keep:
            Wg[a, b] = Cm[a, b]
            if sym: Wg[b, a] = Cm[a, b]
    return Wg

def kernel(Wg, x, tau):
    H = expm(-tau * (np.diag(Wg.sum(1)) - Wg)); np.fill_diagonal(H, 0.0); den = H.sum(1)
    return {t: float(H[i] @ x / den[i]) for i, t in enumerate(T) if den[i] > M.HEAT_FLOOR}

def wmean(Wg, x):
    return {t: float(Wg[i] @ x / Wg[i].sum()) for i, t in enumerate(T) if Wg[i].sum() > 0}

def zs(v): return (v - v.mean()) / v.std()

def make_aux(name):
    def aux(z, rw):
        dm = rw - rw.mean(axis=0, keepdims=True)
        Cm = np.corrcoef(dm); Wg = topk_graph(Cm)
        r5 = zs(dm[:, -5:].sum(1))          # demeaned 5-session return, z-scored
        if name.startswith('heat_tau'): out = kernel(Wg, z, float(name[8:]))
        elif name == 'nbr': out = wmean(Wg, z)
        elif name == 'leadlag_p':      # leaders' pressure: edge a<-b if corr(r_b,t-1 , r_a,t)>0
            L = np.array([[np.corrcoef(dm[a, 1:], dm[b, :-1])[0, 1] for b in range(n)] for a in range(n)])
            out = wmean(topk_graph(L, sym=False), z)
        elif name == 'leadlag_r':      # leaders' latest 1-day demeaned return (Lo-MacKinlay/Hou lead-lag)
            L = np.array([[np.corrcoef(dm[a, 1:], dm[b, :-1])[0, 1] for b in range(n)] for a in range(n)])
            out = wmean(topk_graph(L, sym=False), zs(dm[:, -1]))
        elif name == 'sector_p':
            out = {}
            for i, t in enumerate(T):
                peers = [j for j, u in enumerate(T) if u != t and SECTOR[u] == SECTOR[t]]
                if peers: out[t] = float(np.mean(z[peers]))
        elif name == 'sector_r':
            out = {}
            for i, t in enumerate(T):
                peers = [j for j, u in enumerate(T) if u != t and SECTOR[u] == SECTOR[t]]
                if peers: out[t] = float(np.mean(r5[peers]))
        elif name == 'heat_ret': out = kernel(Wg, r5, 1.0)       # peer momentum on correlation graph
        elif name == 'resid_rev':      # own 5d return minus kernel peer return, reversed (catch-up)
            k = kernel(Wg, r5, 1.0); out = {t: k[t] - r5[i] for i, t in enumerate(T) if t in k}
        else: raise ValueError(name)
        return M.pct_ranks(out)
    return aux

VARIANTS = ['heat_tau1.0', 'heat_tau0.5', 'heat_tau2.0', 'nbr', 'leadlag_p', 'leadlag_r',
            'sector_p', 'sector_r', 'heat_ret', 'resid_rev']

ctx = M.load_all(); dates, ho, hc, C, V, Hh, Ll, spy = ctx
M.HhL = (Hh, Ll); didx = {d: i for i, d in enumerate(dates)}
grid = [d for d in dates if M.ANCHOR <= d][::M.REB_EVERY]
fills = [d for d in grid if M.WIN_FIRST <= d <= M.WIN_LAST]
sigs = [[d for d in dates if d < e][-1] for e in fills]

# ---- IC: rank corr of score with next-period open-to-open return (vs EW is rank-invariant)
ic = {k: [] for k in ['pressure'] + VARIANTS}
for k in range(len(fills) - 1):
    iT = didx[sigs[k]]; e, x = fills[k], fills[k + 1]
    own, z, ret = M.pressure_signals(iT, dates, ho, hc, C, V)
    fwd = np.array([ho[t][x] / ho[t][e] - 1 for t in T])
    rw = ret[:, iT - M.CORR_LB:iT]
    ic['pressure'].append((e, spearmanr([own[t] for t in T], fwd)[0]))
    for v in VARIANTS:
        a = make_aux(v)(z, rw); ts = [t for t in T if t in a]
        ic[v].append((e, spearmanr([a[t] for t in ts], [fwd[T.index(t)] for t in ts])[0]))

# ---- backtests: swap heat term, run mode heat50
def daily(marks):
    eq = np.array([1.0] + [v for _, v in marks]); return [d for d, _ in marks], np.diff(eq) / eq[:-1]
res = {}
for mode, aux in [('ew', None), ('pressure', None)] + [('heat50', v) for v in VARIANTS]:
    if aux:
        f = make_aux(aux); M.heat_scores = lambda z, rw, f=f: (f(z, rw), {}, 0)
    out = M.run(mode, 0.0005, ctx)
    d, r = daily(out[1]); res[aux or mode] = (d, r.tolist(), float(np.mean(out[5])))
json.dump({'ic': ic, 'bt': res}, open(f'netres_{WIN}.json', 'w'))
print('done', WIN, len(fills))
