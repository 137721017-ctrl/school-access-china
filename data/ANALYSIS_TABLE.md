# Analysis-ready table: expected schema

One row per 1 km cell. This is the contract between the export step (not
included, see `DATA_AVAILABILITY.md`) and `src/run_all.py`. Column names are the
ones used in the manuscript tables, so a reviewer can trace a number from a
paper table back to a column here.

## Identifiers

| column | type | meaning |
|---|---|---|
| `cellid` | int | `row_index * 4860 + col_index` in the China Albers 1 km grid |
| `city` | str | city code for the eight case cities; `NA` for cells outside them |
| `x`, `y` | float | cell centroid, China Albers (Krassovsky), metres |
| `pop` | float | residential population assigned to the cell |

## Dependent variable

| column | unit | meaning |
|---|---|---|
| `walk_unreached_share` | share 0-1 | population-weighted share of the cell beyond the 15-minute walk threshold; computed from the nearest-school pipeline, not from G2SFCA |
| `g2sfca_walk`, `g2sfca_cycle`, `g2sfca_motor` | persons per school place | G2SFCA access values, kept separate per mode; **never** compared across modes |

## Street-network morphology (1 km, within 1 000 m of centroid)

| column | unit | meaning |
|---|---|---|
| `rc` | index 0-1 | gamma index of the local subgraph, `e / (3 (v - 2))` |
| `int_density` | count / km2 | nodes of degree >= 3 |
| `link_node` | ratio | `e / v` |
| `dead_end` | share 0-1 | share of degree-1 nodes |
| `circuity` | ratio | median of network distance / straight-line distance to the assigned school |

## Street-view environment

`GVI`, `TreeShare`, `SVF`, `Enclosure`, `RoadSurface`, `Sidewalk`,
`EarthExposure`, `Diversity` — each in [0, 1], 1 km mean of the point-level
segmentation shares. `env` may be supplied or is derived by
`src/streetview.py` using the polarity table in `configs/params.yaml`.

## Community education

| column | unit | meaning |
|---|---|---|
| `edu_score` | index | 30 m composite of community education level, aggregated to 1 km |

## Weights

| column | meaning |
|---|---|
| `pop` | used as the weight for every population-weighted statistic and for the excess co-occurrence test |

## Rules that the code enforces

1. `walk_unreached_share` must be in [0, 1]; values outside indicate a merging
   error between the grid table and the travel-time table.
2. `circuity >= 1` by construction; values below 1 mean a network/straight
   distance mix-up.
3. Modes are separate models. Any table that puts walk, cycle and motor G2SFCA
   means side by side must be labelled as non-comparable.
