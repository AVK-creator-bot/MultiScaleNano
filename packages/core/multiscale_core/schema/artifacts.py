"""Scale artifacts — typed outputs that flow between simulation modules."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from multiscale_core.schema.workflow import ModuleName, SimulationScale


class ArtifactFile(BaseModel):
    path: str
    file_type: str
    description: str


class ProvenanceRecord(BaseModel):
    upstream_artifacts: list[UUID] = Field(default_factory=list)
    translation_method: str | None = None
    force_field: str | None = None
    engine_version: str | None = None
    random_seed: int | None = None


class ScaleArtifact(BaseModel):
    """Versioned, typed output from a simulation module."""

    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    module: ModuleName
    scale: SimulationScale
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: dict[str, Any]
    uncertainty: dict[str, Any] = Field(default_factory=dict)
    provenance: ProvenanceRecord = Field(default_factory=ProvenanceRecord)
    files: list[ArtifactFile] = Field(default_factory=list)


# --- Typed artifact payloads (stored in ScaleArtifact.data) ---


class EncapsulationResult(BaseModel):
    drug_retention_free_energy_kcal_mol: float
    encapsulation_efficiency_estimate: float
    drug_bead_coupling: float
    drug_location: str


class FormationResult(BaseModel):
    hydrodynamic_radius_nm: float
    morphology: str
    polydispersity: float
    drug_core_fraction: float


class StabilityResult(BaseModel):
    stability_score: float
    aggregation_propensity: float
    drug_leakage_rate_per_hour: float
    stable_ph_range: tuple[float, float]


class CoronaResult(BaseModel):
    effective_radius_nm: float
    ligand_accessible_fraction: float
    dominant_proteins: list[str]
    surface_charge_delta_mv: float


class TransportResult(BaseModel):
    effective_diffusion_coefficient_m2_s: float
    penetration_depth_um: float
    tissue: str


class ReleaseResult(BaseModel):
    half_life_hours: float
    release_profile: list[dict[str, float]]
    trigger_mechanism: str


class CellInteractionResult(BaseModel):
    membrane_adhesion_energy_kT: float
    uptake_probability: float
    endosomal_escape_probability: float
    intracellular_release_fraction: float
    primary_pathway: str

