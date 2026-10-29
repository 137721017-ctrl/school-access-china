"""End-to-end smoke test on the synthetic city.

Each assertion below checks one stated property of the pipeline. If one fails,
the behaviour it describes cannot be claimed.

    python demo/run_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from demo.make_synthetic import generate  # noqa: E402
from src import equity, models, morphology, nearest_school, scenarios  # noqa: E402
from src.g2sfca import coverage_share, gaussian_decay, two_step_fca  # noqa: E402

WALK_MPS = 1.4


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    data = generate()
    cells, schools, graph, node_xy = data["cells"], data["schools"], data["graph"], data["node_xy"]
    d0_s = 900.0
    d0_m = d0_s * WALK_MPS

    section("1. G2SFCA identity")
    res = two_step_fca(
        cells[["x", "y"]].to_numpy(),
        cells["pop"].to_numpy(),
        schools[["x", "y"]].to_numpy(),
        schools["capacity"].to_numpy(),
        d0=d0_m,
    )
    gap = abs(res.identity_gap_pp)
    print(f"lhs={res.identity_lhs:,.1f}  rhs={res.identity_rhs:,.1f}  gap={gap:.6f}%")
    assert gap < 1e-6, "supply conservation must hold when all catchments are non-empty"
    cov = coverage_share(res.access, cells["pop"].to_numpy())
    print(f"coverage={cov:.3f}  served={res.n_demand_served}/{len(cells)}")
    assert 0 <= cov <= 1

    section("2. Unallocated capacity is visible, not hidden")
    far = pd.DataFrame(
        {"school_id": ["far"], "node": [(0, 0)], "x": [1e6], "y": [1e6], "capacity": [999]}
    )
    schools2 = pd.concat([schools, far], ignore_index=True)
    res2 = two_step_fca(
        cells[["x", "y"]].to_numpy(), cells["pop"].to_numpy(),
        schools2[["x", "y"]].to_numpy(), schools2["capacity"].to_numpy(), d0=d0_m,
    )
    print(f"unallocated={res2.unallocated_capacity:.0f}  gap={res2.identity_gap_pp:.3f}%")
    assert abs(res2.identity_gap_pp) > 0, "isolated capacity must break the identity"
    assert abs(res2.unallocated_capacity - 999) < 1e-9

    section("3. Nearest school by super-source Dijkstra")
    lengths = nearest_school.nearest_school_length(
        graph, list(schools["node"]), node_xy, cells[["x", "y"]].to_numpy()
    )
    minutes = nearest_school.to_minutes(lengths, speed_kmh=WALK_MPS * 3.6)
    assert np.isfinite(minutes).all()
    print(f"median={np.median(minutes):.1f} min  p95={np.percentile(minutes, 95):.1f} min")
    print(f"unreached(15min)={nearest_school.unreached_share(minutes, cells['pop'].to_numpy()):.3f}")

    section("4. Morphology indicators")
    morph = morphology.morphology_indicators(graph, node_xy, cells[["x", "y"]].to_numpy(), radius_m=600)
    print(morph.describe().loc[["mean", "min", "max"]].round(3).to_string())
    assert morph["dead_end"].dropna().between(0, 1).all()

    section("5. Fractional response model")
    df = cells.merge(morph, left_index=True, right_index=True)
    rng = np.random.default_rng(7)
    df["circuity"] = rng.uniform(1.2, 1.8, len(df))
    z = lambda s: (s - s.mean()) / s.std()
    df["rc_z"], df["circ_z"] = z(df["rc"]), z(df["circuity"])
    df["walk_unreached_share"] = 1 / (
        1 + np.exp(-(-1.0 + 1.2 * df["rc_z"] + 1.5 * df["circ_z"] + rng.normal(0, 0.3, len(df))))
    )
    df["city"] = "demo"
    df["log_pop"] = np.log(df["pop"])
    df["dead_end"] = df["link_node"] = df["int_density"] = 0.0
    fit, X, d = models.fit_fractional(df, "walk_unreached_share", ["rc_z", "circ_z", "log_pop"], mundlak=False)
    me = models.marginal_effects_table(fit, X, ["rc_z", "circ_z", "log_pop"])
    print(me.round(3).to_string(index=False))
    assert fit.params["rc_z"] > 0 and fit.params["circ_z"] > 0, "simulated effects must recover their signs"

    section("6. Equity diagnostics")
    df["env"] = rng.normal(0, 1, len(df))
    df["edu_score"] = -0.6 * df["env"] + rng.normal(0, 1, len(df))
    d2 = df.copy()
    d2["f1"] = equity.tertile_disadvantage(d2, "walk_unreached_share") == "disadvantaged"
    d2["f2"] = equity.tertile_disadvantage(d2, "env") == "disadvantaged"
    d2["f3"] = equity.tertile_disadvantage(d2, "edu_score", higher_is_worse=False) == "disadvantaged"
    co = equity.excess_cooccurrence(d2, ["f1", "f2", "f3"], weights="pop", n_perm=199)
    print({k: round(v, 4) if isinstance(v, float) else v for k, v in co.items()})
    assert co["ratio"] > 0

    section("6b. Quadrant shares and the linear benchmark")
    qs = equity.quadrant_shares(df, "walk_unreached_share", "edu_score", weight="pop")
    print(qs.round(1).to_string(index=False))
    quad_cols = ["both_bad", "social", "spatial", "both_good"]
    assert (qs[quad_cols].sum(axis=1) - 100).abs().max() < 1e-6, "quadrant shares must close to 100%"
    lin, _, _ = models.fit_linear_fe(df, "walk_unreached_share", ["rc_z", "circ_z", "log_pop"])
    print(f"linear rc_z={lin.params['rc_z']:+.4f}   fractional rc_z={fit.params['rc_z']:+.4f}")
    assert np.sign(lin.params["rc_z"]) == np.sign(fit.params["rc_z"]), (
        "the two specifications must at least agree on the sign of the simulated effect"
    )

    section("7. Counterfactual re-prediction")
    fit2, X2, d3 = models.fit_fractional(
        df, "walk_unreached_share", ["circuity", "log_pop"], mundlak=False, keep=["pop"]
    )
    out = scenarios.scenario_delta(fit2, X2, d3, "circuity", population="pop", reference="median")
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in out.items()})
    assert out["children_reached"] > 0, "pulling circuity down to the median must reduce unreached children"

    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
