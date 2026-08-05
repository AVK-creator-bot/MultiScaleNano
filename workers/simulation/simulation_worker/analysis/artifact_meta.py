"""Attach methodology records and uncertainty to simulation artifacts."""

from __future__ import annotations

from typing import Any

from multiscale_core.analysis.methodology import AnalysisMethod, UncertaintyRecord


def enrich_artifact_data(
    data: dict[str, Any],
    methods: list[AnalysisMethod],
    uncertainty: dict[str, UncertaintyRecord] | None = None,
    *,
    analysis_source: str = "openmm_md_trajectory",
    model_disclaimer: str | None = None,
) -> dict[str, Any]:
    data = dict(data)
    data["analysis_source"] = analysis_source
    data["methodology"] = [m.model_dump() for m in methods]
    if model_disclaimer:
        data["model_disclaimer"] = model_disclaimer
    if uncertainty:
        data["uncertainty"] = {k: v.model_dump() for k, v in uncertainty.items()}
    return data
