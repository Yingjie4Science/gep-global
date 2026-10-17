# 2019 US urban mental health direct-NDVI production run

Completed 2026-10-17. Status: **nationwide calculation complete; internal checks passed**. A small cross-engine boundary-cell difference is reported below.

## Result at a glance

| Quantity | Result |
| --- | ---: |
| GUPPD urban features | 3,312 |
| Population in scope | 194,373,474.370 |
| Population with valid NDVI | 194,370,858.997 (99.99865%) |
| Population without valid NDVI | 2,615.374 (0.00135%) |
| Baseline depressive-disorder case equivalents on modelled population | 8,247,794.6 |
| Additional case equivalents under the zero-positive-NDVI counterfactual | **2,453,460.5** |
| Conditional 95% effect-size limits | 714,769.0 to 4,626,257.9 |
| 2019 USD societal-value proxy | **$26.99 billion** |
| Conditional value limits | $7.86 billion to $50.89 billion |

The case result estimates the modelled increase in depressive-disorder case equivalents if every positive 2019 NDVI value in the scoped urban population cells were set to zero. It is a counterfactual model output, not an observed case count or a forecast. The monetary result multiplies this case contrast by a transported mood-disorder societal-cost proxy.

## Scope and method

- Geography: 3,312 GUPPD urban polygons in 49 states plus DC. Alaska is included; Hawaii and territories are excluded. Overlapping source polygons are assigned to the lexically first `SMOD_ID`; state pieces plus the boundary residual form disjoint reporting units.
- Population: WorldPop 2019 constrained R2025A v1 on its native 3-arc-second grid. Reductions are unweighted and use the reviewed city/state reporting geometries.
- Exposure: annual median of valid Landsat 7 and 8 Collection 2 Level 2 NDVI during 2019. QA bits 0–5, saturation, reflectance and denominator checks are applied; at least three observations are required. The nearest 30 m NDVI value is sampled at each WorldPop cell centre, matching the four-city diagnostic.
- Health calculation: US all-age depressive-disorders prevalence 0.0424332878; `p0=0.115`; OR 0.931 with 95% CI 0.887–0.977 per +0.1 NDVI. `p0` converts the OR to an RR. Positive NDVI is reduced to zero in the counterfactual; nonpositive NDVI has zero exposure difference.
- Valuation: 10,999.206774445318 per case equivalent, reported in 2019 USD without PPP. This is a mood-disorder total societal-cost proxy derived from Christensen et al. (2020) and US CPI conversion, not demonstrated treatment spending or cash savings.

## Largest state contributions

| State | Modelled population | Additional case equivalents | 2019 USD proxy |
| --- | ---: | ---: | ---: |
| CA | 35,845,328 | 289,739 | $3.19 billion |
| TX | 17,764,973 | 232,001 | $2.55 billion |
| FL | 15,472,843 | 217,032 | $2.39 billion |
| NY | 14,948,074 | 157,016 | $1.73 billion |
| IL | 9,929,819 | 139,204 | $1.53 billion |
| OH | 6,101,634 | 101,524 | $1.12 billion |
| MI | 5,571,987 | 97,189 | $1.07 billion |
| NJ | 6,947,891 | 89,445 | $0.98 billion |
| PA | 6,297,303 | 82,050 | $0.90 billion |
| VA | 4,462,937 | 72,547 | $0.80 billion |

These rows reflect only the GUPPD urban areas intersecting each state. State values may be compared within this run, but should not be read as whole-state burden estimates.

## Method sensitivity

The earlier five-region pooled land-cover lookup produced 2,522,627 case equivalents. The direct-NDVI result is -2.7% different. This is a method sensitivity comparison, not an uncertainty interval; the pooled lookup was rejected for production because it transferred poorly among test cities.

The four-city gate reproduced the earlier direct-grid estimates closely: exactly for Portland, and within 0.0027% for Anchorage, 0.0021% for Tucson and 0.0003% for New York. The small differences match previously identified boundary-cell membership differences.

## Verification and reproducibility

- All 133 Earth Engine table batches completed.
- Exactly 3,312 unique expected city receipts were recovered; no city was duplicated or omitted.
- The 50 state/DC summaries plus the boundary residual (7,008.7 people; 87.4 case equivalents) reconcile to the national totals.
- Population total equals modelled plus missing-NDVI population within numerical tolerance.
- Case and value limits are ordered correctly, and value arithmetic reproduces cases multiplied by the cost proxy.
- Model source commit: `66e9c165700eba391fdfef8857856840a803bb8e`; model graph SHA-256: `1df0d08b896c29c0a1bbef8d3c71656f6322acdf40ce27de449405cf0223ac98`.
- Machine-readable outputs: [national summary](data/us_direct_ndvi_2019_v1/national_summary.json), [state summary](data/us_direct_ndvi_2019_v1/state_summary.csv), [city summary](data/us_direct_ndvi_2019_v1/city_summary.csv), [city-state rows](data/us_direct_ndvi_2019_v1/city_state_rows.csv), and the [task manifest](data/us_direct_ndvi_2019_v1/direct_ndvi_batch_manifest.json).

The Earth Engine reporting geometry contains 194,373,474.370 people, 6,191.371 (0.00319%) more than the independent local native-cell-centre audit. The difference is distributed across 1,456 feature totals and reflects the known cross-engine boundary-cell membership sensitivity. The reported production values retain the reviewed Earth Engine reporting units and are not rescaled to the local population total.

## Interpretation limits

The 95% limits propagate only the published effect-size interval. They hold `p0`, prevalence, population, NDVI, geographic membership and cost fixed. The exposure-response estimate and `p0` are transported assumptions; the all-age GBD prevalence is aligned with the all-age WorldPop denominator but is not an adult current-MDD endpoint. GUPPD features are physical urban extents rather than municipal boundaries. The cost factor is broader than depression treatment cost, so the dollar figure is best reported as an exploratory societal-value proxy. A future Monte Carlo analysis should jointly vary the effect, `p0`, prevalence, exposure and cost inputs.
