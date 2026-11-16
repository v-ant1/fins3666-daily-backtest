# K1 development input coverage (input-only)

Generated from staged data on 2026-11-11. This report counts only input availability; it contains no forward labels, returns, ICs, or portfolio outcomes.

## Price panel boundaries and coverage

- Common trading-session calendar: 1,488 dates, 2020-11-27 through 2026-10-30.
- S&P 500 adjusted-price source after the registered date filter: 717,569 rows across 566 tickers; roster-active names per session range 462–503; names with price rows/session range 462–503; active names with dated SIC2 range 455–503.
- Dow adjusted-price sources after the registered date filter and initial-window gap overlay: 44,640 rows across 33 tickers; roster-active names/session range 29–30; names with price rows/session range 30–30; active names with dated SIC2 range 29–30.
- SPY adjusted benchmark: 1,488 daily observations; all 1,488 S&P calendar sessions matched.
- Point-in-time S&P roster: 623 dated intervals and 622 ticker identities; Dow roster and dated SIC2 sources are separately hash-pinned below.
- Dates before 2020-11-27 were excluded by Parquet scan predicates before any price rows were materialized; no sealed-holdout file or pre-2020-11-27 Dow price value was read.

## EDGAR event-clock input coverage

Counts below deduplicate to the earliest BMO/AMC Item 2.02 filing per CIK/report quarter, map acceptance time to the first session open strictly after acceptance, and check only event-session and preceding-session adjusted-close availability plus PIT roster and dated SIC2. They do not inspect the 21-session forward endpoint or calculate any price change.

### S&P 500 mechanism input availability

| Event quarter | BMO/AMC events | BMO | AMC | ticker in panel | PIT member | SIC2 known | stock close pair | SPY close pair | all signal inputs available |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2020Q4 | 24 | 11 | 13 | 24 | 24 | 24 | 24 | 24 | 24 |
| 2021Q1 | 472 | 277 | 195 | 435 | 435 | 432 | 435 | 472 | 432 |
| 2021Q2 | 475 | 269 | 206 | 440 | 440 | 439 | 440 | 475 | 439 |
| 2021Q3 | 476 | 268 | 208 | 442 | 442 | 441 | 442 | 476 | 441 |
| 2021Q4 | 469 | 263 | 206 | 438 | 438 | 437 | 438 | 469 | 437 |
| 2022Q1 | 471 | 266 | 205 | 441 | 441 | 440 | 441 | 471 | 440 |
| 2022Q2 | 475 | 267 | 208 | 449 | 449 | 449 | 449 | 475 | 449 |
| 2022Q3 | 475 | 267 | 208 | 451 | 451 | 451 | 451 | 475 | 451 |
| 2022Q4 | 475 | 266 | 209 | 453 | 453 | 453 | 453 | 475 | 453 |
| 2023Q1 | 478 | 273 | 205 | 456 | 456 | 455 | 456 | 478 | 455 |
| 2023Q2 | 480 | 264 | 216 | 461 | 461 | 461 | 461 | 480 | 461 |
| 2023Q3 | 477 | 266 | 211 | 458 | 458 | 458 | 458 | 477 | 458 |
| 2023Q4 | 481 | 274 | 207 | 461 | 461 | 460 | 461 | 481 | 460 |
| 2024Q1 | 482 | 272 | 210 | 463 | 463 | 461 | 463 | 482 | 461 |
| 2024Q2 | 480 | 266 | 214 | 461 | 461 | 459 | 460 | 480 | 458 |
| 2024Q3 | 480 | 267 | 213 | 464 | 464 | 461 | 464 | 480 | 461 |
| 2024Q4 | 482 | 265 | 217 | 465 | 465 | 460 | 465 | 482 | 460 |
| 2025Q1 | 482 | 266 | 216 | 468 | 468 | 464 | 468 | 482 | 464 |
| 2025Q2 | 485 | 271 | 214 | 471 | 471 | 471 | 471 | 485 | 471 |
| 2025Q3 | 483 | 271 | 212 | 474 | 474 | 474 | 474 | 483 | 474 |
| 2025Q4 | 488 | 275 | 213 | 480 | 479 | 477 | 479 | 488 | 476 |
| 2026Q1 | 483 | 260 | 223 | 477 | 477 | 476 | 477 | 483 | 476 |
| 2026Q2 | 488 | 262 | 226 | 484 | 484 | 483 | 483 | 488 | 482 |
| 2026Q3 | 480 | 263 | 217 | 477 | 477 | 477 | 477 | 480 | 477 |

### Dow portfolio signal input availability

| Event quarter | BMO/AMC events | BMO | AMC | ticker in panel | PIT member | SIC2 known | stock close pair | SPY close pair | all signal inputs available |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2020Q4 | 24 | 11 | 13 | 2 | 2 | 2 | 2 | 24 | 2 |
| 2021Q1 | 472 | 277 | 195 | 33 | 30 | 30 | 30 | 472 | 30 |
| 2021Q2 | 475 | 269 | 206 | 32 | 29 | 29 | 29 | 475 | 29 |
| 2021Q3 | 476 | 268 | 208 | 33 | 30 | 30 | 30 | 476 | 30 |
| 2021Q4 | 469 | 263 | 206 | 33 | 30 | 30 | 30 | 469 | 30 |
| 2022Q1 | 471 | 266 | 205 | 33 | 30 | 30 | 30 | 471 | 30 |
| 2022Q2 | 475 | 267 | 208 | 33 | 30 | 30 | 30 | 475 | 30 |
| 2022Q3 | 475 | 267 | 208 | 32 | 29 | 29 | 29 | 475 | 29 |
| 2022Q4 | 475 | 266 | 209 | 33 | 30 | 30 | 30 | 475 | 30 |
| 2023Q1 | 478 | 273 | 205 | 33 | 30 | 30 | 30 | 478 | 30 |
| 2023Q2 | 480 | 264 | 216 | 33 | 30 | 30 | 30 | 480 | 30 |
| 2023Q3 | 477 | 266 | 211 | 32 | 29 | 29 | 29 | 477 | 29 |
| 2023Q4 | 481 | 274 | 207 | 33 | 30 | 30 | 30 | 481 | 30 |
| 2024Q1 | 482 | 272 | 210 | 33 | 30 | 30 | 30 | 482 | 30 |
| 2024Q2 | 480 | 266 | 214 | 33 | 30 | 30 | 30 | 480 | 30 |
| 2024Q3 | 480 | 267 | 213 | 31 | 29 | 29 | 29 | 480 | 29 |
| 2024Q4 | 482 | 265 | 217 | 33 | 31 | 31 | 31 | 482 | 31 |
| 2025Q1 | 482 | 266 | 216 | 33 | 30 | 30 | 30 | 482 | 30 |
| 2025Q2 | 485 | 271 | 214 | 33 | 30 | 30 | 30 | 485 | 30 |
| 2025Q3 | 483 | 271 | 212 | 31 | 29 | 29 | 29 | 483 | 29 |
| 2025Q4 | 488 | 275 | 213 | 33 | 31 | 31 | 31 | 488 | 31 |
| 2026Q1 | 483 | 260 | 223 | 31 | 29 | 29 | 29 | 483 | 29 |
| 2026Q2 | 488 | 262 | 226 | 33 | 31 | 31 | 31 | 488 | 31 |
| 2026Q3 | 480 | 263 | 217 | 31 | 28 | 29 | 29 | 480 | 28 |

## Hashed files

SHA-256 values are stored in `K1_INPUT_MANIFEST.json`; the input manifest includes the staged bundle, both raw point-in-time price sources, isolated SPY development series, event clock, both rosters, and both dated SIC2 sources.
