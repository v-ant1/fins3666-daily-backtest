# R5-L3 rank-2 index-change feasibility

## Scope and rule

I searched S&P Dow Jones Indices press releases for Dow Jones Industrial Average component additions and deletions announced from **2020-11-01 through 2026-10-30**. The R5-L3 input-only rule requires at least **20 distinct source-event dates**; fewer than 20 means **INFEASIBLE**. I counted one independent event per official DJIA announcement date, not per addition/deletion ticker, because one press release can announce multiple paired changes. I used only the announcement text and D4 input graph structure. I did not load prices, returns, CLV, NCP, signals, or holdout data.

## Official announcements and event-date peer support

| Announcement date | Effective date | DJIA additions / deletions | D4 graph support on first following session | In-universe source-to-peer pairs available at response |
|---|---|---|---|---:|
| 2024-02-20 | 2024-02-26 | Add AMZN; delete WBA | 2024-02-21: 30 active names; 435/435 undirected links (870 directed matrix entries) | WBA: 29; AMZN: 0; total 29 |
| 2024-11-01 | 2024-11-08 | Add NVDA and SHW; delete INTC and DOW | 2024-11-04: 30 active names; 435/435 undirected links (870 directed matrix entries) | INTC: 29; DOW: 29; NVDA: 0; SHW: 0; total 58 |
| 2026-06-23 | 2026-06-29 | Add GOOGL; delete VZ | 2026-06-24: 30 active names; 435/435 undirected links (870 directed matrix entries) | VZ: 29; GOOGL: 0; total 29 |

Sources are the official [Feb. 20, 2024 S&P DJI release](https://press.spglobal.com/2024-02-20-Amazon-com-Set-to-Join-Dow-Jones-Industrial-Average-Uber-to-Join-Dow-Jones-Transportation-Average), [Nov. 1, 2024 S&P DJI release](https://press.spglobal.com/2024-11-01-NVIDIA-and-Sherwin-Williams-Set-to-Join-Dow-Jones-Industrial-Average-Vistra-to-Join-Dow-Jones-Utility-Average), and [June 23, 2026 S&P DJI release](https://press.spglobal.com/2026-06-23-Alphabet-Set-to-Join-and-Honeywell-International-to-Remain-in-Dow-Jones-Industrial-Average). Each identifies the DJIA changes and effective date. The earlier [Aug. 24, 2020 release](https://press.spglobal.com/2020-08-24-Salesforce-com-Amgen-and-Honeywell-International-Set-to-Join-Dow-Jones-Industrial-Average) is outside this window and is excluded. No other DJIA-specific addition/deletion announcement appeared in the S&P press-release review for the requested period.

Peer counts come from `r4_harness/runs/D4/D4_INPUTS.npz`, loading only `assets`, `dates`, `roster_mask`, and `adjacency` to inspect the support graph on the first session after each date-only announcement. D4's daily network coverage table independently reports the same dense support: 435/435 positive undirected links on these sessions. An in-roster source therefore has 29 other Dow names with supported common-owner links. An announced entrant has zero D4 graph peer pairs at the response session because it has not yet joined the point-in-time Dow roster. Counts are input structure only; they say nothing about event returns or the effect of index pressure.

## Verdict: INFEASIBLE

There are **3 independent announcement dates**, against the fixed minimum of **20**. Counting individual ticker actions instead gives **8** records (four additions and four deletions), which is also below 20 and does not create independent event dates. The graph supplies many candidate peers for incumbent deletions, but that breadth cannot compensate for event scarcity; entrants also lack an in-universe common-owner edge at their event response. Under the registered rule, the rank-2 index-change direction is **INFEASIBLE before outcome analysis**. Do not inspect outcomes, relax the threshold, or broaden the event universe to rescue it.
