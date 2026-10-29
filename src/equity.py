"""Equity diagnostics: within-city tertiles, excess co-occurrence, bivariate LISA.

Two design choices carry the argument and are therefore explicit here:

1. Advantage and disadvantage are defined by within-city tertiles, not by a
   national median. A national cut would classify whole cities as deprived and
   confound between-city inequality with within-city inequality.

2. Co-occurrence is tested against an independence null built from the marginal
   disadvantage rates, not against a uniform null. The question is whether three
   disadvantages meet more often than the product of their own frequencies.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def tertile_disadvantage(
    df: pd.DataFrame,
    var: str,
    city_col: str = "city",
    higher_is_worse: bool = True,
) -> pd.Series:
    """Return 'advantaged' / 'middle' / 'disadvantaged' within each city."""
    def label(s: pd.Series) -> pd.Series:
        q1, q2 = s.quantile([1 / 3, 2 / 3])
        if higher_is_worse:
            return pd.cut(s, [-np.inf, q1, q2, np.inf], labels=["advantaged", "middle", "disadvantaged"])
        return pd.cut(s, [-np.inf, q1, q2, np.inf], labels=["disadvantaged", "middle", "advantaged"])

    return df.groupby(city_col)[var].transform(lambda s: label(s))


def excess_cooccurrence(
    df: pd.DataFrame,
    flags: list[str],
    weights: str | None = None,
    n_perm: int = 999,
    seed: int = 20261026,
) -> dict:
    """Observed joint rate vs the independence expectation, with a permutation p.

    `flags` are boolean columns marking disadvantage on each dimension.
    The permutation shuffles one dimension against the others, which preserves
    both marginals and the spatial weights while destroying the association.
    """
    w = df[weights].to_numpy(float) if weights else np.ones(len(df))
    w = w / w.sum()
    obs = float(np.sum(w * df[flags].all(axis=1).to_numpy()))
    expected = float(np.prod([np.sum(w * df[f].to_numpy()) for f in flags]))

    rng = np.random.default_rng(seed)
    sims = np.empty(n_perm) if n_perm else np.array([])
    base = df[flags].to_numpy()
    for k in range(n_perm):
        perm = base.copy()
        j = rng.integers(0, len(flags))
        perm[:, j] = rng.permutation(perm[:, j])
        sims[k] = np.sum(w * perm.all(axis=1))

    return {
        "observed": obs,
        "expected_if_independent": expected,
        "ratio": obs / expected if expected else np.nan,
        "p_value": float((sims >= obs).mean()) if n_perm else np.nan,
        "n_perm": n_perm,
    }


def quadrant_shares(
    df: pd.DataFrame,
    acc_var: str,
    edu_var: str,
    weight: str = "pop",
    city_col: str = "city",
    extra_flags: list[str] | None = None,
) -> pd.DataFrame:
    """Population-weighted share of the four accessibility x education quadrants.

    Both dimensions are cut at within-city tertiles first, so the quadrants are
    relative to each city rather than to the national distribution. A cell is
    "disadvantaged" on a dimension when it falls in the bottom tertile of the
    *good* direction; the two mismatch rows are the interesting ones, because
    they separate "cannot reach a school" from "reaches a poorly performing
    one".
    """
    d = df.copy()
    acc_bad = tertile_disadvantage(d, acc_var, city_col, higher_is_worse=True) == "disadvantaged"
    edu_bad = tertile_disadvantage(d, edu_var, city_col, higher_is_worse=False) == "disadvantaged"
    d["_both_bad"] = acc_bad & edu_bad
    d["_social"] = ~acc_bad & edu_bad        # access fine, community education poor
    d["_spatial"] = acc_bad & ~edu_bad       # access poor, community education fine
    d["_both_good"] = ~acc_bad & ~edu_bad

    cols = ["_both_bad", "_social", "_spatial", "_both_good"] + list(extra_flags or [])
    rows = []
    for city, g in d.groupby(city_col):
        w = g[weight].to_numpy(float)
        w = w / w.sum() if w.sum() else w
        row = {"city": city, "n_cells": len(g)}
        row.update({c.strip("_"): float(np.sum(w * g[c].to_numpy(float))) * 100 for c in cols})
        rows.append(row)
    return pd.DataFrame(rows)


def bivariate_lisa(gdf, x: str, y: str, permutations: int = 999, seed: int = 20261026):
    """Bivariate local Moran's I on standardised x and spatially lagged y.

    Requires geopandas + libpysal + esda; kept optional so the rest of the
    pipeline runs without the spatial stack installed.
    """
    from esda.moran import Moran_BV
    from libpysal.weights import Queen

    w = Queen.from_dataframe(gdf, use_index=False)
    w.transform = "r"
    zx = (gdf[x] - gdf[x].mean()) / gdf[x].std()
    zy = (gdf[y] - gdf[y].mean()) / gdf[y].std()
    mi = Moran_BV(np.column_stack([zx, zy]), w, permutations=permutations, seed=seed)
    lag = w.sparse @ zy.to_numpy()
    quadrant = np.select(
        [(zx > 0) & (lag > 0), (zx < 0) & (lag > 0), (zx < 0) & (lag < 0)],
        ["high-high", "low-high", "low-low"],
        default="high-low",
    )
    out = gdf.copy()
    out["lisa_I"] = mi.Is
    out["lisa_p"] = mi.p_sim
    out["quadrant"] = quadrant
    return out, mi
