# R6 Idea Screen AJ — secondary equity-supply pressure

**Verdict: STOP — FAIL. Do not register a variant or start a runner.** Secondary equity issuance can create temporary selling pressure, but the public literature located here reports offering discounts and event-window price changes, not a compatible post-2020 mega-cap weekly rank IC. The SEC metadata check confirms that filings can be found with formation-safe date filters, but it does not establish a sufficiently broad, point-in-time panel of eligible Dow equity offerings; the optimistic sparse-event power design also falls well short of the fixed weekly hurdle.

This is screening only. I did not calculate project signals, forward returns, ICs, portfolio returns, or any other signal outcomes, and did not inspect or use holdout data.

## Identity and immutable-path preflight

- **Proposed short name and mechanism:** AJ, new-equity-supply pressure. A large primary secondary offering increases available shares and may create temporary sell-side pressure; if that pressure overshoots, part may reverse after pricing.
- **Exact new output path:** `r6_ideas/AJ_equity_supply.md`.
- **Target preflight:** this exact path did not exist before creation. No existing file was overwritten.
- **Prior-name check:** the decision registry assigns AJ to this secondary-offering / shelf-takedown direction. I found no earlier AJ artifact or identical filed-supply signal in the screened idea files.
- **Development window:** 2020-11-27 through 2026-10-30; earliest permissible worker-path date is **2020-11-27**.
- **Path/date safety:** the SEC searches below carried explicit server-side start and end dates; the seven-issuer subset query was restricted to 2020-11-27 through 2026-10-30. No pre-start project data, holdout path, or sealed values were opened. Only filing-search metadata was used.
- **Verdict:** PASS for target and date-bound preflight.

## 1. Overlap with prior work

The nearest idea families are other dated corporate-event screens, including earnings-announcement signals (`J1`/`R1`), split and attention events (`AC_split_pressure.md`, `AE_retail_bjzz.md`), and generic news or analyst-action pressure (`AB_alpaca_news.md`, `AE_analyst_ratings.md`). Those directions use information/attention events or share-related trading activity. AJ instead uses the quantity of newly issued primary common equity in an underwritten SEO or shelf takedown as a supply shock, and tests the pressure/reversal channel around offer pricing. Secondary resale shares sold by existing holders are not new supply from the issuer and must be excluded or separately classified.

The registry's AJ entry is consistent with this event family; `R5_FINAL.md` and the extant `r6_ideas/*.md` screens did not show an identical 424B-based primary-share supply measure. The SEC form family itself is not novel, and overlap in event-time testing is not evidence for AJ's issuance-supply mechanism.

- **Verdict:** PASS for mechanism-level novelty, subject to the distinction between newly issued shares and resale-only offerings.

## 2. Exact pressure measure and dated data source

### Candidate one-variant signal

For each point-in-time Dow issuer with a final prospectus supplement describing a priced underwritten primary common-stock offering, calculate the offer-session abnormal return: issuer close-to-close return for the first full session after the pricing terms become public, less SPY's return over the same session. The event pressure signal at that session's close is the negative of this abnormal return, so a larger offer-session decline has a larger positive signal; the fixed prediction is a positive return reversal over the following five sessions. Use the public offering terms to exclude resale-only offers, debt/preferred offerings, warrants, ATM sales without a dated takedown, and amendments that do not price a new offer. Within each eligible issuer-week, retain the largest priced primary offering by primary shares divided by shares outstanding in the most recent 10-Q/10-K publicly filed strictly before pricing; ties are resolved by earliest SEC accession. No event is missing, not a zero-pressure signal. The prior offer-session return is signal input, not part of the forward outcome.

An EDGAR accession acceptance time can be after market close, and 424B filing dates need not equal when the offer was priced or first publicly announced. A later implementation would need a verified pricing time and first-public timestamp, then identify the first full session whose close is available at formation; if that cannot be recovered without hindsight, the observation must be excluded. Company CIK/ticker membership and the share-count denominator must also be point-in-time.

SEC [EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) describe the submissions and XBRL data endpoints as public, key-free resources. SEC [Full-Text Search FAQ](https://www.sec.gov/edgar/search/efts-faq.html) documents filing-form selection and custom date filters. The SEC's official [Form 424B5](https://www.sec.gov/files/form424b5.pdf) is a prospectus supplement form, but a 424B5 search hit alone does not prove an issuer sold new common shares: the filing body and offering terms must be classified. The filing search is free; large-scale reproducible access is rate-limited and requires SEC-compliant request identification. No filing body was downloaded for this coverage screen.

### Literature and what it does, and does not, establish

- Corwin, “The Determinants of Underpricing for Seasoned Equity Offers,” *Journal of Finance* (2003), [DOI](https://doi.org/10.1111/1540-6261.00604). The study reports SEO underpricing averaging about 2.2% in its 1980s/1990s sample and relates it to offer size and demand elasticity. This is an offer-price discount result, not a weekly cross-sectional rank IC or post-2020 mega-cap estimate.
- Altınkılıç and Hansen, “Discounting and underpricing in seasoned equity offers,” *Journal of Financial Economics* (2003), [DOI](https://doi.org/10.1016/S0304-405X(03)00114-4). Their offering-level evidence distinguishes discounting from underpricing and describes economically meaningful offer-day price movements. It does not establish a recurrent Dow-stock return rank effect at the proposed horizon.
- Gustafson, “Price Pressure and Overnight Seasoned Equity Offerings,” *Journal of Financial and Quantitative Analysis* (2018), [DOI](https://doi.org/10.1017/S0022109017001181). The paper studies US SEO timing in 2009–2014 and reports a pre-issue price decline for non-overnight offers that reverses within seven days (reported decline about 2.5%). This is the closest cited short-horizon reversal result, but it is conditional on a relatively narrow offering-time subgroup and is not a cross-sectional IC, a post-2020 sample, or proof of a persistent large-cap effect. It is therefore not a numerical estimate for the proposed weekly signal.

- **No outcomes confirmation:** the above are external published results only; no project prices or returns were read or calculated.
- **Verdict:** FAIL for a fully point-in-time signal source until pricing time and eligible primary share count can be reliably classified; PASS only for the conceptual, ex-ante candidate definition.

## 3. Point-in-time coverage and independent breadth

I queried SEC Full-Text Search with an explicit form and server-side date window. The broad discovery query used `q=offer`, `forms=424B5`, `startdt=2024-01-01`, and `enddt=2024-12-31`; SEC reported 3,014 matching filing documents. This is a full-text keyword result count, **not** the number of equity offerings or independent events, and only a capped response sample was returned. Other 424B form searches also returned large counts, demonstrating why form code alone is insufficient.

For a bounded issuer check, I queried the same `q=offer`/`424B5` combination and explicitly restricted dates to 2020-11-27 through 2026-10-30 for seven manually selected current large-cap CIKs: AAPL, MSFT, JPM, GS, IBM, V, and CRM. The response contained five matching filing documents on five dates across a small subset of those issuers. A separate 2024 query for the same CIKs found two matching documents (JPM and GS). The query is metadata-only: no filing body, price, return, or signal was examined. The CIK sample is convenience-selected, uses present-day issuer identities rather than a point-in-time Dow roster, and the keyword restriction means these counts are not a complete search for all offerings.

| Input-only coverage item | Count / result | Method and limitation |
|---|---:|---|
| Broad 2024 SEC 424B5 keyword matches | 3,014 filing documents | `q=offer`, form and 2024 dates applied at SEC query time; not deal/event count |
| Seven-issuer development-window query | 5 documents on 5 dates | `q=offer`, `424B5`, 2020-11-27..2026-10-30 at read time |
| Same seven issuers in 2024 | 2 documents | Same restricted query, 2024 calendar year |
| Names in the sample | 7 manually selected CIKs | Not a PIT roster or representative sample |
| Eligible primary common-stock offers verified | 0 | No document bodies or offering terms were inspected |
| Usable formation dates / issuer-week signals | Not established | Requires pricing-time extraction, full issuer roster, and filing classification |
| Independent eligible offerings / SIC2 clusters | Not established | Search hits cannot identify distinct primary equity transactions or cluster membership |

SEC filing time is public and searchable, but a filing can be amended, filed after pricing, or refer to a resale, debt, preferred stock, or a prior offering. An empty result for a ticker is not evidence of no issuance. Current CIK selection introduces survivorship and membership bias; issuer name/ticker changes and successor CIKs require historical mapping. A complete event panel would need point-in-time Dow membership, SEC accession and pricing timestamps, offer type, primary-vs-resale classification, share count, and lagged shares outstanding. The current metadata check cannot establish independent-event breadth or post-2020 coverage of those fields.

- **Verdict:** FAIL. Metadata-search feasibility is established; the usable event count, independent breadth, and point-in-time signal coverage are not.

## 4. Effective breadth and power at a sourced plausible effect

No cited paper reports a compatible weekly rank IC for Dow-like mega-cap issuers. Gustafson's 2.5% decline/reversal figure is an event-window price move conditional on non-overnight SEO timing in a 2009–2014 sample, not an unconditional rank IC; Corwin and Altınkılıç–Hansen estimate offer discount/underpricing quantities. Converting any of these to a weekly cross-sectional IC would be unsupported, so there is **no sourced plausible rank-IC effect** to claim. The 2.5% event figure is shown only to clarify this mismatch, not used as a planted IC.

For a transparent optimistic design check, I used the synthetic-only `r4_harness/power_sim.py` with 30 assets, 312 weekly dates (six years), five-session horizon/NW lag 4, signal autocorrelation 0.2, 10,000 simulations, and seed 20261111. To approximate event sparsity only, I set the expected event rate to 0.07 issuer-events per week: this is an extrapolation of five keyword-matched filings from a convenience sample of seven issuers over roughly six years, scaled linearly to 30 names, while optimistically treating every match as a valid independent primary equity offering. It is not a measured offering rate; real classification and clustering can only reduce effective breadth. I set the planted effect to 0.074 solely as the lowest weekly rank-weighted-top-half planning hurdle from `report_drafts/CRITERION4_BOUND_BY_SHAPE.md` at its rho=0.2 scenario. This is a design comparison, not an empirical effect estimate.

The synthetic event simulation returned:

| Planning quantity | Result |
|---|---:|
| Mean active event dates | 19.80 of 312 weekly dates |
| Mean event count | 21.86 over six years |
| Effective event-date observations | 14.40 mean; 14.55 median |
| Power at assumed effect 0.074 for one-sided NW t ≥ 2 | 48.1% (Monte Carlo SE 0.0050) |
| 80%-power minimum detectable effect for NW t ≥ 2 | 0.132 |
| Test simulated | NW t ≥ 2, lag 4; **not** Holm-adjusted block-bootstrap criterion 4 |

This is already below 80% power at the optimistic planning effect, before Holm correction across the currently growing R6 family (about 24 endpoints) or the block bootstrap. Its actual power for the stricter first-step Holm cutoff is lower. The MDE 0.132 is not a source-based expected effect. Event-level correlation, duplicate filings, deal clustering, and imperfect SIC breadth would worsen precision.

- **Verdict:** FAIL. There is no signal-matched, large-cap effect estimate, and sparse event breadth is underpowered even against the optimistic 0.074 planning hurdle.

## 5. Criterion-4 portfolio feasibility first

If this direction were ever reconsidered, the least concentrated eligible candidate would be the weekly rank-weighted top-half long-only portfolio (top 15 names, weights proportional to ranks 1 through 15; active share 55%), benchmarked against EW30, with 0.05% per-side costs and the goal's block-bootstrap/Holm test. The six-year planning table gives this shape a weekly 80%-power threshold of rank IC 0.074 at rho=0.2 (and 0.083 at rho=0.5); modelled total-notional turnover is 116% or 91% per rebalance, respectively. Those turnover values exceed the 50% cap, but modeled annual costs are 24.1% or 16.7% of gross active edge, meeting the alternative cost condition **only if** the assumed edge exists. The threshold uses the conservative first-step Holm approximation for a 24-test family and synthetic Dow-like dispersion/correlation assumptions, not actual Dow results.

The best directly related sourced number is an approximately 2.5% short pre-issue decline and reversal within seven days for a conditional 2009–2014 SEO subgroup. It cannot be translated into weekly rank IC or portfolio excess Sharpe without event frequency, cross-sectional dispersion, and the unconditional post-offer response; it is not a defensible interval that can be compared as if it were the 0.074–0.083 IC hurdle. The SEC sample and event-mode simulation indicate sparse breadth, not a portfolio-level edge. A portfolio forecast would therefore be fabricated, so I do not supply one.

The goal remains unchanged: positive net excess return and higher Sharpe than EW30, with one-sided block-bootstrap p < 0.05 after Holm across all registered family endpoints, plus the turnover/cost condition and DSR at the cumulative trial count. The literature and input check do not establish a plausible effect large enough to clear that gate.

- **Verdict:** FAIL — criterion-4 feasibility is unsupported; do not commission a portfolio run.

## 6. Holdout availability and protocol

No holdout-specific input is needed for this screen, and no sealed holdout data were accessed. This screen does not establish holdout availability. Any later holdout work must follow goal criterion 5 only after a direction passes all development gates, receives a frozen preregistration, and the coordinator controls the single holdout execution. Workers must not inspect, download, or calculate on sealed values; only the designated availability-only check permitted by the project rules may establish whether the required holdout data exist.

- **Verdict:** PASS for this screen's no-holdout-data rule; holdout availability remains unverified.

## Final screen decision

**Overall: STOP — FAIL.** Novelty and the availability of free, date-filtered EDGAR search pass at a conceptual level. The binding failures are the lack of a verified eligible primary-offer panel and point-in-time pricing timestamps, no compatible independently documented large-cap weekly IC, and insufficient sparse-event power against the fixed criterion-4 hurdle. No preregistration, runner, or variant is authorized by this screen.

Evidence that could change the decision would include a date-filtered, point-in-time Dow panel of classified primary common-stock offerings with confirmed pricing timestamps and lagged share denominators, plus independent post-2020 mega-cap research reporting a compatible effect and enough independent event breadth to clear the Holm-adjusted portfolio hurdle after costs.

**Reviewer/date:** dispatched worker screen, 2026-11-11.

## Sources

- SEC, [EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).
- SEC, [EDGAR Full-Text Search FAQ](https://www.sec.gov/edgar/search/efts-faq.html).
- SEC, [Form 424B5](https://www.sec.gov/files/form424b5.pdf).
- Corwin (2003), [“The Determinants of Underpricing for Seasoned Equity Offers”](https://doi.org/10.1111/1540-6261.00604).
- Altınkılıç & Hansen (2003), [“Discounting and underpricing in seasoned equity offers”](https://doi.org/10.1016/S0304-405X(03)00114-4).
- Gustafson (2018), [“Price Pressure and Overnight Seasoned Equity Offerings”](https://doi.org/10.1017/S0022109017001181).
- Project planning hurdle: [`CRITERION4_BOUND_BY_SHAPE.md`](../report_drafts/CRITERION4_BOUND_BY_SHAPE.md); synthetic design tool: [`power_sim.py`](../r4_harness/power_sim.py).

## Proposed replacement wording for the Task-spec brief contract in `ORCHESTRATION.md`

> **Idea screening and file safety.** Before any signal pull or preregistration, complete `specs/IDEA_SCREEN_TEMPLATE.md`. The screen must establish novelty, exact signal and source, point-in-time coverage and independent breadth, power at an independently sourced plausible effect, criterion-4 portfolio feasibility after costs and Holm adjustment, and holdout availability. A failed gate ends the work; do not start a runner or register a variant. Task specs must name exact output paths using forward slashes and must say to check that each path does not exist before writing; never overwrite or reuse an existing artifact name. Worker data paths must begin no earlier than 2020-11-27. Do not inspect outcomes during screening or access sealed holdout values. If a path, date, or data rule is ambiguous, stop and request coordinator review before any pull.
