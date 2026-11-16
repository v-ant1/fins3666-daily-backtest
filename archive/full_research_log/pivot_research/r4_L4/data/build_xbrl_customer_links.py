"""Build Dow point-in-time customer concentration facts from SEC XBRL filings.

Companyfacts/frames omit dimensional facts for this use case, so the script
reads only original SEC inline XBRL filing documents (and the standalone
instance XML for older filings). It never accesses market data.
"""
import csv, json, re, time, warnings
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

OUT = Path(__file__).resolve().parent
START = date(2009, 1, 1)
HOLDOUT_END = date(2020, 10, 31)
DEV_START = date(2020, 11, 27)
DEV_END = date(2026, 10, 30)
UA = "FINS3666 XBRL data research contact research@example.edu"
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
last = [0.0]

def get(url, as_json=False):
    delay = 0.20 - (time.monotonic() - last[0])
    if delay > 0:
        time.sleep(delay)
    r = S.get(url, timeout=90)
    r.raise_for_status()
    last[0] = time.monotonic()
    return r.json() if as_json else r.content

# Half-open Dow membership intervals, effective first trading date.
BASE = [
    ('MMM','0000066740',date(2010,1,1)),('AA','0000004281',date(2010,1,1)),
    ('AXP','0000004962',date(2010,1,1)),('T','0000732717',date(2010,1,1)),
    ('BAC','0000070858',date(2010,1,1)),('BA','0000012927',date(2010,1,1)),
    ('CAT','0000018230',date(2010,1,1)),('CSCO','0000858877',date(2010,1,1)),
    ('CVX','0000093410',date(2010,1,1)),('KO','0000021344',date(2010,1,1)),
    ('DIS','0001001039',date(2010,1,1)),('DD','0000030554',date(2010,1,1)),
    ('XOM','0000034088',date(2010,1,1)),('GE','0000040545',date(2010,1,1)),
    ('HPQ','0000047217',date(2010,1,1)),('HD','0000354950',date(2010,1,1)),
    ('IBM','0000051143',date(2010,1,1)),('INTC','0000050863',date(2010,1,1)),
    ('JNJ','0000200406',date(2010,1,1)),('JPM','0000019617',date(2010,1,1)),
    ('KFT','0001103982',date(2010,1,1)),('MCD','0000063908',date(2010,1,1)),
    ('MRK','0000310158',date(2010,1,1)),('MSFT','0000789019',date(2010,1,1)),
    ('PFE','0000078003',date(2010,1,1)),('PG','0000080424',date(2010,1,1)),
    ('TRV','0000086312',date(2010,1,1)),('UTX','0000101829',date(2010,1,1)),
    ('VZ','0000732712',date(2010,1,1)),('WMT','0000104169',date(2010,1,1)),
]
CHANGES = [
    (date(2012,9,24), [('UNH','0000731766')], ['KFT']),
    (date(2013,9,23), [('GS','0000886982'),('V','0001403161'),('NKE','0000320187')], ['AA','BAC','HPQ']),
    (date(2015,3,19), [('AAPL','0000320193')], ['T']),
    (date(2017,9,1), [('DWDP','0001666700')], ['DD']),
    (date(2018,6,26), [('WBA','0001618921')], ['GE']),
    (date(2019,4,2), [('DOW','0001751788')], ['DWDP']),
    (date(2020,8,31), [('CRM','0001108524'),('AMGN','0000318154'),('HON','0000773840')], ['XOM','PFE','UTX']),
    (date(2024,2,26), [('AMZN','0001018724')], ['WBA']),
    (date(2024,11,8), [('NVDA','0001045810'),('SHW','0000089800')], ['DOW','INTC']),
]
INTERVALS = []
active = [(t,c,date(2010,1,1)) for t,c,_ in BASE]
for cut,adds,drops in CHANGES:
    for ticker,cik,start in list(active):
        if ticker in drops:
            INTERVALS.append((ticker,cik,start,cut))
            active.remove((ticker,cik,start))
    for ticker,cik in adds:
        active.append((ticker,cik,cut))
for ticker,cik,start in active:
    INTERVALS.append((ticker,cik,start,date(2026,10,31)))
# Disney's registrant CIK changed on the successor company's March 2019 filing.
INTERVALS = [x for x in INTERVALS if x[0] != 'DIS']
INTERVALS += [('DIS','0001001039',date(2010,1,1),date(2019,3,20)),
              ('DIS','0001744489',date(2019,3,20),date(2026,10,31))]

def member_for(cik, day):
    return next(((t,lo,hi) for t,c,lo,hi in INTERVALS if c==cik and lo<=day<hi), None)

def local(qname):
    return str(qname or '').split(':')[-1].split('}')[-1]

def attr_ci(tag, name):
    n=name.lower()
    return next((v for k,v in tag.attrs.items() if str(k).lower()==n), '')

def contexts_from(soup):
    out={}
    for c in soup.find_all(lambda x: x.name and local(x.name).lower()=='context'):
        cid=attr_ci(c,'id')
        if not cid: continue
        period={}
        for p in c.find_all(lambda x: x.name and local(x.name).lower() in {'startdate','enddate','instant'}):
            period[local(p.name).lower()]=p.get_text(strip=True)
        dims=[]
        for d in c.find_all(lambda x: x.name and local(x.name).lower() in {'explicitmember','typedmember'}):
            dims.append((attr_ci(d,'dimension'),d.get_text(strip=True)))
        out[cid]={'period':period,'dimensions':dims}
    return out

def parse_doc(data, is_xml=False):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', XMLParsedAsHTMLWarning)
        soup=BeautifulSoup(data,'xml' if is_xml else 'lxml')
    contexts=contexts_from(soup)
    facts=[]
    # Inline XBRL facts are ix:nonFraction elements with a name attribute.
    for tag in soup.find_all(lambda x: x.name and local(x.name).lower()=='nonfraction' and 'concentrationriskpercentage' in str(attr_ci(x,'name')).lower()):
        facts.append((attr_ci(tag,'name'),attr_ci(tag,'contextref'),tag.get_text(strip=True),attr_ci(tag,'scale'),attr_ci(tag,'sign')))
    # Older XBRL filings provide facts as namespace-qualified elements in the instance XML.
    for tag in soup.find_all(lambda x: x.name and 'concentrationriskpercentage' in local(x.name).lower() and local(x.name).lower()!='nonfraction'):
        facts.append((tag.name,attr_ci(tag,'contextref'),tag.get_text(strip=True),attr_ci(tag,'scale'),attr_ci(tag,'sign')))
    return contexts, facts

def get_cik_records(cik):
    root=get(f'https://data.sec.gov/submissions/CIK{cik}.json',True)
    blocks=[root.get('filings',{}).get('recent',{})]
    for meta in root.get('filings',{}).get('files',[]):
        if meta.get('filingTo','') >= '2009-01-01' and meta.get('filingFrom','') <= '2026-10-31':
            blocks.append(get('https://data.sec.gov/submissions/'+meta['name'],True))
    seen=set(); out=[]
    for b in blocks:
        keys=['accessionNumber','filingDate','reportDate','form','primaryDocument','isInlineXBRL']
        cols={k:b.get(k,[]) for k in keys}
        for i,acc in enumerate(cols['accessionNumber']):
            if not acc or acc in seen: continue
            seen.add(acc)
            r={k:(cols[k][i] if i<len(cols[k]) else '') for k in keys}
            try: fd=date.fromisoformat(r['filingDate'])
            except Exception: continue
            try: report_day=date.fromisoformat(r['reportDate'])
            except Exception: report_day=fd
            # Major-customer disclosures are principally annual 10-K facts; the
            # narrower form set keeps the document pull bounded and auditable.
            if (date(2009,1,1)<=fd<=DEV_END and r['form'].upper() in {'10-K','10-K/A'}
                    and member_for(cik,report_day)):
                out.append(r)
    return out

def accession_base(cik, accession):
    return f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace("-","")}/'

def primary_and_instance(cik,r):
    base=accession_base(cik,r['accessionNumber'])
    primary=r['primaryDocument']
    try:
        dat=get(base+primary)
        contexts,facts=parse_doc(dat,primary.lower().endswith('.xml'))
        if facts:
            return primary,contexts,facts,base+primary
    except Exception:
        pass
    # Pre-inline-XBRL filings: use the one instance XML in the filing directory,
    # excluding taxonomy, calculation, definition, label, presentation and report files.
    try:
        idx=get(base+'index.json',True)
        items=idx.get('directory',{}).get('item',[])
        candidates=[]
        for it in items:
            name=it.get('name','')
            low=name.lower()
            if not low.endswith('.xml') or low in {'filingsummary.xml'}: continue
            if re.search(r'_(cal|def|lab|pre|ref)\.xml$',low) or re.fullmatch(r'r\d+\.xml',low): continue
            candidates.append(name)
        # Old SEC instance files conventionally start with ticker and a
        # hyphenated period date, e.g. intc-20091226.xml.
        tickers={t.lower() for t,c,lo,hi in INTERVALS if c==cik}
        preferred=[n for n in candidates if any(n.lower().startswith(t+'-') for t in tickers)]
        if preferred:
            candidates=preferred
        for name in candidates:
            dat=get(base+name)
            contexts,facts=parse_doc(dat,True)
            if facts:
                return name,contexts,facts,base+name
    except Exception:
        pass
    return primary,{},[],base+primary

def build_ticker_map():
    j=get('https://www.sec.gov/files/company_tickers_exchange.json',True)
    fields=j['fields']; out={}
    for row in j['data']:
        d=dict(zip(fields,row)); out[str(d['cik']).zfill(10)]={'ticker':str(d['ticker']).upper(),'name':str(d['name'])}
    # Public names whose member labels use their older/short legal name.
    aliases={'dell':'DELL','dellinc':'DELL','hp':'HPQ','hpinc':'HPQ','hewlettpackard':'HPQ',
             'walmart':'WMT','walmartinc':'WMT','wal-mart':'WMT','amazon':'AMZN','amazoncom':'AMZN',
             'apple':'AAPL','microsoft':'MSFT','boeing':'BA','cisco':'CSCO','intel':'INTC',
             'ibm':'IBM','johnsonandjohnson':'JNJ','unitedhealth':'UNH','verizon':'VZ',
             'att':'T','attinc':'T','cocacola':'KO','cocacolacompany':'KO','pepsico':'PEP',
             'proctergamble':'PG','proctergamblecompany':'PG','target':'TGT','ford':'F','general':'',
             'alphabet':'GOOGL','google':'GOOGL','meta':'META','facebook':'META','nvidia':'NVDA',
             'salesforce':'CRM','salesforcecom':'CRM','amgen':'AMGN','honeywell':'HON',
             'unitedparcelservice':'UPS','fedex':'FDX','lenovo':'LNVGY'}
    aliases.update({'hewlettpackardcompany':'HPQ','lenovogrouplimited':'LNVGY',
                    'unitedcontinentalairlines':'UAL','hawaiianairlines':'HA',
                    'amerisourcebergencorporation':'ABC'})
    return out,aliases

def generic_member(member):
    m=re.sub(r'(?i)member$','',local(member))
    m=re.sub(r'[^A-Za-z0-9]','',m)
    return bool(re.match(r'(?i)^(customer|company|client|buyer|majorcustomer|othercustomer|unnamed|anonymous)(?:[a-z0-9]+)?$',m)) or m in {'','MajorCustomers','Customers'}

def resolve_member(member, bycik, aliases):
    if generic_member(member): return '', '', 'generic'
    raw=local(member)
    core=re.sub(r'(?i)member$','',raw)
    core=re.sub(r'[^A-Za-z0-9]','',core)
    # Remove taxonomy/company prefixes accidentally included in malformed member names.
    low=core.lower()
    if 'mckessoncorporationamerisourcebergencorporationandcardinalhealth' in low:
        return 'McKesson, AmerisourceBergen and Cardinal Health (combined member)','','named_group'
    if low in aliases:
        ticker=aliases[low]
        rec=next((v for v in bycik.values() if v['ticker']==ticker),None)
        return (rec['name'] if rec else core),ticker,'named_listed' if ticker else 'named_unmatched'
    norm=lambda x: re.sub(r'[^a-z0-9]','',x.lower())
    # Exact normalized company-name or ticker match.
    for v in bycik.values():
        n=norm(v['name'])
        nbase=re.sub(r'(incorporated|inc|corporation|corp|company|co|limited|ltd)$','',n)
        if low in {n,nbase} or low==v['ticker'].lower():
            return v['name'],v['ticker'],'named_listed'
    # Camel-case member text is retained as the display name even without a ticker match.
    display=re.sub(r'(?<!^)(?=[A-Z])',' ',core).strip()
    return display,'','named_unmatched'

def number_to_percent(text,scale,sign):
    valtxt=re.sub(r'[,$\s]','',text)
    if valtxt.startswith('(') and valtxt.endswith(')'): valtxt='-'+valtxt[1:-1]
    try: val=Decimal(valtxt)
    except InvalidOperation: return None
    if sign=='-' and val>0: val=-val
    try: exponent=int(scale or 0)
    except ValueError: exponent=0
    return val*(Decimal(10)**exponent)*Decimal(100)

def main():
    bycik,aliases=build_ticker_map()
    ciks=sorted({c for _,c,_,_ in INTERVALS})
    filings=[]
    for i,cik in enumerate(ciks,1):
        try:
            for r in get_cik_records(cik): filings.append((cik,r))
        except Exception as e:
            print('SUBMISSIONS_ERROR',cik,str(e),flush=True)
        print(f'SUBMISSIONS {i}/{len(ciks)} {cik}',flush=True)
    rows=[]; scanned=0; docs_with_candidate=0; errors=[]
    for i,(cik,r) in enumerate(filings,1):
        try: fd=date.fromisoformat(r['filingDate'])
        except Exception: continue
        try:
            filename,contexts,facts,url=primary_and_instance(cik,r)
        except Exception as e:
            errors.append((cik,r['accessionNumber'],str(e))); contexts={}; facts=[]; url=''
        scanned+=1
        local_rows=[]
        for name,ctxref,value,scale,sign in facts:
            if 'concentrationriskpercentage' not in str(name).lower(): continue
            ctx=contexts.get(ctxref)
            if not ctx: continue
            dims=ctx['dimensions']
            customer_dims=[(axis,member) for axis,member in dims
                           if ('customer' in local(axis).lower() and 'bytype' not in local(axis).lower()
                               and 'concentrationriskbytype' not in local(axis).lower())]
            # Company-wide/aggregate percentages have no customer member and are omitted.
            if not customer_dims: continue
            p=ctx['period']; end=p.get('enddate') or p.get('instant')
            if not end: continue
            try: endd=date.fromisoformat(end)
            except ValueError: continue
            if not START<=endd<=DEV_END: continue
            member=customer_dims[0][1]
            active=member_for(cik,endd)
            if not active: continue
            pct=number_to_percent(value,scale,sign)
            if pct is None: continue
            customer_name,customer_ticker,member_status=resolve_member(member,bycik,aliases)
            tier=('holdout' if endd<=HOLDOUT_END and fd<=HOLDOUT_END else
                  'development' if DEV_START<=endd<=DEV_END and fd<=DEV_END else 'transition')
            local_rows.append({'period_class':tier,'supplier_ticker':active[0],'supplier_cik':cik,
                               'customer_member_name':member,'customer_display_name':customer_name,
                               'customer_ticker':customer_ticker,'member_status':member_status,
                               'percentage':format(pct,'f'),'period_start':p.get('startdate',''),
                               'period_end':end,'filing_date':r['filingDate'],'form':r['form'],
                               'accession_number':r['accessionNumber'],'source_url':url})
        if local_rows: docs_with_candidate+=1; rows.extend(local_rows)
        if i%25==0 or i==len(filings): print(f'FILINGS {i}/{len(filings)} docs_with_facts={docs_with_candidate} rows={len(rows)}',flush=True)
    # Preserve filing-date versions; exact duplicate facts in a filing are collapsed.
    dedup={}
    for r in rows:
        key=tuple(r[k] for k in ('period_class','supplier_cik','customer_member_name','percentage','period_start','period_end','filing_date','accession_number'))
        dedup[key]=r
    rows=sorted(dedup.values(),key=lambda r:(r['period_end'],r['supplier_cik'],r['customer_member_name'],r['filing_date']))
    columns=['period_class','supplier_ticker','supplier_cik','customer_member_name','customer_display_name','customer_ticker','member_status','percentage','period_start','period_end','filing_date','form','accession_number','source_url']
    path=OUT/'xbrl_customer_links.csv'
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(rows)
    coverage={}
    for r in rows:
        d=coverage.setdefault(r['period_class'],{'rows':0,'named_rows':0,'named_tickers':set(),'named_members':set(),'issuers':set()})
        d['rows']+=1;d['issuers'].add(r['supplier_cik'])
        if r['member_status']=='named_listed':
            d['named_rows']+=1;d['named_tickers'].add(r['customer_ticker']);d['named_members'].add(r['customer_member_name'])
    print('SUMMARY',scanned,'filings',len(rows),'facts',coverage,flush=True)
    if errors: print('ERRORS',len(errors),errors[:10],flush=True)

if __name__=='__main__': main()
