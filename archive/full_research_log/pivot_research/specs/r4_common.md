# Round 4 shared context (read first, every task)

PROJECT: UNSW FINS3666 group project, report due 20 Nov 2026. Workspace: C:\Users\musta\Desktop\UNSW\SSI\FINS3666\A2\pivot_research. Read RESEARCH_WORKFLOW_PLAN.md and specs\r4_goal.md: they are the rules.

THESIS TO KEEP (Advik's): measurable short-horizon buying pressure persists and/or spreads through a network of related assets. The original implementation (repo\pressure_heat_backtest_daily.py) works like this:
- "Pressure" combines close-location value, signed volume and intraday-minus-overnight return over 5 days.
- "Heat" diffuses that pressure on a 63-day correlation graph using exp(-L).
- It holds the top 5 of 30 Dow stocks, rebalanced weekly.
- It does not beat EW30 after costs.

HISTORY: about 100 variants were tried across earlier rounds (see prior_findings\, w1_engine\, r2_*\, r3_*\, oos3\, ROUND3_SUMMARY.md). They were mostly generic factor tilts that drifted from the thesis. Do NOT repeat that pattern.

DATA RULES:
- Development data only: Dow 30 daily, 2020-11-27 to 2026-10-30 (w1_engine\prices-daily*, repo\prices-daily*). Cross-asset ETF data is in oos3\xasset.
- SEALED: the Dow 30 for 2010-01-01 to 2020-10-31 is the holdout. Never download, load, plot or compute returns or signals on any pre-2020-06 Dow data. The one exception is L4: it may check AVAILABILITY only (roster lists and row counts), with no returns.
- The sealed-holdout tickers in specs\r3_holdout_basket.txt (country ETFs) are also off-limits.

ANTI-OVERFITTING:
- Hard budget of 30 variants for the whole goal, logged in specs\r4_trials.md.
- No parameter sweeps.
- Mechanism and predictive tests come before portfolios.
- Report all results, including failures.

WORKER RULES:
- Write only in your own folder.
- Never edit repo\ or other workers' folders.
- Plain English; cite only real sources with a working DOI or URL.
- The workspace is not a git repo, so skip the commit, push and PR steps. Finish with worker_done, giving --report-path to your main .md.
