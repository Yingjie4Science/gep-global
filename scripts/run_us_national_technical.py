"""Run a windowed 2019 US technical estimate over retained GUPPD features.

The runner avoids a dense national mosaic. It uses WorldPop cell-centre
membership (rasterio geometry_mask, all_touched=False), preserves feature rows,
and reports source fill and missing lookup support explicitly.
"""
import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import Window, from_bounds
from rasterio.warp import Resampling, reproject

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import effect_size_uncertainty
import urban_mental_health_functions as model
from prevalence_inputs import resolve_country_rates


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def window_for_geometry(dataset, geometry):
    window = from_bounds(*geometry.bounds, transform=dataset.transform)
    x0 = max(0, math.floor(window.col_off))
    y0 = max(0, math.floor(window.row_off))
    x1 = min(dataset.width, math.ceil(window.col_off + window.width))
    y1 = min(dataset.height, math.ceil(window.row_off + window.height))
    return Window(x0, y0, x1 - x0, y1 - y0)


def exact_overlap_audit(cities, population):
    records = []
    spatial_index = cities.sindex
    for index, row in cities.iterrows():
        for other_index in spatial_index.query(row.geometry, predicate='intersects'):
            if other_index <= index:
                continue
            other = cities.iloc[other_index]
            intersection = row.geometry.intersection(other.geometry)
            if intersection.is_empty or intersection.area <= 1e-12:
                continue
            window = window_for_geometry(population, intersection)
            values = population.read(1, window=window)
            transform = population.window_transform(window)
            first = geometry_mask([row.geometry], values.shape, transform, invert=True, all_touched=False)
            second = geometry_mask([other.geometry], values.shape, transform, invert=True, all_touched=False)
            valid = first & second & np.isfinite(values) & (values >= 0)
            records.append({
                'first_id': str(row.id),
                'second_id': str(other.id),
                'shared_population_cells': int(valid.sum()),
                'shared_population': float(values[valid].sum(dtype='float64')),
            })
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data_root', type=Path)
    parser.add_argument('output_dir', type=Path)
    parser.add_argument('--lookup', type=Path, required=True)
    parser.add_argument('--effects', type=Path, required=True)
    parser.add_argument('--prevalence', type=Path, required=True)
    parser.add_argument('--crosswalk', type=Path, required=True)
    parser.add_argument('--cost', type=Path, required=True)
    parser.add_argument('--p0', type=float, default=0.115)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise FileExistsError('Choose a fresh output directory; technical runs never reuse cached outputs')
    args.output_dir.mkdir(parents=True, exist_ok=True)

    lookup_table = pd.read_csv(args.lookup).dropna(subset=['lc_ndvi'])
    if lookup_table.lc_code.duplicated().any():
        raise ValueError('Lookup codes must be unique')
    lookup = dict(zip(lookup_table.lc_code.astype(int), lookup_table.lc_ndvi.astype(float)))
    if not lookup or not all(-1 <= value <= 1 for value in lookup.values()):
        raise ValueError('Lookup values must be finite NDVI values in [-1, 1]')
    max_positive_ndvi = max(0.0, max(lookup.values()))

    effects = model.load_depression_effect_sizes(args.effects)
    odds = {
        'additional_cases': effects['effect_size'],
        'additional_cases_lower': effects['ci_upper'],
        'additional_cases_upper': effects['ci_lower'],
    }
    risk_ratios = {
        name: effect_size_uncertainty.odds_ratio_to_risk_ratio(value, args.p0)
        for name, value in odds.items()
    }
    prevalence = resolve_country_rates(['United States'], args.prevalence, args.crosswalk)['United States']
    cost_table = pd.read_csv(args.cost)
    if len(cost_table) != 1:
        raise ValueError('US technical run requires exactly one cost row')
    cost_row = cost_table.iloc[0]
    if not (cost_row['country'] == 'United States' and cost_row['currency'] == 'USD'
            and int(cost_row['price_year']) == 2019
            and str(cost_row['ppp_adjusted']).lower() == 'false'):
        raise ValueError('Cost row must explicitly declare United States, 2019 USD and no PPP adjustment')
    cost_per_case = float(cost_row['cost_per_case'])

    cities_path = args.data_root / 'processed/guppd_us_excluding_hawaii.gpkg'
    population_path = args.data_root / 'raw/worldpop/usa_pop_2019_CN_100m_R2025A_v1.tif'
    plan_path = args.data_root / 'manifests/glc_us_download_plan.json'
    cities = gpd.read_file(cities_path)
    plan = json.loads(plan_path.read_text())['tiles']
    tile_specs = []
    for item in plan:
        name = Path(item['member']).name.replace('20002022', '2019')
        output = args.data_root / 'processed/lulc_2019_us' / name
        status_path = args.data_root / 'manifests/glc_us_tiles' / (Path(item['member']).name + '.json')
        if not output.is_file() or not status_path.is_file() or json.loads(status_path.read_text()).get('status') != 'verified':
            raise ValueError(f'Land-cover tile is not independently verified: {name}')
        tile_specs.append((item['bounds'], output))

    class_cells = Counter()
    class_population = defaultdict(float)
    feature_rows = []
    with ExitStack() as stack:
        population = stack.enter_context(rasterio.open(population_path))
        tile_sources = [(bounds, stack.enter_context(rasterio.open(path))) for bounds, path in tile_specs]
        overlap_records = exact_overlap_audit(cities, population)
        shared_cells = sum(row['shared_population_cells'] for row in overlap_records)
        if shared_cells:
            raise ValueError(f'Feature totals overlap on {shared_cells} native cell centres; deterministic allocation is required')

        for sequence, (_, city) in enumerate(cities.iterrows(), 1):
            window = window_for_geometry(population, city.geometry)
            pop = population.read(1, window=window)
            transform = population.window_transform(window)
            inside = geometry_mask([city.geometry], pop.shape, transform, invert=True, all_touched=False)
            valid = inside & np.isfinite(pop) & (pop >= 0)
            land = np.zeros(pop.shape, dtype='uint16')
            xmin, ymin, xmax, ymax = city.geometry.bounds
            used_tiles = []
            for bounds, source in tile_sources:
                if bounds[0] >= xmax or bounds[2] <= xmin or bounds[1] >= ymax or bounds[3] <= ymin:
                    continue
                reproject(
                    source=rasterio.band(source, 1), destination=land,
                    src_transform=source.transform, src_crs=source.crs, src_nodata=0,
                    dst_transform=transform, dst_crs=population.crs, dst_nodata=0,
                    init_dest_nodata=False, resampling=Resampling.nearest)
                used_tiles.append(Path(source.name).name)

            ndvi = np.full(pop.shape, np.nan, dtype='float64')
            for code, value in lookup.items():
                ndvi[land == code] = value
            fill = valid & np.isin(land, [0, 250])
            missing_lookup = valid & ~np.isin(land, [0, 250]) & ~np.isfinite(ndvi)
            supported = valid & np.isfinite(ndvi)
            delta = np.maximum(ndvi[supported], 0.0)
            supported_pop = pop[supported].astype('float64')
            result = {
                'region_id': str(city.id),
                'region_name': str(city.CIESIN_NAME),
                'smod_level': int(city.SMOD_LEVEL),
                'country': str(city.country),
                'population_cells': int(valid.sum()),
                'population_total': float(pop[valid].sum(dtype='float64')),
                'population_modelled': float(supported_pop.sum(dtype='float64')),
                'population_source_fill': float(pop[fill].sum(dtype='float64')),
                'population_missing_lookup': float(pop[missing_lookup].sum(dtype='float64')),
                'source_fill_cells': int(fill.sum()),
                'missing_lookup_cells': int(missing_lookup.sum()),
                'missing_lookup_classes': '|'.join(map(str, np.unique(land[missing_lookup]))),
                'verified_tiles_used': '|'.join(used_tiles),
                'baseline_prevalence': prevalence,
                'observed_cases_on_modelled_population': float(supported_pop.sum(dtype='float64')) * prevalence,
            }
            for name, risk_ratio in risk_ratios.items():
                cases = supported_pop * prevalence * (np.exp(-10.0 * delta * np.log(risk_ratio)) - 1.0)
                result[name] = float(cases.sum(dtype='float64'))
                result[name + '_value_2019_usd_proxy'] = result[name] * cost_per_case

            unsupported_population = float(pop[valid & ~supported].sum(dtype='float64'))
            fill_upper_factor = math.exp(-10.0 * max_positive_ndvi * math.log(risk_ratios['additional_cases'])) - 1.0
            result['unsupported_population'] = unsupported_population
            result['additional_cases_missing_exposure_lower'] = 0.0
            result['additional_cases_missing_exposure_upper'] = unsupported_population * prevalence * fill_upper_factor
            result['additional_cases_with_missing_exposure_upper'] = (
                result['additional_cases'] + result['additional_cases_missing_exposure_upper'])
            feature_rows.append(result)

            for code in np.unique(land[valid]):
                mask = valid & (land == code)
                class_cells[int(code)] += int(mask.sum())
                class_population[int(code)] += float(pop[mask].sum(dtype='float64'))
            if sequence % 200 == 0:
                print(f'Processed {sequence} of {len(cities)} features', flush=True)

    features = pd.DataFrame(feature_rows)
    features.to_csv(args.output_dir / 'urban_feature_results.csv', index=False)
    class_rows = [{
        'lc_code': code,
        'feature_row_cells': class_cells[code],
        'feature_row_population': class_population[code],
        'lookup_status': 'represented' if code in lookup else ('source_fill' if code in (0, 250) else 'missing_lookup'),
        'lc_ndvi': lookup.get(code),
    } for code in sorted(class_cells)]
    pd.DataFrame(class_rows).to_csv(args.output_dir / 'class_population_summary.csv', index=False)

    totals = {column: float(features[column].sum()) for column in [
        'population_total', 'population_modelled', 'population_source_fill', 'population_missing_lookup',
        'observed_cases_on_modelled_population', 'additional_cases', 'additional_cases_lower',
        'additional_cases_upper', 'additional_cases_value_2019_usd_proxy',
        'additional_cases_lower_value_2019_usd_proxy', 'additional_cases_upper_value_2019_usd_proxy',
        'additional_cases_missing_exposure_upper', 'additional_cases_with_missing_exposure_upper',
    ]}
    summary = {
        'status': 'exploratory_nationwide_technical_run',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'scope': '3,312 GUPPD source features; 49 states plus DC; Alaska included; Hawaii and territories excluded.',
        'membership_rule': 'WorldPop native cell centres inside each source polygon; rasterio geometry_mask all_touched=False.',
        'overlap_audit': overlap_records,
        'summation_valid': True,
        'feature_count': len(features),
        'lookup_status': 'Five-region exploratory pooled lookup derived with community GLC class map; not production or Zenodo-class validated.',
        'primary_missing_data_rule': 'Exclude source fill codes 0/250 and any class without a lookup from modelled population and cases.',
        'missing_exposure_sensitivity': (
            'Lower assigns zero additional cases; upper assigns every unsupported person the maximum positive pooled class NDVI. '
            'This is a structural bound, not a confidence interval.'
        ),
        'effect_interval': 'Conditional 95% effect-size limits only; all other inputs and assumptions fixed.',
        'cost_status': 'Exploratory 2019 USD non-PPP mood-disorder total societal-cost proxy; not treatment savings.',
        'parameters': {
            'prevalence': prevalence, 'p0': args.p0, 'odds_ratio': effects,
            'cost_per_case_2019_usd_proxy': cost_per_case,
            'maximum_positive_lookup_ndvi_for_missing_exposure_upper': max_positive_ndvi,
        },
        'totals': totals,
    }
    (args.output_dir / 'national_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    pd.DataFrame([totals]).to_csv(args.output_dir / 'national_summary.csv', index=False)

    inputs = [args.lookup, args.effects, args.prevalence, args.crosswalk, args.cost,
              cities_path, population_path, plan_path]
    outputs = [args.output_dir / name for name in [
        'urban_feature_results.csv', 'class_population_summary.csv', 'national_summary.json', 'national_summary.csv']]
    record = {
        'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=Path(__file__).resolve().parents[1], text=True).strip(),
        'python': sys.version,
        'input_sha256': {str(path): sha256(path) for path in inputs},
        'source_sha256': {
            'scripts/run_us_national_technical.py': sha256(Path(__file__)),
            'effect_size_uncertainty.py': sha256(Path(__file__).resolve().parents[1] / 'effect_size_uncertainty.py'),
        },
        'output_sha256': {path.name: sha256(path) for path in outputs},
        'land_cover_tile_count': len(tile_specs),
        'land_cover_tile_manifest_sha256': {
            Path(item['member']).name: sha256(args.data_root / 'manifests/glc_us_tiles' / (Path(item['member']).name + '.json'))
            for item in plan
        },
    }
    (args.output_dir / 'run_record.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
