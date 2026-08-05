"""Helpers to enforce MD-derived inputs — no silent defaults."""

from __future__ import annotations

from typing import Any

from simulation_worker.modules.errors import SimulationAnalysisError


def require_field(data: dict[str, Any], key: str, *, source: str) -> Any:
    if key not in data or data[key] is None:
        raise SimulationAnalysisError(f"{source} missing required MD field: {key}")
    return data[key]
