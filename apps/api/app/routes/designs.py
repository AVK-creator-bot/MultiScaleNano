"""Nanocarrier design endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from multiscale_core.lipids import validate_lipid_composition
from multiscale_core.schema.nanocarrier import (
    LNP_MRNA_TEMPLATE,
    LNP_SMALL_MOLECULE_TEMPLATE,
    NanocarrierDesign,
)
from app.services.store import JsonStore

router = APIRouter()

design_store: JsonStore[NanocarrierDesign] = JsonStore("designs", NanocarrierDesign)


class CreateDesignRequest(BaseModel):
    design: NanocarrierDesign


@router.get("/templates")
async def list_templates():
    return {
        "templates": [
            {"id": "lnp_mrna", "name": "Standard mRNA LNP", "design": LNP_MRNA_TEMPLATE},
            {
                "id": "lnp_small_molecule",
                "name": "Small molecule LNP",
                "design": LNP_SMALL_MOLECULE_TEMPLATE,
            },
        ]
    }


@router.post("", status_code=201)
async def create_design(body: CreateDesignRequest):
    design = body.design
    ok, msg = validate_lipid_composition(design.lipids)
    if not ok:
        raise HTTPException(status_code=422, detail=msg)
    design_store.set(design.id, design)
    return design


@router.get("/{design_id}")
async def get_design(design_id: UUID):
    design = design_store.get(design_id)
    if design is None:
        raise HTTPException(status_code=404, detail="Design not found")
    return design


@router.get("")
async def list_designs():
    return design_store.values()
