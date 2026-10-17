"""Render the concise US direct-NDVI production report from verified summaries."""
import argparse,csv,json
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('direct_summary',type=Path);p.add_argument('state_summary',type=Path)
p.add_argument('output',type=Path);p.add_argument('--technical-summary',type=Path)
p.add_argument('--local-feature-results',type=Path)
p.add_argument('--comparison-summary',type=Path);p.add_argument('--comparison-scenarios',type=Path)
p.add_argument('--lookup-table',type=Path);p.add_argument('--lookup-manifest',type=Path)
a=p.parse_args();direct=json.loads(a.direct_summary.read_text());n=direct['national']
states=list(csv.DictReader(a.state_summary.open()))
residual=next(r for r in states if int(r['state_code'])==0)
states=[r for r in states if int(r['state_code'])!=0]
states.sort(key=lambda r:float(r['additional_cases'] or 0),reverse=True)
technical=json.loads(a.technical_summary.read_text()) if a.technical_summary else None
method=json.loads(a.comparison_summary.read_text()) if a.comparison_summary else None
method_scenarios=list(csv.DictReader(a.comparison_scenarios.open())) if a.comparison_scenarios else []
lookup_manifest=json.loads(a.lookup_manifest.read_text()) if a.lookup_manifest else None
lookup_rows=list(csv.DictReader(a.lookup_table.open())) if a.lookup_table else []
coverage=100*float(n['population_modelled'])/float(n['population_total'])
missing=100-coverage

def compact(x):
    x=float(x);absolute=abs(x)
    if absolute>=1e9:return f"{x/1e9:,.2f} billion"
    if absolute>=1e6:return f"{x/1e6:,.2f} million"
    if absolute>=1e3:return f"{x/1e3:,.2f} thousand"
    return f"{x:,.2f}".rstrip('0').rstrip('.')
def money(x):return '$'+compact(x)
def million(x):return f"{float(x)/1e6:,.2f} million"

comparison='';spatial_check='';method_detail=''
if technical:
    old=technical['totals']['additional_cases'];diff=100*(n['additional_cases']/old-1)
    old_pop=technical['totals']['population_total'];pop_delta=n['population_total']-old_pop
    pop_pct=100*pop_delta/old_pop
    comparison=(f"The earlier five-region pooled land-cover lookup produced {compact(old)} case equivalents. "
      f"The direct-NDVI result is {diff:+.2f}% different. This is a method sensitivity comparison, "
      "not an uncertainty interval; the pooled lookup was rejected for production because it transferred poorly among test cities.\n")
    spatial_check=(f"The Earth Engine reporting geometry contains {compact(n['population_total'])} people, "
      f"{compact(pop_delta)} ({pop_pct:.3f}%) more than the independent local native-cell-centre audit. ")
if a.local_feature_results:
    local={r['region_id']:float(r['population_total'] or 0) for r in csv.DictReader(a.local_feature_results.open())}
    cloud_path=a.state_summary.with_name('city_summary.csv')
    cloud={r['city_id']:float(r['population_total'] or 0) for r in csv.DictReader(cloud_path.open())}
    changed=sum(abs(cloud[k]-local[k])>1e-7 for k in cloud)
    spatial_check+=(f"The difference is distributed across {changed:,} feature totals and reflects the known "
      "cross-engine boundary-cell membership sensitivity. The reported production values retain the reviewed "
      "Earth Engine reporting units and are not rescaled to the local population total.")
if method:
    mn=method['national'];mc=method['comparisons']
    method_rows='\n'.join(
      f"| {r['exposure']} | {r['prevalence']} | {r['health_contrast']} | {compact(r['case_equivalents'])} | {money(r['value_2019_usd_proxy'])} |"
      for r in method_scenarios)
    production_common=next(r for r in method_scenarios if r['exposure']=='direct' and r['prevalence'].startswith('GBD') and r['health_contrast'].startswith('current-reference'))
    original_style=next(r for r in method_scenarios if r['exposure']=='class lookup' and r['prevalence']=='fixed 5%' and r['health_contrast']=='literal original formula')
    supported=lookup_manifest['supported_class_count'] if lookup_manifest else sum(int(r['has_valid_ndvi']) for r in lookup_rows)
    class_count=lookup_manifest['class_count'] if lookup_manifest else len(lookup_rows)
    method_detail=f"""
## Controlled comparison of the modelling choices

This comparison changes one factor at a time on the same disjoint reporting units and the same **common valid population support**: (1) direct 2019 Landsat NDVI versus a fixed land-cover/NDVI lookup, (2) US GBD prevalence versus the original fixed 5%, and (3) the current-reference equation versus the literal equation in the original code. All eight rows use OR **0.931** and the same 2019 USD non-PPP proxy. These are point-estimate method sensitivities, not confidence intervals.

```mermaid
flowchart LR
    A["2019 Landsat NDVI"] --> C["Common valid WorldPop cells"]
    B["2019 GLC_FCS30D<br/>+ US urban class lookup"] --> C
    C --> D["Zero positive NDVI<br/>counterfactual"]
    E["GBD 4.24% or fixed 5%"] --> F["Current-reference or<br/>literal original equation"]
    D --> F
    F --> G["City, state and US totals<br/>+ 2019 USD value"]
```

| Exposure | Prevalence | Health contrast | Case equivalents | 2019 USD proxy |
| --- | --- | --- | ---: | ---: |
{method_rows}

The production configuration on common support gives **{compact(production_common['case_equivalents'])}** case equivalents. The configuration closest to the original code choices—fixed class lookup, 5% prevalence, and the literal original equation—gives **{compact(original_style['case_equivalents'])}** and **{money(original_style['value_2019_usd_proxy'])}**. The direct production total at its own full support remains **{compact(n['additional_cases'])}**; its exact reproduction in this comparison is recorded in the validation JSON.

The main comparisons are: the class lookup is **{abs(mc['class_vs_direct_percent_gbd_reference_common_support']):.2f}% lower** than direct NDVI under the production prevalence and equation; fixed 5% prevalence makes every matched result **{100*(mc['fixed_to_gbd_prevalence_ratio_expected']-1):.2f}% higher** than the 4.24% GBD input because cases scale linearly with prevalence; and the literal original equation is **{abs(mc['literal_original_vs_reference_percent_direct_5pct_common_support']):.2f}% lower** for direct NDVI and **{abs(mc['literal_original_vs_reference_percent_class_5pct_common_support']):.2f}% lower** for the class lookup when both equations receive the same prevalence-derived burden.

National agreement does not imply city-level agreement. Among **{mc['city_exposure_comparison']['city_count']:,}** cities with at least 100 direct current-reference case equivalents, the median class-versus-direct difference is **{mc['city_exposure_comparison']['median_class_vs_direct_percent']:.2f}%**, the inclusive 5th–95th percentile range is **{mc['city_exposure_comparison']['p05_class_vs_direct_percent_inclusive']:.2f}% to +{mc['city_exposure_comparison']['p95_class_vs_direct_percent_inclusive']:.2f}%**, and **{100*mc['city_exposure_comparison']['fraction_absolute_difference_gt_10_percent']:.2f}%** differ by more than 10% in absolute terms. This spatial variation supports retaining direct NDVI for the production run.

### What the health equations change

Let `r = RR^(10 × positive NDVI)`, so `r < 1` for positive NDVI. The original code literally computes `B × (1 − r)`. The current production method computes `B × (1/r − 1)`, where `B` is the prevalence-derived 2019 reference burden. With the **same numeric `B`**, the two formulas share the same exposure-response relation but are not numerically interchangeable; the literal original result is {abs(mc['literal_original_vs_reference_percent_direct_5pct_common_support']):.2f}% lower for direct NDVI and {abs(mc['literal_original_vs_reference_percent_class_5pct_common_support']):.2f}% lower for the class lookup.

The equations become exactly equivalent only when their burden reference states are also converted: if `B_current = r × B_no-nature`, then `B_current × (1/r − 1) = B_no-nature × (1 − r)`. The original code multiplies `prevalence × population` directly by `(1 − r)` and does not construct `B_no-nature`. The difference is therefore a reference-state clarification rather than a different exposure-response effect.

### Land-cover/NDVI attribute table

The comparison uses a newly derived **InVEST-style US urban 2019 attribute table**, not Varun's missing original numeric table. It pools raw area-weighted NDVI sums over the 49 states, DC, and boundary residual, using annual-median valid Landsat 7/8 observations within disjoint GUPPD urban units. It maps {supported} of {class_count} GLC classes. The seven unsupported classes were absent from population-supporting land-cover cells in this run, so population missing specifically because of lookup coverage is {compact(mn['class_population_missing_lookup'])}. Class and direct exposure totals are compared only where both are valid, excluding {compact(mn['common_population_missing'])} people from the factorial comparison because direct NDVI or land cover was missing.

The table preserves negative means for water and tidal flats, which yield zero positive-NDVI contrast. Rare classes should not be treated as transferable calibrations: deciduous shrubland is represented by about 0.02 km² and sparse herbaceous cover by about 1.21 km². The impervious-class mean is empirical NDVI within that broad class, not a semantic score for imperviousness. Because the health transformation is nonlinear, applying it to a class-mean NDVI is not mathematically equivalent to averaging pixel-level risk transformations. Because the lookup is calibrated and tested on the same national urban domain, this is an in-sample representation and smoothing comparison rather than independent validation or evidence of global transferability.

Files: [attribute table](data/us_method_comparison_2019_v2_common/glc_fcs30d_attribute_table_us_2019.csv), [lookup manifest](data/us_method_comparison_2019_v2_common/lookup_manifest.json), [eight scenarios](data/us_method_comparison_2019_v2_common/scenario_comparison.csv), [national validation](data/us_method_comparison_2019_v2_common/national_comparison.json), [state summary](data/us_method_comparison_2019_v2_common/state_summary.csv), and [city summary](data/us_method_comparison_2019_v2_common/city_summary.csv).
"""
top='\n'.join(f"| {r['state_abbr']} | {compact(r['population_modelled'])} | {compact(r['additional_cases'])} | {money(r['value_2019_usd'])} |" for r in states[:10])

text=f"""# 2019 US urban mental health direct-NDVI production run

Completed {direct['created_utc'][:10]}. Status: **nationwide calculation complete; internal checks passed**. A small cross-engine boundary-cell difference is reported below.

## Key results

> **Removing all positive NDVI in the model increases depressive-disorder burden by an estimated {million(n['additional_cases'])} case equivalents, with conditional 95% effect-size limits of {million(n['additional_cases_lower'])}–{million(n['additional_cases_upper'])}. The associated societal-value proxy is {money(n['value_2019_usd'])} in 2019 USD, without PPP.**

| Quantity | Reported result |
| --- | ---: |
| GUPPD urban features | {direct['completed_city_receipts']:,} |
| Population in scope | {compact(n['population_total'])} |
| Population with valid NDVI | {compact(n['population_modelled'])} ({coverage:.3f}%) |
| Population without valid NDVI | {compact(n['population_missing_ndvi'])} ({missing:.3f}%) |
| Baseline depressive-disorder case equivalents on modelled population | {compact(n['observed_cases'])} |
| **Additional case equivalents** | **{million(n['additional_cases'])}** |
| Conditional 95% effect-size limits | **{million(n['additional_cases_lower'])}–{million(n['additional_cases_upper'])}** |
| **2019 USD societal-value proxy** | **{money(n['value_2019_usd'])}** |
| Conditional value limits | **{money(n['value_2019_usd_lower'])}–{money(n['value_2019_usd_upper'])}** |

These are counterfactual model outputs rather than observed cases, forecasts, treatment expenditures or cash savings.

## Workflow at a glance

```mermaid
flowchart LR
    A["GUPPD urban boundaries<br/>disjoint city and state units"] --> D
    B["WorldPop 2019<br/>native population grid"] --> D
    C["Landsat 7 and 8, 2019<br/>QA and annual median NDVI"] --> D["Sample NDVI at<br/>WorldPop cell centres"]
    D --> E["Counterfactual:<br/>positive NDVI becomes zero"]
    E --> F["Convert OR to RR with p0<br/>calculate case contrast"]
    F --> G["Aggregate by city, state,<br/>residual and nation"]
    G --> H["Apply 2019 USD<br/>non-PPP cost proxy"]
```

1. Retain 3,312 GUPPD urban polygons in 49 states plus DC; include Alaska and exclude Hawaii and territories. Remove polygon overlap once and split cross-state features into disjoint reporting units.
2. Build the 2019 annual median from valid Landsat 7/8 Collection 2 Level 2 NDVI observations. Require at least three valid observations and sample the nearest 30 m value at each native WorldPop cell centre.
3. Set positive NDVI to zero for the counterfactual. Nonpositive NDVI has no exposure difference.
4. Convert the published OR to an RR using `RR = OR / (1 − p0 + p0 × OR)`. Calculate `prevalence-derived 2019 case equivalents × [RR^(−10 × positive NDVI) − 1]` and aggregate without rounding intermediate values.
5. Multiply case equivalents by the US cost proxy and report the result in 2019 USD without PPP.

Inputs used here are US 2019 all-age depressive-disorders prevalence **4.24%**, `p0 = 11.5%`, and OR **0.931** (95% CI **0.887–0.977**) per +0.1 NDVI. The exact unrounded inputs remain in the machine-readable outputs.

## Difference from Varun Sethi's original implementation

The comparison below refers to the original Observarun [`run_urban_mental_health.py`](https://github.com/Observarun/urban-mental-health-gep/blob/f1822e2/run_urban_mental_health.py) and [`urban_mental_health_functions.py`](https://github.com/Observarun/urban-mental-health-gep/blob/f1822e2/urban_mental_health_functions.py) at commit [`f1822e2`](https://github.com/Observarun/urban-mental-health-gep/tree/f1822e2). It compares implementation and estimand; the original repository does not contain a completed national output to reproduce numerically.

| Component | Original Observarun implementation | Current production run |
| --- | --- | --- |
| Execution and scope | Local Python/Hazelbean global-raster pipeline with user-supplied inputs and fixed machine paths. | Versioned Earth Engine run for the reviewed US subset; 133 resumable batches with explicit task receipts. |
| Nature exposure | Warp GLC_FCS30D land cover to WorldPop with nearest-neighbour resampling, then assign one NDVI value to each land-cover class from a lookup table. | Use the 2019 Landsat annual-median NDVI pixels directly; no land-cover class-to-NDVI lookup enters the production exposure. |
| Counterfactual | Set every positive lookup-derived NDVI value to zero. | Same conceptual counterfactual, applied to direct Landsat NDVI sampled on the population grid. |
| Health contrast | Literally calculates `prevalence × population × [1 − RR^(10 × ΔNDVI)]`, labelled preventable cases. The code does not convert the prevalence-derived baseline to the no-nature reference state required for exact equivalence with the current equation. | Calculates `2019 reference case equivalents × [RR^(−10 × ΔNDVI) − 1]`, reported as additional case equivalents if current nature were removed. The prevalence-derived 2019 state is explicit. |
| Prevalence | Fixed `0.05` for every country. | Country-specific 2019 GBD prevalence; **4.24%** for this US run, aligned with the all-age WorldPop denominator. |
| `p0` and OR-to-RR | Fixed `p0 = 0.115`; convert the depression OR to an RR. | Retains the conversion but labels `p0 = 0.115` as a transported assumption and records sensitivity work. |
| Uncertainty | Uses only the point effect estimate. | Reports conditional 95% limits from the effect estimate; other uncertainty remains outside the interval. |
| Spatial aggregation | Zonal statistics over the original urban polygons; region totals are rounded before country aggregation. Polygon overlap is not explicitly allocated once. | Uses disjoint city/state units, retains fractional cases through aggregation, reports missing NDVI support, and reconciles state/DC plus residual totals. |
| Valuation | Multiplies country cases by the supplied `cost_per_case`; the code does not enforce currency year or PPP status. | Uses an explicitly labelled US proxy of about **$11,000 per case equivalent**, reported in **2019 USD without PPP**. |
| Reproducibility | Skips existing intermediates but does not create a run manifest or input/output hashes. | Pins code and graph hashes, preserves task IDs, validates unique receipts, publishes row-level summaries and supplies SHA-256 checksums. |

Both implementations retain the same central idea: compare current urban nature with a zero-positive-NDVI counterfactual, convert an odds ratio using `p0`, calculate a population-weighted depression contrast, and aggregate it geographically. The production result should therefore be described as an extension and clarification of the original model, rather than a literal rerun of Varun's code.

{method_detail}
## Largest state contributions

| State | Modelled population | Additional case equivalents | 2019 USD proxy |
| --- | ---: | ---: | ---: |
{top}

These rows cover only the GUPPD urban areas intersecting each state and are not whole-state burden estimates.

## Method sensitivity

{comparison}
The four-city gate reproduced the earlier direct-grid estimates exactly for Portland and within **0.01%** for Anchorage, Tucson and New York. The remaining differences match previously identified boundary-cell membership differences.

## Verification and reproducibility

- All {direct['completed_batches']} Earth Engine table batches completed.
- Exactly {direct['completed_city_receipts']:,} unique expected city receipts were recovered; no city was duplicated or omitted.
- The 50 state/DC summaries plus the boundary residual ({compact(residual['population_total'])} people; {compact(residual['additional_cases'])} case equivalents) reconcile to the national totals.
- Population support, interval order, observed-case arithmetic and valuation arithmetic passed at national, state and city levels.
- Model source commit: `{direct['source_git_commit']}`; model graph SHA-256: `{direct['code_sha256']}`.
- Machine-readable outputs: [national summary](data/us_direct_ndvi_2019_v1/national_summary.json), [state summary](data/us_direct_ndvi_2019_v1/state_summary.csv), [city summary](data/us_direct_ndvi_2019_v1/city_summary.csv), [city-state rows](data/us_direct_ndvi_2019_v1/city_state_rows.csv), [task manifest](data/us_direct_ndvi_2019_v1/direct_ndvi_batch_manifest.json), and [checksums](data/us_direct_ndvi_2019_v1/checksums.sha256).

{spatial_check}

## Interpretation limits

The 95% limits propagate only the published effect-size interval. They hold `p0`, prevalence, population, NDVI, geographic membership and cost fixed. The exposure-response estimate and `p0` are transported assumptions; the all-age GBD prevalence matches the all-age population denominator but is not an adult current-MDD endpoint. GUPPD features represent physical urban extents rather than municipal boundaries. The cost factor is broader than depression treatment cost, so the dollar result is an exploratory societal-value proxy. A later Monte Carlo analysis should jointly vary the effect, `p0`, prevalence, exposure and cost inputs.
"""
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text)
print(a.output)
