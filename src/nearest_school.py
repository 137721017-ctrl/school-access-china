"""Nearest-school travel time from a zero-weight super source.

This is the second, deliberately independent pipeline. It shares no code with
the G2SFCA module: it solves a single multi-source shortest-path problem on the
road graph, which cross-checks the catchment results without reusing their
assumptions (manuscript Section 3.2, "two independent pipelines").

A super source connected to every school node with weight 0 turns
"distance to the nearest of k schools" into one Dijkstra pass, which is why
this scales to a national road network.
"""
from __future__ import annotations

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

SUPER_SOURCE = "__super_source__"


def nearest_school_length(
    graph: nx.Graph,
    school_nodes,
    node_xy: dict,
    points_xy: np.ndarray,
    weight: str = "length",
) -> np.ndarray:
    """Network distance (same unit as `weight`) from each point to its nearest school."""
    g = graph.copy()
    g.add_node(SUPER_SOURCE)
    for node in school_nodes:
        g.add_edge(SUPER_SOURCE, node, **{weight: 0.0})

    dist = nx.multi_source_dijkstra_path_length(g, [SUPER_SOURCE], weight=weight)

    ids = list(node_xy)
    coords = np.array([node_xy[i] for i in ids], float)
    tree = cKDTree(coords)
    _, nearest = tree.query(np.asarray(points_xy, float))
    return np.array([dist.get(ids[i], np.nan) for i in nearest], float)


def to_minutes(length_m: np.ndarray, speed_kmh: float) -> np.ndarray:
    return np.asarray(length_m, float) / (speed_kmh * 1000 / 3600) / 60.0


def snap_points(points_xy: np.ndarray, node_ids, node_xy: dict, max_snap_m: float = 500.0):
    """Snap population points to the nearest graph node; returns (ids, distance)."""
    coords = np.array([node_xy[i] for i in node_ids], float)
    tree = cKDTree(coords)
    dist, idx = tree.query(np.asarray(points_xy, float))
    ids = np.asarray(node_ids, dtype=object)[idx]
    ids = np.where(dist <= max_snap_m, ids, None)
    return ids, dist


def unreached_share(minutes: np.ndarray, pop: np.ndarray, threshold_min: float = 15.0) -> float:
    """Population-weighted share of points beyond the time threshold."""
    pop = np.asarray(pop, float)
    m = np.asarray(minutes, float)
    beyond = ~(m <= threshold_min)        # NaN counts as unreached
    return float(np.sum(pop * beyond) / pop.sum()) if pop.sum() else 0.0
