# J2 ? Four-formation smoothed SIC2-relative reversal portfolio

**STATUS: FROZEN CANDIDATE ? AWAITING USER APPROVAL**

## Selection record

J2 is R9-V5, selected mechanically from the 12 pre-logged development candidates. It had the highest strategy net Sharpe among candidates with average active share at least 50% and cost/gross edge below 50%. Its development net Sharpe was 0.9239 versus 0.8804 for PIT EW30; active share was 83.33%, cost/gross edge was 22.49%, mean turnover was 69.66%, and the one-sided bootstrap p-value was 0.1884. These are exploratory development results; they are not confirmation.

## Frozen rules

1. **Fixed signal.** Use the J1 five-session adjusted-close return less the leave-one-out mean return of PIT same-SIC2 peers. Preserve the registered signal direction, one-session execution delay, SIC2 handling, point-in-time membership, and all J1 availability rules. Do not alter the score or add data sources.
2. **Smoothing.** At each scheduled fifth-session formation close, calculate each eligible Dow name's arithmetic mean J1 signal across the current formation and its previous three scheduled weekly formation dates. All four scores must be available and valid; otherwise that name is ineligible. Rank the smoothed scores ascending.
3. **Portfolio.** Hold the five lowest-scoring eligible names at equal 20% target weights. If fewer than five names qualify at a formation, keep the existing portfolio unchanged. Start the common development comparison with PIT EW30 on the common first formation, 2021-03-04. Execute target trades at the next session's open. Rebalance fully at each scheduled weekly formation and hold with price drift between formations.
4. **Costs and benchmark.** Charge 0.05% per dollar of actual traded notional, with buys and sells counted once. Compare with PIT EW30 on the same available-name and common-date basis. The selected construction has no turnover cap; report actual turnover and costs.
5. **Development evidence.** The common comparison period is 2021-03-04 through 2026-10-30. Selection used all 12 R9 candidates, with 3 prior R6 trials, for a DSR trial count of 15. Report the development results as exploratory. Only the user-approved, unchanged J2 may proceed to the single confirmatory holdout run under R9 rule 6.

## Approval gate

No sealed holdout data has been accessed. This candidate remains **AWAITING USER APPROVAL**. Approval applies only to the exact rules above and this SHA-256 content hash.

SHA-256 (content above this line): 23968857b7ebd15502274400e9c0335583656051999626acd6e44de839a9cf80
