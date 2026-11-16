"""Frozen Round 3 inverse-heat portfolio weights for any 30-asset price folder.

CSV input: one <ticker>.csv per asset with date and adjclose columns. The signal
uses the same 63 completed daily returns, positive top-five union graph, and
unit-time heat kernel as the validated project engine. It returns weights only;
execution timing, 5 bp actual-trade costs, and ledger accounting belong to the
caller.
"""
from pathlib import Path
import csv
import numpy as np
from scipy.linalg import expm


def inverse_heat_least15_weights(price_folder, signal_date, tickers=None):
    """Return {ticker: weight} at a signal close for exactly 30 assets.

    The rule selects the 15 lowest off-diagonal heat-connectivity scores from a
    63-return positive top-five correlation graph, then weights them in
    proportion to inverse connectivity. CSVs must contain adjusted close data.
    """
    folder = Path(price_folder)
    if tickers is None:
        tickers = sorted(p.stem for p in folder.glob('*.csv'))
    tickers = list(tickers)
    if len(tickers) != 30 or len(set(tickers)) != 30:
        raise ValueError('exactly 30 unique tickers are required')
    prices = {}
    for ticker in tickers:
        path = folder / f'{ticker}.csv'
        with path.open(newline='', encoding='utf-8-sig') as f:
            rows = {r['date'][:10]: float(r['adjclose']) for r in csv.DictReader(f)
                    if r.get('date') and r.get('adjclose')}
        prices[ticker] = rows
    dates = sorted(set.intersection(*(set(v) for v in prices.values())))
    if signal_date not in dates:
        raise ValueError(f'signal date {signal_date} is not common to all 30 assets')
    end = dates.index(signal_date)
    if end < 64:
        raise ValueError('at least 64 price dates before and including signal_date are required')
    # Match the engine: return columns [iT-63:iT], hence the signal-day close
    # itself is excluded and the graph uses only completed prior close returns.
    px = np.array([[prices[t][d] for d in dates[:end + 1]] for t in tickers], dtype=float)
    ret = px[:, 1:] / px[:, :-1] - 1.0
    window = ret[:, end - 63:end]
    corr = np.corrcoef(window)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    np.fill_diagonal(corr, 1.0)
    graph = np.zeros_like(corr)
    for i in range(30):
        keep = [j for j in np.argsort(-corr[i]) if j != i and corr[i, j] > 0][:5]
        for j in keep:
            graph[i, j] = graph[j, i] = corr[i, j]
    degree = graph.sum(axis=1)
    laplacian = np.diag(degree) - graph
    heat = expm(-laplacian)
    np.fill_diagonal(heat, 0.0)
    connectivity = np.maximum(heat.sum(axis=1), 1e-8)
    selected = np.argsort(connectivity, kind='stable')[:15]
    raw = 1.0 / connectivity[selected]
    raw /= raw.sum()
    return {tickers[i]: float(w) for i, w in zip(selected, raw)}
