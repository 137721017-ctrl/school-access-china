"""Synthetic city used to prove the pipeline runs, not to produce findings.

A 30 x 30 lattice stands in for a street network; 100 cells carry population;
six schools carry capacity. Every module in src/ is exercised on this toy, so a
reader (or reviewer) can run `make demo` and see the code work before any
restricted data is involved.
"""
from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd

SPACING_M = 300.0
N = 30


def generate(seed: int = 20261026) -> dict:
    rng = np.random.default_rng(seed)

    g = nx.grid_2d_graph(N, N)
    node_xy = {(i, j): (i * SPACING_M, j * SPACING_M) for i, j in g.nodes}
    for u, v in g.edges:
        g[u][v]["length"] = SPACING_M

    cells = pd.DataFrame(
        [
            {"cellid": f"c{k}", "row": i, "col": j, "x": node_xy[(i, j)][0], "y": node_xy[(i, j)][1]}
            for k, (i, j) in enumerate([(i, j) for i in range(0, N, 3) for j in range(0, N, 3)])
        ]
    )
    cells["pop"] = rng.integers(200, 3000, len(cells))

    school_nodes = [(3, 4), (10, 12), (18, 7), (24, 22), (8, 25), (27, 3)]
    schools = pd.DataFrame(
        {
            "school_id": [f"s{k}" for k in range(len(school_nodes))],
            "node": school_nodes,
            "x": [node_xy[s][0] for s in school_nodes],
            "y": [node_xy[s][1] for s in school_nodes],
            "capacity": rng.integers(400, 1500, len(school_nodes)),
        }
    )
    return {"graph": g, "node_xy": node_xy, "cells": cells, "schools": schools}


if __name__ == "__main__":
    from pathlib import Path

    out = Path(__file__).resolve().parent / "synthetic"
    out.mkdir(exist_ok=True)
    data = generate()
    data["cells"].to_csv(out / "cells.csv", index=False, encoding="utf-8-sig")
    data["schools"].to_csv(out / "schools.csv", index=False, encoding="utf-8-sig")
    print(f"wrote {out}")
