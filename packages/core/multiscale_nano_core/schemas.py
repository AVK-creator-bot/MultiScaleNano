"""Domain schemas for nanocarrier design and simulation runs."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class CarrierType(str, Enum):
    LNP = "lnp"
    LIPOSOME = "liposome"
    POLYMERIC = "polymeric"
    MICELLE = "micelle"
    DENDRIMER = "dendrimer"
    NANOGEl = "nanogel"
    INORGANIC = "inorganic"
    HYBRID = "hybrid"


class BiologicalFluid(str, Enum):
    PBS = "pbs"
    SERUM = "serum"
    PLASMA = "plasma"
    CYTOSOL = "cytosol"
    CUSTOM = "custom"


class LipidComponent(BaseModel):
    name: str
    mole_fraction: float = Field(ge=0.0, le=1.0)


class DrugPayload(BaseModel):
    name: str = ""
    smiles: str
    loading_percent: float = Field(default=5.0, ge=0.0, le=100.0)


class SurfaceChemistry(BaseModel):
    zeta_potential_mv: float = 0.0
    pegylation_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    ligands: list[str] = Field(default_factory=list)


class Environment(BaseModel):
    ph: float = Field(default=7.4, ge=0.0, le=14.0)
    temperature_k: float = Field(default=310.0, ge=273.0, le=350.0)
    ionic_strength_mm: float = Field(default=150.0, ge=0.0)
    fluid: BiologicalFluid = BiologicalFluid.PBS


class TargetSpec(BaseModel):
    tissue: str = "liver"
    cell_type: str = "hepatocyte"


class NanocarrierDesign(BaseModel):
    """Researcher's nanoparticle design — the starting point for all simulations."""

    id: UUID = Field(default_factory=uuid4)
    name: str = "Untitled LNP"
    carrier_type: CarrierType = CarrierType.LNP
    lipids: list[LipidComponent]
    payload: DrugPayload
    target_size_nm: float = Field(default=80.0, ge=10.0, le=500.0)
    surface: SurfaceChemistry = Field(default_factory=SurfaceChemistry)
    environment: Environment = Field(default_factory=Environment)
    target: TargetSpec = Field(default_factory=TargetSpec)

    @field_validator("lipids")
    @classmethod
    def lipids_sum_to_one(cls, lipids: list[LipidComponent]) -> list[LipidComponent]:
        total = sum(l.mole_fraction for l in lipids)
        if lipids and abs(total - 1.0) > 0.02:
            raise ValueError(f"Lipid mole fractions must sum to 1.0 (got {total:.3f})")
        return lipids


class SimulationStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModuleStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class UncertainValue(BaseModel):
    value: float | None = None
    uncertainty: float | None = None
    unit: str = ""


class BridgeArtifact(BaseModel):
    """Typed output of a scale bridge — consumed by downstream modules."""

    id: UUID = Field(default_factory=uuid4)
    scale: str
    source_modules: list[str]
    fields: dict[str, UncertainValue]
    translation_method: str
    valid_for: list[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PipelineModule(BaseModel):
    id: str
    name: str
    description: str
    engine: str
    depends_on: list[str] = Field(default_factory=list)
    status: ModuleStatus = ModuleStatus.PENDING
    progress_percent: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None


class SimulationRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    design: NanocarrierDesign
    status: SimulationStatus = SimulationStatus.PENDING
    modules: list[PipelineModule]
    artifacts: list[str] = Field(default_factory=list)
    bridge_artifacts: list[BridgeArtifact] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectSummary(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str = ""
    carrier_type: CarrierType = CarrierType.LNP
    created_at: datetime = Field(default_factory=datetime.utcnow)
    latest_run_status: SimulationStatus | None = None
