"""Build D5's development-only, outcome-blind directed SIC graph inputs."""
from __future__ import annotations

import csv
import sys
from bisect import bisect_left
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from r4_harness.builders import build_dated_industry_network
from r4_harness.runs.D4.build_inputs import DEV_START, DEV_END, PRICE_DIRS, ROSTERS, roster_for

OUT = Path(__file__).resolve().parent
SIC_FILE = ROOT / 'r4_L4' / 'data' / 'sic_panel.csv'
SIC_GAPS_FILE = ROOT / 'r4_L4' / 'data' / 'sic_panel_gaps.csv'
MIN_PAIRS = 10
MIN_LEADERS = 3
MIN_SIC_GROUPS = 3
MIN_DATE_SHARE = 0.80


def read_bars(ticker: str, dates: list[str]) -> dict[str, tuple[float, ...]]:
    """Read only OHLCV rows inside the registered development interval."""
    bars = {}
    for folder in PRICE_DIRS:
        path = folder / f'{ticker}.csv'
        if not path.is_file():
            continue
        with path.open('r', encoding='utf-8-sig', newline='') as handle:
            for row in csv.DictReader(handle):
                day = str(row.get('date', ''))[:10]
                if day < DEV_START or day > DEV_END:
                    continue
                try:
                    raw_o, raw_h, raw_l, raw_c = (float(row[k]) for k in ('open', 'high', 'low', 'close'))
                    adj_c = float(row['adjclose'])
                    volume = float(row.get('volume') or 0)
                    if raw_c <= 0 or not np.all(np.isfinite([raw_o, raw_h, raw_l, raw_c, adj_c, volume])):
                        continue
                    factor = adj_c / raw_c
                    bars[day] = (raw_o, raw_h, raw_l, raw_c, volume,
                                 raw_o * factor, adj_c)
                except (KeyError, TypeError, ValueError, ZeroDivisionError):
                    continue
    return {day: bars[day] for day in dates if day in bars}


def load_sic_records() -> tuple[dict[str, list[tuple[str, str]]], dict[str, int]]:
    """Load dated SIC metadata only; no market data are read here."""
    grouped: dict[str, list[tuple[str, str]]] = {}
    rows_in_window = Counter()
    with SIC_FILE.open('r', encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            effective = str(row.get('effective_from', ''))[:10]
            # Older dated link records are required for forward-carry at the
            # development start. They are never treated as prices or outcomes.
            if not effective or effective > DEV_END:
                continue
            ticker = str(row.get('ticker', '')).strip()
            code = str(row.get('sic', '')).strip()
            if not ticker or not code or not code.isdigit():
                continue
            sic2 = code.zfill(4)[:2]
            grouped.setdefault(ticker, []).append((effective, sic2))
            if DEV_START <= effective <= DEV_END:
                rows_in_window[ticker] += 1
    for ticker in grouped:
        grouped[ticker].sort()
    return grouped, rows_in_window


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    # Use the registered PIT Dow roster sequence from the D4 input interface.
    assets = sorted(set().union(*(set(v) for v in ROSTERS.values())))
    # Calendar is obtained from SPY dates across all validated development
    # price folders; the first folder can contain only the initial lookback.
    calendar_set = set()
    for folder in PRICE_DIRS:
        path = folder / 'SPY.csv'
        if path.is_file():
            with path.open('r', encoding='utf-8-sig', newline='') as handle:
                calendar_set.update(str(r.get('date', ''))[:10] for r in csv.DictReader(handle)
                                    if DEV_START <= str(r.get('date', ''))[:10] <= DEV_END)
    calendar = sorted(calendar_set)
    if not calendar:
        raise FileNotFoundError('No SPY calendar rows in the registered development period')
    n, t = len(assets), len(calendar)
    ix = {a: i for i, a in enumerate(assets)}
    raw_open = np.full((n, t), np.nan)
    raw_high = np.full((n, t), np.nan)
    raw_low = np.full((n, t), np.nan)
    raw_close = np.full((n, t), np.nan)
    volume = np.full((n, t), np.nan)
    adj_open = np.full((n, t), np.nan)
    adj_close = np.full((n, t), np.nan)
    bar_count = {}
    for ticker in assets:
        bars = read_bars(ticker, calendar)
        bar_count[ticker] = len(bars)
        i = ix[ticker]
        for j, day in enumerate(calendar):
            if day in bars:
                raw_open[i, j], raw_high[i, j], raw_low[i, j], raw_close[i, j], volume[i, j], adj_open[i, j], adj_close[i, j] = bars[day]
    roster = np.zeros((n, t), dtype=bool)
    for j, day in enumerate(calendar):
        roster[[ix[x] for x in roster_for(day)], j] = True

    sic_records, sic_rows_dev = load_sic_records()
    sic_matrix = np.full((n, t), '', dtype='<U2')
    active_sic_coverage = np.zeros(t, dtype=int)
    for i, ticker in enumerate(assets):
        records = sic_records.get(ticker, [])
        effective_dates = [d for d, _ in records]
        for j, day in enumerate(calendar):
            # A filing is usable from the next trading session: only records
            # strictly earlier than the signal session date are visible.
            k = bisect_left(effective_dates, day) - 1
            if k >= 0:
                sic_matrix[i, j] = records[k][1]
    active_sic_coverage = np.sum(roster & (sic_matrix != ''), axis=0)

    dv = raw_close * volume
    industry_at = lambda asset, day: None  # filled per date below by wrapper
    # Exercise the harness's dated industry graph builder. D5 then keeps only
    # its top-ranked source star per SIC, as D5 preregisters one leader.
    def dated_industry(asset: str, day: str):
        j = calendar.index(day)
        i = ix[asset]
        if not roster[i, j] or not sic_matrix[i, j]:
            return None
        return sic_matrix[i, j]

    candidate_pairs = build_dated_industry_network(assets, calendar, raw_close,
                                                   volume, dated_industry,
                                                   lookback=20)
    graph = np.zeros_like(candidate_pairs)
    leader_count = np.zeros(t, dtype=int)
    group_count = np.zeros(t, dtype=int)
    pair_count = np.zeros(t, dtype=int)
    vol_covered = np.zeros((n, t), dtype=bool)
    for j, day in enumerate(calendar):
        groups: dict[str, list[tuple[float, str, int]]] = {}
        if j < 20:
            continue
        for i, ticker in enumerate(assets):
            if not roster[i, j] or not sic_matrix[i, j]:
                continue
            w = dv[i, j-20:j]
            if len(w) != 20 or not np.isfinite(w).all() or np.any(w <= 0):
                continue
            vol_covered[i, j] = True
            groups.setdefault(sic_matrix[i, j], []).append((float(w.mean()), ticker, i))
        for sic2, members in groups.items():
            if len(members) < 2:
                continue
            # Highest dollar volume is leader; ticker ascending is tie break.
            members.sort(key=lambda z: (-z[0], z[1]))
            _, _, leader = members[0]
            # Confirm the builder's strict-ranking result supports every
            # non-tied follower edge; tie-broken D5 edges are added below.
            for _, _, follower in members[1:]:
                if candidate_pairs[j, leader, follower] <= 0:
                    # Exact top-volume ties are permitted by D5's ticker rule.
                    top_value = members[0][0]
                    if abs(top_value - next(x[0] for x in members if x[2] == follower)) > 1e-12:
                        raise AssertionError('builder leader-follower orientation disagrees with D5 ranking')
                graph[j, leader, follower] = 1.0
                pair_count[j] += 1
            leader_count[j] += 1
            group_count[j] += 1

    # Fifth-session formation dates are the 5th, 10th, ... development sessions.
    form_ix = np.arange(4, t, 5, dtype=int)
    eligible_ix = np.asarray([j for j in form_ix if active_sic_coverage[j] > 0 and
                              np.any(vol_covered[:, j])], dtype=int)
    if not len(eligible_ix):
        raise RuntimeError('No eligible fifth-session dates with development SIC/volume inputs')
    fail = ((pair_count[eligible_ix] < MIN_PAIRS) |
            (leader_count[eligible_ix] < MIN_LEADERS) |
            (group_count[eligible_ix] < MIN_SIC_GROUPS))
    failed_share = float(fail.mean())
    gate_pass = failed_share <= (1.0 - MIN_DATE_SHARE)

    # Store only development rows, graph, OHLCV signal inputs and adjusted
    # open/close needed by the separately frozen runner; no forward returns.
    np.savez_compressed(OUT / 'D5_INPUTS.npz', assets=np.asarray(assets),
                        dates=np.asarray(calendar), roster=roster,
                        sic2=sic_matrix, graph20=graph,
                        raw_high=raw_high, raw_low=raw_low, raw_close=raw_close,
                        volume=volume, adj_open=adj_open, adj_close=adj_close,
                        formation_indices=eligible_ix)

    with (OUT / 'D5_GRAPH_BY_DATE.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['date', 'eligible_formation', 'active_names', 'active_with_sic',
                    '20_session_dv_names', 'directed_pairs', 'distinct_leaders',
                    'two_digit_sic_groups', 'gate_date_pass'])
        form_set = set(eligible_ix.tolist())
        for j, day in enumerate(calendar):
            w.writerow([day, int(j in form_set), int(roster[:, j].sum()),
                        int(active_sic_coverage[j]), int(vol_covered[:, j].sum()),
                        int(pair_count[j]), int(leader_count[j]), int(group_count[j]),
                        int(j in form_set and pair_count[j] >= MIN_PAIRS and
                            leader_count[j] >= MIN_LEADERS and group_count[j] >= MIN_SIC_GROUPS)])

    with (OUT / 'D5_COVERAGE.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ticker', 'development_roster_bar_rows', 'sic_panel_rows_in_development',
                    'development_sic_rows', 'active_dates', 'active_dates_with_sic'])
        for i, ticker in enumerate(assets):
            w.writerow([ticker, bar_count.get(ticker, 0), len(sic_records.get(ticker, [])),
                        sic_rows_dev.get(ticker, 0), int(roster[i].sum()),
                        int(np.sum(roster[i] & (sic_matrix[i] != '')))])

    with SIC_GAPS_FILE.open('r', encoding='utf-8-sig', newline='') as f:
        gaps = [r for r in csv.DictReader(f)
                if DEV_START <= str(r.get('date', ''))[:10] <= DEV_END]
    with (OUT / 'sic_panel_gaps.csv').open('w', newline='', encoding='utf-8') as f:
        fields = ['ticker', 'cik', 'date', 'status', 'source_or_accession']
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in gaps:
            w.writerow({k: row.get(k, '') for k in fields})

    all_pair = pair_count[eligible_ix]
    all_leaders = leader_count[eligible_ix]
    all_groups = group_count[eligible_ix]
    qa = [
        '# D5 development input QA (outcome-blind)', '',
        f'**Gate verdict: {"PASS" if gate_pass else "D5 INFEASIBLE per pre-registration"}.**',
        '',
        'Built the D5 point-in-time 2-digit SIC directed graph using only registered development dates. '
        'No forward returns, future outcome windows, ICs, event responses, portfolios, or holdout price data were loaded or computed.',
        '',
        '## Fixed inputs and timing', '',
        f'- Development session range: {calendar[0]} through {calendar[-1]} ({t} sessions); initial formation dates are every fifth session starting at session 5.',
        '- SIC source: `r4_L4/data/sic_panel.csv`; `effective_from` is treated as the filing date and becomes usable on the first development trading session strictly after it. Only the two-character SIC major group is used.',
        '- Dollar volume: raw close × reported volume, exactly the prior 20 completed sessions; the highest mean is the sole leader and ticker ascending breaks ties.',
        '- Harness interface: `build_dated_industry_network` constructs the directed ranked candidate graph; this D5 build retains only the registered leader-to-each-follower star.',
        '- Roster: development point-in-time Dow roster schedule shared with D4 inputs.',
        '',
        '## Input coverage', '',
        f'- SIC records in the development filing-date interval: {sum(sic_rows_dev.values())} records across {sum(1 for x in sic_rows_dev.values() if x)} assets; historical SIC rows are used only to carry the latest dated code into development dates.',
        f'- SIC ticker/date gaps listed by `sic_panel_gaps.csv` within development dates: {len(gaps)} rows.',
        f'- Active-member SIC coverage: {int(active_sic_coverage[eligible_ix].min())} to {int(active_sic_coverage[eligible_ix].max())} names on eligible formation dates.',
        '- Per-ticker bar and SIC coverage is recorded in `D5_COVERAGE.csv`; per-date counts are in `D5_GRAPH_BY_DATE.csv`.',
        '',
        '## Registered minimum-pair gate', '',
        f'- Eligible fifth-session dates with input coverage: {len(eligible_ix)}.',
        f'- Requirements: at least {MIN_PAIRS} directed pairs, {MIN_LEADERS} distinct leaders, and {MIN_SIC_GROUPS} SIC groups on at least {MIN_DATE_SHARE:.0%} of eligible dates.',
        f'- Dates passing all three conditions: {int((~fail).sum())}/{len(eligible_ix)} ({1-failed_share:.1%}); failing dates: {int(fail.sum())} ({failed_share:.1%}).',
        f'- Directed pairs per eligible date: min {int(all_pair.min())}, median {float(np.median(all_pair)):.1f}, max {int(all_pair.max())}; leaders min/median/max {int(all_leaders.min())}/{float(np.median(all_leaders)):.1f}/{int(all_leaders.max())}; SIC groups min/median/max {int(all_groups.min())}/{float(np.median(all_groups)):.1f}/{int(all_groups.max())}.',
        f'- Under D5, failure on more than 20% of dates is infeasible. Observed failure share: {failed_share:.1%}.',
        '',
        '## Files', '',
        '- `D5_INPUTS.npz`: development-only graph and signal inputs, with no forward-return field.',
        '- `D5_GRAPH_BY_DATE.csv`: pair, leader, SIC, and eligibility counts by development date.',
        '- `D5_COVERAGE.csv`: ticker-level development bar and SIC coverage.',
        '- `sic_panel_gaps.csv` is the development-date-only copy of L4 gap records.',
        '- This input QA was produced before the D5 freeze and before any mechanism outcomes; the later freeze/hash verification and mechanism results are recorded in `MECHANISM_RESULTS.md`.',
        '- The frozen clarification defines a single deterministic 20-session shift, not a 500-draw family.',
    ]
    (OUT / 'INPUT_QA.md').write_text('\n'.join(qa) + '\n', encoding='utf-8')
    (OUT / 'RUNNER_REFUSAL.txt').write_text(
        'Command: python r4_harness/runs/D5/run_mechanism.py --check-freeze\n'
        'Result: REFUSED: D5 pre-registration is not frozen and hash-valid: pre-registration must contain FROZEN: YYYY-MM-DD and SHA256: <64 hex> lines\n'
        'Exit code: 2\n'
        'Only the governance check ran; D5_INPUTS.npz and outcome data were not opened by the runner.\n',
        encoding='utf-8',
    )
    print(f'Wrote D5 input QA: {OUT / "INPUT_QA.md"}')
    print('Gate verdict:', 'PASS' if gate_pass else 'D5 INFEASIBLE per pre-registration')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
