# Urban mental health model: decisions and open work

## Controlled original-method comparison completed — 17 October 2026

This entry supersedes the earlier status notes that describe the national lookup, direct-NDVI production run, or comparison as pending. Historical checkpoints remain below for provenance.

- **Production decision:** retain direct 2019 Landsat NDVI as the primary US exposure. It preserves pixel-level exposure variation and avoids applying a nonlinear health transformation to a class mean.
- **Original-style sensitivity:** derive and publish a 2019 US urban GLC_FCS30D-to-NDVI attribute table, then run it beside direct NDVI. This is a newly calibrated InVEST-style table because Varun's original numeric lookup is absent from the source repository. It is not an exact reconstruction of his table.
- **Factorial comparison:** run both exposure methods with both prevalence choices (GBD 2019 all-age US rate 4.2433% and fixed 5%) and both health equations (current-reference and the literal original formula) on the same common valid WorldPop support. All eight scenarios use OR 0.931, `p0 = 0.115`, and the same 2019 USD non-PPP societal-cost proxy.
- **Result:** under the production prevalence/equation, the class lookup yields 2.43 million case equivalents, 1.16% below direct NDVI. Changing only prevalence from 4.2433% to 5% raises every matched result by 17.83%. With fixed 5% and class lookup, the literal original formula yields 2.18 million case equivalents and a $24.00 billion proxy.
- **Health-equation decision:** the equations are equivalent only after converting the burden reference state. With the same prevalence-derived numeric burden, Varun's literal `B × (1 − r)` and the current `B × (1/r − 1)` differ; the literal result is 23.66% lower for the class lookup and 26.30% lower for direct NDVI. Retain the current-reference equation for production and report the literal equation as a sensitivity.
- **Support and checks:** all 3,312 city receipts and 3,530 city-state rows passed exact-ID, metadata, finite-value, support-reconciliation, state-plus-residual, prevalence-scaling and valuation checks. The direct own-support result reproduces the prior production total to floating-point tolerance. Common support contains 194.37 million people and excludes 4.42 thousand with missing direct NDVI or land cover.
- **Attribute table:** 28 of 35 GLC classes have valid US urban 2019 NDVI estimates. The seven unsupported classes were absent from population-supporting cells, so lookup coverage itself excludes zero population in this run. Coverage status is separate from the `exclude` field; no scientific class exclusion was imposed. Preserve negative water and tidal-flat means, which produce zero positive-NDVI contrast.
- **Interpretation:** this is an in-sample representation and smoothing comparison because the lookup was calibrated and evaluated on the same national urban domain. National agreement conceals material city variation: among 2,468 cities with at least 100 direct current-reference case equivalents, the median class-versus-direct difference is −14.09%, the inclusive 5th–95th percentile range is −29.52% to +28.09%, and 75.61% differ by more than 10% in absolute terms. This does not validate transfer to other countries or establish which exposure representation is epidemiologically superior. Effect-size 95% limits remain available for the production run; differences among methods are sensitivity results, not confidence intervals.

Evidence is in [the concise production and method-comparison report](evidence/us_direct_ndvi_production_run.md) and [the packaged comparison outputs](evidence/data/us_method_comparison_2019_v2_common/).

### Remaining research and reporting work

1. Validate the class lookup on held-out regions or a later year before any claim of predictive validity or reuse outside US urban areas.
2. Replace or bound the transported `p0 = 0.115` assumption with endpoint-matched low-exposure risks when compatible study data become available.
3. Implement joint uncertainty across effect size, `p0`, prevalence, exposure and cost if a full uncertainty interval is required.
4. Revisit the adult-current-MDD pathway only with an age-aligned population denominator and endpoint-matched effect estimate.
5. Complete the final Google Doc reconciliation. The model run is no longer waiting for data access.

## Nationwide local land-cover completion — 17 October 2026

- The active scope remains 49 states plus DC, including Alaska and excluding Hawaii and territories. The official local GLC_FCS30D queue completed after one bounded retry pass.
- All 114 planned annual tiles pass independent raw/output SHA-256 checks, raster metadata checks, and deterministic comparisons of source band 20 with the extracted 2019 raster. Raw annual tiles occupy about 13 GB; the 114 extracted 2019 rasters occupy about 2.5 GB. A dense national mosaic is unnecessary.
- Actual land-cover support was checked for all 3,312 retained GUPPD features on native WorldPop cell centres. Of these, 3,290 have complete support. The other 22 contain 44 feature-row population cells mapped to source fill code 0; none map to fill code 250. Their feature-row population sum is 459.093, which must not be treated as a national total because source polygons may overlap.
- Lowest feature support is 99.7147% for Pataskala (22_16529); the largest affected feature total is 133.997 people for Philadelphia (30_12532). These are source fill/edge findings, not missing downloads. Treat the affected cells as missing exposure pending an explicit exclusion or sensitivity rule; do not assign built-up or zero NDVI silently.
- Completion evidence is outside Git under `data/urban_mental_health/manifests/us_local_completion.json` and `data/urban_mental_health/pilots/us_local_qc_2019_v1/`. The four expanded source-comparison tests remain complete.

Historical priority at this checkpoint was to choose the production exposure strategy. The completed comparison above resolves that choice in favor of direct NDVI for the US production result; the boundary-cell sensitivity and p0, endpoint, cost-proxy and uncertainty limitations remain.

## Nationwide windowed technical run — 17 October 2026

- Implemented a windowed runner over all 3,312 retained GUPPD features. It avoids a dense national raster, preserves the WorldPop centre-cell rule, reads only intersecting verified land-cover tiles, and records input/output/source and tile-manifest hashes.
- The three positive-area GUPPD overlap pairs contain zero shared WorldPop cell centres. Feature sums therefore do not double count under the declared local membership rule.
- Primary missing-data decision: exclude source fill codes and unrepresented lookup classes. Retain a structural sensitivity from zero added cases to the result obtained by assigning the maximum positive pooled class NDVI. Do not call this a confidence interval.
- Technical totals: 194,367,282.999126 people in scope; 194,359,293.686528 modelled; 2,522,626.767 point case equivalents with conditional effect limits 742,974.978–4,696,553.345; 2019 USD societal-value proxy 27.747 billion. These are not production results.
- Missing support comprises 459.093 people on source fill code 0 and 7,530.220 people on unrepresented mangrove class 185. The conservative missing-exposure upper adds 209.488 cases.
- A five-region pooled lookup is not accepted for production. Against city-specific lookups it changes Anchorage −12.2%, Portland −14.7%, New York −7.1%, and Tucson +136.2%.
- A same-grid paired-source diagnostic derived separate Zenodo/community class means from identical 2019 Landsat pixels. Paired case differences range from −1.15% to +0.22% across the four cities. Direct pixel NDVI versus the Zenodo class lookup differs by +33.81% in New York, identifying lookup aggregation/transfer as the larger unresolved issue.

Decision: retain the national run as technical integration evidence only. The preferred next scientific path is direct 2019 NDVI exposure or explicitly regionalized lookups with held-out validation. A single pooled class lookup must not be used for published national estimates. See `docs/evidence/us_national_technical_run.md`.

## Full US app scope — 16 October 2026

All3,312 GUPPD US urban areas excluding Hawaii have been uploaded to the Earth Engine app asset. The all-city interface in `invest-gee/urban_mental_health/us_code_editor.js` supports selection and city-specific lookup/calculation on demand. The one-city pilot was a verification stage, not a scope restriction. All-city results have not been precomputed or nationally validated. Public app publication and rendered checks are pending because both browser-control connections timed out. See that repository's `US_APP_STATUS.md`; do not present the Bhutan app URL as a mental health app URL.

## Executed pilot — 16 October 2026

The population file has arrived. Local Python and GEE Fort Morgan pilots are complete; all 877 modeled city cells pass the matched-input comparison. The real NDVI lookup and private pilot boundary asset are available. **Land-cover sources differ at native resolution**, so national expansion requires an explicit source choice. See [pilot evidence, reproduction and remaining work](evidence/fort_morgan_pilot.md). This supersedes earlier missing-population, unexecuted-lookup and runtime-blocked entries below. Public Bhutan app integration and scientific validation remain pending.


Updated 16 October 2026. The current readiness checklist below supersedes historical acquisition notes later in this file.

This record separates implemented behavior, accepted modelling decisions, evidence limitations, and work that still requires unpublished inputs. It should be read with the main [README](../README.md) and the [Liu NDVI evidence audit](evidence/liu_2023_ndvi_p0_review.md).


## Parallel Earth Engine implementation — 16 October 2026

User requested a parallel cloud implementation within `Yingjie4Science/invest-gee`, alongside the Bhutan app. The experimental module is in `urban_mental_health/` in that repository. The current local workflow remains the comparison reference.

- Earth Engine SDK access through project `natcap-gep` now works; the earlier default-project/access blocker is resolved for this path.
- Verified one US 2019 constrained R2025A v1 population image in `projects/sat-io/open-datasets/WORLDPOP/pop`, ID `USA_POP_2019_CN_100M_R2025A_V1`. Catalog image metadata matches the selected release labels; pixel identity with the user-downloaded raster is still unverified.
- Cloud computation can read GLC and population without completing the full national local download. Preserve the source population grid/counts and export city summaries plus small diagnostic subsets.
- The reviewed lookup, GUPPD cloud asset, polygon edge/overlap reconciliation, real-data comparison, cost interpretation and publication checks still remain. This is a project model port; do not describe it as an officially released InVEST mental health model or a validated Bhutan estimate.
- Local isolated pilot runtime imports and all 11 repository tests passed. GDAL/PROJ resource-directory warnings remain to resolve before local spatial execution. This supersedes the installation-only status below.

## Historical retry status — 16 October 2026

- Source-script blocker resolved: user pasted the Landsat code. See `evidence/shared_ndvi_script_review.md`; adaptation now uses merged L7/L8 2019 annual medians with documented QA changes. No numeric lookup CSV has been exported.
- Land cover checkpoint: 8/114 tiles were verified at this stage. The later 17 October completion record at the top of this file supersedes this checkpoint.
- Runtime: stopped stalled Conda solve; isolated pilot venv setup is being verified. Do not infer runtime readiness from installed-package names alone.
- Population: no completed raster found in the project WorldPop folder or matching US-2019 file in Downloads at this check; user download remains separate.
- Remaining run gates: finish/validate lookup and rasters; verify runtime imports; check population-grid overlaps; approve and package the societal-cost proxy as an explicit scenario; perform a small-city run and inspect outputs.

## Implementation progress — 16 October 2026

- Added explicit input flags to the runner: `--land-cover`, `--population`, `--ndvi-lookup`, `--effects`, `--urban-boundaries`, `--costs`. Explicit files are checked before execution; source files need not be renamed to historical global-input filenames.
- Fixed the sequential-feature-ID assumption: zonal statistics now join attributes using actual OGR FIDs from the precise vector used in aggregation. A regression test covers IDs 0, 7 and 42. All 11 repository unit tests pass in the existing geospatial environment; this is not an end-to-end raster run.
- Added `config/us_country_crosswalk.csv`: GUPPD `United States` maps explicitly to GBD location 102 (`United States of America`). Verified applied prevalence is 0.0424332878 for 2019.
- Added `scripts/check_us_boundaries.py`; the 3,312-feature subset has three positive-area overlap pairs of approximately 702.13, 422.35 and 473.28 m². Saved audit: `manifests/guppd_us_overlap_qc.json`. No geometry is altered. Pixel-level population duplication remains to be checked once population arrives.
- Acquisition update: 8 tiles were verified, then 106 transfers failed with TLS connection errors. Added an optional certificate-validated curl transport and restarted the resumable queue with two workers. Verified files are preserved. Read per-tile statuses for fresh progress; old failure statuses persist until the corresponding retry finishes.
- Started a separate Conda environment from `environment.yml` under the project's `.envs/urban-mental-health`; package solving/install and full import verification remain pending. Existing environments are not changed.
- Added `scripts/derive_glc_ndvi_2019_gee.js` as a **proposed replacement**, not a verified adaptation of the inaccessible shared script. It selects GLC band b20, uses QA-screened and scaled Landsat 8 Collection 2 observations from 2019, retains valid negative NDVI, computes annual pixel medians and area-weighted class summaries, and exports raw sums/coverage statistics. JavaScript syntax check passed; no Earth Engine execution or CSV export has occurred.
- The GEE script defaults to a Delaware export for inspection. After a successful pilot and source-method review, `STATES = ALL_STATES` creates per-state export definitions for 49 states plus DC. Pool raw NDVI-area sums divided by valid area, not unweighted state means. Require coverage/observation review before promoting any result to the model lookup. Full study uncertainty is not inferred from class SD.

## Current US test-run readiness — 16 October 2026

Scope: **49 states plus DC, including Alaska; Hawaii and US territories excluded**. No complete model run or validated monetary result has been produced. Population is being downloaded by the user; no further agent download is needed.

| Item | Verified state | Remaining action | Responsibility |
| --- | --- | --- | --- |
| 2019 population | User download underway | Check complete file, year/release, count units, nodata, CRS, extent, checksum and raster population sum | User supplies file; agent validates |
| 2019 GLC_FCS30D | All 114 planned tiles independently verified; actual support checked for all 3,312 retained features | Keep fill codes 0/250 missing, choose an explicit treatment for 44 source-fill cells, and align classes to population by nearest neighbor | Agent |
| Land-cover-to-NDVI lookup | No derived lookup CSV yet | Shared script text reviewed and adaptation updated; execute 2019 L7/L8 lookup exports and validate class coverage before use | Agent; Earth Engine execution remains blocked by access/timeouts |
| Urban polygons | 3,312 GUPPD polygons after Hawaii exclusion; valid geometries and unique source IDs; actual land-cover support audited | Resolve overlap accounting and the few differing Python/GEE boundary cells; preserve source-FID joins | Agent |
| Effect estimates | Workbook supplied: depression OR 0.931, limits 0.887–0.977 per 0.1 NDVI | Validate workbook loading in the model environment and record its hash | Agent |
| Country prevalence | Country GBD 2023 release / 2019 all-age depressive-disorder table already present | Confirm exact US country crosswalk and applied rate; no silent scalar fallback | Agent |
| US cost | 2019 USD conversion saved: 10,999.206774445318 per patient | Retain mood-disorder societal-cost label; review its use as a depression proxy; build the model-readable cost workbook or add CSV support with explicit status checks | Agent; scientific interpretation remains open |
| Runtime | Inspected invest environment has rasterio/geopandas; lacks hazelbean, rasterstats, dask, distributed, rioxarray and openpyxl | Build a separate environment from the repository specification; record resolved versions and test imports | Agent |
| Local input configuration | Runner still expects historical filenames/layout and an XLSX cost input | Add explicit path configuration or a documented input staging layout; point to the Hawaii-excluded polygons and reviewed derivatives | Agent |
| End-to-end verification | Pending | Fresh small-city run first; compare population/zonal sums, maps, country joins, case formulas and output bounds; then expand to the 49-state scope | Agent |

The **production land-cover-to-NDVI lookup remains the main unresolved scientific input**. Population and land-cover acquisition are complete. The other rows are integration, validation or interpretation work, not requests for additional user files.

### Lookup derivation to document before execution

- Source script: `https://code.earthengine.google.com/70c17ec2df3486da1c0013e3967c3619?accept_repo`. Its contents remain unverified because browser access has not succeeded reliably, even though the user opened it.
- Land-cover asset: `projects/sat-io/open-datasets/GLC-FCS30D/annual`, with 2019 selected as annual band 20. Record the community asset snapshot and compare class codes against the downloaded Zenodo release before assuming equivalence.
- Use the screenshot only as a format illustration: it shows NLCD classes. Derive GLC_FCS30D class values instead of copying NLCD codes or NDVI numbers.
- Proposed temporal basis: observations from calendar year 2019, with a per-pixel annual median followed by a declared area-weighted class mean. This is a proposed replacement method, not a verified description of the shared script or original lookup. Review seasonal coverage, especially Alaska; annual clear-sky observations are not evenly distributed through the year.
- Record sensor/collection, reflectance scaling, red/NIR bands, cloud/shadow/snow/saturation masks, minimum valid observation count, study extent, grid/resolution, sample design or full-pixel reduction, class counts, missing-data fraction, class spread and mean/median differences. Preserve valid negative NDVI values; mask fill codes 0/250 separately.
- Export model columns `lc_code` and `lc_ndvi`, with descriptions and quality/provenance columns alongside them. Water/wetland exclusion is a separate modelling decision. The current reclassification code does not consume an `exclude` column, so an annotation alone cannot implement exclusion.
- Compare the class lookup with direct Landsat NDVI in held-out urban areas. US-derived class means must not be silently reused as a validated global lookup.

### Reproducible run record and acceptance gates

1. Preserve original inputs; generate separately named derivatives. Save acquisition URL, product version, retrieval time, byte size and SHA-256 for each input; preserve raw conversion-factor snapshots.
2. Capture the Git commit, complete command/configuration, resolved environment/package versions, geographic exclusions, country crosswalk, source asset IDs, preprocessing operations and any random seed. Hash both input and output files.
3. Keep the cost conversion ledger: 2018 international dollars × original/matched PPP factor × country CPI2019/CPI2018 ÷ market FX2019. Distinguish the US reference-currency conversion from provisional non-US reconstructions. Do not label societal costs as direct treatment costs.
4. Record raster CRS, transform, shape, nodata, valid-data coverage, population totals before/after spatial operations, polygon counts/IDs and join failures. Fix the current sequential-FID assumption before relying on zonal joins.
5. Use a fresh output directory. Preserve logs and failure states; do not treat a partial download, skipped task or stale output as success. Resume downloads from their recorded queue/status, and do not overwrite source data.
6. Inspect small-city maps and numeric summaries before a national run. A technical test may assess mechanics with explicitly labelled scenarios, but cannot establish predictive or causal validity.
7. Report propagated effect-size limits as conditional intervals. The p0 sensitivity range is not a 95% CI, and full Monte Carlo uncertainty has not yet been implemented or validated.

### Work that does not block a first US technical test

Exact PPP-vintage recovery for non-US costs, Bulgaria reconciliation and the Europe aggregate can wait for expansion beyond the US. Stronger study-specific p0 synthesis, an adult-MDD endpoint and final Google Doc reconciliation remain research/reporting tasks. Their limitations must stay visible in any provisional output.

## Implemented and retained

1. **Baseline prevalence:** the primary workflow accepts country-specific 2019, both-sex, crude all-age prevalence of depressive disorders from the GBD 2023 release. This matches the all-age 2019 WorldPop denominator. The historical fixed 5% adult prevalence is retained only as an explicitly selected sensitivity value.
2. **Reference state for cases:** the model treats prevalence-derived 2019 cases as the observed state and estimates additional cases under the counterfactual exposure.
3. **Exposure counterfactual:** positive land-cover-assigned NDVI values are set to zero. Zero and negative values remain unchanged. This approximates a built-up-like exposure state; it does not relabel land-cover classes.
4. **Effect uncertainty:** the published OR confidence limits are propagated through the OR-to-RR conversion and case calculation. The resulting limits are conditional on fixed prevalence, `p0`, exposure, population, and costs.
5. **Cost metadata:** cost inputs must declare USD, price year 2019, and no PPP adjustment. These declarations are validation gates rather than proof of source provenance.

## `p0` decision

`p0` is the depression probability in the effect study's low-exposure reference group. It is used only to approximate an RR from an OR and must remain separate from country GBD prevalence used for baseline cases.

- Keep `p0 = 0.115` as the labelled legacy scenario. It comes from health-record depression diagnoses in Hystad et al.'s least-green 500 m quartile.
- Keep `p0 = 0.096` as a separate Hystad self-reported doctor-diagnosis scenario. It matches the outcome more closely but was reported for a 250 m exposure grouping rather than the 500 m effect.
- Retain `0.03–0.20` as a structural sensitivity range. It is not a 95% confidence interval.
- Do not replace `p0` with a country prevalence, a whole-sample study prevalence, or an average across incompatible outcomes.
- Do not pool study `p0` values and then apply that pooled value to Liu's pooled OR.

The current evidence does not identify a single globally valid reference risk. Values around 0.10–0.12 are empirically anchored in one low-exposure adult cohort and are broadly plausible against several whole-sample studies, but they remain endpoint-specific and geographically limited.

## Liu et al. (2023) evidence decision

Liu reports a pooled OR of 0.931 (95% CI 0.887–0.977) per 0.1 NDVI with I² above 94%. The review names nine studies but Figure 4 contains 13 estimates because three cohorts contribute multiple outcomes.

The extraction identified mixed symptom, clinical, claims, lifetime, and incident outcomes; repeated cohorts; a Hystad/Perry label error; a Brown sample-size typo; a participant-total mismatch; and an unresolved Gonzales exposure/outcome mapping. The supplementary Table S4 gives leave-one-estimate-out pooled ORs, not individual study effects. These limitations preclude interpreting the pooled OR as a universally transportable causal effect.

For any stronger synthesis:

1. Select one compatible outcome per independent cohort or use a model that accounts for correlated outcomes.
2. Retain only clearly mapped NDVI contrasts and resolve the Gonzales rows.
3. Obtain cases and denominators in the matching low-exposure group, or author-provided marginal standardized risks.
4. Convert each study-specific OR with its own matched `p0`.
5. Pool comparable log RRs using random effects with robust variance or a multilevel model, and report heterogeneity and a prediction interval.

## Open work

### Can proceed when source information is obtained

- Obtain Abraham Cottagiri depression counts by NDVI category.
- Obtain Song CES-D cases and denominators by NDVI quartile.
- Obtain Niu's dichotomous PHQ-2 supplementary model and low-exposure counts.
- Resolve Gonzales-Inca Appendix Table A2/model-to-forest mapping.
- Seek marginal standardized risks near NDVI zero from study authors where feasible.
- Audit every cost rate's source, original currency, original price year, market exchange-rate conversion, and inflation conversion to 2019 USD without PPP.

### Requires unpublished model inputs

- Validate country and polygon joins, urban feature identifiers, raster alignment, water treatment, NDVI lookup coverage, and country totals.
- Run the complete pipeline in a fresh output directory and inspect the run manifest and rendered/tabular outputs.
- Compare reported results with the validated run before making case or monetary claims.

## Reporting language

Describe results as conditional model estimates of additional depression-related cases and associated 2019 USD costs under a zero-positive-NDVI counterfactual. Do not describe them as observed diagnoses, validated causal effects, comprehensive uncertainty intervals, or verified societal savings until the corresponding evidence and input checks are complete.


## US input acquisition update — 2026-10-16

- Scope: acquire 2019 LULC for all 50 states and DC, including Alaska and Hawaii; a single-city tile is insufficient. Territories are outside this stated scope.
- Started an official GLC_FCS30D queue of 114 available annual tiles (12.93 GB compressed transfer), with resumable downloads, ZIP CRC verification, 2019 band extraction and checksums. This historical start record is superseded by the completed 17 October audit at the top of this file.
- Coverage gate at this stage: 3,312 of 3,337 US GUPPD polygons fell within planned tile extents; the other 25 were Hawaiian. Hawaii was subsequently excluded by the user, and the retained 3,312-feature scope has now been audited against actual raster support.
- GUPPD is supplied and the US derivative has 3,337 features, no invalid geometry and no duplicate SMOD_ID. Preserve all settlement levels pending overlap review; verify zonal-statistic FID joins before a model run.
- Retrying the exact WorldPop page 75977 download: 2019, 100 m, constrained R2025A v1. This is an updated-input scenario relative to the original archived WorldPop mosaic. Partial downloads are not usable inputs.
- Cost CSV is supplied but all 33 rows identify 2018 USD PPP, mood disorders, total societal cost per patient. It fails the agreed 2019 USD non-PPP treatment-cost basis. Recover original currency/year and conversion provenance and resolve cost-component/endpoint scope before monetary output.
- Still needed from the original owner: land-cover/NDVI table and its derivation, original population mosaic details, and cost conversion ledger. Raster alignment, valid-data coverage, settlement overlap, test run and final output review remain open.

Reproduction commands are documented in `DATA_SOURCES_AND_PREPROCESSING.md`; large data and local acquisition status remain outside Git.


## Latest user decisions and conversion results — 2026-10-16

- Exclude Hawaii; active scope is 49 states plus DC, with Alaska included. Prepare the 3,312-polygon derivative and retain the complete source copy.
- WorldPop download is assigned to the user. Agent transfer stopped; validate the completed user-supplied raster when available.
- Costs are attributed to Christensen et al. (2020). A reproducible reverse-PPP / local-CPI / market-FX conversion now produces 2019 USD derivatives. US value: $10,999.21 per patient. Thirty other country conversions are provisional because revised WDI GDP PPP replaces the unrecovered original factor vintage.
- Remaining cost tasks: recover original PPP factors for exact non-US conversion; reconcile Bulgaria currency units; disaggregate Europe or omit it; decide whether mood-disorder societal cost is an acceptable depression cost proxy. Do not treat these as direct treatment-cost rates.
- User supplied an NDVI reference script and GEE GLC_FCS30D asset. Verify the shared script, derive a documented 2019 class lookup, and retain coverage/QA statistics. Screenshot NLCD class codes are examples only.


## Separate US GEE app and USD reporting — 2026-10-17

Published app: https://natcap-gep.projects.earthengine.app/view/us-urban-mental-health. Source lives in the invest-gee repository under urban_mental_health, with a saved EE script users/yingjieli/invest_gee:US_Urban_Mental_Health.

- The interface includes city cases and 2019 USD valuation, conditional effect-only limits, landscape comparison, native-cell maps, national/state summaries, state charts and CSV download links. All 3,312 GUPPD urban areas excluding Hawaii are selectable; Alaska is included.
- Valuation uses the reproducibly converted US rate of 10,999.206774445318 USD per patient, with no PPP adjustment in the reported currency. It remains an exploratory mood-disorder total societal-cost proxy. Source model_ready=false is preserved; this is not a validated depression-treatment saving.
- Anonymous public startup, Fort Morgan case/USD results, metric switching and state table rendering were checked. Fort Morgan showed 63.1 case equivalents and $694,017, with conditional limits 19.3–112.9 and $212,089–$1,241,753.
- National population summaries cover all urban units, totaling 194,367,282.99912596 people. Deterministic overlap allocation, geometric state intersections and residual accounting reconcile exactly in cell count (17,669,067), within floating-point tolerance for population.
- All 332 health/valuation chunks were submitted. Verified completed batches appear in the public app, clearly marked partial. At the final public UI check, 250 of 3,312 city receipts were available; this checkpoint will become stale as processing continues.

### Remaining release checks

- Complete all city health batches and reconcile national = state contributions + boundary residual, including missing-data support. Resume the documented local publisher if the host stops.
- Complete large-city and Alaska interactive checks, native-cell inspection and downloaded-file validation for the new interface. State summary chart rendering already includes Alaska completed contributions.
- Resolve the community GLC versus local Zenodo release difference before claiming identical land-cover inputs.
- Continue study-matched p0 synthesis and endpoint/cost applicability review. Conditional limits do not cover these assumptions.
- Reconcile final model language and comments in the Google Doc after full output review.


## Expanded local tests and acquisition — 2026-10-17

- Executed Tucson30_12305, Portland(Maine)30_12572, Anchorage feature23_87444, and New York30_12545. These are GUPPD source features, not municipality definitions.
- All four matched-cell Python/GEE checks pass for point/lower/upper case bands, covering788,807population cells. Population raster values agree exactly and no city population lacks the tested land-cover/lookup support.
- Fixed-lookup source sensitivity: different class fractions8.04%,16.60%,30.05%,12.86%; local case changes+0.24%,+1.42%,+3.89%,+0.66%, respectively. Do not claim source equivalence.
- Regional membership differs by+1cell(Tucson),0(Portland),−1(Anchorage),+6(New York). Same-cell formula checks do not resolve geographic reduction parity. A planar New York geometry diagnostic alone did not remove the difference.
- Official acquisition: all 114 planned tiles independently pass raw/output hashes, raster metadata checks and deterministic band-20 sample comparisons. The bounded retry completed; no downloader or monitor remains active.
- The national urban-coverage audit completed for all 3,312 retained features. A total of 3,290 have complete support; 22 contain 44 feature-row cells mapped to source fill code 0. This is a source support finding rather than an acquisition gap. Status is `data/urban_mental_health/manifests/us_local_completion.json`; detailed results are under `pilots/us_local_qc_2019_v1/`.

### Still required before production parity claims

1. Choose and document an exclusion or sensitivity treatment for the 44 source-fill cells; do not silently assign an exposure value.
2. Resolve the few differing boundary cells with a shared native-grid membership rule.
3. Derive or validate the NDVI lookup against the chosen production land-cover snapshot. Completed source tests hold the community-derived lookup fixed to isolate classification differences.
4. Retain p0/endpoint/cost limitations, conditional effect-only uncertainty, and final methods-document reconciliation.

Full results and provenance are in docs/evidence/expanded_city_tests.md, expanded_city_summary.csv and expanded_city_comparisons.json. Original pilot outputs are preserved.
