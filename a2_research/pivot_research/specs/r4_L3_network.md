# L3 task: Phase 1 research on networks and how pressure propagates

TARGET: the literature on how shocks, pressure and information spread between related assets, and on which network definitions actually carry predictive signal. Folder: r4_L3\ (write only here).

CHANGE: follow specs\r4_research_protocol.md exactly. Questions to answer:
1. WHICH LINKS CARRY PRESSURE? Compare the evidence for each kind of network:
   - Economic links: customer-supplier (Cohen and Frazzini 2008; Menzly and Ozbas 2010).
   - Common ownership and overlapping fund holdings (Anton and Polk 2014, "Connected Stocks"; Greenwood and Thesmar 2011).
   - Shared ETF membership.
   - Analyst co-coverage (Ali and Hirshleifer 2020).
   - Industry or technology links (Lee, Sun, Wang and Zhang 2019).
   - Lead-lag between large and small, or more and less attention-grabbing, stocks (Lo and MacKinlay 1990; Hou 2007).
   - Return-correlation networks, which our current approach uses. Why might they fail?
2. PROPAGATION MATHS: what correctly models DIRECTED, lagged spread?
   - Granger and VAR networks; Diebold and Yilmaz connectedness (2014); transfer entropy.
   - Graph signal processing: low-pass vs high-pass filters. Is "own pressure minus diffused neighbour pressure" a meaningful residual?
   - Heat-kernel diffusion on graphs in finance, if any.
   - For each, how does it compare with our same-window symmetric exp(-L)?
3. CROSS-ASSET: how do pressure or flows propagate across asset classes (bonds, commodities, FX, equity ETFs)?
   - Time-series and cross-asset momentum and lead-lag.
   - Treasury-equity flows.
   - What an ASSET-APPROPRIATE method would look like for the 30 cross-asset ETFs, instead of treating them like stocks.
4. TRADABLE FORMS AND EVIDENCE IN LARGE CAPS: does each effect survive in large caps, in recent years and after costs?

CONSTRAINTS:
- Use web search and verify every source.
- No backtests. Research only.
- Check r4_L1\POSTMORTEM.md when it appears.

OWNERSHIP: r4_L3\ only.

OBSERVABLE ACCEPTANCE:
- r4_L3\SEARCH_LOG.md, and r4_L3\EVIDENCE_CARDS.md meeting the protocol's quality bar.
- r4_L3\SYNTHESIS.md: 2-3 candidate DIRECTIONS that keep "pressure spreads through a network" but use a better network and better propagation maths. At most one may be cross-asset, and it must use an asset-appropriate method. Each needs:
  - mechanism and evidence (cards cited);
  - network definition and data source;
  - predicted sign and horizon;
  - a placebo design (shuffled or random links);
  - a test design and a known failure mode.
