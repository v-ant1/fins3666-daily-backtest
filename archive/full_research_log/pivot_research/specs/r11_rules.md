# R11 rules: one-hour buying-pressure research

**Status:** prospective workflow proposal. It governs R11 development screens once the coordinator freezes the protocol and authorizes a run. It does not authorize opening any holdout. R11 outcomes, price files, and sealed files were not accessed while drafting this ruleset.

## 1. Research question and separation of claims

Test three distinct buying-pressure paths in U.S. large caps: pressure persists in the same stock, pressure spills over to related stocks, or pressure reverses. A candidate must specify which path it tests and why the mechanism should operate at a one-hour horizon.

Keep three conclusions separate:

1. **Predictability:** does the registered signal predict the next eligible return, with the registered direction and placebo tests?
2. **Implementation:** does a predeclared portfolio earn positive net excess after executable timing, turnover, and costs?
3. **Qualification:** does it pass the independent holdout and final statistical gates?

A development screen is exploratory. It cannot validate a strategy or authorize a holdout.

## 2. Scope, data boundary, and bars

- The shared development interval is **2020-11-27 through 2026-10-30**, inclusive, using only regular-session data whose bar end time falls in that interval.
- Default session is the U.S. primary listing regular session, 09:30–16:00 America/New_York, with the historical exchange calendar and daylight-saving changes applied. Extended-hours data are excluded from signals, portfolio formation, execution, and returns unless the exact fields, availability times, and rule are registered before any outcome access.
- Define every one-hour bar by its interval start and end, not by an ambiguous vendor label. The final regular-session interval is a partial 30-minute bar; preregister whether to keep it, combine it with the preceding interval, or exclude it. Apply that choice identically across securities and dates.
- Use point-in-time S&P 500 or Dow 30 membership and security mappings at each signal and execution time, including delisted names. Choose one primary universe before outcomes. If both universes are evaluated, each is a separately counted endpoint in the frozen family.
- Bars used for signals must be complete, adjusted for known corporate actions only as they became effective. Do not use retrospectively dividend-adjusted history in a way that leaks later actions into earlier prices. No imputation of missing bars, prices, membership, or volume. Record missingness and coverage by symbol, year, and time of day.
- Never read prices, signal values, or outcomes before 2020-11-27 for an R11 development run. Do not inspect any sealed directory. This restriction includes exploratory plots and source summaries containing pre-boundary performance values.

## 3. Signal and execution timing

1. At the close of bar \(t\), calculate the signal from information with timestamps no later than that completed bar's end. Freeze the signal value and intended target after the bar closes.
2. Submit and execute at the **open of the next eligible regular-session one-hour bar**. Do not fill at the same close that generated the signal. Do not use the next bar's open, high, low, volume, or close to set the order size or target.
3. When the next bar is the opening bar of a new session, the order must be specified before the opening print. The simulation may use the official opening price plus the registered open-side slippage model; it may not use later knowledge of that bar.
4. Report overnight and regular-session returns separately. A position held across a close owns the close-to-next-open gap. An intraday-only position must be scheduled to exit by a predeclared closing-auction or final-bar rule. Do not treat an after-close signal as executable in that same closing auction.
5. Closing-auction fills are allowed only for an order rule frozen before outcomes, with a feasible submission cutoff and only information available by that cutoff. A signal using the final bar close cannot enter or exit at that same close. Otherwise, use the next bar open for the exit as well.
6. Overnight strategies use the prior close signal, next-session open execution, and include the actual gap return while the position is held. They must not reset positions or prices across the overnight gap. Intraday-only and overnight-holding designs are separate registered strategies if both are tested.
7. No signal may bridge an overnight gap by treating the last bar of one session and first bar of the next as contiguous observations. Pre-register gap features explicitly. Extended-hours bars remain excluded unless separately registered.
8. Use one consistent clock and timestamp convention for features, order eligibility, bar labels, and return attribution. Save the signal timestamp, order-eligible timestamp, modeled fill timestamp, and holding start/end for every portfolio trade.

## 4. Costs and portfolio accounting

### Per-side cost model

For asset \(i\), side \(s\), and order time \(t\), all-in one-way cost is:

\[
c_{i,s,t}=h_{i,s,t}+I_{i,s,t}+f_{i,s,t}
\]

where \(h\) is half the executable bid-ask spread, \(I\) is market impact, and \(f\) is commissions, exchange/regulatory fees, and any applicable borrow or financing charge. Express the components in basis points of traded notional.

If contemporaneous quote and volume data are available, estimate half-spread from the quoted spread at the registered fill time. Estimate impact with a registered square-root model, for example:

\[
I_{\mathrm{bp}}=Y \times \sigma_{i,h} \times \sqrt{Q_{i,t}/ADV_{i,h}} \times 10{,}000
\]

where \(Q\) is order dollars, \(ADV_{i,h}\) is trailing same-hour dollar volume calculated only from prior sessions, \(\sigma_{i,h}\) is trailing same-hour return volatility, and \(Y\) is frozen before outcomes using independent execution evidence. Cap participation at a preregistered fraction of trailing same-hour volume; if the order exceeds it, reduce the fillable quantity and report the unfilled exposure. Do not estimate \(Y\) from R11 strategy returns.

When quote or impact inputs are unavailable or cannot be verified, do not label a bar-based proxy as observed spread. Use an all-in per-side scenario cost instead. The required sensitivities are **1, 2, 5, and 10 bp per one-way fill**. The primary cost is at least **5 bp per side**, or the predeclared quote-plus-impact estimate if that is higher. This preserves the prior 5 bp per-side baseline while allowing explicit intraday stress cases. Report the cost-component model separately from the fixed sensitivity grid.

Apply cost to each filled dollar bought or sold. For weights, dollar turnover is the sum of absolute weight changes, including entry from cash, exits, and both legs of a long-short book. A full switch from 100% long to 100% short is 200% of NAV traded. Charge entry and exit separately. Apply the same cost model to the selected investable benchmark; primary excess is strategy net return minus benchmark net return. Also show gross strategy and gross benchmark returns so the cost contribution is visible. If a benchmark cannot be modeled as an investable portfolio, register that limitation and do not silently compare a net strategy with a costless active benchmark as the only result.

S&P and Dow names must have point-in-time liquidity inputs. Do not apply one present-day average spread to all historical constituents. Report turnover, trade count, average order participation, unfilled quantity, spread cost, impact cost, other fees, and net excess at each of 1/2/5/10 bp. Short positions require separately registered borrow availability and borrow cost; otherwise they are ineligible.

## 5. Statistical protocol

### Common return unit

For inference, aggregate all intraday portfolio P&L to one **daily portfolio return** per trading session, including any overnight gap earned by held positions. Use daily net excess over the matched investable benchmark as the common primary return stream, regardless of signal frequency. This prevents treating six or seven bars in one day as six or seven independent observations. Report hourly-bar results as diagnostics, not as a larger independent sample.

### Newey-West

Use Bartlett-kernel Newey-West standard errors and freeze the lag before outcomes:

- One-hour bar-return diagnostics: primary lag **24 bars** (about four regular sessions); report lag 6 and lag 30 sensitivities. The sequence consists only of eligible regular-session bars; overnight gaps remain separately attributed.
- Daily-aggregated primary return: primary lag **5 trading days**; report lag 10 sensitivity.

Report the mean, HAC standard error, t-statistic, number of daily observations, and annualized Sharpe. The primary screen t-statistic is calculated on the daily-aggregated stream.

### Day-clustered block bootstrap

Use paired portfolio and benchmark daily returns. Resample circular blocks of **10 consecutive trading days**, keeping every hourly observation and every portfolio/security observation from a selected day together. This preserves within-day clustering and short-run serial dependence. Use 5,000 draws, a fixed seed written in the preregistration, and a centered null for the one-sided test of positive net excess. Report one-sided bootstrap p-value and confidence interval. Show 5-day and 20-day block sensitivities. Do not resample individual hourly bars independently.

### Deflated Sharpe ratio and trial count

Use unannualized Sharpe on the common daily net return stream. Let \(n\) be the number of daily return observations and \(T_{\mathrm{trials}}\) the cumulative registered search count. For the expected maximum of \(T_{\mathrm{trials}}\) standard normals, use the R9 approximation:

\[
E[\max Z]=(1-\gamma)\Phi^{-1}(1-1/T_{\mathrm{trials}})
+\gamma\Phi^{-1}(1-1/(eT_{\mathrm{trials}}))
\]

with Euler's constant \(\gamma\). The corrected benchmark is:

\[
SR_0=\sqrt{V}\;E[\max Z]
\]

and the probabilistic DSR is:

\[
DSR=\Phi\left(
\frac{(SR-SR_0)\sqrt{n-1}}
{\sqrt{1-\mathrm{skew}\,SR+((\mathrm{kurtosis}-1)/4)SR^2}}
\right)
\]

Use kurtosis, not excess kurtosis, in the displayed denominator. Do not compare the observed Sharpe directly with \(E[\max Z]\): that is the R9 scaling defect. Keep \(SR\), \(SR_0\), and \(V\) in the same unannualized daily-Sharpe units.

Carry forward the frozen R9/R10 primary variance \(V=0.00008415393784762033\), and also report the R9 null-variance sensitivity \(V_{\mathrm{null}}=1/(n-1)\). The primary DSR alone decides any later DSR gate. Do not substitute the trial count for \(n\) in the null-variance formula.

The R10 L4 ledger recorded 50 cumulative attempts/endpoints before the later R10 screen registrations. The specified R10 logs add 30 counted candidates: L5 (1), L3B (1), L3C (1), S3 (5), S2B (6), S1 (4), S4 (6), S5 (4), and S6 (2). Therefore use a conservative R11 starting count of **80**, which is consistent with the task's approximate 75-trial description and must not be reduced without a coordinator-owned reconciliation made before outcomes. Set:

\[
T_{\mathrm{trials}}=80+\text{all counted R11 hypotheses, variants, and outcome-accessing failed attempts}
\]

Count each separately registered candidate/variant whose result could be selected or reported, including null results, data-gated preregistered hypotheses, and crashes after outcome access. Record pre-outcome implementation crashes and synthetic-only validations separately; do not call them independent return streams. This is a conservative search count, not a claim that all attempts are independent observations. Holm's endpoint family and DSR's cumulative trial count are different quantities; freeze both before a run.

## 6. Screen gate and development-window power

The screen's target is a daily portfolio return stream over **2020-11-27 through 2026-10-30**. The date range contains approximately 1,488 U.S. sessions for planning; actual eligible observations are candidate-specific and must be counted from the permitted development input after a run is authorized. Any missing sessions reduce \(n\); no worker may extend the boundary to improve power.

Before a strategy screen, freeze the family size \(M\), primary universe, benchmark, cost, and endpoint. Use a conservative one-sided planning critical value:

\[
z_*=\max\{\Phi^{-1}(1-0.05/M),\,2.0\}
\]

where \(M\) is the number of separately selectable registered endpoints in that R11 Holm family. Use actual Holm-adjusted p-values for the reported family; Bonferroni \(0.05/M\) is only the conservative power approximation.

For an iid planning approximation with annualized standard deviation \(\sigma_{\mathrm{ann}}\) of daily net excess, \(SE_{\mathrm{ann}}=\sigma_{\mathrm{ann}}\sqrt{252/n}\), and:

\[
MDE_{80,\mathrm{ann}}=(z_*+0.8416)\,SE_{\mathrm{ann}}
\]

The actual MDE uses the daily Newey-West standard error or the registered day-block simulation, not the iid approximation. The 80% MDE is the net annualized mean required for 80% power at the family-adjusted one-sided threshold and the screen's t>=2 requirement.

Design-only illustration at \(n=1,488\), assuming annualized active-return volatility of 10%, 20%, or 30%. These are assumptions, not estimates from price data:

| Family size \(M\) | Assumed annualized volatility | Approximate 80% MDE, annualized |
|---:|---:|---:|
| 1 | 10% | 11.7% |
| 1 | 20% | 23.4% |
| 1 | 30% | 35.1% |
| 12 | 10% | 14.3% |
| 12 | 20% | 28.6% |
| 12 | 30% | 43.0% |

Hourly signals do not multiply the independent sample size: once the portfolio is evaluated as daily returns and trading days are the bootstrap clusters, the relevant planning sample remains about 1,488 days. If one incorrectly treats 6.5 hourly bars per day as independent, an apparent MDE is about \(1/\sqrt{6.5}\) as large; that is invalid for this gate. Positive serial dependence, missing data, and day-block uncertainty can make the actual MDE larger than the illustration.

After outcomes are measured, report the 50%-haircut pass probability using the candidate's observed daily net mean and its registered projected standard error:

\[
P_{\mathrm{pass,haircut}}=
\Phi\left(\frac{0.5\hat{\mu}_{\mathrm{ann}}}{SE_{\mathrm{ann}}}-z_*\right)
\]

This estimates the positive-mean/HAC screen gate only; it is not the probability that a strategy passes every qualification test. For illustration, with \(n=1,488\), \(M=12\), and assumed \(\sigma_{\mathrm{ann}}=20\%\), \(SE_{\mathrm{ann}}\) is about 8.23%. An observed annualized development mean of 10%, 20%, or 40% gives approximate 50%-haircut pass probabilities of 2.1%, 7.7%, or 41.8%. No actual candidate pass probability is available before outcomes. The minimum development screen is: net mean > 0 at the primary cost, daily Newey-West t >= 2, one-sided day-block bootstrap p-value below the frozen Holm threshold, and haircut pass probability >= 30%. Report every cost sensitivity and do not promote a candidate that passes only at 1 or 2 bp when the primary cost is at least 5 bp. Report DSR for every stream; development DSR does not replace an independent holdout.

## 7. Holdout policy — REQUIRES USER/SUPERVISOR RULING

Alpaca history begins in 2016, so the only currently identified free one-hour holdout is **2016-01 through 2020-11-26**. J2 already used that same calendar period on daily data. There is therefore no clearly untouched historical S&P/Dow period for a confirmatory one-hour test. Frequency conversion does not make a period independent after the daily returns and outcomes from those dates have been used.

Options requiring a ruling:

| Option | Pros | Cons |
|---|---|---|
| Treat 2016-01 to 2020-11-26 as spent at every frequency; keep R11 development-only and seek a new independently sourced or prospective period later | Preserves a clean confirmatory boundary and avoids frequency-based reuse | No immediate historical confirmation; new data or a forward test costs time and may be less comparable |
| Permit the hourly bars from 2016-01 to 2020-11-26 only as a non-confirmatory cross-frequency robustness/stress analysis | Can show whether intraday mechanics differ from J2's daily implementation | Reuses the same calendar outcomes; cannot qualify, validate, or provide independent p-values/DSR |
| Explicitly authorize reuse of the same period as a confirmatory one-hour test | Provides an executable historical test without waiting for new data | Not independent of J2's daily test; frequency-specific selection and correlated returns can inflate evidence, so this would change the meaning of confirmation |

**Choice: REQUIRES USER/SUPERVISOR RULING. No option is selected by this ruleset.** Until a ruling is recorded in specs/r11_decisions.md, no R11 worker may read or build from the 2016-01 to 2020-11-26 hourly bars, compute holdout power from their returns, or claim confirmatory qualification.

## 8. Round structure and Luna worker roles

The coordinator owns the queue, protocol freeze, trial ledger, authorization, and final interpretation. Use up to four Luna workers in a round. Each worker receives one bounded task, a unique output path, the same frozen data boundary, and one of these roles:

1. **Persistence:** same-stock buying-pressure continuation; test only the registered next-hour or fixed holding-window return.
2. **Spillover:** pressure transmission to preregistered peers, sector members, suppliers, or other related-stock sets; freeze the relation map and direction before returns.
3. **Reversal:** exhaustion, inventory, or liquidity-reversion mechanisms; define the event and reverse direction before outcomes.
4. **Independent red team/data audit:** challenge duplicates, timing feasibility, point-in-time mapping, costs, power, and placebos; audit another worker's specification before outcomes. If the round needs a fourth signal stream instead, assign a non-duplicative candidate in advance and count it in the same family.

Each worker may submit at most one primary candidate plus two fully specified variants. That caps a four-worker round at 12 selectable endpoints. Freeze the Holm family and all specifications before the first result. The coordinator may reject candidates at a documented duplicate, data, mechanism, cost, or power gate before outcome access; once a candidate is preregistered, it remains in trial accounting even if it is later data-gated. No worker sees another worker's results before registrations are frozen. Do not launch broad unbounded screens.

## 9. Pre-registration template

Copy and complete this template for every candidate and selectable variant before any outcome access. Freeze a timestamped file hash and enter the trial in specs/r11_decisions.md.

### R11 preregistration

- Trial ID and parent idea:
- Worker / reviewer / coordinator:
- Registration timestamp and SHA-256:
- Status: screen candidate / variant / placebo / data-gated:
- Thesis path: persistence / related-stock spillover / reversal:
- Literature source and exact mechanism:
- Duplicate search performed and related prior R6-R10 trials:
- Primary claim: predictability / net profitability / both:
- Primary universe: PIT S&P 500 / PIT Dow 30:
- Security, ticker, issuer, sector/peer mapping and effective-date rules:
- Data sources, fields, timestamps, coverage, missingness, corporate-action handling:
- Development bounds: 2020-11-27 through 2026-10-30:
- Session calendar, timezone, bar interval labels, partial final bar rule:
- Extended-hours rule:
- Signal formula, lookback, direction, cross-sectional ranking, and minimum coverage:
- Information cutoff and signal timestamp:
- Order timestamp: next eligible regular-session bar open:
- Fill proxy, open/close auction rule, participation cap, and unfilled-order handling:
- Holding period; intraday-only or overnight; gap P&L attribution:
- Portfolio weighting, rebalance schedule, cash, leverage, shorting, and exit:
- Primary benchmark and its investable turnover/cost rule:
- Cost inputs and components; primary one-way floor 5 bp; required 1/2/5/10 bp sensitivities:
- Primary endpoint: daily net strategy-minus-benchmark return:
- Predictive endpoint and registered placebo:
- Hourly Newey-West lags 24 (sensitivities 6/30); daily lags 5 (sensitivity 10):
- Day-clustered bootstrap: 10-session blocks, 5,000 draws, seed:
- Holm family ID and size; primary and secondary endpoint list:
- Cumulative DSR trial count: 80 + this and all other R11 counted trials:
- DSR primary V and null sensitivity; common daily Sharpe units:
- Candidate-specific effective daily N, HAC SE, MDE, haircut-pass formula:
- Screen gate: primary-cost mean > 0, daily NW t >= 2, Holm-adjusted bootstrap p < 0.05, haircut pass >= 30%:
- Cost sensitivity and turnover reporting:
- Maximum variants and which endpoints can be selected:
- Stop rules, missing-data rules, and protocol-deviation handling:
- Holdout ruling status: unresolved / explicitly authorized with date and approver:
- Output artifact path, runner hash, input manifest hash:
- Result interpretation limits and planned next decision:

No edits, sign changes, lookbacks, horizons, exclusions, or reruns are permitted after outcome access unless a new prospectively registered trial is approved and counted. A pre-outcome implementation defect may be corrected only if no candidate outcome was computed or exposed; record it and rerun synthetic validation before the one authorized outcome run.
