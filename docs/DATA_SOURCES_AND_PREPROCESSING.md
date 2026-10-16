# Urban mental health input data: sources and preprocessing

Last updated: 2026-10-16. This record separates source files, project derivatives, unresolved owner inputs and model-ready validation. Large rasters and licensed source files are kept outside Git under `../data/urban_mental_health/`.

## Directory convention

- `raw/`: unchanged downloads or unchanged copies supplied by collaborators.
- `processed/`: derived files used by a model run.
- `manifests/`: URLs, retrieval dates, sizes, hashes, transformations and validation results.
- Do not treat a file ending in `.incomplete` as data.

## Current US pilot inventory

| Input | Selected source | Current status | Model role |
| --- | --- | --- | --- |
| Land cover | GLC_FCS30D v2, Zenodo record 15063683 | One annual source tile and its 2019 band are ready for tile W75N40 | Baseline land-cover classes; later mapped to NDVI |
| Urban polygons | NASA SEDAC GUPPD v1, DOI 10.7927/brq1-xc29 | User is copying a local GeoPackage; validation and US subset pending | Urban aggregation units and country/ISO labels |
| Population | WorldPop 2019 | Complete raster still pending; interrupted transfers are labelled `.incomplete` | Population counts on the reference grid |
| Effect estimate | User-supplied workbook | Present and schema-validated | Depression OR 0.931, 95% CI 0.887-0.977 per 0.1 NDVI |
| Country prevalence | IHME GBD 2023 estimates for 2019 | Present in `../depression_prevalence_review/` | Country baseline prevalence |
| Treatment cost | User-supplied workbook | Pending copy and validation | Cost per case in 2019 USD, without PPP adjustment |
| Land-cover/NDVI lookup | Original project input | Missing; derivation is not in Git history | Maps `lc_code` to `lc_ndvi` |

## 1. GLC_FCS30D land cover

**Source.** Liu, Zhang and Li, *GLC_FCS30D: the first global 30-m land-cover dynamic monitoring product with fine classification system from 1985 to 2022*, v2, Zenodo record 15063683, DOI `10.5281/zenodo.15063683`. The product has 35 fine land-cover categories. Its reported overall accuracy is 80.88% for 10 broad classes and 73.24% for the 17-class LCCS level-1 system. The guide asks scientific users to contact the authors before use and consider acknowledgement or authorship guidance.

**US pilot retrieval.** Rather than downloading the entire 135.8 GB archive collection, `scripts/fetch_glc_fcs30d_tile.py` uses HTTP byte ranges to retrieve one member from the official Zenodo ZIP and verifies its ZIP CRC. The selected source member is:

`GLC_FCS30D_19852022maps_W75-W80/GLC_FCS30D_20002022_W75N40_Annual_V1.1.tif`

Its bounds are longitude -75 to approximately -70 and latitude approximately 35 to 40 degrees, so it covers Washington, DC and Philadelphia but not New York City. The source tile has 23 annual bands ordered 2000, 2001, ..., 2022. Band 20 is therefore 2019.

**Preprocessing.** The script copies band 20 to a one-band, tiled, deflate-compressed GeoTIFF without reprojection or resampling. The output retains EPSG:4326, the source transform, uint8 class codes and source-year tags. In a model run, this categorical raster must subsequently be warped to the population grid with nearest-neighbor resampling. Bilinear or cubic resampling must not be used for class codes.

**Observed 2019 values in the pilot tile.** `0, 10, 11, 20, 51, 52, 61, 62, 71, 72, 81, 82, 91, 120, 121, 130, 140, 150, 153, 181, 182, 183, 186, 187, 190, 200, 210`. Code 0 is a fill value in the product guide and should become nodata, not an NDVI value.

## 2. GUPPD urban polygons

**Source.** Center for International Earth Science Information Network (CIESIN), Columbia University, and Joint Research Centre, European Commission. 2024. *Global Urban Polygons and Points Dataset (GUPPD), Version 1*. NASA SEDAC. DOI `10.7927/brq1-xc29`.

GUPPD contains 123,034 named urban settlements and builds on the GHSL settlement hierarchy. It includes urban centres (level 30), dense urban clusters (level 23) and semi-dense urban clusters (level 22), with population attributes for 1975-2030 at five-year intervals. It is the boundary source named by the original model author. The repository filename `urban_boundaries_2019.gpkg` should not be interpreted as polygons observed in 2019; the exact geometry epoch and level selection must be recorded from GUPPD metadata.

**Required preprocessing after the local copy arrives.**

1. Inventory all GeoPackage layers, feature counts, CRS, geometry types and attribute fields.
2. Select the polygon layer and filter to the United States using the authoritative ISO/country field.
3. Decide and document which settlement levels are included. Check for overlapping units before aggregation so population and cases are not counted twice.
4. Preserve the original GUPPD identifier, name, settlement level, ISO code and country name.
5. Repair invalid geometry only when necessary, recording the count and method.
6. Add the model fields `id`, `country` and `iso3` without replacing source identifiers. Use a country label that is explicitly crosswalked to IHME and the cost workbook.
7. Clip or select the Washington, DC pilot polygons whose geometries intersect both the land-cover and population pilot extents.
8. Verify that feature identifiers returned by zonal statistics map to the intended GeoPackage records. The current code's sequential-FID assumption requires an explicit test.

## 3. WorldPop population

### Reproduction-compatible primary choice

The original code points to a custom `100m_2019_global-mosaic.tif`. The email chain says it was made by stitching country-level WorldPop 100 m rasters. For a United States pilot, the closest identifiable source is the archived Global Project file:

`https://data.worldpop.org/GIS/Population/Global_2000_2020/2019/USA/usa_ppp_2019.tif`

This is a 2019, approximately 100 m, EPSG:4326 population-count raster. The archive path is the unconstrained Global 2000-2020 product; the filename without `_UNadj` indicates the UN-adjusted variant. This identification should be confirmed against the original owner's mosaic manifest before claiming exact reproduction.

### Current-release alternative

WorldPop Global 2 R2025A v1 supplies a retrospective 2019 constrained raster at 100 m:

`https://data.worldpop.org/GIS/Population/Global_2015_2030/R2025A/2019/USA/v1/100m/constrained/usa_pop_2019_CN_100m_R2025A_v1.tif`

It is smaller and uses a newer modelling release, but it is not the same population surface as the original pipeline. Use it as an explicitly labelled updated-input scenario, not as an unnoticed replacement. A 1 km constrained version is available for low-resolution technical testing.

**Download status.** The WorldPop file host stalled during this session and rejected byte-range resume. Partial files are retained only with an `.incomplete` suffix. A complete file must match the remote `Content-Length`, open successfully with GDAL/rasterio, have EPSG:4326 and plausible nonnegative counts after masking nodata. Record SHA-256 and the raster sum before use.

**Preprocessing.** Preserve population values as counts. Clip by a grid-aligned window without resampling when possible. If mosaicking country rasters, use a deterministic country list and order, preserve the native resolution and transform, mask each source nodata value, and check for overlaps/gaps. Do not average population counts. The land-cover raster should be aligned to this population grid, not the reverse.

## 4. Effect estimate

The present workbook has one depression row with OR `0.931` and 95% CI `0.887-0.977` per 0.1 NDVI, citing Liu et al. (2023), DOI `10.1016/j.envres.2023.116303`. The model reads only `health_indicator`, `effect_size`, `ci_lower` and `ci_upper`. Preserve the additional exposure, effect-type and reference columns for review. The workbook is an input, not evidence that the selected OR and the land-cover-derived exposure metric are fully compatible.

## 5. Country prevalence and treatment costs

The primary prevalence source is the locally validated GBD 2023 table for 2019, both sexes, all ages, crude prevalence of depressive disorders. The US polygon label must resolve to its GBD location ID; do not silently fall back to a global 5% rate.

The treatment-cost workbook must contain one unique row per included country with `country`, finite nonnegative `cost_per_case`, `currency = USD`, `price_year = 2019`, and Excel Boolean `ppp_adjusted = FALSE`. These declarations are a validation gate. The source rate, cost components, original currency/year, market exchange rate and inflation conversion still require independent provenance.

## 6. Land-cover/NDVI lookup: unresolved provenance

The Git history contains no lookup data or generation script. The model simply reads `glc_fcs30d_attribute_table_processed.csv`, takes `lc_code` and `lc_ndvi`, and assigns that single NDVI number to every raster cell in a class. The email chain shows another team member asking the original author to share the “code/attribute table” and the author saying project data would be placed in the shared submissions directory. No subsequent derivation appears in the supplied chain.

The lookup therefore cannot currently be reproduced from public code. Do not infer NDVI values from class names or colours. Request the original table and method listed below. If it cannot be recovered, build a replacement as a separately versioned empirical product: select a documented satellite NDVI product and 2019 compositing period, apply QA/cloud/snow/water masks, align it with GLC_FCS30D, calculate a declared statistic for each class over a declared geography, report pixel counts and distributions, validate held-out locations, and keep water/fill/nodata handling explicit. A global class mean is a strong simplification and should be tested against region-specific values.

## 7. Files and information needed from the original repository owner

### Essential for exact or close reproduction

1. **Original `glc_fcs30d_attribute_table_processed.csv`.** Include its checksum and all columns.
2. **Lookup-generation code or notebook and precursor data.** Specify the NDVI product/sensor, year and months, compositing statistic, cloud/snow/water QA, spatial sampling extent, class statistic (mean, median or other), weighting, sample count per class, excluded pixels, treatment of codes 0/250 and any manual edits.
3. **Original WorldPop mosaic manifest.** List every country file/URL, release, constrained versus unconstrained choice, UN-adjusted status, mosaic command/order, output CRS/transform/nodata, overlap rule and checksum of `100m_2019_global-mosaic.tif`.
4. **Original GUPPD derivative.** Provide the exact GUPPD version and layer, geometry epoch, settlement-level filters, country filters, country-name edits/crosswalk, geometry repairs and checksum of `urban_boundaries_2019.gpkg`.
5. **Original 32-country inclusion list and rationale.** Clarify whether countries were selected by urban coverage, cost availability or another rule.
6. **Original treatment-cost sources and conversion ledger.** For each country, identify the source, cost components, original currency and price year, market exchange-rate source, inflation index and formula used to express the result in 2019 USD without PPP.
7. **A small known-good run or checksums.** One city/country input bundle and expected intermediate/output summaries would support regression testing.

### Already obtained locally but still subject to scientific review

- The effect-size workbook.
- The 2019 GBD country prevalence table.
- The original code and email explanations of the high- and low-resolution workflows.

## 8. Validation gates before interpreting results

- Every land-cover code in the AOI is either mapped once or explicitly treated as nodata.
- Population and land-cover grids overlap, use expected CRS/transforms and retain population counts.
- Urban polygons do not create unintended overlap or double counting.
- Polygon country labels match both GBD prevalence and cost rows.
- Population sums, urban feature counts and zonal totals are compared with source summaries.
- The model is first run on a fresh small output directory; intermediate rasters are visually inspected.
- Reported uncertainty remains conditional unless prevalence, exposure, population and cost uncertainty are also propagated.
