# Dow adjusted-close gaps in the staged J1 price bundle

Input-only QA checked the point-in-time Dow roster mask and adjusted open/close bar presence in `J1_PRICES_DEV.npz`. It did not inspect or print price values, calculate returns, build signals, or access outcomes.

The initial staging had a GOOGL gap from 2026-06-29 through 2026-10-30. Those 88 sessions have now been filled by copying the matching S&P 500 adjusted open and close bars into the Dow panel; matching Dow names in the same date window were also sourced from that S&P panel. After restaging, no Dow roster member is missing either adjusted open or adjusted close in that date window.

Remaining missing adjusted-close bars in the NPZ are all before the Dow development-trading window begins on 2020-11-27. The 3,780 missing member-days span 33 tickers and 126 sessions:

| Dow ticker | Missing dates (inclusive trading sessions) | Missing sessions |
|---|---|---:|
| AAPL | 2020-06-01 to 2020-11-25 | 126 |
| AMGN | 2020-08-31 to 2020-11-25 | 62 |
| AXP | 2020-06-01 to 2020-11-25 | 126 |
| BA | 2020-06-01 to 2020-11-25 | 126 |
| CAT | 2020-06-01 to 2020-11-25 | 126 |
| CRM | 2020-08-31 to 2020-11-25 | 62 |
| CSCO | 2020-06-01 to 2020-11-25 | 126 |
| CVX | 2020-06-01 to 2020-11-25 | 126 |
| DIS | 2020-06-01 to 2020-11-25 | 126 |
| DOW | 2020-06-01 to 2020-11-25 | 126 |
| GS | 2020-06-01 to 2020-11-25 | 126 |
| HD | 2020-06-01 to 2020-11-25 | 126 |
| HON | 2020-08-31 to 2020-11-25 | 62 |
| IBM | 2020-06-01 to 2020-11-25 | 126 |
| INTC | 2020-06-01 to 2020-11-25 | 126 |
| JNJ | 2020-06-01 to 2020-11-25 | 126 |
| JPM | 2020-06-01 to 2020-11-25 | 126 |
| KO | 2020-06-01 to 2020-11-25 | 126 |
| MCD | 2020-06-01 to 2020-11-25 | 126 |
| MMM | 2020-06-01 to 2020-11-25 | 126 |
| MRK | 2020-06-01 to 2020-11-25 | 126 |
| MSFT | 2020-06-01 to 2020-11-25 | 126 |
| NKE | 2020-06-01 to 2020-11-25 | 126 |
| PFE | 2020-06-01 to 2020-08-28 | 64 |
| PG | 2020-06-01 to 2020-11-25 | 126 |
| RTX | 2020-06-01 to 2020-08-28 | 64 |
| TRV | 2020-06-01 to 2020-11-25 | 126 |
| UNH | 2020-06-01 to 2020-11-25 | 126 |
| V | 2020-06-01 to 2020-11-25 | 126 |
| VZ | 2020-06-01 to 2020-11-25 | 126 |
| WBA | 2020-06-01 to 2020-11-25 | 126 |
| WMT | 2020-06-01 to 2020-11-25 | 126 |
| XOM | 2020-06-01 to 2020-08-28 | 64 |

The remaining gaps are outside the allowed trading period and do not affect J1's Dow portfolio window. This note reports input-bar presence only.
