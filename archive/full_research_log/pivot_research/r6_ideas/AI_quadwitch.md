# AI — Quarterly option-expiry and index-rebalance pressure

**Status: SCREEN ONLY — no signal outcomes, no return calculations, and no variant is authorized by this document.**

## Identity and immutable-path preflight

- **Proposed short name and mechanism:** AI event pressure; option-expiry hedging and index-tracking adjustments may create concentrated, temporary stock demand around quarterly dates, followed by reversal.
- **Exact new output path:** `r6_ideas/AI_quadwitch.md`.
- **Target preflight:** this exact path did not exist immediately before creation. `AI_quadwitch` has not been used in the R6 ideas folder; decision 193 assigns the quad-expiry screen.
- **Development date range:** 2020-11-27 through 2026-10-30; earliest permissible worker data date 2020-11-27. Alpaca options availability is documented from February 2024 onward; the staged market-data audit's illustrative options sample is from June 2024.
- No request or local market-data read covered any date before 2020-11-27; no holdout file or sealed-basket ETF was accessed. The Alpaca audit was read as existing documentation, and only its development-period feasibility statements were used. No API keys or secrets were read or printed.
- No stock/option return, signal, IC, portfolio return, or event outcome was calculated for this screen.

## 1. Overlap with prior work

Two candidate mechanisms were considered:

1. **Quadruple-witching expiry pressure.** This directly repeats the option-expiration family already screened and rejected in `r6_ideas/C.md` (deep-in-the-money call exercise), `r6_ideas/X_options.md` (expiry hedge/pinning), and `r6_ideas/S4-S6.md` (expiration and month-end institutional pressure). A generic calendar-only quad-witching rule would only rename the event and has no cross-sectional pressure measure. Replacing unavailable option open interest with total contract volume would change the signal and would not measure buyer/dealer pressure.
2. **Quarterly index-rebalance pressure.** This overlaps the R5 index-change feasibility failure (`R5_FINAL.md`, including R5-N2), `r6_ideas/W_events.md` direction 2 (float/share-count reweights), and `r6_ideas/P4.md` (passive ownership changes). A scheduled quarterly date or rebalance-day auction-volume spike is not new issuer-specific signed demand; a true issuer score would need a new point-in-time benchmark target-weight change file that is not staged.

These two are not literally the same signal as P1, but they are prior-rejected event families and fail the novelty gate independently of the unavailable inputs. **Novelty verdict: FAIL.**

## 2. Exact pressure measure and dated data source

### Candidate A: quad-witching expiry pressure

A hypothetical usable signal would rank each Dow stock before the third Friday in March, June, September, and December by signed, delta-weighted option exposure requiring dealer hedge adjustment near expiry. A more explicit form would be the pre-expiry change in dealer-equivalent share hedge demand, normalized by the stock's 20-session median share volume; positive values mean implied dealer purchases. The formation timestamp would be the last U.S. close before expiry; the proposed horizon would be expiry-session open-to-close, with a fixed next-session reversal diagnostic only if it were separately authorized. The exact sign must not be changed after outcomes.

This score cannot currently be reconstructed from the free staged inputs. Alpaca states that its historical option data start in February 2024; the **free indicative feed** is a derivative of OPRA with 15-minute-delayed trades and non-OPRA indicative quotes, while OPRA is subscription-only. Official source: [Alpaca Historical Option Data](https://docs.alpaca.markets/us/docs/historical-option-data). The Alpaca audit records one successful 2024 AAPL contract-trades sample, which establishes a narrow access/schema example only. It does not establish full Dow contract-history coverage, historical open interest, customer opening/closing classification, or dealer inventory sign. Even a SIP/OPRA trade sign would not by itself identify whether a position opened or closed or the dealer's net book.

At most **11 quarterly expiry sessions** fall after Alpaca's February 2024 history start and before the 2026-10-30 development cutoff (four in each of 2024 and 2025, and three through September 2026); the number with complete eligible Dow option exposure is unknown. The remainder of development, 2020-11-27 through January 2024, has no Alpaca option history. The full 2010–2020 criterion-5 holdout also has no Alpaca option history.

### Candidate B: quarterly index-rebalance pressure

A distinct, if it were eligible, signal would be each incumbent Dow constituent's signed target-weight change in an identified tracked index, as announced by the provider before the effective rebalance close, multiplied by that index's assets benchmarked to it and divided by the stock's median dollar volume. Positive target-weight change is predicted buying pressure. Form no earlier than the public index announcement; test the effective-date closing-auction window or the next session, with the prediction horizon frozen before any outcomes. A same-day rebalance-volume increase alone has no sign and is not a pressure variable.

Free materials can identify public announcements, and the staged Alpaca audit confirms SIP auction and one-minute-bar endpoint feasibility on development-period samples. However, the needed free point-in-time index target-weight / float-factor changes and associated assets-tracking-the-index panel are not staged. The R5 index-change review found only three Dow index membership announcement dates in its development review; this is not a count of routine quarterly factor-file changes. `W_events.md` also found no verified free point-in-time Dow float-factor panel. Thus, calendar availability is not issuer-pressure coverage. No same-day option or stock values were read to create a signal.

**Signal/data verdict:** Candidate A fails data coverage and identification; Candidate B fails its point-in-time issuer-flow input gate and duplicates screened index-demand work. The short samples described above are input-access checks only, not signal outcomes.

## 3. Point-in-time coverage and independent breadth

| Candidate | Verified dated inputs | Maximum event count in window | Usable name-event coverage | Independent breadth |
|---|---|---:|---|---|
| Quad-witch | Alpaca historical option data start Feb 2024; one AAPL June 2024 contract-trades example in the existing audit | 11 scheduled quarterly expiries after data start, through Sep 2026 | Unknown; complete option chain/OI and Dow-wide contract coverage are not established | At most 11 market-wide event dates; stocks share the same four annual shocks and SIC2 dependence remains |
| Quarterly index rebalance | Quarterly dates are calendar-known; R5's nearest Dow constituent-announcement sample had 3 dates; no point-in-time factor/weight panel established | Up to 24 calendar quarter-ends, but actual nonzero issuer target-weight changes are unknown | Unknown; no dated index target-weight changes joined to Dow names | Quarter events are common shocks; at best 24 dates, and within-SIC2 cross-section is not independent |

The option data have a left-censored start and likely selective contract coverage: currently listed and active contracts are easier to request than complete historical chains; no denominator for missing or inactive contracts is established. The free indicative feed is not the OPRA consolidated feed. Underlying symbol mapping and corporate-action adjustments also require a frozen contract master. For index reweights, constituent membership / target factors need point-in-time effective dates and announcements; present-day membership or restated index shares cannot be substituted. The input audit does not establish counts of eligible names, signals, or independent SIC2 clusters; those counts are **unknown**, not zero observations inferred from price outcomes.

**Coverage/breadth verdict: FAIL.** Option history is truncated to the last 2.7 years of the six-year development window and lacks the necessary exposure fields; index target-weight input coverage is unverified. Neither branch has a sufficiently measured issuer-event panel.

## 4. Effective breadth and power at a sourced plausible effect

### Quad-witch literature and power

- Chen and Lu, [“Stock returns on option expiration dates: Price impact of liquidity trading,” *Journal of Empirical Finance* 28 (2014), 273–290](https://doi.org/10.1016/j.jempfin.2014.03.003), report a roughly **0.8 percentage-point expiration-day fall** among stocks with sufficiently large deep-in-the-money call open interest relative to underlying volume, followed by a short-term reversal. This is conditional, historical, and not a cross-sectional rank IC for modern Dow names.
- Roll, Schwartz, and Subrahmanyam, [“Stock Price Clustering on Option Expiration Dates,” *Journal of Financial Economics* 78 (2005), 331–361](https://doi.org/10.1016/j.jfineco.2004.08.005), study optionable stocks in 1996–2002 and document clustering near strikes; their estimated average return impact is a 16.5 bp lower bound under the paper's exposition, not a post-2020 portfolio edge.
- Plastun et al., [“Witching days and abnormal profits in the US stock market,” *Cogent Economics & Finance* 11 (2023), 2182016](https://doi.org/10.1080/23322039.2023.2182016), examine daily and weekly Dow, S&P 500, and Nasdaq index data from 2000-01-01 to 2021-09-20. The paper reports negative Dow index returns on 55% of witching dates but reports that most indices/tests do not yield statistically different or profitably exploitable patterns; the Dow exception is a market-index directional result, not a Dow cross-sectional stock-imbalance effect. Its strategy discussion does not establish the R6 transaction-cost or family-wise threshold.

I ran the synthetic design-only harness for the **11 maximum option-history event dates**, `assets=30`, `dates=11`, one-lag Newey–West event-series sensitivity (`horizon=2` in the harness), AR(1)=0.20, null rank-IC SD `1/sqrt(29)=0.1857`, hypothetical mean event IC 0.10, 5,000 simulations, seed 20261111. Result: power for NW t≥2 was **0.4832** (MCSE 0.00707), mean effective date count **9.17**, and 80%-power MDE **0.1743**. The assumed 0.10 rank IC is not sourced; the papers' event-day return effects cannot be converted into rank IC without exposure prevalence, conditional dispersion, direction, and cross-sectional ranks. The calculation is optimistic because it assumes all 30 names have valid exposure, independent rank noise, and no extra event/SIC2 clustering.

### Index-rebalance literature and power

- Lynch and Mendenhall, [“New Evidence on Stock Price Effects Associated with Changes in the S&P 500 Index,” *Journal of Business* 70(3) (1997), 351–383](https://doi.org/10.1086/209722), document post-announcement abnormal returns and partial reversal around additions/deletions using post-October-1989 data. This is an inclusion event, not routine quarterly reweighting among incumbent Dow names.
- Bogousslavsky and Muravyev, [“Who Trades at the Close? Implications for Price Discovery and Liquidity,” *Journal of Financial Markets* 66 (2023), 100852](https://doi.org/10.1016/j.finmar.2023.100852), show closing auction volume spikes on index rebalancing days and report a 20% (15%) persistent increase (decrease) in auction volume relative to intraday volume after S&P 500 additions (deletions), compared with controls. Auction volume is unsigned and this is not a post-2020 constituent return IC.
- The S&P Dow Jones Indices review, [“What Happened to the Index Effect?” (2021)](https://www.spglobal.com/spdji/en/research/article/what-happened-to-the-index-effect-a-look-at-three-decades-of-sp-500-adds-and-drops/), studies S&P 500 additions/deletions from 1995 through June 2021 and concludes the index effect has structurally declined, with improved liquidity a possible explanation.

The nearest event-count design has only **three** R5 Dow index membership announcement dates (2024-02-20, 2024-11-01, 2026-06-23), not a verified routine quarterly weight-change panel. I ran `power_sim.py` for 3 dates, 30 names, one-lag Newey–West event-series sensitivity (`horizon=2` in the harness), AR(1)=0.20, rank-IC SD 0.1857, hypothetical mean IC 0.10, 5,000 simulations, seed 20261112. Power was **0.4526** (MCSE 0.00704), mean effective date count **2.50**, and 80%-power MDE **0.3337**. This is a synthetic upper-bound sensitivity only: 0.10 is not literature-calibrated, and no adjustment for event-date market-wide dependence or SIC2 clustering was made. Even treating all 24 quarter-ends as independent events would be an unsupported breadth assumption until nonzero issuer-level adjustments are documented.

**Power verdict: FAIL for both.** The source effects do not match the proposed rank-IC estimand and event-specific power is low even under optimistic assumptions.

## 5. Criterion-4 portfolio feasibility first

If the issuer-level signals existed, a low-turnover implementation could form the rank-weighted top half of Dow names only during the event window and compare it with same-date EW30. This shape has **55% active share** when fully deployed. A complete entry from EW30 to the rank-top-half book and exit back to EW30 implies approximately **220% total-notional turnover per isolated event** (110% each transition); at 0.05% per traded dollar this costs about **11 bp per round trip**, before market impact. Four events per year imply about **44 bp/year** costs and require at least **176 bp/year gross active edge** to keep direct costs below one-quarter of gross edge. These are arithmetic planning assumptions, not measured turnover or a return estimate. A 50% turnover cap would require scaling down the active tilt and could violate the 50% active-share rule during event transitions.

The relevant shape benchmark in `report_drafts/CRITERION4_BOUND_BY_SHAPE.md` is weekly RankTopHalf: 80%-power hurdle rank IC **0.074** at assumed persistence ρ=0.2 (synthetic six-year, 24-test Holm design). That bound assumes 312 weekly formation observations; neither proposed event signal supplies 312 independent weekly observations. The quad-witch option window supplies at most 11 events; the index branch has 24 calendar dates only if all quarterly dates carry measurable, nonzero issuer-level target changes, which is unverified. The simulated event MDEs above (0.159 and 0.305) exceed 0.074 and are not evidence that a portfolio can attain criterion 4. There is no defensible post-cost Dow excess Sharpe, bootstrap p, or Holm-adjusted feasibility estimate from the cited papers.

The event literature cannot be translated into the required positive net excess return, Sharpe above EW30, and one-sided block-bootstrap p<0.05 after the full R6 Holm family. The 0.8% option effect is conditional on unavailable deep-ITM-call exposure, and the index studies concern inclusion/deletion effects or unsigned auction volumes; neither justifies a forecast for an event-conditioned Dow rank portfolio. **Criterion-4 verdict: FAIL — no credible, matched effect or sufficient event breadth.**

## 6. Holdout availability and protocol

This screen needed no holdout path or holdout-specific input and did not read, download, plot, or calculate on sealed Dow or sealed-basket ETF data. The later holdout must follow goal criterion 5 and remain coordinator-only after development gates, frozen preregistration, code hash, and input manifests pass. Alpaca's options history begins in February 2024, so the option-derived signal cannot be reconstructed for the 2010–2020 holdout from this provider; an unavailable option signal must be reported as criterion-5 infeasibility, not replaced with a calendar proxy. Index-event metadata would also need an audited point-in-time historical archive before a coordinator could assess holdout availability.

**Holdout protocol verdict: PASS for this screen; criterion-5 feasibility for the candidate signal is FAIL on current options inputs.**

## Final screen decision

**Overall: STOP — FAIL.** Quad-witch pressure duplicates C3/X_options/S4–S6 and Alpaca options data cover only from February 2024, with a free indicative feed and no point-in-time dealer/OI sign. Index-rebalance pressure duplicates R5 index-change/W_events/P4, while issuer-level quarterly weight-change inputs are unavailable and previous Dow change-event breadth was only three dates. Both lack a sourced large-cap rank effect, adequate effective breadth, and evidence that net costs and criterion 4 can be cleared.

Evidence that could change this decision would require (i) a free, complete point-in-time Dow option OI/open-close/dealer-position history across the entire development period and holdout, or a separately identified pressure variable with a defensible position sign; and (ii) a free point-in-time index target-weight/float-factor history for Dow names with enough independent events plus post-2015 large-cap price-pressure evidence meeting the 0.074 weekly rank-IC benchmark after costs. These are not established; do not preregister or run a portfolio.

**Reviewer/date:** R6 screen, 2026-11-11.

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.