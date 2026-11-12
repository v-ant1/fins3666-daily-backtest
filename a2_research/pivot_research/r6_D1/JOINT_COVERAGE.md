# D1 joint input coverage (development only)

This is an input-only coverage audit under frozen `specs/r6_prereg/D1.md`. It uses point-in-time membership dates, finite paired FINRA ratio availability, and price-bar date/ticker presence only. Price columns and price/return values are not loaded; no forward returns, outcomes, ratios as signals, or ICs are computed.

## Date and mask definitions

The NYSE schedule is the session calendar from the FINRA development manifest. Formation dates are every fifth session starting 2020-11-27, through the last development session. For formation `t`, the complete FINRA score requires valid paired ratios for the five sessions `t-4` through `t`. Price input availability is presence-only: the five signal-window bars `t-4` through `t`, and the five forward-window bars `t+2` through `t+6`. A jointly eligible name must be a PIT member on `t` and have all three complete masks. The final scheduled dates remain in `joint_coverage.csv`; dates without the full calendar-forward window have no eligible names. Daily member-day same-date coverage is also reported separately.

## Gate summary

| Universe | Daily joint ratio + bar coverage | Formation joint member-day coverage | Median eligible names/date | Min names/date | Dates with ≥250 S&P names | 90% member-day | 80% S&P-date gate |
|---|---:|---:|---:|---:|---:|---|---|
| S&P 500 | 95.286% | 94.843% | 480 | 0 | 297/298 | PASS | PASS |
| Dow 30 | 98.244% | 97.494% | 30 | 0 | not applicable | PASS | not applicable |

**Overall gate: PASS.** The fixed rule is strict formation joint-member-day coverage ≥90% in both universes and at least 80% of all scheduled S&P formation dates with ≥250 jointly eligible names. Daily same-date coverage is shown as a separate diagnostic.

## Per-date files and price-data limitation

`joint_coverage.csv` has one row per formation date and universe with scheduled PIT members, valid paired ratios at t, complete five-session ratio scores, complete signal-window bar counts, complete forward-window bar counts, jointly eligible names, and whether the calendar windows exist. `joint_daily_coverage.csv` reports daily scheduled members, finite paired ratios, bar presence, and same-date joint counts. Only date and ticker were used for price availability; no price fields or returns were accessed.

The S&P price source retains the documented 51 unresolved PIT ticker histories: ABMD, ALXN, ANSS, ATVI, AVB, CDAY, CERN, CMA, CTLT, CTRA, CTXS, CXO, DAY, DFS, DISCA, DISCK, DISH, DRE, EA, ETFC, FLIR, FRC, GPS, HBI, HES, HFC, HOLX, INFO, IPG, JNPR, JWN, K, KSU, KVUE, LEG, MRO, MXIM, NBL, NLSN, PBCT, PXD, QRVO, SBNY, SEE, SIVB, TIF, TWTR, VAR, WBA, WBD, XLNX. The fixed gap rule is applied date by date; no missing bar or FINRA pair is imputed, and no issuer is replaced by a survivor. FINRA paired validity is determined by finiteness of the prebuilt paired `short_volume_ratio`; its values are never reported or used in this audit.

Rebuild with `python r6_D1/build_joint_coverage.py`. All source inputs are restricted to development dates; this job does not access or inspect holdout data.
