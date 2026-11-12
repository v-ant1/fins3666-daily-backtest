# Alpaca data audit (read-only)

**Audit date:** 11 November 2026  
**Scope:** API feasibility only. No orders, returns, signals, or outcome analysis were run. No request included a date earlier than 2020-11-27. All persisted market-data samples are small 2024 slices.

## Executive finding

Alpaca can supply the fields needed for a daily signed trade-volume measure in the development period: historical SIP trade prints include time, price, size, venue, conditions and correction status, and historical SIP quotes provide bid/ask prices and sizes. Both credential pairs successfully queried IEX and SIP for old historical slices; this establishes historical endpoint access, not real-time SIP entitlement. A full S&P 500 trade-plus-quote archive is technically possible but likely a multi-terabyte and multi-week/month pull under the observed 200-request/minute limits, so it is not a small or dependable project data task.

## What was tested

Credentials were loaded in memory with `python-dotenv` from `C:/Users/musta/Desktop/UNSW/SSI/FINS3666/A2/.env`; the primary names and the `2_` names were both used. Neither key nor secret values were printed, saved, or included in request logs. All requests were HTTP GETs to data endpoints; no order endpoint was called.

Small 2024 probes used AAPL, JNJ and CAT (Dow constituents), mostly on 2024-06-03, plus daily bars for 2024-06-03 through 2024-06-05. A three-name one-minute SIP bar query returned roughly 390 bars per name for the regular session. I also checked only the single permitted boundary date, 2020-11-27, for stock trades, quotes, minute and daily bars; the first returned timestamps were on that date. Corporate-action, news and auction availability checks covered 2020-11-27 onward only. No boundary observations were saved as market-data samples.

The 2024 sample files in this folder include `dow_micro_samples_2024.json`, `trades_2024.json`, `quotes_2024.json`, `bars_1min_2024.json`, `bars_1day_2024.json`, `corporate_actions_2024.json`, `news_2024.json`, `options_2024.json`, and auction/closing-trade samples. `probe_summary.json` and `boundary_probe_summary.json` hold HTTP status, counts and rate headers only. Samples have no credentials.

## Feed access and endpoint details

Alpaca’s plan page says Basic is free, real-time equity coverage is IEX, and its stated equity historical timeframe begins in 2016; it lists 200 historical API requests per minute for Basic and 10,000/minute for Algo Trader Plus. The same page distinguishes full exchange coverage under Algo Trader Plus from IEX-only real-time Basic. [Alpaca Market Data API plans](https://docs.alpaca.markets/us/v1.1/docs/about-market-data-api)

The IEX and SIP probes for 2024 both returned HTTP 200 under both credential pairs. Historical requests were for dates years before the present, so that does **not** establish real-time SIP access: Alpaca’s FAQ says the feed can be selected with `feed=sip` or `feed=iex`, and notes that Basic real-time equities use IEX while historical SIP queries can be made when the requested end is at least 15 minutes old. Use SIP for a consolidated, market-wide reconstruction; an IEX-only stream omits trades and quotes from the other venues and is not a consolidated NBBO. [Alpaca Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq)

The sample trade records contain `t` (timestamp), `p` (price), `s` (shares), `x` (exchange), `c` (condition codes), and optional `u` correction/cancel status. Historical quote records contain timestamp, bid/ask prices and sizes, venue fields and quote-condition flags. The quotes endpoint supplies a best bid/ask record; request SIP, rather than IEX, to use consolidated-market quotes for a quote-rule or Lee–Ready classification. [Historical trades reference](https://docs.alpaca.markets/us/reference/stocktradesingle-1) · [Historical quotes reference](https://docs.alpaca.markets/us/reference/stockquotesingle-1)

One-minute and daily bars both worked. The bar fields include OHLC, volume, trade count `n`, and VWAP; `1Min` and `1Day` are supported timeframes and the daily sample requested `adjustment=all`. Bars are useful for ordinary volume and price controls, but cannot replace tick-level trades and quotes for signing each trade. [Historical bars reference](https://docs.alpaca.markets/us/reference/stockbarsingle-1)

Both credential pairs returned rate headers of 200 requests/minute, matching the Basic limit shown in the documentation. The response headers expose `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and reset time. Do not assume that using two key pairs doubles throughput: both showed the same nominal limit, and I did not perform a load test. Page limits are up to 10,000 data points, and every endpoint must be paginated using its next-page token.

## Requested data types

| Data type | What the small audit established | Earliest history / caveat |
|---|---|---|
| Stock trades | SIP and IEX historical requests succeeded. Returned records expose trade time, price, size, venue, conditions and correction status. | Alpaca’s general equities plan table says historical stock data since 2016. The earliest date actually checked here was 2020-11-27, not earlier. |
| Quotes / NBBO | SIP and IEX queries succeeded; records include bid/ask, size, bid/ask venue and conditions. | General equities timeframe is since 2016; the earliest date checked was 2020-11-27. SIP is required for consolidated-market quoting; IEX is a single venue. |
| 1-minute / daily bars | Both intervals returned data. `adjustment=all` is available for daily bars. | General equities timeframe is since 2016; the earliest date checked was 2020-11-27. |
| Corporate actions | The 2024 request returned a row; a request for 2020-11-27 through 2020-12-31 also returned one row. | The corporate-actions reference does not state a historical start date. The endpoint warns that provider receipt/processing can be delayed and gives no guarantee of creation time; do not assume complete point-in-time announcement history. [Reference](https://docs.alpaca.markets/us/reference/corporateactions-1) |
| News | The bounded 2024 query returned articles. The allowed 2020-11-27-to-2020-12-31 check also returned articles. | Alpaca documents historical news back to 2015, sourced from Benzinga; that leaves 2010–2014 without vendor news history. [Historical news](https://docs.alpaca.markets/us/v1.1/docs/historical-news-data) |
| Options | A 2024 AAPL contract trades query succeeded on the indicative feed. | Alpaca says historical option data starts in February 2024. Basic real-time option coverage is indicative; OPRA is a paid subscribed feed. No 2010–2020 option history is offered. [Historical options](https://docs.alpaca.markets/us/docs/historical-option-data) |
| Auctions | The auction endpoint returned opening auction records for AAPL, JNJ and CAT on 2024-06-03; the AAPL opening record included a 923,550-share size. The endpoint’s close array was null on that sampled date. Separately, SIP trade prints at the 2024-06-03 close included condition `6` (Market Center Closing Trade) and size 5,079,504 for an AAPL print, so a closing-cross volume can be recovered from eligible SIP trades. | The auction endpoint accepts only SIP and returns price/size entries. Its own reference does not state a history start date; the earliest tested date was 2020-11-27. SIP trade-condition documentation identifies `6` as Market Center Closing Trade. [Auctions reference](https://docs.alpaca.markets/us/reference/stockauctionsingle-1) · [Trade-condition FAQ](https://docs.alpaca.markets/us/docs/market-data-faq) |

## Feasibility: daily signed order-flow imbalance, 2020-11-27 to 2026-10-30

**Data fields: yes. Practical whole-universe pull: likely burdensome.** With full historical SIP trades and quotes, one could sign eligible consolidated trades against the contemporaneous midpoint (with a fixed quote/trade alignment rule and an explicit midpoint tie-break), then aggregate signed shares daily. The trade records provide the required flags for excluding/correcting prints. IEX-only data would produce a different, venue-limited statistic. Alpaca’s API can return multiple symbols per request, but pages are capped at 10,000 total observations and large requests paginate; S&P 500 plus Dow is effectively around 500 unique names because the universes substantially overlap.

For scale, 2024-06-03 full-session one-minute SIP bars reported about 682,000 trades for AAPL, 431,000 for MSFT and 42,000 for DIA in their `n` fields. This is only a few-name scale check, not a representative universe estimate. A planning range of 50,000–400,000 trade records per name per session gives about 25–200 million prints per day for 500 names, or roughly 38–300 billion records over 1,500 sessions. Quote updates add a similarly large or larger stream; their count was not fully sampled here.

At the documented Basic rate of 200 calls/minute and the 10,000-record page ceiling, the purely arithmetic lower bound for trades alone is about 19,000–150,000 minutes (roughly 13–104 continuous days) if every page were full. Real collection would take longer because symbol/time segmentation, incomplete pages, retries, network transfer, and quote pagination reduce the theoretical rate. Using an order-of-magnitude 100-byte JSON representation per record, trade data alone would be roughly 4–30 TB uncompressed; adding quotes plausibly moves combined raw storage into the tens to 100+ TB range. This storage estimate is deliberately broad and assumes the stated record-count range; it is not an observed dataset size. Compression can reduce disk use, but quote/trade data licensing, account permissions, and retention terms should be checked before any bulk pull.

**Recommendation:** bars and daily volume are easy; daily signed OFI is technically possible but not presently a practical pull for this project’s complete 500-name history without a narrower universe, a specialized vendor/export, or a server-scale collection and storage plan. The scope and allowed data period do not themselves establish that an OFI signal has predictive value.

## Auction cross volume

**Opening cross:** yes; the dedicated SIP auction endpoint returned opening events with sizes in the 2024 test.  
**Closing cross:** the sampled endpoint’s close array was null, so I would not rely on that route without broader coverage verification. The historical SIP trade endpoint does expose market-center closing trades (`6`) with size; a tightly time-bounded 2024 sample returned such a print. Condition filtering and duplicate/correction handling are necessary; do not sum all prints around 16:00 as if every one were the cross.

## What the 2010–2020 holdout would lose by vendor start date

This is a vendor-history statement only; the project’s sealed holdout remains off-limits regardless of technical availability.

- **Stocks (trades, quotes, bars):** documented equities history begins in 2016, so the vendor cannot supply 2010–2015, about the first six calendar years of a 2010–2020 holdout. 2016 onward may exist, subject to endpoint/feed coverage, but this audit did not request pre-2020-11-27 data.
- **Options:** history begins February 2024, so the entire 2010–2020 holdout is unavailable.
- **News:** history begins in 2015, so 2010–2014 is unavailable.
- **Corporate actions and auctions:** Alpaca’s cited endpoint documentation gives no separate earliest-history date. The allowed checks establish availability only at/after 2020-11-27; do not claim that either dataset extends to 2010.

## Limits and data discipline

This audit used narrow 2024 windows and the permitted 2020-11-27 boundary only. It did not download the project’s development period, inspect the sealed historical Dow or any sealed-holdout ETF, calculate returns, calculate signals, or test predictive outcomes. The market-data samples are illustrative schema/access checks, not research results.
