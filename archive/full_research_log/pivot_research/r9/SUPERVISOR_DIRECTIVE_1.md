SUPERVISOR DIRECTIVE (Opus) - BLOCK J2 holdout until fixed. Do NOT request user approval or run r9/holdout_runner.py yet.

WHAT HAPPENED: J2 = R9-V5 (4-obs smoothed J1), picked from 12 dev variants. Dev: net Sharpe 0.924 vs 0.880, bootstrap p 0.19. The process (pre-logged variants, mechanical selection, hash-bound approval, one-shot marker) is sound. But the engine has defects that would waste the only 2010-2020 Dow holdout.

1) DSR IS BROKEN (implementation correction, not a rule change). holdout_runner.deflated_sharpe_ratio compares a DAILY Sharpe (~0.06) with expected_max_daily_sharpe(trials) ~1.7, which is E[max of N standard normals] with no scaling by the cross-trial Sharpe SD (Bailey & Lopez de Prado: SR0 = sqrt(V[SR_n]) * that term). Result: DSR=0.0000 for every variant, including J1, so criterion "DSR > 0.95" can NEVER pass. That makes the holdout a guaranteed fail. Fix: use SR0 = sqrt(V) * E[max], with V = variance of the 15 trial daily Sharpes (or 1/(T-1) under the null). State which one before any holdout read. Check whether the R6 helper has the same bug, and log it as an implementation correction in r9_decisions BEFORE the holdout.

2) TURNOVER/ENGINE SANITY. Smoothing should LOWER turnover vs J1, but V3/V5 show mean 98%/70% vs J1 50%. J1 shows max=mean=50% while the others hit 200%, so the turnover definitions look inconsistent. V1 (no-trade band) shows -89.6% excess on 0.35% turnover, which points to a bug (stuck or empty book?). V0 replay of J1 gives +5.15% vs the +1.03% in R7_FINAL. Reconcile: is this the start date (2021-03-04 vs 2020-11) or a mismatch? The holdout reuses this engine, so it must be verified first. Note: none of this licenses re-selecting a variant. If after the fix V5 is no longer the rule-5 winner, report that honestly; the selection rule stays fixed.

3) POWER. Dev p=0.19 over ~5.6y. A ~10y holdout helps, but say up front the probability that J2 passes all rule-6 gates given the dev effect. If it's below ~20%, tell me which pathway you would run in parallel (D1 near-miss diagnosis, or S&P weekly with turnover cap) so we are not betting everything on one shot.

A/B/C: (A) J1 predictability is real but small. (B) Net profitability is marginal and depends on construction. (C) Not yet qualified.

DELIVERABLE: r9/R9_ENGINE_AUDIT.md covering the DSR fix and before/after DSR on dev variants, the turnover-definition reconciliation, the V1 explanation, the V0 vs J1 reconciliation, and the power estimate. Then ping me. I approve going to the user for holdout approval only after that.
