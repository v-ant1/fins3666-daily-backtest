import csv, datetime, json
from pathlib import Path

root = Path('A2/pivot_research/sealed_holdout_dow')
sample = json.loads((root / 'AAPL_20100101_20201031_availability.json').read_text())
result = (sample.get('chart', {}).get('result') or [None])[0]
calendar = [datetime.datetime.fromtimestamp(int(x), datetime.timezone.utc).date().isoformat()
            for x in (result or {}).get('timestamp', [])]
windows = [
('MMM','2010-01-01','2020-10-31','MMM'),('AA','2010-01-01','2013-09-22','AA'),
('AXP','2010-01-01','2020-10-31','AXP'),('T','2010-01-01','2015-03-18','T'),
('BAC','2010-01-01','2013-09-22','BAC'),('BA','2010-01-01','2020-10-31','BA'),
('CAT','2010-01-01','2020-10-31','CAT'),('CVX','2010-01-01','2020-10-31','CVX'),
('KO','2010-01-01','2020-10-31','KO'),('DIS','2010-01-01','2020-10-31','DIS'),
('DD before DowDuPont merger','2010-01-01','2017-08-31','DD'),('DWDP','2017-09-01','2019-04-01','DWDP'),
('DOW','2019-04-02','2020-10-31','DOW'),('XOM','2010-01-01','2020-08-30','XOM'),
('GE','2010-01-01','2018-06-25','GE'),('HPQ','2010-01-01','2013-09-22','HPQ'),
('HD','2010-01-01','2020-10-31','HD'),('IBM','2010-01-01','2020-10-31','IBM'),
('INTC','2010-01-01','2020-10-31','INTC'),('JNJ','2010-01-01','2020-10-31','JNJ'),
('JPM','2010-01-01','2020-10-31','JPM'),('KFT','2010-01-01','2012-09-21','KFT'),
('MCD','2010-01-01','2020-10-31','MCD'),('MRK','2010-01-01','2020-10-31','MRK'),
('MSFT','2010-01-01','2020-10-31','MSFT'),('PFE','2010-01-01','2020-08-30','PFE'),
('PG','2010-01-01','2020-10-31','PG'),('TRV','2010-01-01','2020-10-31','TRV'),
('UTX membership (RTX lineage proxy)','2010-01-01','2020-08-30','RTX'),
('VZ','2010-01-01','2020-10-31','VZ'),('WMT','2010-01-01','2020-10-31','WMT'),
('CSCO','2010-01-01','2020-10-31','CSCO'),('UNH','2012-09-24','2020-10-31','UNH'),
('GS','2013-09-23','2020-10-31','GS'),('V','2013-09-23','2020-10-31','V'),
('NKE','2013-09-23','2020-10-31','NKE'),('AAPL','2015-03-19','2020-10-31','AAPL'),
('WBA','2018-06-26','2020-08-30','WBA'),('CRM','2020-08-31','2020-10-31','CRM'),
('AMGN','2020-08-31','2020-10-31','AMGN'),('HON','2020-08-31','2020-10-31','HON')]
out = Path('A2/pivot_research/r4_L4/samples/holdout_membership_window_metadata.csv')
with out.open('w', newline='', encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['ticker_or_lineage','membership_start','membership_end_inclusive','Yahoo_timestamps_in_membership_window','first_date','last_date','field_schema'])
    for label,start,end,ticker in windows:
        p=root/f'{ticker}_20100101_20201031_availability.json'
        if p.exists():
            j=json.loads(p.read_text()); r=(j.get('chart',{}).get('result') or [None])[0]
            ds=[datetime.datetime.fromtimestamp(int(x),datetime.timezone.utc).date().isoformat() for x in (r or {}).get('timestamp',[])]
            kept=[d for d in ds if start<=d<=end]
            q=(((r or {}).get('indicators') or {}).get('quote') or [{}])[0]
            schema='OHLCV field names present' if all(k in q for k in ('open','high','low','close','volume')) else 'No chart/schema'
        else: kept=[]; schema='Yahoo historical ticker not found'
        w.writerow([label,start,end,len(kept),kept[0] if kept else '',kept[-1] if kept else '',schema])
