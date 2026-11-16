# J2 run-ready

The frozen J2 engine now validates the sealed schema and date bounds from `sealed_holdout_sp500/BUILD_REPORT.md`, and checks the sealed NPZ SHA-256 before loading it. The runner pins the full `J2.md` hash, requires the matching approval file, claims a persistent one-shot marker before engine execution, and reports both frozen DSR variants.

The synthetic end-to-end gate run passed: missing approval and panel-hash mismatch were refused; the successful run wrote a result; a second run was refused. Synthetic schema and gate evidence is in `SYNTHETIC_DRY_RUN.json`; implementation hashes are in `J2_CODE_HASHES.md`.

Development reproduction after the edits: V5 net excess `40.1251%`, strategy Sharpe `0.9239`, EW30 Sharpe `0.8804`. `specs/r9_HOLDOUT_APPROVED.txt` was not created. The optional staged-input manifest check was not run.
