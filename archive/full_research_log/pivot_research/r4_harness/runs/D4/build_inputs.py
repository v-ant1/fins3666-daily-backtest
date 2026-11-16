"""Build D4 development-only 50-manager network and CLV/NCP inputs.

This script is outcome-blind: it reads development OHLCV fields to form CLV
and reads the development 13F panel. It does not load or calculate forward
returns, mechanism statistics, or portfolio returns.
"""
from __future__ import annotations

import csv
import math
import sys
from bisect import bisect_right
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from r4_harness.builders import build_common_owner_network

OUT = Path(__file__).resolve().parent
DATA = ROOT / 'r4_L4' / 'data'
DEFAULT_PIT_ROSTER = DATA / '13f_top50_pit_roster.csv'
PRICE_DIRS = [ROOT / 'repo' / p for p in
              ('prices-daily-lookback', 'prices-daily', 'prices-daily-delisted')]
DEV_START, DEV_END = '2020-11-27', '2026-10-30'
SAFE_13F_START = '2020-06-01'
STALE_DAYS = 180  # r5 decision: flag observations older than two quarters

# D4 development point-in-time Dow rosters, aligned to the L1 development QA.
ROSTERS = {
    'pre2024-02-26': ['AAPL','AMGN','AXP','BA','CAT','CRM','CSCO','CVX','DIS','DOW','GS','HD','HON','IBM','INTC','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','PG','TRV','UNH','V','VZ','WBA','WMT'],
    '2024-02-26': ['AAPL','AMGN','AXP','AMZN','BA','CAT','CRM','CSCO','CVX','DIS','DOW','GS','HD','HON','IBM','INTC','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','PG','TRV','UNH','V','VZ','WMT'],
    '2024-11-08': ['AAPL','AMGN','AXP','AMZN','BA','CAT','CRM','CSCO','CVX','DIS','GS','HD','HON','IBM','JNJ','JPM','KO','MCD','MMM','MRK','MSFT','NKE','NVDA','PG','SHW','TRV','UNH','V','VZ','WMT'],
}
REPORT_ROSTER_BASE = set('MMM AXP AAPL BA CAT CSCO CVX DIS DOW GS HD IBM INTC JNJ JPM KO MCD MRK MSFT NKE PFE PG RTX TRV UNH V VZ WBA WMT XOM'.split())


def _parsed_filing(status: str) -> bool:
    status = str(status).lower()
    return status.startswith('parsed_') or status.startswith('pit_top50_bulk_parsed')


def report_roster_for(report_date: str) -> list[str]:
    """13F quarter-end roster used by the L4 50-manager panel builder."""
    members = set(REPORT_ROSTER_BASE)
    if report_date >= '2020-09-30':
        members -= {'PFE', 'XOM', 'RTX'}
        members |= {'AMGN', 'CRM', 'HON'}
    if report_date >= '2024-03-31':
        members -= {'WBA'}
        members |= {'AMZN'}
    if report_date >= '2024-12-31':
        members -= {'DOW', 'INTC'}
        members |= {'NVDA', 'SHW'}
    return sorted(members)


def roster_for(day: str) -> list[str]:
    if day < '2024-02-26':
        return ROSTERS['pre2024-02-26']
    if day < '2024-11-08':
        return ROSTERS['2024-02-26']
    return ROSTERS['2024-11-08']


def read_development_bars(ticker: str) -> dict[str, tuple[float, float, float, float, float]]:
    """Read adjusted OHLCV only for development dates; date guard precedes parsing."""
    bars = {}
    for folder in PRICE_DIRS:
        path = folder / f'{ticker}.csv'
        if not path.is_file():
            continue
        with path.open('r', encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                day = str(row.get('date', ''))[:10]
                # Do not parse price or volume fields outside the authorized
                # D4 development interval.
                if day < DEV_START or day > DEV_END:
                    continue
                try:
                    close = float(row['adjclose'])
                    raw_close = float(row['close'])
                    if raw_close == 0:
                        continue
                    factor = close / raw_close
                    values = (float(row['open']) * factor,
                              float(row['high']) * factor,
                              float(row['low']) * factor,
                              close, float(row.get('volume') or 0.0))
                except (KeyError, ValueError, TypeError, ZeroDivisionError):
                    continue
                if np.all(np.isfinite(values)):
                    bars[day] = values
    return bars


def make_calendar(tickers: list[str]) -> list[str]:
    spy = read_development_bars('SPY')
    if not spy:
        raise FileNotFoundError('No SPY calendar rows in the D4 development window')
    return sorted(spy)


def build_clv5(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    """Raw CLV averaged over t-4:t, requiring all five development sessions."""
    span = high - low
    raw = np.zeros_like(close, dtype=float)
    ok = np.isfinite(high) & np.isfinite(low) & np.isfinite(close) & (span > 0)
    raw[ok] = (2.0 * close[ok] - high[ok] - low[ok]) / span[ok]
    flat = np.isfinite(high) & np.isfinite(low) & np.isfinite(close) & (span == 0)
    raw[flat] = 0.0
    raw[~(ok | flat)] = np.nan
    result = np.full_like(raw, np.nan)
    for t in range(4, raw.shape[1]):
        window = raw[:, t-4:t+1]
        complete = np.isfinite(window).all(axis=1)
        result[complete, t] = window[complete].mean(axis=1)
    return result


def read_13f_panel(pit_roster_path: Path = DEFAULT_PIT_ROSTER):
    """Read 2020-06+ raw 13F positions and filing metadata only."""
    coverage = defaultdict(list)
    coverage_path = DATA / '13f_filing_coverage.csv'
    with coverage_path.open('r', encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            report = row['report_date']
            if report < SAFE_13F_START or report > '2026-09-30':
                continue
            coverage[report].append(row)

    positions = defaultdict(lambda: defaultdict(float))
    positions_path = DATA / '13f_holder_by_dow_stock.csv'
    with positions_path.open('r', encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            report = row['report_date']
            # Filter development-era filing quarters before parsing position values.
            if report < SAFE_13F_START or report > '2026-09-30':
                continue
            try:
                value = float(row.get('value_usd_thousands') or 0.0)
            except (ValueError, TypeError):
                continue
            manager = row['manager_cik'].lstrip('0') or '0'
            positions[report][(manager, row['ticker'])] += value
    fixed_roster = set()
    with (DATA / '13f_manager_rank_q2_2026.csv').open('r', encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            fixed_roster.add(row['manager_cik'].lstrip('0') or '0')
    pit_rosters = {}
    pit_roster_status = 'missing; provisional fixed Q2 2026 top-50 roster used'
    if pit_roster_path.is_file():
        with pit_roster_path.open('r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            cols = {x.lower(): x for x in (reader.fieldnames or [])}
            manager_col = next((cols[x] for x in ('manager_cik','cik','manager_id') if x in cols), None)
            report_col = next((cols[x] for x in ('report_date','report_period','report_quarter') if x in cols), None)
            avail_col = next((cols[x] for x in ('availability_filing_date','available_date','roster_available_date','public_date','acceptance_date','filing_date') if x in cols), None)
            if not all((manager_col, report_col, avail_col)):
                raise ValueError('PIT top-50 roster must have manager CIK, report date, and public availability date fields')
            by_report = defaultdict(lambda: {'members': set(), 'available': []})
            for row in reader:
                report = row[report_col]
                # Ignore any holdout-era roster rows before parsing manager/date fields.
                if report < SAFE_13F_START or report > '2026-09-30':
                    continue
                manager = row[manager_col].lstrip('0') or '0'
                available = row[avail_col][:10]
                if manager and available:
                    by_report[report]['members'].add(manager)
                    by_report[report]['available'].append(available)
            pit_rosters = {
                report: (x['members'], max(x['available']))
                for report, x in by_report.items() if x['members'] and x['available']
            }
        if pit_rosters:
            pit_roster_status = f'loaded {len(pit_rosters)} development-era report-quarter cohorts'
    return coverage, positions, fixed_roster, pit_rosters, pit_roster_status


def panel_edges(coverage, positions, all_assets, fixed_roster, pit_rosters):
    """Manager-normalized quarter edges per D4 draft and their public dates."""
    output = []
    quarter_qa = []
    reports = sorted(coverage)
    for report in reports:
        filings = [r for r in coverage[report]
                   if _parsed_filing(r['status']) and r['availability_filing_date']]
        eligible = pit_rosters.get(report, (fixed_roster, ''))
        roster_members, roster_available = eligible
        managers = sorted(({r['manager_cik'].lstrip('0') or '0' for r in filings}) & set(roster_members))
        available = max([r['availability_filing_date'] for r in filings
                         if (r['manager_cik'].lstrip('0') or '0') in managers] +
                        ([roster_available] if roster_available else []), default='')
        names = report_roster_for(report)
        totals = defaultdict(float)
        for (manager, ticker), value in positions[report].items():
            if manager in managers and ticker in names and value > 0:
                totals[manager] += value
        manager_weights = defaultdict(dict)
        for (manager, ticker), value in positions[report].items():
            if manager in managers and ticker in names and value > 0 and totals[manager] > 0:
                manager_weights[ticker][manager] = value / totals[manager]
        # Construct each issuer's vector on the same parsed-manager axis.
        vectors = {ticker: np.array([manager_weights[ticker].get(m, 0.0)
                                     for m in managers], dtype=float)
                   for ticker in names}
        norms = {ticker: float(np.linalg.norm(vec)) for ticker, vec in vectors.items()}
        edge_count = 0
        names_with_edges = set()
        for ix, left in enumerate(names):
            for right in names[ix+1:]:
                denom = norms[left] * norms[right]
                cosine = float(vectors[left] @ vectors[right] / denom) if denom else 0.0
                if cosine > 0:
                    edge_count += 1
                    names_with_edges.update((left, right))
                    output.append({
                        'report_date': report,
                        'panel_availability_date': available,
                        'ticker_i': left,
                        'ticker_j': right,
                        'cosine_13f_portfolio_value_overlap': cosine,
                    })
        possible = len(names) * (len(names)-1) / 2
        quarter_qa.append({
            'report_date': report,
            'panel_availability_date': available or 'not available',
            'parsed_manager_count': len(managers),
            'dow_roster_names': len(names),
            'dow_names_with_positive_edges': len(names_with_edges),
            'positive_undirected_edges': edge_count,
            'possible_undirected_edges': int(possible),
            'density': edge_count / possible if possible else 0.0,
        })
    return output, quarter_qa


def _next_session_index(availability_date: str, dates: list[str]) -> int:
    """First development trading date strictly after a filing/public date."""
    return bisect_right(dates, availability_date)


def _elapsed_quarter_boundaries(start: str, end: str) -> int:
    a, b = date.fromisoformat(start), date.fromisoformat(end)
    qa = a.year * 4 + (a.month - 1) // 3
    qb = b.year * 4 + (b.month - 1) // 3
    return max(0, qb - qa)


def _over_six_calendar_months(start: str, end: str) -> bool:
    a, b = date.fromisoformat(start), date.fromisoformat(end)
    month_index = a.year * 12 + a.month - 1 + 6
    year, month = divmod(month_index, 12)
    month += 1
    import calendar as _calendar
    expiry = date(year, month, min(a.day, _calendar.monthrange(year, month)[1]))
    return b > expiry


def _calendar_quarter_boundaries(start: str, end: str) -> int:
    a, b = date.fromisoformat(start), date.fromisoformat(end)
    return max(0, (b.year * 4 + (b.month - 1) // 3) -
               (a.year * 4 + (a.month - 1) // 3))


def filing_time_network(assets, dates, active, coverage, positions,
                        fixed_roster, pit_rosters, edge_method='cosine'):
    """Rebuild the graph after each manager filing becomes usable next session.

    ``edge_method='sum_min'`` implements D4's registered alternative overlap
    weight; the default cosine method preserves the existing primary builder.
    """
    if edge_method not in {'cosine', 'sum_min'}:
        raise ValueError("edge_method must be 'cosine' or 'sum_min'")
    names = list(assets)
    idx = {a: i for i, a in enumerate(names)}
    reports = sorted(coverage)
    filing_events = defaultdict(list)
    for report, rows in coverage.items():
        for row in rows:
            if not _parsed_filing(row['status']) or not row['availability_filing_date']:
                continue
            manager = row['manager_cik'].lstrip('0') or '0'
            filed = row['availability_filing_date'][:10]
            filing_events[manager].append({
                'report': report, 'filed': filed,
                'usable_index': _next_session_index(filed, dates),
            })
    for manager in filing_events:
        filing_events[manager].sort(key=lambda x: (x['report'], x['filed']))

    roster_events = []
    if pit_rosters:
        for report, (members, available) in pit_rosters.items():
            roster_events.append({
                'report': report, 'available': available,
                'usable_index': _next_session_index(available, dates),
                'members': set(members),
            })
        roster_events.sort(key=lambda x: (x['report'], x['available']))

    weights_cache = {}
    def manager_weights(manager, report):
        key = (manager, report)
        if key in weights_cache:
            return weights_cache[key]
        allowed = set(report_roster_for(report))
        values = {ticker: amount for (m, ticker), amount in positions[report].items()
                  if m == manager and ticker in allowed and amount > 0}
        total = sum(values.values())
        result = {ticker: value / total for ticker, value in values.items()} if total > 0 else {}
        weights_cache[key] = result
        return result

    t, n = len(dates), len(names)
    adjacency = np.zeros((t, n, n), dtype=float)
    ages = np.full(t, np.nan)
    quarter_ages = np.full(t, np.nan)
    age_from = np.full(t, '', dtype=object)
    manager_count = np.zeros(t, dtype=int)
    roster_size = np.zeros(t, dtype=int)
    network_available = np.zeros(t, dtype=bool)
    for ti, day in enumerate(dates):
        eligible_rosters = [x for x in roster_events if x['usable_index'] <= ti]
        if pit_rosters:
            if not eligible_rosters:
                continue
            cohort = max(eligible_rosters, key=lambda x: (x['report'], x['available']))
            roster_members = cohort['members']
            roster_event_date = cohort['available']
        else:
            roster_members = fixed_roster
            roster_event_date = ''
        roster_size[ti] = len(roster_members)

        latest = {}
        for manager in roster_members:
            visible = [x for x in filing_events.get(manager, ())
                       if x['usable_index'] <= ti]
            if visible:
                latest[manager] = max(visible, key=lambda x: (x['report'], x['filed']))
        if not latest:
            continue
        manager_count[ti] = len(latest)
        current_names = [a for a in roster_for(day) if a in idx]
        cols = sorted(latest)
        vectors = {}
        for ticker in current_names:
            vectors[ticker] = np.asarray([
                manager_weights(m, latest[m]['report']).get(ticker, 0.0)
                for m in cols
            ], dtype=float)
        norms = {ticker: float(np.linalg.norm(v)) for ticker, v in vectors.items()}
        for p, left in enumerate(current_names):
            i = idx[left]
            for right in current_names[p+1:]:
                j = idx[right]
                if edge_method == 'cosine':
                    denom = norms[left] * norms[right]
                    value = float(vectors[left] @ vectors[right] / denom) if denom > 0 else 0.0
                else:
                    value = float(np.minimum(vectors[left], vectors[right]).sum())
                if value > 0:
                    adjacency[ti, i, j] = adjacency[ti, j, i] = value
        if adjacency[ti].sum() <= 0:
            continue
        latest_dates = [x['filed'] for x in latest.values()]
        if roster_event_date:
            latest_dates.append(roster_event_date)
        age_from[ti] = max(latest_dates)
        ages[ti] = (date.fromisoformat(day) - date.fromisoformat(age_from[ti])).days
        quarter_ages[ti] = _calendar_quarter_boundaries(age_from[ti], day)
        network_available[ti] = True
    return adjacency, ages, quarter_ages, age_from, manager_count, roster_size, network_available


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # Include former 2020 quarter-end constituents because their filed
    # positions may be the last available 13F snapshot at development start.
    union = sorted(set(sum(ROSTERS.values(), [])) | REPORT_ROSTER_BASE)
    dates = make_calendar(union)
    n, t = len(union), len(dates)
    index = {name: i for i, name in enumerate(union)}
    op = np.full((n, t), np.nan)
    hi = np.full((n, t), np.nan)
    lo = np.full((n, t), np.nan)
    cl = np.full((n, t), np.nan)
    vol = np.full((n, t), np.nan)
    for ticker in union:
        bars = read_development_bars(ticker)
        i = index[ticker]
        for j, day in enumerate(dates):
            if day in bars:
                op[i, j], hi[i, j], lo[i, j], cl[i, j], vol[i, j] = bars[day]
    active = np.zeros((n, t), dtype=bool)
    for j, day in enumerate(dates):
        active[[index[x] for x in roster_for(day)], j] = True

    clv5 = build_clv5(hi, lo, cl)
    clv5[~active] = np.nan
    coverage, positions, fixed_roster, pit_rosters, pit_status = read_13f_panel(DEFAULT_PIT_ROSTER)
    edge_rows, quarter_qa = panel_edges(coverage, positions, union, fixed_roster, pit_rosters)
    (adjacency, ages, quarter_ages, graph_filing_dates, manager_count,
     manager_roster_size, network_available) = filing_time_network(
        union, dates, active, coverage, positions, fixed_roster, pit_rosters)
    row_sum = adjacency.sum(axis=2)
    weights = np.divide(adjacency, row_sum[:, :, None],
                        out=np.zeros_like(adjacency), where=row_sum[:, :, None] > 0)

    # D4's draft uses same-date 5-session mean raw neighbor CLV, with a graph
    # that was publicly available before the signal date.
    ncp = np.full((n, t), np.nan)
    for j in range(t):
        if not network_available[j]:
            continue
        usable_sources = np.isfinite(clv5[:, j])
        ncp[:, j] = np.sum(weights[j] * np.where(usable_sources, clv5[:, j], 0.0)[None, :], axis=1)
        ncp[row_sum[j] <= 0, j] = np.nan
        ncp[~active[:, j], j] = np.nan

    stale = np.asarray([
        bool(network_available[j] and graph_filing_dates[j] and
             _over_six_calendar_months(graph_filing_dates[j], day))
        for j, day in enumerate(dates)
    ], dtype=bool)
    usable = np.isfinite(ncp) & active
    total_obs = int(usable.sum())
    stale_obs = int((usable & stale[None, :]).sum())
    active_days = int(network_available.sum())
    age_values = ages[network_available]
    age_bins = [
        ('0-45 days', int(((age_values >= 0) & (age_values <= 45)).sum())),
        ('46-90 days', int(((age_values > 45) & (age_values <= 90)).sum())),
        ('91-180 days', int(((age_values > 90) & (age_values <= STALE_DAYS)).sum())),
        ('>180 days', int((age_values > STALE_DAYS).sum())),
    ]

    np.savez_compressed(
        OUT / 'D4_INPUTS.npz',
        assets=np.asarray(union), dates=np.asarray(dates),
        roster_mask=active, clv5=clv5, ncp=ncp,
        adjacency=adjacency, row_normalized_weights=weights,
        adjusted_open=op, adjusted_close=cl,
        network_age_days=ages, network_age_quarter_boundaries=quarter_ages,
        graph_latest_filing_date=np.asarray(graph_filing_dates, dtype=str),
        graph_manager_count=manager_count, manager_roster_size=manager_roster_size,
        network_stale_gt_2q=stale, manager_roster_source=np.asarray([pit_status]),
    )
    with (OUT / 'quarter_coverage.csv').open('w', newline='', encoding='utf-8') as f:
        fields = list(quarter_qa[0]) if quarter_qa else []
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows(quarter_qa)
    with (OUT / 'network_age_by_date.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['date', 'network_available_before_close', 'network_age_calendar_days',
                    'elapsed_calendar_quarter_boundaries', 'latest_incorporated_filing_date',
                    'managers_with_usable_filings', 'point_in_time_manager_roster_size',
                    'stale_gt_2_quarters', 'active_roster_names', 'valid_ncp_names',
                    'names_with_positive_edges', 'positive_undirected_edges',
                    'possible_undirected_edges', 'network_density'])
        for j, day in enumerate(dates):
            graph = adjacency[j]
            edge_count = int(np.count_nonzero(np.triu(graph > 0, k=1)))
            active_names = int(active[:, j].sum())
            possible = active_names * (active_names - 1) // 2
            positive_names = int(np.sum((graph > 0).sum(axis=0) + (graph > 0).sum(axis=1) > 0))
            w.writerow([day, bool(network_available[j]),
                        '' if not np.isfinite(ages[j]) else int(ages[j]),
                        '' if not np.isfinite(quarter_ages[j]) else int(quarter_ages[j]),
                        graph_filing_dates[j], int(manager_count[j]), int(manager_roster_size[j]),
                        bool(stale[j]), active_names, int(usable[:, j].sum()),
                        positive_names, edge_count, possible,
                        edge_count / possible if possible else 0.0])

    with (OUT / 'INPUT_QA.md').open('w', encoding='utf-8') as f:
        cohort_label = 'point-in-time' if pit_rosters else 'provisional'
        f.write('# D4 development input QA\n\n')
        f.write(f'Sample: {dates[0]} to {dates[-1]} ({t:,} SPY trading dates); {n} unique assets across point-in-time Dow rosters. This is input construction only: no forward returns, mechanism tests, or portfolios were loaded or computed. Price files were date-filtered to {DEV_START}..{DEV_END} before OHLCV fields were parsed. 13F quarters before {SAFE_13F_START} were rejected before positions were parsed.\n\n')
        f.write(f'**Manager-roster status:** `{DEFAULT_PIT_ROSTER}`: {pit_status}. ')
        if pit_rosters:
            f.write('The point-in-time top-50 roster was loaded and used for each available report-quarter cohort; this build does not use the fixed Q2 2026 manager cohort. Re-run only if the roster or underlying filings change before D4 freeze.\n\n')
        else:
            f.write('The point-in-time top-50 roster is missing; this QA and NPZ are provisional and use the available Q2 2026 manager list to select filing histories. Re-run after L4 supplies the dated roster, before D4 can be frozen or any outcome runner can execute.\n\n')
        f.write('## Network construction\n\n')
        f.write('Uses the L4 `13f_holder_by_dow_stock.csv` position panel and filing coverage dates. Each currently eligible manager contributes their latest filing usable before close; a filing dated d becomes usable on the next trading session. Manager positions are value-normalized over that report-quarter Dow holdings roster, combined into stock vectors, converted to cosine overlap, and masked to the point-in-time Dow roster. Diagonal entries are zero, and each nonzero row is normalized for NCP. Each filing can update the graph as soon as it becomes usable; the graph is carried between filings.\n\n')
        f.write('Graph age is reported in calendar days and elapsed calendar-quarter boundaries since the latest incorporated filing. Staleness follows the preregistration: strictly more than six calendar months old; stale graphs are retained.\n\n')
        f.write('## Quarterly 13F coverage\n\n')
        f.write('| Report quarter | Panel public date | Parsed managers (of 50) | Dow names in quarter roster | Names with positive edges | Positive links | Possible links | Density |\n|---|---:|---:|---:|---:|---:|---:|---:|\n')
        for q in quarter_qa:
            f.write(f"| {q['report_date']} | {q['panel_availability_date']} | {q['parsed_manager_count']} | {q['dow_roster_names']} | {q['dow_names_with_positive_edges']} | {q['positive_undirected_edges']} | {q['possible_undirected_edges']} | {q['density']:.3f} |\n")
        f.write('\n')
        available_quarters = [q for q in quarter_qa if q['positive_undirected_edges']]
        if available_quarters and all(q['density'] >= 1.0 for q in available_quarters):
            f.write('**Placebo constraint:** every available quarterly panel is a complete positive-weight graph (30/30 names and 435/435 possible links). Degree-preserving rewiring cannot change a complete graph’s topology, and edge-count-preserving random links also remain complete; the frozen runner therefore can only reassign the observed weight multiset for those two placebos. This tests weight assignment, not whether common-owner link identities matter, and should be treated as a substantive limitation before D4 is frozen.\n\n')
        f.write('## Daily network age and staleness\n\n')
        f.write(f'Network is available on {active_days:,}/{t:,} development dates ({active_days/t:.1%}). Age distribution across available network dates: min {np.min(age_values):.0f}, median {np.median(age_values):.0f}, p90 {np.quantile(age_values,.90):.0f}, p95 {np.quantile(age_values,.95):.0f}, max {np.max(age_values):.0f} calendar days; elapsed calendar-quarter boundaries min/median/p90/max {np.nanmin(quarter_ages):.0f}/{np.nanmedian(quarter_ages):.0f}/{np.nanquantile(quarter_ages,.90):.0f}/{np.nanmax(quarter_ages):.0f}. Manager count across available dates: min/median/p90/max {manager_count[network_available].min()}/{np.median(manager_count[network_available]):.0f}/{np.quantile(manager_count[network_available],.90):.0f}/{manager_count[network_available].max()} of a {np.median(manager_roster_size[network_available]):.0f}-manager {cohort_label} roster.\n\n')
        date_edges = np.asarray([int(np.count_nonzero(np.triu(adjacency[j] > 0, k=1))) for j in range(t)])
        date_possible = active.sum(axis=0) * (active.sum(axis=0) - 1) // 2
        date_density = np.divide(date_edges, date_possible, out=np.zeros(t, dtype=float), where=date_possible > 0)
        positive_ncp_dates = int(np.sum(np.sum(np.isfinite(ncp) & active, axis=0) >= 5))
        f.write('Per-date coverage, edge counts, and density are in `network_age_by_date.csv` (one row for every development trading date). Across available dates, positive edge count min/median/p90/max is '
                f'{date_edges[network_available].min()}/{np.median(date_edges[network_available]):.0f}/{np.quantile(date_edges[network_available], .90):.0f}/{date_edges[network_available].max()}, and density min/median/p90/max is '
                f'{date_density[network_available].min():.3f}/{np.median(date_density[network_available]):.3f}/{np.quantile(date_density[network_available], .90):.3f}/{date_density[network_available].max():.3f}. At least five finite NCP names are available on {positive_ncp_dates}/{t} dates. The input coverage gate is '
                f"{'PASS' if active_days == t and positive_ncp_dates == t and not stale.any() else 'FAIL'} (all dates have a network, five names with scores, and no >2-quarter-stale observations); this is not the mechanism gate.\n\n")
        f.write('| Age bin | Available network dates | Share of available dates |\n|---|---:|---:|\n')
        for label, count in age_bins:
            f.write(f'| {label} | {count} | {count/active_days:.1%} |\n')
        f.write(f'\nDaily asset-date signal observations with graph age strictly over six calendar months: {stale_obs:,}/{total_obs:,} ({stale_obs/total_obs:.2%} of valid NCP observations). A date with no public network panel remains unavailable and does not enter this denominator.\n\n')
        f.write('## Signal construction and artifacts\n\n')
        f.write('Raw daily CLV is `(2C-H-L)/(H-L)`, zero when `H=L`; D4 pressure is the mean raw CLV over the current and prior four sessions. NCP is `NCP[i,t] = sum_j W[i,j,t] * CLV5[j,t]` on the point-in-time roster; `W` is carried-forward cosine adjacency row-normalized per source and incorporates filings only after their next-session availability. This deliberately follows D4 draft semantics, rather than applying the generic builder’s past-z-scored CLV helper.\n\n')
        f.write('Artifacts: `D4_INPUTS.npz` (assets, development dates, active-roster mask, raw CLV5, NCP, adjacency, row weights, age, latest filing date, manager count and stale flags); `quarter_coverage.csv`; and `network_age_by_date.csv`. All source tables and price bars used here are development-era only.\n')
        f.write('\n## Frozen runner gate\n\n')
        f.write('`run_mechanism.py` contains the preregistered primary mechanism/placebo runner. It validates the D4 frozen date and matching SHA-256 before opening input arrays or any price files, and refuses execution while the PIT roster is missing or when the saved input bundle predates it. The required `--check-freeze` smoke check refused this unfrozen D4 draft with exit code 2; see `RUNNER_REFUSAL.txt`. The mechanism runner was not run.\n')
    print(f'Wrote D4 input QA and arrays: {t} dates, {len(quarter_qa)} 13F quarters, {total_obs} valid NCP name-dates; stale share={stale_obs/total_obs:.4%}')


if __name__ == '__main__':
    main()
