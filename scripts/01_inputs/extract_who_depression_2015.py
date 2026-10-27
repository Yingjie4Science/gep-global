import csv
import argparse
import re
from pathlib import Path

import pdfplumber

parser = argparse.ArgumentParser(description='Extract WHO 2015 country depression rates from the 2017 report appendix')
parser.add_argument('--pdf', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
ROW = re.compile(r'^(.+?)\s+(\d[\d ]*)\s+(\d+,\d)%\s+(\d[\d ]*)\s+(\d+,\d)%')
CONTINUED = {
    'Democratic Republic': 'Democratic Republic of the Congo',
    'United Republic of': 'United Republic of Tanzania',
    'Bolivia (Plurinational': 'Bolivia (Plurinational State of)',
    'Saint Vincent and the': 'Saint Vincent and the Grenadines',
    'United States of': 'United States of America',
    'Venezuela (Bolivarian': 'Venezuela (Bolivarian Republic of)',
    'Bosnia and': 'Bosnia and Herzegovina',
    'The former Yugoslav': 'The former Yugoslav Republic of Macedonia',
    "Democratic People's": "Democratic People's Republic of Korea",
    "Lao People's": "Lao People's Democratic Republic",
    'Micronesia (Federated': 'Micronesia (Federated States of)',
}

rows = []
region = None
with pdfplumber.open(args.pdf) as pdf:
    for page_number in range(19, 24):
        text = pdf.pages[page_number - 1].extract_text()
        for line in text.splitlines():
            if line.startswith('WHO ') and 'Region' in line:
                region = line.replace(' (cont.)', '')
                continue
            match = ROW.match(line)
            if match:
                name, cases, prevalence, _, _ = match.groups()
                rows.append({
                    'country_as_published': CONTINUED.get(name.strip(), name.strip()),
                    'year': 2015,
                    'depressive_disorders_prevalence_percent': prevalence.replace(',', '.'),
                    'depressive_disorders_prevalence_fraction': f'{float(prevalence.replace(",", "."))/100:.3f}',
                    'depressive_disorders_cases': int(cases.replace(' ', '')),
                    'source_page': page_number,
                    'who_region_as_published': region,
                })

assert len(rows) >= 170, len(rows)
assert len(rows) == 183, len(rows)
assert len(set(row['country_as_published'] for row in rows)) == len(rows)
with args.output.open('w', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print(len(rows), 'rows written to', args.output)
print('Bhutan:', next((row for row in rows if row['country_as_published'] == 'Bhutan'), None))
