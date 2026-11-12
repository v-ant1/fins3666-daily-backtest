from pathlib import Path
import io
import requests
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'etf'
AS_OF='2026-11-11'
WIKI='https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
GICS='https://www.spglobal.com/spdji/en/index-family/equity/us-equity/sp-sectors/'
SSGA='https://www.ssga.com/us/en/individual/capabilities/equities/sector-investing/select-sector-etfs'
SECTOR_ETF={
 'Communication Services':'XLC','Consumer Discretionary':'XLY','Consumer Staples':'XLP',
 'Energy':'XLE','Financials':'XLF','Health Care':'XLV','Industrials':'XLI',
 'Information Technology':'XLK','Materials':'XLB','Real Estate':'XLRE','Utilities':'XLU'}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    response=requests.get(WIKI,headers={'User-Agent':'FINS3666 Data Research project (research@example.edu)'},timeout=45)
    response.raise_for_status()
    current=pd.read_html(io.StringIO(response.text),attrs={'id':'constituents'})[0]
    current=current.rename(columns={'Symbol':'ticker','Security':'company','GICS Sector':'gics_sector','CIK':'cik'})
    current['ticker']=current.ticker.astype(str).str.replace('.','-',regex=False)
    current['cik']=current.cik.astype(str).str.zfill(10)
    current['sector_spdr']=current.gics_sector.map(SECTOR_ETF)
    current['classification_asof']=AS_OF
    current['classification_source']=WIKI
    # Dated S&P roster intervals; current GICS labels are explicitly as-of only.
    sp=pd.read_csv(ROOT/'sp500_pit_roster.csv',dtype={'ticker':str,'sp100_member_at_2026_10_30':str})
    sp['ticker']=sp.ticker.str.replace('.','-',regex=False)
    sp=sp.merge(current[['ticker','gics_sector','sector_spdr','classification_asof','classification_source']],on='ticker',how='left')
    sp.insert(0,'universe','S&P500')
    sp['sic']='';sp['sic2']='';sp['sic3']='';sp['sic_effective_date']='';sp['sic_source_url']=''
    # Dated Dow SIC membership rows supplied by the research data build.
    dow=pd.read_csv(ROOT.parent/'r6_C1'/'dow_sic_membership.csv',dtype={'ticker':str,'cik':str,'sic':str,'sic2':str,'sic3':str})
    dow=dow[(dow.effective_to_exclusive>'2020-06-01')&(dow.effective_from<'2026-10-31')].copy()
    dow['ticker']=dow.ticker.str.replace('.','-',regex=False)
    dow=dow.rename(columns={'source_url':'sic_source_url'})
    dow_sic_src=dow[['ticker','cik','sic','effective_from','effective_to_exclusive','sic_source_url']].copy()
    dow=dow.merge(current[['ticker','gics_sector','sector_spdr','classification_asof','classification_source','company']],on='ticker',how='left')
    dow.insert(0,'universe','Dow30')
    dow['sp100_member_at_2026_10_30']=''
    dow['start_source']='r6_C1/dow_sic_membership.csv'
    dow['source_refs']='SIC membership windows copied; GICS classification current snapshot'
    dow['sic_effective_date']=dow.effective_from
    cols=['universe','ticker','company','effective_from','effective_to_exclusive','sp100_member_at_2026_10_30','gics_sector','sector_spdr','classification_asof','classification_source','sic','sic2','sic3','sic_effective_date','sic_source_url','start_source','source_refs']
    sp['company']=sp.company.fillna('')
    sp=sp[cols]
    dow=dow[cols]
    pd.concat([sp,dow],ignore_index=True).sort_values(['universe','ticker','effective_from']).to_csv(OUT/'stock_sector_sic_mapping.csv',index=False)
    pd.DataFrame([{'gics_sector':sector,'sector_spdr':symbol,'gics_standard_source':GICS,'sector_fund_source':SSGA,'effective_from':AS_OF,'effective_to_exclusive':'','notes':'Current sector-to-fund mapping; no historical sector-fund classification history supplied.'} for sector,symbol in SECTOR_ETF.items()]).to_csv(OUT/'sector_to_spdr_reference.csv',index=False)
    # Join SIC filings/membership windows by issuer to current GICS snapshot; SIC!=GICS.
    sp_sic=pd.read_csv(ROOT/'sp500_sic_panel.csv',dtype={'ticker':str,'cik':str,'sic':str})
    sp_sic['universe']='S&P500';sp_sic['effective_from']=sp_sic['effective_date'];sp_sic['effective_to_exclusive']='';sp_sic['sic_source_url']=sp_sic['source_url']
    sp_sic=sp_sic[['universe','ticker','cik','sic','effective_from','effective_to_exclusive','sic_source_url']]
    dow_sic=dow_sic_src.copy();dow_sic['universe']='Dow30'
    sic=pd.concat([sp_sic,dow_sic],ignore_index=True)
    sic['ticker']=sic.ticker.astype(str).str.replace('.','-',regex=False)
    sic=sic.merge(current[['ticker','gics_sector']],on='ticker',how='left')
    sic['sector_spdr']=sic.gics_sector.map(SECTOR_ETF)
    sic['gics_source']=WIKI;sic['gics_classification_asof']=AS_OF
    sic.to_csv(OUT/'sector_sic_mapping.csv',index=False)
    print('Wrote sector reference (11 rows), stock intervals, and SIC association table.')

if __name__=='__main__': main()

