"""Build a development-only S&P 500 non-derivative Form 4 P/S panel.

Reads official SEC quarterly archives 2020Q2 through 2026Q3. Since 2020Q2 is
both the first development archive and the overlapping availability-check
boundary, its output is limited to filings and transactions on/after 2020-06-01.
Older archives 2009Q1 through 2020Q1 are checked separately with HEAD only and
are never opened here.
"""
from __future__ import annotations

import json
import re
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RAW = HERE / "raw"
START = date(2020, 6, 1)
END = date(2026, 10, 30)
ROSTER_PATH = ROOT / "sp500_pit_roster.csv"
CIK_PANEL_PATH = ROOT / "sp500_sic_panel.csv"


def ticker_key(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip().upper().replace(".", "-")


def cik_key(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    value = re.sub(r"\.0$", "", str(value).strip())
    return value.zfill(10) if value.isdigit() else ""


def tsv_columns(zf: zipfile.ZipFile, filename: str) -> list[str]:
    with zf.open(filename) as handle:
        return pd.read_csv(handle, sep="\t", nrows=0, encoding="utf-8").columns.tolist()


def read_tsv(zf: zipfile.ZipFile, filename: str, wanted: list[str]) -> pd.DataFrame:
    available = set(tsv_columns(zf, filename))
    usecols = [col for col in wanted if col in available]
    with zf.open(filename) as handle:
        return pd.read_csv(handle, sep="\t", usecols=usecols, dtype=str,
                           encoding="utf-8", keep_default_na=False)


def read_filtered_tsv(zf: zipfile.ZipFile, filename: str, wanted: list[str],
                      accession_set: set[str], chunksize: int = 250_000) -> pd.DataFrame:
    available = set(tsv_columns(zf, filename))
    usecols = [col for col in wanted if col in available]
    selected = []
    with zf.open(filename) as handle:
        for chunk in pd.read_csv(handle, sep="\t", usecols=usecols, dtype=str,
                                 encoding="utf-8", keep_default_na=False,
                                 chunksize=chunksize):
            chunk = chunk[chunk["ACCESSION_NUMBER"].isin(accession_set)]
            if not chunk.empty:
                selected.append(chunk)
    return pd.concat(selected, ignore_index=True) if selected else pd.DataFrame(columns=usecols)


def quarters() -> list[tuple[int, int]]:
    return [(year, quarter) for year in range(2020, 2027) for quarter in range(1, 5)
            if (year, quarter) >= (2020, 2) and (year, quarter) <= (2026, 3)]


def load_membership() -> tuple[dict[str, list[tuple[str, date, date]]], set[str]]:
    roster = pd.read_csv(ROSTER_PATH, dtype={"ticker": str})
    panel = pd.read_csv(CIK_PANEL_PATH, dtype={"ticker": str, "cik": str})
    panel["ticker"] = panel["ticker"].map(ticker_key)
    panel["cik"] = panel["cik"].map(cik_key)
    ticker_cik = panel.drop_duplicates(["ticker", "cik"])[["ticker", "cik"]]
    cik_counts = ticker_cik.groupby("ticker")["cik"].nunique()
    if (cik_counts > 1).any():
        raise RuntimeError("Multiple CIKs in the assembled SEC panel for at least one S&P ticker.")
    cik_by_ticker = dict(zip(ticker_cik["ticker"], ticker_cik["cik"]))
    active: dict[str, list[tuple[str, date, date]]] = defaultdict(list)
    missing = []
    for row in roster.itertuples(index=False):
        ticker = ticker_key(row.ticker)
        cik = cik_by_ticker.get(ticker, "")
        if not cik:
            missing.append(ticker)
            continue
        lo = date.fromisoformat(str(row.effective_from))
        hi = date.fromisoformat(str(row.effective_to_exclusive))
        active[cik].append((ticker, lo, hi))
    if missing:
        raise RuntimeError("No CIK mapping for S&P ticker(s): " + ",".join(sorted(set(missing))))
    return active, set(active)


def active_ticker(cik: str, txn_date: date, filing_symbol: str,
                  active: dict[str, list[tuple[str, date, date]]]) -> tuple[str | None, str]:
    candidates = [ticker for ticker, lo, hi in active.get(cik, []) if lo <= txn_date < hi]
    if not candidates:
        return None, "no active S&P 500 CIK interval on transaction date"
    symbol = ticker_key(filing_symbol)
    if symbol in candidates:
        return symbol, "matched CIK, active interval, and filing symbol"
    if len(candidates) == 1:
        return candidates[0], "matched CIK and sole active ticker interval"
    return None, "ambiguous multiple active S&P tickers for CIK"


def parse_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, format="%d-%b-%Y", errors="coerce")


def main() -> None:
    active, s_and_p_ciks = load_membership()
    all_rows = []
    archive_manifest = []
    mapping_unmatched = defaultdict(int)

    for year, quarter in quarters():
        archive = RAW / f"{year}q{quarter}_form345.zip"
        if not archive.exists():
            raise FileNotFoundError(f"Missing official SEC archive: {archive}")
        with zipfile.ZipFile(archive) as zf:
            submissions = read_tsv(zf, "SUBMISSION.tsv", [
                "ACCESSION_NUMBER", "FILING_DATE", "PERIOD_OF_REPORT", "DATE_OF_ORIG_SUB",
                "DOCUMENT_TYPE", "ISSUERCIK", "ISSUERNAME", "ISSUERTRADINGSYMBOL",
            ])
            submissions["issuer_cik"] = submissions["ISSUERCIK"].map(cik_key)
            submissions["filing_dt"] = parse_date(submissions["FILING_DATE"])
            submissions = submissions[
                submissions["issuer_cik"].isin(s_and_p_ciks)
                & submissions["filing_dt"].between(pd.Timestamp(START), pd.Timestamp(END))
            ].copy()
            accession_set = set(submissions["ACCESSION_NUMBER"])
            archive_manifest.append({
                "quarter": f"{year}Q{quarter}", "zip_file": archive.name,
                "zip_size_bytes": archive.stat().st_size,
                "s_and_p_issuer_submissions_in_window": len(submissions),
            })
            if not accession_set:
                continue

            owners = read_filtered_tsv(zf, "REPORTINGOWNER.tsv", [
                "ACCESSION_NUMBER", "RPTOWNERCIK", "RPTOWNERNAME",
                "RPTOWNER_RELATIONSHIP", "RPTOWNER_TITLE", "RPTOWNER_TXT",
            ], accession_set)
            owner_json_by_accession = {}
            owner_role_by_accession = {}
            if not owners.empty:
                for accession, group in owners.groupby("ACCESSION_NUMBER", sort=False):
                    details = []
                    roles = set()
                    for owner in group.to_dict("records"):
                        detail = {
                            "owner_cik": cik_key(owner.get("RPTOWNERCIK", "")),
                            "name": owner.get("RPTOWNERNAME", ""),
                            "role": owner.get("RPTOWNER_RELATIONSHIP", ""),
                            "title": owner.get("RPTOWNER_TITLE", ""),
                            "other_relationship": owner.get("RPTOWNER_TXT", ""),
                        }
                        details.append(detail)
                        roles.add(str(detail["role"]).strip())
                    owner_json_by_accession[accession] = json.dumps(details, ensure_ascii=False)
                    owner_role_by_accession[accession] = sorted(x for x in roles if x)

            transactions = read_filtered_tsv(zf, "NONDERIV_TRANS.tsv", [
                "ACCESSION_NUMBER", "NONDERIV_TRANS_SK", "SECURITY_TITLE", "TRANS_DATE",
                "TRANS_FORM_TYPE", "TRANS_CODE", "TRANS_SHARES", "TRANS_PRICEPERSHARE",
                "TRANS_TOTAL_VALUE", "TRANS_ACQUIRED_DISP_CD",
            ], accession_set)
            if transactions.empty:
                continue
            transactions = transactions[transactions["TRANS_CODE"].isin(["P", "S"])].copy()
            if transactions.empty:
                continue
            transactions["transaction_dt"] = parse_date(transactions["TRANS_DATE"])
            transactions = transactions[
                transactions["transaction_dt"].between(pd.Timestamp(START), pd.Timestamp(END))
            ].copy()
            if transactions.empty:
                continue
            joined = transactions.merge(submissions, on="ACCESSION_NUMBER", how="inner", suffixes=("", "_submission"))
            for row in joined.to_dict("records"):
                trans_day = row["transaction_dt"].date()
                filing_day = row["filing_dt"].date()
                ticker, reason = active_ticker(row["issuer_cik"], trans_day,
                                               row.get("ISSUERTRADINGSYMBOL", ""), active)
                if ticker is None:
                    mapping_unmatched[reason] += 1
                    continue
                roles = owner_role_by_accession.get(row["ACCESSION_NUMBER"], [])
                roles_upper = {re.sub(r"[^A-Z0-9]", "", role.upper()) for role in roles}
                all_rows.append({
                    "transaction_id": f"{row['ACCESSION_NUMBER']}:{row.get('NONDERIV_TRANS_SK', '')}",
                    "accession_number": row["ACCESSION_NUMBER"],
                    "archive_quarter": f"{year}Q{quarter}",
                    "document_type": row.get("DOCUMENT_TYPE", ""),
                    "issuer_cik": row["issuer_cik"],
                    "ticker": ticker,
                    "issuer_trading_symbol": row.get("ISSUERTRADINGSYMBOL", ""),
                    "issuer_name": row.get("ISSUERNAME", ""),
                    "reporting_owners_json": owner_json_by_accession.get(row["ACCESSION_NUMBER"], "[]"),
                    "owner_roles": "|".join(roles),
                    "is_officer": any("OFFICER" in role for role in roles_upper),
                    "is_director": any("DIRECTOR" in role for role in roles_upper),
                    "is_ten_percent_owner": any("TENPERCENTOWNER" in role or "10PERCENTOWNER" in role for role in roles_upper),
                    "transaction_date": pd.Timestamp(trans_day),
                    "filing_date": pd.Timestamp(filing_day),
                    "filing_lag_days": (filing_day - trans_day).days,
                    "transaction_code": row["TRANS_CODE"],
                    "transaction_form_type": row.get("TRANS_FORM_TYPE", ""),
                    "security_title": row.get("SECURITY_TITLE", ""),
                    "acquired_disposed_code": row.get("TRANS_ACQUIRED_DISP_CD", ""),
                    "shares": pd.to_numeric(row.get("TRANS_SHARES", ""), errors="coerce"),
                    "price_usd": pd.to_numeric(row.get("TRANS_PRICEPERSHARE", ""), errors="coerce"),
                    "value_usd": pd.to_numeric(row.get("TRANS_TOTAL_VALUE", ""), errors="coerce"),
                })

    out = pd.DataFrame(all_rows)
    out = out.drop_duplicates("transaction_id").sort_values(["transaction_date", "ticker", "accession_number", "transaction_id"])
    out.to_parquet(HERE / "form4_dev.parquet", index=False)

    out["transaction_year"] = pd.to_datetime(out["transaction_date"]).dt.year
    out["purchase_count"] = out["transaction_code"].eq("P").astype(int)
    out["sale_count"] = out["transaction_code"].eq("S").astype(int)
    year_counts = out.groupby("transaction_year", as_index=False).agg(
        purchases=("purchase_count", "sum"), sales=("sale_count", "sum"),
        transaction_rows=("transaction_id", "nunique"))
    year_counts.to_csv(HERE / "counts_by_year.csv", index=False)
    issuer_counts = out.groupby(["ticker", "issuer_cik", "issuer_name"], as_index=False).agg(
        purchases=("purchase_count", "sum"), sales=("sale_count", "sum"),
        transaction_rows=("transaction_id", "nunique"))
    issuer_counts.sort_values(["ticker", "issuer_cik"]).to_csv(HERE / "counts_by_issuer.csv", index=False)
    issuer_year = out.groupby(["transaction_year", "ticker", "issuer_cik", "issuer_name"], as_index=False).agg(
        purchases=("purchase_count", "sum"), sales=("sale_count", "sum"),
        transaction_rows=("transaction_id", "nunique"))
    issuer_year.sort_values(["transaction_year", "ticker"]).to_csv(HERE / "counts_by_issuer_year.csv", index=False)

    lag_bins = [-10**9, -1, 0, 1, 2, 3, 5, 10, 30, 90, 365, 10**9]
    lag_labels = ["negative", "0", "1", "2", "3", "4-5", "6-10", "11-30", "31-90", "91-365", ">365"]
    out["filing_lag_bin"] = pd.cut(out["filing_lag_days"], bins=lag_bins,
                                    labels=lag_labels, right=True, include_lowest=True)
    out.groupby("filing_lag_bin", observed=False).size().rename("transaction_rows").reindex(lag_labels, fill_value=0).rename_axis("lag_calendar_days").reset_index().to_csv(HERE / "filing_lag_distribution.csv", index=False)
    pd.DataFrame(archive_manifest).to_csv(HERE / "dev_archive_manifest.csv", index=False)
    (HERE / "mapping_unmatched.json").write_text(json.dumps(dict(mapping_unmatched), indent=2), encoding="utf-8")
    print(f"transactions={len(out)} issuers={out['issuer_cik'].nunique() if len(out) else 0} "
          f"first_transaction={out['transaction_date'].min() if len(out) else ''} "
          f"last_transaction={out['transaction_date'].max() if len(out) else ''} "
          f"unmatched={dict(mapping_unmatched)}")


if __name__ == "__main__":
    main()
