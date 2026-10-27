# `p0` pilot: reference-group alignment and calculation sensitivity

8 October 2026. This is a reproducible **desk pilot** using reported low-NDVI prevalences from one primary study and the project's published pooled OR. It does not estimate a global reference prevalence from individual records and does not run the geospatial model. The numeric calculations are saved in [`p0_pilot_sensitivity_2019.csv`](p0_pilot_sensitivity_2019.csv).

## Source-paired candidate check

[Hystad et al. (2019)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7952103/) provide two relevant low-exposure outcome proportions:

- **11.5%**: health-record depression diagnosis in the least-green quartile in Table 1, which groups residential NDVI within **500 m**. This is the present `p0` setting.
- **9.6%**: self-reported doctor diagnosis of **major depression** in the least-green quartile, described in the article's discussion for residential NDVI within **250 m**. The article reports 5.4% in the highest quartile for this same measure. The paper's statistically significant adjusted depression OR is 0.85 (95% CI 0.76–0.95) per +0.1 NDVI within **500 m**, for *self-reported doctor diagnosis*. The 9.6% therefore improves **outcome** alignment with that specific Hystad OR but its published summary uses a different NDVI buffer. It is also an adult, ever-diagnosed outcome, not current all-age GBD depressive disorders.

These are different ascertainment methods and observation windows. Hystad reports low agreement between medical records and participant self-report. Neither number is an observed risk at NDVI exactly zero or a representative global/country rate. The [Liu et al. (2023)](https://pubmed.ncbi.nlm.nih.gov/37268208/) pooled depression OR of 0.931 (0.887–0.977) per +0.1 NDVI combines different study estimates; the Hystad low-quartile prevalence is not necessarily its reference risk. We did not find a reported pooled-study reference prevalence in Liu's accessible abstract.

## Small numerical pilot using the project OR

The table holds the Liu point OR at 0.931 and calculates `RR = OR/(1-p0+p0×OR)`. The last column uses the **corrected observed-case reference** formula: for a +0.1 observed-versus-zero NDVI difference, additional no-vegetation cases per 100 estimated observed cases equal `100 × (1/RR − 1)`. This is a calculation comparison, **not a prediction of 2019 city cases**.

| `p0` | Evidence status | RR | Added cases per 100 observed cases for ΔNDVI = 0.1 |
| ---: | --- | ---: | ---: |
| 0.030 | Illustrative scenario | 0.93293 | 7.189 |
| 0.050 | Illustrative scenario; **not** the WHO baseline-rate justification | 0.93422 | 7.041 |
| 0.096 | Hystad low-NDVI adult self-reported doctor diagnosis, 250 m | 0.93721 | 6.700 |
| 0.115 | Hystad low-NDVI adult health-record diagnosis, Table 1 at 500 m | 0.93845 | 6.559 |
| 0.200 | Illustrative scenario | 0.94403 | 5.929 |

Within the two observed Hystad choices, moving from 0.115 to 0.096 changes the converted per-step RR from 0.93845 to 0.93721 and the example case difference by **about 2.1%** (6.700 versus 6.559). The broader 0.03–0.20 scenario range changes the example by about **19%** (7.189 versus 5.929, relative to their midpoint), which is a sensitivity range rather than a 95% interval. OR confidence limits are included as separate rows in the CSV; these are still conditional on `p0`, baseline prevalence, exposure and population.

## Decision from this pilot

**Do not promote either Hystad number to a validated global `p0`.** Keep 0.115 for comparability with existing code, add 0.096 as an explicitly labelled outcome-aligned *Hystad sensitivity scenario*, and show a broader scenario grid. The 0.096 choice is potentially preferable if the model later uses the same Hystad self-reported doctor-diagnosis effect and compatible population/NDVI buffer; it does not solve the current all-age GBD/Liu endpoint mismatch.

The most useful next evidence request is the complete Liu NDVI–depression study list and supplements: extract each study's reference-group cases and denominator, exposure definition, age/outcome, adjusted OR and uncertainty. If compatible study pairs are found, convert each **study's own OR using its own reference risk**, then meta-analyse the resulting RRs or obtain marginal RRs from authors. This avoids pairing one pooled OR with a convenient but unrelated `p0`. A second-stage pilot can estimate a low-NDVI prevalence from permissioned geocoded health data in a few settings; national GBD rates can check marginal consistency but cannot identify the exposure-reference risk.

## Expanded follow-up

See the [multi-study evidence check and synthesis decision](p0_evidence_expansion.md) and [evidence matrix](p0_evidence_matrix.csv). A further original study reports 12.44% in its lowest NDVI tertile, but its NDVI range is −0.40 to −0.06, so the model's zero-NDVI counterfactual actually lies in its middle tertile. It is an evidence-audit example, **not** a recommended replacement `p0`. No cross-study pooled `p0` is supported by the currently extractable data.
