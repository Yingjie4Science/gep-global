"""Pool raw 2019 lookup sums from explicitly supplied reviewed AOIs.

This creates an exploratory multi-region lookup for a nationwide technical run.
It is not a production US lookup or a validation against local Zenodo classes.
"""
import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data_root', type=Path)
    parser.add_argument('output_dir', type=Path)
    parser.add_argument('--lookup', type=Path, action='append', required=True,
                        help='Reviewed regional lookup CSV; repeat for each region')
    args = parser.parse_args()
    sources = args.lookup
    if len(sources) < 2 or not all(path.is_file() for path in sources):
        raise FileNotFoundError(f'Expected at least two completed lookup tables, found {sources}')

    grouped = defaultdict(list)
    source_records = []
    for path in sources:
        rows = list(csv.DictReader(path.open(newline='')))
        source_records.append({
            'relative_path': str(path.relative_to(args.data_root)),
            'sha256': sha256(path),
            'region': path.parents[1].name,
        })
        for row in rows:
            valid_area = float(row.get('valid_area_m2') or 0)
            if valid_area > 0 and row.get('lc_ndvi') not in (None, ''):
                grouped[int(row['lc_code'])].append(row)

    output_rows = []
    for code, rows in sorted(grouped.items()):
        valid_area = sum(float(row['valid_area_m2']) for row in rows)
        ndvi_sum = sum(float(row['ndvi_area_sum']) for row in rows)
        ndvi2_sum = sum(float(row['ndvi2_area_sum']) for row in rows)
        class_area = sum(float(row['class_area_m2']) for row in rows)
        means = [float(row['lc_ndvi']) for row in rows]
        mean = ndvi_sum / valid_area
        variance = max(0.0, ndvi2_sum / valid_area - mean * mean)
        output_rows.append({
            'lc_code': code,
            'lc_desc': rows[0]['lc_desc'],
            'lc_ndvi': mean,
            'pooled_ndvi_sd': math.sqrt(variance),
            'region_mean_min': min(means),
            'region_mean_max': max(means),
            'contributing_regions': len(rows),
            'valid_area_m2': valid_area,
            'class_area_m2': class_area,
            'valid_area_fraction': valid_area / class_area if class_area else None,
            'ndvi_area_sum': ndvi_sum,
            'ndvi2_area_sum': ndvi2_sum,
            'year': 2019,
            'temporal_statistic': 'annual median of valid 2019 Landsat 7 and 8 NDVI',
            'spatial_statistic': 'area-weighted pooled mean across explicitly supplied bounded test AOIs',
            'status': 'exploratory_multiregion_technical_lookup',
        })

    coverage_path = args.data_root / 'manifests/us_local_qc_2019_v1/city_land_cover_coverage.csv'
    observed = set()
    with coverage_path.open(newline='') as source:
        for row in csv.DictReader(source):
            observed.update(int(value) for value in row['observed_classes'].split('|') if value)
    represented = {row['lc_code'] for row in output_rows}

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / 'pooled_lookup_candidate.csv'
    with csv_path.open('w', newline='') as target:
        writer = csv.DictWriter(target, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    evidence = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'scientific_status': (
            'Exploratory pooled-region lookup for a nationwide technical run; '
            'not a production US lookup and not validated against the local Zenodo classification snapshot.'
        ),
        'pooling_rule': 'Sum raw NDVI-area, squared-NDVI-area, valid-area and class-area terms; never average region means equally.',
        'landsat_method': '2019 merged Landsat 7/8 annual pixel median; minimum three valid observations; EPSG:6933 at 30 m.',
        'class_map_used_for_derivation': 'Earth Engine community GLC_FCS30D annual b20.',
        'sources': source_records,
        'lookup_sha256': sha256(csv_path),
        'represented_national_urban_classes': sorted(observed & represented),
        'unrepresented_national_urban_classes': sorted(observed - represented),
        'decision': 'Unrepresented classes remain missing; no class receives zero NDVI by default.',
    }
    (args.output_dir / 'pooled_lookup_evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps({
        'lookup': str(csv_path),
        'rows': len(output_rows),
        'unrepresented_national_urban_classes': evidence['unrepresented_national_urban_classes'],
        'sha256': evidence['lookup_sha256'],
    }, indent=2))


if __name__ == '__main__':
    main()
