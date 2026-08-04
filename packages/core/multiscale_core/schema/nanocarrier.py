"""Nanocarrier design schema — the canonical input for all simulation modules."""

from __future__ import annotations

from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class CarrierType(str, Enum):
    LNP = "lnp"
    LIPOSOME = "liposome"
    POLYMERIC = "polymeric"
    MICELLE = "micelle"
    DENDRIMER = "dendrimer"
    NANOGEl = "nanogel"
    INORGANIC = "inorganic"
    HYBRID = "hybrid"


class LipidComponent(BaseModel):
    name: str = Field(description="Lipid identifier, e.g. DSPC, DSPE-PEG2000, SM-102")
    ratio: float = Field(ge=0, le=1, description="Molar fraction (all lipids sum to 1)")
    charge: int = Field(default=0, description="Net charge at design pH")


class PEGylation(BaseModel):
    enabled: bool = False
    mol_pct: float = Field(default=0, ge=0, le=30)
    peg_length: int = Field(default=2000, description="PEG molecular weight (Da)")


class Ligand(BaseModel):
    name: str
    density_pct: float = Field(ge=0, le=10, description="Mol % of total lipids")
    target: str = Field(description="Target receptor or biomarker, e.g. HER2")


from multiscale_core.schema.drug import DrugPayload, PayloadType, StructureSourceType


class Environment(BaseModel):
    ph: float = Field(default=7.4, ge=1, le=14)
    temperature_k: float = Field(default=310.15, description="Kelvin (~37°C)")
    ionic_strength_m: float = Field(default=0.15, description="Molar ionic strength")
    fluid: Literal["pbs", "serum", "plasma", "cell_media"] = "serum"


class DeliveryTarget(BaseModel):
    cell_type: str | None = None
    tissue: str | None = None
    goal: Literal[
        "maximize_uptake",
        "controlled_release",
        "maximize_penetration",
        "minimize_toxicity",
    ] = "maximize_uptake"


class NanocarrierDesign(BaseModel):
    """Complete nanocarrier specification — input to the workflow planner."""

    id: UUID = Field(default_factory=uuid4)
    name: str = "Untitled design"
    carrier_type: CarrierType = CarrierType.LNP

    drug: DrugPayload
    lipids: list[LipidComponent] = Field(min_length=1)
    pegylation: PEGylation = Field(default_factory=PEGylation)
    ligands: list[Ligand] = Field(default_factory=list)

    target_size_nm: float = Field(default=80, ge=20, le=300)
    shape: Literal["spherical", "discoidal"] = "spherical"
    zeta_potential_mv: float | None = None

    environment: Environment = Field(default_factory=Environment)
    target: DeliveryTarget = Field(default_factory=DeliveryTarget)

    @model_validator(mode="after")
    def validate_lipids(self) -> NanocarrierDesign:
        from multiscale_core.lipids import validate_lipid_composition

        ok, msg = validate_lipid_composition(self.lipids)
        if not ok:
            raise ValueError(msg)
        return self

    def lipid_names(self) -> list[str]:
        return [lipid.name for lipid in self.lipids]


# --- Preset templates ---

LNP_MRNA_TEMPLATE = NanocarrierDesign(
    name="Standard mRNA LNP",
    carrier_type=CarrierType.LNP,
    drug=DrugPayload(
        name="mRNA payload",
        payload_type=PayloadType.MRNA,
        structure_source_type=StructureSourceType.SEQUENCE,
        structure_value="AUGGCCUUGCCGCUCUGUUU",
        loading_pct=2,
        encapsulation_mode="core",
    ),
    lipids=[
        LipidComponent(name="SM-102", ratio=0.50, charge=1),
        LipidComponent(name="DSPC", ratio=0.10, charge=0),
        LipidComponent(name="Cholesterol", ratio=0.385, charge=0),
        LipidComponent(name="DSPE-PEG2000", ratio=0.015, charge=0),
    ],
    pegylation=PEGylation(enabled=True, mol_pct=1.5, peg_length=2000),
    target_size_nm=80,
)

LNP_SMALL_MOLECULE_TEMPLATE = NanocarrierDesign(
    name="Small molecule LNP",
    carrier_type=CarrierType.LNP,
    drug=DrugPayload(
        name="Paclitaxel",
        payload_type=PayloadType.SMALL_MOLECULE,
        structure_source_type=StructureSourceType.PUBCHEM,
        structure_value="36314",
        molecular_weight=853.9,
        loading_pct=10,
        encapsulation_mode="core",
    ),
    lipids=[
        LipidComponent(name="DLin-MC3-DMA", ratio=0.45, charge=1),
        LipidComponent(name="DSPC", ratio=0.10, charge=0),
        LipidComponent(name="Cholesterol", ratio=0.40, charge=0),
        LipidComponent(name="DSPE-PEG2000", ratio=0.05, charge=0),
    ],
    target_size_nm=72,
)
