# school-access-china

[![demo](https://github.com/137721017-ctrl/school-access-china/actions/workflows/demo.yml/badge.svg)](https://github.com/137721017-ctrl/school-access-china/actions/workflows/demo.yml)

Measurement code for multi-scale school accessibility in China: Gaussian 2SFCA
with a supply-conservation diagnostic, an independent nearest-school pipeline,
street-network morphology, street-view environmental quality, fractional-response
models, and spatial equity diagnostics.

## Install and run

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-optional.txt             # only for bivariate LISA

make demo                                            # or: python demo/run_demo.py
```

The demo builds a 30 x 30 synthetic city, runs the whole stack on it and prints
eight assertion blocks in about two minutes. It needs no external data, and CI
runs it on Python 3.10 and 3.12 for every push.

On your own data:

```bash
python -m src.run_all --table path/to/analysis_table_1km.csv --out outputs/
```

## Contents

```
configs/params.yaml    every threshold, speed, polarity and path
src/g2sfca.py          Gaussian 2SFCA + supply-conservation diagnostic
src/nearest_school.py  independent pipeline: super-source Dijkstra
src/morphology.py      five street-network indicators, circuity, VIF
src/streetview.py      eight street-view indicators -> disadvantage score
src/models.py          fractional logit, Mundlak device, linear benchmark
src/equity.py          within-city tertiles, quadrants, excess co-occurrence, bivariate LISA
src/scenarios.py       counterfactual re-prediction
src/run_all.py         all stages from an analysis-ready 1 km table
demo/                  synthetic city + end-to-end assertions
```

## Input table

One row per 1 km cell. Columns used by `src/run_all.py`:

| column | unit | meaning |
|---|---|---|
| `cellid` | int | `row_index * 4860 + col_index` in the China Albers 1 km grid |
| `city` | str | city code for the case cities; `NA` outside them |
| `x`, `y` | m | cell centroid, China Albers (Krassovsky) |
| `pop` | persons | residential population; weight for every population-weighted statistic |
| `walk_unreached_share` | share 0-1 | population-weighted share beyond the walk threshold |
| `g2sfca_walk`, `g2sfca_cycle`, `g2sfca_motor` | persons per place | access values, one model per mode |
| `rc` | index 0-1 | gamma index of the local subgraph, `e / (3 (v - 2))` |
| `int_density` | count/km2 | nodes of degree >= 3 |
| `link_node` | ratio | `e / v` |
| `dead_end` | share 0-1 | share of degree-1 nodes |
| `circuity` | ratio | network distance / straight-line distance to the assigned school |
| `GVI` `TreeShare` `SVF` `Enclosure` `RoadSurface` `Sidewalk` `EarthExposure` `Diversity` | share 0-1 | street-view segmentation shares, 1 km mean; `env` is derived from them |
| `edu_score` | index | 30 m community education composite, aggregated to 1 km |

Three rules the code enforces: `walk_unreached_share` must lie in [0, 1];
`circuity >= 1` by construction; and walk, cycle and motor access are separate
models that must never be compared across modes.

## Data

The licensed inputs behind that table - school POI, street-view imagery and the
30 m education grid - cannot be redistributed. `src/run_all.py` therefore starts
from the derived 1 km table, so the pipeline runs without them.

## Licence and citation

Code: MIT (`LICENSE`). Derived tables: CC BY 4.0. Citation metadata: `CITATION.cff`.
