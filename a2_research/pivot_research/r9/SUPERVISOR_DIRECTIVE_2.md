# SUPERVISOR DIRECTIVE 2 (Opus): DEVELOP. J2 may go to the user for holdout approval once conditions 1-3 below are met

Engine audit accepted. The DSR fix is a legitimate implementation correction. The V1 empty-book bug is explained and fixed. The turnover definition is consistent (the V0 cap explains the difference). The V0 vs J1 gap is mostly a start-date effect. Rule-5 selection is unchanged and V5 still wins. Good work.

A/B/C: (A) J1 predictability is real but small. (B) Net profit is marginal and depends on construction (V3/V4/V5 are non-monotone: +32/+12/+40%, which reads as noise). (C) Not qualified yet. The holdout is the only thing that can decide it.

## Conditions before asking the user for approval (short, about 10 minutes)
1. **Holdout cleanliness.** Confirm in writing that no J-family or short-horizon reversal return series was ever computed on 2010-01-01 to 2020-10-31 Dow prices. Check the D7 builds in sealed_holdout_dow/D7 and anything under sealed_holdout/. Also confirm that point-in-time Dow membership and SIC2 codes exist for 2010-2020 (KFT, DWDP, UTX, HPQ, AA, etc.). If SIC2 peers are missing, J2's signal is undefined, so stop.
2. **Freeze the DSR variance choice.** The primary is the 12-stream observed V (12 variants of one signal, so dispersion is small and this choice is lenient). Put the primary choice AND the null 1/(T-1) result into the approval record, tied to the J2 hash, so it cannot be chosen after the result. Report both, and the primary decides. Do not change J2.md.
3. **Correct the power estimate for winner's curse.** The 32.7% assumes V5's best-of-12 development mean is the true effect. Rerun the planning sim at half that effect and at the V3-V5 average, and give the user the range (my guess is about 15-25%). The user needs the honest odds before spending the one-shot holdout.

## Parallel path
The audit recommends S&P weekly with a turnover cap, and I agree it is the better second bet. It has no sealed S&P holdout, though (R7 manifest), so it cannot qualify tonight. Log it as the next registered pathway. First step: check whether a pre-2020-11 S&P point-in-time panel can be built from staged data to serve as its holdout. Do not start it before J2 is resolved unless a worker is idle.

## Fix to log (not urgent)
The R6 helper r4_harness/phase3.py:385-397 has the same DSR bug. Record it in R7_FINAL limitations. It doesn't change any R6 verdict, because no R6 strategy reached the DSR gate, but confirm that.

Then: present J2 + conditions 1-3 + the odds to the user for approval. If approved, run holdout_runner.py once and send me the result file. I will check the evidence before anything is called an edge.
