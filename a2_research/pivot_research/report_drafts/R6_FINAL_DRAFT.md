# R6 Final Report — Draft

**Status: final development-results draft; no holdout result.** R6 registered three variants (3/30) and completed the authorized development runs for D1, E1, and J1. None passes the full R6 criteria: D1 is a mechanism near-miss that is **NOT passing**, E1 is a clear mechanism failure, and J1 confirms its pre-registered mechanism but fails the Dow portfolio Sharpe gate. The sealed holdout has not been opened.

## Executive summary

J1's weekly SIC2-relative reversal mechanism passed its raw development gates (direction-adjusted mean IC 0.01479, NW t(4)=2.077; SIC2 shuffle p=0.002), but the top-five Dow portfolio did not pass: net Sharpe was 0.823 versus 0.902 for EW30, with a block-bootstrap p=0.449. An independent reproduction matched the mechanism statistic and placebo p-value to three significant figures and independently confirmed a lower Sharpe, although its cumulative net-excess return does not reconcile with the official run. D1 had the expected sign and passed its placebo, but t=1.908 fell short of the required 2.0; E1 had negative IC and failed its placebo, so its portfolio endpoint was not run.

The nine-slot R6 Holm family contains raw outcomes for H1, H2, H4, H5, H7, H8, and H9; H3 and H6 were not run. The final saved family-adjusted values are reported below. Decision 76 identifies criterion 4 on the 30-stock Dow as the binding feasibility hurdle, and decision 79 concludes that free-data idea generation is saturated absent licensed inputs or a user-directed change to the fixed criteria.

## Idea-gate record

All results below are gate decisions, not investment outcomes unless explicitly stated. **FAIL-GATE**, **FAIL**, **parked**, **deprioritised**, and **NOT passing** are not passes.

| Round | Outcome | Main reason |
|---|---|---|
| A | All four ideas **FAIL-GATE** after red-team. | Common-owner reversal was too close to an earlier result and had dense links, weak directional identification, and inadequate power or data. |
| B | All four **FAIL-GATE**; B4 tested as a feasibility candidate and failed. | Analyst/co-coverage links lacked point-in-time free coverage; GDELT co-mention graph was dense and Dow power was 41% at IC 0.01. |
| C | **FAIL-GATE as written**; C1 conditionally revived then deprioritised. | Initial cluster and SIC inputs were inadequate; corrected SIC3 power was 32% at the planned effect. C2/C3 also lacked power or free historical data. |
| D | Initially **FAIL-GATE**; D1 advanced conditionally and was frozen. | D1 had free Reg SHO coverage and 63% S&P power at the planning effect after cluster stress, but its realized NW t was 1.908, below 2.0. D2/D3 were dropped. |
| E | All initial directions **FAIL-GATE** under the original Dow-only power framing; E1 advanced after decision 17 clarified S&P mechanism estimation. | Monthly costs were lower, but customer-supplier coverage and peer-high evidence did not clear the gates. E1 later failed its mechanism and placebo. |
| F | Form 4 insider buying / peer spread **FAIL-GATE**. | Approximately one matched Dow event per quarter was too sparse for useful power. The SEC panel was retained as data only. |
| G | Volume-shock/visibility idea **parked; did not pass**. | SIC3-cluster MDE was about IC 0.036 and post-2020 large-cap evidence was thin. |
| H | ETF-to-constituent and DIA ideas **FAIL-GATE**. | Effective sector breadth was about 11 clusters; DIA gave only one source shock per date and no valid Dow cross-sectional ranking. |
| I | Seasonal buying pressure **FAIL-GATE**. | A holdout-safe one-year lag left 59 monthly observations and low power. |
| J | J1 allowed one frozen mechanism test despite an explicitly weak power case; idea gate was not a claim of empirical success. | S&P cluster power was 26.7% at IC 0.0183 (80%-power MDE about 0.0392). The registered mechanism passed, but the portfolio failed. |
| K | Both earnings-announcement pressure and peer transfer **FAIL-GATE**. | Season and SIC2 clustering left only 11–15% power at the cost hurdle; the proposed event-return measures were not evidence of buying flow. |
| L | FINRA short-interest / days-to-cover **FAIL-GATE**. | Monthly SIC2 power was low, and the free all-listed 2010–2020 history needed for the holdout was not verified. This is not a D1 rescue: short interest is a bi-monthly stock of outstanding positions, unlike daily Reg SHO short-sale volume. Licensed historical data may be considered only if access and coverage are verified. |
| M | Evidence-targeting survey; no new direction advanced. | No untried free-data pressure effect was found with documented large-cap, post-2010 effect size above the cluster MDE. |
| N | Cybersecurity-breach peer pressure and serial activist campaigns **both FAIL-GATE**. | Synthetic power was below 14% at planted monthly IC 0.02 (80%-power MDE about 0.10–0.14), with event coverage and sign uncertainty unresolved. |
| O1 | Flow/ownership pressure **FAIL-GATE**. | The best cited full-sample Sharpe was 0.75, below the roughly 0.8 criterion-4 feasibility screen even before costs; it did not establish a post-2010 mega-cap effect. |
| O2 | Cross-asset and macro pressure: no viable candidate. | Published ETF-flow evidence was daily and used paid inputs; mutual-fund allocation evidence ended in 2008 and did not establish Dow excess Sharpe. Neither supported the required post-cost portfolio edge. |

The gate record reflects decisions and source dossiers in [the decision log](../specs/r6_decisions.md), [round K](../r6_ideas/K.md), [round L](../r6_ideas/L.md), [round M survey](../r6_ideas/M_SURVEY.md), [round N](../r6_ideas/N.md), [round O1](../r6_ideasO1.md), and [round O2](../r6_ideasO2.md). Earlier rounds A–J are detailed in the idea dossiers linked from the [idea folder](../r6_ideas/).

## Frozen directions and development results

### D1 — daily FINRA Reg SHO short-volume pressure

D1-V1 measured a five-session average of matched facility short-volume ratio, signed as negative pressure, with a five-session forward horizon. The S&P 500 mechanism result had the expected sign and cleared the IC floor, but did not clear the pre-registered NW t threshold. The SIC2 shuffle passed; the sequence therefore stopped before the Dow portfolio.

| Endpoint | Development result | Holm adjusted p | Status |
|---|---|---:|---|
| R6-H1 mechanism | Mean IC 0.0093742; NW t(4) 1.908; IC floor passed, t≥2 failed; raw p=0.028195 | 0.169170 | **FAIL — near-miss, NOT passing** |
| R6-H2 SIC2 shuffle | Observed IC 0.0093742; null p95 0.0042863; raw p=0.001996 | 0.017964 | Placebo passed; does not rescue H1 |
| R6-H3 Dow portfolio | Not evaluated after H1 failed | Not run | **not run** |

The mechanism was independently reproduced (IC 0.00937; t=1.91). The run retained the placebo p95 and p-value but not all 500 shuffle draws; that limitation is disclosed. See [D1 results](../r6_D1/RESULTS.md) and [reproduction](REPRO_D1.md).

### E1 — monthly SIC2 peer CLV pressure

E1-V1 used prior-month CLV pressure among leave-one-out same-SIC2 peers, estimated at a 21-session horizon on the S&P PIT universe, with a monthly top-five Dow portfolio if mechanism gates passed. Input coverage passed: S&P member-day OHLCV-plus-dated-SIC coverage was 95.1%, Dow coverage 98.4%, and all 72 eligible formation dates met the 250-name threshold. The 51-name historical S&P price gap was handled with the predeclared date-wise exclusion. E1's portfolio was not run after the mechanism and placebo failed.

| Endpoint | Development result | Holm adjusted p | Status |
|---|---|---:|---|
| R6-H4 mechanism | Mean IC −0.004543; NW t(20) −0.2407; raw p=0.595093 | 1.000000 | **FAIL** |
| R6-H5 SIC2 shuffle | Observed IC −0.004543; null p95 0.009595; raw p=0.812375 | 1.000000 | **FAIL** |
| R6-H6 Dow portfolio | Blocked by H4/H5; no portfolio outcomes computed | Not run | **not run** |

All 500 E1 shuffle means are retained in the [E1 result bundle](../r6_E1/RESULTS.md). H6 portfolio returns, Sharpe, costs, turnover, active share, bootstrap p, and DSR are **not estimated**, not zero.

### J1 — weekly SIC2-relative return reversal

J1-V1 ranked a stock by its trailing five-session return relative to its leave-one-out SIC2 peer mean, predicting a negative next-five-session peer-relative return. There were 298 Dow formation dates; ten early rebalances were skipped for insufficient signal coverage. In the S&P mechanism input, 286 of 298 dates had at least 250 eligible names. The frozen run was authorized once after two failed pre-analysis attempts; those attempts were errors/input defects, not extra variants:

1. **Run #1:** portfolio-stage crash because a held Dow name lacked a close. No accepted outcome values were saved. Decision 63 fixed missing-close marking and liquidation handling for both strategy and EW30; decision 65 identified the GOOGL in-window gap and required rebuilding the price panel from the same-source S&P bars. This was disclosed as an implementation/input deviation.
2. **Run #2:** stopped before analysis because the signal bundle used the prior Dow price panel and failed the trailing-signal consistency check. No outcomes were computed; decision 67 created the coordinator-owned H1–H9 family record, and decision 68 ordered a signal-only input rebuild. Decision 69 relaunched the input worker after its terminal had exited.
3. **Run #3:** authorized by decision 70 after the input reconciliation passed; the sole official development execution produced complete results. Decisions 64 and 66 required independent H7/H8 reproduction before accepting the portfolio interpretation.

| Endpoint | Official result | Holm adjusted p | Status |
|---|---|---:|---|
| R6-H7 mechanism | Direction-adjusted mean IC 0.0147863; NW t(4)=2.07704; IC floor 0.0034641 passed; raw p=0.0188989 | 0.132292 | Raw mechanism gate **PASS**; family adjusted decision retain |
| R6-H8 SIC2 shuffle | 500 draws, seed 20261111; observed IC 0.0147863 > p95 0.00560598; p=0.00199601 | 0.017964 | Raw placebo gate **PASS**; family adjusted decision reject |
| R6-H9 Dow portfolio | Net cumulative excess +1.028%; gross excess +14.911%; costs 10.357% (66.2% of gross excess); net Sharpe 0.82318 vs EW30 0.90227; turnover 48.174% mean / 50% cap; active share 54.768%; block-bootstrap p=0.449110 | 1.000000 | **FAIL — NOT passing** on Sharpe and bootstrap evidence |

Portfolio diagnostic results: gross return was 110.784% for J1 and 95.874% for EW30; net return was 96.214% and 95.187%. The turnover cap and active-share checks passed, but the Sharpe comparison and overall portfolio criterion did not. DSR used the cumulative trial count of 3 and was 5.23316e−209.

The independent [J1 reproduction](REPRO_J1.md) matched H7 and the randomization p to three significant figures (IC 0.0148; t=2.08; p=0.00200). Its shuffle p95 was 0.00574 versus the official 0.00561 because the reference helper orders SIC2 groups differently before applying the same fixed seed; both distributions place the observation above their 95th percentile. The independent portfolio replay confirmed the Sharpe failure (0.815 vs 0.902), but its cumulative net excess was −2.66%, not the official +1.03%. That cumulative-excess discrepancy remains **unreconciled**; it does not change the NOT passing Sharpe/portfolio conclusion. The official H9 bootstrap p remains 0.449 (Holm 1.000).

## Final R6 Holm family — H1 through H9

This is the coordinator-owned family in `r6_J1/RESULTS.md`; it reports all nine frozen slots. “Not run” means no endpoint statistic was computed. Holm-adjusted values are copied from the saved final family table; this report does not recompute them.

| Endpoint | Direction / test | Raw p | Holm adjusted p | Status |
|---|---|---:|---:|---|
| H1 | D1 S&P mechanism | 0.028195 | 0.169170 | **FAIL — NOT passing** |
| H2 | D1 SIC2 placebo | 0.001996 | 0.017964 | Placebo pass; H1 failed |
| H3 | D1 Dow portfolio | Not run | Not run | **not run** |
| H4 | E1 S&P mechanism | 0.595093 | 1.000000 | **FAIL** |
| H5 | E1 SIC2 placebo | 0.812375 | 1.000000 | **FAIL** |
| H6 | E1 Dow portfolio | Not run | Not run | **not run** |
| H7 | J1 S&P mechanism | 0.018899 | 0.132292 | Raw gate passed; Holm adjusted decision retain |
| H8 | J1 SIC2 placebo | 0.001996 | 0.017964 | Raw gate passed; Holm adjusted decision reject |
| H9 | J1 Dow portfolio | 0.449110 | 1.000000 | **FAIL — NOT passing** |

Holm labels “reject” and “retain” refer to family-wise hypothesis-test decisions; they do not by themselves define whether the strategy passes all criteria. J1's raw mechanism and placebo gates passed, but H7 was not family-significant and the portfolio H9 failed. No absent portfolio endpoint is represented as an observed p-value.

## Feasibility, deviations, and conclusion

Decision 76 states that the binding constraint is criterion 4: a top-five Dow strategy versus EW30 needs one-sided block-bootstrap significance after Holm over roughly six years, which implies expected annualized excess Sharpe around 0.8 or higher after costs at no more than 20% turnover. J1's official portfolio p was 0.449 and its net Sharpe lagged EW30; the published effects screened in O1/O2 do not supply a credible way over this hurdle.

Decision 79 assesses free-data idea generation as saturated after fourteen idea rounds (A–O, with M an evidence survey) and three executed directions: D1 near-miss, E1 null, and J1 mechanism pass/portfolio fail. It records zero full R6 passes. The remaining data paths are licensed: FactSet/I-B-E-S for analyst co-coverage, Revere for supply-chain links, and Compustat or FactSet for historical short interest. Availability and user entitlement must be confirmed through the user's UNSW access; no such licensed input was used in these tests. Changing the fixed criteria is a user decision, not a coordinator or worker decision.

Disclosed deviations and limitations:

- **Variant count:** 3/30 (D1-V1, E1-V1, J1-V1); the two failed J1 attempts were not variants.
- **Price coverage:** unresolved S&P PIT price gaps were excluded date by date under decision 27; the 54-ticker survivorship gap and the J1 Dow roster/bar gap are disclosed. No missing forward outcome was fabricated.
- **J1 missing bars:** decisions 63 and 65 added the fixed held-name close marking rule and rebuilt the GOOGL price history from same-source S&P bars before run #3. The safety rule is an implementation deviation, disclosed above.
- **Placebo reproduction:** official and independent J1 placebo p95 values differ slightly because of SIC2 group iteration order; mean IC, NW t, and p-value match.
- **Portfolio reproduction:** independent J1 cumulative excess does not reconcile with official output; both Sharpe checks show J1 below EW30, and the official bootstrap/Holm values remain as reported.
- **Holdout:** no holdout prices, signals, returns, or results are reported here. Any future holdout execution is coordinator-only and must follow the frozen R5 protocol and criterion 5 exactly.

**Conclusion:** As of this draft, R6 has **0 full passes**. J1 is a mechanism-confirmed near-miss that is **NOT passing** because its after-cost Dow Sharpe and bootstrap result do not beat EW30; D1 is a near-miss at t=1.91 and is also **NOT passing**. E1 failed clearly, and no later idea round supplies a credible free-data route past the criterion-4 feasibility hurdle.

## Source artifacts

- [R6 decision log](../specs/r6_decisions.md), [R6 trial log](../specs/r4_trials.md), and [Holm family manifest](../specs/r6_holm_family.json).
- [D1 preregistration](../specs/r6_prereg/D1.md), [D1 results](../r6_D1/RESULTS.md), and [D1 independent reproduction](REPRO_D1.md).
- [E1 preregistration](../specs/r6_prereg/E1.md) and [E1 results](../r6_E1/RESULTS.md).
- [J1 preregistration](../specs/r6_prereg/J1.md), [J1 results](../r6_J1/RESULTS.md), and [J1 independent reproduction](REPRO_J1.md).
- [Rounds K–N](../r6_ideas/) and [O1](../r6_ideasO1.md) / [O2](../r6_ideasO2.md) screening notes.

*This draft synthesizes saved decisions and results only. It adds no return, IC, power, portfolio, bootstrap, or Holm calculations.*

