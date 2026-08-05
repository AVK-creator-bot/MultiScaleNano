"""Simulation readiness endpoints."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


def _readiness_payload() -> dict:
    openmm_ok = False
    openmm_version = None
    martini_ok = False
    force_field = "lj_coarse_grained"
    ready = openmm_ok
    try:
        from simulation_worker.engine.md_dispatch import (
            MARTINI_AVAILABLE,
            OPENMM_AVAILABLE,
            active_force_field,
            use_martini3,
        )

        openmm_ok = OPENMM_AVAILABLE
        martini_ok = MARTINI_AVAILABLE
        force_field = active_force_field()
        ready = openmm_ok and (not use_martini3() or martini_ok)
        if openmm_ok:
            import openmm

            openmm_version = openmm.__version__
    except ImportError:
        ready = openmm_ok

    message = "Ready to run MD simulations"
    if not openmm_ok:
        message = "OpenMM not installed — run: pip install openmm"
    elif force_field == "martini3" and not martini_ok:
        message = "Martini 3 requested but martini_openmm/insane unavailable"

    return {
        "status": "ok" if ready else "degraded",
        "service": "multiscale-api",
        "openmm_available": openmm_ok,
        "openmm_version": openmm_version,
        "martini_available": martini_ok,
        "active_force_field": force_field,
        "simulations_ready": ready,
        "message": message,
    }


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "multiscale-api"}


@router.get("/health/ready")
async def readiness_check():
    """Check whether the API can run simulations."""
    payload = _readiness_payload()
    if not payload["simulations_ready"]:
        return JSONResponse(status_code=503, content=payload)
    return payload
