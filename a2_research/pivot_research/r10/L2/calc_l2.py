import math
from statistics import NormalDist
N = NormalDist()
zcrit = N.inv_cdf(.95)
z80 = N.inv_cdf(.80)
mult = zcrit + z80

def power(effect, sd, n):
    lam = effect / (sd / math.sqrt(n))
    return 1 - N.cdf(zcrit - lam), lam

rows = {}
# DTC: 72 month observations, measured monthly IC dispersion .0795; 50% haircut.
rows['DTC'] = power(.0233*.5, .0795, 72)
# Adds: N=125, event SD=7.7446%; gross CAR 1.1904%; deduct twice tier cost before 50% haircut.
for bps in (5,10,20):
    net = .011904 - 2*bps/10000
    rows[f'adds_{bps}'] = (net*.5, *power(net*.5, .077446, 125))
# D1: observed mean/t imply HAC SE; scale from 297 to about 302 weekly dates.
se_d1 = .009374/1.908 * math.sqrt(297)
rows['D1'] = power(.009374*.5, se_d1, 302)
# J1 mechanism: observed effect/t; same formation count scaling.
se_j1 = .014786333277116828/2.0770415514093865 * math.sqrt(297)
rows['J1_mechanism'] = power(.014786333277116828*.5, se_j1, 302)
# Mechanical thresholds: z values and 2010-15 scaling of R9 10.8y tiered report.
scale = mult/(N.inv_cdf(1-.05/3)+z80) * math.sqrt(2700/1510)
print('zcrit',zcrit,'z80',z80,'mult',mult,'threshold_scale',scale)
for k,v in rows.items(): print(k,v)
print('spweekly',.021*scale,'spmonthly',.034*scale)
# D1 IC 80% mechanism requirement using Dow IC SD stress and effective N scaled from prior.
# effective-N ratio 492.5133 / 1488 sessions; 1510-session target.
neff_dow = 492.5133149999232/1488*1510
print('dow_neff',neff_dow,'dow_ic_sd',.242536,'dow_ic_mde',mult*.242536/math.sqrt(neff_dow))
# J1/S&P signal mechanism stress; preserve R7 effective weekly fraction and IC SD.
neff_sp_week = 83.2/312*302
print('sp_week_neff',neff_sp_week,'sp_mechanism_mde',mult*.138675/math.sqrt(neff_sp_week))

