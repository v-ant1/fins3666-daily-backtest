from __future__ import annotations
import argparse, hashlib, json, os, time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from dotenv import dotenv_values
import exchange_calendars as xc

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
ENV_PATH = Path(r"C:\Users\musta\Desktop\UNSW\SSI\FINS3666\A2\.env")
SP_ROSTER = PROJECT / "r6_data" / "sp500_pit_roster.csv"
DOW_ROSTER = PROJECT / "r6_D1" / "dow_pit_roster.csv"
START_DATE = date(2020, 11, 27)
END_DATE = date(2026, 10, 30)
NY = ZoneInfo("America/New_York")
API = "https://data.alpaca.markets"
MANIFEST_PATH = ROOT / "PULL_MANIFEST.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path: Path, obj: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def load_intervals(path: Path, universe: str) -> dict[str, list[tuple[date, date]]]:
    df = pd.read_csv(path, dtype=str).fillna("")
    out: dict[str, list[tuple[date, date]]] = {}
    for row in df.itertuples(index=False):
        ticker = str(getattr(row, "ticker")).strip().upper()
        if not ticker:
            continue
        a = date.fromisoformat(str(getattr(row, "effective_from"))[:10])
        b_raw = str(getattr(row, "effective_to_exclusive"))
        b = date.fromisoformat(b_raw[:10]) if b_raw else date(2100, 1, 1)
        # Clamp the in-memory point-in-time map to the authorized development window.
        a = max(a, START_DATE)
        b = min(b, END_DATE + timedelta(days=1))
        if a < b:
            out.setdefault(ticker, []).append((a, b))
    return out


def active(intervals: dict[str, list[tuple[date, date]]], ticker: str, day: date) -> bool:
    return any(a <= day < b for a, b in intervals.get(ticker, []))


def api_symbol(ticker: str) -> str:
    """Translate roster class-share tickers to Alpaca's dot notation."""
    return {"BF-B": "BF.B", "BRK-B": "BRK.B"}.get(ticker, ticker)


def roster_digest(path: Path) -> str:
    return sha256_file(path)


def init_manifest() -> dict[str, Any]:
    if MANIFEST_PATH.exists():
        m = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    else:
        m = {
            "schema_version": 1,
            "created_utc": datetime.now(tz=ZoneInfo("UTC")).isoformat(),
            "date_window": {"start_inclusive": START_DATE.isoformat(), "end_inclusive": END_DATE.isoformat()},
            "sources": {
                "sp500_roster": {"path": str(SP_ROSTER.relative_to(PROJECT)), "sha256": roster_digest(SP_ROSTER)},
                "dow_roster": {"path": str(DOW_ROSTER.relative_to(PROJECT)), "sha256": roster_digest(DOW_ROSTER)},
            },
            "settings": {
                "feed": "sip", "minute_timeframe": "1Min", "adjustment": "raw",
                "session": "regular US session only (XNYS calendar; local 09:30 inclusive to close exclusive)",
                "rate_limit_target_rpm": 190, "max_page_rows": 10000,
                "split_adjustments": "stored separately from raw minute prices/volume",
            },
            "status": "in_progress",
            "minute_tasks": {}, "auction_tasks": {}, "split_tasks": {},
            "failed_requests": [],
        }
    if m.get("date_window") != {"start_inclusive": START_DATE.isoformat(), "end_inclusive": END_DATE.isoformat()}:
        raise RuntimeError("Manifest date window differs from the authorized window; refusing to resume")
    return m


def save_manifest(m: dict[str, Any]) -> None:
    m["updated_utc"] = datetime.now(tz=ZoneInfo("UTC")).isoformat()
    atomic_json(MANIFEST_PATH, m)


class AlpacaClient:
    def __init__(self, pair: str = "primary") -> None:
        env = dotenv_values(ENV_PATH)
        if pair == "primary":
            key, secret = env.get("ALPACA_API_KEY"), env.get("ALPACA_SECRET_KEY")
        elif pair == "alternate":
            key, secret = env.get("2_ALPACA_API_KEY"), env.get("2_ALPACA_SECRET_KEY")
        else:
            raise ValueError("unknown credential pair")
        if not key or not secret:
            raise RuntimeError(f"Credential pair {pair} is missing in .env")
        self.headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret, "accept": "application/json"}
        self.session = requests.Session()
        self.last_call = 0.0
        self.rpm_target = 190
        self.stats = {"requests": 0, "retries": 0, "last_rate_limit": None, "last_remaining": None}

    def get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if "start" in params and date.fromisoformat(str(params["start"])[:10]) < START_DATE:
            raise RuntimeError("Refusing API request with start before 2020-11-27")
        if "end" in params and date.fromisoformat(str(params["end"])[:10]) > END_DATE:
            raise RuntimeError("Refusing API request with end after 2026-10-30")
        for attempt in range(7):
            wait = 60.0 / self.rpm_target - (time.time() - self.last_call)
            if wait > 0:
                time.sleep(wait)
            started = time.time()
            try:
                response = self.session.get(API + path, params=params, headers=self.headers, timeout=90)
            except requests.RequestException:
                self.stats["retries"] += 1
                if attempt == 6:
                    raise
                time.sleep(min(2 ** attempt, 60))
                continue
            self.last_call = time.time()
            self.stats["requests"] += 1
            self.stats["last_rate_limit"] = response.headers.get("X-RateLimit-Limit")
            self.stats["last_remaining"] = response.headers.get("X-RateLimit-Remaining")
            if response.status_code == 429 or response.status_code >= 500:
                self.stats["retries"] += 1
                if attempt == 6:
                    raise RuntimeError(f"HTTP {response.status_code} after retries for {path}")
                reset = response.headers.get("X-RateLimit-Reset")
                delay = max(1.0, float(reset) - time.time()) if reset and response.status_code == 429 else min(2 ** attempt, 60)
                time.sleep(min(delay + 0.25, 120))
                continue
            if not response.ok:
                try:
                    body = response.json()
                    msg = str(body.get("message", body.get("code", "API error")))[:200]
                except Exception:
                    msg = f"HTTP {response.status_code}"
                raise RuntimeError(f"HTTP {response.status_code}: {msg}")
            return response.json()
        raise RuntimeError("Request loop exhausted")


def get_calendar() -> pd.DataFrame:
    cal = xc.get_calendar("XNYS")
    schedule = cal.schedule.loc[pd.Timestamp(START_DATE):pd.Timestamp(END_DATE)].copy()
    schedule.index = pd.to_datetime(schedule.index).date
    schedule["date"] = schedule.index
    schedule["minute_slots"] = ((schedule["close"] - schedule["open"]).dt.total_seconds() / 60).astype(int)
    return schedule


def months_in_window() -> list[str]:
    return [p.strftime("%Y-%m") for p in pd.period_range(START_DATE.isoformat(), END_DATE.isoformat(), freq="M")]


def eligible_symbols_months(intervals: dict[str, list[tuple[date, date]]], schedule: pd.DataFrame) -> dict[str, list[str]]:
    months = months_in_window()
    days_by_month: dict[str, list[date]] = {}
    for d in schedule.index:
        days_by_month.setdefault(d.strftime("%Y-%m"), []).append(d)
    result: dict[str, list[str]] = {}
    for sym, spans in intervals.items():
        active_months = []
        for month in months:
            days = days_by_month.get(month, [])
            if any(active({sym: spans}, sym, d) for d in days):
                active_months.append(month)
        result[sym] = active_months
    return result


def months_args(month: str, sessions: pd.DataFrame) -> dict[str, str] | None:
    rows = sessions[sessions.index.map(lambda d: d.strftime("%Y-%m") == month)]
    if rows.empty:
        return None
    start_open = rows.iloc[0]["open"].to_pydatetime().astimezone(NY)
    end_close = rows.iloc[-1]["close"].to_pydatetime().astimezone(NY)
    # The window starts at the first regular open of the month and ends at the last regular close.
    return {"start": start_open.isoformat(), "end": end_close.isoformat()}


def partition_path(kind: str, month: str, ticker: str) -> Path:
    folder = ROOT / kind / f"month={month}"
    folder.mkdir(parents=True, exist_ok=True)
    safe = ticker.replace("/", "_").replace("\\", "_")
    return folder / f"part-{safe}.parquet"


def valid_existing(entry: dict[str, Any] | None, path: Path) -> bool:
    if entry and entry.get("status") == "complete" and int(entry.get("rows", -1)) == 0 and not entry.get("path"):
        return True
    return bool(entry and entry.get("status") == "complete" and path.exists() and sha256_file(path) == entry.get("sha256"))


def existing_recover(path: Path, universe_flags: dict[str, dict[str, list[tuple[date,date]]]], ticker: str, kind: str, expected_sessions: list[date], expected_slots: int) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        table = pq.read_table(path)
        df = table.to_pandas()
        count = len(df)
        return {"status":"complete","path":str(path.relative_to(PROJECT)),"sha256":sha256_file(path),"rows":count,"recovered_from_partition":True}
    except Exception:
        return None


def record_membership(ticker: str, d: date, spans: dict[str, dict[str, list[tuple[date,date]]]]) -> tuple[bool,bool]:
    return active(spans["sp500"], ticker, d), active(spans["dow"], ticker, d)


def pull_minute_task(client: AlpacaClient, ticker: str, month: str, schedule: pd.DataFrame, spans: dict[str, dict[str, list[tuple[date,date]]]], m: dict[str,Any]) -> None:
    key=f"{ticker}|{month}"; outpath=partition_path("minute",month,ticker)
    entry=m["minute_tasks"].get(key)
    if valid_existing(entry,outpath): return
    month_days=[d for d in schedule.index if d.strftime("%Y-%m")==month and (active(spans["sp500"],ticker,d) or active(spans["dow"],ticker,d))]
    if not month_days:
        return
    session_rows=schedule.loc[month_days]
    expected_slots=sum(int(x) for x in session_rows["minute_slots"])
    args=months_args(month,schedule)
    assert args and date.fromisoformat(args["start"][:10])>=START_DATE
    pages=[]; token=None; page_count=0
    while True:
        params={"symbols":api_symbol(ticker),"timeframe":"1Min","adjustment":"raw","feed":"sip","start":args["start"],"end":args["end"],"limit":10000,"sort":"asc"}
        if token: params["page_token"]=token
        body=client.get_json("/v2/stocks/bars",params)
        page_count += 1
        pages.extend((body.get("bars") or {}).get(api_symbol(ticker),[]))
        token=body.get("next_page_token")
        if not token: break
    # Retain only the authorized point-in-time membership and regular-session minutes.
    by_date={d:(row["open"].to_pydatetime(),row["close"].to_pydatetime()) for d,row in session_rows.iterrows()}
    rows=[]; per_day={d:0 for d in month_days}
    for b in pages:
        ts=pd.Timestamp(b["t"])
        if ts.tzinfo is None: ts=ts.tz_localize("UTC")
        else: ts=ts.tz_convert("UTC")
        d=ts.tz_convert(NY).date()
        if d not in by_date or not (active(spans["sp500"],ticker,d) or active(spans["dow"],ticker,d)):
            continue
        op,cl=by_date[d]
        if not (op <= ts.to_pydatetime() < cl):
            continue
        sp,dw=record_membership(ticker,d,spans)
        rows.append({"symbol":ticker,"timestamp":ts.to_pydatetime(),"open":b.get("o"),"high":b.get("h"),"low":b.get("l"),"close":b.get("c"),"volume":b.get("v"),"trade_count":b.get("n"),"vwap":b.get("vw"),"sp500_member":sp,"dow_member":dw})
        per_day[d]+=1
    df=pd.DataFrame(rows,columns=["symbol","timestamp","open","high","low","close","volume","trade_count","vwap","sp500_member","dow_member"])
    if len(df):
        df["timestamp"]=pd.to_datetime(df["timestamp"],utc=True,format="mixed")
        df["volume"]=pd.to_numeric(df["volume"],errors="coerce").astype("Int64")
        df["trade_count"]=pd.to_numeric(df["trade_count"],errors="coerce").astype("Int64")
        tmp=outpath.with_suffix(".tmp.parquet")
        df.to_parquet(tmp,index=False,compression="zstd")
        os.replace(tmp,outpath)
    missing=[d.isoformat() for d,n in per_day.items() if n==0]
    minute_shortfall=sum(max(0,int(session_rows.loc[d,"minute_slots"])-per_day[d]) for d in month_days)
    m["minute_tasks"][key]={"status":"complete","path":str(outpath.relative_to(PROJECT)) if len(df) else None,"sha256":sha256_file(outpath) if len(df) else None,"rows":int(len(df)),"requested_pages":page_count,"expected_active_sessions":len(month_days),"expected_regular_minutes":expected_slots,"observed_bar_dates":sum(n>0 for n in per_day.values()),"no_bar_dates":missing,"missing_minute_slots":int(minute_shortfall),"note":"Absent minute bars can mean no qualifying prints; slot shortfall is not by itself proof of vendor data loss."}
    save_manifest(m)


def pull_auction_task(client: AlpacaClient, ticker: str, month: str, schedule: pd.DataFrame, spans: dict[str, dict[str, list[tuple[date,date]]]], m: dict[str,Any]) -> None:
    key=f"{ticker}|{month}"; outpath=partition_path("auctions",month,ticker)
    entry=m["auction_tasks"].get(key)
    if valid_existing(entry,outpath): return
    month_days=[d for d in schedule.index if d.strftime("%Y-%m")==month and (active(spans["sp500"],ticker,d) or active(spans["dow"],ticker,d))]
    if not month_days: return
    args=months_args(month,schedule); assert args
    # The auction API treats `end` as exclusive.  Extend the final regular
    # close by one minute so the closing-cross event at 16:00 ET is included.
    auction_end = datetime.fromisoformat(args["end"]) + timedelta(minutes=1)
    params={"start":args["start"],"end":auction_end.isoformat(),"feed":"sip","limit":10000,"sort":"asc"}
    all_days=[]; token=None; page_count=0
    while True:
        p=dict(params)
        if token: p["page_token"]=token
        body=client.get_json(f"/v2/stocks/{api_symbol(ticker)}/auctions",p)
        page_count += 1
        all_days.extend(body.get("auctions") or [])
        token=body.get("next_page_token")
        if not token: break
    expected=set(month_days); observed=set(); open_dates=set(); close_dates=set(); records=[]
    for item in all_days:
        d=date.fromisoformat(str(item.get("d"))[:10])
        if d not in expected or not (active(spans["sp500"],ticker,d) or active(spans["dow"],ticker,d)): continue
        observed.add(d); sp,dw=record_membership(ticker,d,spans)
        for kind,arr in (("open",item.get("o") or []),("close",item.get("c") or [])):
            if arr:
                (open_dates if kind=="open" else close_dates).add(d)
            for e in arr:
                records.append({"symbol":ticker,"date":d,"auction_type":kind,"timestamp":e.get("t"),"price":e.get("p"),"size":e.get("s"),"condition":e.get("c"),"exchange":e.get("x"),"sp500_member":sp,"dow_member":dw})
    df=pd.DataFrame(records,columns=["symbol","date","auction_type","timestamp","price","size","condition","exchange","sp500_member","dow_member"])
    if len(df):
        df["date"]=pd.to_datetime(df["date"])
        df["timestamp"]=pd.to_datetime(df["timestamp"],utc=True,format="mixed")
        df["size"]=pd.to_numeric(df["size"],errors="coerce").astype("Int64")
        tmp=outpath.with_suffix(".tmp.parquet"); df.to_parquet(tmp,index=False,compression="zstd"); os.replace(tmp,outpath)
    no_data=[d.isoformat() for d in sorted(expected-observed)]
    no_open=[d.isoformat() for d in sorted(expected-open_dates)]
    no_close=[d.isoformat() for d in sorted(expected-close_dates)]
    m["auction_tasks"][key]={"status":"complete","path":str(outpath.relative_to(PROJECT)) if len(df) else None,"sha256":sha256_file(outpath) if len(df) else None,"rows":int(len(df)),"requested_pages":page_count,"expected_active_sessions":len(expected),"observed_auction_dates":len(observed),"no_auction_dates":no_data,"no_open_cross_dates":no_open,"no_close_cross_dates":no_close}
    save_manifest(m)


def pull_split_task(client: AlpacaClient, ticker: str, m: dict[str,Any]) -> None:
    if m["split_tasks"].get(ticker,{}).get("status")=="complete": return
    token=None; actions=[]
    while True:
        params={"symbols":api_symbol(ticker),"types":"forward_split,reverse_split","start":START_DATE.isoformat(),"end":END_DATE.isoformat(),"limit":1000,"sort":"asc"}
        if token: params["page_token"]=token
        body=client.get_json("/v1/corporate-actions",params)
        actions.extend(body.get("corporate_actions",[]))
        token=body.get("next_page_token")
        if not token: break
    m["split_tasks"][ticker]={"status":"complete","events":actions}
    save_manifest(m)


def save_splits(m: dict[str,Any]) -> None:
    all_events=[]
    for ticker,entry in m["split_tasks"].items():
        for ev in entry.get("events",[]):
            all_events.append({"symbol":ev.get("symbol",ticker),"type":ev.get("type"),"ex_date":ev.get("ex_date"),"process_date":ev.get("process_date"),"split_from":ev.get("split_from"),"split_to":ev.get("split_to"),"cash":ev.get("cash"),"raw_action":json.dumps(ev,sort_keys=True)})
    base=ROOT/"minute"/"split_factors"; base.mkdir(parents=True,exist_ok=True)
    p=base/"split_factors.parquet"
    df=pd.DataFrame(all_events,columns=["symbol","type","ex_date","process_date","split_from","split_to","cash","raw_action"])
    tmp=p.with_suffix(".tmp.parquet"); df.to_parquet(tmp,index=False,compression="zstd"); os.replace(tmp,p)
    m["split_factors"]={"path":str(p.relative_to(PROJECT)),"sha256":sha256_file(p),"rows":len(df),"start_inclusive":START_DATE.isoformat(),"end_inclusive":END_DATE.isoformat()}
    save_manifest(m)


def build_summary_context(sp:dict[str,list[tuple[date,date]]],dw:dict[str,list[tuple[date,date]]],schedule:pd.DataFrame) -> dict[str,Any]:
    expected: dict[str, set[str]] = {}
    for roster in (sp,dw):
        for ticker,months in eligible_symbols_months(roster,schedule).items(): expected.setdefault(ticker,set()).update(months)
    sp_sessions={t:sum(active(sp,t,d) for d in schedule.index) for t in sp}
    dw_sessions={t:sum(active(dw,t,d) for d in schedule.index) for t in dw}
    return {"expected_months":expected,"expected_keys":{f"{t}|{month}" for t,months in expected.items() for month in months},"sp500_member_ticker_sessions":sum(sp_sessions.values()),"dow_member_ticker_sessions":sum(dw_sessions.values())}


def rebuild_summary(m: dict[str,Any],sp:dict[str,list[tuple[date,date]]],dw:dict[str,list[tuple[date,date]]],schedule:pd.DataFrame,context:dict[str,Any]) -> None:
    tasks=m["minute_tasks"]; atasks=m["auction_tasks"]
    all_expected=context["expected_months"]
    expected_keys=context["expected_keys"]
    minute_done={k for k,v in tasks.items() if v.get("status")=="complete"}
    auction_done={k for k,v in atasks.items() if v.get("status")=="complete"}
    minute_complete=expected_keys.issubset(minute_done)
    auction_complete=expected_keys.issubset(auction_done)
    complete_tickers={t for t,months in all_expected.items() if all(f"{t}|{month}" in minute_done for month in months)}
    auction_complete_tickers={t for t,months in all_expected.items() if all(f"{t}|{month}" in auction_done for month in months)}
    minute_rows_by_ticker={t:sum(int(v.get("rows",0)) for k,v in tasks.items() if k.startswith(t+"|")) for t in all_expected}
    auction_rows_by_ticker={t:sum(int(v.get("rows",0)) for k,v in atasks.items() if k.startswith(t+"|")) for t in all_expected}
    m["coverage"]={
      "minute_expected_tasks":len(expected_keys),"minute_task_count":len(tasks),"minute_complete_tasks":sum(x.get("status")=="complete" for x in tasks.values()),"minute_unprocessed_tasks":len(expected_keys-minute_done),
      "minute_rows":sum(int(x.get("rows",0)) for x in tasks.values()),"minute_missing_sessions":sum(len(x.get("no_bar_dates",[])) for x in tasks.values()),
      "minute_missing_slots":sum(int(x.get("missing_minute_slots",0)) for x in tasks.values()),
      "auction_expected_tasks":len(expected_keys),"auction_task_count":len(atasks),"auction_complete_tasks":sum(x.get("status")=="complete" for x in atasks.values()),"auction_unprocessed_tasks":len(expected_keys-auction_done),
      "auction_rows":sum(int(x.get("rows",0)) for x in atasks.values()),
      "auction_missing_dates":sum(len(x.get("no_auction_dates",[])) for x in atasks.values()),
      "auction_missing_open_dates":sum(len(x.get("no_open_cross_dates",[])) for x in atasks.values()),
      "auction_missing_close_dates":sum(len(x.get("no_close_cross_dates",[])) for x in atasks.values()),
      "sp500_unique_tickers":len(sp),"dow_unique_tickers":len(dw),
      "sp500_member_ticker_sessions":context["sp500_member_ticker_sessions"],
      "dow_member_ticker_sessions":context["dow_member_ticker_sessions"],
      "missing_tickers_minute":[t for t in sorted(complete_tickers) if minute_rows_by_ticker.get(t,0)==0],
      "missing_tickers_auctions":[t for t in sorted(auction_complete_tickers) if auction_rows_by_ticker.get(t,0)==0],
    }
    m["status"]="complete" if not m.get("failed_requests") and minute_complete and auction_complete else "in_progress_or_gaps"
    save_manifest(m)


def main() -> None:
    parser=argparse.ArgumentParser(description="Checkpointed Alpaca SIP bars/auction downloader; only development dates allowed")
    parser.add_argument("--scope",choices=["dow","sp500","all"],required=True)
    parser.add_argument("--credential-pair",choices=["primary","alternate"],default="primary")
    parser.add_argument("--limit-tasks",type=int,default=0,help="debug cap; does not mark full completion")
    parser.add_argument("--with-splits",action="store_true")
    args=parser.parse_args()
    if not SP_ROSTER.exists() or not DOW_ROSTER.exists(): raise RuntimeError("Required point-in-time roster missing")
    if START_DATE.isoformat()<"2020-11-27": raise RuntimeError("Unauthorized start date")
    sp=load_intervals(SP_ROSTER,"sp500"); dw=load_intervals(DOW_ROSTER,"dow")
    schedule=get_calendar()
    spans={"sp500":sp,"dow":dw}
    summary_context=build_summary_context(sp,dw,schedule)
    target_universes=["dow","sp500"] if args.scope=="all" else [args.scope]
    symbols_by_month:dict[tuple[str,str],set[str]]={}
    for universe in target_universes:
        roster=dw if universe=="dow" else sp
        by=eligible_symbols_months(roster,schedule)
        for ticker,months in by.items():
            for month in months: symbols_by_month.setdefault((ticker,month),set()).add(universe)
    tasks=sorted(symbols_by_month,key=lambda x:(x[1],x[0]))
    if args.limit_tasks: tasks=tasks[:args.limit_tasks]
    m=init_manifest(); client=AlpacaClient(args.credential_pair)
    print(f"scope={args.scope} ticker_month_tasks={len(tasks)} sessions={len(schedule)} start={START_DATE} end={END_DATE}",flush=True)
    for i,(ticker,month) in enumerate(tasks,1):
        try:
            pull_minute_task(client,ticker,month,schedule,spans,m)
            pull_auction_task(client,ticker,month,schedule,spans,m)
            if args.with_splits and month=="2020-11": pull_split_task(client,ticker,m)
            m["failed_requests"]=[f for f in m.get("failed_requests",[]) if not (f.get("symbol")==ticker and f.get("month")==month)]
        except Exception as exc:
            m.setdefault("failed_requests",[]).append({"scope":args.scope,"symbol":ticker,"month":month,"error_type":type(exc).__name__,"error":str(exc)[:300],"attempted_utc":datetime.now(tz=ZoneInfo("UTC")).isoformat()})
            save_manifest(m)
        if i%25==0 or i==len(tasks):
            rebuild_summary(m,sp,dw,schedule,summary_context)
            m["last_run"]={"scope":args.scope,"requests":client.stats["requests"],"retries":client.stats["retries"],"last_rate_limit":client.stats["last_rate_limit"],"last_remaining":client.stats["last_remaining"]}
            save_manifest(m)
            print(json.dumps({"scope":args.scope,"task":i,"tasks":len(tasks),"ticker":ticker,"month":month,"minute_rows":m.get("coverage",{}).get("minute_rows",0),"auction_rows":m.get("coverage",{}).get("auction_rows",0),"expected_tasks":m.get("coverage",{}).get("minute_expected_tasks",0),"requests":client.stats["requests"],"retries":client.stats["retries"],"rate_limit":client.stats["last_rate_limit"],"remaining":client.stats["last_remaining"]}),flush=True)
    if args.with_splits:
        symbols=sorted(set(sp)|set(dw))
        for i,ticker in enumerate(symbols,1):
            pull_split_task(client,ticker,m)
            if i%25==0 or i==len(symbols): print(json.dumps({"phase":"splits","scope":args.scope,"ticker":ticker,"n":i,"total":len(symbols),"requests":client.stats["requests"]}),flush=True)
        save_splits(m)
    rebuild_summary(m,sp,dw,schedule,summary_context)
    m["last_run"]={"scope":args.scope,"requests":client.stats["requests"],"retries":client.stats["retries"],"last_rate_limit":client.stats["last_rate_limit"],"last_remaining":client.stats["last_remaining"]}
    save_manifest(m)
    print(json.dumps({"scope":args.scope,"status":m["status"],"coverage":m.get("coverage",{}),"requests":client.stats["requests"],"retries":client.stats["retries"]},indent=2),flush=True)

if __name__=="__main__": main()

