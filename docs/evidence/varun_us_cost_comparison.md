# US cost-rate sensitivities on the four matched technical runs

Varun's supplied `treatment_cost.xlsx` has one `United States` row at **$5,834.61
per case**. The user confirmed that the estimates are labelled 2019 USD; the
workbook itself does not record price year, PPP status, cost components or the
country-estimation ledger. The current exploratory US societal-cost proxy is
**$10,999.21 per case**, explicitly converted to 2019 USD without PPP. These
rates may measure different cost constructs.

The linked [SNAPP cost note](https://github.com/Yingjie4Science/SNAPP/blob/main/docs/societal_cost_of_depression.md)
compiles US **adult major depressive disorder (MDD)** studies. Its strongest
price-year match here is the [Greenberg et al. 2019 study](https://doi.org/10.1007/s12325-023-02622-x),
which reports **$16,854 per adult with MDD in 2019 USD** as an annual
incremental societal cost. We reviewed the locally available SNAPP `main`
checkout at commit `56edc73cd5bb6888844803d7bdfe11a7fb901f96` and checked
this rate against the primary paper. This comparison uses the study's *reported
2019-dollar figure directly*; no PPP or price-year conversion is applied.

The table below multiplies the **same saved case estimates** by each rate. It is
a cost-only postprocessing comparison; no health or exposure model was rerun.

| 2019 land cover | NDVI lookup | GUPPD urban area (km²) | Case equivalents | Varun $5,834.61/case (2019 USD, conditional) | Project $10,999.21/case (2019 USD, non-PPP proxy) | SNAPP MDD $16,854/case (2019 USD, conditional) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Local Zenodo tiles | US-derived | 129,240.83 | 2.46 million | $14.38 billion | $27.10 billion | $41.53 billion |
| Local Zenodo tiles | Varun's | 129,240.83 | 1.68 million | $9.83 billion | $18.53 billion | $28.40 billion |
| Varun's raster | US-derived | 129,239.81 | 2.46 million | $14.33 billion | $27.01 billion | $41.39 billion |
| Varun's raster | Varun's | 129,239.81 | 1.67 million | $9.74 billion | $18.36 billion | $28.14 billion |

Area is the **dissolved, unique footprint** of each saved non-Hawaii US GUPPD
polygon layer, projected to equal-area EPSG:5070; it is not the area with
population or valid NDVI. The local boundary file has 3,312 features and the
Varun file 3,309. Their unique areas differ by only **1.02 km²** (three local
features with zero modeled population/cases), so the boundary-area difference
does not explain the large lookup-driven case difference. See the
[area audit](data/varun_2026_10/us_urban_area_audit.json) and its
[reproduction script](../../scripts/audit_us_urban_area.py).

### Why SNAPP's own national total is much larger

The [SNAPP existing-greenness national summary](https://github.com/Yingjie4Science/SNAPP/blob/main/results/summaries/national_summary_existing_greenness.md)
currently reports **12.73 million modeled cases × $21,280 per case = $270.98
billion/year in 2024 USD**. Its [technical note](https://github.com/Yingjie4Science/SNAPP/blob/main/docs/gep_existing_greenness_technical_note.md)
defines a separate 2024, adult, metropolitan-county model. The $270,903
million figure supplied for review is $74.43 million (0.03%) below this current
repository total; its exact source version has not been identified.

| Component | SNAPP existing greenness | This project's matched local-land-cover/US-lookup run |
| --- | --- | --- |
| Population and area | 218.64 million adults in 1,167 metropolitan counties | About 194.37 million all-age residents in disjoint GUPPD urban areas |
| Total mapped study-domain area | **2,526,402.14 km²** across SNAPP's 1,167 whole metropolitan counties | **129,240.83 km²** across the local GUPPD urban polygons |
| Health input | Tract-level CDC PLACES adults *ever told* they had a depressive disorder; national reference-group risk `p0 = 0.191045` | GBD 2019 all-age depressive-disorders prevalence, about 4.24%; transported `p0 = 0.115` |
| Greenness | 2024 growing-season Landsat p90 NDVI, averaged within 300 m; observed versus NDVI = 0 | 2019 annual median Landsat NDVI assigned by land-cover class; positive NDVI set to zero at population cells |
| Modeled cases | 12.73 million | 2.46 million |
| Valuation | $21,280 per case in **2024 USD**, pooled adult-MDD societal-cost proxy | $16,854 per case in **2019 USD**, directly reported adult-MDD cost sensitivity |
| Valued result | **$270.98 billion** | **$41.53 billion** |

SNAPP's county footprint is **19.55 times** the GUPPD polygon footprint, but
it includes nonurban land within metropolitan counties. It is the total area
of the actual SNAPP study geography, **not an urban-only area** or the area of
populated/valid-NDVI cells. We calculated both dissolved footprints in
EPSG:5070 from the saved boundaries. SNAPP's 1,167 county GEOIDs exactly match
its locked `config/regions.csv` and the national result count; the separate
Earth Engine upload shapefile gives the same area. The area contrast helps
inspect scope, but cannot by itself explain the case-count difference.

The case count is **5.17 times** larger in SNAPP; the rate is **1.26 times**
larger, with a different price year. Their product explains the **6.53-fold**
numeric total difference. On the *same hypothetical $16,854 rate*, SNAPP's
12.73 million cases would be $214.62 billion versus $41.53 billion here. This
isolates the arithmetic role of cases, but it does not make the outcomes or
study areas scientifically equivalent. SNAPP models **5.82 cases per 100
adults**, whereas this matched run models about **1.27 per 100 all-age
residents**. The denominator and modeled rate are both different. The higher
PLACES prevalence, different exposure season and neighborhood averaging,
spatial domain, `p0`, and accounting implementation all affect modeled cases;
their individual contributions cannot be measured from these unmatched runs.

The Varun-land-cover/Varun-lookup row used in our earlier reply is lower still:
**1.67 million cases × $16,854 = $28.14 billion in 2019 USD**. SNAPP's own
$270.98 billion is **9.63 times** that conditional value. The actual direct-NDVI
production run, which is a separate configuration, reports **2.45 million
cases and $26.99 billion** under its approximately $11,000 2019-dollar proxy.

**Recommended next comparison:** run both implementations on the same geography,
population, prevalence definition, NDVI raster/composite, buffer radius,
`p0`, and case formula, then change one choice at a time. Until that matched
test exists, do not interpret the $270.98 billion and this project's dollar
values as conflicting estimates of the same quantity. Retain SNAPP's original
2024-dollar total as reported; any 2019-dollar restatement needs a documented
conversion before it can enter this project's main 2019-dollar table.

The Varun US rate is **46.95% lower**, so every conditional dollar total is
46.95% lower. Case estimates and their OR-only effect limits do not change.
Neither rate should be described as verified treatment savings. Do not adopt
the Varun-valued totals as a 2019 USD **non-PPP** production result until the
workbook's exchange-rate basis and cost scope are verified.

The SNAPP rate is **53.23% above** the project proxy. It is a stronger source
for a US 2019-dollar *adult-MDD societal cost*, but our case equivalents use
**all-age depressive-disorders** prevalence. Applying adult-MDD costs to those
case equivalents is an endpoint and age-denominator mismatch. Greenberg's
incremental annual burden also includes medical, work, household, and mortality
components; applying it to modeled case equivalents does not demonstrate that
all components would be avoided. These three dollar columns are **scenario
values, not a statistical interval or interchangeable estimates of one cost
construct**. Keep the existing case estimates as the main result.

### SNAPP source review and recommended next steps

1. **Use the reported $16,854 only as a 2019-dollar sensitivity now.** It is
   directly traceable to a 2019 US study and needs no deflation. The SNAPP note's
   preferred pooled ~$21,000 is in **2024 USD**, so it cannot be inserted into a
   2019-dollar report without a documented conversion and source reconciliation.
2. **Resolve SNAPP's small internal arithmetic and metadata issues before using
   its pooled rate.** The note gives a pooled anchor mean of about $21,240 in
   2024 USD, while `estimate_health_cost.py` produces about $21,280 because its
   component shares sum to 100.2%. In `cost_studies.csv`, the Greenberg 2019
   row combines a 2023-dollar total with a reported 2019-dollar per-case rate;
   give each amount its own price-year field. Neither issue changes the $16,854
   value taken directly from the primary study.
3. **Choose a matching outcome before selecting a primary cost.** An adult-MDD
   pathway would require an adult population denominator, adult MDD prevalence
   and an endpoint-compatible exposure effect. If the current all-age depressive
   disorders model is retained, seek a correspondingly defined per-case cost or
   report monetary results strictly as labelled sensitivities. Obtain Varun's
   cost-component and currency ledger before using his country estimates as a
   production non-PPP cost series.

Reproduce the [machine-readable comparison](data/varun_2026_10/us_cost_rate_comparison.json)
from the repository root in the project's spreadsheet-capable Python environment:

```sh
python scripts/compare_varun_us_cost.py \
  docs/evidence/data/varun_2026_10/source_lookup_factorial_summary.json \
  ../data/urban_mental_health/raw/collaborator/varun_2026-10/treatment_cost.xlsx \
  docs/evidence/data/varun_2026_10/us_cost_rate_comparison.json
```

The JSON records input hashes, exact rates, full dollar values, and the
conditional OR-limit valuations. The four underlying full run receipts remain
in `../data/urban_mental_health/pilots/varun_lookup_matched_2019_v1/`.

For the SNAPP scenario, reproduce the [three-rate comparison](data/varun_2026_10/snapp_us_cost_comparison.json)
with the sibling SNAPP checkout:

```sh
python scripts/compare_snapp_us_cost.py \
  docs/evidence/data/varun_2026_10/source_lookup_factorial_summary.json \
  docs/evidence/data/varun_2026_10/us_cost_rate_comparison.json \
  ../../SNAPP/docs/cost_studies.csv \
  ../../SNAPP/docs/societal_cost_of_depression.md \
  docs/evidence/data/varun_2026_10/snapp_us_cost_comparison.json
```

The three-rate JSON stores the SNAPP source row, source-file hashes, paper DOI,
exact rates and cost-only results. The $16,854 source value is also available
in the linked primary paper if the SNAPP checkout is not available.

To reproduce the boundary-area audit with the sibling SNAPP checkout, run:

```sh
python scripts/audit_us_urban_area.py \
  ../data/urban_mental_health/processed/guppd_us_excluding_hawaii.gpkg \
  ../data/urban_mental_health/processed/varun_us_excluding_hawaii.gpkg \
  ../../SNAPP/data/national/counties.gpkg \
  ../../SNAPP/config/regions.csv \
  docs/evidence/data/varun_2026_10/us_urban_area_audit.json
```

Use a Python environment with GeoPandas and Shapely. The JSON records input hashes, feature counts,
CRS, unique area and polygon-overlap area.
