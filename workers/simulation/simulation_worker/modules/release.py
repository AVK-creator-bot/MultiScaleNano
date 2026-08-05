"""Release module — diffusion kinetics from formation + stability MD."""

from __future__ import annotations

from uuid import UUID

from multiscale_core.analysis.methodology import RELEASE_METHODS
from multiscale_core.bridges import apply_bridge
from multiscale_core.paths import ARTIFACT_DIR
from multiscale_core.schema.artifacts import ProvenanceRecord, ReleaseResult, ScaleArtifact
from multiscale_core.schema.nanocarrier import NanocarrierDesign
from multiscale_core.schema.simulation import SimulationMode
from multiscale_core.schema.workflow import ModuleName, SimulationScale

from simulation_worker.analysis.artifact_meta import enrich_artifact_data
from simulation_worker.analysis.require_md import require_field
from simulation_worker.modules.errors import SimulationAnalysisError


def run_release(
    run_id: str,
    design: NanocarrierDesign,
    upstream: dict,
    *,
    mode: SimulationMode = SimulationMode.STANDARD_MD,
) -> ScaleArtifact:
    work_dir = ARTIFACT_DIR / run_id / "release"
    work_dir.mkdir(parents=True, exist_ok=True)

    if "formation" not in upstream or "stability" not in upstream:
        raise SimulationAnalysisError("Release requires formation and stability MD artifacts.")

    rh_nm = require_field(upstream["formation"].data, "hydrodynamic_radius_nm", source="Formation")
    rh_m = rh_nm * 1e-9

    transport_params = apply_bridge("formation_to_transport", upstream["formation"])
    d_stokes = require_field(
        transport_params, "effective_diffusion_coefficient_m2_s", source="Formation→Transport bridge"
    )

    energy_std = require_field(upstream["stability"].data, "energy_std_kj_mol", source="Stability")
    pe = require_field(upstream["formation"].data, "potential_energy_kj_mol", source="Formation")
    energy_cv = energy_std / max(abs(pe), 1.0)
    stability_score = require_field(upstream["stability"].data, "stability_score", source="Stability")

    # Continuum extrapolation from MD-derived D, R_H, and thermal stability — not direct release MD.
    d_eff = d_stokes * max(1e-6, min(1.0, energy_cv**2))
    half_life_s = (rh_m**2) / (2 * d_eff * max(stability_score, 0.05))
    half_life_hours = max(0.1, half_life_s / 3600.0)

    profile = []
    for t in range(0, 49, 3):
        fraction = 1 - (0.5 ** (t / half_life_hours))
        profile.append({"time_hours": float(t), "fraction_released": round(fraction, 3)})

    result = ReleaseResult(
        half_life_hours=round(half_life_hours, 1),
        release_profile=profile,
        trigger_mechanism="continuum_extrapolation",
    )

    data = enrich_artifact_data(
        {
            **result.model_dump(),
            "simulation_mode": mode.value,
            "effective_diffusion_m2_s": d_eff,
            "stokes_diffusion_m2_s": d_stokes,
            "hydrodynamic_radius_nm": rh_nm,
            "energy_std_kj_mol": energy_std,
            "energy_cv": round(energy_cv, 4),
            "stability_score": stability_score,
            "analysis_basis": "continuum_extrapolation_from_md_formation_and_stability",
        },
        RELEASE_METHODS,
        analysis_source="continuum_bridge_from_md",
    )

    artifact = ScaleArtifact(
        run_id=UUID(run_id),
        module=ModuleName.RELEASE,
        scale=SimulationScale.CONTINUUM,
        data=data,
        provenance=ProvenanceRecord(
            upstream_artifacts=[upstream["stability"].id, upstream["formation"].id],
            translation_method="md_energy_fluctuation_diffusion",
        ),
    )

    (work_dir / "artifact.json").write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
    return artifact
