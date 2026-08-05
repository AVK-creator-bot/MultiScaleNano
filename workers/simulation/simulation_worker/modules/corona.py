"""Protein corona module — competitive adsorption MD."""

from __future__ import annotations

import json
from uuid import UUID

from multiscale_core.analysis.constants import FLUID_PROTEINS, SERUM_PROTEIN_MW
from multiscale_core.analysis.methodology import CORONA_METHODS, aggregate_replicates
from multiscale_core.paths import ARTIFACT_DIR
from multiscale_core.simulation.seeds import run_seed
from multiscale_core.schema.artifacts import ArtifactFile, CoronaResult, ProvenanceRecord, ScaleArtifact
from multiscale_core.schema.nanocarrier import NanocarrierDesign
from multiscale_core.schema.simulation import SimulationMode
from multiscale_core.schema.workflow import ModuleName, SimulationScale

from simulation_worker.analysis.artifact_meta import enrich_artifact_data
from simulation_worker.engine.openmm_md import (
    md_steps_for_mode,
    replicate_count_for_mode,
    run_corona_adsorption_md,
    run_replicated_md,
)
from simulation_worker.modules.errors import SimulationAnalysisError
from simulation_worker.structure.export import export_md_structure


def run_corona(
    run_id: str,
    design: NanocarrierDesign,
    upstream: dict,
    *,
    mode: SimulationMode = SimulationMode.STANDARD_MD,
) -> ScaleArtifact:
    work_dir = ARTIFACT_DIR / run_id / "corona"
    work_dir.mkdir(parents=True, exist_ok=True)

    steps = md_steps_for_mode(mode.value)
    n_rep = replicate_count_for_mode(mode.value)
    if mode == SimulationMode.SCREENING or steps <= 0:
        raise SimulationAnalysisError("Corona analysis requires MD simulation.")

    base_radius = design.target_size_nm / 2
    if "formation" in upstream:
        base_radius = upstream["formation"].data.get("hydrodynamic_radius_nm", base_radius * 2) / 2

    fluid = design.environment.fluid
    proteins = FLUID_PROTEINS.get(fluid, FLUID_PROTEINS["serum"])
    protein_beads = max(5, sum(max(1, int(SERUM_PROTEIN_MW.get(p, 50000) / 20000)) for p in proteins[:5]))
    np_beads = max(10, int(base_radius * 6))

    def _one(replicate: int):
        return run_corona_adsorption_md(
            work_dir / f"rep_{replicate}",
            np_beads=np_beads,
            protein_beads=protein_beads,
            np_radius_nm=base_radius,
            steps=steps,
            temperature_k=design.environment.temperature_k,
            random_seed=run_seed(run_id, "corona", replicate),
        )

    rep_results = run_replicated_md(_one, n_rep)
    adsorbed_counts = []
    ligand_fracs = []
    md_ref = None
    for md, adsorbed, ligand_frac in rep_results:
        if not md.success:
            raise SimulationAnalysisError(f"Corona MD failed: {md.log}")
        adsorbed_counts.append(float(adsorbed))
        ligand_fracs.append(ligand_frac)
        md_ref = md

    ads_u = aggregate_replicates(adsorbed_counts)
    ads_u.metric = "adsorbed_protein_count"
    lig_u = aggregate_replicates(ligand_fracs)
    lig_u.metric = "ligand_accessible_fraction"

    corona_thickness = ads_u.mean * 0.35  # nm per adsorbed coarse-grained protein bead
    effective_radius = base_radius + corona_thickness
    dominant = proteins[: max(1, int(ads_u.mean))] if proteins else ["none"]

    result = CoronaResult(
        effective_radius_nm=round(effective_radius, 1),
        ligand_accessible_fraction=round(lig_u.mean, 3),
        dominant_proteins=dominant,
        surface_charge_delta_mv=round(-ads_u.mean * 2.5, 1),
    )

    (work_dir / "inputs.json").write_text(
        json.dumps({"fluid": fluid, "proteins": proteins, "mode": mode.value}, indent=2),
        encoding="utf-8",
    )

    structure = {}
    if md_ref:
        structure = export_md_structure(
            work_dir,
            md_ref,
            ["np"] * np_beads + ["protein"] * protein_beads,
            title=f"Protein corona — {design.name}",
        )

    data = enrich_artifact_data(
        {
            **result.model_dump(),
            "simulation_mode": mode.value,
            "md_steps": steps,
            "n_replicates": n_rep,
            "adsorbed_protein_count": round(ads_u.mean, 1),
            "np_radius_nm": base_radius,
            "structure": structure,
        },
        CORONA_METHODS,
        uncertainty={"adsorbed_protein_count": ads_u, "ligand_accessible_fraction": lig_u},
    )

    artifact = ScaleArtifact(
        run_id=UUID(run_id),
        module=ModuleName.CORONA,
        scale=SimulationScale.MESOSCALE,
        data=data,
        uncertainty={"adsorbed_protein_count": ads_u.model_dump()},
        provenance=ProvenanceRecord(
            upstream_artifacts=[upstream["formation"].id] if "formation" in upstream else [],
            force_field="lj_coarse_grained",
            engine_version=md_ref.engine if md_ref else "openmm",
            translation_method="competitive_adsorption_md",
        ),
        files=(
            [ArtifactFile(path="structure.pdb", file_type="pdb", description="Final MD bead coordinates")]
            if structure.get("available")
            else []
        ),
    )
    (work_dir / "artifact.json").write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
    return artifact
