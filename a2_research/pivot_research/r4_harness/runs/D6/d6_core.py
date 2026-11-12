"""Pure D6 computations; no file access or real-data execution on import."""
from __future__ import annotations

import math
import numpy as np
from scipy.stats import rankdata, t as student_t

ASSETS = ('SPY', 'TLT', 'IEF', 'SHY', 'TIP')
BONDS = ('TLT', 'IEF', 'SHY', 'TIP')


def newey_west_ols(y, x, lag=11):
    """OLS coefficients, Bartlett HAC SE/t and two-sided p-values."""
    y = np.asarray(y, float).reshape(-1)
    x = np.asarray(x, float)
    if x.ndim == 1:
        x = x[:, None]
    ok = np.isfinite(y) & np.all(np.isfinite(x), axis=1)
    y, x = y[ok], x[ok]
    X = np.column_stack([np.ones(len(y)), x])
    if len(y) <= X.shape[1] + 1:
        raise ValueError('not enough complete rows for regression')
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    resid = y - X @ beta
    inv = np.linalg.inv(X.T @ X)
    meat = np.zeros((X.shape[1], X.shape[1]))
    for i in range(len(y)):
        score = X[i] * resid[i]
        meat += np.outer(score, score)
    lag = min(max(int(lag), 0), len(y) - 1)
    for k in range(1, lag + 1):
        weight = 1.0 - k / (lag + 1.0)
        gamma = np.zeros_like(meat)
        for i in range(k, len(y)):
            gamma += np.outer(X[i] * resid[i], X[i-k] * resid[i-k])
        meat += weight * (gamma + gamma.T)
    cov = inv @ meat @ inv
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    stat = np.divide(beta, se, out=np.full_like(beta, np.nan), where=se > 0)
    p_two = 2 * student_t.sf(np.abs(stat), df=max(len(y) - X.shape[1], 1))
    return {'n': len(y), 'beta': beta, 'se': se, 't': stat, 'p_two': p_two,
            'p_positive': student_t.sf(stat, df=max(len(y) - X.shape[1], 1)),
            'p_negative': student_t.cdf(stat, df=max(len(y) - X.shape[1], 1))}


def monthly_inputs(dates, adjusted_close, adjusted_open):
    """Create registered trend and open-to-open monthly panels from daily bars."""
    dates = [str(x)[:7] for x in dates]
    close = np.asarray(adjusted_close, float)
    op = np.asarray(adjusted_open, float)
    if close.shape != op.shape or close.shape[0] != 5 or close.shape[1] != len(dates):
        raise ValueError('expected five asset-by-date adjusted price matrices')
    months = sorted(set(dates))
    close_eom = np.full((5, len(months)), np.nan)
    open_first = np.full((5, len(months)), np.nan)
    for j, month in enumerate(months):
        ids = [i for i, value in enumerate(dates) if value == month]
        close_eom[:, j] = close[:, ids[-1]]
        open_first[:, j] = op[:, ids[0]]
    return months, close_eom, open_first


def trend_panel(close_eom, lookback):
    """m-1 over m-lookback return, indexed at signal month m."""
    c = np.asarray(close_eom, float)
    out = np.full_like(c, np.nan)
    if lookback < 2:
        raise ValueError('lookback must be at least two months')
    out[:, lookback:] = c[:, lookback-1:-1] / c[:, :-lookback] - 1.0
    return out


def cross_asset_series(close_eom, open_first, lookback):
    """Return signal-month labels and fixed predictor/target series."""
    trend = trend_panel(close_eom, lookback)
    months = close_eom.shape[1]
    bond_values = trend[1:5]
    bond_count = np.isfinite(bond_values).sum(axis=0)
    bond = np.divide(np.nansum(bond_values, axis=0), bond_count,
                     out=np.full(trend.shape[1], np.nan), where=bond_count > 0)
    spy_trend = trend[0]
    spy_target = np.full(months, np.nan)
    treasury_target = np.full(months, np.nan)
    # target month m+1 first open through target month m+2 first open
    for m in range(months - 2):
        spy_target[m] = open_first[0, m + 2] / open_first[0, m + 1] - 1
        tr = open_first[1:5, m + 2] / open_first[1:5, m + 1] - 1
        treasury_target[m] = np.mean(tr) if np.all(np.isfinite(tr)) else np.nan
    return bond, spy_trend, spy_target, treasury_target


def circular_placebo(bond, spy_trend, target, draws=500, seed=20261110):
    """Registered circular shifts; returns primary beta draw distribution."""
    b = np.asarray(bond, float); e = np.asarray(spy_trend, float); y = np.asarray(target, float)
    valid = np.isfinite(b) & np.isfinite(e) & np.isfinite(y)
    b, e, y = b[valid], e[valid], y[valid]
    if len(y) < 25:
        raise ValueError('at least 25 valid observations required for registered shifts')
    rng = np.random.default_rng(seed)
    offsets = rng.integers(12, len(y) - 11, size=draws)
    vals = np.empty(draws)
    for i, offset in enumerate(offsets):
        vals[i] = newey_west_ols(y, np.column_stack([np.roll(b, int(offset)), e]), lag=11)['beta'][1]
    return vals


def mechanism_results(months, close_eom, open_first, valid_mask=None):
    """Compute all preregistered D6 mechanism regressions and placebo."""
    outputs = {}
    for lookback, tag in ((12, '12m1'), (6, '6m1')):
        bond, equity, spy_y, treasury_y = cross_asset_series(close_eom, open_first, lookback)
        if valid_mask is not None:
            mask = np.asarray(valid_mask, bool)
            bond = np.where(mask, bond, np.nan)
            equity = np.where(mask, equity, np.nan)
            spy_y = np.where(mask, spy_y, np.nan)
            treasury_y = np.where(mask, treasury_y, np.nan)
        be = newey_west_ols(spy_y, np.column_stack([bond, equity]), 11)
        eb = newey_west_ols(treasury_y, np.column_stack([equity, bond]), 11)
        be_placebo = circular_placebo(bond, equity, spy_y)
        percentile = float(np.mean(be_placebo <= be['beta'][1]))
        rp = float((1 + np.sum(be_placebo >= be['beta'][1])) / (len(be_placebo) + 1))
        own_spy = newey_west_ols(spy_y, equity, 11)
        own_treasury = newey_west_ols(treasury_y, bond, 11)
        outputs[tag] = {
            'bond_to_spy': _reg_json(be, primary=True),
            'spy_to_treasury': _reg_json(eb, primary=False, direction='negative'),
            'placebo': {'draws': be_placebo.tolist(), 'percentile': percentile,
                        'p_one_sided': rp, 'p95': float(np.quantile(be_placebo, .95, method='linear'))},
            'own_trend_spy': _reg_json(own_spy, primary=False),
            'own_trend_treasury': _reg_json(own_treasury, primary=False),
            'n': int(be['n']),
        }
    p = outputs['12m1']
    primary = p['bond_to_spy']
    passed = (primary['beta'] > 0 and primary['nw_t'] >= 2.0
              and primary['p_one_sided'] < .05
              and p['placebo']['p_one_sided'] < .05
              and primary['beta'] > p['placebo']['p95'])
    return {'approach': 'D6', 'pass': bool(passed), 'lookbacks': outputs,
            'gate': {'primary_positive': primary['beta'] > 0,
                     'primary_nw_t_ge_2': primary['nw_t'] >= 2.0,
                     'primary_one_sided_p_lt_05': primary['p_one_sided'] < .05,
                     'placebo_p_lt_05': p['placebo']['p_one_sided'] < .05,
                     'observed_beta_above_placebo_p95': primary['beta'] > p['placebo']['p95']}}


def _reg_json(result, primary, direction='positive'):
    beta = float(result['beta'][1]) if len(result['beta']) > 1 else float(result['beta'][0])
    stat = float(result['t'][1]) if len(result['t']) > 1 else float(result['t'][0])
    p_pos = float(result['p_positive'][1]) if len(result['beta']) > 1 else float(result['p_positive'][0])
    p_neg = float(result['p_negative'][1]) if len(result['beta']) > 1 else float(result['p_negative'][0])
    return {'beta': beta, 'se': float(result['se'][1] if len(result['se']) > 1 else result['se'][0]),
            'nw_t': stat, 'p_one_sided': p_pos if direction == 'positive' else p_neg,
            'p_positive': p_pos, 'p_negative': p_neg}


def portfolio_weights(scores):
    """100% in the highest finite score, with ascending ticker tie-break assumed by input order."""
    s = np.asarray(scores, float)
    if s.ndim != 2 or s.shape[0] != 5:
        raise ValueError('scores must be 5 x months')
    w = np.full_like(s, np.nan)
    for j in range(s.shape[1]):
        valid = np.flatnonzero(np.isfinite(s[:, j]))
        if len(valid):
            # ASSETS order is already ascending within tied score only after explicit key below.
            best = sorted(valid, key=lambda i: (-s[i, j], ASSETS[i]))[0]
            w[:, j] = 0.; w[best, j] = 1.
    return w


def portfolio_returns(scores, monthly_open, monthly_close, trial_count=30,
                       draws=5000, block=10, seed=20261110):
    """Synthetic-testable monthly top-score portfolio with actual turnover costs."""
    del monthly_close  # scores already carry preregistered volatility normalization
    w = portfolio_weights(scores)
    op = np.asarray(monthly_open, float)
    n = w.shape[1]
    if op.shape != w.shape or n < 2:
        raise ValueError('monthly open matrix must match five-asset score dimensions')
    ew = np.repeat(0.2, 5)
    active_w = ew.copy()
    active, benchmark, turnover, costs, shares = [], [], [], [], []
    for j in range(n - 1):
        if not np.all(np.isfinite(w[:, j])) or not np.all(np.isfinite(op[:, j:j+2])):
            continue
        target = w[:, j]
        traded = float(np.abs(target - active_w).sum())
        # Actual trade notional is sum of buys and sells; 5 bp applies once to that notional.
        cost = traded * .0005
        r = op[:, j+1] / op[:, j] - 1
        active.append(float(target @ r - cost))
        benchmark.append(float(ew @ r))
        turnover.append(traded)
        costs.append(cost)
        shares.append(float(.5 * np.abs(target - ew).sum()))
        active_w = target.copy()
    active = np.asarray(active); benchmark = np.asarray(benchmark)
    excess = active - benchmark
    if len(excess) < block:
        raise ValueError('not enough portfolio observations for registered 10-month block bootstrap')
    rng = np.random.default_rng(seed)
    nobs = len(excess)
    blocks = int(math.ceil(nobs / block))
    samples = np.empty(draws)
    for d in range(draws):
        starts = rng.integers(0, nobs, size=blocks)
        sample = np.concatenate([excess[(s + np.arange(block)) % nobs] for s in starts])[:nobs]
        samples[d] = sample.mean()
    p_boot = float((1 + np.sum(samples <= 0)) / (draws + 1))
    std = float(np.std(active, ddof=1))
    std_b = float(np.std(benchmark, ddof=1))
    gross = active + np.asarray(costs)
    edge = float(np.mean(gross - benchmark))
    ratio = float(np.mean(costs) / edge) if edge != 0 else float('inf')
    return {'monthly_net_returns': active.tolist(), 'monthly_ew5_returns': benchmark.tolist(),
            'monthly_excess_net': excess.tolist(), 'portfolio_weights': w.tolist(),
            'net_excess_mean': float(excess.mean()),
            'net_sharpe': float(np.mean(active) / std * math.sqrt(12)) if std else float('nan'),
            'ew5_sharpe': float(np.mean(benchmark) / std_b * math.sqrt(12)) if std_b else float('nan'),
            'mean_turnover': float(np.mean(turnover)), 'total_cost': float(np.sum(costs)),
            'mean_active_share': float(np.mean(shares)), 'gross_active_edge': edge,
            'cost_gross_edge_ratio': ratio, 'bootstrap_p_one_sided': p_boot,
            'bootstrap_excess_samples': samples.tolist(),
            'dsr': float(__import__('r4_harness.phase3', fromlist=['deflated_sharpe_ratio']).deflated_sharpe_ratio(active, trial_count)),
            'trial_count': int(trial_count)}


def build_portfolio_scores(months, close_eom):
    """Registered sign-adjusted monthly scores and trailing population vol scales."""
    c = np.asarray(close_eom, float)
    trend = trend_panel(c, 12)
    bond, equity, _, _ = cross_asset_series(c, np.full_like(c, np.nan), 12)
    monthly_r = c[:, 1:] / c[:, :-1] - 1
    scores = np.full((5, c.shape[1]), np.nan)
    for m in range(13, c.shape[1]):
        # signal at m only uses the prior 12 monthly returns, k=m-12..m-1
        bond_basket_returns = monthly_r[1:5, m-13:m-1].mean(axis=0)
        tr_vol = float(np.std(bond_basket_returns, ddof=0))
        spy_vol = float(np.std(monthly_r[0, m-13:m-1], ddof=0))
        if tr_vol > 0 and np.isfinite(bond[m]): scores[0, m] = bond[m] / tr_vol
        if spy_vol > 0 and np.isfinite(equity[m]): scores[1:, m] = -equity[m] / spy_vol
    return scores
