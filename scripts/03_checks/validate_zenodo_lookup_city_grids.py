"""Compare paired Zenodo/community class lookups on identical city NDVI grids.

This is a bounded source-pairing diagnostic at the native WorldPop grid. It is
not a replacement for the reviewed 30 m lookup derivation or a US lookup.
"""
import argparse
import csv
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import ee
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.features import geometry_mask
from rasterio.windows import Window


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def landsat_ndvi(image, red_band, nir_band):
    qa = image.select('QA_PIXEL')
    clear = qa.bitwiseAnd(63).eq(0)
    unsaturated = image.select('QA_RADSAT').eq(0)
    red = image.select(red_band).multiply(0.0000275).add(-0.2)
    nir = image.select(nir_band).multiply(0.0000275).add(-0.2)
    denominator = nir.add(red)
    valid = clear.And(unsaturated).And(red.gte(0)).And(nir.gte(0)).And(denominator.gt(0))
    return nir.subtract(red).divide(denominator).rename('ndvi').updateMask(valid)


def annual_ndvi(region):
    l7 = (ee.ImageCollection('LANDSAT/LE07/C02/T1_L2')
          .filterBounds(region).filterDate('2019-01-01', '2020-01-01')
          .map(lambda image: landsat_ndvi(image, 'SR_B3', 'SR_B4')))
    l8 = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
          .filterBounds(region).filterDate('2019-01-01', '2020-01-01')
          .map(lambda image: landsat_ndvi(image, 'SR_B4', 'SR_B5')))
    observations = l7.merge(l8)
    count = observations.count().rename('n_obs')
    return observations.median().updateMask(count.gte(3)).rename('ndvi').addBands(count)


def download(image, path, height, width, transform):
    if path.exists():
        return
    incomplete = path.with_suffix('.incomplete.tif')
    profile = dict(driver='GTiff', height=height, width=width, count=2,
                   dtype='float64', crs='EPSG:4326', transform=transform,
                   nodata=-99999, compress='deflate')
    with rasterio.open(incomplete, 'w', **profile) as target:
        for row in range(0, height, 64):
            strip_height = min(64, height - row)
            strip_transform = list(transform)[:6]
            strip_transform[5] += row * strip_transform[4]
            response = None
            for attempt in range(5):
                try:
                    url = image.select(['ndvi', 'n_obs']).unmask(-99999).toDouble().getDownloadURL({
                        'crs': 'EPSG:4326', 'crs_transform': strip_transform,
                        'dimensions': [width, strip_height], 'format': 'GEO_TIFF'})
                    response = requests.get(url, timeout=(30, 120))
                    response.raise_for_status()
                    break
                except requests.RequestException:
                    if attempt == 4:
                        raise
                    time.sleep(5 * (2 ** attempt))
            with rasterio.io.MemoryFile(response.content) as memory:
                with memory.open() as source:
                    target.write(source.read(), window=Window(0, row, width, strip_height))
    incomplete.replace(path)


def class_lookup(land, ndvi, mask):
    rows = []
    lookup = {}
    for code in sorted(int(value) for value in np.unique(land[mask]) if value not in (0, 250, -99999)):
        selected = mask & (land == code)
        values = ndvi[selected]
        if not values.size:
            continue
        mean = float(values.mean(dtype='float64'))
        lookup[code] = mean
        rows.append({'lc_code': code, 'lc_ndvi': mean, 'ndvi_sd': float(values.std()),
                     'valid_cells': int(values.size)})
    return lookup, rows


def cases_from_lookup(population, land, inside, lookup, prevalence, risk_ratio):
    mapped = np.full(land.shape, np.nan, dtype='float64')
    for code, value in lookup.items():
        mapped[land == code] = value
    supported = inside & np.isfinite(population) & (population >= 0) & np.isfinite(mapped)
    delta = np.maximum(mapped[supported], 0.0)
    cases = population[supported].astype('float64') * prevalence * (
        np.exp(-10 * delta * np.log(risk_ratio)) - 1)
    return float(cases.sum(dtype='float64')), float(population[supported].sum(dtype='float64')), int(supported.sum())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data_root', type=Path)
    parser.add_argument('--project', default='natcap-gep')
    parser.add_argument('--prevalence', type=float, default=0.0424332878)
    parser.add_argument('--p0', type=float, default=0.115)
    parser.add_argument('--odds-ratio', type=float, default=0.931)
    args = parser.parse_args()
    ee.Initialize(project=args.project)
    risk_ratio = args.odds_ratio / (1 - args.p0 + args.p0 * args.odds_ratio)
    root = args.data_root / 'outputs/sf_minneapolis_2019_v1'
    summaries = []
    city_dirs = [path for path in root.iterdir() if (path / 'inputs/input_qc.json').is_file()]
    def grid_cells(path):
        with rasterio.open(path / 'inputs/population_2019.tif') as source:
            return source.width * source.height
    for city_dir in sorted(city_dirs, key=grid_cells):
        inputs = city_dir / 'inputs'
        output = city_dir / 'zenodo_lookup_grid_validation'
        output.mkdir(exist_ok=True)
        with rasterio.open(inputs / 'population_2019.tif') as source:
            population = source.read(1)
            transform = source.transform
            height, width = source.height, source.width
            bounds = source.bounds
        region = ee.Geometry.Rectangle([bounds.left, bounds.bottom, bounds.right, bounds.top], 'EPSG:4326', False)
        ndvi_path = output / 'landsat_ndvi_2019_worldpop_grid.tif'
        download(annual_ndvi(region), ndvi_path, height, width, transform)
        with rasterio.open(ndvi_path) as source:
            ndvi = source.read(1)
            observations = source.read(2)
        with rasterio.open(inputs / 'land_cover_2019.tif') as source:
            local_land = source.read(1)
        with rasterio.open(inputs / 'land_cover_gee.tif') as source:
            community_land = source.read(1)
        city = gpd.read_file(inputs / 'city.gpkg')
        inside = geometry_mask(city.geometry, population.shape, transform, invert=True, all_touched=False)
        lookup_ndvi_valid = inside & np.isfinite(ndvi) & (ndvi != -99999) & (observations >= 3)
        population_valid = inside & np.isfinite(population) & (population >= 0)
        direct_valid = lookup_ndvi_valid & population_valid
        local_lookup, local_rows = class_lookup(local_land, ndvi, lookup_ndvi_valid & ~np.isin(local_land, [0, 250]))
        community_lookup, community_rows = class_lookup(
            community_land, ndvi, lookup_ndvi_valid & ~np.isin(community_land, [0, 250, -99999]))
        for name, rows in [('zenodo', local_rows), ('community', community_rows)]:
            with (output / f'{name}_lookup_worldpop_grid.csv').open('w', newline='') as target:
                writer = csv.DictWriter(target, fieldnames=['lc_code', 'lc_ndvi', 'ndvi_sd', 'valid_cells'])
                writer.writeheader(); writer.writerows(rows)
        local_cases, local_population, local_cells = cases_from_lookup(
            population, local_land, inside, local_lookup, args.prevalence, risk_ratio)
        community_cases, community_population, community_cells = cases_from_lookup(
            population, community_land, inside, community_lookup, args.prevalence, risk_ratio)
        direct_population = population[direct_valid].astype('float64')
        direct_delta = np.maximum(ndvi[direct_valid].astype('float64'), 0.0)
        direct_cases = float((direct_population * args.prevalence * (
            np.exp(-10 * direct_delta * np.log(risk_ratio)) - 1)).sum(dtype='float64'))
        summary = {
            'city': city_dir.name,
            'city_id': str(city.iloc[0].id),
            'status': 'same_grid_source_pairing_diagnostic',
            'grid': 'native local WorldPop grid; class means are count-weighted within the GUPPD polygon',
            'scientific_limit': 'Not the reviewed 30 m plus-5-km lookup and not a national production lookup.',
            'lookup_ndvi_valid_cells': int(lookup_ndvi_valid.sum()),
            'direct_model_cells': int(direct_valid.sum()),
            'ndvi_valid_population': float(direct_population.sum(dtype='float64')),
            'direct_ndvi_cases': direct_cases,
            'zenodo_lookup_cases': local_cases,
            'zenodo_lookup_population': local_population,
            'zenodo_lookup_cells': local_cells,
            'community_lookup_cases': community_cases,
            'community_lookup_population': community_population,
            'community_lookup_cells': community_cells,
            'zenodo_vs_community_paired_case_percent': 100 * (local_cases / community_cases - 1),
            'parameters': {'prevalence': args.prevalence, 'p0': args.p0, 'odds_ratio': args.odds_ratio},
            'artifacts_sha256': {
                ndvi_path.name: sha256(ndvi_path),
                'zenodo_lookup_worldpop_grid.csv': sha256(output / 'zenodo_lookup_worldpop_grid.csv'),
                'community_lookup_worldpop_grid.csv': sha256(output / 'community_lookup_worldpop_grid.csv'),
            },
        }
        (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        summaries.append(summary)
        print(json.dumps({key: summary[key] for key in [
            'city', 'lookup_ndvi_valid_cells', 'direct_model_cells', 'zenodo_lookup_cases', 'community_lookup_cases',
            'zenodo_vs_community_paired_case_percent']}, indent=2), flush=True)
    frame = pd.DataFrame([{key: value for key, value in summary.items()
                           if not isinstance(value, (dict, list))} for summary in summaries])
    frame.to_csv(root / 'zenodo_lookup_grid_validation_summary.csv', index=False)
    manifest = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'method': 'Same Landsat 2019 NDVI pixels, same WorldPop grid and polygon mask; derive separate means by local Zenodo and community GLC class labels.',
        'results': summaries,
        'summary_sha256': sha256(root / 'zenodo_lookup_grid_validation_summary.csv'),
        'source_sha256': sha256(Path(__file__)),
    }
    (root / 'zenodo_lookup_grid_validation_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
