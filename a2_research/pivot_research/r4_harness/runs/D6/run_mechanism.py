from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from r4_harness.phase3 import (
    append_trial, prereg_digest, run_registered_trial,
)

PREREG_DIR = ROOT / 'specs' / 'r4_prereg'
TRIAL_LOG = ROOT / 'specs' / 'r4_trials.md'
OUT = Path(__file__).resolve().parent
INPUT = OUT / 'D6_INPUTS.npz'
RESULTS_MD = OUT / 'MECHANISM_RESULTS.md'
RESULTS_JSON = OUT / 'D6_MECHANISM_RESULTS.json'
PASS_JSON = OUT / 'MECHANISM_PASS.json'
FAIL_JSON = OUT / 'MECHANISM_FAIL.json'
ASSETS = ['SPY', 'TLT', 'IEF', 'SHY', 'TIP']
TREASURY = [1, 2, 3, 4]
TARGET_START = '2021-08'
TARGET_END = '2026-09'
NW_LAG = 11
PLACEBO_DRAWS = 500
SEED = 20261110


def _months(dates):
    out = {}
    for i, d in enumerate(dates):
        out.setdefault(d[:7], []).append(i)
    return {m: ix for m, ix in out.items()}


def _one_sided_p(t, direction):
    if not np.isfinite(t):
        return float('nan')
    return float(norm.sf(t) if direction == 'positive' else norm.cdf(t))


def _ols_nw(y, predictors, lag=NW_LAG):
    """OLS with intercept and Bartlett Newey-West HAC covariance."""
    y = np.asarray(y, float)
    predictors = [np.asarray(x, float) for x in predictors]
    X = np.column_stack([np.ones(len(y)), *predictors])
    if len(y) <= X.shape[1] or not np.isfinite(X).all() or not np.isfinite(y).all():
        raise ValueError('regression requires complete finite observations and positive residual df')
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ (X.T @ y)
    resid = y - X @ beta
    score = X * resid[:, None]
    meat = score.T @ score
    lag = min(int(lag), len(y) - 1)
    for k in range(1, lag + 1):
        weight = 1.0 - k / (lag + 1.0)
        cross = score[k:].T @ score[:-k]
        meat += weight * (cross + cross.T)
    covariance = xtx_inv @ meat @ xtx_inv
    se = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    tstat = np.divide(beta, se, out=np.full_like(beta, np.nan), where=se > 0)
    return {
        'n': int(len(y)), 'coefficients': beta, 'standard_errors': se,
        't_statistics': tstat, 'residuals': resid,
    }


def _build_monthly(arrays):
    dates = arrays['dates'].astype(str).tolist()
    assets = arrays['assets'].astype(str).tolist()
    if assets != ASSETS:
        raise ValueError(f'input asset order differs from frozen set: {assets}')
    groups = _months(dates)
    month_list = sorted(groups)
    last_close = {}
    first_open = {}
    for month in month_list:
        ix = groups[month]
        last_close[month] = arrays['adjusted_close'][:, ix[-1]].astype(float)
        first_open[month] = arrays['adjusted_open'][:, ix[0]].astype(float)
    formation_months = []
    y, m = 2021, 7
    while (y, m) <= (2026, 8):
        formation_months.append(f'{y:04d}-{m:02d}')
        m += 1
        if m == 13:
            y, m = y + 1, 1
    observations = []
    for fm in formation_months:
        y, m = map(int, fm.split('-'))
        target = f'{y + (m == 12):04d}-{(m % 12) + 1:02d}'
        ty, tm = map(int, target.split('-'))
        next_month = f'{ty + (tm == 12):04d}-{(tm % 12) + 1:02d}'
        if fm not in last_close or target not in first_open or next_month not in first_open:
            raise ValueError(f'missing month-end/first-open input for formation {fm}')
        ix = month_list.index(fm)
        if ix < 12 or ix < 6:
            raise ValueError(f'insufficient trend warm-up for {fm}')
        prev_month = month_list[ix - 1]
        month_12 = month_list[ix - 12]
        month_6 = month_list[ix - 6]
        trend12 = last_close[prev_month] / last_close[month_12] - 1.0
        trend6 = last_close[prev_month] / last_close[month_6] - 1.0
        target_ret = first_open[next_month] / first_open[target] - 1.0
        observations.append({
            'formation_month': fm, 'target_month': target,
            'trend12': trend12, 'trend6': trend6,
            'spy_return': float(target_ret[0]),
            'treasury_return': float(np.mean(target_ret[TREASURY])),
            'spy_trend12': float(trend12[0]),
            'bond_trend12': float(np.mean(trend12[TREASURY])),
            'spy_trend6': float(trend6[0]),
            'bond_trend6': float(np.mean(trend6[TREASURY])),
        })
    if observations[0]['target_month'] != TARGET_START or observations[-1]['target_month'] != TARGET_END:
        raise ValueError('target-month labels do not match frozen development window')
    return observations, dates


def _regression_result(y, predictor, control, direction):
    fit = _ols_nw(y, [predictor, control], NW_LAG)
    beta, se, t = (float(fit[k][1]) for k in ('coefficients', 'standard_errors', 't_statistics'))
    return {
        'n': fit['n'], 'beta': beta, 'se': se, 'nw_t_lag11': t,
        'one_sided_raw_p': _one_sided_p(t, direction),
        'direction': direction,
    }


def _own_trend_diagnostics(obs, suffix):
    trend_spy = np.asarray([o[f'spy_trend{suffix}'] for o in obs])
    trend_bond = np.asarray([o[f'bond_trend{suffix}'] for o in obs])
    spy = np.asarray([o['spy_return'] for o in obs])
    treasury = np.asarray([o['treasury_return'] for o in obs])
    fit_spy = _ols_nw(spy, [trend_spy], NW_LAG)
    fit_bond = _ols_nw(treasury, [trend_bond], NW_LAG)
    return {
        'spy_return_on_spy_own_trend': {
            'beta': float(fit_spy['coefficients'][1]),
            'se': float(fit_spy['standard_errors'][1]),
            'nw_t_lag11': float(fit_spy['t_statistics'][1]),
        },
        'treasury_return_on_bond_own_trend': {
            'beta': float(fit_bond['coefficients'][1]),
            'se': float(fit_bond['standard_errors'][1]),
            'nw_t_lag11': float(fit_bond['t_statistics'][1]),
        },
    }


def _run_development():
    # Called only inside run_registered_trial, after frozen hash and budget checks.
    with np.load(INPUT, allow_pickle=False) as z:
        data = {k: z[k].copy() for k in z.files}
    obs, daily_dates = _build_monthly(data)
    y_spy = np.asarray([o['spy_return'] for o in obs])
    y_bond = np.asarray([o['treasury_return'] for o in obs])
    B12 = np.asarray([o['bond_trend12'] for o in obs])
    E12 = np.asarray([o['spy_trend12'] for o in obs])
    B6 = np.asarray([o['bond_trend6'] for o in obs])
    E6 = np.asarray([o['spy_trend6'] for o in obs])

    primary = _regression_result(y_spy, B12, E12, 'positive')
    secondary = _regression_result(y_bond, E12, B12, 'negative')
    sensitivity_be = _regression_result(y_spy, B6, E6, 'positive')
    sensitivity_eb = _regression_result(y_bond, E6, B6, 'negative')

    rng = np.random.default_rng(SEED)
    n = primary['n']
    low, high = 12, n - 12
    if high < low:
        raise ValueError(f'primary valid N={n} too small for registered circular shifts')
    offsets = rng.integers(low, high + 1, size=PLACEBO_DRAWS)
    placebo_betas = np.empty(PLACEBO_DRAWS, dtype=float)
    for j, offset in enumerate(offsets):
        shifted = np.roll(B12, int(offset))
        placebo_betas[j] = _regression_result(y_spy, shifted, E12, 'positive')['beta']
    p95 = float(np.quantile(placebo_betas, 0.95))
    percentile = float(np.mean(placebo_betas <= primary['beta']))
    placebo_p = float((1 + np.count_nonzero(placebo_betas >= primary['beta'])) /
                      (PLACEBO_DRAWS + 1))

    primary_gate = bool(primary['beta'] > 0 and primary['nw_t_lag11'] >= 2.0 and primary['beta'] > p95)
    prereg_text = (PREREG_DIR / 'D6.md').read_text(encoding='utf-8')
    digest = prereg_digest(prereg_text)
    # Holm adjustment cannot be finalized here: the frozen family includes D4/D5 and
    # the D6 portfolio endpoint, which is expressly outside this worker's run scope.
    result = {
        'approach': 'D6', 'passed': primary_gate,
        'prereg_sha256': digest,
        'development': {
            'daily_input_first': daily_dates[0], 'daily_input_last': daily_dates[-1],
            'target_first': obs[0]['target_month'], 'target_last': obs[-1]['target_month'],
            'observation_count': n, 'assets': ASSETS,
            'trend_definitions': {
                '12_minus_1': 'adj_close[m-1]/adj_close[m-12]-1',
                '6_minus_1': 'adj_close[m-1]/adj_close[m-6]-1',
            },
            'target_return': 'first adjusted open in target month to first adjusted open in following month',
        },
        'endpoints': {
            'D6-1_12m_bond_to_SPY': primary,
            'D6-2_12m_SPY_to_Treasury': secondary,
            'D6-3_observed_vs_circular_shift': {
                'draws': PLACEBO_DRAWS, 'seed': SEED,
                'offset_min_inclusive': low, 'offset_max_inclusive': high,
                'observed_beta': primary['beta'], 'null_beta_p95': p95,
                'observed_percentile': percentile,
                'one_sided_randomization_p': placebo_p,
            },
            'D6-4_6m_bond_to_SPY': sensitivity_be,
            'D6-5_6m_SPY_to_Treasury': sensitivity_eb,
            'D6-6_portfolio_net_excess_vs_EW5': {
                'status': 'NOT RUN', 'reason': 'portfolio stage is expressly excluded from this dispatch',
            },
        },
        'diagnostics': {
            '12_minus_1_reversed_direction': secondary,
            '12_minus_1_target_own_trend_only': _own_trend_diagnostics(obs, '12'),
            '6_minus_1_target_own_trend_only': _own_trend_diagnostics(obs, '6'),
        },
        'placebo_distribution': {
            'n': PLACEBO_DRAWS,
            'min': float(np.min(placebo_betas)),
            'q05': float(np.quantile(placebo_betas, .05)),
            'q25': float(np.quantile(placebo_betas, .25)),
            'median': float(np.median(placebo_betas)),
            'q75': float(np.quantile(placebo_betas, .75)),
            'q95': p95,
            'max': float(np.max(placebo_betas)),
            'mean': float(np.mean(placebo_betas)),
            'std': float(np.std(placebo_betas, ddof=1)),
        },
        'inference': {
            'newey_west': 'OLS with intercept, Bartlett HAC lag 11; asymptotic one-sided normal p-values',
            'holm': 'Pending coordinator calculation over the complete frozen D4-D6 family; no portfolio endpoint was run.',
        },
        'gate': {
            'primary_beta_positive': bool(primary['beta'] > 0),
            'primary_nw_t_at_least_2': bool(primary['nw_t_lag11'] >= 2.0),
            'observed_beta_exceeds_placebo_p95': bool(primary['beta'] > p95),
            'primary_mechanism_gate': primary_gate,
        },
    }
    RESULTS_JSON.write_text(json.dumps(result, indent=2), encoding='utf-8')
    np.savetxt(OUT / 'D6_PLACEBO_BETAS.csv', placebo_betas, delimiter=',', header='placebo_beta_BE', comments='')
    _write_markdown(result)
    (PASS_JSON if primary_gate else FAIL_JSON).write_text(json.dumps({
        'approach': 'D6', 'passed': primary_gate, 'prereg_sha256': digest,
        'primary': primary, 'placebo': result['endpoints']['D6-3_observed_vs_circular_shift'],
        'gate': result['gate'],
    }, indent=2), encoding='utf-8')
    stale = FAIL_JSON if primary_gate else PASS_JSON
    if stale.exists():
        stale.unlink()
    return result


def _write_markdown(r):
    e = r['endpoints']
    p = e['D6-1_12m_bond_to_SPY']
    s = e['D6-2_12m_SPY_to_Treasury']
    pl = e['D6-3_observed_vs_circular_shift']
    b6 = e['D6-4_6m_bond_to_SPY']
    e6 = e['D6-5_6m_SPY_to_Treasury']
    dist = r['placebo_distribution']
    gate = 'PASS' if r['passed'] else 'FAIL'
    def f(x): return 'NA' if not np.isfinite(x) else f'{x:.6g}'
    lines = [
        '# D6 mechanism and placebo results', '',
        f'**Primary mechanism gate: {gate}.** Frozen preregistration SHA-256 verified: `{r["prereg_sha256"]}`.',
        f'Development targets: {r["development"]["target_first"]}–{r["development"]["target_last"]}, '
        f'{r["development"]["observation_count"]} monthly observations. Only the five specified ETF development inputs were opened.',
        'No portfolio stage or holdout data were run or opened.', '',
        '## Registered endpoints', '',
        '| Endpoint | Estimate / comparison | NW SE | NW t (lag 11) | Raw p | Holm adjusted p | Status |',
        '|---|---:|---:|---:|---:|---|---|',
        f'| D6-1 12-minus-1 Treasury basket → SPY, β>0 | {f(p["beta"])} | {f(p["se"])} | {f(p["nw_t_lag11"])} | {f(p["one_sided_raw_p"])} | Pending complete family | {"PASS" if r["gate"]["primary_mechanism_gate"] else "FAIL"} |',
        f'| D6-2 12-minus-1 SPY → equal-weight Treasury, β<0 | {f(s["beta"])} | {f(s["se"])} | {f(s["nw_t_lag11"])} | {f(s["one_sided_raw_p"])} | Pending complete family | Secondary; cannot rescue primary |',
        f'| D6-3 observed vs circularly shifted bond signal, one-sided | observed β={f(pl["observed_beta"])}; null 95th pct={f(pl["null_beta_p95"])}; percentile={pl["observed_percentile"]:.1%} | — | — | {pl["one_sided_randomization_p"]:.6g} | Pending complete family | {"PASS" if r["gate"]["observed_beta_exceeds_placebo_p95"] else "FAIL"} (β>95th pct required) |',
        f'| D6-4 six-minus-one Treasury basket → SPY, β>0 | {f(b6["beta"])} | {f(b6["se"])} | {f(b6["nw_t_lag11"])} | {f(b6["one_sided_raw_p"])} | Pending complete family | Sensitivity; cannot replace primary |',
        f'| D6-5 six-minus-one SPY → equal-weight Treasury, β<0 | {f(e6["beta"])} | {f(e6["se"])} | {f(e6["nw_t_lag11"])} | {f(e6["one_sided_raw_p"])} | Pending complete family | Sensitivity; cannot replace primary |',
        '| D6-6 portfolio net excess vs EW5, β>0 | — | — | — | Not run | Not calculated | Not run (outside task scope) |',
        '',
        '## Circular-shift placebo distribution', '',
        f'500 draws; seed `{SEED}`; offsets uniformly sampled with replacement from {pl["offset_min_inclusive"]} through {pl["offset_max_inclusive"]} sessions in the monthly observation index. The SPY own-trend control, SPY target series, and internal order of the circularly shifted bond signal were preserved.',
        f'Bond-to-SPY placebo-coefficient summary: min {f(dist["min"])}, 5th pct {f(dist["q05"])}, 25th pct {f(dist["q25"])}, median {f(dist["median"])}, 75th pct {f(dist["q75"])}, 95th pct {f(dist["q95"])}, max {f(dist["max"])}; mean {f(dist["mean"])}; SD {f(dist["std"])}.',
        f'The observed coefficient percentile is {pl["observed_percentile"]:.1%}; the one-sided finite-sample randomization p-value is {pl["one_sided_randomization_p"]:.6g}. Full draw coefficients are in `D6_PLACEBO_BETAS.csv`.',
        '',
        '## Fixed diagnostics', '',
        'The 12-minus-1 reversed-direction regression is reported as D6-2 above. Target-own-trend-only regressions are reported below; they are diagnostics and are not Holm endpoints.',
        '| Diagnostic | β | NW SE | NW t (lag 11) |', '|---|---:|---:|---:|',
    ]
    for label, group in [('12-minus-1', r['diagnostics']['12_minus_1_target_own_trend_only']), ('six-minus-one', r['diagnostics']['6_minus_1_target_own_trend_only'])]:
        for name, value in group.items():
            lines.append(f'| {label}: {name.replace("_", " ")} | {f(value["beta"])} | {f(value["se"])} | {f(value["nw_t_lag11"])} |')
    lines += [
        '', '## Interpretation and multiple testing', '',
        ('The registered primary coefficient is positive, reaches the Newey–West t≥2 threshold, and exceeds the 95th percentile of the fixed circular-shift placebo distribution.' if r['passed'] else 'The primary gate fails because one or more of the frozen requirements (positive coefficient, Newey–West t≥2, and coefficient above the placebo 95th percentile) were not met.'),
        'The six frozen endpoints remain in the goal-wide Holm family. Holm-adjusted p-values are pending the coordinator’s complete D4–D6 outcome family; D4 endpoints have not all been run and D6-6 was not run because this dispatch excludes the portfolio stage. Raw p-values for all mechanism endpoints are shown above; no endpoint was dropped or rescued.',
        '', '## Trial logging', '',
        'D6 endpoints 1–5 were recorded through `run_registered_trial` and the harness `append_trial` logger in `specs/r4_trials.md`. D6-6 is recorded as not run in this report and was not logged as an outcome.',
    ]
    RESULTS_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def _endpoint_log_rows(result):
    e = result['endpoints']
    p, s = e['D6-1_12m_bond_to_SPY'], e['D6-2_12m_SPY_to_Treasury']
    pl, b6, e6 = (e[k] for k in ('D6-3_observed_vs_circular_shift', 'D6-4_6m_bond_to_SPY', 'D6-5_6m_SPY_to_Treasury'))
    return [
        ('D6-2 12-1 SPY-to-Treasury', f'beta={s["beta"]:.8g}; NW_SE={s["se"]:.8g}; NW_t={s["nw_t_lag11"]:.8g}; one_sided_p={s["one_sided_raw_p"]:.8g}'),
        ('D6-3 12-1 observed vs circular shift', f'observed_beta={pl["observed_beta"]:.8g}; null_p95={pl["null_beta_p95"]:.8g}; percentile={pl["observed_percentile"]:.8g}; randomization_p={pl["one_sided_randomization_p"]:.8g}'),
        ('D6-4 six-minus-one bond-to-SPY', f'beta={b6["beta"]:.8g}; NW_SE={b6["se"]:.8g}; NW_t={b6["nw_t_lag11"]:.8g}; one_sided_p={b6["one_sided_raw_p"]:.8g}; sensitivity only'),
        ('D6-5 six-minus-one SPY-to-Treasury', f'beta={e6["beta"]:.8g}; NW_SE={e6["se"]:.8g}; NW_t={e6["nw_t_lag11"]:.8g}; one_sided_p={e6["one_sided_raw_p"]:.8g}; sensitivity only'),
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(description='Run frozen D6 development mechanism endpoints only.')
    parser.add_argument('--check-freeze', action='store_true', help='hash-check only; do not open D6 inputs')
    args = parser.parse_args(argv)
    from r4_harness.phase3 import require_frozen_prereg
    try:
        prereg = require_frozen_prereg('D6', prereg_dir=PREREG_DIR)
    except Exception as exc:
        print(f'REFUSED: D6 pre-registration is not frozen and hash-valid: {exc}', file=sys.stderr)
        return 2
    if args.check_freeze:
        print(f'FROZEN D6 pre-registration verified: {prereg}')
        return 0
    cache = {}
    def callback():
        value = _run_development()
        cache['result'] = value
        p = value['endpoints']['D6-1_12m_bond_to_SPY']
        return (f'D6-1: beta={p["beta"]:.8g}; NW_t={p["nw_t_lag11"]:.8g}; '
                f'one_sided_p={p["one_sided_raw_p"]:.8g}; gate={value["passed"]}')
    try:
        # This call verifies the freeze/hash and trial budget before callback opens the bundle.
        run_registered_trial('D6', 'D6-1 primary 12-minus-1 bond-to-SPY mechanism', callback,
                             prereg_dir=PREREG_DIR, trial_log=TRIAL_LOG)
        result = cache['result']
        for name, detail in _endpoint_log_rows(result):
            append_trial('D6', name, detail, prereg_dir=PREREG_DIR,
                         trial_log=TRIAL_LOG)
    except Exception as exc:
        print(f'FAILED: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1
    print(json.dumps({'passed': result['passed'], 'prereg_sha256': result['prereg_sha256'],
                      'primary': result['endpoints']['D6-1_12m_bond_to_SPY'],
                      'placebo': result['endpoints']['D6-3_observed_vs_circular_shift']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
