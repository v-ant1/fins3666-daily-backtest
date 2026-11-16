"""Summarize input coverage only; it does not load outcomes."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
C1 = ROOT / "r6_C1"
START, END = pd.Timestamp("2020-11-27"), pd.Timestamp("2026-10-30")


def coverage(name: str, bars_path: Path, roster_path: Path, dow: bool) -> tuple[str, pd.DataFrame]:
    c = pd.read_parquet(bars_path, columns=["date", "ticker", "overnight_return", "intraday_return"])
    c["date"] = pd.to_datetime(c.date)
    if dow:
        # Same point-in-time roster construction as build_inputs.py.
        from build_inputs import dow_roster
        cal = pd.DatetimeIndex(sorted(c.date.unique()))
        ex = dow_roster(cal)
        expected = ex.groupby("date").ticker.nunique()
    else:
        r = pd.read_csv(roster_path)
        r["effective_from"] = pd.to_datetime(r.effective_from)
        r["effective_to_exclusive"] = pd.to_datetime(r.effective_to_exclusive)
        expected = {}
        for d in sorted(c.date.unique()):
            expected[d] = int(((r.effective_from <= d) & (r.effective_to_exclusive > d)).sum())
        expected = pd.Series(expected)
    actual = c.groupby("date").ticker.nunique()
    qrows = []
    for q, values in actual.groupby(actual.index.to_period("Q")):
        exp = expected.reindex(values.index).fillna(0)
        qrows.append({"universe": name, "quarter": str(q), "trading_dates": len(values),
                      "median_bars_names": int(values.median()), "min_bars_names": int(values.min()),
                      "median_roster_names": int(exp.median()),
                      "median_bar_coverage_pct": round(100 * (values / exp.replace(0, pd.NA)).median(), 2),
                      "dates_at_full_roster_pct": round(100 * (values >= exp).mean(), 2)})
    t0 = c.groupby("ticker").date.min().sort_values()
    miss = int(((c.overnight_return.isna()) | (c.intraday_return.isna())).sum())
    text = (f"### {name}\n\n- Dates in component panel: {c.date.min().date()} through {c.date.max().date()} ({c.date.nunique():,} sessions).\n"
            f"- Asset-date component rows: {len(c):,}; distinct tickers: {c.ticker.nunique()}; missing same-day components: {c.intraday_return.isna().sum():,}; first-session overnight values without a prior in-window close: {c.overnight_return.isna().sum():,}.\n"
            f"- Earliest available price file begins {t0.min().date()}; daily quarter coverage is in the table below.\n")
    return text, pd.DataFrame(qrows)


def sic_coverage(name: str, bars_path: Path, membership_path: Path) -> pd.DataFrame:
    c = pd.read_parquet(bars_path, columns=["date", "ticker", "component_spread"])
    c["date"] = pd.to_datetime(c.date)
    m = pd.read_csv(membership_path, parse_dates=["effective_from", "effective_to_exclusive"])
    rows = []
    for q, g in c.groupby(c.date.dt.to_period("Q")):
        daily_cover, daily_groups = [], []
        for date, names in g.groupby("date"):
            eligible = set(names.loc[names.component_spread.notna(), "ticker"])
            active = m.loc[(m.effective_from <= date) & (m.effective_to_exclusive > date) & m.ticker.isin(eligible)]
            daily_cover.append(active.ticker.nunique())
            daily_groups.append(active.sic2.nunique())
        rows.append({"universe": name, "quarter": str(q), "median_names_with_dated_SIC": int(pd.Series(daily_cover).median()),
                     "minimum_names_with_dated_SIC": int(min(daily_cover)), "median_dated_SIC2_groups": float(pd.Series(daily_groups).median())})
    return pd.DataFrame(rows)


def main() -> None:
    manifest = json.loads((C1 / "input_manifest.json").read_text(encoding="utf-8"))
    dtext, dq = coverage("Dow", C1 / "dow_components_dev.parquet", ROOT / "repo/prices-daily", True)
    stext, sq = coverage("S&P 500", C1 / "sp500_components_dev.parquet", ROOT / "r6_data/sp500_pit_roster.csv", False)
    quarters = pd.concat([dq, sq], ignore_index=True)
    quarters.to_csv(C1 / "coverage_by_quarter.csv", index=False)
    sections = ["# C1 input QA (development dates only)", "",
                "This report checks inputs, roster membership, and point-in-time SIC availability only. The builder loaded adjusted OHLCV, then created same-day overnight and intraday returns; it did not load or compute forward returns, return outcomes, ICs, or strategy performance. No holdout data were accessed. The input window is 2020-11-27 through 2026-10-30.", "",
                dtext, "", "| Quarter | Sessions | Median bars names | Minimum bars names | Median PIT roster | Median bar coverage | Dates with full-roster bars |", "|---|---:|---:|---:|---:|---:|---:|"]
    sections += [f"| {r.quarter} | {r.trading_dates} | {r.median_bars_names} | {r.min_bars_names} | {r.median_roster_names} | {r.median_bar_coverage_pct:.2f}% | {r.dates_at_full_roster_pct:.2f}% |" for r in dq.itertuples()]
    sections += ["", stext, "", "| Quarter | Sessions | Median bars names | Minimum bars names | Median PIT roster | Median bar coverage | Dates with full-roster bars |", "|---|---:|---:|---:|---:|---:|---:|"]
    sections += [f"| {r.quarter} | {r.trading_dates} | {r.median_bars_names} | {r.min_bars_names} | {r.median_roster_names} | {r.median_bar_coverage_pct:.2f}% | {r.dates_at_full_roster_pct:.2f}% |" for r in sq.itertuples()]
    dmem = pd.read_csv(C1 / "dow_sic_membership.csv")
    smem_path = C1 / "sp500_sic_membership.csv"
    smem = pd.read_csv(smem_path) if smem_path.exists() else pd.DataFrame()
    dedges = pd.read_csv(C1 / "dow_industry_links.csv")
    sedges_path = C1 / "sp500_industry_links.csv"
    sedges = pd.read_csv(sedges_path) if sedges_path.exists() else pd.DataFrame()
    sections += ["", "## Point-in-time industry link coverage", "",
                 "A SIC observation is made available from the next trading day after its SEC filing date. Membership files store SIC2/SIC3 intervals; edge files represent pairwise same-industry overlaps during those intervals. Counts below are input coverage, not outcome evidence.", "",
                 "| Universe | Price tickers | Tickers with dated SIC | SIC coverage | SIC2 linked pairs | SIC3 linked pairs |", "|---|---:|---:|---:|---:|---:|"]
    for nm, bars_path, m, e in [("Dow", C1 / "dow_components_dev.parquet", dmem, dedges), ("S&P 500", C1 / "sp500_components_dev.parquet", smem, sedges)]:
        pnames = set(pd.read_parquet(bars_path, columns=["ticker"]).ticker)
        n = len(pnames & set(m.ticker)) if len(m) else 0
        prices = len(pnames)
        e2 = int((e.sic_level == "sic2").sum()) if len(e) else 0
        e3 = int((e.sic_level == "sic3").sum()) if len(e) else 0
        sections.append(f"| {nm} | {prices} | {n} | {100*n/prices:.1f}% | {e2:,} | {e3:,} |")
    sections += ["", "### Dated SIC coverage by available universe", "",
                 f"Dow SIC panel source: [`r4_L4/data/sic_panel.csv`](../r4_L4/data/sic_panel.csv); the 2-digit/3-digit dates in the emitted files are shifted to the following observed trading day. S&P SIC source: SEC 10-K filing headers pulled from the free [SEC EDGAR submissions and filing APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), supplemented with L4's dated SIC records for retired symbols absent from SEC's current ticker map. Current S&P roster source is [`r6_data/sp500_pit_roster.csv`](../r6_data/sp500_pit_roster.csv), whose manifest describes a reconstructed PIT roster; issuer identity and missing-price mapping need further audit.", "",
                 "| Universe | Quarter | Median available names with dated SIC | Minimum names with dated SIC | Median 2-digit SIC groups |", "|---|---|---:|---:|---:|"]
    sqq = pd.concat([sic_coverage("Dow", C1 / "dow_components_dev.parquet", C1 / "dow_sic_membership.csv"),
                     sic_coverage("S&P 500", C1 / "sp500_components_dev.parquet", C1 / "sp500_sic_membership.csv")], ignore_index=True)
    sections += [f"| {r.universe} | {r.quarter} | {r.median_names_with_dated_SIC} | {r.minimum_names_with_dated_SIC} | {r.median_dated_SIC2_groups:.0f} |" for r in sqq.itertuples()]
    sqq.to_csv(C1 / "sic_coverage_by_quarter.csv", index=False)
    sections += ["", 
                 "The following S&P price tickers have no dated SIC interval in the assembled SEC+L4 panel: " + ", ".join(sorted(set(pd.read_parquet(C1 / "sp500_components_dev.parquet", columns=["ticker"]).ticker) - set(smem.ticker))) + ". Some entered near the end of the window and have no 10-K SIC filing yet; retired/relabelled tickers can also be absent from the current SEC ticker map. S&P price rows also have gaps versus the roster, so this is not a complete 500-name time series on every session. For dates with fewer bars, missing tickers are not silently imputed. The Dow price source has a material early-window gap: daily bars for 29 of the 30 initial constituents begin on 2021-01-04, while WBA has earlier rows; consequently the initial portion before 2021-01-04 is incomplete and no signal should be calculated on those sparse cross-sections.", "",
                 "Dow point-in-time changes follow official S&P DJI announcements: [August 2020 additions](https://press.spglobal.com/2020-08-24-Salesforce-com-Amgen-and-Honeywell-International-Set-to-Join-Dow-Jones-Industrial-Average), [Amazon addition](https://press.spglobal.com/2024-02-20-Amazon-com-Set-to-Join-Dow-Jones-Industrial-Average-Uber-to-Join-Dow-Jones-Transportation-Average), and [November 2024 additions](https://press.spglobal.com/2024-11-01-NVIDIA-and-Sherwin-Williams-Set-to-Join-Dow-Jones-Industrial-Average-Vistra-to-Join-Dow-Jones-Utility-Average?asPDF=1).", "",
                 "## Output files", "",
                 "- `dow_components_dev.parquet` and `sp500_components_dev.parquet`: adjusted open/close, overnight return, intraday return, and their relative component spread, on development dates only.",
                 "- `dow_sic_membership.csv`, `dow_industry_links.csv`, `sp500_sic_membership.csv`, `sp500_industry_links.csv`: dated two-/three-digit SIC classifications and pairwise link intervals.",
                 "- `coverage_by_quarter.csv`, `input_manifest.json`: machine-readable coverage and provenance checks.", ""]
    (C1 / "INPUT_QA.md").write_text("\n".join(sections), encoding="utf-8")
    print(C1 / "INPUT_QA.md")


if __name__ == "__main__":
    main()
