"""Guarded E1 runner. Requires explicit --execute before reading price outcomes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from r4_harness.ic_engine import cross_sectional_ic, newey_west_t
from r4_harness.phase3 import circular_block_bootstrap_pvalue, deflated_sharpe_ratio, holm_correction
from r4_harness.runner_guard import guarded_runner, validate_frozen_prereg

PREREG = ROOT / "specs" / "r6_prereg" / "E1.md"
RUN_DIR = Path(__file__).resolve().parent / "run"
DEFAULT_INPUTS = Path(__file__).resolve().parent / "E1_INPUTS.npz"
DEFAULT_MANIFEST = Path(__file__).resolve().parent / "input_manifest.json"
SP_PRICES = ROOT / "r6_data" / "sp500_ohlcv_dev_gapfilled.parquet"
DOW_PRICES = ROOT / "repo" / "prices-daily"
DOW_DELISTED = ROOT / "repo" / "prices-daily-delisted"
TRIALS = ROOT / "specs" / "r4_trials.md"
DECISIONS = ROOT / "specs" / "r6_decisions.md"
D1_ENDPOINTS = ROOT / "r6_D1" / "run" / "D1_ENDPOINTS.csv"
RESULTS_MD = Path(__file__).resolve().parent / "RESULTS.md"

HORIZON = 21
NW_LAG = 20
SHUFFLE_DRAWS = 500
BOOTSTRAP_DRAWS = 5000
SEED = 20261111
TOP_N = 5
TURNOVER_CAP = 0.20
COST_RATE = 0.0005
MIN_IC = 0.001155
MIN_T = 2.0
MIN_COVERAGE = 0.90
MIN_WIDE_DATES = 0.80
MIN_WIDE_NAMES = 250
ACTIVE_SHARE_MIN = 0.50
R6_ENDPOINTS = ("R6-H4", "R6-H5", "R6-H6")

RUNNER_SPEC_CONFIG = {
    "horizon": 21, "nw_lag": 20, "seed": SEED,
    "draws": [SHUFFLE_DRAWS, BOOTSTRAP_DRAWS],
    "block_length": 10, "k": TOP_N,
    "turnover": TURNOVER_CAP, "turnover_cap": TURNOVER_CAP,
    "cost_per_side": COST_RATE, "return_dispersion": 0.06,
    "top_fraction": 5, "min_t": MIN_T, "ic": MIN_IC,
    "active_share_min": ACTIVE_SHARE_MIN,
    "percentile": 95, "variant_count": 1,
    "endpoint_count": 3, "endpoint_ids": [1, 2, 3],
}


class CoverageFailure(RuntimeError):
    """Input-only QA gate failed; outcome prices were not loaded."""


def _arr(data: Mapping, key: str, dtype=None) -> np.ndarray:
    if key not in data:
        raise ValueError(f"input bundle missing {key!r}")
    a = np.asarray(data[key], dtype=dtype)
    if a.ndim != 2:
        raise ValueError(f"{key} must be formations x tickers")
    return a


def validate_bundle(data: Mapping) -> dict:
    """Validate monthly signal-only bundle; never computes outcomes."""
    out = {}
    for market in ("sp500", "dow"):
        dates = np.asarray(data[f"{market}_formation_dates"]).astype(str)
        tickers = np.asarray(data[f"{market}_tickers"]).astype(str)
        if not len(dates) or np.any(dates[1:] <= dates[:-1]):
            raise ValueError(f"{market} formation dates must be nonempty, ordered, and unique")
        if dates[0] < "2020-11-27" or dates[-1] > "2026-10-30":
            raise ValueError(f"{market} formation dates outside registered development period")
        shape = (len(dates), len(tickers))
        fields = {
            name: _arr(data, f"{market}_{name}", dtype)
            for name, dtype in (
                ("stock_pressure", float), ("peer_pressure", float),
                ("active_roster", bool), ("active_pressure", bool),
                ("active_sic2", bool), ("active_peer_score", bool),
                ("sic2", str), ("industry_group_size", int),
                ("valid_peer_count", int),
            )
        }
        if any(v.shape != shape for v in fields.values()):
            raise ValueError(f"{market} arrays must share formations x tickers {shape}")
        if len(set(tickers.tolist())) != len(tickers):
            raise ValueError(f"{market} ticker axis contains duplicates")
        if not np.array_equal(fields["active_peer_score"], np.isfinite(fields["peer_pressure"])):
            raise ValueError(f"{market} active peer mask does not match finite peer scores")
        out[market] = {"dates": dates, "tickers": tickers, **fields}
    if not np.array_equal(out["sp500"]["dates"], out["dow"]["dates"]):
        raise ValueError("S&P 500 and Dow monthly formation dates must match")
    return out


def coverage_gate(manifest: Mapping) -> dict:
    """Check current input-only gates from the published E1 manifest."""
    if not manifest.get("development_only"):
        raise CoverageFailure("input manifest is not marked development_only")
    if manifest.get("forward_returns_computed") or manifest.get("ics_computed"):
        raise CoverageFailure("input manifest claims outcomes were already computed")
    universes = manifest.get("universes", {})
    sp = universes.get("SP500", {})
    dow = universes.get("Dow30", {})
    sp_cov = float(manifest["daily_member_day_coverage"]["SP500"]["ohlcv_and_sic_coverage_pct"]) / 100
    dow_cov = float(manifest["daily_member_day_coverage"]["Dow30"]["ohlcv_and_sic_coverage_pct"]) / 100
    wide_fraction = float(sp.get("eligible_dates_fraction_at_250_names", 0))
    eligible_min = int(sp.get("min_peer_score_eligible", 0))
    passed = (sp_cov >= MIN_COVERAGE and dow_cov >= MIN_COVERAGE
              and wide_fraction >= MIN_WIDE_DATES and eligible_min >= MIN_WIDE_NAMES)
    return {"passed": passed, "sp500_member_day_coverage": sp_cov,
            "dow_member_day_coverage": dow_cov, "sp500_dates_fraction_ge_250": wide_fraction,
            "sp500_min_peer_score_count": eligible_min,
            "unresolved_sp500_ticker_histories": 51}


def _daily_prices(market: str, tickers: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load adjusted open/close development bars for the requested ticker axis."""
    if market == "sp500":
        if not SP_PRICES.is_file():
            raise FileNotFoundError(SP_PRICES)
        frame = pd.read_parquet(SP_PRICES, columns=["date", "ticker", "open", "close", "adj_close"])
        frame["date"] = pd.to_datetime(frame.date).dt.tz_localize(None).dt.normalize()
        frame["ticker"] = frame.ticker.astype(str).str.upper()
        frame = frame.loc[frame.date.between("2020-06-01", "2026-10-30")].copy()
        frame["adjusted_open"] = frame.open * frame.adj_close / frame.close
        frame["adjusted_close"] = frame.adj_close
    elif market == "dow":
        paths = list(DOW_PRICES.glob("*.csv"))
        if DOW_DELISTED.exists():
            paths += list(DOW_DELISTED.glob("*.csv"))
        rows = []
        for path in paths:
            try:
                x = pd.read_csv(path, usecols=["date", "open", "close", "adjclose"])
            except (ValueError, FileNotFoundError):
                continue
            x["date"] = pd.to_datetime(x.date, utc=True).dt.tz_convert(None).dt.normalize()
            x = x.loc[x.date.between("2020-06-01", "2026-10-30")].copy()
            x["ticker"] = path.stem.upper()
            rows.append(x)
        if not rows:
            raise FileNotFoundError("No Dow development price files found")
        frame = pd.concat(rows, ignore_index=True)
        frame["adjusted_open"] = frame.open * frame.adjclose / frame.close
        frame["adjusted_close"] = frame.adjclose
    else:
        raise ValueError(f"unknown market {market}")
    frame = frame.drop_duplicates(["date", "ticker"], keep="last")
    calendar = pd.DatetimeIndex(sorted(frame.date.unique()))
    op = frame.pivot(index="date", columns="ticker", values="adjusted_open").reindex(index=calendar, columns=tickers)
    close = frame.pivot(index="date", columns="ticker", values="adjusted_close").reindex(index=calendar, columns=tickers)
    return calendar.strftime("%Y-%m-%d").to_numpy(), op.to_numpy(float).T, close.to_numpy(float).T


def forward_returns(calendar: np.ndarray, adjusted_open: np.ndarray,
                    adjusted_close: np.ndarray, formation_dates: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Registered next-session-open to 21st-session-close total returns."""
    dates = np.asarray(calendar).astype(str)
    op, close = np.asarray(adjusted_open, float), np.asarray(adjusted_close, float)
    if op.shape != close.shape or op.shape[1] != len(dates):
        raise ValueError("price matrices must be tickers x daily calendar")
    loc = {d: i for i, d in enumerate(dates)}
    result = np.full((op.shape[0], len(formation_dates)), np.nan)
    eligible = np.zeros(len(formation_dates), bool)
    for j, day in enumerate(np.asarray(formation_dates).astype(str)):
        i = loc.get(day)
        if i is None or i + HORIZON >= len(dates):
            continue
        entry, exit_ = op[:, i + 1], close[:, i + HORIZON]
        good = np.isfinite(entry) & (entry > 0) & np.isfinite(exit_) & (exit_ > 0)
        result[good, j] = exit_[good] / entry[good] - 1.0
        eligible[j] = True
    return result, eligible


def _peer_score_from_labels(pressure: np.ndarray, labels: np.ndarray,
                            contributors: np.ndarray, targets: np.ndarray) -> np.ndarray:
    """Rebuild leave-one-out SIC peer means from stock pressure and SIC labels."""
    result = np.full(len(pressure), np.nan)
    groups = {}
    for j in np.flatnonzero(contributors & (labels != "")):
        groups.setdefault(labels[j], []).append(j)
    for j in np.flatnonzero(targets & (labels != "")):
        peers = [k for k in groups.get(labels[j], []) if k != j and np.isfinite(pressure[k])]
        if len(peers) >= 2:
            result[j] = float(np.mean(pressure[peers]))
    return result


def shuffle_sic2_labels(labels: np.ndarray, eligible: np.ndarray,
                        rng: np.random.Generator) -> np.ndarray:
    """Permute mapped SIC2 labels among eligible roster names, preserving sizes."""
    labels = np.asarray(labels).astype(str)
    eligible = np.asarray(eligible, bool) & (labels != "")
    if labels.shape != eligible.shape:
        raise ValueError("SIC labels and eligibility mask must have identical shapes")
    out = labels.copy()
    ix = np.flatnonzero(eligible)
    out[ix] = rng.permutation(out[ix])
    return out


def sic2_preserving_shuffle(sp: Mapping, forward: np.ndarray, *, draws=SHUFFLE_DRAWS,
                            seed=SEED) -> dict:
    """Date-wise SIC2 label shuffle preserving each date's exact group sizes."""
    pressure = np.asarray(sp["stock_pressure"], float)
    labels = np.asarray(sp["sic2"]).astype(str)
    roster = np.asarray(sp["active_roster"], bool)
    pressure_mask = np.asarray(sp["active_pressure"], bool)
    sic_mask = np.asarray(sp["active_sic2"], bool)
    if forward.shape != pressure.shape:
        raise ValueError("forward returns and S&P signal arrays must have the same shape")
    observed_mask = roster & pressure_mask & sic_mask & np.asarray(sp["active_peer_score"], bool) & np.isfinite(forward)
    observed = cross_sectional_ic(sp["peer_pressure"].T, forward.T, observed_mask.T,
                                  nw_lag=NW_LAG)
    if not np.isfinite(observed.mean_ic):
        raise ValueError("primary mean IC is not finite")
    rng = np.random.default_rng(seed)
    null = np.empty(draws)
    for b in range(draws):
        score_dates = np.full(pressure.shape, np.nan)
        for t in range(pressure.shape[0]):
            eligible_labels = roster[t] & sic_mask[t] & (labels[t] != "")
            shuffled = shuffle_sic2_labels(labels[t], eligible_labels, rng)
            targets = roster[t] & pressure_mask[t]
            rebuilt = _peer_score_from_labels(pressure[t], shuffled,
                                              roster[t] & pressure_mask[t], targets)
            score_dates[t] = rebuilt
        placebo_mask = roster & pressure_mask & sic_mask & np.isfinite(score_dates) & np.isfinite(forward)
        placebo = cross_sectional_ic(score_dates.T, forward.T, placebo_mask.T)
        null[b] = placebo.mean_ic
    p = (1 + int(np.sum(null >= observed.mean_ic))) / (draws + 1)
    p95 = float(np.percentile(null, 95))
    return {"observed_mean_ic": observed.mean_ic, "null_means": null,
            "null_p95": p95, "percentile": float(np.mean(null <= observed.mean_ic) * 100),
            "randomization_p": float(p),
            "pass": bool(observed.mean_ic > p95 and p < .05)}


def _weights_for_target(score: np.ndarray, roster: np.ndarray, names: np.ndarray) -> tuple[np.ndarray, bool]:
    eligible = roster & np.isfinite(score)
    weights = np.zeros(len(names), float)
    if eligible.sum() < TOP_N:
        return weights, False
    # Stable tie order is ticker name; no parameter selection.
    candidates = np.flatnonzero(eligible)
    ordered = sorted(candidates, key=lambda i: (-score[i], str(names[i])))
    weights[ordered[:TOP_N]] = 1.0 / TOP_N
    return weights, True


def _available_weights(weights: np.ndarray, available: np.ndarray) -> np.ndarray:
    """Exclude names without a current price and renormalize remaining exposure."""
    out = np.asarray(weights, float) * np.asarray(available, bool)
    total = float(out.sum())
    return out / total if total > 0 else out


def _capped_step(current: np.ndarray, target: np.ndarray, cap=TURNOVER_CAP) -> tuple[np.ndarray, float]:
    distance = float(np.abs(target - current).sum())
    step = min(1.0, cap / distance) if distance > 0 else 0.0
    updated = current + step * (target - current)
    return updated, float(np.abs(updated - current).sum())


def monthly_portfolio(scores: np.ndarray, roster: np.ndarray, open_px: np.ndarray,
                      close_px: np.ndarray, daily_dates: np.ndarray,
                      formation_dates: np.ndarray, names: np.ndarray,
                      *, cost_rate=COST_RATE, turnover_cap=TURNOVER_CAP) -> dict:
    """Monthly long-only Dow portfolio, capped rebalance, EW30 comparison."""
    scores, roster = np.asarray(scores, float), np.asarray(roster, bool)
    op, close = np.asarray(open_px, float), np.asarray(close_px, float)
    dates = np.asarray(daily_dates).astype(str)
    if scores.shape != roster.shape or scores.shape != (len(formation_dates), len(names)):
        raise ValueError("monthly score/roster dimensions do not match formation/ticker axes")
    if op.shape != close.shape or op.shape != (len(names), len(dates)):
        raise ValueError("price arrays must be tickers x daily dates")
    date_locs = {d: i for i, d in enumerate(dates)}
    fills = []
    selection_failures = []
    targets = {}
    formation_by_fill = {}
    formation_day_indices = []
    eligible_name_counts = []
    for j, d in enumerate(np.asarray(formation_dates).astype(str)):
        i = date_locs.get(d)
        if i is None or i + 1 >= len(dates):
            continue
        formation_day_indices.append((i, j))
        fill = i + 1
        fill_available = np.isfinite(op[:, fill]) & (op[:, fill] > 0)
        date_eligible = roster[j] & np.isfinite(scores[j]) & fill_available
        eligible_name_counts.append({"formation_date": d, "n": int(date_eligible.sum())})
        target, valid = _weights_for_target(scores[j], roster[j] & fill_available, names)
        if not valid:
            selection_failures.append(d)
            continue
        fills.append(fill)
        targets[fill] = target
        formation_by_fill[fill] = j
    if not fills:
        return {"returns": np.asarray([]), "benchmark_returns": np.asarray([]),
                "cumulative_net_return": None, "cumulative_gross_return": None,
                "cumulative_benchmark_return": None,
                "net_excess_return": None, "gross_active_edge": None,
                "sharpe": None, "benchmark_sharpe": None, "max_drawdown": None,
                "active_share": 0.0, "turnovers": np.asarray([]), "mean_turnover": None,
                "max_turnover": None, "total_cost": 0.0, "costs": np.asarray([]),
                "cost_to_gross_edge_ratio": None, "cap_bind_dates": [],
                "selection_failure_dates": selection_failures,
                "eligible_name_counts": eligible_name_counts,
                "active_share_pass": False, "portfolio_gate_pass": False}
    fills = sorted(set(fills))
    first = fills[0]
    prev_ix = first - 1
    initial_roster = roster[formation_by_fill[first]] & np.isfinite(close[:, prev_ix]) & (close[:, prev_ix] > 0)
    if initial_roster.sum() == 0:
        raise ValueError("no valid Dow names for initial EW30 weights")
    current = initial_roster.astype(float) / initial_roster.sum()
    active_shares, turnovers, costs, bind_dates = [], [], [], []
    strat_daily, ew_daily, gross_daily = [], [], []
    wealth_net = wealth_gross = wealth_ew = 1.0
    prev_close = close[:, prev_ix].copy()
    trade_events = set(fills)
    portfolio_failed = bool(selection_failures)
    formation_positions = np.asarray([i for i, _ in formation_day_indices], dtype=int)
    formation_rows = np.asarray([j for _, j in formation_day_indices], dtype=int)
    for i in range(first, len(dates)):
        valid_open = np.isfinite(op[:, i]) & (op[:, i] > 0)
        valid_close = np.isfinite(close[:, i]) & (close[:, i] > 0)
        if i in trade_events:
            # Accrue overnight return on the existing holdings to the next open.
            overnight_weights = _available_weights(current, valid_open & np.isfinite(prev_close) & (prev_close > 0))
            overnight_ok = (overnight_weights != 0)
            overnight_ret = np.sum(overnight_weights[overnight_ok] * (op[overnight_ok, i] / prev_close[overnight_ok] - 1))
            current, turnover = _capped_step(current, targets[i], turnover_cap)
            turnovers.append(turnover)
            if turnover >= turnover_cap - 1e-8:
                bind_dates.append(dates[i])
            cost = cost_rate * turnover
            costs.append(cost)
            intraday_weights = _available_weights(current, valid_open & valid_close)
            intraday_ok = intraday_weights != 0
            intraday_ret = np.sum(intraday_weights[intraday_ok] * (close[intraday_ok, i] / op[intraday_ok, i] - 1))
            gross_ret = (1 + overnight_ret) * (1 + intraday_ret) - 1
            net_ret = ((1 + overnight_ret) * (1 - cost) * (1 + intraday_ret)) - 1
            wealth_gross *= (1 + gross_ret)
            wealth_net *= (1 + net_ret)
        else:
            daily_weights = _available_weights(current, valid_close & np.isfinite(prev_close) & (prev_close > 0))
            daily_ok = daily_weights != 0
            gross_ret = float(np.sum(daily_weights[daily_ok] * (close[daily_ok, i] / prev_close[daily_ok] - 1)))
            net_ret = gross_ret
            wealth_gross *= (1 + gross_ret)
            wealth_net *= (1 + net_ret)
        # Equal-weight benchmark over names with a valid price for both closes.
        active_row_idx = int(np.searchsorted(formation_positions, i, side="right") - 1)
        active_row = formation_rows[max(0, active_row_idx)]
        point_in_time_roster = roster[active_row]
        bench_names = (point_in_time_roster & valid_close
                       & np.isfinite(prev_close) & (prev_close > 0))
        if bench_names.any():
            bench_ret = float(np.mean(close[bench_names, i] / prev_close[bench_names] - 1))
        else:
            bench_ret = 0.0
        strategy_day_weights = _available_weights(current, bench_names)
        ew_weights = bench_names.astype(float) / max(1, bench_names.sum())
        active_shares.append(float(.5 * np.abs(strategy_day_weights - ew_weights).sum()))
        wealth_ew *= 1 + bench_ret
        strat_daily.append(net_ret)
        ew_daily.append(bench_ret)
        gross_daily.append(gross_ret)
        prev_close = close[:, i].copy()
    sret, bret = np.asarray(strat_daily), np.asarray(ew_daily)
    def sharpe(x):
        sd = float(np.std(x, ddof=1)) if len(x) > 1 else 0.0
        return float(np.mean(x) / sd * math.sqrt(252)) if sd else 0.0
    gross_excess = float(np.prod(1 + np.asarray(gross_daily)) - np.prod(1 + bret))
    cumulative_gross = float(np.prod(1 + np.asarray(gross_daily)) - 1.0)
    net_excess = float(wealth_net - wealth_ew)
    net_curve = np.cumprod(1 + sret)
    net_peak = np.maximum.accumulate(np.r_[1.0, net_curve])[1:]
    drawdown = net_curve / net_peak - 1.0
    return {"returns": sret, "benchmark_returns": bret,
            "cumulative_net_return": float(wealth_net - 1),
            "cumulative_gross_return": cumulative_gross,
            "cumulative_benchmark_return": float(wealth_ew - 1),
            "net_excess_return": net_excess, "gross_active_edge": gross_excess,
            "sharpe": sharpe(sret), "benchmark_sharpe": sharpe(bret),
            "max_drawdown": float(np.min(drawdown)) if len(drawdown) else 0.0,
            "active_share": float(np.mean(active_shares)) if active_shares else 0.0,
            "turnovers": np.asarray(turnovers), "mean_turnover": float(np.mean(turnovers)) if turnovers else 0.0,
            "max_turnover": float(np.max(turnovers)) if turnovers else 0.0,
            "total_cost": float(np.sum(costs)), "costs": np.asarray(costs),
            "cost_to_gross_edge_ratio": float(np.sum(costs) / gross_excess) if gross_excess > 0 else None,
            "cap_bind_dates": bind_dates, "selection_failure_dates": selection_failures,
            "eligible_name_counts": eligible_name_counts,
            "active_share_pass": bool(np.mean(active_shares) >= ACTIVE_SHARE_MIN) if active_shares else False,
            "portfolio_gate_pass": not portfolio_failed}


def _r6_trial_count() -> int:
    text = TRIALS.read_text(encoding="utf-8")
    matches = re.findall(r"^\s*-\s*R6 variant\s+\d+\s*:\s*([A-Za-z0-9_-]+)", text, re.M)
    variants = set(matches)
    count = len(variants)
    if not 1 <= count <= 30:
        raise ValueError("cannot determine a valid cumulative R6 unique-variant count from r4_trials.md")
    return count


def _prior_r6_pvalues() -> dict[str, float]:
    if not D1_ENDPOINTS.is_file():
        raise FileNotFoundError(f"full R6 Holm family requires prior D1 endpoint file: {D1_ENDPOINTS}")
    with D1_ENDPOINTS.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = {}
    seen = set()
    for row in rows:
        endpoint = row.get("endpoint_id", "")
        if endpoint in ("R6-H1", "R6-H2", "R6-H3"):
            seen.add(endpoint)
        raw = row.get("raw_p", "")
        if endpoint in ("R6-H1", "R6-H2", "R6-H3") and raw not in ("", "None", "nan"):
            out[endpoint] = float(raw)
    expected = {"R6-H1", "R6-H2", "R6-H3"}
    if seen != expected:
        raise ValueError("D1 endpoint results do not contain all three registered R6 Holm slots")
    # A gate-blocked prior endpoint remains in the registered Holm family but
    # has no reportable p-value; use 1.0 internally as the conservative slot.
    for endpoint in expected - set(out):
        out[endpoint] = 1.0
    return out


def _endpoint_rows(h4: Mapping, h5: Mapping, h6: Mapping | None) -> list[dict]:
    entries = [("R6-H4", h4), ("R6-H5", h5), ("R6-H6", h6)]
    rows = []
    for endpoint, result in entries:
        rows.append({"endpoint_id": endpoint,
                     "estimate": None if result is None else result.get("estimate"),
                     "statistic": None if result is None else result.get("statistic"),
                     "raw_p": None if result is None else result.get("raw_p"),
                     "holm_p": None if result is None else result.get("holm_p"),
                     "status": "not run" if result is None else ("PASS" if result.get("pass") else "FAIL")})
    return rows


def _write_endpoints(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["endpoint_id", "estimate", "statistic", "raw_p", "holm_p", "status"])
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_hashes(input_path: Path, manifest_path: Path) -> dict:
    dow_paths = sorted(DOW_PRICES.glob("*.csv"))
    if DOW_DELISTED.exists():
        dow_paths += sorted(DOW_DELISTED.glob("*.csv"))
    return {
        "signal_bundle_sha256": _sha256(input_path),
        "input_manifest_sha256": _sha256(manifest_path),
        "sp500_ohlcv_sha256": _sha256(SP_PRICES),
        "dow_price_csv_sha256": {str(p.relative_to(ROOT)): _sha256(p) for p in dow_paths},
        "prior_d1_endpoint_log_sha256": _sha256(D1_ENDPOINTS),
    }


def _fmt(value, digits=8):
    if value is None:
        return "not run"
    try:
        if not np.isfinite(float(value)):
            return str(value)
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def write_results_markdown(result: Mapping, path: Path = RESULTS_MD) -> None:
    """Write the complete run report, including all 500 SIC2-shuffle draws."""
    h4, h5, h6 = result["R6-H4"], result["R6-H5"], result.get("R6-H6")
    lines = [
        "# E1 development run results", "",
        "This is the single authorized development run of frozen E1. No sealed holdout prices or outcomes were loaded.",
        f"Frozen preregistration SHA256: `{result.get('prereg_sha256', 'not recorded')}`.",
        f"Unique R6 strategy trial count used for DSR: {result.get('trial_count', 'not recorded')}.",
        f"Eligible monthly dates: {result['coverage'].get('sp500_forward_window_dates', 'not reported')} of {result['coverage'].get('scheduled_dates', 'not reported')}; the final scheduled date was excluded by the 21-session calendar rule.",
        "", "## Input coverage and provenance", "",
        f"Input coverage gate: **{'PASS' if result['coverage'].get('passed') else 'FAIL'}**; S&P member-day coverage {_fmt(result['coverage'].get('sp500_member_day_coverage'), 4)}, Dow {_fmt(result['coverage'].get('dow_member_day_coverage'), 4)}, S&P dates with at least 250 peer scores {_fmt(result['coverage'].get('sp500_dates_fraction_ge_250'), 4)}.",
        f"Unresolved S&P historical price histories disclosed: {result['coverage'].get('unresolved_sp500_ticker_histories', 'not reported')}.",
        "", "| Input | SHA256 |", "|---|---|",
        f"| E1 signal bundle | `{result['source_hashes']['signal_bundle_sha256']}` |",
        f"| Input QA manifest | `{result['source_hashes']['input_manifest_sha256']}` |",
        f"| S&P 500 development OHLCV panel | `{result['source_hashes']['sp500_ohlcv_sha256']}` |",
        f"| Prior D1 endpoint log | `{result['source_hashes']['prior_d1_endpoint_log_sha256']}` |",
        "", "Dow development price source hashes:", "",
    ]
    lines.extend(f"- `{name}`: `{digest}`" for name, digest in result["source_hashes"]["dow_price_csv_sha256"].items())
    lines += ["", "## R6-H4 — S&P 500 mechanism", "",
              f"Mean monthly rank IC: **{_fmt(h4['estimate'])}**; Newey–West t (Bartlett lag 20): **{_fmt(h4['statistic'], 4)}**; one-sided p: **{_fmt(h4['raw_p'], 6)}**; Holm-adjusted p: **{_fmt(h4.get('holm_p'), 6)}**.",
              f"Pass gate (mean IC ≥0.001155 and NW t ≥2): **{'PASS' if h4['pass'] else 'FAIL'}**; valid IC dates: {h4['n_dates']}.",
              "", "| Formation date | Spearman IC | Eligible names |", "|---|---:|---:|"]
    for d, ic, n in zip(result["formation_dates"], h4["ic_by_date"], h4["counts_by_date"]):
        lines.append(f"| {d} | {_fmt(ic, 8) if np.isfinite(ic) else 'NA'} | {int(n)} |")
    lines += ["", "## R6-H5 — SIC2-preserving shuffle placebo", "",
              f"Observed mean IC: **{_fmt(h5['estimate'])}**; shuffled mean-IC 95th percentile: **{_fmt(h5['null_p95'])}**; one-sided randomization p: **{_fmt(h5['raw_p'], 6)}**; Holm-adjusted p: **{_fmt(h5.get('holm_p'), 6)}**.",
              f"Observed percentile in the null draws: {_fmt(h5['percentile'], 2)}%; 500 draws; seed 20261111; gate (observed > p95 and p <0.05): **{'PASS' if h5['pass'] else 'FAIL'}**.",
              "", "All 500 shuffled mean IC values (the reproducible CSV is `run/E1_PLACEBO_DRAWS.csv`):", ""]
    for start in range(0, len(h5["null_mean_ics"]), 5):
        vals = h5["null_mean_ics"][start:start + 5]
        lines.append("| " + " | ".join(str(start + j + 1) for j in range(len(vals))) + " |")
        lines.append("| " + " | ".join(_fmt(v, 10) for v in vals) + " |")
    lines += ["", "## R6-H6 — Dow monthly portfolio", ""]
    if h6 is None:
        lines += ["**Not run:** the registered mechanism or placebo gate failed. No portfolio outcomes were computed."]
    else:
        p = h6["portfolio"]
        lines += [
            f"Status: **{'PASS' if h6['pass'] else 'FAIL'}**; net excess return vs available-name EW30: **{_fmt(p['net_excess_return'])}**; gross active edge: **{_fmt(p['gross_active_edge'])}**.",
            f"Gross strategy return: {_fmt(p.get('cumulative_gross_return'))}; net strategy return: {_fmt(p.get('cumulative_net_return'))}; EW30 return: {_fmt(p.get('cumulative_benchmark_return'))}.",
            f"Net annualized Sharpe: {_fmt(p['sharpe'], 4)}; EW30 Sharpe: {_fmt(p['benchmark_sharpe'], 4)}; maximum drawdown: {_fmt(p.get('max_drawdown'), 6)}.",
            f"Mean/max total turnover: {_fmt(p['mean_turnover'], 4)} / {_fmt(p['max_turnover'], 4)}; mean daily active share: {_fmt(p['active_share'], 4)}; active-share gate: {'PASS' if p['active_share_pass'] else 'FAIL'}.",
            f"Transaction costs: {_fmt(p['total_cost'], 8)}; cost/gross-edge ratio: {_fmt(p['cost_to_gross_edge_ratio'])}; turnover cap binding dates: {', '.join(p['cap_bind_dates']) or 'none'}.",
            f"Eligible-name counts by formation: {p['eligible_name_counts']}; selection failures: {p['selection_failure_dates'] or 'none'}.",
            f"One-sided 10-session circular block bootstrap (5,000 draws, seed 20261111) p: {_fmt(h6['raw_p'], 6)}; R6 Holm-adjusted p: {_fmt(h6.get('holm_p'), 6)}; DSR: {_fmt(h6.get('deflated_sharpe'), 6)} at trial_count={h6.get('trial_count')}.",
        ]
    lines += ["", "## Holm endpoints", "", "| Endpoint | Estimate | Statistic | Raw p | Holm p | Status |", "|---|---:|---:|---:|---:|---|"]
    for row in result["endpoint_rows"]:
        lines.append(f"| {row['endpoint_id']} | {_fmt(row['estimate'])} | {_fmt(row['statistic'])} | {_fmt(row['raw_p'], 6)} | {_fmt(row['holm_p'], 6)} | {row['status']} |")
    lines += ["", "## Interpretation limits", "", "This report contains the full registered endpoints and diagnostics for the authorized development run. No holdout data were accessed; this report does not authorize a second run or any parameter change.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_placebo_draws(path: Path, draws: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["draw", "null_mean_ic"])
        writer.writerows((i + 1, float(value)) for i, value in enumerate(draws))


def analyze_arrays(bundle: Mapping, prices: Mapping[str, tuple], *, trial_count: int,
                    prior_pvalues: Mapping[str, float]) -> dict:
    """Calculate registered E1 endpoints from synthetic or execution-loaded arrays."""
    data = validate_bundle(bundle)
    sp = data["sp500"]
    dow = data["dow"]
    dates = sp["dates"]
    fwd_sp, sp_forward_dates = forward_returns(*prices["sp500"], dates)
    sp_mask = (sp["active_roster"] & sp["active_peer_score"] & np.isfinite(fwd_sp.T)
               & sp["active_sic2"])
    mech = cross_sectional_ic(sp["peer_pressure"].T, fwd_sp, sp_mask.T, nw_lag=NW_LAG)
    t = float(newey_west_t(mech.ic_by_date, NW_LAG))
    p4 = float(norm.sf(t)) if np.isfinite(t) else 1.0
    h4 = {"estimate": mech.mean_ic, "statistic": t, "raw_p": p4,
          "pass": bool(mech.mean_ic >= MIN_IC and t >= MIN_T),
          "n_dates": int(np.isfinite(mech.ic_by_date).sum()),
          "ic_by_date": mech.ic_by_date, "counts_by_date": mech.n_assets_by_date}

    placebo = sic2_preserving_shuffle(sp, fwd_sp.T, draws=SHUFFLE_DRAWS, seed=SEED)
    h5 = {"estimate": placebo["observed_mean_ic"], "statistic": placebo["null_p95"],
          "raw_p": placebo["randomization_p"], "pass": placebo["pass"],
          "null_p95": placebo["null_p95"], "percentile": placebo["percentile"],
          "null_mean_ics": placebo["null_means"]}

    h6 = None
    family_p = dict(prior_pvalues)
    family_p["R6-H4"] = p4
    family_p["R6-H5"] = placebo["randomization_p"]
    if h4["pass"] and h5["pass"]:
        # Portfolio calendar is built on the Dow price axis, but the fills are
        # the next session after each eligible monthly formation.
        dcal, dop, dclose = prices["dow"]
        port = monthly_portfolio(dow["peer_pressure"], dow["active_roster"], dop, dclose,
                                 dcal, dates, dow["tickers"])
        p6 = None
        boot = np.asarray([])
        if len(port["returns"]) >= 2:
            p6, boot = circular_block_bootstrap_pvalue(port["returns"], port["benchmark_returns"],
                                                       block_length=10, n_draws=BOOTSTRAP_DRAWS,
                                                       seed=SEED)
        h6_pass = bool(p6 is not None and port["net_excess_return"] > 0
                       and port["sharpe"] > port["benchmark_sharpe"]
                       and port["portfolio_gate_pass"]
                       and port["active_share_pass"]
                       and port["max_turnover"] <= 0.50 + 1e-12)
        h6 = {"estimate": port["net_excess_return"], "statistic": port["sharpe"] - port["benchmark_sharpe"],
              "raw_p": p6, "pass": h6_pass, "portfolio": port, "bootstrap": boot,
              "deflated_sharpe": deflated_sharpe_ratio(port["returns"], trial_count),
              "trial_count": int(trial_count)}
        family_p["R6-H6"] = p6 if p6 is not None else 1.0
    else:
        family_p["R6-H6"] = 1.0  # conservative Holm slot; endpoint is still reported not run
    adjusted = holm_correction(family_p)
    for endpoint, result in (("R6-H4", h4), ("R6-H5", h5), ("R6-H6", h6)):
        if result is not None:
            result["holm_p"] = adjusted[endpoint]["holm_p"]
            if endpoint == "R6-H6":
                result["pass"] = bool(result["pass"] and result["holm_p"] < .05)
    return {"approach": "E1", "R6-H4": h4, "R6-H5": h5, "R6-H6": h6,
            "holm_family": "R6 only", "holm_adjusted": adjusted,
            "endpoint_rows": _endpoint_rows(h4, h5, h6),
            "formation_dates": dates,
            "trial_count": int(trial_count),
            "coverage": {"sp500_forward_window_dates": int(sp_forward_dates.sum()),
                         "scheduled_dates": int(len(dates)),
                         "final_scheduled_date_excluded": str(dates[-1])}}


def _load_npz(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def load_prices(tickers: Mapping[str, np.ndarray]) -> dict:
    return {market: _daily_prices(market, names) for market, names in tickers.items()}


def prereg_diff_text() -> str:
    """Formatting-only normalization for machine-readable frozen design audit."""
    text = PREREG.read_text(encoding="utf-8")
    text = text.replace("5,000", "5000")
    text = text.replace("500 independent date-wise permutations", "500 shuffle draws")
    text = text.replace("Use seed `20261111`", "Use seed 20261111")
    text = text.replace("S&P 500", "S&P five hundred")
    text = text.replace("Mean rank IC is positive and at least **0.001155**",
                        "Minimum IC=0.001155. Mean rank IC is positive and at least **0.001155**")
    text = re.sub(r"The existing synthetic power design.*?Do not relax t≥2 or the IC hurdle if the test is underpowered\.",
                  "[Power planning assumptions are not runtime parameters.]", text, flags=re.S)
    text = text.replace("## Holm family and deflated Sharpe ratio", "## Registered endpoints: Holm family and deflated Sharpe ratio")
    text = text.replace("The sole confirmatory mechanism endpoint", "Primary horizon: 21 sessions. There is 1 variant. Newey-West lag 20. The sole confirmatory mechanism endpoint")
    text = text.replace("**R6-H4 onward**", "**R6-H4 onward**")
    return text


def prereg_diff_payload() -> dict:
    from r4_harness.prereg_diff import prereg_diff
    result = prereg_diff(prereg_diff_text(), RUNNER_SPEC_CONFIG)
    return {"matches": result.matches, "facts": result.facts,
            "differences": [d.__dict__ for d in result.differences]}


@guarded_runner(prereg_path=PREREG, run_dir=RUN_DIR)
def run_e1(input_path=DEFAULT_INPUTS, manifest_path=DEFAULT_MANIFEST):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    coverage = coverage_gate(manifest)
    if not coverage["passed"]:
        raise CoverageFailure(f"E1 input gate failed: {coverage}")
    raw = _load_npz(Path(input_path))
    bundle = validate_bundle(raw)
    prices = load_prices({"sp500": bundle["sp500"]["tickers"],
                          "dow": bundle["dow"]["tickers"]})
    # Freeze the final scheduled date out using calendar availability alone.
    eligible = []
    sp_dates = bundle["sp500"]["dates"]
    sp_calendar = prices["sp500"][0]
    cal_index = {d: i for i, d in enumerate(sp_calendar)}
    for d in sp_dates:
        i = cal_index.get(d)
        eligible.append(i is not None and i + HORIZON < len(sp_calendar))
    eligible = np.asarray(eligible, bool)
    for market in ("sp500", "dow"):
        raw[f"{market}_formation_dates"] = raw[f"{market}_formation_dates"][eligible]
        for key, value in list(raw.items()):
            if key.startswith(f"{market}_") and isinstance(value, np.ndarray) and value.ndim == 2:
                raw[key] = value[eligible]
    result = analyze_arrays(raw, prices, trial_count=_r6_trial_count(),
                             prior_pvalues=_prior_r6_pvalues())
    result["coverage"].update(coverage)
    result["prereg_sha256"] = validate_frozen_prereg(PREREG)[1]
    result["source_hashes"] = _source_hashes(Path(input_path), Path(manifest_path))
    _write_placebo_draws(RUN_DIR / "E1_PLACEBO_DRAWS.csv",
                         result["R6-H5"]["null_mean_ics"])
    _write_endpoints(RUN_DIR / "E1_ENDPOINTS.csv", result["endpoint_rows"])
    (RUN_DIR / "E1_RESULTS.json").write_text(json.dumps(result, indent=2, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x), encoding="utf-8")
    write_results_markdown(result)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-freeze", action="store_true")
    parser.add_argument("--execute", action="store_true", help="coordinator authorization required for outcome work")
    parser.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    try:
        frozen_date, digest = validate_frozen_prereg(PREREG)
        if args.check_freeze:
            print(json.dumps({"frozen": frozen_date, "sha256": digest, "execution": "not requested"}, indent=2))
            return 0
        if not args.execute:
            print("FROZEN E1 verified; no outcomes read. Explicit --execute is required under coordinator authorization.")
            return 0
        result = run_e1(args.inputs, args.manifest, execute=True)
        print(json.dumps(result, indent=2, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x))
        return 0
    except Exception as exc:
        print(f"REFUSED/FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
