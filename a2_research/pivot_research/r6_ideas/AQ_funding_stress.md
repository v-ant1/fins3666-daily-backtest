# R6 screen: funding-stress pressure from Dow financials to SIC peers

**Status: SCREEN ONLY.** No project forward returns, signal outcomes, ICs, portfolio results, or holdout data were accessed or calculated. The data checks are input-availability counts only.

## Identity and immutable-path preflight

- **Proposed name and one-sentence mechanism:** AQ funding stress — widening financial-commercial-paper funding spreads may tighten intermediary balance sheets, induce selling in Dow financial firms, and transmit temporary negative pressure to economically linked SIC peers.
- **Exact new output path:** `r6_ideas/AQ_funding_stress.md`.
- **Target absent before writing:** confirmed with `Test-Path` before creating the file.
- **Name/overlap review:** the nearest existing screen is `AO_liquidity_shock.md` (peer liquidity stress, Amihud and SIC2 spillovers). `AH_treasury_auction.md` studies rates/auction pressure; `X_comovenet.md` studies cross-stock propagation networks; prior `R1` is daily CLV pressure; and the original pressure-heat design already diffuses OHLCV pressure. I did not open results, `R5_FINAL.md`, the Holm family, or any decision-log outcome lines.
- **Development dates and earliest permissible input date:** 2020-11-27 to 2026-10-30. Every FRED observation request was bounded at read time to those dates. No data path or request reached earlier dates or holdout data.
- **Path check:** only this new report, the prescribed planning/screen files, and the named adjacent idea screens were inspected. No holdout path was used.

## 1. Overlap with prior work

- **AO liquidity shock:** AO proposes peer illiquidity shocks that predict SIC2-peer returns and documents a weekly Dow book. AQ would use an aggregate funding-market stress trigger and hypothesize negative pressure from financial firms to linked peers. The proposed cause differs, but the network/peer endpoint and short-horizon transmission test substantially overlap.
- **R1 / original pressure-heat:** the proposed source leg would still need a stock-level measure of selling in Dow financials (for example, OHLCV sell pressure) before an aggregate funding shock could be said to create stock-specific source pressure. This reuses the project’s pressure ingredients and propagation structure.
- **AH Treasury auction and broader rates screens:** these use rates or funding conditions as common shocks, not a dated bank-to-borrower exposure network. AQ’s purported novelty is the financial-source-to-peer link, which is not available in the proposed free macro inputs.
- **FRED naming correction:** SOFR is the secured overnight financing benchmark; SOFR OIS swaps reference SOFR. SOFR itself is not an OIS quote, so “SOFR–OIS” is not a spread computable from the FRED SOFR series alone. The free FRED alternatives verified here are the daily 90-day AA financial commercial-paper rate (`DCPF3M`) and 3-month Treasury bill rate (`DTB3`), both discount-basis series, whose difference could form a CP–T-bill spread. This still measures aggregate conditions, not an issuer-specific bank shock.
- **Verdict: FAIL on current design.** Funding liquidity is a distinct economic channel, but the observable aggregate spread does not create a bank-to-peer network. A stock-level network would require a predated lender/borrower or equivalent exposure map; adding a broad OHLCV pressure interaction would also duplicate existing pressure and peer-liquidity work.

## 2. Exact pressure measure and dated data source

The only clean candidate macro variable available from the named free data is:

`CPstress[t] = DCPF3M[t] − DTB3[t]`,

measured in percentage points using financial CP and 3-month Treasury bill yields on dates when both are published. A preregistration could form the five-valid-publication-day change `Δ5 CPstress[t] = CPstress[t] − CPstress[t−5]`, then standardize it against the prior 252 valid observations. A rise in the spread predicts **negative** returns if funding stress produces selling pressure. These are design definitions only; I did not calculate a spread, change, standardization, stress threshold, or any stock-level score.

Formation would be at a weekly close using only a FRED observation already publicly available before that close; prediction, if a valid network design were later approved, would be the following five trading sessions. The Federal Reserve says commercial-paper data are usually posted around 1 p.m. but does not guarantee the release timing ([Federal Reserve Commercial Paper Rates release](https://www.federalreserve.gov/releases/cp/)). Therefore a safe implementation would trade no earlier than the next session after the observation is confirmed. FRED pages state that series values are subject to revision; a historical as-of test would need ALFRED vintages or contemporaneous archive evidence, not just today’s revised history.

FRED has the daily [DCPF3M financial CP rate](https://fred.stlouisfed.org/series/DCPF3M), [DTB3 three-month Treasury bill rate](https://fred.stlouisfed.org/series/DTB3), and [SOFR](https://fred.stlouisfed.org/series/SOFR). FRED labels DCPF3M and DTB3 as daily, percent, not seasonally adjusted and discount basis; CP observations can be missing when trade data are insufficient ([Federal Reserve CP release notes](https://www.federalreserve.gov/releases/cp/)). FRED access is free; the series carry their own citation/copyright terms. FRED provides no issuer-level bank funding data through these rates.

The pressure-transfer design is not operationally specified because the missing edge is material. Aggregate CP stress is identical for all names on a date. Multiplying it by a common SIC2 label does not yield a time-varying cross-sectional signal. A valid design would need to freeze a bank-to-borrower exposure network and dated exposure weights, then identify financial-source selling separately from the macro stress. Neither the CP spread nor SOFR provides those two inputs.

**Verdict: FAIL.** The candidate data have a well-defined sign and units, but no stock-specific source pressure or bank-to-peer exposure map follows from the named FRED series.

## 3. Point-in-time coverage and independent breadth

### Input-only feasibility pull

I requested only the following FRED CSV windows, with request-time date parameters `cosd=2020-11-27` and `coed=2026-10-30`: `SOFR`, `DCPF3M`, and `DTB3`. These counts cover input availability, not any signal or return result.

| Input-only item | Count | How obtained |
|---|---:|---|
| SOFR date rows / nonmissing observations | 1,546 / 1,479 | FRED CSV pull bounded at request time to development dates |
| DCPF3M date rows / nonmissing observations | 1,545 / 925 | Same date-filtered pull; blanks were counted as missing, not filled |
| DTB3 date rows / nonmissing observations | 1,546 / 1,482 | Same date-filtered pull |
| DCPF3M–DTB3 common nonmissing dates | 925 | Matched dates on presence only; no spread values calculated |
| Development endpoints for nonmissing CP series | 2020-11-30 to 2026-10-30 | Earliest/latest nonmissing DCPF3M dates from the bounded pull |
| Candidate Dow issuer scores / signal records | 0 / 0 | No issuer network or stock-pressure score was constructed |
| Independent stress events | Not classified | No threshold was set; no event count was manufactured |
| SIC2 clusters available to the design | Not established for AQ | AO’s input-only 2024 audit reports 19 Dow SIC2 groups, but AQ has no lender/borrower exposure crosswalk and those groups are not bank-link clusters |

The target universe would be 30 point-in-time Dow constituents under the project rule, but an eligible source and target set is not defined by this FRED panel. The series are aggregate rates, not financial-company securities. A CP observation can be missing when the market has insufficient trades, and the 925 matching dates are therefore fewer than the daily Treasury/SOFR grids. The source release usually arrives midday with no guaranteed timing. FRED labels all observations subject to revision, so the current download does not prove the as-of value was known at each historical formation date.

The papers do not establish a post-2020 large-cap Dow effect. Brunnermeier and Pedersen is a theoretical model; Bai et al. study a specific Chinese liquidity crunch with loan-level bank-firm relationships; neither transfers a numerical effect to present-day U.S. Dow names. No ticker-, issuer-, or borrower-level observations were retrieved.

- **Verdict: FAIL.** Macro-series coverage is usable for a common stress indicator, but name-level signal coverage is zero and link-level independent breadth is unknown.

## 4. Effective breadth and power at a sourced plausible effect

### Evidence and transfer limits

Brunnermeier and Pedersen, [“Market Liquidity and Funding Liquidity,” *Review of Financial Studies* 22 (2009), 2201–2238, DOI 10.1093/rfs/hhn098](https://doi.org/10.1093/rfs/hhn098), develop a model in which traders’ funding constraints and market liquidity reinforce each other, potentially creating liquidity spirals. This supports the funding-liquidity mechanism, but the paper is theoretical and does not estimate a Dow stock-level weekly return effect.

Bai, Dang, He, and Lu, [“Does lending relationship help or alleviate the transmission of liquidity shocks? Evidence from a liquidity crunch in China,” *Journal of Financial Stability* 58 (2022), 100889, DOI 10.1016/j.jfs.2021.100889](https://doi.org/10.1016/j.jfs.2021.100889), analyze the June 2013 Chinese interbank liquidity crunch using loan-level bank-firm links. Their paper reports 2,377 listed firms in the event CAR table; mean three-day abnormal return around the shock is −2.2%, and effects are more negative for firms with outstanding loans while long-term relationships mitigate some losses. This is a specific non-U.S. banking shock with direct loan links, not a daily CP-spread-to-SIC2 Dow rank signal.

Coval and Stafford, [“Asset Fire Sales (and Purchases) in Equity Markets,” *Journal of Financial Economics* 86 (2007), 479–512, DOI 10.1016/j.jfineco.2006.09.007](https://doi.org/10.1016/j.jfineco.2006.09.007), study U.S. mutual-fund flow-driven transactions over 1980–2004 and find that distressed funds’ widespread selling creates price pressure in securities they hold in common; investors providing liquidity earn significant returns. This supports a general selling-pressure channel but studies mutual-fund flows, not bank funding spreads or bank-borrower SIC peers. None of these sources reports the requested post-2020 Dow weekly rank IC or a transferable numeric effect range.

### Synthetic power sensitivity

Because no paper reports a signal-matched rank IC, there is no sourced plausible effect at which to claim power. I ran `r4_harness/power_sim.py` only as a labeled sensitivity using design assumptions: 309 weekly observations (the approximate count of weeks from 2020-11-27 through 2026-10-30; the actual count of usable dates would be lower after missing inputs), five-session horizon (NW lag 4), assumed date-level autocorrelation 0.20, and 5,000 simulations. To reflect the approximate 19 SIC2 groups in the nearest 2024 Dow roster audit, the conservative sensitivity used 19 independent effective names; a 30-name case is shown as an optimistic bound. At an **illustrative, unsourced** planted mean IC of 0.02, the 19-name case gave `P(NW t ≥ 2)=25.12%`, Monte Carlo SE 0.00613, effective N 224.72, and 80%-power MDE 0.04468. The optimistic 30-name case gave 36.56% power, SE 0.00681, effective N 224.72, and MDE 0.03520. These are synthetic date-level IC power calculations, not results for CP stress, and they omit link-level clustering and Holm adjustment.

- **Verdict: FAIL.** No sourced effect matches the signal, horizon, post-2020 large-cap universe, and sign; the illustrative sensitivity is underpowered and below the criterion-4 planning bound.

## 5. Criterion-4 portfolio feasibility first

- **Hypothetical portfolio if a distinct source/target signal existed:** weekly rank-weighted top-half Dow book, 15 long positions, 55% active share, same-date EW30 benchmark, and 0.05% transaction cost per side. No portfolio or signal weights were formed.
- **Turnover and costs:** the synthetic portfolio-shape audit estimates 116% total-notional weekly turnover for RankTopHalf at signal autocorrelation 0.20. At its 0.074 rank-IC planning bound, costs are 24.1% of gross active edge, meeting the alternative cost rule just under its 25% ceiling. This is a shape calculation, not an AQ turnover or return estimate.
- **Effect translation:** the literature supplies no CP-stress weekly rank IC, Dow active return, Sharpe, or post-cost portfolio effect. The Chinese loan-linked event study and mutual-fund fire-sale study cannot be translated into a cross-sectional Dow IC without imposing unstated exposure, event-frequency, cross-sectional volatility, and persistence assumptions. The illustrative 0.02 synthetic IC is below the 0.074 weekly RankTopHalf planning bound and is not literature sourced.
- **Criterion-4 verdict: FAIL.** The expected signal effect is unsupported and the network cannot be constructed from aggregate FRED series; positive net excess return, Sharpe superiority, and Holm-adjusted block-bootstrap significance cannot be credibly projected. Do not commission portfolio outcomes to fill this evidence gap.

## 6. Holdout availability and protocol

No holdout-specific input is needed. No sealed Dow data, pre-development data, or holdout roster was opened or downloaded. Because the idea fails the development input, overlap, power, and criterion-4 gates, no holdout availability check or test is proposed. If a future idea clears all screens and receives authorization, the coordinator-controlled one-time protocol in goal criterion 5 applies after the preregistration and code are frozen; any scout must remain limited to the authorized availability-only evidence.

- **Verdict: PASS for respecting the holdout rule; no holdout test requested.**

## Final screen decision

**Overall: STOP — FAIL.** Public FRED funding rates can support a common stress series, but the verified inputs do not provide a separate OIS quote for a “SOFR–OIS” spread or an issuer-specific bank-to-SIC-peer network. The literature supports liquidity spirals, borrower effects under a particular loan-linked shock, and fire-sale price pressure, but none supplies a matching post-2020 Dow effect; the closest extant idea AO already covers peer liquidity stress and SIC2 spillovers.

Evidence that could change the decision would be a free, date-stamped and vintage-aware bank funding spread; an ex-ante lender/borrower exposure map covering the Dow and its peers; direct or independently validated selling pressure at the financial source names; and post-2020 large-cap evidence in a compatible effect metric sufficient to clear the weekly criterion-4 bound.

Reviewer/date: Orca worker, 2026-11-11.
