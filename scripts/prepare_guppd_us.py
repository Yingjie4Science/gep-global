#!/usr/bin/env python3
"""Preserve source GUPPD attributes and create a US polygon input plus QC report."""
import argparse, collections, hashlib, json
from pathlib import Path
import fiona
from shapely.geometry import shape, box
from shapely.ops import unary_union

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('data_root',type=Path); args=ap.parse_args(); root=args.data_root
    source=root/'raw/guppd/Urban_boundaries/urbanspatial-guppd-v1-gpkg.gpkg'
    output=root/'processed/guppd_us.gpkg'; report=root/'manifests/guppd_us_qc.json'
    if output.exists(): raise FileExistsError(f'Preserving existing derivative: {output}')
    with fiona.open(source,layer='urbanspatial_guppd_v1_polygons') as src:
        rows=[f for f in src if f['properties']['ISO']=='USA']
        schema=dict(src.schema); schema['properties']=dict(schema['properties'],source_fid='str',id='str',country='str',iso3='str')
        invalid=[f['properties']['SMOD_ID'] for f in rows if not shape(f['geometry']).is_valid]
        ids=[f['properties']['SMOD_ID'] for f in rows]
        if invalid or len(ids)!=len(set(ids)): raise ValueError('Invalid geometry or duplicate source ID; review required')
        with fiona.open(output,'w',driver='GPKG',layer='urban_boundaries',schema=schema,crs=src.crs) as dst:
            for f in rows:
                props=dict(f['properties']);props.update(source_fid=f.id,id=props['SMOD_ID'],country='United States',iso3='USA')
                dst.write(dict(geometry=f['geometry'],properties=props))
    plan=json.loads((root/'manifests/glc_us_download_plan.json').read_text())
    coverage=unary_union([box(*t['bounds']) for t in plan['tiles']])
    missing=[f['properties']['SMOD_ID'] for f in rows if not coverage.covers(shape(f['geometry']))]
    report.write_text(json.dumps(dict(source_layer='urbanspatial_guppd_v1_polygons',filter="ISO == 'USA'",feature_count=len(rows),levels=dict(collections.Counter(f['properties']['SMOD_LEVEL'] for f in rows)),invalid_geometry_count=len(invalid),duplicate_ids=0,polygons_outside_planned_lulc_tiles=missing,coverage_note='Planned nominal tile extents only; downloaded raster coverage and nodata require later validation.',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),geometry_repairs='none',country_crosswalk='USA -> United States; verify downstream GBD alias mapping',epoch_note='GUPPD v1 source geometry retained; not relabelled as observed 2019 boundaries.',overlap_check='pending',output=str(output.relative_to(root))),indent=2))
    print(report.read_text())
if __name__=='__main__': main()
