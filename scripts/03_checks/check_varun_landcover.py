"""Compare Varun's global 2019 GLC raster with local 2019 Zenodo tiles on US model cells.

Usage: python scripts/03_checks/check_varun_landcover.py DATA_ROOT OUTPUT_JSON [--limit N]
"""
import argparse
import collections
import json
import math
from contextlib import ExitStack
from pathlib import Path

import fiona
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import Resampling, reproject
from rasterio.windows import Window, from_bounds
from shapely.geometry import shape


def window_for_geometry(dataset, geometry):
    w = from_bounds(*geometry.bounds, transform=dataset.transform)
    x0=max(0,math.floor(w.col_off)); y0=max(0,math.floor(w.row_off))
    x1=min(dataset.width,math.ceil(w.col_off+w.width));y1=min(dataset.height,math.ceil(w.row_off+w.height))
    return Window(x0,y0,x1-x0,y1-y0)

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('data_root',type=Path);p.add_argument('output_json',type=Path);p.add_argument('--limit',type=int)
a=p.parse_args();root=a.data_root
plan=json.loads((root/'manifests/glc_us_download_plan.json').read_text())['tiles']
tiles=[]
for item in plan:
    name=Path(item['member']).name.replace('20002022','2019')
    tiles.append((item['bounds'],root/'processed/lulc_2019_us'/name))
owner_path=root/'raw/collaborator/varun_2026-10/lulc_glc_fcs30d_2019.tif'
pop_path=root/'raw/worldpop/usa_pop_2019_CN_100m_R2025A_v1.tif'
poly_path=root/'processed/guppd_us_excluding_hawaii.gpkg'
result={'status':'source_comparison_on_active_us_urban_population_cells','scope':'Current 3312 non-Hawaii GUPPD polygons; 2019 WorldPop valid cell centres; nearest-neighbor resampling to population grid.','features_checked':0,'population_cells_checked':0,'population_sum_checked':0.0,'both_valid_cells':0,'both_valid_population':0.0,'same_class_cells':0,'same_class_population':0.0,'different_class_cells':0,'different_class_population':0.0,'owner_missing_local_valid_cells':0,'owner_missing_local_valid_population':0.0,'local_missing_owner_valid_cells':0,'local_missing_owner_valid_population':0.0,'both_missing_cells':0,'class_pair_cells':{},'class_pair_population':{},'first_differing_ids':[]}
pair_cells=collections.Counter();pair_population=collections.defaultdict(float)
with ExitStack() as stack:
    pop=stack.enter_context(rasterio.open(pop_path));owner=stack.enter_context(rasterio.open(owner_path))
    sources=[(bounds,stack.enter_context(rasterio.open(path))) for bounds,path in tiles]
    assert pop.crs==owner.crs
    with fiona.open(poly_path) as polygons:
        for f in polygons:
            if a.limit and result['features_checked']>=a.limit:break
            g=shape(f['geometry']);fid=f['properties']['id']
            win=window_for_geometry(pop,g);poparr=pop.read(1,window=win)
            transform=pop.window_transform(win)
            valid=geometry_mask([g],poparr.shape,transform,invert=True,all_touched=False)&np.isfinite(poparr)&(poparr!=pop.nodata)&(poparr>=0)
            local=np.zeros(poparr.shape,dtype='uint16')
            xmin,ymin,xmax,ymax=g.bounds
            for bounds,src in sources:
                if bounds[0]>=xmax or bounds[2]<=xmin or bounds[1]>=ymax or bounds[3]<=ymin:continue
                reproject(source=rasterio.band(src,1),destination=local,src_transform=src.transform,src_crs=src.crs,src_nodata=0,dst_transform=transform,dst_crs=pop.crs,dst_nodata=0,init_dest_nodata=False,resampling=Resampling.nearest)
            remote=np.full(poparr.shape,255,dtype='uint16')
            reproject(source=rasterio.band(owner,1),destination=remote,src_transform=owner.transform,src_crs=owner.crs,src_nodata=owner.nodata,dst_transform=transform,dst_crs=pop.crs,dst_nodata=255,init_dest_nodata=False,resampling=Resampling.nearest)
            lv=valid&~np.isin(local,[0,250,255]);rv=valid&~np.isin(remote,[0,250,255]);both=lv&rv
            same=both&(local==remote);different=both&(local!=remote)
            om=lv&~rv;lm=rv&~lv;bm=valid&~lv&~rv
            result['features_checked']+=1
            result['population_cells_checked']+=int(valid.sum());result['population_sum_checked']+=float(poparr[valid].sum(dtype='float64'))
            for key,mask in [('both_valid',both),('same_class',same),('different_class',different),('owner_missing_local_valid',om),('local_missing_owner_valid',lm),('both_missing',bm)]:
                result[key+'_cells']+=int(mask.sum())
                if key!='both_missing':result[key+'_population']+=float(poparr[mask].sum(dtype='float64'))
            if different.any():
                if len(result['first_differing_ids'])<20:result['first_differing_ids'].append(str(fid))
                values,pops=local[different],poparr[different]
                for code in np.unique(values):
                    for other in np.unique(remote[different&(local==code)]):
                        sub=different&(local==code)&(remote==other)
                        pair_cells[(int(code),int(other))]+=int(sub.sum())
                        pair_population[(int(code),int(other))]+=float(poparr[sub].sum(dtype='float64'))
            if result['features_checked']%500==0:print('checked',result['features_checked'],flush=True)
result['class_pair_cells']={f'{x}->{y}':n for (x,y),n in pair_cells.most_common(30)}
result['class_pair_population']={f'{x}->{y}':pair_population[(x,y)] for (x,y),n in pair_cells.most_common(30)}
result['fraction_different_among_both_valid_population']=result['different_class_population']/result['both_valid_population'] if result['both_valid_population'] else None
result['interpretation']='Class differences identify source/preprocessing mismatch only; lookup and health equation are not varied in this audit.'
a.output_json.parent.mkdir(parents=True,exist_ok=True);a.output_json.write_text(json.dumps(result,indent=2)+'\n')
print({k:result[k] for k in ['features_checked','population_cells_checked','both_valid_cells','different_class_cells','fraction_different_among_both_valid_population']})
