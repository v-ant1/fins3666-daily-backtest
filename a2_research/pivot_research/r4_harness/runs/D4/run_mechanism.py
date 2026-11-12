"""Frozen-only D4 primary predictive mechanism and prescribed placebos.

This script must not be run until ``specs/r4_prereg/D4.md`` has a valid
FROZEN date and matching SHA256. The gate and trial-budget check happen before
any development price file is opened. The worker input build does not call
this script except in --check-freeze mode, which stops at the gate.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np
from scipy.stats import rankdata
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from r4_harness.phase3 import (
    append_trial,
    authorize_trial,
    newey_west_t,
    prereg_digest,
    require_frozen_prereg,
)
from r4_harness.runs.D4.build_inputs import (
    DEFAULT_PIT_ROSTER,
    filing_time_network,
    read_13f_panel,
    read_development_bars,
)

PREREG_DIR = ROOT / 'specs' / 'r4_prereg'
INPUT_FILE = Path(__file__).resolve().parent / 'D4_INPUTS.npz'
OUTPUT_DIR = Path(__file__).resolve().parent
MECHANISM_PASS_FILE = OUTPUT_DIR / 'MECHANISM_PASS.json'
PIT_ROSTER_FILE = ROOT / 'r4_L4' / 'data' / '13f_top50_pit_roster.csv'
HORIZON = 5
NW_LAG = 4
PLACEBO_DRAWS = 500
SEED = 20261110
NETWORK_SHIFT = 20


def _row_normalize(adjacency: np.ndarray) -> np.ndarray:
    row_sum = adjacency.sum(axis=2)
    return np.divide(adjacency, row_sum[:, :, None],
                      out=np.zeros_like(adjacency), where=row_sum[:, :, None] > 0)


def _apply_roster_mask(adjacency: np.ndarray, roster: np.ndarray) -> np.ndarray:
    result = np.nan_to_num(np.asarray(adjacency, float).copy(), nan=0.0)
    for t in range(result.shape[0]):
        inactive = ~roster[:, t]
        result[t, inactive, :] = 0.0
        result[t, :, inactive] = 0.0
    for t in range(result.shape[0]):
        np.fill_diagonal(result[t], 0.0)
    return result


def _ncp(clv5: np.ndarray, adjacency: np.ndarray, roster: np.ndarray,
         age_days: np.ndarray) -> np.ndarray:
    """D4 NCP: row-normalized weighted five-session peer CLV at date t."""
    active_graph = _apply_roster_mask(adjacency, roster)
    weights = _row_normalize(active_graph)
    n, t = clv5.shape
    result = np.full((n, t), np.nan)
    for k in range(t):
        # D4 retains stale graphs; age is surfaced in QA, not used to censor.
        if not np.isfinite(age_days[k]):
            continue
        pressure = np.where(np.isfinite(clv5[:, k]), clv5[:, k], 0.0)
        result[:, k] = weights[k] @ pressure
        row_sum = weights[k].sum(axis=1)
        result[row_sum <= 0, k] = np.nan
        result[~roster[:, k], k] = np.nan
    return result


def _returns_from_dev_bars(assets: list[str], dates: list[str],
                           price_dirs=None) -> tuple[np.ndarray, np.ndarray]:
    """Load adjusted development open/close and construct the draft's return.

    Called only after the frozen-preregistration and trial-budget checks.
    The bar loader filters to 2020-11-27..2026-10-30 before parsing prices.
    """
    if price_dirs is not None:
        raise ValueError('custom price directories are not supported; use the validated development loader')
    n, t = len(assets), len(dates)
    op = np.full((n, t), np.nan)
    close = np.full((n, t), np.nan)
    date_ix = {d: i for i, d in enumerate(dates)}
    for i, asset in enumerate(assets):
        bars = read_development_bars(asset)
        for day, values in bars.items():
            j = date_ix.get(day)
            if j is not None:
                op[i, j] = values[0]
                close[i, j] = values[3]
    forward = np.full((n, t), np.nan)
    for k in range(t - HORIZON):
        buy = op[:, k+1]
        sell = close[:, k+HORIZON]
        valid = np.isfinite(buy) & np.isfinite(sell) & (buy > 0)
        forward[valid, k] = sell[valid] / buy[valid] - 1.0
    return op, forward


def _date_ic_series(scores: np.ndarray, forward: np.ndarray,
                    roster: np.ndarray) -> np.ndarray:
    values = []
    for t in range(scores.shape[1] - HORIZON):
        y = forward[:, t].copy()
        valid = roster[:, t] & np.isfinite(scores[:, t]) & np.isfinite(y)
        if valid.sum() < 3:
            values.append(np.nan)
            continue
        # Same-date EW30 demean: ranks are unchanged by subtracting one common
        # scalar, but this mirrors the frozen D4 draft's stated return basis.
        y[valid] -= float(np.mean(y[valid]))
        x_rank = rankdata(scores[valid, t], method='average')
        y_rank = rankdata(y[valid], method='average')
        if x_rank.std() == 0 or y_rank.std() == 0:
            values.append(np.nan)
        else:
            values.append(float(np.corrcoef(x_rank, y_rank)[0, 1]))
    return np.asarray(values, dtype=float)


def _stat(scores: np.ndarray, forward: np.ndarray,
          roster: np.ndarray) -> tuple[float, float, int, np.ndarray]:
    series = _date_ic_series(scores, forward, roster)
    finite = series[np.isfinite(series)]
    return (float(finite.mean()) if len(finite) else float('nan'),
            newey_west_t(finite, NW_LAG), len(finite), series)


def _one_sided_p(t_value: float) -> float:
    return float(norm.sf(t_value)) if np.isfinite(t_value) else float('nan')


def _shift_graphs(adjacency: np.ndarray, shift: int = NETWORK_SHIFT) -> np.ndarray:
    """Circularly align signal date t to the graph from t-shift sessions."""
    return np.roll(np.asarray(adjacency), int(shift), axis=0)


def _nw_mean_ci(series: np.ndarray, lag: int = NW_LAG,
                confidence: float = .90) -> tuple[float, float, float, float]:
    """Return mean, NW standard error, and a two-sided normal CI."""
    x = np.asarray(series, float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return (float('nan'),) * 4
    mean = float(x.mean())
    t_value = newey_west_t(x, lag)
    se = abs(mean / t_value) if np.isfinite(t_value) and t_value != 0 else float('nan')
    if not np.isfinite(se):
        # The NW t helper has an exact-zero convention. Compute the same
        # Bartlett long-run variance directly for a zero-mean series.
        u = x - mean
        n = len(x)
        used_lag = min(max(int(lag), 0), n - 1)
        longvar = float(u @ u / n)
        for k in range(1, used_lag + 1):
            longvar += 2 * (1 - k / (used_lag + 1)) * float(u[k:] @ u[:-k]) / n
        se = float(np.sqrt(max(longvar, 0.0) / n))
    critical = float(norm.ppf((1 + confidence) / 2))
    return mean, se, mean - critical * se, mean + critical * se


def _equivalence_result(series: np.ndarray, draw_means: np.ndarray,
                        margin: float = .00577) -> dict:
    mean, se, lower, upper = _nw_mean_ci(series)
    p_lower = _one_sided_p((mean + margin) / se) if se > 0 else float('nan')
    p_upper = float(norm.cdf((mean - margin) / se)) if se > 0 else float('nan')
    equivalence_p = max(p_lower, p_upper) if np.isfinite(p_lower + p_upper) else float('nan')
    q95_abs = float(np.quantile(np.abs(draw_means), .95, method='linear'))
    return {
        'mean_ic': mean, 'nw_se': se, 'ci90_lower': lower, 'ci90_upper': upper,
        'p_lower_tost': p_lower, 'p_upper_tost': p_upper,
        'equivalence_p': equivalence_p, 'p95_abs_draw_mean_ic': q95_abs,
        'margin': margin,
        'passed': bool(lower > -margin and upper < margin and q95_abs < margin),
    }


def _unique_network_snapshots(adjacency: np.ndarray) -> tuple[np.ndarray, list[np.ndarray]]:
    """Compress carried-forward dated graphs for placebo generation speed."""
    labels = np.zeros(adjacency.shape[0], dtype=int)
    snapshots: list[np.ndarray] = []
    for t, graph in enumerate(adjacency):
        found = None
        for k, prior in enumerate(snapshots):
            if np.array_equal(graph, prior):
                found = k
                break
        if found is None:
            snapshots.append(graph.copy())
            found = len(snapshots) - 1
        labels[t] = found
    return labels, snapshots


def _directed_degree_rewire(graph: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Attempt 10E directed double-edge swaps, preserving every in/out degree."""
    source = np.asarray(graph, float)
    edges = [tuple(x) for x in np.argwhere(source > 0)]
    if not edges:
        return np.zeros_like(source)
    binary = source > 0
    attempts = 10 * len(edges)
    # Uniformly select two distinct directed edges for each attempted swap.
    a_draws = rng.integers(0, len(edges), size=attempts)
    b_draws = rng.integers(0, len(edges) - 1, size=attempts) if len(edges) > 1 else np.zeros(attempts, int)
    if len(edges) > 1:
        b_draws += b_draws >= a_draws
    # A complete directed graph on its nonzero rows has no absent destination
    # pairs, so every one of the registered attempts is necessarily skipped.
    nonzero_nodes = np.flatnonzero(binary.any(axis=1) | binary.any(axis=0))
    complete = len(edges) == len(nonzero_nodes) * (len(nonzero_nodes) - 1)
    candidates = () if complete else zip(a_draws, b_draws)
    for a_raw, b_raw in candidates:
        if len(edges) < 2:
            break
        a, b = int(a_raw), int(b_raw)
        u, v = edges[a]
        x, y = edges[b]
        if len({u, v, x, y}) < 4:
            continue
        # (u -> v, x -> y) becomes (u -> y, x -> v).
        if binary[u, y] or binary[x, v]:
            continue
        binary[u, v] = binary[x, y] = False
        binary[u, y] = binary[x, v] = True
        edges[a] = (u, y)
        edges[b] = (x, v)
    original_weights = source[source > 0].copy()
    rng.shuffle(original_weights)
    out = np.zeros_like(source)
    for (u, v), weight in zip(edges, original_weights):
        out[u, v] = weight
    return _row_normalize(out[None, :, :])[0]


def _random_directed_links(graph: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Sample E directed non-self links, retaining the original zero rows."""
    source = np.asarray(graph, float)
    n = source.shape[0]
    edges = np.argwhere(source > 0)
    count = len(edges)
    if not count:
        return np.zeros_like(source)
    active_sources = np.flatnonzero(np.any(source > 0, axis=1))
    possible = np.asarray([(i, j) for i in active_sources for j in range(n) if j != i], int)
    if count > len(possible):
        raise ValueError('cannot place the registered number of directed links while preserving zero rows')
    chosen = rng.choice(len(possible), size=count, replace=False)
    selected = possible[chosen]
    weights = source[source > 0].copy()
    rng.shuffle(weights)
    out = np.zeros_like(source)
    out[selected[:, 0], selected[:, 1]] = weights
    return _row_normalize(out[None, :, :])[0]


def _placebo_cube(snapshots: list[np.ndarray], labels: np.ndarray,
                  roster: np.ndarray, family: str,
                  rng: np.random.Generator) -> np.ndarray:
    """Create one placebo graph cube using the shared frozen RNG stream."""
    generated = []
    for graph in snapshots:
        if family == 'degree_preserving':
            generated.append(_directed_degree_rewire(graph, rng))
        elif family == 'random_links':
            generated.append(_random_directed_links(graph, rng))
        else:
            raise ValueError('family must be degree_preserving or random_links')
    return _apply_roster_mask(np.asarray(generated)[labels].copy(), roster)


def _summarize_draws(draw_means: list[float], draw_t: list[float],
                     draw_series: list[np.ndarray]) -> dict:
    means = np.asarray(draw_means, float)
    ts = np.asarray(draw_t, float)
    means = means[np.isfinite(means)]
    ts = ts[np.isfinite(ts)]
    series = np.asarray(draw_series, float)
    mean_series = np.nanmean(series, axis=0)
    return {
        'draws': int(len(means)),
        'mean_ic': float(np.mean(means)),
        'p50_mean_ic': float(np.quantile(means, .50)),
        'p95_mean_ic': float(np.quantile(means, .95, method='linear')),
        'p99_mean_ic': float(np.quantile(means, .99)),
        'p50_nw_t': float(np.quantile(ts, .50)),
        'share_abs_nw_t_ge_2': float(np.mean(np.abs(ts) >= 2.0)),
        'mean_datewise_ic_series': mean_series.tolist(),
    }


def _variant2_scores(assets, dates, roster, clv5, age) -> np.ndarray:
    """Build D4 variant 2 using sum_m min(weight_i,m, weight_j,m)."""
    coverage, positions, fixed_roster, pit_rosters, _ = read_13f_panel(DEFAULT_PIT_ROSTER)
    alt, *_ = filing_time_network(
        assets, dates, roster, coverage, positions, fixed_roster, pit_rosters,
        edge_method='sum_min',
    )
    return _ncp(clv5, alt, roster, age)


def _randomized_family(family, snapshots, labels, roster, clv5, forward, rng):
    draw_means, draw_t, draw_series = [], [], []
    for _ in range(PLACEBO_DRAWS):
        cube = _placebo_cube(snapshots, labels, roster, family, rng)
        score = _ncp(clv5, cube, roster, np.ones(clv5.shape[1]))
        series = _date_ic_series(score, forward, roster)
        finite = series[np.isfinite(series)]
        draw_means.append(float(finite.mean()) if len(finite) else float('nan'))
        draw_t.append(newey_west_t(finite, NW_LAG))
        draw_series.append(series)
    return (_summarize_draws(draw_means, draw_t, draw_series),
            np.asarray(draw_means), np.asarray(draw_t))


def _quantile_summary(draws: np.ndarray) -> dict:
    x = np.asarray(draws, float)
    return {key: float(np.quantile(x, q, method='linear'))
            for key, q in (('min', 0), ('q05', .05), ('q25', .25),
                           ('median', .5), ('q75', .75), ('q95', .95), ('max', 1))}


def _write_results(result: dict, dates: list[str], primary_series: np.ndarray,
                   shifted_series: np.ndarray, shift_difference: np.ndarray,
                   variant2_series: np.ndarray, draws: dict) -> None:
    result_path = OUTPUT_DIR / 'MECHANISM_RESULTS.json'
    result_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    with (OUTPUT_DIR / 'MECHANISM_PLACEBO_DRAWS.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['family', 'draw', 'mean_rank_ic', 'nw_t_lag4'])
        for family in ('degree_preserving', 'random_links'):
            item = draws[family]
            for i, (mean, stat) in enumerate(zip(item['draw_means'], item['draw_t']), 1):
                w.writerow([family, i, mean, stat])
    with (OUTPUT_DIR / 'MECHANISM_IC_SERIES.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['date', 'primary_ic', 'time_shift_20_ic', 'primary_minus_shift_ic', 'variant2_ic',
                    'degree_placebo_mean_ic', 'random_link_placebo_mean_ic'])
        degree_series = np.asarray(result['placebos']['degree_preserving']['mean_datewise_ic_series'], float)
        random_series = np.asarray(result['placebos']['random_links']['mean_datewise_ic_series'], float)
        n_rows = min(len(dates) - HORIZON, len(primary_series))
        for i in range(n_rows):
            w.writerow([dates[i], primary_series[i], shifted_series[i], shift_difference[i],
                        variant2_series[i], degree_series[i], random_series[i]])


def _write_markdown(result: dict) -> None:
    f = lambda x: 'NA' if x is None or not np.isfinite(x) else f'{x:.6g}'
    ep = result['endpoints']
    lines = [
        '# D4 mechanism and placebo results', '',
        f"**Mechanism gate: {'PASS' if result['passed'] else 'FAIL'}.** Frozen SHA-256 verified: `{result['prereg_sha256']}`.",
        f"Development sample: {result['sample']['start']} to {result['sample']['end']}; {result['sample']['sessions']:,} sessions. No portfolio or holdout run.",
        '', '## Registered endpoints', '',
        '| Endpoint | Estimate / test | NW t (lag 4) | Raw p-value | Result |',
        '|---|---:|---:|---:|---|',
    ]
    for key in ('D4-1 primary IC', 'D4-2 degree-preserving comparison', 'D4-3 random-link comparison',
                'D4-4 fixed 20-session shift comparison', 'D4-5 degree placebo equivalence',
                'D4-6 random-link placebo equivalence', 'D4-7 shifted placebo equivalence',
                'D4-8 variant-2 IC'):
        e = ep[key]
        estimate = e.get('mean_ic', e.get('difference_mean_ic'))
        t_value = e.get('nw_t', e.get('difference_nw_t'))
        if 'placebo_p95' in e:
            display = f"observed {f(estimate)}; null p95 {f(e['placebo_p95'])}"
        elif key.startswith('D4-4'):
            display = f"paired mean difference {f(estimate)}"
        elif 'ci90_lower' in e:
            display = f"mean {f(estimate)}; 90% CI [{f(e['ci90_lower'])}, {f(e['ci90_upper'])}]"
        else:
            display = f(estimate)
        status = 'PASS' if e.get('passed', False) else ('DIAGNOSTIC' if key.startswith('D4-8') else 'FAIL')
        lines.append(f"| {key} | {display} | {f(t_value)} | {f(e['raw_p'])} | {status} |")
    lines.extend(['', '## Randomized placebo distributions', '',
                  '| Family | Draws | Mean IC quantiles (min, 5th, 25th, median, 75th, 95th, max) | p95 absolute draw mean |',
                  '|---|---:|---|---:|'])
    for family in ('degree_preserving', 'random_links'):
        p = result['placebos'][family]
        q = p['mean_ic_quantiles']
        qtext = ', '.join(f(q[k]) for k in ('min','q05','q25','median','q75','q95','max'))
        lines.append(f"| {family} | {p['draws']} | {qtext} | {f(p['equivalence']['p95_abs_draw_mean_ic'])} |")
    shift = result['placebos']['time_shift_20_sessions']
    lines.extend(['', 'The 20-session shift is the frozen deterministic circular alignment, not a randomized family. Its endpoint is the paired Newey–West comparison of the primary and shifted date-wise IC series; the shifted-series equivalence test is reported separately.',
                  '', '## Placebo equivalence checks', '',
                  '| Family | Mean averaged IC | 90% NW CI | Larger TOST p | p95 absolute draw mean | Margin | Result |',
                  '|---|---:|---:|---:|---:|---:|---|'])
    for family, label in (('degree_preserving','degree-preserving'), ('random_links','random-link'), ('time_shift_20_sessions','fixed 20-session shift')):
        e = result['placebos'][family]['equivalence']
        lines.append(f"| {label} | {f(e['mean_ic'])} | [{f(e['ci90_lower'])}, {f(e['ci90_upper'])}] | {f(e['equivalence_p'])} | {f(e['p95_abs_draw_mean_ic'])} | {f(e['margin'])} | {'PASS' if e['passed'] else 'FAIL'} |")
    lines.extend(['', '## Plain-English reading', '',
                  'A direction advances only if the primary IC, all three placebo comparisons, and all three placebo-equivalence checks pass. Variant 2 is an inferential diagnostic and cannot replace variant 1. Raw p-values are shown; round-wide Holm adjustment remains the coordinator’s responsibility.',
                  '', '## Trial logging', '',
                  'Endpoints D4-1 through D4-8 were each recorded once through the harness trial logger. The portfolio endpoint D4-9 was not run or logged as an outcome.',
                  'A preflight invocation stopped at the saved-NCP check before endpoint statistics because the old runner incorrectly required target-own CLV5. After removing that check, the endpoint computation ran once. A formatting error occurred after results were saved; Markdown and trial rows were finalized from that saved JSON without rerunning or recomputing endpoints.'])
    (OUTPUT_DIR / 'MECHANISM_RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def _endpoint_log_rows(result: dict) -> list[tuple[str, str]]:
    """Build one compact logger row for each of the eight registered endpoints."""
    ep = result['endpoints']
    rows = []
    for name, e in ep.items():
        mean = e.get('mean_ic')
        if mean is None:
            mean = e.get('difference_mean_ic')
        t_value = e.get('nw_t')
        if t_value is None:
            t_value = e.get('difference_nw_t')
        pieces = []
        if mean is not None:
            pieces.append(f'mean_IC={float(mean):.8g}')
        if t_value is not None:
            pieces.append(f'NW_t={float(t_value):.8g}')
        pieces.append(f"raw_p={float(e['raw_p']):.8g}")
        if 'placebo_p95' in e:
            pieces.append(f"null_p95={float(e['placebo_p95']):.8g}")
        if 'ci90_lower' in e:
            pieces.append(f"CI90=[{float(e['ci90_lower']):.8g},{float(e['ci90_upper']):.8g}]")
            pieces.append(f"p95_abs={float(e['p95_abs_draw_mean_ic']):.8g}")
        if 'passed' in e and not name.startswith('D4-8'):
            pieces.append(f"gate={bool(e['passed'])}")
        elif name.startswith('D4-8'):
            pieces.append('diagnostic_only=true')
        rows.append((name, '; '.join(pieces)))
    if len(rows) != 8:
        raise ValueError(f'expected 8 D4 endpoint rows, found {len(rows)}')
    return rows


def _finalize_existing_result() -> dict:
    """Write the report and endpoint log from saved results without recomputing."""
    result_path = OUTPUT_DIR / 'MECHANISM_RESULTS.json'
    if not result_path.is_file():
        raise FileNotFoundError('cannot finalize without MECHANISM_RESULTS.json')
    result = json.loads(result_path.read_text(encoding='utf-8'))
    expected = prereg_digest((PREREG_DIR / 'D4.md').read_text(encoding='utf-8'))
    if result.get('prereg_sha256') != expected:
        raise ValueError('saved mechanism result hash does not match frozen D4.md')
    log = ROOT / 'specs' / 'r4_trials.md'
    text = log.read_text(encoding='utf-8')
    if any(re.match(r'^\|\s*\d+\s*\|\s*D4\s*\|', line) for line in text.splitlines()):
        raise RuntimeError('D4 trial-log rows already exist; refusing duplicate endpoint logging')
    authorize_trial('D4', prereg_dir=PREREG_DIR)
    used = sum(bool(re.match(r'^\|\s*\d+\s*\|', line)) for line in text.splitlines())
    rows = _endpoint_log_rows(result)
    if used + len(rows) > 30:
        raise RuntimeError(f'{len(rows)} D4 endpoint rows exceed remaining trial-log budget ({used}/30 already used)')
    for name, detail in rows:
        append_trial('D4', name, detail, prereg_dir=PREREG_DIR)
    _write_markdown(result)
    return result


def run_d4_mechanism(input_file: Path = INPUT_FILE) -> dict:
    """Execute the prespecified D4 mechanism/placebos after the governance gate."""
    with np.load(input_file, allow_pickle=False) as z:
        assets = z['assets'].astype(str).tolist()
        dates = z['dates'].astype(str).tolist()
        roster = z['roster_mask'].astype(bool)
        clv5 = z['clv5'].astype(float)
        ncp_saved = z['ncp'].astype(float)
        adjacency = z['adjacency'].astype(float)
        age = z['network_age_days'].astype(float)
    _, forward = _returns_from_dev_bars(assets, dates)
    scores = _ncp(clv5, adjacency, roster, age)
    # Verify signal output built under QA matches the runner reconstruction.
    if not np.allclose(scores, ncp_saved, atol=1e-12, rtol=0, equal_nan=True):
        raise ValueError('NCP reconstruction differs from D4_INPUTS.npz; rebuild inputs')
    real_mean, real_t, n_dates, primary_series = _stat(scores, forward, roster)
    labels, snapshots = _unique_network_snapshots(adjacency)
    rng = np.random.default_rng(SEED)
    degree_summary, degree_means, degree_ts = _randomized_family(
        'degree_preserving', snapshots, labels, roster, clv5, forward, rng)
    random_summary, random_means, random_ts = _randomized_family(
        'random_links', snapshots, labels, roster, clv5, forward, rng)

    # Frozen deterministic circular shift: signal date t receives graph t-20,
    # with wraparound over the dated graph sequence.
    shifted_adj = _shift_graphs(adjacency)
    shifted_age = np.roll(age, NETWORK_SHIFT)
    shifted_score = _ncp(clv5, shifted_adj, roster, shifted_age)
    shifted_mean, shifted_t, shifted_n, shifted_series = _stat(shifted_score, forward, roster)
    diff_series = primary_series - shifted_series
    diff_finite = diff_series[np.isfinite(diff_series)]
    difference_mean = float(diff_finite.mean())
    difference_t = newey_west_t(diff_finite, NW_LAG)
    difference_p = _one_sided_p(difference_t)

    degree_p = float((1 + np.sum(degree_means >= real_mean)) / (PLACEBO_DRAWS + 1))
    random_p = float((1 + np.sum(random_means >= real_mean)) / (PLACEBO_DRAWS + 1))
    degree_equiv = _equivalence_result(
        np.asarray(degree_summary['mean_datewise_ic_series']), degree_means)
    random_equiv = _equivalence_result(
        np.asarray(random_summary['mean_datewise_ic_series']), random_means)
    shifted_equiv = _equivalence_result(shifted_series, np.asarray([shifted_mean]))

    v2_scores = _variant2_scores(assets, dates, roster, clv5, age)
    v2_mean, v2_t, v2_n, v2_series = _stat(v2_scores, forward, roster)
    v2_p = _one_sided_p(v2_t)
    p1 = _one_sided_p(real_t)

    endpoints = {
        'D4-1 primary IC': {'mean_ic': real_mean, 'nw_t': real_t, 'dates': n_dates,
                            'raw_p': p1, 'passed': bool(real_mean > 0 and real_t >= 2 and real_mean >= .0183)},
        'D4-2 degree-preserving comparison': {'mean_ic': real_mean, 'nw_t': real_t,
                                              'placebo_p95': degree_summary['p95_mean_ic'],
                                              'raw_p': degree_p,
                                              'passed': bool(real_mean > degree_summary['p95_mean_ic'] and degree_p < .05)},
        'D4-3 random-link comparison': {'mean_ic': real_mean, 'nw_t': real_t,
                                        'placebo_p95': random_summary['p95_mean_ic'],
                                        'raw_p': random_p,
                                        'passed': bool(real_mean > random_summary['p95_mean_ic'] and random_p < .05)},
        'D4-4 fixed 20-session shift comparison': {'difference_mean_ic': difference_mean,
                                                   'difference_nw_t': difference_t,
                                                   'dates': int(len(diff_finite)),
                                                   'raw_p': difference_p,
                                                   'passed': bool(difference_mean > 0 and difference_p < .05)},
        'D4-5 degree placebo equivalence': {**degree_equiv, 'raw_p': degree_equiv['equivalence_p']},
        'D4-6 random-link placebo equivalence': {**random_equiv, 'raw_p': random_equiv['equivalence_p']},
        'D4-7 shifted placebo equivalence': {**shifted_equiv, 'raw_p': shifted_equiv['equivalence_p']},
        'D4-8 variant-2 IC': {'mean_ic': v2_mean, 'nw_t': v2_t, 'dates': v2_n,
                              'raw_p': v2_p, 'passed': False},
    }
    passed = all(endpoints[f'D4-{i} ' + name]['passed'] for i, name in (
        (1, 'primary IC'), (2, 'degree-preserving comparison'),
        (3, 'random-link comparison'), (4, 'fixed 20-session shift comparison'),
        (5, 'degree placebo equivalence'), (6, 'random-link placebo equivalence'),
        (7, 'shifted placebo equivalence')))
    result = {
        'approach': 'D4',
        'prereg_sha256': prereg_digest((PREREG_DIR / 'D4.md').read_text(encoding='utf-8')),
        'sample': {'start': dates[0], 'end': dates[-1], 'sessions': len(dates)},
        'passed': bool(passed),
        'endpoints': endpoints,
        'placebos': {
            'degree_preserving': {'draws': PLACEBO_DRAWS,
                                  'mean_ic_quantiles': _quantile_summary(degree_means),
                                  'p95_mean_ic': degree_summary['p95_mean_ic'],
                                  'equivalence': degree_equiv,
                                  'mean_datewise_ic_series': degree_summary['mean_datewise_ic_series']},
            'random_links': {'draws': PLACEBO_DRAWS,
                             'mean_ic_quantiles': _quantile_summary(random_means),
                             'p95_mean_ic': random_summary['p95_mean_ic'],
                             'equivalence': random_equiv,
                             'mean_datewise_ic_series': random_summary['mean_datewise_ic_series']},
            'time_shift_20_sessions': {'mean_ic': shifted_mean, 'nw_t': shifted_t,
                                       'dates': shifted_n, 'equivalence': shifted_equiv},
        },
    }
    draw_objects = {
        'degree_preserving': {'draw_means': degree_means, 'draw_t': degree_ts},
        'random_links': {'draw_means': random_means, 'draw_t': random_ts},
    }
    _write_results(result, dates, primary_series, shifted_series, diff_series, v2_series, draw_objects)
    decision_file = OUTPUT_DIR / ('MECHANISM_PASS.json' if passed else 'MECHANISM_FAIL.json')
    decision_file.write_text(json.dumps({
        'approach': 'D4', 'passed': bool(passed), 'prereg_sha256': result['prereg_sha256'],
        'primary_mean_ic': real_mean, 'primary_nw_t_lag4': real_t,
        'mechanism_results': str(OUTPUT_DIR / 'MECHANISM_RESULTS.json'),
    }, indent=2), encoding='utf-8')
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-freeze', action='store_true',
                        help='validate D4.md only, then exit without loading input or price files')
    parser.add_argument('--finalize-logs', action='store_true',
                        help='write report/log rows from an existing result JSON without recomputing endpoints')
    parser.add_argument('--inputs', type=Path, default=INPUT_FILE)
    args = parser.parse_args(argv)
    try:
        prereg = require_frozen_prereg('D4', prereg_dir=PREREG_DIR)
    except Exception as exc:
        print(f'REFUSED: D4 pre-registration is not frozen and hash-valid: {exc}', file=sys.stderr)
        return 2
    if args.check_freeze:
        print(f'FROZEN D4 preregistration verified: {prereg}')
        return 0
    if args.finalize_logs:
        try:
            result = _finalize_existing_result()
        except Exception as exc:
            print(f'FAILED: {type(exc).__name__}: {exc}', file=sys.stderr)
            return 1
        print(json.dumps({'finalized': True, 'passed': result['passed'],
                          'endpoints': len(result['endpoints']),
                          'prereg_sha256': result['prereg_sha256']}, indent=2))
        return 0
    existing = sorted(p.name for p in OUTPUT_DIR.glob('MECHANISM_*'))
    if existing:
        print(f"REFUSED: D4 mechanism artifacts already exist; refusing a second run: {existing}", file=sys.stderr)
        return 2
    # Provisional input QA may use the legacy fixed Q2-2026 cohort, but it is
    # never eligible for a D4 outcome run. Validate inputs without touching
    # prices/returns; the D4 bundle must be rebuilt after L4's PIT roster lands.
    if not PIT_ROSTER_FILE.is_file():
        print(f'REFUSED: point-in-time manager roster is missing: {PIT_ROSTER_FILE}', file=sys.stderr)
        return 2
    try:
        with np.load(args.inputs, allow_pickle=False) as inputs:
            provenance = inputs['manager_roster_source'].astype(str).tolist()
        if not provenance or not provenance[0].startswith('loaded '):
            print('REFUSED: D4 input bundle predates the point-in-time manager roster; rebuild inputs first', file=sys.stderr)
            return 2
    except Exception as exc:
        print(f'REFUSED: cannot verify D4 input provenance: {exc}', file=sys.stderr)
        return 2
    # Reserve the complete registered endpoint block before opening prices.
    try:
        authorize_trial('D4', prereg_dir=PREREG_DIR)
        log = ROOT / 'specs' / 'r4_trials.md'
        import re
        used = sum(bool(re.match(r'^\|\s*\d+\s*\|', line)) for line in log.read_text(encoding='utf-8').splitlines())
        if used + 8 > 30:
            raise RuntimeError(f'8 D4 endpoint rows exceed remaining trial-log budget ({used}/30 already used)')
        result = run_d4_mechanism(args.inputs)
        for name, detail in _endpoint_log_rows(result):
            append_trial('D4', name, detail, prereg_dir=PREREG_DIR)
        _write_markdown(result)
    except Exception as exc:
        print(f'FAILED: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
