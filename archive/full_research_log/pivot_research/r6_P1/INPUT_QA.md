# P1 trailing overnight-momentum input QA

This is an input-only signal build. It contains no forward returns, ICs, mechanism test, or portfolio outcomes.

## Fixed construction

At each calendar month-end, the formation date is the final observed market session in that month. The signal is the compounded overnight return over the 21 observed market sessions ending on formation: `product(open_adj[t] / close_adj[t-1]) - 1`. Adjusted open is reconstructed as raw open × adjusted close / raw close. The input history is clipped at 2020-06-01; a signal is valid only when all 21 overnight observations and their adjacent-session price bars are present. No missing observations are carried or interpolated.

## Coverage by formation

`coverage_by_formation.csv` reports PIT membership, current formation-date bars, valid 21-session signals, dated SIC2 labels, and joint eligible names. The 250-name gate is based on PIT members with a valid signal; SIC2 availability and joint signal-plus-SIC2 coverage are reported separately. The Dow's 30-name universe is descriptive and is not expected to meet the S&P-scale threshold.

| Universe | Formation dates | Min PIT members | Min formation bars | Min valid signals | Min joint signal + SIC2 | Dates ≥250 valid signals | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| DOW | 70 | 30 | 29 | 29 | 29 | 0/70 | N/A |
| SP500 | 70 | 503 | 462 | 460 | 454 | 70/70 | PASS |

## Inputs and limitations

S&P 500 bars come from `r6_data/sp500_ohlcv_dev_gapfilled.parquet`; the dated constituent intervals are from `r6_data/sp500_pit_roster.csv`. Dow bars are combined from the existing daily/lookback files and `r6_data/dow_dev_gapfill.parquet`; the Dow PIT roster is `r6_D1/dow_pit_roster.csv`. SIC2 is assigned from the latest SEC SIC-panel effective date not after formation (`r6_data/sp500_sic_panel.csv` for S&P 500; `r4_L4/data/sic_panel.csv` for Dow). Historical SIC metadata can predate June 2020 because it establishes the contemporaneous classification at the cutoff; it is not price, return, or outcome data. Price records before 2020-06-01 are discarded before parsing, and no pre-cutoff prices enter return construction.

The output has 37,345 PIT member-formation rows across 70 month-end dates and both universes. The signal parquet is long-form and retains explicit member, bar, signal, SIC2, and eligibility masks for auditability.

## Rebuild

Run `python r6_P1/build_inputs.py` from the project root.
The hashed input-only manifest is `INPUT_MANIFEST.json`; it pins the signal bundle, daily price bundle, and per-formation coverage table before the guarded runner may construct forward labels.
