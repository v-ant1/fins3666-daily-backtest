"""Reconstruct L1's original pressure signal from development daily bars."""
import csv
import unittest
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

from r4_harness.phase3 import cross_sectional_ic

ROOT=Path(__file__).resolve().parents[2]
DATA=[ROOT/'repo'/d for d in ('prices-daily-lookback','prices-daily','prices-daily-delisted')]
START,END,SAFE='2020-11-27','2026-10-30','2020-06-01'
OLD=['AAPL','AMGN','AXP','BA','CAT','CRM','CSCO','CVX','DIS','DOW','GS','HD','HON','IBM','INTC','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','PG','TRV','UNH','V','VZ','WBA','WMT']
MID=['AAPL','AMGN','AXP','AMZN','BA','CAT','CRM','CSCO','CVX','DIS','DOW','GS','HD','HON','IBM','INTC','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','PG','TRV','UNH','V','VZ','WMT']
NEW=['AAPL','AMGN','AXP','AMZN','BA','CAT','CRM','CSCO','CVX','DIS','GS','HD','HON','IBM','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','NVDA','PG','SHW','TRV','UNH','V','VZ','WMT']


def load(ticker):
    out={}
    for folder in DATA:
        path=folder/f'{ticker}.csv'
        if not path.exists(): continue
        with path.open(newline='') as f:
            for row in csv.DictReader(f):
                d=row['date'][:10]
                if d<SAFE or d>END: continue
                close=float(row['adjclose']); factor=close/float(row['close'])
                out[d]=(float(row['open'])*factor,float(row['high'])*factor,float(row['low'])*factor,close,float(row['volume'] or 0))
    return out


def roster(d):
    if d<'2024-02-26': return OLD
    if d<'2024-11-08': return MID
    return NEW


def average_ranks(values): return (rankdata(values,method='average')-1)/(len(values)-1)


def reconstruct_pressure():
    names=sorted(set(OLD+MID+NEW)); bars={t:load(t) for t in names}; spy=load('SPY')
    dates=sorted(d for d in spy if SAFE<=d<=END); index={d:i for i,d in enumerate(dates)}
    close={t:np.array([bars[t].get(d,(np.nan,)*5)[3] for d in dates]) for t in names}
    opn={t:np.array([bars[t].get(d,(np.nan,)*5)[0] for d in dates]) for t in names}
    high={t:np.array([bars[t].get(d,(np.nan,)*5)[1] for d in dates]) for t in names}
    low={t:np.array([bars[t].get(d,(np.nan,)*5)[2] for d in dates]) for t in names}
    vol={t:np.array([bars[t].get(d,(np.nan,)*5)[4] for d in dates]) for t in names}
    scores=np.full((len(names),len(dates)),np.nan); asset_index={t:i for i,t in enumerate(names)}
    for i,d in enumerate(dates):
        if d<START or i<63: continue
        universe=roster(d); clv=[]; svol=[]; oi=[]
        for t in universe:
            clv.append(np.mean([((close[t][j]-low[t][j])-(high[t][j]-close[t][j]))/(high[t][j]-low[t][j]) if high[t][j]>low[t][j] else 0.0 for j in range(i-4,i+1)]))
            ret=close[t][1:]/close[t][:-1]-1
            svol.append(np.sum(np.sign(ret[i-5:i])*vol[t][i-4:i+1])/np.mean(vol[t][i-24:i+1]))
            intra=sum(close[t][j]/opn[t][j]-1 for j in range(i-4,i+1))
            overnight=sum(opn[t][j]/close[t][j-1]-1 for j in range(i-4,i+1))
            oi.append(intra-overnight)
        blend=(average_ranks(clv)+average_ranks(svol)+average_ranks(oi))/3
        for t,x in zip(universe,blend): scores[asset_index[t],i]=x
    return scores,close,opn,dates


class L1ReproductionTest(unittest.TestCase):
    def test_pressure_signal_matches_postmortem_to_3dp(self):
        baseline=ROOT/'r4_L1'/'rank_correlations.csv'
        self.assertTrue(baseline.is_file(),'L1 rank-correlation output is required for independent reproduction')
        with baseline.open(newline='') as f: expected={(r['signal'],r['return'],int(r['horizon_days'])):float(r['mean_IC']) for r in csv.DictReader(f) if r['signal']=='Pressure'}
        scores,close,opn,dates=reconstruct_pressure()
        c=np.vstack([close[t] for t in sorted(close)]); o=np.vstack([opn[t] for t in sorted(opn)])
        got=cross_sectional_ic(scores,c,[1,2,5,10,20],o)
        lookup={(r.return_type,r.horizon):r.mean_ic for r in got}
        for h in (1,2,5,10,20):
            for mode in ('C2C','Next O2C'):
                want=expected[('Pressure',mode,h)]; actual=lookup[(mode,h)]
                self.assertEqual(round(actual,3),round(want,3),f'{mode} {h}d got {actual} vs L1 {want}')
        print('PASS L1 original pressure rank correlations reproduce to 3 dp for both return bases and all five horizons')


if __name__=='__main__': unittest.main(verbosity=2)
