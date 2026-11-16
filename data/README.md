# Data used for J1 (report Section 3)

All files cover the development period, 27 November 2020 to 30 October 2026. No data from the 2016–2020 holdout period is included.

| File | What it is |
|---|---|
| `sp500_pit_roster.csv` | Point-in-time S&P 500 membership: which stocks were in the index on each date |
| `dow_pit_roster.csv` | Point-in-time Dow 30 membership |
| `sp500_sic_panel.csv` | Dated SEC industry codes (SIC) for each stock, used to find industry peers |
| `sp500_ohlcv_dev_gapfilled.parquet` | Daily open, high, low, close, adjusted close and volume for S&P 500 stocks |
| `dow_components_dev.parquet` | Daily prices for Dow 30 stocks |
| `dow_dev_gapfill.parquet` | Extra Dow price bars used to fill gaps |
| `J1_PRICES_DEV.npz` | Prepared price arrays used directly by the J1 runner |
| `J1_PRICES_DEV_manifest.json` | How `J1_PRICES_DEV.npz` was built and from which files |
| `signal_bundle.parquet` | The J1 scores for every stock and review date |

Sources: Yahoo Finance and Alpaca for prices; SEC EDGAR for industry codes; dated S&P Dow Jones Indices announcements for index membership.
