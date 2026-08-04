"""Cell interaction module — membrane approach MD."""

from __future__ import annotations

import json
import math
from uuid import UUID

from multiscale_core.analysis.methodology import CELL_METHODS, aggregate_replicates
from multiscale_core.paths import ARTIFACT_DIR
from multiscale_core.schema.artifacts import CellInteractionResult, ProvenanceRecord, ScaleArtifact
from multiscale_core.schema.nanocarrier import NanocarrierDesign
from multiscale_core.schema.simulation import SimulationMode
from multiscale_core.schema.workflow import ModuleName, SimulationScale

from simulation_worker.analysis.artifact_meta import enrich_artifact_data
from simulation_worker.engine.openmm_md import (
    md_steps_for_mode,
    replicate_count_for_mode,
    run_membrane_approach_md,
    run_replicated_md,
)
from simulation_worker.modules.errors import SimulationAnalysisError


def run_cell_interaction(
    run_id: str,
    design: NanocarrierDesign,
    upstream: dict,
    *,
    mode: SimulationMode = SimulationMode.STANDARD_MD,
) -> ScaleArtifact:
    work_dir = ARTIFACT_DIR / run_id / "cell_interaction"
    work_dir.mkdir(parents=True, exist_ok=True)

    steps = md_steps_for_mode(mode.value)
    n_rep = replicate_count_for_mode(mode.value)
    if mode == SimulationMode.SCREENING or steps <= 0:
        raise SimulationAnalysisError("Cell interaction requires MD simulation.")

    radius_nm = design.target_size_nm / 2
    if "formation" in upstream:
        radius_nm = upstream["formation"].data.get("hydrodynamic_radius_nm", radius_nm * 2) / 2

    n_beads = max(12, int(radius_nm * 4))

    def _one(replicate: int):
        return run_membrane_approach_md(
            work_dir / f"rep_{replicate}",
            n_beads=n_beads,
            radius_nm=radius_nm,
            steps=steps,
            temperature_k=design.environment.temperature_k,
            random_seed=400 + replicate,
        )

    rep_results = run_replicated_md(_one, n_rep)
    adhesions = []
    md_ref = None
    for md, adhesion_kT in rep_results:
        if not md.success:
            raise SimulationAnalysisError(f"Membrane approach MD failed: {md.log}")
        adhesions.append(adhesion_kT)
        md_ref = md

    adh_u = aggregate_replicates(adhesions)
    adh_u.metric = "membrane_adhesion_energy_kT"

    # Boltzmann-weighted uptake from MD adhesion (ΔG in kT units)
    uptake = min(0.95, max(0.05, 1.0 - math.exp(-adh_u.mean)))

    stability = 0.5
    if "stability" in upstream:
        stability = upstream["stability"].data.get("stability_score", 0.5)
    escape = min(0.9, max(0.1, stability * 0.85))

    core_frac = 0.5
    if "formation" in upstream:
        core_frac = upstream["formation"].data.get("drug_core_fraction", 0.5)

    release_frac = min(0.85, uptake * escape * core_frac)
    has_ligand = len(design.ligands) > 0
    pathway = "receptor_mediated" if has_ligand else "clathrin_mediated"

    result = CellInteractionResult(
        membrane_adhesion_energy_kT=round(adh_u.mean, 2),
        uptake_probability=round(uptake, 3),
        endosomal_escape_probability=round(escape, 3),
        intracellular_release_fraction=round(release_frac, 3),
        primary_pathway=pathway,
    )

    (work_dir / "inputs.json").write_text(
        json.dumps({"mode": mode.value, "radius_nm": radius_nm, "cell": design.target.cell_type}, indent=2),
        encoding="utf-8",
    )

    data = enrich_artifact_data(
        {
            **result.model_dump(),
            "simulation_mode": mode.value,
            "md_steps": steps,
            "n_replicates": n_rep,
            "escape_source": "stability_md_upstream",
        },
        CELL_METHODS,
        uncertainty={"membrane_adhesion_energy_kT": adh_u},
    )

    artifact = ScaleArtifact(
        run_id=UUID(run_id),
        module=ModuleName.CELL_INTERACTION,
        scale=SimulationScale.COARSE_GRAINED,
        data=data,
        uncertainty={"membrane_adhesion_energy_kT": adh_u.model_dump()},
        provenance=ProvenanceRecord(
            upstream_artifacts=[upstream["formation"].id] if "formation" in upstream else [],
            force_field="lj_coarse_grained",
            engine_version=md_ref.engine if md_ref else "openmm",
            translation_method="membrane_wall_approach_md",
        ),
    )
    (work_dir / "artifact.json").write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
    return artifact
