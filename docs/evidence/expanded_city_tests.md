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

## Current checkpoint

The four city-specific lookup evaluations and native-grid cloud input readbacks completed. Official local tile acquisition and expanded matched-input outputs remain in progress; no completed national coverage or expanded numeric parity claim is made at this checkpoint.
