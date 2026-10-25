"""Compare the supplied mosaic and current WorldPop raster on all active US urban cell centres.

Usage: python scripts/check_varun_population_mosaic.py DATA_ROOT OUTPUT_JSON
"""
import argparse
import hashlib
import json
from pathlib import Path
import fiona
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds, Window
from shapely.geometry import shape

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("data_root", type=Path)
p.add_argument("output_json", type=Path)
args=p.parse_args()
root=args.data_root
owner=root/'raw/collaborator/varun_2026-10/worldpop/100m_2019_global-mosaic.tif'
current=root/'raw/worldpop/usa_pop_2019_CN_100m_R2025A_v1.tif'
polygons=root/'processed/guppd_us_excluding_hawaii.gpkg'
with rasterio.open(owner) as a,rasterio.open(current) as b,fiona.open(polygons) as ds:
    assert a.crs==b.crs and a.transform==b.transform and a.width==b.width
    assert a.nodata==b.nodata
    tally={'features_checked':0,'polygon_cells_checked':0,'cells_with_current_valid_population':0,'value_mismatches':0,'nodata_mismatches':0,'population_current':0.0,'population_owner':0.0,'max_abs_difference':0.0,'first_mismatch_ids':[]}
    for f in ds:
        g=shape(f['geometry']); fid=f['properties']['id']
        w=from_bounds(*g.bounds,transform=b.transform)
        c0=max(0,int(np.floor(w.col_off)));r0=max(0,int(np.floor(w.row_off)))
        c1=min(b.width,int(np.ceil(w.col_off+w.width)));r1=min(b.height,int(np.ceil(w.row_off+w.height)))
        win=Window(c0,r0,c1-c0,r1-r0)
        x=b.read(1,window=win);y=a.read(1,window=win)
        inside=geometry_mask([g],x.shape,b.window_transform(win),invert=True,all_touched=False)
        valid_x=inside & np.isfinite(x) & (x!=b.nodata) & (x>=0)
        valid_y=inside & np.isfinite(y) & (y!=a.nodata) & (y>=0)
        nodiff=int(np.count_nonzero(valid_x^valid_y))
        both=valid_x&valid_y
        valdiff=int(np.count_nonzero(x[both]!=y[both]))
        tally['features_checked']+=1;tally['polygon_cells_checked']+=int(np.count_nonzero(inside));tally['cells_with_current_valid_population']+=int(np.count_nonzero(valid_x));tally['nodata_mismatches']+=nodiff;tally['value_mismatches']+=valdiff
        tally['population_current']+=float(x[valid_x].sum(dtype='float64'));tally['population_owner']+=float(y[valid_y].sum(dtype='float64'))
        if valdiff:
            tally['max_abs_difference']=max(tally['max_abs_difference'],float(np.max(np.abs(x[both]-y[both]))))
        if (nodiff or valdiff) and len(tally['first_mismatch_ids'])<10:tally['first_mismatch_ids'].append(str(fid))
        if tally['features_checked']%500==0:print('checked',tally['features_checked'],flush=True)
    tally['status']='matched_all_active_us_urban_polygon_cell_centres' if tally['nodata_mismatches']==0 and tally['value_mismatches']==0 else 'mismatch_found'
    tally['scope']='Current 3312 GUPPD US features excluding Hawaii; native WorldPop cell-centre membership, including repeated feature memberships if any.'
    def sha256(path):
        h=hashlib.sha256()
        with path.open('rb') as src:
            for block in iter(lambda:src.read(8*1024*1024),b''):
                h.update(block)
        return h.hexdigest()
    tally['mosaic_sha256']=sha256(owner)
    tally['current_us_sha256']=sha256(current)
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    args.output_json.write_text(json.dumps(tally,indent=2)+'\n')
    print(json.dumps(tally,indent=2))
