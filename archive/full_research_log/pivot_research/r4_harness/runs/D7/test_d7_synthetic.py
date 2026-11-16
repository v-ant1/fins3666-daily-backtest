"""Synthetic-only unit tests for the D7 runner; no project bundle is opened."""
from __future__ import annotations

import datetime as dt
import tempfile
import unittest
from pathlib import Path

import numpy as np

from r4_harness.runs.D7 import run_mechanism as d7
from r4_harness.phase3 import prereg_digest


def synthetic_bundle(metadata_path: Path, price_path: Path):
    # Weekday-only synthetic calendar; every input value is fabricated.
    days=[]; cur=dt.date(2020,11,27)
    while len(days)<90:
        if cur.weekday()<5: days.append(cur.isoformat())
        cur += dt.timedelta(days=1)
    n,t=30,len(days); rng=np.random.default_rng(44)
    op=100*np.exp(np.cumsum(rng.normal(0,.008,(n,t)),axis=1))
    cl=op*np.exp(rng.normal(0,.015,(n,t)))
    roster=np.ones((n,t),bool); sic=np.full((n,t),'20',dtype='U2')
    response=np.repeat(np.arange(5,35),3)
    customers=np.asarray([(3*d+k)%n for d in range(30) for k in range(3)],int)
    filing=[(dt.date.fromisoformat(days[i])-dt.timedelta(days=1)).isoformat() for i in response]
    acc=[f'0000000000-{i:06d}' for i in range(len(response))]
    sources=['https://example.invalid/exhibit']*len(response)
    edges=[]
    for c in range(n):
        edges.extend((c,(c+j)%n) for j in (1,2,3))
    ec,es=zip(*edges)
    np.savez_compressed(metadata_path,
        dates=np.asarray(days),assets=np.asarray([f'A{i:02}' for i in range(n)]),
        roster_mask=roster,sic2=sic,
        event_customer_idx=customers,event_customer_cik=np.asarray([str(100000+i) for i in range(len(response))]),
        event_filing_date=np.asarray(filing),event_form=np.asarray(['8-K']*len(response)),
        event_items=np.asarray(['2.02']*len(response)),
        event_release_timestamp_et=np.asarray(['']*len(response)),
        event_acceptance_timestamp_et=np.asarray(['']*len(response)),
        event_acceptance_timestamp_utc=np.asarray(['']*len(response)),
        event_accession_number=np.asarray(acc),event_source_url=np.asarray(sources),
        event_response_session=np.asarray([days[i] for i in response]),
        link_customer_idx=np.asarray(ec),link_supplier_idx=np.asarray(es),
        link_customer_cik=np.asarray([str(100000+x) for x in ec]),
        link_supplier_cik=np.asarray([str(100000+x) for x in es]),
        link_source_form=np.asarray(['10-Q']*len(ec)),
        link_source_accession=np.asarray([f'0000000000-{i:06d}' for i in range(len(ec))]),
        link_filing_date=np.asarray([(dt.date.fromisoformat(days[0])-dt.timedelta(days=1)).isoformat()]*len(ec)),
        link_source_url=np.asarray(['https://example.invalid/filing']*len(ec)),
        link_first_usable_session=np.asarray([days[0]]*len(ec)),
        link_valid_to=np.asarray(['']*len(ec)))
    np.savez_compressed(price_path,dates=np.asarray(days),assets=np.asarray([f'A{i:02}' for i in range(n)]),
                        adjusted_open=op,adjusted_close=cl)


class D7SyntheticTests(unittest.TestCase):
    def test_event_clock_combines_filing_and_timestamps(self):
        dates=['2024-01-02','2024-01-03','2024-01-04','2024-01-05']
        # Release after close and filing clock both point to the Jan 3 open.
        ix=d7.derive_response_session('2024-01-02','2024-01-02T16:05:00-05:00','2024-01-02T16:06:00-05:00',dates)
        self.assertEqual(dates[ix],'2024-01-03')
        # Unknown release time must use the filing-date anchor, not acceptance.
        ix=d7.derive_response_session('2024-01-02','','2024-01-04T12:00:00-05:00',dates)
        self.assertEqual(dates[ix],'2024-01-03')

    def test_six_registered_endpoints_on_fabricated_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            m=Path(td)/'metadata.npz'; p=Path(td)/'prices.npz'; synthetic_bundle(m,p)
            metadata=d7._load_bundle(m)
            d7._feasibility(metadata)  # metadata-only gate runs before prices are opened
            specdir=Path(td)/'specs'; specdir.mkdir()
            spec='# Synthetic test preregistration\nFROZEN: 2026-11-11\n'
            (specdir/'D7.md').write_text(spec+'SHA256: '+prereg_digest(spec)+'\n',encoding='utf-8')
            ledger=Path(td)/'r4_trials.md'
            ledger.write_text('| # | Approach | Variant | Pre-reg file | Date | Result |\n|---|---|---|---|---|---|\n',encoding='utf-8')
            out=d7.run(m,p,specdir,ledger,Path(td)/'out',execute=True)
            self.assertEqual(len(out['endpoints']),6)
            self.assertEqual(out['shuffle_distribution']['draws'],500)
            self.assertIn('D7-1 primary event-date rank IC',out['endpoints'])
            self.assertIn('D7-6 portfolio net excess vs EW30',out['endpoints'])
            self.assertEqual(out['endpoints']['D7-6 portfolio net excess vs EW30']['status'],'not_run')
            lines=[x for x in ledger.read_text(encoding='utf-8').splitlines() if x.startswith('| ') and x.split('|')[1].strip().isdigit()]
            self.assertEqual(len(lines),6)
            # Separately exercise the portfolio endpoint with fabricated prices;
            # it is not part of the result run because the synthetic IC gates fail.
            portfolio=d7._portfolio(d7._load_bundle(m,p),d7._event_shocks(d7._load_bundle(m,p)))
            self.assertEqual(portfolio['status'],'run')
            self.assertIn('bootstrap_p',portfolio)
            self.assertLessEqual(portfolio['strategy_turnover_executed_mean'],.50)

    def test_cli_requires_explicit_execute_before_input_access(self):
        # The actual prereg remains unfrozen; this call must stop at the flag
        # check and does not name or load any project input file.
        self.assertEqual(d7.main([]),2)

    def test_cli_rejects_unfrozen_prereg_before_opening_input(self):
        missing=Path('this-file-must-not-be-opened.npz')
        self.assertEqual(d7.main(['--execute','--metadata',str(missing)]),2)


if __name__=='__main__':
    unittest.main()
