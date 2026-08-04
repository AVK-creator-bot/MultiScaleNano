"""Workflow orchestrator — builds DAGs, dispatches modules, tracks state."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from multiscale_nano_core.schemas import (
    ModuleStatus,
    NanocarrierDesign,
    SimulationRun,
    SimulationStatus,
)
from multiscale_nano_core.workflow import build_pipeline, get_ready_modules


class Orchestrator:
    """In-memory orchestrator for MVP. Replace with DB + Celery in production."""

    def __init__(self) -> None:
        self._runs: dict[UUID, SimulationRun] = {}
        self._projects: dict[UUID, dict] = {}

    def create_project(self, name: str, description: str = "") -> dict:
        project_id = uuid4()
        project = {
            "id": project_id,
            "name": name,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._projects[project_id] = project
        return project

    def list_projects(self) -> list[dict]:
        return list(self._projects.values())

    def get_project(self, project_id: UUID) -> dict | None:
        return self._projects.get(project_id)

    def create_run(self, project_id: UUID, design: NanocarrierDesign) -> SimulationRun:
        modules = build_pipeline()
        run = SimulationRun(
            project_id=project_id,
            design=design,
            modules=modules,
            status=SimulationStatus.QUEUED,
        )
        self._runs[run.id] = run
        return run

    def get_run(self, run_id: UUID) -> SimulationRun | None:
        return self._runs.get(run_id)

    def list_runs(self, project_id: UUID) -> list[SimulationRun]:
        return [r for r in self._runs.values() if r.project_id == project_id]

    def start_run(self, run_id: UUID) -> SimulationRun | None:
        run = self._runs.get(run_id)
        if not run:
            return None
        run.status = SimulationStatus.RUNNING
        run.updated_at = datetime.utcnow()
        ready = get_ready_modules(run.modules)
        for mod in ready:
            mod.status = ModuleStatus.QUEUED
        return run

    def advance_module(self, run_id: UUID, module_id: str, progress: float = 100.0) -> SimulationRun | None:
        run = self._runs.get(run_id)
        if not run:
            return None
        for mod in run.modules:
            if mod.id == module_id:
                mod.status = ModuleStatus.COMPLETED if progress >= 100 else ModuleStatus.RUNNING
                mod.progress_percent = progress
                if mod.status == ModuleStatus.COMPLETED:
                    mod.completed_at = datetime.utcnow()
                break
        run.updated_at = datetime.utcnow()

        all_done = all(m.status == ModuleStatus.COMPLETED for m in run.modules)
        if all_done:
            run.status = SimulationStatus.COMPLETED
        else:
            for mod in get_ready_modules(run.modules):
                mod.status = ModuleStatus.QUEUED
        return run


orchestrator = Orchestrator()
