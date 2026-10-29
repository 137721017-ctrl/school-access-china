# Paper-to-code map

Numbers in the manuscript should be traceable to a script. This file is the
reverse index: given a table or figure in the paper, which function produces it.

Table and figure numbers follow the current draft of the manuscript
(6 sections, 14 tables, 7 figures). The earlier 8-section draft had 16 tables;
the two extra tables were dropped because a figure already carried the same
information — the coverage column of the old Table 2 became Fig. 2, and the
quadrant shares of the old Table 13 became Fig. 6b.

## Tables

| Paper item | Quantity | Function | Output |
|---|---|---|---|
| Table 1 | Data sources and processing rules | prose; schema in `data/ANALYSIS_TABLE.md` | — |
| Table 2 | Population-weighted supply totals and conservation residual, six mode-stage combinations | `src/g2sfca.py::two_step_fca`, `coverage_share`, `conservation_residual` | `outputs/table2_supply.csv` |
| Table 3 | Time-threshold sensitivity of primary walking coverage and equity | `src/g2sfca.py::threshold_sweep` | `outputs/table3_thresholds.csv` |
| Table 4 | Within-city correlations and VIF of the five morphology indicators (N = 6 009) | `src/morphology.py::correlation_and_vif` | `outputs/table4_vif.csv` |
| Table 5 | Primary 15-minute population coverage by macro-region | `src/g2sfca.py` + regional aggregation | `outputs/table5_regions.csv` |
| Table 6 | Linear fixed-effects vs fractional response, per 1 SD (national, N = 97 338) | `src/models.py::fit_fractional`, `marginal_effects_table`, `fit_linear_fe` | `outputs/table6_specs.csv` |
| Table 7 | Dominant factors by mode and stage | `src/models.py::marginal_effects_table` | `outputs/table7_modes.csv` |
| Table 8 | Within-city correlation of the eight street-view indicators with the unreached share (eight cities, N = 6 012) | `src/streetview.py::within_city_corr` | `outputs/table8_corr.csv` |
| Table 9 | Three specifications of the six-city fractional model (N = 5 277) | `src/models.py::fit_fractional` | `outputs/table9_three_specs.csv` |
| Table 10 | Education gradient of the street-view indicators (N = 6 012, per 1 SD) | `src/streetview.py::education_gradient` | `outputs/table10_gradient.csv` |
| Table 11 | Excess co-occurrence of three disadvantages (within-city tertiles) | `src/equity.py::excess_cooccurrence` | `outputs/table11_excess.csv` |
| Table 12 | Quadrant and deprivation shares by city | `src/equity.py::tertile_disadvantage`, `quadrant_shares` | `outputs/table12_quadrants.csv` |
| Table 13 | Bivariate local Moran's I by city | `src/equity.py::bivariate_lisa` | `outputs/table13_lisa.csv` |
| Table 14 | Nested regression of the three disadvantages (eight cities) | `src/models.py::fit_fractional`, `src/equity.py::tertile_disadvantage` | `outputs/table14_nested.csv` |

## Figures

| Paper item | Quantity | Source of numbers | Output |
|---|---|---|---|
| Fig. 1 | Study area and six case cities | `outputs/table5_regions.csv`, six-city summary | `outputs/fig1.*` |
| Fig. 2 | G2SFCA supply-demand ratio by stage and mode | `outputs/table2_supply.csv` | `outputs/fig2.*` |
| Fig. 3 | Walking unreached share, national and six cities | `src/nearest_school.py::unreached_share` | `outputs/fig3.*` |
| Fig. 4 | Within-city variation of circuity | `src/morphology.py::circuity` | `outputs/fig4.*` |
| Fig. 5 | Street environment vs community education | `src/streetview.py::disadvantage_score` | `outputs/fig5.*` |
| Fig. 6 | Quadrants and triple deprivation | `src/equity.py::quadrant_shares` | `outputs/fig6.*` |
| Fig. 7 | Network-improvement scenarios | `src/scenarios.py::run_scenarios` | `outputs/fig7.*` |

## Status

- Every module in `src/` is exercised by `demo/run_demo.py` on synthetic data,
  and the demo is run by CI on each push.
- The plotting scripts that turn `outputs/` into the seven figures are not part
  of this release: they depend on the boundary and grid shapefiles, which carry
  licences of their own. Figures are redrawn from the CSV outputs; the numbers
  they show come from the functions listed above.
- Upstream construction of the analysis table (population, schools, network,
  street view, education index) is documented in `docs/input_pipeline.md`. The
  production scripts for those stages are available from the corresponding
  author.
