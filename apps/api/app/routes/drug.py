"""Drug structure resolution API."""

from pathlib import Path
from tempfile import mkdtemp

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from multiscale_core.drug.resolver import resolve_drug_structure
from multiscale_core.schema.drug import DrugPayload

router = APIRouter()


class ResolveDrugRequest(BaseModel):
    drug: DrugPayload


@router.get("/health")
async def drug_health():
    return {"status": "ok", "service": "drug_resolver"}


@router.post("/resolve")
async def resolve_drug(body: ResolveDrugRequest):
    """Validate and resolve drug structure before starting simulation."""
    tmp = Path(mkdtemp(prefix="multiscale_drug_"))
    try:
        resolved = resolve_drug_structure(body.drug, tmp)
        return {
            "valid": True,
            "resolved": resolved.model_dump(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/validate")
async def validate_drug(body: ResolveDrugRequest):
    """Alias for /resolve — validate structure is resolvable."""
    return await resolve_drug(body)
