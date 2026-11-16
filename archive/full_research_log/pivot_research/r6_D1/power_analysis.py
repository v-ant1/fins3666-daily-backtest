"""SIC-cluster power inputs and synthetic runs; consumes metadata plus FINRA signal ACF only."""
from pathlib import Path
import subprocess, sys
import numpy as np, pandas as pd, pandas_market_calendars as mcal
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'r6_D1'
START,END='2020-11-27','2026-10-30'
calendar=pd.DatetimeIndex(mcal.get_calendar('NYSE').schedule(START,END).index).tz_localize(None)

def active_group_counts(path, extra_googl=False):
    d=pd.read_csv(path,dtype={'ticker':str,'sic2':str})
    d['a']=pd.to_datetime(d.effective_from); d['b']=pd.to_datetime(d.effective_to_exclusive)
    result=[]
    for day in calendar:
        x=d[(d.a<=day)&(d.b>day)]
        groups=set(x.sic2.dropna().astype(str))
        groups.discard(''); groups.discard('nan')
        if extra_googl and day>=pd.Timestamp('2026-06-29'):
            groups.discard('48') # remove VZ's SIC2 after the Dow substitution
            groups.add('73')    # GOOGL's SEC SIC begins 7372
        result.append((day.date().isoformat(),x.ticker.nunique(),len(groups)))
    return pd.DataFrame(result,columns=['date','sic_covered_names','sic2_clusters'])

sp=active_group_counts(ROOT/'r6_C1'/'sp500_sic_membership.csv')
dow=active_group_counts(ROOT/'r6_C1'/'dow_sic_membership.csv',extra_googl=True)
sp.to_csv(OUT/'sp500_sic_cluster_counts.csv',index=False)
dow.to_csv(OUT/'dow_sic_cluster_counts.csv',index=False)
stat=pd.read_csv(ROOT/'r6_data'/'finra_regsho'/'signal_statistics.csv').set_index('universe')
rows=[]
for uni,cluster in [('SP500',sp),('DOW30',dow)]:
    gmin=int(cluster.sic2_clusters.min())
    median=int(cluster.sic2_clusters.median())
    rho=max(float(stat.loc[uni,'median_name_acf1']),float(stat.loc[uni,'universe_mean_signal_acf1']))
    rows.append({'universe':uni,'calendar_dates':len(calendar),'min_sic2_groups':gmin,'median_sic2_groups':median,
                 'sic_name_coverage_min':int(cluster.sic_covered_names.min()),'sic_name_coverage_median':int(cluster.sic_covered_names.median()),
                 'IC_SD_stress_1_over_sqrt_G_minus_1':1/np.sqrt(gmin-1),'signal_ACF1_stress_rho':rho,
                 'rho_note':'max(median name-level ACF1, universe mean short-volume-ratio ACF1); stress proxy, not IC autocorrelation'})
inputs=pd.DataFrame(rows)
inputs.to_csv(OUT/'power_inputs.csv',index=False)
power_log=OUT/'power_simulations.txt'
power_log.write_text('',encoding='utf-8')
print(inputs.to_string(index=False))
for row in rows:
    assets=500 if row['universe']=='SP500' else 30
    for hurdle in (.0183,.026):
        cmd=[sys.executable,str(ROOT/'r4_harness'/'power_sim.py'),'--assets',str(assets),'--dates',str(len(calendar)),
             '--horizon','5','--signal-autocorrelation',f"{row['signal_ACF1_stress_rho']:.8f}",
             '--ic-sd',f"{row['IC_SD_stress_1_over_sqrt_G_minus_1']:.8f}",'--mean-ic',str(hurdle),
             '--simulations','5000','--seed',str(60421+assets+int(round(hurdle*10000)))]
        result=subprocess.run(cmd,capture_output=True,text=True,check=True)
        with power_log.open('a',encoding='utf-8') as f:
            f.write(f"\n[{row['universe']} mean_IC={hurdle} horizon=5]\n{result.stdout}")
        print(f"[{row['universe']} mean_IC={hurdle}] {result.stdout.strip()}")
