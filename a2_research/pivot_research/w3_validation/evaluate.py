#!/usr/bin/env python3
"""Evaluate daily wealth-index CSVs against EW30 and SPY.

Input requires a date column, an EW benchmark column (default ``ew``), a SPY
column (default ``spy``), and one or more strategy wealth-index columns.
Wealth indexes are converted to close-to-close daily returns by differencing
adjacent rows. Period starts therefore use the first in-period observation's
return from the immediately preceding row, when that row is present.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

PERIODS = {
    "IS": ("2020-11-27", "2022-12-30"),
    "OOS1": ("2023-01-03", "2024-02-23"),
    "OOS2": ("2024-12-06", "2025-12-31"),
}
TRADING_DAYS = 252


def read_csv(path: Path, date_col: str) -> tuple[list[str], dict[str, np.ndarray]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or date_col not in reader.fieldnames:
            raise ValueError(f"CSV must contain a '{date_col}' column")
        dates, values = [], {name: [] for name in reader.fieldnames if name != date_col}
        for row in reader:
            dates.append(row[date_col][:10])
            for name in values:
                raw = row.get(name, "")
                values[name].append(float(raw) if raw not in (None, "") else math.nan)
    if len(dates) < 2 or dates != sorted(dates) or len(set(dates)) != len(dates):
        raise ValueError("Dates must be unique, ascending, and include at least two rows")
    return dates, {k: np.asarray(v, dtype=float) for k, v in values.items()}


def wealth_returns(wealth: np.ndarray, dates: list[str], reset_gap_days: int = 10) -> np.ndarray:
    if np.any(~np.isfinite(wealth)) or np.any(wealth <= 0):
        raise ValueError("Wealth columns must contain finite, positive levels")
    # Treat the wealth index as based at 1.0 immediately before its first row.
    # This captures first-fill costs when a standalone official window begins
    # on its first recorded date.
    out = np.empty(len(wealth), dtype=float)
    out[0] = wealth[0] - 1.0
    for i in range(1, len(wealth)):
        gap = (dt.date.fromisoformat(dates[i]) - dt.date.fromisoformat(dates[i - 1])).days
        # A long gap denotes a separately initialized equity series. Reset to
        # its $1 base instead of treating the gap as a single-period return.
        out[i] = (wealth[i] - 1.0 if gap > reset_gap_days
                  else wealth[i] / wealth[i - 1] - 1.0)
    return out


def longest_drawdown_duration(wealth: np.ndarray) -> int:
    peak = -np.inf
    age = 0
    longest = 0
    for value in wealth:
        if value >= peak:
            peak, age = value, 0
        else:
            age += 1
            longest = max(longest, age)
    return longest


def max_drawdown(wealth: np.ndarray) -> tuple[float, int, np.ndarray]:
    peaks = np.maximum.accumulate(np.r_[1.0, wealth])[1:]
    dd = wealth / peaks - 1.0
    return float(np.min(dd)), longest_drawdown_duration(wealth), dd


def circular_block_p(excess: np.ndarray, block: int, draws: int,
                     rng: np.random.Generator) -> float:
    """Two-sided circular block-bootstrap test of zero mean excess return.

    Resample demeaned returns under the null. Blocks wrap around the observed
    sequence; partial final blocks are truncated to the sample length.
    """
    n = len(excess)
    observed = abs(float(np.mean(excess)))
    centered = excess - np.mean(excess)
    blocks_needed = math.ceil(n / block)
    exceed = 0
    offsets = np.arange(block)
    for _ in range(draws):
        starts = rng.integers(0, n, size=blocks_needed)
        sample = np.concatenate([centered[(s + offsets) % n] for s in starts])[:n]
        if abs(float(sample.mean())) >= observed:
            exceed += 1
    return (exceed + 1) / (draws + 1)


def deflated_sharpe(daily_returns: np.ndarray, trials: int) -> float:
    """Estimated DSR probability using the independent-trial expected max SR.

    Uses daily (not annualized) Sharpe, sample skewness, and Pearson kurtosis.
    Trial dependence is unavailable in a single strategy CSV, so this is a
    conservative-independence approximation, not a multiple-testing correction
    estimated from the variants' joint return matrix.
    """
    n = len(daily_returns)
    sd = float(daily_returns.std(ddof=1))
    if n < 3 or sd == 0:
        return math.nan
    sr = float(daily_returns.mean() / sd)
    z = (daily_returns - daily_returns.mean()) / sd
    skew = float(np.mean(z ** 3))
    kurtosis = float(np.mean(z ** 4))
    euler = 0.5772156649015329
    if trials <= 1:
        benchmark_sr = 0.0
    else:
        expected_max_z = ((1 - euler) * norm.ppf(1 - 1 / trials)
                          + euler * norm.ppf(1 - 1 / (trials * math.e)))
        benchmark_sr = expected_max_z / math.sqrt(n - 1)
    denom_sq = 1 - skew * sr + ((kurtosis - 1) / 4) * sr * sr
    if denom_sq <= 0:
        return math.nan
    zscore = (sr - benchmark_sr) * math.sqrt(n - 1) / math.sqrt(denom_sq)
    return float(norm.cdf(zscore))


def metrics(strategy: np.ndarray, ew: np.ndarray, spy: np.ndarray,
            strategy_wealth: np.ndarray, ew_wealth: np.ndarray,
            spy_wealth: np.ndarray, trials: int, seed: int,
            bootstrap_draws: int, block: int) -> dict[str, float]:
    n = len(strategy)
    wealth = strategy_wealth / strategy_wealth[0]
    ew_norm = ew_wealth / ew_wealth[0]
    spy_norm = spy_wealth / spy_wealth[0]
    total = float(np.prod(1 + strategy) - 1)
    cagr = float((1 + total) ** (TRADING_DAYS / n) - 1) if 1 + total > 0 else math.nan
    vol = float(strategy.std(ddof=1) * math.sqrt(TRADING_DAYS))
    sharpe = float(strategy.mean() / strategy.std(ddof=1) * math.sqrt(TRADING_DAYS)) if strategy.std(ddof=1) else math.nan
    downside = float(np.sqrt(np.mean(np.minimum(strategy, 0) ** 2)))
    sortino = float(strategy.mean() / downside * math.sqrt(TRADING_DAYS)) if downside else math.nan
    mdd, dd_duration, _ = max_drawdown(wealth)
    loss = -strategy
    var95 = float(np.quantile(loss, 0.95, method="linear"))
    es95 = float(loss[loss >= var95].mean())
    active_ew = strategy - ew
    active_spy = strategy - spy

    def capm(bench: np.ndarray) -> tuple[float, float, float]:
        cov = float(np.cov(strategy, bench, ddof=1)[0, 1])
        var = float(np.var(bench, ddof=1))
        beta = cov / var if var else math.nan
        alpha = float((strategy.mean() - beta * bench.mean()) * TRADING_DAYS) if math.isfinite(beta) else math.nan
        corr = float(np.corrcoef(strategy, bench)[0, 1]) if strategy.std() and bench.std() else math.nan
        return beta, alpha, corr

    te = float(active_ew.std(ddof=1) * math.sqrt(TRADING_DAYS))
    ir = float(active_ew.mean() * TRADING_DAYS / te) if te else math.nan
    # Non-overlapping five-session blocks, anchored at the first in-period row.
    five_n = n // 5
    wins = 0
    for i in range(five_n):
        sl = slice(i * 5, (i + 1) * 5)
        wins += int(np.prod(1 + strategy[sl]) > np.prod(1 + ew[sl]))
    beta_spy, alpha_spy, corr_spy = capm(spy)
    beta_ew, alpha_ew, corr_ew = capm(ew)
    rng = np.random.default_rng(seed)
    return {
        "n": n, "total": total, "cagr": cagr, "vol": vol,
        "sharpe": sharpe, "sortino": sortino, "maxdd": mdd,
        "dd_duration": dd_duration, "var95": var95, "es95": es95,
        "beta_spy": beta_spy, "alpha_spy": alpha_spy, "corr_spy": corr_spy,
        "beta_ew": beta_ew, "alpha_ew": alpha_ew, "corr_ew": corr_ew,
        "te": te, "ir": ir, "five_win": wins / five_n if five_n else math.nan,
        "five_n": five_n,
        "excess_t": float(active_ew.mean() / (active_ew.std(ddof=1) / math.sqrt(n))) if n > 1 and active_ew.std(ddof=1) else math.nan,
        "bootstrap_p": circular_block_p(active_ew, block, bootstrap_draws, rng),
        "dsr": deflated_sharpe(strategy, trials),
        "excess_total": float(np.prod(1 + strategy) - np.prod(1 + ew)),
        "wealth": wealth, "ew_wealth": ew_norm, "spy_wealth": spy_norm,
        "drawdown": max_drawdown(wealth)[2],
        "rolling_excess": np.r_[np.full(62, np.nan),
                                 np.array([np.prod(1 + active_ew[i-62:i+1]) - 1
                                           for i in range(62, n)])],
    }


def pct(x: float) -> str:
    return "—" if not math.isfinite(x) else f"{x:.2%}"


def num(x: float, digits: int = 2) -> str:
    return "—" if not math.isfinite(x) else f"{x:.{digits}f}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--append", type=Path, action="append", default=[],
                        help="additional CSV segment(s), e.g. separately run official windows")
    parser.add_argument("--outdir", type=Path, default=Path("evaluation"))
    parser.add_argument("--date-col", default="date")
    parser.add_argument("--ew-col", default="ew")
    parser.add_argument("--spy-col", default="spy")
    parser.add_argument("--strategies", nargs="*", help="strategy columns; default: all except date/EW/SPY")
    parser.add_argument("--trials", type=int, default=44, help="total strategies/variants tried, including tested candidate")
    parser.add_argument("--seed", type=int, default=3666)
    parser.add_argument("--bootstrap-draws", type=int, default=5000)
    parser.add_argument("--block-days", type=int, default=10)
    args = parser.parse_args()
    if args.trials < 1 or args.bootstrap_draws < 1 or args.block_days < 1:
        parser.error("trials, bootstrap-draws, and block-days must be positive")
    dates, vals = read_csv(args.csv, args.date_col)
    for extra in args.append:
        extra_dates, extra_vals = read_csv(extra, args.date_col)
        if set(extra_vals) != set(vals):
            parser.error(f"columns in appended file {extra} differ from {args.csv}")
        dates.extend(extra_dates)
        for name in vals:
            vals[name] = np.r_[vals[name], extra_vals[name]]
    if dates != sorted(dates) or len(set(dates)) != len(dates):
        parser.error("combined CSV segments must have unique dates")
    order = np.argsort(dates)
    dates = [dates[i] for i in order]
    vals = {name: arr[order] for name, arr in vals.items()}
    for col in (args.ew_col, args.spy_col):
        if col not in vals:
            parser.error(f"missing benchmark column '{col}'")
    strategies = args.strategies or [c for c in vals if c not in (args.ew_col, args.spy_col)]
    if not strategies or any(c not in vals for c in strategies):
        parser.error("specify at least one valid strategy column")
    wealths = {c: vals[c] for c in vals}
    rets = {c: wealth_returns(v, dates) for c, v in wealths.items()}
    args.outdir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, dict[str, float]]] = {}
    period_dates: dict[str, list[str]] = {}
    for pidx, (period, (first, last)) in enumerate(PERIODS.items()):
        # Include one pre-period row to calculate the first in-period close-to-close return.
        idx = [i for i, d in enumerate(dates) if first <= d <= last]
        if not idx:
            continue
        start = idx[0] - 1 if idx[0] > 0 else idx[0]
        use = np.arange(start, idx[-1] + 1)
        period_dates[period] = [dates[i] for i in use]
        results[period] = {}
        for sidx, strategy in enumerate(strategies):
            # Drop leading pre-period return from the metric sample.
            r = rets[strategy][use][1:] if use[0] < idx[0] else rets[strategy][use]
            ew = rets[args.ew_col][use][1:] if use[0] < idx[0] else rets[args.ew_col][use]
            spy = rets[args.spy_col][use][1:] if use[0] < idx[0] else rets[args.spy_col][use]
            sw = wealths[strategy][use]
            ewv = wealths[args.ew_col][use]
            spyv = wealths[args.spy_col][use]
            if use[0] < idx[0]:
                sw, ewv, spyv = sw[1:], ewv[1:], spyv[1:]
            if np.any(~np.isfinite(np.r_[r, ew, spy])):
                raise ValueError(f"missing returns in {period}/{strategy}; check input coverage and columns")
            results[period][strategy] = metrics(r, ew, spy, sw, ewv, spyv,
                                                args.trials, args.seed + pidx * 100 + sidx,
                                                args.bootstrap_draws, args.block_days)

    if not results:
        raise ValueError("input has no observations within the preregistered periods")
    make_charts(args.outdir, results, strategies)
    write_report(args.outdir / "EVALUATION.md", results, strategies, args)
    print(f"Evaluated {len(strategies)} strategy column(s) across {len(results)} period(s); outputs: {args.outdir.resolve()}")


def make_charts(outdir: Path, results: dict, strategies: list[str]) -> None:
    periods = list(results)
    colors = plt.get_cmap("tab10")
    fig, axes = plt.subplots(len(periods), 1, figsize=(11, 3.4 * len(periods)), squeeze=False)
    for ax, period in zip(axes[:, 0], periods):
        for i, s in enumerate(strategies):
            m = results[period][s]
            ax.plot(m["wealth"], label=s, color=colors(i), linewidth=1.5)
        first = results[period][strategies[0]]
        ax.plot(first["ew_wealth"], label="EW30", color="black", linewidth=1.3, linestyle="--")
        ax.plot(first["spy_wealth"], label="SPY", color="gray", linewidth=1.2, linestyle=":")
        ax.set_title(f"{period}: cumulative wealth"); ax.set_ylabel("Growth of $1"); ax.grid(alpha=.25)
    axes[-1, 0].set_xlabel("Daily observations within period")
    axes[0, 0].legend(ncol=min(5, len(strategies) + 2), fontsize=8)
    fig.tight_layout(); fig.savefig(outdir / "cumulative_equity.png", dpi=180); plt.close(fig)

    fig, axes = plt.subplots(len(periods), 1, figsize=(11, 3.0 * len(periods)), squeeze=False)
    for ax, period in zip(axes[:, 0], periods):
        for i, s in enumerate(strategies):
            ax.plot(results[period][s]["drawdown"], label=s, color=colors(i), linewidth=1.25)
        ax.axhline(0, color="black", linewidth=.6); ax.set_title(f"{period}: drawdown from running peak")
        ax.set_ylabel("Drawdown"); ax.grid(alpha=.25)
    axes[-1, 0].set_xlabel("Daily observations within period")
    fig.tight_layout(); fig.savefig(outdir / "drawdown.png", dpi=180); plt.close(fig)

    fig, axes = plt.subplots(len(periods), 1, figsize=(11, 3.0 * len(periods)), squeeze=False)
    for ax, period in zip(axes[:, 0], periods):
        for i, s in enumerate(strategies):
            ax.plot(results[period][s]["rolling_excess"], label=s, color=colors(i), linewidth=1.25)
        ax.axhline(0, color="black", linewidth=.7); ax.set_title(f"{period}: rolling 63-session compounded excess vs EW30")
        ax.set_ylabel("63-session excess"); ax.grid(alpha=.25)
    axes[-1, 0].set_xlabel("Daily observations within period")
    fig.tight_layout(); fig.savefig(outdir / "rolling_63d_excess.png", dpi=180); plt.close(fig)

    x = np.arange(len(periods)); width = .8 / len(strategies)
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, s in enumerate(strategies):
        v = [results[p][s]["excess_total"] * 100 for p in periods]
        ax.bar(x + (i - (len(strategies)-1)/2) * width, v, width, label=s, color=colors(i))
    ax.axhline(0, color="black", linewidth=.8); ax.set_xticks(x, periods)
    ax.set_ylabel("Difference in cumulative return vs EW30 (percentage points)")
    ax.set_title("Cumulative excess return by fixed period"); ax.legend()
    ax.grid(axis="y", alpha=.25); fig.tight_layout()
    fig.savefig(outdir / "excess_return_by_period.png", dpi=180); plt.close(fig)


def write_report(path: Path, results: dict, strategies: list[str], args) -> None:
    lines = ["# Daily return evaluation", "", f"Input: `{args.csv}`" + (" plus " + ", ".join(f"`{p}`" for p in args.append) if args.append else "") + f". EW benchmark: `{args.ew_col}`; market benchmark: `{args.spy_col}`. Trials for DSR: **{args.trials}**. Bootstrap: circular {args.block_days}-session blocks, {args.bootstrap_draws:,} draws, seed {args.seed} (period and strategy offsets applied).", ""]
    for period, per in results.items():
        lines += [f"## {period}", "", "| Strategy | Total | CAGR | Vol | Sharpe | Sortino | Max DD | DD duration (days) | VaR95 | ES95 | β SPY | α SPY (ann.) | ρ SPY | β EW | α EW (ann.) | ρ EW | TE | IR | 5d win % | Excess t | Block p | DSR |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for s in strategies:
            m = per[s]
            cells = [s, pct(m["total"]), pct(m["cagr"]), pct(m["vol"]), num(m["sharpe"]), num(m["sortino"]), pct(m["maxdd"]), str(int(m["dd_duration"])), pct(m["var95"]), pct(m["es95"]), num(m["beta_spy"]), pct(m["alpha_spy"]), num(m["corr_spy"]), num(m["beta_ew"]), pct(m["alpha_ew"]), num(m["corr_ew"]), pct(m["te"]), num(m["ir"]), pct(m["five_win"]), num(m["excess_t"]), num(m["bootstrap_p"], 3), pct(m["dsr"])]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    lines += ["## Reading the results", ""]
    if "heat50" in strategies:
        periods = list(results)
        differences = [results[p]["heat50"]["excess_total"] for p in periods]
        directions = ", ".join(f"{p} {pct(x)}" for p, x in zip(periods, differences))
        sig = [p for p in periods if results[p]["heat50"]["bootstrap_p"] < .05]
        sig_text = ("The block-bootstrap test is below 5% in " + ", ".join(sig) + ".") if sig else "no heat50 block-bootstrap p-value is below 5%, so these observed differences do not establish statistically reliable outperformance."
        lines.append(f"Heat50 cumulative return relative to EW30 is {directions}. The sign changes across periods, and {sig_text} The same tables show pressure-only and neighbour-average results, so the heat blend should be judged against both the benchmark and its simpler controls; one favourable subperiod alone is not evidence of a persistent edge.")
    else:
        lines.append("Compare each strategy's return and risk with EW30 in each fixed period. A positive excess return is descriptive; evidence of reliable outperformance also requires the dependence-aware bootstrap test and must be read in light of the number of variants explored.")
    lines += ["", "## Validation design", "", "The evaluation periods were fixed before inspecting these outputs: IS 2020-11-27–2022-12-30, OOS1 2023-01-03–2024-02-23, and OOS2 2024-12-06–2025-12-31. Only IS is suitable for selecting among candidates; OOS1 and OOS2 are held-out checks and are not used to retune parameters. For each strategy and period, report daily-return diagnostics, a conventional excess-return t-statistic, and a two-sided circular 10-session block-bootstrap test with 5,000 draws against zero mean excess return versus EW30. Because roughly 44 or more signal and portfolio variants were explored across the broader research process, the DSR uses a trial count of 44 by default to account approximately for selection; this independent-trial adjustment is a sensitivity summary and cannot recover dependence across trials. No outperformance claim is made from a positive point estimate alone.", "", "## Usage", "", "A pivot equity CSV with `date`, one or more strategy wealth-index columns, `ew`, and `spy` can be evaluated in one command from this folder:", "", "```powershell", "py -3 evaluate.py path\\to\\pivot_equity.csv --outdir path\\to\\evaluation", "```", "", "Strategy columns are inferred automatically; pass `--strategies candidate_a candidate_b` to select them, `--trials 44` to set the documented search count, or repeat `--append another.csv` for separately initialized windows. The output folder receives this report and all four PNG charts. The date column must be ascending and unique, wealth indexes finite and positive, and a gap greater than 10 calendar days resets the wealth series to its $1 baseline.", "", "## Definitions", "", "Returns are computed from adjacent wealth observations; at a gap longer than 10 calendar days the input is treated as a separately initialized wealth segment and reset to its $1 base. Annualisation uses 252 sessions. Volatility and Sharpe use sample standard deviation and a zero risk-free rate. Sortino uses the root mean square of negative daily returns with a zero target. Maximum drawdown is the worst peak-to-trough decline; duration is the longest consecutive daily span below a running peak before recovery. Historical VaR95 is the 95th percentile of daily loss (so positive means loss); ES95 is the average loss at or beyond that cutoff. CAPM alpha is the annualised arithmetic daily intercept against each benchmark. Tracking error and information ratio use daily strategy-minus-EW30 returns. Five-session win rate uses non-overlapping blocks anchored at the period start and compares compounded returns. The excess-return t-stat is the ordinary two-sided daily-mean statistic and does not adjust for serial dependence.", "", f"The bootstrap p-value resamples circular {args.block_days}-day blocks from demeaned excess returns under the null, retaining local dependence approximately; a plus-one correction avoids zero p-values. DSR is the estimated probability that the strategy Sharpe exceeds the expected maximum Sharpe across {args.trials} independent trials, using observed sample skewness and kurtosis following Bailey and López de Prado (2014). The independent-trial approximation cannot model correlation among historical variants and does not replace a joint, fully documented trial return matrix.", "", "Charts: `cumulative_equity.png`, `drawdown.png`, `rolling_63d_excess.png`, and `excess_return_by_period.png`.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
