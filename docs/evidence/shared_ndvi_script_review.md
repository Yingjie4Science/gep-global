# Shared Landsat script review — 16 October 2026

Source: user pasted the contents associated with https://code.earthengine.google.com/70c17ec2df3486da1c0013e3967c3619?accept_repo into this chat. This is a review of supplied text; browser execution is not verified.

## What the supplied script actually does

- Loads Landsat 5, 7 and 8 Collection 2 Tier 1 Level 2 data over a user-defined `AOI`; filters 1986-01-01 to 2024-12-31 (exclusive end).
- Applies optical scale 0.0000275 and offset -0.2 before calculating NDVI; thermal scaling is present but is not needed for NDVI.
- Uses red/NIR bands B3/B4 for L5/L7 and B4/B5 for L8. Calculates per-scene normalized differences, merges sensors and computes calendar-year pixel medians for 2010–2021.
- Explicit selected exports are 2010, 2011, 2020 and 2021. **2019 is included in the composite collection but is not exported.**
- No GLC_FCS30D layer, class reduction, lookup CSV, spatial class statistic or class sampling scheme appears. This script therefore does not establish how the original model lookup was generated.

## Changes made in the lookup adaptation

1. Restrict the calculation to 2019-01-01 through 2020-01-01 (exclusive). Merge L7 and L8 NDVI; L5 is unavailable in 2019. Retain the annual median of per-observation NDVI rather than deriving NDVI after a reflectance composite.
2. Preserve Collection 2 optical scaling and band mapping. Use an explicit ratio with nonnegative red/NIR and positive-denominator screening; valid negative NDVI is retained. The supplied `normalizedDifference` also masks negative input-band values implicitly.
3. Mask QA_PIXEL bits 0–5. The supplied active mask uses bits 0–4 and does not exclude snow. Its unused `cloud` variable and accompanying older bit comments are not the active mask and should not be copied into the new method description.
4. Require QA_RADSAT = 0 for both sensors. The supplied script applies this to L8 but not L5/L7. This is a stricter QA choice and must be disclosed. L7 scan-line gaps remain masked rather than filled.
5. Add a proposed minimum of three valid observations per pixel; export observation and valid-area diagnostics. Test seasonal/observation-threshold sensitivity, especially for Alaska; this threshold was not in the supplied script.
6. Select GLC annual band b20 (2019), mask fill 0/250, reduce on an explicit equal-area 30 m analysis grid, and export per-class area-weighted means plus raw sums, counts, spatial SD and coverage. These class aggregation steps are new and have not been validated against the original lookup.
7. Keep Hawaii excluded. The script starts with Delaware; national execution uses 49 states plus DC and per-state exports. Whole-state means are an initial lookup scenario; compare urban-only/regional means before generalizing to GUPPD urban exposures.
8. Retain negative NDVI and valid water values for diagnostics. Screenshot NLCD codes/exclusions are not applied to GLC. Missing classes are null, never zero. Snow/permanent-ice classes may lack adequate snow-free observations and require explicit handling.

## Remaining execution gates

The updated JavaScript passes syntax checking only. Run a small export in a registered Earth Engine project, verify reducer output keys and schema, inspect valid-area and sensor/seasonal coverage, compare community GLC labels/values with local Zenodo tiles, and review means against direct Landsat NDVI. Pool state raw sums using valid area, not equal state weighting. A class SD is spatial spread, not a 95% CI. No lookup CSV or real-data validation has yet been produced.
