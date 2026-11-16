# G1 input-only build QA

This report describes development inputs and availability masks only. No forward labels, returns, ICs, mechanism tests, or portfolios were created; no holdout data were loaded.

- Calendar: 1488 sessions, 2020-11-27 through 2026-10-30.
- S&P PIT names: 622; Dow PIT names: 37.
- Split-adjusted volume: Yahoo chart `volume` is already split-restated in the source; the development-only split event ledger is pinned (97 event rows across 567 symbols with status). No dividend adjustment or second split adjustment was applied.
- S&P ≥250-name coverage gate: PASS.

| Universe | Formation dates | Minimum eligible | Median eligible | Maximum eligible |
|---|---:|---:|---:|---:|
| dow | 68 | 29 | 30 | 30 |
| sp500 | 68 | 453 | 476 | 494 |

Coverage counts require PIT roster, dated SIC2, complete 50-session positive-volume baseline plus five current-volume observations, and presence of the fixed endpoint open/close bars. These are availability checks; endpoint prices were not divided or used as returns.

- Input NPZ SHA256: `1c39e9768730019c1f1e688cfa81e273577b77767405caffb6090a5c5baf346f`.
- Coverage CSV SHA256: `8fc9ad2b8ae04a609f4bcfc8d34fe1351d87391ade2d6e9b85319bedd4f6b6de`.
- Build manifest SHA256: `461b453b40993ebf6e12588606d17d7e3e2a0ba9e5d4d00b5bed18a6a53c510e`.
- S&P coverage gate dry-check: `True`.

## Source gaps and action ledger

The point-in-time S&P roster contains 622 symbols; 566 have at least one OHLCV row inside the G1 window, leaving 56 roster tickers with no in-window source bars. These are retained in the roster and availability masks with missing prices, not imputed. The Dow PIT roster contains 37 historical ticker labels; 33 have staged daily CSV price files and four have none (`GOOGL`, `PFE`, `RTX`, `XOM`). The availability mask still has 29–30 eligible names at each Dow formation.

The split-event ledger queried 567 symbols with staged bars and recorded 97 split-event rows, 484 symbols with no split reported, and three Yahoo HTTP failures (`FBHS`, `WBA`, `WLTW`). The underlying staged Yahoo chart `volume` values are already split-restated, so the builder did not apply event ratios again; this avoids double adjustment. As an input-only spot check, the staged NVDA chart row on 2024-06-07 has volume 412,386,000, matching Yahoo's development-window chart response after the 10:1 split. The split-event request errors and unavailable ticker bars are disclosed; neither changes the fixed coverage date set or the S&P gate.
