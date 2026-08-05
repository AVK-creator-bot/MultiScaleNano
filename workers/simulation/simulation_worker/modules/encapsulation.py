"""Encapsulation module — MD-only analysis from resolved drug structure."""

from __future__ import annotations

from uuid import UUID

from multiscale_core.analysis.methodology import ENCAPSULATION_METHODS, aggregate_replicates
from multiscale_core.drug.resolver import resolve_drug_structure
from multiscale_core.lipids import drug_bead_count_from_loading, lipid_bead_counts
from multiscale_core.paths import ARTIFACT_DIR
from multiscale_core.schema.artifacts import ArtifactFile, ProvenanceRecord, ScaleArtifact
from multiscale_core.schema.nanocarrier import NanocarrierDesign
from multiscale_core.schema.simulation import SimulationMode
from multiscale_core.schema.workflow import ModuleName, SimulationScale

from simulation_worker.analysis.artifact_meta import enrich_artifact_data
from simulation_worker.analysis.md_analysis import encapsulation_from_md
from simulation_worker.engine.openmm_md import (
    md_steps_for_mode,
    replicate_count_for_mode,
    run_encapsulation_md,
    run_replicated_md,
)
from simulation_worker.modules.errors import SimulationAnalysisError
from simulation_worker.structure.export import export_md_structure


def run_encapsulation(
    run_id: str,
    design: NanocarrierDesign,
    upstream: dict,
    *,
    mode: SimulationMode = SimulationMode.STANDARD_MD,
) -> ScaleArtifact:
    work_dir = ARTIFACT_DIR / run_id / "encapsulation"
    work_dir.mkdir(parents=True, exist_ok=True)

    resolved = resolve_drug_structure(design.drug, work_dir / "structure")
    (work_dir / "resolved_structure.json").write_text(
        resolved.model_dump_json(indent=2), encoding="utf-8"
    )

    steps = md_steps_for_mode(mode.value)
    n_rep = replicate_count_for_mode(mode.value)
    if mode == SimulationMode.SCREENING or steps <= 0:
        raise SimulationAnalysisError(
            "Encapsulation requires MD simulation. Select Standard MD or Production MD mode."
        )

    lipid_alloc = lipid_bead_counts(design, total_lipid_beads=max(16, int(design.target_size_nm / 2)))
    lipid_beads = sum(n for _, n, _ in lipid_alloc)
    drug_beads = drug_bead_count_from_loading(
        design, resolved.molecular_weight, resolved.bead_count, lipid_beads
    )
    lipid_specs = []
    for _, n, p in lipid_alloc:
        lipid_specs.extend([(p.bead_mass_amu, 0.45, p.epsilon_kj_mol)] * n)

    total_beads = lipid_beads + drug_beads

    def _one(replicate: int):
        return run_encapsulation_md(
            work_dir=work_dir / f"rep_{replicate}",
            lipid_bead_count=lipid_beads,
            drug_bead_count=drug_beads,
            steps=steps,
            temperature_k=design.environment.temperature_k,
            target_radius_nm=design.target_size_nm / 2,
            random_seed=100 + replicate,
            lipid_bead_specs=lipid_specs,
        )

    md_results = run_replicated_md(_one, n_rep)
    if not all(r.success and r.potential_energy_kj_mol is not None for r in md_results):
        failed = next(r for r in md_results if not r.success)
        raise SimulationAnalysisError(f"Encapsulation MD failed: {failed.log}")

    md = md_results[0]
    enc = encapsulation_from_md(
        md,
        drug_bead_count=drug_beads,
        total_beads=total_beads,
        drug_location=design.drug.encapsulation_mode,
    )
    enc.md_analysis.temperature_k = design.environment.temperature_k

    pe_u = aggregate_replicates([r.potential_energy_kj_mol for r in md_results])
    pe_u.metric = "potential_energy_kj_mol"
    eff_values = []
    for r in md_results:
        e = encapsulation_from_md(r, drug_beads, total_beads, design.drug.encapsulation_mode)
        eff_values.append(e.encapsulation_efficiency_estimate)
    eff_u = aggregate_replicates(eff_values)
    eff_u.metric = "encapsulation_efficiency_estimate"

    structure = export_md_structure(
        work_dir,
        md,
        ["drug"] * max(2, drug_beads) + ["lipid"] * max(8, lipid_beads),
        title=f"Encapsulation — {design.name}",
    )

    data = enrich_artifact_data(
        {
            "drug_retention_free_energy_kcal_mol": enc.drug_retention_free_energy_kcal_mol,
            "encapsulation_efficiency_estimate": round(eff_u.mean, 3),
            "drug_bead_coupling": enc.drug_bead_coupling,
            "drug_location": enc.drug_location,
            "core_fraction": enc.core_fraction,
            "simulation_mode": mode.value,
            "md_steps": md.steps,
            "n_replicates": n_rep,
            "potential_energy_kj_mol": round(pe_u.mean, 2),
            "energy_std_kj_mol": md.energy_std_kj_mol,
            "radius_of_gyration_nm": md.radius_of_gyration_nm,
            "drug_core_fraction_md": md.drug_core_fraction,
            "drug_bead_count": drug_beads,
            "lipid_bead_count": lipid_beads,
            "loading_pct": design.drug.loading_pct,
            "lipid_composition": [
                {"name": name, "beads": n, "ratio": next(l.ratio for l in design.lipids if l.name == name)}
                for name, n, _ in lipid_alloc
            ],
            "drug_structure": {
                "payload_type": resolved.payload_type.value,
                "molecular_weight": resolved.molecular_weight,
                "bead_count": resolved.bead_count,
                "source": resolved.source_type.value,
                "source_value": resolved.source_value,
            },
            "structure": structure,
        },
        ENCAPSULATION_METHODS,
        uncertainty={"potential_energy_kj_mol": pe_u, "encapsulation_efficiency_estimate": eff_u},
    )

    artifact = ScaleArtifact(
        run_id=UUID(run_id),
        module=ModuleName.ENCAPSULATION,
        scale=SimulationScale.COARSE_GRAINED,
        data=data,
        uncertainty={
            "potential_energy_kj_mol": pe_u.model_dump(),
            "encapsulation_efficiency_estimate": eff_u.model_dump(),
        },
        provenance=ProvenanceRecord(
            force_field="lj_coarse_grained",
            engine_version=md.engine,
            translation_method="md_trajectory_analysis",
        ),
        files=(
            [ArtifactFile(path="structure.pdb", file_type="pdb", description="Final MD bead coordinates")]
            if structure.get("available")
            else []
        ),
    )

    (work_dir / "artifact.json").write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
    return artifact
