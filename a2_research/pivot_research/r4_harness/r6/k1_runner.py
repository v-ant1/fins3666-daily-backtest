"""Guarded K1 earnings-event drift runner. Real inputs are read only with --execute."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr, t as student_t

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from r4_harness.ic_engine import cross_sectional_ic
from r4_harness.phase3 import (
    append_trial, break_even_rank_ic, circular_block_bootstrap_pvalue,
    deflated_sharpe_ratio, holm_correction, newey_west_t, prereg_digest,
)
from r4_harness.prereg_diff import prereg_diff
from r4_harness.runner_guard import guarded_runner, validate_frozen_prereg
from r6_J1.run_j1 import (
    _execute_pending_close as _j1_execute_pending_close,
    _execute_pending_open as _j1_execute_pending_open,
    _mark_close as _j1_mark_close,
    _price_ok as _j1_price_ok,
)

PREREG = ROOT / "specs/r6_prereg/K1.md"
EXPECTED_PREREG_SHA256 = "889a6ffa50fe65864b0c432e1590c2252b7f2a76de6f914bafbdf2578441d3b3"
INPUTS = HERE / "K1_INPUTS.npz"
EVENTS = ROOT / "r6_data/earnings_clock_sp500.csv"
INPUT_MANIFEST = HERE / "K1_INPUT_MANIFEST.json"
RUN_DIR = HERE / "run"
RESULTS = HERE / "K1_RESULTS.json"
ENDPOINT_LOG = HERE / "R6_ENDPOINTS.csv"
HOLM_CONFIG = ROOT / "specs/r6_holm_family.json"
TRIAL_LOG = ROOT / "specs/r4_trials.md"
DIFF_SOURCE = HERE / "K1_PREREG_DIFF_SOURCE.md"
DIFF_CONFIG = HERE / "k1_prereg_diff_config.json"

EVENT_START, EVENT_END = "2020-11-30", "2026-09-30"
FIRST_FORMATION, LAST_FORMATION = "2020-12-31", "2026-09-30"
NW_LAG, HORIZON = 4, 21
PLACEBO_DRAWS, PLACEBO_SEED = 500, 20261111
BOOTSTRAP_DRAWS, BOOTSTRAP_BLOCK, BOOTSTRAP_SEED = 5000, 10, 20261111
TURNOVER_CAP, COST_PER_SIDE, ACTIVE_SHARE_MIN = .50, .0005, .50
TOP_N = 5
RETURN_DISPERSION, COST_TURNOVER_REFERENCE = .10, .50
COST_IC_FLOOR = break_even_rank_ic(.50, .10, .0005, 5 / 30)
ENDPOINTS = ("R6-H16", "R6-H17", "R6-H18")
NY = ZoneInfo("America/New_York")

RUNNER_CONFIG = {
    "min_t": 2, "cap": .50, "turnover_cap": .50,
    "return_dispersion": .10, "cost_per_side": .0005,
    "top_fraction": 5 / 30, "top_n": 5, "nw_lag": 4,
    "draws": [500, 5000], "percentile": 95, "seed": 20261111,
    "block_length": 10, "alpha": [.05, .1], "active_share_min": .50,
    "endpoint_ids": [1, 2, 3], "endpoint_count": 3,
    "horizon": 21,
}


class InputManifestError(RuntimeError):
    pass


def prereg_diff_payload():
    config = json.loads(DIFF_CONFIG.read_text(encoding="utf-8"))
    if config != RUNNER_CONFIG:
        raise ValueError("K1 prereg-diff config differs from implementation constants")
    return prereg_diff(DIFF_SOURCE, RUNNER_CONFIG)


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_input_manifest(path: str | Path, *, root: str | Path = ROOT) -> dict:
    """Verify every staged development source before reading prices or labels."""
    p, base = Path(path).resolve(), Path(root).resolve()
    if not p.is_file():
        raise InputManifestError(f"K1 input manifest missing: {p}")
    obj = json.loads(p.read_text(encoding="utf-8"))
    if obj.get("schema") != "K1_INPUTS_V1":
        raise InputManifestError("unsupported K1 input manifest schema")
    if obj.get("development_window") != ["2020-11-27", "2026-10-30"]:
        raise InputManifestError("K1 manifest must pin the permitted development window")
    if obj.get("holdout_loaded") is not False or obj.get("forward_labels_built") is not False:
        raise InputManifestError("K1 manifest must attest no holdout and no prebuilt forward labels")
    files = obj.get("files")
    if not isinstance(files, dict) or not {"prices", "events", "sic", "sp500_roster", "dow_roster"}.issubset(files):
        raise InputManifestError("manifest must hash prices, event clock, SIC panel, and both PIT rosters")
    for label, entry in files.items():
        if not isinstance(entry, dict) or not {"path", "sha256"}.issubset(entry):
            raise InputManifestError(f"malformed manifest entry: {label}")
        file_path = (base / str(entry["path"])).resolve()
        if base not in file_path.parents:
            raise InputManifestError(f"input path escapes project root: {label}")
        if not file_path.is_file():
            raise InputManifestError(f"manifest input missing: {label} ({file_path})")
        if sha256_file(file_path).lower() != str(entry["sha256"]).lower():
            raise InputManifestError(f"input SHA-256 mismatch: {label}")
    registered_paths = [str(files[k]["path"]) for k in ("prices", "events", "sic", "sp500_roster", "dow_roster")]
    if len(set(registered_paths)) != len(registered_paths):
        raise InputManifestError("manifest roles must point to distinct source files")
    expected_prices = (base / str(obj["files"]["prices"]["path"])).resolve()
    if expected_prices != (base / INPUTS.relative_to(ROOT)).resolve():
        raise InputManifestError("prices entry must reference the registered K1 development-only NPZ bundle")
    expected_events = (base / str(obj["files"]["events"]["path"])).resolve()
    if expected_events != (base / EVENTS.relative_to(ROOT)).resolve():
        raise InputManifestError("event clock entry must reference the registered K1 EDGAR clock")
    return obj


def load_price_bundle(path: str | Path) -> dict:
    """Load raw development OHLC/roster/SIC arrays, never precomputed outcomes."""
    with np.load(path, allow_pickle=False) as z:
        required = {
            "dates", "sp500_tickers", "sp500_open", "sp500_close", "sp500_roster", "sp500_sic2",
            "dow_tickers", "dow_open", "dow_close", "dow_roster", "dow_sic2",
            "spy_open", "spy_close",
        }
        missing = required - set(z.files)
        if missing:
            raise InputManifestError(f"K1 price bundle lacks keys: {sorted(missing)}")
        extra = set(z.files) - required
        if extra:
            raise InputManifestError(f"K1 price bundle contains unregistered fields: {sorted(extra)}")
        b = {k: z[k] for k in required}
    b["dates"] = np.asarray(b["dates"]).astype(str)
    for universe in ("sp500", "dow"):
        b[f"{universe}_tickers"] = np.asarray(b[f"{universe}_tickers"]).astype(str)
        b[f"{universe}_sic2"] = np.asarray(b[f"{universe}_sic2"]).astype(str)
        b[f"{universe}_roster"] = np.asarray(b[f"{universe}_roster"], bool)
        for field in ("open", "close"):
            b[f"{universe}_{field}"] = np.asarray(b[f"{universe}_{field}"], float)
        n, t = b[f"{universe}_close"].shape
        if b[f"{universe}_open"].shape != (n, t) or b[f"{universe}_roster"].shape != (n, t) or b[f"{universe}_sic2"].shape != (n, t):
            raise InputManifestError(f"{universe} input arrays must share assets x sessions shape")
        if len(b[f"{universe}_tickers"]) != n or len(b["dates"]) != t:
            raise InputManifestError(f"{universe} ticker/date dimensions do not match prices")
    for field in ("spy_open", "spy_close"):
        b[field] = np.asarray(b[field], float)
        if b[field].shape != b["dates"].shape:
            raise InputManifestError(f"{field} must have one value per session")
    if len(set(b["dates"])) != len(b["dates"]) or np.any(b["dates"][1:] <= b["dates"][:-1]):
        raise InputManifestError("dates must be unique and strictly increasing")
    if b["dates"][0] != "2020-11-27" or b["dates"][-1] != "2026-10-30":
        raise InputManifestError("price bundle dates must begin/end at registered development boundaries")
    return b


def _session_index(timestamp: str, dates: np.ndarray, classification: str) -> int | None:
    """Index first complete session whose open strictly follows SEC acceptance."""
    ts = datetime.fromisoformat(str(timestamp)).astimezone(NY)
    if classification not in {"BMO", "AMC"}:
        return None
    if classification == "BMO" and not ts.time() < time(9, 30):
        raise ValueError("BMO label contradicts acceptance timestamp")
    if classification == "AMC" and ts.time() < time(16, 0):
        raise ValueError("AMC label contradicts acceptance timestamp")
    for j, day in enumerate(dates):
        session_open = datetime.fromisoformat(str(day)).replace(tzinfo=NY, hour=9, minute=30)
        if session_open > ts:
            return j
    return None


def _market_adjusted_event(signal_close, prior_close, spy_close, spy_prior):
    vals = (signal_close, prior_close, spy_close, spy_prior)
    if not all(np.isfinite(v) and v > 0 for v in vals):
        return float("nan")
    return float(signal_close / prior_close - 1 - (spy_close / spy_prior - 1))


def _forward_abret21(close_i, open_i, spy_close, spy_open, event_i):
    end = event_i + HORIZON
    vals = (close_i[end], open_i[event_i + 1], spy_close[end], spy_open[event_i + 1])
    if not all(np.isfinite(v) and v > 0 for v in vals):
        return float("nan")
    return float(close_i[end] / open_i[event_i + 1] - 1 - (spy_close[end] / spy_open[event_i + 1] - 1))


def make_event_rows(events: pd.DataFrame, bundle: dict, universe: str) -> list[dict]:
    """Map SEC events to prices, retaining signal-only rows separately from labels."""
    tickers = bundle[f"{universe}_tickers"]
    close, op = bundle[f"{universe}_close"], bundle[f"{universe}_open"]
    roster, sic = bundle[f"{universe}_roster"], bundle[f"{universe}_sic2"]
    dates = bundle["dates"]
    tix = {str(x): i for i, x in enumerate(tickers)}
    by_key: dict[tuple[str, str], pd.Series] = {}
    for _, row in events.sort_values("acceptance_timestamp_et").iterrows():
        if str(row.get("classification", "")) not in {"BMO", "AMC"}:
            continue
        report = pd.Timestamp(row["report_date"])
        quarter = f"{report.year}Q{report.quarter}"
        key = (str(row["cik"]).lstrip("0"), quarter)
        by_key.setdefault(key, row)
    out = []
    for (cik, report_quarter), row in by_key.items():
        ticker = str(row["ticker"])
        if ticker not in tix:
            continue
        e = _session_index(row["acceptance_timestamp_et"], dates, str(row["classification"]))
        if e is None or e <= 0 or dates[e] < EVENT_START or dates[e] > EVENT_END:
            continue
        i = tix[ticker]
        if not roster[i, e]:
            continue
        score = _market_adjusted_event(close[i, e], close[i, e-1], bundle["spy_close"][e], bundle["spy_close"][e-1])
        if not np.isfinite(score):
            continue
        sic2 = str(sic[i, e]).strip()
        if sic2.lower() in {"", "nan", "none", "00", "0"}:
            continue
        fwd = _forward_abret21(close[i], op[i], bundle["spy_close"], bundle["spy_open"], e) if e + HORIZON < len(dates) else float("nan")
        out.append({"cik": cik, "ticker": ticker, "event_index": int(e), "event_date": dates[e],
                    "quarter": f"{dates[e][:4]}Q{(int(dates[e][5:7])-1)//3+1}",
                    "report_quarter": report_quarter, "classification": str(row["classification"]),
                    "sic2": sic2, "signal": score, "fwd_abret21": fwd})
    # One event per CIK and calendar event quarter for inferential consistency.
    out.sort(key=lambda x: (x["cik"], x["quarter"], x["event_index"]))
    unique = {}
    for row in out:
        unique.setdefault((row["cik"], row["quarter"]), row)
    return list(unique.values())


def quarterly_ic_series(rows: list[dict], *, require_forward=True) -> tuple[np.ndarray, list[str], list[int]]:
    quarters = sorted({str(r["quarter"]) for r in rows})
    values, used, counts = [], [], []
    for q in quarters:
        group = [r for r in rows if r["quarter"] == q and np.isfinite(r["signal"])
                 and (np.isfinite(r["fwd_abret21"]) or not require_forward)]
        if len(group) < 2:
            continue
        ic = float(spearmanr([r["signal"] for r in group], [r["fwd_abret21"] for r in group]).statistic)
        if np.isfinite(ic):
            values.append(ic); used.append(q); counts.append(len(group))
    return np.asarray(values, float), used, counts


def mechanism(rows: list[dict]) -> dict:
    ics, quarters, counts = quarterly_ic_series(rows)
    if len(ics) < 2:
        return {"mean_ic": float("nan"), "nw_t": float("nan"), "p": float("nan"),
                "quarters": quarters, "event_counts": counts, "pass": False}
    tval = float(newey_west_t(ics, NW_LAG))
    p = float(student_t.sf(tval, max(1, len(ics)-1)))
    mean = float(np.mean(ics))
    return {"mean_ic": mean, "nw_t": tval, "p": p, "quarters": quarters,
            "event_counts": counts, "pass": bool(mean > 0 and tval >= 2.0)}


def sic2_shuffle(rows: list[dict], draws=PLACEBO_DRAWS, seed=PLACEBO_SEED) -> dict:
    """Shuffle signal labels within calendar-quarter/SIC2 cells, preserving outcomes."""
    observed, quarters, _ = quarterly_ic_series(rows)
    if len(observed) < 2:
        raise ValueError("placebo requires at least two usable quarterly ICs")
    obs_mean = float(observed.mean())
    rng = np.random.default_rng(seed)
    null = np.empty(draws, float)
    for b in range(draws):
        fake = [dict(r) for r in rows]
        groups: dict[tuple[str, str], list[int]] = {}
        for i, r in enumerate(fake):
            if np.isfinite(r["signal"]) and np.isfinite(r["fwd_abret21"]):
                groups.setdefault((r["quarter"], r["sic2"]), []).append(i)
        for ids in groups.values():
            if len(ids) > 1:
                shuffled = rng.permutation([fake[i]["signal"] for i in ids])
                for i, value in zip(ids, shuffled):
                    fake[i]["signal"] = float(value)
        draw, _, _ = quarterly_ic_series(fake)
        null[b] = float(draw.mean())
    p = float((1 + np.sum(null >= obs_mean)) / (draws + 1))
    p95 = float(np.quantile(null, .95, method="linear"))
    return {"observed_mean_ic": obs_mean, "draws": null, "p95": p95, "p": p,
            "pass": bool(obs_mean > p95 and p < .05)}


def monthly_formations(dates: np.ndarray) -> np.ndarray:
    frame = pd.DataFrame({"date": dates})
    frame["month"] = frame.date.str[:7]
    ids = frame.groupby("month", sort=True).tail(1).index.to_numpy(dtype=int)
    return np.asarray([i for i in ids if FIRST_FORMATION <= dates[i] <= LAST_FORMATION and i + 1 < len(dates)], int)


def latest_scores(rows: list[dict], tickers: np.ndarray, dates: np.ndarray, formation: int) -> np.ndarray:
    """Latest event score, formed by close and live for no more than 21 sessions."""
    lookup = {str(t): i for i, t in enumerate(tickers)}
    score = np.full(len(tickers), np.nan)
    latest = np.full(len(tickers), -1, dtype=int)
    lo = max(0, formation - HORIZON + 1)
    for r in rows:
        e = int(r["event_index"])
        if r["ticker"] in lookup and lo <= e <= formation:
            i = lookup[r["ticker"]]
            if e > latest[i]:
                score[i] = float(r["signal"])
                latest[i] = e
    return score


def target_weights(score, roster_at_open, open_at_open, tickers, *, top_n=TOP_N):
    """Use the EW30 open-available roster for n, and only signal-valid names as candidates."""
    roster = np.asarray(roster_at_open, bool)
    op = np.asarray(open_at_open, float)
    sig = np.asarray(score, float)
    n = int(np.sum(roster & np.isfinite(op) & (op > 0)))
    k = min(int(top_n), n // 2)
    eligible = roster & np.isfinite(op) & (op > 0) & np.isfinite(sig)
    ids = np.flatnonzero(eligible)
    w = np.zeros(len(sig), float)
    if not len(ids) or k <= 0:
        return w, n, k, 0
    order = sorted(ids.tolist(), key=lambda i: (-float(sig[i]), str(tickers[i])))
    chosen = order[:min(k, len(order))]
    w[chosen] = 1.0 / len(chosen)
    return w, n, k, len(chosen)


def cap_turnover(current, target, cap=TURNOVER_CAP):
    cur, tgt = np.asarray(current, float), np.asarray(target, float)
    if cur.shape != tgt.shape or np.any(cur < -1e-12) or np.any(tgt < -1e-12):
        raise ValueError("weights must be aligned nonnegative vectors")
    turnover = float(np.sum(np.abs(tgt-cur)))
    scale = 1.0 if turnover <= cap else cap / turnover
    weights = cur + scale * (tgt-cur)
    return weights, float(np.sum(np.abs(weights-cur))), bool(scale < 1.0)


def stale_close_returns(close):
    """Decision-63 marking: carry last valid close, zero interim return, catch up later."""
    px = np.asarray(close, float)
    if px.ndim != 2:
        raise ValueError("close prices must be assets x sessions")
    out = np.zeros_like(px)
    last = np.full(px.shape[0], np.nan)
    for d in range(px.shape[1]):
        valid = np.isfinite(px[:, d]) & (px[:, d] > 0)
        both = valid & np.isfinite(last) & (last > 0)
        out[both, d] = px[both, d] / last[both] - 1
        last[valid] = px[valid, d]
    return out


def _simple_monthly_book(bundle, rows, *, cost_rate=COST_PER_SIDE):
    """K1 monthly books using J1's reviewed share-based decision-63 primitives."""
    dates, names = bundle["dates"], bundle["dow_tickers"]
    close, op, roster = (np.asarray(bundle["dow_close"], float),
                         np.asarray(bundle["dow_open"], float),
                         np.asarray(bundle["dow_roster"], bool))
    n, t = close.shape
    forms = monthly_formations(dates)
    if len(forms) < 2:
        raise ValueError("K1 requires at least two monthly formation/fill dates")
    signals = np.full((n, t), np.nan)
    for f in forms:
        signals[:, f] = latest_scores(rows, names, dates, int(f))
    fills = [int(f) + 1 for f in forms]
    first_form = int(forms[0])
    initial_ok = roster[:, first_form] & _j1_price_ok(close[:, first_form])
    if not np.any(initial_ok):
        raise ValueError("no available Dow holdings for initial EW30 staging")

    def simulate(strategy: bool):
        # Match r6_J1.run_j1's shares/cash state model and its reviewed exact
        # pending-open, stale-close, and last-close fallback primitives.
        start_weights = np.zeros(n, float)
        start_weights[initial_ok] = 1.0 / int(initial_ok.sum())
        shares = np.divide(start_weights, close[:, first_form], out=np.zeros(n), where=initial_ok)
        cash = 0.0
        last_close = np.full(n, np.nan)
        _j1_mark_close(close[:, first_form], last_close)
        pending = np.zeros(n, bool)
        prev_nav = 1.0
        rets, turns, fees, actives, binds, cohort_n, ks, selected_counts = [], [], [], [], [], [], [], []
        for q, (form, fill) in enumerate(zip(forms, fills)):
            form, fill = int(form), int(fill)
            # A stale holding is not silently dropped at formation. Queue it
            # and execute only when a valid open appears after the rebalance.
            pending |= (shares > 1e-14) & ~_j1_price_ok(close[:, form])
            px = op[:, fill]
            open_ok = _j1_price_ok(px)
            mark_open = np.where(open_ok, px, np.where(_j1_price_ok(last_close), last_close, 0.0))
            nav_before = cash + float(np.sum(shares * mark_open))
            forced_at_fill = pending & open_ok & (shares > 1e-14)
            shares, cash, pending, forced_notional, forced_fee = _j1_execute_pending_open(
                shares, cash, pending, px, cost_rate)
            nav_open = cash + float(np.sum(shares * mark_open))
            if nav_open <= 0:
                raise ValueError("K1 portfolio NAV reached zero")
            current = shares * mark_open / nav_open
            available = roster[:, fill] & open_ok
            n_available = int(available.sum())
            k = min(TOP_N, n_available // 2)
            locked = (shares > 1e-14) & ~open_ok
            target = np.zeros(n, float)
            target[locked] = current[locked]
            if strategy:
                elig = available & np.isfinite(signals[:, form]) & ~forced_at_fill
                ids = sorted(np.flatnonzero(elig).tolist(),
                             key=lambda i: (-float(signals[i, form]), str(names[i])))
                chosen = ids[:k] if k > 0 else []
                if chosen:
                    remainder = max(0.0, 1.0 - float(target[locked].sum()))
                    target[chosen] = remainder / len(chosen)
                # If no signal qualifies, the frozen rule is to hold cash;
                # stale locked positions remain until their queued valid-open sale.
                selected_counts.append(len(chosen))
            else:
                ids = np.flatnonzero(available & ~forced_at_fill)
                if len(ids):
                    remainder = max(0.0, 1.0 - float(target[locked].sum()))
                    target[ids] = remainder / len(ids)
            cohort_n.append(n_available); ks.append(k)

            def candidate(scale):
                weights = current + scale * (target - current)
                new_shares = shares.copy()
                new_shares[open_ok] = nav_open * weights[open_ok] / px[open_ok]
                notional = float(np.sum(np.abs(new_shares[open_ok] - shares[open_ok]) * px[open_ok]))
                nav_after = nav_open - cost_rate * notional
                return weights, new_shares, notional, nav_after

            cap = TURNOVER_CAP if strategy else 1.0
            full_turnover = (forced_notional + candidate(1.0)[2]) / max(nav_before, 1e-12)
            scale = 1.0
            if full_turnover > cap + 1e-12:
                lo, hi = 0.0, 1.0
                for _ in range(60):
                    mid = (lo + hi) / 2.0
                    if (forced_notional + candidate(mid)[2]) / max(nav_before, 1e-12) <= cap + 1e-12:
                        lo = mid
                    else:
                        hi = mid
                scale = lo
            weights, new_shares, notional, nav_after = candidate(scale)
            turnover = (forced_notional + notional) / max(nav_before, 1e-12)
            if strategy and turnover > TURNOVER_CAP + 1e-8:
                raise ArithmeticError("K1 total traded-notional turnover cap exceeded")
            turns.append(turnover); fees.append(forced_fee + nav_open - nav_after); binds.append(bool(scale < 1-1e-10))
            ew_target = np.zeros(n, float)
            ew_ids = np.flatnonzero(available)
            if len(ew_ids): ew_target[ew_ids] = 1.0 / len(ew_ids)
            actives.append(.5 * float(np.abs(weights - ew_target).sum()) if strategy else 0.0)
            shares = new_shares
            cash = nav_after - float(np.sum(shares * mark_open))

            # A holding excluded because this rebalance open is missing stays
            # carried and is queued for the first later valid open, exactly as
            # in J1's pending-sale path. This also covers missing-open rebalances
            # even where the formation close itself was valid.
            pending |= (shares > 1e-14) & ~open_ok
            next_fill = fills[q + 1] if q + 1 < len(fills) else t
            for d in range(fill, min(int(next_fill), t)):
                if d > fill:
                    open_ok_d = _j1_price_ok(op[:, d])
                    mark_open_d = np.where(open_ok_d, op[:, d], np.where(_j1_price_ok(last_close), last_close, 0.0))
                    nav_before_exit = cash + float(np.sum(shares * mark_open_d))
                    shares, cash, pending, delayed_notional, delayed_fee = _j1_execute_pending_open(
                        shares, cash, pending, op[:, d], cost_rate)
                    if delayed_notional:
                        turns.append(delayed_notional / max(nav_before_exit, 1e-12)); fees.append(delayed_fee)
                mark = _j1_mark_close(close[:, d], last_close)
                day_nav = cash + float(np.sum(shares * np.where(_j1_price_ok(mark), mark, 0.0)))
                rets.append(day_nav / max(prev_nav, 1e-12) - 1.0)
                prev_nav = day_nav
        pending |= (shares > 1e-14) & ~_j1_price_ok(close[:, -1])
        terminal_fallback_names = int(np.sum(pending & (shares > 1e-14) & _j1_price_ok(last_close)))
        # Reuse J1's exact end-of-sample sale-at-last-valid-close accounting.
        shares, cash, pending, terminal_notional, terminal_fee = _j1_execute_pending_close(
            shares, cash, pending, last_close, cost_rate)
        if terminal_notional:
            before = prev_nav
            after = before - terminal_fee
            if rets:
                prior = before / max(1 + rets[-1], 1e-12)
                rets[-1] = after / prior - 1.0
            turns.append(terminal_notional / max(before, 1e-12)); fees.append(terminal_fee)
        return {"returns": np.asarray(rets, float), "turnover": np.asarray(turns, float),
                "costs": np.asarray(fees, float), "active_share": np.asarray(actives, float),
                "cap_binds": np.asarray(binds, bool), "n": cohort_n, "k": ks,
                "selected": selected_counts, "terminal_fallback_names": terminal_fallback_names}

    strategy = simulate(True)
    benchmark = simulate(False)
    return {"strategy_returns": strategy["returns"], "ew_returns": benchmark["returns"],
            "turnover": strategy["turnover"], "costs": strategy["costs"],
            "active_share": strategy["active_share"], "cap_binds": strategy["cap_binds"],
            "n": strategy["n"], "k": strategy["k"], "selected": strategy["selected"],
            "ew_turnover": benchmark["turnover"], "ew_costs": benchmark["costs"],
            "terminal_stale_fallback_names": strategy["terminal_fallback_names"],
            "benchmark_terminal_stale_fallback_names": benchmark["terminal_fallback_names"]}

def _read_holm(path, current_p):
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    manifest=obj.get("manifest",[]); pvals=obj.get("p_values",{})
    if (not isinstance(manifest,list) or not manifest
            or any(not isinstance(x,str) for x in manifest)
            or len(set(manifest)) != len(manifest)):
        raise ValueError("R6 Holm manifest must be a nonempty list of unique endpoint IDs")
    digest=hashlib.sha256(json.dumps(manifest).encode("utf-8")).hexdigest()
    if digest != obj.get("manifest_sha256") or not set(ENDPOINTS).issubset(manifest):
        raise ValueError("R6 Holm manifest/hash must include K1 H16-H18 before execution")
    if not isinstance(pvals,dict) or set(pvals) != set(manifest):
        raise ValueError("Holm p_values must include every manifest endpoint; null means unrun")
    current_p = {} if current_p is None else current_p
    if not isinstance(current_p,dict) or not set(current_p).issubset(set(ENDPOINTS)):
        raise ValueError("current K1 p-values may only fill H16-H18")
    full={}
    for endpoint in manifest:
        # A result from this execution takes precedence for K1 slots. Otherwise
        # retain registered prior results; a null slot is unrun and maps to 1
        # only for Holm accounting (the reported raw value remains null).
        value = current_p.get(endpoint)
        if value is None:
            value = pvals[endpoint]
        full[endpoint] = 1.0 if value is None else float(value)
        if not 0 <= full[endpoint] <= 1:
            raise ValueError(f"invalid Holm p-value for {endpoint}: {value}")
    return holm_correction(full)


def _r6_variant_count(path: str | Path) -> int:
    text=Path(path).read_text(encoding="utf-8")
    section="## R6 Holm family"
    if section not in text:
        raise ValueError("trial log lacks the R6 variant registry section")
    text=text.split(section,1)[1]
    ids=set(re.findall(r"\b([A-Z]\d+-V1)\b",text))
    if "K1-V1" not in ids:
        raise ValueError("K1-V1 must be registered in specs/r4_trials.md before outcome execution")
    return len(ids)


def _governance_preflight(events_path, inputs_path, manifest_path, holm_path, trial_log):
    """Validate governance and every pinned input before any forward label is formed."""
    _, digest = validate_frozen_prereg(PREREG)
    if digest.lower() != EXPECTED_PREREG_SHA256:
        raise ValueError("K1 prereg canonical hash differs from the reviewed digest")
    prereg_diff_payload().require_match()

    manifest = validate_input_manifest(manifest_path)
    expected_events = (ROOT / manifest["files"]["events"]["path"]).resolve()
    if Path(events_path).resolve() != expected_events:
        raise InputManifestError("event clock path must be the file pinned by the input manifest")
    expected_prices = (ROOT / manifest["files"]["prices"]["path"]).resolve()
    if Path(inputs_path).resolve() != expected_prices:
        raise InputManifestError("price bundle path must be the file pinned by the input manifest")

    trial_count = _r6_variant_count(trial_log)
    # Calling with an empty current-result map verifies Holm schema/hash and all
    # p-value slots before make_event_rows can compute any forward outcomes.
    _read_holm(holm_path, {})
    holm_config = json.loads(Path(holm_path).read_text(encoding="utf-8"))
    bundle = load_price_bundle(inputs_path)
    events = pd.read_csv(events_path, dtype={"cik":str,"ticker":str})
    required={"cik","ticker","report_date","acceptance_timestamp_et","classification"}
    if not required.issubset(events.columns):
        raise InputManifestError(f"event clock lacks required columns: {sorted(required-events.columns)}")
    return manifest, bundle, events, trial_count, holm_config


def analyze(events_path=EVENTS, inputs_path=INPUTS, manifest_path=INPUT_MANIFEST,
            holm_path=HOLM_CONFIG, trial_log=TRIAL_LOG):
    manifest,bundle,events,trial_count,holm_config = _governance_preflight(
        events_path, inputs_path, manifest_path, holm_path, trial_log)
    sp_rows=make_event_rows(events,bundle,"sp500")
    dow_rows=make_event_rows(events,bundle,"dow")
    mech=mechanism(sp_rows)
    placebo=sic2_shuffle(sp_rows)
    portfolio=None
    pvals={"R6-H16":mech["p"],"R6-H17":placebo["p"],"R6-H18":None}
    if mech["pass"] and placebo["pass"]:
        portfolio=_simple_monthly_book(bundle,dow_rows)
        p,boot=circular_block_bootstrap_pvalue(portfolio["strategy_returns"],portfolio["ew_returns"],
            block_length=BOOTSTRAP_BLOCK,n_draws=BOOTSTRAP_DRAWS,seed=BOOTSTRAP_SEED)
        sr=portfolio["strategy_returns"]; er=portfolio["ew_returns"]
        annual_sharpe=lambda x: float(np.mean(x)/np.std(x,ddof=0)*math.sqrt(252)) if np.std(x,ddof=0) else 0.0
        portfolio.update({"bootstrap_p":float(p),"bootstrap_draws":boot,
            "net_excess":float(np.prod(1+sr)-np.prod(1+er)),"net_sharpe":annual_sharpe(sr),
            "ew_sharpe":annual_sharpe(er),"dsr":float(deflated_sharpe_ratio(sr,trial_count)),
            "trial_count":trial_count,"active_share_mean":float(np.mean(portfolio["active_share"])) if len(portfolio["active_share"]) else 0.0})
        portfolio["max_rebalance_turnover"] = float(np.max(portfolio["turnover"])) if len(portfolio["turnover"]) else 0.0
        portfolio["criterion4_raw_pass"] = bool(
            portfolio["net_excess"] > 0
            and portfolio["net_sharpe"] > portfolio["ew_sharpe"]
            and portfolio["active_share_mean"] >= ACTIVE_SHARE_MIN
            and portfolio["max_rebalance_turnover"] <= TURNOVER_CAP + 1e-12
        )
        pvals["R6-H18"]=float(p)
    holm=_read_holm(holm_path,pvals)
    holm_status = {
        endpoint: ("not run" if pvals.get(endpoint) is None
                   and holm_config["p_values"].get(endpoint) is None else "computed")
        for endpoint in holm_config["manifest"]
    }
    result={"approach":"K1","prereg_sha256":prereg_digest(PREREG.read_text(encoding="utf-8")),
        "input_manifest_sha256":sha256_file(manifest_path),"mechanism":mech,"placebo":placebo,
        "portfolio":portfolio,"holm":holm,"holm_status":holm_status,
        "status":"complete" if portfolio is not None else "portfolio_not_run"}
    RESULTS.parent.mkdir(parents=True,exist_ok=True)
    RESULTS.write_text(json.dumps(_jsonable(result),indent=2),encoding="utf-8")
    rows=[]
    for endpoint, raw in pvals.items():
        adj=holm[endpoint]
        rows.append({"endpoint":endpoint,"raw_p":raw,"raw_gate_pass":(mech["pass"] if endpoint=="R6-H16" else placebo["pass"] if endpoint=="R6-H17" else bool(portfolio and portfolio.get("criterion4_raw_pass",False))),
            "holm_p":adj["holm_p"],"holm_reject":adj["reject"],"status":"not run" if raw is None else "computed"})
    with ENDPOINT_LOG.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    return result


def _jsonable(obj):
    if isinstance(obj,np.ndarray): return obj.tolist()
    if isinstance(obj,(np.integer,)): return int(obj)
    if isinstance(obj,(np.floating,)): return float(obj)
    if isinstance(obj,dict): return {k:_jsonable(v) for k,v in obj.items()}
    if isinstance(obj,(list,tuple)): return [_jsonable(v) for v in obj]
    return obj


@guarded_runner(prereg_path=PREREG,run_dir=RUN_DIR,lock_name=".k1-run.lock")
def _execute(*, output_dir=RUN_DIR, prereg_dir=PREREG.parent,
             trial_log=TRIAL_LOG, analysis_kwargs=None):
    frozen_date,digest=validate_frozen_prereg(PREREG)
    if digest.lower()!=EXPECTED_PREREG_SHA256:
        raise ValueError("K1 prereg canonical hash differs from the reviewed digest")
    diff=prereg_diff_payload(); diff.require_match()
    result=analyze(**(analysis_kwargs or {}))
    out=Path(output_dir)
    out.mkdir(parents=True,exist_ok=True)
    result_path=out/"K1_RESULTS.json"
    result_path.write_text(json.dumps(_jsonable(result),indent=2,allow_nan=False)+"\n",encoding="utf-8")
    portfolio=result.get("portfolio")
    portfolio_summary=("not_run" if portfolio is None else
                       f"net_excess={portfolio.get('net_excess')}; bootstrap_p={portfolio.get('bootstrap_p')}")
    print(f"K1 run: status={result['status']}; mechanism_pass={result['mechanism']['pass']}; "
          f"placebo_pass={result['placebo']['pass']}; portfolio={portfolio_summary}; result={result_path}")
    append_trial("K1","K1-V1",f"K1-V1: status={result['status']}; prereg={digest}",
                 prereg_dir=prereg_dir,trial_log=trial_log)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute",action="store_true",help="explicit coordinator-authorized development execution")
    args=parser.parse_args(argv)
    _execute(execute=args.execute)


if __name__=="__main__":
    main()
