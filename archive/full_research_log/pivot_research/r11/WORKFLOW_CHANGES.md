# R11 workflow changes from the daily research process

R11 adapts the existing daily buying-pressure process to one-hour signals and executable regular-session trading. The change is prospective. It does not reopen a prior result or authorize any holdout.

## What changes

| Daily workflow | R11 one-hour workflow | Why |
|---|---|---|
| Signals and returns are often measured at daily close or monthly formation points | A signal is fixed at a completed one-hour bar close and executed at the next eligible regular-session bar open | A close cannot be used both to make the decision and to claim a fill |
| Overnight and intraday price movement may be combined in a daily bar | Attribute overnight close-to-open gaps separately; include them only while the registered position is held | The strategy may be flat overnight or exposed to the gap; daily closes hide that distinction |
| Daily bars do not usually require a partial-session bar rule | Define interval timestamps, opening bar, final 30-minute bar, and auction execution rules before outcomes | Hourly vendors label intervals differently, and the final interval is not always a full hour |
| Earlier workflows used a flat per-side cost such as 5 or 10 bp | Use half-spread plus market-impact cost where verifiable; otherwise use all-in 1/2/5/10 bp one-way scenarios with a 5 bp primary floor | Short holding periods can be dominated by spread and execution timing |
| Strategy turnover cost was compared with a benchmark that could be shown gross | Model strategy and investable benchmark costs symmetrically; report gross and net results | Net active performance should compare two feasible portfolios |
| Hourly bars could be mistakenly treated as a large independent sample | Use the daily portfolio return as the primary inference unit, Newey-West lags suited to bar and daily streams, and day-clustered moving-block bootstrap | Bars from the same session share market conditions and are not independent |
| R10's search history was 50 at the L4 ledger checkpoint | Carry a conservative R11 starting DSR count of 80 after adding later registered R10 screens; add every R11 candidate and selectable variant | Keep the full search visible; the DSR must use a scaled expected maximum |
| Daily holdout history could be considered by calendar window | The only identified free hourly window is 2016-01 to 2020-11-26, and J2 used the same dates on daily data | Same dates at a finer frequency are not automatically independent confirmation |
| Coordinator and workers divided data, ideas, and runner tasks | Use up to four bounded Luna roles: persistence, spillover, reversal, and independent red-team/data audit | Keep mechanisms distinct, parallelize bounded work, and audit timing/cost before results |
| Trial registration was mainly daily signal/portfolio rules | Preregister interval labels, next-open execution, auction policy, overnight treatment, cost components, day bootstrap, hourly/daily lags, and power before a run | These choices can change the measured strategy and must not be selected after results |

## What stays governed by the prior process

The R11 workflow retains point-in-time membership, reproducible inputs, pre-registration, duplicate checks, cumulative trial accounting, one-shot outcome handling, transparent protocol deviations, and separate claims for predictability, profitability, and qualification. Any result from the 2020-11-27 to 2026-10-30 development period remains exploratory. The holdout choice is unresolved and requires a user or supervisor ruling.

## Practical sequence

1. Freeze a candidate's mechanism, point-in-time universe, signal timestamp, next-bar fill, holding schedule, cost model, benchmark, placebo, family membership, trial count, and power calculation.
2. Audit bar timestamps, session coverage, partial bars, membership, gaps, corporate actions, and executable costs without inspecting outcomes outside the registered development interval.
3. Run synthetic validation, hash the registration and runner, and have an independent worker red-team it before the coordinator authorizes the one development run.
4. Evaluate daily net excess with HAC and day-clustered block inference. Report hourly diagnostics, net returns at all required costs, MDE, haircut pass probability, DSR, and missingness.
5. Stop on a failed screen. A development pass remains exploratory. Do not open 2016-2020 hourly data or label any test confirmatory until a ruling is entered in specs/r11_decisions.md.
