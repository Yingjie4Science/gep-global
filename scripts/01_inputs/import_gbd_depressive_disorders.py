"""Validate an IHME GBD Results CSV of country depressive-disorder prevalence.

The input must contain one crude, all-age, both-sex rate per country/territory
for a single estimate year. The GBD release is supplied separately because
the result CSV does not state which release produced the estimates.
"""

import argparse
import csv
import hashlib
import json
import math
import re
from datetime import date
from pathlib import Path


def normalize(value):
    return str(value).strip().casefold()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Official GBD Results CSV')
    parser.add_argument('--output', type=Path, required=True, help='Validated prevalence CSV')
    parser.add_argument('--gbd-release', required=True, help='Release shown by the tool, e.g. GBD 2023')
    parser.add_argument('--estimate-year', type=int, required=True, help='Year selected in GBD Results')
    parser.add_argument('--expected-locations', type=int, required=True,
                        help='Country/territory count selected and checked in GBD Results')
    parser.add_argument('--source-url', required=True, help='IHME request-details URL')
    parser.add_argument('--retrieved-on', required=True, help='Local retrieval date, YYYY-MM-DD')
    parser.add_argument('--archive', type=Path, help='Original IHME ZIP, retained for provenance')
    args = parser.parse_args()

    if args.expected_locations < 1 or not 1990 <= args.estimate_year <= 2100:
        parser.error('Expected locations must be positive and estimate year must be plausible')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.retrieved_on):
        parser.error('--retrieved-on must use YYYY-MM-DD')
    try:
        date.fromisoformat(args.retrieved_on)
    except ValueError:
        parser.error('--retrieved-on must be a real date in YYYY-MM-DD format')
    if not args.source_url.startswith('https://vizhub.healthdata.org/gbd-results/result/'):
        parser.error('--source-url must be the IHME GBD Results request-details URL')

    with args.input.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        required = {'population_group_name', 'measure_name', 'location_id', 'location_name',
                    'sex_name', 'age_name', 'cause_name', 'metric_name', 'year',
                    'val', 'lower', 'upper'}
        missing = required - set(reader.fieldnames or ())
        if missing:
            parser.error(f'Missing GBD columns: {sorted(missing)}')
        rows = list(reader)
    if not rows:
        parser.error('Input contains no data rows')

    expected = {
        'population_group_name': 'all population',
        'measure_name': 'prevalence',
        'sex_name': 'both',
        'age_name': 'all ages',
        'cause_name': 'depressive disorders',
        'metric_name': 'rate',
        'year': str(args.estimate_year),
    }
    output = []
    seen = set()
    for line, row in enumerate(rows, start=2):
        wrong = {field: row[field] for field, value in expected.items()
                 if normalize(row[field]) != value and not
                 (field == 'sex_name' and normalize(row[field]) == 'both sexes')}
        if wrong:
            parser.error(f'Row {line} has incompatible settings: {wrong}')
        location_id = row['location_id'].strip()
        location_name = row['location_name'].strip()
        if not location_id or not location_name:
            parser.error(f'Missing location identifier/name on row {line}')
        if location_id in seen:
            parser.error(f'Duplicate location ID {location_id} on row {line}')
        seen.add(location_id)
        try:
            val, lower, upper = (float(row[key]) for key in ('val', 'lower', 'upper'))
        except ValueError:
            parser.error(f'Non-numeric estimate on row {line}')
        if not all(map(math.isfinite, (val, lower, upper))):
            parser.error(f'Non-finite estimate on row {line}')
        if not (0 <= lower <= val <= upper <= 100000):
            parser.error(f'Invalid estimate interval on row {line}')
        output.append({
            'location_id': location_id,
            'country_as_gbd': location_name,
            'year': args.estimate_year,
            'prevalence_fraction': f'{val / 100000:.10f}',
            'prevalence_lower_fraction': f'{lower / 100000:.10f}',
            'prevalence_upper_fraction': f'{upper / 100000:.10f}',
            'rate_per_100000': val,
            'rate_lower_per_100000': lower,
            'rate_upper_per_100000': upper,
            'gbd_release': args.gbd_release,
        })

    if len(output) != args.expected_locations:
        parser.error(f'Found {len(output)} locations; expected {args.expected_locations}. '
                     'Check the country selection before using this file')
    output.sort(key=lambda item: item['country_as_gbd'])
    with args.output.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=output[0].keys())
        writer.writeheader()
        writer.writerows(output)
    manifest = {
        'source_url': args.source_url,
        'retrieved_on': args.retrieved_on,
        'input_path': str(args.input.resolve()),
        'input_sha256': sha256(args.input),
        'archive_path': str(args.archive.resolve()) if args.archive else None,
        'archive_sha256': sha256(args.archive) if args.archive else None,
        'input_rows': len(rows),
        'output_path': str(args.output.resolve()),
        'output_rows': len(output),
        'gbd_release': args.gbd_release,
        'selection': expected,
        'conversion': 'Rate per 100,000 divided by 100,000 to get population fraction',
        'location_check': 'Country/territory status and polygon join still require review',
    }
    args.output.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Validated {len(output)} locations; output: {args.output}')


if __name__ == '__main__':
    main()
