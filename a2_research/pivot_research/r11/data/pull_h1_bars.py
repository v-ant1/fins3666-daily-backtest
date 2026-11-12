from __future__ import annotations

import csv
import hashlib
import os
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, time as day_time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pyarrow as pa
import pyarrow.parquet as pq
import requests
from dotenv import dotenv_values


PROJECT = Path(__file__).resolve().parents[2]
A2_ROOT = PROJECT.parent
ENV_PATH = A2_ROOT / ".env"
SP500_ROSTER = PROJECT / "r6_data" / "sp500_pit_roster.csv"
DOW_ROSTER = PROJECT / "r6_D1" / "dow_pit_roster.csv"
DATA_DIR = PROJECT / "r11" / "data"
HOLDOUT_DIR = PROJECT / "sealed_holdout_1h"
DEV_PATH = DATA_DIR / "H1_DEV.parquet"
HOLDOUT_PATH = HOLDOUT_DIR / "H1_HOLDOUT.parquet"
QA_PATH = DATA_DIR / "H1_DATA_QA.md"
HASH_LOG = PROJECT / "specs" / "STAGED_INPUT_HASHES.csv"
DECISIONS_PATH = PROJECT / "specs" / "r11_decisions.md"

API_BASE = "https://data.alpaca.markets"
START_UTC = datetime(2016, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
END_UTC = datetime(2026, 10, 30, 23, 59, 59, tzinfo=timezone.utc)
CUTOFF_UTC = datetime(2020, 11, 27, 0, 0, 0, tzinfo=timezone.utc)
START_DATE = START_UTC.date()
END_DATE = END_UTC.date()
DEV_START_DATE = CUTOFF_UTC.date()
NY = ZoneInfo("America/New_York")
SYMBOLS_PER_REQUEST = 25
MAX_PAGE_ROWS = 10000
RPM_TARGET = 190

SCHEMA = pa.schema(
    [
        pa.field("symbol", pa.string()),
        pa.field("timestamp", pa.timestamp("us", tz="UTC")),
        pa.field("open", pa.float64()),
        pa.field("high", pa.float64()),
        pa.field("low", pa.float64()),
        pa.field("close", pa.float64()),
        pa.field("volume", pa.float64()),
        pa.field("trade_count", pa.int64()),
        pa.field("vwap", pa.float64()),
        pa.field("is_regular_session", pa.bool_()),
    ]
)


def read_roster(path: Path) -> tuple[set[str], list[tuple[str, date, date]]]:
    symbols: set[str] = set()
    intervals: list[tuple[str, date, date]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            ticker = (row.get("ticker") or "").strip().upper()
            if not ticker:
                continue
            start_raw = (row.get("effective_from") or "").strip()
            end_raw = (row.get("effective_to_exclusive") or "").strip()
            if not start_raw:
                continue
            start = date.fromisoformat(start_raw[:10])
            end = date.fromisoformat(end_raw[:10]) if end_raw else date.max
            symbols.add(ticker)
            intervals.append((ticker, start, end))
    return symbols, intervals


def make_api_symbols(symbols: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    to_api: dict[str, str] = {}
    from_api: dict[str, str] = {}
    for symbol in symbols:
        api_symbol = {"BF-B": "BF.B", "BRK-B": "BRK.B"}.get(symbol, symbol)
        if api_symbol in from_api and from_api[api_symbol] != symbol:
            raise RuntimeError("Roster symbols collide after Alpaca class-share normalization")
        to_api[symbol] = api_symbol
        from_api[api_symbol] = symbol
    return to_api, from_api


def expected_symbols_by_dev_year(
    intervals: list[tuple[str, date, date]],
) -> dict[int, set[str]]:
    expected = {year: set() for year in range(2020, 2027)}
    window_end_exclusive = END_DATE + timedelta(days=1)
    for ticker, roster_start, roster_end in intervals:
        active_start = max(roster_start, DEV_START_DATE)
        active_end = min(roster_end, window_end_exclusive)
        if active_start >= active_end:
            continue
        for year in expected:
            year_start = max(date(year, 1, 1), DEV_START_DATE)
            year_end = min(date(year + 1, 1, 1), window_end_exclusive)
            if active_start < year_end and year_start < active_end:
                expected[year].add(ticker)
    return expected


def month_windows() -> list[tuple[datetime, datetime]]:
    windows: list[tuple[datetime, datetime]] = []
    month_start = date(START_DATE.year, START_DATE.month, 1)
    while month_start <= END_DATE:
        if month_start.month == 12:
            next_month = date(month_start.year + 1, 1, 1)
        else:
            next_month = date(month_start.year, month_start.month + 1, 1)
        start = datetime.combine(month_start, day_time.min, tzinfo=timezone.utc)
        end = min(
            datetime.combine(next_month, day_time.min, tzinfo=timezone.utc) - timedelta(microseconds=1),
            END_UTC,
        )
        windows.append((start, end))
        month_start = next_month
    return windows


class AlpacaClient:
    def __init__(self, key: str, secret: str) -> None:
        self.headers = {
            "APCA-API-KEY-ID": key,
            "APCA-API-SECRET-KEY": secret,
            "accept": "application/json",
        }
        self.session = requests.Session()
        self.interval = 60.0 / RPM_TARGET
        self.next_allowed = 0.0
        self.rate_lock = threading.Lock()
        self.attempts = 0
        self.successes = 0
        self.retries = 0

    def get_json(self, params: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(8):
            with self.rate_lock:
                now = time.monotonic()
                wait = max(0.0, self.next_allowed - now)
                if wait:
                    time.sleep(wait)
                self.next_allowed = time.monotonic() + self.interval
                self.attempts += 1
            try:
                response = self.session.get(
                    API_BASE + "/v2/stocks/bars",
                    params=params,
                    headers=self.headers,
                    timeout=(15, 120),
                )
            except requests.RequestException as exc:
                self.retries += 1
                if attempt == 7:
                    raise RuntimeError(f"Alpaca GET failed after retries ({type(exc).__name__})") from None
                time.sleep(min(2**attempt, 60))
                continue

            if response.status_code == 429 or response.status_code >= 500:
                self.retries += 1
                if attempt == 7:
                    raise RuntimeError(f"Alpaca GET returned HTTP {response.status_code} after retries")
                retry_after = response.headers.get("Retry-After")
                reset = response.headers.get("X-RateLimit-Reset")
                delay = min(2**attempt, 60)
                if retry_after:
                    try:
                        delay = max(delay, float(retry_after))
                    except ValueError:
                        pass
                elif response.status_code == 429 and reset:
                    try:
                        delay = max(delay, float(reset) - time.time())
                    except ValueError:
                        pass
                time.sleep(min(max(delay, 1.0), 120.0))
                continue

            if not response.ok:
                raise RuntimeError(f"Alpaca GET returned HTTP {response.status_code}")
            self.successes += 1
            try:
                result = response.json()
            except ValueError:
                raise RuntimeError("Alpaca GET returned invalid JSON") from None
            if not isinstance(result, dict):
                raise RuntimeError("Alpaca GET returned an unexpected response shape")
            return result
        raise RuntimeError("Alpaca GET retry loop exhausted")


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def is_regular_session(timestamp: datetime) -> bool:
    local = timestamp.astimezone(NY)
    return day_time(9, 30) <= local.time().replace(tzinfo=None) <= day_time(16, 0)


def table_for_rows(rows: list[dict[str, Any]]) -> pa.Table:
    return pa.Table.from_pylist(rows, schema=SCHEMA)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fmt_date_range(minimum: datetime | None, maximum: datetime | None) -> str:
    if minimum is None or maximum is None:
        return "none"
    return f"{minimum.date().isoformat()} to {maximum.date().isoformat()} (UTC timestamp dates)"


def fmt_mean(bars: int, symbol_days: int) -> str:
    return f"{bars / symbol_days:.2f}" if symbol_days else "n/a"


def main() -> None:
    for path in (SP500_ROSTER, DOW_ROSTER, HASH_LOG):
        if not path.is_file():
            raise RuntimeError(f"Required input is missing: {path.relative_to(PROJECT)}")
    for path in (DEV_PATH, HOLDOUT_PATH, QA_PATH):
        if path.exists():
            raise RuntimeError(f"Refusing to overwrite existing output: {path.relative_to(PROJECT)}")

    sp_symbols, sp_intervals = read_roster(SP500_ROSTER)
    dow_symbols, dow_intervals = read_roster(DOW_ROSTER)
    symbols = sorted(sp_symbols | dow_symbols)
    intervals = sp_intervals + dow_intervals
    to_api, from_api = make_api_symbols(symbols)
    expected_by_year = expected_symbols_by_dev_year(intervals)
    batches = [symbols[i : i + SYMBOLS_PER_REQUEST] for i in range(0, len(symbols), SYMBOLS_PER_REQUEST)]
    tasks = [(batch, window_start, window_end) for window_start, window_end in month_windows() for batch in batches]

    env = dotenv_values(ENV_PATH, encoding="utf-8")
    primary = (env.get("ALPACA_API_KEY"), env.get("ALPACA_SECRET_KEY"))
    alternate = (env.get("2_ALPACA_API_KEY"), env.get("2_ALPACA_SECRET_KEY"))
    if not all(primary):
        raise RuntimeError("Primary Alpaca credential pair is missing in A2/.env")
    clients = [AlpacaClient(str(primary[0]), str(primary[1]))]
    if all(alternate):
        clients.append(AlpacaClient(str(alternate[0]), str(alternate[1])))
    elif any(alternate):
        raise RuntimeError("Secondary Alpaca credential pair is incomplete in A2/.env")

    run_id = uuid.uuid4().hex
    dev_tmp = DATA_DIR / f".H1_DEV.{run_id}.partial.parquet"
    holdout_tmp = HOLDOUT_DIR / f".H1_HOLDOUT.{run_id}.partial.parquet"
    writers: dict[str, pq.ParquetWriter] = {}
    try:
        writers["dev"] = pq.ParquetWriter(dev_tmp, SCHEMA, compression="zstd")
        writers["holdout"] = pq.ParquetWriter(holdout_tmp, SCHEMA, compression="zstd")
    except Exception:
        for writer in writers.values():
            writer.close()
        for path in (dev_tmp, holdout_tmp):
            if path.exists():
                path.unlink()
        raise

    state_lock = threading.Lock()
    writer_lock = threading.Lock()
    job_lock = threading.Lock()
    progress_lock = threading.Lock()
    jobs = iter(enumerate(tasks, start=1))
    stop_event = threading.Event()
    completed_batches = 0
    total_pages = 0
    aggregate = {
        "holdout_rows": 0,
        "holdout_symbols": set(),
        "holdout_min": None,
        "holdout_max": None,
        "dev_rows": 0,
        "dev_symbols": set(),
        "dev_min": None,
        "dev_max": None,
        "dev_regular_bars": 0,
        "dev_extended_bars": 0,
        "dev_regular_symbol_days": 0,
        "dev_extended_symbol_days": 0,
        "dev_symbols_by_year": {year: set() for year in range(2020, 2027)},
        "present_symbols": set(),
    }

    def download_batch(
        client: AlpacaClient,
        batch: list[str],
        window_start: datetime,
        window_end: datetime,
    ) -> tuple[dict[str, Any], int]:
        local: dict[str, Any] = {
            "holdout_rows": 0,
            "holdout_symbols": set(),
            "holdout_min": None,
            "holdout_max": None,
            "dev_rows": 0,
            "dev_symbols": set(),
            "dev_min": None,
            "dev_max": None,
            "dev_regular_bars": 0,
            "dev_extended_bars": 0,
            "dev_regular_days": set(),
            "dev_extended_days": set(),
            "dev_symbols_by_year": {year: set() for year in range(2020, 2027)},
            "present_symbols": set(),
        }
        params: dict[str, Any] = {
            "symbols": ",".join(to_api[symbol] for symbol in batch),
            "timeframe": "1Hour",
            "start": window_start.isoformat().replace("+00:00", "Z"),
            "end": window_end.isoformat().replace("+00:00", "Z"),
            "limit": MAX_PAGE_ROWS,
            "feed": "sip",
            "adjustment": "all",
            "sort": "asc",
        }
        token: str | None = None
        page_count = 0
        while True:
            if stop_event.is_set():
                raise RuntimeError("Download cancelled after a peer request failed")
            request_params = dict(params)
            if token:
                request_params["page_token"] = token
            body = client.get_json(request_params)
            page_count += 1
            rows_dev: list[dict[str, Any]] = []
            rows_holdout: list[dict[str, Any]] = []
            bars_by_symbol = body.get("bars") or {}
            if not isinstance(bars_by_symbol, dict):
                raise RuntimeError("Alpaca bars response has an unexpected shape")
            for api_symbol in sorted(bars_by_symbol):
                symbol = from_api.get(api_symbol, api_symbol)
                for bar in bars_by_symbol[api_symbol] or []:
                    timestamp = parse_timestamp(str(bar["t"]))
                    if timestamp < START_UTC or timestamp > END_UTC or timestamp < window_start or timestamp > window_end:
                        continue
                    regular = is_regular_session(timestamp)
                    local_day = timestamp.astimezone(NY).date()
                    row = {
                        "symbol": symbol,
                        "timestamp": timestamp,
                        "open": bar.get("o"),
                        "high": bar.get("h"),
                        "low": bar.get("l"),
                        "close": bar.get("c"),
                        "volume": bar.get("v"),
                        "trade_count": bar.get("n"),
                        "vwap": bar.get("vw"),
                        "is_regular_session": regular,
                    }
                    local["present_symbols"].add(symbol)
                    if timestamp < CUTOFF_UTC:
                        rows_holdout.append(row)
                        local["holdout_rows"] += 1
                        local["holdout_symbols"].add(symbol)
                        local["holdout_min"] = timestamp if local["holdout_min"] is None else min(local["holdout_min"], timestamp)
                        local["holdout_max"] = timestamp if local["holdout_max"] is None else max(local["holdout_max"], timestamp)
                    else:
                        rows_dev.append(row)
                        local["dev_rows"] += 1
                        local["dev_symbols"].add(symbol)
                        local["dev_min"] = timestamp if local["dev_min"] is None else min(local["dev_min"], timestamp)
                        local["dev_max"] = timestamp if local["dev_max"] is None else max(local["dev_max"], timestamp)
                        local["dev_symbols_by_year"].setdefault(timestamp.year, set()).add(symbol)
                        if regular:
                            local["dev_regular_bars"] += 1
                            local["dev_regular_days"].add((symbol, local_day))
                        else:
                            local["dev_extended_bars"] += 1
                            local["dev_extended_days"].add((symbol, local_day))
            with writer_lock:
                if rows_holdout:
                    writers["holdout"].write_table(table_for_rows(rows_holdout), row_group_size=MAX_PAGE_ROWS)
                if rows_dev:
                    writers["dev"].write_table(table_for_rows(rows_dev), row_group_size=MAX_PAGE_ROWS)
            token = body.get("next_page_token")
            if not token:
                break

        local["dev_regular_symbol_days"] = len(local.pop("dev_regular_days"))
        local["dev_extended_symbol_days"] = len(local.pop("dev_extended_days"))
        with state_lock:
            for key in (
                "holdout_rows",
                "dev_rows",
                "dev_regular_bars",
                "dev_extended_bars",
                "dev_regular_symbol_days",
                "dev_extended_symbol_days",
            ):
                aggregate[key] += local[key]
            aggregate["holdout_symbols"].update(local["holdout_symbols"])
            aggregate["dev_symbols"].update(local["dev_symbols"])
            aggregate["present_symbols"].update(local["present_symbols"])
            for year in range(2020, 2027):
                aggregate["dev_symbols_by_year"][year].update(local["dev_symbols_by_year"].get(year, set()))
            for key in ("holdout_min", "dev_min"):
                value = local[key]
                if value is not None:
                    aggregate[key] = value if aggregate[key] is None else min(aggregate[key], value)
            for key in ("holdout_max", "dev_max"):
                value = local[key]
                if value is not None:
                    aggregate[key] = value if aggregate[key] is None else max(aggregate[key], value)
        return local, page_count

    def worker(client: AlpacaClient) -> None:
        nonlocal completed_batches, total_pages
        while not stop_event.is_set():
            with job_lock:
                try:
                    task_number, (batch, window_start, window_end) = next(jobs)
                except StopIteration:
                    return
            try:
                _local, pages = download_batch(client, batch, window_start, window_end)
            except Exception:
                stop_event.set()
                raise
            with progress_lock:
                completed_batches += 1
                total_pages += pages
                attempts = sum(item.attempts for item in clients)
                retries = sum(item.retries for item in clients)
                if completed_batches % len(batches) == 0 or completed_batches == len(tasks):
                    print(
                        f"Completed symbol-month tasks {completed_batches}/{len(tasks)}; "
                        f"successful pages={total_pages}; GET attempts={attempts}; retries={retries}",
                        flush=True,
                    )

    started_at = datetime.now(timezone.utc)
    started_clock = time.monotonic()
    successful = False
    try:
        print(
            f"Starting 1-hour SIP download for {len(symbols)} roster symbols in {len(batches)} symbol batches and "
            f"{len(month_windows())} monthly windows ({len(tasks)} multi-symbol tasks); "
            f"credential pairs={len(clients)}; window={START_UTC.date()}..{END_UTC.date()}",
            flush=True,
        )
        with ThreadPoolExecutor(max_workers=len(clients)) as pool:
            futures = [pool.submit(worker, client) for client in clients]
            for future in as_completed(futures):
                future.result()
        for writer in writers.values():
            writer.close()
        writers.clear()

        if DEV_PATH.exists() or HOLDOUT_PATH.exists() or QA_PATH.exists():
            raise RuntimeError("Refusing to replace a final output created during this run")
        os.replace(dev_tmp, DEV_PATH)
        os.replace(holdout_tmp, HOLDOUT_PATH)
        elapsed = time.monotonic() - started_clock
        finished_at = datetime.now(timezone.utc)
        dev_hash = sha256_file(DEV_PATH)
        holdout_hash = sha256_file(HOLDOUT_PATH)
        dev_metadata = pq.read_metadata(DEV_PATH)
        holdout_metadata = pq.read_metadata(HOLDOUT_PATH)
        if dev_metadata.num_rows != aggregate["dev_rows"]:
            raise RuntimeError("DEV parquet metadata row count does not match streamed row count")
        if holdout_metadata.num_rows != aggregate["holdout_rows"]:
            raise RuntimeError("Holdout parquet metadata row count does not match streamed row count")

        dev_regular = aggregate["dev_regular_bars"]
        dev_extended = aggregate["dev_extended_bars"]
        dev_regular_days = aggregate["dev_regular_symbol_days"]
        dev_extended_days = aggregate["dev_extended_symbol_days"]
        missing = sorted(set(symbols) - aggregate["present_symbols"])
        requests_attempted = sum(client.attempts for client in clients)
        requests_succeeded = sum(client.successes for client in clients)
        retries = sum(client.retries for client in clients)

        qa_lines = [
            "# R11 H1 Data QA",
            "",
            "## Acquisition",
            "",
            f"- Measured wall time: {elapsed:.1f} seconds ({started_at.isoformat()} to {finished_at.isoformat()}).",
            f"- Alpaca GET attempts: {requests_attempted}; successful responses: {requests_succeeded}; retries: {retries}.",
            f"- Credential pairs used: {len(clients)}; each was paced at no more than {RPM_TARGET} requests per minute.",
            "- Endpoint: `GET https://data.alpaca.markets/v2/stocks/bars`; `timeframe=1Hour`, `feed=sip`, `adjustment=all`, `limit=10000`.",
            f"- Requested UTC window: {START_UTC.isoformat()} through {END_UTC.isoformat()}; the complete roster union contains {len(symbols)} tickers.",
            "- The optional `adjustment=raw` pass was omitted because it would add a second full-history panel and approximately double transfer and storage.",
            "- Bars were routed by UTC timestamp: values before `2020-11-27T00:00:00Z` were streamed to the sealed panel; later bars were routed to DEV. Session flags use America/New_York local time, inclusive from 09:30 through 16:00.",
            "",
            "## DEV panel",
            "",
            f"- Rows: {aggregate['dev_rows']}; symbols: {len(aggregate['dev_symbols'])}; timestamp date range: {fmt_date_range(aggregate['dev_min'], aggregate['dev_max'])}.",
            f"- SHA-256: `{dev_hash}`.",
            f"- Regular-session bars: {dev_regular}; extended-session bars: {dev_extended}.",
            f"- Distinct regular symbol-days: {dev_regular_days}; bars per regular symbol-day: {fmt_mean(dev_regular, dev_regular_days)}.",
            f"- Distinct extended symbol-days: {dev_extended_days}; bars per extended symbol-day: {fmt_mean(dev_extended, dev_extended_days)}.",
            "",
            "### DEV annual symbol coverage against PIT roster",
            "",
            "| Year | PIT roster symbols active in DEV window | Symbols with at least one bar | Coverage |",
            "|---:|---:|---:|---:|",
        ]
        for year in sorted(expected_by_year):
            expected = expected_by_year[year]
            covered = len(expected & aggregate["dev_symbols_by_year"].get(year, set()))
            percent = 100.0 * covered / len(expected) if expected else 0.0
            qa_lines.append(f"| {year} | {len(expected)} | {covered} | {percent:.1f}% |")
        qa_lines.extend(
            [
                "",
                "### Tickers with no bars over the requested window",
                "",
                ", ".join(missing) if missing else "None.",
                "",
                "## Sealed holdout metadata",
                "",
                f"- Row count: {aggregate['holdout_rows']}",
                f"- Symbol count: {len(aggregate['holdout_symbols'])}",
                f"- Date range: {fmt_date_range(aggregate['holdout_min'], aggregate['holdout_max'])}",
                f"- SHA-256: `{holdout_hash}`",
                "",
            ]
        )
        qa_tmp = DATA_DIR / f".H1_DATA_QA.{run_id}.partial.md"
        qa_tmp.write_text("\n".join(qa_lines), encoding="utf-8")
        if QA_PATH.exists():
            raise RuntimeError("Refusing to overwrite existing QA output")
        os.replace(qa_tmp, QA_PATH)

        hashed_at = finished_at.isoformat()
        with HASH_LOG.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256", "hashed_at"], lineterminator="\n")
            writer.writerow({"path": str(DEV_PATH.relative_to(PROJECT)).replace("/", "\\"), "bytes": DEV_PATH.stat().st_size, "sha256": dev_hash, "hashed_at": hashed_at})
            writer.writerow({"path": str(HOLDOUT_PATH.relative_to(PROJECT)).replace("/", "\\"), "bytes": "", "sha256": holdout_hash, "hashed_at": hashed_at})

        decision = (
            "\n## R11 H1-DATA — Alpaca hourly bar staging\n\n"
            "- Built the 1-hour SIP panel for the union of the S&P 500 and Dow PIT roster tickers over 2016-01-01 through 2026-10-30 UTC.\n"
            "- Used `adjustment=all`; the optional raw pass was not run because it would approximately double the full-history download and storage.\n"
            "- Retained extended-hours bars and derived `is_regular_session` from America/New_York timestamp time (09:30-16:00 inclusive).\n"
            "- Routed timestamps earlier than 2020-11-27 00:00:00 UTC directly to `sealed_holdout_1h/H1_HOLDOUT.parquet`; all later timestamps went to `r11/data/H1_DEV.parquet`.\n"
            "- QA and permitted holdout metadata are in `r11/data/H1_DATA_QA.md`; both panel hashes were appended to `STAGED_INPUT_HASHES.csv`.\n"
        )
        with DECISIONS_PATH.open("a", encoding="utf-8", newline="") as handle:
            handle.write(decision)
        successful = True

        print(
            f"Finished in {elapsed:.1f} seconds; GET attempts={requests_attempted}; successful responses={requests_succeeded}; "
            f"retries={retries}; DEV rows={aggregate['dev_rows']}; DEV symbols={len(aggregate['dev_symbols'])}",
            flush=True,
        )
        print(
            f"Sealed holdout metadata: row count={aggregate['holdout_rows']}; "
            f"symbol count={len(aggregate['holdout_symbols'])}; "
            f"date range={fmt_date_range(aggregate['holdout_min'], aggregate['holdout_max'])}; "
            f"SHA-256={holdout_hash}",
            flush=True,
        )
    finally:
        for writer in writers.values():
            writer.close()
        if not successful:
            for path in (dev_tmp, holdout_tmp):
                if path.exists():
                    path.unlink()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"H1 download failed ({type(exc).__name__}); details suppressed to protect sealed values and credentials.", file=sys.stderr)
        raise SystemExit(1) from None
