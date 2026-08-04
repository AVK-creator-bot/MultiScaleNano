"""Scale bridges — translate artifacts between simulation modules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from multiscale_core.schema.artifacts import (
    EncapsulationResult,
    FormationResult,
    ScaleArtifact,
)
from multiscale_core.schema.workflow import ModuleName, SimulationScale


class ValidationResult(BaseModel):
    valid: bool
    warnings: list[str] = []
    errors: list[str] = []


class ScaleBridge(ABC):
    name: str
    source_module: ModuleName
    target_module: ModuleName
    input_scale: SimulationScale
    output_scale: SimulationScale

    @abstractmethod
    def validate(self, artifact: ScaleArtifact) -> ValidationResult:
        ...

    @abstractmethod
    def translate(self, artifact: ScaleArtifact) -> dict[str, Any]:
        ...


class EncapsulationToFormation(ScaleBridge):
    """Map atomistic/CG encapsulation results to formation module inputs."""

    name = "encapsulation_to_formation"
    source_module = ModuleName.ENCAPSULATION
    target_module = ModuleName.FORMATION
    input_scale = SimulationScale.COARSE_GRAINED
    output_scale = SimulationScale.COARSE_GRAINED

    def validate(self, artifact: ScaleArtifact) -> ValidationResult:
        if artifact.module != ModuleName.ENCAPSULATION:
            return ValidationResult(valid=False, errors=["Expected encapsulation artifact"])
        required = {"drug_bead_coupling", "encapsulation_efficiency_estimate"}
        missing = required - set(artifact.data.keys())
        if missing:
            return ValidationResult(valid=False, errors=[f"Missing fields: {missing}"])
        return ValidationResult(valid=True)

    def translate(self, artifact: ScaleArtifact) -> dict[str, Any]:
        enc = EncapsulationResult.model_validate(artifact.data)
        return {
            "drug_bead_coupling": enc.drug_bead_coupling,
            "initial_drug_loading": enc.encapsulation_efficiency_estimate,
            "translation_method": "md_encapsulation_to_formation",
        }


class FormationToTransport(ScaleBridge):
    """Map CG formation structure to continuum transport parameters."""

    name = "formation_to_transport"
    source_module = ModuleName.FORMATION
    target_module = ModuleName.TRANSPORT
    input_scale = SimulationScale.COARSE_GRAINED
    output_scale = SimulationScale.CONTINUUM

    def validate(self, artifact: ScaleArtifact) -> ValidationResult:
        if artifact.module != ModuleName.FORMATION:
            return ValidationResult(valid=False, errors=["Expected formation artifact"])
        if "hydrodynamic_radius_nm" not in artifact.data:
            return ValidationResult(valid=False, errors=["Missing hydrodynamic_radius_nm"])
        return ValidationResult(valid=True)

    def translate(self, artifact: ScaleArtifact) -> dict[str, Any]:
        form = FormationResult.model_validate(artifact.data)
        radius_m = form.hydrodynamic_radius_nm * 1e-9
        # Stokes-Einstein at 310 K, water viscosity
        viscosity = 0.692e-3  # Pa·s
        k_b = 1.380649e-23
        temperature = 310.15
        d_stokes = k_b * temperature / (6 * 3.14159 * viscosity * radius_m)
        return {
            "particle_radius_nm": form.hydrodynamic_radius_nm,
            "effective_diffusion_coefficient_m2_s": d_stokes,
            "morphology": form.morphology,
            "translation_method": "stokes_einstein_v1",
        }


BRIDGE_REGISTRY: dict[str, ScaleBridge] = {
    "encapsulation_to_formation": EncapsulationToFormation(),
    "formation_to_transport": FormationToTransport(),
}


def apply_bridge(bridge_name: str, artifact: ScaleArtifact) -> dict[str, Any]:
    bridge = BRIDGE_REGISTRY[bridge_name]
    result = bridge.validate(artifact)
    if not result.valid:
        raise ValueError(f"Bridge validation failed: {result.errors}")
    return bridge.translate(artifact)
