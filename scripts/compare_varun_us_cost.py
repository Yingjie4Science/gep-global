"""Revalue four saved US technical runs at Varun's supplied US cost rate.

Usage: python scripts/compare_varun_us_cost.py SCENARIO_JSON COST_XLSX OUTPUT_JSON
This changes valuation only; cases and conditional OR limits are copied from
the four saved runs. The owner workbook does not document PPP status or scope.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('scenario_json', type=Path)
    p.add_argument('cost_xlsx', type=Path)
    p.add_argument('output_json', type=Path)
    a = p.parse_args()
    scenarios = json.loads(a.scenario_json.read_text())['scenarios']
    table = pd.read_excel(a.cost_xlsx)
    if list(table.columns) != ['country', 'cost_per_case'] or len(table) != 199:
        raise ValueError('Unexpected owner cost workbook schema or country count')
    row = table.loc[table.country == 'United States']
    if len(row) != 1:
        raise ValueError('Expected exactly one United States row')
    owner_cost = float(row.iloc[0].cost_per_case)
    current_cost = 10999.206774445318
    output = {
        'status': 'cost_only_postprocessing_comparison_not_new_case_model_run',
        'scope': 'Same four 2019 US non-Hawaii technical case runs; only cost per case changes.',
        'source_sha256': {str(a.scenario_json): sha(a.scenario_json), str(a.cost_xlsx): sha(a.cost_xlsx)},
        'costs': {
            'project_exploratory_us_societal_proxy_per_case_2019_usd_non_ppp': current_cost,
            'varun_workbook_us_row_per_case_user_confirmed_2019_usd_ppp_status_unverified': owner_cost,
            'owner_minus_project_per_case_percent': 100 * (owner_cost / current_cost - 1),
        },
        'scenarios': {},
        'interpretation': 'Case counts and OR-only effect limits are unchanged. The two rates may measure different cost constructs. Varun workbook is user-confirmed as 2019 USD, but does not itself record currency year, PPP status, cost components, or country estimation ledger. Varun-valued totals are conditional illustrations, not approved non-PPP production values or treatment savings.',
    }
    for name, row in scenarios.items():
        cases = row['additional_cases']
        project_value = row['value_2019_usd_societal_proxy']
        if abs(project_value / cases - current_cost) > 1e-7:
            raise AssertionError(f'Current cost did not reconcile for {name}')
        output['scenarios'][name] = {
            'case_equivalents_unchanged': cases,
            'effect_lower_unchanged': row['effect_lower'],
            'effect_upper_unchanged': row['effect_upper'],
            'project_cost_value_usd': project_value,
            'varun_cost_value_usd_conditional': cases * owner_cost,
            'varun_cost_effect_lower_value_usd_conditional': row['effect_lower'] * owner_cost,
            'varun_cost_effect_upper_value_usd_conditional': row['effect_upper'] * owner_cost,
            'difference_usd': cases * owner_cost - project_value,
        }
    a.output_json.parent.mkdir(parents=True, exist_ok=True)
    a.output_json.write_text(json.dumps(output, indent=2) + '\n')


if __name__ == '__main__':
    main()
