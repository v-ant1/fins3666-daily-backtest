# S&P 500 addition announcement-to-effective CAR — DEV

**Tag:** L-ADDS. **Decision:** S2 exhausted; no preregistration drafted. This is development evidence only. No pre-2020-11-27 price/return data or sealed holdout files were accessed.

## Definition

Events are roster S&P 500 additions with a dated public S&P DJI announcement from 2020-11-27 through 2026-10-30 and an effective date by 2026-10-30. Entry is the next trading session's open after the announcement date; exit is the effective-date close. The stock holding return uses direct Alpaca SIP daily bars with `adjustment=all`, fetched by symbol. The benchmark compounds daily equal-weight returns for PIT S&P members from `r9/data/J2_DEV_FROM_20201127.npz` over the same sessions. Event CAR is the stock holding return minus the benchmark holding return. Costs subtract twice the one-way rate.

The roster now has `announcement_date` and `announcement_source_url` fields. It contains 103 dated, eligible official S&P source events; CEG's mismatched link was corrected to the [2022-01-26 S&P release](https://press.spglobal.com/2022-01-26-Constellation-Energy-Set-to-Join-S-P-500-Others-to-Join-S-P-MidCap-400-and-S-P-SmallCap-600). Ten events lacked a direct entry or effective-date bar and were excluded; all fetches returned without API errors. The measured sample is **N=93**.

## Results

| Statistic | Result |
|---|---:|
| Mean gross CAR | **1.19%** |
| Cross-event sample SD | **7.74%** |
| Median CAR | **0.61%** |
| 95% Student-t CI for mean | **−0.40% to +2.79%** |
| Holding sessions | **7.2 mean; 6 median; range 2–11** |
| Mean CAR after 5 bp one-way cost (10 bp round trip) | **1.09%** |
| Mean CAR after 10 bp one-way cost (20 bp round trip) | **0.99%** |
| Mean CAR after 20 bp one-way cost (40 bp round trip) | **0.79%** |

The holdout planning MDE is `2.970 × 7.74% / √96 = 2.35%`. The primary 5 bp one-way net mean (**1.09%**) is below that MDE, so the registered decision rule says to stop S2 as exhausted. No holdout analysis or preregistration was authorized by this result.

## Trial accounting

L-ADDS-01 was registered before the data fetch and completed in one attempt. Its full definition and the result entry are in `specs/r9_variant_log_S2.md`; the tagged decision is in `specs/r9_decisions.md`. Supporting per-event output is `r9/S2_INDEX_ADD_DEV_results.json`.
