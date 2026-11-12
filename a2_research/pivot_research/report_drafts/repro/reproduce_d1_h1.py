"""Minimal independent reproduction of the frozen D1 S&P H1 statistic.

Reads only the hash-pinned development input bundle. It does not import or
invoke the D1 runner, write endpoint logs, or access any holdout files.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from scipy.stats import rankdata


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "r6_D1" / "D1_INPUTS.npz"
EXPECTED_SHA256 = "33b977f9454b50f1d197751a6883d92bdd45e3041ed92082a18e43fc32108538"


def nw_t_mean(values: np.ndarray, lag: int = 4) -> float:
    """Bartlett Newey-West t for the mean, matching the frozen lag-4 rule."""
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 2:
        raise ValueError("need at least two finite date-wise ICs")
    u = x - x.mean()
    long_var = float(u @ u / n)
    for k in range(1, min(lag, n - 1) + 1):
        long_var += 2 * (1 - k / (lag + 1)) * float(u[k:] @ u[:-k]) / n
    se = np.sqrt(max(long_var, 0.0) / n)
    return float(x.mean() / se) if se > 0 else float("inf")


def main() -> None:
    digest = hashlib.sha256(BUNDLE.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"input hash mismatch: {digest}")

    with np.load(BUNDLE, allow_pickle=False) as z:
        dates = z["dates"].astype(str)
        if dates[0] < "2020-06-01" or dates[-1] > "2026-10-30":
            raise SystemExit("bundle includes dates outside the allowed development range")
        ratio = z["sp500_ratio"].astype(float)
        roster = z["sp500_roster"].astype(bool)
        op = z["sp500_adjusted_open"].astype(float)
        close = z["sp500_adjusted_close"].astype(float)

    # Frozen D1: five consecutive paired nonnegative facility ratios; P = -R.
    n_names, n_dates = ratio.shape
    score = np.full((n_names, n_dates), np.nan)
    for t in range(4, n_dates):
        w = ratio[:, t - 4:t + 1]
        ok = np.isfinite(w).all(axis=1) & (w >= 0).all(axis=1)
        score[ok, t] = -w[ok].mean(axis=1)

    # Frozen forward window: t+2 adjusted open to t+6 adjusted close.
    forward = np.full_like(score, np.nan)
    for t in range(n_dates - 6):
        good = (np.isfinite(op[:, t + 2]) & (op[:, t + 2] > 0) &
                np.isfinite(close[:, t + 6]) & (close[:, t + 6] > 0))
        forward[good, t] = close[good, t + 6] / op[good, t + 2] - 1.0

    # Every fifth session beginning 2020-11-27, excluding dates without t+6.
    dev = np.flatnonzero((dates >= "2020-11-27") & (dates <= "2026-10-30"))
    formations = dev[::5]
    formations = formations[formations + 6 < n_dates]

    ics = []
    counts = []
    for t in formations:
        eligible = roster[:, t] & np.isfinite(score[:, t]) & np.isfinite(forward[:, t])
        x, y = score[eligible, t], forward[eligible, t]
        counts.append(len(x))
        if len(x) < 3:
            ics.append(np.nan)
            continue
        rx, ry = rankdata(x, method="average"), rankdata(y, method="average")
        if np.std(rx) == 0 or np.std(ry) == 0:
            ics.append(np.nan)
        else:
            ics.append(float(np.corrcoef(rx, ry)[0, 1]))

    ics = np.asarray(ics, dtype=float)
    valid = ics[np.isfinite(ics)]
    mean_ic = float(valid.mean())
    t_stat = nw_t_mean(ics, lag=4)
    print(f"bundle_sha256={digest}")
    print(f"sessions={n_dates}; formations={len(formations)}; valid_ics={len(valid)}")
    print(f"mean_ic={mean_ic:.9g} ({mean_ic:.3g} to 3 s.f.)")
    print(f"nw_t_lag4={t_stat:.9g} ({t_stat:.3g} to 3 s.f.)")
    print(f"eligible_names_per_formation_min={min(counts)}; max={max(counts)}")


if __name__ == "__main__":
    main()
