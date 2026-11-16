"""Compute every Section 4 metric from the saved backtest results.

Run from this folder:  python compute_metrics.py
Writes metrics_summary.csv and yearly_returns.csv next to this script.

Inputs (all in this repository):
  ../results/J1_RESULTS.json                       official J1 run (daily net returns, J1 and EW30)
  ../../6_refinement_J2/results/R9_VARIANTS_V2.json  12 variants on the common window (daily net returns)
  ../../6_refinement_J2/results/HOLDOUT_RESULT.json  J2 one-time holdout run (summary only)
  ../../2_data/J1_PRICES_DEV.npz                    trading calendar for the J1 run

Conventions: daily returns, 252 trading days a year, zero risk-free rate.
"""
import csv, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
A = 252


def stats(r, bench=None):
    r = np.asarray(r, float)
    cum = np.prod(1 + r) - 1
    cagr = (1 + cum) ** (A / len(r)) - 1
    vol = r.std(ddof=1) * np.sqrt(A)
    sharpe = r.mean() / r.std(ddof=1) * np.sqrt(A)
    sortino = r.mean() / np.sqrt((np.minimum(r, 0) ** 2).mean()) * np.sqrt(A)
    eq = np.cumprod(1 + r)
    mdd = (eq / np.maximum.accumulate(eq) - 1).min()
    q = np.quantile(r, 0.05)
    out = dict(net_cumulative_return=cum, cagr=cagr, volatility=vol, max_drawdown=mdd,
               var95_daily=-q, es95_daily=-r[r <= q].mean(), sharpe=sharpe, sortino=sortino,
               calmar=cagr / abs(mdd), days=len(r))
    if bench is not None:
        b = np.asarray(bench, float)
        ex = r - b
        beta = np.cov(r, b, ddof=1)[0, 1] / b.var(ddof=1)
        weekly = [np.prod(1 + r[i:i + 5]) - np.prod(1 + b[i:i + 5]) for i in range(0, len(r) - 4, 5)]
        out.update(beta=beta, alpha_annual=(r.mean() - beta * b.mean()) * A,
                   correlation=np.corrcoef(r, b)[0, 1], tracking_error=ex.std(ddof=1) * np.sqrt(A),
                   information_ratio=ex.mean() / ex.std(ddof=1) * np.sqrt(A),
                   weekly_hit_rate=float(np.mean(np.array(weekly) > 0)))
    return out


def main():
    rows = []
    # 1. Official J1 run, full development period
    j1 = json.load(open(os.path.join(HERE, "..", "results", "J1_RESULTS.json")))["portfolio"]
    s, b = j1["net"]["returns"], j1["ew_net"]["returns"]
    npz = np.load(os.path.join(ROOT, "2_data", "J1_PRICES_DEV.npz"), allow_pickle=True)
    dates = np.array(npz["dow_dates"])[np.array(j1["net"]["return_date_indices"])]
    period = f"{str(dates[0])[:10]} to {str(dates[-1])[:10]}"
    rows.append(dict(run="J1 official run", sample="in-sample (development)", period=period, **stats(s, b),
                     mean_turnover=j1["mean_turnover"], cost_to_gross_edge=j1["cost_to_gross_edge_ratio"],
                     bootstrap_p=j1["bootstrap_p_raw"]))
    rows.append(dict(run="EW30 benchmark (J1 run)", sample="in-sample (development)", period=period, **stats(b)))

    # yearly returns for the J1 run
    yearly = {}
    for r1, r2, t in zip(s, b, dates):
        y = str(t)[:4]
        a, c = yearly.get(y, (1.0, 1.0))
        yearly[y] = (a * (1 + r1), c * (1 + r2))
    with open(os.path.join(HERE, "yearly_returns.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "J1_net_return", "EW30_net_return", "J1_minus_EW30"])
        for y, (a, c) in sorted(yearly.items()):
            w.writerow([y, round(a - 1, 4), round(c - 1, 4), round(a - c, 4)])

    # 2. Common-window variants: J1 as V0, J2 as V5
    v2 = json.load(open(os.path.join(ROOT, "6_refinement_J2", "results", "R9_VARIANTS_V2.json")))
    bench = v2["benchmark"]["daily_returns"]
    for v in v2["variants"]:
        if v["id"] in ("R9-V0", "R9-V5"):
            name = "J1 (V0), common window" if v["id"] == "R9-V0" else "J2 (V5), common window"
            dts = v["daily_dates"]
            rows.append(dict(run=name, sample="in-sample (development)", period=f"{dts[0][:10]} to {dts[-1][:10]}",
                             **stats(v["daily_returns"], bench), mean_turnover=v["mean_turnover"],
                             cost_to_gross_edge=v["cost_to_gross_edge"], bootstrap_p=v["bootstrap_p"]))
    rows.append(dict(run="EW30 benchmark (common window)", sample="in-sample (development)",
                     period=f"{v2['benchmark']['daily_dates'][0][:10]} to {v2['benchmark']['daily_dates'][-1][:10]}",
                     **stats(bench)))

    # 3. J2 holdout (summary figures only are stored)
    h = json.load(open(os.path.join(ROOT, "6_refinement_J2", "results", "HOLDOUT_RESULT.json")))
    hp = f"{h['period']['start']} to {h['period']['end']}"
    rows.append(dict(run="J2 holdout run", sample="out-of-sample (holdout)", period=hp,
                     net_cumulative_return=h["strategy_net_cumulative_return"], sharpe=h["strategy_annualized_net_sharpe"],
                     bootstrap_p=h["one_sided_10_session_circular_bootstrap_p"], deflated_sharpe=h["dsr"],
                     days=h["period"]["n_daily"]))
    rows.append(dict(run="EW30 benchmark (holdout)", sample="out-of-sample (holdout)", period=hp,
                     net_cumulative_return=h["ew30_net_cumulative_return"], sharpe=h["ew30_annualized_net_sharpe"],
                     days=h["period"]["n_daily"]))

    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(os.path.join(HERE, "metrics_summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    for r in rows:
        print(r["run"], "|", r["period"], "| return", round(r["net_cumulative_return"], 4), "| sharpe", round(r["sharpe"], 3))


if __name__ == "__main__":
    main()
