# R9 J2 pre-approval conditions

Prepared 2026-11-11 under Supervisor Directive 2. **Do not approve or run the holdout yet.** No approval marker was created; `r9/holdout_runner.py` was not run.

## Conditions

| Condition | Status | Finding and evidence |
|---|---|---|
| 1. Holdout cleanliness | **STOP** | **Computation check: GO.** No evidence was found that a J-family or short-horizon reversal return/IC series was computed on 2010-01-01–2020-10-31 Dow prices. `r9/R9_ENGINE_AUDIT.md` records dev-only scope and that the runner was not run; `r9/j2_variants.py` only loads the 2020-11-27–2026-10-30 dev inputs. `sealed_holdout_dow/D7/QA.md` and `D7/build_holdout_links.py` describe a SEC filing metadata build with no price/return/signal calculations. The files in `sealed_holdout/` are a separate 30-country-ETF, 63-session idiosyncratic-skew run, not a Dow J-family test (`specs/r3_holdout_basket.txt`, `sealed_holdout/run_holdout.py`). **Inspection-scope incident:** a broad search accidentally displayed raw `sealed_holdout_dow/finra_si/raw` short-sale volume-like rows dated 2018–2019. No J-family calculation or price/return value was involved, but this violated the holdout inspection restriction and was escalated to the coordinator; keep this condition STOP pending review. |
| 2. PIT membership, SIC2, and signal inputs | **STOP** | PIT membership windows are encoded by the dated roster changes in `sealed_holdout_dow/D7/build_holdout_links.py` and summarized in `sealed_holdout_dow/R6_READINESS.md`. SIC2 coverage is not complete at membership entry: **DWDP** has no as-of SIC2 from its 2017-09-01 Dow entry until the first dated SIC record on 2018-02-15; **DOW** has no usable as-of SIC2 from its 2019-04-02 entry until 2020-02-07. The readiness table records “none” for the SIC observation before each window. Other requested examples KFT, UTX, HPQ, and AA have dated/as-of SIC coverage in that table. J2 requires the fixed J1 score: five-session adjusted-close return less the leave-one-out mean among PIT same-SIC2 peers (`specs/r9_prereg/J2.md`). The current holdout path cannot supply this: `r9/j2_variants.py` reads only the trimmed Dow development NPZ and the J1 development signal bundle; the holdout directory has no S&P-wide 2010–2020 peer-price panel. `holdout_runner.py` expects `run_frozen_j2` from that development-only module, but that function is absent. Thus the frozen signal is not reproducible from the current holdout inputs even aside from the SIC gaps. |
| 3. DSR variance freeze and reporting | **GO** | The primary is the 12-stream observed R9 variance `V=0.00008415393784762033`; the null sensitivity is `V=1/(T-1)`, with `T` the number of daily observations. The primary decides. The runner now emits both DSRs and uses only the primary for the pass gate. Exact hashes and decision are in `specs/r9_dsr_variance_freeze.md`; the implementation correction is logged in `specs/r9_decisions.md`. `specs/r9_prereg/J2.md` was not changed. |
| 4. Power sensitivity (dev inputs only) | **GO** | Same planning design as the engine audit: paired EW30 daily returns and centered V5 excess residuals, circular 10-session blocks, 2,722-session paths, 3,000 paths, seed `20261111`; p gate uses the audit's lag-9 HAC normal approximation. The V3–V5 effect is the arithmetic average of their observed daily mean excess returns. |

### Power estimates

| Assumed daily effect | Daily effect | All four gates, primary V | All four gates, `1/(T-1)` |
|---|---:|---:|---:|
| V5 observed dev mean | 0.00015749 | 32.7% (MC SE 0.9 pp) | 21.6% (0.8 pp) |
| Half V5 | 0.00007875 | 15.3% (0.7 pp) | 9.6% (0.5 pp) |
| V3–V5 average | 0.00011941 | 23.6% (0.8 pp) | 14.8% (0.6 pp) |

The gates are positive net cumulative excess, net Sharpe above EW30, one-sided p<0.05, and DSR>0.95. For the planned horizon, `T=2,722` and the null variance is `1/2,721 = 0.0003675119441381845`. These are planning odds, not holdout evidence.

## Evidence and scope

- `sealed_holdout_dow/R6_READINESS.md` reports the 2010–2020 constituent windows and dated SIC record coverage; its row-count evidence also documents price gaps for KFT, DWDP, and WBA and UTX's RTX-lineage proxy.
- `r6_J1/build_manifest.json` and `r6_J1/INPUT_QA.md` document the S&P peer feature build as development-only; its price boundary begins 2020-06-01 and J1 formations begin 2020-11-27.
- `r9/R9_ENGINE_AUDIT.md`, `r9/j2_variants.py`, `r9/holdout_runner.py`, and `specs/r9_prereg/J2.md` support the scope and input-path findings above.
- Holdout access in this review was limited to filenames, metadata, permitted build scripts/logs, and membership/SIC coverage except for the disclosed accidental display of raw FINRA SI volume-like rows. No 2010–2020 price or return values were opened, and the holdout runner was not executed.
