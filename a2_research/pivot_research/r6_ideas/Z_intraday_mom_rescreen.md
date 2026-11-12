# R6 idea screen — Z intraday momentum rescreen

**Status: SCREEN ONLY. Overall: STOP — FAIL, criterion-4 infeasible on documented evidence.** This is a literature and input-feasibility screen; no signal values, returns, ICs, or portfolio outcomes were calculated. Project data inspected for feasibility were limited to the staged 2024 SIP samples and source/input metadata; no data dated before 2020-11-27 or any holdout data were opened.

## Identity and immutable-path preflight

- **Direction:** cross-sectional early-session return pressure predicts the same day's final-half-hour return.
- **Exact new output path:** `r6_ideas/Z_intraday_mom_rescreen.md`.
- **Existence/name check:** this exact path did not exist before authoring. The label distinguishes this signal from `T_daily.md` T1, which is same-stock/same-slot continuation from one day to the next, and from the auction and signed-flow screens.
- **Permitted project dates:** 2020-11-27 through 2026-10-30 only. Literature samples can be older; none of those research data were loaded.
- **Holdout-specific path/input:** none. Later holdout work remains coordinator-controlled under goal criterion 5.

## 1. Overlap with prior work

The prior screen T1 asked whether a stock's return in a fixed half-hour interval predicts that same stock's return in the same interval on the following day. That interday periodicity is the Heston–Korajczyk–Sadka pattern. This rescreen instead asks whether a stock's opening half-hour move predicts its **own last-half-hour return on the same date**, and whether that relationship survives cross-sectional ranking and SIC2 controls. It is therefore the permitted, still-untested Gao-style direction recorded in decision 157, not a horizon change or rescue of a failed mechanism.

The signal also differs from J1's weekly SIC2-relative reversal: its pre-registered sign is positive, its formation is within a trading day, its outcome window is the closing half-hour, and it has no weekly-reversal component. Any eventual test must not add same-slot lagged return, closing auction size, or a post-hoc reversal as extra variants.

**Overlap verdict: PASS, narrowly.** The cross-sectional same-day version was not tested in the cited prior screens; adjacent literature and T1 are not the same timing relation.

## 2. Exact pressure measure and dated data source

For stock *i* on regular-session date *t*, define the signal at 10:00 a.m. New York time as

`X(i,t) = log(close_i,t,09:59 / close_i,t−1,15:59)`,

using the close of the final full one-minute SIP bar ending at each boundary. The first half-hour score includes the overnight move, matching Gao et al.'s previous-close-to-first-half-hour convention. The primary cross-sectional signal is the date-wise rank of `X`, centered and scaled within point-in-time SIC2, with a positive expected sign. The mechanism outcome, if later authorized, is the same stock's SIP bar log return from the 15:30 bar open to the 15:59 bar close (the final 30 minutes). Information stops at 10:00; the portfolio decision is made no later than 15:30 and cannot use final-half-hour prices. Bar-close returns are a proxy for midpoint returns and may contain bid-ask bounce; the fixed cost assumption below does not remove that measurement limitation.

**Tradable timing:** At the 15:30 bar open, after the signal has been formed and carried forward unchanged, select the top five available Dow constituents by that date's frozen score; hold from that bar open through the 15:59 close, then close the active sleeve. Compare with an equal-weight Dow 30 book over the identical final-half-hour interval. This is explicitly an intraday-sleeve comparison, not a claim that the intraday signal predicts close-to-close or next-day returns. If required bars or PIT roster membership are absent at either boundary, exclude that stock/date under a frozen coverage rule.

**Sources and limits.** The contemplated input is the development-only SIP one-minute-bar pull in `r6_data/alpaca/`, with point-in-time roster and SIC2 mapping already staged in the project. The audit's 2024 examples confirm access to a regular-session SIP bar schema for sampled Dow names. Alpaca documents separate IEX and SIP feeds and indicates historical equity data beginning in 2016; SIP historical access in a test does not establish free real-time SIP entitlement, and historical bulk-use/retention terms should be confirmed before any later pull. See [Alpaca market-data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq), [minute bars reference](https://docs.alpaca.markets/us/reference/stockbars), and the staged [Alpaca audit](../r6_data/alpaca/ALPACA_AUDIT.md). Decision 154 estimates roughly 30,000 pages for the full S&P 500 development minute-bar pull; the complete point-in-time SIP panel is in progress and is assumed here to supply each full regular session as instructed.

**No outcomes:** I did not calculate any stock's opening return, closing return, signal, rank, predictive statistic, or portfolio result. The defined returns above specify a future test only.

**Gate (d) verdict: PASS conditional on the in-progress full-session panel.** The existing 2024 sample proves endpoint and schema feasibility only; if the completed development input lacks the boundary bars or PIT coverage, stop rather than substitute another bar rule after seeing outcomes.

## 3. Point-in-time coverage and independent breadth

The prior development inventory has 1,488 trading dates from 2020-11-27 to 2026-10-30, 503 price-covered point-in-time S&P names at the last development date, and 53 SIC2 groups. The 2024 Alpaca feasibility sample confirms regular-session one-minute coverage for the sampled symbols, but it is a bounded date/symbol probe rather than a complete history. I rely on the requested assumption that the ongoing SIP pull supplies the full regular session for the development universe; no sample was used to infer price behavior.

Under that assumption, upper-bound mechanism coverage is at most 1,488 daily cross-sections × 503 names (about 748,000 stock-days) before missing quotes, IPOs, halts, ticker mapping, or PIT membership filters. The time-series test has only 1,488 date clusters, not 748,000 independent dates. SIC2 demeaning addresses sector-wide common returns but does not make SIC2 groups independent across days; market-wide shocks can still correlate groups. Dow portfolio coverage is at most 30 names and selection must use the roster known at 15:30 on each date. The 2024 probe alone cannot establish full-window completeness, so INPUT_QA for a later runner must report name-date and boundary-quote coverage before any return merge.

**Gate (d), coverage sub-gate: PASS only as a conditional data plan; not as observed full-panel coverage.** Point-in-time rosters, name changes, missing SIP bars, and halt dates must be diagnosed without looking at outcome values before freezing.

## 4. Effective breadth and power at a sourced plausible effect

### (a) Verified literature

Gao, Han, Li and Zhou, [“Market Intraday Momentum,” *Journal of Financial Economics* 129 (2018), 394–414](https://doi.org/10.1016/j.jfineco.2018.05.009), use high-frequency SPY data for 1993–2013. The previous-close-to-first-half-hour market return predicts SPY's last-half-hour market return; the paper reports forecast R-squared of 1.6% in-sample and 1.4% out-of-sample. This is a **time-series market-ETF regression**, not a cross-sectional stock rank IC, and R-squared cannot be translated to the Dow rank IC without extra assumptions.

Baltussen, Da, Lammers and Martens, [“Hedging Demand and Market Intraday Momentum,” *Journal of Financial Economics* 142 (2021), 377–403](https://doi.org/10.1016/j.jfineco.2021.04.029), examine more than 60 futures across equities, bonds, commodities and currencies over 1974–2020. They find rest-of-day returns predict last-half-hour returns and link the effect to short-gamma hedging; the predictability reverses over subsequent days. Again, the result is market/time-series predictability, not a Dow cross-sectional stock-level premium.

The cross-sectional literature is adjacent but not equivalent. Heston, Korajczyk and Sadka, [“Intraday Patterns in the Cross-Section of Stock Returns,” *Journal of Finance* 65 (2010), 1369–1407](https://doi.org/10.1111/j.1540-6261.2010.01573.x), document continuation at the **same half-hour slot across different days**, not opening-to-close continuation on one day. Chen, Haboub, Khan and Mahmud, [“Investor Clientele and Intraday Patterns in the Cross Section of Stock Returns,” *Review of Quantitative Finance and Accounting* (2025)](https://doi.org/10.1007/s11156-024-01319-8), study the Heston-style same-slot cross-section in UK, China and Brazil; the Chinese pattern is weaker for retail-dominated A-shares, and their sample is 2016–2019. Schlie and Zhou, [“Interday Cross-Sectional Momentum: Global Evidence and Determinants,” *Finance* 47(1) (2026), 97–141](https://doi.org/10.3917/fina.pr.048), also study cross-sectional same-slot continuation; their nine-developed-market sample says the U.S. pattern has weakened and that measured long-short returns fail to cover the full bid-ask spread. Neither result supplies the desired same-day first-to-last-half-hour effect in U.S. mega-cap stocks.

Thus, the documented plausible effect **for the exact cross-sectional Dow signal is unavailable**. The main paper's 1.4% OOS R-squared is not a plausible rank-IC estimate, and the cross-sectional follow-ups concern another lag structure. I do not convert either to an IC or expected Dow Sharpe.

### (b) Why the effect might persist in mega-caps after 2020 — and why the evidence fails

There is a coherent mechanism case: large U.S. equities are heavily represented in index and leveraged products, and market makers with short gamma hedge in the direction of the underlying move; these trades can create late-session pressure after an early move. Mega-cap liquidity may also allow more reliable execution than small stocks. But this explanation naturally predicts a common market or index effect, not a cross-sectional difference among mega-caps. The direct Gao sample ends in 2013, the Baltussen futures sample ends in 2020, and the newer U.S. cross-sectional evidence says same-slot continuation has weakened. Option-expiration/hedging demand need not map from index futures to individual Dow names; high liquidity and competition can compress stock-level residual effects. **No cited paper establishes that the specific positive stock-level first-half-hour-to-last-half-hour premium survives in post-2020 U.S. mega-caps. Gate (b): FAIL / transfer evidence insufficient.**

### Synthetic power check

For a sensitivity check only, I ran `r4_harness/power_sim.py` with 1,488 date observations; 500 assets; 53 SIC2 groups; 5-session Newey–West lag (lag 4); AR(1) dependence 0.20; 5,000 synthetic draws; and seed `20261125`. The date-level IC standard deviation was set to 0.2089 from `sqrt([1 + (500/53 − 1) × 0.15] / (53 − 1))`, using an assumed within-SIC2 correlation of 0.15. The simulator found power **85.78%** (Monte Carlo SE **0.00494**) to reject NW *t* < 2 at a **planted mean IC of 0.020**; effective N was **1,082** and the approximate 80%-power MDE was **0.0180**. These are model-conditional synthetic calculations; 0.020 is an illustrative assumption, not a paper estimate or project finding. The lag-4 choice is a conservative weekly dependence allowance for a daily test.

**Gate (c) verdict: FAIL as a sourced-effect test.** The panel is statistically large enough to detect the illustrative 0.020 effect under these assumptions, but no verified paper documents that effect as a same-day cross-sectional rank IC in U.S. large-cap equities. The simulation cannot establish a credible signal size; its SIC2/serial assumptions may also overstate effective breadth.

## 5. Criterion-4 portfolio feasibility first

### Exact daily turnover and cost arithmetic

The candidate captures only the final half-hour. A fully funded top-five sleeve funded at 15:30 and liquidated at 16:00 has **200% total-notional turnover per date** (100% buys plus 100% sells), before any basket changes. Its active share against EW30 while invested is 83.3% (`0.5 × sum(abs(top-five weights − EW30 weights))`), so it clears the active-share minimum at the cost of requiring full entry and exit each date. At 0.05% per dollar traded, that costs `2.00 × 0.0005 = 0.001` NAV per date: **10 bp each session**, or 25.2% of initial NAV on a simple 252-session annualization. This mechanical round trip exceeds criterion 4's 50% turnover cap. Carrying the names overnight to avoid the exit does not match the registered last-half-hour outcome; it adds unpredicted hours and changes the question.

For the cost-only rank-IC floor, the harness function is

`break_even_rank_ic(turnover, dispersion, cost_per_side=0.0005, top_fraction=5/30)`

where turnover counts buys plus sells, and `dispersion` is the cross-sectional SD of the **last-half-hour** returns. That dispersion is not an observed value here, so the following is transparent sensitivity analysis, not data:

| Assumed last-half-hour cross-sectional SD | Cost-only rank-IC floor at 200% daily turnover | Rank IC needed for costs ≤25% of gross edge |
|---:|---:|---:|
| 0.5% | 0.1386 | 0.5543 |
| 1.0% | 0.0693 | 0.2771 |
| 2.0% | 0.0346 | 0.1386 |

The rightmost column is four times the cost-only break-even IC, because costs below one quarter of gross requires gross edge ≥4× cost. The calculation assumes the harness linear rank-to-top-tail mapping, a fixed top-five portfolio, and no extra market impact. Even its 2% dispersion scenario needs rank IC about **0.139** before any inference hurdle. For comparison only, the criterion-4 bound audit's monthly top-five illustration requires rank IC around **0.083–0.087** for a six-year Holm-adjusted path under its assumptions; that monthly figure is not mathematically portable to a 30-minute sleeve. The daily intraday book needs its own return-risk and bootstrap calculation, which cannot be justified from the cited literature.

At 50% turnover, the cost-only floors in the table would be one-quarter as large (0.0346, 0.0173, and 0.0087 respectively), but the sleeve cannot both enter fully and exit daily within that cap. A partial active sleeve sized to respect the cap would also fail the goal's ≥50% active-share rule if its active deviation is reduced below half the book. The alternative goal clause (costs <25% gross edge) therefore requires effects several times the floor above.

### Expected effect, Sharpe and R6 family

The evidence does not give a cross-sectional intraday rank IC or a matching top-five-vs-EW30 effect, so no defensible expected Dow excess Sharpe or bootstrap *p* can be supplied. The S&P 500 mechanism test may estimate a same-day signal precisely, but six years of dates and greater cross-section do not solve the portfolio turnover/cost mismatch. The Holm family already contains 21 endpoints and would grow with any preregistration; the criterion-4 bound audit's approximately 0.8–1.05 annual active-Sharpe planning hurdle is a warning benchmark, not a measured expected effect for this direction. No available evidence supports that after costs.

**Gate 5 verdict: STOP — FAIL, criterion-4 infeasible on documented effects.** To proceed would require either gross cross-sectional effects not reported by the papers (roughly IC ≥0.139 even under the optimistic 2% dispersion assumption and full daily round-trip cost) or altering the signal/holding period/turnover rules. Neither is authorized in this screen. Do not submit a portfolio variant from this direction under current evidence.

## 6. Holdout availability and protocol

No holdout-specific input was requested, read, downloaded, or calculated on. The later holdout must follow the coordinator's one-shot criterion-5 protocol after a valid preregistration, runner, and input manifests are frozen. The Alpaca audit records a vendor stock-history start around 2016; therefore an Alpaca-based future holdout would have an availability gap for 2010–2015 that must be disclosed, while the available 2016–2020 portion remains sealed from this worker. Nothing in the source audit authorizes opening those values.

**Gate 6 verdict: PASS for this screen's discipline; holdout not touched.**

## Final screen decision

- **Overall:** **STOP — FAIL.** This remains a useful mechanism question, but a same-day cross-sectional U.S. large-cap effect of sufficient magnitude is not documented, and full daily entry/exit makes the fixed cost condition implausible.
- **Gate summary:** (a) PASS for verified adjacent literature, but no matched effect size; (b) FAIL for post-2020 mega-cap transfer; (c) FAIL for lack of a sourced plausible effect despite adequate synthetic sensitivity; (d) conditional PASS on the assumed ongoing full-session SIP bars; (e) PASS as distinct from T1/J1, under decision 157.
- **Expected-edge rank:** the sole candidate screened; no competing intraday signal is advanced.
- **What could change the decision:** an independent, post-2020 U.S. large-cap cross-sectional study of the same first-half-hour-to-last-half-hour relation with effect size net of execution costs, or a separately authorized design meeting the existing active-share and turnover/cost criteria without changing this signal after outcomes.
- **Reviewer/date:** L2, 2026-11-11.

## Sources checked

- Gao et al. (2018), [DOI](https://doi.org/10.1016/j.jfineco.2018.05.009).
- Baltussen et al. (2021), [DOI](https://doi.org/10.1016/j.jfineco.2021.04.029).
- Heston et al. (2010), [DOI](https://doi.org/10.1111/j.1540-6261.2010.01573.x).
- Chen et al. (2025), [DOI](https://doi.org/10.1007/s11156-024-01319-8).
- Schlie and Zhou (2026), [DOI](https://doi.org/10.3917/fina.pr.048).
- [Criterion-4 bound audit](../report_drafts/CRITERION4_BOUND_AUDIT.md), [Alpaca data audit](../r6_data/alpaca/ALPACA_AUDIT.md), and [R6 goal](../specs/r6_goal.md).
