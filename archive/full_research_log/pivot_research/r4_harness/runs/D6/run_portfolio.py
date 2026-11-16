"""Coordinator-only D6 monthly portfolio runner; never auto-runs real inputs."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from r4_harness.holdout.frozen_utils import load_holm_family, trial_budget
from r4_harness.phase3 import (circular_block_bootstrap_pvalue, deflated_sharpe_ratio,
                               holm_correction, prereg_digest)
from r4_harness.runs.D6.d6_core import (ASSETS, build_portfolio_scores,
    monthly_inputs, portfolio_weights)
from r4_harness.runs.D6.d6_governance import (PREREG,
    require_d6_frozen, require_d6_mechanism_pass)

HERE = Path(__file__).resolve().parent
INPUTS = HERE / 'D6_INPUTS.npz'
TRIAL_LOG = ROOT / 'specs' / 'r4_trials.md'
ENDPOINT = 'D6-6'


def _simulate(scores, monthly_open, target_columns):
    """Monthly target allocation with drift-aware traded-notional costs."""
    weights = portfolio_weights(scores)
    active_nav = ew_nav = 1.0
    active_hold = np.repeat(.2, 5)
    ew_hold = np.repeat(.2, 5)
    previous_returns = None
    strategy_net = []; benchmark_net = []; strategy_gross = []; benchmark_gross = []
    costs = []; turnover = []; active_share = []
    for m in target_columns:
        if m + 2 >= monthly_open.shape[1] or not np.all(np.isfinite(weights[:, m])):
            continue
        target = weights[:, m]
        returns = monthly_open[:, m+2] / monthly_open[:, m+1] - 1.0
        if not np.all(np.isfinite(returns)):
            continue
        gross = float(target @ returns)
        ew_gross = float(.2 * returns.sum())
        drift = active_hold.copy() if previous_returns is None else active_hold * (1 + previous_returns)
        drift_ew = ew_hold.copy() if previous_returns is None else ew_hold * (1 + previous_returns)
        drift = drift / drift.sum()
        drift_ew = drift_ew / drift_ew.sum()
        traded = float(np.abs(target - drift).sum())
        ew_traded = float(np.abs(np.repeat(.2, 5) - drift_ew).sum())
        cost = traded * .0005
        ew_cost = ew_traded * .0005
        net = gross - cost
        ew_net = ew_gross - ew_cost
        strategy_gross.append(gross); benchmark_gross.append(ew_gross)
        strategy_net.append(net); benchmark_net.append(ew_net)
        costs.append(cost); turnover.append(traded)
        active_share.append(.5 * float(np.abs(target - .2).sum()))
        active_hold = target.copy(); ew_hold = np.repeat(.2, 5)
        previous_returns = returns.copy()
        active_nav *= (1 + net); ew_nav *= (1 + ew_net)
    return {'strategy_net': np.asarray(strategy_net), 'benchmark_net': np.asarray(benchmark_net),
            'strategy_gross': np.asarray(strategy_gross), 'benchmark_gross': np.asarray(benchmark_gross),
            'costs': np.asarray(costs), 'turnover': np.asarray(turnover),
            'active_share': np.asarray(active_share), 'net_nav': active_nav, 'ew_net_nav': ew_nav}


def run(inputs=INPUTS, holm_path=None, mechanism_path=None):
    proof = require_d6_mechanism_pass(PREREG, mechanism_path)
    if holm_path is None:
        raise ValueError('a frozen round-wide --holm-family JSON is required')
    family = load_holm_family(holm_path, ENDPOINT)
    trial_count = trial_budget(TRIAL_LOG)
    with np.load(inputs, allow_pickle=False) as z:
        months, close_eom, open_first = monthly_inputs(z['dates'].astype(str),
                                                        z['adjusted_close'],
                                                        z['adjusted_open'])
    scores = build_portfolio_scores(months, close_eom)
    targets = [i for i in range(len(months)-2)
               if i + 1 < len(months) and '2021-08' <= months[i+1] <= '2026-09']
    sim = _simulate(scores, open_first, targets)
    s, b = sim['strategy_net'], sim['benchmark_net']
    if len(s) != 62:
        raise ValueError(f'expected 62 registered target months; got {len(s)}')
    bootstrap_p, bootstrap_distribution = circular_block_bootstrap_pvalue(
        s, b, block_length=10, n_draws=5000, seed=20261110)
    raw_family = dict(family)
    raw_family[ENDPOINT] = bootstrap_p
    adjusted = holm_correction(raw_family)
    gross_edge = float(np.mean(sim['strategy_gross'] - sim['benchmark_gross']))
    actual_cost = float(np.sum(sim['costs']))
    turnover_mean = float(np.mean(sim['turnover']))
    net_sr = float(np.mean(s) / np.std(s, ddof=1) * np.sqrt(12)) if np.std(s, ddof=1) else 0.
    ew_sr = float(np.mean(b) / np.std(b, ddof=1) * np.sqrt(12)) if np.std(b, ddof=1) else 0.
    ratio = actual_cost / max(gross_edge * len(s), 1e-15)
    portfolio_pass = (float(np.mean(s-b)) > 0 and net_sr > ew_sr
                      and gross_edge * len(s) >= 4 * actual_cost
                      and (turnover_mean <= .50 or gross_edge * len(s) >= 4 * actual_cost)
                      and adjusted[ENDPOINT]['holm_p'] < .05)
    return {'approach': 'D6', 'endpoint': ENDPOINT, 'passed': bool(portfolio_pass),
            'pre_registration_sha256': prereg_digest(PREREG.read_text(encoding='utf-8')),
            'formation_months': [months[i] for i in targets],
            'target_months': [months[i+1] for i in targets],
            'monthly_net_returns': s.tolist(), 'monthly_ew5_net_returns': b.tolist(),
            'net_excess_mean': float(np.mean(s-b)), 'net_sharpe': net_sr, 'ew5_net_sharpe': ew_sr,
            'gross_active_edge_total': gross_edge * len(s), 'total_actual_cost': actual_cost,
            'cost_to_gross_edge_ratio': ratio, 'mean_total_notional_turnover': turnover_mean,
            'mean_active_share': float(np.mean(sim['active_share'])),
            'bootstrap_p_raw': bootstrap_p, 'bootstrap_p_holm': adjusted[ENDPOINT]['holm_p'],
            'holm_family': adjusted, 'bootstrap_distribution': bootstrap_distribution.tolist(),
            'deflated_sharpe_trial_count': trial_count,
            'deflated_sharpe': float(deflated_sharpe_ratio(s, trial_count)),
            'mechanism_primary_beta': float(proof.get('primary_beta', proof.get('primary', {}).get('beta')))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute', action='store_true', help='explicit coordinator authorization to calculate D6 portfolio outcomes')
    ap.add_argument('--inputs', type=Path, default=INPUTS)
    ap.add_argument('--mechanism-pass', type=Path, default=HERE / 'MECHANISM_PASS.json')
    ap.add_argument('--holm-family', type=Path, required=True)
    ap.add_argument('--output', type=Path, default=HERE / 'PORTFOLIO_RESULTS.json')
    args = ap.parse_args(argv)
    try:
        require_d6_frozen(PREREG)
        if not args.execute:
            raise PermissionError('D6 execution refused: pass --execute only after a passing mechanism gate')
        result = run(args.inputs, args.holm_family, args.mechanism_pass)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
        print(f"D6 portfolio completed: passed={result['passed']}, net excess={result['net_excess_mean']:.6g}")
        return 0 if result['passed'] else 1
    except (ValueError, FileNotFoundError, PermissionError, KeyError) as exc:
        print(f'D6 portfolio refused: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__': raise SystemExit(main())
