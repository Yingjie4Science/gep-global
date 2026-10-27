#!/usr/bin/env python3
"""Convert supplied 2018 international-dollar costs to 2019 market USD.
Source: Christensen et al. 2020, doi:10.1017/S204579602000075X.
Their original OECD 2018 PPP vintage is unavailable here. Current WDI GDP PPP
is a labelled approximation for non-US rows, not an exact reconstruction.
No provisional row is automatically promoted to the model cost workbook.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
from datetime import datetime,timezone
ISO=dict(zip('Australia|Austria|Belgium|Bulgaria|Cyprus|Czech Republic|Denmark|Estonia|Finland|France|Germany|Greece|Hungary|Iceland|Ireland|Italy|Latvia|Lithuania|Luxembourg|Malta|Netherlands|Norway|Poland|Portugal|Romania|Slovakia|Slovenia|Spain|Sweden|Switzerland|United Kingdom|United States'.split('|'),'AUS AUT BEL BGR CYP CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ITA LVA LTU LUX MLT NLD NOR POL PRT ROU SVK SVN ESP SWE CHE GBR USA'.split()))
def convert(value,ppp,cpi18,cpi19,fx19):
    if not all(math.isfinite(x) and x>0 for x in [ppp,cpi18,cpi19,fx19]) or not math.isfinite(value) or value<0: raise ValueError('Invalid conversion input')
    return value*ppp*(cpi19/cpi18)/fx19

def main():
    ap=argparse.ArgumentParser();ap.add_argument('data_root',type=Path);args=ap.parse_args();root=args.data_root
    raw=root/'raw/cost_conversion'; source=root/'processed/data_cost_mental_health.csv'
    series={};snapshots={}
    for ind in ['PA.NUS.PPP','PA.NUS.FCRF','FP.CPI.TOTL']:
        path=raw/(ind+'.json');data=json.loads(path.read_text())
        if len(data)!=2 or data[0]['pages']!=1:raise ValueError('Incomplete WDI response')
        series[ind]={(r['countryiso3code'],r['date']):r['value'] for r in data[1]}
        snapshots[ind]=dict(url=f'https://api.worldbank.org/v2/country/all/indicator/{ind}?date=2018:2019&format=json&per_page=20000',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),lastupdated=data[0]['lastupdated'])
    rows=list(csv.DictReader(source.open()));out=[]
    if len({r['country'] for r in rows})!=len(rows):raise ValueError('Duplicate countries')
    for r in rows:
        if r['year']!='2018':raise ValueError('Source price year must be 2018')
        iso=ISO.get(r['country'],'');row=dict(r,iso3=iso,cost_per_case_2019_usd='',currency='USD',price_year=2019,ppp_adjusted=False,conversion_status='',model_ready=False,source_doi='10.1017/S204579602000075X')
        for name,ind,year in [('ppp_lcu_per_intl_dollar_2018','PA.NUS.PPP','2018'),('cpi_2018','FP.CPI.TOTL','2018'),('cpi_2019','FP.CPI.TOTL','2019'),('fx_lcu_per_usd_2019','PA.NUS.FCRF','2019')]:row[name]=series[ind].get((iso,year))
        if not iso:row['conversion_status']='blocked_aggregate_no_single_currency'
        elif iso=='BGR':row['conversion_status']='blocked_PPP_and_FX_currency_unit_reconciliation'
        elif any(row[k] is None for k in ['ppp_lcu_per_intl_dollar_2018','cpi_2018','cpi_2019','fx_lcu_per_usd_2019']):row['conversion_status']='blocked_missing_factor'
        else:
            v=convert(float(r['Price_USD_PPP']),row['ppp_lcu_per_intl_dollar_2018'],row['cpi_2018'],row['cpi_2019'],row['fx_lcu_per_usd_2019'])
            row['cost_per_case_2019_usd']=v
            row['conversion_status']='US_reference_currency_conversion' if iso=='USA' else 'provisional_revised_WDI_GDP_PPP'
            # Algebraic round trip is a numerical check, not provenance validation.
            reverse=v*row['fx_lcu_per_usd_2019']/(row['cpi_2019']/row['cpi_2018'])/row['ppp_lcu_per_intl_dollar_2018']
            if not math.isclose(reverse,float(r['Price_USD_PPP']),rel_tol=1e-12):raise ValueError('Round-trip failure')
        out.append(row)
    target=root/'processed/data_cost_mental_health_2019_usd_conversion_audit.csv'
    with target.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    us=next(r for r in out if r['iso3']=='USA')
    with (root/'processed/data_cost_mental_health_US_2019_USD.csv').open('w',newline='') as f:
        fields=['country','cost_per_case','currency','price_year','ppp_adjusted','dx_broad','cost_broad_type','cost_unit','conversion_status','model_ready']
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerow(dict(us,cost_per_case=us['cost_per_case_2019_usd']))
    manifest=dict(created_at=datetime.now(timezone.utc).isoformat(),formula='cost_2018_intl_dollars * PPP_2018_LCU_per_intl_dollar * CPI_2019 / CPI_2018 / FX_2019_LCU_per_USD',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),factor_snapshots=snapshots,source_rows=len(rows),converted_rows=sum(r['cost_per_case_2019_usd']!='' for r in out),model_ready_rows=0,limitations=['Non-US PPP factors are revised WDI GDP factors, not recovered February 2020 OECD vintage.','Europe aggregate cannot be converted using a single currency factor.','Bulgaria held pending currency-unit reconciliation.','Mood-disorder societal cost is not depression-specific treatment cost.'])
    (root/'manifests/cost_conversion_2019_usd.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(US_2019_USD=us['cost_per_case_2019_usd'],converted_rows=manifest['converted_rows'],blocked=[r['country'] for r in out if r['cost_per_case_2019_usd']=='']),indent=2))
if __name__=='__main__':main()
