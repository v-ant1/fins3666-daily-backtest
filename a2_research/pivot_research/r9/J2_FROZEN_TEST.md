# J2 frozen engine check

The new `j2_frozen.py` engine matched logged R9-V5 on the trimmed development slice: net excess **40.1251%** (logged 40.1251%), strategy net Sharpe **0.9239** (logged 0.9239), and PIT EW30 net Sharpe **0.8804** (logged 0.8804). The replay used only development prices and J1 score rows verified post-2020-11-27 by Parquet row-group metadata.

Synthetic checks passed for a known SIC2 peer, a target with missing SIC2, and a target with no eligible same-SIC2 peer. `holdout_runner.py --self-test` and Python compilation also passed.

No sealed panel or pre-2020-11-27 prices/returns were read, and the one-shot holdout runner was not invoked. The gated engine currently expects the future sealed panel at `sealed_holdout_sp500/J2_HOLDOUT.npz`; that artifact path and its contents remain unverified until the builder delivers it.
