# R10 L3B — ideas round 2 and one dev evidence trial

**Date:** 2026-11-12 · **Trial:** R10-L3B-01 · **Decision: NO-GO for freezing.** Only the top candidate below received a development outcome calculation. No `sealed_holdout*` file was opened, and no pre-2020-11-27 price or return values were read.

## Decision summary

| Rank | Strategy | Research status | 2010–2015 planning power | Decision |
|---:|---|---|---|---|
| 1 | Public 13F net-buyer breadth / post-disclosure accumulation | One pre-logged dev trial; negative net excess | 22 usable quarterly observations projected; MDE 1.163% net per quarter; 0.45% one-sided pass probability after 50% haircut | **NO-GO** |
| 2 | Forward split disclosure and retail-demand pulse | Screen-only candidate; no dev outcome measured | Illustrative only: N=6 events, 8% event SD gives 8.11% MDE; about 12.3% pass probability after halving the 3.38% published announcement effect and 20 bp round-trip cost | **NO-GO at idea gate** |

The R10 L4 ledger has 50 cumulative historical attempts/endpoints; these two ideas were not R10 executions in that ledger. R6 screened 13F herding/window dressing (S6/AO) and stock splits (AC); those negative screening records remain part of the search history and make these proposals exploratory re-evaluations rather than untouched discoveries. The 13F strategy's development panel covers only a narrow selected issuer set, not a full S&P 500 13F census. The returned Alpaca gap bars were not folded into a second outcome run, so the reported development statistic below is explicitly a pre-gap panel estimate and cannot authorize a freeze.

## 1. Top candidate — 13F broad net-buyer breadth at public disclosure

**Mechanism.** Broad institutional accumulation may generate correlated buying pressure and continuation after it becomes public. At each quarter's +45-calendar-day disclosure cutoff, compare each manager's reported shares with its previous-quarter report; among continuing managers with both reports public by the cutoff, calculate `(buyers − sellers)/(buyers + sellers)` for each PIT S&P 500 stock, requiring at least five changing managers. Form the equal-weight top tercile, enter the next session, and hold 20 sessions. A missing position row is a zero in a complete public filing; missing filings are excluded. This is a price/filing-only signal and does not require FactSet or crypto data.

**Published evidence and effect sizes.**

- Coval and Stafford (2007), “Asset Fire Sales,” identify severe mutual-fund flow-driven selling pressure and report a mean **−7.9% abnormal return** for heavily fire-sold stocks, followed by a **+6.13% rebound** as the pressure retreats (t=2.47). This is direct evidence of temporary flow-induced price pressure, but their pressure identification uses mutual-fund flows, which our 13F panel does not contain. [Journal of Financial Economics paper PDF](https://www.hbs.edu/ris/Publication%20Files/Asset%20Fire%20Sales%20in%20Equity%20Markets_59c0327e-b7ec-4487-b531-5e7dd1c62aad.pdf), [NY Fed summary](https://libertystreeteconomics.newyorkfed.org/2016/02/are-asset-managers-vulnerable-to-fire-sales/).
- Choi, Sias and coauthors (2014), “What Does Stock Ownership Breadth Measure?”, report that a one-standard-deviation increase in institutional ownership breadth predicts **+0.27% next-month return** (about **3.2% annualized**) after controls. This is a closer holdings-change outcome, though it is not an S&P-only public-filing-date strategy and does not isolate temporary price pressure. [Full paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC3992521/).

**2010–2015 holdout power.** The fixed design has at most 24 quarterly observations over six years. The dev eligible-window rate projects 22 observations. Using observed dev SD 2.194%, family=1, one-sided α=.05, and 80% target power gives `MDE = 2.4865 × 2.194% / √22 = 1.163%` net per quarter. The observed net mean is negative; after halving it for winner's curse, the estimated positive primary-gate pass probability is **0.45%**. This is a planning probability for the positive mean gate only, not full qualification. Since the source panel only covers roughly 30 names per quarter, it is not a calibrated probability for a complete S&P 500 universe.

**Red-team critique.** Form 13F records stale quarter-end positions, disclosed up to 45 days later; observed share changes are not dated trades and may reflect corporate actions, security mapping, manager reporting changes, or price-driven portfolio adjustments. Missing positions can be affected by confidential-treatment requests, manager exits and CUSIP/ticker lineage. The available extract is selected-manager / Dow-scale coverage and has only 22 development quarters; it cannot represent S&P-wide institutional crowding. Any measured return could be continuation in prior winners rather than causal pressure. Prior R6 screens S6 and AO already found timing, coverage and breadth problems. The negative, incomplete dev statistic and the tiny estimated positive-gate probability rule out freezing.

**Development evidence (R10-L3B-01).** Pre-registered in `specs/r10_trial_log.md` before the outcome computation. It used the specified PIT S&P panel and the locally staged 13F position extract, 10 bp one-way cost, one 20-session holding period per quarter, and a same-window equal-weight PIT S&P benchmark. The development period was 2020-11-27 through 2026-10-30.

| Measure | Result |
|---|---:|
| Quarterly observations | 22 |
| Mean net excess return | −0.902% |
| Sample SD | 2.194% |
| Median | −1.466% |
| 95% t interval | [−1.875%, +0.071%] |
| Holdout MDE (family 1, α=.05, 80%) | 1.163% |
| Positive-gate pass probability after 50% haircut | 0.45% |
| Cost | 10 bp one way (20 bp round trip) |

The mean was negative in four of the six entry years and the 2025 mean was −2.466%; yearly estimates are descriptive only. The local 13F file has 30 covered tickers in most report quarters and is not a full S&P panel. Initial calculation skipped non-finite NPZ endpoints; a subsequent Alpaca SIP GET-only gap retrieval obtained **883 of 895** unique missing S&P endpoint ticker-date pairs across 46 tickers, with 12 unavailable. The 13F outcome was not rerun after that retrieval, so the table remains the original frozen computation on the staged NPZ only. This data-completeness limitation independently supports NO-GO. Gap artifact: `alpaca_gap_bars.csv` (deduplicate by ticker/date; 84 retries duplicated rows). Reproduction code: `analyze_13f_dev.py`; it writes `dev_result.json` and `quarterly_outcomes.csv` from the preregistered staged panel but does not merge the later gap file.

## 2. Alternate candidate — forward stock-split disclosure pulse

**Mechanism.** The first public announcement of a forward split can lower the nominal share price, attract retail attention, and coordinate small-ticket buying. A candidate event study would use the earliest issuer disclosure as information time, verify the ratio/effective date with an action feed, and measure a fixed short post-announcement window. R6's AC screen already flagged the major risk: a split 8-K may follow the first public announcement, and the action feed's record creation time is not a reliable point-in-time signal. This is still a distinct event trigger versus the R10 trial above and no split outcome has been tested in the R10 ledger.

**Published evidence and effect sizes.**

- Ikenberry, Rankine and Stice (1996), “What Do Stock Splits Really Signal?”, report a **3.38% announcement return** and **7.93% first-year excess return** after split announcements. The sample predates modern fractional trading and these are event-study returns, not an identified retail-demand effect. [Journal article](https://doi.org/10.2307/2331396).
- “Post-split underreaction: The importance of prior split history” reports about **5% abnormal buy-and-hold return over the 12 months after announcement** for its full split sample; the effect depends on prior split history and does not establish a one-week, large-cap retail-flow premium. [Journal article](https://www.sciencedirect.com/science/article/pii/S1057521921002660).

**2010–2015 holdout power.** A real S&P event census and event-return SD were not verified, so no empirical power claim is justified. As a transparent low-breadth planning scenario only, assume one eligible independent S&P event per year (N=6) and 8% SD of net event CAR. Then family=1, α=.05 one-sided, 80%-power MDE is `2.4865 × 8% / √6 = 8.11%`. Halve the published 3.38% announcement return for winner's curse and deduct 20 bp round-trip cost before halving (1.59% effect); the corresponding positive-gate probability is about **12.3%**. At more events it rises, but neither N=6 nor 8% SD has been measured for this S&P window. The output is therefore a stress illustration, not a source-verified power result.

**Red-team critique.** Corporate signaling and past momentum can explain the published announcement return; a split is not itself a buy order. Public disclosure often precedes the SEC filing, so a filing-only clock may miss the move. Retail fractional access reduces the nominal-price barrier, and split events are sparse and clustered. The SEC item labels are heterogeneous; the Alpaca action feed does not provide a guaranteed first-public timestamp. R6's AC screen found one event in its bounded example and no evidence that split-specific pressure can rank or diversify an S&P portfolio. Freeze is not supported without a complete PIT event census and a genuinely executable first-disclosure rule.

## Final decision

**NO-GO for freezing either candidate.** The 13F trial has negative development net excess, a 0.45% haircut-adjusted positive-gate probability, narrow holdings coverage and unincorporated price gaps. The split candidate is rarer and its power calculation depends on unverified event-count and variance assumptions. Preserve the R10 50-trial historical ledger and the prior R6 idea screens; do not reinterpret these results as evidence that institutional holdings or split effects are universally absent.
