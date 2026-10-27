"""Audit supplied GUPPD layer and calculate a matched-support US lookup sensitivity.

Usage: python scripts/03_checks/audit_varun_inputs.py DATA_ROOT REPO_ROOT OUTPUT_DIR
Outputs are diagnostics, not a full rerun of Varun's model.
"""
import argparse
import collections
import csv
import hashlib
import json
import math
import sqlite3
from pathlib import Path

from shapely import wkb


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def table(conn, query):
    return list(conn.execute(query))


def boundary_audit(data):
    source = data / 'raw/guppd/Urban_boundaries/urbanspatial-guppd-v1-gpkg.gpkg'
    owner = data / 'raw/collaborator/varun_2026-10/urban_boundaries_2019.gpkg'
    active = data / 'processed/guppd_us_excluding_hawaii.gpkg'
    with sqlite3.connect(source) as a, sqlite3.connect(owner) as b, sqlite3.connect(active) as c:
        originals = {r[0]: r[1:] for r in table(a, 'SELECT SMOD_ID, SMOD_LEVEL, ISO, GHSPOP_R23_2020, AREA_SQKM FROM urbanspatial_guppd_v1_polygons')}
        supplied = {r[0]: r[1:] for r in table(b, 'SELECT id, iso3, country, population_2019, area_km2 FROM urban_boundaries_2019')}
        current = {r[0] for r in table(c, 'SELECT id FROM urban_boundaries')}
        owner_geoms = dict(table(b, "SELECT id, geom FROM urban_boundaries_2019 WHERE iso3='USA'"))
        source_geoms = dict(table(a, "SELECT SMOD_ID, Shape FROM urbanspatial_guppd_v1_polygons WHERE ISO='USA'"))
        # Skip the GeoPackage binary header; Shapely's loader handles the WKB at its documented offset.
        def gpkg_geometry(blob):
            flags = blob[3]
            envelope_code = (flags >> 1) & 7
            size = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[envelope_code]
            return wkb.loads(blob[8 + size:])
        us_common = set(owner_geoms) & set(source_geoms)
        geometry_equal = sum(gpkg_geometry(owner_geoms[i]).equals_exact(gpkg_geometry(source_geoms[i]), 0) for i in us_common)
        omitted = set(originals) - set(supplied)
        owner_us = {i for i, fields in supplied.items() if fields[0] == 'USA'}
        current_us = current
        unmatched_current = sorted(current_us - owner_us)
        owner_hawaii = sorted(owner_us - current_us)
        missing_2020 = [originals[i][2] for i in omitted]
        level_counts = lambda ids: dict(sorted(collections.Counter(i.split('_')[0] for i in ids).items()))
        return {
            'status': 'source_file_audit',
            'input_sha256': {str(p.relative_to(data)): sha256(p) for p in (source, owner, active)},
            'owner_layer': 'urban_boundaries_2019',
            'owner_feature_count': len(supplied),
            'owner_levels': level_counts(supplied),
            'source_feature_count': len(originals),
            'owner_ids_all_in_source': len(set(supplied) - set(originals)) == 0,
            'source_ids_omitted_by_owner': len(omitted),
            'omitted_levels': level_counts(omitted),
            'omitted_source_2020_population_zero': sum(x == 0 for x in missing_2020),
            'omitted_source_2020_population_max': max(missing_2020),
            'owner_us_count': len(owner_us),
            'owner_us_levels': level_counts(owner_us),
            'active_us_count': len(current_us),
            'active_us_levels': level_counts(current_us),
            'source_us_count': len(source_geoms),
            'us_matching_geometry_count': geometry_equal,
            'us_common_geometry_count': len(us_common),
            'active_ids_absent_from_owner': unmatched_current,
            'absent_from_owner_have_zero_population_in_published_us_results': ['22_15706', '22_15770', '23_88815'] == unmatched_current,
            'owner_ids_absent_from_active': owner_hawaii,
            'owner_us_population_2019_attribute_sum_on_active_ids': sum(supplied[i][2] for i in current_us & owner_us),
            'owner_population_attribute_note': 'Stored attribute is not the modeled raster cell-centre total; do not substitute it for modeled population.',
            'filter_inference': 'All three GUPPD levels retained; 1,482 source IDs omitted. Omitted source GHSPOP_R23_2020 is usually zero, but the actual 2019-population selection rule is not in the file.',
            'fid_note': 'Owner layer FIDs are sequential 1..121552; original code assigned matching sequential FIDs, but a different derivative could break that assumption.',
        }


def lookup(path):
    with path.open(newline='') as f:
        rows = list(csv.DictReader(f))
    return {int(r['lc_code']): float(r['lc_ndvi']) for r in rows if r.get('lc_ndvi')}


def sensitivity(data, repo):
    classes = data / 'archive/extracted/pilots/us_national_technical_2019_v1/run_002/class_population_summary.csv'
    prior = data / 'archive/extracted/pilots/us_national_technical_2019_v1/run_002/national_summary.json'
    owner = data / 'raw/collaborator/varun_2026-10/glc_fcs30d_attribute_table_processed_updated.csv'
    derived = repo / 'docs/evidence/data/us_method_comparison_2019_v2_common/glc_fcs30d_attribute_table_us_2019.csv'
    with classes.open(newline='') as f:
        rows = list(csv.DictReader(f))
    owner_map, derived_map = lookup(owner), lookup(derived)
    prior_map = {int(r['lc_code']): float(r['lc_ndvi']) for r in rows if r['lc_ndvi']}
    prior_record = json.loads(prior.read_text())
    def result(values, prevalence, odds_ratio, equation, codes):
        rr = odds_ratio / (1 - 0.115 + 0.115 * odds_ratio)
        acc = 0.0
        for r in rows:
            code = int(r['lc_code'])
            if code not in codes:
                continue
            n = max(values[code], 0.0)
            factor = (rr ** (-10 * n) - 1) if equation == 'current_reference' else (1 - rr ** (10 * n))
            acc += float(r['feature_row_population']) * prevalence * factor
        return acc
    previous = result(prior_map, .0424332878, .931, 'current_reference', set(prior_map))
    assert abs(previous - prior_record['totals']['additional_cases']) < 1e-5
    populated = {int(r['lc_code']) for r in rows if int(r['lc_code']) not in (0, 250) and float(r['feature_row_population']) > 0}
    common = populated & set(owner_map) & set(derived_map)
    population = sum(float(r['feature_row_population']) for r in rows if int(r['lc_code']) in common)
    outputs = []
    for rate_name, prevalence in [('GBD_2019_US_all_age', .0424332878), ('fixed_5_percent', .05)]:
        for equation in ('current_reference', 'literal_original'):
            for variant, mapping in [('US_2019_derived', derived_map), ('Varun_confirmed_run_lookup', owner_map)]:
                outputs.append({'lookup': variant, 'prevalence': rate_name, 'health_equation': equation,
                                'common_population': population,
                                'case_equivalents': result(mapping, prevalence, .931, equation, common),
                                'effect_lower': result(mapping, prevalence, .977, equation, common),
                                'effect_upper': result(mapping, prevalence, .887, equation, common)})
    primary = [r for r in outputs if r['prevalence'] == 'GBD_2019_US_all_age' and r['health_equation'] == 'current_reference']
    by_name = {r['lookup']: r for r in primary}
    return {
        'status': 'national_lookup_value_sensitivity_from_existing_class_population_totals',
        'scope': 'Local Zenodo 2019 land-cover classes on the current 3312-feature non-Hawaii US selection, sampled at WorldPop cell centres; same populated class support for both lookups.',
        'input_sha256': {str(p.relative_to(data) if p.is_relative_to(data) else p.relative_to(repo)): sha256(p) for p in (classes, prior, owner, derived)},
        'source_run_reconstruction': {'previous_cases_recomputed': previous, 'previous_cases_reported': prior_record['totals']['additional_cases'], 'absolute_difference': abs(previous - prior_record['totals']['additional_cases'])},
        'common_class_codes': sorted(common),
        'common_population': population,
        'source_fill_population_excluded': sum(float(r['feature_row_population']) for r in rows if int(r['lc_code']) in (0,250)),
        'scenarios': outputs,
        'primary_varun_minus_derived_percent': 100 * (by_name['Varun_confirmed_run_lookup']['case_equivalents'] / by_name['US_2019_derived']['case_equivalents'] - 1),
        'interpretation': 'Isolates fixed lookup values on existing national class-population totals. It does not rerun raster preprocessing, produce city results, verify the owner lookup derivation, or validate either lookup against outcomes. OR limits are conditional on all other inputs.',
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('data_root', type=Path)
    p.add_argument('repo_root', type=Path)
    p.add_argument('output_dir', type=Path)
    a = p.parse_args()
    a.output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in [('urban_boundaries_audit.json', boundary_audit(a.data_root)),
                        ('us_lookup_value_sensitivity.json', sensitivity(a.data_root, a.repo_root))]:
        (a.output_dir / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
        print(name)


if __name__ == '__main__':
    main()
