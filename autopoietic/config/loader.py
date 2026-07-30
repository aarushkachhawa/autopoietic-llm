from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from autopoietic.config.schema import RootConfig


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = _deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


def apply_dotted_override(data: dict[str, Any], dotted_key: str, value: Any) -> None:
    """Set data['a']['b']['c'] = value given dotted_key = 'a.b.c'."""
    keys = dotted_key.split(".")
    d = data
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


def load_config(
    paths: Path | list[Path] | None = None,
    overrides: dict[str, Any] | None = None,
) -> RootConfig:
    """Load and layer config files in order (later files override earlier
    ones), then apply an optional final overrides dict."""
    if paths is None:
        paths = []
    elif isinstance(paths, Path):
        paths = [paths]

    data: dict[str, Any] = {}
    for path in paths:
        with open(path) as f:
            data = _deep_merge(data, yaml.safe_load(f) or {})
    if overrides:
        data = _deep_merge(data, overrides)
    return RootConfig.model_validate(data)
