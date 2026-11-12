# Round 3 goal and stop rule (set by coordinator, 2026-11-10)

GOAL: find 2-3 strategy directions that "actually work", defined in advance as ALL of:
1. Chosen using only the selection periods (Dow and cross-asset, 2020-11-27..2022-12-30) under a rule written before testing.
2. On the four development test periods (Dow 2023-01-03..2024-02-23, Dow 2024-12-06..2025-12-31, Dow 2026-01-02..2026-10-30, cross-asset 2023-01-03..2026-10-30): Sharpe above EW30 in at least 3 of 4, and pooled excess return over EW30 positive after costs.
3. Clearly different from EW30: tracking error vs EW30 of at least 3% a year, or an active share of at least 20%.
4. Pooled block-bootstrap p-value vs EW30 below 0.10, reported together with the deflated Sharpe at the cumulative trial count.
5. Average turnover of 50% or less per rebalance, under the same actual-trade cost model (0.05%/side).
6. PASSES THE SEALED HOLDOUT, run once by the coordinator only: 30 single-country equity ETFs (list fixed in specs\r3_holdout_basket.txt), 2020-11-27..2026-10-30. Workers never download or test this universe.

WORKERS: use a fixed team of at most 4 Luna workers (GPT-6 Luna, high effort) for the whole goal: R3-A (inverse-heat optimisation), R3-R (researcher), R3-I (implementer), plus at most 1 spare. Do not start a new worker for each cycle. When a worker finishes a task, keep its terminal (do not release it) and give it the next task in that same terminal (`worker-start --task <id> --terminal <handle>`), so it keeps its context from earlier cycles. Start a replacement only if a worker has crashed or exited, and say so.

STOP RULE: stop when 2-3 directions meet 1-5 and pass 6, or after 4 research-implementation cycles, whichever comes first. If the budget runs out, report the honest negative result. Every variant run counts towards the trial total.
