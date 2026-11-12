"""Independent minimal reproduction of D4-1 from the saved development bundle.

This intentionally does not import any D4 runner, builder, or harness module.
It reads only the prebuilt development NPZ and uses its adjusted open/close
matrices to form the registered t+1 open through t+5 close return.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.stats import rankdata, norm


ROOT = Path(__file__).resolve().parents[2]
NPZ = ROOT / "r4_harness" / "runs" / "D4" / "D4_INPUTS.npz"
OUT = Path(__file__).with_name("REPRO_D4_VALUES.json")
LAG = 4
HORIZON = 5


def nw_t(values: np.ndarray, lag: int = LAG) -> float:
    """Bartlett/Newey-West t for a mean, matching the registered formula."""
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    n = x.size
    if n < 2:
        return float("nan")
    mean = float(x.mean())
    centered = x - mean
    used_lag = min(max(int(lag), 0), n - 1)
    long_run_variance = float(centered @ centered / n)
    for k in range(1, used_lag + 1):
        weight = 1.0 - k / (used_lag + 1.0)
        long_run_variance += 2.0 * weight * float(centered[k:] @ centered[:-k]) / n
    se = np.sqrt(max(long_run_variance, 0.0) / n)
    return float(mean / se) if se > 0 else float("nan")


def main() -> None:
    with np.load(NPZ, allow_pickle=False) as z:
        assets = z["assets"].astype(str)
        dates = z["dates"].astype(str)
        roster = z["roster_mask"].astype(bool)
        score = z["ncp"].astype(float)
        op = z["adjusted_open"].astype(float)
        close = z["adjusted_close"].astype(float)

    if dates[0] != "2020-11-27" or dates[-1] != "2026-10-30":
        raise ValueError("Bundle dates do not match the registered development window")
    if not (score.shape == op.shape == close.shape == roster.shape):
        raise ValueError("Bundle matrices have inconsistent shapes")

    # At score date t, buy at adjusted open t+1 and mark at adjusted close t+5.
    forward = np.full_like(score, np.nan, dtype=float)
    for t in range(score.shape[1] - HORIZON):
        buy = op[:, t + 1]
        sell = close[:, t + HORIZON]
        valid = np.isfinite(buy) & np.isfinite(sell) & (buy > 0)
        forward[valid, t] = sell[valid] / buy[valid] - 1.0

    date_ics: list[float] = []
    used_dates = []
    for t in range(score.shape[1] - HORIZON):
        valid = roster[:, t] & np.isfinite(score[:, t]) & np.isfinite(forward[:, t])
        if int(valid.sum()) < 3:
            continue
        # Subtracting same-date EW return leaves ranks unchanged.
        y = forward[valid, t]
        y = y - y.mean()
        xr = rankdata(score[valid, t], method="average")
        yr = rankdata(y, method="average")
        if xr.std() == 0 or yr.std() == 0:
            continue
        date_ics.append(float(np.corrcoef(xr, yr)[0, 1]))
        used_dates.append(str(dates[t]))

    series = np.asarray(date_ics, dtype=float)
    result = {
        "source": "r4_harness/runs/D4/D4_INPUTS.npz only; no runner/builder/harness imports",
        "development_start": str(dates[0]),
        "development_end": str(dates[-1]),
        "sessions": int(dates.size),
        "asset_count": int(assets.size),
        "first_ic_date": used_dates[0] if used_dates else None,
        "last_ic_date": used_dates[-1] if used_dates else None,
        "finite_ic_dates": int(series.size),
        "mean_ic": float(series.mean()) if series.size else None,
        "newey_west_bartlett_lag4_t": nw_t(series),
        "one_sided_positive_raw_p": float(norm.sf(nw_t(series))) if series.size else None,
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
