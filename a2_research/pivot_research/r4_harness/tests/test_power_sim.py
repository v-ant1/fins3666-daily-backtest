import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from power_sim import simulate_power


def test_null_vs_planted_effect_detection_is_synthetic_and_reproducible():
    params = dict(universe_size=30, n_dates=600, horizon=5,
                  signal_autocorrelation=0.15, cross_sectional_ic_sd=0.08,
                  simulations=1200, seed=812)
    null = simulate_power(**params, planted_mean_ic=0.0)
    planted = simulate_power(**params, planted_mean_ic=0.03)
    planted_repeat = simulate_power(**params, planted_mean_ic=0.03)
    assert null.p_nw_t_ge_2 < 0.15
    assert planted.p_nw_t_ge_2 > null.p_nw_t_ge_2 + 0.25
    assert planted.p_nw_t_ge_2 > 0.8
    assert planted == planted_repeat
    assert planted.nw_lag == 4
    assert planted.effective_n_mean < 600
    assert planted.minimum_detectable_effect_80 > 0


def test_longer_overlap_reduces_effective_n_and_increases_mde():
    short = simulate_power(100, 1000, 5, signal_autocorrelation=0.2,
                           cross_sectional_ic_sd=0.1, simulations=200, seed=9)
    long = simulate_power(100, 1000, 21, signal_autocorrelation=0.2,
                          cross_sectional_ic_sd=0.1, simulations=200, seed=9)
    assert long.nw_lag == 20
    assert long.effective_n_mean < short.effective_n_mean
    assert long.minimum_detectable_effect_80 > short.minimum_detectable_effect_80


def test_clustered_event_mode_counts_only_event_dates():
    result = simulate_power(30, 1000, 5, signal_autocorrelation=0.1,
                           cross_sectional_ic_sd=0.1, event_rate=0.08,
                           event_cluster_shape=0.3, event_effect=0.2,
                           simulations=500, seed=44)
    assert result.event_mode
    assert 0 < result.event_dates_mean < 1000
    assert result.event_count_mean > result.event_dates_mean
    assert result.observations_mean == pytest.approx(result.event_dates_mean)
    assert result.p_nw_t_ge_2 > 0.8
    assert math.isfinite(result.minimum_detectable_effect_80)


def test_rejects_invalid_assumptions():
    with pytest.raises(ValueError):
        simulate_power(30, 100, 5, signal_autocorrelation=1.0)
    with pytest.raises(ValueError):
        simulate_power(30, 100, 5, event_effect=0.1)
