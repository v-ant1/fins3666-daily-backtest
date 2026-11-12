# R6 idea screen — AA: large-cap flow effects above the criterion-4 scale

**Status:** SCREEN ONLY — no project signal outcomes, forward returns, portfolio returns, or variant authorization. **Overall: STOP — FAIL.** The closest large-cap weekly flow result is economically notable, but it is from a 1999–2004 sample, is a liquidity-provision reversal rather than sustained buying pressure, and depends on proprietary market-maker inventory records. I found no non-overlapping, post-2010-sample effect with a reported rank IC of at least 0.06 or a comparable large-cap weekly spread that is buildable from the permitted free/Alpaca inputs.

## Identity and immutable-path preflight

- **Proposed short name / mechanism searched:** AA high-IC literature screen; whether intermediary inventory or signed demand pressure can move large U.S. stocks enough to exceed the R6 portfolio hurdle.
- **Exact new output:** `r6_ideas/AA_highIC_lit.md`.
- **Existence check:** this exact path did not exist before this screen.
- **Name check:** `AA_highIC_lit` is new. I reviewed the 38 prior screens listed in the R6 decision record and the current `r6_ideas/*.md` inventory; the nearest prior families include liquidity provision and reversal, signed minute-bar flow, microstructure/OFI, sector flows, fund flows, and peer/network flow.
- **Date boundary:** any worker input used here is dated **2020-11-27 or later**. Literature samples are reported as described in the cited papers; no project data older than 2020-11-27 was opened or requested.
- **Path/date preflight:** no holdout path is used. The target is new; no ambiguous worker path was needed.

## 1. Overlap with prior work

| Literature lead considered | Nearest prior screens | Mechanism difference | Novelty verdict |
|---|---|---|---|
| Dealer inventory and liquidity-provider flow | `J.md` / reversal and liquidity provision; `Z_minute_flow.md` / signed minute flow; `V_microstructure.md` | Direct specialist inventory and competing-market-maker trades are not daily CLV or aggregate signed bars. However, both are established liquidity-provision/reversal pressure and the inventory information is not in the permitted data. | **FAIL** as a new R6 family: too close to already screened microstructure/reversal, with no observable new input. |
| Institutional-manager transaction flow | `U_fundflow.md`, `M_SURVEY.md`, `Z_minute_flow.md` | Daily identified manager transactions differ from quarterly holdings or undifferentiated SIP bar flow. | **FAIL**: institutional flow/fund-flow family already screened; the cited data are proprietary. |
| Cross-asset order-book OFI | `E1`, `Z_minute_flow.md`, `X_comovenet.md` | Quote-depth changes and OFI are more direct than CLV; cross-impact connects assets. | **FAIL**: same signed peer-flow question as E1/Z and order-book event data unavailable from the free minute-bar bundle. |

These are evidence leads, not three new proposals. Renaming an existing mechanism or combining them after examining project results would violate the exclusion. No candidate passes novelty.

Candidate-level gate summary (P = pass, F = fail, with the specific failing condition):

| Lead | (a) papers/effect | (b) large-cap, post-2010 sample | (c) useful power input | (d) free/Alpaca data | (e) novelty | Result |
|---|---|---|---|---|---|---|
| Hendershott–Seasholes dealer inventory | **P** for a reported large-stock weekly spread in its sample | **F**: observations end 2004; no post-2010 sample | **F**: no rank IC or comparable effect for the allowed Dow shape | **F**: requires proprietary specialist/CMM records | **F**: overlaps prior liquidity-provision/reversal and flow screens | **STOP** |
| Hendershott–Menkveld intermediary pressure | **F** for the requested statistic: 0.49% is a price-pressure estimate, not a future rank IC/spread | **F**: the headline is not a post-2010 cross-sectional large-cap return result | **F**: pressure half-life cannot supply an IC-based power input | **F**: proprietary intermediary data | **F**: same liquidity-provision/reversal family | **STOP** |
| Foster–Gallagher–Looi manager trades | **F** for the threshold: ten-day predictability is reported, but no compatible effect size | **F**: Australian sample, no post-2010 observation evidence identified | **F**: cannot specify power without a matched magnitude | **F**: manager database not free/staged | **F**: institutional/fund-flow overlap with prior screens | **STOP** |

## 2. Exact pressure measure and dated data source

There is no eligible signal to preregister. For completeness, the closest literature-defined candidate would be a **dealer-inventory reversal**: form daily normalized NYSE specialist inventory as the deviation of end-of-day inventory from its trailing three-month mean, scaled by its trailing standard deviation; also use the paper’s normalized competing-market-maker net trades. At each weekly close, apply the published sort/double-sort rule and predict the next five-session return, with the inventory-pressure direction fixed by the paper. The measure is observable only in NYSE proprietary files, not in daily OHLCV, one-minute OHLCV, or Alpaca auction records.

Relevant verified research:

- Hendershott and Seasholes, [“Liquidity Provision and Stock Return Predictability,” *Journal of Banking & Finance* 45 (2014), 140–151](https://doi.org/10.1016/j.jbankfin.2013.12.021), use NYSE Specialist Summary File and Consolidated Equity Audit Trail records from March 1999 through December 2004. Weekly sorts predict reversals. The full-universe double sort earns 88 basis points over the following week, but this is not a large-cap-only estimate; their size-split Fama–MacBeth inventory high-minus-low estimate for large stocks is 0.23 percentage points per week (t=3.81). CMM's marginal estimate is not significant for the large-stock tercile. This supplies a documented large-stock weekly spread, but its observation period is pre-2010 and it is explicitly a reversal/liquidity-provision result.
- Hendershott and Menkveld, [“Price Pressures,” *Journal of Financial Economics* 114 (2014), 405–423](https://doi.org/10.1016/j.jfineco.2014.08.001), estimate intermediary-induced transitory pressure averaging 0.49% with a 0.92-day half-life using NYSE intermediary data. This is a price-impact/half-life statistic, not a weekly stock-rank IC or investable long-short spread; it cannot be substituted for one.
- Foster, Gallagher, and Looi, [“Institutional Trading and Share Returns,” *Journal of Banking & Finance* 35 (2011), 3383–3399](https://doi.org/10.1016/j.jbankfin.2011.05.018), use daily transactions from 34 Australian equity managers and the largest 50 ASX stocks. They report statistically and economically significant prediction of large-cap returns over ten days, but the accessible result does not give a compatible rank IC or a post-2010 observation window. The manager-transaction database is not a free public feed.
- Cont, Cucuringu, and Zhang, [“Cross-Impact of Order Flow Imbalance in Equity Markets,” *Quantitative Finance* 23 (2023), 1373–1393](https://doi.org/10.1080/14697688.2023.2236159), study order-book OFI among the top 100 S&P 500 names using 2017–2019 Nasdaq/LOBSTER events. Their forecasts are at short intraday horizons and are not a 21-session IC or weekly Dow spread. This is post-2010 large-cap mechanism evidence, but it is not the required magnitude statistic and overlaps prior R6 peer-flow screens.

Thus, under a strict interpretation that “after 2010” means **the underlying observations must be after 2010**, none of the large weekly spreads above qualifies. Even if “after 2010” means publication date, the strongest inventory result still fails free-data feasibility, novelty, and criterion-4 comparability. No signal was constructed; no project returns or ICs were calculated.

**Gate 2: FAIL.** The only strong candidate uses proprietary counterpart identity and end-of-day dealer inventories. Alpaca trade/quote fields may permit a much larger signed-flow proxy, but they do not identify which liquidity provider accumulated inventory and cannot reconstruct specialist/CMM classifications. Applying the same literature's inventory interpretation to aggregate bar imbalance would be a new, unsupported proxy rather than the frozen measure.

## 3. Point-in-time coverage and independent breadth

The only data check was an input-schema/count audit of already-staged 2024 Alpaca samples; I did not inspect prices, trade directions, auction imbalance, signals, or outcomes.

| Input sample | Development-period coverage | Input-only counts | Result |
|---|---|---:|---|
| `r6_data/alpaca/bars_1min_dow_2024.json` | 2024-06-03, six minute labels | 3 symbols × 6 rows = 18 rows; fields include OHLC, volume, trade count, VWAP | Confirms a small SIP minute-bar schema sample only. |
| `r6_data/alpaca/bars_1day_dow_2024.json` | 2024-06-03 to 2024-06-05 | 3 symbols × 3 dates = 9 rows; same bar fields | Confirms a three-name daily schema sample only. |
| `auctions_AAPL_2024.json`, `auctions_DIA_2024.json`, `auctions_MSFT_2024.json` | one 2024 sample date per symbol | one saved sample row per file | Auction records have no market-maker identity or signed buyer/seller field. |

Usable full-window dates, names, signal nonmissingness, event count, and SIC2 breadth are **not established** by these samples. The sample bar names are AAPL, CAT, and JNJ; they are not a point-in-time roster test. The larger historical SIP feasibility audit says full S&P minute bars are technically pageable, but that does not establish data access or identity of the inventory holders. The local audit also estimates that a signed trade-plus-quote archive would require an impractical multi-terabyte pull. No 2024 sample path is before the permitted start. Survivorship, symbol lineage, trade-condition corrections, and completeness remain unverified at whole-universe scale.

**Gate 3: FAIL.** Three names and a handful of rows do not establish independent event breadth, and the missing dealer identity is intrinsic to the source, not a coverage gap that more bars would fix.

## 4. Effective breadth and power at a sourced plausible effect

The 0.23% weekly large-stock estimate from Hendershott–Seasholes is a spread in its old NYSE sample; the paper does not report rank IC for that size tercile, and its universe, execution assumptions, and specialist data differ from this task. I do **not** convert basis points into an IC because there is no matched return dispersion, investable R6 portfolio shape, or turnover/cost series that supports such a conversion.

As a design-only sensitivity—not as an effect estimate—I ran `r4_harness/power_sim.py` for 312 weekly dates, horizon 5 / NW lag 4, signal autocorrelation 0.20, 5,000 synthetic simulations and seed 20261611. The harness null IC SD is `1/sqrt(N−1)`. N=500 represents a hypothetical S&P-sized cross-section; N=70 is a conservative independent-cluster proxy, not a measured SIC count.

| Synthetic cross-section | Planted mean IC | Power for NW t ≥ 2 | 80% MDE | Meaning |
|---:|---:|---:|---:|---|
| 500 names | 0.060 | 1.000 | 0.0084 | Conditional sensitivity only; no source reports this IC for an eligible signal. |
| 70 independent units | 0.060 | 1.000 | 0.0227 | Conditional cluster proxy; actual cluster dependence is unknown. |
| 500 names | 0.074 | 1.000 | 0.0084 | Same as the rank-weighted top-half weekly portfolio hurdle; planted solely as a reference. |
| 70 independent units | 0.074 | 1.000 | 0.0227 | Does not establish real S&P breadth or portfolio power. |

The high simulated mechanism-test power is not evidence that either paper's spread equals an IC of 0.06 or 0.074; it only shows what this synthetic design would detect if such a mean IC were supplied. It is not portfolio-level or Holm-adjusted power.

**Gate 4: FAIL.** No matched post-2010 large-cap IC effect supports the required power input, and the available strong study result is not a signal realizable from the allowed inputs.

## 5. Criterion-4 portfolio feasibility first

The relevant fixed comparison is criterion 4: positive net excess return over EW30, Sharpe above EW30, and one-sided block-bootstrap evidence after Holm. The shape-specific synthetic audit estimates that the cheapest qualifying long-only shape—rank-weighted top half, 55% active share—needs about **0.074 weekly rank IC** at signal autocorrelation 0.2 under a 24-endpoint Holm family. It also states that widening the portfolio lowers the previous top-five bound but does not bring it down to typical documented large-cap effects.

The only numeric candidate result that looks large is Hendershott–Seasholes' 23 bp/week high-minus-low large-size-tercile coefficient on the inventory sort, in a 1999–2004 sample. It is a value from their study's own weekly cross-section, not a rank IC, and is gross of this project's fixed 0.05% per-side trading cost and its portfolio/turnover rules. Their 88 bp/week double-sort result is for the whole sample and cannot be represented as a mega-cap effect. The 0.49% average price pressure in Hendershott–Menkveld is a short-lived price-impact estimate, not recurring weekly alpha. It would be misleading to compare these numbers directly with an IC hurdle or assume a six-year Sharpe.

For the 2024 Alpaca bars/auction fields, there is no specified signal to translate. Even the optimistic bar-derived alternative requires a new measurement hypothesis and cannot inherit the paper's dealer-inventory effect. A turnover estimate is therefore not meaningful; it cannot be shown to meet ≤50% turnover or the cost share condition. Against a 21-test current R6 Holm family (and a growing family as more endpoints are registered), no eligible effect range exists to support criterion 4.

**Gate 5: FAIL — criterion-4 feasibility not established.** The paper's weekly spread may warrant academic follow-up with proper dealer data, but it is not evidence that an allowed Dow implementation clears the fixed after-cost, Holm-adjusted hurdle.

## 6. Holdout availability and protocol

This screen did not open, read, download, or calculate on any sealed holdout input. No holdout-specific path is needed for a fail-gated idea. If a genuinely eligible proposal were ever reviewed, the only later test would be the coordinator-controlled criterion-5 protocol; it would require a point-in-time market-maker inventory/transaction archive and an explicit availability-only check before any holdout values could be considered. Such a historical inventory source is not available in the staged inputs.

**Gate 6: PASS for protocol compliance; no holdout test is justified.**

## Final screen decision

- **Overall:** **STOP — FAIL.** No candidate clears overlap, matched post-2010 large-cap effect, data, power-input, and criterion-4 gates together.
- **Evidence rank (research lead only, not eligible ideas):** (1) Hendershott–Seasholes dealer-inventory/liquidity-provider reversal; strongest directly reported weekly large-stock evidence, but old and requires proprietary identities/inventories. (2) Hendershott–Menkveld intermediary price pressure; large direct impact with sub-day half-life, but it is not weekly cross-sectional alpha and relies on proprietary data. (3) Foster–Gallagher–Looi institutional transactions; large-cap and daily, but no comparable effect statistic and proprietary input. Cont et al. is a useful recent large-cap OFI mechanism check, but it overlaps E1/Z and has no weekly/monthly rank effect.
- **What could change the decision:** an authorized, point-in-time dealer-inventory/transaction data source spanning the development window; an independent post-2010 large-cap validation with a directly reported weekly spread or rank IC; and a frozen mapping to the Dow long-only portfolio demonstrating realistic turnover and costs. None is supplied by the current free/Alpaca bundle.
- **Reviewer/date:** L2, 2026-11-11.

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
