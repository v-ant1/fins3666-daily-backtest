"""Outcome-blind builders for the common-owner and directed-industry candidates.

No function in this module accepts or computes forward returns. Network cubes
are returned as dates x source x target; signal matrices are assets x dates.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

import numpy as np


DEFAULT_13F_EDGE_FILE = (
    Path(__file__).resolve().parents[2]
    / 'r4_L4' / 'data' / '13f_cosine_overlap_edges.csv'
)


def _date_text(value) -> str:
    return str(value)[:10]


def _validate_dates(dates: Sequence) -> list[str]:
    result = [_date_text(d) for d in dates]
    if any(not d for d in result):
        raise ValueError('dates must be non-empty ISO date strings')
    if result != sorted(result) or len(set(result)) != len(result):
        raise ValueError('dates must be unique and sorted ascending')
    return result


def _network_cube(network, n_assets: int, n_dates: int) -> np.ndarray:
    """Return a copy/view with shape (date, source, target)."""
    g = np.asarray(network, dtype=float)
    if g.shape == (n_dates, n_assets, n_assets):
        return g
    if g.shape == (n_assets, n_assets, n_dates):
        return np.moveaxis(g, 2, 0)
    raise ValueError(
        f'network must have shape (T,N,N) or (N,N,T), got {g.shape}'
    )


def load_13f_cosine_edges(path: str | Path = DEFAULT_13F_EDGE_FILE) -> list[dict]:
    """Read L4's prebuilt cosine edges, containing no price/outcome fields."""
    required = {
        'report_date', 'ticker_i', 'ticker_j',
        'cosine_13f_portfolio_value_overlap', 'panel_availability_date',
    }
    with Path(path).open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f'13F edge file missing fields: {sorted(missing)}')
        rows = []
        for row in reader:
            if not row['panel_availability_date']:
                # A report quarter without a known public-availability date is
                # not safe to use as a point-in-time graph.
                continue
            rows.append(row)
    return rows


def build_common_owner_network(
    assets: Sequence[str], dates: Sequence, edges: Iterable[Mapping] | None = None,
    edge_file: str | Path = DEFAULT_13F_EDGE_FILE,
) -> np.ndarray:
    """Build an undirected, weighted, point-in-time 13F cosine graph.

    L4's ``panel_availability_date`` is the conservative public availability
    date (latest filing date among the parsed manager filings in a quarter).
    On each requested date, use the most recent report quarter whose panel was
    already public; carry that graph forward until a newer panel is available.
    Missing pairs/names remain zero. Output axes are date, source, target.
    """
    ds = _validate_dates(dates)
    names = list(assets)
    if len(set(names)) != len(names):
        raise ValueError('assets must be unique')
    rows = list(load_13f_cosine_edges(edge_file) if edges is None else edges)
    by_quarter: dict[tuple[str, str], list[tuple[str, str, float]]] = defaultdict(list)
    for r in rows:
        report = _date_text(r['report_date'])
        available = _date_text(r.get('panel_availability_date', ''))
        if not report or not available:
            continue
        try:
            weight = float(r['cosine_13f_portfolio_value_overlap'])
        except (TypeError, ValueError):
            continue
        if not np.isfinite(weight) or weight <= 0:
            continue
        by_quarter[(report, available)].append(
            (str(r['ticker_i']), str(r['ticker_j']), weight)
        )
    name_ix = {name: i for i, name in enumerate(names)}
    out = np.zeros((len(ds), len(names), len(names)), dtype=float)
    for ti, day in enumerate(ds):
        eligible = [key for key in by_quarter if key[1] <= day]
        if not eligible:
            continue
        # Report date determines information vintage; availability controls
        # when that vintage first enters the observable graph.
        report, available = max(eligible, key=lambda key: (key[0], key[1]))
        for left, right, weight in by_quarter[(report, available)]:
            if left not in name_ix or right not in name_ix or left == right:
                continue
            i, j = name_ix[left], name_ix[right]
            out[ti, i, j] = out[ti, j, i] = weight
    return out


def build_trailing_clv_pressure(
    high, low, close, lookback: int = 63, min_history: int = 20,
) -> np.ndarray:
    """Daily CLV normalized against each asset's strictly prior trailing CLV.

    Inputs are adjusted OHLC arrays shaped assets x dates. Raw CLV is
    ``(2*C-H-L)/(H-L)`` and is zero when H == L. At date t, z-scoring uses
    only raw CLV observations in ``[t-lookback, t)``; current and future
    observations are never used to estimate normalization parameters. Until
    ``min_history`` prior observations exist, the result is NaN.
    """
    h, l, c = (np.asarray(x, dtype=float) for x in (high, low, close))
    if h.ndim != 2 or h.shape != l.shape or h.shape != c.shape:
        raise ValueError('high, low and close must share assets x dates shape')
    if not isinstance(lookback, int) or lookback < 2:
        raise ValueError('lookback must be an integer >= 2')
    if not isinstance(min_history, int) or not 1 <= min_history <= lookback:
        raise ValueError('min_history must be in [1, lookback]')
    valid = np.isfinite(h) & np.isfinite(l) & np.isfinite(c) & (h >= l)
    span = h - l
    raw = np.full(h.shape, np.nan, dtype=float)
    normal = valid & (span > 0)
    raw[normal] = (2.0*c[normal] - h[normal] - l[normal]) / span[normal]
    raw[valid & (span == 0)] = 0.0
    out = np.full(raw.shape, np.nan, dtype=float)
    for t in range(raw.shape[1]):
        start = max(0, t - lookback)
        hist = raw[:, start:t]
        for i in range(raw.shape[0]):
            past = hist[i, np.isfinite(hist[i])]
            if len(past) < min_history or not np.isfinite(raw[i, t]):
                continue
            sd = float(past.std(ddof=0))
            if sd > 1e-12:
                out[i, t] = (raw[i, t] - float(past.mean())) / sd
            elif abs(float(raw[i, t]) - float(past.mean())) <= 1e-12:
                out[i, t] = 0.0
    return out


def build_peer_pressure(
    clv_pressure, network, lag: int = 1,
) -> np.ndarray:
    """Aggregate source pressure into targets using lagged weighted links.

    A target at t receives the normalized weighted average of connected source
    scores at t-lag, using the network snapshot from that same information
    date. For directed graphs, row=source and column=target. Output is
    assets x dates; dates with no usable incoming weight are NaN.
    """
    x = np.asarray(clv_pressure, dtype=float)
    if x.ndim != 2:
        raise ValueError('clv_pressure must be assets x dates')
    if not isinstance(lag, int) or lag < 1:
        raise ValueError('lag must be a positive integer')
    g = _network_cube(network, x.shape[0], x.shape[1])
    out = np.full(x.shape, np.nan, dtype=float)
    for t in range(lag, x.shape[1]):
        src_t = t - lag
        w = np.where(np.isfinite(g[src_t]) & (g[src_t] > 0), g[src_t], 0.0)
        for target in range(x.shape[0]):
            incoming = w[:, target]
            valid = np.isfinite(x[:, src_t]) & (incoming > 0)
            denom = float(incoming[valid].sum())
            if denom > 0:
                out[target, t] = float(incoming[valid] @ x[valid, src_t] / denom)
    return out


def sic_provider_from_records(
    records: Iterable[Mapping], asset_field: str = 'asset',
    sic_field: str = 'sic', available_field: str = 'available_date',
) -> Callable[[str, str], str | None]:
    """Create a dated SIC lookup that never reveals a not-yet-filed record.

    The caller must provide a genuine historical series with one row per
    security/SIC observation and a public availability date, such as the SEC
    10-K filing date. L4's current ``issuer_sic_snapshot.csv`` does not meet
    this contract and must not be used as a historical PIT panel.
    """
    by_asset: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for r in records:
        try:
            asset = str(r[asset_field])
            sic = str(r[sic_field]).strip()
            available = _date_text(r[available_field])
        except (KeyError, TypeError):
            continue
        if asset and sic and available:
            by_asset[asset].append((available, sic))
    for asset in by_asset:
        by_asset[asset].sort(key=lambda row: row[0])

    def industry_at(asset: str, date: str) -> str | None:
        day = _date_text(date)
        visible = [row for row in by_asset.get(str(asset), ()) if row[0] <= day]
        return visible[-1][1] if visible else None

    return industry_at


def build_dated_industry_network(
    assets: Sequence[str], dates: Sequence, close, volume,
    industry_at: Callable[[str, str], str | None],
    lookback: int = 63,
) -> np.ndarray:
    """Build a directed SIC graph from larger to smaller prior dollar volume.

    Industry membership is queried as-of each date through ``industry_at``.
    Within each SIC, all strictly ordered pairs point from the higher to the
    lower trailing mean dollar-volume issuer. Dollar volume uses close*volume
    observations strictly before the decision date. Ties and missing industry
    or volume histories generate no link. Edge weights are 1.0. Output axes
    are date, source, target. The dated SIC panel is a required caller input.
    """
    ds = _validate_dates(dates)
    names = list(assets)
    if len(set(names)) != len(names):
        raise ValueError('assets must be unique')
    c, v = np.asarray(close, float), np.asarray(volume, float)
    if c.shape != (len(names), len(ds)) or v.shape != c.shape:
        raise ValueError('close and volume must have assets x dates shape')
    if not isinstance(lookback, int) or lookback < 1:
        raise ValueError('lookback must be a positive integer')
    dollar = c * v
    out = np.zeros((len(ds), len(names), len(names)), dtype=float)
    for t, day in enumerate(ds):
        begin = max(0, t - lookback)
        industries: dict[str, list[tuple[int, float]]] = defaultdict(list)
        for i, asset in enumerate(names):
            sic = industry_at(asset, day)
            hist = dollar[i, begin:t]
            hist = hist[np.isfinite(hist) & (hist > 0)]
            if sic is not None and len(hist) and str(sic).strip():
                industries[str(sic).strip()].append((i, float(hist.mean())))
        for members in industries.values():
            for i, vi in members:
                for j, vj in members:
                    if i != j and vi > vj:
                        out[t, i, j] = 1.0
    return out


def reverse_direction(network) -> np.ndarray:
    """Reverse every directed edge while preserving date and weight."""
    g = np.asarray(network, dtype=float)
    if g.ndim != 3 or g.shape[1] != g.shape[2]:
        raise ValueError('network must have shape (T,N,N)')
    return np.swapaxes(g, 1, 2).copy()


def degree_preserving_shuffle(
    network, seed: int = 0, swaps_per_edge: int = 10,
) -> np.ndarray:
    """Undirected per-date degree-preserving edge swaps, retaining weights.

    Binary topology degrees and the observed edge-weight multiset are
    preserved per date. The fixed seed makes identical prefixes reproducible.
    Directed inputs are rejected; use ``reverse_direction`` for a directed
    orientation placebo.
    """
    g = np.asarray(network, dtype=float)
    if g.ndim != 3 or g.shape[1] != g.shape[2]:
        raise ValueError('network must have shape (T,N,N)')
    if not np.allclose(g, np.swapaxes(g, 1, 2), equal_nan=True):
        raise ValueError('degree-preserving shuffle requires undirected networks')
    if swaps_per_edge < 0:
        raise ValueError('swaps_per_edge must be non-negative')
    out = np.nan_to_num(g.copy(), nan=0.0)
    rng = np.random.default_rng(seed)
    n = out.shape[1]
    for t in range(out.shape[0]):
        edges = [(i, j, out[t, i, j]) for i in range(n)
                 for j in range(i+1, n) if out[t, i, j] > 0]
        attempts = swaps_per_edge * len(edges)
        for _ in range(attempts):
            if len(edges) < 2:
                break
            a, b = rng.choice(len(edges), size=2, replace=False)
            i, j, wij = edges[a]
            k, l, wkl = edges[b]
            if len({i, j, k, l}) < 4:
                continue
            if rng.random() < 0.5:
                k, l = l, k
            x, y = sorted((i, l))
            u, v = sorted((k, j))
            if x == y or u == v or (x, y) == (u, v):
                continue
            if out[t, x, y] > 0 or out[t, u, v] > 0:
                continue
            out[t, i, j] = out[t, j, i] = 0.0
            out[t, k, l] = out[t, l, k] = 0.0
            out[t, x, y] = out[t, y, x] = wij
            out[t, u, v] = out[t, v, u] = wkl
            edges[a] = (x, y, wij)
            edges[b] = (u, v, wkl)
    return out


def matched_same_industry_nonowners(
    common_owner_network, assets: Sequence[str], dates: Sequence,
    industry_at: Callable[[str, str], str | None], seed: int = 0,
) -> np.ndarray:
    """Sample non-owner pairs within SIC, matching owner-edge counts by SIC.

    For each date and SIC, sample as many currently unlinked pairs as there
    are positive common-owner pairs, without replacement. Sampled edges are
    symmetric; their weights are sampled from that SIC's owner-edge weights.
    If a SIC has too few non-owner pairs, all available pairs are used.
    """
    names = list(assets)
    ds = _validate_dates(dates)
    g = _network_cube(common_owner_network, len(names), len(ds))
    if len(set(names)) != len(names):
        raise ValueError('assets must be unique')
    rng = np.random.default_rng(seed)
    out = np.zeros_like(g)
    n = len(names)
    for t, day in enumerate(ds):
        groups: dict[str, list[int]] = defaultdict(list)
        for i, asset in enumerate(names):
            sic = industry_at(asset, day)
            if sic is not None and str(sic).strip():
                groups[str(sic).strip()].append(i)
        for members in groups.values():
            owners = [(i, j, g[t, i, j]) for p, i in enumerate(members)
                      for j in members[p+1:] if g[t, i, j] > 0]
            nonowners = [(i, j) for p, i in enumerate(members)
                         for j in members[p+1:] if g[t, i, j] <= 0]
            if not owners or not nonowners:
                continue
            chosen_ix = rng.choice(len(nonowners),
                                   size=min(len(owners), len(nonowners)),
                                   replace=False)
            weights = np.asarray([edge[2] for edge in owners], float)
            for k, q in enumerate(chosen_ix):
                i, j = nonowners[int(q)]
                w = float(weights[k % len(weights)])
                out[t, i, j] = out[t, j, i] = w
    return out
