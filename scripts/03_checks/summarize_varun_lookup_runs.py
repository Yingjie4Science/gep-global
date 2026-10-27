"""Compare two completed runs of run_us_national_technical.py on matched US support.

Usage: python scripts/03_checks/summarize_varun_lookup_runs.py DERIVED_RUN VARUN_RUN OUTPUT_DIR
"""
import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_rows(path):
    with path.open(newline='') as f:
        return {r['region_id']: r for r in csv.DictReader(f)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('derived_run', type=Path)
    p.add_argument('varun_run', type=Path)
    p.add_argument('output_dir', type=Path)
    a = p.parse_args()
    a.output_dir.mkdir(parents=True, exist_ok=True)
    paths = [a.derived_run/'urban_feature_results.csv', a.varun_run/'urban_feature_results.csv']
    left, right = map(read_rows, paths)
    assert left.keys() == right.keys()
    summaries = [json.loads((d/'national_summary.json').read_text()) for d in (a.derived_run, a.varun_run)]
    assert len(left) == summaries[0]['feature_count'] == summaries[1]['feature_count'] == 3312
    out = []
    for i in sorted(left):
        x, y = left[i], right[i]
        for column in ('population_total', 'population_modelled', 'population_source_fill'):
            assert abs(float(x[column]) - float(y[column])) < 1e-6, (i, column)
        base, owner = float(x['additional_cases']), float(y['additional_cases'])
        out.append({'city_id': i, 'city_name': x['region_name'], 'population_total': x['population_total'],
                    'derived_cases': base, 'varun_lookup_cases': owner,
                    'case_difference': owner-base,
                    'percent_difference': 100*(owner/base-1) if base>0 else ''})
    vals = [r['percent_difference'] for r in out if r['derived_cases'] >= 100]
    ranked = sorted(vals)
    result = {
        'status': 'complete_matched_local_lookup_runs',
        'comparison': 'Same local 2019 Zenodo GLC classes, WorldPop raster, 3312 GUPPD features, OR/p0, GBD prevalence and cost proxy; only lookup CSV differs.',
        'input_sha256': {'derived_city_results': sha256(paths[0]), 'varun_city_results': sha256(paths[1])},
        'derived_run_record_sha256': sha256(a.derived_run/'run_record.json'),
        'varun_run_record_sha256': sha256(a.varun_run/'run_record.json'),
        'city_rows': len(out),
        'population_total': summaries[0]['totals']['population_total'],
        'population_modelled': summaries[0]['totals']['population_modelled'],
        'derived_cases': summaries[0]['totals']['additional_cases'],
        'varun_lookup_cases': summaries[1]['totals']['additional_cases'],
        'percent_difference': 100*(summaries[1]['totals']['additional_cases']/summaries[0]['totals']['additional_cases']-1),
        'varun_conditional_effect_limits': [summaries[1]['totals']['additional_cases_lower'], summaries[1]['totals']['additional_cases_upper']],
        'cities_with_derived_cases_at_least_100': len(vals),
        'median_city_percent_difference_at_least_100': statistics.median(vals),
        'city_percent_difference_5th_95th_at_least_100': [ranked[int(.05*(len(ranked)-1))], ranked[int(.95*(len(ranked)-1))]],
        'fraction_cities_absolute_difference_over_10_percent_at_least_100': sum(abs(v)>10 for v in vals)/len(vals),
        'limitation': 'Technical lookup sensitivity, not Varun full-run reproduction or empirical validation. Both runs use current 3312-feature US selection and current cost proxy; Varun supplied polygon layer and cost workbook are not substituted. Effect limits hold other inputs fixed.',
    }
    (a.output_dir/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    with (a.output_dir/'city_comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]))
        w.writeheader();w.writerows(out)
    print(json.dumps({k: result[k] for k in ('city_rows','derived_cases','varun_lookup_cases','percent_difference','median_city_percent_difference_at_least_100')},indent=2))


if __name__ == '__main__':
    main()
