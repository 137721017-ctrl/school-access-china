"""Fractional response model with a Mundlak device for city fixed effects.

The dependent variable is a share in [0, 1], so a linear model can predict
impossible values and misweights the tails. Papke-Wooldridge quasi-likelihood
(Binomial GLM with a logit link, no transformation of the outcome) handles the
boundary correctly. City fixed effects are absorbed via the Mundlak device:
within-city means of every covariate are added as regressors, which reproduces
the within estimator when the mean is computed over the full unbalanced panel.

Marginal effects are reported per 1 SD of the covariate and converted to
percentage points, because the logit is non-linear and a raw coefficient is not
interpretable on the scale the results are reported in.

See `fit_fractional` and `marginal_effects_per_sd`.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm


def _mundlak_augment(X: pd.DataFrame, groups: pd.Series) -> pd.DataFrame:
    means = X.groupby(groups.values).transform("mean")
    means.columns = [f"{c}_bar" for c in means.columns]
    return pd.concat([X, means], axis=1)


def fit_fractional(
    df: pd.DataFrame,
    y: str,
    covariates: list[str],
    city_col: str = "city",
    mundlak: bool = True,
    cluster: bool = True,
    keep: list[str] | None = None,
):
    """Fit the fractional logit and return (result, design matrix, used rows).

    `keep` names extra columns (e.g. population weights) that must travel with
    the estimation sample so that later aggregation stays aligned row by row.
    """
    cols = [y, city_col] + covariates + [c for c in (keep or []) if c not in covariates]
    d = df[cols].dropna().copy()
    X = d[covariates].astype(float)
    if mundlak:
        X = _mundlak_augment(X, d[city_col])
    X = sm.add_constant(X)
    model = sm.GLM(d[y].astype(float), X, family=sm.families.Binomial())
    n_groups = d[city_col].nunique()
    if cluster and n_groups > 1:
        res = model.fit(cov_type="cluster", cov_kwds={"groups": d[city_col]})
    else:
        res = model.fit()
    warn_if_suspicious(res)
    return res, X, d


def fit_linear_fe(
    df: pd.DataFrame,
    y: str,
    covariates: list[str],
    city_col: str = "city",
    weights: str | None = None,
):
    """Linear probability benchmark with city fixed effects.

    Present only as the comparison the paper reports (Table 6): the linear model
    is fitted the way it usually is, so that the difference between it and the
    fractional model is a difference in specification rather than in coding
    choices. Returns the results object and the design matrix.
    """
    d = df[[y, city_col] + covariates + ([weights] if weights else [])].dropna().copy()
    X = pd.get_dummies(d[covariates + [city_col]], columns=[city_col], drop_first=True)
    X = sm.add_constant(X.astype(float))
    model = sm.WLS(d[y].astype(float), X, weights=d[weights] if weights else 1.0)
    return model.fit(), X, d


def warn_if_suspicious(res) -> None:
    """Flag separation / non-convergence instead of returning silent garbage.

    A share that is almost perfectly predicted by the covariates produces huge
    t values; reporting them as strong evidence would be a mistake.
    """
    if not getattr(res, "converged", True):
        warnings.warn("fractional logit did not converge; check covariates and scaling")
    t = np.abs(np.asarray(res.tvalues, float))
    if np.nanmax(t) > 100:
        warnings.warn(
            "|t| > 100: likely perfect separation. Check whether the dependent "
            "share is a deterministic function of the covariates."
        )


def average_marginal_effect(res, X: pd.DataFrame, var: str, per: str = "sd") -> dict:
    """Average partial effect of `var`, rescaled to a 1 SD change, in pp."""
    mu = res.fittedvalues.to_numpy()
    dmu = res.params[var] * mu * (1 - mu)
    step = float(X[var].std()) if per == "sd" else 1.0
    return {
        "variable": var,
        "ame": float(np.mean(dmu)),
        "per": per,
        "step": step,
        "effect_pp": float(np.mean(dmu) * step * 100),
    }


def marginal_effects_table(res, X: pd.DataFrame, covariates: list[str], per: str = "sd") -> pd.DataFrame:
    rows = []
    for v in covariates:
        row = average_marginal_effect(res, X, v, per=per)
        row["t"] = float(res.tvalues[v])
        row["p"] = float(res.pvalues[v])
        rows.append(row)
    return pd.DataFrame(rows)[["variable", "effect_pp", "t", "p", "step"]]


def predict_share(res, X: pd.DataFrame) -> np.ndarray:
    """Counterfactual prediction. The non-linear link is why scenarios are
    re-predicted rather than extrapolated from coefficients (Section 4.4)."""
    return np.asarray(res.predict(X), float)
