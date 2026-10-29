"""Street-network morphology at the 1 km cell level.

Five indicators are computed on the road graph inside a fixed radius around each
cell centroid:

    rc            gamma index of the local subgraph, e / (3 * (v - 2))
    int_density   nodes of degree >= 3 per km2
    link_node     e / v
    dead_end      share of degree-1 nodes
    circuity      median of network distance / straight-line distance

`rc` is reported as a connectivity index rather than a raw node count so that
cells with different numbers of snapped nodes stay comparable. All five are
scale-free with respect to the local subgraph size, which is why they can enter
the same regression.
"""
from __future__ import annotations

from itertools import islice

import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree


def _local_subgraph_counts(graph: nx.Graph, nodes: set) -> tuple[int, int, int, int]:
    v = len(nodes)
    e = sum(1 for u, w in graph.edges if u in nodes and w in nodes)
    intersections = sum(1 for n in nodes if graph.degree[n] >= 3)
    dead_ends = sum(1 for n in nodes if graph.degree[n] == 1)
    return v, e, intersections, dead_ends


def morphology_indicators(
    graph: nx.Graph,
    node_xy: dict,
    cells_xy: np.ndarray,
    radius_m: float = 1000.0,
) -> pd.DataFrame:
    ids = list(node_xy)
    coords = np.array([node_xy[i] for i in ids], float)
    tree = cKDTree(coords)
    area_km2 = np.pi * (radius_m / 1000.0) ** 2

    rows = []
    for cxy in np.asarray(cells_xy, float):
        local = tree.query_ball_point(cxy, r=radius_m)
        nodes = {ids[i] for i in local}
        v, e, intersections, dead_ends = _local_subgraph_counts(graph, nodes)
        rows.append(
            {
                "rc": e / (3 * (v - 2)) if v > 2 else np.nan,
                "int_density": intersections / area_km2,
                "link_node": e / v if v else np.nan,
                "dead_end": dead_ends / v if v else np.nan,
                "n_nodes_local": v,
            }
        )
    return pd.DataFrame(rows)


def circuity_median(
    graph: nx.Graph,
    node_xy: dict,
    origins,
    destinations,
    sample: int | None = 200,
    seed: int = 20261026,
) -> float:
    """Median detour ratio over sampled origin-destination pairs."""
    rng = np.random.default_rng(seed)
    origins, destinations = list(origins), list(destinations)
    if sample and len(origins) > sample:
        origins = list(rng.choice(origins, size=sample, replace=False))
    ratios = []
    for o in origins:
        if not destinations:
            break
        lengths = nx.single_source_dijkstra_path_length(graph, o, weight="length")
        best_node = min(destinations, key=lambda d: lengths.get(d, np.inf))
        net = lengths.get(best_node)
        if net is None or not np.isfinite(net) or net <= 0:
            continue
        straight = np.hypot(
            node_xy[o][0] - node_xy[best_node][0], node_xy[o][1] - node_xy[best_node][1]
        )
        if straight > 0:
            ratios.append(net / straight)
    return float(np.median(ratios)) if ratios else np.nan


def correlation_and_vif(df: pd.DataFrame, cols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Within-city correlation matrix and variance inflation factors (Table 6)."""
    corr = df[cols].corr()
    X = df[cols].astype(float).dropna().to_numpy()
    X = np.column_stack([np.ones(len(X)), X])
    vif = []
    for k, col in enumerate(cols, start=1):
        y = X[:, k]
        Z = np.delete(X, k, axis=1)
        beta, *_ = np.linalg.lstsq(Z, y, rcond=None)
        resid = y - Z @ beta
        r2 = 1 - resid.var() / y.var()
        vif.append({"variable": col, "vif": 1 / (1 - r2) if r2 < 1 else np.inf})
    return corr, pd.DataFrame(vif)


def first_n(d: dict, n: int) -> dict:
    return dict(islice(d.items(), n))
