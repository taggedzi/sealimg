"""Profile resolution helpers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def merge_profile(
    config_defaults: dict[str, Any],
    selected_profile: dict[str, Any],
    cli_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Merge profile values with precedence:
    config defaults < selected profile < CLI overrides.
    """
    merged = _deep_merge(config_defaults, selected_profile)
    if cli_overrides:
        merged = _deep_merge(merged, cli_overrides)
    return merged


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result
