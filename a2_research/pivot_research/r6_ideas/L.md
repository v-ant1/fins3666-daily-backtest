# R6 Idea Gate L — FINRA short interest and days to cover

**Status: FAIL-GATE as written. Rank: 1 of 1. Subjective chance of passing the full R6 stack: 1%.** This is an outcome-free feasibility and literature review. I used only the two permitted development-period FINRA snapshots, PIT roster/SIC metadata, public source documentation and synthetic `power_sim.py`; I did not load prices, returns, project outcomes, or holdout rows. The fail decision is driven by low design-matched power and lack of a verified free all-listed 2010–2020 FINRA series for the sealed holdout, not by any investment result.

## The proposed direction

Test whether a stock with more outstanding short positions relative to its normal trading volume underperforms over the next month. At each month-end formation, use the latest FINRA semi-monthly short-interest settlement that had already been publicly released by that date. For every security with a matched record and positive reported average daily volume, define **DTC = `currentShortPositionQuantity / averageDailyVolumeQuantity`**; use this direct ratio rather than FINRA's rounded/capped `daysToCoverQuantity`. The score is **negative DTC**: a lower DTC is a higher long score. A missing record stays missing; it is not set to zero or carried forward. The primary mechanism test is the date-wise Spearman IC of negative DTC against next-21-session relative returns, estimated on the PIT S&P 500. Expected sign: positive. The sole portfolio is an equal-weighted long-only top five of the Dow 30 by lowest DTC, rebalanced monthly, compared with EW30.

Use only settled records that were public before formation; settlement date alone is not the information-availability date. FINRA reports positions twice a month and disseminates them later. The data measure reported outstanding short positions at a snapshot, not the identity or motive of short sellers, and do not include every economically short exposure. This is a single-stock pressure-persistence test; it does not claim pressure has propagated along a peer network.

## Cheap pull and availability check

The two complete, raw API responses are in [`r6_data/finra_si_sample/`](../r6_data/finra_si_sample/). Each was downloaded by exact settlement-date filter and paged until FINRA's `record-total` was reached; the 5,000-row synchronous API page limit was not treated as full-file coverage. Ticker matching uses the project PIT S&P 500 roster and the pinned Dow roster active on each settlement date.

| Settlement date | Full FINRA rows | S&P 500 PIT names | S&P rows with position and positive ADV | Dow PIT names | Dow rows with position and positive ADV |
|---|---:|---:|---:|---:|---:|
| 2021-12-15 | 20,312 | 505 | 494 (97.82%) | 30 | 30 (100%) |
| 2025-12-15 | 21,107 | 503 | 499 (99.20%) | 30 | 30 (100%) |

These are two-date feasibility counts, not evidence of continuous panel coverage. Absence from a file is not interpreted as a zero short position. Raw file hashes and the per-date symbol coverage list are in `sample_manifest.json` and `sample_coverage.csv`.

For the 2010 availability request, I inspected only FINRA's public OTC archive index metadata, not the listed-security records or any pre-cutoff rows. The index lists **112 archive-file entries**, from 2014-11-14 through 2019-06-28, and **zero entries in 2010** (counts by year are saved in `archive_availability_counts.json`). This is FINRA's OTC archive, not an all-listed archive. FINRA's consolidated API release note describes a rolling five-year data history, with short-interest data from all exchanges beginning in June 2022; it does not provide a free FINRA consolidated 2010 series. Therefore the 2010 holdout's all-Dow coverage is **not established**. I did not open or count rows from any 2010 file.

The modern sample has useful coverage and the FINRA consolidated dataset is free to query, but the historical gate is not solved. Nasdaq says its issue-level public view is rolling 12 months and points to historical data on Nasdaq.com; this does not establish a free bulk PIT archive for the complete Dow. NYSE lists historical short-interest data back to 1988, but as a NYSE Group market-data product, not a verified free dataset. Compustat/WRDS or an exchange/vendor entitlement may provide a substitute, but availability and permissions for this project have not been confirmed. The exact data needed are (1) twice-monthly shares short, (2) matched average daily share volume, (3) publication date, (4) historical ticker/issuer lineage, (5) PIT membership, and (6) returns for later tests. FINRA fields and PIT rosters are free for the two modern samples; full pre-2020 listed history is currently unverified and may require licensed data. No FactSet or other licensed source was accessed.

## Gates (a)–(e)

### (a) Verified literature — SUPPORTS the sign, with citation correction

- Hong, Li, Ni, Scheinkman and **Yan** (not Wang), [“Days to Cover and Stock Returns,” NBER Working Paper 21166](https://www.nber.org/papers/w21166), DOI [10.3386/w21166](https://doi.org/10.3386/w21166). They define DTC as short interest relative to average trading volume, interpret it as capturing short-position exit costs, and find that higher DTC predicts lower returns. Their 1988–2012 sample reports a 1.19% monthly equal-weighted low-minus-high DTC spread and 0.67% value-weighted spread; their post-2000 subperiod ends in 2012. This is a working paper, not a 2016 journal article.
- Boehmer, Huszár and Jordan (2010), [“The Good News in Short Interest,” *Journal of Financial Economics* 96(1), 80–97](https://doi.org/10.1016/j.jfineco.2009.12.002). Their 1988–2005 NYSE/AMEX/Nasdaq sample finds higher short interest precedes negative abnormal returns, but calls that effect transient and of debatable economic significance; heavily traded stocks with low short interest have positive abnormal returns. It supports the direction but not current persistence.
- Rapach, Ringgenberg and Zhou (2016), [“Short Interest and Aggregate Stock Returns,” *Journal of Financial Economics* 121(1), 46–65](https://doi.org/10.1016/j.jfineco.2016.03.004). They find aggregate U.S. short interest forecasts aggregate market returns through 2014, including out-of-sample evidence through 2014. This supports informed short selling at the market level, but it is not a cross-sectional single-stock DTC result.

FINRA sources: [Consolidated Short Interest dataset catalog](https://developer.finra.org/catalog), [January 2023 API release note](https://developer.finra.org/release-notes/january-2023-release-notes), [OTC archive index page](https://otce.finra.org/otce/EquityShortInterest/archives), and [short-interest reporting rule](https://www.finra.org/rules-guidance/rulebooks/finra-rules/4560).

### (b) Mega-cap and post-2010 case — WEAK

Hong et al. provide the most relevant large-stock support: DTC continued to add value relative to the short-interest ratio in the 2000–2012 subsample and remained informative after removing the bottom market-cap decile or quintile. That is some evidence in larger stocks and includes only 2010–2012 after 2010. It is not a result for Dow mega-caps, the 2020s, or this FINRA panel. Boehmer et al. end in 2005. Rapach et al. extend market-level short-interest prediction through 2014, but cannot establish that individual Dow stocks with low DTC outperform. The sample pull shows modern S&P/Dow record coverage, not edge survival. The post-2012 and especially post-2020 case remains unproven; this is a material reason for the low probability.

### (c) S&P 500 monthly power — FAIL at a plausible effect size

The input-only design has 72 month-end formations from 2020-11 through 2026-10 and 21-session forward horizons. I ran `r4_harness/power_sim.py` with 54 effective SIC2 clusters, horizon 21 (NW lag 20), IC-series autocorrelation 0.20, 20,000 simulations, and seed `20261152`. To represent SIC2 dependence, I use the dated E1 input coverage of about 499 S&P names / 54 SIC2 groups = 9.24 names per group, assume within-group correlation 0.15, and set IC SD to `sqrt([1 + (9.24 − 1) × 0.15] / (54 − 1)) = 0.20538`. This is a cluster-design approximation, not an estimated dependence parameter or a two-way cluster bootstrap.

| Planted mean IC scenario | Power for one-sided NW t ≥ 2 | 80% MDE | Effective monthly N |
|---:|---:|---:|---:|
| 0.0183 (R6 comparison benchmark; not a claimed literature estimate) | 18.2% (Monte Carlo SE 0.27 percentage points) | 0.0834 | 49.0 |

The Hong et al. long-short monthly return spread is not convertible to Spearman IC without the corresponding return dispersion and portfolio mapping, so I do not claim it implies an IC of 0.0183 or 0.0834. The cost-only hurdle below is much smaller than the power MDE; low costs cannot repair this inference problem. Power output is saved in `power_sim.json`.

### (d) Data and holdout feasibility — PARTIAL; holdout FAIL

The exact free FINRA fields for the modern test are `currentShortPositionQuantity`, `averageDailyVolumeQuantity`, `settlementDate`, and publication availability, plus ticker lineage and dated constituent rosters. Compute DTC from the first two fields only when average daily volume is positive. FINRA metadata notes its average daily volume excludes non-media trades; the ratio is therefore a FINRA-based proxy and may not match a full-market volume denominator. A point-in-time panel must use the most recent released settlement at each formation, keep absent rows missing, and disclose revisions and symbol changes.

The 2021/2025 coverage sample passes a cheap modern coverage check. A 2010 FINRA archive was not found in the public archive index and all-listed pre-2020 history is not available from the rolling consolidated endpoint. The sealed holdout cannot be run from these verified free inputs. Do not substitute daily Reg SHO short-sale volume: that is a daily flow of reported trades, not a twice-monthly stock of open short positions. FINRA explicitly describes short interest and daily short-sale volume as different quantities. A licensed historical short-interest panel may solve the data gap only after access and ticker coverage are verified; until then this is **not holdout-feasible**.

### (e) Novelty

The published DTC papers study broad cross-sections and mostly long-short or decile portfolios. This proposal would ask whether the sign survives a modern, point-in-time S&P 500 mechanism test and a Dow-only top-five low-DTC long portfolio after realistic turnover limits and costs, using FINRA's accessible consolidated schema. It is a new target universe and implementation, not a claim that DTC itself is novel. The proposal makes no network-diffusion claim and is explicitly separate from D1's daily Reg SHO flow measure.

## Portfolio and cost specification for any future preregistration

- Monthly formation; latest **publicly disseminated** short-interest settlement as of formation; score `−DTC`.
- Equal-weight top five Dow names with the lowest raw DTC; compare gross and net return and Sharpe with EW30; 0.05% cost per side, applied once to total traded notional.
- Require active share ≥50% and cap monthly total turnover at **20% of NAV** (buys plus sells). The cap is tighter than the R6 50% maximum and is the planned turnover used for the cost hurdle. If actual trading cannot maintain both the top-five target and this cap without violating active share, disclose it and fail the portfolio design; no silent turnover suppression.
- With planned turnover 0.20, assumed one-month cross-sectional return dispersion 0.06, cost 0.0005 per side, and top fraction 5/30, `r4_harness.phase3.break_even_rank_ic(0.20, 0.06, 0.0005, 5/30) = 0.0011547`. This is a planning floor, not measured alpha; costs are 1 bp NAV per monthly rebalance at that turnover. A later portfolio test must report actual turnover and costs and meet the fixed R6 net-return, Sharpe, Holm, bootstrap, DSR and holdout rules.

## Decision

Do not freeze or spend a variant on this direction yet. It clears the literature/sign and modern sample-coverage parts, but it fails the plausible-effect power check and has no verified free all-listed 2010 holdout panel. Revisit only if a licensed or otherwise free historical panel is verified for the PIT Dow and the coordinator accepts a power design tied to a defensible effect size; this is not a reason to weaken fixed R6 gates.
