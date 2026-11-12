#!/usr/bin/env python3
"""Build the R9 FactSet panel and seal it with counts, coverage, and hashes only.

Input CSV contract and export steps: r9/factset/EXPORT_SPEC.md. The module does
not display panel values. Membership/classification are point-in-time; SIC2 is
available at the first session strictly after SEC acceptance (when supplied),
then carried only within the security ID. No current classification is backfilled.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import numpy as np

START, END = "2010-01-01", "2020-10-30"
GATE = 0.03
SCHEMA = {
    "sp500_dates": ("<U10", 1), "sp500_assets": ("<U5", 1),
    "sp500_roster": ("bool", 2), "sp500_sic2": ("<U2", 2),
    "sp500_adjusted_open": ("float64", 2), "sp500_adjusted_close": ("float64", 2),
    "dow_dates": ("<U10", 1), "dow_assets": ("<U5", 1),
    "dow_roster": ("bool", 2), "dow_sic2": ("<U2", 2),
    "dow_adjusted_open": ("float64", 2), "dow_adjusted_close": ("float64", 2),
}

class InputError(Exception): pass

def read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            return [{k.strip(): (v or "").strip() for k, v in row.items()}
                    for row in csv.DictReader(f)]
    except OSError as e:
        raise InputError("required FactSet CSV unavailable") from e

def parse_day(s: str) -> date | None:
    if not s: return None
    try: return date.fromisoformat(s[:10])
    except ValueError as e: raise InputError("invalid date field in FactSet CSV") from e

def num(s: str) -> float:
    if not s: return math.nan
    try: return float(s)
    except ValueError as e: raise InputError("invalid numeric field in FactSet CSV") from e

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
    return h.hexdigest()

def next_session_after(day: date, sessions: list[date]) -> date | None:
    lo, hi=0,len(sessions)
    while lo<hi:
        m=(lo+hi)//2
        if sessions[m] <= day: lo=m+1
        else: hi=m
    return sessions[lo] if lo<len(sessions) else None

def sic2(value: str) -> str:
    digits="".join(c for c in value if c.isdigit())
    return digits[:2] if len(digits)>=2 else ""

def build(raw: Path, output: Path) -> dict[str, object]:
    mem=read_csv(raw/"membership.csv"); sec=read_csv(raw/"security_master.csv")
    prices=read_csv(raw/"daily_prices.csv"); classes=read_csv(raw/"classifications.csv")
    dels=read_csv(raw/"delistings.csv")
    required={"membership.csv":(mem,{"index_code","security_id","ticker","membership_start","membership_end"}),
      "security_master.csv":(sec,{"security_id","ticker","ticker_start","ticker_end","cusip","isin","cik"}),
      "daily_prices.csv":(prices,{"security_id","date","open","close"}),
      "classifications.csv":(classes,{"security_id","sic","sic_effective_start","sic_effective_end"}),
      "delistings.csv":(dels,{"security_id","delisting_date","delisting_reason","delisting_return"})}
    for name,(rows,cols) in required.items():
        if not rows or not cols.issubset(rows[0]): raise InputError("FactSet CSV headers or rows are incomplete")
    members=defaultdict(list)
    for r in mem:
        idx=r["index_code"].upper(); sid=r["security_id"]
        if idx not in ("SPX","DOW") or not sid: continue
        a=parse_day(r["membership_start"]); b=parse_day(r["membership_end"])
        if a is None: raise InputError("membership start is required")
        members[idx].append((sid,r["ticker"],max(a,date.fromisoformat(START)),min(b or date.fromisoformat(END),date.fromisoformat(END))))
    session_set=set()
    px={}
    for r in prices:
        d=parse_day(r["date"]); sid=r["security_id"]
        if not d or not sid or not (START <= d.isoformat() <= END): continue
        session_set.add(d)
        adj_o,adj_c=num(r.get("adjusted_open","")),num(r.get("adjusted_close",""))
        if not math.isfinite(adj_o): adj_o=num(r.get("open",""))*num(r.get("split_factor",""))*num(r.get("dividend_factor",""))
        if not math.isfinite(adj_c): adj_c=num(r.get("close",""))*num(r.get("split_factor",""))*num(r.get("dividend_factor",""))
        px[sid,d]=(adj_o,adj_c)
    dates=sorted(session_set)
    if not dates: raise InputError("no daily price sessions in requested range")
    # SIC records are usable strictly after SEC acceptance; otherwise effective-from
    # is treated as the documented usable date. End dates are inclusive.
    sicrows=defaultdict(list)
    for r in classes:
        sid=r["security_id"]
        if not sid: continue
        effective=parse_day(r.get("sic_effective_start", ""))
        accepted=parse_day(r.get("sec_acceptance_date", ""))
        usable=(next_session_after(accepted,dates) if accepted else effective)
        end=parse_day(r.get("sic_effective_end", ""))
        code=sic2(r.get("sic", ""))
        if usable and code: sicrows[sid].append((usable,end,code))
    for v in sicrows.values(): v.sort(key=lambda x:x[0])
    delist={}
    for r in dels:
        sid=r["security_id"]; day=parse_day(r.get("delisting_date", ""))
        if not sid or not day: continue
        reason=r.get("delisting_reason", "").strip().lower()
        ret=num(r.get("delisting_return", ""))
        if not math.isfinite(ret):
            if any(s in reason for s in ("merger","acquisition","cash offer","conversion")): ret=0.0
            elif any(s in reason for s in ("performance","failure","bankruptcy")): ret=-0.30
            else: raise InputError("missing delisting return has no registered reason mapping")
        delist[sid]=(day,ret)
    arrs={}; stats={}; key_rows={}
    for idx,prefix in (("SPX","sp500"),("DOW","dow")):
        # One row per stable security ID. Ticker label is the latest available
        # historical ticker, constrained to the NPZ's original <U5 asset dtype.
        rows=[]
        sec_by=defaultdict(list)
        for r in sec: sec_by[r["security_id"]].append(r)
        for sid,ticker,a,b in members[idx]:
            if b<a: continue
            master=sec_by.get(sid,[])
            labels=sorted((x.get("ticker_end", ""),x.get("ticker", "")) for x in master)
            label=(labels[-1][1] if labels else ticker).upper()
            if not label or len(label)>5: raise InputError("ticker label cannot fit the development schema")
            rows.append((sid,label,a,b))
        # collapse repeated or adjacent membership intervals by identity
        ids=sorted({x[0] for x in rows})
        n,m=len(ids),len(dates); ix={sid:i for i,sid in enumerate(ids)}; dx={d:i for i,d in enumerate(dates)}
        roster=np.zeros((n,m),bool); op=np.full((n,m),np.nan); cl=np.full((n,m),np.nan)
        sic=np.full((n,m),"",dtype="<U2"); dlret=np.full((n,m),np.nan); dldef=np.zeros((n,m),bool)
        labels_by={sid:next(x[1] for x in rows if x[0]==sid) for sid in ids}
        for sid,label,a,b in rows:
            i=ix[sid]
            for j,d in enumerate(dates):
                if a<=d<=b: roster[i,j]=True
        for (sid,d),(o,c) in px.items():
            if sid in ix and d in dx: op[ix[sid],dx[d]]=o; cl[ix[sid],dx[d]]=c
        for sid,events in sicrows.items():
            if sid not in ix: continue
            i=ix[sid]
            for j,d in enumerate(dates):
                known=[(start,end,code) for start,end,code in events if start<=d and (end is None or d<=end)]
                if known: sic[i,j]=known[-1][2]
        for sid,(d,val) in delist.items():
            if sid in ix and d in dx:
                dlret[ix[sid],dx[d]]=val
                # mark defaults so coverage report can disclose count without any value
                source=[r for r in dels if r["security_id"]==sid and parse_day(r.get("delisting_date",""))==d]
                dldef[ix[sid],dx[d]]=not source or not source[-1].get("delisting_return","")
        arrs.update({f"{prefix}_dates":np.array([d.isoformat() for d in dates],dtype="<U10"),
          f"{prefix}_assets":np.array([labels_by[s] for s in ids],dtype="<U5"),
          f"{prefix}_roster":roster, f"{prefix}_sic2":sic,
          f"{prefix}_adjusted_open":op.astype("float64"), f"{prefix}_adjusted_close":cl.astype("float64"),
          f"{prefix}_delist_return":dlret, f"{prefix}_delist_defaulted":dldef,
          f"{prefix}_security_ids":np.array(ids,dtype="<U64")})
        roster_days=int(roster.sum()); valid=roster & np.isfinite(op) & np.isfinite(cl) & (op>0)&(cl>0)
        missing=int(roster_days-valid.sum()); missing_pct=(missing/roster_days if roster_days else 1.0)
        stats[prefix]={"security_count":n,"session_count":m,"roster_member_days":roster_days,
          "valid_adjusted_ohlc_member_days":int(valid.sum()),"missing_price_member_days":missing,
          "missing_price_pct":missing_pct,"missing_sic2_member_days":int((roster & (sic=="")).sum()),
          "delisting_events":int(np.isfinite(dlret).sum()),"defaulted_delisting_returns":int(dldef.sum())}
        key_rows[prefix]=ids
    output.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(output,**arrs)
    return {"stats":stats,"arrays":arrs}

def seal(output: Path, report: Path, seal_file: Path, result: dict[str,object]) -> bool:
    stats=result["stats"]; h=sha256(output); passed=all(v["missing_price_pct"]<=GATE for v in stats.values())
    report.parent.mkdir(parents=True,exist_ok=True); seal_file.parent.mkdir(parents=True,exist_ok=True)
    lines=["# FactSet panel build report", "", "Counts, coverage, missingness, and hashes only; no panel values.", "",
      f"Status: {'PASS' if passed else 'FAIL'} (maximum missing-price rate {GATE:.0%})",f"Panel SHA-256: `{h}`","", "| Panel | Securities | Sessions | Roster member-days | Valid adjusted OHLC member-days | Missing price member-days | Missing % | SIC2 missing member-days | Delist events | Defaulted delist returns |","|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name,v in stats.items(): lines.append(f"| {name} | {v['security_count']} | {v['session_count']} | {v['roster_member_days']} | {v['valid_adjusted_ohlc_member_days']} | {v['missing_price_member_days']} | {v['missing_price_pct']:.4%} | {v['missing_sic2_member_days']} | {v['delisting_events']} | {v['defaulted_delisting_returns']} |")
    lines.extend(["",f"Output: `{output.as_posix()}`", ""])
    report.write_text("\n".join(lines),encoding="utf-8")
    if passed:
        seal_file.write_text("# R9 FactSet panel seal\n\n"+f"Status: SEALED\n\nPanel: `{output.as_posix()}`\n\nSHA-256: `{h}`\n\nCoverage report: `{report.as_posix()}`\n",encoding="utf-8")
    else:
        seal_file.write_text("# R9 FactSet panel seal\n\nStatus: NOT SEALED — missing-price coverage gate failed.\n",encoding="utf-8")
    return passed

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw",type=Path,default=Path("factset_raw")); p.add_argument("--output",type=Path,default=Path("r9/factset/factset_panel.npz"))
    p.add_argument("--report",type=Path,default=Path("r9/factset/FACTSET_BUILD_REPORT.md")); p.add_argument("--seal-file",type=Path,default=Path("specs/r9_factset_seal.md"))
    a=p.parse_args()
    try:
        result=build(a.raw,a.output); passed=seal(a.output,a.report,a.seal_file,result)
    except InputError as e:
        raise SystemExit(str(e))
    # No values or hashes are printed to the terminal.
    if not passed: raise SystemExit(2)

if __name__=="__main__": main()
