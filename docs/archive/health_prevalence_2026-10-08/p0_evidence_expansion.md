# Expanded `p0` evidence check and synthesis decision

8 October 2026. Desk review for the urban mental health GEP model. `p0` is the outcome probability in the **low-exposure reference group** used to approximate an RR from an OR. It is separate from country-wide prevalence used for baseline cases. No model run or primary parameter was changed.

## Re-reading Liu et al. (2023)

[Liu et al.](https://pubmed.ncbi.nlm.nih.gov/37268208/) standardised observational ORs to a 0.1-unit NDVI increase and reported a pooled depression OR of **0.931 (95% CI 0.887–0.977)**. The main article and author-supplied supplement have now been reviewed. Liu identifies **nine studies**, while Figure 4 contains **13 estimates** because three cohorts contribute multiple outcomes. The extracted study list, effects, outcome definitions, available prevalence values, and source discrepancies are recorded in the [row-level extraction](liu_2023_ndvi_study_extraction.csv) and [synthesis audit](liu_2023_ndvi_synthesis_audit.md). No pooled reference-group event probability is reported.

The synthesis has material internal inconsistencies: Brown's sample is printed as 24,905 instead of 249,405; the nine printed sample sizes do not sum to Liu's stated 267,744; the Canadian Hystad paper is labelled “Perry 2019”; and one Gonzales row is described as total residential green-space percentage despite appearing in the NDVI forest. The supplement's Table S4 values are leave-one-estimate-out **pooled** ORs, not study effects. Liu also reports I² above 94% and publication-bias asymmetry. These issues make a single pooled OR and pooled `p0` particularly unsuitable for direct transport as a global causal effect.

The most consequential synthesis issue is **pairing**: the reference risk should come from the same outcome and exposure comparison as its OR. A low-NDVI proportion for any outcome called “depression” cannot be paired automatically with Liu's pooled OR, especially when individual studies define symptoms, diagnosis and time window differently. Furthermore, published low NDVI quantiles are not observations at the model's NDVI=0 counterfactual.

## Evidence extraction beyond Hystad

The adjacent [`p0_evidence_matrix.csv`](p0_evidence_matrix.csv) records extractable values and explicit non-use decisions. Sources are original studies, except for the Liu row. Key findings:

| Study | Low-NDVI outcome proportion | Outcome / exposure | Relevance |
| --- | ---: | --- | --- |
| [Hystad et al. 2019, Quebec](https://pmc.ncbi.nlm.nih.gov/articles/PMC7952103/) | **11.5%** (234 cases in the least-green 500 m quartile) | Adult health-record depression diagnosis, residential NDVI | Existing `p0`; local, diagnosis-specific, and not zero NDVI. |
| Hystad et al. 2019 | **9.6%** (published percentage, least-green 250 m quartile) | Adult self-reported doctor diagnosis of major depression | Alternative outcome measure within the **same cohort**. Do not count as a second independent study or average with 11.5%; the reported significant OR uses 500 m, so the buffer is not exactly paired. |
| [Perrino et al. 2019, Miami](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/DFB02DA7FF7EDC6E2D715A67DC45ADE7/S0007125019001296a.pdf/neighbourhood_greenness_and_depression_among_older_adults.pdf) | **12.44%** (least-green census-block NDVI tertile, 82,790 people; percentage reported in Table 1) | Medicare beneficiaries aged ≥65; claims algorithm includes depression, MDD, dysthymia, bipolar and adjustment disorders; adjusted OR 0.92 for middle vs low and 0.84 for high vs low NDVI | **Poor counterfactual match:** low tertile is NDVI **−0.40 to −0.06**, below the model's zero value. Useful demonstration of the exposure-reference problem, **not a replacement `p0`**. Its categorical OR is not Liu's per-0.1 OR. |
| [Song et al. 2019, Korean Community Health Survey](https://pdfs.semanticscholar.org/006f/df9fac95a4759092482309494e37142c853f.pdf) | **Unavailable** in article (11.7% is the overall sample, not low-NDVI quartile) | 65,128 adults, seven cities; CES-D≥16 over the previous week; least-green district NDVI quartile 0.20–0.29 | Strong candidate for author/data request, but overall 11.7% is **not `p0`**. |
| [Mexico national survey analysis, 2026](https://www.sciencedirect.com/science/article/pii/S2211335526000951) | **Unavailable** in accessible text (16.2% is the overall sample) | Ages 20–59; CESD-7≥9 descriptive endpoint; published NDVI regression uses continuous symptom score | Valuable geographic check, but neither overall 16.2% nor a continuous-score coefficient can supply the binary outcome `p0` paired with Liu's OR. Published after Liu and cannot be in its study set. |

The [Perrino source](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/DFB02DA7FF7EDC6E2D715A67DC45ADE7/S0007125019001296a.pdf/neighbourhood_greenness_and_depression_among_older_adults.pdf) gives 12.44%, 8.60%, and 6.74% across low, middle and high tertiles, respectively, showing why the overall 9.25% cannot substitute for a low-exposure `p0`. **Its low tertile mean NDVI is −0.11 and its range is −0.40 to −0.06**; the hypothetical model counterfactual of zero NDVI lies in Perrino's *middle*, not low, tertile (−0.06 to 0.006; 83,314 people). The **8.60% middle-tertile proportion** is a more informative *near-zero exposure check* than the 12.44% low-tertile proportion, but its wide NDVI band, broad claims endpoint and older age group still prevent direct substitution for the project's `p0`.

## Numerical implication and recommended synthesis

For illustration **only**, inserting these three *reported* low-exposure percentages into the project's **same** pooled OR 0.931 gives:

| `p0` | Converted RR per +0.1 NDVI | Added zero-vegetation cases per 100 observed cases for a +0.1 NDVI contrast* |
| ---: | ---: | ---: |
| 0.096 (Hystad self-report) | 0.93721 | 6.700 |
| 0.115 (Hystad health record; current setting) | 0.93845 | 6.559 |
| 0.1244 (Perrino broad claims diagnosis; exposure-incompatible) | 0.93906 | 6.489 |
| 0.086 (Perrino broad claims diagnosis; NDVI band straddles zero) | 0.93656 | 6.774 |

*Arithmetic comparison: `RR=OR/(1-p0+p0×OR)` and `100×(1/RR−1)`. These are **not a meta-analysis, CI, or city forecast**. Hystad's two rows are correlated; none of these studies supplies a verified reference probability for Liu's pooled OR at zero NDVI. The narrow numerical span does not validate a global 0.115.

**Current decision:** Retain 0.115 as a clearly labelled legacy scenario and 0.096 as a **Hystad self-report** scenario. Record Perrino's 0.1244 and near-zero 0.086 in the evidence audit and arithmetic illustration, but **exclude both as proposed replacements or preferred sensitivity values** because the age/outcome differ and neither estimates an adjusted probability at NDVI exactly zero. Do not create a pooled `p0` or a confidence interval from these percentages. Preserve the broader prespecified 0.03–0.20 sensitivity grid because the observed studies cover only particular ages, countries and endpoints. Keep the Liu OR confidence interval separate from this structural `p0` uncertainty.

**Preferred study-level synthesis when the necessary information is available:**

1. Use the completed Liu row-level extraction to select one effect estimate per independent cohort. Confirm unresolved Gonzales row mapping and record exact endpoint, diagnostic window, age, year, geography, NDVI scale/buffer, reference range, cases/denominator, fully adjusted OR and 95% CI. Mark estimates with missing low-exposure counts as missing, rather than inserting whole-sample prevalence.
2. Form outcome-specific strata: **current depressive disorder**, **ever/claims diagnosis**, and **screen-positive symptoms**. Keep age and exposure contrasts visible. The current all-age GBD depressive-disorders baseline is most plausibly paired with the first stratum; if the effect literature cannot support it, report an outcome mismatch and consider an adult endpoint as a later, separately specified analysis.
3. Where an OR and `p0` truly refer to the same study comparison, derive `RR_i=OR_i/(1-p0_i+p0_i×OR_i)`. Propagate the OR CI and sampling uncertainty of `p0_i`; account for shared cohorts and adjusted-versus-crude risk mismatch. Prefer author-supplied marginal standardised RRs or exposure-specific risks if obtainable. Meta-analyse comparable log RRs using random effects, report heterogeneity and a prediction interval when estimable. **Do not** pool the `p0_i` values first and then convert Liu's pooled OR.
4. If low-group counts remain inaccessible, use an **explicit calibration model** as sensitivity analysis: fit a baseline intercept so the population-weighted predictions under the chosen NDVI distribution reproduce the GBD 2019 country marginal prevalence, given a specified OR slope and age frame. Label its zero-NDVI risk *model-implied*; do not call it observed or independently validated. An urban-only NDVI distribution cannot by itself be calibrated to a national all-population rate without an urban/rural bridge.
5. Request aggregate low-NDVI counts/denominators from the Korean CHS and any relevant 2019-era survey custodians. Focus especially on an NDVI band around **zero** or fitted marginal probability at zero, not merely each study's lowest quantile. Validate candidate calibrations against held-out observed exposure-group prevalence. Only then consider changing the primary `p0`.

**Data request template:** “For the analysis corresponding to your reported NDVI–depression OR, could you provide the depression case count and participant denominator in the lowest NDVI category, its NDVI bounds and buffer, the outcome definition/time window, and, if possible, covariate-standardised outcome probabilities (with uncertainty) at NDVI 0 and at representative observed values?”
