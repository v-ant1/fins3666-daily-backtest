"""R8: J1 standard metrics and the gross-vs-net excess figure.

Reads the frozen, already-reported R6 J1 development results only
(r6_J1/J1_RESULTS.json) and the development date index (r6_J1/J1_PRICES_DEV.npz).
No new strategy test. Writes:
  report_drafts/figures/R8_J1_METRICS.json
  report_drafts/figures/r8_j1_excess.png
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
res = json.loads((ROOT / "r6_J1/J1_RESULTS.json").read_text())["portfolio"]
dates = np.load(ROOT / "r6_J1/J1_PRICES_DEV.npz", allow_pickle=True)["dow_dates"]

series = {k: np.asarray(res[k]["returns"], float) for k in ("gross", "net", "ew_gross", "ew_net")}
idx = np.asarray(res["net"]["return_date_indices"], int)
x = np.array(dates[idx], dtype="datetime64[D]")
years = len(series["net"]) / 252


def stats(r):
    wealth = np.cumprod(1 + r)
    cum = wealth[-1] - 1
    sd = r.std(ddof=1)
    down = r[r < 0].std(ddof=1)
    return {
        "cumulative_return": cum,
        "annualised_return": (1 + cum) ** (1 / years) - 1,
        "annualised_volatility": sd * np.sqrt(252),
        "sharpe": r.mean() / sd * np.sqrt(252),
        "sortino": r.mean() * 252 / (down * np.sqrt(252)),
        "max_drawdown": (wealth / np.maximum.accumulate(wealth) - 1).min(),
    }


metrics = {k: stats(v) for k, v in series.items()}
active = series["net"] - series["ew_net"]
metrics["net_vs_ew30"] = {
    "tracking_error": active.std(ddof=1) * np.sqrt(252),
    "information_ratio": active.mean() * 252 / (active.std(ddof=1) * np.sqrt(252)),
}
metrics["sample"] = {"trading_days": int(len(active)), "years": years,
                     "first_day": str(x[0]), "last_day": str(x[-1]),
                     "rebalances": len(res["net"]["turnovers"])}
for tag, a, b in (("gross", "gross", "ew_gross"), ("net", "net", "ew_net")):
    lead = np.cumprod(1 + series[a]) - np.cumprod(1 + series[b])
    metrics["net_vs_ew30"][f"share_of_days_ahead_{tag}"] = float((lead > 0).mean())
metrics["net_vs_ew30"]["ew30_total_cost"] = res["total_ew30_cost"]
for k in ("mean_turnover", "total_strategy_cost", "cost_to_gross_edge_ratio",
          "average_active_share", "gross_excess_return", "net_excess_return"):
    metrics.setdefault("official", {})[k] = res[k]
(OUT / "R8_J1_METRICS.json").write_text(json.dumps(metrics, indent=1, default=float))

# Figure: cumulative excess over EW30, gross and net (one axis, percentage points).
gross_ex = (np.cumprod(1 + series["gross"]) - np.cumprod(1 + series["ew_gross"])) * 100
net_ex = (np.cumprod(1 + series["net"]) - np.cumprod(1 + series["ew_net"])) * 100
ink, muted, grid = "#0b0b0b", "#52514e", "#e4e3df"
fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
fig.patch.set_facecolor("#fcfcfb"); ax.set_facecolor("#fcfcfb")
ax.axhline(0, color=muted, lw=1)
h_gross, = ax.plot(x, gross_ex, color="#2a78d6", lw=1.6, label="Before costs")
h_net, = ax.plot(x, net_ex, color="#eb6834", lw=1.6, label="After costs (0.05% per side)")
ax.text(x[-1], gross_ex[-1], f"  Before costs {gross_ex[-1]:+.1f} pp", color=ink, va="center", fontsize=8.5)
ax.text(x[-1], net_ex[-1], f"  After costs {net_ex[-1]:+.1f} pp", color=ink, va="center", fontsize=8.5)
ax.set_title("J1 beat EW30 by 14.9 pp before costs; 0.05% trading costs cut it to 1.0 pp",
             loc="left", fontsize=10, color=ink)
ax.set_ylabel("Cumulative return minus EW30 (pp)", fontsize=8.5, color=muted)
ax.grid(axis="y", color=grid, lw=0.8); ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(grid)
ax.tick_params(colors=muted, labelsize=8)
ax.legend(handles=[h_gross, h_net], frameon=False, fontsize=8, loc="upper left")
fig.tight_layout(rect=(0, 0, 0.84, 1))
fig.savefig(OUT / "r8_j1_excess.png", facecolor=fig.get_facecolor())
print(json.dumps({k: metrics[k] for k in ("net", "ew_net", "net_vs_ew30", "sample")}, indent=1, default=float))
