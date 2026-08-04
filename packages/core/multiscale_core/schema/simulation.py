"""Simulation execution modes and timing."""

from __future__ import annotations

from enum import Enum


class SimulationMode(str, Enum):
    """Controls fidelity vs speed."""

    SCREENING = "screening"  # Fast physics proxies (~seconds)
    STANDARD_MD = "standard_md"  # Short real MD runs (~5–30 min)
    PRODUCTION_MD = "production_md"  # Extended CG-MD pipelines (~hours)


# Wall-clock estimates per module (minutes) — pipeline runs sequentially
RUNTIME_ESTIMATES: dict[SimulationMode, dict[str, int]] = {
    SimulationMode.SCREENING: {
        "encapsulation": 1,
        "formation": 1,
        "stability": 1,
        "corona": 1,
        "cell_interaction": 1,
        "transport": 1,
        "release": 1,
    },
    SimulationMode.STANDARD_MD: {
        "encapsulation": 5,
        "formation": 15,
        "stability": 10,
        "corona": 8,
        "cell_interaction": 12,
        "transport": 1,
        "release": 1,
    },
    SimulationMode.PRODUCTION_MD: {
        "encapsulation": 120,
        "formation": 240,
        "stability": 180,
        "corona": 120,
        "cell_interaction": 360,
        "transport": 5,
        "release": 5,
    },
}


def estimate_wall_clock_min(modules: list, mode: SimulationMode) -> int:
    """Critical-path estimate (modules run sequentially)."""
    table = RUNTIME_ESTIMATES[mode]
    return sum(table.get(m.value if hasattr(m, "value") else str(m), 5) for m in modules)


def format_runtime(minutes: int) -> str:
    if minutes < 2:
        return "under 1 minute"
    if minutes < 60:
        return f"~{minutes} minutes"
    hours = minutes / 60
    if hours < 2:
        return f"~{hours:.1f} hour"
    return f"~{hours:.0f} hours"
