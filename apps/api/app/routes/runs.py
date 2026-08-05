"""Simulation run endpoints."""

import csv
import io
import json
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from multiscale_core.paths import ARTIFACT_DIR
from multiscale_core.lipids import validate_lipid_composition
from multiscale_core.schema.simulation import SimulationMode
from multiscale_core.schema.workflow import ModuleName, plan_lnp_workflow

from app.routes.designs import design_store
from app.services.queue import enqueue_simulation_job
from app.services.store import JsonStore

router = APIRouter()


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ModuleRunStatus(BaseModel):
    module: ModuleName
    status: RunStatus = RunStatus.QUEUED
    started_at: datetime | None = None
    completed_at: datetime | None = None
    artifact_id: UUID | None = None
    error: str | None = None


class SimulationRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    design_id: UUID
    status: RunStatus = RunStatus.QUEUED
    simulation_mode: SimulationMode = SimulationMode.STANDARD_MD
    modules: list[ModuleRunStatus] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


run_store: JsonStore[SimulationRun] = JsonStore("runs", SimulationRun)


class StartRunRequest(BaseModel):
    design_id: UUID
    enabled_modules: list[ModuleName] | None = None
    simulation_mode: SimulationMode = SimulationMode.STANDARD_MD


@router.post("", status_code=201)
async def start_run(body: StartRunRequest):
    design = design_store.get(body.design_id)
    if design is None:
        raise HTTPException(status_code=404, detail="Design not found")

    if body.simulation_mode == SimulationMode.SCREENING:
        raise HTTPException(
            status_code=400,
            detail="Screening mode is disabled — all metrics require MD simulation.",
        )

    # Validate drug structure resolves before queuing expensive MD work
    from multiscale_core.drug.resolver import resolve_drug_structure

    validation_dir = ARTIFACT_DIR / "validation" / str(body.design_id)
    try:
        resolve_drug_structure(design.drug, validation_dir)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Drug structure validation failed: {exc}") from exc

    try:
        from simulation_worker.engine.md_dispatch import OPENMM_AVAILABLE
    except ImportError:
        OPENMM_AVAILABLE = False
    if not OPENMM_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="OpenMM is not installed. Run: pip install openmm — then restart the API.",
        )

    ok, msg = validate_lipid_composition(design.lipids)
    if not ok:
        raise HTTPException(status_code=422, detail=msg)

    plan = plan_lnp_workflow(enabled=body.enabled_modules, mode=body.simulation_mode)
    run = SimulationRun(
        design_id=body.design_id,
        simulation_mode=body.simulation_mode,
        status=RunStatus.RUNNING,
        modules=[ModuleRunStatus(module=node.module) for node in plan.modules],
    )
    run_store.set(run.id, run)

    await enqueue_simulation_job(
        run_id=str(run.id),
        design_json=design.model_dump_json(),
        modules=[m.value for m in plan.module_names()],
        mode=body.simulation_mode,
    )

    return run


@router.get("")
async def list_runs():
    runs = run_store.values()
    runs.sort(key=lambda r: r.created_at, reverse=True)
    return runs


def _load_run_results(run_id: UUID) -> tuple[SimulationRun, dict[str, dict]]:
    run = run_store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    run_dir = ARTIFACT_DIR / str(run_id)
    results: dict[str, dict] = {}
    if run_dir.exists():
        for module_dir in run_dir.iterdir():
            artifact_file = module_dir / "artifact.json"
            if artifact_file.exists():
                results[module_dir.name] = json.loads(artifact_file.read_text(encoding="utf-8"))

    return run, results


@router.get("/{run_id}")
async def get_run(run_id: UUID):
    run = run_store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/{run_id}/results")
async def get_run_results(run_id: UUID):
    """Return aggregated module artifacts for a completed run."""
    run, results = _load_run_results(run_id)
    return {"run_id": str(run_id), "status": run.status, "modules": results}


@router.get("/{run_id}/structure/{module_name}")
async def get_run_structure(run_id: UUID, module_name: str):
    """Return final MD bead coordinates as PDB for 3D visualization."""
    run = run_store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    pdb_path = ARTIFACT_DIR / str(run_id) / module_name / "structure.pdb"
    if not pdb_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Structure not available for this module (run a new simulation after the viewer update)",
        )

    return FileResponse(
        pdb_path,
        media_type="chemical/x-pdb",
        filename=f"run-{run_id}-{module_name}.pdb",
    )


@router.get("/{run_id}/export")
async def export_run_results(run_id: UUID, format: str = Query("json")):
    """Export run results as JSON or CSV for downstream analysis."""
    run, results = _load_run_results(run_id)
    payload = {
        "run_id": str(run_id),
        "design_id": str(run.design_id),
        "status": run.status.value if hasattr(run.status, "value") else run.status,
        "simulation_mode": (
            run.simulation_mode.value
            if hasattr(run.simulation_mode, "value")
            else run.simulation_mode
        ),
        "created_at": run.created_at.isoformat(),
        "modules": results,
    }

    if format.lower() == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["module", "metric", "value", "unit"])
        for module_name, artifact in results.items():
            data = artifact.get("data", {})
            uncertainty = artifact.get("uncertainty", {})
            for key, value in data.items():
                if key in ("methodology", "release_profile", "lipid_composition", "drug_structure"):
                    continue
                if isinstance(value, (dict, list)):
                    continue
                row = [module_name, key, value, ""]
                unc = uncertainty.get(key)
                if isinstance(unc, dict) and "ci_95_low" in unc and "ci_95_high" in unc:
                    row[3] = f"CI [{unc['ci_95_low']:.4g}, {unc['ci_95_high']:.4g}]"
                writer.writerow(row)
        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="run-{run_id}.csv"'},
        )

    if format.lower() != "json":
        raise HTTPException(status_code=400, detail="format must be json or csv")

    return Response(
        content=json.dumps(payload, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="run-{run_id}.json"'},
    )


@router.patch("/{run_id}/modules/{module_name}")
async def update_module_status(
    run_id: UUID,
    module_name: ModuleName,
    status: RunStatus = Query(...),
    error: str | None = Query(None),
):
    """Called by workers to report progress."""
    run = run_store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    for mod in run.modules:
        if mod.module == module_name:
            mod.status = status
            if error:
                mod.error = error[:2000]
            if status == RunStatus.RUNNING:
                mod.started_at = datetime.now(timezone.utc)
            elif status in (RunStatus.COMPLETED, RunStatus.FAILED):
                mod.completed_at = datetime.now(timezone.utc)
            break
    else:
        raise HTTPException(status_code=404, detail="Module not found in run")

    if all(m.status == RunStatus.COMPLETED for m in run.modules):
        run.status = RunStatus.COMPLETED
    elif any(m.status == RunStatus.FAILED for m in run.modules):
        run.status = RunStatus.FAILED
    elif any(m.status == RunStatus.RUNNING for m in run.modules):
        run.status = RunStatus.RUNNING
    elif not any(m.status in (RunStatus.QUEUED, RunStatus.RUNNING) for m in run.modules):
        # All modules reached a terminal state
        run.status = RunStatus.COMPLETED if all(
            m.status == RunStatus.COMPLETED for m in run.modules
        ) else RunStatus.FAILED

    run_store.set(run_id, run)
    return run
