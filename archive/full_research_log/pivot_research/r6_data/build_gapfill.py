"""Recover missing S&P 500 development bars via Yahoo's documented ticker lineage.

Only current Yahoo Finance chart symbols that represent the same publicly traded
share line are used. Dates are limited to 2020-06-01 through 2026-10-30 and to
the point-in-time membership interval for each historical ticker.
"""
from __future__ import annotations

import time
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests

OUT = Path(__file__).resolve().parent
START = date(2020, 6, 1)
END = date(2026, 10, 30)
END_EXCLUSIVE = date(2026, 10, 31)
ALIASES = {
    "ADS": ("BFH", "Same issuer; Alliance Data Systems changed its name and ticker to Bread Financial/BFH on 2022-04-04."),
    "FBHS": ("FBIN", "Same share line; Fortune Brands Home & Security changed its name and ticker to FBIN on 2022-12-15."),
    "SATS": ("ECHO", "Same issuer/share line; EchoStar changed ticker from SATS to ECHO on 2026-06-24."),
}


def main() -> None:
    roster = pd.read_csv(OUT / "sp500_pit_roster.csv", dtype={"ticker": str})
    base = pd.read_parquet(OUT / "sp500_ohlcv_dev.parquet")
    existing = set(base["ticker"].astype(str))
    missing = sorted(set(roster["ticker"].astype(str)) - existing)
    selected = [t for t in missing if t in ALIASES]
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 FINS3666 academic data research"})
    p1 = int(datetime(2020, 6, 1, tzinfo=ZoneInfo("America/New_York")).timestamp())
    p2 = int(datetime(2026, 10, 31, tzinfo=ZoneInfo("America/New_York")).timestamp())
    records, manifest, errors = [], [], []
    last_request = 0.0

    for ticker in selected:
        source_symbol, note = ALIASES[ticker]
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{source_symbol}"
               f"?period1={p1}&period2={p2}&interval=1d&events=div%2Csplits")
        wait = 0.35 - (time.monotonic() - last_request)
        if wait > 0:
            time.sleep(wait)
        try:
            response = session.get(url, timeout=30)
            last_request = time.monotonic()
            response.raise_for_status()
            obj = response.json()
            result = obj["chart"]["result"][0]
            timestamps = result.get("timestamp") or []
            quote = result["indicators"]["quote"][0]
            adj = result.get("indicators", {}).get("adjclose", [{}])[0].get("adjclose", [])
            active = roster.loc[roster["ticker"].astype(str).eq(ticker)]
            spans = [(date.fromisoformat(r.effective_from), date.fromisoformat(r.effective_to_exclusive))
                     for r in active.itertuples()]
            before = len(records)
            for i, ts in enumerate(timestamps):
                day = pd.Timestamp(ts, unit="s", tz="UTC").tz_convert("America/New_York").date()
                if not (START <= day <= END and any(lo <= day < hi for lo, hi in spans)):
                    continue
                records.append({
                    "date": pd.Timestamp(day), "ticker": ticker,
                    "open": quote.get("open", [None])[i],
                    "high": quote.get("high", [None])[i],
                    "low": quote.get("low", [None])[i],
                    "close": quote.get("close", [None])[i],
                    "adj_close": adj[i] if i < len(adj) else None,
                    "volume": quote.get("volume", [None])[i],
                })
            count = len(records) - before
            manifest.append({"ticker": ticker, "source_symbol": source_symbol,
                             "source": "Yahoo Finance chart endpoint", "source_url": url,
                             "rows_added": count,
                             "first_date": min((r["date"] for r in records[before:]), default=""),
                             "last_date": max((r["date"] for r in records[before:]), default=""),
                             "lineage_note": note})
            if not count:
                errors.append({"ticker": ticker, "source_symbol": source_symbol,
                               "error": "No Yahoo rows fell inside the point-in-time membership window."})
        except Exception as exc:
            errors.append({"ticker": ticker, "source_symbol": source_symbol, "error": str(exc)})

    gap = pd.DataFrame(records, columns=["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"])
    if not gap.empty:
        gap["date"] = pd.to_datetime(gap["date"]).dt.tz_localize(None)
        gap = gap.sort_values(["ticker", "date"]).drop_duplicates(["ticker", "date"])
    gap.to_parquet(OUT / "sp500_ohlcv_gapfill.parquet", index=False)
    pd.DataFrame(manifest).to_csv(OUT / "gapfill_manifest.csv", index=False)
    pd.DataFrame(errors).to_csv(OUT / "gapfill_errors.csv", index=False)
    combined = pd.concat([base, gap], ignore_index=True).drop_duplicates(["ticker", "date"])
    combined = combined.sort_values(["ticker", "date"])
    combined.to_parquet(OUT / "sp500_ohlcv_dev_gapfilled.parquet", index=False)
    print(f"missing_before={len(missing)} aliases_attempted={len(selected)} rows_added={len(gap)} "
          f"tickers_added={gap['ticker'].nunique() if not gap.empty else 0} "
          f"remaining_missing={len(set(missing)-set(gap['ticker'].astype(str)))}")
    print("recovered=" + ",".join(sorted(gap["ticker"].astype(str).unique())) if not gap.empty else "recovered=none")


if __name__ == "__main__":
    main()
