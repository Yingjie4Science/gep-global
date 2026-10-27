"""Bounded real-data pilot using the project's existing case/aggregation functions.

The lightweight lookup below is identical to the production lookup array but
avoids starting eight Dask workers for a tiny window. No national claim is made.
"""
import argparse,json,hashlib,sys,platform,subprocess
from pathlib import Path
import numpy as np,pandas as pd,rasterio
from rasterio.features import geometry_mask
import geopandas as gpd
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
import urban_mental_health_functions as model
from prevalence_inputs import resolve_country_rates

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('pilot',type=Path);ap.add_argument('--lookup',type=Path,required=True);ap.add_argument('--effects',type=Path,required=True);ap.add_argument('--prevalence',type=Path,required=True);ap.add_argument('--crosswalk',type=Path,required=True);ap.add_argument('--cost',type=Path);ap.add_argument('--output',type=Path);ap.add_argument('--land-cover',type=Path);args=ap.parse_args();d=args.pilot;o=args.output or d/'local_outputs'
 if o.exists() and any(o.iterdir()):raise FileExistsError('Choose a fresh --output directory; cached stages are not reused')
 o.mkdir(exist_ok=True)
 table=pd.read_csv(args.lookup);table=table.dropna(subset=['lc_ndvi']);assert not table.lc_code.duplicated().any();lookup=dict(zip(table.lc_code.astype(int),table.lc_ndvi.astype(float)))
 assert all(-1<=v<=1 for v in lookup.values())
 land_path=args.land_cover or d/'land_cover_2019.tif'
 with rasterio.open(land_path) as r:
  lc=r.read(1);profile=r.profile.copy();ndvi=np.full(lc.shape,np.nan,dtype=np.float32)
  for code,val in lookup.items():ndvi[lc==code]=val
  ndvi[np.isin(lc,[0,250])]=np.nan
  profile.update(dtype='float32',nodata=np.nan)
  with rasterio.open(o/'ndvi_2019.tif','w',**profile) as out:out.write(ndvi,1)
 with rasterio.open(d/'population_2019.tif') as r:pop=r.read(1);transform=r.transform
 cities=gpd.read_file(d/'city.gpkg');inside=geometry_mask(cities.geometry,out_shape=pop.shape,transform=transform,all_touched=False,invert=True)
 valid=inside & np.isfinite(pop) & (pop>=0);supported=valid & np.isfinite(ndvi)
 missing_codes=np.unique(lc[valid & ~supported]).tolist()
 if missing_codes:raise ValueError('Population on unrepresented lookup classes: '+str(missing_codes))
 model.create_no_vegetation_ndvi_scenario(o/'ndvi_2019.tif',o/'ndvi_no_vegetation.tif')
 model.calculate_delta_raster(o/'ndvi_2019.tif',o/'ndvi_no_vegetation.tif',o/'delta_ndvi.tif',lambda a,b:a-b)
 e=model.load_depression_effect_sizes(args.effects);rate=resolve_country_rates(['United States'],args.prevalence,args.crosswalk)['United States'];p0=0.115
 summary={'city_id':str(cities.iloc[0]['id']),'city_name':str(cities.iloc[0]['CIESIN_NAME']),'population_total':float(pop[valid].sum(dtype='float64')),'population_modelled':float(pop[supported].sum(dtype='float64')),'observed_cases':float(pop[supported].sum(dtype='float64'))*rate,'prevalence':rate,'p0':p0,'lookup_scope':'Selected GUPPD urban area plus 5 km UTM buffer; city-specific technical pilot proxy','interval_scope':'conditional 95% effect-size limits only','scientific_status':'technical pilot; not causal or locally validated'}
 for name,odds in [('additional_cases',e['effect_size']),('additional_cases_lower',e['ci_upper']),('additional_cases_upper',e['ci_lower'])]:
  raster=o/(name+'_factor.tif');csv=o/(name+'_city.csv')
  model.calculate_preventable_cases(o/'delta_ndvi.tif',d/'population_2019.tif',args.effects,1,p0,raster,odds_ratio=odds,overwrite=True)
  model.aggregate_preventable_cases_by_region(str(raster),str(d/'city.gpkg'),str(csv),country_prevalence_table_path=args.prevalence,country_crosswalk_path=args.crosswalk)
  result=float(pd.read_csv(csv).total_preventable_cases.sum());summary[name]=result
  # Independent algebra using direct OR expression and double precision.
  rr=odds/(1-p0+p0*odds);independent=float(np.sum(pop[supported].astype(float)*rate*(np.exp(-10*np.maximum(ndvi[supported].astype(float),0)*np.log(rr))-1)))
  if not np.isclose(result,independent,rtol=2e-6,atol=1e-6):raise AssertionError((name,result,independent))
  summary[name+'_independent']=independent
 if args.cost:
  cost=pd.read_csv(args.cost);assert len(cost)==1;cost=cost.iloc[0]
  assert cost['currency']=='USD' and int(cost['price_year'])==2019 and not bool(cost['ppp_adjusted'])
  # Monetary sensitivity is separately labelled; never override model_ready=False.
  price=float(cost['cost_per_case'])
  summary.update(societal_cost_proxy_2019_usd=price,monetary_status='exploratory mood-disorder societal-cost proxy; not depression treatment cost')
  for name in ['additional_cases','additional_cases_lower','additional_cases_upper']:summary[name+'_societal_value_proxy_2019_usd']=summary[name]*price
 pd.DataFrame([summary]).to_csv(o/'pilot_summary.csv',index=False)
 sources=[args.lookup,args.effects,args.prevalence,args.crosswalk,d/'population_2019.tif',land_path,d/'city.gpkg']
 if args.cost:sources.append(args.cost)
 report={'summary':summary,'inputs':{str(x):sha(x) for x in sources},'python':platform.python_version(),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parents[2],text=True).strip(),'source_hashes':{n:sha(Path(__file__).resolve().parents[2]/n) for n in ['src/urban_mental_health_functions.py','src/effect_size_uncertainty.py','scripts/02_models/run_local_pilot.py']},'outputs':{x.name:sha(x) for x in o.iterdir() if x.suffix in ['.tif','.csv']}}
 (o/'run_record.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
