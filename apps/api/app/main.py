"""MultiscaleNano API — orchestration layer."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import designs, drug, health, lipids, runs, workflow

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MultiscaleNano API",
    description="Unified nanotechnology drug-delivery simulation orchestrator",
    version="0.1.0",
)


@app.on_event("startup")
async def verify_simulation_engine() -> None:
    try:
        from simulation_worker.engine.openmm_md import OPENMM_AVAILABLE

        if OPENMM_AVAILABLE:
            import openmm

            logger.info("OpenMM %s ready — simulations enabled", openmm.__version__)
        else:
            logger.error("OpenMM not installed — simulations disabled")
    except ImportError as exc:
        logger.error("Simulation worker not installed — simulations disabled: %s", exc)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(designs.router, prefix="/api/designs", tags=["designs"])
app.include_router(drug.router, prefix="/api/drug", tags=["drug"])
app.include_router(lipids.router, prefix="/api/lipids", tags=["lipids"])
app.include_router(workflow.router, prefix="/api/workflow", tags=["workflow"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
