# Reproduce and inspect the project

Run commands from the `gep-global` repository root.
The Git checkout moved here from `urban-mental-health-gep-fork/` on 27 October 2026.
Published receipts retain their original paths and commit hashes. Their
relative-path translation is in the [root migration record](../config/project_root_migration_2026-10-27.json);
keep the recorded hashes and source revisions when checking older results.
Start with the smallest workflow that answers the question; a cost comparison
does not require a raster rerun.
The [data guide](DATA_SOURCES_AND_PREPROCESSING.md) owns input provenance.
Older run records mentioning `../data/urban_mental_health/` now resolve to
`data/`; see the [data path migration](../config/data_layout_migration_2026-10-27.json).
The [run registry](../config/run_registry.json) locates outputs, and the
[task register](DECISIONS_AND_TODOS.md) records current decisions and owners.

## 1. Set up and check the checkout

```sh
conda env create -f environment.yml
conda activate urban-mental-health-gep
python -m pip install --no-deps --no-build-isolation -e .
python scripts/check_repository.py
python -m unittest discover -s tests -v
```

For an existing compatible environment, activate it and run the last three
commands. Use the editable install from this checkout: source hashing expects the repository
files to remain available. `pyproject.toml` installs the shared modules from `src/` and the
`umh-global` command; native geospatial dependencies are managed by Conda.
`environment.yml` is a dependency specification, not an exact historical lock.
[Runtime versions](../config/runtime_versions_2026-10-27.json) record the
installation used to check this reorganization. Historical runs have their own
code/input hashes; use their recorded commit for exact source reproduction.

If a Python virtual environment reuses Conda's geospatial packages, PROJ may
need the base environment's database path. Before a spatial audit, use:

```sh
export PROJ_DATA="$(python -c 'import sys; print(sys.base_prefix + "/share/proj")')"
test -f "$PROJ_DATA/proj.db"
```

This was required by the existing local pilot environment. A newly activated
Conda environment normally supplies its own PROJ data path.

`check_repository.py` is offline and uses only the Python standard library. It
checks layout, source syntax, links, the run registry and frozen evidence hashes.
The unit tests cover model formulas, input validation, feature-ID handling and
provenance. These checks do not validate the epidemiology or acquire data.

## 2. Locate inputs and select the workflow

```sh
DATA=data
GBD=data/processed/gbd_2023_2019_depressive_disorders_country_prevalence.csv
```

The raw GBD CSV and ZIP are in `data/raw/ihme_gbd_2023/`; the
validated table and saved import receipt are in `data/processed/` and
`data/manifests/`. The import script is `scripts/01_inputs/import_gbd_depressive_disorders.py`.
Use explicit paths if your checkout has a different parent layout. Large inputs
are not stored in Git. Keep original downloads and collaborator files under
`raw/`; derivatives under `processed/`; source/QA records under `manifests/`.
Full retained comparisons are under `outputs/`; older full runs are in the
verified `archive/` bundle. Historical receipts record original `pilots/` paths.
Use fresh output names for any new run. To inspect archived national or city files, list
`$DATA/archive/historical_pilots_through_2026-10-27.tar.gz`; extract into
`$DATA/archive/extracted/` when a historical script needs its original path.
The archive checksum and each preserved file hash are in
`$DATA/manifests/pilot_reorganization_2026-10-27.json`. Pick a new run-directory name whenever inputs or assumptions change.

| Goal | Inputs needed | Workflow and output |
| --- | --- | --- |
| Inspect published results | This Git checkout only | Read report and machine-readable evidence via the [run registry](../config/run_registry.json). |
| Recalculate US cost and area comparisons | Saved case summaries, owner cost workbook, sibling SNAPP tables and geometries | Section 3; writes small JSON audits. |
| Repeat local source/lookup calculations | Prepared GUPPD, WorldPop, verified tiles or owner mosaic, lookup, effect, GBD and cost tables | Section 4; full outputs in a fresh external run directory. |
| Recreate direct-NDVI production or cloud comparison | Companion cloud code, Earth Engine account/project and source assets | Section 5; versioned cloud receipts and exports. |
| Reproduce the original global workflow | Global rasters, boundaries, reviewed country prevalence and audited cost workbook | Section 6; owner-source gaps remain in the task register. |

## 3. Recalculate values and study areas

Choose a new output directory; plain `mkdir` deliberately fails if it exists:

```sh
REVIEW=$DATA/outputs/cost_area_review_v1
mkdir "$REVIEW"
python scripts/03_checks/compare_varun_us_cost.py   docs/evidence/data/varun_2026_10/source_lookup_factorial_summary.json   "$DATA/raw/collaborator/varun_2026-10/treatment_cost.xlsx"   "$REVIEW/varun_cost.json"
python scripts/03_checks/compare_snapp_us_cost.py   docs/evidence/data/varun_2026_10/source_lookup_factorial_summary.json   "$REVIEW/varun_cost.json"   ../SNAPP/docs/cost_studies.csv   ../SNAPP/docs/societal_cost_of_depression.md   "$REVIEW/snapp_cost.json"
python scripts/03_checks/audit_us_urban_area.py   "$DATA/processed/guppd_us_excluding_hawaii.gpkg"   "$DATA/processed/varun_us_excluding_hawaii.gpkg"   ../SNAPP/data/national/counties.gpkg   ../SNAPP/config/regions.csv   "$REVIEW/study_areas.json"
```

Check rates, unchanged case totals, endpoint/currency caveats and source hashes
against the [published comparison](evidence/varun_us_cost_comparison.md).
Paths in a new receipt can differ from the historical receipt without changing
numerical results; compare both values and hashes. SNAPP's full county footprint
and GUPPD's urban footprint measure different geographic domains.

## 4. Run a local national lookup sensitivity

The default scope is now the 48 contiguous states plus DC. Prepare the new
boundaries once with `python scripts/01_inputs/prepare_contiguous_us_boundaries.py "$DATA"`.
It refuses to overwrite an existing derivative. Historical recipes retain the
non-Hawaii inputs and include Alaska; for close historical reproduction pass
`--urban-boundaries "$DATA/processed/guppd_us_excluding_hawaii.gpkg"` explicitly.
Use `processed/varun_us_contiguous.gpkg` for new owner-source comparisons.

The acquisition is already complete for the current data copy. For new data,
follow the acquisition, extraction and QA steps in the data guide before running.
The tile runner reads only intersecting windows and rejects reused output folders.
For a bounded check, use San Francisco (`30_12257`) or Minneapolis (`30_12427`);
the current two-city orchestration writes under `outputs/sf_minneapolis_2019_v1/`.

```sh
RUN=$DATA/outputs/us_lookup_review_v1
python scripts/02_models/run_us_national_technical.py "$DATA" "$RUN"   --lookup docs/evidence/data/us_method_comparison_2019_v2_common/glc_fcs30d_attribute_table_us_2019.csv   --effects "$DATA/processed/effect_size.xlsx"   --prevalence "$GBD"   --crosswalk config/us_country_crosswalk.csv   --cost "$DATA/processed/data_cost_mental_health_US_2019_USD.csv"
```

Inspect `run_record.json`, `national_summary.json`,
`urban_feature_results.csv` and `class_population_summary.csv`. Require no shared
population-cell double counting, explicit missing support, finite values,
ordered conditional limits and reconciled city-to-national totals. Confirm the
intended inputs and hashes before interpreting the result.

To repeat all four source/lookup combinations, follow the exact variants in the
[collaborator comparison recipe](evidence/data/varun_2026_10/README.md). It changes
`--lookup`, `--land-cover-mosaic`, `--population-raster` and `--urban-boundaries`
while keeping the declared health inputs fixed. Its five-percent/original-equation
analytical sensitivities are not additional raster runs.

**Recovery:** incomplete model output folders are not resumable caches. Keep
failed receipts for diagnosis and choose a new run name. Acquisition scripts
can resume their recorded per-tile downloads; inspect manifests and run the
independent verification before accepting them. Do not regenerate an old receipt
in place merely to update a path or date.

## 5. Reproduce cloud production and render a report

Cloud code lives in [invest-gee/urban_mental_health](https://github.com/Yingjie4Science/invest-gee/tree/main/urban_mental_health).
Use the published batch manifests' source revision, asset snapshots and graph
hashes. Earth Engine authentication and a registered project are required.
Follow that repository's deployment/release instructions; do not infer that
current live assets reproduce a historical result. This checkout's
`scripts/01_inputs/derive_glc_ndvi_2019_gee.js` is the early lookup adaptation, not the
complete national production graph.

Render the saved direct-NDVI report to a scratch output without overwriting the
published report:

```sh
REPORT=$DATA/outputs/report_review_v1
mkdir "$REPORT"
python scripts/04_reports/render_us_direct_ndvi_report.py   docs/evidence/data/us_direct_ndvi_2019_v1/national_summary.json   docs/evidence/data/us_direct_ndvi_2019_v1/state_summary.csv   "$REPORT/direct_ndvi_report.md"   --comparison-summary docs/evidence/data/us_method_comparison_2019_v2_common/national_comparison.json   --comparison-scenarios docs/evidence/data/us_method_comparison_2019_v2_common/scenario_comparison.csv   --lookup-table docs/evidence/data/us_method_comparison_2019_v2_common/glc_fcs30d_attribute_table_us_2019.csv   --lookup-manifest docs/evidence/data/us_method_comparison_2019_v2_common/lookup_manifest.json
```

This creates a review copy; optional historical technical diagnostics require the
additional arguments shown by `--help`. Relative links in a published copy must
resolve from `docs/evidence/`, where the existing report lives.

## 6. Global workflow and scientific acceptance

The original-style global driver is now `src/run_urban_mental_health.py`
(or installed command `umh-global`). Run `umh-global --help` and supply explicit
`--land-cover`, `--population`, `--ndvi-lookup`, `--effects`, `--urban-boundaries`,
`--costs`, `--country-prevalence-table`, `--country-crosswalk` and `--project-dir`.
Its built-in defaults retain the owner's historical layout. Country cost rows
must declare 2019 USD and `ppp_adjusted=False`; the supplied owner workbook has
not passed that provenance gate. Country-specific prevalence and an explicit
scalar `--baseline-prevalence 0.05` are mutually exclusive.

Before releasing any new model result, verify outcome/denominator compatibility,
exposure support, `p0` and reference state, aggregation, cost basis and uncertainty
scope. Record source code, inputs, parameters and output hashes. Do not replace
primary results with sensitivities without a recorded scientific decision.

## 7. Publish and maintain

1. Validate the new receipt and compare it with the relevant historical run.
2. Put only small, reviewed results in `docs/evidence/`; leave source rasters and local outputs outside Git.
3. Add the completed run to `config/run_registry.json`; update current tasks once in `DECISIONS_AND_TODOS.md`.
4. Verify report links, labels and numerical reconciliation, then rerun repository checks and unit tests.
5. Review the staged diff and commit in coherent stages (code, evidence, documentation). Push only under the user's current publication authorization.

The frozen evidence checksum list is a preservation baseline for the 27 October
reorganization. A future intentional update to published outputs must update its
entry with a reviewable reason; it is not an invitation to recompute historical
receipts against changed inputs.

## Script catalog

Use `--help` for arguments. Acquisition and model scripts can consume substantial
network, disk or cloud resources; they are never launched by the offline checker.

| Stage / script | Purpose and status |
| --- | --- |
| `01_inputs/fetch_glc_fcs30d_us.py` | National tile queue and resumable extraction; active. |
| `01_inputs/fetch_glc_fcs30d_tile.py` | Single-tile ZIP-range helper, used by national downloader. |
| `01_inputs/download_with_ranges.py` | Generic resumable download utility. |
| `01_inputs/prepare_guppd_us.py` | Prepare US GUPPD selection excluding Hawaii. |
| `01_inputs/prepare_varun_us_boundaries.py` | Preserve owner geometry while preparing the same non-Hawaii selection. |
| `01_inputs/prepare_local_pilot.py` | Prepare bounded native-grid city inputs. |
| `01_inputs/import_gbd_depressive_disorders.py` | Validate a fresh IHME GBD export and record query and checksums. |
| `01_inputs/extract_who_depression_2015.py` | Reproduce the older WHO country table for historical comparison. |
| `01_inputs/convert_costs_2019_usd.py` | Explicit PPP reversal/inflation/market-FX audit; source caveats remain. |
| `scripts/01_inputs/derive_glc_ndvi_2019_gee.js` | Historical GEE lookup adaptation; use companion code for national production. |
| `01_inputs/build_pooled_us_lookup.py` | Exploratory lookup pooled from explicitly supplied regional tables; superseded for production. |
| `01_inputs/monitor_us_local_completion.py` | Historical acquisition monitor; no monitor is required for completed inputs. |
| `02_models/run_local_pilot.py` | Bounded local health calculation. |
| `02_models/run_expanded_city_tests.py` | Two-city San Francisco/Minneapolis local/GEE test orchestration; cloud credentials needed. |
| `02_models/run_us_national_technical.py` | Active windowed national lookup runner. |
| `03_checks/check_us_boundaries.py` | Polygon validity, duplication and overlap inspection. |
| `03_checks/check_us_land_cover_coverage.py` | Native WorldPop-cell land-cover support. |
| `03_checks/verify_land_cover_acquisition.py` | Independently verify downloaded/extracted rasters. |
| `03_checks/validate_zenodo_lookup_city_grids.py` | Matched local/GEE city-grid and formula check. |
| `03_checks/audit_varun_inputs.py` | Owner table, boundary and input review. |
| `03_checks/check_varun_landcover.py` | Compare both categorical sources at population cells. |
| `03_checks/check_varun_population_mosaic.py` | Compare population counts and nodata on urban support. |
| `03_checks/audit_us_urban_area.py` | Dissolved local, owner and SNAPP footprints and ID checks. |
| `03_checks/compare_pilot_results.py` | Pilot raster diagnostics and comparison. |
| `03_checks/summarize_varun_lookup_runs.py` | Two matched local lookup runs. |
| `03_checks/summarize_varun_factorial.py` | Four source/lookup runs and analytical sensitivities. |
| `03_checks/compare_varun_us_cost.py` | Owner versus project rates on saved cases. |
| `03_checks/compare_snapp_us_cost.py` | Add the explicit 2019-dollar SNAPP MDD sensitivity. |
| `04_reports/render_us_direct_ndvi_report.py` | Render published-summary evidence as Markdown. |
| `04_reports/plot_lookup_comparison.py` | Compare the US-derived and Varun land-cover-to-NDVI tables; write the paired CSV, summary and figure. |

Paths in this catalog are under `scripts/`. Shared model modules live in `src/`;
`run_provenance.py` records source/input/output hashes and `vector_attributes.py`
preserves nonsequential feature IDs. The [migration map](../config/layout_migration_2026-10-27.json)
resolves previous script locations.
