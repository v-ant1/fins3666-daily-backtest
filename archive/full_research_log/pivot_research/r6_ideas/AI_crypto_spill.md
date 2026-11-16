# Round AI — Crypto-market pressure spilling into US equities

**Status:** SCREEN ONLY — no signal outcomes, no return calculations, and no variant is authorized by this document.

## Identity and immutable-path preflight

- **Proposed short name and mechanism:** AI crypto spill. BTC/ETH spot buyer flow, futures funding, or forced liquidation pressure may transmit risk appetite or deleveraging pressure to crypto-exposed US equities when US stocks reopen.
- **Exact new output path:** `r6_ideas/AI_crypto_spill.md`.
- **Target path preflight:** confirmed absent before writing. The `AI_crypto_spill` basename was not present in `r6_ideas/` or `R5_FINAL.md`; decision 193 assigns the direction but does not authorize a runner.
- **Permitted data dates:** development window only, from 2020-11-27 through 2026-10-30; earliest worker-path date is **2020-11-27**. Provider documentation says its archive begins 2025-06-28.
- **Path and date check:** the API probe requested only 2025-06-28 and 2025-08-01 files; the 2026-10-30 endpoint probe returned a generic request error and supplied no data. No input or output path used pre-2020-11-27 data or a holdout path.
- **Credential handling:** `CRYPTOHFTDATA_API_KEY` was read from `A2/.env` in memory and sent only in the API request. It was not printed, written to a file, or included in an error message.

## 1. Overlap with prior work

- `r6_ideas/P1.md` screens own-stock overnight-return pressure; this proposal uses an external 24/7 crypto-market input, not Dow overnight returns.
- `r6_ideas/AH_foreign_session.md` screens foreign-session moves and `r6_ideas/U_crossasset.md` screens macro and commodity-linked inputs. Both are broad cross-market relatives, but neither measures crypto trades, funding, or liquidations.
- The indexed registry has no prior CryptoHFTData or crypto-flow test, and `R5_FINAL.md` contains no such tested direction. Decision 193 is the assigned idea, not prior evidence from a run.
- **Duplicate check:** this would be a new data source and transmission channel, although the equity outcome in the literature is usually an index, not a stock-level pressure rank. The current data cannot define a usable, point-in-time list of Dow firms with direct crypto exposure.
- **Verdict: PASS for novelty only.** This does not establish thesis fit, coverage, or feasibility.

## 2. Exact pressure measure and dated data source

The API offers three distinct possible inputs; they should not be blended after looking at results:

1. **Spot buyer imbalance:** for BTCUSDT and ETHUSDT spot trades, aggregate signed notional over a predeclared UTC interval as `(buyer-initiated notional − seller-initiated notional) / total notional`, using the exchange aggressor flag (`is_buyer_maker`: buyer-maker means seller-initiated; otherwise buyer-initiated). A weekend interval ending before the US Monday open is the cleanest timing test. Positive values mean net aggressive buying.
2. **Perpetual funding:** use the latest funding rate observed by the time cutoff for BTC and ETH futures. Positive funding is a crowding/long-demand measure, not a signed trade-flow measure; whether it should predict continuation or reversal is ambiguous from the thesis alone.
3. **Liquidation imbalance:** aggregate signed forced-liquidation notional, assigning long liquidations a negative sign and short liquidations a positive sign, over the same pre-open interval. These are forced trades and can signal either pressure transmission or exhaustion. Binance warns its public liquidation stream is sampled and incomplete.

A future clean test would have to choose **one** of these definitions before outcomes. A development-only formation would use an interval ending before a US equity open; any equity measurement would start no earlier than the next regular-session open. Funding `event_time` requires special handling: provider documentation warns some historical OKX event times were settlement times later than observation time, so `received_time` or a corrected publish-time field must be used to prevent look-ahead. This API sample did not test any equity returns or build these signals.

**Source / access:** CryptoHFTData’s [REST documentation](https://www.cryptohftdata.com/docs/rest-introduction) describes hourly compressed Parquet files and the `/download` endpoint; its [funding dataset page](https://www.cryptohftdata.com/datasets/crypto-funding-rate-data) reports history since 2025-06-28 and free-account API access. The [liquidations documentation](https://www.cryptohftdata.com/docs/rest-liquidations) says some venue feeds are sampled and incomplete, and flags late OKX records; the [mark-price documentation](https://www.cryptohftdata.com/docs/rest-mark-price) flags historical funding timestamp semantics. Individual files were requested by exact date/hour, so the API itself filtered the probe before rows were read. The free-account terms and data access are documented; redistribution/licensing for a research release was not established and would need a separate check.

**No-outcomes confirmation:** this screen computes no signal values, forward returns, ICs, portfolio returns, or other outcome statistics.

- **Verdict: FAIL for full-window data readiness.** The vendor's documented first date is 2025-06-28, so this source cannot supply the goal's approximately six-year development window beginning 2020-11-27.

## 3. Point-in-time coverage and independent breadth

Input-only availability probe, requested at read time for one UTC hour on 2025-08-01 (inside the development window):

| Input | BTC rows | ETH rows | Fields observed |
|---|---:|---:|---|
| Binance spot trades | 204,029 | 241,286 | `event_time`, `price`, `quantity`, `is_buyer_maker`, trade identifiers |
| Binance futures mark/funding | 3,600 | 3,600 | `event_time`, `received_time`, `funding_rate`, `next_funding_time`, mark/index prices |
| Binance futures liquidations | 54 | 98 | `event_time`, `received_time`, `side`, `quantity`, `price` fields |
| **Total** | **207,683** | **244,984** | Six downloaded hourly files; 452,667 rows in total |

A separate input-only spot/funding probe for 2025-06-28 confirmed one BTC spot-trade file (20,994 rows) and one BTC futures mark/funding file (10,800 rows). This confirms that some earliest-date files are available and that the sample schemas contain the relevant fields; it does not establish complete daily coverage. The 2026-10-30 exact-hour requests did not complete successfully, so the latest end-of-development coverage was not verified from files.

- **Usable dates checked:** one fully readable sampled date (2025-08-01), plus two individual files on 2025-06-28. The provider documents a start date of 2025-06-28; file-by-file coverage and outage counts over the full period were not measured.
- **Names:** two crypto contracts (BTCUSDT and ETHUSDT), across three data types, in the sampled hour. No issuer exposure roster was constructed.
- **Nonmissing signals:** zero candidate signals were constructed by design. The sampled source fields were present in the schemas; no nonmissing signal count can be reported without creating a signal.
- **Independent events / clusters:** no pressure threshold or event labels were constructed; therefore independent event count is not established. No issuer-to-crypto-exposure map exists in this screen, so independent SIC2 cluster count is also not established. The three crypto feeds and two coins are correlated inputs, not independent market events.
- **Point-in-time and selection limits:** timestamps and arrival timestamps are both supplied, but there are venue-specific delays, sampled liquidations, symbol/contract changes, and hourly outages. BTC/ETH availability does not equal equity exposure. A survivorship-safe exposure cohort would require contemporaneous public filings or a dated point-in-time classification; classifying Dow technology/financial names by sector alone would create an overly broad and weak proxy.
- **Evidence transfer:** the studies below mainly use aggregate indices. They do not establish a stock-level cross-sectional signal for current Dow mega-caps.
- **Verdict: FAIL.** A one-hour sample is enough to confirm the format, not enough to establish six-year coverage, stock-level breadth, independent events, or issuer mapping.

## 4. Effective breadth and power at a sourced plausible effect

**What the literature establishes:** Iyer’s IMF note, [“Cryptic Connections: Spillovers between Crypto and Equity Markets”](https://doi.org/10.5089/9781616358068.065), uses daily return/volatility connectedness for BTC and Tether against equity indices including the S&P 500. It reports that BTC spillovers to equity indices rose after the pandemic, and attributes roughly 8–10% of equity-return variation and 14–18% of equity-volatility variation to BTC in its index-level decomposition. Those percentages are forecast-error variance shares, **not** rank ICs, mean return premia, or stock-selection Sharpe ratios.

Mourey, Shahrour and Şoiman, [“A crypto-stock weekend effect: Predicting Monday stock returns using weekend cryptocurrency returns,” *Finance Research Letters* (2025), DOI 10.1016/j.frl.2025.108661](https://doi.org/10.1016/j.frl.2025.108661), use 20 large cryptocurrencies covering about 85% of crypto market cap and 798 daily observations from 2021-01-01 to 2025-06-01, with the S&P 500 index and sector indices. They report asymmetric evidence: negative crypto weekend returns predict lower Monday equity-index returns; positive returns do not show comparable effects. This is relevant to timing and stress transmission, but it tests crypto **returns**, not spot order flow, funding, or liquidations; its primary equity outcome is an index, not a cross-section of individual firms. Its equity market data are licensed/commercial, rather than the proposed free API input.

A further US study, Akyildirim et al., [“Connectedness of cryptocurrency-related stocks and the cryptocurrency market: Evidence from the United States,” *North American Journal of Economics and Finance* (2025), DOI 10.1016/j.najef.2024.102344](https://doi.org/10.1016/j.najef.2024.102344), reports crypto-to-equity volatility spillovers among Nasdaq blockchain-economy stocks during the COVID period. That selected crypto-related stock set and volatility-connectedness estimator do not establish a point-in-time Dow stock rank IC.

**No independent source provides a matched large-cap rank IC for these proposed inputs and horizon.** The public papers therefore do not supply a defensible plausible IC range. For planning only, the weekly RankTopHalf hurdle in `report_drafts/CRITERION4_BOUND_BY_SHAPE.md` is approximately **0.074**; this is a required portfolio hurdle, not a literature estimate or an assumed empirical effect.

Synthetic sensitivity using `r4_harness/power_sim.py` only (no market outcomes): assume a 30-name Dow cross-section, 70 weekly dates (roughly the number of calendar weeks from the vendor start to the development cutoff), a five-session horizon, AR(1) serial correlation 0.5, null rank-IC SD `1/sqrt(30−1)`, 2,000 simulations, seed 20261111, and planted IC 0.074. Result: probability of Newey–West `t ≥ 2` was **0.636** (Monte Carlo SE 0.0108), effective N **31.46**, and 80%-power MDE **0.0941**. This simulator does not apply the Holm first-step cutoff or the portfolio block bootstrap; the actual criterion is harder. Its independent-date and null-SD assumptions are optimistic because the upstream crypto pressure is common across names and equity exposure clusters by industry.

- **Verdict: FAIL.** There is no effect estimate matched to the candidate signal, horizon, or individual mega-cap cross-section; even the optimistic synthetic Dow-sized power at the portfolio hurdle is below 80%, before Holm and bootstrap adjustments. The documented index spillover percentages cannot be converted into cross-sectional rank IC without unsupported assumptions.

## 5. Criterion-4 portfolio feasibility first

- **Candidate portfolio if feasibility changed:** point-in-time Dow roster, long-only `K = min(5, floor(n/2))` selected among issuers with a predeclared direct crypto-exposure classification; compare with EW30 on the same eligible roster. Weekly rebalancing would align with the approximately weekly criterion-4 planning bound. The exposed cohort size and weights are unknown, and no reliable current/history mapping was established.
- **Turnover and active share:** neither can be estimated from the one-hour input-only sample. Exposure labels would likely be sparse and stable, while a daily crypto signal is common across exposed names; a turnover cap and active share cannot be claimed without a predeclared stock-level mapping and weights.
- **Costs:** use the fixed 0.05% per side and the goal's block-bootstrap/Holm procedure if ever authorized. The shape audit puts the weekly rank-weighted upper-half reference at about 0.074 IC under its stated assumptions; its cost/turnover screen is conditional and not a signal-specific estimate.
- **Effect-to-portfolio translation:** unavailable. The cited index variance-explained shares and the weekend study's index-level regression evidence are not rank ICs for 30 Dow names, so a net excess-return or Sharpe range would be invented. The input provider also lacks the first 4.6+ years of the six-year development interval.
- **Verdict: FAIL — criterion-4 infeasible on present evidence.** No sourced plausible effect supports the needed approximately 0.074 weekly rank IC; no stock-level cross-sectional exposure can be formed; the synthetic sensitivity at that hurdle yields 63.6% power at unadjusted `t ≥ 2`, below 80%. There is no basis to commission a portfolio run.

## 6. Holdout availability and protocol

No holdout file, path, value, roster, or return was opened. The provider's published first date (2025-06-28) is after the sealed holdout (2010-01-01 to 2020-10-31), so this particular data source cannot support the goal's holdout test. A future alternative source or substitute would require the goal's coordinator-controlled procedure and approval before any test; the coordinator must perform any holdout availability check without exposing values to workers.

- **Verdict: FAIL for this source under goal criterion 5.** It cannot provide holdout-period pressure inputs, and workers must not access the sealed panel.

## Final screen decision

- **Overall: STOP — FAIL.** Novelty is plausible, but data history is too short; the source measures crypto market inputs, not direct issuer exposure; effective independent breadth and stock-level effect sizes are unproven; synthetic power at the criterion-4 reference effect is under 80% even before family correction; and the specified input source cannot support the holdout protocol.
- **Evidence that could change this decision:** a licensed, documented point-in-time BTC/ETH flow/funding/liquidation history covering the full development period and holdout; a verifiable dated Dow/S&P issuer exposure map; independent large-cap stock-level results with the same pressure variable and horizon; and a predeclared power design clearing criterion 4 after Holm and block-bootstrap adjustments.
- **Reviewer/date:** dispatched screen, 2026-11-11.

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
