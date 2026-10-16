# Expanded 2019 US local tests

Started 17 October 2026. This is an execution and source-sensitivity check, not epidemiological validation. Original Fort Morgan outputs are preserved.

## Design

| GUPPD urban feature | Source ID | Reason |
| --- | --- | --- |
| Tucson | 30_12305 | Dry inland urban landscape |
| Portland, Maine | 30_12572 | Humid coastal landscape |
| Anchorage feature | 23_87444 | High-latitude exposure and seasonality |
| New York | 30_12545 | Large urban area crossing state boundaries |

GUPPD features are not municipal boundaries. In particular, the selected Anchorage feature is a bounded part of the named settlement, not all Anchorage residents.

For each feature, derive its own 2019 Landsat 7/8 class lookup over the source polygon plus a 5 km local UTM buffer. Preserve QA, scaling, annual median, minimum-three-observation rule, class areas, raw sums, scene IDs and lookup hash. Keep the local Zenodo source and GEE community source distinct. Compare complete city support on the native WorldPop grid, including class-confusion counts and population on differing classes. Run the Python model once with local land cover, once with the identical GEE land cover, then compare the matched Python and exact JS model outputs cell by cell. The native-grid result check uses rtol=2e-6 and atol=1e-7 case equivalents; source sensitivity is reported separately from implementation parity.

## Reproduction

`run_expanded_city_tests.py` accepts data root, local repository, invest-gee repository, local model Python and prevalence CSV paths. It generates the declared test plan and lookup AOIs when absent, executes the reviewed GEE lookup serializer/evaluator, and resumes only completed recorded stages. Use `--prefetch-only` to retrieve cloud inputs on the native local grid during acquisition, then `--wait` for the complete comparison workflow. Cloud downloads are bounded in 256-row strips and record no signed URLs. Original input files are not overwritten.

The acquisition uses `fetch_glc_fcs30d_us.py`, `GEP_DOWNLOAD_TRANSPORT=curl`, `GEP_DOWNLOAD_CHUNK_BYTES=1048576`, `GEP_DOWNLOAD_RANGES=2`, and three tile workers (at most four open HTTP transfers, one new request per second across workers). `--priority-tiles` moves test-city inputs to the front without changing the full 114-tile plan. Per-tile process locks prevent duplicate queues writing the same partial member. Higher concurrency triggered HTTP429 responses and was stopped. The transport now honors Retry-After and shared exponential cooldowns of at least60seconds. Every appended range must match its HTTP Content-Range and byte count; the completed member must pass ZIP size/CRC checks. Interrupted partials remain resumable. An oversized partial from an older overlapping queue was preserved separately instead of accepted.

After acquisition, run `verify_land_cover_acquisition.py DATA_ROOT OUTPUT_JSON` to independently re-read raw/output hashes and deterministic band-20 extraction windows. Run `check_us_land_cover_coverage.py DATA_ROOT OUTPUT_DIRECTORY` to inspect actual land-cover support for all 3,312 source urban units, on native population cell centres. Per-city population values must not be summed because the source polygons can overlap.

All expanded run files stay under `data/urban_mental_health/pilots/expanded_2019_v1`. The scientific constants remain prevalence 0.0424332878, p0=0.115, OR0.931 (0.887–0.977) per0.1NDVI, and the positive-NDVI-to-zero counterfactual. The USD calculation is an exploratory 2019 USD non-PPP mood-disorder societal-cost proxy. Confidence limits propagate the effect-size CI only.

## Executed results — 17 October 2026

All three official tiles required by the four selected test features are verified. The four local runs, matched-cloud-source local runs, and exact-JS GEE raster evaluations completed. All three case bands pass cellwise tolerance in all four tests; WorldPop values match exactly. These checks cover **788,807 urban population cells** across the four tests. All modeled city populations have land-cover and lookup support.

| Test feature | Population cells | Different land-cover cells | Local case equivalents | Local vs cloud-source case change |
| --- | ---: | ---: | ---: | ---: |
| tucson | 54,794 | 8.04% | 3,345.95 | +0.24% |
| portland_maine | 10,664 | 16.60% | 1,461.18 | +1.42% |
| anchorage | 3,551 | 30.05% | 468.43 | +3.89% |
| new_york | 719,798 | 12.86% | 225,676.37 | +0.66% |

“Local vs cloud-source” holds the city-specific lookup, population, formula and local cell mask constant and changes land-cover input only. Both products remain distinct snapshots. A small change in the case total does not imply the classifications are equivalent.

### Regional membership finding

The GEE unweighted polygon reductions and local centre masks agree exactly for Portland. They differ slightly for the other three geometries:

| Test feature | Local cells | GEE regional cells | GEE minus local population | GEE regional cases minus matched local cases |
| --- | ---: | ---: | ---: | ---: |
| tucson | 54,794 | 54,795 | +17.242109 | +0.087268 |
| portland_maine | 10,664 | 10,664 | +0.000000 | +0.000054 |
| anchorage | 3,551 | 3,550 | -2.449538 | -0.034348 |
| new_york | 719,798 | 719,804 | +46.421400 | +0.755565 |

The population rasters agree exactly on the test grids; the differences arise in geographic membership/reduction, separately from the formula check. A New York diagnostic using explicitly planar EE geometry reduced the population discrepancy only from46.421400 to45.361691 people; therefore geodesic-versus-planar edges alone do not resolve it. Exact boundary-cell reconciliation remains open. Do not relabel the four matched-cell passes as exact regional or national parity.

### Decisions and remaining actions

- Keep official Zenodo land cover as the local source-sensitivity reference; label the existing cloud run with its community snapshot. Do not merge or substitute them silently. This is not approval of an unmatched land-cover/lookup pair for production.
- These tests deliberately hold the lookup fixed to isolate class-map differences. The class means were derived with community land cover; a production local-Zenodo workflow must derive or validate a lookup against the selected Zenodo snapshot. A full source-specific lookup comparison is distinct from the completed fixed-lookup tests.
- Retain source sensitivity alongside the case and USD results. The Anchorage feature showed the largest difference in these four tests; it is not a whole-Anchorage estimate.
- Investigate the small set of differing boundary cells and pin one shared native-grid membership rule before claiming cross-platform regional/national equality. Preserve the original geometries and these diagnostic outputs.
- Local estimates and conditional intervals are exported in `expanded_city_summary.csv`. The USD column remains the exploratory mood-disorder societal-cost proxy, not demonstrated treatment savings.
- Nationwide acquisition completed after one bounded retry pass. All 114 planned official tiles independently pass raw/output SHA-256 checks, raster metadata checks and deterministic comparisons between the source archive's band 20 and the extracted 2019 raster. The retained raw annual tiles occupy about 13 GB and the 114 extracted 2019 rasters about 2.5 GB. No national dense mosaic was required.
- The national support audit evaluated all 3,312 retained GUPPD features on native WorldPop cell centres. A total of 3,290 features have complete land-cover support. The other 22 contain 44 population-grid cells that map to GLC source fill code 0; none map to fill code 250. The affected feature rows sum to 459.093 people, but this is not a national total because GUPPD features may overlap. The lowest feature-level support fraction is 0.9971468 (Pataskala, source ID 22_16529); the largest affected feature total is 133.997 people (Philadelphia, source ID 30_12532). These are source fill/edge findings, not missing acquisition tiles. Preserve them as missing exposure and choose an explicit exclusion or sensitivity rule before national estimation.
- Reproducible completion records are in the external data tree: `manifests/us_local_completion.json`, `pilots/us_local_qc_2019_v1/acquisition_audit.json`, `coverage_summary.json`, and `city_land_cover_coverage.csv`. The completion monitor installed no scheduler or service.

During matched-source writes, GDAL emitted non-tiled block-size-option warnings. The output files were re-opened and all cellwise numeric checks passed; no result is inferred from a successful write alone. The existing outputs are retained with their recorded hashes.
