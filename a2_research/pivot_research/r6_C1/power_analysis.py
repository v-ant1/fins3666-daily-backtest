"""Synthetic power analysis for the final SIC3 peer-intraday C1 design.

Inputs are the built signal and point-in-time SIC3 membership only. This script
never reads forward returns, outcomes, or ICs. SIC3 clustering is represented by
a transparent design-effect inflation of a literature-calibrated IC SD.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "r4_harness"))
from power_sim import simulate_power

IC_SD_LITERATURE = 0.15  # Ding & Sun (2023), synthetic factor-model calibration.
WITHIN_SIC3_ICC = 0.15   # Predeclared sensitivity assumption; not estimated from outcomes.
EFFECTS = (0.0183, 0.026)
SIMULATIONS = 5000
SEED = 20261111


def main():
    panel = pd.read_parquet(OUT / "peer_intraday_signal_dev.parquet")
    panel["date"] = pd.to_datetime(panel.date).dt.normalize()
    weekly_dates = pd.DatetimeIndex(sorted(panel.date.unique()))[4::5]
    sp = panel.loc[(panel.universe == "S&P 500") & panel.date.isin(weekly_dates)].copy()
    sp["signal_available"] = sp.peer_intraday_signal.notna()
    counts = sp.groupby("date").signal_available.sum()
    # This is the registered S&P mechanism coverage rule: >=250 eligible peers.
    eligible_dates = counts.index[counts >= 250]
    sp = sp.loc[sp.date.isin(eligible_dates) & sp.signal_available].copy()
    if len(eligible_dates) < 3:
        raise ValueError("fewer than three eligible S&P weekly dates")

    # Cluster count and average group size are computed from the actual scored
    # names on each weekly date, using their active dated SIC3 labels.
    cluster_rows = []
    for date, g in sp.groupby("date"):
        group_n = g.groupby("sic3").ticker.nunique()
        group_n = group_n[group_n > 0]
        n_names = int(g.ticker.nunique())
        n_clusters = int(len(group_n))
        if n_clusters:
            avg_size = n_names / n_clusters
            deff = 1.0 + max(avg_size - 1.0, 0.0) * WITHIN_SIC3_ICC
            cluster_rows.append((date, n_names, n_clusters, avg_size, deff))
    c = pd.DataFrame(cluster_rows, columns=["date", "names", "clusters", "avg_cluster_size", "design_effect"])
    n_clusters = max(2, int(round(c.clusters.median())))
    avg_cluster = float(c.avg_cluster_size.median())
    design_effect = float(c.design_effect.median())
    ic_sd = IC_SD_LITERATURE * math.sqrt(design_effect)

    # Use input-only signal persistence: median lag-one autocorrelation of
    # within-date percentile ranks for names with >=20 weekly observations.
    wide = sp.pivot(index="date", columns="ticker", values="peer_intraday_signal")
    ranks = wide.rank(axis=1, pct=True)
    acfs = [ranks[t].autocorr(lag=1) for t in ranks.columns if ranks[t].notna().sum() >= 20]
    rho = float(np.nanmedian(acfs)) if acfs else 0.0
    rho = float(np.clip(rho, -0.95, 0.95))

    sims = []
    for i, effect in enumerate(EFFECTS):
        result = simulate_power(
            universe_size=n_clusters,
            n_dates=len(eligible_dates),
            horizon=5,
            signal_autocorrelation=rho,
            cross_sectional_ic_sd=ic_sd,
            planted_mean_ic=effect,
            simulations=SIMULATIONS,
            seed=SEED + i,
        )
        sims.append(result)

    summary = {
        "design": "weekly S&P 500 C1; trailing five-session SIC3 peer intraday-return signal",
        "development_only": True,
        "outcomes_or_forward_returns_loaded": False,
        "observed_ics_loaded_or_computed": False,
        "eligible_weekly_dates_n": int(len(eligible_dates)),
        "eligible_name_count_median": int(counts.loc[eligible_dates].median()),
        "eligible_name_count_min": int(counts.loc[eligible_dates].min()),
        "sic3_cluster_count_median": int(c.clusters.median()),
        "sic3_mean_cluster_size_median": avg_cluster,
        "within_sic3_icc_assumption": WITHIN_SIC3_ICC,
        "cluster_design_effect_median": design_effect,
        "base_ic_sd_literature": IC_SD_LITERATURE,
        "cluster_adjusted_ic_sd": ic_sd,
        "input_signal_rank_autocorrelation_weekly": rho,
        "horizon_sessions": 5,
        "newey_west_lag": 4,
        "simulations_per_effect": SIMULATIONS,
        "seed_base": SEED,
        "effects": [r.__dict__ for r in sims],
    }
    (OUT / "power_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = [
        "# C1 power analysis: final SIC3 peer intraday-return design", "",
        "This is a synthetic, input-only power calculation. It used the final development signal panel and active SIC3 groups, but loaded no forward returns, outcome variables, or observed ICs. The mechanism is sampled weekly (every fifth trading session), with a five-session horizon and Newey–West lag 4.", "",
        "## Assumptions", "",
        f"- Eligible S&P mechanism dates: {len(eligible_dates)} weekly dates with at least 250 names having a valid leave-one-out SIC3 peer score; median eligible names {int(counts.loc[eligible_dates].median())}, minimum {int(counts.loc[eligible_dates].min())}.",
        f"- Median SIC3 clusters among eligible scored names: {int(c.clusters.median())}; median mean cluster size: {avg_cluster:.3f} names.",
        f"- Base IC-series SD: {IC_SD_LITERATURE:.3f}, literature calibration from Ding and Sun (2023), *The Statistics of Time Varying Cross-Sectional Information Coefficients* ([DOI](https://doi.org/10.1057/s41260-022-00295-9)); not estimated from project outcomes.",
        f"- SIC3 design effect: `1 + (mean cluster size - 1) × ICC`, with within-SIC3 ICC = {WITHIN_SIC3_ICC:.2f} as a fixed sensitivity assumption. Median design effect = {design_effect:.4f}; cluster-adjusted IC SD = {ic_sd:.4f}.",
        f"- Weekly signal autocorrelation input: {rho:.4f}, the median per-name lag-one autocorrelation of within-date percentile ranks of the peer signal; this is input persistence, not IC autocorrelation.",
        f"- `r4_harness/power_sim.py`, horizon=5, Bartlett NW lag=4, {SIMULATIONS:,} draws per planted effect; seed base {SEED}, incremented by effect. This date-level AR(1) simulator applies SIC3 clustering through the SD design effect; it is a sensitivity approximation, not a full date-by-industry block bootstrap.", "",
        "## Results", "",
        "| Planted mean IC (hypothetical) | Power for NW t ≥ 2 | Monte Carlo SE | Effective dates | Effective N median | MDE at 80% power |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for r in sims:
        lines.append(f"| {r.planted_effect:.4f} | {r.p_nw_t_ge_2:.3f} | {r.monte_carlo_se:.3f} | {r.observations_mean:.1f} | {r.effective_n_median:.1f} | {r.minimum_detectable_effect_80:.4f} |")
    lines += ["", "Effects 0.0183 and 0.026 are pre-outcome planning values carried from the red-team calibration; they are hypothetical IC values, not observations or estimates. Power below 80% at 0.0183 means the registered S&P mechanism would not meet its power gate under these assumptions. The manifest retains all simulation inputs and results.", ""]
    (OUT / "POWER.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
