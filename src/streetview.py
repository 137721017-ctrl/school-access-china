"""Street-view based environmental quality, oriented as a disadvantage score.

Eight indicators are derived from semantic segmentation of street-view imagery.
Each is oriented with `polarity` (+1 worse when higher, -1 protective), z-scored
within city, and averaged. The result, `env`, is a disadvantage score: larger
values mean a worse walking environment. Keeping the orientation in one place
avoids the sign flips that plague composite indices.

"""
from __future__ import annotations

import numpy as np
import pandas as pd


def disadvantage_score(
    df: pd.DataFrame,
    indicators: list[str],
    polarity: dict[str, int],
    city_col: str = "city",
    eps: float = 1e-9,
) -> pd.Series:
    z = df.groupby(city_col)[indicators].transform(lambda s: (s - s.mean()) / (s.std() + eps))
    signed = z.mul(pd.Series(polarity).reindex(indicators), axis=1)
    return signed.mean(axis=1).rename("env")


def within_city_corr(df: pd.DataFrame, cols: list[str], target: str, city_col: str = "city") -> pd.DataFrame:
    """Within-city Pearson r between each indicator and a deprivation measure."""
    parts = []
    for col in cols:
        rs = df.groupby(city_col).apply(
            lambda g: g[col].corr(g[target]), include_groups=False
        )
        parts.append({"indicator": col, "r_within_city": float(rs.mean()), "n_cities": int(rs.notna().sum())})
    return pd.DataFrame(parts).sort_values("r_within_city")


def education_gradient(
    df: pd.DataFrame,
    indicators: list[str],
    education: str = "edu_score",
    city_col: str = "city",
    cluster: bool = True,
) -> pd.DataFrame:
    """Regress each street-view indicator on community education, city FE.

    Returns coefficients per 1 SD of education, in indicator SD units, which is
    the quantity reported in Table 11.
    """
    import statsmodels.api as sm

    rows = []
    for col in indicators:
        d = df[[col, education, city_col]].dropna()
        d = d.copy()
        d["edu_z"] = (d[education] - d[education].mean()) / d[education].std()
        X = pd.get_dummies(d[city_col], drop_first=True, dtype=float)
        X["edu_z"] = d["edu_z"]
        X = sm.add_constant(X)
        y = (d[col] - d[col].mean()) / d[col].std()
        if cluster:
            res = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": d[city_col]})
        else:
            res = sm.OLS(y, X).fit()
        rows.append(
            {
                "indicator": col,
                "coef_per_sd": res.params["edu_z"],
                "t": res.tvalues["edu_z"],
                "p": res.pvalues["edu_z"],
                "n": int(res.nobs),
            }
        )
    return pd.DataFrame(rows)
