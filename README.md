# school-access-ceus

Code and derived data for a multi-scale measurement of school accessibility in
China, prepared for submission to *Computers, Environment and Urban Systems*.

The repository answers one question: **can someone else re-run the measurement
protocol on their own data?** It is not a dump of the working directory. Every
number in the manuscript maps to a script (`docs/paper_mapping.md`), and every
parameter lives in one YAML file (`configs/params.yaml`).

## What is here

```
configs/params.yaml       every threshold, speed, polarity and path in the paper
src/g2sfca.py             Gaussian 2SFCA + supply-conservation diagnostic
src/nearest_school.py     independent pipeline: super-source Dijkstra
src/morphology.py         five street-network indicators, circuity, VIF
src/streetview.py         eight street-view indicators -> disadvantage score
src/models.py             fractional logit, Mundlak device, linear benchmark
src/equity.py             within-city tertiles, quadrants, excess co-occurrence, bivariate LISA
src/scenarios.py          counterfactual re-prediction
src/run_all.py            tables from an analysis-ready 1 km table
demo/                     synthetic city + end-to-end assertions
docs/paper_mapping.md     paper item -> function -> output
docs/input_pipeline.md    how the 1 km analysis table itself is built
docs/ceus_outline.md      narrative plan for the manuscript
data/ANALYSIS_TABLE.md    schema contract for the analysis table
DATA_AVAILABILITY.md      what can be shared, what cannot, and the exact wording
```

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

make demo                       # or, without make: python demo/run_demo.py
```

`make demo` takes about two minutes, needs no external data, and prints eight
assertion blocks. On Windows without `make`, `python demo/run_demo.py` is the
equivalent, and it is the command CI runs.

The demo builds a 30 x 30 lattice city, runs the full stack on it, and checks the
properties the manuscript relies on:

1. the G2SFCA identity `sum P_i A_i = sum S_j` holds to 1e-6 when every catchment
   has demand;
2. the identity fails by exactly the capacity of an isolated school — the
   diagnostic reports the shortfall instead of hiding it;
3. the super-source Dijkstra pipeline runs independently of G2SFCA;
4. morphology indicators stay bounded and scale-free;
5. the fractional model recovers a known positive effect and reports marginal
   effects per 1 SD in percentage points;
6. the excess co-occurrence test returns observed / expected / ratio / p;
7. quadrant shares close to 100 %, and the linear benchmark agrees with the
   fractional model on the sign of the simulated effect;
8. the counterfactual moves children in the expected direction.

All numbers printed by the demo are synthetic. They test behaviour, not findings.

## Reproducing the paper

```bash
export SCHOOL_ACCESS_DATA=/path/to/derived/tables     # Windows: set SCHOOL_ACCESS_DATA=...
python -m src.run_all --table "$SCHOOL_ACCESS_DATA/analysis_table_1km.csv" --out outputs/
```

The expected columns are documented in `data/ANALYSIS_TABLE.md`. The export step
that turns raw POI, road network and street-view imagery into that table is
described in `docs/input_pipeline.md` and is not included, because the inputs
cannot be redistributed — see `DATA_AVAILABILITY.md` for the protocol and the
statement to paste into the manuscript.

## Design decisions worth stating in the paper

- **Conservation is a diagnostic, not an assumption.** The identity is reported
  with its residual, so a reader can see when capacity goes unallocated.
- **Two pipelines, no shared code.** G2SFCA and nearest-school Dijkstra are
  computed independently; agreement is evidence, not tautology.
- **Tertiles within city.** A national cut would turn whole cities into
  "deprived" and confound between- with within-city inequality.
- **Independence null, not uniform null.** Co-occurrence is compared with the
  product of marginal disadvantage rates, not with a flat expectation.
- **Re-prediction, not extrapolation.** Scenarios edit covariates and re-predict
  through the fitted non-linear model.

## What is deliberately not included

- Licensed inputs: school POI, street-view imagery, the 30 m education grid.
  Their aggregation rules are documented so the inputs can be rebuilt.
- The plotting scripts: they depend on boundary shapefiles with their own
  licences. Figures are redrawn from the CSV outputs.
- Any absolute path or personal data. The repository is meant to run on someone
  else's machine.

## Licence and citation

Code: MIT (`LICENSE`). Derived data: CC BY 4.0. Cite via `CITATION.cff`.
