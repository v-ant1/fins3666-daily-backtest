"""Independent, outcome-free-now J1 mechanism reference.

This module deliberately has no project-data CLI.  It accepts aligned arrays so
it can be used for the synthetic self-test now and, after the official J1 run,
for an independent reproduction using the authorized development outcomes.
"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

import numpy as np
from scipy.stats import rankdata

NW_LAG = 4
SHUFFLE_DRAWS = 500
SEED = 20261111


@dataclass(frozen=True)
class J1Result:
    ic_by_date: np.ndarray
    n_by_date: np.ndarray
    mean_ic: float
    direction_adjusted_mean_ic: float
    direction_adjusted_nw_t: float
    placebo_direction_adjusted_means: np.ndarray
    placebo_p95: float
    placebo_p: float
    placebo_pass: bool


def _matrix(value, name, dtype=None):
    arr = np.asarray(value, dtype=dtype)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be a dates x tickers 2D matrix")
    return arr


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 3:
        return float("nan")
    rx = rankdata(x, method="average")
    ry = rankdata(y, method="average")
    if np.ptp(rx) == 0 or np.ptp(ry) == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def datewise_spearman(signal, relative_forward_return, eligible_mask):
    """Return date-wise Spearman IC and valid-name count.

    Inputs have shape dates x tickers. The caller supplies the registered
    point-in-time and input-availability mask; finite signal and outcome are
    additionally required. J1's expected sign is negative.
    """
    s = _matrix(signal, "signal", float)
    y = _matrix(relative_forward_return, "relative_forward_return", float)
    m = _matrix(eligible_mask, "eligible_mask", bool)
    if s.shape != y.shape or s.shape != m.shape:
        raise ValueError("signal, relative outcomes, and mask must have matching shapes")
    ics = np.full(s.shape[0], np.nan)
    counts = np.zeros(s.shape[0], dtype=int)
    for t in range(s.shape[0]):
        ok = m[t] & np.isfinite(s[t]) & np.isfinite(y[t])
        counts[t] = int(ok.sum())
        if counts[t] >= 3:
            ics[t] = _spearman(s[t, ok], y[t, ok])
    return ics, counts


def newey_west_t(values, lag=NW_LAG) -> float:
    """Bartlett Newey-West t for the mean, independently implemented."""
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 2:
        return float("nan")
    lag = min(max(int(lag), 0), n - 1)
    centered = x - x.mean()
    long_run_variance = float(centered @ centered / n)
    for k in range(1, lag + 1):
        bartlett = 1.0 - k / (lag + 1.0)
        autocovariance = float(centered[k:] @ centered[:-k] / n)
        long_run_variance += 2.0 * bartlett * autocovariance
    standard_error = math.sqrt(max(long_run_variance, 0.0) / n)
    if standard_error == 0:
        return math.copysign(float("inf"), x.mean()) if x.mean() else 0.0
    return float(x.mean() / standard_error)


def relative_forward_returns(forward_returns, sic2, eligible_mask):
    """Create each name's leave-one-out same-SIC2 forward return.

    This is the J1 outcome transformation: an own forward return less the
    equal-weight mean forward return of other eligible names sharing SIC2.
    Shapes are dates x tickers. SIC groups with no other valid peer remain NaN.
    """
    y = _matrix(forward_returns, "forward_returns", float)
    groups = _matrix(sic2, "sic2").astype(str)
    mask = _matrix(eligible_mask, "eligible_mask", bool)
    if y.shape != groups.shape or y.shape != mask.shape:
        raise ValueError("forward returns, SIC2 labels, and mask must match")
    out = np.full(y.shape, np.nan)
    for t in range(y.shape[0]):
        valid = mask[t] & np.isfinite(y[t]) & (groups[t] != "")
        for g in np.unique(groups[t, valid]):
            ix = np.flatnonzero(valid & (groups[t] == g))
            if len(ix) < 2:
                continue
            group_total = float(y[t, ix].sum())
            out[t, ix] = y[t, ix] - (group_total - y[t, ix]) / (len(ix) - 1)
    return out


def sic2_signal_shuffle(signal, relative_forward_return, sic2, eligible_mask,
                        *, draws=SHUFFLE_DRAWS, seed=SEED):
    """Shuffle signal labels within date x SIC2 cells, preserving group sizes."""
    s = _matrix(signal, "signal", float)
    y = _matrix(relative_forward_return, "relative_forward_return", float)
    groups = _matrix(sic2, "sic2").astype(str)
    mask = _matrix(eligible_mask, "eligible_mask", bool)
    if not (s.shape == y.shape == groups.shape == mask.shape):
        raise ValueError("signal, outcomes, SIC2, and mask must have matching shapes")
    if draws < 1:
        raise ValueError("draws must be positive")
    active = mask & np.isfinite(s) & np.isfinite(y) & (groups != "")
    observed_ics, _ = datewise_spearman(s, y, active)
    finite_observed = observed_ics[np.isfinite(observed_ics)]
    if not len(finite_observed):
        raise ValueError("no eligible date-wise ICs")
    observed_direction = -float(finite_observed.mean())
    rng = np.random.default_rng(seed)
    null = np.empty(draws, dtype=float)
    for b in range(draws):
        shuffled = s.copy()
        for t in range(s.shape[0]):
            for group in np.unique(groups[t, active[t]]):
                ix = np.flatnonzero(active[t] & (groups[t] == group))
                if len(ix) >= 2:
                    shuffled[t, ix] = rng.permutation(s[t, ix])
        ics, _ = datewise_spearman(shuffled, y, active)
        finite = ics[np.isfinite(ics)]
        null[b] = -float(finite.mean())
    p95 = float(np.percentile(null, 95))
    p = float((1 + int(np.sum(null >= observed_direction))) / (draws + 1))
    return observed_direction, null, p95, p


def analyze_j1(signal, relative_forward_return, sic2, eligible_mask,
               *, draws=SHUFFLE_DRAWS, seed=SEED) -> J1Result:
    """Compute the registered negative-sign mechanism and fixed placebo."""
    ics, counts = datewise_spearman(signal, relative_forward_return, eligible_mask)
    finite = ics[np.isfinite(ics)]
    if not len(finite):
        raise ValueError("no eligible date-wise ICs")
    mean_ic = float(finite.mean())
    direction_t = newey_west_t(-ics, NW_LAG)
    direction_mean, null, p95, p = sic2_signal_shuffle(
        signal, relative_forward_return, sic2, eligible_mask,
        draws=draws, seed=seed,
    )
    placebo_pass = bool(direction_mean > p95 and p < 0.05)
    return J1Result(
        ic_by_date=ics, n_by_date=counts, mean_ic=mean_ic,
        direction_adjusted_mean_ic=direction_mean,
        direction_adjusted_nw_t=direction_t,
        placebo_direction_adjusted_means=null,
        placebo_p95=p95, placebo_p=p, placebo_pass=placebo_pass,
    )


def synthetic_self_test():
    """Deterministic synthetic test with planted negative rank relation."""
    rng = np.random.default_rng(8172026)
    dates, names, groups_per_date, group_size = 72, 120, 12, 10
    signal = rng.normal(size=(dates, names))
    sic2 = np.tile(np.repeat([f"{i:02d}" for i in range(groups_per_date)], group_size),
                   (dates, 1))
    # The synthetic outcome is deliberately lower for higher signal scores.
    relative_fwd = -0.8 * signal + rng.normal(scale=0.7, size=signal.shape)
    mask = np.ones(signal.shape, dtype=bool)
    result = analyze_j1(signal, relative_fwd, sic2, mask, draws=SHUFFLE_DRAWS, seed=SEED)
    assert result.mean_ic < 0, result.mean_ic
    assert result.direction_adjusted_nw_t >= 2, result.direction_adjusted_nw_t
    assert result.direction_adjusted_mean_ic > result.placebo_p95
    assert result.placebo_p < 0.05, result.placebo_p
    assert result.placebo_pass
    assert len(result.placebo_direction_adjusted_means) == SHUFFLE_DRAWS
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="validate only on deterministic synthetic arrays")
    args = parser.parse_args(argv)
    if not args.self_test:
        parser.error("No project-data mode is provided; use --self-test only. Real outcomes are reserved until the official J1 run.")
    result = synthetic_self_test()
    print({"synthetic_dates": len(result.ic_by_date),
           "synthetic_mean_ic": result.mean_ic,
           "direction_adjusted_nw_t": result.direction_adjusted_nw_t,
           "placebo_p95": result.placebo_p95,
           "placebo_p": result.placebo_p,
           "placebo_pass": result.placebo_pass,
           "draws": len(result.placebo_direction_adjusted_means),
           "scope": "synthetic only; no project outcomes loaded"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
