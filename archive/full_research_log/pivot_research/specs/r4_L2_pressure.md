# L2 task: Phase 1 research on price pressure (persistence and measurement)

TARGET: the academic literature on how short-horizon buying pressure is measured, and on when it persists (continues) or reverts. Folder: r4_L2\ (write only here).

CHANGE: follow specs\r4_research_protocol.md exactly. Questions to answer:
1. MEASUREMENT: what are the best measures of buying pressure from daily or intraday data? Cover signed volume, order-flow imbalance, Lee-Ready, bulk-volume classification (Easley, Lopez de Prado and O'Hara 2012), Amihud and Kyle lambda, close-location value, the overnight vs intraday split (Lou, Polk and Skouras 2019, "A tug of war"), and retail flow (Boehmer, Jones, Zhang and Zhang 2021).
2. PERSISTENCE vs REVERSAL: when does pressure continue and when does it revert?
   - Theory and evidence on liquidity-driven pressure that reverts versus information-driven pressure that persists (Campbell, Grossman and Wang 1993; Llorente, Michaely, Saar and Wang 2002; Avramov, Chordia and Goyal 2006).
   - Flow-driven pressure: mutual fund flows and fire sales (Coval and Stafford 2007; Lou 2012).
   - ETF arbitrage pressure (Ben-David, Franzoni and Moussawi 2018).
   - Index and rebalance pressure.
3. WHAT DAILY OHLCV CAN AND CANNOT CAPTURE for large caps, and at which horizon (1 day, 1 week or 1 month) the effects live.
4. TRADABLE FORMS: event-conditioned designs (big pressure shocks) and long-short designs, with evidence on costs.

CONSTRAINTS:
- Use web search and verify every source.
- No backtests or outcome data. Research only.
- Check r4_L1\POSTMORTEM.md when it appears, and align your proposals with its root causes.

OWNERSHIP: r4_L2\ only.

OBSERVABLE ACCEPTANCE:
- r4_L2\SEARCH_LOG.md, and r4_L2\EVIDENCE_CARDS.md meeting the protocol's quality bar.
- r4_L2\SYNTHESIS.md: 2-3 candidate DIRECTIONS that substantially change the strategy while keeping the pressure thesis. Each needs:
  - mechanism and evidence (cards cited);
  - predicted sign and horizon;
  - required data and how to get it;
  - a test design (predictive test or event study first, then a long-short or concentrated portfolio, with active share of at least 50%);
  - a known failure mode.
