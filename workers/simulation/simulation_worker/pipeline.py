"""Unified simulation pipeline executor."""

from __future__ import annotations

import logging
from typing import Callable

import httpx

from multiscale_core.schema.artifacts import ScaleArtifact
from multiscale_core.schema.simulation import SimulationMode

logger = logging.getLogger(__name__)


def _default_status(run_id: str, api_url: str) -> Callable[[str, str, str | None], None]:
    def update(module: str, status: str, error: str | None = None) -> None:
        try:
            params: dict[str, str] = {"status": status}
            if error:
                params["error"] = error[:2000]
            response = httpx.patch(
                f"{api_url}/api/runs/{run_id}/modules/{module}",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Status update failed %s/%s: %s", run_id, module, exc)
            raise

    return update


def execute_pipeline(
    run_id: str,
    design_json: str,
    modules: list[str],
    mode: SimulationMode = SimulationMode.STANDARD_MD,
    api_url: str = "http://localhost:8000",
) -> dict[str, ScaleArtifact]:
    from multiscale_core.schema.nanocarrier import NanocarrierDesign
    from simulation_worker.engine.md_dispatch import OPENMM_AVAILABLE
    from simulation_worker.modules.cell_interaction import run_cell_interaction
    from simulation_worker.modules.corona import run_corona
    from simulation_worker.modules.encapsulation import run_encapsulation
    from simulation_worker.modules.formation import run_formation
    from simulation_worker.modules.release import run_release
    from simulation_worker.modules.stability import run_stability
    from simulation_worker.modules.transport import run_transport

    runners = {
        "encapsulation": run_encapsulation,
        "formation": run_formation,
        "stability": run_stability,
        "corona": run_corona,
        "cell_interaction": run_cell_interaction,
        "transport": run_transport,
        "release": run_release,
    }

    design = NanocarrierDesign.model_validate_json(design_json)
    if not OPENMM_AVAILABLE:
        raise RuntimeError(
            "OpenMM is not installed. Run: pip install openmm — simulations require real MD."
        )
    artifacts: dict[str, ScaleArtifact] = {}
    update = _default_status(run_id, api_url)

    for module_name in modules:
        runner = runners.get(module_name)
        if runner is None:
            update(module_name, "failed")
            raise RuntimeError(f"Module not implemented: {module_name}")

        update(module_name, "running")
        try:
            artifact = runner(
                run_id=run_id,
                design=design,
                upstream=artifacts,
                mode=mode,
            )
            artifacts[module_name] = artifact
            update(module_name, "completed")
            logger.info("Completed %s for run %s", module_name, run_id)
        except Exception as exc:
            update(module_name, "failed", str(exc))
            raise

    logger.info("Pipeline complete for run %s: %s", run_id, list(artifacts.keys()))
    return artifacts
