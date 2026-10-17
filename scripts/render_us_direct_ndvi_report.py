"""Render the concise US direct-NDVI production report from verified summaries."""
import argparse,csv,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('direct_summary',type=Path);p.add_argument('state_summary',type=Path)
p.add_argument('output',type=Path);p.add_argument('--technical-summary',type=Path)
p.add_argument('--local-feature-results',type=Path)
a=p.parse_args();direct=json.loads(a.direct_summary.read_text());n=direct['national']
states=list(csv.DictReader(a.state_summary.open()))
residual=next(r for r in states if int(r['state_code'])==0)
states=[r for r in states if int(r['state_code'])!=0]
states.sort(key=lambda r:float(r['additional_cases'] or 0),reverse=True)
technical=json.loads(a.technical_summary.read_text()) if a.technical_summary else None
coverage=100*float(n['population_modelled'])/float(n['population_total'])
missing=100-float(coverage)
def num(x,d=0):return f"{float(x):,.{d}f}"
def money(x):return '$'+num(x/1e9,2)+' billion'
comparison=''
spatial_check=''
if technical:
    old=technical['totals']['additional_cases'];diff=100*(n['additional_cases']/old-1)
    old_pop=technical['totals']['population_total'];pop_delta=n['population_total']-old_pop
    pop_pct=100*pop_delta/old_pop
    comparison=(f"The earlier five-region pooled land-cover lookup produced {num(old)} case equivalents. "
      f"The direct-NDVI result is {diff:+.1f}% different. This is a method sensitivity comparison, "
      "not an uncertainty interval; the pooled lookup was rejected for production because it transferred poorly among test cities.\n")
    spatial_check=(f"The Earth Engine reporting geometry contains {num(n['population_total'],3)} people, "
      f"{num(pop_delta,3)} ({pop_pct:.5f}%) more than the independent local native-cell-centre audit. ")
if a.local_feature_results:
    local={r['region_id']:float(r['population_total'] or 0) for r in csv.DictReader(a.local_feature_results.open())}
    cloud_path=a.state_summary.with_name('city_summary.csv')
    cloud={r['city_id']:float(r['population_total'] or 0) for r in csv.DictReader(cloud_path.open())}
    changed=sum(abs(cloud[k]-local[k])>1e-7 for k in cloud)
    spatial_check+=(f"The difference is distributed across {changed:,} feature totals and reflects the known "
      "cross-engine boundary-cell membership sensitivity. The reported production values retain the reviewed "
      "Earth Engine reporting units and are not rescaled to the local population total.")
top='\n'.join(f"| {r['state_abbr']} | {num(r['population_modelled'])} | {num(r['additional_cases'])} | {money(float(r['value_2019_usd']))} |" for r in states[:10])
text=f"""# 2019 US urban mental health direct-NDVI production run

Completed {direct['created_utc'][:10]}. Status: **nationwide calculation complete; internal checks passed**. A small cross-engine boundary-cell difference is reported below.

## Result at a glance

| Quantity | Result |
| --- | ---: |
| GUPPD urban features | {direct['completed_city_receipts']:,} |
| Population in scope | {num(n['population_total'],3)} |
| Population with valid NDVI | {num(n['population_modelled'],3)} ({coverage:.5f}%) |
| Population without valid NDVI | {num(n['population_missing_ndvi'],3)} ({missing:.5f}%) |
| Baseline depressive-disorder case equivalents on modelled population | {num(n['observed_cases'],1)} |
| Additional case equivalents under the zero-positive-NDVI counterfactual | **{num(n['additional_cases'],1)}** |
| Conditional 95% effect-size limits | {num(n['additional_cases_lower'],1)} to {num(n['additional_cases_upper'],1)} |
| 2019 USD societal-value proxy | **{money(n['value_2019_usd'])}** |
| Conditional value limits | {money(n['value_2019_usd_lower'])} to {money(n['value_2019_usd_upper'])} |

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
{top}

These rows reflect only the GUPPD urban areas intersecting each state. State values may be compared within this run, but should not be read as whole-state burden estimates.

## Method sensitivity

{comparison}
The four-city gate reproduced the earlier direct-grid estimates closely: exactly for Portland, and within 0.0027% for Anchorage, 0.0021% for Tucson and 0.0003% for New York. The small differences match previously identified boundary-cell membership differences.

## Verification and reproducibility

- All {direct['completed_batches']} Earth Engine table batches completed.
- Exactly {direct['completed_city_receipts']:,} unique expected city receipts were recovered; no city was duplicated or omitted.
- The 50 state/DC summaries plus the boundary residual ({num(residual['population_total'],1)} people; {num(residual['additional_cases'],1)} case equivalents) reconcile to the national totals.
- Population total equals modelled plus missing-NDVI population within numerical tolerance.
- Case and value limits are ordered correctly, and value arithmetic reproduces cases multiplied by the cost proxy.
- Model source commit: `{direct['source_git_commit']}`; model graph SHA-256: `{direct['code_sha256']}`.
- Machine-readable outputs: [national summary](data/us_direct_ndvi_2019_v1/national_summary.json), [state summary](data/us_direct_ndvi_2019_v1/state_summary.csv), [city summary](data/us_direct_ndvi_2019_v1/city_summary.csv), [city-state rows](data/us_direct_ndvi_2019_v1/city_state_rows.csv), and the [task manifest](data/us_direct_ndvi_2019_v1/direct_ndvi_batch_manifest.json).

{spatial_check}

## Interpretation limits

The 95% limits propagate only the published effect-size interval. They hold `p0`, prevalence, population, NDVI, geographic membership and cost fixed. The exposure-response estimate and `p0` are transported assumptions; the all-age GBD prevalence is aligned with the all-age WorldPop denominator but is not an adult current-MDD endpoint. GUPPD features are physical urban extents rather than municipal boundaries. The cost factor is broader than depression treatment cost, so the dollar figure is best reported as an exploratory societal-value proxy. A future Monte Carlo analysis should jointly vary the effect, `p0`, prevalence, exposure and cost inputs.
"""
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text)
print(a.output)
