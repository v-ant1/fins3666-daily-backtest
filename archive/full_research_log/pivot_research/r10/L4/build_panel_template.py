#!/usr/bin/env python3
"""Build an R10 2010–2015 panel in the staged development NPZ schema.

Input is a long CSV with columns: universe,date,asset,roster,sic2,
adjusted_open,adjusted_close. `universe` is `sp500` or `dow`. The builder
creates schema-compatible arrays and writes only coverage/count metadata and
the output digest to its report. It does not calculate or display returns.

This is a template. It was not run against historical data in this dispatch.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

START = "2010-01-04"
END = "2015-12-31"
GROUPS = ("sp500", "dow")
FIELDS = ("universe", "date", "asset", "roster", "sic2", "adjusted_open", "adjusted_close")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def build(csv_path: Path, output_path: Path, report_path: Path) -> dict:
    dates: set[str] = set()
    assets: dict[str, set[str]] = {g: set() for g in GROUPS}
    rows: dict[tuple[str, str, str], tuple[bool, str, float, float]] = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or not set(FIELDS).issubset(reader.fieldnames):
            raise ValueError(f"source CSV must contain columns: {', '.join(FIELDS)}")
        for row in reader:
            group, date, asset = row["universe"].strip().lower(), row["date"].strip(), row["asset"].strip().upper()
            if group not in GROUPS:
                raise ValueError("universe must be sp500 or dow")
            if not START <= date <= END:
                raise ValueError("source date falls outside the frozen 2010–2015 interval")
            if not asset or len(asset) > 5:
                raise ValueError("asset labels must contain 1–5 characters to match the dev NPZ dtype")
            sic = row["sic2"].strip()
            if sic and (len(sic) != 2 or not sic.isdigit()):
                raise ValueError("SIC2 must be blank or exactly two digits")
            roster = row["roster"].strip().lower() in {"1", "true", "yes"}
            op = float(row["adjusted_open"]) if row["adjusted_open"].strip() else np.nan
            cl = float(row["adjusted_close"]) if row["adjusted_close"].strip() else np.nan
            key = (group, date, asset)
            if key in rows:
                raise ValueError("duplicate universe/date/asset row in source CSV")
            rows[key] = (roster, sic, op, cl)
            dates.add(date)
            assets[group].add(asset)

    axis = np.array(sorted(dates), dtype="<U10")
    if axis.size < 2:
        raise ValueError("source must provide at least two shared session dates")
    if not np.all(axis[:-1] < axis[1:]):
        raise ValueError("session dates must be unique and increasing")
    if str(axis[0]) != START or str(axis[-1]) != END:
        raise ValueError("source must span the complete frozen interval 2010-01-04 through 2015-12-31")
    panel: dict[str, np.ndarray] = {}
    coverage = {}
    for group in GROUPS:
        names = np.array(sorted(assets[group]), dtype="<U5")
        n, t = len(names), len(axis)
        roster = np.zeros((n, t), dtype=bool)
        sic = np.full((n, t), "", dtype="<U2")
        op = np.full((n, t), np.nan, dtype=np.float64)
        cl = np.full((n, t), np.nan, dtype=np.float64)
        name_ix = {v: i for i, v in enumerate(names.tolist())}
        date_ix = {v: i for i, v in enumerate(axis.tolist())}
        for (g, date, asset), (member, sic2, open_px, close_px) in rows.items():
            if g != group:
                continue
            i, j = name_ix[asset], date_ix[date]
            roster[i, j], sic[i, j], op[i, j], cl[i, j] = member, sic2, open_px, close_px
        prefix = group
        panel[f"{prefix}_dates"] = axis
        panel[f"{prefix}_assets"] = names
        panel[f"{prefix}_roster"] = roster
        panel[f"{prefix}_sic2"] = sic
        panel[f"{prefix}_adjusted_open"] = op
        panel[f"{prefix}_adjusted_close"] = cl
        has_bars = np.any(np.isfinite(op) & np.isfinite(cl), axis=1) if n else np.zeros(0, dtype=bool)
        coverage[group] = {
            "asset_count": int(n),
            "member_days": int(roster.sum()),
            "assets_with_any_adjusted_open_close": int(has_bars.sum()),
            "assets_missing_all_adjusted_open_close": int((~has_bars).sum()),
            "sic2_member_day_coverage": float((np.count_nonzero((sic != "") & roster) / roster.sum()) if roster.sum() else 0.0),
        }

    if not np.array_equal(panel["sp500_dates"], panel["dow_dates"]):
        raise ValueError("S&P and Dow date axes must match")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path, **panel)
    digest = sha256(output_path)
    report = {
        "period_bounds": {"start": str(axis[0]), "end": str(axis[-1])},
        "requested_period": {"start": START, "end": END},
        "session_count": int(len(axis)),
        "schema": {k: {"shape": list(v.shape), "dtype": str(v.dtype)} for k, v in panel.items()},
        "coverage_counts": coverage,
        "panel_sha256": digest,
        "price_or_return_values_emitted": False,
        "source_sha256": sha256(csv_path),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-csv", required=True, type=Path)
    parser.add_argument("--output-npz", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source_csv, args.output_npz, args.report), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
