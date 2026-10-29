# How the 1 km analysis table is built

`src/` reproduces every table in the manuscript **from** the 1 km analysis
table. This document describes the step **before** that: how the analysis table
itself was produced from licensed inputs. The production scripts for these
stages are not in this repository (they read multi-gigabyte licensed files from
fixed paths); they are available from the corresponding author for inspection.

The stages are listed in the order they run. Each one writes a flat table keyed
on `cellid`, so the pipeline can be restarted at any stage.

## 1. Grid definition

A single 1 km lattice is used for the whole country, in China Albers
(Krassovsky): `+proj=aea +lat_1=25 +lat_2=47 +lon_0=105 +ellps=krass`. The
lattice has 4 860 columns and 4 350 rows, with the north-west corner at
(-2 640 000, 5 950 000) m. `cellid = row_index * 4860 + col_index`, so a cell
identifier is stable across every table in the project.

A cell is kept if it intersects the national land mask; 3.10 million cells are
retained, of which those with a residential population form the analysis set.

## 2. Population

Population is disaggregated to 100 m points and then summed to the 1 km cell.
Each 100 m point is snapped to its nearest network node with a KD-tree, which is
what lets a cell inherit a travel time: a cell is represented by the node its
population is closest to, not by its centroid.

Cells with zero population are kept in the grid but excluded from every
population-weighted statistic.

## 3. Schools

School locations come from a POI service (Amap), retrieved in 2025, with
separate queries for primary and secondary schools, using the Chinese
stage names as keywords. Records are
deduplicated on normalised name plus a 150 m radius, which removes the
campuses that the vendor lists under near-identical names while keeping genuine
adjacent schools. The national set contains 224 900 schools after
deduplication.

Each school is snapped to its nearest network node and carries its teaching
capacity `S_j`. Because the point set cannot be redistributed, the
`DATA_AVAILABILITY.md` statement commits to publishing the query terms, dates,
per-city counts and the deduplication rule so the set can be rebuilt.

## 4. Road network and travel time

A routable graph is built per city and per national tile from OpenStreetMap
extracts. Edges carry mode-specific speeds: 4.8 km/h walking, 12 km/h cycling,
25 km/h motorised. The graph is contracted before use, so that a shortest-path
query traverses intersections rather than every geometry vertex.

Two independent time layers are then produced:

- **G2SFCA inputs** — for each school, the set of 1 km cells whose
  population point falls inside the 900 s isochrone; for each cell, the same set
  seen from the demand side.
- **Nearest-school layer** — a single Dijkstra run from a zero-weight
  super-source connected to all school nodes, giving every network node its
  travel time to the closest school of a given stage. This layer never touches
  the G2SFCA code and is what the paper's second pipeline validates against.

## 5. Accessibility, coverage and the 100 m rule

Accessibility uses Gaussian 2SFCA with a 900 s catchment and
`f(d) = exp(-0.5 (d/d0)^2)`, `d0` = half the threshold. Six runs are produced:
{walk, cycle, motor} x {primary, secondary}.

A cell is **covered** when at least 100 m of its area — 10 % of the cell — can
reach a school within the threshold. The 100 m rule is used for every coverage
number in the paper. Coverage computed at the 1 km level (any part of the cell
reached) is a different quantity and is not reported, because it inflates
coverage by construction.

## 6. Street-network morphology

For each cell, the induced subgraph within 1 000 m of the population point is
extracted and five indicators are computed on it: the gamma index `rc`,
intersection density, link/node ratio, dead-end share, and circuity. Circuity is
the median over sampled origin-destination pairs of network distance divided by
straight-line distance to the assigned school, which is why it is a cell-level
median rather than a mean: the distribution is right-skewed and a few
pathological pairs would otherwise dominate.

## 7. Street view

Street-view imagery is sampled along the road network, segmented with a
pre-trained semantic segmentation model, and reduced to eight shares per image:
green view index, tree share, sky view fraction, enclosure, road surface,
sidewalk, earth exposure, diversity. Image-level values are averaged to the
1 km cell.

The eight indicators are then combined into a single disadvantage score by
z-scoring within city and weighting by polarity (`configs/params.yaml`,
`streetview.polarity`), so that a higher score always means a worse street
environment. Coverage is uneven — imagery is denser in central areas — and the
diagnostic is reported in the validation section rather than hidden.

## 8. Community education

A 30 m composite of community-level education is aggregated to the 1 km cell by
population-weighted mean. The 30 m source is not redistributable; the 1 km
aggregate is.

## What is deliberately absent

- No imputation of missing street view: cells without imagery are flagged and
  excluded from street-view models, not filled.
- No smoothing across cells: every statistic is computed on the cell itself, so
  that the spatial autocorrelation reported in the paper is a property of the
  data rather than of the preprocessing.
- No re-projection of the grid: the Albers lattice is the analysis unit
  everywhere, including in the shapefiles exported for mapping.
