from __future__ import annotations

import csv
import json
import math
import re
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import numpy as np
import requests
from dotenv import dotenv_values
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parents[1]
ROSTER = ROOT / "r6_data" / "sp500_pit_roster.csv"
PANEL = ROOT / "r9" / "data" / "J2_DEV_FROM_20201127.npz"
ENV_PATH = Path(r"C:\Users\musta\Desktop\UNSW\SSI\FINS3666\A2\.env")
OUT_JSON = ROOT / "r9" / "S2_INDEX_ADD_DEV_results.json"
START = date(2020, 11, 27)
END = date(2026, 10, 30)
API_ROOT = "https://data.alpaca.markets/v2/stocks"
NY = ZoneInfo("America/New_York")
CEG_RELEASE = (
    "https://press.spglobal.com/2022-01-26-Constellation-Energy-Set-to-Join-"
    "S-P-500-Others-to-Join-S-P-MidCap-400-and-S-P-SmallCap-600"
)


def dated_public_snp_url(url: str) -> bool:
    return any(host in url.lower() for host in ("spglobal.com", "spindices.com"))


def announcement_date_from_url(url: str) -> date | None:
    patterns = (
        r"(?<!\d)(20\d{2})-(\d{2})-(\d{2})(?=[-/])",
        r"(?<!\d)(20\d{2})(\d{2})(\d{2})-\d{5,}(?=/)",
    )
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            try:
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                return None
    return None


def api_symbol(ticker: str) -> str:
    return {"BF-B": "BF.B", "BRK-B": "BRK.B"}.get(ticker.upper(), ticker.upper())


def prepare_roster() -> list[dict[str, str]]:
    with ROSTER.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    for name in ("announcement_date", "announcement_source_url"):
        if name not in fieldnames:
            fieldnames.append(name)

    for row in rows:
        url = row.get("start_source", "").strip()
        if row.get("ticker", "").strip().upper() == "CEG" and row.get("effective_from") == "2022-02-02":
            url = CEG_RELEASE
            row["start_source"] = url
        announced = announcement_date_from_url(url) if dated_public_snp_url(url) else None
        effective = date.fromisoformat(row["effective_from"][:10])
        if START <= effective <= END and announced is not None:
            row["announcement_date"] = announced.isoformat()
            row["announcement_source_url"] = url
        else:
            row["announcement_date"] = ""
            row["announcement_source_url"] = ""

    with ROSTER.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    events: list[dict[str, str]] = []
    for row in rows:
        ticker = row.get("ticker", "").strip().upper()
        if not ticker:
            continue
        try:
            effective = date.fromisoformat(row["effective_from"][:10])
            announced = date.fromisoformat(row["announcement_date"])
        except (ValueError, TypeError):
            continue
        source = row.get("announcement_source_url", "").strip()
        if not source or not (START <= announced <= END and START <= effective <= END):
            continue
        if announced >= effective:
            continue
        refs = row.get("source_refs", "").lower()
        # A documented issuer ticker change is not a new addition event.
        if "issuer ticker change" in refs and effective.isoformat() in refs:
            continue
        events.append(
            {
                "ticker": ticker,
                "company": row.get("company", ""),
                "announcement_date": announced.isoformat(),
                "effective_date": effective.isoformat(),
                "announcement_source_url": source,
            }
        )
    # A ticker/effective-date pair is one roster event even if the source has duplicate lines.
    unique: dict[tuple[str, str], dict[str, str]] = {}
    for event in events:
        unique[(event["ticker"], event["effective_date"])] = event
    return sorted(unique.values(), key=lambda e: (e["announcement_date"], e["effective_date"], e["ticker"]))


def load_api_headers() -> dict[str, str]:
    env = dotenv_values(ENV_PATH)
    key = env.get("ALPACA_API_KEY")
    secret = env.get("ALPACA_SECRET_KEY")
    if not key or not secret:
        raise RuntimeError("Required Alpaca credential pair is unavailable in the configured dotenv file")
    return {"APCA-API-KEY-ID": str(key), "APCA-API-SECRET-KEY": str(secret), "accept": "application/json"}


def fetch_symbol_bars(session: requests.Session, headers: dict[str, str], ticker: str,
                      start: date, end: date) -> dict[date, tuple[float, float]]:
    if start < START or end > END:
        raise RuntimeError("Refusing a direct-price request outside the authorized development boundary")
    symbol = quote(api_symbol(ticker), safe=".")
    params = {
        "timeframe": "1Day",
        "start": f"{start.isoformat()}T00:00:00Z",
        "end": f"{end.isoformat()}T23:59:59Z",
        "feed": "sip",
        "adjustment": "all",
        "limit": 1000,
        "sort": "asc",
    }
    result: dict[date, tuple[float, float]] = {}
    token: str | None = None
    for _ in range(10):
        request_params = dict(params)
        if token:
            request_params["page_token"] = token
        response = session.get(f"{API_ROOT}/{symbol}/bars", params=request_params, headers=headers, timeout=60)
        if not response.ok:
            raise RuntimeError(f"Alpaca GET failed for {ticker}: HTTP {response.status_code}")
        payload = response.json()
        for bar in payload.get("bars", []):
            stamp = datetime.fromisoformat(bar["t"].replace("Z", "+00:00"))
            day = stamp.astimezone(NY).date()
            if start <= day <= end:
                result[day] = (float(bar["o"]), float(bar["c"]))
        token = payload.get("next_page_token")
        if not token:
            break
    else:
        raise RuntimeError(f"Alpaca pagination did not finish for {ticker}")
    return result


def main() -> None:
    events = prepare_roster()
    with np.load(PANEL, allow_pickle=False) as z:
        dates = [date.fromisoformat(x) for x in z["sp500_dates"].tolist()]
        date_to_i = {d: i for i, d in enumerate(dates)}
        members = z["sp500_roster"]
        adj_open = z["sp500_adjusted_open"]
        adj_close = z["sp500_adjusted_close"]

        headers = load_api_headers()
        session = requests.Session()
        result_rows: list[dict[str, object]] = []
        exclusions: dict[str, int] = {}
        fetch_errors: list[dict[str, str]] = []
        for event in events:
            announced = date.fromisoformat(event["announcement_date"])
            effective = date.fromisoformat(event["effective_date"])
            entry_i = next((i for i, d in enumerate(dates) if d > announced), None)
            exit_i = date_to_i.get(effective)
            if entry_i is None or exit_i is None or entry_i > exit_i:
                reason = "calendar_boundary_or_order"
                exclusions[reason] = exclusions.get(reason, 0) + 1
                continue
            entry_date, exit_date = dates[entry_i], dates[exit_i]
            if entry_date < START or exit_date > END:
                exclusions["window_outside_development"] = exclusions.get("window_outside_development", 0) + 1
                continue
            try:
                stock = fetch_symbol_bars(session, headers, event["ticker"], entry_date, exit_date)
            except Exception as exc:
                fetch_errors.append({"ticker": event["ticker"], "effective_date": event["effective_date"],
                                     "error_type": type(exc).__name__, "message": str(exc)[:180]})
                exclusions["direct_fetch_failed"] = exclusions.get("direct_fetch_failed", 0) + 1
                time.sleep(0.34)
                continue
            time.sleep(0.34)
            if entry_date not in stock or exit_date not in stock:
                exclusions["missing_direct_entry_or_exit_bar"] = exclusions.get("missing_direct_entry_or_exit_bar", 0) + 1
                continue
            stock_return = stock[exit_date][1] / stock[entry_date][0] - 1.0
            benchmark_daily: list[float] = []
            for i in range(entry_i, exit_i + 1):
                if i == entry_i:
                    valid = members[:, i] & np.isfinite(adj_open[:, i]) & np.isfinite(adj_close[:, i]) & (adj_open[:, i] > 0)
                    values = adj_close[valid, i] / adj_open[valid, i] - 1.0
                else:
                    valid = (members[:, i - 1] & members[:, i]
                             & np.isfinite(adj_close[:, i - 1]) & np.isfinite(adj_close[:, i])
                             & (adj_close[:, i - 1] > 0))
                    values = adj_close[valid, i] / adj_close[valid, i - 1] - 1.0
                values = values[np.isfinite(values)]
                if values.size == 0:
                    benchmark_daily = []
                    break
                benchmark_daily.append(float(values.mean()))
            if not benchmark_daily:
                exclusions["missing_benchmark_session"] = exclusions.get("missing_benchmark_session", 0) + 1
                continue
            benchmark_return = float(np.prod(1.0 + np.asarray(benchmark_daily)) - 1.0)
            car = stock_return - benchmark_return
            result_rows.append({
                **event,
                "entry_date": entry_date.isoformat(),
                "holding_sessions": exit_i - entry_i + 1,
                "stock_return": stock_return,
                "benchmark_return": benchmark_return,
                "car": car,
            })

    cars = np.array([float(x["car"]) for x in result_rows], dtype=float)
    n = int(cars.size)
    if n:
        mean = float(cars.mean())
        median = float(np.median(cars))
        sd = float(cars.std(ddof=1)) if n > 1 else float("nan")
        if n > 1:
            half = float(student_t.ppf(0.975, n - 1) * sd / math.sqrt(n))
            ci = [mean - half, mean + half]
            mde = float(2.970 * sd / math.sqrt(96))
        else:
            ci, mde = [None, None], None
        mean_net = {str(bps): mean - 2 * bps / 10000 for bps in (5, 10, 20)}
        holding = np.array([int(x["holding_sessions"]) for x in result_rows])
        holding_summary = {"mean": float(holding.mean()), "median": float(np.median(holding)),
                           "min": int(holding.min()), "max": int(holding.max())}
    else:
        mean = median = sd = None
        ci, mde, mean_net, holding_summary = [None, None], None, {}, None
    primary_net = mean_net.get("5") if mean_net else None
    decision = "prereg_draft" if primary_net is not None and mde is not None and primary_net > mde else "s2_exhausted"
    output = {
        "tag": "L-ADDS",
        "registered_test": "L-ADDS-01",
        "run_started_utc": "2026-11-11T19:13:19Z",
        "data_window": [START.isoformat(), END.isoformat()],
        "event_rule": "roster additions with dated official S&P source; next session after announcement open to effective close",
        "eligible_dated_event_n": len(events),
        "measured_n": n,
        "mean_car": mean,
        "cross_event_sample_sd": sd,
        "median_car": median,
        "ci95_t": ci,
        "mean_holding_sessions": holding_summary,
        "mean_net_car_by_one_way_bps": mean_net,
        "holdout_mde_n96": mde,
        "primary_decision_net_mean_5bp": primary_net,
        "decision": decision,
        "exclusions": exclusions,
        "fetch_errors": fetch_errors,
        "events": result_rows,
    }
    OUT_JSON.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({k: output[k] for k in (
        "eligible_dated_event_n", "measured_n", "mean_car", "cross_event_sample_sd", "median_car",
        "ci95_t", "mean_holding_sessions", "mean_net_car_by_one_way_bps", "holdout_mde_n96",
        "decision", "exclusions", "fetch_errors")}, indent=2))


if __name__ == "__main__":
    main()
