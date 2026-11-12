# Round V — recent literature on large-stock pressure and spillovers

**Screen status: one distinct candidate identified; it FAILS the full idea gate and should not be frozen.** I screened 2022–2026 papers in the requested journals against the R5 final report and all existing R6 idea files. The sole candidate retained as a genuinely different mechanism is an earnings-calendar memory cue: one firm's earnings announcement cues buying in a different, non-announcing company that previously shared an announcement context with it. The analysis below is literature and input feasibility only; no project prices, signal outcomes, forward returns, ICs, or portfolios were calculated, and no holdout data were opened.

## Rank by expected edge

| Rank | Candidate | Literature potential | Verdict | Subjective chance of clearing the complete fixed R6 stack |
|---:|---|---|---|---:|
| 1 | Earnings-calendar memory cues: anticipated short-lived demand in a non-announcing associated firm | The exact 2025 RFS paper documents attention-driven buying pressure and near-term reversal, but only in 2005–2019 and not as a low-turnover Dow strategy. | **FAIL-GATE**: weak modern mega-cap evidence, low season-clustered power, and a timing/cost mismatch. | **0.5%** |

This is the expected-edge rank among ideas that survived the exact-mechanism novelty check, not a claim that the signal has positive expected returns in our data. The probability is a judgment, not a statistical estimate.

## Candidate: earnings-calendar memory cue pressure

### Proposed mechanism to evaluate

Define a link between two firms only when they released earnings on the same date in at least one of the target firm's prior four fiscal-quarter seasons, using information that was already public then. At a later announcement by firm A, a linked firm B that has no own announcement within three sessions receives a “memory cue.” The published mechanism predicts extra attention and buying in B, followed by reversal as the temporary demand dissipates. The event schedule, source-to-target timing, cue count, and buy sign would be frozen before any future project outcome is inspected.

For a future measurement, the cue is the externally dated demand shock; public daily OHLCV could supply a provisional target pressure proxy (close-location weighted by abnormal volume) for a mechanism check. That proxy is not signed order flow and cannot be described as a direct buy-imbalance measure. A portfolio would need to forecast cues from information known before formation and then form a monthly Dow book with total traded notional capped at 20% of NAV per rebalance; simply buying after the announcement would miss much of the immediate response. Full replacement of one 20%-weight name trades about 40% of NAV, so a 20% cap would defer some changes and further dilute a short-lived signal.

### Gates (a)–(e)

- **(a) Recent literature — PASS for the behavioral mechanism; mixed for a durable return signal.** Charles, [“Memory Moves Markets,” *Review of Financial Studies* 38 (2025), 1641–1686](https://doi.org/10.1093/rfs/hhae086), uses firms' rigid earnings schedules to identify memory associations. It reports that a later announcement by one firm cues attention and buying pressure in its associated non-announcing firms; the paper's main sample is 2005–2019, and the cue response is followed by reversal over roughly five weeks. Gödker, Jiao, and Smeets, [“Investor Memory,” *Review of Financial Studies* 38 (2025), 1595–1640](https://doi.org/10.1093/rfs/hhaf006), provide experimental evidence that investors over-remember positive outcomes and consequently reinvest too much, offering a plausible behavioral basis for memory-driven demand; they do not test an inter-firm trading strategy. Wang, Hirshleifer, and Peng, [“News Diffusion in Social Networks and Stock Market Reactions,” *Review of Financial Studies* 38 (2025), 883–937](https://doi.org/10.1093/rfs/hhae025), find that socially connected firms have stronger immediate earnings reactions and volume, but weaker post-announcement drift. That result cautions that more connected attention can speed information incorporation rather than create a persistent peer premium.

- **(b) Large-cap and post-2010 survival — PARTIAL historically; FAIL for a post-2020 Dow claim.** Charles's sample includes post-2010 years but ends in 2019; the article does not establish a separately estimated effect in the largest firms or a result after 2020. Its earnings-schedule logic could still generate memory cues among well-followed firms, because the cue comes from timing overlap rather than weak analyst coverage. Against that argument, large firms' events are highly visible, while the 2025 social-network study finds weaker drift where social news transmission is stronger. Nothing in these papers establishes that a five-week reversal or buying-pressure effect survives in Dow mega-caps after 2020.

- **(c) S&P power — FAIL under season-clustered planning.** I ran `r4_harness/power_sim.py` with 500 S&P names, 20 independent quarterly-season observations (six development years after a four-quarter, development-only warm-up), a 10-session outcome condensed to one statistic per season, signal autocorrelation 0.50, 5,000 simulations, seed `20261111`, and an assumed cross-sectional IC SD of 0.06737. The SD is the cluster-adjusted planning value `sqrt((1 + (500/53 − 1) × 0.15)/(500 − 1))`, using 53 SIC2 groups and assumed within-SIC2 correlation 0.15; neither the correlation nor the SD is estimated from project returns. The simulator's `horizon=1` represents one non-overlapping seasonal IC observation (NW lag 0), not the underlying 10-session target return. At a hypothetical mean rank IC of 0.020, simulated power for NW *t* ≥ 2 was **38.98%**, with an 80%-power MDE of **0.0428** and 20 seasonal observations. These are synthetic assumptions, not observed performance or an effect-size conversion from the paper. If one instead counts daily cue dates as independent, power rises sharply, but that ignores common quarterly earnings-season shocks and overlapping 10-session responses; the season-cluster result is the more credible planning screen.

- **(d) Free-data feasibility — PARTIAL at the event-metadata layer; FAIL as a ready cue panel.** The project already has the SEC-derived `r6_data/earnings_clock_sp500.csv`, covering the development-only period from 2020-06-01 through 2026-10-30. An input-only count gave **13,443 filings**, **603 filing issuers**, **622 ticker identities**, **13,373 distinct issuer-date rows**, and **1,279 distinct filing dates**. Of those dates, **1,047** had at least two S&P issuers filing, representing **187,995 unordered same-date issuer pairs** before de-duplication across dates. These are raw co-filing counts, not lagged memory links or valid cue events; no edge panel was constructed. They show that the free event timestamps exist, but not that the past four-quarter schedule rule produces enough independent cue-target observations. SEC acceptance time is also not necessarily the first public release time. Before any outcome join, a cheap next step would count eligible, point-in-time cue links and target coverage using only this event clock, dated S&P rosters, and filings; discard amended duplicates and use the conservative acceptance-time execution rule. No stock-price values were read for these counts.

- **(e) Novelty and criterion-4 feasibility — PARTIAL novelty; FAIL expected-edge feasibility.** This is not the same as E1's same-industry prior-month CLV pressure, C1/J1's within-industry intraday or reversal tests, K1's own-stock earnings-event pressure, or B4's GDELT article co-mention graph. The edge here is a historical earnings-calendar coincidence that creates a cognitive cue in a non-announcing stock; there is no economic-link graph and no source-stock price pressure. The broad “news/attention network” family is adjacent to B4 and K2, so the distinction must remain this exact schedule-based memory mechanism. Even if the event effect is real, the literature does not show that a strategy can anticipate the cue, trade at ≤20% monthly turnover, and deliver the roughly 0.8 annualized excess Sharpe needed by decision 76 after costs and Holm correction. This screen therefore does not support a portfolio pass claim.

## Other recent papers screened out before shortlisting

| Paper | Reason it was not retained as a new candidate |
|---|---|
| Chen, [“Production Complementarity and Information Transmission across Industries,” *Journal of Financial Economics* 155 (2024), 103812](https://doi.org/10.1016/j.jfineco.2024.103812) | The reported connected-peer return lead-lag is important, but a peer-return momentum network is too close to E1/J1's monthly or SIC-linked peer pressure, and its return signal is not itself an observed buying-pressure measure. |
| Charles's 2023 JFE study, [“When Can the Market Identify Old News?”](https://doi.org/10.1016/j.jfineco.2023.04.008) | Recombined old news causes larger price and volume reactions with subsequent reversal, but its Bloomberg news input overlaps B4's GDELT/news-network family and is not a fresh low-cost input path. |
| Kim, [“Correlated Demand Shocks and Asset Pricing,” *Review of Financial Studies* (2026)](https://doi.org/10.1093/rfs/hhag094) | Directly relevant benchmark-induced demand pressure, but its identification uses exogenous index membership and its institutional benchmark channel overlaps the explicitly excluded index-change/passive-flow family. |

## Recommendation

Keep only the memory-cue idea as a documented literature lead; **do not freeze it or spend an R6 variant**. Its exact mechanism is distinct enough to deserve a mention in the scan, but its published evidence is pre-2020, it lacks a ready free point-in-time cue-link panel, the conservative S&P power is only 36%, and the fast event response conflicts with a low-turnover Dow portfolio. A filing-only link-coverage audit could resolve whether the memory graph can even be built; it cannot repair the criterion-4 edge-size gap. No project signal or return outcomes, prices, or holdout data were used here.

## Reproducibility notes

- Input coverage counts were computed from `r6_data/earnings_clock_sp500.csv` using filing-date and issuer/ticker identifiers only; no filing body, price, return, signal, or outcome column was used.
- Synthetic power command:

```powershell
python r4_harness/power_sim.py --assets 500 --dates 20 --horizon 1 --signal-autocorrelation 0.5 --ic-sd 0.06737408413976867 --mean-ic 0.02 --simulations 5000 --seed 20261111
```

- Paper evidence above refers to published research estimates; those are not project outcomes and are not treated as an IC or portfolio Sharpe for this design.
