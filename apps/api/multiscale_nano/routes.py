"""REST API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from multiscale_nano_core.schemas import NanocarrierDesign, SimulationRun
from multiscale_nano.orchestrator import orchestrator

router = APIRouter()


class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""


class CreateRunRequest(BaseModel):
    design: NanocarrierDesign


@router.get("/health")
async def health():
    return {"status": "ok", "service": "multiscale-nano-api"}


@router.get("/projects")
async def list_projects():
    return orchestrator.list_projects()


@router.post("/projects")
async def create_project(body: CreateProjectRequest):
    return orchestrator.create_project(body.name, body.description)


@router.get("/projects/{project_id}")
async def get_project(project_id: UUID):
    project = orchestrator.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.post("/projects/{project_id}/runs")
async def create_run(project_id: UUID, body: CreateRunRequest) -> SimulationRun:
    if not orchestrator.get_project(project_id):
        raise HTTPException(404, "Project not found")
    return orchestrator.create_run(project_id, body.design)


@router.get("/projects/{project_id}/runs")
async def list_runs(project_id: UUID):
    return orchestrator.list_runs(project_id)


@router.get("/runs/{run_id}")
async def get_run(run_id: UUID) -> SimulationRun:
    run = orchestrator.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run


@router.post("/runs/{run_id}/start")
async def start_run(run_id: UUID) -> SimulationRun:
    run = orchestrator.start_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run
