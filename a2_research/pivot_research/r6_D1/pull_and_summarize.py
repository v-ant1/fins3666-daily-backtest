"""Download FINRA daily Reg SHO public files (dev window only) and summarize signal-only coverage."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time
import re
import requests
import pandas as pd
import numpy as np
import pandas_market_calendars as mcal

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "r6_data" / "finra_regsho"
RAW = OUT / "raw"
START, END = "2020-06-01", "2026-10-30"
BASE = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{}.txt"


def norm(s):
    s = str(s).strip().upper().replace(".", "/")
    return re.sub(r"^([A-Z]+)-([A-Z])$", r"\1/\2", s)


# Historical issuer/ticker transitions needed to match the supplied PIT roster
# to the symbol actually printed by FINRA. VTRS/MYL is a predecessor mapping;
# it is flagged as such rather than treated as a simple ticker rename.
ALIASES = {
    "BALL": [("1900-01-01", "2022-05-10", "BLL")],
    "BBWI": [("1900-01-01", "2021-08-03", "LB")],
    "CPAY": [("1900-01-01", "2024-03-25", "FLT")],
    "COR": [("1900-01-01", "2023-08-30", "ABC")],
    "CTRA": [("1900-01-01", "2021-10-01", "COG")],
    "EG": [("1900-01-01", "2023-07-10", "RE")],
    "ELV": [("1900-01-01", "2022-06-28", "ANTM")],
    "GEN": [("1900-01-01", "2022-11-08", "NLOK")],
    "LUMN": [("1900-01-01", "2020-09-18", "CTL")],
    "META": [("1900-01-01", "2022-06-09", "FB")],
    "MRSH": [("1900-01-01", "2026-01-14", "MMC")],
    "RVTY": [("1900-01-01", "2023-05-09", "PKI")],
    "SKYD": [("1900-01-01", "2022-02-16", "VIAC"),
             ("2022-02-16", "2025-08-07", "PARA"),
             ("2025-08-07", "2026-10-06", "PSKY")],
    "SW": [("1900-01-01", "2024-07-08", "WRK")],
    "VTRS": [("1900-01-01", "2020-11-16", "MYL")],
}


def source_symbol(ticker, day):
    target = norm(ticker)
    for lo, hi, src in ALIASES.get(target, []):
        if lo <= day < hi:
            return norm(src)
    return target


def get_calendar_dates():
    return [x.strftime("%Y-%m-%d") for x in mcal.get_calendar("NYSE").schedule(START, END).index]


def fetch(day):
    path = RAW / f"CNMSshvol{day.replace('-', '')}.txt"
    if path.exists() and path.stat().st_size > 0:
        return day, "cached", path.stat().st_size, BASE.format(day.replace("-", ""))
    url = BASE.format(day.replace("-", ""))
    for attempt in range(4):
        try:
            res = requests.get(url, timeout=60)
            if res.status_code == 404:
                return day, "missing_404", 0, url
            if res.status_code == 200 and res.text.startswith("Date|Symbol|"):
                tmp = path.with_suffix(".tmp")
                tmp.write_bytes(res.content)
                tmp.replace(path)
                return day, "downloaded", len(res.content), url
            msg = f"HTTP {res.status_code}; invalid header={res.text[:40]!r}"
        except Exception as e:
            msg = repr(e)
        if attempt < 3:
            time.sleep(0.6 * (attempt + 1))
    return day, "error", 0, f"{url} :: {msg}"


def load_membership(path, cols):
    d = pd.read_csv(path, dtype={"ticker": str})
    d["ticker"] = d.ticker.map(norm)
    d["effective_from"] = pd.to_datetime(d.effective_from)
    d["effective_to_exclusive"] = pd.to_datetime(d.effective_to_exclusive)
    return d


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    alias_rows = [(t, lo, hi, src, "ticker/issuer continuity mapping; VTRS-to-MYL is predecessor mapping")
                  for t, ranges in ALIASES.items() for lo, hi, src in ranges]
    alias_rows.extend([(t, "2020-06-01", "2026-10-31", norm(t), "FINRA share-class slash matched to roster hyphen")
                       for t in ("BF-B", "BRK-B")])
    pd.DataFrame(alias_rows, columns=["roster_ticker", "from_inclusive", "to_exclusive", "FINRA_symbol", "note"]).to_csv(OUT / "ticker_aliases.csv", index=False)
    days = get_calendar_dates()
    with ThreadPoolExecutor(max_workers=12) as pool:
        rows = list(pool.map(fetch, days))
    fetchlog = pd.DataFrame(rows, columns=["date", "status_this_run", "bytes", "source"])
    old_manifest = OUT / "download_manifest.csv"
    if old_manifest.exists():
        prior = pd.read_csv(old_manifest)
        prior_status = dict(zip(prior.date.astype(str), prior.get("retrieval_status", prior.get("status", []))))
    else:
        prior_status = {}
    fetchlog["retrieval_status"] = [prior_status.get(str(day), status) if status == "cached" else status
                                    for day, status in zip(fetchlog.date, fetchlog.status_this_run)]
    fetchlog = fetchlog[["date", "retrieval_status", "status_this_run", "bytes", "source"]]
    fetchlog.to_csv(OUT / "download_manifest.csv", index=False)

    sp = load_membership(ROOT / "r6_data" / "sp500_pit_roster.csv", None)
    dow = load_membership(ROOT / "r6_D1" / "dow_pit_roster.csv", None)
    # Read only the FINRA public flow files; no price or return inputs are opened.
    data = []
    daily = []
    for day in days:
        dt = pd.Timestamp(day)
        path = RAW / f"CNMSshvol{day.replace('-', '')}.txt"
        status = fetchlog.loc[fetchlog.date.eq(day), "retrieval_status"].iloc[0]
        if not path.exists():
            for uni, roster in (("SP500", sp), ("DOW30", dow)):
                n = int(((roster.effective_from <= dt) & (roster.effective_to_exclusive > dt)).ticker.nunique())
                daily.append((day, uni, status, 0, n, np.nan, 0, ";".join("NO_FILE" for _ in range(n))))
            continue
        f = pd.read_csv(path, sep="|", dtype={"Date": str, "Symbol": str})
        f["ticker"] = f.Symbol.map(norm)
        f["short_ratio"] = pd.to_numeric(f.ShortVolume, errors="coerce") / pd.to_numeric(f.TotalVolume, errors="coerce").replace(0, np.nan)
        f = f[["ticker", "short_ratio", "ShortVolume", "ShortExemptVolume", "TotalVolume"]]
        f = f.drop_duplicates("ticker", keep="last")
        symbols = set(f.ticker)
        by = f.set_index("ticker")
        for uni, roster in (("SP500", sp), ("DOW30", dow)):
            active = roster.loc[(roster.effective_from <= dt) & (roster.effective_to_exclusive > dt), "ticker"].drop_duplicates().tolist()
            symbol_map = {t: source_symbol(t, day) for t in active}
            matched = [t for t, s in symbol_map.items() if s in symbols]
            missing_names = [t for t, s in symbol_map.items() if s not in symbols]
            source_names = [symbol_map[t] for t in matched]
            ratios = by.loc[source_names, "short_ratio"].replace([np.inf, -np.inf], np.nan).dropna() if matched else pd.Series(dtype=float)
            total_rows = int(len(f))
            daily.append((day, uni, status, len(matched), len(active), float(ratios.mean()) if len(ratios) else np.nan, total_rows, ";".join(missing_names)))
            for t in matched:
                rec = by.loc[symbol_map[t]]
                data.append((day, uni, t, float(rec.short_ratio) if pd.notna(rec.short_ratio) else np.nan,
                             float(rec.ShortVolume), float(rec.ShortExemptVolume), float(rec.TotalVolume)))

    dailydf = pd.DataFrame(daily, columns=["date", "universe", "file_status", "matched_names", "roster_names", "mean_name_short_ratio", "finra_file_symbol_rows", "unmatched_roster_symbols"])
    dailydf["coverage_pct"] = 100 * dailydf.matched_names / dailydf.roster_names.replace(0, np.nan)
    dailydf.to_csv(OUT / "daily_coverage.csv", index=False)
    sig = pd.DataFrame(data, columns=["date", "universe", "ticker", "short_volume_ratio", "short_volume", "short_exempt_volume", "finra_total_volume"])
    sig.to_csv(OUT / "signal_panel.csv.gz", index=False, compression="gzip")

    summaries = []
    for uni, g in sig.groupby("universe"):
        g["date"] = pd.to_datetime(g.date)
        wide = g.pivot(index="date", columns="ticker", values="short_volume_ratio").sort_index()
        cs_sd = wide.std(axis=1, ddof=1)
        # ACF is computed on per-name daily short-volume ratios; gaps remain missing,
        # so lag-1 uses only adjacent observed exchange sessions.
        acfs = []
        for t in wide.columns:
            x = wide[t]
            pairs = pd.concat([x, x.shift(1)], axis=1).dropna()
            if len(pairs) >= 30:
                acf = pairs.iloc[:, 0].corr(pairs.iloc[:, 1])
                if pd.notna(acf): acfs.append(float(acf))
        cross_mean = wide.mean(axis=1)
        summaries.append({
            "universe": uni, "signal_rows": len(g), "names_seen": int(g.ticker.nunique()),
            "daily_dates_with_any_signal": int(wide.notna().any(axis=1).sum()),
            "median_cross_sectional_sd": float(cs_sd.median()),
            "p10_cross_sectional_sd": float(cs_sd.quantile(.10)),
            "p90_cross_sectional_sd": float(cs_sd.quantile(.90)),
            "median_name_acf1": float(np.median(acfs)) if acfs else np.nan,
            "p25_name_acf1": float(np.quantile(acfs, .25)) if acfs else np.nan,
            "p75_name_acf1": float(np.quantile(acfs, .75)) if acfs else np.nan,
            "names_in_name_acf1_summary": len(acfs),
            "universe_mean_signal_acf1": float(cross_mean.corr(cross_mean.shift(1))),
            "mean_short_volume_ratio": float(g.short_volume_ratio.mean()),
            "median_short_volume_ratio": float(g.short_volume_ratio.median()),
        })
    pd.DataFrame(summaries).to_csv(OUT / "signal_statistics.csv", index=False)
    print(f"calendar sessions={len(days)}; downloaded={(fetchlog.retrieval_status=='downloaded').sum()}; cached={(fetchlog.status_this_run=='cached').sum()}; missing={(fetchlog.status_this_run=='missing_404').sum()}; errors={(fetchlog.status_this_run=='error').sum()}")
    print(pd.DataFrame(summaries).to_string(index=False))

if __name__ == "__main__":
    main()
