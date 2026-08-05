"""Formation module — MD-derived morphology only."""

from __future__ import annotations

from uuid import UUID

from multiscale_core.analysis.methodology import FORMATION_METHODS, aggregate_replicates
from multiscale_core.bridges import apply_bridge
from multiscale_core.drug.resolver import resolve_drug_structure
from multiscale_core.lipids import lipid_bead_counts
from multiscale_core.paths import ARTIFACT_DIR
from multiscale_core.simulation.seeds import run_seed
from multiscale_core.schema.artifacts import ArtifactFile, FormationResult, ProvenanceRecord, ScaleArtifact
from multiscale_core.schema.nanocarrier import NanocarrierDesign
from multiscale_core.schema.simulation import SimulationMode
from multiscale_core.schema.workflow import ModuleName, SimulationScale

from simulation_worker.analysis.artifact_meta import enrich_artifact_data
from simulation_worker.engine.openmm_md import (
    md_steps_for_mode,
    replicate_count_for_mode,
    run_formation_md,
    run_replicated_md,
)
from simulation_worker.modules.errors import SimulationAnalysisError
from simulation_worker.structure.export import export_md_structure


def run_formation(
    run_id: str,
    design: NanocarrierDesign,
    upstream: dict,
    *,
    mode: SimulationMode = SimulationMode.STANDARD_MD,
) -> ScaleArtifact:
    work_dir = ARTIFACT_DIR / run_id / "formation"
    work_dir.mkdir(parents=True, exist_ok=True)

    resolved = resolve_drug_structure(design.drug, work_dir / "structure")
    bridge_params = {}
    if "encapsulation" in upstream:
        bridge_params = apply_bridge("encapsulation_to_formation", upstream["encapsulation"])

    steps = md_steps_for_mode(mode.value)
    n_rep = replicate_count_for_mode(mode.value)
    if mode == SimulationMode.SCREENING or steps <= 0:
        raise SimulationAnalysisError(
            "Formation requires MD simulation. Select Standard MD or Production MD mode."
        )

    lipid_alloc = lipid_bead_counts(design, total_lipid_beads=max(20, int(design.target_size_nm / 2)))
    n_beads = sum(n for _, n, _ in lipid_alloc) + max(2, resolved.bead_count // 2)
    lipid_specs = []
    for _, n, p in lipid_alloc:
        lipid_specs.extend([(p.bead_mass_amu, 0.45, p.epsilon_kj_mol)] * n)

    def _one(replicate: int):
        return run_formation_md(
            work_dir / f"rep_{replicate}",
            n_beads=n_beads,
            radius_nm=design.target_size_nm / 2,
            steps=steps,
            temperature_k=design.environment.temperature_k,
            random_seed=run_seed(run_id, "formation", replicate),
            lipid_bead_specs=lipid_specs if len(lipid_specs) == n_beads else None,
        )

    md_results = run_replicated_md(_one, n_rep)
    if not all(r.success and r.radius_of_gyration_nm is not None for r in md_results):
        failed = next(r for r in md_results if not r.success)
        raise SimulationAnalysisError(f"Formation MD failed: {failed.log}")

    md = md_results[0]
    radii = [r.radius_of_gyration_nm * 2 for r in md_results]
    rg_u = aggregate_replicates(radii)
    rg_u.metric = "hydrodynamic_radius_nm"

    polydispersities = []
    for r in md_results:
        pd = (r.energy_std_kj_mol or 0) / max(abs(r.potential_energy_kj_mol or 1), 1)
        polydispersities.append(min(0.3, max(0.02, pd)))
    pd_u = aggregate_replicates(polydispersities)
    pd_u.metric = "polydispersity"

    drug_core = md.drug_core_fraction
    if drug_core is None and "encapsulation" in upstream:
        drug_core = upstream["encapsulation"].data.get("core_fraction", 0.0)

    enc_eff = bridge_params.get("initial_drug_loading")
    if enc_eff is None and "encapsulation" in upstream:
        enc_eff = upstream["encapsulation"].data.get("encapsulation_efficiency_estimate", 0.0)

    form = FormationResult(
        hydrodynamic_radius_nm=round(rg_u.mean, 1),
        morphology="core-shell" if (drug_core or 0) > 0.3 else "compact-sphere",
        polydispersity=round(pd_u.mean, 3),
        drug_core_fraction=round(drug_core or enc_eff or 0.0, 3),
    )

    structure = export_md_structure(
        work_dir,
        md,
        ["lipid"] * len(md.final_positions_nm or []),
        title=f"Formation — {design.name}",
    )

    data = enrich_artifact_data(
        {
            **form.model_dump(),
            "simulation_mode": mode.value,
            "md_steps": md.steps,
            "n_replicates": n_rep,
            "potential_energy_kj_mol": md.potential_energy_kj_mol,
            "radius_of_gyration_nm": md.radius_of_gyration_nm,
            "compactness": md.compactness,
            "structure": structure,
        },
        FORMATION_METHODS,
        uncertainty={"hydrodynamic_radius_nm": rg_u, "polydispersity": pd_u},
    )

    artifact = ScaleArtifact(
        run_id=UUID(run_id),
        module=ModuleName.FORMATION,
        scale=SimulationScale.COARSE_GRAINED,
        data=data,
        uncertainty={"hydrodynamic_radius_nm": rg_u.model_dump()},
        provenance=ProvenanceRecord(
            upstream_artifacts=[upstream["encapsulation"].id] if "encapsulation" in upstream else [],
            translation_method="encapsulation_to_formation",
            force_field="lj_coarse_grained",
            engine_version=md.engine,
        ),
        files=(
            [ArtifactFile(path="structure.pdb", file_type="pdb", description="Final MD bead coordinates")]
            if structure.get("available")
            else []
        ),
    )

    (work_dir / "artifact.json").write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
    return artifact
