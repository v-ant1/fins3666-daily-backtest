# D4 Inputs and SIC Panel Audit

**Scope.** Read-only review of `r4_L4/data/sic_panel.csv`, its EDGAR header links, `r4_harness/runs/D4/build_inputs.py`, and `INPUT_QA.md`. No forward-return, signal-outcome, or portfolio data were loaded or computed. The SIC row checks used EDGAR filing headers only; D4 code review was static.

## Findings

### BLOCKER — SIC ticker/issuer lineage is wrong for DD and historical DOW

The header parser appears to extract SIC accurately from the header linked in each row, but ticker-to-CIK lineage is not point-in-time correct. The `DD` rows use CIK 0000030554 (legacy E. I. du Pont / later EIDP-Corteva lineage); its 2024 row reports SIC `0100`, which maps to two-digit industry `01`. Current DuPont de Nemours trades as DD under CIK 0001666700, which is also the CIK represented by rows labelled `DWDP`; its 2024 10-K reports the DD symbol and SEC header SIC 2821 (`28`). The panel therefore assigns the wrong issuer and industry to DD after the separation, while retaining the correct issuer under the obsolete DWDP label. Separately, `DOW` uses only CIK 0001751788 (Dow Inc., the issuer that began independent trading in 2019) and has no pre-2019 rows for The Dow Chemical Company, CIK 0000029915, which traded as DOW before the 2017 merger. The 2017 merger filing says old Dow and DuPont were delisted and DowDuPont began trading as DWDP on 2017-09-01; the 2019 filing identifies DD as the ticker for the continuing DowDuPont/DuPont issuer from 2019-06-03, while Dow Inc. separated and began independent trading 2019-04-01.

Evidence: [Dow Chemical 2016 10-K, CIK 29915](https://www.sec.gov/Archives/edgar/data/29915/000002991517000011/dow201610k.htm); [DowDuPont 2017 10-K, merger and DWDP listing](https://www.sec.gov/Archives/edgar/data/1666700/000166670018000009/a2017dwdp10-k.htm); [DuPont 2019 10-K, DD ticker and continuing CIK 1666700](https://www.sec.gov/Archives/edgar/data/1666700/000166670020000006/dupont201910-k.htm); [Dow Inc. separation, CIK 1751788](https://www.sec.gov/Archives/edgar/data/1751788/000119312519069293/d502004dex991.htm); [DuPont 2024 10-K, DD ticker and CIK 1666700](https://www.sec.gov/Archives/edgar/data/1666700/000166670025000005/dd-20241231.htm).

**Required correction:** build the SIC panel on issuer CIK plus effective ticker intervals, not a current ticker-to-CIK map. Keep legacy Dow Chemical CIK 29915 as DOW through the 2017 merger; map the post-merger issuer CIK 1666700 as DWDP through the documented ticker change and as DD from 2019-06-03 onward; keep Dow Inc. CIK 1751788 as DOW from its 2019-04-01 separation. Do not use CIK 30554 as post-2017 DD. Rebuild the panel and coverage, then recheck the D5 two-digit industry membership gate before any outcome data.

### BLOCKER — D4 input QA describes a missing PIT roster although one is now present

`INPUT_QA.md` says `13f_top50_pit_roster.csv` is missing and that its arrays use a provisional fixed Q2 2026 manager list. At audit time, the roster file exists and contains 50 ranked `sec_quarterly_bulk` members for sampled report quarters 2020-06-30, 2020-09-30, 2021-03-31, and 2026-06-30; 2026-09-30 has no cohort yet. The QA and `D4_INPUTS.npz` have matching modification timestamps, while the roster file predates them. Thus QA and the saved input bundle are stale relative to the current input state and cannot establish that the required point-in-time roster was used. This matters because `D4.md` prohibits using the Q2 2026 roster for earlier quarters. The runner code checks for the roster file and checks the bundle's `manager_roster_source` provenance before outcomes, but the input build and QA need to be rerun so that the refreshed bundle and its QA can be reviewed together; the freeze gate has not been satisfied by the inspected QA.

Evidence: [D4 QA](../r4_harness/runs/D4/INPUT_QA.md); [builder roster selection and source provenance](../r4_harness/runs/D4/build_inputs.py); [point-in-time roster file](../r4_L4/data/13f_top50_pit_roster.csv); [D4 preregistration](../specs/r4_prereg/D4.md).

### SHOULD-FIX — SIC panel cannot implement D5's specified acceptance-time cutoff exactly

The SIC panel schema is `ticker,cik,sic,effective_from,source_url`; it stores filing dates but not EDGAR acceptance timestamps. D5 specifies eligibility using the SEC acceptance timestamp and a 16:00 America/New_York cutoff on the preceding NYSE session. The checked headers show why a calendar date alone is not the same field: for example, AMGN's 2024-02-14 filing was accepted at 16:23:32 ET, CSCO's 2024-09-05 filing at 16:41:20, and RTX's 2024-02-05 filing at 16:17:23. A strict next-trading-session-after-filing-date implementation is conservative and does not create look-ahead, but the current SIC panel cannot verify or reproduce the more specific cutoff in the preregistration.

**Required correction:** add the exact EDGAR acceptance timestamp (with timezone convention) to each panel row and enforce the frozen cutoff, or revise the preregistered availability rule before freeze to the auditable rule “a SIC filing dated d becomes usable on the first NYSE session strictly after d.” Do not infer intraday availability from `effective_from` alone.

### NIT — Staleness age bins and flag use different cutoffs

The builder's stale flag uses `_over_six_calendar_months`, while the adjacent constant and QA bins use 180 days (`STALE_DAYS = 180`, `91-180`, `>180`). A calendar six-month threshold can differ from 180 days by several days. The flag follows D4's stated “strictly more than six calendar months” convention, but the age-bin labels/counts should be described as separate 180-day diagnostics or use the same calendar-month function. Also, the variable `network_stale_gt_2q` and comment “older than two quarters” are shorthand; the implementation is strictly six calendar months, not a count of elapsed calendar-quarter boundaries.

## 12 EDGAR header spot-checks

For each row below I fetched the exact `source_url` stored in the SIC panel. All 12 returned HTTP 200; each `<ASSIGNED-SIC>` matched the panel's SIC value. This confirms the row's linked header and extracted value, but does not cure the issuer/ticker lineage error above.

| Panel ticker | Effective filing date | Panel / header SIC | EDGAR header |
|---|---:|---:|---|
| AAPL | 2024-11-01 | 3571 / 3571 | [header](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/0000320193-24-000123.hdr.sgml) |
| AMGN | 2024-02-14 | 2836 / 2836 | [header](https://www.sec.gov/Archives/edgar/data/318154/000031815424000011/0000318154-24-000011.hdr.sgml) |
| AXP | 2024-02-09 | 6199 / 6199 | [header](https://www.sec.gov/Archives/edgar/data/4962/000000496224000013/0000004962-24-000013.hdr.sgml) |
| BA | 2024-01-31 | 3721 / 3721 | [header](https://www.sec.gov/Archives/edgar/data/12927/000001292724000010/0000012927-24-000010.hdr.sgml) |
| CAT | 2024-02-16 | 3531 / 3531 | [header](https://www.sec.gov/Archives/edgar/data/18230/000001823024000009/0000018230-24-000009.hdr.sgml) |
| CSCO | 2024-09-05 | 3576 / 3576 | [header](https://www.sec.gov/Archives/edgar/data/858877/000085887724000017/0000858877-24-000017.hdr.sgml) |
| CVX | 2024-02-26 | 2911 / 2911 | [header](https://www.sec.gov/Archives/edgar/data/93410/000009341024000013/0000093410-24-000013.hdr.sgml) |
| DD | 2024-02-08 | 0100 / 0100 | [header](https://www.sec.gov/Archives/edgar/data/30554/000175567224000004/0001755672-24-000004.hdr.sgml) |
| DOW | 2024-01-31 | 2821 / 2821 | [header](https://www.sec.gov/Archives/edgar/data/1751788/000175178824000010/0001751788-24-000010.hdr.sgml) |
| DWDP | 2024-02-15 | 2821 / 2821 | [header](https://www.sec.gov/Archives/edgar/data/1666700/000166670024000008/0001666700-24-000008.hdr.sgml) |
| RTX | 2024-02-05 | 3724 / 3724 | [header](https://www.sec.gov/Archives/edgar/data/101829/000010182924000008/0000101829-24-000008.hdr.sgml) |
| WBA | 2024-10-15 | 5912 / 5912 | [header](https://www.sec.gov/Archives/edgar/data/1618921/000161892124000084/0001618921-24-000084.hdr.sgml) |

The WBA panel's first observation is 2015-10-28; there is no earlier WBA-ticker observation. This is consistent with the listed issuer/ticker history, but any pre-WBA predecessor ticker coverage must be separately mapped if the holdout expects that issuer lineage.

## D4 builder checks that passed static review

- **Filing availability:** `_next_session_index` calls `bisect_right`, selecting the first D4 development session strictly after the filing date. `filing_time_network` filters each manager's filing events to `usable_index <= t` before using its positions. Thus a filing dated d cannot enter a graph dated d; it can enter on the next session. This honors the Round 5 next-trading-day rule.
- **CLV window:** `build_clv5` uses `raw[:, t-4:t+1]`, requires all five sessions, and assigns the score at t. The source bars are date-filtered to 2020-11-27..2026-10-30 before OHLCV fields are parsed. This is same-close information and does not read future prices; D4's outcome starts at the next open.
- **Graph availability and normalization:** NCP uses the adjacency available at t after filing events with `usable_index <= t`. The adjacency is symmetric cosine overlap with zero diagonal; `weights = adjacency / row_sum` row-normalizes each nonzero row. NCP multiplies those weights by same-date CLV5, and sets inactive assets and zero-degree rows to unavailable. This matches the stated row-normalized peer-pressure construction.
- **Staleness:** graph-age and a stale flag are retained in the input artifact, and the code does not discard stale observations. The issue is the cutoff/diagnostic wording mismatch above, not an observed future-data path.

## Audit limitation

The SEC header spot-check is a schema and issuer-lineage audit only. It did not load price data, calculate any SIC-network outcome, or test D5's pair-coverage gate. The D4 QA's reported development coverage figures were not revalidated against price files.
