"""Synthetic-only tests for D7's outcome-blind input builder."""
from __future__ import annotations

import csv
import datetime as dt
import tempfile
import unittest
from pathlib import Path

import numpy as np

from r4_harness.runs.D7 import build_inputs as b


def _write(path, rows, fields):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def _sessions():
    out=[];day=dt.date(2020,11,27)
    while len(out)<42:
        if day.weekday()<5:out.append(day.isoformat())
        day+=dt.timedelta(days=1)
    return out+[b.END]

class D7InputSyntheticTests(unittest.TestCase):
    def test_builder_clock_gate_and_price_free_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); sessions=_sessions(); members=sorted(b.roster_at(sessions[1]))
            cik={ticker:f'{100000+i:010d}' for i,ticker in enumerate(members)}
            earnings=[]; links=[]; sic=[]
            for i,ticker in enumerate(members):
                sic.append({'ticker':ticker,'cik':cik[ticker],'sic':'2000','effective_from':b.START,'source_url':'synthetic'})
                response=sessions[i+1]
                filing=sessions[i]
                acc=f'0000000000-{i+1:06d}'
                earnings.append({'ticker':ticker,'cik':cik[ticker],'company_name':ticker+' Co',
                    'acceptance_timestamp_et':filing+'T16:05:00-05:00','acceptance_timestamp_utc':filing+'T21:05:00Z',
                    'form':'8-K','items':'2.02','filing_date':filing,'report_date':f'2020-Q{i+1}',
                    'accession_number':acc,'source_url':'https://example.invalid/filing/'+acc})
                suppliers=[x for x in members if x!=ticker][:3]
                for j,supplier in enumerate(suppliers):
                    links.append({'customer_cik':cik[ticker],'customer_ticker':ticker,'supplier_cik':cik[supplier],
                        'supplier_ticker':supplier,'source_form':'10-K','source_accession':f'link-{i}-{j}',
                        'filing_date':sessions[0] if i else '2020-11-26','first_usable_session':b.START,
                        'valid_from':b.START,'valid_to':'','source_url':'https://example.invalid/link',
                        'valid_for_development':'true'})
            # All link filing dates use the pre-window day, so the expected next
            # session is the first development date.
            for row in links: row['filing_date']='2020-11-26'
            lf=root/'links.csv';ef=root/'earnings.csv';sf=root/'sic.csv';rf=root/'release.csv'
            _write(lf,links,list(links[0]));_write(ef,earnings,list(earnings[0]));_write(sf,sic,list(sic[0]))
            _write(rf,[{'customer_cik':cik[members[0]],'accession_number':earnings[0]['accession_number'],
                'release_timestamp_et':sessions[0]+'T16:10:00-05:00','exhibit_source_url':'https://example.invalid/exhibit'}],
                ['customer_cik','accession_number','release_timestamp_et','exhibit_source_url'])
            result=b.build(lf,ef,sf,root/'out',sessions=sessions,release_map_path=rf)
            self.assertTrue(result['gate']['pass'],result['gate'])
            with (root/'out'/'D7_EVENT_TABLE.csv').open(encoding='utf-8-sig',newline='') as f:
                table=list(csv.DictReader(f))
            first=next(x for x in table if x['accession_number']==earnings[0]['accession_number'])
            self.assertEqual(first['release_timestamp_et'],sessions[0]+'T16:10:00-05:00')
            self.assertEqual(first['f'],sessions[1]);self.assertEqual(first['a'],sessions[1]);self.assertEqual(first['response_session'],sessions[1])
            # An unknown release timestamp follows f even when acceptance is later.
            second=next(x for x in table if x['accession_number']==earnings[1]['accession_number'])
            self.assertEqual(second['release_timestamp_et'],'');self.assertEqual(second['response_session'],second['f'])
            qa=(root/'out'/'INPUT_QA.md').read_text(encoding='utf-8')
            self.assertIn('Gate verdict: PASS',qa)
            self.assertNotIn('{{',qa)
            with np.load(root/'out'/'D7_METADATA.npz',allow_pickle=False) as z:
                self.assertNotIn('adjusted_open',z.files);self.assertNotIn('adjusted_close',z.files)
                self.assertEqual(z['roster_mask'].shape[0],len(set(sum([list(x) for x in b.ROSTER_MEMBERS.values()],[]))))

    def test_unknown_release_does_not_use_acceptance_as_response_clock(self):
        sessions=['2024-01-02','2024-01-03','2024-01-04']
        row={'cik':'1','filing_date':'2024-01-02','acceptance_timestamp_et':'2024-01-03T18:00:00-05:00',
             'acceptance_timestamp_utc':'','accession_number':'x','ticker':'A','source_url':'x','form':'8-K','items':'2.02'}
        e=b.event_clock_row(row,sessions)
        self.assertEqual(e['f'],'2024-01-03');self.assertEqual(e['a'],'2024-01-04');self.assertEqual(e['response_session'],'2024-01-03')

if __name__=='__main__':unittest.main()
