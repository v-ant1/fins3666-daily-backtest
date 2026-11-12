# R6 Idea Gate — J: within-industry short-horizon reversal

## Ranking and decision

| Rank | Direction | Gate assessment now | Judgmental chance of passing the complete R6 stack |
|---:|---|---|---:|
| 1 | Reverse a stock's weekly return relative to same-SIC2 peers | **FAIL-GATE for weekly power/economic transport; worth one tightly specified mechanism test only if the group accepts that risk** | 5% |
| 2 | Reverse a stock's trailing CLV pressure relative to same-SIC2 peers | **FAIL-GATE pending evidence that CLV isolates non-fundamental pressure; exploratory and weaker** | 2% |

The probabilities are judgment calls for clearing the frozen sign, mechanism and placebo gates, net Dow performance above EW30, Holm and DSR requirements, the turnover/cost hurdle, and the coordinator-only holdout. They are not the Monte Carlo powers below. Direction 1 ranks higher because it is closest to the published intra-industry reversal evidence; the substantial mismatch is that the lead paper uses monthly returns, while the proposed test is weekly and the Dow portfolio holds only five names.

No returns, forward outcomes, ICs, or holdout data were loaded or calculated for this review. Power inputs below are synthetic design assumptions and point-in-time roster/SIC coverage counts only.

## Verified literature and what it does (and does not) support

- Hameed and Mian, [“Industries and Stock Return Reversals,” *Journal of Financial and Quantitative Analysis* 50 (2015), 89–117](https://doi.org/10.1017/S0022109014000404), document **monthly** reversals relative to same-industry stocks, larger than market-relative reversals and present among large and liquid stocks. They attribute the effect to order imbalances/noninformational shocks and liquidity supply. This is the closest precedent, but it is neither a weekly result nor evidence about this post-2020 sample. The published abstract does not establish current mega-cap investability.
- Da, Liu, and Schaumburg, [“A Closer Look at the Short-Term Return Reversal,” *Management Science* 60 (2014), 658–674](https://doi.org/10.1287/mnsc.2013.1766), find that reversals are stronger after removing cash-flow-news-related returns; they link the long side to liquidity shocks and the short side to sentiment/short-sale constraints. Their result motivates separating pressure from information, but it is not a modern weekly SIC2 test.
- Lehmann, [“Fads, Martingales, and Market Efficiency,” *Quarterly Journal of Economics* 105 (1990), 1–28](https://doi.org/10.2307/2937816), reports one-week winner/loser reversals and argues that they remain after plausible transaction-cost corrections. It supports the horizon, not the industry-relative design or survival in today’s most liquid stocks.
- Nagel, [“Evaporating Liquidity,” *Review of Financial Studies* 25 (2012), 2005–2039](https://doi.org/10.1093/rfs/hhs066), interprets short-term reversal returns as compensation for liquidity provision and finds the expected compensation rises in market turmoil. It supplies a mechanism and a warning that unconditional effects may be weak.
- The skeptical large-firm evidence matters: Cheng, Hameed, Subrahmanyam, and Titman, [“Short-Term Reversals: The Effects of Institutional Exits and Past Returns,” *JFQA* (2016)](https://doi.org/10.1017/S0022109016000958), find reversal concentrated in past-quarter losers and report evidence consistent with market makers responding faster to changes in informed investors in the more recent period, particularly for large firms. This does not directly falsify Hameed–Mian, but weakens a broad claim that a simple weekly contrarian signal survives in mega-caps.

**Post-2010 assessment:** these sources establish historical mechanisms and, in Hameed–Mian, a large/liquid subgroup result. They do not establish that an unconditional weekly SIC2 reversal survives among mega-caps after 2020. The proposal is a falsifiable transport test, not an assumption that the premium persists.

## Planning power and cost calculation

### Synthetic weekly power (S&P 500 mechanism)

I ran `r4_harness/power_sim.py` for the 5-session horizon (NW Bartlett lag 4), with 297 weekly dates, 54 effective SIC2 clusters (median), and signal-series autocorrelation 0.20. The SIC2-cluster adjustment is an explicit sensitivity approximation: about 479 SIC-covered names / 54 groups = 8.87 names per group; assuming within-industry correlation 0.15 gives design effect `1 + (8.87 − 1) × 0.15 = 2.1805`. I used synthetic IC SD `sqrt(2.1805 / 53) = 0.2028`, i.e. the null-rank SD adjusted for clustering. Neither the ICC nor autocorrelation is estimated from returns or outcomes. This simulator models industry clustering by inflating date-level IC noise; it is not a two-way SIC2-by-date cluster bootstrap.

| Hypothetical mean Spearman IC | Simulated probability NW t ≥ 2 | Effective dates | 80% MDE |
|---:|---:|---:|---:|
| 0.0183 | 26.7% | 216.0 | 0.0392 |
| 0.0392 | 78.7% | 216.0 | 0.0392 |

Each row used 5,000 synthetic draws; seeds 20261115 and 20261116. The 0.0183 value is a planning scenario from the prior R6 power discussion, not a published industry IC or observed project result. Thus S&P estimation has enough dates to test a fairly large effect, but has poor power at that smaller scenario. Do not turn the monthly portfolio returns in Hameed–Mian into an IC estimate. A frozen mechanism run should use a SIC2-and-date clustered inference procedure, and the design should fail if its pre-specified effect does not clear the power rationale.

Reproducible command (the second run changes only the predeclared hypothetical mean effect):

```powershell
python r4_harness/power_sim.py --assets 54 --dates 297 --horizon 5 --signal-autocorrelation 0.2 --ic-sd 0.20283628287856098 --mean-ic 0.0183 --simulations 5000 --seed 20261115
python r4_harness/power_sim.py --assets 54 --dates 297 --horizon 5 --signal-autocorrelation 0.2 --ic-sd 0.20283628287856098 --mean-ic 0.0392 --simulations 5000 --seed 20261116
```

### Dow turnover and break-even hurdle

For an equal-weight top-five long-only portfolio among 30 names, keep four current holdings and permit at most one replacement on each weekly rebalance. One replacement sells 20% NAV and buys 20%, so total traded notional is about 40% of NAV, within the 50% cap; use the harness turnover convention (buys plus sells) and reject any rebalance above 50%. If more than one name would need replacement, the signal cannot trade all desired changes that week. This rule limits turnover but may dilute the signal; it is a constraint to test, not proof the portfolio can pass.

Using `r4_harness.phase3.break_even_rank_ic(turnover=0.40, return_dispersion=0.04, cost_per_side=0.0005, top_fraction=5/30)`, the illustrative break-even IC is **0.00346**. At the absolute 50% cap, it is **0.00433**. These use a **hypothetical 4% weekly cross-sectional return dispersion**, not measured project returns. The helper maps rank IC to top-quantile gross active return as `IC × dispersion × sqrt(12) × (0.5 − q/2)`; it treats turnover as total buy-plus-sell notional, so do not double it. At 40% turnover the cost is 2 bp per rebalance, or about 104 bp/year at 52 weekly rebalances; the stricter R6 rule that costs be <25% of gross edge requires at least 8 bp gross per week, equivalent to IC **0.01386** under these assumptions. At the cap the comparable hurdle is IC 0.01732. These are screening hurdles; register the dispersion source and compute actual turnover/costs from executed trades before any performance conclusion.

The Dow SIC2 universe is a serious limitation: based on development point-in-time SIC and date-key coverage, only about 16 names per sampled weekly date had at least one same-SIC2 peer (range 0–18), across roughly five active SIC2 groups. This cuts the eligible breadth nearly in half and can leave some industry groups unable to form an intra-industry rank. The input QA also shows an initial 2020Q4 Dow price-coverage gap; the frozen date rule must disclose and apply the data-availability start consistently, without choosing dates based on any outcomes. The S&P panel has around 479 SIC-covered names across 54 SIC2 groups on a typical weekly date, but S&P mechanism evidence does not substitute for Dow portfolio evidence.

## Direction 1 — weekly peer-relative return reversal (rank 1)

**Fixed question and sign:** At each weekly formation close, compute each PIT member's close-to-close return over the previous five sessions, less the equal-weight mean return of its other SIC2 peers over those same sessions. Rank only stocks with at least one other SIC2 peer. The registered prediction is **negative** next-five-session return relative to that stock's SIC2 peer group for a high relative-return score; equivalently, recent relative losers should outperform relative winners. Use next-session executable fills and make the exact signal/formation convention explicit before freezing.

- **(a) Literature — PASS for historical precedent, PARTIAL for this exact weekly design.** Hameed–Mian gives direct monthly intra-industry support, and Lehmann supports one-week stock reversal. Neither directly tests five-day within-SIC2 ranks on PIT mega-caps. Da–Liu–Schaumburg and Nagel provide plausible liquidity-pressure mechanisms.
- **(b) Large-cap/post-2020 case — FAIL as an established edge; testable hypothesis only.** Industry-relative returns can remove common industry news and isolate stock-specific noninformational pressure. However, the key large/liquid result is monthly and historical; faster market-making responses in large firms and uncertain post-2020 persistence cut against the case. Weekly reversal can also reflect bid–ask bounce, which must be controlled by the fill/return convention and not mistaken for tradable alpha.
- **(c) Power — FAIL at the 0.0183 planning effect.** The S&P SIC2-adjusted simulation reaches only 26.7% probability of NW t≥2 at IC 0.0183; the 80% MDE is about 0.0392. The S&P mechanism is feasible for a large effect, but the small eligible Dow peer cross-section cannot validate the edge with comparable power.
- **(d) Free-data feasibility — PARTIAL/PASS for inputs.** `r6_C1` contains daily adjusted OHLCV for point-in-time Dow and S&P rosters, and `r6_C1` / `r6_data` contain dated SIC2/SIC3 membership. No paid price source is needed. Dow coverage and the 2020Q4 gap must be resolved/disclosed; freeze exact observation eligibility and corporate-action treatment before measuring any outcomes.
- **(e) Novelty — modest.** This transports published industry-relative reversal to weekly SIC2 peer groups, PIT mega-caps, and a constrained Dow top-five portfolio. It is structurally different from D4's 13F common-owner network: links are SIC industry membership, and the signal is the target's return relative to its leave-one-out industry peer mean. It is not a claim that the general reversal effect is new.

## Direction 2 — weekly peer-relative CLV-pressure reversal (rank 2)

**Fixed question and sign:** Compute daily close-location value `CLV=(2C−H−L)/(H−L)` from adjusted bars, with a defined zero-range rule; sum over the preceding five sessions and subtract the equal-weight mean of the other PIT SIC2 peers' five-session CLV score. Rank eligible stocks cross-sectionally within the whole SIC2-covered universe. The pre-registered prediction is **negative** next-week within-SIC2 relative return for high relative CLV pressure. If desired, a trailing-only normalisation must be fixed in advance; do not search CLV windows or transformations after outcomes.

- **(a) Literature — PARTIAL.** Hameed–Mian, Da–Liu–Schaumburg, Lehmann, and Nagel support short-term reversal/liquidity provision generally, but they do not establish this OHLC-derived CLV score as a measure of signed buying pressure. CLV records where a close lies within its daily range, not buyer-initiated flow; it can respond to information and volatility as well as pressure.
- **(b) Large-cap/post-2020 case — FAIL/weak.** The same liquidity-provision story applies, but large-cap liquidity and faster arbitrageurs may make a daily range-location measure less persistent. There is no verified post-2020 mega-cap result for SIC2-relative CLV reversal. This hypothesis is more novel but less grounded than Direction 1.
- **(c) Power — FAIL at plausible small effects.** The design has the same weekly SIC2 calendar and cross-sectional breadth, so the same synthetic calculation applies: 26.7% power at IC 0.0183 and 80% MDE about 0.0392. CLV is noisier than a direct return measure unless a reliable pressure interpretation is established; no effect-size evidence justifies assuming a larger IC.
- **(d) Free-data feasibility — PASS for raw inputs, PARTIAL for score validity.** Adjusted daily OHLCV and dated SIC data are already available for development Dow/S&P universes. Validate range adjustment and define `H=L` handling before freeze; this checks input integrity only, not predictive power.
- **(e) Novelty — higher, but not sufficient.** Relative CLV is a distinct pressure proxy over SIC2 peers, not D4's ownership-network peer pressure. The novelty comes with a construct-validity problem: OHLC alone does not reveal order-side imbalance. Do not proceed unless a mechanism can be stated without relabelling CLV as observed buying flow.

## Recommendation

If one direction is retained, choose Direction 1 as a **new, capped mechanism test**, not a rescue or sign flip of a prior result. Its best evidence is monthly and old, S&P weekly power is low for modest ICs, and Dow peer coverage is narrow; freeze only if the team accepts a high probability of an inconclusive/failing mechanism. Direction 2 should remain second-choice because it adds a less validated proxy without improving power or Dow breadth. Neither proposal is currently a PASS-GATE, and neither should move to a portfolio run until the exact pre-registration, SIC2/date cluster inference, turnover rule, endpoint family, and pass/fail thresholds are frozen.
