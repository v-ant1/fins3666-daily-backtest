"""Synthetic power analysis for short-horizon cross-sectional IC / event studies.

This module deliberately accepts design assumptions only. It has no price-data or
return-data loaders. The Monte Carlo statistic is a one-sided Newey-West t-test
of a positive mean, using Bartlett weights and lag horizon - 1.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from statistics import NormalDist
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class PowerResult:
    p_nw_t_ge_2: float
    monte_carlo_se: float
    simulations: int
    observations_mean: float
    effective_n_mean: float
    effective_n_median: float
    minimum_detectable_effect_80: float
    planted_effect: float
    event_mode: bool
    event_dates_mean: Optional[float] = None
    event_count_mean: Optional[float] = None
    nw_lag: int = 0


def _validate(universe_size: int, n_dates: int, horizon: int, rho: float,
              ic_sd: float, simulations: int) -> None:
    if universe_size < 2 or n_dates < 3 or horizon < 1 or horizon > n_dates:
        raise ValueError("require assets>=2, dates>=3, and 1<=horizon<=dates")
    if not -0.95 <= rho <= 0.95:
        raise ValueError("signal_autocorrelation must be between -0.95 and 0.95")
    if not math.isfinite(ic_sd) or ic_sd <= 0:
        raise ValueError("cross_sectional_ic_sd must be finite and positive")
    if simulations < 100:
        raise ValueError("simulations must be at least 100")


def _nw_t(x: np.ndarray, lag: int) -> float:
    """One-sample mean t-stat with Bartlett Newey-West covariance estimate."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 3 or not np.all(np.isfinite(x)):
        return float("nan")
    centered = x - x.mean()
    gamma0 = float(centered @ centered / n)
    long_run = gamma0
    for k in range(1, min(lag, n - 1) + 1):
        gamma = float(centered[k:] @ centered[:-k] / n)
        long_run += 2.0 * (1.0 - k / (lag + 1.0)) * gamma
    variance_mean = max(long_run, 0.0) / n
    if variance_mean <= 0:
        return float("inf") if x.mean() > 0 else float("-inf")
    return float(x.mean() / math.sqrt(variance_mean))


def _design_effect(rho: float, lag: int) -> float:
    return max(1.0 + 2.0 * sum((1 - k / (lag + 1.0)) * rho**k
                              for k in range(1, lag + 1)), 1e-9)


def simulate_power(
    universe_size: int,
    n_dates: int,
    horizon: int,
    signal_autocorrelation: float = 0.2,
    cross_sectional_ic_sd: Optional[float] = None,
    event_rate: Optional[float] = None,
    event_cluster_shape: float = 0.5,
    planted_mean_ic: float = 0.0,
    event_effect: Optional[float] = None,
    simulations: int = 2000,
    seed: int = 20261110,
) -> PowerResult:
    """Estimate power using synthetic date-level IC observations.

    ``event_rate`` is expected events per calendar date. When supplied, event
    counts follow a negative binomial with mean ``event_rate`` and shape
    ``event_cluster_shape`` (variance mu + mu^2/shape); only event dates enter
    the test, and the date-level noise SD scales as ic_sd/sqrt(event count).
    Event mode tests ``event_effect`` (defaults to zero) instead of planted_mean_ic.

    If IC SD is omitted, use the normal approximation 1/sqrt(assets - 1) for
    the sampling SD of a null cross-sectional rank correlation. This is a
    design approximation, not estimated from project observations.
    """
    ic_sd = (1.0 / math.sqrt(universe_size - 1)
             if cross_sectional_ic_sd is None else float(cross_sectional_ic_sd))
    rho = float(signal_autocorrelation)
    _validate(universe_size, n_dates, horizon, rho, ic_sd, simulations)
    if event_rate is not None and (not math.isfinite(event_rate) or event_rate <= 0):
        raise ValueError("event_rate must be finite and positive")
    if event_rate is not None and (not math.isfinite(event_cluster_shape) or event_cluster_shape <= 0):
        raise ValueError("event_cluster_shape must be finite and positive")
    if event_rate is None and event_effect is not None:
        raise ValueError("event_effect requires event_rate")

    rng = np.random.default_rng(seed)
    lag = horizon - 1
    observed_counts = []
    effective_counts = []
    active_dates = []
    total_events = []
    detected = 0
    effects = []

    for _ in range(simulations):
        if event_rate is None:
            counts = np.ones(n_dates, dtype=int)
            effect = float(planted_mean_ic)
        else:
            # Gamma-Poisson mixture gives NB(mean=mu, shape=r): overdispersed
            # event counts with explicit date clustering.
            rate = rng.gamma(shape=event_cluster_shape,
                             scale=event_rate / event_cluster_shape, size=n_dates)
            counts = rng.poisson(rate)
            active = counts > 0
            counts = counts[active]
            effect = float(0.0 if event_effect is None else event_effect)
        n = len(counts)
        observed_counts.append(n)
        active_dates.append(n)
        total_events.append(int(counts.sum()))
        if n < 3:
            effective_counts.append(float(n))
            effects.append(effect)
            continue
        eps = rng.normal(size=n)
        if abs(rho) > 0:
            # Stationary unit-variance Gaussian AR(1), then event-count
            # heteroskedasticity reflects averaging several source events.
            for t in range(1, n):
                eps[t] = rho * eps[t - 1] + math.sqrt(1 - rho * rho) * eps[t]
        values = effect + eps * (ic_sd / np.sqrt(counts))
        detected += _nw_t(values, lag) >= 2.0
        mean_count = float(np.mean(counts))
        eff_n = n / _design_effect(rho, lag)
        effective_counts.append(eff_n)
        effects.append(effect)

    p = detected / simulations
    mean_n = float(np.mean(observed_counts))
    neff_mean = float(np.mean(effective_counts))
    # Expected standard error of the mean under the planning HAC approximation.
    # Event mode uses the mean per-date variance after event averaging.
    if event_rate is None:
        date_variance = ic_sd * ic_sd
    else:
        # E[1/count | count>0] approximated from the seeded synthetic design.
        # Track a broad, conservative count-based estimate analytically by
        # using E[count | count>0], with Jensen's inequality upper bound.
        p_zero = (event_cluster_shape / (event_cluster_shape + event_rate)) ** event_cluster_shape
        positive_mean = event_rate / (1.0 - p_zero)
        date_variance = ic_sd * ic_sd / positive_mean
    mde = (2.0 + NormalDist().inv_cdf(0.80)) * math.sqrt(
        date_variance * _design_effect(rho, lag) / max(mean_n, 1.0))
    return PowerResult(
        p_nw_t_ge_2=float(p),
        monte_carlo_se=float(math.sqrt(p * (1 - p) / simulations)),
        simulations=simulations,
        observations_mean=mean_n,
        effective_n_mean=neff_mean,
        effective_n_median=float(np.median(effective_counts)),
        minimum_detectable_effect_80=float(mde),
        planted_effect=float(np.mean(effects)),
        event_mode=event_rate is not None,
        event_dates_mean=float(np.mean(active_dates)) if event_rate is not None else None,
        event_count_mean=float(np.mean(total_events)) if event_rate is not None else None,
        nw_lag=lag,
    )


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=int, required=True)
    parser.add_argument("--dates", type=int, required=True)
    parser.add_argument("--horizon", type=int, required=True)
    parser.add_argument("--signal-autocorrelation", type=float, default=0.2)
    parser.add_argument("--ic-sd", type=float, default=None,
                        help="SD assumption; default 1/sqrt(assets-1), a null-rank-IC approximation")
    parser.add_argument("--mean-ic", type=float, default=0.0)
    parser.add_argument("--event-rate", type=float, default=None,
                        help="expected events per calendar date; activates clustered event mode")
    parser.add_argument("--cluster-shape", type=float, default=0.5)
    parser.add_argument("--event-effect", type=float, default=None)
    parser.add_argument("--simulations", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261110)
    args = parser.parse_args()
    result = simulate_power(
        universe_size=args.assets, n_dates=args.dates, horizon=args.horizon,
        signal_autocorrelation=args.signal_autocorrelation,
        cross_sectional_ic_sd=args.ic_sd, event_rate=args.event_rate,
        event_cluster_shape=args.cluster_shape, planted_mean_ic=args.mean_ic,
        event_effect=args.event_effect, simulations=args.simulations, seed=args.seed)
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    _main()
