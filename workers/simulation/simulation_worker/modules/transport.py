"""Transport module — Stokes-Einstein + Fickian penetration from formation MD."""

from __future__ import annotations

from uuid import UUID

from multiscale_core.analysis.constants import TISSUE_POROSITY
from multiscale_core.analysis.methodology import TRANSPORT_METHODS
from multiscale_core.bridges import apply_bridge
from multiscale_core.paths import ARTIFACT_DIR
from multiscale_core.schema.artifacts import ProvenanceRecord, ScaleArtifact, TransportResult
from multiscale_core.schema.nanocarrier import NanocarrierDesign
from multiscale_core.schema.simulation import SimulationMode
from multiscale_core.schema.workflow import ModuleName, SimulationScale

from simulation_worker.analysis.artifact_meta import enrich_artifact_data
from simulation_worker.modules.errors import SimulationAnalysisError


def run_transport(
    run_id: str,
    design: NanocarrierDesign,
    upstream: dict,
    *,
    mode: SimulationMode = SimulationMode.STANDARD_MD,
) -> ScaleArtifact:
    work_dir = ARTIFACT_DIR / run_id / "transport"
    work_dir.mkdir(parents=True, exist_ok=True)

    if "formation" not in upstream:
        raise SimulationAnalysisError("Transport requires formation MD artifact.")

    transport_params = apply_bridge("formation_to_transport", upstream["formation"])
    tissue = (design.target.tissue or "tumor").lower()
    porosity_entry = TISSUE_POROSITY.get(tissue, TISSUE_POROSITY["tumor"])
    porosity, porosity_ref = porosity_entry

    d_eff = transport_params.get("effective_diffusion_coefficient_m2_s", 1e-12)
    time_s = 3600
    penetration_m = (2 * d_eff * porosity * time_s) ** 0.5
    penetration_um = penetration_m * 1e6

    result = TransportResult(
        effective_diffusion_coefficient_m2_s=d_eff,
        penetration_depth_um=round(penetration_um, 2),
        tissue=tissue,
    )

    data = enrich_artifact_data(
        {
            **result.model_dump(),
            "simulation_mode": mode.value,
            "tissue_porosity": porosity,
            "porosity_reference": porosity_ref,
            "integration_time_s": time_s,
            "particle_radius_nm": transport_params.get("particle_radius_nm"),
        },
        TRANSPORT_METHODS,
    )

    artifact = ScaleArtifact(
        run_id=UUID(run_id),
        module=ModuleName.TRANSPORT,
        scale=SimulationScale.CONTINUUM,
        data=data,
        provenance=ProvenanceRecord(
            upstream_artifacts=[upstream["formation"].id],
            translation_method="formation_to_transport_stokes_einstein",
        ),
    )

    (work_dir / "artifact.json").write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
    return artifact
