# FINS3666 Group Project: Buying-Pressure Strategy

This repository holds the strategy, code and data behind our FINS3666 report. Folders follow the report's sections, so each writer can go straight to their part.

## The strategy in one line

**J1 (Section 3):** each week, buy the five Dow 30 stocks that have fallen furthest behind their industry peers over the last five sessions, and hold until the next weekly review.
**J2 (Section 6):** J1 with its score averaged over the last four weeks, chosen from 12 pre-logged variants and then tested once on a held-out period (2016–2020).

## Where to find each report section

| Report section | Folder | What is there |
|---|---|---|
| 2. Data description | [`2_data/`](2_data/) | Index membership, industry codes, daily prices and the J1 scores (development period) |
| 3. Strategy development | [`3_strategy_J1/`](3_strategy_J1/) | J1 design, score, trading rules, input-building code and the frozen specification |
| 4. Testing and validation<br>5. Evaluation of results | [`4_5_testing_and_evaluation/`](4_5_testing_and_evaluation/) | The backtesters (main J1 runner and an independent replay) and the J1 results |
| 6. Strategy refinement | [`6_refinement_J2/`](6_refinement_J2/) | The 12 pre-logged variants, how J2 was selected, the code audit, and the one-time holdout result |
| 7. Critical reflection | [`7_reflection_other_strategies/`](7_reflection_other_strategies/) | Other strategies tried (positive but not significant) and a summary of every attempt |
| — | [`archive/`](archive/) | Vedant's original heat-diffusion backtest and the full research log |

## Key facts

| Item | Value |
|---|---|
| Development (in-sample) period | 27 Nov 2020 – 30 Oct 2026 |
| Holdout (out-of-sample) period | 3 Feb 2016 – 30 Oct 2020, opened once, for J2 only |
| Traded universe | Point-in-time Dow 30 |
| Industry peers | Point-in-time S&P 500, grouped by two-digit SIC code |
| Trading cost | 0.05% of each dollar bought or sold |
| Benchmark | Point-in-time equal-weighted Dow 30 (EW30) |
| Data sources | Yahoo Finance and Alpaca (prices), SEC EDGAR (industry codes), S&P Dow Jones Indices announcements (membership) |
