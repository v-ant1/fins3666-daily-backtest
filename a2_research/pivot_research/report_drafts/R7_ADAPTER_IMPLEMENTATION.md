# R7 adapter implementation

Implemented the new point-in-time S&P portfolio adapter, read-only pre-run checklist, synthetic e2e tests, and prospective Holm family scaffold.

The adapter forms each strategy at the prior close and executes at the next open using point-in-time roster and available-open membership. It supports equal-weight top decile, top quintile, and descending-rank-weighted top half portfolios, enforces a 50% buys-plus-sells turnover cap, compares with the available-name equal-weight S&P book, and applies decision-63 stale-close marking to both books. Inference uses the shared Newey–West, block-bootstrap, Holm, and DSR helpers; the caller provides the cumulative variant count and completed prior endpoint p-values.

`specs/r7_holm_family.json` contains R6-H1 through R6-H21 followed by R7-H1 through R7-H3, with the required `sha256(json.dumps(manifest))` digest. It is deliberately a no-outcome scaffold: the R6 slots are null, and the pre-run check refuses execution until the coordinator populates them from the preserved family. No market outcome or holdout inputs were loaded.

The checklist verifies config/input/output paths, hashes, development-window bounds, preregistration and manifest integrity, sealed-root access denial, helper/test status, placebo interpretation, Holm slots, cumulative trial count, one-shot authorization, and output uniqueness. Its runtime check reads only the manifest and hashes declared input bytes; it never parses price arrays or computes outcomes.

Validation: `python -m py_compile r4_harness/r7_sp500_adapter.py r4_harness/r7_prerun_check.py r4_harness/tests/test_r7_sp500_adapter.py` succeeded; `python -m pytest r4_harness/tests/test_r7_sp500_adapter.py -q` returned **9 passed**. The only warning is an unrelated pytest deprecation warning. The checklist CLI help invocation also succeeded. No real portfolio was run.

