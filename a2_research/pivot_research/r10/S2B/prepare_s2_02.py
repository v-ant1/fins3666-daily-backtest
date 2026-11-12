from __future__ import annotations

import json, math, re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import numpy as np
import requests
from dotenv import dotenv_values

import run_s2b as common

OUT = Path(__file__).resolve().parent
START, END = common.START, common.END


def main():
    sec = common.ThrottledGet(.112, {"User-Agent": common.SEC_UA, "Accept-Encoding": "gzip, deflate"})
    ticker_cik = common.read_cik_map(sec)
    dates, assets, roster, sic2, op, cl = common.get_dev_panel()
    metadata = json.load(open(OUT / "sec_dev_filing_metadata.json", encoding="utf-8"))
    acc_meta = {r["accession"]: r for r in metadata if r["form"] in ("10-Q", "10-K")}
    cik_asset = {ticker_cik[t]: t for t in assets if t in ticker_cik}
    asset_ix = {t: i for i, t in enumerate(assets)}
    submission_ciks = {r["cik"] for r in metadata if r["form"] in ("10-Q", "10-K")}
    ciks = sorted(c for c in submission_ciks if c in cik_asset)
    print("mapped issuer CIKs with dev 10-Q/K filings", len(ciks))
    candidates = defaultdict(list)
    fact_fetch_errors = 0
    fact_tags_seen = set()

    for n, cik in enumerate(ciks, 1):
        response = sec.get(f"{common.SEC_ROOT}/api/xbrl/companyfacts/CIK{cik}.json")
        if not response.ok:
            fact_fetch_errors += 1
            continue
        usgaap = response.json().get("facts", {}).get("us-gaap", {})
        rep_tags = [tag for tag in usgaap if re.search(
            r"StockRepurchasedAndRetiredDuringPeriodShares|StockRepurchasedDuringPeriodShares|CommonStockSharesRepurchasedDuringPeriod",
            tag, re.I)]
        share_tags = [tag for tag in usgaap if re.search(r"CommonStockSharesOutstanding|EntityCommonStockSharesOutstanding", tag, re.I)]
        fact_tags_seen.update(rep_tags)
        rep_rows = []
        for tag in rep_tags:
            for unit, vals in usgaap[tag].get("units", {}).items():
                if unit.lower() not in ("shares", "share"):
                    continue
                for x in vals:
                    if x.get("form") not in ("10-Q", "10-K") or x.get("accn") not in acc_meta:
                        continue
                    acc = acc_meta[x["accn"]]
                    filed = date.fromisoformat(acc["accepted_date"])
                    if not (date.fromisoformat(START) <= filed <= date.fromisoformat(END)):
                        continue
                    try:
                        value = float(x["val"])
                    except Exception:
                        continue
                    if value < 0 or not x.get("end"):
                        continue
                    period_days = None
                    if x.get("start"):
                        period_days = (date.fromisoformat(x["end"]) - date.fromisoformat(x["start"])).days + 1
                    if acc["form"] == "10-Q" and (period_days is None or not 70 <= period_days <= 120):
                        continue
                    if acc["form"] == "10-K" and period_days is not None and not 300 <= period_days <= 400:
                        continue
                    rep_rows.append({"accn": x["accn"], "filed": filed.isoformat(), "end": x["end"],
                                     "value": value, "tag": tag, "form": acc["form"]})
        rep_rows.sort(key=lambda x: (x["filed"], x["end"], x["accn"]))
        shares_rows = []
        for tag in share_tags:
            for unit, vals in usgaap[tag].get("units", {}).items():
                if unit.lower() not in ("shares", "share"):
                    continue
                for x in vals:
                    if x.get("accn") not in acc_meta or x.get("form") not in ("10-Q", "10-K") or not x.get("end"):
                        continue
                    filed = date.fromisoformat(acc_meta[x["accn"]]["accepted_date"])
                    # Do not inspect pre-development reported values.
                    if filed.isoformat() < START or filed.isoformat() > END:
                        continue
                    try:
                        value = float(x["val"])
                    except Exception:
                        continue
                    if value > 0:
                        shares_rows.append({"filed": filed.isoformat(), "end": x["end"], "value": value, "accn": x["accn"]})
        for r in rep_rows:
            if r["value"] <= 0:
                continue
            filed = r["filed"]
            previous = [p for p in rep_rows if p["tag"] == r["tag"] and p["end"] < r["end"] and p["filed"] < filed]
            if not previous:
                continue
            prior_shares = [s for s in shares_rows if s["end"] < r["end"] and s["filed"] < filed]
            if not prior_shares:
                continue
            prior_shares.sort(key=lambda s: (s["end"], s["filed"]))
            denominator = prior_shares[-1]["value"]
            if denominator <= 0:
                continue
            issuer = cik_asset[cik]
            cohort = common.next_month_session(dates.tolist(), date.fromisoformat(filed))
            if cohort is None:
                continue
            cohort_ix = int(np.searchsorted(dates, cohort))
            if cohort_ix >= len(dates) or not roster[asset_ix[issuer], cohort_ix]:
                continue
            candidates[(cohort, issuer)].append({"event_date": filed, "cohort_month": cohort,
                                                 "asset": issuer, "score": r["value"] / denominator,
                                                 "reported_shares_repurchased": r["value"],
                                                 "prior_quarter_shares_outstanding": denominator,
                                                 "form": r["form"], "period_end": r["end"], "accession": r["accn"]})
        if n % 50 == 0:
            print(f"SEC companyfacts processed: {n}/{len(ciks)}")

    earliest = []
    for key, rows in candidates.items():
        earliest.append(sorted(rows, key=lambda x: (x["event_date"], x["accession"]))[0])
    month_rows = defaultdict(list)
    for e in earliest:
        month_rows[e["cohort_month"]].append(e)
    selected = []
    for cohort, rows in sorted(month_rows.items()):
        if len(rows) >= 5:
            rows.sort(key=lambda x: (-x["score"], x["asset"]))
            selected.extend(rows[:max(1, math.ceil(.2*len(rows)))])

    gap_summary = common.fill_alpaca_gaps(dates, assets, roster, sic2, op, cl)
    with (OUT / "S2_02_EVENTS.json").open("w", encoding="utf-8") as f:
        json.dump(selected, f, indent=2)
    prep = {"event_count": len(selected), "event_months": len({e["cohort_month"] for e in selected}),
            "mapped_issuer_ciks": len(ciks), "companyfacts_fetch_failures": fact_fetch_errors,
            "repurchase_fact_tags_found": sorted(fact_tags_seen), "gap_fill": gap_summary,
            "outcomes_computed": False}
    with (OUT / "PREPARED_S2_02.json").open("w", encoding="utf-8") as f:
        json.dump(prep, f, indent=2)
    print(json.dumps(prep, indent=2))


if __name__ == "__main__":
    main()
