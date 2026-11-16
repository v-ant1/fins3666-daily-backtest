"""Minimal independent re-derivation of D5 and D6 primary statistics.

Reads only the development mechanism-input bundles and result JSON files.
Does not import or call either registered runner or the harness.
"""
from __future__ import annotations
import json
import re
import hashlib
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[2]
D5 = ROOT / 'r4_harness' / 'runs' / 'D5'
D6 = ROOT / 'r4_harness' / 'runs' / 'D6'
SPECS = ROOT / 'specs' / 'r4_prereg'


def frozen_hash(name):
    text = (SPECS / f'{name}.md').read_text(encoding='utf-8')
    frozen = re.search(r'^FROZEN:\s*(\d{4}-\d{2}-\d{2})\s*$', text, re.M)
    declared = re.search(r'^SHA256:\s*([0-9a-fA-F]{64})\s*$', text, re.M)
    canonical = '\n'.join(line for line in text.splitlines() if not line.startswith('SHA256:')) + '\n'
    actual = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    return {'date': frozen.group(1) if frozen else None,
            'declared': declared.group(1).lower() if declared else None,
            'actual': actual,
            'valid': bool(frozen and declared and actual == declared.group(1).lower())}


def nw_mean_t(x, lag):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 2:
        return float('nan')
    centered = x - x.mean()
    long_var = float(centered @ centered / n)
    for k in range(1, min(lag, n - 1) + 1):
        bartlett = 1 - k / (lag + 1)
        long_var += 2 * bartlett * float(centered[k:] @ centered[:-k]) / n
    return float(x.mean() / np.sqrt(long_var / n))


def d5_primary():
    with np.load(D5 / 'D5_INPUTS.npz', allow_pickle=False) as z:
        dates = z['dates'].astype(str).tolist()
        formation_indices = z['formation_indices'].astype(int)
        roster = z['roster'].astype(bool)
        graph = z['graph20'].astype(float)
        high, low, close = (z[k].astype(float) for k in ('raw_high', 'raw_low', 'raw_close'))
        adj_open, adj_close = (z[k].astype(float) for k in ('adj_open', 'adj_close'))

    # Independent five-session CLV rolling mean.
    span = high - low
    raw = np.full(high.shape, np.nan)
    valid = np.isfinite(high) & np.isfinite(low) & np.isfinite(close) & (span > 0)
    raw[valid] = (2 * close[valid] - high[valid] - low[valid]) / span[valid]
    flat = np.isfinite(high) & np.isfinite(low) & np.isfinite(close) & (span == 0)
    raw[flat] = 0.0
    pressure = np.full_like(raw, np.nan)
    for t in range(4, raw.shape[1]):
        window = raw[:, t - 4:t + 1]
        complete = np.isfinite(window).all(axis=1)
        pressure[complete, t] = window[complete].mean(axis=1)

    # Independent target incoming-leader pressure aggregation from saved directed graph.
    n_assets, n_dates = pressure.shape
    score = np.full((n_assets, n_dates), np.nan)
    for t in range(n_dates):
        for target in range(n_assets):
            source_idx = np.flatnonzero(graph[t, :, target] > 0)
            source_idx = [i for i in source_idx if np.isfinite(pressure[i, t])]
            if source_idx:
                score[target, t] = float(np.mean(pressure[source_idx, t]))

    forward = np.full_like(adj_close, np.nan)
    for t in range(n_dates - 5):
        buy = adj_open[:, t + 1]
        sell = adj_close[:, t + 5]
        ok = np.isfinite(buy) & np.isfinite(sell) & (buy > 0)
        forward[ok, t] = sell[ok] / buy[ok] - 1.0

    ic = np.full(n_dates, np.nan)
    for t in range(n_dates - 5):
        ok = roster[:, t] & np.isfinite(score[:, t]) & np.isfinite(forward[:, t])
        if ok.sum() < 3:
            continue
        x_rank = rankdata(score[ok, t], method='average')
        y_rank = rankdata(forward[ok, t], method='average')
        if x_rank.std() > 0 and y_rank.std() > 0:
            ic[t] = float(np.corrcoef(x_rank, y_rank)[0, 1])
    observed = ic[np.isfinite(ic)]
    return {
        'n_dates_in_bundle': n_dates,
        'date_start': dates[0], 'date_end': dates[-1],
        'eligible_ic_dates': int(len(observed)),
        'input_fifth_session_dates': int(len(formation_indices)),
        'ic_values_on_fifth_session_dates': int(np.isfinite(ic[formation_indices]).sum()),
        'mean_ic': float(observed.mean()),
        'nw_t_lag4': nw_mean_t(observed, 4),
    }


def nw_ols_beta(y, predictor, control, lag):
    y = np.asarray(y, float)
    x = np.column_stack([np.ones(len(y)), np.asarray(predictor, float), np.asarray(control, float)])
    b = np.linalg.solve(x.T @ x, x.T @ y)
    resid = y - x @ b
    z = x * resid[:, None]
    meat = z.T @ z
    for k in range(1, min(lag, len(y) - 1) + 1):
        weight = 1 - k / (lag + 1)
        cross = z[k:].T @ z[:-k]
        meat += weight * (cross + cross.T)
    inv = np.linalg.inv(x.T @ x)
    cov = inv @ meat @ inv
    se = float(np.sqrt(max(float(cov[1, 1]), 0)))
    beta = float(b[1])
    return {'n': len(y), 'beta': beta, 'nw_se': se, 'nw_t': beta / se}


def d6_primary():
    with np.load(D6 / 'D6_INPUTS.npz', allow_pickle=False) as z:
        assets = z['assets'].astype(str).tolist()
        dates = z['dates'].astype(str).tolist()
        close = z['adjusted_close'].astype(float)
        open_ = z['adjusted_open'].astype(float)
    if assets != ['SPY', 'TLT', 'IEF', 'SHY', 'TIP']:
        raise ValueError(f'unexpected frozen D6 asset order: {assets}')
    month_rows = {}
    for i, day in enumerate(dates):
        month_rows.setdefault(day[:7], []).append(i)
    months = sorted(month_rows)
    month_last_close = {m: close[:, month_rows[m][-1]] for m in months}
    month_first_open = {m: open_[:, month_rows[m][0]] for m in months}
    formation = []
    year, month = 2021, 7
    while (year, month) <= (2026, 8):
        formation.append(f'{year:04d}-{month:02d}')
        month += 1
        if month == 13:
            year, month = year + 1, 1
    y, x_bond, x_spy = [], [], []
    for fm in formation:
        year, month = map(int, fm.split('-'))
        target = f'{year + int(month == 12):04d}-{month % 12 + 1:02d}'
        ty, tm = map(int, target.split('-'))
        following = f'{ty + int(tm == 12):04d}-{tm % 12 + 1:02d}'
        loc = months.index(fm)
        prior = months[loc - 1]
        lag12 = months[loc - 12]
        spy_trend = month_last_close[prior][0] / month_last_close[lag12][0] - 1
        treasury_trends = month_last_close[prior][1:] / month_last_close[lag12][1:] - 1
        bond_trend = float(treasury_trends.mean())
        spy_ret = month_first_open[following][0] / month_first_open[target][0] - 1
        y.append(float(spy_ret))
        x_bond.append(bond_trend)
        x_spy.append(float(spy_trend))
    return {
        'date_start': dates[0], 'date_end': dates[-1],
        'first_target_month': '2021-08', 'last_target_month': '2026-09',
        'n_observations': len(y),
        **nw_ols_beta(y, x_bond, x_spy, lag=11),
    }


def main():
    hashes = {name: frozen_hash(name) for name in ('D5', 'D6')}
    if not all(value['valid'] for value in hashes.values()):
        raise SystemExit(f'Frozen prereg hash validation failed: {hashes}')
    d5 = d5_primary()
    d6 = d6_primary()
    logged_d5 = json.loads((D5 / 'D5_MECHANISM_RESULTS.json').read_text(encoding='utf-8'))['primary_variant_1_20_session']
    logged_d6 = json.loads((D6 / 'D6_MECHANISM_RESULTS.json').read_text(encoding='utf-8'))['endpoints']['D6-1_12m_bond_to_SPY']
    result = {
        'frozen_specs': hashes,
        'd5': {'independent': d5, 'logged': {
            'mean_ic': logged_d5['mean_ic'], 'nw_t_lag4': logged_d5['nw_t_lag4'],
        }},
        'd6': {'independent': d6, 'logged': {
            'beta': logged_d6['beta'], 'nw_t_lag11': logged_d6['nw_t_lag11'],
        }},
        'runner_settings': {
            'D5': {'window': '20-session leader graph; 5-session CLV and forward return',
                   'NW_lag': 4, 'permutation_draws': 500, 'seed': 20261110,
                   'fixed_shift_sessions': 20},
            'D6': {'development_targets': '2021-08 through 2026-09 (62 monthly observations)',
                   'primary_trend': '12-minus-1', 'NW_lag': 11,
                   'circular_shift_draws': 500, 'seed': 20261110,
                   'offset_range_for_N62': '12 through 50 inclusive'},
        },
    }
    (Path(__file__).resolve().parent / 'REPRO_VALUES.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
