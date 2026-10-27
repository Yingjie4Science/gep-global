> Historical full outputs are now in `data/archive/historical_pilots_through_2026-10-27.tar.gz` under `pilots/us_national_technical_2019_v1/`; commands below retain their original paths.

# 2019 US windowed technical run

Executed 17 October 2026. This is a nationwide **technical integration result**, not a production epidemiological estimate. The lookup remains exploratory and the monetary result remains a mood-disorder societal-cost proxy.

## Scope and reproducible method

- Scope: 3,312 retained GUPPD source features in 49 states plus DC; Alaska included; Hawaii and territories excluded.
- Population: supplied WorldPop 2019 constrained R2025A v1 raster.
- Land cover: 114 official Zenodo GLC_FCS30D annual tiles, 2019 band 20. Every raw and extracted tile passed independent hashes, metadata checks and deterministic source/output pixel comparisons.
- Membership: WorldPop native cell centres within each original GUPPD polygon, implemented with `geometry_mask(all_touched=False)`. The three positive-area polygon overlaps contain zero shared native population cell centres, so feature rows can be summed under this rule.
- Exposure: positive land-cover-derived NDVI set to zero. Source fill codes 0/250 and classes without a lookup are excluded from the primary modelled population.
- Epidemiological inputs: US all-age depressive-disorders prevalence 0.0424332878; `p0=0.115`; OR 0.931 with 95% limits 0.887–0.977 per +0.1 NDVI.
- Valuation: 10,999.206774445318 per person in 2019 USD without PPP in the reported currency. It is an exploratory mood-disorder total societal-cost proxy, not demonstrated depression treatment savings.

`build_pooled_us_lookup.py` sums raw NDVI-area, squared-NDVI-area, valid-area and class-area terms from Fort Morgan, Tucson, Portland, Anchorage and New York. It does not average city means equally. `run_us_national_technical.py` processes each source feature in a bounded WorldPop window and reads only intersecting verified land-cover tiles; it does not construct a dense national raster. It records input, source, output and per-tile-manifest hashes.

```sh
python scripts/01_inputs/build_pooled_us_lookup.py DATA_ROOT \
  DATA_ROOT/pilots/us_national_technical_2019_v1/lookup

python scripts/02_models/run_us_national_technical.py DATA_ROOT \
  DATA_ROOT/pilots/us_national_technical_2019_v1/run_002 \
  --lookup DATA_ROOT/pilots/us_national_technical_2019_v1/lookup/pooled_lookup_candidate.csv \
  --effects DATA_ROOT/processed/effect_size.xlsx \
  --prevalence data/processed/gbd_2023_2019_depressive_disorders_country_prevalence.csv \
  --crosswalk config/us_country_crosswalk.csv \
  --cost DATA_ROOT/processed/data_cost_mental_health_US_2019_USD.csv
```

## Technical result

| Quantity | Result |
| --- | ---: |
| Population in source features | 194,367,282.999126 |
| Population modelled | 194,359,293.686528 |
| Population on source fill code 0 | 459.093025 |
| Population on unrepresented class 185 | 7,530.219573 |
| Estimated observed cases on modelled population | 8,247,303.845605 |
| Additional case equivalents, point | 2,522,626.767240 |
| Conditional effect-limit lower | 742,974.977829 |
| Conditional effect-limit upper | 4,696,553.344681 |
| 2019 USD societal-value proxy, point | 27,746,893,427.63 |

The population total matches the independently reconciled cloud population total to floating-point precision. All 3,312 feature IDs are unique; population support, observed-case, interval-order, class-population, cost and output-hash checks pass.

The recorded `run_002` manifest pins implementation commit `c62bba9223e270284bdb867ba57f6dd1a68e6bc6`. Its feature, class and national CSV hashes are identical to the earlier pre-commit execution, providing a deterministic rerun check.

The primary result excludes 7,989.313 people with missing exposure support, about 0.0041% of the scoped population. A deliberately conservative structural sensitivity assigns them either zero additional cases or the maximum positive pooled class NDVI. Its upper addition is 209.488 cases, producing 2,522,836.255 cases. This is not a confidence interval.

## Lookup and source comparison

The five-region pooled lookup represents 26 of 27 classes observed in urban population cells. Mangrove class 185 has no valid estimate in the five lookup AOIs and remains missing. The pooled lookup is unsuitable for production: compared with each test city's reviewed city-specific 30 m lookup, it changes Anchorage by −12.2%, Portland by −14.7%, New York by −7.1%, and Tucson by +136.2%.

To separate lookup pairing from classification-source differences, `validate_zenodo_lookup_city_grids.py` downloads the reviewed 2019 Landsat 7/8 annual-median NDVI onto each test city's WorldPop grid. It derives separate class means for the local official Zenodo map and the Earth Engine community map from the same valid NDVI pixels and polygon mask.

| Feature | Zenodo-paired cases | Community-paired cases | Zenodo vs community |
| --- | ---: | ---: | ---: |
| Anchorage feature | 446.739 | 445.779 | +0.22% |
| Portland, Maine | 1,327.615 | 1,331.287 | −0.28% |
| Tucson | 3,096.772 | 3,117.840 | −0.68% |
| New York | 223,424.908 | 226,025.347 | −1.15% |

These paired differences are small in the four tests, but they do not establish national source equivalence. The same-grid Zenodo class lookup differs from direct pixel NDVI by +0.39% in Anchorage, −4.43% in Portland, +1.30% in Tucson, and +33.81% in New York. The New York result shows that class aggregation can dominate the land-cover-source difference.

## Decision and remaining gate

Use this run to verify input wiring, grid membership, missing-data accounting, formulas, interval direction, and scalable windowed execution. Do not publish its national case or dollar values as final results.

The next scientific gate is a reviewed production lookup strategy. Feasible options are a direct 2019 NDVI exposure run, region-specific lookups with a declared assignment rule and held-out validation, or a national lookup derived from official Zenodo classes and Landsat pixels with regional sensitivity reported. The four-city evidence favors direct NDVI or explicit regionalization over one pooled class lookup. Exact GEE/local regional parity also still requires a shared exported native-grid membership mask.
