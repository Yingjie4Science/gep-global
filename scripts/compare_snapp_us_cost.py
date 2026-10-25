"""Apply the SNAPP Greenberg-2019 US cost anchor to four saved case runs.

Usage: python scripts/compare_snapp_us_cost.py FACTORIAL_JSON EXISTING_COST_JSON
       SNAPP_COST_STUDIES_CSV SNAPP_NOTE_MD OUTPUT_JSON

This is valuation postprocessing. It does not rerun or change cases.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


DOI = '10.1007/s12325-023-02622-x'
PAPER_URL = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC10499687/'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ('factorial_json', 'existing_cost_json', 'snapp_studies_csv',
                     'snapp_note_md', 'output_json'):
        parser.add_argument(argument, type=Path)
    args = parser.parse_args()
    factorial = json.loads(args.factorial_json.read_text())['scenarios']
    earlier = json.loads(args.existing_cost_json.read_text())
    with args.snapp_studies_csv.open(newline='') as source:
        rows = list(csv.DictReader(source))
    matches = [row for row in rows if row['doi'].lower() == DOI.lower()]
    if len(matches) != 1:
        raise ValueError('Expected exactly one Greenberg 2019 source row')
    selected = matches[0]
    note = args.snapp_note_md.read_text()
    if (selected['base_year'] != '2019'
            or '2019 USD' not in selected['notes']
            or '$16,854 (2019$)' not in note):
        raise ValueError('SNAPP source does not establish the 2019-dollar rate')
    snapp_rate = float(selected['per_case_reported_usd'])
    if not math.isclose(snapp_rate, 16854.0):
        raise ValueError('Unexpected reported per-case rate')
    prior_rates = earlier['costs']
    project_rate = prior_rates['project_exploratory_us_societal_proxy_per_case_2019_usd_non_ppp']
    varun_rate = prior_rates['varun_workbook_us_row_per_case_user_confirmed_2019_usd_ppp_status_unverified']
    out = {
        'status': 'three_cost_rate_postprocessing_comparison_on_four_unchanged_us_case_runs',
        'scope': '2019 non-Hawaii US technical case equivalents; GBD all-age depressive-disorders endpoint; no case model rerun',
        'sources': {
            'factorial_summary_sha256': sha256(args.factorial_json),
            'existing_cost_comparison_sha256': sha256(args.existing_cost_json),
            'snapp_cost_studies_sha256': sha256(args.snapp_studies_csv),
            'snapp_cost_note_sha256': sha256(args.snapp_note_md),
            'snapp_study_doi': DOI,
            'primary_paper_url': PAPER_URL,
            'snapp_study_row': selected,
        },
        'rates_per_case_usd': {
            'varun_conditional_2019_usd_ppp_and_scope_unverified': varun_rate,
            'project_exploratory_2019_usd_non_ppp_mood_disorders_proxy': project_rate,
            'snapp_greenberg_adult_mdd_incremental_societal_2019_usd': snapp_rate,
        },
        'comparison': {},
        'limitations': [
            'SNAPP/Greenberg rate is annual incremental societal cost per US adult with MDD, while modeled cases use all-age GBD depressive-disorders prevalence. Endpoint and age denominator differ.',
            'Varun workbook is user-labelled 2019 USD; PPP status and cost components are not embedded. Cost constructs may differ.',
            'The SNAPP 2024 pooled value is excluded because the project reports 2019 USD; its documentation also differs from the script output due to component shares summing to 100.2%.',
            'Multiplying case equivalents by cost per prevalent case is a valuation sensitivity, not a measured causal reduction in spending.'
        ],
    }
    for key, run in factorial.items():
        earlier_run = earlier['scenarios'][key]
        cases = run['additional_cases']
        for name, other in (
            ('project', earlier_run['project_cost_value_usd']),
            ('varun', earlier_run['varun_cost_value_usd_conditional']),
        ):
            expected = cases * (project_rate if name == 'project' else varun_rate)
            if not math.isclose(other, expected, abs_tol=0.01):
                raise AssertionError(f'{key}: previous {name} valuation does not reconcile')
        out['comparison'][key] = {
            'case_equivalents_unchanged': cases,
            'effect_lower_unchanged': run['effect_lower'],
            'effect_upper_unchanged': run['effect_upper'],
            'varun_value_usd_conditional': cases * varun_rate,
            'project_value_usd_exploratory': cases * project_rate,
            'snapp_value_usd_conditional': cases * snapp_rate,
            'snapp_effect_lower_value_usd_conditional': run['effect_lower'] * snapp_rate,
            'snapp_effect_upper_value_usd_conditional': run['effect_upper'] * snapp_rate,
        }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(out, indent=2) + '\n')


if __name__ == '__main__':
    main()
