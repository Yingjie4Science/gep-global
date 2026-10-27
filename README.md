# Urban mental health for Global GEP

Estimate depression-related case equivalents associated with urban greenness,
and explore their societal value. The active scope is US GUPPD urban areas in
the **48 contiguous states plus DC**, excluding Alaska, Hawaii and territories.
Published runs below retain the earlier Alaska-inclusive scope; updated totals
are pending.
Global replication is still under review.

**Historical Alaska-inclusive result:** the direct 2019 Landsat NDVI run gives **2.45 million case
equivalents** and an exploratory **$26.99 billion in 2019 USD without PPP**.
These are conditional counterfactual model results. Effect-size limits do not
include all input or model uncertainty.

## Start here

| Your task | Read or run |
| --- | --- |
| Understand the result and method | [Production report](docs/evidence/us_direct_ndvi_production_run.md) |
| Compare Varun, project and SNAPP values and study areas | [Cost and area comparison](docs/evidence/varun_us_cost_comparison.md) |
| Reproduce a calculation or resume a workflow | [Reproduction guide](docs/REPRODUCING.md) |
| Locate data, source links and preprocessing | [Data guide](docs/DATA_SOURCES_AND_PREPROCESSING.md) |
| See what is open, who owns it and the next action | [Current decisions and tasks](docs/DECISIONS_AND_TODOS.md) |
| Trace a completed run to its evidence | [Run registry](config/run_registry.json) |

## Project layout

```text
gep-global/
├── README.md                 orientation and workflow choice
├── environment.yml           geospatial environment dependencies
├── pyproject.toml            install shared Python modules and umh-global CLI
├── src/                      shared model, health, cost and provenance code
├── scripts/
│   ├── 01_inputs/            acquisition and preparation
│   ├── 02_models/            pilot and national local calculations
│   ├── 03_checks/            audits, comparisons and valuation sensitivities
│   ├── 04_reports/           report rendering
│   └── check_repository.py   offline layout, link and evidence checks
├── config/                   country crosswalk, run registry and layout history
├── docs/                     data guide, reproduction guide and current tasks
│   ├── evidence/             published reports and small numerical snapshots
│   └── archive/              dated decisions, retained for context
├── tests/                    model and provenance regression checks
├── data/                     raw, processed, manifests, outputs and archive (ignored by Git)
└── archive/                  local early project snapshots (ignored by Git)
```

The active Git checkout begins at `gep-global/`. The data guide is the
authoritative input inventory, and the task register is the sole current
owner/status list. Full local comparisons are in `data/outputs/`; older runs are in
`data/archive/`. The [data path migration](config/data_layout_migration_2026-10-27.json)
resolves paths in historical receipts.
The ignored data folder must be supplied separately for a new clone.
Its original IHME export is under `data/raw/ihme_gbd_2023/`; the model-ready
2019 country table is under `data/processed/`.

## Workflow

**Prepare and audit inputs → choose exposure and health assumptions → run in a
fresh directory → compare and validate → publish a labelled result.**

The primary US exposure is direct annual-median 2019 Landsat NDVI, processed in
Earth Engine. Local sensitivities assign NDVI from land-cover classes. Both
use the reviewed population support and explicit prevalence, OR-to-RR `p0`,
case reference state and cost basis. The [production report](docs/evidence/us_direct_ndvi_production_run.md)
explains the equations and original-code differences.

The separate [Earth Engine app](https://natcap-gep.projects.earthengine.app/view/us-urban-mental-health)
and its cloud scripts live in the [invest-gee companion repository](https://github.com/Yingjie4Science/invest-gee/tree/main/urban_mental_health).
This repository holds the local methods, audits and frozen published outputs.

## Quick verification

From the repository root, with Python installed:

```sh
python scripts/check_repository.py
```

With the geospatial environment configured as described in the
[reproduction guide](docs/REPRODUCING.md#1-set-up-and-check-the-checkout):

```sh
python -m pip install --no-deps --no-build-isolation -e .
python -m unittest discover -s tests -v
```

The first command checks organization, links and frozen evidence; the tests
check model mechanics. Neither establishes epidemiological validity. Full
raster runs need the external data described in the data guide.

The checkout moved into `gep-global/` on 27 October 2026;
[the root migration record](config/project_root_migration_2026-10-27.json) documents that move.
Existing scripts moved on 27 October 2026. The [migration map](config/layout_migration_2026-10-27.json)
records old and new paths and the previous commit. Source paths inside old run
manifests refer to their historical revisions and have not been rewritten.
