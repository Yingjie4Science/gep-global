"""Resume four real-city, matched-input local/EE comparisons without overwriting runs.

Requires the reviewed invest-gee JS module, authenticated EE Python runtime,
local model Python runtime, and verified official land-cover tiles. The caller
supplies all paths; no credentials or signed download URLs are retained.
"""
import argparse,csv,hashlib,json,os,subprocess,time,math,shutil
from pathlib import Path
import ee,numpy as np,requests,rasterio,geopandas as gpd,pandas as pd
from rasterio.features import geometry_mask
from rasterio.windows import Window

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(command):subprocess.run([str(x) for x in command],check=True)
def download(image,path,qc,bands):
 if path.exists():return
 height,width=qc['pilot_shape'];tr=qc['pilot_transform'];temp=path.with_suffix('.incomplete.tif')
 profile=dict(driver='GTiff',height=height,width=width,count=len(bands),dtype='float64',crs='EPSG:4326',transform=rasterio.Affine(*tr),nodata=-99999,compress='deflate')
 with rasterio.open(temp,'w',**profile) as dst:
  for row in range(0,height,256):
   h=min(256,height-row);parttr=list(tr);parttr[5]+=row*tr[4]
   url=image.select(bands).unmask(-99999).toDouble().getDownloadURL({'crs':'EPSG:4326','crs_transform':parttr,'dimensions':[width,h],'format':'GEO_TIFF'})
   response=requests.get(url,timeout=240);response.raise_for_status()
   with rasterio.io.MemoryFile(response.content) as mem:
    with mem.open() as src:dst.write(src.read(),window=Window(0,row,width,h))
 temp.replace(path)
def prefetch(c,a):
 d=a.data_root/'pilots/expanded_2019_v1'/c['label'];out=d/'cloud_readback';out.mkdir(exist_ok=True)
 with rasterio.open(a.data_root/'raw/worldpop/usa_pop_2019_CN_100m_R2025A_v1.tif') as src:
  win=rasterio.windows.from_bounds(*c['bounds'],transform=src.transform);x0=max(0,math.floor(win.col_off)-2);y0=max(0,math.floor(win.row_off)-2);x1=math.ceil(win.col_off+win.width)+2;y1=math.ceil(win.row_off+win.height)+2
  qc={'pilot_shape':[y1-y0,x1-x0],'pilot_transform':list(src.window_transform(Window(x0,y0,x1-x0,y1-y0)))[:6]}
 tr=qc['pilot_transform'];h,w=qc['pilot_shape'];region=ee.Geometry.Rectangle([tr[2],tr[5]+h*tr[4],tr[2]+w*tr[0],tr[5]],'EPSG:4326',False)
 population=ee.Image('projects/sat-io/open-datasets/WORLDPOP/pop/USA_POP_2019_CN_100M_R2025A_V1').select('population')
 land=ee.ImageCollection('projects/sat-io/open-datasets/GLC-FCS30D/annual').filterBounds(region).sort('system:index').select('b20').mosaic().rename('land_cover')
 download(population,out/'population_gee.tif',qc,['population']);download(land,out/'land_cover_gee.tif',qc,['land_cover'])
 (out/'grid.json').write_text(json.dumps(qc,indent=2)+'\n');print('GEE source readback complete',c['label'],flush=True)

def process(c,a):
 d=a.data_root/'pilots/expanded_2019_v1'/c['label'];inputs=d/'inputs';result=d/'comparison.json'
 if result.exists():return True
 plan=json.loads((a.data_root/'manifests/glc_us_download_plan.json').read_text())['tiles'];needed=[r for r in plan if Path(r['member']).name in c['required_tiles']]
 if any(not (a.data_root/'manifests/glc_us_tiles'/(Path(r['member']).name+'.json')).exists() or json.loads((a.data_root/'manifests/glc_us_tiles'/(Path(r['member']).name+'.json')).read_text()).get('status')!='verified' for r in needed):return False
 lookup=d/'lookup/lookup_candidate.csv'
 if not lookup.exists():return False
 print('Running expanded test',c['label'],flush=True)
 if not (inputs/'input_qc.json').exists():
  if len(needed)!=1:raise ValueError('This bounded test requires one source tile; add a documented mosaic for multi-tile cities')
  lc=a.data_root/'processed/lulc_2019_us'/Path(needed[0]['member']).name.replace('20002022','2019')
  run([a.local_python,a.repo/'scripts/prepare_local_pilot.py',a.data_root,'--city-id',c['city_id'],'--land-cover',lc,'--output',inputs])
 qc=json.loads((inputs/'input_qc.json').read_text());city=gpd.read_file(inputs/'city.gpkg')
 if (d/'cloud_readback/grid.json').exists():
  grid=json.loads((d/'cloud_readback/grid.json').read_text());assert grid['pilot_shape']==qc['pilot_shape'] and grid['pilot_transform']==qc['pilot_transform']
  for name in ['population_gee.tif','land_cover_gee.tif']:
   if not (inputs/name).exists():shutil.copy2(d/'cloud_readback'/name,inputs/name)
 tr=qc['pilot_transform'];h,w=qc['pilot_shape'];region=ee.Geometry.Rectangle([tr[2],tr[5]+h*tr[4],tr[2]+w*tr[0],tr[5]],'EPSG:4326',False)
 population=ee.Image('projects/sat-io/open-datasets/WORLDPOP/pop/USA_POP_2019_CN_100M_R2025A_V1').select('population')
 land=ee.ImageCollection('projects/sat-io/open-datasets/GLC-FCS30D/annual').filterBounds(region).sort('system:index').select('b20').mosaic().rename('land_cover')
 download(population,inputs/'population_gee.tif',qc,['population']);download(land,inputs/'land_cover_gee.tif',qc,['land_cover'])
 common=['--lookup',lookup,'--effects',a.data_root/'processed/effect_size.xlsx','--prevalence',a.prevalence,'--crosswalk',a.repo/'config/us_country_crosswalk.csv','--cost',a.data_root/'processed/data_cost_mental_health_US_2019_USD.csv']
 for output,lc in [('local_outputs',None),('matched_cloud_outputs',inputs/'land_cover_gee.tif')]:
  if not (d/output/'run_record.json').exists():
   command=[a.local_python,a.repo/'scripts/run_local_pilot.py',inputs,*common,'--output',d/output]
   if lc:command+=['--land-cover',lc]
   run(command)
 valid=[{'lcCode':int(r['lc_code']),'ndvi':float(r['lc_ndvi'])} for r in csv.DictReader(lookup.open()) if r['lc_ndvi']]
 config={'populationAsset':'projects/sat-io/open-datasets/WORLDPOP/pop/USA_POP_2019_CN_100M_R2025A_V1','urbanAsset':'projects/natcap-gep/assets/umh_guppd_us_excluding_hawaii_v1','urbanIds':[c['city_id']],'model':{'year':2019,'endpoint':'all-age depressive-disorders case-equivalent contrast; expanded technical test','p0':0.115,'prevalence':0.0424332878,'effect':{'oddsRatio':0.931,'lower':0.887,'upper':0.977},'lookup':valid,'sources':{'population':'Supplied WorldPop constrained R2025A2019','landCover':'GLC community b20; compare separately with official Zenodo','lookup':'City-specific local UTM5km buffer, SHA256 '+sha(lookup),'prevalence':'GBD2023/2019 all-age USA','effect':'Liu2023 OR per0.1NDVI; supplied workbook','p0':'Transported health-record proxy0.115; not country prevalence'}}}
 (d/'cloud_config.json').write_text(json.dumps(config,indent=2)+'\n');alg=d/'ee_algorithms.json'
 if not alg.exists():alg.write_text(json.dumps(ee.data.getAlgorithms()))
 run(['node',a.gee_repo/'urban_mental_health/serialize_real_pilot.cjs',alg,d/'cloud_config.json',d/'cloud_graph.json'])
 graph=json.loads((d/'cloud_graph.json').read_text());keys=['additional_cases','additional_cases_lower','additional_cases_upper'];image=ee.Image(ee.deserializer.fromJSON(graph['image']))
 download(image,d/'cloud_cases.tif',qc,keys)
 with rasterio.open(inputs/'population_2019.tif') as src:pop=src.read(1);inside=geometry_mask(city.geometry,out_shape=pop.shape,transform=src.transform,invert=True,all_touched=False)
 with rasterio.open(inputs/'land_cover_2019.tif') as src:lc=src.read(1)
 with rasterio.open(inputs/'land_cover_gee.tif') as src:glc=src.read(1)
 with rasterio.open(inputs/'population_gee.tif') as src:gp=src.read(1)
 validpop=inside&(pop>=0)&np.isfinite(pop);vl=validpop&~np.isin(lc,[0,250]);vg=validpop&~np.isin(glc,[-99999,0,250]);both=vl&vg;different=both&(lc!=glc)
 assert np.array_equal(pop[validpop],gp[validpop]),'Population mismatch'
 local=pd.read_csv(d/'local_outputs/pilot_summary.csv').iloc[0];bridge=pd.read_csv(d/'matched_cloud_outputs/pilot_summary.csv').iloc[0];comparisons={}
 with rasterio.open(d/'cloud_cases.tif') as src:
  for i,k in enumerate(keys):
   cloud=src.read(i+1)
   with rasterio.open(d/'matched_cloud_outputs'/(k+'_factor.tif')) as x:py=x.read(1).astype(float)*float(bridge.prevalence)
   mask=inside&np.isfinite(py);cmask=inside&(cloud!=-99999)&np.isfinite(cloud)
   assert np.array_equal(mask,cmask),(k,'support mismatch')
   assert np.allclose(py[mask],cloud[mask],rtol=2e-6,atol=1e-7),(k,'numeric mismatch')
   comparisons[k]={'passed':True,'cells':int(mask.sum()),'max_absolute_cell_difference':float(np.max(np.abs(py[mask]-cloud[mask]))),'local_zenodo_total':float(local[k]),'matched_local_total':float(bridge[k]),'gee_cell_sum':float(cloud[mask].sum(dtype='float64'))}
 classes=np.unique(np.stack([lc[both],glc[both]],axis=1),axis=0,return_counts=True)
 pd.DataFrame({'local_class':classes[0][:,0],'gee_class':classes[0][:,1],'cells':classes[1]}).to_csv(d/'land_cover_confusion.csv',index=False)
 report={'city':c,'scope':'Native population-grid complete city; identical-input implementation check, not epidemiological validation. GUPPD feature may be only part of named settlement.','population_cells':int(validpop.sum()),'population_total':float(pop[validpop].sum(dtype='float64')),'population_readback_exact':True,'source_comparison':{'both_valid_cells':int(both.sum()),'different_cells':int(different.sum()),'different_fraction':float(different.sum()/both.sum()),'population_on_different_classes':float(pop[different].sum(dtype='float64')),'support_masks_equal':bool(np.array_equal(vl,vg)),'point_case_percent_difference':float(100*(float(local.additional_cases)/float(bridge.additional_cases)-1))},'outputs':comparisons,'lookup_sha256':sha(lookup),'cloud_model_sha256':sha(a.gee_repo/'urban_mental_health/model.js'),'conditional_uncertainty':'Effect-size95%CI only','cost_status':'Exploratory2019USD societal-cost proxy; nonPPP; not treatment savings'}
 regional=ee.deserializer.fromJSON(graph['summary']).getInfo();(d/'cloud_regional_summary.json').write_text(json.dumps(regional,indent=2)+'\n');rr=regional['features'][0]['properties']
 report['regional_reconciliation']={'gee_population_cells':rr.get('population_valid_cells'),'local_population_cells':int(validpop.sum()),'population_difference':rr['population_total']-report['population_total'],'case_difference_from_matched_local':rr['additional_cases']-float(bridge.additional_cases),'same_cell_count':rr.get('population_valid_cells')==int(validpop.sum()),'interpretation':'Cellwise formulas and geographic membership are separate checks; nonzero membership differences remain a finding, not a passed exact regional parity check.'}
 report['artifact_sha256']={str(p.relative_to(d)):sha(p) for p in [inputs/'population_2019.tif',inputs/'population_gee.tif',inputs/'land_cover_2019.tif',inputs/'land_cover_gee.tif',d/'cloud_cases.tif',d/'cloud_config.json',d/'cloud_graph.json']}
 report['land_cover_asset_ids']=ee.ImageCollection('projects/sat-io/open-datasets/GLC-FCS30D/annual').filterBounds(region).sort('system:index').aggregate_array('system:id').getInfo()
 report['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.repo,text=True).strip()
 result.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True);return True

def main():
 p=argparse.ArgumentParser();p.add_argument('data_root',type=Path);p.add_argument('--repo',type=Path,required=True);p.add_argument('--gee-repo',type=Path,required=True);p.add_argument('--local-python',type=Path,required=True);p.add_argument('--prevalence',type=Path,required=True);p.add_argument('--wait',action='store_true');p.add_argument('--prefetch-only',action='store_true');a=p.parse_args();ee.Initialize(project='natcap-gep')
 root=a.data_root/'pilots/expanded_2019_v1';root.mkdir(parents=True,exist_ok=True)
 plan_path=root/'test_plan.json'
 if not plan_path.exists():
  boundaries=gpd.read_file(a.data_root/'processed/guppd_us_excluding_hawaii.gpkg');tiles=json.loads((a.data_root/'manifests/glc_us_download_plan.json').read_text())['tiles'];cities=[]
  for label,id in {'tucson':'30_12305','portland_maine':'30_12572','anchorage':'23_87444','new_york':'30_12545'}.items():
   d=root/label;d.mkdir(exist_ok=True);city=boundaries[boundaries.id==id].copy();assert len(city)==1;city.to_file(d/'city.geojson',driver='GeoJSON')
   buffer=city.to_crs(city.estimate_utm_crs());buffer.geometry=buffer.buffer(5000);buffer.to_crs(4326).to_file(d/'lookup_aoi.geojson',driver='GeoJSON')
   xmin,ymin,xmax,ymax=city.total_bounds;needed=[Path(t['member']).name for t in tiles if t['bounds'][0]<xmax and t['bounds'][2]>xmin and t['bounds'][1]<ymax and t['bounds'][3]>ymin]
   cities.append({'label':label,'city_id':id,'city_name':str(city.iloc[0].CIESIN_NAME),'bounds':list(city.total_bounds),'required_tiles':needed})
  plan_path.write_text(json.dumps({'selection_rationale':'Dry inland, humid coastal, high latitude, and large cross-state urban areas. GUPPD features are not municipality definitions.','cities':cities},indent=2)+'\n')
 cities=json.loads(plan_path.read_text())['cities']
 for c in cities:
  d=root/c['label'];lookup=d/'lookup/lookup_candidate.csv'
  if not lookup.exists():
   alg=d/'ee_algorithms.json';alg.write_text(json.dumps(ee.data.getAlgorithms()))
   run(['node',a.gee_repo/'urban_mental_health/serialize_lookup.cjs',alg,d/'lookup_aoi.geojson',d/'lookup_graph.json',c['label']])
   run([os.sys.executable,a.gee_repo/'urban_mental_health/run_lookup.py',d/'lookup_graph.json',d/'lookup'])
 if a.prefetch_only:
  for c in cities:prefetch(c,a)
  return
 while True:
  pending=[]
  for c in cities:
   try:
    if not process(c,a):pending.append(c['label'])
   except Exception as e:
    (a.data_root/'pilots/expanded_2019_v1'/c['label']/'failure.json').write_text(json.dumps({'error':repr(e)},indent=2)+'\n');raise
  if not pending:break
  if pending!=locals().get('previous_pending'):print('Waiting for verified tiles/lookups:',pending,flush=True)
  previous_pending=pending
  if not a.wait:break
  time.sleep(30)
if __name__=='__main__':main()
