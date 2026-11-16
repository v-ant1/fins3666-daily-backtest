# R6 Idea Screen AE — analyst upgrade/downgrade drift

**Verdict: STOP — FAIL. Do not register a variant or start a runner.** Analyst recommendations can move prices and may be followed by drift, but the Alpaca News API sample did not expose normalized rating-change fields and yielded no explicit upgrade/downgrade headline in the strict one-day sample. The historical effect evidence also does not establish a compatible post-2020 Dow rank IC; under explicit sparse-event assumptions, Holm-adjusted power falls below the weekly portfolio hurdle.

No project signals, forward returns, portfolio returns, ICs, or other outcomes were calculated or inspected. The only API pull was for three names on one 2024 US trading date, with article content excluded; API credentials were read locally from `A2/.env` and never displayed, written, or included in output.

## Identity and immutable-path preflight

- **Proposed short name:** AE, analyst rating-revision pressure.
- **Mechanism:** an explicit broker upgrade represents positive recommendation pressure and a downgrade negative pressure; delayed investor response may allow the signed demand shock to persist briefly.
- **Exact new output path:** `r6_ideas/AE_analyst_ratings.md`.
- **Target check:** the exact target did not exist before writing, and no prior `r6_ideas/AE*` artifact was found.
- **Prior-name check:** decision 181 assigned the analyst-upgrade/downgrade idea to Round AE, but this specific output path is new.
- **Development window:** 2020-11-27 through 2026-10-30; earliest permissible worker-path date is **2020-11-27**.
- **Path/date safety:** the only API query used `2024-06-04 00:00–23:59 America/New_York` (expressed as UTC bounds); no earlier data, price series, holdout path, or sealed values were accessed.
- **Credential handling:** the Alpaca key names were read from local configuration without printing values; credentials were not persisted.
- **Verdict:** PASS for output-path and date safety.

## 1. Overlap with prior work

The closest prior files are `r6_ideas/B.md`, which considered shared-analyst coverage and forecast-revision spillovers, and `r6_ideas/AB_alpaca_news.md`, which rejected generic Alpaca/Benzinga news tone or volume as a repeat of GDELT attention ideas. AE is distinct in its event: an explicit own-company sell-side rating change, with signed upgrade/downgrade direction and short post-event drift. It does not use analyst co-coverage links, broad headline tone, or news volume. The use of Alpaca/Benzinga itself is not novel; the fixed rating-revision event is the distinction.

The `R5_FINAL.md`, `r6_ideas/*.md`, and `specs/r6_decisions.md` review found no previously screened, identical own-stock Benzinga rating-revision signal. Decision 181 explicitly queued it for AE.

- **Verdict:** PASS for distinctness from prior signal definitions, with a clear data-identification limitation below.

## 2. Exact pressure measure and dated data source

### Proposed one-variant signal

For each point-in-time Dow constituent at Friday close, count rating-change events with an admissible Benzinga `created_at` timestamp strictly before that close and within the preceding five completed US sessions. Assign `+1` only to a true upgrade and `−1` only to a true downgrade; exclude initiations, reiterations, maintained ratings, price-target-only changes, general analyst commentary, ambiguous headlines, and duplicate republications. Sum the signed events by issuer to form weekly pressure. A higher signal means more positive analyst pressure. At the next session's open, test the fixed positive sign against the next five-session return. Event date, timestamp, ticker, and prior/new recommendation must be available before formation; no event is not an upgrade or downgrade.

This is a screen definition, not a claim that Alpaca News currently provides all required fields. Alpaca's [Historical News guide](https://docs.alpaca.markets/us/docs/historical-news-data) says articles have a `created_at` timestamp, related `symbols`, a source label, and paging by date and ticker. The [News API reference](https://docs.alpaca.markets/us/v1.1/reference/news-3) documents the historical news endpoint, start/end filters, ticker filter, page limit, and page token. Alpaca's legacy historical-news guide states history is available back to 2015 and is currently sourced from Benzinga ([documentation](https://docs.alpaca.markets/us/v1.1/docs/historical-news-data)). These sources document news metadata, not a normalized historical analyst-ratings table. A separate Benzinga [Analyst Ratings product description](https://www.benzinga.com/apis/cloud-product/analyst-ratings-api/) advertises fields such as action, previous/current rating, price target, analyst, and a 2013 history start; it does **not** establish that those structured fields are returned in Alpaca's News API or that a separate licensed product is included in this account.

The feasibility pull requested only 2024-06-04 ET; no signal or return inputs were queried. API `created_at` is the vendor's article timestamp, not independently verified evidence of when the analyst report first reached all clients. Revisions can be repeated, corrected, summarized, or posted after the underlying report; any later test would need a deterministic rule for repeated broker actions, headline wording, ratings scale, multi-symbol stories, story ID and first-publication time.

- **Verdict:** FAIL as presently observable. Alpaca News does not document the structured action/prior-rating/current-rating fields needed to reliably distinguish true upgrades and downgrades.

## 3. Point-in-time coverage and independent breadth

For a small metadata check, I queried the Alpaca News API separately for AAPL, MSFT, and NVDA for the single New York calendar date 2024-06-04, converted to UTC bounds 2024-06-04 04:00 through 2024-06-05 04:00. Each request used `limit=50`, ascending sort, and `include_content=false`. Each response returned without a next-page token. The three symbol-specific responses had 18, 17, and 32 rows (67 ticker-query rows); after deduplicating by article ID there were 49 unique articles. Every unique article had a `created_at`, a Benzinga source label, and at least one related ticker; the queried ticker was present in all rows returned for its own query. Because stories can tag multiple tickers, the 67 rows are not 67 independent events.

A strict headline keyword scan for upgrade/downgrade verbs found **0** explicit upgrade/downgrade matches among 49 unique articles. A broader screen for recommendation-action language found three candidate headlines, but they were not verifiable as true recommendation changes from normalized fields; they must not be counted as events. Across the 49 unique article timestamps, 19 were pre-open, 26 during regular trading hours, and four after the close. Of the three broad candidate headlines, one timestamp was pre-open and two were during regular hours. In 33 of the 49 rows, `updated_at` differed from `created_at`, so a researcher must distinguish the original item time from later vendor updates. None of these counts uses prices or outcomes.

| Input-only coverage item | Count / result | How obtained and limitation |
|---|---:|---|
| 2024 dates queried | 1 | Fixed 2024-06-04 ET session, explicit API time bounds |
| Requested names | 3 (AAPL, MSFT, NVDA) | Manually fixed sample; not a representative issuer draw |
| Query rows / unique article IDs | 67 / 49 | Three requests; deduplicated by API article ID |
| Returned rows with timestamp, source and related symbols | 49 / 49 | Response metadata only |
| Strict upgrade/downgrade headline hits | 0 | Fixed explicit upgrade/downgrade verb search; does not prove no event exists outside this sample |
| Broad analyst-action headline candidates | 3 | Requires manual/structured validation; not counted as confirmed signals |
| Confirmed nonmissing rating-change signals | 0 in this date sample | No normalized action and prior/current rating fields in these News API results |
| Independent events / SIC2 clusters | 0 confirmed / not estimable | No confirmed rating event; only three sampled names and no SIC join |
| Eligible weekly dates or issuer-week signals | Not established | One date cannot measure development-period completeness |

This one-day sample checks metadata shape and relative timing only. It does not estimate 2024 news coverage rates, all Dow issuer coverage, rating-event precision/recall, or point-in-time completeness over the development window. A ticker may be missing because no story was returned, the vendor omitted it, a company changed identifiers, or the underlying analyst action was published elsewhere or later. The API's related-symbol tag may be updated after publication; `updated_at` differing from `created_at` in many records confirms that timestamp policy must be frozen. Three queried companies represent no useful industry breadth, and no SIC2 cluster count was measured.

- **Verdict:** FAIL. The sample confirms timestamped/tagged news is available, but it does not establish a usable, complete stream of actual rating revisions or independent weekly breadth.

## 4. Effective breadth and power at a sourced plausible effect

### Literature and transport

Womack, [“Do Brokerage Analysts' Recommendations Have Investment Value?” *Journal of Finance* 51 (1996), 137–167](https://doi.org/10.1111/j.1540-6261.1996.tb05205.x), studies 1,573 recommendation changes for 822 US firms over 1989–1991. He reports a mean post-event drift of 2.4% for buy recommendations over one month and −9.1% for sell recommendations over six months; the sign and horizon do not supply a modern weekly cross-sectional rank IC. Loh and Stulz, [“When Are Analyst Recommendation Changes Influential?” *Review of Financial Studies* 24 (2011), 593–627](https://doi.org/10.1093/rfs/hhq094), use 154,134 recommendation changes from 1994–2006 (I/B/E/S, cross-referenced with First Call) and find only 12% meet their definition of influential. Influence is more likely for star/leader analysts and revisions away from consensus, and on growth, small, high-institutional-ownership, or high-dispersion firms. That cautions against treating every rating headline as a comparable pressure shock and weakens transfer to the most-covered Dow firms.

No cited paper reports the rank IC for a five-day Dow signal constructed from Alpaca/Benzinga news headlines, and the historical event-return estimates cannot be converted into that rank IC without additional distribution and event-frequency assumptions. The best defensible effect range for this exact large-cap signal is therefore **unknown**, not a positive number. The older published results are mechanism support, not evidence that this source or effect survives post-2020 in mega-caps.

### Synthetic power sensitivity

For a design-only check, I ran `r4_harness/power_sim.py` with a six-year weekly schedule (312 dates), 30 Dow names, five-session horizon (NW lag 4), signal autocorrelation 0.20, cross-sectional IC SD `1/sqrt(20) = 0.224` as an assumed effective SIC2-cluster noise level, event rate 1.0 eligible issuer event per week, negative-binomial cluster shape 0.5, 10,000 simulations, and seed 20261111. The event rate and effective cluster count are planning assumptions, not estimates from the single-day metadata sample. This simulator uses synthetic date-level IC noise only.

| Synthetic planted mean rank IC | Power for one-sided NW t ≥ 2 | Approximate 80% MDE for t ≥ 2 | Mean effective observations |
|---:|---:|---:|---:|
| 0.020 (sensitivity only) | 21.2% | 0.0422 | 96.0 |
| 0.074 (weekly criterion-4 shape-audit hurdle) | 97.5% | 0.0422 | 96.0 |

The 0.074 value is a portfolio planning threshold from [`CRITERION4_BOUND_BY_SHAPE.md`](../report_drafts/CRITERION4_BOUND_BY_SHAPE.md), not an analyst-rating effect estimate. This synthetic t≥2 test does not implement Holm adjustment. If the R6 family has at least 24 endpoints, the first-step Holm cutoff is `0.05/24 = 0.00208`; a normal-approximation 80% mean-IC hurdle under these same assumed effective observations is about `(2.87 + 0.84) × 0.224 / sqrt(96) = 0.085`, before uncertainty in event coverage or cluster dependence. Thus even the unrelated 0.074 design threshold is below the approximate multiplicity-adjusted 80% threshold in this sparse-event scenario. The actual event rate and plausible rank IC remain unknown.

- **Verdict:** FAIL. Literature does not supply a compatible post-2010 mega-cap effect; at least 24-test multiplicity also pushes the synthetic 80%-power hurdle above the weekly shape threshold under stated sparse-event assumptions.

## 5. Criterion-4 portfolio feasibility first

A fixed candidate portfolio would rank the point-in-time Dow 30 by the preceding week's signed upgrade-minus-downgrade count and hold the rank-weighted top half long-only for the next week. The shape-audit `RankTopHalf` has 55% active share. The benchmark is EW30, with 0.05% cost per side; turnover must remain at or below 50% per rebalance or estimated costs must be below 25% of gross edge. No turnover or cost-to-edge estimate can be credibly derived because the sample produced no confirmed event signals and no gross edge is sourced. The screened shape-audit hurdle is approximately 0.074 weekly rank IC under its own six-year assumptions, while this event-based design has unverified coverage and, in the synthetic sparse-event case, an approximate Holm-adjusted 80% IC hurdle of 0.085.

A strategy would also need positive net excess return, Sharpe above EW30, and a one-sided block-bootstrap result surviving Holm correction. Neither Womack's sample effect nor Loh–Stulz's influential-event classification supplies an estimate for that Dow portfolio or these costs. With only one date sampled for source feasibility, no verified ratings, unknown event rate, and no matching post-2020 mega-cap effect, criterion-4 feasibility is not established. No portfolio outcome was calculated.

- **Verdict:** **FAIL — criterion-4 feasibility unsupported.** Do not register a variant to find out whether the source contains enough actual revisions.

## 6. Holdout availability and protocol

No holdout path or holdout-specific input was needed or accessed. The sealed Dow series and restricted country ETFs remain untouched. A later coordinator-controlled holdout evaluation would require all development gates and a frozen preregistration/independent runner to pass first, then the goal's criterion-5 availability and execution controls; this screen does not request or authorize holdout access.

- **Verdict:** PASS for respecting the holdout rule; no holdout availability claim is made.

## Final screen decision

**Overall: STOP — FAIL.** The research mechanism is credible historically, and the Alpaca API returns timestamped, ticker-tagged Benzinga articles, but the tested endpoint did not expose structured historical recommendation changes. A one-day three-name sample had zero strict upgrade/downgrade headline matches, while its timing/update behavior requires an as-of rule; the historical literature is not a substitute for current Dow effect-size evidence. A permitted normalized rating-action feed or explicit action/prior/current fields, a broader date-filtered input-only sample proving non-sparse issuer-week coverage, and a matched post-2010 large-cap rank-IC estimate could change this decision; none is established here. **Estimated chance of passing all gates if pursued under current evidence: below 1% (judgment, not a measured probability).**

### Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.

**Reviewer:** Round AE screen, 2026-11-11.
