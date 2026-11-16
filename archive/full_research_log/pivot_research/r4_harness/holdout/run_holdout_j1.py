"""Coordinator-only, one-shot holdout runner for frozen J1.

Importing this module and running its synthetic tests never reads sealed data.
The price loader is reached only after all authorization and manifest checks.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from bisect import bisect_right
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from r4_harness.holdout.portfolio_core import portfolio_report
from r4_harness.phase3 import prereg_digest, require_frozen_prereg

START, END = "2010-01-01", "2020-10-31"
DWDP_START, DWDP_END = "2017-09-01", "2019-04-30"
EXPECTED_PREREG_SHA256 = "996b971090be395fffb1e11dff1430bbf581b338637250716607bf6b51cb7698"
TURNOVER_CAP = 0.50
COST_RATE = 0.0005
BOOTSTRAP_DRAWS = 5000
BOOTSTRAP_SEED = 20261111
BOOTSTRAP_BLOCK = 10
LOOKBACK = FORMATION_STEP = TOP_N = 5
DEFAULT_LOCK = Path(__file__).resolve().parent / "HOLDOUT_J1_RUN_LOCK.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "HOLDOUT_J1_RESULTS.json"
KNOWN_GAPS = {
    "KFT": "missing price lineage",
    "DWDP": "missing price lineage; include/exclude window reported, with no fabricated prices",
    "WBA": "missing price lineage",
    "UTX": "RTX price lineage proxy",
}


def validate_holdout_path(path: Path, *, must_exist=True) -> Path:
    p = Path(path).resolve()
    parts = {x.lower() for x in p.parts}
    if "sealed_holdout_dow" not in parts:
        raise PermissionError("holdout inputs must be under sealed_holdout_dow")
    if any(x in parts for x in {"repo", "w1_engine", "oos3", "r6_data", "r6_j1"}):
        raise PermissionError("development/input-bundle paths are refused for holdout prices")
    if must_exist and not p.exists():
        raise FileNotFoundError(p)
    return p


def acquire_one_run_lock(path: Path, details: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as f:
            json.dump(details, f, indent=2)
            f.write("\n")
    except FileExistsError as exc:
        raise PermissionError(f"J1 holdout already attempted; one-run lock exists: {path}") from exc
    return path


def _field(row, *names):
    keys = {k.lower(): k for k in row}
    key = next((keys[n.lower()] for n in names if n.lower() in keys), None)
    return None if key is None else row[key]


def _price_values(row):
    def number(*names):
        raw = _field(row, *names)
        if raw in (None, ""):
            raise ValueError("missing " + "/".join(names))
        return float(raw)
    raw_open = number("open")
    raw_high = number("high")
    raw_low = number("low")
    raw_close = number("close")
    adj_close = number("adjclose", "adj_close", "adjusted_close")
    if raw_close <= 0 or adj_close <= 0:
        raise ValueError("nonpositive close")
    factor = adj_close / raw_close
    adj_open_raw = _field(row, "adjopen", "adj_open", "adjusted_open")
    adj_open = float(adj_open_raw) if adj_open_raw not in (None, "") else raw_open * factor
    return adj_open, raw_high * factor, raw_low * factor, adj_close


def _price_source(asset):
    return "RTX" if asset == "UTX" else asset


def load_holdout_prices(price_dir: Path, assets):
    """Load requested-window OHLC only; never parse numeric cells outside dates."""
    price_dir = validate_holdout_path(price_dir)
    rows_by_asset = {}
    calendar = set()
    coverage = {}
    for asset in assets:
        source = _price_source(asset)
        if asset in {"KFT", "DWDP", "WBA"}:
            coverage[asset] = {"source": None, "rows": 0, "gap": KNOWN_GAPS[asset]}
            rows_by_asset[asset] = {}
            continue
        path = price_dir / f"{source}.csv"
        if not path.is_file():
            coverage[asset] = {"source": source, "rows": 0,
                               "gap": KNOWN_GAPS.get(asset, "no price file")}
            rows_by_asset[asset] = {}
            continue
        vals_by_date = {}
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                day = str(_field(row, "date") or "")[:10]
                # Date guard precedes parsing any price field.
                if day < START or day > END:
                    continue
                try:
                    vals = _price_values(row)
                    if not np.all(np.isfinite(vals)) or vals[0] <= 0 or vals[3] <= 0 or vals[1] < vals[2]:
                        continue
                except (TypeError, ValueError, ZeroDivisionError):
                    continue
                vals_by_date[day] = vals
                calendar.add(day)
        rows_by_asset[asset] = vals_by_date
        coverage[asset] = {"source": source, "rows": len(vals_by_date),
                           "gap": "RTX lineage proxy" if asset == "UTX" else None}
    dates = sorted(calendar)
    if not dates:
        raise ValueError("no authorized 2010-01-01 through 2020-10-31 OHLC rows; holdout infeasible")
    n, t = len(assets), len(dates)
    op = np.full((n, t), np.nan)
    high = np.full((n, t), np.nan)
    low = np.full((n, t), np.nan)
    close = np.full((n, t), np.nan)
    for i, asset in enumerate(assets):
        for d, vals in rows_by_asset[asset].items():
            j = bisect_right(dates, d) - 1
            if dates[j] == d:
                op[i, j], high[i, j], low[i, j], close[i, j] = vals
    return dates, op, high, low, close, coverage


def load_pit_roster(path: Path, assets, dates):
    """Expand effective-dated PIT intervals without using any price data."""
    path = validate_holdout_path(path)
    by_asset = {str(a): [] for a in assets}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"ticker", "effective_from", "effective_to_exclusive"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError("PIT roster requires ticker,effective_from,effective_to_exclusive columns")
        for row in reader:
            ticker = str(row["ticker"]).strip()
            if ticker in by_asset:
                by_asset[ticker].append((row["effective_from"], row["effective_to_exclusive"]))
    out = np.zeros((len(assets), len(dates)), dtype=bool)
    for i, asset in enumerate(assets):
        for start, end in by_asset[str(asset)]:
            lo, hi = max(start, START), min(end or END, "2020-11-01")
            for j, day in enumerate(dates):
                if lo <= day < hi:
                    out[i, j] = True
    return out


def load_dated_sic2(path: Path, assets, dates):
    """Use the last dated SIC effective by each formation session, SIC2 only."""
    p = Path(path).resolve()
    if not p.is_file():
        raise FileNotFoundError(p)
    by_asset = {str(a): [] for a in assets}
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        effective_key = "effective_from" if "effective_from" in fields else "effective_date"
        if not {"ticker", "sic"}.issubset(fields) or effective_key not in fields:
            raise ValueError("dated SIC panel needs ticker,sic,effective_from (or effective_date)")
        for row in reader:
            ticker = str(row["ticker"]).strip()
            day, sic = str(row[effective_key])[:10], str(row["sic"]).strip()
            if ticker in by_asset and day and len(sic) >= 2 and sic[:2].isdigit() and sic[:2] != "00":
                by_asset[ticker].append((day, sic[:2]))
    for rows in by_asset.values():
        rows.sort()
    out = np.full((len(assets), len(dates)), "", dtype="U2")
    for i, asset in enumerate(assets):
        rows = by_asset[str(asset)]
        starts = [r[0] for r in rows]
        for j, day in enumerate(dates):
            k = bisect_right(starts, day) - 1
            if k >= 0:
                out[i, j] = rows[k][1]
    return out


def r6_trial_count(path: Path) -> int:
    text = Path(path).read_text(encoding="utf-8")
    variants = set(re.findall(r"^\s*-\s*R6\s+variant\s+\d+\s*:\s*([A-Za-z0-9_-]+)\s*$",
                              text, re.M | re.I))
    if "J1-V1" not in variants:
        raise ValueError("R6 trial log must contain J1-V1 before holdout DSR")
    return len(variants)


def build_j1_scores(close, roster, sic2, dates, *, formation_step=FORMATION_STEP):
    """J1-V1: trailing five-session return minus leave-one-out SIC2 peer mean."""
    close, roster, sic2 = np.asarray(close, float), np.asarray(roster, bool), np.asarray(sic2).astype(str)
    if close.ndim != 2 or close.shape != roster.shape or close.shape != sic2.shape:
        raise ValueError("close, roster and SIC2 matrices must be assets x dates")
    n, t = close.shape
    signal = np.full((n, t), np.nan)
    scheduled = np.arange(0, t, formation_step, dtype=int)
    for d in scheduled:
        if d < LOOKBACK:
            continue
        ok = roster[:, d] & np.isfinite(close[:, d]) & np.isfinite(close[:, d - LOOKBACK])
        ok &= (close[:, d] > 0) & (close[:, d - LOOKBACK] > 0)
        r5 = np.full(n, np.nan)
        r5[ok] = close[ok, d] / close[ok, d - LOOKBACK] - 1.0
        groups = {}
        for i in np.flatnonzero(ok):
            code = str(sic2[i, d]).strip()
            if len(code) == 2 and code.isdigit() and code != "00":
                groups.setdefault(code, []).append(int(i))
        for members in groups.values():
            if len(members) >= 2:
                ix = np.asarray(members, int)
                total = float(np.sum(r5[ix]))
                signal[ix, d] = r5[ix] - (total - r5[ix]) / (len(ix) - 1)
    return signal, scheduled


def dwdp_membership(dates):
    return np.asarray([DWDP_START <= d <= DWDP_END for d in dates], dtype=bool)


def analyze_arrays(assets, dates, open_px, close_px, roster, sic2, *,
                   development_net_excess_sign, trial_count=3,
                   bootstrap_draws=BOOTSTRAP_DRAWS):
    """Pure array analysis for synthetic tests and the authorized adapter."""
    assets, dates = list(map(str, assets)), list(map(str, dates))
    op, close, roster, sic2 = (np.asarray(x) for x in (open_px, close_px, roster, sic2))
    if op.shape != close.shape or op.shape != roster.shape or op.shape != sic2.shape or op.shape != (len(assets), len(dates)):
        raise ValueError("J1 holdout arrays must share assets x dates dimensions")
    if development_net_excess_sign not in {-1, 1}:
        raise ValueError("development net excess-return sign must be +1 or -1")
    dwdp = dwdp_membership(dates)
    scenarios = {}
    for label, exclude in (("included", False), ("excluded", True)):
        active = roster.astype(bool).copy()
        if exclude and "DWDP" in assets:
            active[assets.index("DWDP"), dwdp] = False
        signal, scheduled = build_j1_scores(close, active, sic2, dates)
        formations = [int(i) for i in scheduled if np.isfinite(signal[:, i]).sum() >= TOP_N]
        if len(formations) < 2:
            raise ValueError(f"{label}: fewer than two formations have five eligible PIT names")
        # portfolio_core selects the highest score; negation implements the
        # frozen lowest-five signal without changing tie handling/cost math.
        scores = -signal
        port = portfolio_report(
            scores, op, close, active, formations, trial_count=trial_count,
            bootstrap_draws=bootstrap_draws, seed=BOOTSTRAP_SEED,
            turnover_cap=TURNOVER_CAP, cost_rate=COST_RATE, holdout=False,
            turnover_cap_basis="absolute", asset_names=assets,
            endpoint_name="R6-J1-holdout-net-excess")
        held_sign = int(np.sign(port["net_excess_return"]))
        same_sign = held_sign == development_net_excess_sign and held_sign != 0
        sharpe_above_ew = port["strategy_net"]["sharpe"] > port["benchmark_net"]["sharpe"]
        p_pass = port["bootstrap_p_raw"] < 0.10
        # Criterion 5 only: same sign, Sharpe above EW30, one-sided p < .10.
        scenarios[label] = {
            "portfolio": port,
            "development_net_excess_sign": development_net_excess_sign,
            "holdout_net_excess_sign": held_sign,
            "same_sign_pass": bool(same_sign),
            "net_sharpe_above_EW30_pass": bool(sharpe_above_ew),
            "one_sided_block_bootstrap_p_lt_0_10_pass": bool(p_pass),
            "criterion_5_pass": bool(same_sign and sharpe_above_ew and p_pass),
            "dwdp_window_sessions": int(dwdp.sum()),
            "dwdp_prices_missing_or_unrepresented": "DWDP absent prices have no available-name effect; exclusion is retained as a labeled sensitivity.",
            "insufficient_signal_formations_skipped": [int(i) for i in scheduled if np.isfinite(signal[:, i]).sum() < TOP_N],
        }
    return {"approach": "J1", "dates": [dates[0], dates[-1]],
            "known_gaps": KNOWN_GAPS, "dwdp_window": [DWDP_START, DWDP_END],
            "turnover_cap": TURNOVER_CAP, "cost_rate_per_traded_notional": COST_RATE,
            "bootstrap": {"draws": bootstrap_draws, "block_length": BOOTSTRAP_BLOCK,
                          "seed": BOOTSTRAP_SEED}, "trial_count": int(trial_count),
            "holdout_pass_rule": "net excess-return sign matches development; net Sharpe exceeds EW30; one-sided 10-session circular block-bootstrap p < 0.10",
            "dwdp_included": scenarios["included"], "dwdp_excluded": scenarios["excluded"]}


def _load_development_sign(proof_path: Path, results_path: Path, prereg_sha: str):
    if Path(proof_path).with_name("MECHANISM_FAIL.json").is_file():
        raise PermissionError("J1 mechanism failure artifact exists; holdout is prohibited")
    if not Path(proof_path).is_file():
        raise PermissionError("missing J1 MECHANISM_PASS artifact")
    proof = json.loads(Path(proof_path).read_text(encoding="utf-8"))
    if proof.get("approach") != "J1" or proof.get("passed") is not True:
        raise PermissionError("artifact does not certify a passing J1 mechanism gate")
    if proof.get("prereg_sha256") != prereg_sha:
        raise PermissionError("mechanism artifact hash does not match frozen J1")
    if not proof.get("placebo_passed"):
        raise PermissionError("J1 SIC2 placebo did not pass")
    if float(proof.get("direction_adjusted_mean_ic", -1)) < 0.0034641016 or float(proof.get("nw_t_lag4", 0)) > -2.0:
        raise PermissionError("J1 mechanism artifact does not meet the frozen sign, IC floor and NW t gate")
    if not Path(results_path).is_file():
        raise PermissionError("J1_RESULTS.json is required to determine the registered development portfolio sign")
    result = json.loads(Path(results_path).read_text(encoding="utf-8"))
    if result.get("prereg_sha256") != prereg_sha or not result.get("portfolio"):
        raise PermissionError("development results do not match frozen J1 or contain no portfolio")
    if result.get("passed") is not True:
        raise PermissionError("development J1 portfolio gate failed; holdout cannot rescue it")
    value = result["portfolio"].get("net_excess_return")
    if value is None or not np.isfinite(float(value)) or float(value) == 0:
        raise PermissionError("development portfolio has no nonzero net excess-return sign to compare")
    sign = int(np.sign(float(value)))
    if sign != 1:
        raise PermissionError("development net excess must be positive before a confirmatory holdout")
    return proof, result, sign


def run_holdout_once(*, execute_holdout, prereg_path, price_dir, roster_path,
                     sic_path, mechanism_pass_path, development_results_path,
                     output_path=DEFAULT_OUTPUT, lock_path=DEFAULT_LOCK,
                     caller_role=None):
    if execute_holdout is not True:
        raise PermissionError("refusing: coordinator must pass --execute-holdout")
    if caller_role != "coordinator" or os.environ.get("ORCA_HOLDOUT_AUTH") != "COORDINATOR_ONLY":
        raise PermissionError("coordinator-only authorization is required")
    prereg_path = Path(prereg_path).resolve()
    frozen = require_frozen_prereg("J1", prereg_dir=prereg_path.parent)
    if frozen.resolve() != prereg_path:
        raise ValueError("pre-registration path must be the canonical frozen J1.md")
    actual_sha = prereg_digest(frozen.read_text(encoding="utf-8"))
    if actual_sha != EXPECTED_PREREG_SHA256:
        raise PermissionError("frozen J1 hash differs from the coordinator-approved SHA256")
    proof, dev_result, dev_sign = _load_development_sign(mechanism_pass_path,
                                                          development_results_path,
                                                          actual_sha)
    prices = validate_holdout_path(price_dir)
    roster_file = validate_holdout_path(roster_path)
    # SIC classification is not sealed return data; the dated panel is explicitly prescribed.
    sic_file = Path(sic_path).resolve()
    if not sic_file.is_file():
        raise FileNotFoundError(sic_file)
    expected_sic = (ROOT / "r4_L4" / "data" / "sic_panel.csv").resolve()
    if sic_file != expected_sic:
        raise PermissionError(f"J1 holdout must use the frozen dated SIC panel: {expected_sic}")
    # The lock precedes every read of the holdout roster or price values.
    trial_count = r6_trial_count(ROOT / "specs" / "r4_trials.md")
    acquire_one_run_lock(lock_path, {"approach": "J1", "pre_registration_sha256": actual_sha,
                                    "mechanism_pass": str(mechanism_pass_path),
                                    "development_results": str(development_results_path),
                                    "price_directory": str(prices), "started_by": "coordinator"})
    assets = []
    with roster_file.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            ticker = str(row.get("ticker", "")).strip()
            if ticker and ticker not in assets:
                assets.append(ticker)
    if not assets:
        raise ValueError("PIT roster contains no ticker identities")
    dates, op, high, low, close, coverage = load_holdout_prices(prices, assets)
    roster = load_pit_roster(roster_file, assets, dates)
    # Prices and roster are date-wise; never substitute names or impute bars.
    roster &= np.isfinite(close) & np.isfinite(op)
    sic2 = load_dated_sic2(sic_file, assets, dates)
    result = analyze_arrays(assets, dates, op, close, roster, sic2,
                            development_net_excess_sign=dev_sign, trial_count=trial_count,
                            bootstrap_draws=BOOTSTRAP_DRAWS)
    result.update({"pre_registration_sha256": actual_sha,
                   "mechanism_pass_artifact": str(mechanism_pass_path),
                   "development_results_artifact": str(development_results_path),
                   "asset_price_coverage": coverage,
                   "PIT_roster_path": str(roster_file), "dated_SIC2_path": str(sic_file),
                   "input_limitations": ["No bars outside 2010-01-01 through 2020-10-31 enter the price panel.",
                                         "No price imputation or successor substitution; unavailable prices are excluded date-wise.",
                                         "KFT, DWDP and WBA are known price gaps; UTX maps to RTX lineage.",
                                         "This runner expects a coordinator-staged historical PIT Dow roster and OHLC CSVs; if absent, report infeasibility."]})
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else float(x)), encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prereg", type=Path, default=ROOT / "specs" / "r6_prereg" / "J1.md")
    parser.add_argument("--prices", type=Path, required=True)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--sic-panel", type=Path, default=ROOT / "r4_L4" / "data" / "sic_panel.csv")
    parser.add_argument("--mechanism-pass", type=Path, required=True)
    parser.add_argument("--development-results", type=Path, default=ROOT / "r6_J1" / "J1_RESULTS.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--coordinator-only", action="store_true", required=True)
    parser.add_argument("--execute-holdout", action="store_true", required=True)
    args = parser.parse_args(argv)
    try:
        if os.environ.get("ORCA_HOLDOUT_AUTH") != "COORDINATOR_ONLY":
            raise PermissionError("set ORCA_HOLDOUT_AUTH=COORDINATOR_ONLY in the coordinator terminal")
        result = run_holdout_once(execute_holdout=args.execute_holdout,
                                  prereg_path=args.prereg, price_dir=args.prices,
                                  roster_path=args.roster, sic_path=args.sic_panel,
                                  mechanism_pass_path=args.mechanism_pass,
                                  development_results_path=args.development_results,
                                  output_path=args.output, lock_path=args.lock,
                                  caller_role="coordinator")
        print(json.dumps(result, indent=2, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else float(x)))
        return 0
    except Exception as exc:
        print(f"REFUSED/FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
