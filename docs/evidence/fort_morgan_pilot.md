# Fort Morgan 2019: first local and Earth Engine pilot

Completed 16 October 2026. **Ready as a bounded technical pilot, with scientific caveats.** This checks execution and implementation fidelity for one urban polygon; it does not validate causal benefits, country totals, or a Bhutan endpoint.

## What ran

- GUPPD city `23_87603`, Fort Morgan, Colorado; exact source geometry retained. Its polygon is smaller than a general administrative definition of Fort Morgan. Hawaii remains excluded from the wider US workflow.
- User-supplied WorldPop `usa_pop_2019_CN_100m_R2025A_v1.tif`: 1.4 GB compressed, SHA-256 `8b0ef7a8994d7686e49298f4d5f0b5129460e053d92ad6ec9eef5a300f5cc66c`. Source grid is EPSG:4326 at 3 arc seconds. Full-file checksum, 22 sampled read windows and all pilot cells checked; a complete national cell scan was not performed.
- Exact native-grid pilot window: 54 columns × 38 rows. All 1,860 valid population cells in that window match GEE exactly, including masks, transform and CRS. Inside the GUPPD polygon there are **877 valid cells and 7833.566076 people**. No population is lost to missing lookup or land cover in this pilot.
- GUPPD pilot uploaded privately to `projects/natcap-gep/assets/umh_guppd_fort_morgan_2019_v1`; task `PQY46GRQPT2X4C7A67PCLCGQ` completed. The remaining US polygons have not been uploaded.
- Actual lookup derived in Earth Engine from 40 Landsat 7 and 40 Landsat 8 scene intersections in 2019, over the city plus a 5 km UTM buffer. Annual pixel medians, at least three valid observations, documented QA/scaling, then area-weighted class means on the explicit 30 m equal-area grid. All ten local city classes have values; 18 classes occur in the buffer. Observed NDVI coverage is complete on classified area, but rare-class reliability and seasonal bias still require review.
- Lookup SHA-256 `71e06d0cfb1cdcd41f5f506e5c8a21eeb1ad16404d71ccba5a24215a2a21edb7`. This regional table is accepted for the technical test only; it is not a national or Bhutan calibration. Class SD is not a confidence interval.

## Results and comparison

The country prevalence is 0.0424332878, from GBD 2023 release / 2019 all-age depressive disorders. The reference-group `p0=0.115` remains a transported proxy. Supplied depression OR is 0.931 with 95% limits 0.887–0.977 per 0.1 NDVI. Observed case baseline is 332.403964 case equivalents. The no-positive-NDVI scenario uses `P*N*(RR**(-10*max(NDVI,0))-1)`.

| Run | Point case equivalents | Lower effect limit | Upper effect limit |
| --- | ---: | ---: | ---: |
| Python, local Zenodo land cover | 63.791761 | 19.476032 | 114.257584 |
| GEE, community land cover | 63.096895 | 19.282191 | 112.894560 |
| Python, same land cover as GEE | 63.096900 | 19.282211 | 112.894570 |

The interval is conditional propagation of the effect-size 95% CI. It excludes uncertainty in prevalence, p0, classification, lookup construction, population and costs. It is not a full Monte Carlo uncertainty interval. The values are modeled case-equivalent contrasts, not observed annual cases prevented.

Every one of the 877 modeled city cells was compared for point/lower/upper outputs using identical inputs. Differences pass `rtol=2e-6, atol=1e-7` case equivalents, allowing the Python Float32 path versus GEE double precision. Largest city-total discrepancy is 0.0000202 case equivalents. Population/observed-case totals and polygon cell counts agree. Independent double-precision calculations also agree with Python regional aggregation within the recorded tolerance.

### Material finding: the land-cover sources are not interchangeable

The local Zenodo derivative and GEE community b20 disagree in **408/2,052 population-grid cells (19.88%)** in the rectangular pilot window. On the native land-cover grid, **2,818/19,992 cells (14.10%)** differ, so population-grid sampling alone does not explain the mismatch. Both native affine grids are effectively identical. The precise source-release history still needs reconciliation; no exact version-equivalence claim is made.

This changes the point result by about **1.10%** in this city. That small result difference cannot establish equivalence elsewhere. Retain local Zenodo land cover for the current local specification; label the community-source cloud run separately. Use matched-source bridge runs to test implementation parity. Before expansion, choose and pin one agreed land-cover snapshot for production, or explicitly report a source-sensitivity analysis.

### Monetary sensitivity only

An optional local sensitivity multiplies the contrast by **10,999.206774445318 in 2019 USD, non-PPP**. The source is **mood-disorder total societal cost per patient**, not depression treatment cost. The local point value is approximately **$701,659**, with conditional effect-only limits **$214,221–$1,256,743**. This is an exploratory proxy calculation; its source `model_ready=False` has not been overridden. No monetary result is enabled in the GEE pilot or endorsed for reporting as a validated saving.

## Reproduction and artifacts

Data folder, relative to `gep-global`: `data/urban_mental_health/pilots/fort_morgan_2019/`.

- `input_qc.json`: source checksum, metadata, read-window checks, population totals and output hashes.
- `lookup/`: candidate CSV and complete source/scene/QA/coverage evidence.
- `local_outputs/`: final committed-source Python run, three interval rasters and regional CSVs, `pilot_summary.csv`, `run_record.json`.
- `local_cloud_inputs_outputs/`: matched-input Python comparison. `initial_*` folders preserve earlier execution trials.
- `cloud_config.json`, `cloud_graph.json`, `cloud_run_record.json`, `cloud_summary.json`, `cloud_outputs.tif`: exact GEE settings, expression, source hash, bands and output. No signed URLs or credentials retained.
- `pilot_comparison.json` / `.csv`: cell-level checks and three-run table; `native_lc_source_check.json`: native-grid source diagnosis.
- `pilot_diagnostics.png`: inspected population, source-disagreement and case-equivalent maps. Labels and color bars were visually reviewed; this is a static diagnostic, not a public-app UI test.

Scripts in this repo: `scripts/prepare_local_pilot.py`, `scripts/run_local_pilot.py`, `scripts/compare_pilot_results.py`. Scripts in `invest-gee/urban_mental_health`: `serialize_lookup.cjs`, `run_lookup.py`, `prepare_pilot_cloud_inputs.py`, `run_real_pilot.py`, `check_native_land_cover.py`. The lookup reproduction note in that repository contains the exact EE execution steps. Every new local run requires a fresh output directory; original inputs are preserved.

Use the isolated pilot Python environment with `PROJ_DATA` and `GDAL_DATA` set to its geospatial base environment's `share/proj` and `share/gdal` directories. Setting these paths resolved the earlier GDAL/PROJ resource warnings. The environment inherits that existing base; it is not a self-contained portable installation. Record resolved package versions and supply the reference inputs before reproducing elsewhere.

## Next steps

1. Resolve/pin the land-cover source before expanding comparable results. Keep both current products and their difference evidence.
2. Extend beyond this small city: contrasting vegetation/climate/urban forms, then Alaska. Review rare classes, seasonal coverage, p0 sensitivity and direct-NDVI versus class-lookup differences.
3. Upload/reconcile the remaining GUPPD urban subset in batches; resolve the three known overlaps and boundary cell assignment before national summation.
4. Keep the societal-cost approximation explicitly exploratory until the endpoint/cost match is reviewed. Exact non-US PPP-factor recovery remains open.
5. Configure/visually test the GEE interface using this pilot. Bhutan adaptation requires Bhutan prevalence, urban boundaries and reviewed exposure lookup; the US values are not Bhutan defaults. Public Bhutan app integration remains pending these gates.
6. Research/reporting: stronger p0 synthesis, adult-MDD endpoint pathway, full uncertainty propagation and final Google Doc reconciliation remain open.

## Review disposition

A separate agent reviewed formulas, interval direction, same-input comparison, the source-discrepancy conclusion and cost labels. No material numerical issue was found. Its single provenance finding (missing cost-file hash) was fixed and the final local run was regenerated from committed source. Resolved environment versions are retained locally in `environment-resolved.txt`. The configured GEE pilot is `invest-gee/urban_mental_health/fort_morgan_code_editor.js`; regenerate with `node urban_mental_health/build_pilot.cjs urban_mental_health/evidence/fort_morgan_config.json`. The script is syntax checked; rendered Code Editor controls and public deployment remain unverified.
