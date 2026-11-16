"""Synthetic-only end-to-end checks for the R7 S&P adapter and governance."""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from r4_harness import phase3
from r4_harness.r7_sp500_adapter import (
    R6_ENDPOINTS, R7_ENDPOINTS, _apply_returns, _cap_trade, _target_weights, build_holm_family,
    cumulative_trial_count, run_portfolio, validate_holm_family,
)
from r4_harness.r7_prerun_check import PreRunError, _safe_path, synthetic_helper_check


def _synthetic_panel():
    n, t = 10, 18
    open_px = np.full((n, t), 100.0)
    close_px = np.full((n, t), 100.0)
    # Small deterministic movement, including a resumed close for asset 0.
    for d in range(t):
        open_px[:, d] *= 1.0 + .0002 * d
        close_px[:, d] = open_px[:, d] * (1.0 + .001 * ((np.arange(n) % 3) - 1))
    roster = np.ones((n, t), dtype=float)
    roster[9, 5] = 0.0
    roster[8, 8:] = 0.0
    scores = np.tile(np.arange(n, dtype=float)[:, None], (1, t))
    scores[0, :] = np.nan
    open_px[9, 5] = np.nan
    # A gap is carried and then caught up against the prior valid close.
    close_px[0, 6] = np.nan
    close_px[0, 7] = close_px[0, 5] * 1.04
    return scores, open_px, close_px, roster


def test_shape_weights_are_long_only_and_rank_weighted():
    names = [f"A{i:02}" for i in range(10)]
    score = np.arange(10, dtype=float)
    eligible = np.ones(10, dtype=bool)
    decile = _target_weights(score, eligible, "top_decile", names)
    quintile = _target_weights(score, eligible, "top_quintile", names)
    ranked = _target_weights(score, eligible, "rank_weighted_top_half", names)
    assert decile.sum() == pytest.approx(1.0) and np.count_nonzero(decile) == 1
    assert quintile.sum() == pytest.approx(1.0) and np.count_nonzero(quintile) == 2
    assert ranked.sum() == pytest.approx(1.0) and np.count_nonzero(ranked) == 5
    assert ranked[9] > ranked[8] > ranked[7] > ranked[6] > ranked[5]
    assert np.all(decile >= 0) and np.all(quintile >= 0) and np.all(ranked >= 0)


@pytest.mark.parametrize("shape", ["top_decile", "top_quintile", "rank_weighted_top_half"])
def test_synthetic_portfolio_e2e_uses_pit_open_cohort_and_real_helpers(shape):
    scores, opens, closes, roster = _synthetic_panel()
    frozen_family = {f"R6-H{i}": 1.0 for i in range(1, 22)}
    frozen_family.update({"R7-H1": .5, "R7-H2": .5})
    result = run_portfolio(scores, opens, closes, roster, [2, 5, 8, 11, 14, 16],
                           [f"A{i:02}" for i in range(10)], shape=shape,
                           turnover_cap=.5, cost_rate=.0005, trial_count=12,
                           holm_family=frozen_family,
                           bootstrap_draws=100, seed=31)
    assert len(result["strategy_daily_net"]) == closes.shape[1] - 2
    assert len(result["benchmark_daily_net"]) == len(result["strategy_daily_net"])
    assert result["turnover_max"] <= .5 + 1e-12
    assert result["trial_count"] == 12
    assert 0 <= result["bootstrap_p_raw"] <= 1
    assert 0 <= result["bootstrap_p_holm"] <= 1
    assert np.isfinite(result["strategy_mean_nw_t"])
    assert np.isfinite(result["deflated_sharpe"])
    record = next(x for x in result["formation_records"] if x["fill_index"] == 5)
    assert "A09" not in record["benchmark_cohort_names"]
    assert "A09" not in record["strategy_target_names"]
    # Decision 63 holds the prior close through the gap; resumed close recovers
    # the 4% movement instead of dropping the asset or imputing a zero price.
    assert result["decision63_terminal_stale_strategy_names"] == 0


def test_r7_holm_family_appends_to_frozen_r6_21_and_hashes_json_dump(tmp_path):
    path = tmp_path / "r7_holm_family.json"
    obj = build_holm_family(path)
    checked = validate_holm_family(path)
    assert obj["manifest"] == [*R6_ENDPOINTS, *R7_ENDPOINTS]
    assert len(obj["manifest"]) == 24
    assert set(obj["p_values"].values()) == {None}
    expected = hashlib.sha256(json.dumps(obj["manifest"]).encode("utf-8")).hexdigest()
    assert obj["manifest_sha256"] == expected == checked["manifest_sha256"]
    with pytest.raises(ValueError, match="populate preserved R6"):
        validate_holm_family(path, require_r6_populated=True)


def test_trial_count_is_cumulative_and_budgeted():
    # DSR counts tried strategy variants, not the separate Holm endpoints.
    assert cumulative_trial_count(prior_trials=7, r7_registered_trials=3) == 10
    with pytest.raises(ValueError, match="budget"):
        cumulative_trial_count(prior_trials=29, r7_registered_trials=2)


def test_turnover_cap_preserves_uninvested_cash():
    target = np.array([1.0, 0.0, 0.0])
    weights, turnover, binds = _cap_trade(np.zeros(3), target, np.ones(3, dtype=bool), .5)
    held, daily_return = _apply_returns(weights, np.zeros(3))
    assert binds and turnover == pytest.approx(.5)
    assert weights.sum() == pytest.approx(.5)
    assert held.sum() == pytest.approx(.5)
    assert daily_return == pytest.approx(0.0)


def test_prerun_path_guard_rejects_pre_window_and_sealed_paths(tmp_path):
    root = tmp_path.resolve()
    with pytest.raises(PreRunError, match="pre-window"):
        _safe_path(root / "prices_2019-12-31.csv", root=root)
    with pytest.raises(PreRunError, match="sealed-holdout"):
        _safe_path(root / "sealed_holdout" / "prices.csv", root=root)


def test_synthetic_preflight_helper_contracts_use_shared_real_helpers():
    assert synthetic_helper_check() == {
        "newey_west": "pass", "placebo": "pass", "block_bootstrap": "pass",
        "holm": "pass", "dsr": "pass", "portfolio_engine": "pass",
    }

