# S2 design for a hypothetical 2010–2020 FactSet holdout

**Tag: L-S2F. Design only.** Assumed holdout: point-in-time S&P 500 membership and historical security master, including inactive/delisted names and delisting returns, 2010-01-04 through 2020-10-30 (approximately 2,700 sessions). No signal, IC, portfolio, price, return, or other outcome was computed. No sealed directory or pre-2020-11-27 price/return values were opened.

## Power rerun

Family size is fixed at three confirmatory tests (J2 plus at most two S2); conservative first Holm step is one-sided α=.05/3. The 80%-power normal multiplier is z(1−.05/3)+z(.80)=2.970. Scaling the prior T≈1,215-session design by √(1215/2700)=0.671 and replacing its Holm-26 multiplier 3.73 with 2.970 gives the synthetic ρ=.8 rank-weighted Cap50 base at approximately .0165 weekly and .0369 monthly IC before tier-cost uplift. Applying the prior R7 tier-cost uplift (5/10/20 bp one-way half-spread by liquidity tercile, charged on strategy and same-schedule EW benchmark trades) gives a planning estimate of **about .021 weekly and .034 monthly IC** for the 500-name S&P design. Treat these as approximate bands (.020–.022; .033–.035): cost scaling is inherited from the R7 synthetic method, not estimated from returns. Only ρ=.8 rank-weighted top-half Cap50 clears the 50% active-share floor in the documented design; lower persistence and narrower shapes require larger effects or fail that floor. These thresholds are power requirements, not measured effects.

For event tests, use independent event counts over 10.8 years and the same multiplier 2.970. Under the prior 5% event-CAR SD assumption, MDE = 2.970×SD/√N_eff:

| Design | Planning event count | 80%-power MDE | Evidence comparison |
|---|---:|---:|---|
| S&P additions or deletions, tested separately | ≈216 each (≈20/year) | ≈1.01% CAR | Published 2010–2020 means are +0.8% additions and −0.6% deletions. Neither clears 5% SD case. At an optimistic 2% SD the MDE is ≈0.40%; this sensitivity would clear the means but is unsupported by a measured event variance. |
| Month-end, four-session market window | ≈130 | ≈0.63% CAR | ≈0.4% cumulative cited effect; below MDE and market-wide, not cross-sectional stock pressure. |
| Quarter-end, four-session window | ≈43 | ≈1.09% CAR | No matched post-2010 S&P stock-level forced-flow CAR. |
| Secondary offering, three-session announcement window | ≈54–162 (5–15/year planning range) | ≈2.02%–1.16% CAR | −2.5% cited estimate is from 1997–2006; it is announcement repricing, not a current forced-sale reversal estimate. |
| Lockup expirations / dividend ex-dates / ETF flows | No defensible S&P event count/effect pair established | Not estimable | FactSet security data alone does not supply the necessary dated lockup, dividend, or fund-creation/redemption event series. |

Event dependence/clustering lowers effective N and raises these MDEs. No outcome-derived variance is used.

## Re-ranked leads

| Rank / lead | Forced-trading mechanism and distinctness from J2 | Evidence and 80%-power requirement | Decision |
|---|---|---|---|
| 1. S&P additions | Index funds must buy new constituents; temporary demand may persist to effective date. Event CAR is distinct from J2's five-session industry-relative reversal. | Post-2010 +0.8% addition effect vs ≈1.01% MDE at 5% event SD; deletion −0.6% likewise below its ≈1.01% MDE, and no adequately powered post-effective reversal magnitude. [Chen et al.](https://www.nber.org/papers/w30748) | Closest forced-flow lead, but does not clear the conservative power case. No prereg. |
| 2. Days-to-cover / short interest | Constrained crowded shorts may be forced to buy to cover; informed shorting can also predict weakness. Distinct from J2's industry-relative reversal. | Prior 1.19% monthly low-minus-high spread (1988–2012) converts to ≈.038 pseudo-IC by the old rough convention, only slightly above ≈.034 monthly planning hurdle. This is not a reported rank IC and is not an isolated post-2010 estimate; effect, persistence, and transaction timing are unverified. [Hong et al.](https://www.nber.org/papers/w21166) | Not a defensible 80%-power pass; FactSet can fix data availability but not evidence mismatch. No prereg. |
| 3. Analyst recommendation/estimate revisions | Mandate-following managers can react to upgrades/downgrades or estimate changes; drift can persist as investors process information. Mechanism differs from J2. | A published study reports disappearance of significant average post-revision drift in 2003–2010; another conditional result reports drift by prior-return state but gives no matched S&P rank effect at the ≈.021 weekly / ≈.034 monthly hurdle. [Research paper](https://www.sciencedirect.com/science/article/pii/S0304405X15001713) | FactSet/IBES vintages make the signal observable, but no matched effect supports 80% power. No prereg. |
| 4. Industry momentum | Slow diffusion and industry-linked flows can sustain winners; distinct direction/mechanism from J2 reversal. | Legacy ≈.014 pseudo-IC is below both cost-aware cutoffs and has no matched post-2010 S&P estimate. [Moskowitz & Grinblatt](https://doi.org/10.1111/0022-1082.00146) | Drop. |
| 5. 52-week high | Anchoring can sustain demand, distinct from J2 but not a forced trade. | Legacy ≈.014 pseudo-IC is below both cutoffs; no post-2010 matched estimate. [George & Hwang](https://doi.org/10.1111/j.1540-6261.2004.00695.x) | Drop. |
| 6. Offerings / lockups | New share supply or contractual unlock can produce forced selling and possible absorption. | Event MDE ≈1.16–2.02% at assumed 5% SD; quantified −2.5% SEO result is pre-2010 and announcement-based; no post-2010 S&P reversal estimate or verified event rate. | Drop. |
| 7. Turn-of-month / quarter-end | Calendar-constrained institutional trades may generate temporary common demand; not a stock-selection mechanism. | Month-end MDE ≈.63% vs ≈.4% cited four-day broad-market effect; quarter-end MDE ≈1.09%; neither is a matched stock-level S&P effect. | Drop. |
| 8. Dividend ex-date / ETF flows / PEAD / overnight pressure / abnormal volume | Potential scheduled, fund-flow, information, or attention pressure. | No complete post-2010 S&P effect-size plus event-count estimate meets the corresponding hurdle; several require event or consensus feeds beyond the specified FactSet fields. | Drop. |

## Disposition and governance

**No S2 survivor; no `S2_<name>.md` draft.** The FactSet premise solves the prior point-in-time/delist coverage blocker, but not the power-and-evidence gate. Index additions are below the conservative event MDE; DTC is borderline only under a non-matched pseudo-IC; analyst revisions have observable vintages but no credible effect magnitude at the required hurdle. None supports an honest 80%-power preregistration. J2 remains in the family, so any later S2 must be frozen and hashed before any family member opens this holdout.

The portfolio design, if revived after new independent evidence, must use weekly/monthly rank-weighted top-half Cap50 at fixed sign/horizon; no-signal dates hold the same-universe EW benchmark; benchmark is EW of the same PIT universe and same schedule; apply 5/10/20 bp one-way half-spread tiers to both strategy and benchmark; 50% total-notional turnover cap; missing delisting return is −30% for performance delists and 0% for merger/acquisition. DSR trial accounting must include all prior R6/R7/R9/D1/S2 exploratory attempts and any new development trials; no new S2 outcome trial was run here, so trial counts are not incremented. A shared FactSet holdout opens only after all family members are frozen and hashed and the user approves.

Sources for historical effect sizes and mechanisms are linked in the candidate table and S2_ROUND2/S2_ROUND3. Design follows `specs/r9_rules.md`/J1's availability discipline; no holdout computation or data access is authorized by this design.

