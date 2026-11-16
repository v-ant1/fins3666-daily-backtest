# Dossier 5 — Directed within-industry leader-to-follower pressure

## Pitch and thesis fit

Test whether a large/attention-grabbing Dow firm’s daily pressure leads lower-dollar-volume firms in the same point-in-time industry. This keeps the spread component of Advik’s thesis but replaces symmetric, same-window return correlation with a one-way, lagged leader-to-follower relation. The source signal is OHLCV close-location value, so the proposal is a pressure proxy, not direct signed trade flow. With 30 large firms, a thin same-industry graph is a likely failure, not something to repair after seeing outcomes.

## L1 root causes this addresses

L1’s five-day pressure blend had close-to-close IC +0.0034 (NW t=0.34); heat had −0.0015 (t=−0.12), and plain-neighbor average −0.0034 (t=−0.29). The mix offsets components: signed volume was negative while CLV and intraday-minus-overnight were positive. CLV’s one-day next-open-to-close IC was +0.0142 (t=2.34), with two-day t=2.05 and five-day t=1.40. D5 isolates a component with short-horizon evidence and asks whether pressure propagates directionally within a dated industry. It addresses root causes 1–3, but cannot solve weak effective breadth, regime instability or costs. L1’s top-five heat strategy had 161.2% weekly turnover, 8.06 bp cost and net Sharpe 0.64 versus EW30 0.92; this dossier imposes a mechanism gate and a 50%-turnover ceiling.

## Mechanism and verified evidence

Hou (2007) attributes much of the stock lead-lag effect to industry information diffusing from large firms to small firms; negative news adjusts sluggishly. Its result is monthly and especially strong for small, neglected firms and less competitive industries. This makes the direction and mechanism interpretable but makes Dow applicability weak. Menzly and Ozbas (2010) likewise document cross-predictability among economically linked industries, with weaker relations for more covered/owned firms. These papers do not establish a modern daily large-cap pressure effect or after-cost result.

- Hou (2007), “Industry Information Diffusion and the Lead-lag Effect in Stock Returns,” *Review of Financial Studies*: [DOI](https://doi.org/10.1093/rfs/hhm003), verified L3 Evidence Card 6. Accessible primary abstract supports the large-to-small, within-industry direction; the L3 card correctly supplies no unverified table statistic.
- Menzly & Ozbas (2010), “Market Segmentation and Cross-predictability of Returns,” *Journal of Finance*: [DOI](https://doi.org/10.1111/j.1540-6261.2010.01578.x), verified L3 Evidence Card 2. Monthly linked-industry evidence; exact table estimate is not asserted here because it was unavailable in the opened record.
- Lo & MacKinlay (1990), “When Are Contrarian Profits Due to Stock Market Overreaction?,” *Review of Financial Studies*: [DOI](https://doi.org/10.1093/rfs/3.2.175), L3 Evidence Card 7 is marked **UNVERIFIED** for detailed claims; it is not used as quantitative support.
- Proxy limitation: Chordia, Roll & Subrahmanyam (2002): [DOI](https://doi.org/10.1016/S0304-405X(02)00136-8), L3 Card 21; daily OHLCV bars cannot recover signed trade initiation.

## Exact signal and network

Build point-in-time industry membership from each firm’s latest public 10-K filing header as of the signal date. Use two-digit SIC as the predeclared broad industry grouping; do not use the current SIC snapshot for historical dates. For each pair in the same active SIC group, orient the edge `i → j` when source `i` has a greater trailing 60-session mean dollar volume than follower `j`, where dollar volume is close × volume. Freeze each day’s rank using only information through *t−1*. Define source pressure as `CLV_i,t=(2C−H−L)/(H−L)` (zero when H=L) and follower network pressure `LP_j,t = mean_i(CLV_i,t)` across higher-dollar-volume, same-SIC source firms, weighting by lagged ADV20 dollars and excluding self-links. Use the correctly spelled `CLV` symbol in code; no signed-flow interpretation. At close *t*, test follower `j`’s next-session open-to-close residual return and next-session CLV conditional on its own lagged CLV/return, market return, and industry return.

The network is directed from higher to lower trailing dollar volume, changes only using dated public SIC and lagged OHLCV, and is not estimated from future returns or same-window correlations. If a follower has no valid higher-volume same-SIC source, it has no network signal; do not widen the industry rule to make the graph denser. The exact 60-session ranking is a design choice, not a tuned optimum.

L4’s `NETWORK_DATA.md` confirms a current SIC snapshot and explains that annual 10-K headers could be parsed to reconstruct a dated SIC history for both periods. It has **not** built that point-in-time series; current SIC is not acceptable as a substitute. Its data inventory says SEC customer-supplier disclosures are sparse and often anonymized, so D5 uses industry labels rather than claiming a complete supplier/customer graph. Daily Dow OHLCV is present for development; holdout OHLCV has the separate KFT/DWDP/WBA gaps and UTX/RTX lineage caveat.

## Prediction and mechanism test

**Prediction:** positive CLV at a higher-dollar-volume same-industry leader at day *t* predicts positive follower residual open-to-close return and/or follower CLV at *t+1*. This is a next-session test of directed pressure/information diffusion. Literature support is monthly and old-sample; the daily sign is the explicit new prediction, not a reported paper result.

First test the directed source-pressure slope/IC, conditional on recipient own CLV and common market/industry moves. Primary horizon is one non-overlapping session, with NW lag 0. Require positive coefficient and NW t≥2; require the reversed-edge and shuffled-link placebos to be insignificant. Report how many valid edges, source/follower pairs, and filing-date SIC changes occur each date. If the network is too sparse to form a stable date-level test, report infeasible rather than broadening SIC after looking at outcomes.

**Placebos:** (1) reverse every leader→follower edge (lower-volume to higher-volume); (2) degree-preserving shuffled links within the same dated SIC group; (3) future source CLV as timing placebo. A similar response for reversed or shuffled links falsifies directional transmission.

## Portfolio design after the mechanism gate

Only after the primary predictive test passes, hold the equal-weight top five follower names by the frozen `LP` signal, rebalanced weekly at next-session open. This concentration gives approximately 83% active share versus EW30, above the required 50%. Cap total traded notional per rebalance at 50% of NAV; otherwise stop unless measured costs stay below one quarter of gross edge. No sector-level fallback or long-short switch may be selected after outcomes.

## Variants and selection rule

Maximum of three fixed variants; primary is frozen before future returns are joined:

1. **Primary:** two-digit point-in-time SIC × 60-session dollar-volume leader ranking × CLV.
2. Same dated graph and ranking with leader intraday-minus-overnight return instead of CLV.
3. Four-digit SIC as a predeclared finer-industry sensitivity, only if filing headers actually report it consistently; no fallback to two-digit based on which result is stronger (variant 1 remains primary).

Only variant 1 determines go/no-go. Variants 2–3 cannot rescue a failed primary. These are three fixed definitions, not parameter sweeps.

## Strongest objection and falsifier

All Dow names are large, so the size/attention gap within industries may be small; industries represented by 30 members may yield few valid leader/follower pairs. Daily dollar volume is an imperfect proxy for attention/size, and information diffusion may be faster in current megacaps than in Hou’s historical small/neglected stocks. The current SIC snapshot is not PIT, while 10-K parsing and identifier changes consume time; costs may exceed a fleeting daily effect. The weakest evidence is extrapolating an old monthly return lead-lag in smaller stocks to daily CLV pressure in the Dow. Falsify if the primary directed signal does not predict the next-session follower response after own/market/industry controls, or if reversed/shuffled links are comparable.

## Feasibility, effort and risk

Scores: 1=low, 5=high; effort and risk worsen as scores rise. **Development feasibility 2/5:** OHLCV is available, but L4 has only a current SIC snapshot; dated 10-K parsing is feasible in principle, not yet produced. **Holdout feasibility 2/5:** historical 10-K headers exist and can in principle give dated SIC for 2010–20, but the panel is unbuilt and Dow price lineages are incomplete. **Effort 4/5; risk 5/5.** Before either test, confirm historical SEC 10-K header completeness/identifier mapping and resolve the holdout price route. Do not access holdout outcomes unless the coordinator approves a route and freezes the specification.

