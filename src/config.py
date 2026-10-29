"""Configuration loading and path resolution.

Every script reads its parameters from configs/params.yaml via `load_config()`,
never from hard-coded numbers. This is what makes the manuscript reproducible:
changing a threshold changes it in one place only.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def load_config(path: str | None = None) -> dict:
    cfg_path = Path(path) if path else REPO_ROOT / "configs" / "params.yaml"
    with open(cfg_path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    paths = cfg["paths"]
    data_root = Path(os.environ.get("SCHOOL_ACCESS_DATA", paths["data_root"]))
    if not data_root.is_absolute():
        data_root = (REPO_ROOT / data_root).resolve()
    cfg["_data_root"] = data_root
    cfg["_outputs"] = (REPO_ROOT / paths["outputs"]).resolve()
    cfg["_outputs"].mkdir(parents=True, exist_ok=True)
    return cfg


def data_path(key: str) -> Path:
    """Resolve a path entry against the configured data root."""
    cfg = load_config()
    return cfg["_data_root"] / cfg["paths"][key]


def output_path(name: str) -> Path:
    return load_config()["_outputs"] / name
