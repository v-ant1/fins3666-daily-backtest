# R10 S2B — SEC filing/event pressure screen

**Run status:** completed under the coordinator's capacity direction. No candidate is GO. The copied S2B harness passed synthetic validation before S2-02 outcomes were accessed; the six registered definitions were not changed.

## Development results

All returns use only the development panel from 2020-11-27 through 2026-10-30 and compare the event book with the equal-weight PIT S&P 500 benchmark on the same 20-session window. Primary costs are 10 bp one-way at entry and exit.

| ID | Usable cohorts | Net excess mean | NW t (lag 3) | Net Sharpe vs EW PIT S&P | Half-L1 turnover / entry-exit notional | Cost share of abs. gross excess | By-year net signs | 2010–2015 MDE / haircut pass probability | Decision |
|---|---:|---:|---:|---:|---|---:|---|---|---|
| S2-01 | — | Not measured | — | — | — | — | — | — | Data-gated |
| S2-02 | 15 | **−0.58%** | **−0.52** | **−0.41** | 0.90 / 2.00× | 53.0% | 2021 +; 2022 +; 2023 −; 2024 −; 2025 −; 2026 − (2/6 years positive) | **3.10%** / **3.0%** (projected N=15) | **NO GO** |
| S2-03 | — | Not measured | — | — | — | — | — | — | Data-gated |
| S2-04 | — | Not measured | — | — | — | — | — | — | **Data-gated; counted trial** |
| S2-05 | — | Not measured | — | — | — | — | — | — | Data-gated |
| S2-06 | — | Not measured | — | — | — | — | — | — | Data-gated |

S2-02's net mean is −0.5772% per usable 20-session cohort, with a gross excess mean of −0.3772%. The 53.0% cost share uses the fixed 20 bp round-trip cost divided by the absolute gross excess mean. Annual net excess means were +3.35% (N=1) in 2021, +0.97% (N=4) in 2022, −1.50% (N=1) in 2023, −2.71% (N=3) in 2024, −1.05% (N=4) in 2025, and −1.01% (N=2) in 2026.

The per-idea 2010–2015 planning estimate uses family=1, one-sided alpha=.05, 80% power, and the registered projected sample size: the 15 usable development cohorts averaged over six observed calendar years and scaled by six. The MDE is 2.4865 × development net-excess SD / √15; pass probability uses the 50%-haircut net mean and the same projected standard error. This estimate is not full qualification probability.

S2-02 fails each GO condition: net excess is not positive, NW t is below 2, and haircut pass probability is below 30%.

## Data gates and trial accounting

- **S2-01, S2-03, S2-05, S2-06:** Filing-body classification is required by the frozen definitions. The coordinator directed stopping the full EDGAR filing-body census at the source-capacity gate; no returns were calculated for these ideas. They remain registered and counted, with no outcome estimate.
- **S2-04:** The staged PIT roster has 107 distinct tickers with date-encoded S&P Global/S&P DJI end-source URLs among 615 rows whose membership ends fall in the development window (one additional row has an S&P-hosted URL without a date in the URL). This is not a complete verified deletion census, so S2-04 is data-gated and remains counted; no return estimate was produced. The provided roster metadata was used; no pre-boundary or sealed data was read.
- A few pre-outcome dev-window filing-body batches were stopped before a complete census. They produced no complete event list or strategy outcome.
- **S2-02:** SEC companyfacts was fetched for 606 mapped issuers with development-window 10-Q/K metadata, with zero fetch failures; repurchase facts were available only for issuers reporting the relevant tags. After requiring a prior comparable report and prior-quarter shares outstanding, applying PIT membership and selecting the top quintile, 200 issuer-months across 52 cohorts entered the fixed event list. Complete-price rules left 15 usable cohorts.

The development price panel had 31,648 roster-active open gaps and 31,648 close gaps before backfill. Alpaca SIP `adjustment=all` GETs were throttled; 49 symbols were requested and 76,792 missing price fields were filled. Forty-one open and 41 close roster-active fields still had no returned bars. The complete-benchmark rule was enforced, which reduced S2-02 to 15 usable cohorts.

All six S2 definitions remain one counted hypothesis each. S2-02 was scored once. S2-04 was recorded as a counted data-gated trial. S2-01, S2-03, S2-05 and S2-06 were not outcome-scored under the coordinator's instruction to stop the full body census. No orders were placed and no sealed holdout was opened.

## Reproducibility artifacts

- Harness: `r10/S2B/event_harness.py`
- Synthetic-only validation: `r10/S2B/SYNTHETIC_VALIDATION.json`
- SEC/companyfacts and gap preparation: `r10/S2B/prepare_s2_02.py`, `r10/S2B/PREPARED_S2_02.json`
- Fixed event list: `r10/S2B/S2_02_EVENTS.json`
- Single development scoring invocation: `r10/S2B/execute_s2_02.py`
- Metrics: `r10/S2B/DEV_RESULTS.json`
- Development-only input/output price panel: `r10/S2B/dev_panel_prices.npz`
- Development-window SEC submissions metadata cache: `r10/S2B/sec_dev_filing_metadata.json`
