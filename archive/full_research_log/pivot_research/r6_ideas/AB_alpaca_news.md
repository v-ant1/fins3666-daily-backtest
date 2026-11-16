# R6 idea screen: Alpaca ticker-tagged news pressure

**Status: SCREEN ONLY — no signal outcomes, no return calculations, and no variant is authorized.** This screen uses only the bounded 2024 news metadata sample in `r6_data/alpaca/news_2024.json`; it does not inspect article titles or content, request any price data, or access holdout data.

## Identity and immutable-path preflight

- **Proposed short name:** AB-AlpacaNews.
- **Mechanism:** issuer-tagged news may create temporary, stock-specific investor attention and one-sided demand; the API's related-symbol labels improve attribution relative to broad news feeds, but do not identify who traded or the direction of order flow.
- **Exact new output path:** `r6_ideas/AB_alpaca_news.md`.
- **Path check:** the target did not exist before this screen. `AB_alpaca_news` is not an existing filename in `r6_ideas`; the two candidate concepts themselves overlap prior work as discussed below.
- **Development dates:** the only sample is 2024-06-03 through 2024-06-05. Earliest permissible worker-path date is **2020-11-27**. No worker input or output path used here refers to earlier market data, a holdout folder, or another date range. The sample request asks only for news metadata and has no prices or outcomes.
- **Credential handling:** no API key was read or printed; no new API pull was required.
- **Preflight verdict: PASS.**

## 1. Overlap with prior work

The closest prior screen is [`Y_news.md`](Y_news.md), which proposed (i) negative news tone followed by reversal and (ii) abnormal news volume as an attention proxy. Its data source was GDELT, where company-name matching was ambiguous. This screen replaces that matching step with Alpaca's `symbols` tags and `created_at` timestamps. That improves the *measurement and timing route*, but does not create a distinct economic mechanism: the first proposal is still news-tone reversal, and the second is still news-volume attention.

Other relevant overlaps are `P3.md` (attention-driven demand/reversal), `B4_REVISED.md` (news co-mention network), and the earnings/news-event family in `V_recent_lit.md` and `W_events.md`. Neither candidate below uses a co-mention graph or an earnings calendar; however, that difference is not enough to make generic news attention novel. News volume may also proxy for fundamental information, and the timestamped ticker tag alone does not separate the two.

**Gate 1 — FAIL.** Both candidates substantially repeat the signal family screened in Y. A source change from GDELT to Alpaca is useful for data quality, but is not sufficient novelty under the R6 rules.

## 2. Exact pressure measures and dated data source

Alpaca's [Historical News documentation](https://docs.alpaca.markets/us/v1.1/docs/historical-news-data) states that its historical feed goes back to 2015 and is sourced from Benzinga. The [News API reference](https://docs.alpaca.markets/us/reference/news-3) exposes article timestamps, related symbols, and start/end filters; the [current news guide](https://docs.alpaca.markets/us/docs/historical-news-data) describes the returned article fields. This gives the vendor a development-period history, but the 2015 start means it cannot cover 2010–2014. No query outside the permitted development window was made in this screen.

### Candidate 1 — prior-week negative headline tone as selling pressure, then reversal

For each S&P 500 issuer at Friday formation, define a headline tone score for every article whose `created_at` timestamp is strictly before that formation close and whose exact ticker appears in `symbols`. A future preregistration would need to freeze one text source (headline only), one dictionary/model, and one treatment of multi-ticker stories before looking at outcomes. One possible fixed dictionary score is `(positive-word count − negative-word count) / headline word count`; define the weekly signal as the negative of the mean score across the preceding five completed sessions, with a minimum article count. Higher values mean more negative prior-week tone. The proposed sign is **positive** for the next five-session return, as a reversal of hypothesized attention-driven selling pressure.

This proposal is only operationally complete after the dictionary, minimum count, duplicate-story rule and multi-symbol weighting are frozen. The 2024 sample deliberately did not inspect headline text or validate any sentiment score.

### Candidate 2 — issuer-specific news-volume surprise as buying attention

At Friday formation, count articles with `created_at` strictly before close and an exact ticker in `symbols` during the last five completed sessions. Compare the count to that issuer's prior 60 completed sessions using `log((1 + count_5) / (1 + 5 * count_60 / 60))`. The proposed sign is **positive** for the next five-session return: unusually high issuer-specific news attention is hypothesized to draw attention-sensitive purchases that persist briefly. The exact ticker-tag requirement and the fixed 5/60-session windows would be part of the candidate definition; no count was calculated from market or outcome data here.

Alpaca's returned `created_at` is the API timestamp used for admissibility; it should not be assumed to be a verified original-publication timestamp. Articles tagged to many symbols can create incidental attribution. Any later use would need a fixed rule for one story tagging multiple names, syndicated duplicates, and articles whose tags are broad market or ETF symbols.

**No signal outcome was calculated.** Neither a tone score, signal value, forward return, rank IC, portfolio return, nor relationship between a news record and a price was computed.

**Gate 2 — partial / FAIL.** A timestamped, symbol-tagged source exists during the permitted dates, but exact issuer relevance, the sentiment model, duplicate handling, and point-in-time tag quality are not established by the metadata sample.

## 3. Point-in-time coverage and independent breadth

The staged request metadata records `symbols=AAPL,MSFT,DIA`, a request window of 2024-06-03 through 2024-06-05 UTC, `limit=5`, and `include_content=false`. The first page contains **5 articles**, all **5** with a `created_at` date of 2024-06-05, all **5** with at least one related-symbol tag, and all sourced to Benzinga. The requested stock tags include AAPL and MSFT; DIA is an ETF. The five returned rows therefore establish only **2 requested Dow stock names observed** in this tiny first-page response. They are not a complete Dow article count, and the first-page cap prevents inferring three-day volume or daily issuer coverage.

| Input-only coverage item | Count / result | Interpretation |
|---|---:|---|
| Calendar dates requested | 3 | Request bounds only; not three observed coverage dates. |
| Dates represented in returned first page | 1 | All five returned records are dated 2024-06-05. |
| Returned article rows | 5 | Limited by `limit=5`; not a complete pull. |
| Rows with timestamp / related-symbol tags | 5 / 5 | Schema usability for these five rows only. |
| Requested Dow names represented | 2 of 2 (AAPL, MSFT) | This is not a universe coverage estimate. |
| Independent article events | Not established | No text-level deduplication or event classification was done. |
| Independent SIC2 clusters | Not measurable from this sample | No broad issuer panel was requested or joined to a classification file. |
| Usable weekly dates / nonmissing issuer signals | Not established | Would require complete, paginated issuer-level pulls and a frozen eligibility rule. |

The source provides news as far back as 2015 per Alpaca documentation, so historical availability covers the development window in principle. The small sample does **not** establish complete date coverage, article relevance, broad Dow coverage, industry breadth, or stable weekly issuer counts. Firms changing names/tickers, multiple share classes, tags added after publication, vendor selection, and Benzinga's own source mix can all create survivorship or timing errors. A strict as-of timestamp avoids including later API records, but does not prove the tag itself was known at the formation time.

Literature coverage does not close these gaps. Tetlock's sample is a Wall Street Journal market-commentary series, not Alpaca ticker-tagged firm news; Fang and Peress study long-run media coverage rather than weekly news shocks; Ahmad et al. study historical news tone for a small set of large firms, not the proposed modern Dow signal. No cited study establishes the coverage or SIC2 breadth of this exact API measure.

**Gate 3 — FAIL.** Five capped first-page records are a schema check, not adequate independent coverage or breadth evidence.

## 4. Effective breadth and power at a sourced plausible effect

The literature below does not report a large-cap, post-2010, next-week rank IC for either exact Alpaca measure. Therefore there is **no defensible sourced plausible effect size** to use as the template requires. For scale only, I ran the repository's synthetic `r4_harness/power_sim.py` using assumptions of 500 names, 312 weekly observations (six years), five-session horizon / Newey–West lag 4, cross-sectional null IC SD `1/sqrt(499)`, signal autocorrelation 0.20, 5,000 simulations, seed 20261111:

| Synthetic planted mean IC | Nominal `NW t ≥ 2` power | 80% MDE | Mean effective observations |
|---:|---:|---:|---:|
| 0.020 (assumption only) | 1.000 | 0.00844 | 226.90 |
| 0.074 (criterion-4 planning hurdle) | 1.000 | 0.00844 | 226.90 |

These are simulations of date-wise IC noise, **not** power at a published Alpaca-news effect. `power_sim.py` does not model SIC2 cluster dependence, sparse issuer coverage, story duplication, text-model error, or the Holm correction. The effective count reflects only its AR(1) assumption. Since the articles could be driven by shared events and industries, actual effective breadth may be materially smaller. Neither the papers nor the sample support choosing 0.020 (or any other positive number) as a plausible signal effect. The mechanism gate therefore cannot pass on this synthetic output.

**Gate 4 — FAIL.** A sourced effect matched to the signal, horizon and large-cap setting is absent; the simulation only shows that a hypothetical planted mean can be detected under simplified assumptions.

## 5. Criterion-4 portfolio feasibility first

The fixed planning benchmark requested for this screen is the [criterion-4 bound by shape](../report_drafts/CRITERION4_BOUND_BY_SHAPE.md): approximately **0.074 weekly rank IC** for a rank-weighted long-only top-half portfolio under the stated planning assumptions. This is a feasibility hurdle, not an observed project effect. Use the goal's Dow long-only portfolio, top-half rank-weighted, with active share at least 50%, weekly rebalancing, EW30 benchmark, 0.05% cost per side, and turnover no more than 50% or costs below 25% of gross edge; criterion-4 inference must retain the one-sided block bootstrap and Holm family rather than weakening the goal.

Neither candidate has a published effect range that can be converted into portfolio excess return, Sharpe, or net edge. Tetlock's market-level sentiment finding does not supply an issuer rank IC. Fang–Peress's coverage premium is strongest among small and neglected firms and is not a five-session shock effect. Ahmad et al.'s historical tone study and Heston–Sinha's short-lived daily news predictability do not provide the required post-2020 Dow weekly coefficient or a large-cap, long-only top-half effect estimate. No paper justifies claiming that Alpaca attribution can lift either signal to 0.074. The costs and turnover caps are stated, but without a sourced gross edge the cost hurdle cannot be evaluated as met.

**Gate 5 — FAIL: criterion-4 feasibility not established.** The best defensible effect bound for these exact measures is unknown, not 0.074; do not commission a portfolio variant to discover it.

## 6. Holdout availability and protocol

This screen used no holdout path or holdout-specific input and did not read, query, download, or calculate on sealed values. Alpaca's documented 2015 start would leave 2010–2014 unavailable even if later coordinator-controlled research were authorized; technical availability never authorizes access. Any later holdout evaluation would require coordinator approval under goal criterion 5 after all development gates pass, with the specified sealed-holdout controls. This failed screen does not request such access.

**Gate 6 — PASS for screen discipline only.** No holdout data were needed or used.

## Final screen decision

| Candidate | 1 Novelty | 2 Measure/source | 3 Coverage/breadth | 4 Sourced-effect power | 5 Criterion-4 feasibility | Overall |
|---|---|---|---|---|---|---|
| Negative prior-week headline tone, next-week reversal | Fail: repeats Y tone-reversal family | Partial | Fail | Fail | Fail | **STOP — FAIL** |
| Abnormal tagged-news volume, next-week attention drift | Fail: repeats Y news-volume attention family | Partial | Fail | Fail | Fail | **STOP — FAIL** |

**Overall: STOP — FAIL.** Alpaca's ticker tags and timestamps address a real weakness in GDELT matching, but this 2024 sample is too small to establish issuer coverage, and better attribution alone neither supplies evidence of buying pressure nor differentiates the proposed mechanisms from the prior news screens. There is no published effect matching the required weekly large-cap design, and no basis for reaching the approximate 0.074 IC planning hurdle after costs and Holm adjustment.

Evidence that could change the decision: an outcome-free, complete paginated development-window coverage audit with point-in-time ticker-map and event-deduplication checks; an independently sourced post-2010 mega-cap effect at the proposed horizon; and a novel pressure mechanism that is not simply tone or story volume followed by return reversal. Any such follow-up needs coordinator review before variant registration.

**Reviewer/date:** dispatched worker screen, 2026-11-11.

## Sources

- Tetlock (2007), [“Giving Content to Investor Sentiment: The Role of Media in the Stock Market,” *Journal of Finance*](https://doi.org/10.1111/j.1540-6261.2007.01232.x). Wall Street Journal market-commentary tone; its market-level results do not establish the proposed ticker-specific weekly IC.
- Fang & Peress (2009), [“Media Coverage and the Cross-section of Stock Returns,” *Journal of Finance*](https://doi.org/10.1111/j.1540-6261.2009.01493.x). Coverage premium concentrated among less-followed/smaller firms; not a news-shock pressure estimate.
- Ahmad, Han, Hutson, Kearney & Liu (2016), [“Media-expressed negative tone and firm-level stock returns,” *Journal of Corporate Finance*](https://doi.org/10.1016/j.jcorpfin.2015.12.014). Historical news-tone study of large US firms; it does not estimate this Alpaca weekly signal.
- Heston & Sinha (2016), [“News versus Sentiment: Predicting Stock Returns from News Stories,” Federal Reserve FEDS](https://www.federalreserve.gov/econres/feds/news-versus-sentiment-predicting-stock-returns-from-news-stories.htm). Short-lived news-based predictability is not evidence of the specified weekly Dow rank IC.
- Alpaca, [Historical News Data](https://docs.alpaca.markets/us/v1.1/docs/historical-news-data) and [News API reference](https://docs.alpaca.markets/us/reference/news-3).
- Project synthetic hurdle: [`CRITERION4_BOUND_BY_SHAPE.md`](../report_drafts/CRITERION4_BOUND_BY_SHAPE.md); synthetic diagnostic: [`power_sim.py`](../r4_harness/power_sim.py).

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
