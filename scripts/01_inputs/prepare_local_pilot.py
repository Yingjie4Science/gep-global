from pathlib import Path
import argparse,json,hashlib,math,datetime
import numpy as np,geopandas as gpd,rasterio
from rasterio.windows import Window,from_bounds
from rasterio.warp import reproject,Resampling
from rasterio.features import geometry_mask

def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()

def main():
 a=argparse.ArgumentParser();a.add_argument('data_root',type=Path);a.add_argument('--city-id',default='23_87603');a.add_argument('--land-cover',type=Path,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args();d=args.data_root;o=args.output
 if o.exists() and any(o.iterdir()):raise FileExistsError('Use a fresh output directory; original pilot inputs are preserved')
 o.mkdir(parents=True,exist_ok=True)
 source=d/'raw/worldpop/usa_pop_2019_CN_100m_R2025A_v1.tif';boundary=d/'processed/guppd_us_excluding_hawaii.gpkg'
 g=gpd.read_file(boundary);city=g[g.id==args.city_id].copy();assert len(city)==1
 city=city[['id','SMOD_ID','country','iso3','CIESIN_NAME','geometry']]
 city.to_file(o/'city.gpkg',driver='GPKG');city.to_file(o/'city.geojson',driver='GeoJSON')
 buffer=city.to_crs(city.estimate_utm_crs());buffer.geometry=buffer.geometry.buffer(5000);buffer.to_crs(4326).to_file(o/'lookup_aoi.geojson',driver='GeoJSON')
 before=source.stat();samples=[]
 with rasterio.open(source) as r:
  assert r.count==1 and r.crs.to_epsg()==4326 and r.nodata==-99999
  # Check deterministic blocks across the stored file. This is not a full national scan.
  rng=np.random.default_rng(2019)
  indices=[(0,0),(r.height-1,r.width-1)]+[(int(rng.integers(r.height)),int(rng.integers(r.width))) for _ in range(20)]
  for y,x in indices:
   arr=r.read(1,window=Window(x,y,min(512,r.width-x),min(512,r.height-y)),masked=True)
   v=arr.compressed();assert np.isfinite(v).all() and (v>=0).all();samples.append({'row':y,'col':x,'valid_cells':int(v.size)})
  b=city.total_bounds;win=from_bounds(*b,transform=r.transform)
  x0=max(0,math.floor(win.col_off)-2);y0=max(0,math.floor(win.row_off)-2);x1=math.ceil(win.col_off+win.width)+2;y1=math.ceil(win.row_off+win.height)+2
  win=Window(x0,y0,x1-x0,y1-y0);pop=r.read(1,window=win);transform=r.window_transform(win);profile=r.profile.copy();profile.update(width=pop.shape[1],height=pop.shape[0],transform=transform)
  with rasterio.open(o/'population_2019.tif','w',**profile) as dst:dst.write(pop,1)
  metadata={'crs':str(r.crs),'transform':list(r.transform)[:6],'width':r.width,'height':r.height,'nodata':r.nodata,'dtype':r.dtypes[0],'bounds':list(r.bounds),'sampled_blocks':samples}
 with rasterio.open(args.land_cover) as r:
  land=np.full(pop.shape,0,dtype='uint16')
  reproject(source=rasterio.band(r,1),destination=land,src_transform=r.transform,src_crs=r.crs,src_nodata=r.nodata,dst_transform=transform,dst_crs=profile['crs'],dst_nodata=0,resampling=Resampling.nearest)
  land[np.isin(land,[0,250])]=0
 profile.update(dtype='uint16',nodata=0)
 with rasterio.open(o/'land_cover_2019.tif','w',**profile) as dst:dst.write(land,1)
 inside=geometry_mask(city.geometry,out_shape=pop.shape,transform=transform,invert=True,all_touched=False)
 valid=inside & np.isfinite(pop) & (pop>=0)
 report={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'city_id':args.city_id,'city_name':city.iloc[0].CIESIN_NAME,'source_population':str(source),'population_bytes':source.stat().st_size,'population_sha256':digest(source),'source_land_cover':str(args.land_cover),'land_cover_sha256':digest(args.land_cover),'boundary_sha256':digest(boundary),'source_metadata':metadata,'window':dict(col_off=x0,row_off=y0,width=int(win.width),height=int(win.height)),'pilot_transform':list(transform)[:6],'pilot_shape':list(pop.shape),'city_valid_population_cells':int(valid.sum()),'city_population_sum':float(pop[valid].sum(dtype='float64')),'city_land_cover_codes':np.unique(land[inside]).tolist(),'population_on_missing_lc':float(pop[valid & (land==0)].sum(dtype='float64')),'scope':'Full-file checksum; 22 read-window checks plus complete pilot-window read; not full nationwide data validation','lookup_aoi':'GUPPD urban polygon buffered 5 km in local UTM, returned to EPSG:4326; local technical-pilot proxy only'}
 assert source.stat().st_size==before.st_size and source.stat().st_mtime_ns==before.st_mtime_ns,'Population file changed during validation'
 report['output_sha256']={p.name:digest(p) for p in o.iterdir() if p.suffix in ['.tif','.geojson','.gpkg']}
 (o/'input_qc.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['city_id','city_name','city_population_sum','city_valid_population_cells','city_land_cover_codes','population_on_missing_lc','population_sha256']},indent=2))
if __name__=='__main__':main()
