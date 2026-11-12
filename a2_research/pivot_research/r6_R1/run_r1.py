"""Guarded implementation of frozen R1-V1; never run without --execute."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from r4_harness.phase3 import circular_block_bootstrap_pvalue, deflated_sharpe_ratio, holm_correction, newey_west_t
from r4_harness.prereg_diff import prereg_diff
from r4_harness.runner_guard import guarded_runner, validate_frozen_prereg

PREREG = ROOT / "specs/r6_prereg/R1.md"
INPUTS = HERE / "R1_INPUTS.npz"
COVERAGE = HERE / "formation_coverage.csv"
MANIFEST = HERE / "build_manifest.json"
RUN_DIR = HERE / "run"
HOLM_CONFIG = ROOT / "specs/r6_holm_family.json"
J1_RESULTS = ROOT / "r6_J1/RESULTS.md"
TRIALS = ROOT / "specs/r4_trials.md"
NW_LAG, SHUFFLE_DRAWS, BOOTSTRAP_DRAWS, SEED = 3, 500, 5000, 20261111
MIN_SP500_NAMES, TURNOVER_CAP, COST_PER_SIDE = 250, .50, .0005
RUNNER_SPEC_CONFIG = {
    "min_t": 2, "nw_lag": 3, "draws": [500, 5000], "percentile": 95,
    "ic_sd": .08, "seed": SEED, "horizon": 4,
    "active_share_min": .50, "cost_per_side": COST_PER_SIDE,
    "alpha": .05, "endpoint_ids": [1, 2, 3], "endpoint_count": 3,
}


def prereg_diff_payload():
    """Formatting-only thousands-separator normalization for harness parser."""
    text = PREREG.read_text(encoding="utf-8")
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
    return prereg_diff(text, RUNNER_SPEC_CONFIG)


class CoverageFailure(RuntimeError):
    pass


def check_coverage(frame) -> dict:
    """Input-only gate; fail before any forward price division or return series."""
    required = {"universe", "formation_date", "valid_flag_sic_next_month_bars"}
    if not required.issubset(frame.columns):
        raise CoverageFailure(f"coverage table lacks {sorted(required - set(frame.columns))}")
    sp = frame.loc[frame.universe.eq("sp500")].sort_values("formation_date")
    if len(sp) != 64:
        raise CoverageFailure(f"expected 64 S&P formation rows, got {len(sp)}")
    counts = sp.valid_flag_sic_next_month_bars.astype(int).to_numpy()
    if (counts < MIN_SP500_NAMES).any():
        raise CoverageFailure(f"coverage gate failed: minimum complete S&P names {counts.min()} < 250")
    return {"passed": True, "formations": len(sp), "minimum_names": int(counts.min()),
            "median_names": float(np.median(counts)), "eligible_name_counts": counts.tolist()}


def spread_series(payer, sic2, returns, eligible):
    vals, details = [], []
    for j in range(returns.shape[1]):
        sector_spreads = []
        for sector in sorted(set(sic2[:, j][eligible[:, j]].tolist()) - {""}):
            ix = eligible[:, j] & (sic2[:, j] == sector)
            p, n = ix & (payer[:, j] == 1), ix & (payer[:, j] == 0)
            if p.any() and n.any():
                sector_spreads.append(float(np.mean(returns[p, j]) - np.mean(returns[n, j])))
        vals.append(float(np.mean(sector_spreads)) if sector_spreads else np.nan)
        details.append(len(sector_spreads))
    return np.asarray(vals), np.asarray(details, dtype=int)


def shuffle_placebo(payer, sic2, returns, eligible, draws=SHUFFLE_DRAWS, seed=SEED):
    observed, groups = spread_series(payer, sic2, returns, eligible)
    observed_mean = float(np.nanmean(observed))
    rng = np.random.default_rng(seed)
    null = np.full(draws, np.nan)
    for b in range(draws):
        fake = payer.copy()
        for j in range(payer.shape[1]):
            for sector in sorted(set(sic2[:, j][eligible[:, j]].tolist()) - {""}):
                ix = np.flatnonzero(eligible[:, j] & (sic2[:, j] == sector))
                flags = payer[ix, j].copy()
                rng.shuffle(flags)
                fake[ix, j] = flags
        draw, _ = spread_series(fake, sic2, returns, eligible)
        null[b] = float(np.nanmean(draw))
    p = (1 + int(np.sum(null >= observed_mean))) / (draws + 1)
    return {"observed": observed_mean, "monthly_spreads": observed,
            "sector_group_counts": groups, "draws": null,
            "p95": float(np.nanquantile(null, .95)), "p": float(p),
            "pass": bool(observed_mean > np.nanquantile(null, .95) and p < .05)}


def mechanism(payer, sic2, returns, eligible):
    monthly, groups = spread_series(payer, sic2, returns, eligible)
    keep = np.isfinite(monthly)
    x = monthly[keep]
    tval = newey_west_t(x, NW_LAG)
    p = float(student_t.sf(tval, max(len(x) - 1, 1)))
    return {"monthly_spreads": monthly, "groups": groups, "mean": float(np.mean(x)) if len(x) else float("nan"),
            "nw_t": float(tval), "p": p, "n_months": int(len(x)),
            "pass": bool(len(x) >= 2 and np.mean(x) > 0 and tval >= 2.0)}


def stale_mark_return(last_close: float, current_close: float) -> float:
    """No close means zero return; a later valid close catches up from stale mark."""
    if not np.isfinite(current_close) or current_close <= 0:
        return 0.0
    if not np.isfinite(last_close) or last_close <= 0:
        return 0.0
    return float(current_close / last_close - 1.0)


def target_weights(names, member, status, payer, count, opened, daily_roster, j):
    """Use opening-price benchmark availability for n and payer eligibility."""
    open_ok = np.isfinite(opened) & (opened > 0)
    benchmark_available = daily_roster & open_ok
    ids = np.flatnonzero(benchmark_available)
    target = np.zeros(len(names), dtype=float)
    n_benchmark = int(len(ids))
    k = min(15, n_benchmark // 2)
    candidates = [i for i in ids if member[i, j] and status[i, j] and payer[i, j] == 1]
    candidates.sort(key=lambda i: (-int(count[i, j]), str(names[i])))
    selected = candidates[:k] if len(candidates) >= k else candidates
    if selected:
        target[selected] = 1.0 / len(selected)
    ew = np.zeros(len(names))
    if n_benchmark:
        ew[ids] = 1.0 / n_benchmark
    active_share = 0.5 * float(np.abs(target - ew).sum())
    return target, active_share, n_benchmark, k, len(selected), benchmark_available


def _trade_toward(old, target, can_trade, cap=None):
    """Keep untradeable holdings marked; trade available names toward fixed target."""
    old = np.asarray(old, dtype=float)
    desired = np.asarray(target, dtype=float).copy()
    pinned = ~np.asarray(can_trade, dtype=bool) & (old > 0)
    fixed = float(old[pinned].sum())
    desired[pinned] = old[pinned]
    tradable = ~pinned & np.asarray(can_trade, dtype=bool)
    mass = float(desired[tradable].sum())
    if mass > 0:
        desired[tradable] *= max(0.0, 1.0 - fixed) / mass
    delta = desired - old
    distance = float(np.abs(delta[tradable]).sum())
    scale = min(1.0, float(cap) / distance) if cap is not None and distance > 0 else 1.0
    new = old.copy()
    new[tradable] = old[tradable] + scale * delta[tradable]
    traded = float(np.abs(new - old).sum())
    return new, traded, np.abs(new - old) > 1e-12


def portfolio(dates, names, member, status, payer, count, op, close, daily_member=None):
    """Monthly open execution with stale-close marks, capped trades, and EW30."""
    d = np.asarray(dates).astype(str)
    names = np.asarray(names).astype(str)
    n, t = op.shape
    if close.shape != op.shape:
        raise ValueError("open and close panels must align")
    if daily_member is None:
        daily_member = np.ones((n, t), dtype=bool)
    if daily_member.shape != (n, t):
        raise ValueError("daily PIT membership must align to price panel")
    month_ids = [j for j, label in enumerate(d) if j == 0 or label[:7] != d[j - 1][:7]]
    form_by_month = {}
    for i, v in enumerate(np.asarray(FORMATION_DATES).astype(str)):
        f = np.datetime64(v, "D").astype(object)
        next_month = (f.replace(day=1) + __import__("datetime").timedelta(days=32)).replace(day=1)
        form_by_month[next_month.strftime("%Y-%m")] = i
    formation_starts = {j: form_by_month.get(d[j][:7]) for j in month_ids}
    active_starts = [j for j in month_ids if formation_starts[j] is not None]
    if len(active_starts) < 2:
        raise ValueError("portfolio needs at least two eligible monthly fills")
    first_fill = active_starts[0]

    # The last observed close before entry initializes stale marks without
    # forming any pre-entry portfolio return.
    last_close = np.full(n, np.nan)
    for i in range(n):
        past = close[i, :first_fill]
        valid = np.flatnonzero(np.isfinite(past) & (past > 0))
        if len(valid):
            last_close[i] = past[valid[-1]]

    strat_gross, strat_net, bench = [], [], []
    turnover, active, costs, selected_counts, benchmark_counts = [], [], [], [], []
    stale_fallback_names, benchmark_stale_fallback_names = set(), set()
    forced_exit_count = 0
    own = np.zeros(n); ew_own = np.zeros(n)
    started = False
    for j in range(first_fill, t):
        is_start = j in formation_starts and formation_starts[j] is not None
        close_ok = np.isfinite(close[:, j]) & (close[:, j] > 0)
        open_ok = np.isfinite(op[:, j]) & (op[:, j] > 0)
        current_available = daily_member[:, j] & open_ok
        trade_cost = 0.0
        traded_mask = np.zeros(n, dtype=bool)
        ew_traded_mask = np.zeros(n, dtype=bool)
        overnight_gross = 0.0
        bench_overnight = 0.0

        if is_start:
            # Old holdings receive the observed overnight move only when a
            # close is available today; a missing close stays at its stale mark.
            gap = np.zeros(n)
            for i in range(n):
                if close_ok[i] and open_ok[i] and np.isfinite(last_close[i]) and last_close[i] > 0:
                    gap[i] = op[i, j] / last_close[i] - 1.0
            overnight_gross = float(np.sum(own * gap))
            if 1 + overnight_gross > 0:
                own = own * (1 + gap) / (1 + overnight_gross)
            bench_overnight = float(np.sum(ew_own * gap))
            if 1 + bench_overnight > 0:
                ew_own = ew_own * (1 + gap) / (1 + bench_overnight)

            fj = formation_starts[j]
            target, _, n_bench, k, chosen, available = target_weights(
                names, member, status, payer, count, op[:, j],
                daily_member[:, j], fj)
            old_own = own.copy()
            own, traded, traded_mask = _trade_toward(own, target, open_ok & daily_member[:, j], TURNOVER_CAP)
            trade_cost = traded * COST_PER_SIDE
            turnover.append(traded); costs.append(trade_cost)
            ew_target = np.zeros(n)
            if n_bench:
                ew_target[available] = 1.0 / n_bench
            ew_own, _, ew_traded_mask = _trade_toward(ew_own, ew_target, open_ok & daily_member[:, j])
            actual_as = .5 * float(np.abs(own - ew_target).sum())
            active.append(actual_as)
            selected_counts.append(chosen); benchmark_counts.append(n_bench)
            forced_exit_count += int(np.sum((old_own > 1e-12) & (own < 1e-12) & open_ok))
            started = True

        # Daily close return uses the last valid close, not the immediately
        # preceding row. Thus missing days are flat and resumed prices catch up.
        strat_day_r = np.zeros(n); bench_day_r = np.zeros(n)
        for i in range(n):
            if not close_ok[i]:
                if own[i] > 0:
                    stale_fallback_names.add(i)
                if ew_own[i] > 0:
                    benchmark_stale_fallback_names.add(i)
                continue
            if is_start and open_ok[i]:
                strat_day_r[i] = close[i, j] / op[i, j] - 1.0
            else:
                strat_day_r[i] = stale_mark_return(last_close[i], close[i, j])
            if is_start and open_ok[i]:
                bench_day_r[i] = close[i, j] / op[i, j] - 1.0
            else:
                bench_day_r[i] = stale_mark_return(last_close[i], close[i, j])

        sg = float(np.sum(own * strat_day_r))
        bg = float(np.sum(ew_own * bench_day_r))
        sgross = (1 + overnight_gross) * (1 + sg) - 1
        snet = (1 + overnight_gross) * (1 - trade_cost) * (1 + sg) - 1
        bret = (1 + bench_overnight) * (1 + bg) - 1
        strat_gross.append(sgross); strat_net.append(snet); bench.append(bret)

        if 1 + sg > 0:
            own = own * (1 + strat_day_r) / (1 + sg)
        if 1 + bg > 0:
            ew_own = ew_own * (1 + bench_day_r) / (1 + bg)
        last_close[close_ok] = close[close_ok, j]

    if not started:
        raise ValueError("no portfolio formation dates in available price calendar")
    # At terminal, stale holdings are liquidated at their last valid close;
    # charge the registered one-side cost and disclose the fallback count.
    terminal_stale = np.asarray(sorted(i for i in stale_fallback_names if own[i] > 0 and
                                       not (np.isfinite(close[i, -1]) and close[i, -1] > 0)), dtype=int)
    benchmark_terminal_stale = np.asarray(sorted(i for i in benchmark_stale_fallback_names if ew_own[i] > 0 and
                                                 not (np.isfinite(close[i, -1]) and close[i, -1] > 0)), dtype=int)
    terminal_exit_cost = float(np.sum(own[terminal_stale]) * COST_PER_SIDE) if len(terminal_stale) else 0.0
    if terminal_exit_cost and strat_net:
        strat_net[-1] = (1 + strat_net[-1]) * (1 - terminal_exit_cost) - 1

    s, sn, b = np.asarray(strat_gross), np.asarray(strat_net), np.asarray(bench)
    pboot, boot = circular_block_bootstrap_pvalue(sn, b, block_length=10,
                                                   n_draws=BOOTSTRAP_DRAWS, seed=SEED)
    ss = float(np.mean(sn) / np.std(sn, ddof=1) * math.sqrt(252)) if len(sn) > 1 and np.std(sn, ddof=1) else 0.0
    bs = float(np.mean(b) / np.std(b, ddof=1) * math.sqrt(252)) if len(b) > 1 and np.std(b, ddof=1) else 0.0
    gross_edge = float(np.prod(1+s) - np.prod(1+b))
    net_edge = float(np.prod(1+sn) - np.prod(1+b))
    total_cost = float(np.sum(costs) + terminal_exit_cost)
    return {"strategy_daily_gross": s, "strategy_daily_net": sn, "benchmark_daily_gross": b,
            "gross_excess_cumulative": gross_edge, "net_excess_cumulative": net_edge,
            "strategy_gross_cumulative": float(np.prod(1+s)-1),
            "strategy_net_cumulative": float(np.prod(1+sn)-1),
            "ew30_cumulative": float(np.prod(1+b)-1),
            "sharpe_strategy_net": ss, "sharpe_ew30": bs, "bootstrap_p": pboot,
            "bootstrap_draws": boot, "turnover": np.asarray(turnover),
            "mean_turnover": float(np.mean(turnover)) if turnover else 0.0,
            "max_turnover": float(np.max(turnover)) if turnover else 0.0,
            "active_share": np.asarray(active), "mean_active_share": float(np.mean(active)) if active else 0.0,
            "selected_counts": np.asarray(selected_counts), "benchmark_available_counts": np.asarray(benchmark_counts),
            "costs": np.asarray(costs), "total_transaction_cost": total_cost,
            "cost_gross_edge_ratio": total_cost / gross_edge if gross_edge > 0 else None,
            "terminal_stale_fallback_names": int(len(terminal_stale)),
            "benchmark_terminal_stale_fallback_names": int(len(benchmark_terminal_stale)),
            "terminal_exit_cost": terminal_exit_cost, "forced_exit_count": forced_exit_count,
            "turnover_pass": bool(len(turnover) and np.max(turnover) <= TURNOVER_CAP + 1e-9),
            "active_share_pass": bool(len(active) and np.mean(active) >= .50)}


def _trial_count():
    text = TRIALS.read_text(encoding="utf-8")
    variants = set(re.findall(r"^\s*-\s*R6\s+variant\s+\d+\s*:\s*([A-Za-z0-9_-]+)\s*$", text, re.M | re.I))
    if "R1-V1" not in variants:
        raise ValueError("R1-V1 must be present in specs/r4_trials.md before execution")
    return len(variants)


def _h12_allowed(h10_pass: bool, h11_pass: bool) -> bool:
    return bool(h10_pass and h11_pass)


def _holm(p_current):
    cfg = json.loads(HOLM_CONFIG.read_text(encoding="utf-8"))
    prior_lines = J1_RESULTS.read_text(encoding="utf-8").splitlines()
    pvals = {k: float(v) if v is not None else 1.0 for k, v in cfg["endpoints"].items()}
    found = {}
    for line in prior_lines:
        fields = [x.strip() for x in line.strip().strip("|").split("|")]
        if fields and fields[0] in {"R6-H7", "R6-H8", "R6-H9"} and len(fields) >= 4:
            found[fields[0]] = float(fields[2])
    if set(found) != {"R6-H7", "R6-H8", "R6-H9"}:
        raise ValueError("r6_J1/RESULTS.md must contain raw p rows for H7-H9")
    pvals.update(found)
    for k in ("R6-H10", "R6-H11", "R6-H12"):
        pvals[k] = float(p_current.get(k)) if p_current.get(k) is not None else 1.0
    return holm_correction(pvals)


def _endpoint_rows(pvals, gatepass, adjusted, status):
    rows = []
    for endpoint in ("R6-H10", "R6-H11", "R6-H12"):
        raw = pvals.get(endpoint)
        rows.append({"endpoint": endpoint, "raw_p": "" if raw is None else raw,
                     "raw_gate_pass": "" if gatepass.get(endpoint) is None else gatepass[endpoint],
                     "holm_p": adjusted[endpoint]["holm_p"],
                     "holm_decision": "reject" if adjusted[endpoint]["reject"] else "retain",
                     "status": status.get(endpoint, "not run")})
    return rows


def _json_safe(value):
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


@guarded_runner(prereg_path=PREREG, run_dir=RUN_DIR)
def run_r1(input_path=INPUTS, coverage_path=COVERAGE, manifest_path=MANIFEST, output_dir=RUN_DIR):
    # Coverage proof is read before NPZ containing price values; it was created
    # from bar-presence masks only and contains no return/outcome columns.
    meta = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    coverage_hash = hashlib.sha256(Path(coverage_path).read_bytes()).hexdigest()
    if meta.get("coverage_sha256") != coverage_hash:
        raise CoverageFailure("coverage table hash differs from input build manifest")
    cov = __import__("pandas").read_csv(coverage_path)
    try:
        gate = check_coverage(cov)
    except CoverageFailure as exc:
        pvals = {f"R6-H{i}": None for i in (10, 11, 12)}
        adjusted = _holm(pvals)
        status = {"R6-H10": "not run; coverage gate failed", "R6-H11": "not run; coverage gate failed",
                  "R6-H12": "not run; coverage/H10/H11 gate failed"}
        rows = _endpoint_rows(pvals, {k: None for k in pvals}, adjusted, status)
        result = {"coverage_gate": {"passed": False, "reason": str(exc)}, "portfolio": None,
                  "endpoints": rows, "holm_family": adjusted,
                  "prereg_sha256": validate_frozen_prereg(PREREG)[1], "variant": "R1-V1"}
        out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
        (out / "R1_RESULTS.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        with (out / "R1_ENDPOINTS.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        return result
    if meta.get("outcomes_computed") is not False or meta.get("holdout_loaded") is not False:
        raise CoverageFailure("input manifest does not certify development-only input construction")
    bundle_hash = hashlib.sha256(Path(input_path).read_bytes()).hexdigest()
    if meta.get("input_bundle_sha256") != bundle_hash:
        raise CoverageFailure("input bundle hash differs from input build manifest")
    data = np.load(input_path, allow_pickle=False)
    dates = data["sessions"].astype(str)
    formations = data["formations"].astype(str)
    global FORMATION_DATES
    FORMATION_DATES = formations
    current_p = {f"R6-H{i}": None for i in (10, 11, 12)}
    gatepass = {f"R6-H{i}": None for i in (10, 11, 12)}
    status = {f"R6-H{i}": "not run" for i in (10, 11, 12)}
    results = {"coverage_gate": gate, "endpoints": None}
    endpoint_pass = False
    op, close = data["sp500_fwd_open"], data["sp500_fwd_close"]
    ret = np.full_like(op, np.nan)
    ok = np.isfinite(op) & (op > 0) & np.isfinite(close) & (close > 0)
    ret[ok] = close[ok] / op[ok] - 1
    elig = data["sp500_member"] & data["sp500_dividend_status_ok"] & (data["sp500_sic2"] != "") & np.isfinite(ret)
    m = mechanism(data["sp500_payer"], data["sp500_sic2"], ret, elig)
    sh = shuffle_placebo(data["sp500_payer"], data["sp500_sic2"], ret, elig)
    current_p["R6-H10"], current_p["R6-H11"] = m["p"], sh["p"]
    gatepass["R6-H10"], gatepass["R6-H11"] = m["pass"], sh["pass"]
    status["R6-H10"] = "pass" if m["pass"] else "fail"
    status["R6-H11"] = "pass" if sh["pass"] else "fail"
    endpoint_pass = m["pass"] and sh["pass"]
    results["mechanism"] = {k: v for k, v in m.items() if k not in {"monthly_spreads", "groups"}}
    results["mechanism"]["monthly_spreads"] = m["monthly_spreads"].tolist()
    results["mechanism"]["eligible_sector_groups"] = m["groups"].tolist()
    results["placebo"] = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in sh.items()}
    if _h12_allowed(gatepass["R6-H10"], gatepass["R6-H11"]):
        dow = portfolio(dates, data["dow_names"].astype(str), data["dow_member"], data["dow_dividend_status_ok"],
                        data["dow_payer"], data["dow_recurrence_count"], data["dow_adj_open"], data["dow_adj_close"],
                        data["dow_daily_member"])
        current_p["R6-H12"] = dow["bootstrap_p"]
        gatepass["R6-H12"] = bool(dow["net_excess_cumulative"] > 0 and
                                    dow["sharpe_strategy_net"] > dow["sharpe_ew30"] and
                                    dow["turnover_pass"] and dow["active_share_pass"] and
                                    dow["bootstrap_p"] < .05)
        status["R6-H12"] = "raw gates passed" if gatepass["R6-H12"] else "raw gates failed"
        results["portfolio"] = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in dow.items()}
        trial_count = _trial_count()
        results["portfolio"]["dsr"] = deflated_sharpe_ratio(dow["strategy_daily_net"], trial_count)
        results["portfolio"]["dsr_trial_count"] = trial_count
    else:
        status["R6-H12"] = "not run; H10/H11 did not both pass"
        results["portfolio"] = None
    adjusted = _holm(current_p)
    if current_p["R6-H12"] is not None and not adjusted["R6-H12"]["reject"]:
        status["R6-H12"] = ("raw gates passed; Holm failed" if gatepass["R6-H12"]
                             else "raw gates failed; Holm failed")
    elif current_p["R6-H12"] is not None:
        status["R6-H12"] = "pass" if gatepass["R6-H12"] else "raw gates failed"
    rows = _endpoint_rows(current_p, gatepass, adjusted, status)
    results["endpoints"] = rows
    results["holm_family"] = {k: v for k, v in adjusted.items()}
    results["prereg_sha256"] = validate_frozen_prereg(PREREG)[1]
    results["variant"] = "R1-V1"
    results["draw_settings"] = {"shuffle": SHUFFLE_DRAWS, "seed": SEED, "bootstrap": BOOTSTRAP_DRAWS}
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    (out / "R1_RESULTS.json").write_text(json.dumps(_json_safe(results), indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with (out / "R1_ENDPOINTS.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    if "placebo" in results:
        with (out / "R1_PLACEBO_DRAWS.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["draw", "mean_spread"])
            w.writerows(enumerate(results["placebo"]["draws"], 1))
    mechanism_pass = bool(gatepass["R6-H10"] and gatepass["R6-H11"])
    mechanism_file = out / "MECHANISM_PASS.json"
    if mechanism_pass:
        mechanism_file.write_text(json.dumps({"approach": "R1", "variant": "R1-V1",
                                              "passed": True, "prereg_sha256": results["prereg_sha256"],
                                              "H10_mean_spread": results["mechanism"]["mean"],
                                              "H10_nw_t_lag3": results["mechanism"]["nw_t"],
                                              "H11_placebo_p": results["placebo"]["p"]}, indent=2) + "\n",
                                  encoding="utf-8")
    else:
        mechanism_file.unlink(missing_ok=True)
    return results


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute", action="store_true", help="explicit authorization required for outcomes")
    p.add_argument("--inputs", type=Path, default=INPUTS)
    p.add_argument("--coverage", type=Path, default=COVERAGE)
    p.add_argument("--manifest", type=Path, default=MANIFEST)
    p.add_argument("--output-dir", type=Path, default=RUN_DIR)
    a = p.parse_args(argv)
    try:
        result = run_r1(a.inputs, a.coverage, a.manifest, a.output_dir, execute=a.execute)
        print(json.dumps({"variant": "R1-V1", "coverage_pass": result["coverage_gate"]["passed"],
                          "portfolio_run": result["portfolio"] is not None}, indent=2))
        return 0
    except Exception as exc:
        print(f"R1 refused/failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
