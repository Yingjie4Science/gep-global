#!/usr/bin/env python3
"""Prepare contiguous-US boundaries from preserved non-Hawaii derivatives.

USA source selection already excludes territories. Alaska is identified by a
representative point north of 50N (all Alaska is north of 51N; lower 48 south
of 50N). Verify geographic CRS and preserve geometry/attributes unchanged.
This is a new scope derivative, not a rewrite of historical inputs or results.
"""
import argparse, hashlib, json
from pathlib import Path
import fiona
from shapely.geometry import shape

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('data_root',type=Path)
    a=ap.parse_args(); records=[]
    for stem in ('guppd','varun'):
        src=a.data_root/f'processed/{stem}_us_excluding_hawaii.gpkg'
        dst=a.data_root/f'processed/{stem}_us_contiguous.gpkg'
        if dst.exists(): raise FileExistsError(dst)
        with fiona.open(src) as ds:
            if ds.crs.to_epsg()!=4326: raise ValueError('Expected EPSG:4326')
            rows=list(ds); keep=[]; excluded=[]
            for row in rows:
                geom=shape(row['geometry'])
                if geom.representative_point().y>=50:
                    excluded.append(row['properties']['id'])
                else:
                    if not (-125<=geom.representative_point().x<=-66 and 24<=geom.representative_point().y<50):
                        raise ValueError('Unexpected geometry outside contiguous-US envelope')
                    keep.append(row)
            assert excluded and keep
            ids=[r['properties']['id'] for r in keep]
            assert len(ids)==len(set(ids))
            with fiona.open(dst,'w',driver='GPKG',layer='urban_boundaries',schema=ds.schema,crs=ds.crs) as out:
                out.writerecords(keep)
        records.append(dict(source=str(src.relative_to(a.data_root)),source_sha256=sha(src),output=str(dst.relative_to(a.data_root)),output_sha256=sha(dst),source_features=len(rows),retained_features=len(keep),excluded_alaska_ids=excluded,geometry_changed=False))
    receipt={'scope':'48 contiguous states plus DC; excludes Alaska, Hawaii and territories','selection':'From prior non-Hawaii USA selection; exclude representative-point latitude >=50N; verify EPSG4326 and retained envelope','records':records,'health_results_recalculated':False}
    (a.data_root/'manifests/contiguous_us_scope_2026-10-27.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
