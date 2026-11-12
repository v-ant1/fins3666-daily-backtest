"""Frozen D4 long-only portfolio stage (never run before its mechanism gate)."""
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
PREREG = ROOT / 'specs' / 'r4_prereg' / 'D4.md'
PASS_FILE = HERE / 'MECHANISM_PASS.json'
PORTFOLIO_ENDPOINT = 'D4_v1_portfolio_net_excess'
INPUTS = HERE / 'D4_INPUTS.npz'
TRIAL_LOG = ROOT / 'specs' / 'r4_trials.md'


def _formations(scores, roster):
    valid = np.sum(np.isfinite(scores) & roster, axis=0) >= 5
    ids = np.flatnonzero(valid)
    if len(ids) == 0:
        raise ValueError('no formation date has five valid D4 scores')
    return np.arange(ids[0], scores.shape[1] - 1, 5, dtype=int)


def run_d4_portfolio(input_path=INPUTS, holm_path=None):
    proof = require_mechanism_pass('D4', PREREG, PASS_FILE)
    family = load_holm_family(holm_path, PORTFOLIO_ENDPOINT)
    trial_count = trial_budget(TRIAL_LOG)
    with np.load(input_path, allow_pickle=False) as z:
        if z['manager_roster_source'].astype(str)[0].startswith('missing'):
            raise PermissionError('D4 provisional fixed-roster input cannot enter a portfolio run')
        scores = z['ncp'].astype(float)
        roster = z['roster_mask'].astype(bool)
        op = z['adjusted_open'].astype(float)
        close = z['adjusted_close'].astype(float)
        dates = z['dates'].astype(str).tolist()
        assets = z['assets'].astype(str).tolist()
    formations = _formations(scores, roster)
    result = portfolio_report(scores, op, close, roster, formations,
                              trial_count=trial_count, bootstrap_draws=5000,
                              seed=20261110, turnover_cap=.50,
                              cost_rate=.0005, holm_family=family,
                              turnover_cap_basis='benchmark_relative',
                              asset_names=assets, endpoint_name=PORTFOLIO_ENDPOINT)
    result.update({'approach': 'D4', 'formation_dates': [dates[i] for i in formations],
                   'mechanism_mean_ic': proof.get('mean_ic'),
                   'mechanism_nw_t_lag4': proof.get('nw_t_lag4')})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, default=INPUTS)
    parser.add_argument('--holm-family', type=Path, required=True,
                        help='frozen round-wide raw p-values excluding the portfolio endpoint')
    parser.add_argument('--output', type=Path, default=HERE / 'D4_PORTFOLIO_RESULTS.json')
    args = parser.parse_args(argv)
    try:
        # Both gates execute before the data bundle is opened.
        require_mechanism_pass('D4', PREREG, PASS_FILE)
        load_holm_family(args.holm_family, PORTFOLIO_ENDPOINT)
        result = run_registered_trial(
            'D4', 'variant 1 capped top-five portfolio',
            lambda: run_d4_portfolio(args.inputs, args.holm_family),
        )
        serializer = lambda x: x.tolist() if isinstance(x, np.ndarray) else float(x)
        args.output.write_text(json.dumps(result, indent=2, default=serializer), encoding='utf-8')
        print(json.dumps(result, indent=2, default=serializer))
        return 0
    except Exception as exc:
        print(f'REFUSED/FAILED: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
