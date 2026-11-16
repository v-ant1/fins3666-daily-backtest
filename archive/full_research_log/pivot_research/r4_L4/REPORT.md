# L4 data scouting and holdout feasibility

## Findings

- The strongest immediately usable network data are SEC 13F filings (quarterly, delayed) and issuer ETF holdings (current daily, but historical daily files are not assured). SEC N-PORT offers lagged monthly holdings from October 2019. Intraday data cannot be obtained free across the full 2020–2026 development period from yfinance's rolling retention, Alpha Vantage's premium intraday history, or Massive/Polygon's two-year free window. FactSet/Compustat may be available through UNSW, but student access to the relevant Supply Chain/Segments modules needs confirmation.
- The free Yahoo availability scan covers 37 of 40 security/lineage membership windows by dates and OHLCV field schema. KFT, DWDP, and WBA have no Yahoo legacy-symbol chart result; UTX uses RTX as a lineage proxy. This makes the holdout **partially feasible** pending an approved licensed/archived source or a user-approved substitute.
- A historical DWDP page rendered quote rows during source verification. The coordinator was notified and ruled the DWDP window must be reported with and without it in any later holdout; this worker is excluded from future hypothesis, pre-registration, and implementation work.

## Reports and evidence

- [DATA_INVENTORY.md](DATA_INVENTORY.md): access, coverage, cost, effort, verdicts, and sample-pull proof.
- [HOLDOUT_FEASIBILITY.md](HOLDOUT_FEASIBILITY.md): initial and dated Dow roster snapshots, per-window timestamp row counts, source links, verdict, and fallback proposal.
- [samples/](samples/): development-period sample evidence and availability-only CSVs.
- [sealed_holdout_dow/](../sealed_holdout_dow/): raw Yahoo API responses only; no price columns were read from these files.

No outcome test was run and no substitute holdout was selected. User approval is required before any substitute holdout is tested.
