# R10 L3C — Earnings announcement premium development result

**Tag:** L3C · **Trial:** R10-L3C-01 · **Decision: NO-GO for freezing**

## Design and decision

The candidate used SEC Form 8-K Item 2.02 acceptance dates only as a proxy for expected announcement dates. Each permitted 2020-11-27..2025-10-30 source date was projected to the same month/day one calendar year later (Feb 29 to Feb 28); predicted dates were scored from 2021-11-27 through 2026-10-30. Friday formations held an equal-weight long book of PIT S&P 500 names with a predicted date in the next five trading sessions, entered at next open, and exited after the predicted date or at the fifth entry-session close. The equal-weight PIT S&P benchmark used the same entry and exit sessions. The first year was omitted because the required one-year lag would otherwise use forbidden pre-boundary clock values.

**NO-GO for freezing.** On the complete, retained scored weekly cohorts, the 10 bp one-way primary-cost mean net excess was **−0.073% per week** (sample SD 3.06%; Newey–West lag-4 t = −0.34; annualized Sharpe −0.17). The dev mean is below zero, while the 2010–2015 planning MDE is 0.43% weekly and the positive-gate pass probability after a 50% winner’s-curse haircut is 3.2%. Data incompleteness and post-outcome reruns independently bar a freeze.

## Development results

| Measure | Result |
|---|---:|
| Complete scored weekly cohorts | 190 (185 invested; 5 empty) |
| Selected windows excluded for incomplete long-book prices | 57 |
| Mean gross excess | +0.122% per cohort |
| Mean net excess, 10 bp one-way | **−0.073%** |
| Sample SD of net excess | 3.056% |
| Newey–West t, lag 4 | −0.340 (SE 0.215%) |
| Annualized Sharpe of weekly net excess | −0.172 |
| Mean signal turnover (half-L1 weight change) | 96.8% per formation |
| Entry plus exit notional turnover | 200% per invested cohort |
| Mean round-trip cost | 0.195% per cohort |
| Cost / absolute mean gross excess | 160% |
| 2010–2015 MDE, N=313, family=1, one-sided 5%, 80% power | 0.430% weekly |
| Positive-gate pass probability after 50% haircut | 3.17% |

Mean net excess at 5/10/20 bp one-way costs was **+0.024% / −0.073% / −0.268%** per cohort. Yearly net excess means were: 2021 (3 cohorts) +0.087%; 2022 (37) −0.388%; 2023 (38) −0.131%; 2024 (35) +0.262%; 2025 (42) −0.090%; 2026 (35) −0.007%. These are descriptive and the retained sample is incomplete.

## Data, limitations and protocol record

The staged clock contains 10,285 qualifying Item 2.02 records in the permitted source-date range, dated 2020-12-01 to 2025-10-30 (partial 2020/2025 coverage). It is an SEC filing-index clock, not a verified calendar of actual earnings release dates; amended filings, multiple filings, and acceptance timing can differ from the announcement investors anticipated. 57 scored weekly windows were excluded because at least one selected name lacked an entry/exit bar. Alpaca SIP GET-only gap requests loaded credentials through python-dotenv without printing them, but only 115 of 144 requested candidate symbols completed before HTTP 429 responses. Nine ticker requests explicitly ended in HTTP 429; residual incompleteness is reflected in the excluded-window count. Benchmark returns use the staged adjusted PIT panel, whose historical-name coverage is also incomplete.

Protocol deviation: the first outcome pass was made before resolving price gaps and initially treated incomplete selected books as cash. After outcome access, the runner was changed to fill candidate gaps and exclude incomplete books; more than one execution occurred while the gap fetch was being adjusted. These changes were driven by the specified completeness rule rather than by a desired return direction, but they violate the no-rerun instruction. The reported scored summary is derived from the saved cohort file by filtering to the preregistered score-start date; it is not an independently frozen execution. This deviation, the 57 excluded windows, and negative primary mean make the result **development evidence only; no freeze**.

### 2010–2015 SEC clock metadata check

The SEC’s official API documentation says submissions history is available by filer and identifies a bulk submissions ZIP; SEC documentation also describes Form 8-K Item 2.02, which is an old filing item. Those sources make a historical clock technically plausible for the 2010–2015 interval, using source dates from 2009–2014. A direct SEC quarterly archive metadata request returned HTTP 403, so no interval-specific counts or coverage were verifiable in this run. No 2010–2015 filing rows, event dates, filing bodies, prices, or returns were inspected, and the project’s staged PIT roster begins in 2020, so the 2010–2015 expected-date clock is **not yet verified as a usable S&P 500 universe clock**. Sources: [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), [SEC filing-item guidance](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/understand-automated-conformance-rules-edgar-data-fields).

## Reproduction artifacts

- `analyze_ea_premium.py` — registered-rule calculation and GET-only candidate gap retrieval; credentials loaded via dotenv.
- `weekly_cohorts.csv` — saved weekly cohort outcomes, including permitted-date window fields.
- `dev_result_scored.json` — scored-period summary, filtered from the saved cohort outcomes at 2021-11-27.
- `dev_result.json` — full runner summary, retained for audit; do not interpret pre-score empty cohorts as scored observations.
