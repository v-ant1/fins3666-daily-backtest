# R6 event-concentrated pressure screen (Round AA)

**Status: SCREEN ONLY — STOP, no new candidate advances.** I could not find a dated event-pressure signal that is simultaneously novel relative to all 38 existing R6 screens, supported by post-2015 Dow-size evidence, measurable from free/staged data, and plausibly large enough for the weekly rank-weighted top-half hurdle. I do not recommend a new variant or a relabeling of an earlier direction.

## Identity and immutable-path preflight

- **Short name / mechanism:** AA event-concentrated pressure search; no new mechanism survived the overlap and evidence screen.
- **Exact new output:** `r6_ideas/AA_event_concentrated.md` (checked absent before writing).
- **Prior-name check:** all existing 38 `r6_ideas/*.md` files were read, plus `R5_FINAL.md` and the R6 decision log.
- **Allowed project interval:** 2020-11-27 through 2026-10-30 only. No holdout input or path was used.
- **Sources considered:** only free/staged SEC, FINRA and Alpaca families already inventoried for development. I did not download or inspect any sealed data.

## 1. Overlap with prior work — FAIL for any plausible direct event candidate

The existing screens already cover the event sources most capable of creating measurable, concentrated pressure:

- **SEC Form 4 insider purchase clusters:** F (`r6_ideas/F.md`) already tests dated insider buying; the separate activist-disclosure path is in N (`r6_ideas/N.md`). Alldredge and Blank report that clustered insider purchases are followed by abnormal returns exceeding 2% over the subsequent month ([*Do Insiders Cluster Trades With Colleagues?*, *Journal of Financial Research* 42 (2019), DOI 10.1111/jfir.12172](https://doi.org/10.1111/jfir.12172)). Jeng, Metrick and Zeckhauser report insider purchases earn more than 6% abnormal returns per year in their study ([*Review of Economics and Statistics* 85 (2003), DOI 10.1162/003465303765299936](https://doi.org/10.1162/003465303765299936)). These results make the source interesting, but re-testing it as a “cluster” or “event-time” variant would still duplicate F's Form 4 buying-pressure family. Their reported horizons/portfolio effects are not weekly rank ICs in current Dow-size stocks.
- **SEC activism / beneficial ownership disclosures:** N already screens activist campaign events; P4 and U cover ownership-demand disclosures. Recasting an activist or passive-holder filing as an event shock is not a distinct pressure source.
- **FINRA short sale, short interest and delivery-failure signals:** D, L, V, and the related S/W screens cover these event/timing variants; they do not supply an untested event family.
- **Alpaca intraday and auction pressure:** T, Z, and the Z intraday momentum re-screen cover minute bars, closing-auction size, same-day intraday momentum, and end-of-day pressure/reversal. Auction size has no buy/sell side, and renaming the last-hour or signed-bar feature does not create a new source.
- **Other dated filings and flows:** K/B cover earnings/news disclosures; W and Y cover buybacks, dividend dates, index changes and seasonal flow. R5_FINAL already records index-change and ETF-flow feasibility kills.

Accordingly, overlap gate is **FAIL** for each plausible free/staged route. The insider-cluster literature is mentioned as the strongest-looking near-neighbor, not advanced as a candidate.

## 2. Exact pressure measure and dated data source — FAIL / no eligible source-signal pair

There is no new pressure variable to define without reusing one of the screen families above. A prospective event design would need to state whether pressure is executed buying, a filing disclosure, an auction imbalance, or inferred activity, and when it first becomes public. The existing literature distinguishes these: Form 4 reports trade details with a lag; a disclosure is not contemporaneous evidence that flow continues after it becomes tradable. The SEC Form 4 dataset description and field definitions are public ([SEC Insider Transactions Data Sets](https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets), [SEC data dictionary](https://www.sec.gov/files/insider_transactions_readme.pdf)), but the same data source is already in F.

**Input-only incident and correction:** during an initial local Form 4 coverage attempt, I opened the staged `r6_data/insider/form4_dev.parquet` before applying the 2020-11-27 predicate. The file includes earlier development warm-up rows. I did not inspect, report, or use any earlier-period counts or outcomes, stopped that attempt, and notified the coordinator by escalation. Following the coordinator's ruling, I re-read with PyArrow row filters applied at file-read time to **both** `filing_date >= 2020-11-27` and `transaction_date >= 2020-11-27`. The filtered read returned 130,434 P/S transaction rows, including 6,175 code-P rows across 445 tickers/443 issuer CIKs and 303 filing weeks (latest filing 2026-09-30). These are raw transaction/coverage counts, not independent insider clusters: code P combines open-market and private purchases, and amendments can duplicate transactions. They confirm the broad SEC source is technically available but do not solve the overlap or yield a clean signed execution-pressure series.

No new SEC/FINRA/Alpaca pull was made for a second event definition because no distinct candidate survived novelty. Thus no source/date/formation specification or independent-event manifest exists for a *new* direction. Gate (d): **partial for the overlapping SEC source; FAIL for a novel event direction**. The accidental unfiltered read remains disclosed and is not used for any signal or effect claim.

## 3. Point-in-time coverage and independent breadth — FAIL / no eligible event series

There are 312 nominal weekly observations over the six-year development interval under the shape-audit convention. This is not 312 independent event clusters, and an event-only strategy has fewer active weeks still. Because no novel event series survived gate 1, there are no admissible counts of independent events, valid non-event controls, covered issuers, or independent SIC2-event clusters to report. I did not infer coverage from project returns or use pre-start records.

Plausible SEC events also have practical issues: filing timestamps may follow the transaction; amendments can repeat events; form codes may mix transaction types; insider trades are sparse and uneven across issuers. FINRA summaries and auction-size fields are not signed issuer-level buying pressure by themselves. Gate (c) breadth/coverage for a *new* event test: **FAIL / not established**.

## 4. Effective breadth and power against the weekly hurdle — FAIL as evidence for any candidate

The requested shape audit reports a **0.074 weekly mean rank-IC hurdle** for a rank-weighted top-half long-only book, under its stated 24-test Holm, turnover, and synthetic return assumptions; it is a design bound, not an empirical minimum guaranteed for this candidate. The published Form 4 cluster estimate above is a monthly abnormal-return portfolio effect, not a weekly cross-sectional rank IC. It cannot be mapped to 0.074 or declared sufficient without an unsupported conversion. Existing intraday/auction papers likewise do not provide a directly matched weekly rank IC for a novel event signal in large U.S. stocks.

For context only, I ran the synthetic `r4_harness/power_sim.py` with 500 assets, 312 weekly dates, horizon 5 (NW lag 4), AR(1) 0.20, assumed SIC2 clustering (53 groups, within-group correlation 0.15; IC SD 0.2089), 5,000 draws, and seed 20261111. At a planted mean IC of **0.074**, power for NW *t* ≥ 2 was **99.96%**, with 80%-power MDE **0.0394** and mean effective N **226.9**; at an illustrative 0.020 it was **30.54%**. These are optimistic synthetic, continuous-week calculations. They do not represent event-signal power: they assume a cross-section every week, whereas rare event concentration reduces active dates and can increase event-cluster dependence. The 0.074 hurdle itself is not a sourced event effect. No candidate therefore passes the power/effect-size gate.

**Gate (c): FAIL** for all novel event candidates, because none has a matched, documented post-2015 large-cap weekly effect to plant. The high synthetic power at the hurdle only says that a sufficiently persistent weekly IC of that size would be detectable under these assumptions; it does not supply the missing effect.

## 5. Criterion-4 portfolio feasibility first — FAIL / unsupported edge

The shape under consideration is the audit's weekly **rank-weighted top half** (55% active share), compared with EW30, with 0.05% per traded dollar and the weekly turnover/cost rule as specified in the shape audit. It requires approximately **0.074 mean weekly rank IC** for the audit's 80%-power criterion-4 planning case. Event-only investing would need an event-frequency-adjusted calculation; fewer exposed weeks cannot be treated as a free reduction in the required per-event effect. No independently documented post-2015 Dow-size event estimate in the remaining untried free-data families reaches or translates to that threshold. The Form 4 paper's >2% subsequent-month return is not a candidate estimate here because (i) it is monthly, (ii) its result is an abnormal-return portfolio estimate, not rank IC, and (iii) Form 4 pressure is already screened in F.

**Gate (d/economic feasibility): FAIL.** There is no valid gross-edge estimate to subtract transaction costs from, nor a defensible six-year excess-Sharpe or bootstrap-p estimate. Replacing the event with a more frequent proxy, changing to a different signal, or moving the formation timestamp after inspecting outcomes would be a new direction and outside this screen.

## 6. Holdout availability and protocol

No holdout-specific input is needed for a screen that stops before a candidate. I did not open, read, download, or calculate on holdout data. If a future direction is selected, criterion 5 remains coordinator-only under the one-shot frozen-code protocol in `specs/r4_goal.md`; any data gap must be addressed through the authorized availability-only process before the coordinator's run.

## Final screen decision

- **Overall:** **STOP — FAIL.** No novel, free-data event-concentrated pressure direction survives the prior-screen exclusion and has a documented effect that supports the 0.074 weekly criterion-4 hurdle.
- **Gates:** overlap **FAIL**; exact novel signal/source **FAIL**; eligible event breadth and power **FAIL**; criterion-4 effect/cost evidence **FAIL**; holdout discipline **PASS** (untouched).
- **What could change this decision:** a genuinely untested event source with an independently documented post-2015 large-cap weekly rank IC near the shape hurdle, together with a clean, development-only, point-in-time input manifest and event-cluster power design.
- **Chance of a complete R6 pass:** effectively **0% on the evidence available for this screen**; this is a judgment, not a statistical estimate.
- **Reviewer/date:** R6 worker, 2026-11-11.
