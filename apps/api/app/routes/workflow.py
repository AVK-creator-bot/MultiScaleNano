"""Workflow planning endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from multiscale_core.schema.simulation import SimulationMode
from multiscale_core.schema.workflow import ModuleName, plan_lnp_workflow

router = APIRouter()


class PlanRequest(BaseModel):
    enabled_modules: list[ModuleName] | None = None
    simulation_mode: SimulationMode = SimulationMode.STANDARD_MD


@router.post("/plan")
async def plan_workflow(body: PlanRequest):
    return plan_lnp_workflow(enabled=body.enabled_modules, mode=body.simulation_mode)


@router.get("/modules")
async def list_modules():
    from multiscale_core.schema.workflow import MODULE_REGISTRY

    return list(MODULE_REGISTRY.values())
