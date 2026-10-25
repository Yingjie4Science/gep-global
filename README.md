# Global GEP Urban Mental Health Service

This project estimates additional depression-related case equivalents under a
built-up-like counterfactual in which positive NDVI is set to zero. Results are
conditional model estimates, not observed diagnoses, verified causal effects, or
validated monetary savings.

## Current US results

**Direct-NDVI national production calculation (17 October 2026).** All 133 Earth
Engine batches completed with exactly 3,312 expected GUPPD city receipts for 49
states plus DC, including Alaska and excluding Hawaii. The result is **2.45
million** additional depressive-disorder case equivalents, with effect-estimate
limits of **0.71–4.63 million**, and an exploratory **$26.99 billion** 2019 USD
non-PPP societal-value proxy. See the [concise production
report](docs/evidence/us_direct_ndvi_production_run.md), [machine-readable
summaries](docs/evidence/data/us_direct_ndvi_2019_v1/), and [public Earth Engine
app](https://natcap-gep.projects.earthengine.app/view/us-urban-mental-health).

**Controlled original-method comparison.** On common population support, the
newly derived 2019 US urban GLC_FCS30D class lookup gives **2.43 million** case
equivalents under the production prevalence and health equation, **1.16% below**
direct NDVI nationally. City differences are often much larger. The configuration
closest to the original code choices—class lookup, fixed 5% prevalence and the
literal original equation—gives **2.18 million** and a **$24.00 billion** proxy.
See the [comparison](docs/evidence/us_direct_ndvi_production_run.md#controlled-comparison-of-the-modelling-choices)
and [validated outputs](docs/evidence/data/us_method_comparison_2019_v2_common/).

Varun confirmed that his supplied 35-class lookup was used in his run. A new
matched local sensitivity gives **1.68 million** case equivalents with his table
versus **2.46 million** with our US-derived table on identical 2019 GLC and
population support. This is a technical lookup comparison; the published
direct-NDVI result remains the primary estimate. His GUPPD layer, WorldPop mosaic and 2019 land-cover raster are now present.
The population cells match, while land-cover class assignments differ for
**11.35%** of population on cells valid in both sources. The crossed full runs
show **1.67 million** cases with his land cover and lookup under our GBD/current-reference
health settings; changing the raster alone shifts cases by less than 1% nationally,
while changing the lookup lowers cases by about 32%. See the [data guide](docs/DATA_SOURCES_AND_PREPROCESSING.md)
and [four-scenario evidence](docs/evidence/data/varun_2026_10/source_lookup_factorial_summary.json).
The [US cost comparison](docs/evidence/varun_us_cost_comparison.md) applies
Varun's rate, the current project proxy and a directly reported 2019 USD
adult-MDD rate from SNAPP to these same case outputs; all dollar totals are
conditional on their different cost definitions.

## Model workflow

The two exposure paths share the health calculation but estimate baseline NDVI
differently:

```text
2019 WorldPop + GUPPD cities
             │
             ├── production: sample annual-median 2019 Landsat NDVI
             │
             └── sensitivity: map 2019 GLC_FCS30D classes to fixed NDVI
                              values from an attribute table
             │
             ▼
set positive NDVI to zero in the counterfactual
             │
             ▼
OR → approximate RR using p0; calculate population case factor
             │
             ▼
apply matched 2019 prevalence; aggregate city → state → national
             │
             ▼
apply the labelled 2019 USD non-PPP cost proxy
```

For the local class-lookup code path:

1. Warp 2019 GLC_FCS30D classes to the WorldPop grid with nearest-neighbor
   resampling.
2. Assign one NDVI value to each class from the selected lookup table.
3. Set positive mapped NDVI to zero in the counterfactual; retain zero and
   negative values and do not change class codes.
4. Calculate `delta_NDVI = observed_NDVI - counterfactual_NDVI`.
5. Convert the Liu et al. (2023) OR per +0.1 NDVI to an approximate RR with
   `RR = OR / (1 - p0 + p0 × OR)`.
6. Calculate a pixel case factor at prevalence 1 as
   `population × (RR^(-10 × delta_NDVI) - 1)`.
7. Aggregate by urban polygon, multiply by matched 2019 prevalence, and then
   apply a reviewed cost rate.

The production workflow instead samples signed Landsat NDVI directly at native
WorldPop cell centres. The controlled comparison runs both exposure paths on the
same valid cells and independently varies prevalence and health equation.

## Health inputs and interpretation

The primary prevalence input is the locally validated IHME GBD 2023 table for
2019, both sexes, all ages, crude prevalence of depressive disorders. It matches
the all-age WorldPop denominator. The historical 5% WHO adult prevalence is an
explicit sensitivity only.

The default `p0 = 0.115` is the health-record depression-diagnosis proportion in
the lowest residential-NDVI quartile in Table 1 of [Hystad et al.
(2019)](https://pubmed.ncbi.nlm.nih.gov/33778335/). It is a transported Quebec
adult-cohort proxy for OR-to-RR conversion, not a GBD prevalence or measured
zero-NDVI risk. The project also retains 0.096 as a Hystad self-report scenario
and 0.03–0.20 as structural sensitivity. See the [decision
record](docs/DECISIONS_AND_TODOS.md) and [evidence
review](docs/evidence/liu_2023_ndvi_p0_review.md).

The reported 95% limits propagate only Liu et al.'s OR limits. They hold `p0`,
prevalence, population, exposure, model structure and costs fixed.

## Current data layout

The inventory is organized below by **scientific category**, so each source and
its prepared derivative remain together conceptually. Large files are physically
stored outside Git under `../data/urban_mental_health/` using provenance stages:
`raw/` for unchanged sources, `processed/` for prepared derivatives,
`manifests/` for traceability, and `pilots/` for run outputs. The stage folder
does not define the scientific category or imply that a file is model-ready.

| Main category | Source or raw record | Prepared or selected input | Current use and status |
| --- | --- | --- | --- |
| **Land cover and exposure** | GLC_FCS30D annual source tiles: `raw/glc_fcs30d/` ([Zenodo 15063683](https://zenodo.org/records/15063683)); Varun’s supplied 2019 mosaic: `raw/collaborator/varun_2026-10/lulc_glc_fcs30d_2019.tif`; direct NDVI: Earth Engine Landsat 7/8 | 2019 local tiles: `processed/lulc_2019_us/`; derived US lookup in `docs/evidence/data/us_method_comparison_2019_v2_common/` | Direct NDVI remains the production exposure. Both class rasters and both lookup tables have crossed US technical runs; owner mosaic and lookup generation remain to document. |
| **Population** | WorldPop record [75977](https://hub.worldpop.org/geodata/summary?id=75977) | `raw/worldpop/usa_pop_2019_CN_100m_R2025A_v1.tif` | Complete 2019 constrained R2025A count raster used in the published US run. Varun's global mosaic is available; all modeled US urban cell values and nodata statuses match the selected raster. |
| **Urban boundaries** | GUPPD v1 source: `raw/guppd/Urban_boundaries/` ([DOI](https://doi.org/10.7927/brq1-xc29)); Varun’s supplied global GeoPackage | `processed/guppd_us_excluding_hawaii.gpkg`; owner US subset `processed/varun_us_excluding_hawaii.gpkg` | 3,312 current versus 3,309 owner non-Hawaii polygons; the three current-only IDs carry zero modeled population. |
| **Health parameters** | Liu et al. effect evidence and IHME GBD Results | `processed/effect_size.xlsx`; `../depression_prevalence_review/gbd_2023_2019_depressive_disorders_country_prevalence.csv` | OR 0.931 with 95% CI 0.887–0.977; primary prevalence is 2019 both-sex all-age depressive disorders. `p0` remains a labelled transported parameter. |
| **Valuation** | Christensen source table and Varun's reference bundle | US proxy: `processed/data_cost_mental_health_US_2019_USD.csv`; conversion audit beside it | Published US values use the explicitly exploratory $10,999.206774 societal-cost proxy. Varun's 199-country workbook is user-confirmed as 2019 USD but still needs explicit non-PPP confirmation and a prediction ledger. |
| **Reproducibility records** | Acquisition and source manifests | `manifests/current_data_inventory_2026-10-21.json`; published evidence under `docs/evidence/data/` | Current file/hash register, validation receipts, run summaries and cleanup history. |

This organization separates four different states that should not be conflated:
an unchanged source, a prepared derivative, an input selected for a run, and an
output from that run. See [Data sources and
preprocessing](docs/DATA_SOURCES_AND_PREPROCESSING.md) for the category-specific
file register, source links, transformations, validation status and remaining
actions.

## Reproducing work

The published direct-NDVI national calculation ran in Earth Engine. Its batch
receipts, validation, summaries and checksums are versioned under
`docs/evidence/data/us_direct_ndvi_2019_v1/`; the cloud source is in
`Yingjie4Science/invest-gee/urban_mental_health/`.

`run_urban_mental_health.py` implements the local land-cover lookup path. It
accepts explicit paths for all inputs; use these flags with the current data
layout because its default filenames preserve Varun's historical folder layout:

```bash
python run_urban_mental_health.py \
  --land-cover /path/to/one_2019_categorical_land_cover_raster.tif \
  --population ../data/urban_mental_health/raw/worldpop/usa_pop_2019_CN_100m_R2025A_v1.tif \
  --ndvi-lookup /path/to/reviewed_lookup.csv \
  --effects ../data/urban_mental_health/processed/effect_size.xlsx \
  --urban-boundaries ../data/urban_mental_health/processed/guppd_us_excluding_hawaii.gpkg \
  --costs /path/to/reviewed_2019_usd_non_ppp_costs.xlsx \
  --country-prevalence-table ../depression_prevalence_review/gbd_2023_2019_depressive_disorders_country_prevalence.csv \
  --country-crosswalk config/us_country_crosswalk.csv \
  --project-dir /path/to/new_run
```

The 114 national land-cover tiles are intentionally kept tiled; a single dense
national raster spanning Alaska's antimeridian has not been created. Use the
tiled pilot and cloud workflows unless a reviewed regional mosaic strategy is
added. The Varun cost workbook is not used in the command above until its missing
non-PPP and model-provenance fields are resolved.

Use `--baseline-prevalence 0.05` for the explicitly labelled original-method
prevalence scenario instead of the country table; the 2019 GBD version remains
the primary run. The [controlled comparison](docs/evidence/us_direct_ndvi_production_run.md#controlled-comparison-of-the-modelling-choices)
already includes both on common US support. Use `--p0` for a
reference-risk sensitivity. Always use a fresh output directory when inputs change. `run_manifest.json` records parameters,
code revision and SHA-256 checksums; review machine paths before publication.

## Review gates

Before reporting a new run, verify:

- exposure and outcome definitions match the effect estimate;
- the GBD country join is complete and age denominators match WorldPop;
- `p0` transportability and sensitivity are reported;
- every populated land-cover code has one reviewed lookup value or is explicit
  nodata;
- polygon IDs and aggregation totals reconcile without double counting;
- every cost rate is auditable 2019 USD with `ppp_adjusted = FALSE` and a stated
  cost scope; and
- output limits are labelled as conditional on all inputs not propagated.
