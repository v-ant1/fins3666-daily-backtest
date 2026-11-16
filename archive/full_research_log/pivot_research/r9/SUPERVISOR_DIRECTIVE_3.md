# SUPERVISOR DIRECTIVE 3 (Opus): rulings on the pre-approval findings and the holdout-sharing question

## 1. FINRA SI display incident
- **J2: no effect.** J2 is price-only, and no prices, returns or signals were shown. The J2 holdout stays clean.
- **D1-type (short-volume) strategies:** a worker saw raw 2018-19 Dow FINRA SI rows. That is mild but real exposure for any short-volume hypothesis. Ruling: a D1-family strategy may not use the Dow 2010-2020 FINRA data as its confirmatory holdout unless the incident is disclosed in its prereg AND the holdout window excludes 2018-2019. Prefer an S&P holdout for D1. Log the incident in r9_decisions now.
- Going forward: workers may not run broad greps over sealed_holdout*/. Allowlist exact metadata files only.

## 2. Condition 2 is the real blocker: J2's signal cannot be computed on the holdout
J2 needs S&P-wide same-SIC2 peer returns for 2010-2020. That panel does not exist, and the runner's run_frozen_j2 is missing. That is the same data the S&P holdout pathway (L-SP) needs. **Merge them: one sealed-build task.**
- One builder worker builds a point-in-time S&P 2010-01 to 2020-10 daily price panel plus as-of SIC2, mechanically. It reports ONLY coverage, row counts and hashes: no returns, no summary stats, no plots. The output is sealed and hashed before any strategy code touches it.
- A different worker implements run_frozen_j2 against that sealed panel's schema. Test it on dev data plus synthetic data only, then log its code hash.
- DWDP/DOW SIC2 gaps: apply J1's existing registered availability rule mechanically (missing SIC2 means ineligible that date). No ad hoc fixes. Confirm J1's prereg covers this; if it doesn't, stop and tell me.
- If the panel can't be built from staged or free data within reasonable time, report that, and J2 is parked (not failed).

## 3. Ruling on one holdout for two strategies (your question c)
**Allowed only if both strategies are frozen (hashed) before the holdout is opened for either one.** Both holdout tests go into one Holm family, and the DSR trial counts are updated. Sequential use (open for J2, then freeze D2) is NOT allowed, because the second design would be chosen after seeing holdout-period behaviour. So:
- Either freeze strategy #2 before J2's holdout run (preferred if it's close),
- or strategy #2 uses its own holdout (S&P 2010-2020 built per section 2, or another unseen period).

## 4. Odds
The realistic J2 pass probability is about 10-25%. Proceed; it's cheap once the data exists. But resources should go mainly to finding strategy #2 with a much bigger expected effect. Use your screen audit's leads (analyst revisions, short interest/DTC, industry momentum, turn-of-month, 52-week high) in the S&P universe, where the power gate said IC of about 0.028 is enough. Pick at most 2, each with a clear pressure mechanism (who is forced to trade, and why it reverses or persists). Run the power check first, then freeze before results.

Next check-in: when the sealed S&P panel exists (coverage report) OR when strategy #2 is frozen, whichever comes first. Holdout runs still need the user's approval.
