# AK — passive-weighted ETF demand pressure

**Status: SCREEN ONLY — STOP — FAIL.** The passive-demand mechanism is credible for large firms, but the staged free data do not supply the point-in-time daily fund flows and constituent weights needed to form this stock-level signal, and the documented effect does not establish the six-year Dow portfolio hurdle. This is input-feasibility and literature synthesis only: no signal values, forward returns, ICs, portfolio returns, or other project outcomes were calculated; no Holm manifest or result file was opened, and no holdout data were accessed. Subjective chance that this exact design would clear every gate with the currently staged free inputs: **below 1%**.

## Identity and immutable-path preflight

- **Mechanism:** unexpected subscriptions to passive index funds create price-insensitive buying in their underlying stocks. A stock’s demand shock is its lagged index weight multiplied by each fund’s net primary-market flow; aggregate this across a frozen universe of passive funds to rank Dow stocks by recent pressure.
- **Exact new output path:** `r6_ideas/AK_passive_weight.md`; it was absent at preflight. This is the requested new artifact.
- **Development boundary:** 2020-11-27 through 2026-10-30 only; earliest permissible date is 2020-11-27. The staged feasibility queries were date-filtered at read time. No holdout-specific path was required or read.
- **Scope:** this proposal is not authorized to proceed to signal, mechanism-outcome, or portfolio testing.

## 1. Overlap with prior work

Nearest items are:

- **R6 P4, passive-ownership change:** P4 tried to estimate a change in passive ownership from quarterly 13F positions. It failed because the staged positions are manager-level, not mandate-level, and criterion-4 evidence was missing. AK instead proposes dated fund net flows multiplied by lagged benchmark weights; it does not use reported manager ownership changes. But it needs the same key input—identifiable passive fund exposure to each issuer—and its assumed flow history is not staged.
- **R5 Cycle 3 ETF flow:** the R5 review found that daily shares/flow histories were verified only for SPY and DIA, while the available N-PORT holdings were quarterly; the proposal failed its input gate before outcomes. AK is a stock-level, holdings-weighted ETF-flow map rather than an aggregate ETF time series, but it relies on the same unavailable broad fund-flow and historical holdings panel. This is substantive mechanism overlap, not a clean new data source.
- **R6 AC / Round H DIA:** those directions used DIA-level trading or flow proxies and could not distinguish stock-specific demand absent a valid holdings map. AK would differ by applying passive-fund flows to each constituent’s point-in-time index weight. The required broader data are not verified here.

**Verdict: FAIL.** The stock-specific weighting is a distinct construction from P4’s ownership stock, but the central ETF-flow mechanism repeats the R5 flow direction that was already stopped for lack of inputs. The added exposure map is not currently available at the required granularity.

## 2. Exact pressure measure and dated data source

The only coherent version I would consider is a **monthly positive-pressure** signal. For passive index fund *f* and stock *i*, define dollar pressure for month *t* as:

`flow_f,t × index_weight_i,f,t−1`,

where `flow_f,t` is net primary-market subscription/redemption dollars—not the raw change in AUM—and `index_weight_i,f,t−1` is the last constituent weight publicly available before the month begins. Sum across a pre-specified set of plain-vanilla US passive index funds and divide each stock’s 20-session dollar pressure by its prior 20-session average daily dollar volume. A larger positive value predicts a higher next-month return. Raw `ΔAUM` is invalid because it includes mark-to-market appreciation in underlying holdings; weights must also be lagged because contemporaneous price weights mechanically respond to past returns.

The fund universe, benchmark label, net flows, and constituent weights must all be public and point-in-time as of formation. Candidate public sources are fund share counts/NAV and filings, plus index provider constituent weights; any fund universe and passive classification must be frozen before outcomes. The SEC explains that Form N-PORT contains portfolio holdings, but its public dataset is quarterly and only includes information disseminated by the SEC; it does not provide the daily creation/redemption flow series required here ([SEC Form N-PORT datasets](https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets)). Free ETF OHLCV is not a substitute for primary creations and redemptions.

**Input-only development feasibility pull:** with PyArrow date predicates on `r6_data/etf/etf_ohlcv_dev.parquet`, the in-range panel contains **28,272 rows, 1,488 dates, and 19 tickers** (2020-11-27–2026-10-30). The stored columns are daily OHLCV and adjusted close; they do not include NAV, shares outstanding, daily net creations/redemptions, AUM, or historical basket weights. Date-filtered input-only checks of staged N-PORT coverage found **366 filing-coverage rows over 46 report dates / 60 availability dates**, and **2,531 mapped Dow holdings over 46 report dates / 60 availability dates**. The panel is sparse quarterly disclosure, not a daily passive-fund flow/benchmark-weight panel; 13F-like manager holdings cannot be called passive holdings without mandate-level classification. These counts are coverage checks only, not signal construction or outcomes.

**Formation:** month-end portfolio formation may use only flows and weights fully available by that close; predict the following month’s returns. A usable source would need to report the flow and PIT constituent-weight timestamp. The currently staged inputs do not allow this measure to be formed without substituting secondary-market volume or stale quarterly holdings, both of which change the proposed signal.

**Verdict: FAIL.** Exact measure is well-defined, but the available free inputs cannot supply it point in time.

## 3. Point-in-time coverage and independent breadth

The usable ETF OHLCV coverage is the **1,488 dates and 19 tickers** above. That confirms a long daily price/volume history for a selected ETF sample, not flow coverage. SEC holdings coverage has 46 report dates and 60 filing-availability dates after filtering both dates to the development window. The mapped panel includes **36 Dow symbols** and 2,531 holding records, but the selected records are quarterly and do not identify passive mandates; those counts do not demonstrate 30-stock daily signal coverage. Independent flow shocks and issuer SIC2 breadth cannot be counted because the necessary stock-level net-flow series does not exist in the staged files.

Coverage would also need survivorship-safe point-in-time fund constituents, historical fund labels (passive vs active), delisted/merged fund histories, symbol/CIK lineage, and filing-availability timestamps. Current ETF labels or current benchmark compositions cannot be applied retrospectively. N-PORT disclosures cover only publicly disseminated filings, so reporting lags and missing funds would create availability selection. No SIC2 or cross-sectional breadth count is claimed for this unbuildable signal.

**Verdict: FAIL.** Free staged inputs establish ETF price coverage and a sparse holdings subset, not point-in-time coverage for the proposed passive-demand shocks.

## 4. Effective breadth and power at a sourced plausible effect

**What the literature documents.** Harris and Gurel’s S&P 500 addition study reports that prices rose by more than 3% immediately after additions were announced and nearly fully reversed within two weeks. That is strong historical price-pressure evidence, but it is a discrete index-inclusion event from 1986, not monthly passive fund flow × stock weight among today’s Dow constituents ([Harris & Gurel (1986), *Journal of Finance*, DOI 10.1111/j.1540-6261.1986.tb04550.x](https://doi.org/10.1111/j.1540-6261.1986.tb04550.x)).

Jiang, Vayanos, and Zheng find that, in **99 quarterly observations** for large S&P 500 firms over their historical sample, one standard deviation in aggregate S&P 500 passive fund flows is associated with roughly **0.528%–0.557% higher quarterly excess returns** for their top-50 portfolio, depending on weighting and controls; their Newey–West t-statistics are around 3.65–4.19. Their sample averages passive flow at 0.05% of index capitalization per quarter, with 0.09% standard deviation. This is relevant large-firm evidence, but the regressor is one common aggregate flow series and the outcome is a large-firm portfolio—not a within-Dow issuer cross-sectional rank signal, an IC, or a post-2020 strategy effect ([Jiang, Vayanos & Zheng, *Passive Investing and the Rise of Mega-Firms*, NBER WP 28253, revised 2024; published in RFS 2025, DOI 10.1093/rfs/hhaf085](https://doi.org/10.1093/rfs/hhaf085)).

Haddad, Huebner, and Loualiche estimate that the growth of passive investing made individual-stock demand about **11% more inelastic** over two decades. That supports price impact as a mechanism, but it is a demand-elasticity estimate, not a return forecast or cross-sectional strategy Sharpe ([Haddad, Huebner & Loualiche (2025), *American Economic Review*, DOI 10.1257/aer.20230505](https://doi.org/10.1257/aer.20230505)). Coles, Heath, and Ringgenberg report that passive index investing does not undermine price efficiency in their Russell-index design, a useful counterweight to extrapolating mechanical demand into persistent alpha ([Coles, Heath & Ringgenberg (2022), *Journal of Financial Economics*, DOI 10.1016/j.jfineco.2022.05.007](https://doi.org/10.1016/j.jfineco.2022.05.007)).

**Power check (synthetic only).** I used `r4_harness/power_sim.py` with 54 SIC2 clusters, 72 monthly observations, `horizon=3` (Newey–West lag 2), signal autocorrelation 0.80, assumed IC standard deviation 0.20538, 10,000 simulations, seed 20261111, and a hypothetical planted mean IC of 0.020. Power to reach NW *t* ≥ 2 is **25.4%** (Monte Carlo SE 0.0044); the 80%-power minimum detectable IC is **0.1086**; effective date count is about 28.9. The 54 clusters and 0.20538 standard deviation are design assumptions inherited from the S&P SIC2 power setup, not observations on an AK signal. The assumed IC 0.020 is only a sensitivity input: no published effect above is legitimately convertible into this stock-level IC. The 72 dates likely overstate independent information if usable holdings refresh only quarterly. The 54 SIC2s are a conservative industry-cluster proxy, not 54 independent passive-flow shocks; the one aggregate market flow is a common shock.

**Verdict: FAIL.** There is strong broad large-cap flow evidence but no effect-size estimate matching this cross-sectional monthly signal; sensitivity power is low and an equivalent number of independent issuer-specific flow shocks is not demonstrated.

## 5. Criterion-4 portfolio feasibility first

The intended portfolio would rank Dow names monthly by the one-month aggregate passive-flow × lagged-weight pressure. It would hold the positive-pressure top half, compare with EW30, require positive net excess return, Sharpe above EW30, and one-sided block-bootstrap evidence after the fixed Holm family. Use 0.05% per side and cap turnover at 50% of NAV per monthly rebalance. A cap would carry existing positions when the uncapped target change exceeded the limit; that would lower costs but also dilute exposure to the supposed shock. This is only the candidate design for feasibility analysis, not an authorized portfolio test.

The `report_drafts/CRITERION4_BOUND_BY_SHAPE.md` planning audit estimates that at monthly rank-weighted top-half, even under its **high persistence ρ=0.8** assumption, the 80%-power IC threshold is about **0.247** and expected turnover about **58%**, already above the proposed 50% cap. At ρ=0.5 the threshold is 0.160 with 91% turnover; at ρ=0.2 it is 0.120 with 116% turnover. These are synthetic conditional bounds under the audit’s assumed dispersion, six-year length, cost and Holm design, not observed project statistics. Capping turnover at 50% would not make the signal more predictive; it should reduce its effective exposure and cannot rescue a design whose literature does not supply an IC estimate in the required range.

The 0.528%–0.557% quarterly estimate from Jiang et al. cannot be compared directly with these IC hurdles: it is a portfolio response to a single common aggregate-flow regressor, and the regression sample is 99 historical quarters, not the 72 monthly Dow observations and SIC2-rank design. Even a rough annualization of that coefficient would not establish the *cross-sectional* alpha of the AK portfolio, and would ignore the difference between aggregate flow dispersion then and current stock-specific exposures. There is no defensible mapping to a six-year Dow excess Sharpe or bootstrap *p* without importing unsupported assumptions. At the available evidence-only estimate, expected strategy alpha is unsubstantiated; neither the criterion-4 Sharpe nor its Holm-adjusted p-value can be projected as passing.

**Verdict: FAIL — criterion-4 feasibility is not established.** The required effect is not sourced for this cross-sectional design; the planning bound is demanding even before the cap; the estimated portfolio performance is unknown and must not be invented.

## 6. Holdout availability and protocol

No holdout path or holdout-specific input is needed for this screen, and no sealed-holdout values were accessed. If a future idea passes development, the only holdout procedure is the coordinator-controlled one-shot run under goal criterion 5; workers must not read, download, plot, or calculate on those values. Before any such consideration, the coordinator should verify availability from approved manifests/roster and row counts only, without loading returns or signals. This proposal fails development feasibility and therefore does not approach holdout consideration.

**Verdict: PASS** for screen compliance; no holdout access occurred and none is proposed here.

## Final screen decision

- **Overall: STOP — FAIL.**
- The passive-flow price-pressure hypothesis has supporting large-firm evidence, but the proposed free-data measure is not presently buildable point in time; it repeats the failed R5 ETF-flow input problem; and its specific stock-level expected effect is unknown against a demanding criterion-4 bound.
- Evidence that could change this decision: a verified free daily historical file containing primary-market net flows and point-in-time constituent weights for a pre-specified passive fund universe, with complete dated coverage across Dow names; and independent post-2020 research matching stock-specific flow-weighted pressure to a monthly long-only rank IC large enough to meet the audited hurdle. Do not start an outcome test merely to fill these gaps.
- Reviewer/date: dispatched screen review, 2026-11-11.

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
