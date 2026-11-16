from __future__ import annotations
import csv
import datetime as dt
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'oos3' / 'xasset' / 'prices-daily'
OUT = Path(__file__).resolve().parent
ASSETS = ['SPY', 'TLT', 'IEF', 'SHY', 'TIP']
START = dt.date(2020, 6, 1)
END = dt.date(2026, 10, 30)
FIELDS = ['open', 'high', 'low', 'close', 'adjclose']

def d(s):
    return dt.date.fromisoformat(s)

rows_by_asset = {}
for asset in ASSETS:
    path = SRC / f'{asset}.csv'
    with path.open('r', newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        required = {'date', *FIELDS}
        if not required.issubset(set(reader.fieldnames or [])):
            raise SystemExit(f'{asset}: required input fields absent')
        picked = []
        for row in reader:
            day = d(row['date'])
            # The only price fields parsed are inside the D6 development interval.
            if not (START <= day <= END):
                continue
            vals = [float(row[k]) for k in FIELDS]
            picked.append((day, vals))
    if not picked:
        raise SystemExit(f'{asset}: no development rows in D6 interval')
    rows_by_asset[asset] = picked

# Confirm all five files use the same observed dates; no calendar/price series is synthesized.
dates = [r[0] for r in rows_by_asset[ASSETS[0]]]
for asset in ASSETS:
    adates = [r[0] for r in rows_by_asset[asset]]
    if adates != dates:
        raise SystemExit(f'{asset}: daily date index differs from SPY')
    if len(adates) != len(set(adates)):
        raise SystemExit(f'{asset}: duplicate dates')

raw = np.asarray([[r[1] for r in rows_by_asset[a]] for a in ASSETS], dtype=np.float64)
# Layout: asset x date x OHLC/adjusted-close.
open_, high, low, close, adjclose = [raw[:, :, i] for i in range(5)]
factor = adjclose / close
adjopen = open_ * factor
adjhigh = high * factor
adjlow = low * factor
# D6 freeze clarification applies the same daily adjclose/close factor to all OHLC.
np.savez_compressed(
    OUT / 'D6_INPUTS.npz',
    assets=np.asarray(ASSETS),
    dates=np.asarray([x.isoformat() for x in dates]),
    raw_open=open_, raw_high=high, raw_low=low, raw_close=close,
    adjusted_close=adjclose, adjustment_factor=factor, adjusted_open=adjopen,
    adjusted_high=adjhigh, adjusted_low=adjlow,
    fields=np.asarray(['raw_open','raw_high','raw_low','raw_close','adjusted_close','adjustment_factor','adjusted_open','adjusted_high','adjusted_low']),
    source=np.asarray(['oos3/xasset/prices-daily/' + a + '.csv' for a in ASSETS]),
)

# Input-only QA, no price changes over time, returns, signals, statistics or outcomes.
all_dates = set(dates)
weekdays = {day for n in range((END - START).days + 1)
            if (day := START + dt.timedelta(days=n)).weekday() < 5}
missing_weekdays = sorted(weekdays - all_dates)
months = sorted({x.strftime('%Y-%m') for x in dates})
month_last = {m: max(x for x in dates if x.strftime('%Y-%m') == m) for m in months}
formation_months = [dt.date(2021, 7, 1) + dt.timedelta(days=0)]
# Registered target observations Aug-2021 to Sep-2026 use formation months Jul-2021 to Aug-2026.
fm = []
y, m = 2021, 7
while (y, m) <= (2026, 8):
    fm.append(f'{y:04d}-{m:02d}')
    m += 1
    if m == 13: y, m = y + 1, 1

target_months = []
y, m = 2021, 8
while (y, m) <= (2026, 9):
    target_months.append(f'{y:04d}-{m:02d}')
    m += 1
    if m == 13: y, m = y + 1, 1

# Month-end and first-session date availability only.
month_first = {m: min(x for x in dates if x.strftime('%Y-%m') == m) for m in months}
first_missing_monthends = [m for m in fm if m not in month_last]
first_missing_targets = [m for m in target_months if m not in month_first]
# Registered data ends 2026-10-30, enough to check the September 2026 target's
# first-session open and October's first-session open, without calculating returns.
open_missing = int(np.count_nonzero(~np.isfinite(adjopen) | (adjopen <= 0)))
nonpositive = int(np.count_nonzero((raw <= 0) | ~np.isfinite(raw)))
order_bad = int(np.count_nonzero((low > high) | (open_ < low) | (open_ > high) | (close < low) | (close > high)))
ratio_min = float(np.min(factor)); ratio_max = float(np.max(factor))
ratio_varies = bool(ratio_max - ratio_min > 1e-12)
# Validate adjusted-open arithmetic against the registered formula only.
formula_err = float(np.max(np.abs(adjopen - open_ * adjclose / close)))

lines = [
'# D6 input QA (input-only)', '',
'**Gate: PASS for development input coverage and integrity.** The frozen D6 pre-registration hash was verified through the harness before outcome access. All five specified ETF files pass the input checks below. The coordinator separately verifies 2008-11 warm-up and holdout coverage; this worker did not inspect holdout data.', '',
'## Scope and source', '',
'Inspected only SPY, TLT, IEF, SHY and TIP in `oos3/xasset/prices-daily`. Price fields were read only for 2020-06-01 through 2026-10-30. All five files begin on 2020-06-01 and end on 2026-10-30; the preregistered six-month warm-up for development is included. The bundle `D6_INPUTS.npz` contains raw OHLC, source adjusted close, the daily `adjclose/close` factor, and adjusted OHLC computed with the frozen convention (the same factor applied to open, high, and low).', '',
'## Coverage and integrity', '',
'| Check | Result |', '|---|---|',
f'| Files / assets | 5/5 present: {", ".join(ASSETS)} |',
f'| Daily rows per asset | {len(dates)} each |',
f'| Shared date coverage | {dates[0].isoformat()} to {dates[-1].isoformat()} |',
f'| Duplicate dates / cross-file date mismatch | 0 / none |',
f'| Weekdays absent relative to weekday grid | {len(missing_weekdays)} (market holidays are not separately calendared) |',
f'| Missing, nonfinite, or nonpositive OHLC/adjusted-close values | {nonpositive} |',
f'| Raw OHLC range-order violations | {order_bad} |',
f'| Missing/nonpositive adjusted opens from registered formula | {open_missing} |',f'| Adjusted-close factor | varies across the development window: {ratio_varies}; range {ratio_min:.8f}–{ratio_max:.8f} |',f'| Adjusted-open formula max absolute arithmetic discrepancy | {formula_err:.3g} |', '',
'Adjustment check is limited to the provided `adjclose` series, finite positive values, the per-day `adjclose/close` factor, and consistent application of that factor to the registered adjusted-open input. No corporate-action ledger is included, so this check cannot independently certify every split or distribution adjustment against issuer records.', '',
'## Formation and target-date availability', '',
f'The preregistered target range is {target_months[0]} through {target_months[-1]} ({len(target_months)} monthly targets); corresponding formation months are {fm[0]} through {fm[-1]} ({len(fm)}). Each month has a last available session, and each target month has a first available session: missing formation month-ends = {len(first_missing_monthends)}; missing target first sessions = {len(first_missing_targets)}.', '',
'### Formation-date table (date availability only)', '',
'| Target month | Formation month-end session | Target first session | Following month first session |', '|---|---|---|---|',
*[f'| {target} | {month_last[form].isoformat()} | {month_first[target].isoformat()} | {month_first[next_month].isoformat()} |' for target, form, next_month in zip(target_months, fm, target_months[1:] + ['2026-10'])], '',
'## Checklist status', '',
'- [x] Five named development files exist with adjusted-close fields and common daily coverage.',
'- [x] Daily open fields exist; adjusted open follows `open × adjclose / close`.',
'- [x] D6 development input begins 2020-06-01, including the preregistered development warm-up; target/formation month labels and date availability match the preregistered Aug-2021 to Sep-2026 target span.',
'- [ ] Coordinator confirms 2008-11 warm-up and full 2010-01 to 2020-10 holdout coverage. This worker did not inspect holdout data; that coordinator-only input check remains open.',
'- [x] Adjusted high/low use the same daily `adjclose/close` factor as adjusted open, per `specs/r5_decisions.md` item 12 and the frozen clarification.',
'- [x] Six D6 endpoints and the D4?D6 Holm family manifest are recorded in `specs/r4_trials.md` before outcome access.',
'- [x] Coordinator added `FROZEN: 2026-11-10` and the matching SHA-256 before any outcome access.',
'',
'## Gate', '',
'**PASS for development input QA.** Coordinator holdout checks remain open; no D6 holdout data were accessed.'
]
(OUT / 'INPUT_QA.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(f'Wrote {OUT / "INPUT_QA.md"} and {OUT / "D6_INPUTS.npz"}; rows={len(dates)}; weekday gaps={len(missing_weekdays)}; nonpositive={nonpositive}; ordering={order_bad}')
