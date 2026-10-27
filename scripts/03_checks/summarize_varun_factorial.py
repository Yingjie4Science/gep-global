"""Summarize four saved US class-lookup runs without changing their inputs.

The owner-raster runs use the supplied urban layer and population mosaic.
The local-tile runs use the current US derivatives. Audits establish that the
population values agree on every active US urban cell and the three extra
current polygons carry zero modeled population. Results therefore describe a
technical source sensitivity, not a validation of either raster or lookup.
"""
import argparse
import csv
import json
import math
from pathlib import Path


def read_run(path):
    path = Path(path)
    summary = json.loads((path / "national_summary.json").read_text())
    record = json.loads((path / "run_record.json").read_text())
    with (path / "urban_feature_results.csv").open(newline="") as source:
        rows = {row["region_id"]: row for row in csv.DictReader(source)}
    return summary, record, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("local_us_lookup", type=Path)
    parser.add_argument("local_varun_lookup", type=Path)
    parser.add_argument("owner_us_lookup", type=Path)
    parser.add_argument("owner_varun_lookup", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    paths = {
        "local_landcover_us_lookup": args.local_us_lookup,
        "local_landcover_varun_lookup": args.local_varun_lookup,
        "varun_landcover_us_lookup": args.owner_us_lookup,
        "varun_landcover_varun_lookup": args.owner_varun_lookup,
    }
    runs = {key: read_run(path) for key, path in paths.items()}
    common_ids = set.intersection(*(set(run[2]) for run in runs.values()))
    if len(common_ids) != 3309:
        raise AssertionError(f"Expected 3,309 owner US IDs, found {len(common_ids)}")
    current_only = set(runs["local_landcover_us_lookup"][2]) - common_ids
    if len(current_only) != 3:
        raise AssertionError(f"Expected three zero-population current-only IDs, found {current_only}")
    for key in ("local_landcover_us_lookup", "local_landcover_varun_lookup"):
        for region_id in current_only:
            row = runs[key][2][region_id]
            if float(row["population_total"]) != 0 or float(row["additional_cases"]) != 0:
                raise AssertionError(f"Current-only {region_id} has modeled population or cases")

    columns = ("population_total", "population_modelled", "additional_cases",
               "additional_cases_lower", "additional_cases_upper",
               "additional_cases_value_2019_usd_proxy")
    scenarios = {}
    for key, (summary, record, rows) in runs.items():
        totals = summary["totals"]
        for column in columns:
            matched = math.fsum(float(rows[region_id][column]) for region_id in common_ids)
            if not math.isclose(matched, totals[column], rel_tol=1e-10, abs_tol=1e-5):
                raise AssertionError(f"{key} {column} does not reconcile")
        scenarios[key] = {
            "feature_count": summary["feature_count"],
            "common_feature_count": len(common_ids),
            "population_total": totals["population_total"],
            "population_modelled": totals["population_modelled"],
            "population_source_fill": totals["population_source_fill"],
            "additional_cases": totals["additional_cases"],
            "effect_lower": totals["additional_cases_lower"],
            "effect_upper": totals["additional_cases_upper"],
            "value_2019_usd_societal_proxy": totals["additional_cases_value_2019_usd_proxy"],
            "prevalence": summary["parameters"]["prevalence"],
            "p0": summary["parameters"]["p0"],
            "input_sha256": record["input_sha256"],
            "run_output_sha256": record["output_sha256"],
        }
    for key, scenario in scenarios.items():
        if not math.isclose(scenario["population_total"], 194367282.999126, abs_tol=.01):
            raise AssertionError(f"{key} has unexpected population support")
        if not math.isclose(scenario["prevalence"], .0424332878, abs_tol=1e-12):
            raise AssertionError(f"{key} has unexpected prevalence")
        if not math.isclose(scenario["p0"], .115, abs_tol=1e-12):
            raise AssertionError(f"{key} has unexpected p0")

    def pct(new, base):
        return 100 * (new / base - 1)

    def cases(key):
        return scenarios[key]["additional_cases"]

    contrasts = {
        "varun_lookup_minus_us_lookup_percent_on_local_landcover": pct(cases("local_landcover_varun_lookup"), cases("local_landcover_us_lookup")),
        "varun_lookup_minus_us_lookup_percent_on_varun_landcover": pct(cases("varun_landcover_varun_lookup"), cases("varun_landcover_us_lookup")),
        "varun_landcover_minus_local_percent_with_us_lookup": pct(cases("varun_landcover_us_lookup"), cases("local_landcover_us_lookup")),
        "varun_landcover_minus_local_percent_with_varun_lookup": pct(cases("varun_landcover_varun_lookup"), cases("local_landcover_varun_lookup")),
    }

    # The 5% and literal-original rows are algebraic re-evaluations of the
    # saved per-class population totals, not additional full raster runs.
    owner_summary, _, _ = runs["varun_landcover_varun_lookup"]
    rr = .931 / (1 - .115 + .115 * .931)
    with (args.owner_varun_lookup / "class_population_summary.csv").open(newline="") as source:
        class_rows = list(csv.DictReader(source))
    def class_cases(prevalence, literal):
        total = 0.0
        for row in class_rows:
            if row["lookup_status"] != "represented":
                if float(row["feature_row_population"]) != 0:
                    raise AssertionError("Unsupported population in owner run")
                continue
            exposure = max(0.0, float(row["lc_ndvi"]))
            factor = 1 - rr ** (10 * exposure) if literal else rr ** (-10 * exposure) - 1
            total += float(row["feature_row_population"]) * prevalence * factor
        return total
    if not math.isclose(class_cases(.0424332878, False), owner_summary["totals"]["additional_cases"], rel_tol=1e-10):
        raise AssertionError("Class-population reconstruction failed")
    sensitivities = {
        "varun_landcover_varun_lookup_fixed_5_percent_current_reference": class_cases(.05, False),
        "varun_landcover_varun_lookup_gbd_literal_original": class_cases(.0424332878, True),
        "varun_landcover_varun_lookup_fixed_5_percent_literal_original": class_cases(.05, True),
    }
    output = {
        "status": "four_full_us_technical_runs_and_three_analytic_health_sensitivities",
        "scope": "2019 US non-Hawaii, owner and local categorical land cover crossed with owner and US-derived lookup. Full runs hold GBD US all-age prevalence, p0, OR, current-reference health equation, and exploratory US cost proxy fixed.",
        "comparability": "Owner runs use 3309 owner polygons, owner population and land-cover mosaics; local runs use 3312 current polygons, current US population and Zenodo 2019 tiles. Audits confirm equal population cell values on active support, and the three current-only IDs have zero modeled population and cases. Source fill differs by 459.093 people.",
        "scenarios": scenarios,
        "contrasts": contrasts,
        "analytic_sensitivities": sensitivities,
        "limits": "Effect lower/upper values are conditional 95% OR limits only. Neither land-cover nor lookup is independently validated by this comparison. Monetary values use a broad US societal proxy, not Varun's cost workbook.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"contrasts": contrasts, "analytic_sensitivities": sensitivities}, indent=2))


if __name__ == "__main__":
    main()
