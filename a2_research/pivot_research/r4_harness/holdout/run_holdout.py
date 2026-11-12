"""One-shot coordinator adapter for the frozen D4/D5 holdout.

This module is safe to import and its tests use generated synthetic arrays
only. It opens a supplied holdout price folder only after the explicit
coordinator flag, frozen-hash check, mechanism-pass check, path checks, and
atomic one-run lock succeed.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from datetime import date
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from r4_harness.holdout.frozen_utils import require_mechanism_pass, trial_budget
from r4_harness.holdout.portfolio_core import portfolio_report
from r4_harness.phase3 import newey_west_t, require_frozen_prereg

START, END = '2010-01-01', '2020-10-31'
DWDP_START, DWDP_END = '2017-09-01', '2019-04-30'
KNOWN_GAPS = ['KFT (missing)', 'DWDP (missing)', 'WBA (missing)',
              'UTX (RTX lineage proxy)']
DEFAULT_LOCK = Path(__file__).resolve().parent / 'HOLDOUT_RUN_LOCK.json'
DEFAULT_OUTPUT = Path(__file__).resolve().parent / 'HOLDOUT_RESULTS.json'


def validate_price_path(price_dir: Path):
    path = Path(price_dir).resolve()
    parts = {p.lower() for p in path.parts}
    if not any('holdout' in p for p in parts):
        raise PermissionError('price folder must explicitly identify itself as holdout')
    if any(p in parts for p in {'repo', 'w1_engine', 'oos3', 'prices-daily',
                                'prices-daily-lookback', 'prices-daily-delisted'}):
        raise PermissionError('development price folders are refused')
    return path


def validate_network_path(input_path: Path):
    path = Path(input_path).resolve()
    parts = {p.lower() for p in path.parts}
    if not any('holdout' in p for p in parts):
        raise PermissionError('network input path must explicitly identify itself as holdout')
    if any(p in parts for p in {'repo', 'w1_engine', 'oos3', 'prices-daily',
                                'prices-daily-lookback', 'prices-daily-delisted'}):
        raise PermissionError('development network/input folders are refused')
    return path


def acquire_one_run_lock(lock_path: Path, details: dict):
    """Atomically create an irreversible lock; a second invocation refuses."""
    path = Path(lock_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('x', encoding='utf-8') as handle:
            json.dump(details, handle, indent=2)
            handle.write('\n')
    except FileExistsError as exc:
        raise PermissionError(f'holdout already attempted; one-run lock exists: {path}') from exc
    return path


def load_network_inputs(npz_path: Path):
    with np.load(npz_path, allow_pickle=False) as z:
        required = {'assets', 'dates', 'adjacency', 'roster_mask'}
        missing = required - set(z.files)
        if missing:
            raise ValueError(f'holdout network bundle missing fields: {sorted(missing)}')
        assets = z['assets'].astype(str).tolist()
        dates = z['dates'].astype(str).tolist()
        adjacency = z['adjacency'].astype(float)
        roster = z['roster_mask'].astype(bool)
        stale = z['network_stale_gt_2q'].astype(bool) if 'network_stale_gt_2q' in z.files else np.zeros(len(dates), bool)
        age = z['network_age_days'].astype(float) if 'network_age_days' in z.files else np.full(len(dates), np.nan)
        dwdp = z['dwdp_membership'].astype(bool) if 'dwdp_membership' in z.files else np.asarray(
            [DWDP_START <= d <= DWDP_END for d in dates], dtype=bool)
    if len(set(assets)) != len(assets) or len(set(dates)) != len(dates):
        raise ValueError('network input assets and dates must be unique')
    if any(d < START or d > END for d in dates):
        raise ValueError('network input dates must be limited to 2010-01-01 through 2020-10-31')
    if dates != sorted(dates):
        raise ValueError('network input dates must be strictly chronological')
    n, t = len(assets), len(dates)
    if roster.shape != (n, t) or adjacency.shape != (t, n, n):
        raise ValueError('roster/network shape must match assets and dates')
    if dwdp.shape != (t,) or stale.shape != (t,) or age.shape != (t,):
        raise ValueError('age/stale/DWDP arrays must have one value per date')
    return assets, dates, adjacency, roster, age, stale, dwdp


def _price_row(row):
    cols = {k.lower(): k for k in row}
    def field(*names):
        key = next((cols[x] for x in names if x in cols), None)
        if key is None or row[key] in (None, ''):
            raise ValueError('missing ' + '/'.join(names))
        return float(row[key])
    raw_open = field('open')
    high = field('high')
    low = field('low')
    raw_close = field('close')
    adj_close = field('adjclose', 'adj_close', 'adjusted_close')
    adj_open_key = next((cols[x] for x in ('adjopen', 'adj_open', 'adjusted_open') if x in cols), None)
    adj_open = float(row[adj_open_key]) if adj_open_key and row[adj_open_key] else raw_open * adj_close / raw_close
    factor = adj_close / raw_close
    return adj_open, high * factor, low * factor, adj_close


def load_holdout_prices(price_dir: Path, assets, dates):
    """Read only requested holdout rows; date guard comes before numeric parsing."""
    index = {d: i for i, d in enumerate(dates)}
    n, t = len(assets), len(dates)
    op = np.full((n, t), np.nan)
    hi = np.full((n, t), np.nan)
    lo = np.full((n, t), np.nan)
    close = np.full((n, t), np.nan)
    absent = {'KFT', 'DWDP', 'WBA'}
    proxy = {'UTX': 'RTX'}
    available = {}
    for i, asset in enumerate(assets):
        source = proxy.get(asset, asset)
        if asset in absent:
            available[asset] = {'source': None, 'rows': 0, 'gap': 'known missing lineage'}
            continue
        path = Path(price_dir) / f'{source}.csv'
        if not path.is_file():
            available[asset] = {'source': source, 'rows': 0, 'gap': 'price file unavailable'}
            continue
        count = 0
        with path.open('r', encoding='utf-8-sig', newline='') as handle:
            for row in csv.DictReader(handle):
                date_key = next((k for k in row if k.lower() == 'date'), 'date')
                day = str(row.get(date_key, ''))[:10]
                if day < START or day > END or day not in index:
                    continue
                try:
                    vals = _price_row(row)
                    if not np.all(np.isfinite(vals)) or vals[0] <= 0 or vals[3] <= 0 or vals[1] < vals[2]:
                        continue
                except (KeyError, TypeError, ValueError, ZeroDivisionError):
                    continue
                j = index[day]
                op[i, j], hi[i, j], lo[i, j], close[i, j] = vals
                count += 1
        available[asset] = {'source': source, 'rows': count,
                            'gap': 'RTX lineage proxy' if asset == 'UTX' else None}
    return op, hi, lo, close, available


def clv5_from_bars(high, low, close):
    span = high - low
    daily = np.full_like(close, np.nan, dtype=float)
    ok = np.isfinite(high) & np.isfinite(low) & np.isfinite(close) & (span > 0)
    daily[ok] = (2 * close[ok] - high[ok] - low[ok]) / span[ok]
    flat = np.isfinite(high) & np.isfinite(low) & np.isfinite(close) & (span == 0)
    daily[flat] = 0.0
    out = np.full_like(daily, np.nan)
    for j in range(4, daily.shape[1]):
        window = daily[:, j - 4:j + 1]
        valid = np.isfinite(window).all(axis=1)
        out[valid, j] = window[valid].mean(axis=1)
    return out


def score_from_network(approach: str, clv5, adjacency, roster):
    n, t = clv5.shape
    scores = np.full((n, t), np.nan)
    for k in range(t):
        g = np.nan_to_num(adjacency[k], nan=0.0)
        np.fill_diagonal(g, 0.0)
        g[~roster[:, k], :] = 0.0
        g[:, ~roster[:, k]] = 0.0
        peer_observed = np.isfinite(clv5[:, k]) & roster[:, k]
        g[:, ~peer_observed] = 0.0
        if approach == 'D4':
            rows = g.sum(axis=1)
            w = np.divide(g, rows[:, None], out=np.zeros_like(g), where=rows[:, None] > 0)
            x = np.where(peer_observed, clv5[:, k], 0.0)
            scores[:, k] = w @ x
            scores[rows <= 0, k] = np.nan
        elif approach == 'D5':
            # Directed edges encode leader -> follower; score is mean incoming
            # leader pressure at each follower.
            inc = g.T
            degree = inc.sum(axis=1)
            x = np.where(peer_observed, clv5[:, k], 0.0)
            have = degree > 0
            scores[have, k] = (inc @ x)[have] / degree[have]
            scores[~have, k] = np.nan
        else:
            raise ValueError('approach must be D4 or D5')
        scores[~roster[:, k], k] = np.nan
    return scores


def _forward_o2c(open_px, close_px, horizon=5):
    n, t = open_px.shape
    out = np.full((n, t), np.nan)
    for k in range(t - horizon):
        buy, sell = open_px[:, k + 1], close_px[:, k + horizon]
        valid = np.isfinite(buy) & np.isfinite(sell) & (buy > 0)
        out[valid, k] = sell[valid] / buy[valid] - 1
    return out


def datewise_ic(scores, forward, roster, horizon=5):
    out = np.full(scores.shape[1], np.nan)
    for k in range(scores.shape[1] - horizon):
        valid = roster[:, k] & np.isfinite(scores[:, k]) & np.isfinite(forward[:, k])
        if valid.sum() < 3:
            continue
        x = rankdata(scores[valid, k], method='average')
        y = rankdata(forward[valid, k], method='average')
        if x.std() and y.std():
            out[k] = np.corrcoef(x, y)[0, 1]
    return out


def _scenario(approach, assets, clv5, scores, adjacency, open_px, close_px, roster, dates, dwdp,
              exclude_dwdp_window, *, trial_count, bootstrap_draws=5000):
    active = roster.copy()
    dwdp_removed = 0
    if exclude_dwdp_window:
        # Exclude the missing/proxy DWDP membership name only. Since the
        # disclosed price lineage has no DWDP bars, this sensitivity should
        # have no return effect, which is itself reported explicitly.
        if 'DWDP' in assets:
            dwdp_removed = int(np.sum(active[assets.index('DWDP'), dwdp]))
            active[assets.index('DWDP'), dwdp] = False
        scores = scores.copy()
        if 'DWDP' in assets:
            scores[assets.index('DWDP'), dwdp] = np.nan
    forward = _forward_o2c(open_px, close_px, 5)
    ic = datewise_ic(scores, forward, active, 5)
    finite = ic[np.isfinite(ic)]
    tstat = newey_west_t(finite, 4)
    # Fixed deterministic negative control and circular 20-session network lag.
    reverse_graph = np.swapaxes(adjacency, 1, 2)
    reversed_score = score_from_network(approach, clv5, reverse_graph, active)
    reverse_ic = datewise_ic(reversed_score, forward, active, 5)
    shifted = np.roll(adjacency, 20, axis=0)
    shifted_score = score_from_network(approach, clv5, shifted, active)
    shifted_ic = datewise_ic(shifted_score, forward, active, 5)
    if not np.any(np.isfinite(scores)):
        raise ValueError('no score/outcome coverage in the holdout scenario')
    formed = np.flatnonzero(np.sum(np.isfinite(scores) & active, axis=0) >= 5)
    if not len(formed):
        raise ValueError('no holdout date has five eligible scores')
    formations = np.arange(formed[0], scores.shape[1] - 1, 5)
    port = portfolio_report(scores, open_px, close_px, active, formations,
                            trial_count=trial_count, bootstrap_draws=bootstrap_draws,
                            seed=20261110, turnover_cap=.50, cost_rate=.0005,
                            holdout=True, turnover_cap_basis=(
                                'benchmark_relative' if approach == 'D4' else 'absolute'),
                            asset_names=assets)
    return {
        'primary_mechanism': {'mean_ic': float(np.mean(finite)) if len(finite) else None,
                              'nw_t_lag4': float(tstat), 'effective_dates': int(len(finite)),
                              'positive_sign': bool(len(finite) and np.mean(finite) > 0),
                              'mechanism_pass': bool(len(finite) and
                                  (np.mean(finite) > 0 if approach == 'D4' else np.mean(finite) >= .0183))},
        'portfolio': port,
        'dwdp_window_excluded': bool(exclude_dwdp_window),
        'dwdp_window_dates': int(np.sum(dwdp)),
        'dwdp_window_dates_removed': dwdp_removed,
        'dwdp_exclusion_note': 'DWDP prices are unavailable in the disclosed lineage, so excluding DWDP membership does not change available-name returns.',
        'placebo_reverse_mean_ic': float(np.nanmean(reverse_ic)) if np.isfinite(reverse_ic).any() else None,
        'placebo_reverse_nw_t': float(newey_west_t(reverse_ic, 4)),
        'placebo_shift20_mean_ic': float(np.nanmean(shifted_ic)) if np.isfinite(shifted_ic).any() else None,
        'placebo_shift20_nw_t': float(newey_west_t(shifted_ic, 4)),
        'full_holdout_pass': bool(
            len(finite) and
            (np.mean(finite) > 0 if approach == 'D4' else np.mean(finite) >= .0183) and
            port['holdout_pass']),
    }


def analyze_arrays(approach, assets, dates, adjacency, roster, open_px, high,
                   low, close, dwdp, *, trial_count=30,
                   bootstrap_draws=5000):
    """Pure array analysis entry for synthetic tests and coordinator adapter."""
    if len(assets) == 0 or len(dates) == 0:
        raise ValueError('holdout arrays cannot be empty')
    n, t = len(assets), len(dates)
    if np.shape(adjacency) != (t, n, n) or any(np.shape(a) != (n, t) for a in
        (roster, open_px, high, low, close)) or np.shape(dwdp) != (t,):
        raise ValueError('synthetic/holdout arrays must agree on assets and dates')
    clv5 = clv5_from_bars(np.asarray(high, float), np.asarray(low, float), np.asarray(close, float))
    active = np.asarray(roster, bool) & np.isfinite(open_px) & np.isfinite(close)
    scores = score_from_network(approach, clv5, np.asarray(adjacency, float), active)
    included = _scenario(approach, assets, clv5, scores, adjacency, open_px, close, active, dates,
                         np.asarray(dwdp, bool), False, trial_count=trial_count,
                         bootstrap_draws=bootstrap_draws)
    excluded = _scenario(approach, assets, clv5, scores, adjacency, open_px, close, active, dates,
                          np.asarray(dwdp, bool), True, trial_count=trial_count,
                          bootstrap_draws=bootstrap_draws)
    return {'approach': approach, 'dates': [dates[0], dates[-1]],
            'known_gaps': KNOWN_GAPS,
            'price_coverage_count': int(np.isfinite(close).sum()),
            'dwdp_included': included, 'dwdp_excluded': excluded}


def run_holdout_once(approach, prereg_path, price_dir, network_inputs,
                     mechanism_pass, *, output_path=DEFAULT_OUTPUT, caller_role=None,
                     bootstrap_draws=5000):
    if caller_role != 'coordinator':
        raise PermissionError('only the coordinator may invoke the sealed holdout runner')
    prereg_path = Path(prereg_path).resolve()
    frozen = require_frozen_prereg(approach, prereg_dir=prereg_path.parent)
    if frozen.resolve() != prereg_path:
        raise ValueError('pre-registration file name and approach do not match')
    proof = require_mechanism_pass(approach, prereg_path, mechanism_pass)
    price_path = validate_price_path(price_dir)
    network_path = validate_network_path(network_inputs)
    # Lock is acquired before any price or network input is opened.
    acquire_one_run_lock(DEFAULT_LOCK, {'approach': approach,
                                    'preregistration': str(prereg_path),
                                    'mechanism_pass': str(mechanism_pass),
                                    'started_by': 'coordinator'})
    assets, dates, adjacency, roster, age, stale, dwdp = load_network_inputs(network_path)
    op, high, low, close, coverage = load_holdout_prices(price_path, assets, dates)
    active = roster & np.isfinite(op) & np.isfinite(close)
    # No input outside the authorized period can enter; the bundle loader also
    # rejects dates outside this exact holdout window.
    result = analyze_arrays(approach, assets, dates, adjacency, active, op,
                            high, low, close, dwdp,
                            trial_count=trial_budget(ROOT / 'specs' / 'r4_trials.md'),
                            bootstrap_draws=bootstrap_draws)
    result.update({'frozen_date': require_frozen_prereg(approach, prereg_path.parent).read_text(encoding='utf-8').split('FROZEN: ',1)[1].splitlines()[0],
                   'pre_registration_sha256': proof['prereg_sha256'],
                   'network_available_dates': int(np.sum(np.isfinite(age) | np.any(adjacency != 0, axis=(1, 2)))),
                   'network_unavailable_dates': int(len(dates) - np.sum(np.isfinite(age) | np.any(adjacency != 0, axis=(1, 2)))),
                   'stale_network_dates': int(np.sum(stale)),
                   'network_age_days_min_median_p90_max': (
                       [float(np.min(age[np.isfinite(age)])),
                        float(np.median(age[np.isfinite(age)])),
                        float(np.quantile(age[np.isfinite(age)], .90)),
                        float(np.max(age[np.isfinite(age)]))]
                       if np.isfinite(age).any() else None),
                   'asset_price_coverage': coverage,
                   'lineage_notes': 'No imputation: KFT, DWDP, WBA missing; UTX uses RTX lineage proxy.'})
    Path(output_path).write_text(json.dumps(result, indent=2, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else float(x)), encoding='utf-8')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approach', choices=('D4', 'D5'), required=True)
    parser.add_argument('--prereg', type=Path, required=True)
    parser.add_argument('--prices', type=Path, required=True)
    parser.add_argument('--network-inputs', type=Path, required=True)
    parser.add_argument('--mechanism-pass', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--coordinator-only', action='store_true', required=True)
    args = parser.parse_args(argv)
    try:
        if os.environ.get('ORCA_HOLDOUT_AUTH') != 'COORDINATOR_ONLY':
            raise PermissionError('set ORCA_HOLDOUT_AUTH=COORDINATOR_ONLY in the coordinator terminal')
        result = run_holdout_once(args.approach, args.prereg, args.prices,
                                  args.network_inputs, args.mechanism_pass,
                                  output_path=args.output,
                                  caller_role='coordinator')
        print(json.dumps(result, indent=2, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else float(x)))
        return 0
    except Exception as exc:
        print(f'REFUSED/FAILED: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
