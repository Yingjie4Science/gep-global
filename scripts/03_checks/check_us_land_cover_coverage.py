"""Check actual local LULC support on native population cells for each US GUPPD unit.

No national benefit is calculated. City counts may overlap; do not sum population
rows as a country total. Reads only verified tiles; partial acquisitions are marked.
"""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd,rasterio
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds,Window
from rasterio.warp import reproject,Resampling

def main():
 p=argparse.ArgumentParser();p.add_argument('data_root',type=Path);p.add_argument('output',type=Path);a=p.parse_args();root=a.data_root;a.output.mkdir(parents=True,exist_ok=True)
 cities=gpd.read_file(root/'processed/guppd_us_contiguous.gpkg');plan=json.loads((root/'manifests/glc_us_download_plan.json').read_text())['tiles'];tiles=[]
 for r in plan:
  status=root/'manifests/glc_us_tiles'/(Path(r['member']).name+'.json')
  if status.exists() and json.loads(status.read_text()).get('status')=='verified':tiles.append((r['bounds'],root/'processed/lulc_2019_us'/Path(r['member']).name.replace('20002022','2019')))
 records=[]
 with rasterio.open(root/'raw/worldpop/usa_pop_2019_CN_100m_R2025A_v1.tif') as population:
  for i,city in cities.iterrows():
   xmin,ymin,xmax,ymax=city.geometry.bounds;w=from_bounds(xmin,ymin,xmax,ymax,population.transform);x0=max(0,math.floor(w.col_off));y0=max(0,math.floor(w.row_off));win=Window(x0,y0,math.ceil(w.col_off+w.width)-x0,math.ceil(w.row_off+w.height)-y0)
   pop=population.read(1,window=win);transform=population.window_transform(win);inside=geometry_mask([city.geometry],out_shape=pop.shape,transform=transform,invert=True,all_touched=False);valid=inside&(pop>=0)&np.isfinite(pop);land=np.zeros(pop.shape,dtype='uint16');used=[]
   for bounds,path in tiles:
    if bounds[0]>=xmax or bounds[2]<=xmin or bounds[1]>=ymax or bounds[3]<=ymin:continue
    with rasterio.open(path) as src:reproject(source=rasterio.band(src,1),destination=land,src_transform=src.transform,src_crs=src.crs,src_nodata=0,dst_transform=transform,dst_crs=population.crs,dst_nodata=0,init_dest_nodata=False,resampling=Resampling.nearest)
    used.append(path.name)
   supported=valid&~np.isin(land,[0,250]);total=float(pop[valid].sum(dtype='float64'));missing=float(pop[valid&~supported].sum(dtype='float64'))
   records.append({'city_id':str(city.id),'city_name':str(city.CIESIN_NAME),'population_valid_cells':int(valid.sum()),'land_cover_supported_cells':int(supported.sum()),'population_total':total,'population_missing_land_cover':missing,'population_support_fraction':1-missing/total if total else None,'verified_tiles_used':'|'.join(used),'observed_classes':'|'.join(map(str,np.unique(land[supported]))),'status':'supported' if int(valid.sum())==int(supported.sum()) else 'missing_support'})
   if (i+1)%200==0:print('Checked',i+1,'cities',flush=True)
 pd.DataFrame(records).to_csv(a.output/'city_land_cover_coverage.csv',index=False)
 summary={'city_count':len(records),'verified_tiles':len(tiles),'planned_tiles':len(plan),'cities_with_missing_support':sum(r['status']!='supported' for r in records),'scope':'Each original GUPPD polygon on native WorldPop centre grid; city populations must not be summed due overlaps. Hawaii excluded. Missing support includes missing acquisition and source fill.','source_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 (a.output/'coverage_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
