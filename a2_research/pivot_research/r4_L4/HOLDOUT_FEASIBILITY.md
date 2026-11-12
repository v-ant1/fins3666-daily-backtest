# Sealed Dow holdout: availability-only feasibility

**Scope and handling.** This check covers 2010-01-01 through 2020-10-31. I reconstructed roster changes from S&P Dow Jones Indices releases and checked Yahoo chart timestamp arrays plus OHLCV field names. During a source search, the ChartExchange DWDP page rendered historical OHLCV rows in tool output; I did not calculate or use those values and disclosed the exposure to the coordinator. The coordinator ruled that the DWDP interval must be reported with and without it in any later holdout; this worker is excluded from later hypothesis, pre-registration, and implementation work. Other availability checks below use only timestamp arrays and OHLCV field names. All raw Yahoo API responses are in `sealed_holdout_dow/`; the CSVs in `r4_L4/samples/` contain only date/count/schema metadata.

## Roster reconstruction

Initial roster used for 2010-01-01 (no Dow membership change in the period before the first listed change): **MMM, AA, AXP, T, BAC, BA, CAT, CSCO, CVX, KO, DIS, DD, XOM, GE, HPQ, HD, IBM, INTC, JNJ, JPM, KFT, MCD, MRK, MSFT, PFE, PG, TRV, UTX, VZ, WMT.** The date-boundary rule is last trading day under the old roster, then the effective date before the open under the new roster.

| Effective date | Addition(s) | Deletion(s) | Source and note |
|---|---|---|---|
| 2010-01-01 | — | — | Starting roster reconstructed from S&P DJI's historical component infographic and the subsequent official change chain. See the 2000s/2010s timeline in the [S&P DJI component-history infographic](https://www.spglobal.com/spdji/en/documents/additional-material/spdji-the-changing-dow-jones-industrial-average.pdf). The members at the start of 2010 are the roster immediately before the 2012 change. |
| 2012-09-24 | UNH | KFT | [S&P DJI release](https://press.spglobal.com/2012-09-14-UnitedHealth-Group-Inc-Set-to-Join-the-Dow-Jones-Industrial-Average); effective after the close Sep 21. |
| 2013-09-23 | GS, V, NKE | BAC, AA, HPQ | [S&P DJI release](https://press.spglobal.com/2013-09-10-Goldman-Sachs-Visa-Nike-to-Join-the-Dow-Jones-Industrial-Average); effective after the close Sep 20. |
| 2015-03-19 | AAPL | T | [S&P DJI release](https://press.spglobal.com/2015-03-06-Apple-Set-to-Join-the-Dow-Jones-Industrial-Average); effective after the close Mar 18. |
| 2017-09-01 | DowDuPont (ticker DWDP) | DuPont (ticker DD) | The DowDuPont merger changed the listed issuer/ticker lineage; it is included here as a constituent security transition, not an Index Committee stock selection. DowDuPont's SEC filing says its common stock began trading as DWDP on Sep 1, 2017: [SEC filing](https://www.sec.gov/Archives/edgar/data/1666700/000166670017000010/dwdupont-424b3.htm). |
| 2018-06-26 | WBA | GE | [S&P DJI release](https://press.spglobal.com/2018-06-19-Walgreens-Boots-Alliance-Set-to-Join-Dow-Jones-Industrial-Average); effective before the open Jun 26. |
| 2019-04-02 | DOW | DWDP | [S&P DJI release](https://press.spglobal.com/2019-03-26-Dow-Set-to-Join-Dow-Jones-Industrial-Average); Dow Inc replaced DowDuPont before the open Apr 2. |
| 2020-08-31 | CRM, AMGN, HON | XOM, PFE, RTX | [S&P DJI release](https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20200824-1208960/1208960_aug20aaplsplitcrmxomamgnpfehonrtxdjia.pdf); effective Aug 31. The third deletion was then-ticker RTX, formerly UTX. |

The reconstructed roster snapshots are:

| Roster effective date | Dow 30 tickers |
|---|---|
| 2010-01-01 | MMM, AA, AXP, T, BAC, BA, CAT, CSCO, CVX, KO, DIS, DD, XOM, GE, HPQ, HD, IBM, INTC, JNJ, JPM, KFT, MCD, MRK, MSFT, PFE, PG, TRV, UTX, VZ, WMT |
| 2012-09-24 | MMM, AA, AXP, T, BAC, BA, CAT, CSCO, CVX, KO, DIS, DD, XOM, GE, HPQ, HD, IBM, INTC, JNJ, JPM, UNH, MCD, MRK, MSFT, PFE, PG, TRV, UTX, VZ, WMT |
| 2013-09-23 | MMM, AXP, T, BA, CAT, CSCO, CVX, KO, DIS, DD, XOM, GE, HD, IBM, INTC, JNJ, JPM, UNH, MCD, MRK, MSFT, PFE, PG, TRV, UTX, VZ, WMT, GS, V, NKE |
| 2015-03-19 | MMM, AXP, AAPL, BA, CAT, CSCO, CVX, KO, DIS, DD, XOM, GE, HD, IBM, INTC, JNJ, JPM, UNH, MCD, MRK, MSFT, PFE, PG, TRV, UTX, VZ, WMT, GS, V, NKE |
| 2017-09-01 | MMM, AXP, AAPL, BA, CAT, CSCO, CVX, KO, DIS, DWDP, XOM, GE, HD, IBM, INTC, JNJ, JPM, UNH, MCD, MRK, MSFT, PFE, PG, TRV, UTX, VZ, WMT, GS, V, NKE |
| 2018-06-26 | MMM, AXP, AAPL, BA, CAT, CSCO, CVX, KO, DIS, DWDP, XOM, WBA, HD, IBM, INTC, JNJ, JPM, UNH, MCD, MRK, MSFT, PFE, PG, TRV, UTX, VZ, WMT, GS, V, NKE |
| 2019-04-02 | MMM, AXP, AAPL, BA, CAT, CSCO, CVX, KO, DIS, DOW, XOM, WBA, HD, IBM, INTC, JNJ, JPM, UNH, MCD, MRK, MSFT, PFE, PG, TRV, UTX, VZ, WMT, GS, V, NKE |
| 2020-08-31 | MMM, AXP, AAPL, AMGN, BA, CAT, CRM, CSCO, CVX, DIS, DOW, GS, HD, HON, IBM, INTC, JNJ, JPM, KO, MCD, MRK, MSFT, NKE, PG, RTX, TRV, V, VZ, WBA, WMT |

Symbol/issuer transitions needing special treatment are KFT (removed in 2012; it did not continue as a Dow member under MDLZ), DD→DWDP (2017 merger), DWDP→DOW (2019 index replacement), and UTX→RTX (same Dow slot through the 2020 deletion). Yahoo's RTX timestamp history is a **lineage proxy** for the period when the Dow held UTX; it is not evidence that the ticker was UTX at the time.

## OHLCV availability by membership window

Rows count trading-date timestamps within that name's membership window. Dates and OHLCV **field names** were checked; OHLCV values were not read. A zero means Yahoo had no chart result for that historical ticker, not that the security did not trade. Symbols with a Yahoo alias/proxy are called out in the last column. The [machine-readable table](samples/holdout_membership_window_metadata.csv) has every row; the full-window raw response metadata is in [holdout_availability_metadata.csv](samples/holdout_availability_metadata.csv).

| Ticker / index security | Membership window (inclusive dates) | Yahoo date rows | First–last date seen | Field schema / caveat |
|---|---|---:|---|---|
| MMM | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| AA | 2010-01-01–2013-09-22 | 936 | 2010-01-04–2013-09-20 | OHLCV fields present |
| AXP | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| T | 2010-01-01–2015-03-18 | 1,310 | 2010-01-04–2015-03-18 | OHLCV fields present |
| BAC | 2010-01-01–2013-09-22 | 936 | 2010-01-04–2013-09-20 | OHLCV fields present |
| BA | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| CAT | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| CSCO | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| CVX | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| KO | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| DIS | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| DD (DuPont) | 2010-01-01–2017-08-31 | 1,930 | 2010-01-04–2017-08-31 | OHLCV fields present |
| DWDP (DowDuPont) | 2017-09-01–2019-04-01 | 0 | — | Yahoo chart unavailable; source page rendered historical quote rows during research, so no alternative row count is reported here |
| DOW | 2019-04-02–2020-10-31 | 401 | 2019-04-02–2020-10-30 | OHLCV fields present |
| XOM | 2010-01-01–2020-08-30 | 2,683 | 2010-01-04–2020-08-28 | OHLCV fields present |
| GE | 2010-01-01–2018-06-25 | 2,134 | 2010-01-04–2018-06-25 | OHLCV fields present |
| HPQ | 2010-01-01–2013-09-22 | 936 | 2010-01-04–2013-09-20 | OHLCV fields present |
| HD | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| IBM | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| INTC | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| JNJ | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| JPM | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| KFT | 2010-01-01–2012-09-21 | 0 | — | Yahoo chart unavailable; do not substitute MDLZ (KFT was removed from the index) |
| UNH | 2012-09-24–2020-10-31 | 2,040 | 2012-09-24–2020-10-30 | OHLCV fields present |
| MCD | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| MRK | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| MSFT | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| PFE | 2010-01-01–2020-08-30 | 2,683 | 2010-01-04–2020-08-28 | OHLCV fields present |
| PG | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| TRV | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| UTX (queried as RTX lineage proxy) | 2010-01-01–2020-08-30 | 2,683 | 2010-01-04–2020-08-28 | OHLCV fields present under RTX symbol; legacy UTX not separately served by Yahoo |
| VZ | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| WMT | 2010-01-01–2020-10-31 | 2,727 | 2010-01-04–2020-10-30 | OHLCV fields present |
| GS | 2013-09-23–2020-10-31 | 1,791 | 2013-09-23–2020-10-30 | OHLCV fields present |
| V | 2013-09-23–2020-10-31 | 1,791 | 2013-09-23–2020-10-30 | OHLCV fields present |
| NKE | 2013-09-23–2020-10-31 | 1,791 | 2013-09-23–2020-10-30 | OHLCV fields present |
| AAPL | 2015-03-19–2020-10-31 | 1,417 | 2015-03-19–2020-10-30 | OHLCV fields present |
| WBA | 2018-06-26–2020-08-30 | 0 | — | Yahoo chart unavailable; [StockAnalysis history](https://stockanalysis.com/stocks/wba/history/) is a possible secondary source, not row-counted here |
| CRM | 2020-08-31–2020-10-31 | 44 | 2020-08-31–2020-10-30 | OHLCV fields present |
| AMGN | 2020-08-31–2020-10-31 | 44 | 2020-08-31–2020-10-30 | OHLCV fields present |
| HON | 2020-08-31–2020-10-31 | 44 | 2020-08-31–2020-10-30 | OHLCV fields present |

The three zero-row cases are the retired tickers KFT, DWDP, and WBA. Yahoo did not return separate legacy-ticker OHLCV series for them. An additional identity caveat applies to UTX→RTX: the returned RTX series has date coverage, but a coordinator should source/verify the pre-merger UTX security history rather than silently treat a current ticker series as a point-in-time security identifier. Thirty-seven of the 40 listed ticker/lineage windows have Yahoo timestamp coverage; one of those 37 uses the RTX lineage proxy.

## Verdict and proposed path

**Verdict: partially feasible using the tested free Yahoo route; potentially feasible with licensed/archived legacy-symbol data.** Thirty-six constituent/security windows have Yahoo date coverage, but KFT, DWDP, and WBA need a separately verified source. UTX/RTX also needs a point-in-time security mapping. The list [Kibot Dow 30 history](https://www.kibot.com/datasets/dow-30-historical.html) explicitly describes retained delisted files for DWDP, KFT, UTX, and WBA from 2009 onward; this is a potential paid source, not a sample checked or purchased. UNSW Business School lists CRSP and FactSet resources but access must be confirmed for the project team.

If the missing ticker windows cannot be sourced, the fallback proposal is **Dow 2010–2020 with those ticker gaps explicitly documented and no silent fills**. Its advantage is that it preserves the Dow setting and most breadth; its disadvantage is that incomplete names and membership windows make EW30 comparison and test power non-equivalent to the registered 30-stock holdout. A point-in-time S&P 100 subset would broaden breadth but changes the universe and requires a separate roster reconstruction. Either substitute needs user approval before any outcome data is opened; no substitute has been tested or selected.

## Audit artifacts

- [`samples/holdout_membership_window_metadata.csv`](samples/holdout_membership_window_metadata.csv): per ticker, membership window, timestamp rows and endpoint dates.
- [`samples/holdout_availability_metadata.csv`](samples/holdout_availability_metadata.csv): full Yahoo chart-window timestamp coverage / OHLCV field names.
- `../sealed_holdout_dow/`: raw JSON responses only. No price values were opened.

