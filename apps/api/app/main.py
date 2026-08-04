"""MultiscaleNano API — orchestration layer."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import designs, drug, health, lipids, runs, workflow

app = FastAPI(
    title="MultiscaleNano API",
    description="Unified nanotechnology drug-delivery simulation orchestrator",
    version="0.1.0",
)

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
