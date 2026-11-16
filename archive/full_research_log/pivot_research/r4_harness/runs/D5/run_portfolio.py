"""Frozen D5 20-session SIC leader/follower portfolio stage."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from r4_harness.holdout.frozen_utils import (
    load_holm_family, require_mechanism_pass, trial_budget,
)
from r4_harness.holdout.portfolio_core import portfolio_report
from r4_harness.phase3 import run_registered_trial

HERE = Path(__file__).resolve().parent
PREREG = ROOT / 'specs' / 'r4_prereg' / 'D5.md'
PASS_FILE = HERE / 'MECHANISM_PASS.json'
PORTFOLIO_ENDPOINT = 'D5_v1_portfolio_net_excess'
INPUTS = HERE / 'D5_INPUTS.npz'
TRIAL_LOG = ROOT / 'specs' / 'r4_trials.md'


def _clv5(high, low, close):
    span = high - low
    daily = np.full_like(close, np.nan, dtype=float)
    ok = np.isfinite(high) & np.isfinite(low) & np.isfinite(close) & (span > 0)
    daily[ok] = (2 * close[ok] - high[ok] - low[ok]) / span[ok]
    flat = np.isfinite(high) & np.isfinite(low) & np.isfinite(close) & (span == 0)
    daily[flat] = 0.0
    out = np.full_like(daily, np.nan)
    for t in range(4, daily.shape[1]):
        w = daily[:, t - 4:t + 1]
        good = np.isfinite(w).all(axis=1)
        out[good, t] = w[good].mean(axis=1)
    return out


def _follower_score(clv5, graph):
    # Graph edges point leader -> follower; each follower averages incoming
    # leader pressure. A zero-incoming node has no score.
    n, t = clv5.shape
    score = np.full((n, t), np.nan)
    for j in range(t):
        incoming = np.nan_to_num(graph[j], nan=0.0).T
        incoming[:, ~np.isfinite(clv5[:, j])] = 0.0
        degree = incoming.sum(axis=1)
        x = np.where(np.isfinite(clv5[:, j]), clv5[:, j], 0.0)
        have = degree > 0
        score[have, j] = (incoming @ x)[have] / degree[have]
    return score


def run_d5_portfolio(input_path=INPUTS, holm_path=None):
    proof = require_mechanism_pass('D5', PREREG, PASS_FILE)
    family = load_holm_family(holm_path, PORTFOLIO_ENDPOINT)
    trial_count = trial_budget(TRIAL_LOG)
    with np.load(input_path, allow_pickle=False) as z:
        graph = z['graph20'].astype(float)
        roster = z['roster'].astype(bool)
        high, low, close = (z[k].astype(float) for k in ('raw_high', 'raw_low', 'raw_close'))
        op, adj_close = (z[k].astype(float) for k in ('adj_open', 'adj_close'))
        assets = z['assets'].astype(str).tolist()
        dates = z['dates'].astype(str).tolist()
        registered_formations = z['formation_indices'].astype(int)
    clv5 = _clv5(high, low, close)
    scores = _follower_score(clv5, graph)
    formations = [int(i) for i in registered_formations
                  if np.sum(np.isfinite(scores[:, i]) & roster[:, i]) >= 5]
    if len(formations) < 2:
        raise ValueError('D5 has fewer than two eligible pre-registered portfolio formation dates')
    result = portfolio_report(scores, op, adj_close, roster, formations,
                              trial_count=trial_count, bootstrap_draws=5000,
                              seed=20261110, turnover_cap=.50,
                              cost_rate=.0005, holm_family=family,
                              turnover_cap_basis='absolute',
                              asset_names=assets, endpoint_name=PORTFOLIO_ENDPOINT)
    result.update({'approach': 'D5', 'formation_dates': [dates[i] for i in formations],
                   'mechanism_mean_ic': proof.get('mean_ic'),
                   'mechanism_nw_t_lag4': proof.get('nw_t_lag4')})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, default=INPUTS)
    parser.add_argument('--holm-family', type=Path, required=True,
                        help='frozen round-wide raw p-values excluding the portfolio endpoint')
    parser.add_argument('--output', type=Path, default=HERE / 'D5_PORTFOLIO_RESULTS.json')
    args = parser.parse_args(argv)
    try:
        require_mechanism_pass('D5', PREREG, PASS_FILE)
        load_holm_family(args.holm_family, PORTFOLIO_ENDPOINT)
        result = run_registered_trial(
            'D5', 'variant 1 capped top-five follower portfolio',
            lambda: run_d5_portfolio(args.inputs, args.holm_family),
        )
        args.output.write_text(json.dumps(result, indent=2, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else float(x)), encoding='utf-8')
        print(json.dumps(result, indent=2, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else float(x)))
        return 0
    except Exception as exc:
        print(f'REFUSED/FAILED: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
