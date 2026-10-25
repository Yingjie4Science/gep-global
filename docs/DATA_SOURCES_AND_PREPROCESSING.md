# Urban mental health data sources and preprocessing

Last updated: 21 October 2026. The active US scope is 49 states plus DC,
including Alaska and excluding Hawaii and US territories.

## Data folder structure

The Git repository and data folder are siblings under `gep-global/`. The active
US data are in `../data/urban_mental_health/` relative to this repository:

```text
data/urban_mental_health/
├── raw/                 original downloads and collaborator-supplied files
│   ├── glc_fcs30d/      114 annual land-cover source tiles
│   ├── worldpop/        complete 2019 US population raster
│   ├── guppd/           original urban-boundary package
│   ├── cost_conversion/ saved exchange-rate and price-index inputs
│   └── collaborator/varun_2026-10/  unchanged land cover, lookup, population, boundaries and costs
├── processed/           prepared inputs and historical source files
│   └── lulc_2019_us/    114 one-band 2019 land-cover tiles
├── manifests/           source, checksum, processing and validation records
└── pilots/              local tests and diagnostic outputs
```

The 2019 GBD prevalence table is in the sibling
`../depression_prevalence_review/` folder. Small published results are tracked
inside this repository at `docs/evidence/data/`. The folder name describes a
file's history, not its scientific role or approval status. For example,
`processed/data_cost_mental_health.csv` retains a historical path but is an
unchanged, 2018 PPP-labelled source table; it is not a validated model cost.

Keep originals unchanged, record transformations in `manifests/`, and give
each run a fresh output directory. The current file and checksum register is
`manifests/current_data_inventory_2026-10-21.json`; it supersedes the 16 October
pilot inventory. The 21 October partial-download cleanup is recorded in
`manifests/data_cleanup_2026-10-21.json`.

## Current input inventory

This register traces each input from source to selected derivative. Paths under
`raw/`, `processed/`, `manifests/` and `pilots/` are relative to the data folder
above; `docs/` paths are relative to this repository. The sections that follow
give the source links, processing choices, checks and unresolved provenance.

| Category | Source location | Selected derivative or parameter | Provenance record |
| --- | --- | --- | --- |
| **Land cover** | `raw/glc_fcs30d/` ([Zenodo](https://zenodo.org/records/15063683)); Varun’s supplied 2019 global mosaic under `raw/collaborator/varun_2026-10/` | `processed/lulc_2019_us/` (band 20 of 114 annual tiles); owner mosaic retained unchanged | `manifests/glc_us_tiles/`; [source comparison](evidence/data/varun_2026_10/land_cover_us_urban_cell_audit.json); [processing details](#1-land-cover) |
| **NDVI exposure** | Landsat 7/8 in Earth Engine; Varun's confirmed run lookup in `raw/collaborator/varun_2026-10/` | Direct 2019 NDVI in Earth Engine; derived lookup in `docs/evidence/data/us_method_comparison_2019_v2_common/` | Published batch evidence and collaborator-file checksums; [method details](#2-ndvi-exposure-inputs) |
| **Population** | Current US [WorldPop](https://hub.worldpop.org/geodata/summary?id=75977) raster; Varun's supplied mosaic under `raw/collaborator/varun_2026-10/worldpop/` | US raster used directly; mosaic retained for reproduction tests | `raw/worldpop/README.md` and current inventory manifest; [grid and comparison](#3-population) |
| **Urban boundaries** | [GUPPD](https://doi.org/10.7927/brq1-xc29) source in `raw/guppd/`; Varun's prepared GeoPackage in `raw/collaborator/varun_2026-10/` | `processed/guppd_us_excluding_hawaii.gpkg` | Owner-layer comparison in [review evidence](evidence/data/varun_2026_10/urban_boundaries_audit.json); [selection details](#4-urban-polygons) |
| **Health parameters** | `processed/effect_size.xlsx`; GBD export in `../depression_prevalence_review/` | Liu et al. OR, 2019 all-age country prevalence, and separately declared `p0` | GBD import manifest and model run manifest; [definitions](#5-health-inputs) |
| **Valuation** | `processed/data_cost_mental_health.csv`; Varun's workbook in `raw/collaborator/varun_2026-10/` | `processed/data_cost_mental_health_US_2019_USD.csv` with conversion audit | `manifests/cost_conversion_2019_usd.json`; [cost basis and limits](#6-costs-and-valuation) |

Varun's land-cover and population mosaics, prepared urban layer, and confirmed
run lookup are now present. The US audits below separate measured input differences
from lookup-generation and cost-provenance questions. Source files remain unchanged.

## 1. Land cover

**Source.** Liu, Zhang and Li, *GLC_FCS30D: the first global 30-m
land-cover dynamic monitoring product with fine classification system from 1985
to 2022*, v2, DOI `10.5281/zenodo.15063683`. The community Earth Engine copy is
documented in the [GLC_FCS catalog](https://gee-community-catalog.org/projects/glc_fcs/).
Identity between every community asset pixel and the locally downloaded Zenodo
v2 tiles has not been established, so the source used by each workflow is stated.

**Acquisition.** `scripts/fetch_glc_fcs30d_us.py DATA_ROOT --workers 2`
selected 114 available annual tiles for conservative envelopes around the active
US scope. It downloaded only the required ZIP members, checked member size and
CRC, and recorded per-tile hashes and raster metadata under
`manifests/glc_us_tiles/`. `manifests/glc_us_download_plan.json` records the
queue. All 114 source tiles and outputs passed the independent acquisition audit.

**2019 extraction.** The source annual tiles contain bands for 2000–2022. Band
20 is 2019. It was copied to `processed/lulc_2019_us/` without reprojection or
resampling. Class rasters remain uint8 in their native EPSG:4326 grids. Use
nearest-neighbor resampling when aligning classes to WorldPop. Do not use
bilinear or cubic interpolation.

### Varun's supplied 2019 global land-cover raster

`raw/collaborator/varun_2026-10/lulc_glc_fcs30d_2019.tif` is the raster named by
Varun's script and now supplied by him. It is a 25,709,308,922-byte, one-band
uint8 GeoTIFF in EPSG:4326, with a 1/3600-degree grid, nodata 255 and SHA-256
`05c1aeb0a827ea0de956c88c0314bfcbaa80896cf617f65d2e9e68be674dcdf2`.
The source's GLC release and 2019 extraction/compositing recipe are not embedded
in the file. It remains unchanged in `raw/`.

Our [cell-level audit](evidence/data/varun_2026_10/land_cover_us_urban_cell_audit.json)
resampled both sources by nearest neighbor to the same 2019 WorldPop cell centres
inside all 3,312 current non-Hawaii US polygons. Both had a valid class on
17,669,023 cell memberships, representing 194.37 million people. Classes differ
on 3,134,545 memberships, representing **22.06 million people (11.35% of
both-valid population)**. Forty-four cells representing 459 people are fill in
the local tiles but valid in Varun's raster; none have the reverse pattern.
This identifies a material classification or preprocessing difference, without
establishing which map is more accurate. `scripts/check_varun_landcover.py`
recreates the audit. The [four-scenario comparison](evidence/data/varun_2026_10/source_lookup_factorial_summary.json)
isolates its modeled effect from the lookup-value effect.

**Nodata.** Codes 0 and 250 are fill. Keep them missing; do not convert them to
built-up land or zero NDVI. The completed support audit found 44 population-cell
rows in 22 of the 3,312 retained GUPPD features mapped to code 0 and none to 250.
See `pilots/us_local_qc_2019_v1/`.

## 2. NDVI exposure inputs

### Direct 2019 Landsat NDVI: production workflow

The US production run uses annual-median 2019 NDVI from Earth Engine
[Landsat 7](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LE07_C02_T1_L2)
and [Landsat 8](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2)
Collection 2 Level 2, sampled at native WorldPop cell centres. Surface-reflectance scaling is
applied before NDVI. Fill, dilated cloud, cloud, shadow, snow, applicable cirrus,
and radiometric saturation are masked, and at least three valid observations are
required. Positive NDVI is set to zero only in the counterfactual; signed observed
NDVI remains unchanged. The Earth Engine execution source is in
`Yingjie4Science/invest-gee/urban_mental_health/`. The run evidence is in
`docs/evidence/data/us_direct_ndvi_2019_v1/`.

### Derived US GLC_FCS30D-to-NDVI table: completed sensitivity

The controlled comparison used
`glc_fcs30d_attribute_table_us_2019.csv`. It pools area-weighted raw NDVI sums
over disjoint GUPPD city-state units plus the boundary residual. It reports class
area, valid NDVI area, means, standard deviations, observation support and method
metadata. Twenty-eight of 35 classes have valid NDVI on the US urban calibration
domain; the seven unsupported classes occur on no population-supporting cells in
the comparison. This is an in-sample US method sensitivity, not a globally
validated lookup.

### Varun's run lookup: supplied, method pending

Varun confirmed that `raw/collaborator/varun_2026-10/glc_fcs30d_attribute_table_processed_updated.csv`
was used in his run. The original public script at commit `f1822e2` instead names
`glc_fcs30d_attribute_table_processed.csv`; record this as a filename/version
difference, not evidence that the two files are identical. The supplied table
has one value for each of 35 GLC classes, blank values for fill codes 0 and 250,
and signed NDVI from −0.10 to 0.80, recorded to at most two decimal places.
It has no class counts, uncertainty, exclusion rule, generation method or
temporal/geographic metadata.

Against the 28 supported classes in the independently derived US urban 2019
table, its unweighted class-value mean absolute difference is **0.164 NDVI**,
RMSE **0.205**, and mean signed difference **−0.084** (Varun minus US). The
largest class gaps are sparse vegetation (−0.461), sparse herbaceous (−0.449)
and deciduous shrubland (−0.390). Impervious surfaces are 0.20 versus 0.392.
These comparisons show a material exposure-assignment difference, not which
table is more accurate: the US values are in-sample urban estimates, and rare
classes have weak support. We ran it as a **separate original-lookup
sensitivity** on the same local population, GLC and city support, then compared
national and city cases. Keep the published derived-table comparison labelled
as such. A claim of empirical lookup quality requires the lookup's NDVI source,
year/season, sampling domain, compositing, weighting, pixel counts, QA and edits.

**Matched local sensitivity completed.** On the same 3,312 US polygons, native
WorldPop cells, verified local 2019 GLC tiles, GBD rate and current-reference
health equation, rerunning the local model with only the lookup changed gives
**2.46 million** case equivalents for the US-derived table and **1.68 million** for Varun's table (**31.62% lower**). Both runs model
the same **194.37 million** people after excluding 459 people on source fill.
Among 2,307 cities with at least 100 cases in the derived-table run, the median
city change is **−37.32%**. These are technical exposure sensitivities, not a
reproduction of Varun's global run or evidence that either table is more valid.
The paired [summary and city results](evidence/data/varun_2026_10/summary.json)
are reproducible with `scripts/run_us_national_technical.py` and
`scripts/summarize_varun_lookup_runs.py`; the raw run records are under
`pilots/varun_lookup_matched_2019_v1/` in the data folder. A separate
[fixed-5% calculation](evidence/data/varun_2026_10/us_lookup_value_sensitivity.json)
uses the same class-population totals and is labelled a sensitivity.

**Owner-raster crossed sensitivity.** Using Varun's supplied 2019 land-cover
raster, population mosaic and 3,309 non-Hawaii polygons, but holding the same
GBD US rate, `p0`, OR, current-reference equation and US societal-cost proxy,
his lookup gives **1.67 million** case equivalents (conditional effect limits
0.50–3.08 million); the US-derived lookup gives **2.46 million**. Holding the
lookup fixed while switching local tiles to Varun's raster changes national
cases by **−0.90%** with Varun's lookup or **−0.34%** with the US-derived lookup.
On Varun's raster, changing the lookup lowers cases by **32.01%**. These are
four *full local technical runs*; the separate fixed-5% plus literal-original
equation result of **1.54 million** is an algebraic re-evaluation of the saved
class-population totals, not a fifth raster run. See the [scenario summary](evidence/data/varun_2026_10/source_lookup_factorial_summary.json)
and saved receipts in `pilots/varun_lookup_matched_2019_v1/`.

## 3. Population

### US input used in the published run

The selected file is the WorldPop Global 2 R2025A v1 retrospective 2019
constrained raster:

`raw/worldpop/usa_pop_2019_CN_100m_R2025A_v1.tif`

Direct URL:
`https://data.worldpop.org/GIS/Population/Global_2015_2030/R2025A/2019/USA/v1/100m/constrained/usa_pop_2019_CN_100m_R2025A_v1.tif`

The file is 1,511,305,409 bytes with SHA-256
`8b0ef7a8994d7686e49298f4d5f0b5129460e053d92ad6ec9eef5a300f5cc66c`.
It opens as a one-band float32 GeoTIFF in EPSG:4326, 430,706 by 62,971 cells,
with 0.00083333333-degree pixels and nodata -99999. The raster was used in the
local pilots, nationwide support audit and cloud production workflow. Its local
record is `raw/worldpop/README.md`.

### Varun's supplied WorldPop mosaic

`raw/collaborator/varun_2026-10/worldpop/100m_2019_global-mosaic.tif` is the
file named by Varun's original script (4,019,600,915 bytes; SHA-256
`86bc5772d6cec40b21977bc88cb82ac981ef0a2c353ce614ede22a1d3bafef56`).
It is one-band float32 EPSG:4326, 430,706 × 151,396 cells, with
0.00083333333-degree resolution and nodata −99999. It shares the current US
raster's origin, width and resolution.

A complete comparison over the **3,312 active US urban polygons** found identical
values and nodata status at all **17,669,067 valid population cell memberships**
(19,058,233 polygon cell memberships checked); both sum to 194,367,283 people.
The [cell audit](evidence/data/varun_2026_10/population_mosaic_us_urban_cell_audit.json)
is reproduced by `scripts/check_varun_population_mosaic.py`. This closes US
modeled-population equivalence on the declared cell-centre support, not global
mosaic provenance or pixel identity outside those polygons. Keep the original
published input fixed; use the supplied mosaic for a separately labelled owner
rerun. For future global work, request its country-file releases, constrained
status, mosaic command and overlap rule. Preserve population counts and align
categorical land cover to its grid with nearest neighbor.

## 4. Urban polygons

**Source.** CIESIN and the European Commission Joint Research Centre (2024),
*Global Urban Polygons and Points Dataset (GUPPD), Version 1*, NASA SEDAC, DOI
[`10.7927/brq1-xc29`](https://doi.org/10.7927/brq1-xc29).

The source GeoPackage has 123,034 features in each of its point and polygon
layers. Filtering the polygon layer to `ISO = USA` gives 3,337 polygons: 324
level 30, 1,748 level 23, and 1,265 level 22. All were valid and `SMOD_ID` was
unique. `scripts/prepare_guppd_us.py` preserves source fields and adds stable
`id`, `source_fid`, `country`, and `iso3` fields. The active derivative excludes
25 Hawaii polygons and contains 3,312 features. Source and selected identifiers
are recorded in `manifests/guppd_us_excluding_hawaii_qc.json`.

Varun's original script at commit `f1822e2` reads the whole prepared
`urban_boundaries_2019.gpkg` with no further level, country, area or population
filter. His supplied copy contains **121,552** polygons worldwide, including
levels **22 (17,302), 23 (91,174), and 30 (13,076)**; all IDs are present in
the 123,034-feature GUPPD v1 source. It omits 1,482 source IDs, mostly with
zero source 2020 population, but the exact preparation rule cannot be recovered
from the GeoPackage alone. Its feature IDs are sequential in this copy, so the
original code's sequential-FID join is consistent with this supplied file.

For the US, the owner layer contains **3,334** polygons (levels 22: 1,263;
23: 1,747; 30: 324). All 3,334 geometries match the source exactly. After
excluding its 25 Hawaii polygons, 3,309 owner IDs match our active selection;
our selection retains three additional polygons (`22_15706`, `22_15770`,
`23_88815`) that have zero modeled WorldPop cells and cases. Thus the US
**modeled population and case totals are unaffected by those three IDs** under
the current cell-centre rule, though feature counts differ. Varun's stored
`population_2019` values are auxiliary attributes: on the 3,309 shared US
non-Hawaii IDs they sum to 197.32 million, versus 194.37 million in our
cell-centre raster calculation. Do not substitute those attributes for the
model population. The [boundary audit](evidence/data/varun_2026_10/urban_boundaries_audit.json)
and `scripts/audit_varun_inputs.py` record IDs, levels, source geometry and
checksums. The owner's exact global selection rule remains a provenance request,
not a blocker for the matched US lookup test.

## 5. Health inputs

**Effect.** `processed/effect_size.xlsx` contains one depression row with OR
0.931 and 95% CI 0.887–0.977 per +0.1 NDVI from
[Liu et al. (2023)](https://doi.org/10.1016/j.envres.2023.116303). Preserve its
exposure, effect-type, outcome and reference columns. The workbook's presence
does not by itself establish full compatibility between the meta-analytic effect
and either exposure representation.

**Prevalence: two declared scenarios.** The primary input is the locally
validated [IHME GBD Results](https://vizhub.healthdata.org/gbd-results/) GBD
2023 release table for 2019, both sexes, all ages, crude depressive-disorders
prevalence (204 locations), joined by reviewed country crosswalk to all-age
WorldPop. The original script at commit `f1822e2` explicitly sets
`baseline_prevalence_rate = 0.05` for every country. Retain this fixed 5% as a
second, labelled original-method sensitivity; it is an adult WHO approximate
rate applied to an all-age denominator, not a country estimate. Never silently
substitute one source for the other. The US GBD rate is **4.2433%**; on identical
exposure/support and equation, changing only to 5% raises modeled cases and
valuation by **17.83%**. Both versions are already present in the eight-scenario
[controlled comparison](evidence/data/us_method_comparison_2019_v2_common/scenario_comparison.csv).
This checks implementation sensitivity, not independent epidemiologic
cross-validation: both runs share population, exposure and effect assumptions.
Missing country joins stop a GBD run; the fixed-rate run must report its
age-denominator mismatch.

**`p0`.** The default 0.115 is the health-record depression-diagnosis proportion
for the lowest residential-NDVI quartile in Hystad et al. (2019), used in the
approximate OR-to-RR conversion. It is a transported Quebec adult-cohort proxy,
not the GBD country prevalence or a measured zero-NDVI risk. Its alternatives and
structural sensitivity range are documented in `docs/DECISIONS_AND_TODOS.md`.

## 6. Costs and valuation

### Existing 33-country source and US proxy

`processed/data_cost_mental_health.csv` contains 33 rows labelled 2018 USD PPP,
`mood disorders`, and `total societal cost`. It is preserved unchanged. The
Christensen paper first inflated costs within country to 2018 and then converted
them with 2018 PPP factors, mainly OECD factors with World Bank/Quandl fallbacks.

The documented non-PPP conversion is:

`2019 USD = 2018 international dollars × PPP2018 (LCU/international dollar) × CPI2019/CPI2018 ÷ annual-average FX2019 (LCU/USD)`

PPP appears only to reverse the supplied normalization; the final conversion
uses market exchange rates. Saved WDI responses and URLs are under
`raw/cost_conversion/`; `manifests/cost_conversion_2019_usd.json` records hashes
and factors. `scripts/convert_costs_2019_usd.py DATA_ROOT` reproduces the audit
CSV and the US rate of $10,999.206774 per case equivalent in 2019 USD. The 30
non-US numeric conversions use revised WDI GDP PPP and remain provisional; the
exact historical OECD factor ledger was not recovered. Bulgaria and the Europe
aggregate remain unresolved.

All conversions retain `model_ready = False` because the source outcome is broad
mood-disorder total societal cost per patient. The production report labels the
US result as an exploratory societal-value proxy. Currency conversion does not
make the endpoint depression-specific or establish causal savings.

### Varun-supplied 199-country estimates and decision

The supplied `treatment_cost.xlsx` has 199 unique country rows and two columns:
`country` and `cost_per_case`. The United States value is 5,834.61 and Bhutan is
398.07. There are no formulas or embedded metadata fields. The user confirmed
on 21 October 2026 that the estimates are denominated in 2019 USD; this
confirmation is recorded in the external-data manifest rather than written into
the source workbook. The accompanying appendix describes a pooled depression
and hypertension GDP-based meta-regression:
a shared slope of 0.87 (SE 0.29; 95% CI 0.28–1.45), compared with 1.52 (SE 0.32)
for depression alone. It also notes no depression observations below about
$27,000 GDP per capita, differing cost definitions, and extrapolation for the
lowest-income countries.

The two accompanying World Bank files are GDP per capita in current US dollars
(`NY.GDP.PCAP.CD`) and the GDP deflator (`NY.GDP.DEFL.ZS`). They are predictor or
inflation references, not a row-level proof of the non-PPP basis or prediction
and conversion method.
At the US rate, Varun's **$5,834.61** is **46.95% below** the Christensen-derived
**$10,999.21**. Applied to the identical 2.45 million common-support direct-NDVI
case equivalents, those alternatives give **$14.31 billion** and **$26.99
billion**, respectively. This is a cost-input comparison, not two independent
estimates of cases or a confidence interval. They differ in cost scope, source
coverage (199 versus 33 countries), construction (regression prediction versus
published review/conversion), and auditability. The Christensen US rate has a
reproducible currency conversion but is a broad mood-disorder *total societal*
proxy; Varun's workbook has broader coverage and a smaller US value but no
row-level evidence for the cost components or non-PPP status. Neither currently
supports a claim of depression-specific treatment savings.

**Decision.** Retain the published US societal valuation as a clearly labelled
exploratory baseline; show Varun's rate as a separate conditional valuation
sensitivity using identical case outputs, without changing the published run.
For a global production valuation, prioritize obtaining Varun's prediction and
currency ledger, explicit non-PPP confirmation and country crosswalk, then make
a reviewed derivative with `currency=USD`, `price_year=2019`,
`ppp_adjusted=FALSE`, a cost-scope label and row-level provenance. If that
cannot be recovered, report cases without monetary totals for unverified
countries. Do not compare the dollar totals as if they measured the same
cost construct.

**Additional US price sensitivity.** The SNAPP project's Greenberg 2019
adult-MDD anchor is $16,854 per case in reported 2019 USD. We applied it to
the same four saved case outputs without changing cases; see the [three-rate
comparison](evidence/varun_us_cost_comparison.md). This source is more explicit
about US price year, but its adult-MDD endpoint differs from the model's
all-age depressive-disorders endpoint. It remains a conditional valuation,
not the selected production rate. The SNAPP 2024 pooled estimate was excluded
because this project reports 2019 USD and its pooled calculation needs a small
source/rounding reconciliation.

## 7. Remaining requests, owners and decisions

The US polygon levels/geometries, modeled population equivalence, owner
land-cover source difference and paired lookup effect are now checked. **No additional user modelling decision is needed
for the next US technical comparisons.** Keep direct 2019 NDVI as the primary US
exposure and retain the two class lookups as separate sensitivities. Do not
replace the published production result with either lookup run.

| Status | Waiting on | Specific information or decision | Recommended action |
| --- | --- | --- | --- |
| **Ask Varun now: lookup provenance** | Varun | For the confirmed `glc_fcs30d_attribute_table_processed_updated.csv`: NDVI sensor/product, year and months, mask/composite, calibration geography, class statistic and weights, sample counts, fill/water treatment, manual edits, generation code; explain why the public script names `...processed.csv` | Keep his table as an original-run sensitivity until its source and sampling method can be checked; then test against held-out direct NDVI |
| **Ask Varun now: cost provenance** | Varun | Row-level prediction/price ledger or code, source cost components, 2019 USD market-exchange basis, explicit PPP status and country crosswalk for `treatment_cost.xlsx` | Retain the US societal proxy as exploratory; display Varun's rate only as conditional cost sensitivity until non-PPP basis and cost scope are verified |
| **Useful for later global replication** | Varun | Supplied land-cover mosaic’s GLC release, 2019 extraction/compositing and nodata/merge recipe; population mosaic country-source releases and build/overlap rule; GeoPackage selection rule and stored-population calculation; country inclusion list and one known-good original intermediate/final run | Supplied rasters permit the completed US comparison; request these records before claiming pixel-identical global reproduction |
| **Internal, completed for US** | Project team | Compare Varun's GUPPD layer, population cells, land-cover raster and both lookup tables | Boundary/population audits, class-map audit and four crossed full runs are linked above; retain the published direct-NDVI result unchanged |
| **Internal, still open** | Project team | Validate lookup against held-out areas/years, assess `p0` and endpoint compatibility, and propagate uncertainty beyond the OR interval | Do this before interpreting lookup differences as predictive accuracy or the intervals as full model uncertainty |

The key request to Varun is **how the lookup was produced**, not another
confirmation that he used it; his use of that file is already confirmed.

## 8. Reproduction and validation gates

The original local code accepts explicit `--land-cover`, `--population`,
`--ndvi-lookup`, `--effects`, `--urban-boundaries`, and `--costs` paths. The
windowed nationwide technical runner additionally accepts
`--land-cover-mosaic`, `--population-raster` and `--urban-boundaries` to
reproduce the owner-input sensitivity without building a dense US mosaic. Use explicit paths for
current data; the built-in filenames preserve Varun's historical directory
layout. The national land cover is deliberately tiled, so the current local data
folder is suited to tiled pilots and audits rather than an unreviewed dense
Alaska-spanning mosaic. The published direct-NDVI national workflow ran in Earth
Engine and is documented separately.

Before interpreting a new run, check the status of the particular inputs used.
The published direct-NDVI run and the new local lookup sensitivities have
different evidence scopes.

| Gate | Current status | Next action |
| --- | --- | --- |
| Urban support and population | **US technical check passed:** all 3,334 owner US geometries match GUPPD; the three IDs absent from the owner file have zero modeled population; all 17.67 million active urban population cell memberships match between the supplied mosaic and current US raster | Keep owner and current boundary selections separately named; obtain the global filter recipe only for global replication |
| Land cover and lookup | **Four US technical runs complete:** both land-cover sources crossed with both lookups. The maps differ for 11.35% of both-valid population, but switching raster at a fixed lookup changes national cases by −0.34% to −0.90%; switching lookup changes cases by about −32%. The owner mosaic recipe, lookup calibration and held-out validity remain unknown | Request source and lookup-generation records; test both tables against held-out direct NDVI before promoting an exposure method |
| Health inputs | GBD US crosswalk and fixed-5% sensitivities are complete; `p0` and pooled effect remain transported assumptions | Keep age denominators and reference state explicit; repeat country joins and `p0` sensitivity on expansion |
| Valuation | Published US cost is documented 2019 USD non-PPP but a broad societal proxy. Varun workbook is user-labelled 2019 USD; PPP status and scope remain unverified | Keep monetary estimates conditional; obtain the prediction/currency ledger before adopting Varun's 199-country rates |
| Run integrity and uncertainty | All four full local source/lookup runs have fresh output directories, input/output hashes and per-city results. The owner-raster runs use his 3,309-feature non-Hawaii layer. OR limits hold other inputs fixed | Preserve receipts; the 5%/literal-original result is an analytic sensitivity; extend uncertainty before claiming full intervals or causal savings |

These completed technical checks support a **US method comparison**. A strict
global reproduction still needs the owner records in Section 7.

Useful local preparation commands are:

```sh
GEP_DOWNLOAD_TRANSPORT=curl python scripts/fetch_glc_fcs30d_us.py DATA_ROOT --workers 2
python scripts/prepare_guppd_us.py DATA_ROOT
python scripts/check_us_boundaries.py DATA_ROOT
python scripts/verify_land_cover_acquisition.py DATA_ROOT
python scripts/convert_costs_2019_usd.py DATA_ROOT
```

See the [production report](evidence/us_direct_ndvi_production_run.md),
[controlled comparison data](evidence/data/us_method_comparison_2019_v2_common/),
and [decisions and remaining work](DECISIONS_AND_TODOS.md) for interpretation.
