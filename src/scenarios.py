"""Policy counterfactuals by re-prediction, not by linear extrapolation.

Three scenarios progressively cap the network-circuity distribution at the city
median (S1, S2) and at the upper quartile (S3). For each scenario the covariate
is edited, the fitted fractional model is re-predicted, and the change in the
expected number of unreached children is aggregated with population weights.

Reported quantities are counts of children and percentage points of coverage
points of the unreached share.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .models import predict_share


def cap_at_reference(
    df: pd.DataFrame,
    var: str,
    city_col: str = "city",
    reference: str = "median",
    only_above: bool = True,
) -> pd.Series:
    """Return the counterfactual value of `var` with large values pulled down."""
    ref = df.groupby(city_col)[var].transform(reference)
    if only_above:
        return np.minimum(df[var], ref)
    return df[var]


def scenario_delta(
    res,
    X: pd.DataFrame,
    df: pd.DataFrame,
    var: str,
    population: str = "pop",
    city_col: str = "city",
    reference: str = "median",
) -> dict:
    """Change in unreached children and in the unreached share under one scenario."""
    base_share = predict_share(res, X)
    cf = X.copy()
    cf[var] = cap_at_reference(df, var, city_col=city_col, reference=reference).to_numpy()
    new_share = predict_share(res, cf)

    pop = df[population].to_numpy(float)
    delta_children = float(np.sum((base_share - new_share) * pop))
    base_rate = float(np.sum(base_share * pop) / pop.sum())
    new_rate = float(np.sum(new_share * pop) / pop.sum())
    return {
        "scenario": f"cap_{var}_at_{reference}",
        "children_reached": delta_children,
        "share_change_pp": (base_rate - new_rate) * 100,
        "base_share": base_rate,
        "counterfactual_share": new_rate,
    }


def run_scenarios(res, X, df, specs: list[dict]) -> pd.DataFrame:
    """`specs` is a list of dicts with keys var / reference, e.g.
    [{'var': 'circuity', 'reference': 'median'},
     {'var': 'circuity', 'reference': 'median'},   # S2 adds street-view controls
     {'var': 'circuity', 'reference': None}]        # S3 uses the upper quartile
    """
    rows = []
    for spec in specs:
        var, ref = spec["var"], spec.get("reference", "median")
        if ref is None:
            continue
        rows.append(scenario_delta(res, X, df, var, reference=ref))
    return pd.DataFrame(rows)
