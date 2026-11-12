# Online research protocol (L2 and L3 must follow this)

## How to search
1. Use web search. Do not rely on memory. For every claim you record, open the actual source page (journal page, SSRN, NBER, arXiv or the author's PDF).
2. Sources, in order of trust:
   - Peer-reviewed journals: Journal of Finance, JFE, RFS, JFQA, Review of Finance, Management Science, Journal of Financial Markets.
   - NBER and SSRN working papers with many citations.
   - arXiv q-fin.
   - Practitioner pieces (AQR, Research Affiliates, Two Sigma) for context only, never as primary evidence.
   - Never cite blogs or forums as evidence.
3. Search-term lists: write your planned search terms in SEARCH_LOG.md BEFORE searching, then record every query and how many useful hits it gave.
4. Snowballing from 3-5 anchor papers:
   - Backward: check each anchor's reference list.
   - Forward: check who cites the anchor (Google Scholar "Cited by").
   - This finds the newer evidence, the critiques and the failed replications.
5. Always search "<paper> replication" and "<effect> post-publication decay" (for example McLean and Pontiff 2016; Hou, Xue and Zhang 2020 "Replicating anomalies").

## How to read a paper (about 15 minutes each)
- **Abstract:** the claim.
- **Introduction:** the mechanism and the contribution.
- **Data section:** the universe, period, frequency and data source. Can WE get this data?
- **Main results table:** the effect size, the t-stat, and the horizon at which the effect shows up.
- **Robustness section:** does the effect hold in large caps, recent years and after costs?
- Separate "shown" (in a table) from "suggested" (in the discussion). Record the page or table number.

## Evidence card (one per paper, in EVIDENCE_CARDS.md)
- Citation: authors, year, title, journal, and a working DOI or URL. You must have opened it. Mark it VERIFIED or UNVERIFIED.
- Claim, in one sentence.
- Mechanism: why it works economically.
- Data: universe, period, frequency and source.
- Horizon of the effect, and its effect size (bps per day or week, or Sharpe), with the t-stat.
- Does it hold in large caps? After costs? After publication? Any replication or critique?
- Relevance to Advik's thesis (pressure, persistence, network spread), rated 0-3.
- Feasibility for us: can we build it from Dow daily OHLCV, free data (SEC EDGAR 13F, ETF holdings, FRED, yfinance), or UNSW FactSet? Rated 0-3, with the reason.
- Testable prediction for our data: the predicted sign and horizon.

## Quality bar
- At least 15 evidence cards. At least 10 must be VERIFIED and peer-reviewed or NBER.
- Never invent a paper, number or DOI. If you cannot verify something, mark it UNVERIFIED and say why.
- Include at least 2 cards that argue AGAINST the direction you are researching.
