# FINS3666 Phase 3 research harness

This is a direction-agnostic library for testing a frozen pressure/network hypothesis. It does not define or implement any new signal. It accepts user-defined asset/date score functions or event lists and a point-in-time network. The harness never writes the shared trial log during normal import or tests.

## One-command validation

From the `pivot_research` project root:

```powershell
python r4_harness/run_tests.py
```

This runs synthetic planted-effect and null checks, event-response, placebo, portfolio and governance tests, then reconstructs the original L1 pressure signal from development daily bars and compares its close-to-close and next-open-to-close mean ICs with `r4_L1/rank_correlations.csv` to three decimals. It saves the complete output to `r4_harness/TEST_OUTPUT.txt` and reads no holdout prices. Expected key lines include:

```text
PASS planted IC detected ...; null not detected ...
PASS planted event response detected ...
PASS L1 original pressure rank correlations reproduce to 3 dp ...
Ran 11 tests ...
OK
```

Dependencies are Python 3.10+, NumPy and SciPy. The runner does not require pytest.

## Array conventions

- Price and score matrices are `assets × dates` (`N × T`). Missing/inactive assets use `NaN`.
- A dated network is `dates × assets × assets` (`T × N × N`) or `assets × assets × dates`; row `i` of a date slice gives outgoing weights from source `i` to targets.
- Scores are observed at close T. Portfolio fills occur at the next session's open.
- Returns and costs use adjusted prices supplied by the caller. The data adapter is intentionally left to each pre-registered direction.

## Pre-registration cost hurdle

`break_even_rank_ic(turnover, return_dispersion, cost_per_side=0.0005,
top_fraction=1/6)` gives a transparent cost-only rank-IC hurdle. Turnover is
total traded notional divided by NAV per rebalance (buys plus sells); use
benchmark-relative turnover for a benchmark-relative hurdle. Dispersion is
the cross-sectional standard deviation of holding-period returns. The mapping
assumes a linear relation between standardized percentile ranks and returns,
so expected top-quantile active return per unit Spearman IC is
`dispersion * sqrt(12) * (0.5 - top_fraction/2)`. Costs are `cost_per_side *
turnover`; turnover is not doubled again. This is an explicit planning
assumption, not a fitted alpha estimate.

## Signals and mechanism tests

Evaluate a generic `signal(asset, date, data) -> score` function, then calculate cross-sectional ICs:

```python
from r4_harness import signal_matrix, cross_sectional_ic

scores = signal_matrix(signal_fn, tickers, dates, data, mode="asset_date")
ic = cross_sectional_ic(scores, close, [1, 2, 5, 10, 20], open_prices=open_)
for row in ic:
    print(row.return_type, row.horizon, row.mean_ic, row.nw_t)
```

`mode="cross_section"` is also supported for a function shaped like `signal(data, date) -> N scores`. ICs are Spearman correlations computed cross-sectionally for each date. Close-to-close is `close[t+h] / close[t] - 1`; next-open-to-close is `close[t+h] / open[t+1] - 1`. The reported t-stat is Newey–West with Bartlett weights and lag `horizon - 1`. Non-finite scores and returns are dropped independently each date for point-in-time rosters.

For a source-shock event list, measure market-adjusted cumulative returns among linked neighbours. The network slice at the event date is used, self-links are excluded, and same-date events are clustered before the Newey–West t-statistic:

```python
from r4_harness import event_study

events = [{"source": "AAA", "date": 120}, {"source": "BBB", "date": 250}]
studies = event_study(events, network, close, windows=[1, 5, 10], asset_names=tickers)
```

By default, the benchmark is the equal-weight return of all assets with valid prices; pass `benchmark_close` to use an explicit benchmark price series. Each event is assumed to have already passed the frozen shock definition and threshold.

## Network placebos

The placebo engine runs 500 draws per family by default (fixed seed `20261110`):

```python
from r4_harness import network_placebos, event_study

def statistic(g):
    return event_study(events, g, close, windows=[5], asset_names=tickers)[0].mean_car

placebos = network_placebos(network, statistic, n_draws=500, seed=20261110)
for family, result in placebos.items():
    print(family, result.real_statistic, result.percentile,
          result.upper_tail_p, result.two_sided_p)
```

Families are (1) degree-preserving rewires with edge weights reassigned, (2) random links preserving edge count and weight distribution, and (3) the observed network sequence shifted in time relative to events/signals. `percentile` is the share of placebo statistics less than or equal to the real statistic; p-values include the finite-sample `+1` correction.

## Portfolio and inference

`portfolio_engine` supports concentrated long-only portfolios and 100%-gross dollar-neutral long-short portfolios (50% long, 50% short):

```python
from r4_harness import portfolio_engine

result = portfolio_engine(
    scores, open_, close, fill_indices,
    design="long_short", n_long=5, n_short=5,
    cost_rate=0.0005, bootstrap_draws=5000, trial_count=30,
    p_value_family={"preregistered_test_1": 0.03, "preregistered_test_2": 0.10},
)
print(result.strategy_gross, result.strategy_net)
print(result.excess_return_net, result.bootstrap_p, result.holm_adjusted_p)
print(result.strategy_net["active_share"], result.strategy_net["turnover"])
print(result.cost_to_gross_edge_ratio, result.deflated_sharpe)
```

`fill_indices` are execution dates; the signal at `fill_index - 1` is used. At each fill, the engine solves `new_NAV = pretrade_NAV - cost_rate × actual traded notional`, including buys, sells, short legs, stayer drift and final liquidation. It checks costs against independently calculated share notional. Results include strategy and EW30 gross/net returns, daily-mark Sharpe, active share, average total-notional turnover per rebalance, total costs, excess return, one-sided circular 10-session block-bootstrap p-value, optional Holm-adjusted p-value, DSR at the supplied trial count and cost/gross-active-edge ratio. Defaults are 5,000 bootstrap draws, 10-session blocks and a fixed seed.

Standalone inference helpers are also available:

```python
from r4_harness import circular_block_bootstrap_pvalue, holm_correction, deflated_sharpe_ratio

p, bootstrap_means = circular_block_bootstrap_pvalue(strategy_daily, ew_daily,
                                                       block_length=10, n_draws=5000)
adjusted = holm_correction({"test_a": p, "test_b": 0.04})
dsr = deflated_sharpe_ratio(strategy_daily, trial_count=30)
```

## Trial governance and look-ahead guard

Before execution, `run_registered_trial` refuses unless `specs/r4_prereg/<approach>.md` exists, contains `FROZEN: YYYY-MM-DD`, and has a matching `SHA256: <64 hex>` line. The canonical hash excludes the hash line itself:

```python
from r4_harness import prereg_digest

frozen_text = "# Hypothesis and tests\nFROZEN: 2026-11-12\n"
sha256 = prereg_digest(frozen_text)
prereg_text = frozen_text + f"SHA256: {sha256}\n"
```

The registered-run gate also refuses when the trial log is missing or the 30-variant budget is full; it records both success and failure results. Its default log is shared `specs/r4_trials.md`, but only an explicit later trial call appends to it. Harness tests use disposable preregistration and log fixtures inside `r4_harness/`.

Use `assert_future_truncation_invariant(signal_fn, data, signal_index, truncate_fn)` to recompute a signal after removing all post-signal-date data; it raises if the output changes.

## Coordinator-only holdout entry point

`run_holdout(config_path, price_folder, runner, caller_role="coordinator")` requires a frozen JSON config with `approach`, `prereg_dir`, `frozen_date` and matching `sha256`; it verifies the pre-registration, rejects paths without `holdout` in their name and refuses `repo`, `w1_engine` or `oos3` development directories. It does not inspect prices before passing the folder to the coordinator's adapter. Non-coordinator calls are refused.

The CLI requires explicit config, holdout path, adapter and coordinator acknowledgement. It has no default price directory:

```powershell
python r4_harness/holdout_runner.py --config frozen_config.json `
  --prices C:\path\to\sealed_holdout_dow --runner my_adapter:run `
  --coordinator-only
```

Compute the config hash with `config_digest(config_dict)` after removing its own `sha256` key. This entry point has only been tested against synthetic paths; it has not been run on sealed data.
