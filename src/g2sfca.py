"""Gaussian two-step floating catchment area (G2SFCA) with an explicit
supply-conservation diagnostic.

The identity  sum_i P_i A_i == sum_j S_j  holds only when every supply site
has a non-empty catchment. Capacity sitting in catchments with no demand is
never allocated, and the shortfall is exactly the amount by which the identity
fails. We therefore return the residual instead of hiding it, because the
paper's central claim is about redistribution, not creation, of capacity.

Reference: Dai (2010) and the G2SFCA formulation in the manuscript, Eq. (1)-(2).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.spatial import cKDTree


def gaussian_decay(d: np.ndarray, d0: float) -> np.ndarray:
    d = np.asarray(d, dtype=float)
    w = np.exp(-0.5 * (d / d0) ** 2)
    return np.where(d <= d0, w, 0.0)


@dataclass
class G2SFCAResult:
    access: np.ndarray          # A_i, one value per demand point
    supply_ratio: np.ndarray    # R_j, one value per supply site
    identity_lhs: float         # sum_i P_i A_i
    identity_rhs: float         # sum_j S_j
    identity_gap_pp: float      # relative gap, in percent of total supply
    unallocated_capacity: float
    n_demand_served: int

    def as_dict(self) -> dict:
        return {
            "identity_lhs": self.identity_lhs,
            "identity_rhs": self.identity_rhs,
            "identity_gap_pp": self.identity_gap_pp,
            "unallocated_capacity": self.unallocated_capacity,
            "n_demand_served": self.n_demand_served,
        }


def two_step_fca(
    demand_xy: np.ndarray,
    demand_pop: np.ndarray,
    supply_xy: np.ndarray,
    supply_cap: np.ndarray,
    d0: float,
    decay=gaussian_decay,
) -> G2SFCAResult:
    """Run G2SFCA.

    Parameters are plain arrays so the function can be unit-tested on synthetic
    data (see demo/run_demo.py) and reused for any mode or school stage.
    """
    demand_xy = np.asarray(demand_xy, float)
    supply_xy = np.asarray(supply_xy, float)
    pop = np.asarray(demand_pop, float)
    cap = np.asarray(supply_cap, float)

    n_d, n_s = len(demand_xy), len(supply_xy)
    d_tree, s_tree = cKDTree(demand_xy), cKDTree(supply_xy)

    rows, cols, vals = [], [], []
    for j, neighbours in enumerate(s_tree.query_ball_point(demand_xy, r=d0)):
        if not neighbours:
            continue
        d = np.linalg.norm(supply_xy[neighbours] - demand_xy[j], axis=1)
        w = decay(d, d0)
        keep = w > 0
        rows.extend(np.full(keep.sum(), j))
        cols.extend(np.asarray(neighbours)[keep])
        vals.extend(w[keep])

    W = sparse.csr_matrix((vals, (rows, cols)), shape=(n_d, n_s))

    demand_weight = W.T @ pop            # sum_i P_i f(d_ij)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(demand_weight > 0, cap / demand_weight, 0.0)
    access = W @ ratio

    lhs = float(np.sum(pop * access))
    rhs = float(np.sum(cap))
    unallocated = float(np.sum(cap[demand_weight == 0]))
    gap = (rhs - lhs) / rhs * 100 if rhs else 0.0

    return G2SFCAResult(
        access=access,
        supply_ratio=ratio,
        identity_lhs=lhs,
        identity_rhs=rhs,
        identity_gap_pp=gap,
        unallocated_capacity=unallocated,
        n_demand_served=int(np.sum(access > 0)),
    )


def coverage_share(access: np.ndarray, pop: np.ndarray, threshold: float = 0.0) -> float:
    """Population-weighted share of demand points above a coverage threshold."""
    pop = np.asarray(pop, float)
    hit = (np.asarray(access) > threshold).astype(float)
    return float(np.sum(pop * hit) / pop.sum()) if pop.sum() else 0.0


def threshold_sweep(
    demand_xy: np.ndarray,
    demand_pop: np.ndarray,
    supply_xy: np.ndarray,
    supply_cap: np.ndarray,
    thresholds=(600, 900, 1200, 1500, 1800),
) -> pd.DataFrame:
    """Sensitivity of coverage to the time threshold (manuscript Table 3)."""
    out = []
    for t in thresholds:
        res = two_step_fca(demand_xy, demand_pop, supply_xy, supply_cap, d0=t)
        out.append(
            {
                "threshold_s": t,
                "coverage": coverage_share(res.access, demand_pop),
                "identity_gap_pp": res.identity_gap_pp,
            }
        )
    return pd.DataFrame(out)
