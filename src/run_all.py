"""Analysis stages on an analysis-ready cell table.

This entry point intentionally starts from a *derived* table (one row per 1 km
cell, columns documented in the README) rather than from raw
imagery and POI files. Reproducing the results therefore requires one export
step plus this script, not a multi-terabyte download — which is exactly what a
analysis portable.

Usage
-----
    python -m src.run_all --table path/to/analysis_table.csv --out outputs/
    python -m src.run_all --demo
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd

from . import equity, models, scenarios, streetview
from .config import REPO_ROOT, load_config

NUMERIC_REQUIRED = [
    "pop",
    "walk_unreached_share",
    "circuity",
    "dead_end",
    "rc",
    "int_density",
    "link_node",
]
INDICATORS = ["GVI", "TreeShare", "SVF", "Enclosure", "RoadSurface", "Sidewalk", "EarthExposure", "Diversity"]


def check_schema(df: pd.DataFrame) -> list[str]:
    missing = [c for c in NUMERIC_REQUIRED + ["cellid", "city"] if c not in df.columns]
    missing += [c for c in INDICATORS if c not in df.columns]
    return missing


def stage_models(df: pd.DataFrame, cfg: dict, out: Path) -> None:
    covariates = ["circuity", "dead_end", "rc", "int_density", "link_node"]
    if "log_pop" not in df.columns:
        df["log_pop"] = (df["pop"].clip(lower=1)).apply(lambda v: __import__("math").log(v))
    covariates = covariates + ["log_pop"]
    res, X, d = models.fit_fractional(df, cfg["models"]["dependent"], covariates, keep=["pop"])
    me = models.marginal_effects_table(res, X, covariates)
    me.to_csv(out / "table_marginal_effects.csv", index=False, encoding="utf-8-sig")
    print(f"[models] N={int(res.nobs)}  McFadden R2={res.pseudo_rsquared('mcf'):.4f}")
    print(me.to_string(index=False))


def stage_equity(df: pd.DataFrame, out: Path) -> None:
    d = df.copy()
    d["flag_access"] = equity.tertile_disadvantage(d, "walk_unreached_share", higher_is_worse=True) == "disadvantaged"
    d["flag_env"] = equity.tertile_disadvantage(d, "env", higher_is_worse=True) == "disadvantaged"
    d["flag_edu"] = equity.tertile_disadvantage(d, "edu_score", higher_is_worse=False) == "disadvantaged"
    res = equity.excess_cooccurrence(d, ["flag_access", "flag_env", "flag_edu"], weights="pop")
    pd.DataFrame([res]).to_csv(out / "table_excess_cooccurrence.csv", index=False, encoding="utf-8-sig")
    print(f"[equity] observed={res['observed']:.4f} expected={res['expected_if_independent']:.4f} "
          f"ratio={res['ratio']:.2f} p={res['p_value']:.3f}")


def stage_scenarios(df: pd.DataFrame, cfg: dict, out: Path) -> None:
    covariates = ["circuity", "dead_end", "rc", "int_density", "link_node", "log_pop"]
    res, X, d = models.fit_fractional(df, cfg["models"]["dependent"], covariates, keep=["pop"])
    X = X.loc[d.index]
    table = scenarios.run_scenarios(
        res, X, d, [{"var": "circuity", "reference": "median"}, {"var": "circuity", "reference": None}]
    )
    table.to_csv(out / "table_scenarios.csv", index=False, encoding="utf-8-sig")
    print(table.to_string(index=False))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--table", type=Path, help="analysis-ready cell table (csv/parquet)")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--demo", action="store_true", help="run the synthetic end-to-end demo instead")
    args = ap.parse_args(argv)

    if args.demo:
        return subprocess.call([sys.executable, str(REPO_ROOT / "demo" / "run_demo.py")])
    if not args.table:
        ap.error("--table is required (or pass --demo)")

    cfg = load_config()
    out = args.out or cfg["_outputs"]
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.table) if args.table.suffix == ".parquet" else pd.read_csv(args.table)
    missing = check_schema(df)
    if missing:
        print("missing columns:", ", ".join(missing), file=sys.stderr)
        print("see data/ANALYSIS_TABLE.md for the expected schema", file=sys.stderr)
        return 2

    if "env" not in df.columns:
        df["env"] = streetview.disadvantage_score(
            df, INDICATORS, cfg["streetview"]["polarity"], city_col="city"
        )

    stage_models(df, cfg, out)
    stage_equity(df, out)
    stage_scenarios(df, cfg, out)
    print(f"[done] outputs written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
