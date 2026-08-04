from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


def _readiness_payload() -> dict:
    openmm_ok = False
    openmm_version = None
    try:
        from simulation_worker.engine.openmm_md import OPENMM_AVAILABLE

        openmm_ok = OPENMM_AVAILABLE
        if openmm_ok:
            import openmm

            openmm_version = openmm.__version__
    except ImportError:
        pass

    return {
        "status": "ok" if openmm_ok else "degraded",
        "service": "multiscale-api",
        "openmm_available": openmm_ok,
        "openmm_version": openmm_version,
        "simulations_ready": openmm_ok,
        "message": (
            "Ready to run MD simulations"
            if openmm_ok
            else "OpenMM not installed — run: pip install openmm"
        ),
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
