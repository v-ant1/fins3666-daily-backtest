# L4 task: Phase 1b data scouting and holdout feasibility

TARGET: what data we can actually obtain for new directions, and whether the sealed holdout (Dow 30, point-in-time rosters, 2010-01 to 2020-10) is feasible. Folder: r4_L4\ (write only here).

CHANGE:
1. DATA INVENTORY. For each source, give access method, coverage (dates and tickers), frequency, cost, effort and a sample-pull proof (development period only):
   - SEC EDGAR 13F holdings, to build common-ownership networks for Dow names.
   - ETF holdings history (SPY, DIA, XLK and other SPDR sector funds; iShares).
   - Customer-supplier links: SEC 10-K major-customer disclosures, or Compustat segments via FactSet. UNSW students have FactSet; document how to export and what is in it.
   - Intraday data: yfinance's 60-day limit, Alpha Vantage, Polygon free tier, and the source behind the existing hourly feed in the project.
   - Short interest (FINRA).
   - Options-implied data, if free.
   - Analyst coverage.
   - Fund flows.
2. HOLDOUT FEASIBILITY (availability only):
   - Reconstruct the Dow 30 roster at each change date from 2010-01 to 2020-10, using S&P DJI press releases, with sources.
   - For every name ever in the index, check whether daily OHLCV exists for its membership window (yfinance, or stockanalysis.com for delisted names such as WBA, UTX/RTX, DWDP/DD, KFT/MDLZ, AA, BAC, HPQ, T, GE, XOM, PFE, CVX). Report ROW COUNTS AND DATE RANGES ONLY.
   - Do NOT compute or look at returns, prices or signals. Store any downloaded raw files ONLY in sealed_holdout_dow\ and do not open their price columns.
   - If any name is missing, propose a substitute holdout (for example Dow 2010-2020 with the gap documented, or an S&P 100 subset) with its pros and cons. The user must approve any substitute.

CONSTRAINTS:
- Never compute anything outcome-related on pre-2020-06 data.
- Respect site terms and rate limits; no scraping that violates terms.

OWNERSHIP: r4_L4\ and sealed_holdout_dow\ (raw files only).

OBSERVABLE ACCEPTANCE:
- r4_L4\DATA_INVENTORY.md: a table of source, access, coverage, cost, effort and verdict, with sample pulls saved in r4_L4\samples\ (development dates only).
- r4_L4\HOLDOUT_FEASIBILITY.md: the dated roster table with sources, plus a data-availability table per ticker (rows and dates only), and a clear verdict of feasible / partially feasible / not feasible, with a substitute if needed.
