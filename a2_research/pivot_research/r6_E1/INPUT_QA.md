# E1 monthly CLV-pressure input QA

This is an input-only signal build. No forward returns, signal-outcome joins, ICs, or portfolio outcomes were loaded or computed. Price OHLCV was loaded only from 2020-06-01 through 2026-10-30 so the first registered formation has its full 21-session lookback; the registered formation window begins 2020-11-27 and its first month-end observation is 2020-11-30. No price data before 2020-06 or holdout data were read; SIC filing metadata starts in 2019 as preregistered.

## Registered construction

- Formation: final observed trading session of each calendar month.
- Stock pressure: 21 sessions through formation close; daily CLV is `(2*close-high-low)/(high-low)` with zero for a zero range; pressure is weighted by raw close times volume. Any incomplete 21-session OHLCV window is missing.
- Peer score: equal-weight, leave-one-out mean of same active SIC2 peers with at least two other valid peer-pressure observations.
- Active masks separately identify point-in-time roster membership, pressure availability, SIC2 membership, and usable peer score.

## Input coverage

### SP500

- Monthly formations: 72 (2020-11-30 to 2026-10-30).
- Ticker axis: 614; tickers with at least one development-window bar: 566; daily OHLCV rows: 775,398.
- Median (minimum) roster size: 503 (503).
- Median (minimum) complete 21-session pressure count: 481 (459).
- Median (minimum) members with dated SIC2: 499 (497).
- Median (minimum) eligible leave-one-out peer scores: 452 (430).
- SIC2 group-size distribution over formation-date/group observations: `{'1': 613, '2': 549, '3': 433, '4': 356, '5': 626, '6': 235, '7': 104, '8': 39, '9': 31, '10': 45, '11': 36, '13': 34, '14': 25, '15': 62, '16': 4, '17': 38, '18': 7, '19': 45, '20': 23, '21': 46, '22': 6, '23': 15, '24': 49, '25': 36, '26': 48, '27': 13, '28': 48, '29': 35, '30': 11, '31': 10, '32': 19, '33': 18, '34': 19, '35': 8, '36': 19, '37': 36, '38': 28, '39': 64, '40': 9, '41': 14, '42': 3, '54': 6, '55': 17, '56': 14, '57': 14, '58': 12, '59': 2, '60': 5, '61': 2}`.
- Singleton industry observations: 613; counts by SIC2: `{'01': 72, '16': 72, '17': 58, '22': 61, '24': 25, '25': 13, '30': 6, '31': 72, '32': 11, '54': 72, '57': 52, '65': 22, '72': 5, '78': 72}`.
- Preregistration 250-name/80%-date input threshold passed: True.
- Input limitation: missing dated SIC classifications and bars are left missing; no peers are invented or substituted.

### Dow30

- Monthly formations: 72 (2020-11-30 to 2026-10-30).
- Ticker axis: 33; tickers with at least one development-window bar: 33; daily OHLCV rows: 48,104.
- Median (minimum) roster size: 30 (30).
- Median (minimum) complete 21-session pressure count: 30 (1).
- Median (minimum) members with dated SIC2: 30 (30).
- Median (minimum) eligible leave-one-out peer scores: 12 (0).
- SIC2 group-size distribution over formation-date/group observations: `{'1': 984, '2': 168, '3': 72, '4': 96, '5': 48}`.
- Singleton industry observations: 984; counts by SIC2: `{'20': 72, '29': 72, '30': 72, '36': 72, '38': 72, '48': 72, '52': 48, '53': 72, '58': 72, '59': 72, '60': 72, '61': 72, '62': 72, '79': 72}`.
- Preregistration 250-name/80%-date input threshold passed: not applicable to Dow.
- Input limitation: missing dated SIC classifications and bars are left missing; no peers are invented or substituted.

## Unchanged E1 input gates

- S&P 500 member-day coverage with complete OHLCV and dated SIC lineage: 95.09% (registered minimum 90%); gate PASS.
- Dow 30 member-day coverage with complete OHLCV and dated SIC lineage: 98.44% (registered minimum 90%); gate PASS.
- S&P 500 dates with at least 250 eligible peer scores: 100.00% (registered minimum 80%); gate PASS.
- These are input-coverage gates only; no signal-outcome statistics were computed.

## S&P 500 gap and feasibility caveat

The source QA reports 622 distinct PIT tickers across the wider data window and 614 whose PIT intervals overlap this formation window. Original Yahoo OHLCV covered 568 of 622; the documented gap-fill recovered ADS (15 rows), FBHS (644 rows), and SATS (64 rows), leaving 51 ticker histories without rows. The unresolved PIT symbols are ABMD, ALXN, ANSS, ATVI, AVB, CDAY, CERN, CMA, CTLT, CTRA, CTXS, CXO, DAY, DFS, DISCA, DISCK, DISH, DRE, EA, ETFC, FLIR, FRC, GPS, HBI, HES, HFC, HOLX, INFO, IPG, JNPR, JWN, K, KSU, KVUE, LEG, MRO, MXIM, NBL, NLSN, PBCT, PXD, QRVO, SBNY, SEE, SIVB, TIF, TWTR, VAR, WBA, WBD, and XLNX. The gap-fill histories are same-share-line aliases only over their documented PIT membership intervals. This builder preserves the missing-name price-history gap and does not replace issuers with acquirer or current-survivor prices.

The dated SIC source is `r6_data/sp500_sic_panel.csv`, built from SEC 10-K headers and the SEC CIK/ticker lineage. It contains usable SIC for 621 unique symbols, including 4624 dated 10-K rows and 4 explicitly flagged current-SIC fallback rows; FRC remains without SIC because no usable 10-K header or current SIC was returned. The same issuer SIC timeline is applied to Dow holdings when a ticker is present in the S&P PIT SIC panel. No missing classification is invented. The numeric coverage above is checked against the unchanged E1 250-name/80%-of-dates gate; failure blocks any outcome work.

## Files

- `E1_INPUTS.npz`: rectangular arrays, separate axes and dates for S&P500 and Dow; `*_stock_pressure`, `*_peer_pressure`, active masks, SIC2 labels, group sizes, and valid-peer counts.
- `*_sic2_group_sizes.csv`: per-formation-date SIC2 group sizes, including singleton groups.
- `input_manifest.json`: machine-readable input QA and construction provenance.
- `build_inputs.py`: reproducible builder. All output paths are inside `r6_E1/`.
