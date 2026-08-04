"""Lipid preset and validation endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from multiscale_core.lipids import LIPID_LIBRARY, LIPID_PRESETS, validate_lipid_composition
from multiscale_core.schema.drug import PayloadType
from multiscale_core.schema.nanocarrier import LipidComponent

router = APIRouter()


@router.get("/library")
async def lipid_library():
    return {
        name: {
            "molecular_weight": p.molecular_weight,
            "charge": p.charge,
            "category": p.category,
        }
        for name, p in LIPID_LIBRARY.items()
    }


@router.get("/presets")
async def lipid_presets():
    return {
        key: [c.model_dump() for c in components]
        for key, components in LIPID_PRESETS.items()
    }


class ValidateLipidsRequest(BaseModel):
    lipids: list[LipidComponent]


@router.post("/validate")
async def validate_lipids(body: ValidateLipidsRequest):
    ok, msg = validate_lipid_composition(body.lipids)
    if not ok:
        raise HTTPException(status_code=422, detail=msg)
    total = sum(l.ratio for l in body.lipids)
    return {"valid": True, "total_ratio": total}


@router.get("/preset/{payload_type}")
async def preset_for_payload(payload_type: PayloadType):
    from multiscale_core.lipids import preset_for_payload

    lipids = preset_for_payload(payload_type)
    return {"lipids": [l.model_dump() for l in lipids]}
