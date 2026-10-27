"""Audit unique GUPPD area for the two saved US boundary inputs.

Usage: python scripts/03_checks/audit_us_urban_area.py LOCAL_GPKG VARUN_GPKG
       SNAPP_COUNTIES_GPKG SNAPP_REGIONS_CSV OUTPUT_JSON
Requires geopandas and shapely (the project's InVEST environment has both).
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import shapely


def file_hash(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inspect(path, id_col='id'):
    frame = gpd.read_file(path)
    if frame.crs is None:
        raise ValueError(f'{path}: missing CRS')
    if id_col not in frame or frame[id_col].duplicated().any():
        raise ValueError(f'{path}: missing or duplicate GUPPD IDs')
    if frame.geometry.isna().any() or (~frame.geometry.is_valid).any():
        raise ValueError(f'{path}: missing or invalid geometry')
    planar = frame.to_crs('EPSG:5070')
    sum_area = float(planar.geometry.area.sum() / 1e6)
    unique_area = float(shapely.union_all(planar.geometry.array).area / 1e6)
    return {
        'path': str(path),
        'sha256': file_hash(path),
        'feature_count': len(frame),
        'input_crs': str(frame.crs),
        'area_method': 'reproject polygon geometry to EPSG:5070; shapely.union_all; area / 1e6',
        'unique_area_km2': unique_area,
        'polygon_area_sum_km2': sum_area,
        'overlap_km2': sum_area - unique_area,
        'ids': set(frame[id_col]),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('local_gpkg', type=Path)
    p.add_argument('varun_gpkg', type=Path)
    p.add_argument('snapp_counties_gpkg', type=Path)
    p.add_argument('snapp_regions_csv', type=Path)
    p.add_argument('output_json', type=Path)
    a = p.parse_args()
    local = inspect(a.local_gpkg)
    varun = inspect(a.varun_gpkg)
    snapp = inspect(a.snapp_counties_gpkg, id_col='GEOID')
    with a.snapp_regions_csv.open(newline='') as source:
        expected_snapp_ids = {row['GEOID'].zfill(5) for row in csv.DictReader(source)}
    if snapp['ids'] != expected_snapp_ids or len(expected_snapp_ids) != 1167:
        raise ValueError('SNAPP county geometries differ from locked national region IDs')
    snapp.pop('ids')
    snapp['region_list_path'] = str(a.snapp_regions_csv)
    snapp['region_list_sha256'] = file_hash(a.snapp_regions_csv)
    local_ids = local.pop('ids')
    varun_ids = varun.pop('ids')
    extra = sorted(local_ids - varun_ids)
    if (local['feature_count'] != 3312 or varun['feature_count'] != 3309
            or len(extra) != 3 or varun_ids - local_ids):
        raise ValueError('Boundary counts or extra-ID count changed; review before reporting area')
    out = {
        'status': 'unique_footprint_area_of_saved_non_hawaii_us_guppd_polygons',
        'local': local,
        'varun': varun,
        'snapp_metropolitan_counties': snapp,
        'local_only_ids': extra,
        'unique_area_difference_km2': local['unique_area_km2'] - varun['unique_area_km2'],
        'interpretation': 'Polygon footprint only; not populated area or valid-NDVI area. SNAPP metropolitan county geography is a different spatial support.',
    }
    a.output_json.parent.mkdir(parents=True, exist_ok=True)
    a.output_json.write_text(json.dumps(out, indent=2) + '\n')


if __name__ == '__main__':
    main()
