"""Small actual-trade portfolio simulator shared by frozen stage runners.

It uses target weights from a close-time score, next-open execution, a total
traded-notional cap, and costs on every buy and sell. The same function is used
for development portfolio runners and coordinator-only synthetic/holdout runs.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from r4_harness.phase3 import (
    circular_block_bootstrap_pvalue,
    deflated_sharpe_ratio,
    holm_correction,
)


def _target(score, active, top_n=5, asset_names=None):
    ok = active & np.isfinite(score)
    ix = np.flatnonzero(ok)
    if len(ix) < top_n:
        raise ValueError(f'only {len(ix)} eligible scores; need {top_n}')
    # Higher score first; exact ties break by ticker ascending, as D5 freezes.
    names = list(asset_names) if asset_names is not None else [str(i) for i in range(len(score))]
    selected = sorted(ix.tolist(), key=lambda i: (-score[i], names[i]))[:top_n]
    w = np.zeros(len(score), dtype=float)
    w[selected] = 1.0 / top_n
    return w


def _simulate(scores, op, close, roster, fill_indices, cap, cost_rate, top_n=5,
              equal_weight=False, cap_basis='absolute', benchmark_turnovers=None,
              asset_names=None):
    scores = np.asarray(scores, float)
    op = np.asarray(op, float)
    close = np.asarray(close, float)
    roster = np.asarray(roster, bool)
    if scores.ndim != 2 or scores.shape != op.shape or scores.shape != close.shape or roster.shape != scores.shape:
        raise ValueError('scores, prices and roster must share assets x dates shape')
    n, t = scores.shape
    if asset_names is not None and len(asset_names) != n:
        raise ValueError('asset_names length must equal the asset axis')
    fills = sorted(set(int(x) for x in fill_indices))
    if len(fills) < 2 or any(x <= 0 or x >= t for x in fills):
        raise ValueError('need at least two in-range next-open fill dates')
    shares = np.zeros(n, float)
    cash = 1.0
    marks = []
    turnovers, paid_costs, active_shares = [], [], []
    for k, fi in enumerate(fills):
        price = op[:, fi]
        tradable = roster[:, fi] & np.isfinite(price) & (price > 0)
        if np.any((np.abs(shares) > 1e-14) & (~np.isfinite(price) | (price <= 0))):
            raise ValueError('missing next-open price for an existing holding')
        nav_open = cash + float(np.sum(shares * np.where(np.isfinite(price), price, 0.0)))
        if nav_open <= 0:
            raise ValueError('portfolio NAV reached zero or below')
        if equal_weight:
            desired = np.zeros(n, dtype=float)
            if tradable.sum() == 0:
                raise ValueError('no available names for equal-weight benchmark')
            desired[tradable] = 1.0 / tradable.sum()
        else:
            desired = _target(scores[:, fi - 1], tradable, top_n=top_n,
                              asset_names=asset_names)
        current = np.divide(shares * np.where(np.isfinite(price), price, 0.0), nav_open)

        def execute(scale):
            weights = current + scale * (desired - current)
            nav_after = nav_open
            target_shares = shares
            notional = 0.0
            for _ in range(200):
                target_shares = np.divide(nav_after * weights, price,
                                          out=np.zeros(n), where=tradable)
                notional = float(np.sum(np.abs(target_shares - shares) *
                                        np.where(np.isfinite(price), price, 0.0)))
                updated = nav_open - cost_rate * notional
                if abs(updated - nav_after) <= 1e-13 * max(1.0, nav_open):
                    nav_after = updated
                    break
                nav_after = updated
            target_shares = np.divide(nav_after * weights, price,
                                      out=np.zeros(n), where=tradable)
            notional = float(np.sum(np.abs(target_shares - shares) *
                                    np.where(np.isfinite(price), price, 0.0)))
            cost = cost_rate * notional
            return weights, target_shares, notional, nav_open - cost, cost

        if math.isinf(cap):
            scale = 1.0
        else:
            benchmark_turnover = (float(benchmark_turnovers[k])
                                  if benchmark_turnovers is not None and k < len(benchmark_turnovers) else 0.0)
            def capped_metric(candidate):
                absolute = candidate[2] / nav_open
                if cap_basis == 'benchmark_relative':
                    return max(0.0, absolute - benchmark_turnover)
                if cap_basis != 'absolute':
                    raise ValueError("cap_basis must be 'absolute' or 'benchmark_relative'")
                return absolute
            full = execute(1.0)
            if capped_metric(full) <= cap + 1e-12:
                scale = 1.0
            else:
                lo, hi = 0.0, 1.0
                for _ in range(60):
                    mid = (lo + hi) / 2
                    if capped_metric(execute(mid)) <= cap:
                        lo = mid
                    else:
                        hi = mid
                scale = lo
        weights, new_shares, notional, nav_after, cost = execute(scale)
        benchmark_turnover = (float(benchmark_turnovers[k])
                              if benchmark_turnovers is not None and k < len(benchmark_turnovers) else 0.0)
        cap_metric = (max(0.0, notional / nav_open - benchmark_turnover)
                      if cap_basis == 'benchmark_relative' else notional / nav_open)
        if not math.isinf(cap) and cap_metric > cap + 1e-8:
            raise ArithmeticError('turnover cap failed')
        if abs(nav_open - nav_after - cost) > 1e-9 * max(1.0, nav_open):
            raise ArithmeticError('actual-trade costs do not reconcile')
        turnovers.append(notional / nav_open)
        paid_costs.append(cost)
        bench = np.zeros(n, float)
        if tradable.sum():
            bench[tradable] = 1.0 / tradable.sum()
        active_shares.append(.5 * float(np.abs(weights - bench).sum()))
        shares = new_shares
        cash = nav_after - float(np.sum(shares * np.where(np.isfinite(price), price, 0.0)))

        stop = fills[k + 1] if k + 1 < len(fills) else t
        for j in range(fi, stop):
            cp = close[:, j]
            if np.any((np.abs(shares) > 1e-14) & (~np.isfinite(cp) | (cp <= 0))):
                raise ValueError('missing close price for a held asset')
            nav = cash + float(np.sum(shares * np.where(np.isfinite(cp), cp, 0.0)))
            marks.append((j, nav))
    if marks:
        j, before = marks[-1]
        close_last = close[:, j]
        liquidation = float(np.sum(np.abs(shares) * np.where(np.isfinite(close_last), close_last, 0.0)))
        final_cost = cost_rate * liquidation
        marks[-1] = (j, before - final_cost)
        paid_costs.append(final_cost)
    navs = np.asarray([v for _, v in marks], float)
    returns = np.diff(np.r_[1.0, navs]) / np.maximum(np.abs(np.r_[1.0, navs[:-1]]), 1e-12)
    sd = float(np.std(returns, ddof=0)) if len(returns) else 0.0
    return {
        'marks': marks,
        'returns': returns,
        'cumulative_return': float(navs[-1] - 1.0) if len(navs) else 0.0,
        'sharpe': float(np.mean(returns) / sd * math.sqrt(252)) if sd > 0 else 0.0,
        'total_cost': float(np.sum(paid_costs)),
        'turnover': float(np.mean(turnovers)) if turnovers else 0.0,
        'turnovers': turnovers,
        'active_share': float(np.mean(active_shares)) if active_shares else 0.0,
    }


def portfolio_report(scores, open_prices, close_prices, roster, formation_indices,
                     *, trial_count, bootstrap_draws=5000, seed=20261110,
                     turnover_cap=.50, cost_rate=.0005, holm_family=None,
                     holdout=False, turnover_cap_basis='absolute',
                     asset_names=None, endpoint_name='portfolio_net_excess'):
    """Run capped long-only top-five versus EW with fixed inference settings."""
    scores = np.asarray(scores, float)
    open_prices = np.asarray(open_prices, float)
    close_prices = np.asarray(close_prices, float)
    roster = np.asarray(roster, bool)
    fills = [int(i) + 1 for i in formation_indices if int(i) + 1 < scores.shape[1]]
    ew_scores = np.zeros_like(scores)
    benchmark_gross = _simulate(ew_scores, open_prices, close_prices, roster, fills,
                                math.inf, 0.0, equal_weight=True, asset_names=asset_names)
    strategy_gross = _simulate(scores, open_prices, close_prices, roster, fills,
                               turnover_cap, 0.0, cap_basis=turnover_cap_basis,
                               benchmark_turnovers=benchmark_gross['turnovers'],
                               asset_names=asset_names)
    strategy_net = _simulate(scores, open_prices, close_prices, roster, fills,
                             turnover_cap, cost_rate, cap_basis=turnover_cap_basis,
                             benchmark_turnovers=benchmark_gross['turnovers'],
                             asset_names=asset_names)
    benchmark_net = _simulate(ew_scores, open_prices, close_prices, roster, fills,
                              math.inf, cost_rate, equal_weight=True,
                              asset_names=asset_names)
    m = min(len(strategy_net['returns']), len(benchmark_net['returns']))
    sr, br = strategy_net['returns'][-m:], benchmark_net['returns'][-m:]
    p, _ = circular_block_bootstrap_pvalue(sr, br, block_length=10,
                                            n_draws=bootstrap_draws, seed=seed)
    family = dict(holm_family or {})
    family[endpoint_name] = p
    adjusted = holm_correction(family)[endpoint_name]['holm_p']
    gross_edge = strategy_gross['cumulative_return'] - benchmark_gross['cumulative_return']
    incremental_cost = max(0.0, strategy_net['total_cost'] - benchmark_net['total_cost'])
    rel_turns = [max(0.0, float(a) - float(b)) for a, b in zip(
        strategy_net['turnovers'], benchmark_net['turnovers'])]
    benchmark_relative_turnover = float(np.mean(rel_turns)) if rel_turns else 0.0
    turnover_gate = (benchmark_relative_turnover <= turnover_cap + 1e-8
                     if turnover_cap_basis == 'benchmark_relative'
                     else strategy_net['turnover'] <= turnover_cap + 1e-8)
    return {
        'strategy_gross': strategy_gross,
        'strategy_net': strategy_net,
        'benchmark_gross': benchmark_gross,
        'benchmark_net': benchmark_net,
        'net_excess_return': strategy_net['cumulative_return'] - benchmark_net['cumulative_return'],
        'gross_active_edge': gross_edge,
        'realized_strategy_cost': strategy_net['total_cost'],
        'realized_benchmark_cost': benchmark_net['total_cost'],
        'incremental_realized_cost': incremental_cost,
        'turnover_cap_basis': turnover_cap_basis,
        'benchmark_turnover': benchmark_net['turnover'],
        'benchmark_relative_turnover': benchmark_relative_turnover,
        'bootstrap_p_raw': p,
        'bootstrap_p_holm': adjusted,
        'holm_endpoint': endpoint_name,
        'deflated_sharpe': deflated_sharpe_ratio(strategy_net['returns'], trial_count),
        'trial_count': int(trial_count),
        'cost_to_gross_edge_ratio': incremental_cost / gross_edge if gross_edge > 0 else None,
        'holdout_pass': (bool(strategy_net['sharpe'] > benchmark_net['sharpe'] and
                              strategy_net['cumulative_return'] > benchmark_net['cumulative_return'] and
                              p < .10 and strategy_net['active_share'] >= .50 and
                              turnover_gate and gross_edge >= 4 * incremental_cost)
                         if holdout else None),
        'portfolio_pass': bool(strategy_net['sharpe'] > benchmark_net['sharpe'] and
                               strategy_net['cumulative_return'] > benchmark_net['cumulative_return'] and
                               adjusted < .05 and turnover_gate and
                               strategy_net['active_share'] >= .50 and
                               (gross_edge >= 4 * incremental_cost)),
    }
