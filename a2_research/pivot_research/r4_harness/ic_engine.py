"""Generic cross-sectional Spearman IC and mechanism placebo helpers.

All matrices are assets × dates. The caller supplies forward returns already
aligned to the date on which each score is known and an arbitrary point-in-time
asset mask (for example, an S&P 500, S&P 100, or Dow roster).
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

import numpy as np
from scipy.stats import rankdata


@dataclass(frozen=True)
class ICResult:
    ic_by_date: np.ndarray
    n_assets_by_date: np.ndarray
    mean_ic: float
    nw_t: float
    nw_lag: int
    bootstrap_p: float | None = None
    bootstrap_means: np.ndarray | None = None


@dataclass(frozen=True)
class PlaceboResult:
    observed_mean_ic: float
    placebo_means: np.ndarray
    percentile: float
    upper_tail_p: float


def _mat(x, label):
    a = np.asarray(x, dtype=float)
    if a.ndim != 2:
        raise ValueError(f"{label} must be an assets × dates 2D array")
    return a


def _mask(mask, shape):
    n, t = shape
    if mask is None:
        return np.ones(shape, dtype=bool)
    m = np.asarray(mask, dtype=bool)
    if m.ndim == 1 and m.shape == (n,):
        return np.broadcast_to(m[:, None], shape)
    if m.shape == shape:
        return m
    if m.shape == (t, n):
        return m.T
    raise ValueError(f"universe_mask must have shape {(n,)}, {(n,t)} or {(t,n)}; got {m.shape}")


def _spearman(x, y):
    if len(x) < 3:
        return float("nan")
    rx = rankdata(x, method="average")
    ry = rankdata(y, method="average")
    if np.std(rx) == 0 or np.std(ry) == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def ic_series(scores, forward_returns, universe_mask=None) -> tuple[np.ndarray, np.ndarray]:
    """Return one Spearman rank IC and valid asset count per date.

    Dates with fewer than three finite active assets or a constant rank vector
    receive NaN IC. A static one-dimensional mask is broadcast through time.
    """
    s = _mat(scores, "scores")
    r = _mat(forward_returns, "forward_returns")
    if s.shape != r.shape:
        raise ValueError("scores and forward_returns must have identical shapes")
    m = _mask(universe_mask, s.shape)
    vals = np.full(s.shape[1], np.nan)
    counts = np.zeros(s.shape[1], dtype=int)
    for t in range(s.shape[1]):
        ok = m[:, t] & np.isfinite(s[:, t]) & np.isfinite(r[:, t])
        counts[t] = int(ok.sum())
        if counts[t] >= 3:
            vals[t] = _spearman(s[ok, t], r[ok, t])
    return vals, counts


def newey_west_t(values, lag=0) -> float:
    """Bartlett Newey–West t-statistic for the mean of a dated IC series."""
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 2:
        return float("nan")
    lag = min(max(int(lag), 0), n - 1)
    u = x - x.mean()
    long_var = float(u @ u / n)
    for k in range(1, lag + 1):
        long_var += 2 * (1 - k / (lag + 1)) * float(u[k:] @ u[:-k]) / n
    se = math.sqrt(max(long_var, 0) / n)
    if se == 0:
        return math.copysign(float("inf"), x.mean()) if x.mean() else 0.0
    return float(x.mean() / se)


def circular_block_bootstrap_test(values, *, block_length=10, n_draws=5000,
                                  seed=20261110,
                                  alternative: Literal["positive", "two-sided"] = "positive"):
    """Centered circular block-bootstrap test of a mean IC against zero."""
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 2 or block_length < 1 or n_draws < 1:
        raise ValueError("need at least two finite ICs, positive block length and draws")
    if alternative not in ("positive", "two-sided"):
        raise ValueError("alternative must be 'positive' or 'two-sided'")
    observed = float(x.mean())
    centered = x - observed
    rng = np.random.default_rng(seed)
    blocks = int(math.ceil(n / block_length))
    offsets = np.arange(block_length)
    means = np.empty(n_draws)
    for b in range(n_draws):
        starts = rng.integers(0, n, size=blocks)
        ix = ((starts[:, None] + offsets) % n).ravel()[:n]
        means[b] = centered[ix].mean()
    if alternative == "positive":
        p = (1 + int(np.sum(means >= observed))) / (n_draws + 1)
    else:
        p = (1 + int(np.sum(np.abs(means) >= abs(observed)))) / (n_draws + 1)
    return float(p), means


def cross_sectional_ic(scores, forward_returns, universe_mask=None, *, nw_lag=0,
                       bootstrap=False, block_length=10, n_draws=5000,
                       seed=20261110, alternative="positive") -> ICResult:
    """Compute date-wise IC, its mean/NW t, and optional block-bootstrap p-value."""
    vals, counts = ic_series(scores, forward_returns, universe_mask)
    finite = vals[np.isfinite(vals)]
    mean = float(finite.mean()) if len(finite) else float("nan")
    t = newey_west_t(vals, nw_lag)
    p = boot = None
    if bootstrap:
        p, boot = circular_block_bootstrap_test(vals, block_length=block_length,
                                                 n_draws=n_draws, seed=seed,
                                                 alternative=alternative)
    return ICResult(vals, counts, mean, t, min(max(int(nw_lag), 0), max(len(finite)-1, 0)), p, boot)


def permutation_placebo(scores, forward_returns, universe_mask=None, *, n_draws=500,
                        seed=20261110) -> PlaceboResult:
    """Shuffle scores within each date's active roster and compare mean ICs."""
    s = _mat(scores, "scores")
    r = _mat(forward_returns, "forward_returns")
    if s.shape != r.shape or n_draws < 1:
        raise ValueError("matching score/return arrays and positive n_draws required")
    m = _mask(universe_mask, s.shape)
    observed = cross_sectional_ic(s, r, m).mean_ic
    if not np.isfinite(observed):
        raise ValueError("observed mean IC is not finite")
    rng = np.random.default_rng(seed)
    placebo = np.empty(n_draws)
    for k in range(n_draws):
        shuffled = s.copy()
        for t in range(s.shape[1]):
            eligible = np.flatnonzero(m[:, t] & np.isfinite(s[:, t]))
            shuffled[eligible, t] = rng.permutation(s[eligible, t])
        placebo[k] = cross_sectional_ic(shuffled, r, m).mean_ic
    p = (1 + int(np.sum(placebo >= observed))) / (n_draws + 1)
    return PlaceboResult(observed, placebo, float(np.mean(placebo <= observed)), float(p))


def shift_placebo(scores, forward_returns, shift_sessions: int, universe_mask=None) -> ICResult:
    """Compare returns with scores shifted by whole dates, without wraparound.

    A positive shift aligns a past score to a later return date; a negative
    shift aligns a future score and should only be used as a labeled placebo.
    Boundary dates are NaN, and the contemporaneous universe mask remains in
    force on the return date.
    """
    s = _mat(scores, "scores")
    r = _mat(forward_returns, "forward_returns")
    if s.shape != r.shape:
        raise ValueError("scores and forward_returns must have identical shapes")
    shift = int(shift_sessions)
    if shift == 0 or abs(shift) >= s.shape[1]:
        raise ValueError("shift_sessions must be non-zero and shorter than the date axis")
    shifted = np.full_like(s, np.nan)
    if shift > 0:
        shifted[:, shift:] = s[:, :-shift]
    else:
        shifted[:, :shift] = s[:, -shift:]
    return cross_sectional_ic(shifted, r, universe_mask)

