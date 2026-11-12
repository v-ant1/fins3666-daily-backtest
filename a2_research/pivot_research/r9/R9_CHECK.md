# Independent J2 development replay check

This checker independently replayed R9-V0 (J1 baseline), R9-V4 (three-formation smoothing), and selected R9-V5 (four-formation smoothing) from the frozen variant log and J2 rules. It did not import `j2_variants.py`; it used only the development-only price archive and score rows proven by Parquet metadata to be dated on or after 2020-11-27.

Pre-run log SHA-256 matched the variant-run record: `b3aae7eea8aed6c8c3223ca64faaf4f29674b7fb2eb58eff0253a76c0a792de2`. The log contains exactly R9-V0 through R9-V11, each with one pre-run timestamp. The price archive matched the coordinator-supplied SHA-256 and its date axis was exactly 2020-11-27 through 2026-10-30. The shared evaluation start was 2021-03-04.

**Agreement:** PASS (tolerances: net excess ±0.3 percentage points; strategy and benchmark Sharpe ±0.02).

| Variant | Independent net excess | Logged net excess | Difference | Independent strategy Sharpe | Logged strategy Sharpe | Sharpe difference | Result |
|---|---:|---:|---:|---:|---:|---:|:---:|
| R9-V0 | 5.1528% | 5.1528% | +0.000 pp | 0.8360 | 0.8360 | +0.0000 | Pass |
| R9-V4 | 12.0535% | 12.0535% | +0.000 pp | 0.7941 | 0.7941 | +0.0000 | Pass |
| R9-V5 | 40.1251% | 40.1251% | +0.000 pp | 0.9239 | 0.9239 | +0.0000 | Pass |

The EW30 Sharpe comparison is also checked against the shared official benchmark for each variant; it must agree within 0.02. The selected J2 candidate is R9-V5. This is a development-only reproducibility check, not holdout evidence.

No sealed holdout file or pre-2020-11-27 data rows were opened. The holdout runner was tested only with synthetic inputs; the approval file is absent and no holdout run was attempted.

## Holdout status

The supervisor directive in `r9/SUPERVISOR_DIRECTIVE_1.md` blocks the holdout pending a separate engine audit of DSR, turnover and portfolio-path anomalies, and power. This replay verifies only the reported development returns and Sharpes for V0, V4, and V5; it does not resolve those audit items or clear the holdout gate. The approval file was not created, and no holdout data was accessed.
