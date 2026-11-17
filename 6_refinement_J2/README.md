# Section 6: Refinement from J1 to J2

## What was done

J1's signal predicted returns, but trading costs ate most of the gain. The refinement kept the J1 score, sign, peer definition and timing fixed and only changed how the portfolio is built.

1. **Eleven alternatives to J1 (V0) were written down before any were run** ([`spec/variant_log_prelogged.md`](spec/variant_log_prelogged.md)): a no-trade band, a holding buffer, partial rebalancing, biweekly trading, smoothing the score over 2, 3 or 4 weeks, holding 8 or 10 names, and inverse-volatility weights.
2. **A fixed selection rule:** average active share of at least 50%, costs below 50% of the gross edge, then the highest net Sharpe.
3. **The winner, V5 (4-week smoothing), was frozen as J2** ([`spec/J2_preregistration.md`](spec/J2_preregistration.md)).
4. **Code audit before the holdout** ([`results/R9_ENGINE_AUDIT.md`](results/R9_ENGINE_AUDIT.md)) fixed two bugs: the deflated Sharpe scaling and V1's weight allocation. Neither changed the winner.
5. **J2 was run once on the sealed 2016–2020 holdout** ([`results/HOLDOUT_RESULT.json`](results/HOLDOUT_RESULT.json)); an independent audit confirmed the run was clean ([`results/HOLDOUT_AUDIT.md`](results/HOLDOUT_AUDIT.md)).

## J2 signal

$$
s^{(4)}_{i,t} = \frac{1}{4}\sum_{k=0}^{3} s_{i,t-5k}
$$

where $s_{i,t}$ is the J1 score. Buy the five Dow stocks with the lowest smoothed score.

## Results

All 12 variants are in [`results/R9_VARIANTS.md`](results/R9_VARIANTS.md).

| | J1 (V0), development | J2 (V5), development | J2, holdout 2016–2020 | EW30, holdout |
|---|---:|---:|---:|---:|
| Net excess / total net return | +5.15% excess | +40.12% excess | 72.54% total | 77.81% total |
| Net Sharpe | 0.836 (EW30 0.880) | 0.924 (EW30 0.880) | 0.608 | 0.727 |
| Mean turnover | 50.0% | 69.7% | — | — |
| Costs / gross edge | 53.2% | 22.5% | — | — |
| Bootstrap p-value | 0.391 | 0.188 | 0.478 | — |

**Holdout verdict:** J2 failed all four checks: lower return than EW30, lower Sharpe, bootstrap p above 0.05, and a deflated Sharpe ratio of 0.840 against the 0.95 required.

## Code

| File | What it does |
|---|---|
| [`code/j2_variants_v2.py`](code/j2_variants_v2.py) | Runs all 12 variants with the audit fixes (the version used for the final table) |
| [`code/j2_variants.py`](code/j2_variants.py) | The original variant run, before the audit fixes |
| [`code/j2_frozen.py`](code/j2_frozen.py) | The frozen J2 strategy |
| [`code/holdout_runner.py`](code/holdout_runner.py) | Runs J2 once on the holdout; refuses to run without approval or a second time |
| [`code/check_j2.py`](code/check_j2.py) | Independent check of the variant results |

The holdout price data is not included in this repository.

## J2 holdout daily returns

[`results/J2_holdout_daily_returns.csv`](results/J2_holdout_daily_returns.csv): date, J2 net return, EW30 net return for every holdout day (3 Feb 2016 – 30 Oct 2020, 1,196 days, net of 0.05% costs). It comes from a reporting-only re-run of the frozen J2 rule, used for the Section 5 risk table (Table 5b). The re-run reproduced `HOLDOUT_RESULT.json` exactly: J2 72.54%, EW30 77.81%.
