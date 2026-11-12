"""Frozen-only D5 predictive mechanism and placebo runner.

The freeze/hash and trial-budget guards run before opening D5_INPUTS.npz or
any OHLCV-derived input. Use --check-freeze to exercise only that guard.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm, rankdata

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from r4_harness.phase3 import (
    append_trial, authorize_trial, newey_west_t, prereg_digest,
    require_frozen_prereg,
)

PREREG_DIR = ROOT / 'specs' / 'r4_prereg'
OUT = Path(__file__).resolve().parent
INPUT_FILE = OUT / 'D5_INPUTS.npz'
HORIZON = 5
NW_LAG = 4
PLACEBO_DRAWS = 500
SEED = 20261110
GRAPH_SHIFT = 20
PRIMARY_IC_FLOOR = 0.0183


def _raw_clv5(high, low, close):
    span = high - low
    raw = np.full(high.shape, np.nan, dtype=float)
    ok = np.isfinite(high) & np.isfinite(low) & np.isfinite(close) & (span > 0)
    raw[ok] = (2 * close[ok] - high[ok] - low[ok]) / span[ok]
    flat = np.isfinite(high) & np.isfinite(low) & np.isfinite(close) & (span == 0)
    raw[flat] = 0.0
    out = np.full_like(raw, np.nan)
    for t in range(4, raw.shape[1]):
        win = raw[:, t-4:t+1]
        complete = np.isfinite(win).all(axis=1)
        out[complete, t] = win[complete].mean(axis=1)
    return out


def _dollar_volume_graph(close, volume, sic2, roster, lookback):
    n, t = close.shape
    graph = np.zeros((t, n, n), dtype=float)
    dollar = close * volume
    for day in range(lookback, t):
        groups = {}
        for i in range(n):
            if not roster[i, day] or not sic2[i, day]:
                continue
            hist = dollar[i, day-lookback:day]
            if len(hist) != lookback or not np.isfinite(hist).all() or np.any(hist <= 0):
                continue
            groups.setdefault(str(sic2[i, day]), []).append((float(hist.mean()), i))
        for members in groups.values():
            if len(members) < 2:
                continue
            members.sort(key=lambda z: (-z[0], z[1]))
            leader = members[0][1]
            for _, follower in members[1:]:
                graph[day, leader, follower] = 1.0
    return graph


def _score(clv5, graph):
    # Vectorized incoming weighted mean; graph axis order is date/source/target.
    incoming = np.asarray(graph, float).transpose(0, 2, 1)
    pressure = np.asarray(clv5, float).T
    valid = np.isfinite(pressure)
    weights = incoming * valid[:, None, :]
    denominator = weights.sum(axis=2)
    numerator = np.einsum('tij,tj->ti', weights,
                          np.where(valid, pressure, 0.0), optimize=True)
    scores = np.divide(numerator, denominator,
                       out=np.full_like(numerator, np.nan),
                       where=denominator > 0)
    return scores.T


def _forward_returns(adj_open, adj_close):
    n, t = adj_open.shape
    forward = np.full((n, t), np.nan)
    for day in range(t - HORIZON):
        buy = adj_open[:, day+1]
        sell = adj_close[:, day+HORIZON]
        valid = np.isfinite(buy) & np.isfinite(sell) & (buy > 0)
        forward[valid, day] = sell[valid] / buy[valid] - 1.0
    return forward


def _ic_series(scores, forward, roster):
    result = np.full(scores.shape[1], np.nan)
    for day in range(scores.shape[1] - HORIZON):
        valid = roster[:, day] & np.isfinite(scores[:, day]) & np.isfinite(forward[:, day])
        if valid.sum() < 3:
            continue
        x = rankdata(scores[valid, day], method='average')
        y = rankdata(forward[valid, day], method='average')
        if x.std() and y.std():
            result[day] = float(np.corrcoef(x, y)[0, 1])
    return result


def _mean_and_t(series):
    x = np.asarray(series, float)
    x = x[np.isfinite(x)]
    return (float(x.mean()) if len(x) else float('nan'),
            float(newey_west_t(x, NW_LAG)), int(len(x)))


def _nw_pvalue(t_stat, n, two_sided=False):
    if not np.isfinite(t_stat) or n < 2:
        return float('nan')
    tail = float(norm.sf(abs(t_stat) if two_sided else t_stat))
    return min(1.0, 2.0 * tail) if two_sided else tail


def _permute_leaders(sic2, roster, eligible_graph, rng):
    """Randomly choose one leader per existing SIC group/date, preserving breadth."""
    t, n, _ = eligible_graph.shape
    out = np.zeros_like(eligible_graph)
    for day in range(t):
        groups = {}
        graph_nodes = set(np.flatnonzero((eligible_graph[day].sum(axis=0) +
                                          eligible_graph[day].sum(axis=1)) > 0).tolist())
        for i in range(n):
            if i in graph_nodes and roster[i, day] and sic2[i, day]:
                groups.setdefault(str(sic2[i, day]), []).append(i)
        for members in groups.values():
            if len(members) < 2:
                continue
            leader = int(rng.choice(np.asarray(members)))
            for follower in members:
                if follower != leader:
                    out[day, leader, follower] = 1.0
    return out


def _stats_for_graph(clv5, graph, forward, roster):
    score = _score(clv5, graph)
    return _mean_and_t(_ic_series(score, forward, roster))


def _run(input_file=INPUT_FILE):
    with np.load(input_file, allow_pickle=False) as z:
        assets = z['assets'].astype(str).tolist()
        dates = z['dates'].astype(str).tolist()
        roster = z['roster'].astype(bool)
        sic2 = z['sic2'].astype(str)
        primary_graph = z['graph20'].astype(float)
        high, low, close = (z[k].astype(float) for k in ('raw_high', 'raw_low', 'raw_close'))
        volume = z['volume'].astype(float)
        adj_open, adj_close = (z[k].astype(float) for k in ('adj_open', 'adj_close'))

    clv5 = _raw_clv5(high, low, close)
    forward = _forward_returns(adj_open, adj_close)
    primary = _stats_for_graph(clv5, primary_graph, forward, roster)
    sensitivity_graph = _dollar_volume_graph(close, volume, sic2, roster, 60)
    sensitivity = _stats_for_graph(clv5, sensitivity_graph, forward, roster)
    reverse = _stats_for_graph(clv5, np.swapaxes(primary_graph, 1, 2), forward, roster)

    rng = np.random.default_rng(SEED)
    perm_means, perm_ts, perm_series = [], [], []
    for _ in range(PLACEBO_DRAWS):
        placebo = _permute_leaders(sic2, roster, primary_graph, rng)
        series = _ic_series(_score(clv5, placebo), forward, roster)
        mean, t_stat, _ = _mean_and_t(series)
        perm_means.append(mean); perm_ts.append(t_stat)
        perm_series.append(series)

    # D5's frozen clarification defines one deterministic 20-session control.
    shifted = np.zeros_like(primary_graph)
    shifted[GRAPH_SHIFT:] = primary_graph[:-GRAPH_SHIFT]
    shift_series = _ic_series(_score(clv5, shifted), forward, roster)
    shift_mean, shift_t, shift_n = _mean_and_t(shift_series)

    perm = np.asarray(perm_means, float)
    perm_finite = perm[np.isfinite(perm)]
    perm_p = (1 + int(np.sum(perm_finite >= primary[0]))) / (len(perm_finite) + 1)
    perm_matrix = np.vstack(perm_series)
    perm_valid = np.isfinite(perm_matrix)
    perm_n = perm_valid.sum(axis=0)
    perm_family_series = np.divide(
        np.where(perm_valid, perm_matrix, 0.0).sum(axis=0), perm_n,
        out=np.full(perm_matrix.shape[1], np.nan), where=perm_n > 0,
    )
    perm_family_series = perm_family_series[np.isfinite(perm_family_series)]
    perm_family_t = float(newey_west_t(perm_family_series, NW_LAG))
    p_primary = _nw_pvalue(primary[1], primary[2])
    p_reverse = _nw_pvalue(reverse[1], reverse[2], True)
    p_sensitivity = _nw_pvalue(sensitivity[1], sensitivity[2])
    p_shift = _nw_pvalue(shift_t, shift_n, True)
    gate_pass = bool(primary[0] >= PRIMARY_IC_FLOOR and primary[1] >= 2.0 and
                     primary[0] > np.quantile(perm_finite, .95) and
                     abs(reverse[1]) < 2.0 and abs(perm_family_t) < 2.0 and
                     abs(shift_t) < 2.0)
    result = {
        'primary_variant_1_20_session': {'mean_ic': primary[0], 'nw_t_lag4': primary[1], 'dates': primary[2],
                                         'one_sided_nw_p': p_primary},
        'reverse_edge_control': {'mean_ic': reverse[0], 'nw_t_lag4': reverse[1], 'dates': reverse[2],
                                 'two_sided_nw_p': p_reverse},
        'sensitivity_variant_2_60_session': {'mean_ic': sensitivity[0], 'nw_t_lag4': sensitivity[1],
                                             'dates': sensitivity[2],
                                             'one_sided_nw_p': p_sensitivity},
        'within_sic_permuted_leaders': {
            'draws': int(len(perm_finite)), 'mean_ic_p95': float(np.quantile(perm_finite, .95)),
            'one_sided_randomization_p': float(perm_p),
            'observed_percentile': float(np.mean(perm_finite <= primary[0])),
            'family_mean_series_nw_t': perm_family_t,
        },
        'shifted_graph_20_sessions': {
            'draws': 1, 'mean_ic': shift_mean, 'nw_t_lag4': shift_t,
            'dates': shift_n, 'two_sided_nw_p': p_shift,
            'observed_percentile': None,
            'note': 'One deterministic 20-session displacement, per frozen clarification.',
        },
        'pass': {
            'primary_mean_ic_ge_0_0183_and_nw_t_ge_2': bool(primary[0] >= PRIMARY_IC_FLOOR and primary[1] >= 2.0),
            'variant_2_reported_not_advanced': True,
            'exceeds_within_sic_p95': bool(primary[0] > np.quantile(perm_finite, .95)),
            'reverse_abs_nw_t_lt_2': bool(abs(reverse[1]) < 2.0),
            'permuted_abs_nw_t_lt_2': bool(abs(perm_family_t) < 2.0),
            'shifted_abs_nw_t_lt_2': bool(abs(shift_t) < 2.0),
            'mechanism_gate_pass': gate_pass,
        },
        'approach': 'D5', 'passed': gate_pass,
        'prereg_sha256': prereg_digest((PREREG_DIR / 'D5.md').read_text(encoding='utf-8')),
        'input_metadata': {'assets': len(assets), 'development_dates': len(dates),
                           'date_start': dates[0], 'date_end': dates[-1],
                           'seed': SEED, 'permutation_draws': PLACEBO_DRAWS,
                           'time_shift_draws': 1, 'time_shift_sessions': GRAPH_SHIFT},
    }
    (OUT / 'D5_MECHANISM_RESULTS.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    with (OUT / 'D5_PLACEBO_DRAWS.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['family', 'draw', 'mean_rank_ic', 'nw_t_lag4'])
        for k, (mean, stat) in enumerate(zip(perm_means, perm_ts), 1):
            w.writerow(['within_sic_permuted_leaders', k, mean, stat])
        w.writerow(['shifted_graph_20_sessions', 1, shift_mean, shift_t])
    (OUT / ('MECHANISM_PASS.json' if gate_pass else 'MECHANISM_FAIL.json')).write_text(
        json.dumps(result, indent=2), encoding='utf-8')
    _write_markdown_results(result, perm_finite, p_shift)
    return result


def _write_markdown_results(result, permutation_means, shift_p):
    primary = result['primary_variant_1_20_session']
    reverse = result['reverse_edge_control']
    sens = result['sensitivity_variant_2_60_session']
    perm = result['within_sic_permuted_leaders']
    shift = result['shifted_graph_20_sessions']
    q = np.quantile(permutation_means, [0, .05, .25, .5, .75, .95, 1])
    gate = 'PASS' if result['passed'] else 'FAIL'
    rows = [
        '# D5 mechanism and placebo results', '',
        f'**Mechanism gate: {gate}.** Development sample: {result["input_metadata"]["date_start"]} '
        f'to {result["input_metadata"]["date_end"]}; {result["input_metadata"]["development_dates"]} sessions.',
        'Only development prices were used. The portfolio stage and sealed holdout were not run.',
        '',
        '## Pre-outcome graph gate', '',
        'Input-only feasibility gate: PASS, 293/293 eligible fifth-session dates met the minimum of 10 pairs, '
        '3 leaders and 3 SIC groups. There were 11 directed pairs on each eligible date (see `INPUT_QA.md` and `D5_GRAPH_BY_DATE.csv`).',
        '',
        '## Registered endpoints', '',
        '| Endpoint | Mean rank IC / statistic | NW t (lag 4) | Raw p-value | Result |',
        '|---|---:|---:|---:|---|',
        f'| Variant 1 primary, 20-session graph (one-sided NW) | {primary["mean_ic"]:.6f} | {primary["nw_t_lag4"]:.4f} | {primary["one_sided_nw_p"]:.6g} | '
        f'{"PASS" if result["pass"]["primary_mean_ic_ge_0_0183_and_nw_t_ge_2"] else "FAIL"} (mean ≥ 0.0183 and t ≥ 2) |',
        f'| Reverse-edge deterministic control (two-sided NW) | {reverse["mean_ic"]:.6f} | {reverse["nw_t_lag4"]:.4f} | {reverse["two_sided_nw_p"]:.6g} | '
        f'{"PASS" if result["pass"]["reverse_abs_nw_t_lt_2"] else "FAIL"} (|t| < 2) |',
        f'| Within-SIC leader permutations, observed vs null (one-sided randomization) | observed {primary["mean_ic"]:.6f}; null p95 {perm["mean_ic_p95"]:.6f} | pooled null-series t {perm["family_mean_series_nw_t"]:.4f} | {perm["one_sided_randomization_p"]:.6g} | '
        f'{"PASS" if result["pass"]["exceeds_within_sic_p95"] and result["pass"]["permuted_abs_nw_t_lt_2"] else "FAIL"} |',
        f'| Fixed 20-session shifted graph (two-sided NW) | {shift["mean_ic"]:.6f} | {shift["nw_t_lag4"]:.4f} | {shift_p:.6g} | '
        f'{"PASS" if result["pass"]["shifted_abs_nw_t_lt_2"] else "FAIL"} (|t| < 2) |',
        f'| Variant 2 sensitivity, 60-session graph (one-sided NW) | {sens["mean_ic"]:.6f} | {sens["nw_t_lag4"]:.4f} | {sens["one_sided_nw_p"]:.6g} | Reported only; cannot replace variant 1 |',
        '| Variant 1 net portfolio excess vs EW30 (one-sided block bootstrap) | — | — | Not run | Portfolio stage excluded from this task |',
        '',
        '## Permutation null distribution', '',
        f'- Draws: {perm["draws"]}; fixed seed: `{SEED}`; finite-sample one-sided randomization p-value: {perm["one_sided_randomization_p"]:.6g}; observed percentile: {perm["observed_percentile"]:.1%}.',
        f'- Mean-IC quantiles (min, 5th, 25th, median, 75th, 95th, max): {", ".join(f"{x:.6f}" for x in q)}.',
        '- Full draw-by-draw mean IC and Newey–West t values are in `D5_PLACEBO_DRAWS.csv`.',
        '- Time shift is one fixed, deterministic 20-session control, as clarified before freeze; its endpoint is the two-sided Newey–West test, not a randomized p-value.',
        '',
        '## Plain-English reading', '',
        ('The registered primary and placebo conditions pass.' if result['passed'] else
         'At least one registered primary or placebo condition failed, so D5 does not advance to a portfolio test.'),
        'The 60-session version is a fixed sensitivity only. Raw p-values are shown here; goal-wide Holm adjustment is maintained by the coordinator in `specs/r4_trials.md` and the corresponding Holm manifest, not recalculated in this run.',
        '',
        '## Trial logging', '',
        'Every computed D5 mechanism endpoint was appended through the harness trial logger. The portfolio endpoint is not logged as an outcome because it was not run.',
    ]
    (OUT / 'MECHANISM_RESULTS.md').write_text('\n'.join(rows) + '\n', encoding='utf-8')


def _log_registered_results(result):
    p = result['primary_variant_1_20_session']
    r = result['reverse_edge_control']
    v2 = result['sensitivity_variant_2_60_session']
    perm = result['within_sic_permuted_leaders']
    shift = result['shifted_graph_20_sessions']
    endpoints = [
        ('variant 1 primary five-session follower IC',
         result['pass']['primary_mean_ic_ge_0_0183_and_nw_t_ge_2'],
         f'mean_IC={p["mean_ic"]:.8g}; NW_t={p["nw_t_lag4"]:.8g}; one_sided_p={p["one_sided_nw_p"]:.8g}'),
        ('reverse-edge mean IC placebo', result['pass']['reverse_abs_nw_t_lt_2'],
         f'mean_IC={r["mean_ic"]:.8g}; NW_t={r["nw_t_lag4"]:.8g}; two_sided_p={r["two_sided_nw_p"]:.8g}'),
        ('within-SIC permuted leader comparison',
         result['pass']['exceeds_within_sic_p95'] and result['pass']['permuted_abs_nw_t_lt_2'],
         f'null_p95={perm["mean_ic_p95"]:.8g}; randomization_p={perm["one_sided_randomization_p"]:.8g}; observed_percentile={perm["observed_percentile"]:.8g}; pooled_null_NW_t={perm["family_mean_series_nw_t"]:.8g}'),
        ('fixed 20-session shifted graph placebo', result['pass']['shifted_abs_nw_t_lt_2'],
         f'mean_IC={shift["mean_ic"]:.8g}; NW_t={shift["nw_t_lag4"]:.8g}; two_sided_p={shift["two_sided_nw_p"]:.8g}'),
        ('variant 2 60-session sensitivity follower IC', None,
         f'mean_IC={v2["mean_ic"]:.8g}; NW_t={v2["nw_t_lag4"]:.8g}; one_sided_p={v2["one_sided_nw_p"]:.8g}; reported sensitivity, not advanced'),
    ]
    for name, passed, detail in endpoints:
        status = 'REPORTED' if passed is None else ('PASS' if passed else 'FAIL')
        append_trial('D5', name, f'{status}: {detail}', prereg_dir=PREREG_DIR)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-freeze', action='store_true',
                        help='validate D5.md only; do not open development inputs')
    parser.add_argument('--inputs', type=Path, default=INPUT_FILE)
    args = parser.parse_args(argv)
    try:
        prereg = require_frozen_prereg('D5', prereg_dir=PREREG_DIR)
    except Exception as exc:
        print(f'REFUSED: D5 pre-registration is not frozen and hash-valid: {exc}', file=sys.stderr)
        return 2
    if args.check_freeze:
        print(f'FROZEN D5 pre-registration verified: {prereg}')
        return 0
    try:
        authorize_trial('D5', prereg_dir=PREREG_DIR)
        result = _run(args.inputs)
        _log_registered_results(result)
    except Exception as exc:
        try:
            append_trial('D5', 'primary mechanism/placebo runner',
                         f'FAILED: {type(exc).__name__}: {exc}', prereg_dir=PREREG_DIR)
        except Exception as log_exc:
            print(f'FAILED TO LOG RUNNER FAILURE: {type(log_exc).__name__}: {log_exc}', file=sys.stderr)
        print(f'FAILED: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
