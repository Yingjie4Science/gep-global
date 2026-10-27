> Historical review dated 8 October 2026. For current input status use the [data guide](../../DATA_SOURCES_AND_PREPROCESSING.md#5-health-inputs). Source and script paths below were updated after the 27 October folder move; the original locations and checksums are in [the migration record](../../../config/health_input_migration_2026-10-27.json).

# Country depression prevalence: source review

Status: official 2019 country extract obtained and validated; **agreed as the proposed baseline source, but not yet joined or implemented as a model input**. Updated 8 October 2026.

## Recommended model input

The model multiplies prevalence by a 2019 **all-age** WorldPop count. The replacement for its fixed `0.05` should therefore be a 2019 country estimate for **both sexes, all ages, crude prevalence of depressive disorders**, expressed as a proportion. Use the IHME [GBD Results tool](https://vizhub.healthdata.org/gbd-results/) and select: GBD release 2023, estimate year 2019, cause *Depressive disorders*, measure *Prevalence*, metric *Rate*, age *All ages*, sex *Both*, population group *All Population*, and all countries/territories. Avoid age-standardized rates: they do not use the actual country age composition and are not directly multiplied by WorldPop all-age counts. Save the raw download, version, query settings, retrieval date, country identifiers, point estimate, lower and upper uncertainty bounds, and conversion from rate per 100,000 to a fraction where applicable. Check country coverage and naming against the model's urban polygons before a run. Do not silently fill missing countries with `0.05`.

The [GBD 2019 data resources](https://ghdx.healthdata.org/gbd-2019/datainput-sources) identify GBD Results as the official download route. Its published [mental disorders analysis](https://doi.org/10.1016/S2215-0366(21)00395-3) includes depressive disorders and 204 countries/territories in 2019. Access to the detailed extract can require a registered IHME account. The GBD release, age, measure, metric, and cause must be checked in the downloaded file before any rate replaces the code default.

## Official IHME extract obtained on 7 October 2026

The user signed in, and the GBD Results tool returned **204 countries and territories** for the exact query above. The [request details and source download](https://vizhub.healthdata.org/gbd-results/result/c1431a534b1726c9d2392bafb05a66f6) identify GBD **2023** as the release. The estimate **year is 2019**; do not call this a GBD 2019-release extract. The export used both IDs and names. The original ZIP, CSV, and IHME-provided `citation.txt` are retained in `data/raw/ihme_gbd_2023/`. The ZIP SHA-256 is `c084fe7fdb42ebe44e618d1078b2ef604ff6830712e0e4e7132132880212cb04`; the raw CSV SHA-256 is `3914f7ec30b38d4900c280330d28f5f4603436435dcb1ccc69beea9c5229432b`. The tool states that its result-page download is available for seven days after creation; the saved local copy remains available afterward.

The validated, analysis-ready table is [`gbd_2023_2019_depressive_disorders_country_prevalence.csv`](../../../data/processed/gbd_2023_2019_depressive_disorders_country_prevalence.csv), with one row per location and point, lower, and upper estimates. `scripts/01_inputs/import_gbd_depressive_disorders.py` verifies the selected dimensions, 204 unique location IDs, finite values, and interval order, then divides the crude rate per 100,000 by 100,000 to obtain a population fraction. The adjacent `.manifest.json` records the query, source request URL, retrieval date, and CSV/ZIP SHA-256 checksums. To reproduce it:

```sh
python scripts/01_inputs/import_gbd_depressive_disorders.py \
  --input data/raw/ihme_gbd_2023/IHME-GBD_2023_DATA-c1431a53-1.csv \
  --archive data/raw/ihme_gbd_2023/IHME-GBD_2023_DATA-c1431a53-1.zip \
  --output data/processed/gbd_2023_2019_depressive_disorders_country_prevalence.csv \
  --gbd-release 'GBD 2023' --estimate-year 2019 \
  --expected-locations 204 --retrieved-on 2026-10-07 \
  --source-url https://vizhub.healthdata.org/gbd-results/result/c1431a534b1726c9d2392bafb05a66f6
```

Spot checks: Bhutan 2.979% (2.523–3.572%), China 3.742% (3.371–4.197%), India 3.222% (2.780–3.823%), Brazil 3.500% (3.081–4.005%), and United States 4.243% (3.777–4.828%). These are GBD 95% **uncertainty intervals**, not confidence intervals from the NDVI effect meta-analysis. They are estimates for *depressive disorders* (including major depressive disorder and dysthymia in the GBD cause hierarchy), not a depression measure observed in each city. They also differ in release, year, and precision from the historical WHO table below.

**Adoption direction agreed; implementation and verification remain open.** The current model accepts one scalar `baseline_prevalence`, and its run was held pending unpublished spatial inputs. Country-specific values would require a country-to-polygon join, an explicit missing/duplicate-country policy, and a parameterized pipeline change; do not silently replace the scalar or treat national values as measured city rates. Check that the outcome in the pooled NDVI association is sufficiently comparable to GBD depressive disorders. The GBD intervals can form a separate prevalence sensitivity analysis, but combining them with effect-size uncertainty requires a stated method. `p0 = 0.115` has a distinct role in OR-to-RR conversion and is **not** replaced by the country-wide GBD prevalence. The shared-chat suggestion to calibrate country-specific `p0` from NDVI is a possible later sensitivity analysis, not something established by this download.

IHME's included citation reads: Global Burden of Disease Collaborative Network. *Global Burden of Disease Study 2023 (GBD 2023) Results*. Seattle: IHME, 2024. Available from https://vizhub.healthdata.org/gbd-results/. The GBD Results download interface notes that commercial use requires licensing; check that condition before external redistribution or commercial use.

## Repeat the extraction for a later year or GBD release

1. Sign in to the [IHME GBD Results tool](https://vizhub.healthdata.org/gbd-results/). Record the **GBD release** displayed by the tool separately from the **estimate year** you select. An updated release may revise its earlier-year estimates, so compare releases explicitly rather than treating their difference as a time trend.
2. Under **GBD Estimate**, select **Cause of death or injury**. Set **Measure = Prevalence** only, **Metric = Rate** only, and **Cause = Depressive disorders** only. Remove the tool's other default selections; a query with extra measures or causes can produce a mixed export.
3. Under **Location**, use **Select all countries and territories**. Remove **Global** and any regions if they remain selected. Set **Age = All ages**, **Sex = Both**, and **Year = the desired estimate year only**. Leave total percentage change off. The 2026 interface returned **All Population** as the population group in the resulting CSV; verify that column in any future export. For an age-specific model, choose a matching age group instead and adapt this validator before use.
4. Click **Search**. Check that the on-screen table shows Prevalence, Rate, Depressive disorders, the selected year, All ages, Both sexes, and country/territory locations. Check the row/location count. The 2019 export had 204; a future release may differ, so do not hard-code 204 as a universal count.
5. Click **Download**, choose **Both** IDs and names, and submit the export request. The tool sends a completion email and provides a **request-details** link. Save that link, the query settings, the returned ZIP, its CSV, and the included `citation.txt` together. The 2026 request page said download links last seven days. Check IHME's current terms before redistributing the data.
6. Run the importer with the new `--gbd-release`, `--estimate-year`, `--expected-locations`, `--retrieved-on`, and `--source-url` values. Name the output with **both** release and estimate year. The importer deliberately rejects extra locations, ages, measures, metrics, causes, sexes, years, duplicate IDs, invalid bounds, and non-finite values. It cannot independently establish that every selected location is a country: retain the UI selection evidence and inspect location IDs/names.
7. Inspect the new `.manifest.json`; compare its CSV and ZIP checksums with the saved raw files. Spot-check several countries against the IHME table; confirm the `rate_per_100000` and fraction fields agree. Before model use, join the country IDs to the project's polygons, report matched/unmatched locations, review changes in outcome definitions or country coverage, and keep `p0` separate from national prevalence. The current model still needs a country-aware prevalence input and cannot ingest this table directly.

For a future extract, copy the tested command in the section above and replace its input and output filenames, archive filename, release, estimate year, expected location count, retrieval date, and request URL with the new values. Never reuse the 204-location expectation without checking that release's country/territory selection.

## Historical WHO comparison table

`data/processed/who_depression_prevalence_2015_country.csv` contains 183 country rows transcribed from the Appendix (printed pages 17–21; PDF pages 19–23) of WHO's [*Depression and Other Common Mental Disorders: Global Health Estimates*](https://www.afro.who.int/sites/default/files/2017-05/WHO-MSD-MER-2017.2-eng.pdf). The report identifies these as **2015 GBD crude prevalence rates**, not age-standardized rates. They are both-sex, population percentage estimates for depressive disorders; they are not 2019 estimates. Percentages are published to one decimal place, so the fractional field retains only that precision. Country names are reproduced from the report, including historical names. Eleven names that wrap onto two PDF lines are joined in the CSV.

The source PDF had SHA-256 `a0c7ce63d269df3f59bbb536e2579c181724491b43de75c8649efffafbe7a75c`. To reproduce the CSV, download that PDF and run `python scripts/01_inputs/extract_who_depression_2015.py --pdf PATH_TO_PDF --output data/processed/who_depression_prevalence_2015_country.csv` with `pdfplumber`. Extraction checks 183 unique country rows. Manual spot checks against the PDF include Bhutan 4.2%, China 4.2%, India 4.5%, Brazil 5.8%, and United States of America 5.9%.

Do not use these 2015 rates as the default for the 2019 analysis without explicitly deciding to use an older proxy. The existing `0.05` comes from a WHO *adult* summary and is not denominator matched to all-age WorldPop. The separate `p0 = 0.115` comes from the least-green adult group in Hystad et al. (2019) and is used for odds-ratio conversion; country-wide rates do not automatically replace that parameter.

## Pending decisions

1. Review the obtained 2019 GBD 2023-release extract against the NDVI depression outcome; map its 204 locations to project country codes and decide whether to implement country-specific baseline prevalence. Keep `p0` separate.
2. Agree on the observed-case reference state and change the case formula and effect-size bounds together if the team accepts the proposed correction.
3. Audit each country cost to confirm 2019 USD with market exchange rates and no PPP adjustment.
4. Wait for the unpublished spatial inputs before validating raster joins and numerical outputs.
5. Review the pending Google Docs suggestions and comments; no suggestions have been accepted or threads resolved by this compilation.

The two public shared-chat URLs did not load. The later `codex://threads/019f655b-8bc3-7823-b9e2-0829e51e1a62` reference was accessible. Its three relevant recent exchanges on global prevalence and `p0` were reviewed; the long thread also contains separate U.S. case-study and NDVI export work, which was not audited in full. The chat recommends **adult, current MDD** prevalence and calibrated `p0`. This extract instead covers **all ages, depressive disorders (MDD plus dysthymia)** to match the current all-age WorldPop denominator. These are different endpoints, so the chat recommendation is not already implemented by the extract. Its matched-denominator principle is useful; calibration still needs endpoint, exposure, reference-state, and code review before adoption.

## Reference-group `p0` research — 8 October 2026

The team agreed to retain `p0 = 0.115` as a provisional scenario while seeking an outcome- and exposure-matched reference risk. See the [source review and practical replacement protocol](p0_source_and_strategy_review.md). Country GBD prevalence is for baseline cases and must not be relabelled as `p0`.

## `p0` desk pilot — 8 October 2026

See [pilot findings](p0_pilot_findings.md) and [calculated sensitivity table](p0_pilot_sensitivity_2019.csv). The 9.6% Hystad self-report low-NDVI figure is an outcome-aligned sensitivity candidate; it is not a validated global reference risk.

## Liu NDVI study extraction — 8 October 2026

The local Liu main article and author supplementary document have now been reviewed. See the [13-row study extraction](liu_2023_ndvi_study_extraction.csv) and [synthesis audit](liu_2023_ndvi_synthesis_audit.md). They record the nine named studies, repeated cohort outcomes, standardized forest effects, recoverable prevalence values, and unresolved source mismatches. No fully paired study-specific `p0` was recovered, so the extraction supports transparent scenarios and targeted data requests rather than a new pooled `p0`.
