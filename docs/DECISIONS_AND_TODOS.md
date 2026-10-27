# Decisions and current work

Updated 27 October 2026. This is the authoritative live task register.
Completed output locations are in the [run registry](../config/run_registry.json);
input provenance is in the [data guide](DATA_SOURCES_AND_PREPROCESSING.md).
The [dated decision log](archive/DECISIONS_THROUGH_2026-10-25.md) preserves prior
checkpoints, including superseded pending statuses.

## Current decisions

| Topic | Decision | Evidence |
| --- | --- | --- |
| Primary US exposure | Retain direct annual-median 2019 Landsat NDVI. Both land-cover lookups remain technical sensitivities. | [Production and eight-scenario comparison](evidence/us_direct_ndvi_production_run.md) |
| Prevalence and denominator | GBD 2019 all-age depressive disorders with all-age WorldPop; retain fixed 5% as a separately labelled sensitivity. | [Health inputs](DATA_SOURCES_AND_PREPROCESSING.md#5-health-inputs) |
| Case reference state | Primary: additional cases relative to estimated current burden, `B × (1/r − 1)`. Retain the original literal `B × (1 − r)` as a sensitivity. | [Equation comparison](evidence/us_direct_ndvi_production_run.md#what-the-health-equations-change) |
| Reference risk and uncertainty | `p0=0.115` remains a transported assumption. Published intervals propagate OR limits only. | [Liu and p0 review](evidence/liu_2023_ndvi_p0_review.md) |
| Valuation | Report 2019 USD, no PPP. The project rate is an exploratory societal proxy; Varun and SNAPP rates are separate sensitivities with scope caveats. | [Cost and area report](evidence/varun_us_cost_comparison.md) |
| Geography | Active scope: 48 contiguous states plus DC; exclude Alaska, Hawaii and territories. Saved US results still include Alaska. SNAPP uses a different county domain. | [Area audit](evidence/data/varun_2026_10/us_urban_area_audit.json) |

## Open tasks

“Ready” means work can proceed with available inputs, not that a new run has
started. “Waiting” names the missing evidence and who can provide it. No task
below blocks reading or reproducing the saved US results.

| ID | Priority / status | Owner / waiting on | Concrete next action and completion evidence |
| --- | --- | --- | --- |
| UMH-10 | High · new boundaries prepared; totals pending | Project analyst | Re-run local national calculations and update cloud selection for contiguous US; reconcile all summaries and regenerate reports. Keep Alaska-inclusive evidence versioned. |
| UMH-01 | High · waiting for original result | Varun / Global GEP team | Obtain the US country row and run version behind the reported $61 million: case count, input geography, price/unit, aggregation and logs. Reconcile it to an explicit formula and output receipt. Current US reproduction does not explain that figure. |
| UMH-02 | High · waiting for cost provenance | Varun | Obtain `treatment_cost.xlsx` prediction/conversion code or ledger, cost components, country crosswalk, price year and explicit non-PPP basis. Accept a primary rate only after endpoint and currency checks. |
| UMH-03 | High · waiting for lookup provenance | Varun | Obtain NDVI sensor, months/year, mask/composite, calibration geography, class weights/counts, manual edits and generation code for `glc_fcs30d_attribute_table_processed_updated.csv`. His use of that table is already confirmed. |
| UMH-04 | High · ready to design matched comparison | Project analyst + team | Compare SNAPP and Global GEP on the same geography, population, prevalence endpoint, NDVI/composite, buffer, `p0`, formula and price year; change one factor at a time. Preserve each run's receipt. The existing totals are unmatched. |
| UMH-05 | Medium · evidence partly available | Project analyst; study authors for missing tables | Complete endpoint-matched low-exposure risks for the Liu study set, resolve Gonzales mapping and repeated outcomes, and pool compatible study-specific RRs. Keep transported `p0` scenarios explicit meanwhile. |
| UMH-06 | Medium · ready after parameter specification | Project analyst | Specify distributions/dependencies for prevalence, exposure, `p0`, effect and cost before Monte Carlo. Save seed, assumptions and intervals; do not relabel effect-only limits as full uncertainty. |
| UMH-07 | Medium · ready to scope validation | Project analyst + team | Hold out regions or years to compare class lookups with direct NDVI. Separate classification/exposure agreement from validation of the health relationship. |
| UMH-08 | Medium · pending manuscript review | Yingjie + methods team | Reconcile the Google Doc and comments with the selected run, denominator, reference state, price basis and uncertainty wording. Record the reviewed document version. |
| UMH-09 | Later · waiting for global source recipe | Varun | Supply land-cover release/merge recipe, population mosaic sources, polygon filters, inclusion list and a known-good global run. Required for close global reproduction, not the completed US sensitivities. |

## If adult current MDD becomes the endpoint

1. Agree the diagnosis and period first; CDC PLACES “ever diagnosed” is not current MDD.
2. Use adult population counts and matching adult MDD prevalence; preserve the all-age pathway as a separate scenario.
3. Select an exposure effect and reference-group `p0` compatible with that outcome; do not infer `p0` directly from national average prevalence.
4. Match the per-case cost population, components and year, then express it in 2019 USD without PPP.
5. Run a small matched-area pilot and compare cases before values. Expand only after denominator, reference-state and input-support checks pass.

## Maintaining this register

Update the row when evidence arrives; link the receipt and move resolved items
to the dated history when the table becomes crowded. Do not duplicate open
statuses in the README or data guide. Numerical claims belong in a report with
a linked run record. Reorganization on 27 October changed paths and navigation;
it did not create new health-model results.
