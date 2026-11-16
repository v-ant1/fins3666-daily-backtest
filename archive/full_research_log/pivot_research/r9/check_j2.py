#!/usr/bin/env python3
"""Independent, development-only replay of R9-V0, V4, and selected V5.

This implementation uses the frozen R9 variant log and J2 rules, but does not
import or call j2_variants.py. It reads the coordinator-provided price archive
that contains only dates from 2020-11-27 onward. For the score parquet it reads
only row groups whose metadata proves every record is on or after that cutoff.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

FIRST_DATE = "2020-11-27"
LAST_DATE = "2026-10-30"
COMMON_START = "2021-03-04"
COST_RATE = 0.0005
PRICE_SHA256 = "58f82f61d0947e5174cf7c47cc319cde5c59942b1b59c607159e7eeae98f6153"
OFFICIAL_VARIANTS = ("R9-V0", "R9-V4", "R9-V5")
TOL_EXCESS = 0.003  # 0.3 percentage points in decimal-return units
TOL_SHARPE = 0.02


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def date_value(value) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def validate_pre_run_log(root: Path, official: dict) -> str:
    log_path = root / "specs" / "r9_variant_log.md"
    digest = sha256(log_path)
    expected_digest = official.get("input_sha256", {}).get("r9_variant_log")
    if digest != expected_digest:
        raise ValueError("variant log hash does not match the one recorded by the variant run")
    text = log_path.read_text(encoding="utf-8")
    logged = set(re.findall(r"(?m)^\|\s*(R9-V\d+)\s*\|\s*(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)\s*\|", text))
    ids = {variant_id for variant_id, _ in logged}
    required = {f"R9-V{i}" for i in range(12)}
    if ids != required:
        raise ValueError(f"pre-run log must contain exactly V0 through V11; found {sorted(ids)}")
    for variant_id in OFFICIAL_VARIANTS:
        rows = [stamp for ident, stamp in logged if ident == variant_id]
        if len(rows) != 1:
            raise ValueError(f"expected exactly one pre-run row for {variant_id}")
    official_ids = {r["id"] for r in official.get("variants", [])}
    if official_ids != required:
        raise ValueError("official development output does not contain the 12 logged candidates")
    return digest


def read_development_scores(path: Path) -> dict[str, dict[str, dict]]:
    """Read only row groups proven by parquet stats to be post-cutoff."""
    pf = pq.ParquetFile(path)
    columns = pf.schema.names
    if "formation_date" not in columns or "universe" not in columns:
        raise ValueError("score bundle lacks formation_date/universe columns")
    date_col = columns.index("formation_date")
    post_groups = []
    for group_i in range(pf.metadata.num_row_groups):
        col_meta = pf.metadata.row_group(group_i).column(date_col)
        stats = col_meta.statistics
        if stats is None or stats.min is None or stats.max is None:
            raise ValueError("cannot establish development-only row group bounds from metadata")
        lo, hi = date_value(stats.min), date_value(stats.max)
        if hi < FIRST_DATE:
            continue
        if lo < FIRST_DATE:
            raise ValueError(
                f"score row group {group_i} spans pre-cutoff dates; refusing to read it"
            )
        if lo > LAST_DATE:
            continue
        post_groups.append(group_i)
    if not post_groups:
        raise ValueError("no score rows in the authorized development window")
    table = pf.read_row_groups(
        post_groups,
        columns=["universe", "formation_date", "ticker", "relative_return", "relative_return_mask"],
    )
    frame = table.to_pandas()
    frame = frame[(frame["universe"] == "dow")
                  & (frame["formation_date"].astype(str) >= FIRST_DATE)
                  & (frame["formation_date"].astype(str) <= LAST_DATE)]
    frame["formation_date"] = frame["formation_date"].astype(str).str[:10]
    rows: dict[str, dict[str, dict]] = {}
    for d, group in frame.groupby("formation_date", sort=True):
        rows[d] = {
            str(r.ticker): {
                "score": r.relative_return,
                "valid": bool(r.relative_return_mask),
            }
            for r in group.itertuples(index=False)
        }
    return rows


def current_score_rows(form_date, score_rows, ticker_to_i, eligible):
    out = []
    for ticker, row in score_rows.get(form_date, {}).items():
        j = ticker_to_i.get(ticker)
        score = row["score"]
        if j is None or not eligible[j] or not row["valid"] or pd.isna(score):
            continue
        score = float(score)
        if np.isfinite(score):
            out.append((score, ticker, j))
    out.sort(key=lambda x: (x[0], x[1]))
    return out


def target_for_variant(variant, form_date, score_rows, history_dates, ticker_to_i,
                       eligible, current_weights, current_names):
    rows = current_score_rows(form_date, score_rows, ticker_to_i, eligible)
    if variant["kind"] == "smooth":
        pos = history_dates.index(form_date)
        window = variant["window"]
        if pos + 1 < window:
            return None, current_names
        available = []
        for _, ticker, j in rows:
            history = []
            valid = True
            for d in history_dates[pos - window + 1:pos + 1]:
                row = score_rows.get(d, {}).get(ticker)
                if row is None or not row["valid"] or pd.isna(row["score"]):
                    valid = False
                    break
                value = float(row["score"])
                if not np.isfinite(value):
                    valid = False
                    break
                history.append(value)
            if valid:
                available.append((float(np.mean(history)), ticker, j))
        rows = sorted(available, key=lambda x: (x[0], x[1]))
    k = 5
    if len(rows) < k:
        return None, current_names
    chosen = [j for _, _, j in rows[:k]]
    target = np.zeros_like(current_weights)
    target[chosen] = 1.0 / k
    if variant["kind"] == "j1_cap":
        requested = float(np.abs(target - current_weights).sum())
        if requested > 0.50:
            target = current_weights + (0.50 / requested) * (target - current_weights)
    return target, target > 1e-12


def simulate(variant, dates, roster, opens, closes, tickers, score_rows, history_dates):
    date_to_i = {str(d): i for i, d in enumerate(dates)}
    ticker_to_i = {name: i for i, name in enumerate(tickers)}
    forms = sorted((date_to_i[d], d) for d in score_rows
                   if d in date_to_i and COMMON_START <= d <= LAST_DATE)
    if not forms:
        raise ValueError("no scheduled formations on the common development window")
    first_i, _ = forms[0]
    if str(dates[first_i]) != COMMON_START:
        raise ValueError(f"expected common first formation {COMMON_START}, got {dates[first_i]}")
    member = roster[:, first_i] & np.isfinite(closes[:, first_i]) & (closes[:, first_i] > 0)
    if not member.any():
        raise ValueError("no PIT Dow members for the common initial book")
    weights = np.zeros(len(tickers), dtype=float)
    weights[member] = 1.0 / int(member.sum())
    active_names = member.copy()
    last_close = closes[:, first_i].copy()
    last_close[~(np.isfinite(last_close) & (last_close > 0))] = np.nan
    nav = 1.0
    daily = []
    form_by_index = {i: d for i, d in forms}

    for day in range(first_i + 1, len(dates)):
        open_px = opens[:, day]
        valid_open = np.isfinite(open_px) & (open_px > 0)
        overnight_ret = np.zeros(len(tickers), dtype=float)
        can_mark = valid_open & np.isfinite(last_close)
        overnight_ret[can_mark] = open_px[can_mark] / last_close[can_mark] - 1.0
        overnight = float(np.dot(weights, overnight_ret))
        nav_open = nav * (1.0 + overnight)
        open_weights = weights * (1.0 + overnight_ret)
        if open_weights.sum() > 0:
            open_weights /= open_weights.sum()

        cost_fraction = 0.0
        form_date = form_by_index.get(day - 1)
        if form_date is not None:
            eligible = roster[:, day - 1] & valid_open
            if variant["kind"] == "benchmark":
                target = np.zeros_like(open_weights)
                if eligible.any():
                    target[eligible] = 1.0 / int(eligible.sum())
                target_names = eligible.copy()
            else:
                target, target_names = target_for_variant(
                    variant, form_date, score_rows, history_dates, ticker_to_i,
                    eligible, open_weights, active_names,
                )
            if target is not None:
                turnover = float(np.abs(target - open_weights).sum())
                cost_fraction = turnover * COST_RATE
                open_weights = target
                active_names = target_names

        close_px = closes[:, day]
        valid_close = np.isfinite(close_px) & (close_px > 0)
        intraday_ret = np.zeros(len(tickers), dtype=float)
        valid_pair = valid_close & valid_open
        intraday_ret[valid_pair] = close_px[valid_pair] / open_px[valid_pair] - 1.0
        gross_intraday = float(np.dot(open_weights, intraday_ret))
        net_return = (1.0 + overnight - cost_fraction) * (1.0 + gross_intraday) - 1.0
        daily.append({"date": str(dates[day]), "net": net_return})
        nav *= 1.0 + net_return
        last_close[valid_close] = close_px[valid_close]
        weights = open_weights * (1.0 + intraday_ret)
        if weights.sum() > 0:
            weights /= weights.sum()
    return daily


def metrics(strategy, benchmark):
    s = np.asarray([r["net"] for r in strategy], dtype=float)
    b = np.asarray([r["net"] for r in benchmark], dtype=float)
    if len(s) != len(b):
        raise ValueError("strategy and benchmark daily return lengths differ")
    if [r["date"] for r in strategy] != [r["date"] for r in benchmark]:
        raise ValueError("strategy and benchmark dates do not align")
    total_s = float(np.prod(1.0 + s) - 1.0)
    total_b = float(np.prod(1.0 + b) - 1.0)
    sharpe_s = float(np.sqrt(252.0) * np.mean(s) / np.std(s, ddof=1))
    sharpe_b = float(np.sqrt(252.0) * np.mean(b) / np.std(b, ddof=1))
    return {"net_excess_return": total_s - total_b,
            "strategy_net_sharpe": sharpe_s,
            "ew30_net_sharpe": sharpe_b,
            "n_daily": len(s)}


def main():
    root = Path(__file__).resolve().parents[1]
    report_path = root / "r9" / "R9_VARIANTS.json"
    input_path = root / "r9" / "data" / "J2_DEV_FROM_20201127.npz"
    scores_path = root / "r6_J1" / "signal_bundle.parquet"
    j2_rules_path = root / "specs" / "r9_prereg" / "J2.md"
    if not j2_rules_path.is_file():
        raise ValueError("frozen J2 rules text is missing")
    rules = j2_rules_path.read_text(encoding="utf-8")
    if "R9-V5" not in rules or "previous three scheduled weekly formation dates" not in rules:
        raise ValueError("J2 rules do not describe the selected four-formation smoothing variant")

    official = json.loads(report_path.read_text(encoding="utf-8"))
    log_hash = validate_pre_run_log(root, official)
    input_hash = sha256(input_path)
    if input_hash != PRICE_SHA256:
        raise ValueError("coordinator-provided development-only price archive hash mismatch")
    z = np.load(input_path, allow_pickle=False)
    dates = z["dow_dates"].astype(str)
    if dates[0] != FIRST_DATE or dates[-1] != LAST_DATE:
        raise ValueError("development-only price date bounds do not match the authorized period")
    tickers = z["dow_assets"].astype(str).tolist()
    ticker_to_i = {name: i for i, name in enumerate(tickers)}
    roster = z["dow_roster"]
    opens = z["dow_adjusted_open"]
    closes = z["dow_adjusted_close"]
    score_rows = read_development_scores(scores_path)
    if min(score_rows) < FIRST_DATE or max(score_rows) > LAST_DATE:
        raise ValueError("filtered score rows contain a date outside the development window")
    history_dates = sorted(score_rows)

    benchmark = simulate({"kind": "benchmark"}, dates, roster, opens, closes,
                         tickers, score_rows, history_dates)
    own = {}
    for variant_id, variant in (("R9-V0", {"kind": "j1_cap"}),
                                ("R9-V4", {"kind": "smooth", "window": 3}),
                                ("R9-V5", {"kind": "smooth", "window": 4})):
        own[variant_id] = metrics(
            simulate(variant, dates, roster, opens, closes, tickers, score_rows, history_dates),
            benchmark,
        )

    official_by_id = {row["id"]: row for row in official["variants"]}
    checks = []
    for variant_id in OFFICIAL_VARIANTS:
        expected = official_by_id[variant_id]
        got = own[variant_id]
        excess_delta = got["net_excess_return"] - float(expected["net_excess_return"])
        sharpe_delta = got["strategy_net_sharpe"] - float(expected["strategy_net_sharpe"])
        ew_sharpe_delta = got["ew30_net_sharpe"] - float(expected["ew30_net_sharpe"])
        checks.append({
            "variant": variant_id,
            "independent_excess_return": got["net_excess_return"],
            "official_excess_return": float(expected["net_excess_return"]),
            "excess_difference_pp": excess_delta * 100.0,
            "independent_strategy_net_sharpe": got["strategy_net_sharpe"],
            "official_strategy_net_sharpe": float(expected["strategy_net_sharpe"]),
            "strategy_sharpe_difference": sharpe_delta,
            "independent_ew30_net_sharpe": got["ew30_net_sharpe"],
            "official_ew30_net_sharpe": float(expected["ew30_net_sharpe"]),
            "ew30_sharpe_difference": ew_sharpe_delta,
            "net_excess_within_0_3pp": abs(excess_delta) <= TOL_EXCESS,
            "strategy_sharpe_within_0_02": abs(sharpe_delta) <= TOL_SHARPE,
            "ew30_sharpe_within_0_02": abs(ew_sharpe_delta) <= TOL_SHARPE,
            "daily_observations": got["n_daily"],
        })

    overall = all(row["net_excess_within_0_3pp"] and row["strategy_sharpe_within_0_02"]
                  and row["ew30_sharpe_within_0_02"] for row in checks)
    lines = [
        "# Independent J2 development replay check",
        "",
        "This checker independently replayed R9-V0 (J1 baseline), R9-V4 (three-formation smoothing), and selected R9-V5 (four-formation smoothing) from the frozen variant log and J2 rules. It did not import `j2_variants.py`; it used only the development-only price archive and score rows proven by Parquet metadata to be dated on or after 2020-11-27.",
        "",
        f"Pre-run log SHA-256 matched the variant-run record: `{log_hash}`. The log contains exactly R9-V0 through R9-V11, each with one pre-run timestamp. The price archive matched the coordinator-supplied SHA-256 and its date axis was exactly {FIRST_DATE} through {LAST_DATE}. The shared evaluation start was {COMMON_START}.",
        "",
        f"**Agreement:** {'PASS' if overall else 'FAIL'} (tolerances: net excess ±0.3 percentage points; strategy and benchmark Sharpe ±0.02).",
        "",
        "| Variant | Independent net excess | Logged net excess | Difference | Independent strategy Sharpe | Logged strategy Sharpe | Sharpe difference | Result |",
        "|---|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for row in checks:
        status = "Pass" if row["net_excess_within_0_3pp"] and row["strategy_sharpe_within_0_02"] else "Fail"
        lines.append(
            f"| {row['variant']} | {row['independent_excess_return']:.4%} | {row['official_excess_return']:.4%} | {row['excess_difference_pp']:+.3f} pp | {row['independent_strategy_net_sharpe']:.4f} | {row['official_strategy_net_sharpe']:.4f} | {row['strategy_sharpe_difference']:+.4f} | {status} |"
        )
    lines += [
        "",
        "The EW30 Sharpe comparison is also checked against the shared official benchmark for each variant; it must agree within 0.02. The selected J2 candidate is R9-V5. This is a development-only reproducibility check, not holdout evidence.",
        "",
        "No sealed holdout file or pre-2020-11-27 data rows were opened. The holdout runner was tested only with synthetic inputs; the approval file is absent and no holdout run was attempted.",
        "",
    ]
    (root / "r9" / "R9_CHECK.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    if not overall:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
